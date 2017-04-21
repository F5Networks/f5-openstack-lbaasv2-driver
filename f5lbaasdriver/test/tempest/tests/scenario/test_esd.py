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


class TestEsdBasic(f5_base.F5BaseTestCase):
    def SetUp(self):
        super(TestEsdBasic, self).setUp()

    def tearDown(self):
        try:
            self._remove_members()
        except NotFound:
            pass
        super(TestEsdBasic, self).tearDown()

    def _remove_members(self):
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

    def _create_esd(self, esd_name, action='REJECT'):
        self.l7policy_args = {
            'listener_id': self.listener.get('id'),
            'action': action,
            'name': esd_name}

        self.l7policy = self._create_l7policy(**self.l7policy_args)

    def _delete_esd(self):
        self._delete_l7policy(self.l7policy['id'])

    def test_policy_deployment(self):
        self._create_esd('esd_demo_3')
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        self._run_traffic('server1')
        self._delete_esd()
        self._run_traffic('server1')
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))

    def test_policy_abort_deployment(self):
        self._create_esd('esd_demo_1')
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        with pytest.raises(Exception) as ex:
            self._run_traffic('server1')
        assert 'Connection aborted' in str(ex)
        self._delete_esd()
        self._run_traffic('server1')
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))
