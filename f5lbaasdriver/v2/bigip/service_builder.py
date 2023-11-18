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
import json

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

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

        self.plugin = self.driver.plugin
        self.disconnected_service = DisconnectedService()
        self.q_client = q_client.F5NetworksNeutronClient(self.plugin)

    def build(self, context, loadbalancer, agent, **kwargs):
        """Get full service definition from loadbalancer ID."""

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
            vip_subnet = self._get_subnet(
                context,
                subnet_id
            )
            subnet_map[subnet_id] = vip_subnet

            # Get the network associated with the Loadbalancer.
            network_map = {}
            vip_port = service['loadbalancer']['vip_port']
            network_id = vip_port['network_id']
            service['loadbalancer']['network_id'] = network_id
            network = self._get_network(
                context,
                network_id
            )
            # Override the segmentation ID and network type for this network
            # if we are running in disconnected service mode
            agent_config = self.deserialize_agent_configurations(
                agent['configurations'])
            segment_data = self.disconnected_service.get_network_segment(
                context, agent_config, network
            )
            LOG.debug('segment_data obtained from get_network_segment is:')
            LOG.debug(segment_data)

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
                LOG.warning("Creating a loadbalancer %s for tenant %s on a"
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

            # Assign default values
            service['listeners'] = []
            service['pools'] = []
            service['healthmonitors'] = []
            service['members'] = []
            service['l7policies'] = []
            service['l7policy_rules'] = []

            # Get listeners and pools.
            append_listeners = kwargs.get(
                "append_listeners", self._append_listeners)
            append_pools_monitors = kwargs.get(
                "append_pools_monitors", self._append_pools_monitors)
            append_members = kwargs.get("append_members", self._append_members)
            append_l7policies_rules = kwargs.get(
                "append_l7policies_rules", self._append_l7policies_rules)

            append_listeners(context, loadbalancer, service)
            append_pools_monitors(context, loadbalancer, service)
            append_members(
                context, loadbalancer, service, network_map, subnet_map)
            if not service.get('subnets'):
                service['subnets'] = subnet_map
            if not service.get('networks'):
                service['networks'] = network_map
            append_l7policies_rules(context, loadbalancer, service)

        return service

    @log_helpers.log_method_call
    def _append_listeners(self, context, loadbalancer, service):
        service['listeners'] = self._get_listeners(context, loadbalancer)

    @log_helpers.log_method_call
    def _append_pools_monitors(self, context, loadbalancer, service):
        service['pools'], service['healthmonitors'] = \
            self._get_pools_and_healthmonitors(context, loadbalancer)

    # TODO(x): why do we set network_map and subnet_map for service again?
    # _get_members never use these two arguments
    @log_helpers.log_method_call
    def _append_members(self, context, loadbalancer, service,
                        network_map, subnet_map):
        service['members'] = self._get_members(
            context, loadbalancer, service['pools'], subnet_map, network_map)
        service['subnets'] = subnet_map
        service['networks'] = network_map

    @log_helpers.log_method_call
    def _append_l7policies_rules(self, context, loadbalancer, service):
        service['l7policies'] = self._get_l7policies(
            context, loadbalancer, service['listeners'])
        service['l7policy_rules'] = self._get_l7policy_rules(
            context, loadbalancer, service['l7policies'])

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
    def _get_subnet(self, context, subnet_id):
        """Retrieve subnet from Neutron."""
        subnet = self.plugin.db._core_plugin.get_subnet(
            context,
            subnet_id
        )
        return subnet

    @log_helpers.log_method_call
    def _get_network(self, context, network_id):
        """Retrieve network from Neutron."""
        network = self.plugin.db._core_plugin.get_network(
            context,
            network_id
        )
        LOG.debug("Network %s obtained from core plugin is: %s",
                  network_id, network)

        if 'provider:network_type' not in network:
            network['provider:network_type'] = 'undefined'
        if 'provider:segmentation_id' not in network:
            network['provider:segmentation_id'] = 0

        return network

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
    def _get_l7policies(self, context, loadbalancer, listeners):
        """Get l7 policies filtered by listeners."""
        l7policies = []
        if listeners:
            listener_ids = [listener['id'] for listener in listeners]

            def get_db_policies():
                if cfg.CONF.f5_driver_perf_mode in (1, 3):
                    db_policies = []
                    for l1 in loadbalancer.listeners:
                        for l2 in listeners:
                            if l1.id == l2['id']:
                                db_policies.extend(l1.l7_policies)
                    return db_policies
                else:
                    return self.plugin.db.get_l7policies(
                        context, filters={'listener_id': listener_ids})

            policies = get_db_policies()
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
    def _get_l7policy_rules(self, context, loadbalancer, l7policies):
        """Get l7 policy rules filtered by l7 policies."""
        l7policy_rules = []
        if l7policies:
            policy_ids = [p['id'] for p in l7policies]
            for pol_id in policy_ids:

                def get_db_rules():
                    if cfg.CONF.f5_driver_perf_mode in (1, 3):
                        for listener in loadbalancer.listeners:
                            for policy in listener.l7_policies:
                                if policy.id == pol_id:
                                    return policy.rules
                    else:
                        return self.plugin.db.get_l7policy_rules(
                            context, pol_id)

                rules = get_db_rules()
                l7policy_rules.extend(
                    self._l7rule_to_dict(rule, pol_id) for rule in rules)

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

        def get_db_listeners():
            if cfg.CONF.f5_driver_perf_mode in (1, 3):
                return loadbalancer.listeners
            else:
                return self.plugin.db.get_listeners(
                    context,
                    filters={'loadbalancer_id': [loadbalancer.id]}
                )

        db_listeners = get_db_listeners()

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

        def get_db_pools():
            if cfg.CONF.f5_driver_perf_mode in (1, 3):
                return loadbalancer.pools
            else:
                return self.plugin.db.get_pools(
                    context,
                    filters={'loadbalancer_id': [loadbalancer.id]}
                )

        if loadbalancer and loadbalancer.id:
            db_pools = get_db_pools()

            for pool in db_pools:
                pools.append(self._pool_to_dict(pool))
                pool_id = pool.id
                healthmonitor_id = pool.healthmonitor_id

                def get_db_healthmonitor():
                    if cfg.CONF.f5_driver_perf_mode in (1, 3):
                        return pool.healthmonitor
                    else:
                        return self.plugin.db.get_healthmonitor(
                            context,
                            healthmonitor_id)

                if healthmonitor_id:
                    healthmonitor = get_db_healthmonitor()
                    if healthmonitor:
                        healthmonitor_dict = healthmonitor.to_dict(pool=False)
                        healthmonitor_dict['pool_id'] = pool_id
                        healthmonitors.append(healthmonitor_dict)

        return pools, healthmonitors

    # TODO(x) subnet_map and network_map are never used in ng.
    @log_helpers.log_method_call
    def _get_members(self, context, loadbalancer, pools,
                     subnet_map, network_map):
        pool_members = []

        def get_db_members():
            # NOTE(x): normally, there is only one pending updated pool in
            # 'pools' list.

            if cfg.CONF.f5_driver_perf_mode in (1, 3):
                members = []
                for p1 in loadbalancer.pools:
                    for p2 in pools:
                        if p1.id == p2['id']:
                            LOG.info('pool id here:')
                            LOG.info(p1.id)
                            members.extend([m for m in p1.members])
                LOG.info('members right here:')
                LOG.info(members)
                return members
            else:
                return self.plugin.db.get_pool_members(
                    context,
                    filters={'pool_id': [p['id'] for p in pools]}
                )

        if pools:
            # TODO(niklaus): might have to modify if SY don't.
            # in that case seems we have to fetch them
            # using db.get_pool_members, which is not desired.
            members = get_db_members()
            for member in members:
                pool_members.append(member.to_dict(pool=False))

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
        LOG.info('the members of pool_dict here is:')
        LOG.info(pool_dict['members'])
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

        # Listener attribte of policy fetched from loadbalancer object may be
        # None. However, l7policy.to_api_dict() assumes it is not None. So we
        # append its listener id.
        if cfg.CONF.f5_driver_perf_mode in (1, 3) \
                and l7policy_dict['listener_id'] \
                and len(l7policy_dict['listeners']) == 0:
            l7policy_dict['listeners'].append(
                {'id': l7policy_dict['listener_id']})

        return l7policy_dict

    def _l7rule_to_dict(self, l7rule, l7policy_id):
        """Convert l7Policy rule to dict.

        Adds provisioning_status to dict from to_api_dict()
        """
        l7rule_dict = l7rule.to_api_dict()
        l7rule_dict['provisioning_status'] = l7rule.provisioning_status

        # Policy attribte of rule fetched from loadbalancer object may be
        # None. However, l7rule.to_api_dict() assumes it is not None. So we
        # append its policy id.
        if cfg.CONF.f5_driver_perf_mode in (1, 3) and l7policy_id \
                and len(l7rule_dict['policies']) == 0:
            l7rule_dict['policies'].append({'id': l7policy_id})

        return l7rule_dict
