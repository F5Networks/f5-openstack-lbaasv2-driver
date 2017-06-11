# coding=utf-8
u"""Service Module for F5® LBaaSv2."""
# Copyright 2017 F5 Networks Inc.
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

from neutron.api.v2 import attributes
from neutron.common import constants as neutron_const
from neutron.extensions import portbindings

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class F5NetworksNeutronClient(object):

    def __init__(self, plugin):
        self.plugin = plugin

    @log_helpers.log_method_call
    def create_port_on_subnet(self, context, subnet_id=None,
                              mac_address=None, ip_address=None,
                              name="", fixed_address_count=1, host=""):
        """Create port on subnet."""
        port = None

        if not mac_address:
            mac_address = attributes.ATTR_NOT_SPECIFIED

        if subnet_id:
            try:
                subnet = self.plugin.db._core_plugin.get_subnet(
                    context,
                    subnet_id
                )
                fixed_ip = {'subnet_id': subnet['id']}
                if ip_address:
                    fixed_ip['ip_address'] = ip_address
                fixed_ips = [fixed_ip]

                port_data = {
                    'tenant_id': subnet['tenant_id'],
                    'name': name,
                    'network_id': subnet['network_id'],
                    'mac_address': mac_address,
                    'admin_state_up': True,
                    'device_id': "",
                    'device_owner': 'network:f5lbaasv2',
                    'status': neutron_const.PORT_STATUS_ACTIVE,
                    'fixed_ips': fixed_ips
                }

                if ('binding:capabilities' in
                        portbindings.EXTENDED_ATTRIBUTES_2_0['ports']):
                    port_data['binding:capabilities'] = {
                        'port_filter': False}
                port = self.plugin.db._core_plugin.create_port(
                    context, {'port': port_data})

                # Because ML2 marks ports DOWN by default on creation
                update_data = {
                    'status': neutron_const.PORT_STATUS_ACTIVE
                }
                self.plugin.db._core_plugin.update_port(
                    context, port['id'], {'port': update_data})

            except Exception as e:
                LOG.error("Exception: create_port_on_subnet: %s",
                          e.message)
            return port

    @log_helpers.log_method_call
    def delete_port(self, context, port_id=None, mac_address=None):
        """Delete port."""
        if port_id:
            self.plugin.db._core_plugin.delete_port(context, port_id)
        elif mac_address:
            filters = {'mac_address': [mac_address]}
            ports = self.plugin.db._core_plugin.get_ports(
                context,
                filters=filters
            )
            for port in ports:
                self.plugin.db._core_plugin.delete_port(
                    context,
                    port['id']
                )
