# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2016 Rackspace Inc.
# Copyright 2017 F5 Networks
# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import pytest


from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base

CONF = config.CONF


class CommonNetworks(base.F5BaseTestCase):
    """Test that f5_common_networks performs proper behavior"""
    timeout_for_agent_start = 5
    agent_ini_file = "/etc/neutron/services/f5/f5-openstack-agent.ini"

    @classmethod
    def resource_setup(cls):
        super(CommonNetworks, cls).resource_setup()
        cls.__re_init_agent(True)
        if not test.is_extension_enabled('lbaas', 'network'):
            msg = "lbaas extension not enabled!"
            raise cls.resource_setupskipException(msg)
        network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(network_name)
        cls.subnet = cls.create_subnet(cls.network)

        cls.create_lb_kwargs = {'tenant_id': cls.subnet['tenant_id'],
                                'vip_subnet_id': cls.subnet['id']}
        cls.load_balancer = \
            cls._create_active_load_balancer(**cls.create_lb_kwargs)
        cls.load_balancer_id = cls.load_balancer['id']

        # create listener
        listener_kwargs = {'loadbalancer_id': cls.load_balancer_id,
                           'protocol': 'HTTP',
                           'protocol_port': 80}
        cls.listener = cls._create_listener(**listener_kwargs)
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    def __re_init_agent(cls, f5_common_networks):
        """Performs action to modify the agent config

        This is a no-opt that is to be filled in on just how things will
        interact with the agent
        """
        pass

    @classmethod
    def resource_cleanup(cls):
        super(CommonNetworks, cls).resource_cleanup()
        cls.__re_init_agent(False)

    def construct_and_clean(cls, kw_args, construct_method, delete_method,
                            cleanup_args=None):
        obj = construct_method(**kw_args)
        args = [delete_method, obj.get('id')]
        if cleanup_args:
            # less costly than a splice...
            args = [delete_method]
            args.extend(cleanup_args)
            args.append(obj.get('id'))
        cls.addCleanup(*args)

    @pytest.mark.skip(reason="RBAC and dynamic agent not implemented yet")
    def test_common_networks(self):
        # create pool
        pool_wkargs = dict(listener_id=self.listener['id'],
                           protocol='HTTP',
                           lb_algorithm='ROUND_ROBIN')
        pool = self.construct_and_clean(pool_wkargs, self._create_pool,
                                        self._delete_pool)
        # add ping monitor
        monitor_kwargs = dict(pool_id=pool['id'], type='PING', delay=1,
                              timeout=1, max_retries=5)
        self.construct_and_clean(monitor_kwargs, self._create_health_monitor,
                                 self._delete_health_monitor)
        # create member:
        allocation_pool = self.subnet['allocation_pools'][0]
        member_kwargs = dict(pool_id=pool['id'], protocol_port=8080,
                             address=allocation_pool['start'],
                             subnet_id=self.subnet['id'])
        member = self.construct_and_clean(member_kwargs, self._create_member,
                                          self._delete_member,
                                          cleanup_args=[pool.get('id')])
        assert self._wait_for_member_status(member, 'ONLINE') == 'ONLINE'
        assert 'Common' in self.load_balancer['id']
        assert 'Common' in self.network
