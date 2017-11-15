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

from collections import namedtuple
from time import sleep

from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base

CONF = config.CONF
ArgSet = namedtuple('ArgSet', 'expected, project')


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

    def _create_detached_pool(self):
        pool = {
            'loadbalancer_id': self.load_balancer.get('id'),
            'lb_algorithm': 'ROUND_ROBIN',
            'protocol': 'HTTP'
        }
        self.detached_pool = self.pools_client.create_pool(**pool)
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self.assertTrue(self.detached_pool)
        self.addCleanup(self._delete_pool, self.detached_pool.get('id'))

    def setUp(self):
        self.policies = []
        self._create_detached_pool()
        super(L7PolicyTestJSONBasic, self).setUp()

    def tearDown(self):
        for policy in self.policies:
            try:
                self._delete_l7policy(policy.get('id'))
            except Exception as ex:
                if 'could not be found' in str(ex):
                    continue
                raise
        super(L7PolicyTestJSONBasic, self).tearDown()


class L7PolicyTestConstructor(L7PolicyTestJSONBasic):
    # leave consistency checking to my IDE...
    try_cnt_max = 3
    sleep_seconds = 5
    rj_1 = 'reject_1'
    rj_2 = 'reject_2'
    cnts = 'contains'
    es = 'es'
    ireal = 'ireal'
    real = 'real'
    starts_with = 'startsWith'
    ends_with = 'endsWith'
    wrap_pol = 'wrapper_policy'
    proj = 'Project_'
    test = 'test'
    al = 'al'
    http_header = "httpHeader"
    not_ = "not_"
    qcow2 = 'qcow2'
    redirect_to_url_1 = 'redirect_to_url_1'
    ext = 'extension'
    jpg = 'jpg'
    _re = 're'
    redirect_to_pool_1 =  'redirect_to_pool_1'
    wrapper_policy = ArgSet([wrap_pol], proj)
    reject_1 = ArgSet([wrap_pol, rj_1], proj)
    reject_1_contains_al = ArgSet([wrap_pol, rj_1, cnts, al], proj)
    reject_1_contains_es = ArgSet([wrap_pol, rj_1, cnts, es], proj)
    reject_1_contains_l = ArgSet([wrap_pol, rj_1, cnts, 'l'], proj)
    reject_1_endswith_ireal = ArgSet([wrap_pol, rj_1, ends_with, ireal], proj)
    reject_1_endswith_real = ArgSet([wrap_pol, rj_1, ends_with, real], proj)
    reject_1_endswith_test = ArgSet([wrap_pol, rj_1, ends_with, test], proj)
    reject_1_startswith_re = ArgSet([wrap_pol, rj_1, starts_with, _re], proj)
    reject_1_startswith_real = ArgSet([wrap_pol, rj_1, starts_with, real],
                                      proj)
    reject_2 = ArgSet([wrap_pol, rj_2], proj)
    reject_2_contains_es = ArgSet([wrap_pol, rj_2, cnts, es], proj)
    reject_2_startswith_real = ArgSet([wrap_pol, rj_2, starts_with, real],
                                      proj)
    redirect_to_url_l_httpheader_es = \
        ArgSet([wrap_pol, redirect_to_url_1, http_header, es], proj)
    redirect_to_pool_1_extension_qcow2 = \
        ArgSet([wrap_pol, redirect_to_pool_1, ext, qcow2], proj)
    redirect_to_pool_1_not__qcow2 = \
        ArgSet([wrap_pol, redirect_to_pool_1, not_, qcow2], proj)
    redirect_to_pool_1_extension_jpg = \
        ArgSet([wrap_pol, redirect_to_pool_1, ext, jpg], proj)
    redirect_to_pool_1 = ArgSet([wrap_pol, redirect_to_pool_1], proj)
    redirect_to_url_1 = ArgSet([wrap_pol, redirect_to_url_1], proj)

    @classmethod
    def assert_with_retry(cls, check, method, arg_set, tenant_id, **kwargs):
        """Performs an object manipulation"""
        proj = arg_set.project + tenant_id
        args = list(arg_set.expected)
        args.append(proj)
        try_cnt = 0
        try_cnt_max = cls.try_cnt_max
        sleep_seconds = 5
        while True:
            try:
                check(method, *args, **kwargs)
            except AssertionError:
                if try_cnt < try_cnt_max:
                    try_cnt += 1
                    sleep(sleep_seconds)
                    continue
                raise
            except TypeError as Err:
                raise TypeError("{}: ({})".format(Err, args))
            else:
                break


class L7PolicyJSONReject(L7PolicyTestConstructor):
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
        l7policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self.policies.append(l7policy)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        assert (l7policy.get('action') == "REJECT")
        for bigip_client in self.bigip_clients:
            self.neg_assertion_check(
                bigip_client.policy_exists, self.wrapper_policy,
                self.project_tenant_id, should_exist=False)

    def test_policy_reject_header_ends_with(self):
        '''Reject traffic when header value ends with value.'''

        l7policy = self._create_l7policy(**self.reject_args)
        self.policies.append(l7policy)
        rule_args = {'type': 'HEADER', 'compare_type': 'ENDS_WITH',
                     'key': 'X-HEADER', 'value': 'real'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self._create_l7rule(l7policy.get('id'), **rule_args)

        for bigip_client in self.bigip_clients:
            self.assertion_check(
                bigip_client.policy_exists, self.wrapper_policy,
                self.project_tenant_id)
            self.assertion_check(
                bigip_client.rule_exists, self.reject_1,
                self.project_tenant_id)
            self.assertion_check(
                bigip_client.rule_has_condition,
                self.reject_1_endswith_real,
                self.project_tenant_id)

    def test_policy_reject_header_contains(self):
        '''Reject traffic when header value ends with value.'''

        l7policy = self._create_l7policy(**self.reject_args)
        self.policies.append(l7policy)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'es'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self._create_l7rule(l7policy.get('id'), **rule_args)

        for bigip_client in self.bigip_clients:
            self.assertion_check(bigip_client.policy_exists,
                                 self.wrapper_policy, self.project_tenant_id)
            self.assertion_check(bigip_client.rule_exists, self.reject_1,
                                 self.project_tenant_id)
            self.assertion_check(bigip_client.rule_has_condition,
                                 self.reject_1_contains_es,
                                 self.project_tenant_id)

    def test_policy_reject_three_rules(self):
        l7policy = self._create_l7policy(**self.reject_args)
        self.policies.append(l7policy)
        rule1_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                      'key': 'X-HEADER', 'value': 'es'}
        rule2_args = {'type': 'COOKIE', 'compare_type': 'STARTS_WITH',
                      'key': 'cook', 'value': 'real'}
        rule3_args = {'type': 'HOST_NAME', 'compare_type': 'ENDS_WITH',
                      'value': 'test'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.rule1 = self._create_l7rule(l7policy.get('id'), **rule1_args)
        self.rule2 = self._create_l7rule(l7policy.get('id'), **rule2_args)
        self.rule3 = self._create_l7rule(l7policy.get('id'), **rule3_args)

        for bigip_client in self.bigip_clients:
            rule_has_condition = bigip_client.rule_has_condition
            self.assertion_check(bigip_client.policy_exists,
                                 self.wrapper_policy, self.project_tenant_id)
            self.assertion_check(bigip_client.rule_exists, self.reject_1,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition, self.reject_1_contains_es,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_startswith_real,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_endswith_test,
                                 self.project_tenant_id)

        self._delete_l7rule(l7policy.get('id'), self.rule1.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer_id)

        for bigip_client in self.bigip_clients:
            rule_has_condition = bigip_client.rule_has_condition
            self.assertion_check(bigip_client.policy_exists,
                                 self.wrapper_policy,
                                 self.project_tenant_id)
            self.neg_assertion_check(rule_has_condition,
                                     self.reject_1_contains_es,
                                     self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_startswith_real,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_endswith_test,
                                 self.project_tenant_id)

        self._delete_l7rule(l7policy.get('id'), self.rule2.get('id'))
        self._delete_l7rule(l7policy.get('id'), self.rule3.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            self.neg_assertion_check(
                bigip_client.policy_exists, self.wrapper_policy,
                self.project_tenant_id, should_exist=False)

    def test_policy_reject_multi_policy_multi_rules(self):
        l7policy1 = self._create_l7policy(**self.reject_args)
        self.policies.append(l7policy1)
        rule1_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                      'key': 'X-HEADER', 'value': 'es'}
        rule2_args = {'type': 'COOKIE', 'compare_type': 'STARTS_WITH',
                      'key': 'cook', 'value': 'real'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self.rule1 = self._create_l7rule(l7policy1.get('id'), **rule1_args)
        self.rule2 = self._create_l7rule(l7policy1.get('id'), **rule2_args)

        l7policy2 = self._create_l7policy(**self.reject_args)
        self.policies.append(l7policy2)
        self.rule3 = self._create_l7rule(l7policy2.get('id'), **rule1_args)
        self.rule4 = self._create_l7rule(l7policy2.get('id'), **rule2_args)

        self._delete_l7rule(l7policy1.get('id'), self.rule1.get('id'))
        for bigip_client in self.bigip_clients:
            rule_exists = bigip_client.rule_exists
            rule_has_condition = bigip_client.rule_has_condition
            self.assertion_check(bigip_client.policy_exists,
                                 self.wrapper_policy,
                                 self.project_tenant_id)
            self.assertion_check(
                rule_exists, self.reject_1, self.project_tenant_id)
            self.assertion_check(
                rule_exists, self.reject_2, self.project_tenant_id)
            self.neg_assertion_check(  # did not evaluate as true in one run
                rule_has_condition, self.reject_1_contains_es,
                self.project_tenant_id)
            self.neg_assertion_check(
                rule_has_condition, self.reject_1_startswith_real,
                self.project_tenant_id)
            self.neg_assertion_check(
                rule_has_condition, self.reject_2_startswith_real,
                self.project_tenant_id)
            self.neg_assertion_check(
                rule_has_condition, self.reject_2_contains_es,
                self.project_tenant_id)

        self._delete_l7policy(l7policy1.get('id'))
        for bigip_client in self.bigip_clients:
            rule_exists = bigip_client.rule_exists
            rule_has_condition = bigip_client.rule_has_condition
            self.neg_assertion_check(rule_exists, self.reject_1,
                                     self.project_tenant_id)
            self.assertion_check(rule_exists, self.reject_2,
                                 self.project_tenant_id)
            self.assertion_check(
                bigip_client.policy_exists, self.wrapper_policy,
                self.project_tenant_id)
            self.assertion_check(
                rule_has_condition, self.reject_2_contains_es,
                self.project_tenant_id)
            self.assertion_check(
                rule_has_condition, self.reject_2_startswith_real,
                self.project_tenant_id)
        self._delete_l7policy(l7policy2.get('id'))
        for bigip_client in self.bigip_clients:
            assert not bigip_client.policy_exists("wrapper_policy",
                                                  "Project_" +
                                                  self.project_tenant_id,
                                                  should_exist=False)

    def test_policy_reject_many_rules(self):
        l7policy = self._create_l7policy(**self.reject_args)
        self.policies.append(l7policy)
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
        self.rule1 = self._create_l7rule(l7policy.get('id'), **rule1_args)
        self.rule2 = self._create_l7rule(l7policy.get('id'), **rule2_args)
        self.rule3 = self._create_l7rule(l7policy.get('id'), **rule3_args)
        self.rule4 = self._create_l7rule(l7policy.get('id'), **rule4_args)
        self.rule5 = self._create_l7rule(l7policy.get('id'), **rule5_args)
        self.rule6 = self._create_l7rule(l7policy.get('id'), **rule6_args)
        self.rule7 = self._create_l7rule(l7policy.get('id'), **rule7_args)

        for bigip_client in self.bigip_clients:
            rule_has_condition = bigip_client.rule_has_condition
            self.assertion_check(bigip_client.policy_exists,
                                 self.wrapper_policy, self.project_tenant_id)
            self.assertion_check(bigip_client.rule_exists, self.reject_1,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition, self.reject_1_contains_es,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_startswith_real,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_endswith_real,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_startswith_re,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition, self.reject_1_contains_al,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition, self.reject_1_contains_l,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.reject_1_endswith_ireal,
                                 self.project_tenant_id)

        self._delete_l7rule(l7policy.get('id'), self.rule1.get('id'))
        for bigip_client in self.bigip_clients:
            self.neg_assertion_check(bigip_client.rule_has_condition,
                                     self.reject_1_contains_es,
                                     self.project_tenant_id)
        self._delete_l7rule(l7policy.get('id'), self.rule2.get('id'))
        self._delete_l7rule(l7policy.get('id'), self.rule3.get('id'))
        self._delete_l7rule(l7policy.get('id'), self.rule4.get('id'))
        self._delete_l7rule(l7policy.get('id'), self.rule5.get('id'))
        self._delete_l7rule(l7policy.get('id'), self.rule6.get('id'))
        self._delete_l7rule(l7policy.get('id'), self.rule7.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            self.neg_assertion_check(
                bigip_client.policy_exists, self.wrapper_policy,
                self.project_tenant_id, should_exist=False)


class TestL7PolicyTestJSONRedirectToUrl(L7PolicyTestConstructor):
    def setUp(self):
        super(TestL7PolicyTestJSONRedirectToUrl, self).setUp()
        self._redirect_url_args()

    def _redirect_url_args(self):
        self.redirect_url_args = {
            'listener_id': self.listener.get('id'), 'admin_state_up': 'true',
            'action': 'REDIRECT_TO_URL', 'redirect_url': 'http://www.cdc.gov'}

    def test_create_l7_redirect_to_url_policy(self):
        """Test the creationg of a L7 URL redirect policy."""
        l7policy = self._create_l7policy(
            **self.redirect_url_args)
        self.policies.append(l7policy)
        self._wait_for_load_balancer_status(self.load_balancer_id)

    def test_policy_redirect_url_contains(self):
        l7policy = self._create_l7policy(**self.redirect_url_args)
        self.policies.append(l7policy)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'es'}
        self._wait_for_load_balancer_status(self.load_balancer_id)
        self._create_l7rule(l7policy.get('id'), **rule_args)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        for bigip_client in self.bigip_clients:
            policy_exists = bigip_client.policy_exists
            rule_exists = bigip_client.rule_exists
            rule_has_condition = bigip_client.rule_has_condition
            self.assertion_check(policy_exists, self.wrapper_policy,
                                 self.project_tenant_id)
            self.assertion_check(rule_exists, self.redirect_to_url_1,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.redirect_to_url_l_httpheader_es,
                                 self.project_tenant_id)


class L7PolicyJSONRedirectToPool(L7PolicyTestConstructor):
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
        l7policy = self._create_l7policy(
            **self.redirect_pool_args)
        self.policies.append(l7policy)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        # File type rule cannot have contains as compare type
        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO',
                     'value': 'jpg'}
        self._create_l7rule(l7policy.get('id'), **rule_args)
        for bigip_client in self.bigip_clients:
            self.assertion_check(bigip_client.policy_exists,
                                 self.wrapper_policy, self.project_tenant_id)
            self.assertion_check(bigip_client.rule_exists,
                                 self.redirect_to_pool_1,
                                 self.project_tenant_id)
            self.assertion_check(bigip_client.rule_has_condition,
                                 self.redirect_to_pool_1_extension_jpg,
                                 self.project_tenant_id)

    def test_create_l7_redirect_to_pool_policy_not_file_type(self):
        """Test the creationg of a L7 pool redirect policy."""
        l7policy = self._create_l7policy(
            **self.redirect_pool_args)
        self.policies.append(l7policy)
        self._wait_for_load_balancer_status(self.load_balancer_id)
        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO',
                     'value': 'qcow2', 'invert': True}
        rule1 = self._create_l7rule(l7policy.get('id'), **rule_args)
        for bigip_client in self.bigip_clients:
            policy_exists = bigip_client.policy_exists
            rule_has_condition = bigip_client.rule_has_condition
            rule_exists = bigip_client.rule_exists
            self.assertion_check(policy_exists, self.wrapper_policy,
                                 self.project_tenant_id)
            self.assertion_check(rule_exists, self.redirect_to_url_1,
                                 self.project_tenant_id)
            self.assertion_check(rule_has_condition,
                                 self.redirect_to_pool_1_extension_qcow2,
                                 self.project_tenant_id)
            # Verify same rule exists, but invert is set to True
            self.assertion_check(rule_has_condition,
                                 self.redirect_to_pool_1_not__qcow2,
                                 self.project_tenant_id)
        rule_args['invert'] = False
        # Change invert to False and check if it sticks
        self._update_l7rule(l7policy.get('id'), rule1.get('id'), **rule_args)
        for bigip_client in self.bigip_clients:
            rule_has_condition = bigip_client.rule_has_condition
            self.neg_assertion_check(rule_has_condition,
                                     self.redirect_to_pool_1_not__qcow2,
                                     self.project_tenant_id)
