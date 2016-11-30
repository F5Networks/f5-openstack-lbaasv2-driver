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

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.services.clients.bigip_client import \
    BigIpClient
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

        cls.partition = 'Project_' + cls.subnet['tenant_id']
        cls.vs_name = 'Project_' + cls.listener_id
        cls.bigip = BigIpClient()

    @classmethod
    def resource_cleanup(cls):
        super(L7PolicyRulesTestJSON, cls).resource_cleanup()

    def check_policy(self, policy='wrapper_policy'):
        assert self.bigip.policy_exists(policy, partition=self.partition)

    def check_rule(self, rule='', policy='wrapper_policy',
                   action=None, condition=None, value=None):
        # Validate BIG-IP has rule
        assert self.bigip.rule_exists(
            policy, rule, partition=self.partition)

        if action:
            assert self.bigip.rule_has_action(
                policy, rule, action, partition=self.partition)

        if condition:
            assert self.bigip.rule_has_condition(
                policy, rule, condition, value, partition=self.partition)

    def check_virtual_server(self):
        # Validate virtual server has policy
        vs_name = 'Project_' + self.listener_id
        assert self.bigip.virtual_server_exists(vs_name, self.partition)
        assert self.bigip.virtual_server_has_policy(
            vs_name, 'wrapper_policy', self.partition)

    @test.attr(type='smoke')
    def test_create_policy_no_rule(self):
        create_l7policy_rule_kwargs = {'listener_id': self.listener_id,
                                       'action': 'REJECT',
                                       'admin_state_up': 'true'}
        new_policy = self._create_l7policy(
            **create_l7policy_rule_kwargs)
        policy_id = new_policy['id']
        self.addCleanup(self._delete_l7policy, policy_id)

        assert not self.bigip.policy_exists(
            'wrapper_policy', partition=self.partition)

        assert not self.bigip.virtual_server_has_policy(
            self.vs_name, 'wrapper_policy', self.partition)

    @test.attr(type='smoke')
    def test_create_policy_one_rule(self):
        # Create basic args for policy creation
        create_l7policy_rule_kwargs = {'listener_id': self.listener_id,
                                       'action': 'REJECT',
                                       'admin_state_up': 'true'}
        policy = self._create_l7policy(
            **create_l7policy_rule_kwargs)
        policy_id = policy['id']
        self.addCleanup(self._delete_l7policy, policy_id)

        rule = self._create_l7rule(
            policy_id, type='PATH', compare_type='STARTS_WITH', value='/api')
        self.addCleanup(self._delete_l7rule, policy_id, rule['id'])

        self.check_policy()
        self.check_rule(
            'reject_1',
            action=create_l7policy_rule_kwargs['action'],
            condition='startsWith', value='/api')
        self.check_virtual_server()

    @test.attr(type='smoke')
    def test_create_two_policies(self):
        # Create basic args for policy creation
        create_l7policy1_rule_kwargs = {'listener_id': self.listener_id,
                                        'action': 'REJECT',
                                        'admin_state_up': 'true',
                                        'position': 1}

        create_l7policy2_rule_kwargs = {'listener_id': self.listener_id,
                                        'action': 'REDIRECT_TO_URL',
                                        'redirect_url': 'http://www.acm.org',
                                        'admin_state_up': 'true',
                                        'position': 2}
        policy1 = self._create_l7policy(
            **create_l7policy1_rule_kwargs)
        policy1_id = policy1['id']
        self.addCleanup(self._delete_l7policy, policy1_id)

        rule1 = self._create_l7rule(
            policy1_id, type='PATH', compare_type='STARTS_WITH', value='/api')
        self.addCleanup(self._delete_l7rule, policy1_id, rule1['id'])

        self.check_policy()
        self.check_rule(rule='reject_1', action='REJECT',
                        condition='startsWith', value='/api')
        self.check_virtual_server()

        policy2 = self._create_l7policy(
            **create_l7policy2_rule_kwargs)
        policy2_id = policy2['id']
        self.addCleanup(self._delete_l7policy, policy2_id)

        rule2 = self._create_l7rule(policy2_id,
                                    type='HOST_NAME',
                                    compare_type='ENDS_WITH',
                                    value='.org')
        self.addCleanup(self._delete_l7rule, policy2_id, rule2['id'])

        self.check_policy()
        self.check_rule('redirect_to_url_2', action='REDIRECT_TO_URL',
                        condition='endsWith', value='.org')
        self.check_virtual_server()

    @test.attr(type='smoke')
    def test_reorder_policies(self):
        # Create basic args for policy creation
        create_l7policy1_rule_kwargs = {'listener_id': self.listener_id,
                                        'action': 'REJECT',
                                        'admin_state_up': 'true',
                                        'position': 1}

        create_l7policy2_rule_kwargs = {'listener_id': self.listener_id,
                                        'action': 'REDIRECT_TO_URL',
                                        'redirect_url': 'http://www.acm.org',
                                        'admin_state_up': 'true',
                                        'position': 2}
        policy1 = self._create_l7policy(
            **create_l7policy1_rule_kwargs)
        policy1_id = policy1['id']
        self.addCleanup(self._delete_l7policy, policy1_id)

        rule1 = self._create_l7rule(
            policy1_id, type='PATH', compare_type='STARTS_WITH', value='/api')
        self.addCleanup(self._delete_l7rule, policy1_id, rule1['id'])

        self.check_policy()
        self.check_rule('reject_1', action='REJECT', condition='startsWith',
                        value='/api')
        self.check_virtual_server()

        policy2 = self._create_l7policy(
            **create_l7policy2_rule_kwargs)
        policy2_id = policy2['id']
        self.addCleanup(self._delete_l7policy, policy2_id)

        rule2 = self._create_l7rule(
            policy2_id, type='PATH', compare_type='ENDS_WITH', value='.jpg')
        self.addCleanup(self._delete_l7rule, policy2_id, rule2['id'])

        self.check_policy()
        self.check_rule('redirect_to_url_2', action='REDIRECT_TO_URL',
                        condition='endsWith', value='.jpg')
        self.check_virtual_server()

        update_rule_kwargs = {'position': 2}
        self._update_l7policy(policy1_id, **update_rule_kwargs)

        # redirect should now be first
        self.check_policy()
        self.check_rule('redirect_to_url_1', action='REDIRECT_TO_URL',
                        condition='endsWith', value='.jpg')
        self.check_rule('reject_2', action='REJECT', condition='startsWith',
                        value='/api')
        self.check_virtual_server()

    @test.attr(type='smoke')
    def test_delete_policy(self):
        # Create basic args for policy creation
        create_l7policy_rule_kwargs = {'listener_id': self.listener_id,
                                       'action': 'REJECT',
                                       'admin_state_up': 'true'}
        policy = self._create_l7policy(
            **create_l7policy_rule_kwargs)
        policy_id = policy['id']

        rule = self._create_l7rule(
            policy_id, type='PATH', compare_type='STARTS_WITH', value='/api')
        rule_id = rule['id']

        self.check_policy()
        self.check_rule('reject_1', action='REJECT', condition='startsWith',
                        value='/api')
        self.check_virtual_server()

        # remove both rule and policy and expect policy removed from BIG-IP
        self._delete_l7rule(policy_id, rule_id, wait=True)
        self._delete_l7policy(policy_id, wait=True)
        assert not self.bigip.policy_exists(
            'wrapper_policy', partition=self.partition)
        assert not self.bigip.virtual_server_has_policy(
            self.vs_name, 'wrapper_policy', self.partition)

    @test.attr(type='smoke')
    def test_delete_all_rules(self):
        # Create basic args for policy creation
        create_l7policy_rule_kwargs = {'listener_id': self.listener_id,
                                       'action': 'REJECT',
                                       'admin_state_up': 'true'}
        policy = self._create_l7policy(
            **create_l7policy_rule_kwargs)
        policy_id = policy['id']
        self.addCleanup(self._delete_l7policy, policy_id)

        rule = self._create_l7rule(
            policy_id, type='PATH', compare_type='STARTS_WITH', value='/api')
        rule_id = rule['id']

        self.check_policy()
        self.check_rule('reject_1', action='REJECT', condition='startsWith',
                        value='/api')
        self.check_virtual_server()

        # remove rule and expect policy removed from BIG-IP
        self._delete_l7rule(policy_id, rule_id, wait=True)
        assert not self.bigip.policy_exists(
            'wrapper_policy', partition=self.partition)
        assert not self.bigip.virtual_server_has_policy(
            self.vs_name, 'wrapper_policy', self.partition)

    @test.attr(type='smoke')
    def test_delete_one_rule(self):
        # Create basic args for policy creation
        create_l7policy_rule_kwargs = {'listener_id': self.listener_id,
                                       'action': 'REJECT',
                                       'admin_state_up': 'true'}
        policy = self._create_l7policy(
            **create_l7policy_rule_kwargs)
        policy_id = policy['id']
        self.addCleanup(self._delete_l7policy, policy_id)

        rule1 = self._create_l7rule(
            policy_id, type='PATH', compare_type='STARTS_WITH', value='/api')
        rule1_id = rule1['id']

        self.check_policy()
        self.check_rule('reject_1', action='REJECT', condition='startsWith',
                        value='/api')
        self.check_virtual_server()

        rule2 = self._create_l7rule(
            policy_id, type='PATH', compare_type='ENDS_WITH', value='/api')
        rule2_id = rule2['id']
        self.addCleanup(self._delete_l7rule, policy_id, rule2_id)
        self.check_policy()
        self.check_rule('reject_1', action='REJECT', condition='endsWith',
                        value='/api')
        self.check_virtual_server()

        # remove first rule leaving second and expect new policy on BIG-IP
        self._delete_l7rule(policy_id, rule1_id, wait=True)
        assert self.bigip.policy_exists(
            'wrapper_policy', partition=self.partition)
        assert self.bigip.virtual_server_has_policy(
            self.vs_name, 'wrapper_policy', self.partition)
