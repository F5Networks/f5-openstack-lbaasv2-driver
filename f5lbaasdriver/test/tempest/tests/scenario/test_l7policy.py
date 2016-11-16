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

import urllib2


class TestL7PolicyBasic(f5_base.F5BaseTestCase):
    '''Testing L7Policies deployed to BIG-IP device.'''

    def run_traffic(self, expected_status_code, expected_server):
        import time
        print('sleeping')
        time.sleep(30)
        resp = urllib2.urlopen('http://{}'.format(self.vip_ip))
        # assert resp.code == expected_status_code
        assert expected_server in resp.read()

    def test_policy_deployment(self):
        pol_args = {'listener_id': self.listener.get('id'),
                    'admin_state_up': 'true', 'action': 'REDIRECT_TO_POOL',
                    'redirect_pool_id': self.detached_pool.get('id')}
        self.run_traffic(200, 'server1')
        self.l7policy = self._create_l7policy(**pol_args)
        self.run_traffic(200, 'server2')
