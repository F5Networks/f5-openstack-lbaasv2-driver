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

from neutron.plugins.common import constants as plugin_const
from neutron_lbaas.services.loadbalancer import constants as lb_const
from tempest import config
from tempest.lib.common.utils import data_utils
from tempest import test

from f5lbaasdriver.test.tempest.tests.api import base


CONF = config.CONF


class L7PolicyTestJSON(base.BaseTestCase):
    """L7 Policy tempest tests.

    Tests the following operations in the Neutron-LBaaS API using the
    REST client with default credentials:

    1) Creating a L7 policy with REJECT action.
    2) Creating a L7 policy with a REDIRECT_URL action.
    3) Creating a L7 policy with a REDIRECT_POOL action.
    """

    @classmethod
    def resource_setup(cls):
        super(L7PolicyTestJSON, cls).resource_setup()
        if not test.is_extension_enabled('lbaasv2', 'network'):
            msg = "lbaas extension not enabled."
            raise cls.skipException(msg)
        network_name = data_utils.rand_name('network')
        cls.network = cls.create_network(network_name)
        cls.subnet = cls.create_subnet(cls.network)
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

        # Create basic args for policy creation
        cls.create_l7policy_kwargs = {'listener_id': cls.listener_id,
                                      'admin_state_up': "true"}

        # Get a client to emulate the agent's behavior.
        cls.client = cls.plugin_rpc.get_client()
        cls.context = cls.plugin_rpc.get_context()

    @classmethod
    def resource_cleanup(cls):
        super(L7PolicyTestJSON, cls).resource_cleanup()

    def check_policies(self):
        # Check service object has policies we expect
        res = self.client.call(self.context, "get_service_by_loadbalancer_id",
                               loadbalancer_id=self.load_balancer_id)
        assert 'l7policies' in res.keys()
        assert len(res['l7policies']) == 1
        policy = res['l7policies'][0]
        assert policy['listener_id'] == self.listener_id

    def check_agent_calls(self, policy_id):
        # These actions should be performed by the agent.
        self.client.call(self.context, "update_l7policy_status",
                         l7policy_id=policy_id,
                         provisioning_status=plugin_const.ACTIVE)
        self.client.call(self.context, "update_loadbalancer_status",
                         loadbalancer_id=self.load_balancer_id,
                         status=plugin_const.ACTIVE,
                         operating_status=lb_const.ONLINE)

    @test.attr(type='smoke')
    def test_create_l7_reject_policy(self):
        """Test the creationg of a L7 reject policy."""
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REJECT"

        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self.addCleanup(self._delete_l7policy, new_policy['id'])
        assert(new_policy['action'] == "REJECT")

        self.check_policies()
        self.check_agent_calls(new_policy['id'])

    @test.attr(type='smoke')
    def test_create_l7_redirect_to_url_policy(self):
        """Test the creationg of a L7 URL redirect policy."""
        redirect_url = "http://www.mysite.com/my-widget-app"
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REDIRECT_TO_URL"
        create_l7policy_kwargs['redirect_url'] = redirect_url

        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self.addCleanup(self._delete_l7policy, new_policy['id'])
        assert(new_policy['action'] == "REDIRECT_TO_URL")
        assert(new_policy['redirect_url'] == redirect_url)

        self.check_policies()
        self.check_agent_calls(new_policy['id'])

    @test.attr(type='smoke')
    def test_create_l7_redirect_to_pool_policy(self):
        """Test the creationg of a L7 pool redirect policy."""
        create_l7policy_kwargs = self.create_l7policy_kwargs
        create_l7policy_kwargs['action'] = "REDIRECT_TO_POOL"
        create_l7policy_kwargs['redirect_pool_id'] = self.pool_id

        new_policy = self._create_l7policy(
            **create_l7policy_kwargs)
        self.addCleanup(self._delete_l7policy, new_policy['id'])
        assert(new_policy['action'] == "REDIRECT_TO_POOL")
        assert(new_policy['redirect_pool_id'] == self.pool_id)

        self.check_policies()
        self.check_agent_calls(new_policy['id'])
