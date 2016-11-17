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

import pytest
import requests


class TestL7PolicyBasic(f5_base.F5BaseTestCase):
    '''Testing L7Policies deployed to BIG-IP device.'''

    def remove_members(self):
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
        super(TestL7PolicyBasic, self).tearDown()

    def _redirect_pool_args(self):
        self.redirect_pool_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REDIRECT_TO_POOL',
            'redirect_pool_id': self.detached_pool.get('id')}

    def _reject_pool_args(self):
        self.reject_pool_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REJECT'}

    def _redirect_url_args(self):
        self.redirect_url_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REDIRECT_TO_URL',
            'redirect_url': 'http://10.190.0.20'}

    def setUp(self):
        super(TestL7PolicyBasic, self).setUp()
        self._redirect_pool_args()
        self._reject_pool_args()
        self._redirect_url_args()

    def _run_traffic(
            self, expected_server, headers=None, cookies=None,
            expected_status=200):
        print('##################')
        print('##################')
        print('making request to {}'.format(self.vip_ip))
        res = None
        res = requests.get('http://{}'.format(self.vip_ip),
                           headers=headers, cookies=cookies)
        print('Expected_server: {}'.format(expected_server))
        print('Return server: {}'.format(res.text))
        assert expected_server in res.text
        assert res.status_code == expected_status

    def test_policy_deployment(self):
        '''Policy without rule will have no effect.'''

        self._run_traffic('server1')
        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self._run_traffic('server1')
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self.remove_members()

    def test_policy_redirect_pool_header_equal_to(self):
        '''Redirect to pool when header seen with value equal to.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'EQUAL_TO',
                     'key': 'X-HEADER', 'value': 'yes'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', headers={'X-HEADER': 'yes'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'X-HEADER': 'yes'})
        self.remove_members()

    def test_policy_redirect_pool_cookie_contains(self):
        '''Redirect to pool when cookie contains value.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        rule_args = {'type': 'COOKIE', 'compare_type': 'CONTAINS',
                     'key': 'cook', 'value': 'es'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', cookies={'cook': 'test'})
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', cookies={'cook': 'test'})
        self.remove_members()

    def test_policy_reject_header_starts_with(self):
        '''Reject traffic when header value starts with value.'''

        self.l7policy = self._create_l7policy(**self.reject_pool_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'real'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server1', headers={'X-HEADER': 'test'})
        with pytest.raises(Exception) as ex:
            self._run_traffic('server2', headers={'X-HEADER': 'real_head'})
        assert 'Connection aborted' in str(ex)
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'X-HEADER': 'test'})
        self.remove_members()

    def test_policy_reject_header_starts_with_issue_393(self):
        '''Test should fail until pool delete also deletes nodes on device.'''

        self.l7policy = self._create_l7policy(**self.reject_pool_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'CONTAINS',
                     'key': 'X-HEADER', 'value': 'real'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server1', headers={'X-HEADER': 'test'})
        with pytest.raises(Exception) as ex:
            self._run_traffic('server2', headers={'X-HEADER': 'real_head'})
        assert 'Connection aborted' in str(ex)
        self._delete_l7policy(self.l7policy.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1', headers={'X-HEADER': 'test'})

    def test_policy_redirect_url_hostname_ends_with(self):
        '''Redirect traffic to url when hostname ends with value.'''

        self.l7policy = self._create_l7policy(**self.redirect_url_args)
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
        self.remove_members()
