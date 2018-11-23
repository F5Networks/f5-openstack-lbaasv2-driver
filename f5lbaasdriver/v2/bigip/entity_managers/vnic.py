# coding=utf-8
u"""F5 Networks® LBaaSv2 Driver Implementation."""
# Copyright (c) 2016-2018, F5 Networks, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import sys

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron.plugins.common import constants as plugin_constants
from neutron_lib import constants as q_const

from neutron_lbaas.db.loadbalancer import models
from neutron_lbaas.extensions import lbaas_agentschedulerv2

from f5lbaasdriver.v2.bigip import agent_rpc
from f5lbaasdriver.v2.bigip import driver_v2
from f5lbaasdriver.v2.bigip import exceptions as f5_exc
from f5lbaasdriver.v2.bigip import neutron_client
from f5lbaasdriver.v2.bigip import plugin_rpc

LOG = logging.getLogger(__name__)


class DriverSpec(driver_v2.DriverSpec):
    """DriverSpec for driver"""

    def __init__(self, driver):
        super(DriverSpec, self).__init__(driver)
        self.port_binding_vnic_type = "normal"

    def func_example_to_do_some_job(self):
        pass


class LoadBalancerManager(driver_v2.LoadBalancerManager):
    """LoadBalancerManager class handles Neutron LBaaS CRUD."""
    pass


class ListenerManager(driver_v2.ListenerManager):
    """ListenerManager class handles Neutron LBaaS listener CRUD."""

    def __init__(self, driver):
        # example of __init__
        super(ListenerManager, self).__init__(driver)
        LOG.info("Do customized initializing.")


class PoolManager(driver_v2.PoolManager):
    """PoolManager class handles Neutron LBaaS pool CRUD."""
    pass


class MemberManager(driver_v2.MemberManager):
    """MemberManager class handles Neutron LBaaS pool member CRUD."""

    def create(self, context, member):
        """Create a member."""

        self.loadbalancer = member.pool.loadbalancer
        driver = self.driver
        subnet = driver.plugin.db._core_plugin.get_subnet(context, member.subnet_id)
        agent_host, service = self._setup_crud(context, member)
        driver.plugin.db._core_plugin.create_port(context, {
            'port': {
                'tenant_id': subnet['tenant_id'],
                'network_id': subnet['network_id'],
                'mac_address': attributes.ATTR_NOT_SPECIFIED,
                'fixed_ips': attributes.ATTR_NOT_SPECIFIED,
                'device_id': member.id,
                'device_owner': 'network:f5lbaasv2',
                'admin_state_up': member.admin_state_up,
                'name': 'fake_pool_port_' + member.id,
                portbindings.HOST_ID: agent_host}})
        self.api_dict = member.to_dict(pool=False)
        self._call_rpc(context, member, 'create_member')
        filters = {'device_id': [member.id]}
        port_id = None
        port = driver.plugin.db._core_plugin.get_ports(context, filters)
        if port:
            port_id = port[0]['id']
            LOG.debug('BBBBBBBBBBBBB:%s' % port_id)
        if port_id:
            driver.plugin.db._core_plugin.delete_port(context, port_id)
            LOG.debug('XXXXXX delete port: %s' % port_id)


class HealthMonitorManager(driver_v2.HealthMonitorManager):
    pass


class L7PolicyManager(driver_v2.L7PolicyManager):
    pass


class L7RuleManager(driver_v2.L7RuleManager):
    pass
