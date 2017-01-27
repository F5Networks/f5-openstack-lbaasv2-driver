# Copyright 2017 F5 Networks Inc.
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import time

from neutron_lbaas.services.loadbalancer import constants as lb_const
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest.lib import decorators
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base

CONF = config.CONF


class MemberStatusTestJSON(base.BaseTestCase):
    """Test that pool member's operating status is set correctly."""

    @classmethod
    def resource_setup(cls):
        """Setup client fixtures for test suite."""
        super(MemberStatusTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('lbaas', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(network_name)
        cls.subnet = cls.create_subnet(cls.network)

        cls.create_lb_kwargs = {'tenant_id': cls.subnet['tenant_id'],
                                'vip_subnet_id': cls.subnet['id']}
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

    @classmethod
    def resource_cleanup(cls):
        super(MemberStatusTestJSON, cls).resource_cleanup()

    @test.attr(type='smoke')
    def test_no_monitor(self):
        # create pool
        pool_kwargs = {'listener_id': self.listener['id'],
                       'protocol': 'HTTP',
                       'lb_algorithm': 'ROUND_ROBIN'}
        pool = self._create_pool(**pool_kwargs)
        self.addCleanup(self._delete_pool, pool.get('id'))

        # create member
        allocation_pool = self.subnet['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet['id']}
        member = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member.get('id'))

        # Because pool does not have monitor, expect NO_MONITOR status
        expected_status = lb_const.NO_MONITOR
        assert self._wait_for_member_status(member,
                                            expected_status) == expected_status

    @test.attr(type='smoke')
    def test_online(self):
        # create pool
        pool_kwargs = {'listener_id': self.listener['id'],
                       'protocol': 'HTTP',
                       'lb_algorithm': 'ROUND_ROBIN'}
        pool = self._create_pool(**pool_kwargs)
        self.addCleanup(self._delete_pool, pool.get('id'))

        #  add ping monitor
        ping_monitor_kwargs = {'pool_id': pool['id'],
                               'type': 'PING',
                               'delay': 1,
                               'timeout': 1,
                               'max_retries': 5}
        self._create_health_monitor(**ping_monitor_kwargs)

        # create member
        allocation_pool = self.subnet['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet['id']}
        member = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member.get('id'))

        # Because monitor is PING, expect monitor to verify member up
        expected_status = "ONLINE"
        assert self._wait_for_member_status(member,
                                            expected_status) == expected_status

    @test.attr(type='smoke')
    def test_offline(self):
        # create pool
        pool_kwargs = {'listener_id': self.listener['id'],
                       'protocol': 'HTTP',
                       'lb_algorithm': 'ROUND_ROBIN'}
        pool = self._create_pool(**pool_kwargs)
        self.addCleanup(self._delete_pool, pool.get('id'))

        #  add HTTP monitor
        ping_monitor_kwargs = {'pool_id': pool['id'],
                               'type': 'HTTP',
                               'delay': 1,
                               'timeout': 1,
                               'max_retries': 5}
        self._create_health_monitor(**ping_monitor_kwargs)

        # create member
        allocation_pool = self.subnet['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet['id']}
        member = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member.get('id'))

        # Because monitor is HTTP, never expect monitor to verify member up
        expected_status = lb_const.OFFLINE
        assert self._wait_for_member_status(member,
                                            expected_status) == expected_status

        # verify degraded state for loadbalancer
        status_tree = self.load_balancers_client.\
            get_load_balancer_status_tree(self.load_balancer_id)
        lb_status = status_tree.get('loadbalancer').get('operating_status')
        assert lb_status == lb_const.DEGRADED

    @decorators.skip_because(bug="497")
    def test_disabled(self):
        """Test setting admin state down.

        Skipped because setting admin state is not currently supported. Remove
        decorator when issue has been fixed.
        """
        # create pool
        pool_kwargs = {'listener_id': self.listener['id'],
                       'protocol': 'HTTP',
                       'lb_algorithm': 'ROUND_ROBIN'}
        pool = self._create_pool(**pool_kwargs)
        self.addCleanup(self._delete_pool, pool.get('id'))

        #  add ping monitor
        ping_monitor_kwargs = {'pool_id': pool['id'],
                               'type': 'PING',
                               'delay': 1,
                               'timeout': 1,
                               'max_retries': 5}
        self._create_health_monitor(**ping_monitor_kwargs)

        # create member
        allocation_pool = self.subnet['allocation_pools'][0]
        member_kwargs = {'pool_id': pool['id'],
                         'address': allocation_pool['start'],
                         'protocol_port': 8080,
                         'subnet_id': self.subnet['id']}
        member = self._create_member(**member_kwargs)
        self.addCleanup(self._delete_member, pool.get('id'), member.get('id'))

        # verify member up
        expected_status = lb_const.ONLINE
        assert self._wait_for_member_status(member,
                                            expected_status) == expected_status

        # Set admin down -- status should change to disabled
        member_opts = {"admin_state_up": False}
        member = self._update_member(pool.get('id'),
                                     member.get('id'),
                                     **member_opts)
        expected_status = lb_const.OFFLINE
        assert self._wait_for_member_status(member,
                                            expected_status) == expected_status

    @test.attr(type='smoke')
    def _wait_for_member_status(self, member, expected_status):
        """Query member operating status until it changes to expected status.

        :param member: member to query status.
        :param expected_status: Status to wait for.
        :return: Final status, either from changing to expected_status, or
        result after timing out.
        """
        status = ""
        count = 0
        while status != expected_status and count < 60:
            count += 1
            time.sleep(2)
            svc = self.client.call(self.context,
                                   'get_service_by_loadbalancer_id',
                                   loadbalancer_id=self.load_balancer_id)
            m = self._get_member_from_service(svc, member['id'])
            status = m["operating_status"]

        return status

    @staticmethod
    def _get_member_from_service(svc, member_id):
        for m in svc['members']:
            if m['id'] == member_id:
                return m
        return None
