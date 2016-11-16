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

    @pytest.fixture
    def redirect_pool_args(self):
        return {'listener_id': self.listener.get('id'),
                'admin_state_up': 'true', 'action': 'REDIRECT_TO_POOL',
                'redirect_pool_id': self.detached_pool.get('id')}

    def run_traffic(self, expected_status_code, expected_server, headers=None):
        contents = None
        if headers:
            request = urllib2.Request(
                "http://{}".format(self.vip_ip), headers=headers)
            contents = urllib2.urlopen(request).read()
        else:
            contents = urllib2.urlopen("http://{}".format(self.vip_ip)).read()
        assert expected_server in contents

    def test_policy_deployment(self, redirect_pool_args):
        '''Policy without rule will have no effect.'''
        self.run_traffic(200, 'server1')
        self.l7policy = self._create_l7policy(**redirect_pool_args)
        # Policy without a rule should have no effect
        self.run_traffic(200, 'server1')

    def test_policy_redirect_pool_header_equal_to(self, redirect_pool_args):
        '''Redirect to pool when header seen with value equal to.'''

        self.l7policy = self._create_l7policy(**redirect_pool_args)
        rule_args = {'type': 'HEADER', 'compare_type': 'EQUAL_TO',
                     'key': 'X-HEADER', 'value': 'yes'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self.run_traffic(200, 'server1')
        self.run_traffic(200, 'server2', headers={'X-HEADER': 'yes'})

    def test_policy_redirect_pool_cookie_contains(self, redirect_pool_args):
        '''Redirect to pool when cookie contains value.'''

        self.l7policy = self._create_l7policy(**redirect_pool_args)
        rule_args = {'type': 'COOKIE', 'compare_type': 'CONTAINS',
                     'key': 'TEST_COOKIE', 'value': 'cookie_value'}
        self._create_l7rule(self.l7policy.get('id'), **rule_args)
        self.run_traffic(200, 'server1')
