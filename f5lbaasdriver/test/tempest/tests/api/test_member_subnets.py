# coding=utf-8
u"""F5 Networks® LBaaSv2 L7 policy tempest tests."""
# Copyright 2017 F5 Networks Inc.
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
import ipaddress

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5.bigip import ManagementRoot
from f5lbaasdriver.test.tempest.tests.api import base

config = config.CONF


class MemberSubnetTestJSON(base.BaseAdminTestCase):
    """Test creating two members on different subnets, same network.

    Verifies that a self IP is created for configurations that have
    multiple pool members on separate subnets. To do so, the test
    creates a network and three subnest: one for lb, one for first
    member, and one for the second memeber. A loadbalancer with listener,
    pool, and members is created, and the test verifies that a self IP
    is created for each member (that the self IP address and member address
    overlap).

    Note: this test will only execute correctly on undercloud deployments.
    """

    @classmethod
    def resource_setup(cls):
        """Setup client fixtures for test suite."""
        super(MemberSubnetTestJSON, cls).resource_setup()
        network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(network_name)

        # subnet for load balancer
        cls.subnet1 = cls.create_subnet(cls.network)

        # subnet for first member
        cls.subnet2 = cls.create_subnet(cls.network)

        # subnet for second member
        cls.subnet3 = cls.create_subnet(cls.network)

        cls.create_lb_kwargs = {'tenant_id': cls.subnet1['tenant_id'],
                                'vip_subnet_id': cls.subnet1['id']}
        cls.load_balancer = \
            cls._create_active_load_balancer(**cls.create_lb_kwargs)
        cls.load_balancer_id = cls.load_balancer['id']

        # create listener
        listener_kwargs = {'loadbalancer_id': cls.load_balancer_id,
                           'protocol': 'HTTP',
                           'protocol_port': 80}
        cls.listener = cls._create_listener(**listener_kwargs)

        # get an RPC client for calling into driver
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @test.attr(type='smoke')
    def test_member_selfips(self):

        self.bigip = ManagementRoot(config.f5_lbaasv2_driver.icontrol_hostname,
                                    config.f5_lbaasv2_driver.icontrol_username,
                                    config.f5_lbaasv2_driver.icontrol_password)

        # create pool
        pool_kwargs = {'listener_id': self.listener['id'],
                       'protocol': 'HTTP',
                       'lb_algorithm': 'ROUND_ROBIN'}
        pool = self._create_pool(**pool_kwargs)
        self.addCleanup(self._delete_pool, pool.get('id'))

        # create first member on subnet2
        allocation_pool = self.subnet2['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet2['id']}
        member1 = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member1.get('id'))
        assert self._has_selfip_for_member(member1)

        # create second member on subnet3
        allocation_pool = self.subnet3['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet3['id']}
        member2 = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member2.get('id'))
        assert self._has_selfip_for_member(member2)

        # delete first and check second self IP
        self._delete_member(pool.get('id'), member1.get('id'))
        assert self._has_selfip_for_member(member2)

        # re-create first member and check both self IPs
        allocation_pool = self.subnet2['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet2['id']}
        member1 = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member1.get('id'))
        assert self._has_selfip_for_member(member1)
        assert self._has_selfip_for_member(member2)

    def _has_selfip_for_member(self, member):
        # Verify that a self IP exists that overlaps with member IP
        address = self._split_address(member['address'])
        member_address = ipaddress.ip_address(address)

        selfips = self.bigip.tm.net.selfips.get_collection()
        for selfip in selfips:
            selfip_address, selfip_rd = self._split_address(selfip.address)
            network = ipaddress.ip_network(selfip_address, False)
            if member_address in network:
                return True

        return False

    def _split_address(self, address):
        '''Extract IP address which might have a route domain.

        Input address may or may not have route domains, mask.
        Some examples of different possible forms:
           10.1.1.1
           10.1.1.1%3
           10.1.1.1/24
           10.1.1.1%3/24
        '''

        if '%' in address:
            # has route domain
            parts = address.split('%')
            ip_address = parts[0]
            rd = parts[1]
            if '/' in rd:
                # retain CIDR form without route domain
                parts = rd.split('/')
                ip_address += '/' + parts[1]
        else:
            # no route domain
            ip_address = address

        return unicode(ip_address)
