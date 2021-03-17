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

from f5lbaasdriver.v2.bigip import constants_v2 as constants

from neutron.common import rpc as neutron_rpc
from neutron.db import agents_db
from neutron.db.models import agent as agents_model
from neutron.plugins.common import constants as plugin_constants

from neutron_lbaas.db.loadbalancer import models
from neutron_lbaas.services.loadbalancer import constants as nlb_constant
from neutron_lbaas.services.loadbalancer.data_models import LoadBalancer

from neutron_lib.api.definitions import portbindings
from neutron_lib import constants as neutron_const
from neutron_lib import exceptions as q_exc
from oslo_log import helpers as log_helpers
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class LBaaSv2PluginCallbacksRPC(object):
    """Agent to plugin RPC API."""

    def __init__(self, driver=None):
        """LBaaSv2PluginCallbacksRPC constructor."""
        self.driver = driver
        self.cluster_wide_agents = {}

    def create_rpc_listener(self):
        topic = constants.TOPIC_PROCESS_ON_HOST_V2
        if self.driver.env:
            topic = topic + "_" + self.driver.env

        self.conn = neutron_rpc.create_connection()

        self.conn.create_consumer(
            topic,
            [self, agents_db.AgentExtRpcCallback(self.driver.plugin.db)],
            fanout=False)
        self.conn.consume_in_threads()

    # change the admin_state_up of the an agent
    @log_helpers.log_method_call
    def set_agent_admin_state(self, context, admin_state_up, host=None):
        """Set the admin_up_state of an agent."""
        if not host:
            LOG.error('tried to set agent admin_state_up without host')
            return False
        with context.session.begin(subtransactions=True):
            query = context.session.query(agents_model.Agent)
            query = query.filter(
                agents_model.Agent.agent_type ==
                nlb_constant.AGENT_TYPE_LOADBALANCERV2,
                agents_model.Agent.host == host)
            try:
                agent = query.one()
                if not agent.admin_state_up == admin_state_up:
                    agent.admin_state_up = admin_state_up
                    context.session.add(agent)
            except Exception as exc:
                LOG.error('query for agent produced: %s' % str(exc))
                return False
        return True

    # change the admin_state_up of the an agent
    @log_helpers.log_method_call
    def scrub_dead_agents(self, context, env, group, host=None):
        """Remove all non-alive or admin down agents."""
        LOG.debug('scrubing dead agent bindings')
        with context.session.begin(subtransactions=True):
            try:
                self.driver.scheduler.scrub_dead_agents(
                    context, self.driver.plugin, env, group=None)
            except Exception as exc:
                LOG.error('scub dead agents exception: %s' % str(exc))
                return False
        return True

    @log_helpers.log_method_call
    def get_service_by_loadbalancer_id(
            self, context, loadbalancer_id=None, host=None):
        """Get the complete service definition by loadbalancer_id."""
        service = {}
        with context.session.begin(subtransactions=True):
            LOG.debug('Building service definition entry for %s'
                      % loadbalancer_id)

            try:
                LOG.info('before get_loadbalancer')
                lb = self.driver.plugin.db.get_loadbalancer(
                    context,
                    id=loadbalancer_id
                )
                lb = LoadBalancer(**lb) if type(lb) == dict else lb
                LOG.info('after get_loadbalancer')
                agent = self.driver.plugin.db.get_agent_hosting_loadbalancer(
                    context,
                    loadbalancer_id
                )
                # the preceeding get call returns a nested dict, unwind
                # one level if necessary
                agent = (agent['agent'] if 'agent' in agent else agent)
                LOG.info('before build')
                service = self.driver.service_builder.build(
                    context, lb, agent)
                LOG.info('after build')
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
            self.driver.scheduler.scrub_dead_agents(
                context, plugin, env, group)
            agents = self.driver.scheduler.get_agents_in_env(
                context, plugin, env, group, active=None)
            for agent in agents:
                LOG.info('before list_loadbalancers_on_lbaas_agent')
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                LOG.info('after list_loadbalancers_on_lbaas_agent')
                for lb in agent_lbs:
                    lbobj = LoadBalancer(**lb) if type(lb) == dict else lb
                    loadbalancers.append(
                        {
                            'agent_host': agent['host'],
                            'lb_id': lbobj.id,
                            'tenant_id': lbobj.tenant_id
                        }
                    )
        if host:
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def get_active_loadbalancers(self, context, env, group=None, host=None):
        """Get active loadbalancers for this group in this env."""
        loadbalancers = []
        plugin = self.driver.plugin
        with context.session.begin(subtransactions=True):
            self.driver.scheduler.scrub_dead_agents(
                context, plugin, env, group)
            agents = self.driver.scheduler.get_agents_in_env(
                context, plugin, env, group, active=None)
            for agent in agents:
                LOG.info('before list_loadbalancers_on_lbaas_agent')
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                LOG.info('after list_loadbalancers_on_lbaas_agent')
                for lb in agent_lbs:
                    lbobj = LoadBalancer(**lb) if type(lb) == dict else lb
                    if lbobj.provisioning_status == plugin_constants.ACTIVE:
                        loadbalancers.append(
                            {
                                'agent_host': agent['host'],
                                'lb_id': lbobj.id,
                                'tenant_id': lbobj.tenant_id
                            }
                        )
        if host:
            LOG.debug('get active lb with host %s' % host)
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def get_pending_loadbalancers(self, context, env, group=None, host=None):
        """Get pending loadbalancers for this group in this env."""
        loadbalancers = []
        plugin = self.driver.plugin
        with context.session.begin(subtransactions=True):
            self.driver.scheduler.scrub_dead_agents(
                context, plugin, env, group)
            agents = self.driver.scheduler.get_agents_in_env(
                context, plugin, env, group, active=None)
            for agent in agents:
                LOG.info('before list_loadbalancers_on_lbaas_agent')
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                LOG.info('after list_loadbalancers_on_lbaas_agent')
                for lb in agent_lbs:
                    lbobj = LoadBalancer(**lb) if type(lb) == dict else lb
                    if (lbobj.provisioning_status !=
                        plugin_constants.ACTIVE and
                            lbobj.provisioning_status !=
                            plugin_constants.ERROR):
                        loadbalancers.append(
                            {
                                'agent_host': agent['host'],
                                'lb_id': lbobj.id,
                                'tenant_id': lbobj.tenant_id
                            }
                        )
        if host:
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def get_errored_loadbalancers(self, context, env, group=None, host=None):
        """Get pending loadbalancers for this group in this env."""
        loadbalancers = []
        plugin = self.driver.plugin
        with context.session.begin(subtransactions=True):
            self.driver.scheduler.scrub_dead_agents(
                context, plugin, env, group)
            agents = self.driver.scheduler.get_agents_in_env(
                context, plugin, env, group, active=None)
            for agent in agents:
                LOG.info('before list_loadbalancers_on_lbaas_agent')
                agent_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context,
                    agent.id
                )
                LOG.info('after list_loadbalancers_on_lbaas_agent')
                for lb in agent_lbs:
                    lbobj = LoadBalancer(**lb) if type(lb) == dict else lb
                    if (lbobj.provisioning_status == plugin_constants.ERROR):
                        loadbalancers.append(
                            {
                                'agent_host': agent['host'],
                                'lb_id': lbobj.id,
                                'tenant_id': lbobj.tenant_id
                            }
                        )
        if host:
            return [lb for lb in loadbalancers if lb['agent_host'] == host]
        else:
            return loadbalancers

    @log_helpers.log_method_call
    def update_loadbalancer_stats(
            self, context, loadbalancer_id=None, stats=None):
        """Update service stats."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_loadbalancer_stats')
                self.driver.plugin.db.update_loadbalancer_stats(
                    context, loadbalancer_id, stats
                )
                LOG.info('after update_loadbalancer_stats')
            except Exception as e:
                LOG.error('Exception: update_loadbalancer_stats: %s',
                          e.message)

    @log_helpers.log_method_call
    def update_loadbalancer_status(self, context, loadbalancer_id=None,
                                   status=None, operating_status=None,
                                   lb_name=None):
        """Agent confirmation hook to update loadbalancer status."""
        pref_list = ['419-name-', 'for-one-time-name-', 'name-only-temp-']

        with context.session.begin(subtransactions=True):
            try:
                if lb_name and lb_name.startswith(tuple(pref_list)):
                    LOG.warn('there comes lb name, u SHOULD modify it later')

                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.LoadBalancer,
                    loadbalancer_id,
                    status,
                    operating_status
                )
                LOG.info('after update_status')
            except Exception as e:
                LOG.error('Exception: update_loadbalancer_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def loadbalancer_destroyed(self, context, loadbalancer_id=None):
        """Agent confirmation hook that loadbalancer has been destroyed."""
        self.driver.plugin.db.delete_loadbalancer(context, loadbalancer_id)

    @log_helpers.log_method_call
    def update_listener_status(self, context, listener_id=None,
                               provisioning_status=plugin_constants.ERROR,
                               operating_status=None):
        """Agent confirmation hook to update listener status."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.Listener,
                    listener_id,
                    provisioning_status,
                    operating_status
                )
                LOG.info('after update_status')
            except Exception as e:
                LOG.error('Exception: update_listener_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def listener_destroyed(self, context, listener_id=None):
        """Agent confirmation hook that listener has been destroyed."""
        self.driver.plugin.db.delete_listener(context, listener_id)

    @log_helpers.log_method_call
    def update_pool_status(self, context, pool_id=None,
                           provisioning_status=plugin_constants.ERROR,
                           operating_status=None):
        """Agent confirmations hook to update pool status."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.PoolV2,
                    pool_id,
                    provisioning_status,
                    operating_status
                )
                LOG.info('after update_status')
            except Exception as e:
                LOG.error('Exception: update_pool_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def pool_destroyed(self, context, pool_id=None):
        """Agent confirmation hook that pool has been destroyed."""
        self.driver.plugin.db.delete_pool(context, pool_id)

    @log_helpers.log_method_call
    def update_member_status_in_batch(self, context, members=[]):
        """Agent confirmations hook to update member status in batch."""
        LOG.info('before update status in batch %d', len(members))
        for member in members:
            try:
                LOG.info('member is %s %s.', member['id'], member['state'])
                self.driver.plugin.db.update_status(
                    context,
                    models.MemberV2,
                    member['id'],
                    None,
                    member['state']
                )
            # we only deal with Not found exception and skip all the others
            except q_exc.NotFound:
                LOG.warning('member %s not found.', member['id'])
        LOG.info('end of update status in batch.')

        return

    @log_helpers.log_method_call
    def update_member_status(self, context, member_id=None,
                             provisioning_status=None,
                             operating_status=None):
        """Agent confirmations hook to update member status."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.MemberV2,
                    member_id,
                    provisioning_status,
                    operating_status
                )
                LOG.info('after update_status')
            except Exception as e:
                LOG.error('Exception: update_member_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def member_destroyed(self, context, member_id=None):
        """Agent confirmation hook that member has been destroyed."""
        self.driver.plugin.db.delete_member(context, member_id)

    @log_helpers.log_method_call
    def update_health_monitor_status(
            self, context, health_monitor_id,
            provisioning_status=plugin_constants.ERROR, operating_status=None):
        """Agent confirmation hook to update health monitor status."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.HealthMonitorV2,
                    health_monitor_id,
                    provisioning_status,
                    operating_status
                )
                LOG.info('after update_status')
            except Exception as e:
                LOG.error('Exception: update_health_monitor_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def healthmonitor_destroyed(self, context, healthmonitor_id=None):
        """Agent confirmation hook that health_monitor has been destroyed."""
        self.driver.plugin.db.delete_healthmonitor(context, healthmonitor_id)

    @log_helpers.log_method_call
    def update_l7policy_status(self, context, l7policy_id=None,
                               provisioning_status=plugin_constants.ERROR,
                               operating_status=None):
        """Agent confirmation hook to update l7 policy status."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.L7Policy,
                    l7policy_id,
                    provisioning_status,
                    operating_status
                )
                LOG.info('after update_status')
            except Exception as e:
                LOG.error('Exception: update_l7policy_status: %s',
                          e.message)

    @log_helpers.log_method_call
    def l7policy_destroyed(self, context, l7policy_id=None):
        LOG.debug("l7policy_destroyed")
        """Agent confirmation hook that l7 policy has been destroyed."""
        self.driver.plugin.db.delete_l7policy(context, l7policy_id)

    @log_helpers.log_method_call
    def update_l7rule_status(self, context, l7rule_id=None, l7policy_id=None,
                             provisioning_status=plugin_constants.ERROR,
                             operating_status=None):
        """Agent confirmation hook to update l7 policy status."""
        with context.session.begin(subtransactions=True):
            try:
                LOG.info('before update_status')
                self.driver.plugin.db.update_status(
                    context,
                    models.L7Rule,
                    l7rule_id,
                    provisioning_status,
                    operating_status
                )
                LOG.info('after update_status')
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
                              fixed_address_count=1, host=None,
                              device_id=None,
                              vnic_type=portbindings.VNIC_NORMAL,
                              binding_profile={}):
        """Create port on subnet."""
        port = None

        if subnet_id:
            try:
                subnet = self.driver.plugin.db._core_plugin.get_subnet(
                    context,
                    subnet_id
                )
                if not mac_address:
                    mac_address = neutron_const.ATTR_NOT_SPECIFIED
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
                    'device_owner': 'network:f5lbaasv2',
                    'status': neutron_const.PORT_STATUS_ACTIVE,
                    'fixed_ips': fixed_ips
                }

                if device_id:
                    port_data['device_id'] = device_id
                port_data[portbindings.HOST_ID] = host
                port_data[portbindings.VNIC_TYPE] = vnic_type
                port_data[portbindings.PROFILE] = binding_profile

                # TODO(xie): several lines different between 9.6
                # and master. check if it's needed in master later
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

    @log_helpers.log_method_call
    def create_port_on_network(self, context, network_id=None,
                               mac_address=None, name=None, host=None,
                               device_id=None,
                               vnic_type=portbindings.VNIC_NORMAL,
                               binding_profile={}):
        """Create a port on a network."""
        ports = []
        if network_id and name:
            filters = {'name': [name]}
            ports = self.driver.plugin.db._core_plugin.get_ports(
                context,
                filters=filters
            )

        if not ports:
            network = self.driver.plugin.db._core_plugin.get_network(
                context,
                network_id
            )

            if not mac_address:
                mac_address = neutron_const.ATTR_NOT_SPECIFIED
            if not host:
                host = ''
            if not name:
                name = ''

            port_data = {
                'tenant_id': network['tenant_id'],
                'name': name,
                'network_id': network_id,
                'mac_address': mac_address,
                'admin_state_up': True,
                'device_owner': 'network:f5lbaasv2',
                'status': neutron_const.PORT_STATUS_ACTIVE,
                'fixed_ips': neutron_const.ATTR_NOT_SPECIFIED
            }
            if device_id:
                port_data['device_id'] = device_id
            port_data[portbindings.HOST_ID] = host
            port_data[portbindings.VNIC_TYPE] = vnic_type
            port_data[portbindings.PROFILE] = binding_profile

            LOG.info('before create_port')
            port = self.driver.plugin.db._core_plugin.create_port(
                context, {'port': port_data})
            LOG.info('after create_port')

            # Because ML2 marks ports DOWN by default on creation
            update_data = {
                'status': neutron_const.PORT_STATUS_ACTIVE
            }
            LOG.info('before update_port')
            self.driver.plugin.db._core_plugin.update_port(
                context, port['id'], {'port': update_data})
            LOG.info('after update_port')
            return port

        else:
            return ports[0]

    # return a single active agent to implement cluster wide changes
    # which can not efficiently mapped back to a particulare agent
    @log_helpers.log_method_call
    def get_clusterwide_agent(self, context, env, group, host=None):
        """Get an agent to perform clusterwide tasks."""
        LOG.debug('getting agent to perform clusterwide tasks')
        with context.session.begin(subtransactions=True):
            if (env, group) in self.cluster_wide_agents:
                known_agent = self.cluster_wide_agents[(env, group)]
                if self.driver.plugin.db.is_eligible_agent(active=True,
                                                           agent=known_agent):
                    return known_agent
                else:
                    del(self.cluster_wide_agents[(env, group)])
            try:
                agents = \
                    self.driver.scheduler.get_agents_in_env(context,
                                                            self.driver.plugin,
                                                            env, group, True)
                if agents:
                    self.cluster_wide_agents[(env, group)] = agents[0]
                    return agents[0]
                else:
                    LOG.error('no active agents available for clusterwide ',
                              ' tasks %s group number %s' % (env, group))
                    return {}
            except Exception as exc:
                LOG.error('clusterwide agent exception: %s' % str(exc))
                return {}
        return {}

    # validate a list of loadbalancer id - assure they are not deleted
    @log_helpers.log_method_call
    def validate_loadbalancers_state(self, context, loadbalancers, host=None):
        lb_status = {}
        for lbid in loadbalancers:
            with context.session.begin(subtransactions=True):
                try:
                    LOG.info('before get_loadbalancer')
                    lb_db = self.driver.plugin.db.get_loadbalancer(context,
                                                                   lbid)
                    LOG.info('after get_loadbalancer')
                    lb_db = LoadBalancer(**lb_db) \
                        if type(lb_db) == dict else lb_db
                    lb_status[lbid] = lb_db.provisioning_status

                except q_exc.NotFound:
                    lb_status[lbid] = 'Unknown'

                except Exception as e:
                    LOG.error('Exception: get_loadbalancer: %s',
                              e.message)
                    if 'could not be found' in e.message:
                        lb_status[lbid] = 'Unknown'
                    else:
                        lb_status[lbid] = ''

        return lb_status

    # validate a list of pools id - assure they are not deleted
    @log_helpers.log_method_call
    def validate_pools_state(self, context, pools, host=None):
        pool_status = {}
        for poolid in pools:
            with context.session.begin(subtransactions=True):
                try:
                    LOG.info('before get_pool')
                    pool_db = self.driver.plugin.db.get_pool(context, poolid)
                    LOG.info('after get_pool')
                    pool_status[poolid] = pool_db.provisioning_status

                except q_exc.NotFound:
                    pool_status[poolid] = 'Unknown'

                except Exception as e:
                    LOG.error('Exception: get_pool: %s',
                              e.message)
                    if 'could not be found' in e.message:
                        pool_status[poolid] = 'Unknown'
                    else:
                        pool_status[poolid] = ''
        return pool_status

    @log_helpers.log_method_call
    def get_pools_members(self, context, pools, host=None):
        pools_members = dict()
        for poolid in pools:
            LOG.info('before get_pool_members')
            members = self.driver.plugin.db.get_pool_members(
                context,
                filters={'pool_id': [poolid]}
            )
            LOG.info('after get_pool_members')
            pools_members[poolid] = [member.to_dict(pool=False)
                                     for member in members]
        return pools_members

    # validate a list of listeners id - assure they are not deleted
    @log_helpers.log_method_call
    def validate_listeners_state(self, context, listeners, host=None):
        listener_status = {}
        for listener_id in listeners:
            with context.session.begin(subtransactions=True):
                try:
                    LOG.info('before get_listener')
                    listener_db = \
                        self.driver.plugin.db.get_listener(context,
                                                           listener_id)
                    LOG.info('after get_listener')
                    listener_status[listener_id] = \
                        listener_db.provisioning_status

                except q_exc.NotFound:
                    listener_status[listener_id] = 'Unknown'

                except Exception as e:
                    LOG.error('Exception: get_listener: %s',
                              e.message)
                    if 'could not be found' in e.message:
                        listener_status[listener_id] = 'Unknown'
                    else:
                        listener_status[listener_id] = ''
        return listener_status

    # validate a list of l7policys id - assure they are not deleted
    @log_helpers.log_method_call
    def validate_l7policys_state_by_listener(self, context, listeners):
        """Performs a validation against l7policies with a list of listeners

        This method will attempt to check the Neutron DB for a list of
        l7policies that reference the given list of listener_id's.

        This will return a dict of:
            {listener_id_0: bool,
             ...
            }
        The bool will indicate that true: there are l7policies here, false:
        there are none on this listener.
        """
        has_l7policy = {}
        try:
            LOG.info('before get_l7policies')
            # NOTE: neutron_lbaas has a deprecated code filter for queries
            # that appears to silence filter queries for 'listener_id'
            l7policy_db = self.driver.plugin.db.get_l7policies(context)
            LOG.info('after get_l7policies')
        except Exception as error:
            LOG.exception("Exception: plugin.db.get_l7policies({}): "
                          "({})".format(listeners, error))
            return {}
        LOG.debug("({}) = get_l7policies({})".format(l7policy_db, context))
        for listener_id in listeners:
            # Given filter limitations, double-loop iterator results
            result = False
            if l7policy_db:
                if isinstance(l7policy_db, list):
                    for l7policy in l7policy_db:
                        if l7policy.listener_id == listener_id:
                            result = True
                            break
                else:
                    if l7policy_db.listener_id == listener_id:
                        result = True
            else:
                result = False
            has_l7policy[listener_id] = result
        LOG.debug("has_l7policy: ({})".format(has_l7policy))
        return has_l7policy
