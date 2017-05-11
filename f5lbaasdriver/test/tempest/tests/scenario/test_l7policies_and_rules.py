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

from f5lbaasdriver.test.tempest.tests.scenario import f5_base

from tempest.lib.exceptions import NotFound

import pytest
import requests
import time


class TestL7Basic(f5_base.F5BaseTestCase):
    def setUp(self):
        super(TestL7Basic, self).setUp()
        self.policies = []

    def tearDown(self):
        for policy in self.policies:
            self._delete_l7policy(policy.get('id'))
        try:
            self._remove_members()
        except NotFound:
            pass
        super(TestL7Basic, self).tearDown()

    def _remove_members(self):
        # Due to issue 393 in github, nodes from the device are not deleted
        # unless the members are explicitly deleted
        self.members_client.delete_member(
            self.pool.get('id'),
            self.members['primary'].get('id')
        )
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self.members_client.delete_member(
            self.detached_pool.get('id'),
            self.members['secondary'].get('id')
        )
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))

    def _run_traffic(
            self, expected_server, headers=None, cookies=None, uri_path=None,
            expected_status=200):

        # We must allow time for changes in the control plane to propagate
        # to the data plane. So let's retry if we fail in any way.
        print('##################')
        print('##################')
        retries = 10
        for x in range(retries):
            try:
                if not uri_path:
                    uri_path = 'http://{}'.format(self.vip_ip)
                print('making request to {}'.format(uri_path))
                res = requests.get(uri_path, headers=headers, cookies=cookies)
                print('Expected_server: {}'.format(expected_server))
                print('Return server: {}'.format(res.text))
                assert expected_server in res.text
                assert res.status_code == expected_status
            except Exception as ex:
                if expected_server == 'fail':
                    if 'Connection aborted' in str(ex):
                        raise ex
                if x == retries - 1:
                    raise ex
                time.sleep(1)
                continue

    def _reject_args(self):
        self.reject_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REJECT'}

    def _redirect_pool_args(self):
        self.redirect_pool_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REDIRECT_TO_POOL',
            'redirect_pool_id': self.detached_pool.get('id')}

    def _redirect_url_args(self):
        self.redirect_url_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REDIRECT_TO_URL',
            'redirect_url': 'http://10.190.0.20'}


class TestL7BasicRedirectToPool(TestL7Basic):
    '''Testing L7 Redirect To Pool Policies deployed to BIG-IP device.'''

    def setUp(self):
        super(TestL7BasicRedirectToPool, self).setUp()
        self._redirect_pool_args()

    def test_policy_deployment(self):
        '''Policy without rule will have no effect.'''

        self._run_traffic('server1')
        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self.policies.append(self.l7policy)
        self._run_traffic('server1')
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._remove_members()

    def test_policy_redirect_pool_header_equal_to(self):
        '''Redirect to pool when header seen with value equal to.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'HEADER', 'compare_type': 'EQUAL_TO',
                     'key': 'X-HEADER', 'value': 'yes'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', headers={'X-HEADER': 'yes'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'X-HEADER': 'yes'})
        self._remove_members()

    def test_policy_redirect_pool_cookie_contains(self):
        '''Redirect to pool when cookie contains value.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'COOKIE', 'compare_type': 'CONTAINS',
                     'key': 'cook', 'value': 'es'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', cookies={'cook': 'test'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', cookies={'cook': 'test'})
        self._remove_members()

    def test_policy_redirect_pool_hostname_starts_with(self):
        '''Redirect traffic to pool when hostname ends with value.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'HOST_NAME', 'compare_type': 'STARTS_WITH',
                     'value': '2.3'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', headers={'Host': '2.3.4.2'})
        self._run_traffic('server1', headers={'Host': '2.2.3.2'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'Host': '2.3.4.2'})
        self._remove_members()

    def test_policy_redirect_pool_cookie_not_contains(self):
        '''Redirect to pool when cookie contains value.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'COOKIE', 'compare_type': 'CONTAINS',
                     'key': 'cook', 'value': 'es', 'invert': True}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server1', cookies={'cook': 'test'})
        self._run_traffic('server2', cookies={'cook': 'tetst'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', cookies={'cook': 'tetst'})
        self._remove_members()


class TestL7BasicRedirectToUrl(TestL7Basic):
    '''Testing L7 Redirect To Pool Policies deployed to BIG-IP device.'''

    def setUp(self):
        super(TestL7BasicRedirectToUrl, self).setUp()
        self._redirect_url_args()

    def test_policy_redirect_url_hostname_ends_with(self):
        '''Redirect traffic to url when hostname ends with value.'''

        self.l7policy = self._create_l7policy(**self.redirect_url_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'HOST_NAME', 'compare_type': 'ENDS_WITH',
                     'value': '1.1.1'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('coverity-doc', headers={'Host': '11.1.1.1'})
        self._run_traffic('coverity-doc', headers={'Host': '1.1.1.1'})
        self._run_traffic('server1', headers={'Host': '10.1.32.2'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'Host': '1.1.1.1'})
        self._remove_members()

    def test_policy_redirect_url_path_starts_with(self):
        '''Redirect traffic to url when path starts with value.'''

        self.l7policy = self._create_l7policy(**self.redirect_url_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'PATH', 'compare_type': 'STARTS_WITH',
                     'value': '/rel'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('coverity-doc',
                          uri_path='http://{}/release'.format(self.vip_ip))
        self._run_traffic('server1',
                          uri_path='http://{}/repre'.format(self.vip_ip))
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1',
                          uri_path='http://{}/release'.format(self.vip_ip))
        self._remove_members()

    def test_policy_redirect_url_file_type_not_contains(self):
        '''Redirect traffic to url when file type does not contains value.'''

        self.l7policy = self._create_l7policy(**self.redirect_url_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO',
                     'value': 'qcow2', 'invert': True}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('coverity-doc')
        self._run_traffic('server1',
                          uri_path='http://{}/t.qcow2'.format(self.vip_ip))
        self._run_traffic('coverity-doc',
                          uri_path='http://{}/t.txt'.format(self.vip_ip))
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1',
                          uri_path='http://{}/t.qcow2'.format(self.vip_ip))
        self._remove_members()

    def test_policy_redirect_url_file_type_fails_bad_compare_type(self):
        '''Redirect traffic to url when file type does not contains value.'''

        self.l7policy = self._create_l7policy(**self.redirect_url_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'STARTS_WITH',
                     'value': 'qcow2', 'invert': True}
        with pytest.raises(Exception) as ex:
            self._create_l7rule(self.l7policy.get('id'), **rule_args)
        assert 'Bad request' in ex.value.message
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._remove_members()


class TestL7BasicReject(TestL7Basic):
    '''Testing L7 Redirect To Pool Policies deployed to BIG-IP device.'''

    def setUp(self):
        super(TestL7BasicReject, self).setUp()
        self._reject_args()

    def test_policy_reject_header_starts_with(self):
        '''Reject traffic when header value starts with value.'''

        self.l7policy = self._create_l7policy(**self.reject_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'HEADER', 'compare_type': 'STARTS_WITH',
                     'key': 'X-HEADER', 'value': 'real'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server1', headers={'X-HEADER': 'test'})
        with pytest.raises(Exception) as ex:
            self._run_traffic('fail', headers={'X-HEADER': 'real_head'})
        assert 'Connection aborted' in str(ex)
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'X-HEADER': 'real_head'})
        self._remove_members()

    def test_policy_reject_file_type_equal_to(self):
        '''Reject traffic when header value starts with value.'''

        self.l7policy = self._create_l7policy(**self.reject_args)
        self.policies.append(self.l7policy)
        rule_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO',
                     'value': 'jpg'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic(
            'server1', uri_path='http://{}/test.jpeg'.format(self.vip_ip))
        with pytest.raises(Exception) as ex:
            self._run_traffic(
                'fail', uri_path='http://{}/test.jpg'.format(self.vip_ip))
        assert 'Connection aborted' in str(ex)
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1')
        self._remove_members()


class TestL7BasicUpdate(TestL7Basic):
    '''Test update operation on more complex set of policies and rules.'''

    def setUp(self):
        super(TestL7BasicUpdate, self).setUp()
        self._redirect_pool_args()
        self._redirect_url_args()
        self._reject_args()

    def test_policy_reorder_and_rule_update(self):
        '''Create multiple policies and rules then reorder policies.

        Due to SOL17095, on 11.6.0 before HF6, a bigip rule cannot contain
        multiple conditions that use the same operand and match type:
            such as header and ends_with.
        '''

        # Reject policy first becomes reject rule on device
        r1_args = {'type': 'FILE_TYPE', 'compare_type': 'EQUAL_TO'}
        r2_args = {'type': 'PATH', 'compare_type': 'CONTAINS'}
        r3_args = {'type': 'COOKIE', 'compare_type': 'ENDS_WITH', 'key': 'cky'}

        rej1_pol = self._create_l7policy(**self.reject_args)
        self.policies.append(rej1_pol)
        self._create_l7rule(rej1_pol.get('id'), value='i_t', **r2_args)
        self._create_l7rule(rej1_pol.get('id'), value='i', **r3_args)
        redir1_pol = self._create_l7policy(**self.redirect_pool_args)
        self.policies.append(redir1_pol)
        self._create_l7rule(redir1_pol.get('id'), value='/api', **r2_args)
        ru1 = self._create_l7rule(redir1_pol.get('id'), value='wav', **r1_args)
        rej2_pol = self._create_l7policy(**self.reject_args)
        self.policies.append(rej2_pol)
        self._create_l7rule(rej2_pol.get('id'), value='ookie', **r3_args)
        self._create_l7rule(rej2_pol.get('id'), value='gif', **r1_args)
        # Test policy1
        with pytest.raises(Exception) as ex1:
            self._run_traffic(
                'fail', uri_path='http://{}/fi_t.jpg'.format(self.vip_ip),
                cookies={'cky': 'ci'})
        assert 'Connection aborted' in str(ex1)
        # Test policy2
        self._run_traffic('server2',
                          uri_path='http://{}/api.wav'.format(self.vip_ip))
        # Test policy3
        with pytest.raises(Exception) as ex2:
            self._run_traffic(
                'fail', uri_path='http://{}/test.gif'.format(self.vip_ip),
                cookies={'cky': 'bookie'})
        assert 'Connection aborted' in str(ex2)
        # Test no match for any policy
        self._run_traffic('server1')

        # Reorder policies
        self._update_l7policy(redir1_pol.get('id'), position=1)
        # Redir should be matched first and we should get server2
        self._run_traffic('server2',
                          uri_path='http://{}/api_t.wav'.format(self.vip_ip),
                          cookies={'cky': 'cooki'})

        # Update rule for redirect policy3
        self._update_l7rule(redir1_pol.get('id'), ru1.get('id'), value='png')
        # Run traffic to check it was applied
        self._run_traffic('server1',
                          uri_path='http://{}/api.wav'.format(self.vip_ip))
        self._run_traffic('server2',
                          uri_path='http://{}/api.png'.format(self.vip_ip))
        self._delete_l7policy(rej1_pol.get('id'))
        self._delete_l7policy(redir1_pol.get('id'))
        self._delete_l7policy(rej2_pol.get('id'))
        self._remove_members()

    def test_policy_deployment_operand_match(self):
        '''Deploy multiple conditions for a rule with operands that match.

        This test will fail on 11.6.0 before Hotfix 6 due to issue: SOL17095
        '''

        # Reject policy first become reject rule on device
        r1_args = {'type': 'PATH', 'compare_type': 'CONTAINS'}

        rej1_pol = self._create_l7policy(**self.reject_args)
        self.policies.append(rej1_pol)
        self._create_l7rule(rej1_pol.get('id'), value='i_a', **r1_args)
        self._create_l7rule(rej1_pol.get('id'), value='i_b', **r1_args)
        self._create_l7rule(rej1_pol.get('id'), value='i_c', **r1_args)
        with pytest.raises(Exception) as ex:
            self._run_traffic('fail',
                              uri_path='http://{}/_i_ai_bdc_i_c'.format(
                                  self.vip_ip))
        assert 'Connection aborted' in str(ex)
        self._delete_l7policy(rej1_pol.get('id'))
        self._remove_members()
