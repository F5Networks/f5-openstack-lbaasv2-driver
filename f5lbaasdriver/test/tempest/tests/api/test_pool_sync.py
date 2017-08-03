# coding=utf-8
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

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base

CONF = config.CONF


class PoolSyncTestJSON(base.F5BaseTestCase):
    """Test re-sync pools after BIG-IP restart.

    To simulate a restart, the test directly deletes a pool on a BIG-IP, as
    if a BIG-IP was restarted without saving a configuration. The test then
    updates a listener and tests that pool was re-created.
    """

    @classmethod
    def resource_setup(cls):
        super(PoolSyncTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('lbaasv2', 'network'):
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

        # Create listener for tests
        cls.create_listener_kwargs = {'loadbalancer_id': cls.load_balancer_id,
                                      'protocol': "HTTP",
                                      'protocol_port': "80"}
        cls.listener = (
            cls._create_listener(**cls.create_listener_kwargs))
        cls.listener_id = cls.listener['id']

        # Create pool for tests
        cls.create_pool_kwargs = {'loadbalancer_id': cls.load_balancer_id,
                                  'protocol': "HTTP",
                                  'lb_algorithm': "ROUND_ROBIN"}
        cls.partition = 'Project_' + cls.load_balancer.get('tenant_id')

        # Get a client to emulate the agent's behavior.
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @classmethod
    def resource_cleanup(cls):
        super(PoolSyncTestJSON, cls).resource_cleanup()

    def _pool_exists(self, pool_id, partition):
        name = 'Project_' + pool_id
        return self.bigip_client.pool_exists(name, partition)

    def _remove_pool(self, pool_id, partition):
        name = 'Project_' + pool_id
        return self.bigip_client.delete_pool(name, partition)

    def _members_exists(self, pool_id, partition):
        '''Expects only one member to exist in pool'''
        pool_name = 'Project_' + pool_id
        members = self.bigip_client.get_members(pool_name, partition)
        if len(list(members)) > 0:
            return True
        return False

    def _remove_members(self, pool_id, partition):
        pool_name = 'Project_' + pool_id
        self.bigip_client.delete_members(pool_name, partition)

    @test.attr(type='smoke')
    def test_pool_active_sync(self):
        self.pool = (
            self._create_pool(**self.create_pool_kwargs))
        self.pool_id = self.pool['id']
        self.addCleanup(self._delete_pool, self.pool_id)

        # verify pool exists
        assert self._pool_exists(self.pool_id, self.partition)

        # delete pool directly on BIG-IP
        self._remove_pool(self.pool['id'], self.partition)

        # update listener to force pool sync
        update_kwargs = {'description': 'resync ACTIVE pool'}
        self._update_listener(self.listener['id'], **update_kwargs)

        # verify pool exists
        assert self._pool_exists(self.pool_id, self.partition)

    @test.attr(type='smoke')
    def test_pool_member_active_sync(self):
        self.pool = (
            self._create_pool(**self.create_pool_kwargs))
        self.pool_id = self.pool['id']
        self.addCleanup(self._delete_pool, self.pool_id)

        allocation_pool = self.subnet['allocation_pools'][0]
        member_kwargs = {
            'pool_id': self.pool_id,
            'address': allocation_pool['start'],
            'protocol_port': 8080,
            'subnet_id': self.subnet['id']}
        self._create_member(**member_kwargs)

        # delete member directly on BIG-IP
        self._remove_members(self.pool_id, self.partition)
        # delete pool directly on BIG-IP
        self._remove_pool(self.pool_id, self.partition)

        # update listener to force pool sync
        update_kwargs = {'description': 'resync ACTIVE pool and member'}
        self._update_listener(self.listener['id'], **update_kwargs)

        # verify pool and member exists
        assert self._members_exists(self.pool_id, self.partition)
        assert self._pool_exists(self.pool_id, self.partition)
