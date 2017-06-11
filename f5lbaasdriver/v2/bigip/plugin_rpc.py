# coding=utf-8
u"""RPC Callbacks for F5® LBaaSv2 Plugins."""
# Copyright 2016 F5 Networks Inc.
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
import uuid

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron.api.v2 import attributes
from neutron.common import constants as neutron_const
from neutron.common import rpc as neutron_rpc
from neutron.db import agents_db
from neutron.extensions import portbindings
from neutron.plugins.common import constants as plugin_constants
from neutron_lbaas.db.loadbalancer import models

from f5lbaasdriver.v2.bigip import constants_v2 as constants

LOG = logging.getLogger(__name__)


class LBaaSv2PluginCallbacksRPC(object):
    """Agent to plugin RPC API."""

    def __init__(self, driver=None):
        """LBaaSv2PluginCallbacksRPC constructor."""
        self.driver = driver

    def create_rpc_listener(self):
        topic = constants.TOPIC_PROCESS_ON_HOST_V2
        if self.driver.env:
            topic = topic + "_" + self.driver.env

        self.conn = neutron_rpc.create_connection()
        self.conn.create_consumer(
            topic,
            [self,
             agents_db.AgentExtRpcCallback(self.driver.plugin.db)],
            fanout=False)
        self.conn.consume_in_threads()

    # get a list of loadbalancer ids which are active on this agent host
    @log_helpers.log_method_call
    def get_active_loadbalancers_for_agent(self, context, host=None):
        """Get a list of loadbalancers active on this host."""
        with context.session.begin(subtransactions=True):
            if not host:
                return []
            agents = self.driver.plugin.db.get_lbaas_agents(
                context,
                filters={'host': [host]}
            )
            if not agents:
                return []
            elif len(agents) > 1:
                LOG.warning('Multiple lbaas agents found on host %s' % host)
            lbs = self.driver.plugin.db.list_loadbalancers_on_lbaas_agent(
                context,
                agents[0].id
            )
            lb_ids = [loadbalancer.id
                      for loadbalancer in lbs]
            active_lb_ids = set()
            lbs = self.driver.plugin.db.get_loadbalancers(
                context,
                filters={
                    'status': [plugin_constants.ACTIVE],
                    'id': lb_ids,
                    'admin_state_up': [True]
                })
            for lb in lbs:
                active_lb_ids.add(lb.id)
            return active_lb_ids

    @log_helpers.log_method_call
    def get_service_by_loadbalancer_id(
            self,
            context,
            loadbalancer_id=None,
            host=None):
        """Get the complete service definition by loadbalancer_id."""
        service = {}
        with context.session.begin(subtransactions=True):
            LOG.debug('Building service definition entry for %s'
                      % loadbalancer_id)

            try:
                lb = self.driver.plugin.db.get_loadbalancer(
                    context,
                    id=loadbalancer_id
                )
                agent = self.driver.plugin.db.get_agent_hosting_loadbalancer(
                    context,
                    loadbalancer_id
                )
                # the preceeding get call returns a nested dict, unwind
                # one level if necessary
                agent = (agent['agent'] if 'agent' in agent else agent)
                service = self.driver.service_builder.build(context,
                                                            lb,
                                                            agent)
            except Exception as e:
                LOG.error("Exception: get_service_by_loadbalancer_id: %s",
                          e.message)

            return service

    @log_helpers.log_method_call
    def get_all_loadbalancers(self, context, env, group=None, host=None):
        """Get all loadbalancers for this group in this env."""
        loadbalancers = []
        plugin = self.driver.plugin

        with context.session.begin(subtransactions=True):
            agents = self.driver.scheduler.get_agents_in_env(
                context,
                self.driver.plugin,
                env,
                group)

            for agent in agents:
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                for lb in agent_lbs:
                    loadbalancers.append(
                        {
                            'agent_host': agent['host'],
                            'lb_id': lb.id,
                            'tenant_id': lb.tenant_id
                        }
                    )
        if host:
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def get_active_loadbalancers(self, context, env, group=None, host=None):
        """Get all loadbalancers for this group in this env."""
        loadbalancers = []
        plugin = self.driver.plugin

        with context.session.begin(subtransactions=True):
            agents = self.driver.scheduler.get_agents_in_env(
                context,
                self.driver.plugin,
                env,
                group=group,
                active=True
            )

            for agent in agents:
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                for lb in agent_lbs:
                    if lb.provisioning_status == plugin_constants.ACTIVE:

                        loadbalancers.append(
                            {
                                'agent_host': agent['host'],
                                'lb_id': lb.id,
                                'tenant_id': lb.tenant_id
                            }
                        )

        if host:
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def get_pending_loadbalancers(self, context, env, group=None, host=None):
        """Get all loadbalancers for this group in this env."""
        loadbalancers = []
        plugin = self.driver.plugin

        with context.session.begin(subtransactions=True):
            agents = self.driver.scheduler.get_agents_in_env(
                context,
                self.driver.plugin,
                env,
                group)

            for agent in agents:
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                for lb in agent_lbs:
                    if (lb.provisioning_status != plugin_constants.ACTIVE and
                            lb.provisioning_status != plugin_constants.ERROR):

                        loadbalancers.append(
                            {
                                'agent_host': agent['host'],
                                'lb_id': lb.id,
                                'tenant_id': lb.tenant_id
                            }
                        )

        if host:
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def update_loadbalancer_stats(self,
                                  context,
                                  loadbalancer_id=None,
                                  stats=None):
        """Update service stats."""
        with context.session.begin(subtransactions=True):
            try:
                self.driver.plugin.db.update_loadbalancer_stats(
                    context,
                    loadbalancer_id,
                    stats
                )
            except Exception as e:
                LOG.error('Exception: update_loadbalancer_stats: %s',
                          e.message)

    @log_helpers.log_method_call
    def update_loadbalancer_status(self, context,
                                   loadbalancer_id=None,
                                   status=None,
                                   operating_status=None):
        """Agent confirmation hook to update loadbalancer status."""
        with context.session.begin(subtransactions=True):
            try:
                lb_db = self.driver.plugin.db.get_loadbalancer(
                    context,
                    loadbalancer_id
                )
                if (lb_db.provisioning_status ==
                        plugin_constants.PENDING_DELETE):
                    status = plugin_constants.PENDING_DELETE

                self.driver.plugin.db.update_status(
                    context,
                    models.LoadBalancer,
                    loadbalancer_id,
                    status,
                    operating_status
                )
            except Exception as e:
                LOG.error('Exception: update_loadbalancer_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def loadbalancer_destroyed(self, context, loadbalancer_id=None):
        """Agent confirmation hook that loadbalancer has been destroyed."""
        self.driver.plugin.db.delete_loadbalancer(context, loadbalancer_id)

    @log_helpers.log_method_call
    def update_listener_status(
            self,
            context,
            listener_id=None,
            provisioning_status=plugin_constants.ERROR,
            operating_status=None):
        """Agent confirmation hook to update listener status."""
        with context.session.begin(subtransactions=True):
            try:
                listener_db = self.driver.plugin.db.get_listener(
                    context,
                    listener_id
                )
                if (listener_db.provisioning_status ==
                        plugin_constants.PENDING_DELETE):
                    provisioning_status = plugin_constants.PENDING_DELETE
                self.driver.plugin.db.update_status(
                    context,
                    models.Listener,
                    listener_id,
                    provisioning_status,
                    operating_status
                )
            except Exception as e:
                LOG.error('Exception: update_listener_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def listener_destroyed(self, context, listener_id=None):
        """Agent confirmation hook that listener has been destroyed."""
        self.driver.plugin.db.delete_listener(context, listener_id)

    @log_helpers.log_method_call
    def update_pool_status(
            self,
            context,
            pool_id=None,
            provisioning_status=plugin_constants.ERROR,
            operating_status=None):
        """Agent confirmations hook to update pool status."""
        with context.session.begin(subtransactions=True):
            try:
                pool = self.driver.plugin.db.get_pool(
                    context,
                    pool_id
                )
                if (pool.provisioning_status !=
                        plugin_constants.PENDING_DELETE):
                    self.driver.plugin.db.update_status(
                        context,
                        models.PoolV2,
                        pool_id,
                        provisioning_status,
                        operating_status
                    )
            except Exception as e:
                LOG.error('Exception: update_pool_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def pool_destroyed(self, context, pool_id=None):
        """Agent confirmation hook that pool has been destroyed."""
        self.driver.plugin.db.delete_pool(context, pool_id)

    @log_helpers.log_method_call
    def update_member_status(
            self,
            context,
            member_id=None,
            provisioning_status=None,
            operating_status=None):
        """Agent confirmations hook to update member status."""
        with context.session.begin(subtransactions=True):
            try:
                member = self.driver.plugin.db.get_pool_member(
                    context,
                    member_id
                )
                if (member.provisioning_status !=
                        plugin_constants.PENDING_DELETE):
                    self.driver.plugin.db.update_status(
                        context,
                        models.MemberV2,
                        member_id,
                        provisioning_status,
                        operating_status
                    )
            except Exception as e:
                LOG.error('Exception: update_member_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def member_destroyed(self, context, member_id=None):
        """Agent confirmation hook that member has been destroyed."""
        self.driver.plugin.db.delete_member(context, member_id)

    @log_helpers.log_method_call
    def update_health_monitor_status(
            self,
            context,
            health_monitor_id,
            provisioning_status=plugin_constants.ERROR,
            operating_status=None):
        """Agent confirmation hook to update health monitor status."""
        with context.session.begin(subtransactions=True):
            try:
                health_monitor = self.driver.plugin.db.get_healthmonitor(
                    context,
                    health_monitor_id
                )
                if (health_monitor.provisioning_status !=
                        plugin_constants.PENDING_DELETE):
                    self.driver.plugin.db.update_status(
                        context,
                        models.HealthMonitorV2,
                        health_monitor_id,
                        provisioning_status,
                        operating_status
                    )
            except Exception as e:
                LOG.error('Exception: update_health_monitor_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def healthmonitor_destroyed(self, context, healthmonitor_id=None):
        """Agent confirmation hook that health_monitor has been destroyed."""
        self.driver.plugin.db.delete_healthmonitor(context, healthmonitor_id)

    @log_helpers.log_method_call
    def update_l7policy_status(
            self,
            context,
            l7policy_id=None,
            provisioning_status=plugin_constants.ERROR,
            operating_status=None):
        """Agent confirmation hook to update l7 policy status."""
        with context.session.begin(subtransactions=True):
            try:
                l7policy_db = self.driver.plugin.db.get_l7policy(
                    context,
                    l7policy_id
                )
                if (l7policy_db.provisioning_status ==
                        plugin_constants.PENDING_DELETE):
                    provisioning_status = plugin_constants.PENDING_DELETE
                self.driver.plugin.db.update_status(
                    context,
                    models.L7Policy,
                    l7policy_id,
                    provisioning_status,
                    operating_status
                )
            except Exception as e:
                LOG.error('Exception: update_l7policy_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def l7policy_destroyed(self, context, l7policy_id=None):
        LOG.debug("l7policy_destroyed")
        """Agent confirmation hook that l7 policy has been destroyed."""
        self.driver.plugin.db.delete_l7policy(context, l7policy_id)

    @log_helpers.log_method_call
    def update_l7rule_status(
            self,
            context,
            l7rule_id=None,
            l7policy_id=None,
            provisioning_status=plugin_constants.ERROR,
            operating_status=None):
        """Agent confirmation hook to update l7 policy status."""
        with context.session.begin(subtransactions=True):
            try:
                l7rule_db = self.driver.plugin.db.get_l7policy_rule(
                    context,
                    l7rule_id,
                    l7policy_id
                )
                if (l7rule_db.provisioning_status ==
                        plugin_constants.PENDING_DELETE):
                    provisioning_status = plugin_constants.PENDING_DELETE
                self.driver.plugin.db.update_status(
                    context,
                    models.L7Rule,
                    l7rule_id,
                    provisioning_status,
                    operating_status
                )
            except Exception as e:
                LOG.error('Exception: update_l7rule_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def l7rule_destroyed(self, context, l7rule_id):
        """Agent confirmation hook that l7 policy has been destroyed."""
        self.driver.plugin.db.delete_l7policy_rule(context, l7rule_id)

    # Neutron core plugin core object management

    @log_helpers.log_method_call
    def get_ports_for_mac_addresses(self, context, mac_addresses=None):
        """Get ports for mac addresses."""
        ports = []
        try:
            if not isinstance(mac_addresses, list):
                mac_addresses = [mac_addresses]
            filters = {'mac_address': mac_addresses}
            ports = self.driver.plugin.db._core_plugin.get_ports(
                context,
                filters=filters
            )
        except Exception as e:
            LOG.error("Exception: get_ports_for_mac_addresses: %s",
                      e.message)

        return ports

    @log_helpers.log_method_call
    def get_ports_on_network(self, context, network_id=None):
        """Get ports for network."""
        ports = []
        try:
            if not isinstance(network_id, list):
                network_ids = [network_id]
            filters = {'network_id': network_ids}
            ports = self.driver.plugin.db._core_plugin.get_ports(
                context,
                filters=filters
            )
        except Exception as e:
            LOG.error("Exception: get_ports_on_network: %s", e.message)

        return ports

    @log_helpers.log_method_call
    def create_port_on_subnet(self, context, subnet_id=None,
                              mac_address=None, name=None,
                              fixed_address_count=1, host=None):
        """Create port on subnet."""
        port = None
        if subnet_id:
            try:
                subnet = self.driver.plugin.db._core_plugin.get_subnet(
                    context,
                    subnet_id
                )
                if not mac_address:
                    mac_address = attributes.ATTR_NOT_SPECIFIED
                fixed_ip = {'subnet_id': subnet['id']}
                if fixed_address_count > 1:
                    fixed_ips = []
                    for _ in range(0, fixed_address_count):
                        fixed_ips.append(fixed_ip)
                else:
                    fixed_ips = [fixed_ip]

                if not host:
                    host = ''
                if not name:
                    name = ''

                port_data = {
                    'tenant_id': subnet['tenant_id'],
                    'name': name,
                    'network_id': subnet['network_id'],
                    'mac_address': mac_address,
                    'admin_state_up': True,
                    'device_id': str(uuid.uuid5(
                        uuid.NAMESPACE_DNS, str(host))),
                    'device_owner': 'network:f5lbaasv2',
                    'status': neutron_const.PORT_STATUS_ACTIVE,
                    'fixed_ips': fixed_ips
                }
                port_data[portbindings.HOST_ID] = host
                port_data[portbindings.VIF_TYPE] = constants.VIF_TYPE
                if ('binding:capabilities' in
                        portbindings.EXTENDED_ATTRIBUTES_2_0['ports']):
                    port_data['binding:capabilities'] = {
                        'port_filter': False}
                port = self.driver.plugin.db._core_plugin.create_port(
                    context, {'port': port_data})
                # Because ML2 marks ports DOWN by default on creation
                update_data = {
                    'status': neutron_const.PORT_STATUS_ACTIVE
                }
                self.driver.plugin.db._core_plugin.update_port(
                    context, port['id'], {'port': update_data})

            except Exception as e:
                LOG.error("Exception: create_port_on_subnet: %s",
                          e.message)

            return port

    @log_helpers.log_method_call
    def create_port_on_subnet_with_specific_ip(self, context, subnet_id=None,
                                               mac_address=None, name=None,
                                               ip_address=None, host=None):
        """Create port on subnet with specific ip address."""
        if subnet_id and ip_address:
            subnet = self.driver.plugin.db._core_plugin.get_subnet(
                context,
                subnet_id
            )
            if not mac_address:
                mac_address = attributes.ATTR_NOT_SPECIFIED
            fixed_ip = {
                'subnet_id': subnet['id'],
                'ip_address': ip_address
            }
            if not host:
                host = ''
            if not name:
                name = ''
            port_data = {
                'tenant_id': subnet['tenant_id'],
                'name': name,
                'network_id': subnet['network_id'],
                'mac_address': mac_address,
                'admin_state_up': True,
                'device_id': str(uuid.uuid5(uuid.NAMESPACE_DNS, str(host))),
                'device_owner': 'network:f5lbaasv2',
                'status': neutron_const.PORT_STATUS_ACTIVE,
                'fixed_ips': [fixed_ip]
            }
            port_data[portbindings.HOST_ID] = host
            port_data[portbindings.VIF_TYPE] = 'f5'
            if ('binding:capabilities' in
                    portbindings.EXTENDED_ATTRIBUTES_2_0['ports']):
                port_data['binding:capabilities'] = {'port_filter': False}
            port = self.driver.plugin.db._core_plugin.create_port(
                context, {'port': port_data})
            # Because ML2 marks ports DOWN by default on creation
            update_data = {
                'status': neutron_const.PORT_STATUS_ACTIVE
            }
            self.driver.plugin.db._core_plugin.update_port(
                context, port['id'], {'port': update_data})
            return port

    @log_helpers.log_method_call
    def get_port_by_name(self, context, port_name=None):
        """Get port by name."""
        if port_name:
            filters = {'name': [port_name]}
            return self.driver.plugin.db._core_plugin.get_ports(
                context,
                filters=filters
            )

    @log_helpers.log_method_call
    def delete_port(self, context, port_id=None, mac_address=None):
        """Delete port."""
        if port_id:
            self.driver.plugin.db._core_plugin.delete_port(context, port_id)
        elif mac_address:
            filters = {'mac_address': [mac_address]}
            ports = self.driver.plugin.db._core_plugin.get_ports(
                context,
                filters=filters
            )
            for port in ports:
                self.driver.plugin.db._core_plugin.delete_port(
                    context,
                    port['id']
                )

    @log_helpers.log_method_call
    def delete_port_by_name(self, context, port_name=None):
        """Delete port by name."""
        if port_name:
            filters = {'name': [port_name]}
            try:
                ports = self.driver.plugin.db._core_plugin.get_ports(
                    context,
                    filters=filters
                )
                for port in ports:
                    self.driver.plugin.db._core_plugin.delete_port(
                        context,
                        port['id']
                    )
            except Exception as e:
                LOG.error("failed to delete port: %s", e.message)

    @log_helpers.log_method_call
    def add_allowed_address(self, context, port_id=None, ip_address=None):
        """Add allowed addresss."""
        if port_id and ip_address:
            try:
                port = self.driver.plugin.db._core_plugin.get_port(
                    context=context, id=port_id)
                found_pair = False
                address_pairs = []
                if 'allowed_address_pairs' in port:
                    for aap in port['allowed_address_pairs']:
                        if (aap['ip_address'] == ip_address and
                                aap['mac_address'] == port['mac_address']):
                            found_pair = True
                            break
                        address_pairs.append(aap)

                    if not found_pair:
                        address_pairs.append(
                            {'ip_address': ip_address,
                             'mac_address': port['mac_address']}
                        )
                port = {'port': {'allowed_address_pairs': address_pairs}}
                self.driver.plugin.db._core_plugin.update_port(
                    context,
                    port_id,
                    port
                )
            except Exception as exc:
                LOG.error('could not add allowed address pair: %s'
                          % exc.message)

    @log_helpers.log_method_call
    def remove_allowed_address(self, context, port_id=None, ip_address=None):
        """Remove allowed addresss."""
        if port_id and ip_address:
            try:
                port = self.driver.plugin.db._core_plugin.get_port(
                    context=context, id=port_id)
                address_pairs = []
                if 'allowed_address_pairs' in port:
                    for aap in port['allowed_address_pairs']:
                        if (aap['ip_address'] == ip_address and
                                aap['mac_address'] == port['mac_address']):
                            continue
                        address_pairs.append(aap)
                port = {'port': {'allowed_address_pairs': address_pairs}}
                self.driver.plugin.db._core_plugin.update_port(
                    context,
                    port_id,
                    port
                )
            except Exception as exc:
                LOG.error('could not remove allowed address pair: %s'
                          % exc.message)
