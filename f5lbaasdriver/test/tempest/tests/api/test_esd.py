# coding=utf-8
u"""F5 Networks® LBaaSv2 L7 policy tempest tests."""
# Copyright 2016 F5 Networks Inc.
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


class ESDTestJSON(base.BaseTestCase):
    """Enhanced service definition tempest tests.

    """

    @classmethod
    def resource_setup(cls):
        super(ESDTestJSON, cls).resource_setup()
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
        cls.create_pool_kwargs = {'listener_id': cls.listener_id,
                                  'protocol': "HTTP",
                                  'lb_algorithm': "ROUND_ROBIN"}
        cls.pool = (
            cls._create_pool(**cls.create_pool_kwargs))
        cls.pool_id = cls.pool['id']

        # Create basic args for policy creation
        cls.create_l7policy_kwargs = {'listener_id': cls.listener_id,
                                      'admin_state_up': "true"}

        # Get a client to emulate the agent's behavior.
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

        cls.partition = 'Project_' + cls.subnet['tenant_id']

    @classmethod
    def resource_cleanup(cls):
        super(ESDTestJSON, cls).resource_cleanup()

    @test.attr(type='smoke')
    def test_create_esd(self):
        """Test the creation of a L7 reject policy."""
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REJECT"
        create_l7policy_kwargs['name'] = "esd_demo_1"

        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self.addCleanup(self._delete_l7policy, new_policy['id'])

        self.check_esd()

    def check_esd(self):
        vs_name = 'Project_' + self.listener_id
        assert self.bigip_client.virtual_server_has_profile(
            vs_name, 'clientssl', self.partition)
        assert self.bigip_client.virtual_server_has_profile(
            vs_name, 'serverssl', self.partition)
        assert self.bigip_client.virtual_server_has_profile(
            vs_name, 'tcp-mobile-optimized', self.partition)
        assert self.bigip_client.virtual_server_has_profile(
            vs_name, 'tcp-lan-optimized', self.partition)
        assert self.bigip_client.virtual_server_has_value(
            vs_name, 'fallbackPersistence',
            '/Common/source_addr', self.partition)
