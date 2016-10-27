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
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base


CONF = config.CONF


class ServiceBuilderTestJSON(base.BaseTestCase):
    """F5 driver service builder tests."""

    @classmethod
    def resource_setup(cls):
        super(ServiceBuilderTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('lbaasv2', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        cls.subnet = cls.get_tenant_network()

        cls.network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(cls.network_name)
        cls.subnet = cls.create_subnet(cls.network)
        cls.create_lb_kwargs = {'tenant_id': cls.subnet['tenant_id'],
                                'vip_subnet_id': cls.subnet['id']}

        cls.load_balancer = \
            cls._create_active_load_balancer(**cls.create_lb_kwargs)
        cls.load_balancer_id = cls.load_balancer['id']

        # create listener
        cls.create_listener_kwargs = {'loadbalancer_id': cls.load_balancer_id,
                                      'protocol': 'HTTP',
                                      'protocol_port': 80}
        cls.listener = (
            cls._create_listener(**cls.create_listener_kwargs))
        cls.listener_id = cls.listener['id']

        # create pool for listener
        cls.create_pool_kwargs = {'listener_id': cls.listener_id,
                                  'protocol': 'HTTP',
                                  'description': 'ATTACHED pool',
                                  'lb_algorithm': 'ROUND_ROBIN'}
        cls.pool = (
            cls._create_pool(**cls.create_pool_kwargs))
        cls.pool_id = cls.pool['id']

        # create member
        cls.create_member_kwargs = {'address': '10.2.2.3',
                                    'protocol_port': 8080,
                                    'subnet_id': cls.subnet['id']}
        cls.member = (
            cls._create_member(cls.pool_id, **cls.create_member_kwargs))

        cls.create_monitor_kwargs = {'pool_id': cls.pool_id,
                                     'type': 'HTTP',
                                     'delay': 1,
                                     'timeout': 1,
                                     'max_retries': 5}

        # get an RPC client for calling into driver
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @classmethod
    def resource_cleanup(cls):
        super(ServiceBuilderTestJSON, cls).resource_cleanup()

    def check_service_object(self):
        # get service object from driver
        res = self.client.call(self.context, "get_service_by_loadbalancer_id",
                               loadbalancer_id=self.load_balancer_id)

        # loadbalancer
        self.assertEqual(self.load_balancer_id,
                         res['loadbalancer']['id'],
                         message="Invalid loadbalancer ID")

        # listeners
        self.assertEqual(1,
                         len(res['listeners']),
                         message="Expected 1 listener.")
        self.check_lbaas_object(res['listeners'][0],
                                self.create_listener_kwargs)

        # check attached pool
        self.assertEqual(1,
                         len(res['pools']),
                         message="Expected 1 pool.")
        self.check_lbaas_object(
            self.find_object(self.pool_id, res['pools']),
            self.create_pool_kwargs)

        # members
        self.assertEqual(1,
                         len(res['members']),
                         message="Expected 1 member.")

        # subnets
        self.assertIsNotNone(res['subnets'],
                             message="Expected subnets in service object.")

        # networks
        self.assertIsNotNone(res['networks'],
                             message="Expected networks in service object.")

    def check_lbaas_object(self, lbaas_obj, kwargs):
        for key in kwargs:
            # skip args like 'loadbalancer_id'
            if "_id" not in key:
                self.assertIn(key,
                              lbaas_obj,
                              message="Excpected key {0} in object.".format(
                                  key))
                self.assertEqual(kwargs[key],
                                 lbaas_obj[key],
                                 message="Expected value {0} for key {1}".
                                 format(kwargs[key], key))

    def find_object(self, id, list):
        for obj in list:
            if obj['id'] == id:
                return obj
        return None

    @test.attr(type='smoke')
    def test_service_builder(self):

        self._create_health_monitor(**self.create_monitor_kwargs)
        self.check_service_object()
