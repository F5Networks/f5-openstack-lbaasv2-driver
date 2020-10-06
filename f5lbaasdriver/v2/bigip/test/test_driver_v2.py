# Copyright 2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import mock
import pytest

import f5lbaasdriver.v2.bigip.driver_v2 as dv2
from f5lbaasdriver.v2.bigip import exceptions as f5_exc

from neutron_lbaas.db.loadbalancer import models
from neutron_lbaas.extensions import lbaas_agentschedulerv2


class FakeNoEligibleAgentExc(lbaas_agentschedulerv2.NoEligibleLbaasAgent):
    msg = 'test exception'


class FakeLB(object):
    def __init__(self, id='test_lb_id', tenant_id='test-tenant-id'):
        self.id = id
        self.tenant_id = tenant_id
        self.vip_port_id = 'test_vip_port_id'

    def to_api_dict(self):
        return self.__dict__


class FakeBaseObj(object):
    def __init__(self, id='test_obj_id', attached_to_lb=True):
        self.id = id
        self.attached_to_lb = attached_to_lb

    def attached_to_loadbalancer(self):
        return self.attached_to_lb

    def to_dict(self, **kwargs):
        return self.__dict__


class FakeListener(FakeBaseObj):
    def __init__(self, id='test_obj_id', attached_to_lb=True):
        super(FakeListener, self).__init__(
            id=id, attached_to_lb=attached_to_lb)
        self.id = id
        self.loadbalancer = FakeLB()


class FakePool(FakeBaseObj):
    def __init__(self, id='test_pool_id', attached_to_lb=True):
        super(FakePool, self).__init__(id=id, attached_to_lb=attached_to_lb)
        self.provisioning_status = 'good'
        self.operating_status = 'really_good'
        self.loadbalancer = FakeLB()

    def to_api_dict(self):
        return self.__dict__


class FakeMember(FakeBaseObj):
    def __init__(
        self, id='test_obj_id', attached_to_lb=True,
        subnet_id='test_sub_id', admin_state_up='test_state'
    ):
        super(FakeMember, self).__init__(id=id, attached_to_lb=attached_to_lb)
        self.id = id
        self.pool = FakePool()
        self.subnet_id = subnet_id
        self.admin_state_up = admin_state_up


class FakeHM(FakeBaseObj):
    def __init__(self, id='test_obj_id', attached_to_lb=True):
        super(FakeHM, self).__init__(id=id, attached_to_lb=attached_to_lb)
        self.id = id
        self.pool = FakePool()


class FakePolicy(FakeBaseObj):
    def __init__(self, id='test_obj_id', attached_to_lb=True):
        super(FakePolicy, self).__init__(id=id, attached_to_lb=attached_to_lb)
        self.id = id
        self.listener = FakeListener()


class FakeRule(FakeBaseObj):
    def __init__(self, id='test_obj_id', attached_to_lb=True):
        super(FakeRule, self).__init__(id=id, attached_to_lb=attached_to_lb)
        self.id = id
        self.policy = FakePolicy()


@pytest.fixture
def happy_path_driver():
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.return_value = {'host': 'test_agent'}
    mock_driver.service_builder.build.return_value = {}
    return mock_driver, mock.MagicMock(name='mock_context')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.agent_rpc')
@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.plugin_rpc')
def test_f5driverv2(mock_plugin_rpc, mock_agent_rpc):
    mock_plugin = mock.MagicMock(name='mock_plugin')
    d = dv2.F5DriverV2(plugin=mock_plugin)
    assert d.plugin == mock_plugin
    assert d.env is None
    assert isinstance(d.loadbalancer, dv2.LoadBalancerManager)
    assert isinstance(d.listener, dv2.ListenerManager)


def test_lbmgr_create():
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.return_value = {'host': 'test_agent'}
    mock_driver.service_builder.build.return_value = {}
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    fake_lb = FakeLB()
    lb_mgr.create(mock_ctx, fake_lb)
    assert mock_driver.agent_rpc.create_loadbalancer.call_args == \
        mock.call(mock_ctx, fake_lb.to_api_dict(), {}, 'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_create_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.return_value = {}
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    fake_lb = FakeLB()
    with pytest.raises(KeyError) as ex:
        lb_mgr.create(mock_ctx, fake_lb)
    assert 'host' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer create: host')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_create_mismatched_tenant_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.side_effect = f5_exc.F5MismatchedTenants
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    with pytest.raises(f5_exc.F5MismatchedTenants) as ex:
        lb_mgr.create(mock_ctx, FakeLB())
    assert 'Tenant Id of network and loadbalancer mismatched' in \
        ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer create: Tenant Id of network and '
        'loadbalancer mismatched')
    assert mock_driver.plugin.db.update_status.call_args is None


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_create_no_eligible_agent(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.side_effect = FakeNoEligibleAgentExc
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    lb_mgr.create(mock_ctx, FakeLB())
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer create: test exception')
    assert mock_driver.plugin.db.update_status.call_args == \
        mock.call(mock_ctx, models.LoadBalancer, 'test_lb_id', 'ERROR')


def test_lbmgr_update():
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.return_value = {'host': 'test_agent'}
    mock_driver.service_builder.build.return_value = {}
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    old_lb = FakeLB(id='old_lb')
    new_lb = FakeLB(id='new_lb')
    lb_mgr.update(mock_ctx, old_lb, new_lb)
    assert mock_driver.agent_rpc.update_loadbalancer.call_args == \
        mock.call(
            mock_ctx, old_lb.to_api_dict(),
            new_lb.to_api_dict(), {}, 'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_update_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.return_value = {}
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    old_lb = FakeLB(id='old_lb')
    new_lb = FakeLB(id='new_lb')
    with pytest.raises(KeyError) as ex:
        lb_mgr.update(mock_ctx, old_lb, new_lb)
    assert 'host' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer update: host')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_update_no_active_agent_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.agent_rpc.update_loadbalancer.side_effect = \
        lbaas_agentschedulerv2.NoActiveLbaasAgent(loadbalancer_id='new_lb')
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    old_lb = FakeLB(id='old_lb')
    new_lb = FakeLB(id='new_lb')
    lb_mgr.update(mock_ctx, old_lb, new_lb)
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer update: No active agent found for '
        'loadbalancer new_lb.')
    assert mock_driver._handle_driver_error.call_args == \
        mock.call(mock_ctx, models.LoadBalancer, 'new_lb', 'ERROR')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_update_no_eligible_agent_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.agent_rpc.update_loadbalancer.side_effect = \
        lbaas_agentschedulerv2.NoEligibleLbaasAgent(loadbalancer_id='new_lb')
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    old_lb = FakeLB(id='old_lb')
    new_lb = FakeLB(id='new_lb')
    lb_mgr.update(mock_ctx, old_lb, new_lb)
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer update: No eligible agent found for '
        'loadbalancer new_lb.'
    )
    assert mock_driver._handle_driver_error.call_args == \
        mock.call(mock_ctx, models.LoadBalancer, 'new_lb', 'ERROR')


def test_lbmgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    fake_lb = FakeLB(tenant_id="test-tenant-id")
    lb_mgr.delete(mock_ctx, fake_lb)
    assert mock_driver.agent_rpc.delete_loadbalancer.call_args == \
        mock.call(mock_ctx, fake_lb.to_api_dict(), {}, 'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_delete_no_eligible_agent_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.agent_rpc.delete_loadbalancer.side_effect = \
        lbaas_agentschedulerv2.NoEligibleLbaasAgent(loadbalancer_id='test_lb')
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    fake_lb = FakeLB(id='test_lb')
    fake_lb = FakeLB(tenant_id="test-tenant-id")
    lb_mgr.delete(mock_ctx, fake_lb)
    assert mock_log.error.call_args == mock.call(
        'Exception: loadbalancer delete: No eligible agent found for '
        'loadbalancer test_lb.'
    )


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_lbmgr_delete_exception(mock_log):
    mock_driver = mock.MagicMock(name='mock_driver')
    mock_driver.scheduler.schedule.return_value = {}
    lb_mgr = dv2.LoadBalancerManager(mock_driver)
    mock_ctx = mock.MagicMock(name='mock_context')
    fake_lb = FakeLB()
    with pytest.raises(KeyError) as ex:
        lb_mgr.delete(mock_ctx, fake_lb)
    assert 'host' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        "Exception: loadbalancer delete: 'host'")


def test_listenermgr_create(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    lstnr_mgr = dv2.ListenerManager(mock_driver)
    fake_lstnr = FakeListener()
    lstnr_mgr.create(mock_ctx, fake_lstnr)
    assert mock_driver.agent_rpc.create_listener.call_args == \
        mock.call(mock_ctx, fake_lstnr.to_dict(), {}, 'test_agent')


def test_listener_update(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    lstnr_mgr = dv2.ListenerManager(mock_driver)
    fake_old_lstnr = FakeListener(id='old_listener')
    fake_new_lstnr = FakeListener(id='new_listener')
    lstnr_mgr.update(mock_ctx, fake_old_lstnr, fake_new_lstnr)
    assert mock_driver.agent_rpc.update_listener.call_args == \
        mock.call(
            mock_ctx,
            fake_old_lstnr.to_dict(),
            fake_new_lstnr.to_dict(),
            {},
            'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_listener_update_exception(mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    mock_driver.agent_rpc.update_listener.side_effect = Exception('test')
    lstnr_mgr = dv2.ListenerManager(mock_driver)
    fake_old_lstnr = FakeListener(id='old_listener')
    fake_new_lstnr = FakeListener(id='new_listener')
    with pytest.raises(Exception) as ex:
        lstnr_mgr.update(mock_ctx, fake_old_lstnr, fake_new_lstnr)
    assert 'test' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: listener update: test'
    )


def test_listenermgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    lstnr_mgr = dv2.ListenerManager(mock_driver)
    fake_lstnr = FakeListener()
    lstnr_mgr.delete(mock_ctx, fake_lstnr)
    assert mock_driver.agent_rpc.delete_listener.call_args == \
        mock.call(mock_ctx, fake_lstnr.to_dict(), {}, 'test_agent')


def test_poolmgr_create(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    pool_mgr = dv2.PoolManager(mock_driver)
    fake_pool = FakePool()
    pool_mgr.create(mock_ctx, fake_pool)
    assert mock_driver.agent_rpc.create_pool.call_args == \
        mock.call(mock_ctx, fake_pool.to_dict(), {}, 'test_agent')


def test_poolmgr_update(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    pool_mgr = dv2.PoolManager(mock_driver)
    fake_old_pool = FakePool(id='old_pool')
    fake_new_pool = FakePool(id='new_pool')
    pool_mgr.update(mock_ctx, fake_old_pool, fake_new_pool)
    assert mock_driver.agent_rpc.update_pool.call_args == \
        mock.call(
            mock_ctx,
            fake_old_pool.to_dict(),
            fake_new_pool.to_dict(),
            {},
            'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_pool_update_exception(mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    mock_driver.agent_rpc.update_pool.side_effect = Exception('test')
    pool_mgr = dv2.PoolManager(mock_driver)
    fake_old_pool = FakePool(id='old_pool')
    fake_new_pool = FakePool(id='new_pool')
    with pytest.raises(Exception) as ex:
        pool_mgr.update(mock_ctx, fake_old_pool, fake_new_pool)
    assert 'test' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: pool update: test'
    )


def test_poolmgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    pool_mgr = dv2.PoolManager(mock_driver)
    fake_pool = FakePool()
    pool_mgr.delete(mock_ctx, fake_pool)
    assert mock_driver.agent_rpc.delete_pool.call_args == \
        mock.call(mock_ctx, fake_pool.to_dict(), {}, 'test_agent')


def test_membermgr_create(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    member_mgr = dv2.MemberManager(mock_driver)
    fake_member = FakeMember()
    member_mgr.create(mock_ctx, fake_member)
    assert mock_driver.agent_rpc.create_member.call_args == \
        mock.call(mock_ctx, fake_member.to_dict(), {}, 'test_agent')


def test_member_update(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    member_mgr = dv2.MemberManager(mock_driver)
    fake_old_member = FakeMember(id='old_member')
    fake_new_member = FakeMember(id='new_member')
    member_mgr.update(mock_ctx, fake_old_member, fake_new_member)
    assert mock_driver.agent_rpc.update_member.call_args == \
        mock.call(
            mock_ctx,
            fake_old_member.to_dict(),
            fake_new_member.to_dict(),
            {},
            'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_member_update_exception(mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    mock_driver.agent_rpc.update_member.side_effect = Exception('test')
    member_mgr = dv2.MemberManager(mock_driver)
    fake_old_member = FakeMember(id='old_member')
    fake_new_member = FakeMember(id='new_member')
    with pytest.raises(Exception) as ex:
        member_mgr.update(mock_ctx, fake_old_member, fake_new_member)
    assert 'test' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: member update: test'
    )


def test_membermgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    member_mgr = dv2.MemberManager(mock_driver)
    fake_member = FakeMember()
    member_mgr.delete(mock_ctx, fake_member)
    assert mock_driver.agent_rpc.delete_member.call_args == \
        mock.call(mock_ctx, fake_member.to_dict(), {}, 'test_agent')


def test_health_monitormgr_create(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    health_monitor_mgr = dv2.HealthMonitorManager(mock_driver)
    fake_health_monitor = FakeHM()
    health_monitor_mgr.create(mock_ctx, fake_health_monitor)
    assert mock_driver.agent_rpc.create_health_monitor.call_args == \
        mock.call(mock_ctx, fake_health_monitor.to_dict(), {}, 'test_agent')


def test_health_monitor_update(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    health_monitor_mgr = dv2.HealthMonitorManager(mock_driver)
    fake_old_health_monitor = FakeHM(id='old_health_monitor')
    fake_new_health_monitor = FakeHM(id='new_health_monitor')
    health_monitor_mgr.update(
        mock_ctx, fake_old_health_monitor, fake_new_health_monitor)
    assert mock_driver.agent_rpc.update_health_monitor.call_args == \
        mock.call(
            mock_ctx,
            fake_old_health_monitor.to_dict(),
            fake_new_health_monitor.to_dict(),
            {},
            'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_health_monitor_update_exception(mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    mock_driver.agent_rpc.update_health_monitor.side_effect = Exception('test')
    health_monitor_mgr = dv2.HealthMonitorManager(mock_driver)
    fake_old_health_monitor = FakeHM(id='old_health_monitor')
    fake_new_health_monitor = FakeHM(id='new_health_monitor')
    with pytest.raises(Exception) as ex:
        health_monitor_mgr.update(
            mock_ctx, fake_old_health_monitor,
            fake_new_health_monitor)
    assert 'test' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: health monitor update: test'
    )


def test_health_monitormgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    health_monitor_mgr = dv2.HealthMonitorManager(mock_driver)
    fake_health_monitor = FakeHM()
    health_monitor_mgr.delete(mock_ctx, fake_health_monitor)
    assert mock_driver.agent_rpc.delete_health_monitor.call_args == \
        mock.call(mock_ctx, fake_health_monitor.to_dict(), {}, 'test_agent')


def test_l7policymgr_create(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    l7policy_mgr = dv2.L7PolicyManager(mock_driver)
    fake_l7policy = FakePolicy()
    l7policy_mgr.create(mock_ctx, fake_l7policy)
    assert mock_driver.agent_rpc.create_l7policy.call_args == \
        mock.call(mock_ctx, fake_l7policy.to_dict(), {}, 'test_agent')


def test_l7policymgr_update(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    l7policy_mgr = dv2.L7PolicyManager(mock_driver)
    fake_old_l7policy = FakePolicy(id='old_policy')
    fake_new_l7policy = FakePolicy(id='new_policy')
    l7policy_mgr.update(mock_ctx, fake_old_l7policy, fake_new_l7policy)
    assert mock_driver.agent_rpc.update_l7policy.call_args == \
        mock.call(
            mock_ctx,
            fake_old_l7policy.to_dict(),
            fake_new_l7policy.to_dict(),
            {},
            'test_agent')


def test_l7policymgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    l7policy_mgr = dv2.L7PolicyManager(mock_driver)
    fake_l7policy = FakePolicy()
    l7policy_mgr.delete(mock_ctx, fake_l7policy)
    assert mock_driver.agent_rpc.delete_l7policy.call_args == \
        mock.call(mock_ctx, fake_l7policy.to_dict(), {}, 'test_agent')


def test_l7rulemgr_create(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    l7rule_mgr = dv2.L7RuleManager(mock_driver)
    fake_l7rule = FakeRule()
    l7rule_mgr.create(mock_ctx, fake_l7rule)
    assert mock_driver.agent_rpc.create_l7rule.call_args == \
        mock.call(mock_ctx, fake_l7rule.to_dict(), {}, 'test_agent')


def test_l7rulemgr_update(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    l7rule_mgr = dv2.L7RuleManager(mock_driver)
    fake_old_l7rule = FakeRule(id='old_rule')
    fake_new_l7rule = FakeRule(id='new_rule')
    l7rule_mgr.update(mock_ctx, fake_old_l7rule, fake_new_l7rule)
    assert mock_driver.agent_rpc.update_l7rule.call_args == \
        mock.call(
            mock_ctx,
            fake_old_l7rule.to_dict(),
            fake_new_l7rule.to_dict(),
            {},
            'test_agent')


def test_l7rulemgr_delete(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    l7rule_mgr = dv2.L7RuleManager(mock_driver)
    fake_l7rule = FakeRule()
    l7rule_mgr.delete(mock_ctx, fake_l7rule)
    assert mock_driver.agent_rpc.delete_l7rule.call_args == \
        mock.call(mock_ctx, fake_l7rule.to_dict(), {}, 'test_agent')


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_mgr__call_rpc_no_eligible_agent_exception(
        mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    pol_mgr = dv2.L7PolicyManager(mock_driver)
    pol_mgr._setup_crud = mock.MagicMock(
        name='mock_setup_crud',
        side_effect=lbaas_agentschedulerv2.NoEligibleLbaasAgent(
            loadbalancer_id='test_lb')
    )
    fake_pol = FakePolicy(id='test_lb')
    pol_mgr.delete(mock_ctx, fake_pol)
    assert mock_log.error.call_args == mock.call(
        'Exception: delete_l7policy: No eligible agent found for '
        'loadbalancer test_lb.'
    )
    assert mock_driver.plugin.db.update_status.call_args is None


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_mgr__call_rpc_mismatch_tenant_exception(
        mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    rule_mgr = dv2.L7RuleManager(mock_driver)
    rule_mgr._setup_crud = mock.MagicMock(
        name='mock_setup_crud', side_effect=f5_exc.F5MismatchedTenants
    )
    fake_rule = FakeRule(id='test_lb')
    with pytest.raises(f5_exc.F5MismatchedTenants) as ex:
        rule_mgr.create(mock_ctx, fake_rule)
    assert 'Tenant Id of network and loadbalancer mismatched' in \
        ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: create_l7rule: Tenant Id of network and loadbalancer '
        'mismatched'
    )
    assert mock_driver.plugin.db.update_status.call_args is None


@mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG')
def test_mgr__call_rpc_exception(
        mock_log, happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    pol_mgr = dv2.L7PolicyManager(mock_driver)
    pol_mgr._setup_crud = mock.MagicMock(
        name='mock_setup_crud', side_effect=Exception('test')
    )
    fake_pol = FakePolicy(id='test_lb')
    with pytest.raises(Exception) as ex:
        pol_mgr.delete(mock_ctx, fake_pol)
    assert 'test' == ex.value.message
    assert mock_log.error.call_args == mock.call(
        'Exception: delete_l7policy: test'
    )


def test_membermgr_delete_no_lb_attached(happy_path_driver):
    mock_driver, mock_ctx = happy_path_driver
    member_mgr = dv2.MemberManager(mock_driver)
    fake_member = FakeMember(attached_to_lb=False)
    with pytest.raises(dv2.F5NoAttachedLoadbalancerException) as ex:
        member_mgr.delete(mock_ctx, fake_member)
    assert 'Entity has no associated loadbalancer' == ex.value.message
