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

import pytest

from tempest import config
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base

CONF = config.CONF


class L7PolicyTestJSONBasic(base.F5BaseTestCase):
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

    def _create_detached_pool(self):
        pool = {
            'loadbalancer_id': self.load_balancer.get('id'),
            'lb_algorithm': 'ROUND_ROBIN',
            'protocol': 'HTTP'
        }
        self.detached_pool = self.create_pool(self.load_balancer, **pool)
        assert self.detached_pool

    def _setup_layer3(self):
        self.network = self.create_network()
        self.subnet = self.create_subnet(self.network)
        self.project_tenant_id = self.subnet['tenant_id']

    def _setup_to_pool(self):
        self.create_lb_kwargs = {'tenant_id': self.subnet['tenant_id'],
                                 'vip_subnet_id': self.subnet['id']}
        self.load_balancer = \
            self.create_loadbalancer(**self.create_lb_kwargs)
        self.load_balancer_id = self.load_balancer['id']

        # Create listener for tests
        self.create_listener_kwargs = \
            {'loadbalancer_id': self.load_balancer_id,
             'protocol': "HTTP",
             'protocol_port': "80"}
        self.listener = (
            self.create_listener(loadbalancer=self.load_balancer,
                                 **self.create_listener_kwargs))
        self.listener_id = self.listener['id']

        # Create pool for tests
        self.create_pool_kwargs = {'listener_id': self.listener_id,
                                   'protocol': "HTTP",
                                   'lb_algorithm': "ROUND_ROBIN"}
        self.pool = (
            self.create_pool(loadbalancer=self.load_balancer,
                             **self.create_pool_kwargs))
        self.pool_id = self.pool['id']

    def setUp(self):
        super(L7PolicyTestJSONBasic, self).setUp()
        self._setup_layer3()
        self._setup_to_pool()
        self._create_detached_pool()

    def tearDown(self):
        super(L7PolicyTestJSONBasic, self).tearDown()


class L7PolicyJSONReject(L7PolicyTestJSONBasic):
    def setUp(self):
        super(L7PolicyJSONReject, self).setUp()
        self._reject_args()

    def _reject_args(self):
        self.reject_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REJECT'}

    def test_create_l7_reject_policy(self):
        """Test the creationg of a L7 reject policy."""
        create_l7policy_kwargs = self.reject_args
        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **create_l7policy_kwargs)
        policy_name = "wrapper_policy_{}".format(self.listener_id)

        assert (l7policy.get('action') == "REJECT")
        for bigip_client in self.bigip_clients:
            assert not bigip_client.policy_exists(
                policy_name,
                "Project_" +
                self.project_tenant_id,
                should_exist=False)

    def test_policy_reject_header_ends_with(self):
        '''Reject traffic when header value ends with value.'''

        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.reject_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)
        rule_args = {'type': 'HEADER', 'compare_type': 'ENDS_WITH',
                     'key': 'X-HEADER', 'value': 'real'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule_args)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "endsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)

    def test_policy_reject_header_contains(self):
        '''Reject traffic when header value ends with value.'''

        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.reject_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'es'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule_args)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "contains",
                                                   "es",
                                                   "Project_" +
                                                   self.project_tenant_id)

    def test_policy_reject_three_rules(self):
        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.reject_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)
        rule1_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                      'key': 'X-HEADER', 'value': 'es'}
        rule2_args = {'type': 'COOKIE', 'compare_type': 'STARTS_WITH',
                      'key': 'cook', 'value': 'real'}
        rule3_args = {'type': 'HOST_NAME', 'compare_type': 'ENDS_WITH',
                      'value': 'test'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.rule1 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule1_args)
        self.rule2 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule2_args)
        self.rule3 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule3_args)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "contains",
                                                   "es",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "startsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "endsWith",
                                                   "test",
                                                   "Project_" +
                                                   self.project_tenant_id)

        self.delete_l7rule(
            l7policy.get('id'), self.rule1.get('id'), self.load_balancer_id)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert not \
                bigip_client.rule_has_condition(policy_name,
                                                "reject_1",
                                                "contains",
                                                "es",
                                                "Project_" +
                                                self.project_tenant_id)
            assert \
                bigip_client.rule_has_condition(policy_name,
                                                "reject_1",
                                                "startsWith",
                                                "real",
                                                "Project_" +
                                                self.project_tenant_id)
            assert \
                bigip_client.rule_has_condition(policy_name,
                                                "reject_1",
                                                "endsWith",
                                                "test",
                                                "Project_" +
                                                self.project_tenant_id)

        self.delete_l7rule(
            l7policy.get('id'), self.rule2.get('id'), self.load_balancer_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule3.get('id'), self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            assert not bigip_client.policy_exists(policy_name,
                                                  "Project_" +
                                                  self.project_tenant_id,
                                                  should_exist=False)

    def test_policy_reject_multi_policy_multi_rules(self):
        l7policy1 = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.reject_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)
        rule1_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                      'key': 'X-HEADER', 'value': 'es'}
        rule2_args = {'type': 'COOKIE', 'compare_type': 'STARTS_WITH',
                      'key': 'cook', 'value': 'real'}

        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.rule1 = self.create_l7rule(
            l7policy1.get('id'), loadbalancer=self.load_balancer, **rule1_args)
        self.rule2 = self.create_l7rule(
            l7policy1.get('id'), loadbalancer=self.load_balancer, **rule2_args)

        l7policy2 = self.create_l7policy(**self.reject_args)
        self.rule3 = self.create_l7rule(
            l7policy2.get('id'), loadbalancer=self.load_balancer, **rule1_args)
        self.rule4 = self.create_l7rule(
            l7policy2.get('id'), loadbalancer=self.load_balancer, **rule2_args)

        self.delete_l7rule(
            l7policy1.get('id'), self.rule1.get('id'), self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_2",
                                            "Project_" +
                                            self.project_tenant_id)
            assert not bigip_client.rule_has_condition(policy_name,
                                                       "reject_1",
                                                       "contains",
                                                       "es",
                                                       "Project_" +
                                                       self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "startsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_2",
                                                   "startsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_2",
                                                   "contains",
                                                   "es",
                                                   "Project_" +
                                                   self.project_tenant_id)

        self.delete_l7policy(l7policy1.get('id'), self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            assert not bigip_client.rule_exists(policy_name,
                                                "reject_1",
                                                "Project_" +
                                                self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_2",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_2",
                                                   "contains",
                                                   "es",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_2",
                                                   "startsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)
        self.delete_l7policy(l7policy2.get('id'), self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            assert not bigip_client.policy_exists(policy_name,
                                                  "Project_" +
                                                  self.project_tenant_id,
                                                  should_exist=False)

    def test_policy_reject_many_rules(self):
        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.reject_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)
        rule1_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                      'key': 'X-HEADER', 'value': 'es'}
        rule2_args = {'type': 'HOST_NAME', 'compare_type': 'STARTS_WITH',
                      'value': 'real'}
        rule3_args = {'type': 'PATH', 'compare_type': 'ENDS_WITH',
                      'value': 'real'}
        rule4_args = {'type': 'PATH', 'compare_type': 'STARTS_WITH',
                      'value': 're'}
        rule5_args = {'type': 'PATH', 'compare_type': 'CONTAINS',
                      'value': 'al'}
        rule6_args = {'type': 'PATH', 'compare_type': 'CONTAINS',
                      'value': 'l'}
        rule7_args = {'type': 'PATH', 'compare_type': 'ENDS_WITH',
                      'value': 'ireal'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.rule1 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule1_args)
        self.rule2 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule2_args)
        self.rule3 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule3_args)
        self.rule4 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule4_args)
        self.rule5 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule5_args)
        self.rule6 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule6_args)
        self.rule7 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule7_args)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "reject_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "contains",
                                                   "es",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "startsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "endsWith",
                                                   "real",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "startsWith",
                                                   "re",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "contains",
                                                   "al",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "contains",
                                                   "l",
                                                   "Project_" +
                                                   self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "reject_1",
                                                   "endsWith",
                                                   "ireal",
                                                   "Project_" +
                                                   self.project_tenant_id)

        self.delete_l7rule(
            l7policy.get('id'), self.rule1.get('id'),
            loadbalancer=self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            assert not bigip_client.rule_has_condition(policy_name,
                                                       "reject_1",
                                                       "contains",
                                                       "es",
                                                       "Project_" +
                                                       self.project_tenant_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule2.get('id'),
            loadbalancer=self.load_balancer_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule3.get('id'),
            loadbalancer=self.load_balancer_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule4.get('id'),
            loadbalancer=self.load_balancer_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule5.get('id'),
            loadbalancer=self.load_balancer_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule6.get('id'),
            loadbalancer=self.load_balancer_id)
        self.delete_l7rule(
            l7policy.get('id'), self.rule7.get('id'),
            loadbalancer=self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            assert not bigip_client.policy_exists(policy_name,
                                                  "Project_" +
                                                  self.project_tenant_id,
                                                  should_exist=False)


class TestL7PolicyTestJSONRedirectToUrl(L7PolicyTestJSONBasic):
    def setUp(self):
        super(TestL7PolicyTestJSONRedirectToUrl, self).setUp()
        self._redirect_url_args()

    def _redirect_url_args(self):
        self.redirect_url_args = {
            'listener_id': self.listener.get('id'), 'admin_state_up': 'true',
            'action': 'REDIRECT_TO_URL', 'redirect_url': 'http://www.cdc.gov'}

    @pytest.mark.skip(reason=str("40ac765cec41927c9310f91243b113d4de789583 has"
                                 " a complete removal of fn() here"))
    def test_create_l7_redirect_to_url_policy(self):
        """Test the creationg of a L7 URL redirect policy."""
        # l7policy = self.create_l7policy(
        #     loadbalancer=self.load_balancer, **self.redirect_url_args)
        # self._wait_for_load_balancer_status(self.load_balancer_id)
        pass

    def test_policy_redirect_url_contains(self):
        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.redirect_url_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'es'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule_args)
        self._wait_for_load_balancer_status(self.load_balancer_id)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "redirect_to_url_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "redirect_to_url_1",
                                                   "httpHeader",
                                                   "es",
                                                   "Project_" +
                                                   self.project_tenant_id)


class L7PolicyJSONRedirectToPool(L7PolicyTestJSONBasic):
    def setUp(self):
        super(L7PolicyJSONRedirectToPool, self).setUp()
        self._redirect_pool_args()

    def _redirect_pool_args(self):
        self.redirect_pool_args = {
            'listener_id': self.listener.get('id'), 'admin_state_up': 'true',
            'action': 'REDIRECT_TO_POOL',
            'redirect_pool_id': self.detached_pool.get('id')}

    def test_create_l7_redirect_to_pool_policy_file_type_contains(self):
        """Test the creationg of a L7 pool redirect policy."""
        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.redirect_pool_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)

        self._wait_for_load_balancer_status(self.load_balancer_id)
        # File type rule cannot have contains as compare type
        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO',
                     'value': 'jpg'}
        self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule_args)
        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "redirect_to_pool_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "redirect_to_pool_1",
                                                   "extension",
                                                   "jpg",
                                                   "Project_" +
                                                   self.project_tenant_id)

    def test_create_l7_redirect_to_pool_policy_not_file_type(self):
        """Test the creationg of a L7 pool redirect policy."""
        l7policy = self.create_l7policy(
            loadbalancer=self.load_balancer, **self.redirect_pool_args)
        policy_name = "wrapper_policy_{}".format(self.listener_id)

        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO',
                     'value': 'qcow2', 'invert': True}
        rule1 = self.create_l7rule(
            l7policy.get('id'), loadbalancer=self.load_balancer, **rule_args)

        for bigip_client in self.bigip_clients:
            assert bigip_client.policy_exists(policy_name,
                                              "Project_" +
                                              self.project_tenant_id)
            assert bigip_client.rule_exists(policy_name,
                                            "redirect_to_pool_1",
                                            "Project_" +
                                            self.project_tenant_id)
            assert bigip_client.rule_has_condition(policy_name,
                                                   "redirect_to_pool_1",
                                                   "extension",
                                                   "qcow2",
                                                   "Project_" +
                                                   self.project_tenant_id)
            # Verify same rule exists, but invert is set to True
            assert bigip_client.rule_has_condition(policy_name,
                                                   "redirect_to_pool_1",
                                                   "not_",
                                                   "qcow2",
                                                   "Project_" +
                                                   self.project_tenant_id)
        rule_args['invert'] = False
        # Change invert to False and check if it sticks
        self.update_l7rule(
            l7policy.get('id'), rule1.get('id'),
            loadbalancer=self.load_balancer, **rule_args)
        for bigip_client in self.bigip_clients:
            assert not bigip_client.rule_has_condition(policy_name,
                                                       "redirect_to_pool_1",
                                                       "not_",
                                                       "qcow2",
                                                       "Project_" +
                                                       self.project_tenant_id)
