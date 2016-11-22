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


class L7PolicyTestJSONBasic(base.BaseTestCase):
    """L7 Policy tempest tests.

    Tests the following operations in the Neutron-LBaaS API using the
    REST client with default credentials:

    1) Creating a L7 policy with REJECT action.
    2) Creating a L7 policy with a REDIRECT_URL action.
    3) Creating a L7 policy with a REDIRECT_POOL action.
    """

    @classmethod
    def resource_setup(cls):
        super(L7PolicyTestJSONBasic, cls).resource_setup()
        if not test.is_extension_enabled('lbaasv2', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(network_name)
        cls.subnet = cls.create_subnet(cls.network)
        cls.project_tenant_id = cls.subnet['tenant_id']
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


class TestL7PolicyTestJSONReject(L7PolicyTestJSONBasic):
    @test.attr(type='smoke')
    def test_create_l7_reject_policy(self):
        """Test the creationg of a L7 reject policy."""
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REJECT"

        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.addCleanup(self._delete_l7policy, new_policy['id'])
        assert (new_policy['action'] == "REJECT")

    def setUp(self):
        super(TestL7PolicyTestJSONReject, self).setUp()
        self._reject_args()

    def _reject_args(self):
        self.reject_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REJECT'}

    def test_policy_reject_header_ends_with(self):
        '''Reject traffic when header value ends with value.'''

        self.l7policy = self._create_l7policy(**self.reject_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'ENDS_WITH',
                     'key': 'X-HEADER', 'value': 'real'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self._create_l7rule(self.l7policy.get('id'), **rule_args)

        assert self.bigip_client.policy_exists("wrapper_policy",
                                               "Project_" +
                                               self.project_tenant_id)
        assert self.bigip_client.rule_exists("wrapper_policy",
                                             "reject_1",
                                             "Project_" +
                                             self.project_tenant_id)

    def test_policy_reject_header_contains(self):
        '''Reject traffic when header value ends with value.'''

        self.l7policy = self._create_l7policy(**self.reject_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'es'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self._create_l7rule(self.l7policy.get('id'), **rule_args)

        assert self.bigip_client.policy_exists("wrapper_policy",
                                               "Project_" +
                                               self.project_tenant_id)
        assert self.bigip_client.rule_exists("wrapper_policy",
                                             "reject_1",
                                             "Project_" +
                                             self.project_tenant_id)

    def test_policy_reject_two_rules(self):
        self.l7policy = self._create_l7policy(**self.reject_args)
        rule1_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                      'key': 'X-HEADER', 'value': 'es'}
        rule2_args = {'type': 'HEADER', 'compare_type': 'STARTS_WITH',
                      'key': 'X-HEADER', 'value': 'real'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.rule1 = self._create_l7rule(self.l7policy.get('id'), **rule1_args)
        self.rule2 = self._create_l7rule(self.l7policy.get('id'), **rule2_args)

        assert self.bigip_client.policy_exists("wrapper_policy",
                                               "Project_" +
                                               self.project_tenant_id)
        assert self.bigip_client.rule_exists("wrapper_policy",
                                             "reject_1",
                                             "Project_" +
                                             self.project_tenant_id)
        assert self.bigip_client.rule_has_condition("wrapper_policy",
                                                    "reject_1",
                                                    "contains",
                                                    "Project_" +
                                                    self.project_tenant_id)
        assert self.bigip_client.rule_has_condition("wrapper_policy",
                                                    "reject_1",
                                                    "startsWith",
                                                    "Project_" +
                                                    self.project_tenant_id)

        self._delete_l7rule(self.l7policy.get('id'), self.rule1.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer_id)
        assert self.bigip_client.policy_exists("wrapper_policy",
                                               "Project_" +
                                               self.project_tenant_id)
        assert not \
            (self.bigip_client.rule_has_condition("wrapper_policy",
                                                  "reject_1",
                                                  "contains",
                                                  "Project_" +
                                                  self.project_tenant_id))
        assert \
            self.bigip_client.rule_has_condition("wrapper_policy",
                                                 "reject_1",
                                                 "startsWith",
                                                 "Project_" +
                                                 self.project_tenant_id)

        self._delete_l7rule(self.l7policy.get('id'), self.rule2.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer_id)
        assert not \
            (self.bigip_client.policy_exists("wrapper_policy",
                                             "Project_" +
                                             self.project_tenant_id))


class TestL7PolicyTestJSONRedirectToUrl(L7PolicyTestJSONBasic):
    @test.attr(type='smoke')
    def test_create_l7_redirect_to_url_policy(self):
        """Test the creationg of a L7 URL redirect policy."""
        redirect_url = "http://www.mysite.com/my-widget-app"
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REDIRECT_TO_URL"
        create_l7policy_kwargs['redirect_url'] = redirect_url
        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.addCleanup(self._delete_l7policy, new_policy['id'])
        assert (new_policy['action'] == "REDIRECT_TO_URL")
        assert (new_policy['redirect_url'] == redirect_url)

    def setUp(self):
        super(TestL7PolicyTestJSONRedirectToUrl, self).setUp()
        self._redirect_url_args()

    def _redirect_url_args(self):
        self.redirect_url_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REDIRECT_TO_URL',
            'redirect_url': 'http://10.190.0.20'}

    def test_policy_redirect_url_contains(self):
        self.l7policy = self._create_l7policy(**self.redirect_url_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'es'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        assert self.bigip_client.policy_exists("wrapper_policy",
                                               "Project_" +
                                               self.project_tenant_id)
        assert self.bigip_client.rule_exists("wrapper_policy",
                                             "redirect_to_url_1",
                                             "Project_" +
                                             self.project_tenant_id)
        assert self.bigip_client.rule_has_condition("wrapper_policy",
                                                    "redirect_to_url_1",
                                                    "httpHeader",
                                                    "Project_" +
                                                    self.project_tenant_id)


class TestL7PolicyTestJSONRedirectToPool(L7PolicyTestJSONBasic):
    @test.attr(type='smoke')
    def test_create_l7_redirect_to_pool_policy(self):
        """Test the creationg of a L7 pool redirect policy."""
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REDIRECT_TO_POOL"
        create_l7policy_kwargs['redirect_pool_id'] = self.pool_id

        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.addCleanup(self._delete_l7policy, new_policy['id'])
        assert (new_policy['action'] == "REDIRECT_TO_POOL")
        assert (new_policy['redirect_pool_id'] == self.pool_id)
