# coding=utf-8
u"""Service Module for F5® LBaaSv2."""
# Copyright 2014-2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import datetime
import json

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from f5lbaasdriver.v2.bigip import constants_v2
from f5lbaasdriver.v2.bigip.disconnected_service import DisconnectedService
from f5lbaasdriver.v2.bigip import exceptions as f5_exc
from f5lbaasdriver.v2.bigip import neutron_client as q_client

LOG = logging.getLogger(__name__)


class LBaaSv2ServiceBuilder(object):
    """The class creates a service definition from neutron database.

    A service definition represents all the information required to
    construct a load-balancing service on BigIP.

    Requests come in to agent as full service definitions, not incremental
    changes. The driver looks up networks, mac entries, segmentation info,
    etc and places all information in a service object (which is a python
    dictionary variable) and passes that to the agent.

    """

    def __init__(self, driver):
        """Get full service definition from loadbalancer id."""
        self.driver = driver

        self.net_cache = {}
        self.subnet_cache = {}
        self.last_cache_update = datetime.datetime.fromtimestamp(0)
        self.plugin = self.driver.plugin
        self.disconnected_service = DisconnectedService()
        self.q_client = q_client.F5NetworksNeutronClient(self.plugin)

    def build(self, context, loadbalancer, agent):
        """Get full service definition from loadbalancer ID."""
        # Invalidate cache if it is too old
        if ((datetime.datetime.now() - self.last_cache_update).seconds >
                constants_v2.NET_CACHE_SECONDS):
            self.net_cache = {}
            self.subnet_cache = {}

        service = {}
        with context.session.begin(subtransactions=True):
            LOG.debug('Building service definition entry for %s'
                      % loadbalancer.id)

            # Start with the neutron loadbalancer definition
            service['loadbalancer'] = self._get_extended_loadbalancer(
                context,
                loadbalancer
            )

            # Get the subnet network associated with the VIP.
            subnet_map = {}
            subnet_id = loadbalancer.vip_subnet_id
            vip_subnet = self._get_subnet_cached(
                context,
                subnet_id
            )
            subnet_map[subnet_id] = vip_subnet

            # Get the network associated with the Loadbalancer.
            network_map = {}
            vip_port = service['loadbalancer']['vip_port']
            network_id = vip_port['network_id']
            service['loadbalancer']['network_id'] = network_id
            network = self._get_network_cached(
                context,
                network_id
            )
            # Override the segmentation ID and network type for this network
            # if we are running in disconnected service mode
            agent_config = self.deserialize_agent_configurations(
                agent['configurations'])
            segment_data = self.disconnected_service.get_network_segment(
                context, agent_config, network)
            if segment_data:
                network['provider:segmentation_id'] = \
                    segment_data.get('segmentation_id', None)
                network['provider:network_type'] = \
                    segment_data.get('network_type', None)
                network['provider:physical_network'] = \
                    segment_data.get('physical_network', None)
            network_map[network_id] = network

            # Check if the tenant can create a loadbalancer on the network.
            if (agent and not self._valid_tenant_ids(network,
                                                     loadbalancer.tenant_id,
                                                     agent)):
                LOG.error("Creating a loadbalancer %s for tenant %s on a"
                          "  non-shared network %s owned by %s." % (
                              loadbalancer.id,
                              loadbalancer.tenant_id,
                              network['id'],
                              network['tenant_id']))

            # Get the network VTEPs if the network provider type is
            # either gre or vxlan.
            if 'provider:network_type' in network:
                net_type = network['provider:network_type']
                if net_type == 'vxlan' or net_type == 'gre':
                    self._populate_loadbalancer_network_vteps(
                        context,
                        service['loadbalancer'],
                        net_type
                    )

            # Get listeners and pools.
            service['listeners'] = self._get_listeners(context, loadbalancer)

            service['pools'], service['healthmonitors'] = \
                self._get_pools_and_healthmonitors(context, loadbalancer)

            service['members'] = self._get_members(
                context, service['pools'], subnet_map, network_map)

            service['subnets'] = subnet_map
            service['networks'] = network_map

            service['l7policies'] = self._get_l7policies(
                context, service['listeners'])
            service['l7policy_rules'] = self._get_l7policy_rules(
                context, service['l7policies'])

        return service

    @log_helpers.log_method_call
    def _get_extended_member(self, context, member):
        """Get extended member attributes and member networking."""
        member_dict = member.to_dict(pool=False)
        subnet_id = member.subnet_id
        subnet = self._get_subnet_cached(
            context,
            subnet_id
        )
        network_id = subnet['network_id']
        network = self._get_network_cached(
            context,
            network_id
        )

        member_dict['network_id'] = network_id

        # Use the fixed ip.
        filter = {'fixed_ips': {'subnet_id': [subnet_id],
                                'ip_address': [member.address]}}
        ports = self.plugin.db._core_plugin.get_ports(
            context,
            filter
        )

        # we no longer support member port creation
        if len(ports) == 1:
            member_dict['port'] = ports[0]
            self._populate_member_network(context, member_dict, network)
        elif len(ports) == 0:
            self._populate_member_network(context, member_dict, network)
            LOG.warning("Lbaas member %s has no associated neutron port"
                        % member.address)
        elif len(ports) > 1:
            LOG.warning("Multiple ports found for member: %s" % member.address)

        return (member_dict, subnet, network)

    @log_helpers.log_method_call
    def _get_extended_loadbalancer(self, context, loadbalancer):
        """Get loadbalancer dictionary and add extended data(e.g. VIP)."""
        loadbalancer_dict = loadbalancer.to_api_dict()
        vip_port = self.plugin.db._core_plugin.get_port(
            context,
            loadbalancer.vip_port_id
        )
        loadbalancer_dict['vip_port'] = vip_port

        return loadbalancer_dict

    @log_helpers.log_method_call
    def _get_subnet_cached(self, context, subnet_id):
        """Retrieve subnet from cache if available; otherwise, from Neutron."""
        if subnet_id not in self.subnet_cache:
            subnet = self.plugin.db._core_plugin.get_subnet(
                context,
                subnet_id
            )
            self.subnet_cache[subnet_id] = subnet
        return self.subnet_cache[subnet_id]

    @log_helpers.log_method_call
    def _get_network_cached(self, context, network_id):
        """Retrieve network from cache or from Neutron."""
        if network_id not in self.net_cache:
            network = self.plugin.db._core_plugin.get_network(
                context,
                network_id
            )
            if 'provider:network_type' not in network:
                network['provider:network_type'] = 'undefined'
            if 'provider:segmentation_id' not in network:
                network['provider:segmentation_id'] = 0
            self.net_cache[network_id] = network

        return self.net_cache[network_id]

    def _populate_member_network(self, context, member, network):
        """Add vtep networking info to pool member and update the network."""
        member['vxlan_vteps'] = []
        member['gre_vteps'] = []

        agent_config = {}
        segment_data = self.disconnected_service.get_network_segment(
            context, agent_config, network)
        if segment_data:
            network['provider:segmentation_id'] = \
                segment_data.get('segmentation_id', None)
            network['provider:network_type'] = \
                segment_data.get('network_type', None)
            network['provider:physical_network'] = \
                segment_data.get('physical_network', None)

        net_type = network.get('provider:network_type', "undefined")
        if net_type == 'vxlan':
            if 'port' in member and 'binding:host_id' in member['port']:
                host = member['port']['binding:host_id']
                member['vxlan_vteps'] = self._get_endpoints(
                    context, 'vxlan', host)
        if net_type == 'gre':
            if 'port' in member and 'binding:host_id' in member['port']:
                host = member['port']['binding:host_id']
                member['gre_vteps'] = self._get_endpoints(
                    context, 'gre', host)
        if 'provider:network_type' not in network:
            network['provider:network_type'] = 'undefined'
        if 'provider:segmentation_id' not in network:
            network['provider:segmentation_id'] = 0

    @log_helpers.log_method_call
    def _populate_loadbalancer_network_vteps(
            self,
            context,
            loadbalancer,
            net_type):
        """Put related tunnel endpoints in loadbalancer definiton."""
        loadbalancer['vxlan_vteps'] = []
        loadbalancer['gre_vteps'] = []
        network_id = loadbalancer['vip_port']['network_id']

        ports = self._get_ports_on_network(
            context,
            network_id=network_id
        )

        vtep_hosts = []
        for port in ports:
            if ('binding:host_id' in port and
                    port['binding:host_id'] not in vtep_hosts):
                vtep_hosts.append(port['binding:host_id'])

        for vtep_host in vtep_hosts:
            if net_type == 'vxlan':
                endpoints = self._get_endpoints(context, 'vxlan')
                for ep in endpoints:
                    if ep not in loadbalancer['vxlan_vteps']:
                        loadbalancer['vxlan_vteps'].append(ep)
            elif net_type == 'gre':
                endpoints = self._get_endpoints(context, 'gre')
                for ep in endpoints:
                    if ep not in loadbalancer['gre_vteps']:
                        loadbalancer['gre_vteps'].append(ep)

    def _get_endpoints(self, context, net_type, host=None):
        """Get vxlan or gre tunneling endpoints from all agents."""
        endpoints = []

        agents = self.plugin.db._core_plugin.get_agents(context)
        for agent in agents:
            if ('configurations' in agent and (
                    'tunnel_types' in agent['configurations'])):

                if net_type in agent['configurations']['tunnel_types']:
                    if 'tunneling_ip' in agent['configurations']:
                        if not host or (agent['host'] == host):
                            endpoints.append(
                                agent['configurations']['tunneling_ip']
                            )
                    if 'tunneling_ips' in agent['configurations']:
                        for ip_addr in (
                                agent['configurations']['tunneling_ips']):
                            if not host or (agent['host'] == host):
                                endpoints.append(ip_addr)

        return endpoints

    def deserialize_agent_configurations(self, configurations):
        """Return a dictionary for the agent configuration."""
        agent_conf = configurations
        if not isinstance(agent_conf, dict):
            try:
                agent_conf = json.loads(configurations)
            except ValueError as ve:
                LOG.error('can not JSON decode %s : %s'
                          % (agent_conf, ve.message))
                agent_conf = {}
        return agent_conf

    @log_helpers.log_method_call
    def _is_common_network(self, network, agent):
        common_external_networks = False
        common_networks = {}

        if agent and "configurations" in agent:
            agent_configs = self.deserialize_agent_configurations(
                agent['configurations'])

            if 'common_networks' in agent_configs:
                common_networks = agent_configs['common_networks']

            if 'f5_common_external_networks' in agent_configs:
                common_external_networks = (
                    agent_configs['f5_common_external_networks'])

        return (network['shared'] or
                (network['id'] in common_networks) or
                ('router:external' in network and
                 network['router:external'] and
                 common_external_networks))

    def _valid_tenant_ids(self, network, lb_tenant_id, agent):
        if (network['tenant_id'] == lb_tenant_id):
            return True
        else:
            return self._is_common_network(network, agent)

    @log_helpers.log_method_call
    def _get_ports_on_network(self, context, network_id=None):
        """Get ports for network."""
        if not isinstance(network_id, list):
            network_ids = [network_id]
        filters = {'network_id': network_ids}
        return self.driver.plugin.db._core_plugin.get_ports(
            context,
            filters=filters
        )

    @log_helpers.log_method_call
    def _get_l7policies(self, context, listeners):
        """Get l7 policies filtered by listeners."""
        l7policies = []
        if listeners:
            listener_ids = [l['id'] for l in listeners]
            policies = self.plugin.db.get_l7policies(
                context, filters={'listener_id': listener_ids})
            l7policies.extend(self._l7policy_to_dict(p) for p in policies)

        for index, pol in enumerate(l7policies):
            try:
                assert len(pol['listeners']) == 1
            except AssertionError:
                msg = 'A policy should have only one listener, but found ' \
                    '{0} for policy {1}'.format(
                        len(pol['listeners']), pol['id'])
                raise f5_exc.PolicyHasMoreThanOneListener(msg)
            else:
                listener = pol.pop('listeners')[0]
                l7policies[index]['listener_id'] = listener['id']

        return l7policies

    @log_helpers.log_method_call
    def _get_l7policy_rules(self, context, l7policies):
        """Get l7 policy rules filtered by l7 policies."""
        l7policy_rules = []
        if l7policies:
            policy_ids = [p['id'] for p in l7policies]
            for pol_id in policy_ids:
                rules = self.plugin.db.get_l7policy_rules(context, pol_id)
                l7policy_rules.extend(
                    self._l7rule_to_dict(rule) for rule in rules)

        for index, rule in enumerate(l7policy_rules):
            try:
                assert len(rule['policies']) == 1
            except AssertionError:
                msg = 'A rule should have only one policy, but found ' \
                    '{0} for rule {1}'.format(
                        len(rule['policies']), rule['id'])
                raise f5_exc.RuleHasMoreThanOnePolicy(msg)
            else:
                pol = rule['policies'][0]
                l7policy_rules[index]['policy_id'] = pol['id']

        return l7policy_rules

    @log_helpers.log_method_call
    def _get_listeners(self, context, loadbalancer):
        listeners = []
        db_listeners = self.plugin.db.get_listeners(
            context,
            filters={'loadbalancer_id': [loadbalancer.id]}
        )

        for listener in db_listeners:
            listener_dict = listener.to_dict(
                loadbalancer=False,
                default_pool=False,
                l7_policies=False
            )
            listener_dict['l7_policies'] = \
                [{'id': l7_policy.id} for l7_policy in listener.l7_policies]
            if listener.default_pool:
                listener_dict['default_pool_id'] = listener.default_pool.id

            listeners.append(listener_dict)

        return listeners

    @log_helpers.log_method_call
    def _get_pools_and_healthmonitors(self, context, loadbalancer):
        """Return list of pools and list of healthmonitors as dicts."""
        healthmonitors = []
        pools = []

        if loadbalancer and loadbalancer.id:
            db_pools = self.plugin.db.get_pools(
                context,
                filters={'loadbalancer_id': [loadbalancer.id]}
            )

            for pool in db_pools:
                pools.append(self._pool_to_dict(pool))
                pool_id = pool.id
                healthmonitor_id = pool.healthmonitor_id
                if healthmonitor_id:
                    healthmonitor = self.plugin.db.get_healthmonitor(
                        context,
                        healthmonitor_id)
                    if healthmonitor:
                        healthmonitor_dict = healthmonitor.to_dict(pool=False)
                        healthmonitor_dict['pool_id'] = pool_id
                        healthmonitors.append(healthmonitor_dict)

        return pools, healthmonitors

    @log_helpers.log_method_call
    def _get_members(self, context, pools, subnet_map, network_map):
        pool_members = []
        if pools:
            members = self.plugin.db.get_pool_members(
                context,
                filters={'pool_id': [p['id'] for p in pools]}
            )

            for member in members:
                # Get extended member attributes, network, and subnet.
                member_dict, subnet, network = (
                    self._get_extended_member(context, member)
                )

                subnet_map[subnet['id']] = subnet
                network_map[network['id']] = network
                pool_members.append(member_dict)

        return pool_members

    @log_helpers.log_method_call
    def _pool_to_dict(self, pool):
        """Convert Pool data model to dict.

        Provides an alternative to_api_dict() in order to get additional
        object IDs without exploding object references.
        """

        pool_dict = pool.to_dict(healthmonitor=False,
                                 listener=False,
                                 listeners=False,
                                 loadbalancer=False,
                                 l7_policies=False,
                                 members=False,
                                 session_persistence=False)

        pool_dict['members'] = [{'id': member.id} for member in pool.members]
        pool_dict['l7_policies'] = [{'id': l7_policy.id}
                                    for l7_policy in pool.l7_policies]
        if pool.session_persistence:
            pool_dict['session_persistence'] = (
                pool.session_persistence.to_api_dict())

        return pool_dict

    def _l7policy_to_dict(self, l7policy):
        """Convert l7Policy to dict.

        Adds provisioning_status to dict from to_api_dict()
        """
        l7policy_dict = l7policy.to_api_dict()
        l7policy_dict['provisioning_status'] = l7policy.provisioning_status
        return l7policy_dict

    def _l7rule_to_dict(self, l7rule):
        """Convert l7Policy rule to dict.

        Adds provisioning_status to dict from to_api_dict()
        """
        l7rule_dict = l7rule.to_api_dict()
        l7rule_dict['provisioning_status'] = l7rule.provisioning_status
        return l7rule_dict
