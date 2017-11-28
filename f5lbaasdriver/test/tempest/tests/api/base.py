# Copyright 2015, 2016 Rackspace Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from collections import namedtuple
from collections import deque

from neutron_lbaas.tests.tempest.v2.api import base
from oslo_log import log as logging
from tempest import config
from tempest.lib.common.utils import data_utils

from f5lbaasdriver.test.tempest.services.clients.bigip_client \
    import BigIpClient
from f5lbaasdriver.test.tempest.services.clients import \
    plugin_rpc_client
from f5lbaasdriver.test.tempest.tests.api.bigip_interaction import \
    BigIpInteraction

CONF = config.CONF

LOG = logging.getLogger(__name__)


class F5BaseTestCaseBuilder(object):
    """This class will share many operations between base classes for F5

    This class methodology offers an abstraction to tests that allow callers
    to transparently provide themselves with a instantiated means to
    orchestrate themselves in a way that does not impact other tests.

    By using this class  the caller will clean up after yourself implicitely
    via automation during setUp() and tearDown() methods.
    """
    TearDown = namedtuple('TearDown', 'obj, delete_method, delete_args')
    # Note, setUp and tearDown SHOULD NOT be added to this class!

    @property
    def __testname__(self):
        name = str(self.__class__).replace("<class '", "")
        name = name.replace("'>", '::')
        name += self.__name__
        return name

    def _find_loadbalancer(self, **kwargs):
        """Will find a LB object by the name 'load_balancer' or 'loadbalancer'

        This method will do its best to find the stored lb object at either the
        class level, inherited, neutorn-lbaas level, or at the instance level.
        If not lb object can be found, this method will raise a ValueError.

        The last attempt will be the string 'loadbalancer_id' in the kwargs
        passed (usually, but not always provided in a create or update).
        """
        lb_id = kwargs.get('loadbalancer_id', None)
        if hasattr(self, 'load_balancer') or hasattr(self, 'loadbalancer'):
            return \
                getattr(self, 'loadbalancer', getattr(self, 'load_balancer'))
        elif hasattr(self.__class__, 'load_balancer') or \
                hasattr(self.__class__, 'loadbalancer'):
            cls = self.__class__
            return getattr(cls, 'loadbalancer', getattr(cls, 'load_balancer'))
        elif hasattr(base.BaseTestCase, 'load_balancer') or \
                hasattr(base.BaseTestCase, 'loadbalancer'):
            return \
                getattr(base.BaseTestCase, 'load_balancer',
                        getattr(base.BaseTestCase, 'loadbalancer'))
        elif lb_id:
            return lb_id
        raise ValueError("Cannot perform action without a "
                         "specified loadbalancer")

    def _not_implemented(self, method_call):
        raise NotImplementedError(
            "'{}' is not implemented in '{}'".format(
                method_call, self.__class__))

    # ABC methods:
    def _create_listener(self, *args, **kwargs):
        self._not_implemented(self._create_listener)

    def _create_loadbalancer(self, *args, **kwargs):
        self._not_implemented(self._create_loadbalancer)

    def _create_load_balancer(self, *args, **kwargs):
        self._not_implemented(self._create_load_balancer)

    def _create_pool(self, *args, **kwargs):
        self._not_implemented(self._create_pool)

    def _delete_loadbalancer(self, *args, **kwargs):
        self._not_implemented(self._delete_loadbalancer)

    def _delete_load_balancer(self, *args, **kwargs):
        self._not_implemented(self._delete_load_balancer)

    def _delete_listener(self, *args, **kwargs):
        self._not_implemented(self._delete_listener)

    def _create_pool(self, *args, **kwargs):
        self._not_implemented(self._create_pool)

    def _delete_pool(self, *args, **kwargs):
        self._not_implemented(self._delete_pool)

    def _create_l7policy(self, *args, **kwargs):
        self._not_implemented(self._create_l7policy)

    def _delete_l7policy(self, *args, **kwargs):
        self._not_implemented(self._delete_l7policy)

    def _update_l7policy(self, *args, **kwargs):
        self._not_implemented(self._update_l7policy)

    def _create_l7rule(self, *args, **kwargs):
        self._not_implemented(self._create_l7rule)

    def _delete_l7rule(self, *args, **kwargs):
        self._not_implemented(self._delete_l7rule)

    def _update_l7rule(self, *args, **kwargs):
        self._not_implemented(self._update_l7rule)

    # Instantiated methods...
    def construct_setup(self):
        BigIpInteraction.store_existing()
        self.teardown_que = deque()

    def create_l7rule(
            self, policy_id, loadbalancer=None, **kwargs):
        my_l7rule = self.l7rule_client.create_l7rule(policy_id, **kwargs)
        self.teardown_que.appendleft(
            self.TearDown(
                my_l7rule, self.delete_l7rule, [loadbalancer]))
        self.wait_for_lb(loadbalancer.get('id'))
        return my_l7rule

    def delete_l7rule(self, policy_id, rule_id, loadbalancer=None):
        import pdb
        pdb.set_trace()
        print("foul play!")
        self.l7rule_client.delete_l7rule(policy_id, rule_id)
        self.wait_for_lb(loadbalancer)

    def update_l7rule(self, policy_id, rule_id, loadbalancer=None, **kwargs):
        self.l7rule_client.update_l7rule(policy_id, rule_id, **kwargs)
        self.wait_for_lb(loadbalancer)

    def create_l7policy(
            self, loadbalancer=None, **kwargs):
        my_l7policy = self.l7policy_client.create_l7policy(**kwargs)
        self.teardown_que.appendleft(
            self.TearDown(
                my_l7policy, self.delete_l7policy, [loadbalancer]))
        self.wait_for_lb(loadbalancer.get('id'))
        return my_l7policy

    def delete_l7policy(self, li_id, loadbalancer=None):
        self.l7policy_client.delete_l7policy(li_id)
        self.wait_for_lb(loadbalancer)

    def update_l7policy(self, li_id, loadbalancer=None, **kwargs):
        self.l7policy_client.update_l7policy(li_id, **kwargs)
        self.wait_for_lb(loadbalancer)

    def create_listener(
            self, loadbalancer=None, **kwargs):
        my_listener = self.listeners_client.create_listener(**kwargs)
        self.teardown_que.appendleft(
            self.TearDown(
                my_listener, self.delete_listener, [loadbalancer]))
        self.wait_for_lb(loadbalancer.get('id'))
        return my_listener

    def delete_listener(self, li_id, loadbalancer=None):
        self.listeners_client.delete_listener(li_id)
        self.wait_for_lb(loadbalancer)

    def update_listener(self, li_id, loadbalancer=None, **kwargs):
        self.listeners_client.update_listener(li_id, **kwargs)
        self.wait_for_lb(loadbalancer)

    def create_loadbalancer(self, **kwargs):
        my_loadbalancer = \
            self.load_balancers_client.create_load_balancer(**kwargs)
        teardown = self.TearDown(my_loadbalancer, self.delete_loadbalancer, [])
        self.teardown_que.appendleft(teardown)
        self.wait_for_lb(my_loadbalancer)
        return my_loadbalancer

    def delete_loadbalancer(self, my_id, *args):
        self.load_balancers_client.delete_load_balancer(my_id)
        self.wait_for_lb(my_id, delete=True)

    def update_loadbalancer(self, loadbalancer, **kwargs):
        lb_id = loadbalancer
        if hasattr('get', loadbalancer):
            lb_id = loadbalancer.get('id')
        updated_lb = self.load_balancers_client.update_load_balancer(
            lb_id, **kwargs)
        self.wait_for_lb(loadbalancer)
        return updated_lb

    def rand_name(self, name=None, name_type='network'):
        if not name:
            name = \
                data_utils.rand_name(
                    '{}_{}'.format(self.__name__, name_type))
        return name

    def create_network(self, network_name=None):
        network_name = self.rand_name(network_name)
        my_network = self.create_network(network_name=network_name)
        base.teardown_que.appendleft(
            self.TearDown(base.network_client.delete_network, []))
        return my_network

    def delete_network(self, network_name):
        self.client.delete_network(network_name)

    def create_pool(self, loadbalancer=None, **kwargs):
        my_pool = self.pools_client.create_pool(**kwargs)
        self.teardown_que.appendleft(
            self.TearDown(
                my_pool, self.delete_pool, [loadbalancer]))
        self.wait_for_lb(loadbalancer)
        return my_pool

    def delete_pool(self, my_id, loadbalancer=None):
        self.pools_client.delete_pool(my_id)
        self.wait_for_lb(loadbalancer)

    def update_pool(self, my_id, loadbalancer=None, **kwargs):
        updated_pool = self.pools_client.update_pool(my_id, **kwargs)
        self.wait_for_lb(loadbalancer)
        return updated_pool

    def create_shared_network(self, network_name=None, **kwargs):
        network_name = self.rand_name(network_name)
        network = super(F5BaseTestCaseBuilder, self).create_shared_network(
            network_name=network_name, **kwargs)
        return network

    def create_subnet(self, *args, **kwargs):
        subnet = \
            super(F5BaseTestCaseBuilder, self).create_subnet(*args, **kwargs)
        return subnet

    def delete_subnet(self, subnet_id):
        self.client.delete_subnet(subnet_id)

    def create_subnetpool(self, name, **kwargs):
        name = self.rand_name(name, 'subnetpool')
        subnetpool = \
            super(F5BaseTestCaseBuilder, self).create_subnet_pool(
                name, **kwargs)
        return subnetpool

    def delete_subnetpool(self, subnet_id):
        self.client.delete_subnetpool(subnet_id)

    def wait_for_lb(self, loadbalancer, **kwargs):
        if not loadbalancer:
            loadbalancer = self._find_loadbalancer(**kwargs)
        lb_id = loadbalancer
        if hasattr(loadbalancer, 'get'):
            lb_id = loadbalancer.get('id')
        self._wait_for_load_balancer_status(lb_id, **kwargs)


class F5BaseTestCase(base.BaseTestCase, F5BaseTestCaseBuilder):
    """This class picks non-admin credentials and run the tempest tests."""

    _lbs_to_delete = []

    @classmethod
    def resource_setup(cls):
        """Setup the clients and fixtures for test suite.

        When testing BIG-IP clusters, CONF.f5_lbaasv2_driver.icontrol_hostname
        will be a comma delimited string of IP addresses. A list of clients is
        created, and test writers should iterate the list when validating
        BIG-IP operations. Test writers can choose to reference a single
        BIG-IP using self.bigip_client, which points to the client created
        with the first address in CONF.f5_lbaasv2_driver.icontrol_hostname.
        """
        super(F5BaseTestCase, cls).resource_setup()
        BigIpInteraction.store_config()

        cls.bigip_clients = []
        for host in CONF.f5_lbaasv2_driver.icontrol_hostname.split(","):
            cls.bigip_clients.append(BigIpClient(
                host,
                CONF.f5_lbaasv2_driver.icontrol_username,
                CONF.f5_lbaasv2_driver.icontrol_password))
        cls.bigip_client = cls.bigip_clients[0]

        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )

    def setUp(self):
        """Performs basic setup operations for inheriting test classes"""
        self.construct_setup()
        super(F5BaseTestCase, self).setUp()

    def tearDown(self):
        """Performs basic teardown operations for inheriting test classes"""
        for item in self.teardown_que:
            item.delete_method(item.obj.get('id'), *item.delete_args)
        BigIpInteraction.check_resulting_cfg(self.__name__)
        super(F5BaseTestCase, self).tearDown()


class F5BaseAdminTestCase(base.BaseTestCase, F5BaseTestCaseBuilder):
    """This class picks admin credentials and run the tempest tests."""

    @classmethod
    def resource_setup(cls):
        """Initialize the client objects."""
        super(F5BaseAdminTestCase, cls).resource_setup()
        BigIpInteraction.store_config()
        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )

    def setUp(self):
        """Performs basic setup operation for inheriting test classes"""
        self.construct_setup()
        super(F5BaseAdminTestCase, self).setUp()

    def tearDown(self):
        """Performs basic teardown operation for inheriting test classes"""
        BigIpInteraction.check_resulting_cfg(self.__name__)
        super(F5BaseAdminTestCase, self).tearDown()
