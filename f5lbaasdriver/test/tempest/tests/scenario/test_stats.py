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

import pprint
import requests
import time

from neutron_lbaas.tests.tempest.v2.scenario import base
from tempest import config

config = config.CONF


class F5StatsBaseTestCase(base.BaseTestCase):

    def setUp(self):
        super(F5StatsBaseTestCase, self).setUp()
        self.tenant_id = self.subnet['tenant_id']
        self.members = {}
        self._create_servers()
        self._start_servers()
        self._create_load_balancer()
        self._create_member(
            self.server_fixed_ips[self.servers['primary']],
            'primary',
            load_balancer_id=self.load_balancer.get('id'),
            pool_id=self.pool.get('id'),
            subnet_id=self.subnet.get('id'))
        self._create_member(
            self.server_fixed_ips[self.servers['secondary']],
            'secondary',
            load_balancer_id=self.load_balancer.get('id'),
            pool_id=self.pool.get('id'),
            subnet_id=self.subnet.get('id'))
        self._wait_for_load_balancer_status(self.load_balancer.get('id'))

    def _create_load_balancer(self, ip_version=4, persistence_type=None):
        self.create_lb_kwargs = {'tenant_id': self.tenant_id,
                                 'vip_subnet_id': self.subnet['id']}
        self.load_balancer = self.load_balancers_client.create_load_balancer(
            **self.create_lb_kwargs)
        load_balancer_id = self.load_balancer['id']
        self.addCleanup(self._cleanup_load_balancer, load_balancer_id)
        self._wait_for_load_balancer_status(load_balancer_id)

        listener = self._create_listener(load_balancer_id=load_balancer_id)
        self._wait_for_load_balancer_status(load_balancer_id)
        self.listener_id = listener.get('id')

        self.pool = self._create_pool(listener_id=listener.get('id'),
                                      persistence_type=persistence_type)
        self._wait_for_load_balancer_status(load_balancer_id)

        # self._create_members(load_balancer_id=load_balancer_id,
        #                     pool_id=self.pool['id'],
        #                     subnet_id=self.subnet['id'])

        self.vip_ip = self.load_balancer.get('vip_address')

        # if the ipv4 is used for lb, then fetch the right values from
        # tempest.conf file
        if ip_version == 4:
            if (config.network.public_network_id and not
                    config.network.project_networks_reachable):
                self._assign_floating_ip_to_lb_vip(self.load_balancer)
                self.vip_ip = self.floating_ips[
                    load_balancer_id][0]['floating_ip_address']

        # Currently the ovs-agent is not enforcing security groups on the
        # vip port - see https://bugs.launchpad.net/neutron/+bug/1163569
        # However the linuxbridge-agent does, and it is necessary to add a
        # security group with a rule that allows tcp port 80 to the vip port.
        self.ports_client.update_port(
            self.load_balancer.get('vip_port_id'),
            security_groups=[self.security_group.get('id')])

    def _create_member(self, server_ip, server_position, load_balancer_id=None,
                       pool_id=None, subnet_id=None):
        """Create two members.

        In case there is only one server, create both members with the same ip
        but with different ports to listen on.
        """

        member = self.members_client.create_member(
            pool_id=pool_id,
            address=server_ip,
            protocol_port=self.port1,
            subnet_id=subnet_id)
        self._wait_for_load_balancer_status(load_balancer_id)
        self.members[server_position] = member
        self.assertTrue(self.members[server_position])

    def _run_traffic(
            self, headers=None, cookies=None, uri_path=None,
            expected_status=200, count=10):

        for x in range(count):
            try:
                if not uri_path:
                    uri_path = 'http://{}'.format(self.vip_ip)
                print('making request to {}'.format(uri_path))
                res = requests.get(uri_path, headers=headers, cookies=cookies)
                assert res.status_code == expected_status
            except Exception:
                time.sleep(1)
                continue

    def _get_stats(self):
        return self.load_balancers_client.get_load_balancer_stats(
            self.load_balancer.get('id'))


class TestLoadBalancerStats(F5StatsBaseTestCase):

    def setUp(self):
        super(TestLoadBalancerStats, self).setUp()

    def test_stats(self):
        request_count = 10  # number of requests to make

        # get initial stats -- should be 0
        before_stats = self._get_stats()
        assert before_stats['active_connections'] == 0
        assert before_stats['bytes_in'] == 0
        assert before_stats['bytes_out'] == 0
        assert before_stats['total_connections'] == 0

        # send traffic through load balancer
        self._run_traffic(count=request_count)

        # Get stats -- may take some time for BIG-IP to update. Try
        # until stats total_connections is equal to number of requests.
        # Bail after 60 seconds.
        for x in range(60):
            after_stats = self._get_stats()
            if after_stats['total_connections'] == request_count:
                break
            time.sleep(1)

        # validate final stats
        assert after_stats['active_connections'] == 0
        assert after_stats['bytes_in'] > 0
        assert after_stats['bytes_out'] > 0
        assert after_stats['total_connections'] == request_count

        print('===Success===')
        print(pprint.pprint(after_stats))
