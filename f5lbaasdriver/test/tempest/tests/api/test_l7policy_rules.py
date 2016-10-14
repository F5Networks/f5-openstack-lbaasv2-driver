# coding=utf-8
u"""F5 Networks® LBaaSv2 L7 policy rules tempest tests."""
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

from neutron.plugins.common import constants as plugin_const
from neutron_lbaas.services.loadbalancer import constants as lb_const
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base


CONF = config.CONF


class L7PolicyRulesTestJSON(base.BaseTestCase):
    """L7 Policy tempest tests.

    Tests the following operations in the Neutron-LBaaS API using the
    REST client with default credentials:
    """

    @classmethod
    def resource_setup(cls):
        super(L7PolicyRulesTestJSON, cls).resource_setup()
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
        create_l7policy_rule_kwargs = {'listener_id': cls.listener_id,
                                       'action': 'REJECT',
                                       'admin_state_up': 'true'}
        new_policy = cls._create_l7policy(
            **create_l7policy_rule_kwargs)
        cls.policy_id = new_policy['id']

        # Get a client to emulate the agent's behavior.
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @classmethod
    def resource_cleanup(cls):
        super(L7PolicyRulesTestJSON, cls).resource_cleanup()

    def check_rules(self):
        # Check service object has rules we expect
        res = self.client.call(self.context, "get_service_by_loadbalancer_id",
                               loadbalancer_id=self.load_balancer_id)
        assert 'l7policy_rules' in res.keys()
        print(res['l7policy_rules'])
        assert len(res['l7policy_rules']) == 1
        rule = res['l7policy_rules'][0]
        assert rule['policy_id'] == self.policy_id

    def set_agent_calls(self, rule_id):
        # These actions should be performed by the agent.
        self.client.call(self.context, "update_l7rule_status",
                         l7rule_id=rule_id,
                         l7policy_id=self.policy_id,
                         provisioning_status=plugin_const.ACTIVE)
        self.client.call(self.context, "update_l7policy_status",
                         l7policy_id=self.policy_id,
                         provisioning_status=plugin_const.ACTIVE)
        self.client.call(self.context, "update_loadbalancer_status",
                         loadbalancer_id=self.load_balancer_id,
                         status=plugin_const.ACTIVE,
                         operating_status=lb_const.ONLINE)

    @test.attr(type='smoke')
    def test_create_l7_starts_with_rule(self):
        """Test the creationg of a L7 reject policy."""
        l7rule = self._create_l7rule(
            self.policy_id,
            type='PATH', compare_type='STARTS_WITH', value='/api')
        self.set_agent_calls(l7rule['id'])
        self.addCleanup(self._delete_l7rule, self.policy_id, l7rule['id'])
        self.check_rules()
