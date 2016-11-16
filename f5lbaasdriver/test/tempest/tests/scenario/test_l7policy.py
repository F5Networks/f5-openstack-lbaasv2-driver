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
import urllib2


class TestL7PolicyBasic(f5_base.F5BaseTestCase):
    '''Testing L7Policies deployed to BIG-IP device.'''

    def _redirect_pool_args(self):
        self.redirect_pool_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REDIRECT_TO_POOL',
            'redirect_pool_id': self.detached_pool.get('id')}

    def _reject_pool_args(self):
        self.reject_pool_args = {
            'listener_id': self.listener.get('id'),
            'admin_state_up': 'true', 'action': 'REJECT'}

    def setUp(self):
        super(TestL7PolicyBasic, self).setUp()
        self._redirect_pool_args()
        self._reject_pool_args()

    def _run_traffic(self, expected_server, headers=None):
        print('##################')
        print('##################')
        print('making request to {}'.format(self.vip_ip))
        import time
        time.sleep(5)
        contents = None
        if headers:
            request = urllib2.Request(
                "http://{}".format(self.vip_ip), headers=headers)
            contents = urllib2.urlopen(request).read()
        else:
            contents = urllib2.urlopen("http://{}".format(self.vip_ip)).read()
        print('Expected_server: {}'.format(expected_server))
        print('Return server: {}'.format(contents))
        assert expected_server in contents

    def test_policy_deployment(self):
        '''Policy without rule will have no effect.'''

        self._run_traffic('server1')
        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        self._run_traffic('server1')

    def test_policy_redirect_pool_header_equal_to(self):
        '''Redirect to pool when header seen with value equal to.'''

        self.l7policy = self._create_l7policy(**self.redirect_pool_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'EQUAL_TO',
                     'key': 'X-HEADER', 'value': 'yes'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', headers={'X-HEADER': 'yes'})

    def test_policy_redirect_pool_cookie_contains(self):
        '''Redirect to pool when cookie contains value.'''

        self.l7policy = self._create_l7policy(**self._redirect_pool_args)
        rule_args = {'type': 'COOKIE', 'compare_type': 'CONTAINS',
                     'key': 'TEST_COOKIE', 'value': 'cookie_value'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self._run_traffic('server1')
        self._run_traffic('server2', headers={'Cookie': 'TEST_COOKIE=value'})

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
        import time
        print('###########')
        print(type(ex))
        print(ex)
        time.sleep(5)
        assert 'test' in ex.value.message

    def test_policy_redirect_url_hostname_ends_with(self):
        '''Redirect traffic to url when hostname ends with value.'''

        self.l7policy = self._create_l7policy(**self.redirect_url_args)
        #rule_args = {'type': 'REDIRECT_TO_URL'
