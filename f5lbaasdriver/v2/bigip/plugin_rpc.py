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
from neutron_lbaas.extensions import loadbalancerv2

from f5lbaasdriver.v2.bigip import constants_v2 as constants

LOG = logging.getLogger(__name__)


class LBaaSv2PluginCallbacksRPC(object):
    """Agent to plugin RPC API."""

    def __init__(self, driver=None):
        """LBaaSv2PluginCallbacksRPC constructor."""
        self.driver = driver
        self._create_rpc_listener()

    def _create_rpc_listener(self):
        topic = constants.TOPIC_PROCESS_ON_HOST_V2
        if self.driver.env:
            topic = topic + "_" + self.driver.env

        self.conn = neutron_rpc.create_connection(new=True)
        self.conn.create_consumer(
            topic,
            [self,
             agents_db.AgentExtRpcCallback(self.driver.plugin.db)],
            fanout=False)
        self.conn.consume_in_threads()

    # get a list of service ids which are active on this agent host
    @log_helpers.log_method_call
    def get_active_services_for_agent(self, context, host=None):
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

    # get a list of services which have a pending state of some object
    # for this agent host
    @log_helpers.log_method_call
    def get_pending_services_for_agent(self, context, host=None):
        """Get a list of loadbalancers that are in the pending state."""
        pass

    # LBaaSv2 object status update methods

    @log_helpers.log_method_call
    def update_service_status(self, context, service, host=None):
        """Agent confirmation hook to update service status."""
        try:
            pass
        except Exception:
            # except lbext.VipNotFound:
            pass

    @log_helpers.log_method_call
    def update_service_stats(self, context, service_id=None,
                             stats=None, host=None):
        """Update service stats."""
        pass

    @log_helpers.log_method_call
    def update_loadbalancer_status(self, context,
                                   loadbalancer_id=None,
                                   status=plugin_constants.ERROR,
                                   operating_status=None):
        """Agent confirmation hook to update loadbalancer status."""
        try:
            lb_db = self.driver.plugin.db.get_loadbalancer(
                context,
                loadbalancer_id
            )
            if lb_db.provisioning_status == plugin_constants.PENDING_DELETE:
                status = plugin_constants.PENDING_DELETE
            self.driver.plugin.db.update_status(
                context,
                models.LoadBalancer,
                loadbalancer_id,
                status,
                operating_status
            )
        except loadbalancerv2.EntityNotFound:
            LOG.debug('Entity Not Found')

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
        except Exception:
            LOG.debug('Entity Not Found')

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
        try:
            pool = self.driver.plugin.db.get_pool(
                context,
                pool_id
            )
            if (pool.provisioning_status !=
                    plugin_constants.PENDING_DELETE):
                self.driver.plugin.db.update_status(
                    context,
                    models.Pool,
                    pool_id,
                    provisioning_status,
                    operating_status
                )
        except Exception:
            LOG.debug('Entity Not Found')

    @log_helpers.log_method_call
    def pool_destroyed(self, context, pool_id=None):
        """Agent confirmation hook that pool has been destroyed."""
        self.driver.plugin.db.delete_pool(context, pool_id)

    @log_helpers.log_method_call
    def update_member_status(
            self,
            context,
            member_id=None,
            provisioning_status=plugin_constants.ERROR,
            operating_status=None):
        """Agent confirmations hook to update member status."""
        try:
            member = self.driver.plugin.db.get_member(
                context,
                member_id
            )
            if (member.provisioning_status !=
                    plugin_constants.PENDING_DELETE):
                self.driver.plugin.db.update_status(
                    context,
                    models.Member,
                    member_id,
                    provisioning_status,
                    operating_status
                )
        except Exception:
            LOG.debug('Entity Not Found')

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
        try:
            health_monitor = self.driver.plugin.db.get_healthmonitor(
                context,
                health_monitor_id
            )
            if (health_monitor.provisioning_status !=
                    plugin_constants.PENDING_DELETE):
                self.driver.plugin.db.update_status(
                    context,
                    models.HealthMonitor,
                    health_monitor_id,
                    provisioning_status,
                    operating_status
                )
        except Exception:
            LOG.debug('Entity Not Found')

    @log_helpers.log_method_call
    def healthmonitor_destroyed(self, context, healthmonitor_id=None):
        """Agent confirmation hook that health_monitor has been destroyed."""
        self.driver.plugin.db.delete_healthmonitor(context, healthmonitor_id)

    # Neutron core plugin core object management

    @log_helpers.log_method_call
    def create_network(self, context, tenant_id=None, name=None,
                       shared=False, admin_state_up=True, network_type=None,
                       physical_network=None, segmentation_id=None):
        """Create neutron network."""
        network_data = {
            'tenant_id': tenant_id,
            'name': name,
            'admin_state_up': admin_state_up,
            'shared': shared
        }
        if network_type:
            network_data['provider:network_type'] = network_type
        if physical_network:
            network_data['provider:physical_network'] = physical_network
        if segmentation_id:
            network_data['provider:segmentation_id'] = segmentation_id
        return self.driver.plugin.db._core_plugin.create_network(
            context, {'network': network_data})

    @log_helpers.log_method_call
    def delete_network(self, context, network_id):
        """Delete neutron network."""
        self.driver.plugin.db._core_plugin.delete_network(context, network_id)

    @log_helpers.log_method_call
    def create_subnet(self, context, tenant_id=None, network_id=None,
                      name=None, shared=False, cidr=None, ip_version=None,
                      enable_dhcp=False, gateway_ip=None,
                      allocation_pools=None, dns_nameservers=None,
                      host_routes=None):
        """Create neutron subnet."""
        subnet_data = {'tenant_id': tenant_id,
                       'network_id': network_id,
                       'name': name,
                       'shared': shared,
                       'enable_dhcp': enable_dhcp}
        subnet_data['cidr'] = cidr
        subnet_data['ip_version'] = ip_version
        subnet_data['allocation_pools'] = allocation_pools
        subnet_data['dns_nameservers'] = dns_nameservers
        subnet_data['gateway_ip'] = gateway_ip
        subnet_data['host_routes'] = host_routes

        return self.driver.plugin.db._core_plugin.create_subnet(
            context,
            {'subnet': subnet_data}
        )

    @log_helpers.log_method_call
    def delete_subnet(self, context, subnet_id):
        """Delete neutron subnet."""
        self.driver.plugin.db._core_plugin.delete_subnet(context, subnet_id)

    @log_helpers.log_method_call
    def get_ports_for_mac_addresses(self, context, mac_addresses=None):
        """Get ports for mac addresses."""
        if not isinstance(mac_addresses, list):
            mac_addresses = [mac_addresses]
        filters = {'mac_address': mac_addresses}
        return self.driver.plugin.db._core_plugin.get_ports(
            context,
            filters=filters
        )

    @log_helpers.log_method_call
    def get_ports_on_network(self, context, network_id=None):
        """Get ports for network."""
        if not isinstance(network_id, list):
            network_ids = [network_id]
        filters = {'network_id': network_ids}
        return self.driver.plugin.db._core_plugin.get_ports(
            context,
            filters=filters
        )

    @log_helpers.log_method_call
    def create_port_on_subnet(self, context, subnet_id=None,
                              mac_address=None, name=None,
                              fixed_address_count=1, host=None):
        """Create port on subnet."""
        if subnet_id:
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
                'device_id': str(uuid.uuid5(uuid.NAMESPACE_DNS, str(host))),
                'device_owner': 'network:f5lbaas',
                'status': neutron_const.PORT_STATUS_ACTIVE,
                'fixed_ips': fixed_ips
            }
            port_data[portbindings.HOST_ID] = host
            port_data[portbindings.VIF_TYPE] = constants.VIF_TYPE
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
                'device_owner': 'network:f5lbaas',
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
    def allocate_fixed_address_on_subnet(self, context, subnet_id=None,
                                         port_id=None, name=None,
                                         fixed_address_count=1, host=None):
        """Allocate a fixed ip address on subnet."""
        if subnet_id:
            subnet = self.driver.plugin.db._core_plugin.get_subnet(
                context,
                subnet_id
            )
            fixed_ips = []
            existing_fixed_ips = []
            if not port_id:
                port = self.create_port_on_subnet(
                    context,
                    subnet_id=subnet_id,
                    mac_address=None,
                    name=name,
                    fixed_address_count=fixed_address_count,
                    host=host
                )
            else:
                port = self.driver.plugin.db._core_plugin.get_port(
                    context,
                    port_id
                )
                existing_fixed_ips = port['fixed_ips']

                fixed_ip = {'subnet_id': subnet['id']}

                if fixed_address_count > 1:
                    fixed_ips = []
                    for _ in range(0, fixed_address_count):
                        fixed_ips.append(fixed_ip)
                else:
                    fixed_ips = [fixed_ip]

                port['fixed_ips'] = existing_fixed_ips + fixed_ips
                port = self.driver.plugin.db._core_plugin.update_port(
                    context,
                    port['id'], {'port': port}
                )

            new_fixed_ips = port['fixed_ips']
            port['new_fixed_ips'] = []
            for new_fixed_ip in new_fixed_ips:
                ip_address = new_fixed_ip['ip_address']
                is_new = True
                for existing_fixed_ip in existing_fixed_ips:
                    if ip_address == existing_fixed_ip['ip_address']:
                        is_new = False
                if is_new:
                    port['new_fixed_ips'].append(new_fixed_ip)
            return port

    @log_helpers.log_method_call
    def allocate_specific_fixed_address_on_subnet(self, context,
                                                  subnet_id=None,
                                                  port_id=None, name=None,
                                                  ip_address=None,
                                                  host=None):
        """Allocate specific fixed ip address on subnet."""
        if subnet_id and ip_address:
            subnet = self.driver.plugin.db._core_plugin.get_subnet(
                context,
                subnet_id
            )
            if not port_id:
                port = self.create_port_on_subnet_with_specific_ip(
                    context,
                    subnet_id=subnet_id,
                    mac_address=None,
                    name=name,
                    ip_address=ip_address,
                    host=host
                )
            else:
                port = self.driver.plugin.db._core_plugin.get_port(
                    context,
                    port_id
                )
                existing_fixed_ips = port['fixed_ips']
                fixed_ip = {'subnet_id': subnet['id'],
                            'ip_address': ip_address}
                port['fixed_ips'] = existing_fixed_ips + [fixed_ip]
                port = self.driver.plugin.db._core_plugin.update_port(
                    context,
                    {'port': port}
                )
            return port

    @log_helpers.log_method_call
    def deallocate_fixed_address_on_subnet(self, context, fixed_addresses=None,
                                           subnet_id=None, host=None,
                                           auto_delete_port=False):
        """Allocate fixed ip address on subnet."""
        if fixed_addresses:
            if not isinstance(fixed_addresses, list):
                fixed_addresses = [fixed_addresses]
            # strip all route domain decorations if they exist
            for i in range(len(fixed_addresses)):
                try:
                    decorator_index = str(fixed_addresses[i]).index('%')
                    fixed_addresses[i] = fixed_addresses[i][:decorator_index]
                except Exception:
                    pass
            subnet = self.driver.plugin.db._core_plugin.get_subnet(
                context,
                subnet_id
            )
            # get all ports for this host on the subnet
            filters = {
                'network_id': [subnet['network_id']],
                'tenant_id': [subnet['tenant_id']],
                'device_id': [str(uuid.uuid5(uuid.NAMESPACE_DNS, str(host)))]
            }
            ports = self.driver.plugin.db._core_plugin.get_ports(
                context,
                filters=filters)
            fixed_ips = {}
            ok_to_delete_port = {}
            for port in ports:
                ok_to_delete_port[port['id']] = False
                for fixed_ip in port['fixed_ips']:
                    fixed_ips[fixed_ip['ip_address']] = port['id']
            # only get rid of associated fixed_ips
            for fixed_ip in fixed_ips:
                if fixed_ip in fixed_addresses:
                    self.driver.plugin.db._core_plugin._delete_ip_allocation(
                        context,
                        subnet['network_id'],
                        subnet_id,
                        fixed_ip
                    )
                    ok_to_delete_port[fixed_ips[fixed_ip]] = True
                else:
                    ok_to_delete_port[fixed_ips[fixed_ip]] = False
            if auto_delete_port:
                for port in ok_to_delete_port:
                    if ok_to_delete_port[port]:
                        self.delete_port(context, port)

    @log_helpers.log_method_call
    def add_allowed_address(self, context, port_id=None, ip_address=None):
        """Add allowed addresss."""
        if port_id and ip_address:
            try:
                port = self.driver.plugin.db._core_plugin.get_port(
                    context=context, id=port_id)
                address_pairs = []
                if 'allowed_address_pairs' in port:
                    for aap in port['allowed_address_pairs']:
                        if (aap['ip_address'] == ip_address and
                                aap['mac_address'] == port['mac_address']):
                            return True
                        address_pairs.append(aap)
                address_pairs.append(
                    {
                        'ip_address': ip_address,
                        'mac_address': port['mac_address']
                    }
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
                LOG.error('could not add allowed address pair: %s'
                          % exc.message)
