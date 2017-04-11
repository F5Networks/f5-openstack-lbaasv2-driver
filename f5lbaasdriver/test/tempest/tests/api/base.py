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

import time

from oslo_log import log as logging
from tempest.api.network import base
from tempest import config
from tempest.lib import exceptions

from f5lbaasdriver.test.tempest.services.clients import \
    l7policy_client
from f5lbaasdriver.test.tempest.services.clients import \
    l7rule_client
from f5lbaasdriver.test.tempest.services.clients import \
    plugin_rpc_client
from neutron_lbaas.tests.tempest.v2.clients import \
    health_monitors_client
from neutron_lbaas.tests.tempest.v2.clients import listeners_client
from neutron_lbaas.tests.tempest.v2.clients import \
    load_balancers_client
from neutron_lbaas.tests.tempest.v2.clients import members_client
from neutron_lbaas.tests.tempest.v2.clients import pools_client

from f5lbaasdriver.test.tempest.services.clients import \
    bigip_client

CONF = config.CONF

LOG = logging.getLogger(__name__)


def _setup_client_args(auth_provider):
    """Set up ServiceClient arguments using config settings."""
    service = CONF.network.catalog_type or 'network'
    region = CONF.network.region or 'regionOne'
    endpoint_type = CONF.network.endpoint_type
    build_interval = CONF.network.build_interval
    build_timeout = CONF.network.build_timeout

    # The disable_ssl appears in identity
    disable_ssl_certificate_validation = (
        CONF.identity.disable_ssl_certificate_validation)
    ca_certs = None

    # Trace in debug section
    trace_requests = CONF.debug.trace_requests

    return [auth_provider, service, region, endpoint_type,
            build_interval, build_timeout,
            disable_ssl_certificate_validation, ca_certs,
            trace_requests]


class BaseTestCase(base.BaseNetworkTest):
    """This class picks non-admin credentials and run the tempest tests."""

    _lbs_to_delete = []

    @classmethod
    def resource_setup(cls):
        """Setup the clients and fixtures for test suite."""
        super(BaseTestCase, cls).resource_setup()

        mgr = cls.get_client_manager()
        auth_provider = mgr.auth_provider
        client_args = _setup_client_args(auth_provider)

        cls.bigip_client = bigip_client.BigIpClient()
        cls.load_balancers_client = (
            load_balancers_client.LoadBalancersClientJSON(*client_args))
        cls.listeners_client = (
            listeners_client.ListenersClientJSON(*client_args))
        cls.pools_client = pools_client.PoolsClientJSON(*client_args)
        cls.members_client = members_client.MembersClientJSON(*client_args)
        cls.health_monitors_client = (
            health_monitors_client.HealthMonitorsClientJSON(*client_args))
        cls.l7policy_client = (
            l7policy_client.L7PolicyClientJSON(*client_args))
        cls.l7rule_client = (
            l7rule_client.L7RuleClientJSON(*client_args))
        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )

    @classmethod
    def resource_cleanup(cls):
        """Cleanup the remaining objects from the test run."""
        for lb_id in cls._lbs_to_delete:
            try:
                lb = cls.load_balancers_client.get_load_balancer_status_tree(
                    lb_id).get('loadbalancer')
            except exceptions.NotFound:
                continue
            for listener in lb.get('listeners'):
                for pool in listener.get('pools'):
                    hm = pool.get('healthmonitor')
                    if hm:
                        cls._try_delete_resource(
                            cls.health_monitors_client.delete_health_monitor,
                            pool.get('healthmonitor').get('id'))
                        cls._wait_for_load_balancer_status(lb_id)
                    cls._try_delete_resource(cls.pools_client.delete_pool,
                                             pool.get('id'))
                    cls._wait_for_load_balancer_status(lb_id)
                for l7policy in listener.get('l7policies'):
                    for rule in l7policy.get('rules'):
                        cls._try_delete_resource(
                            cls.l7rule_client.delete_l7rule,
                            l7policy.get('id'), rule.get('id'))
                    cls._try_delete_resource(
                        cls.l7policy_client.delete_l7policy,
                        l7policy.get('id'))
                cls._try_delete_resource(cls.listeners_client.delete_listener,
                                         listener.get('id'))
                cls._wait_for_load_balancer_status(lb_id)
            cls._try_delete_resource(cls._delete_load_balancer, lb_id)
        # Wait for VIP port to be deleted
        for vip_port in cls.vip_ports:
            port_deleted = False
            for i in range(20):
                if cls.ports_client.is_resource_deleted(vip_port['id']):
                    port_deleted = True
                    break
                time.sleep(1)
            if port_deleted is False:
                raise AssertionError(
                    'VIP port {} not deleted by loadbalancer'.format(
                        vip_port['id']))

        # Loadbalancer is gone, so folder on device should be gone too
        assert not cls.bigip_client.folder_exists(
            'Project_' + cls.subnet['tenant_id'])
        super(BaseTestCase, cls).resource_cleanup()

    @classmethod
    def _try_delete_resource(cls, delete_callable, *args, **kwargs):
        """Cleanup resources in case of test-failure.

        Some resources are explicitly deleted by the test.
        If the test failed to delete a resource, this method will execute
        the appropriate delete methods. Otherwise, the method ignores NotFound
        exceptions thrown for resources that were correctly deleted by the
        test.

        :param delete_callable: delete method
        :param args: arguments for delete method
        :param kwargs: keyword arguments for delete method
        """
        try:
            delete_callable(*args, **kwargs)
        # if resource is not found, this means it was deleted in the test
        except exceptions.NotFound:
            pass

    @classmethod
    def setUpClass(cls):
        cls.LOG = logging.getLogger(cls._get_full_case_name())
        cls.vip_ports = []
        super(BaseTestCase, cls).setUpClass()

    def setUp(cls):
        cls.LOG.info(('Starting: {0}').format(cls._testMethodName))
        super(BaseTestCase, cls).setUp()

    def tearDown(cls):
        super(BaseTestCase, cls).tearDown()
        cls.LOG.info(('Finished: {0}\n').format(cls._testMethodName))

    @classmethod
    def _create_load_balancer(cls, wait=True, **lb_kwargs):
        lb = cls.load_balancers_client.create_load_balancer(**lb_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(lb.get('id'))

        cls._lbs_to_delete.append(lb.get('id'))
        # Due to a possible race betwen the test port teardown and the lb
        # delete in neutron-lbaas, the test should not tear down the VIP port.
        port = cls.ports_client.show_port(lb['vip_port_id'])
        cls.vip_ports.append(port['port'])
        return lb

    @classmethod
    def _create_active_load_balancer(cls, **kwargs):
        lb = cls._create_load_balancer(**kwargs)
        lb = cls._wait_for_load_balancer_status(lb.get('id'))
        return lb

    @classmethod
    def _delete_load_balancer(cls, load_balancer_id, wait=True):
        cls.load_balancers_client.delete_load_balancer(load_balancer_id)
        if wait:
            cls._wait_for_load_balancer_status(
                load_balancer_id, delete=True)

    @classmethod
    def _update_load_balancer(cls, load_balancer_id, wait=True, **lb_kwargs):
        lb = cls.load_balancers_client.update_load_balancer(
            load_balancer_id, **lb_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(
                load_balancer_id)
        return lb

    @classmethod
    def _wait_for_load_balancer_status(cls, load_balancer_id,
                                       provisioning_status='ACTIVE',
                                       operating_status='ONLINE',
                                       delete=False):
        interval_time = 1
        timeout = 60
        end_time = time.time() + timeout
        lb = {}
        while time.time() < end_time:
            try:
                lb = cls.load_balancers_client.get_load_balancer(
                    load_balancer_id)
                if not lb:
                        # loadbalancer not found
                    if delete:
                        break
                    else:
                        raise Exception(
                            ("loadbalancer {lb_id} not"
                             " found").format(
                                 lb_id=load_balancer_id))
                if (lb.get('provisioning_status') == provisioning_status and
                        lb.get('operating_status') == operating_status):
                    break
                time.sleep(interval_time)
            except exceptions.NotFound as e:
                # if wait is for delete operation do break
                if delete:
                    break
                else:
                    # raise original exception
                    raise e
        else:
            if delete:
                raise exceptions.TimeoutException(
                    ("Waited for load balancer {lb_id} to be deleted for "
                     "{timeout} seconds but can still observe that it "
                     "exists.").format(
                         lb_id=load_balancer_id,
                         timeout=timeout))
            else:
                raise exceptions.TimeoutException(
                    ("Wait for load balancer ran for {timeout} seconds and "
                     "did not observe {lb_id} reach {provisioning_status} "
                     "provisioning status and {operating_status} "
                     "operating status.").format(
                         timeout=timeout,
                         lb_id=load_balancer_id,
                         provisioning_status=provisioning_status,
                         operating_status=operating_status))
        return lb

    @classmethod
    def _create_listener(cls, wait=True, **listener_kwargs):
        listener = cls.listeners_client.create_listener(**listener_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))
        return listener

    @classmethod
    def _delete_listener(cls, listener_id, wait=True):
        cls.listeners_client.delete_listener(listener_id)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))

    @classmethod
    def _update_listener(cls, listener_id, wait=True, **listener_kwargs):
        listener = cls.listeners_client.update_listener(
            listener_id, **listener_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(
                cls.load_balancer.get('id'))
        return listener

    @classmethod
    def _create_pool(cls, wait=True, **pool_kwargs):
        pool = cls.pools_client.create_pool(**pool_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))
        return pool

    @classmethod
    def _delete_pool(cls, pool_id, wait=True):
        cls.pools_client.delete_pool(pool_id)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))

    @classmethod
    def _update_pool(cls, pool_id, wait=True, **pool_kwargs):
        pool = cls.pools_client.update_pool(pool_id, **pool_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(
                cls.load_balancer.get('id'))
        return pool

    def _create_health_monitor(self, wait=True, cleanup=True,
                               **health_monitor_kwargs):
        hm = self.health_monitors_client.create_health_monitor(
            **health_monitor_kwargs)
        if cleanup:
            self.addCleanup(self._delete_health_monitor, hm.get('id'))
        if wait:
            self._wait_for_load_balancer_status(self.load_balancer.get('id'))
        return hm

    def _delete_health_monitor(self, health_monitor_id, wait=True):
        self.health_monitors_client.delete_health_monitor(health_monitor_id)
        if wait:
            self._wait_for_load_balancer_status(self.load_balancer.get('id'))

    def _update_health_monitor(self, health_monitor_id, wait=True,
                               **health_monitor_kwargs):
        health_monitor = self.health_monitors_client.update_health_monitor(
            health_monitor_id, **health_monitor_kwargs)
        if wait:
            self._wait_for_load_balancer_status(
                self.load_balancer.get('id'))
        return health_monitor

    @classmethod
    def _create_member(cls, pool_id, wait=True, **member_kwargs):
        member = cls.members_client.create_member(pool_id, **member_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))
        return member

    @classmethod
    def _delete_member(cls, pool_id, member_id, wait=True):
        cls.members_client.delete_member(pool_id, member_id)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))

    @classmethod
    def _update_member(cls, pool_id, member_id, wait=True,
                       **member_kwargs):
        member = cls.members_client.update_member(
            pool_id, member_id, **member_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(
                cls.load_balancer.get('id'))
        return member

    @classmethod
    def _create_l7policy(cls, wait=True, **l7policy_kwargs):
        l7policy = cls.l7policy_client.create_l7policy(**l7policy_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))
        return l7policy

    @classmethod
    def _delete_l7policy(cls, l7policy_id, wait=True):
        cls.l7policy_client.delete_l7policy(l7policy_id)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))

    @classmethod
    def _update_l7policy(cls, l7policy_id, wait=True, **l7policy_kwargs):
        l7policy = cls.l7policy_client.update_l7policy(
            l7policy_id, **l7policy_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(
                cls.load_balancer.get('id'))
        return l7policy

    @classmethod
    def _create_l7rule(cls, policy_id, wait=True, **l7rule_kwargs):
        l7rule = cls.l7rule_client.create_l7rule(policy_id, **l7rule_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))
        return l7rule

    @classmethod
    def _delete_l7rule(cls, policy_id, l7rule_id, wait=True):
        cls.l7rule_client.delete_l7rule(policy_id, l7rule_id)
        if wait:
            cls._wait_for_load_balancer_status(cls.load_balancer.get('id'))

    @classmethod
    def _update_l7rule(
            cls, l7policy_id, l7rule_id, wait=True, **l7rule_kwargs):
        l7rule = cls.l7rule_client.update_l7rule(
            l7policy_id, l7rule_id, **l7rule_kwargs)
        if wait:
            cls._wait_for_load_balancer_status(
                cls.load_balancer.get('id'))
        return l7rule

    @classmethod
    def _check_status_tree(cls, load_balancer_id, listener_ids=None,
                           pool_ids=None, health_monitor_id=None,
                           member_ids=None):
        statuses = cls.load_balancers_client.get_load_balancer_status_tree(
            load_balancer_id=load_balancer_id)
        load_balancer = statuses['loadbalancer']
        assert 'ONLINE' == load_balancer['operating_status']
        assert 'ACTIVE' == load_balancer['provisioning_status']

        if listener_ids:
            cls._check_status_tree_thing(listener_ids,
                                         load_balancer['listeners'])
        if pool_ids:
            cls._check_status_tree_thing(pool_ids,
                                         load_balancer['listeners']['pools'])
        if member_ids:
            cls._check_status_tree_thing(
                member_ids,
                load_balancer['listeners']['pools']['members'])
        if health_monitor_id:
            health_monitor = (
                load_balancer['listeners']['pools']['health_monitor'])
            assert health_monitor_id == health_monitor['id']
            assert 'ACTIVE' == health_monitor['provisioning_status']

    @classmethod
    def _check_status_tree_thing(cls, actual_thing_ids, status_tree_things):
        found_things = 0
        status_tree_things = status_tree_things
        assert len(actual_thing_ids) == len(status_tree_things)
        for actual_thing_id in actual_thing_ids:
            for status_tree_thing in status_tree_things:
                if status_tree_thing['id'] == actual_thing_id:
                    assert 'ONLINE' == (
                        status_tree_thing['operating_status'])
                    assert 'ACTIVE' == (
                        status_tree_thing['provisioning_status'])
                    found_things += 1
        assert len(actual_thing_ids) == found_things

    @classmethod
    def _get_full_case_name(cls):
        name = '{module}:{case_name}'.format(
            module=cls.__module__,
            case_name=cls.__name__
        )
        return name


class BaseAdminTestCase(BaseTestCase):
    """This class picks admin credentials and run the tempest tests."""

    @classmethod
    def resource_setup(cls):
        """Initialize the client objects."""
        super(BaseAdminTestCase, cls).resource_setup()

        mgr = cls.get_client_manager(credential_type='admin')
        auth_provider_admin = mgr.auth_provider
        client_args = _setup_client_args(auth_provider_admin)

        cls.bigip_client = bigip_client.BigIpClient()
        cls.load_balancers_client = (
            load_balancers_client.LoadBalancersClientJSON(*client_args))
        cls.listeners_client = (
            listeners_client.ListenersClientJSON(*client_args))
        cls.pools_client = (
            pools_client.PoolsClientJSON(*client_args))
        cls.members_client = (
            members_client.MembersClientJSON(*client_args))
        cls.health_monitors_client = (
            health_monitors_client.HealthMonitorsClientJSON(*client_args))

    @classmethod
    def resource_cleanup(cls):
        """Call BaseTestCase.resource_cleanup."""
        super(BaseAdminTestCase, cls).resource_cleanup()
