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

import json
import mock
import pytest

from neutron_lbaas.extensions.lbaas_agentschedulerv2 import NoActiveLbaasAgent
from neutron_lbaas.services.loadbalancer import data_models

from f5lbaasdriver.v2.bigip import agent_scheduler


def test_get_capacity():

    sched = agent_scheduler.TenantScheduler()
    config = {}
    assert(sched.get_capacity(config) == 0.0)

    config['environment_capacity_score'] = 1.234
    assert(sched.get_capacity(config) == 1.234)


def test_get_lbaas_agent_hosting_loadbalancer():

    plugin = mock.MagicMock()
    context = mock.MagicMock()
    loadbalancer_id = 'uuid_1234'

    sched = agent_scheduler.TenantScheduler()
    agent = sched.get_lbaas_agent_hosting_loadbalancer(
        plugin, context, loadbalancer_id)
    assert agent


def test_schedule():

    plugin = mock.MagicMock()
    context = mock.MagicMock()
    loadbalancer = data_models.LoadBalancer(id='uuid_1234')

    sched = agent_scheduler.TenantScheduler()
    agent = sched.schedule(plugin, context, loadbalancer)
    assert agent


def test_rebind_loadbalancers():

    plugin = mock.MagicMock()
    context = mock.MagicMock()
    sched = agent_scheduler.TenantScheduler()
    sched.get_agents_in_env = mock.MagicMock(name='get_agents_in_env')
    agents_in_env = [{'fake_agent': {'id': 'test_agent_2_id',
                                     'alive': True,
                                     'admin_state_up': True,
                                     'configurations': {
                                         'environment_prefix': 'prod',
                                         'environment_group_number': 2}}}]
    sched.get_agents_in_env.return_value = agents_in_env
    return_all = [type('test', (), {})()]
    context.session.query.all = mock.MagicMock(name='all',
                                               return_value=return_all)
    context.session.add = mock.MagicMock(name='add', return_value=None)
    sched.rebind_loadbalancers(context, plugin, 'prod',
                               2, agents_in_env[0]['fake_agent'])


def test_get_lbaas_agent_hosting_loadbalancer_none():
    mock_plugin = mock.MagicMock(name='plugin')
    mock_plugin.db.get_agent_hosting_loadbalancer.return_value = None
    mock_cxt = mock.MagicMock(name='context')
    lb_id = 'test_lb_id'
    sched = agent_scheduler.TenantScheduler()
    agent = sched.get_lbaas_agent_hosting_loadbalancer(
        mock_plugin, mock_cxt, lb_id)
    assert agent is None


def test_deserialize_agent_configurations():
    conf = '{"bar":["baz", null, 1.0, 2]}'
    sched = agent_scheduler.TenantScheduler()
    res = sched.deserialize_agent_configurations(conf)
    assert res == json.loads(conf)


@mock.patch('f5lbaasdriver.v2.bigip.agent_scheduler.LOG')
def test_deserialize_agent_configurations_error(mock_log):
    conf = '{'
    sched = agent_scheduler.TenantScheduler()
    res = sched.deserialize_agent_configurations(conf)
    assert res == {}
    assert mock_log.error.call_args_list == [mock.call(
        "Can't decode JSON { : Expecting object: line 1 column 1 (char 0)")]


def test_deserialize_agent_configurations_is_dict():
    conf = {}
    sched = agent_scheduler.TenantScheduler()
    assert conf == sched.deserialize_agent_configurations(conf)


def test_schedule_get_active_agent():
    mock_plugin = mock.MagicMock(name='plugin')
    mock_plugin.db.get_agent_hosting_loadbalancer.return_value = \
        {
            'agent': {
                'alive': True,
                'id': 'test_agent_id',
                'admin_state_up': True,
                'configurations': {
                    'environment_prefix': 'prod',
                    'environment_group_number': 2
                }
            }
        }
    mock_cxt = mock.MagicMock(name='context')
    lb_id = 'test_lb_id'
    sched = agent_scheduler.TenantScheduler()
    sched.get_agents_in_env = mock.MagicMock(
        name='get_agents_in_env', return_value=['agent_has_no_id'])
    agent = sched.schedule(mock_plugin, mock_cxt, lb_id, env=4)
    assert agent['id'] == 'test_agent_id'


def test_get_lbaas_agent_hosting_loadbalancer_agent_dead():
    mock_plugin = mock.MagicMock(name='plugin')
    fake_agent = {
        'agent': {
            'alive': False,
            'id': 'test_agent_id',
            'admin_state_up': True,
            'configurations': {
                'environment_prefix': 'prod',
                'environment_group_number': 2
            }
        }
    }
    mock_plugin.db.get_agent_hosting_loadbalancer.return_value = fake_agent
    mock_cxt = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    res = sched.get_lbaas_agent_hosting_loadbalancer(
        mock_plugin, mock_cxt, 'test_lb_id', env='test_env')
    assert res == fake_agent


def test_get_lbaas_agent_hosting_loadbalancer_agent_dead_has_env_gn():
    mock_plugin = mock.MagicMock(name='plugin')
    fake_agent = {
        'agent': {
            'alive': False,
            'id': 'test_agent_id',
            'admin_state_up': True,
            'configurations': {
                'environment_prefix': 'prod',
                'environment_group_number': 2
            }
        }
    }
    mock_plugin.db.get_agent_hosting_loadbalancer.return_value = fake_agent
    mock_cxt = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    res = sched.get_lbaas_agent_hosting_loadbalancer(
        mock_plugin, mock_cxt, 'test_lb_id', env='test_env')
    assert res == fake_agent


def test_get_lbaas_agent_hosting_loadbalancer_agent_dead_env_agents_active():
    mock_plugin = mock.MagicMock(name='plugin')
    fake_agent = {'agent': {'alive': False,
                            'id': 'test_agent_id',
                            'admin_state_up': True,
                            'configurations': {'environment_prefix': 'prod',
                                               'environment_group_number': 2}}}
    mock_plugin.db.get_agent_hosting_loadbalancer.return_value = fake_agent
    mock_cxt = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    sched.get_agents_in_env = mock.MagicMock(name='get_agents_in_env')
    agents_in_env = [
        {'fake_agent': {'id': 'test_agent_2_id',
                        'alive': True,
                        'admin_state_up': True,
                        'configurations': {'environment_prefix': 'prod',
                                           'environment_group_number': 2}}}]
    sched.get_agents_in_env.return_value = agents_in_env
    sched.rebind_loadbalancers = mock.MagicMock(name='rebind_loadbalancers')
    sched.rebind_loadbalancers.return_value = agents_in_env[0]
    res = sched.get_lbaas_agent_hosting_loadbalancer(
        mock_plugin, mock_cxt, 'test_lb_id', env='test_env')
    assert res == {'agent': agents_in_env[0]}


def test_get_agents_in_env():
    mock_plugin = mock.MagicMock(name='plugin')
    agent_conf = {'configurations': '{"environment_prefix": "Project"}'}
    mock_plugin.db.get_lbaas_agents.return_value = [agent_conf, agent_conf]
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    agents = sched.get_agents_in_env(mock_ctx, mock_plugin, 'Project')
    assert agents == [agent_conf, agent_conf]

    non_env_agent_conf = {'configurations': '{"environment_prefix": "Diff"}'}
    mock_plugin.db.get_lbaas_agents.return_value = [
        agent_conf, non_env_agent_conf]
    agents = sched.get_agents_in_env(mock_ctx, mock_plugin, 'Project')
    assert agents == [agent_conf]


def test_get_agents_in_env_with_env_group_number():
    mock_plugin = mock.MagicMock(name='plugin')
    agent_conf = {'configurations':
                  '{"environment_prefix": "Project", \
                  "environment_group_number": 4}'
                  }
    mock_plugin.db.get_lbaas_agents.return_value = [agent_conf, agent_conf]
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    agents = sched.get_agents_in_env(mock_ctx, mock_plugin, 'Project', group=4)
    assert agents == [agent_conf, agent_conf]


@mock.patch('f5lbaasdriver.v2.bigip.agent_scheduler.LOG')
def test_get_agents_in_env_error(mock_log):
    mock_plugin = mock.MagicMock(name='plugin')
    mock_plugin.db.get_lbaas_agents.side_effect = Exception('test')
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    assert sched.get_agents_in_env(mock_ctx, mock_plugin, 'Project') == []
    assert mock_log.error.call_args_list == [
        mock.call('Exception retrieving agent candidates '
                  'for scheduling: test')]


def test_schedule_candidates():
    mock_plugin = mock.MagicMock(name='plugin')
    agent_conf = {'id': 34, 'configurations':
                  '{"environment_prefix": "Project", \
                    "environment_group_number": 4}'
                  }
    mock_plugin.db.get_lbaas_agents.return_value = [agent_conf, agent_conf]
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    sched.get_lbaas_agent_hosting_loadbalancer = mock.MagicMock(
        name='get_lbaas_agent_hosting_loadbalancer', return_value=None)
    res = sched.schedule(mock_plugin, mock_ctx, 'test_lb_id', 'Project')
    assert res == agent_conf


@mock.patch('f5lbaasdriver.v2.bigip.agent_scheduler.LOG')
def test_schedule_no_candidates(mock_log):
    mock_plugin = mock.MagicMock(name='plugin')
    mock_plugin.db.get_lbaas_agents.return_value = []
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    sched.get_lbaas_agent_hosting_loadbalancer = mock.MagicMock(
        name='get_lbaas_agent_hosting_loadbalancer', return_value=None)
    with pytest.raises(NoActiveLbaasAgent) as ex:
        sched.schedule(mock_plugin, mock_ctx, 'test_lb_id', 'Project')
    assert 'No active agent found for loadbalancer' in ex.value.message
    assert mock_log.error.call_args_list == \
        [mock.call('No f5 lbaas agents are active for env Project')]


def test_schedule_cap_by_group():
    mock_plugin = mock.MagicMock(name='plugin')
    agent1_conf = {'id': 34, 'configurations':
                   '{"environment_prefix": "Project", \
                    "environment_group_number": 4, \
                    "environment_capacity_score": 0.5}'}
    agent2_conf = {'id': 34, 'configurations':
                   '{"environment_prefix": "Project", \
                    "environment_group_number": 4, \
                    "environment_capacity_score": 0.8}'}
    mock_plugin.db.get_lbaas_agents.return_value = [agent1_conf, agent2_conf]
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    sched.get_lbaas_agent_hosting_loadbalancer = mock.MagicMock(
        name='get_lbaas_agent_hosting_loadbalancer', return_value=None)
    res = sched.schedule(mock_plugin, mock_ctx, 'test_lb_id', 'Project')
    # Agent chosen at random if capacity is less than 1.0
    try:
        assert res == agent1_conf
    except AssertionError:
        assert res == agent2_conf


def test_schedule_already_assigned_agent():
    mock_plugin = mock.MagicMock(name='plugin')
    mock_lb = mock.MagicMock(name='lb')
    mock_lb.tenant_id = 'test_tenant'
    mock_plugin.db.get_loadbalancer.return_value = mock_lb
    mock_plugin.db.list_loadbalancers_on_lbaas_agent.return_value = [mock_lb]
    agent1_conf = {'id': 34, 'configurations':
                   '{"environment_prefix": "Project", \
                    "environment_group_number": 4, \
                    "environment_capacity_score": 1.5}'}
    agent2_conf = {'id': 34, 'configurations':
                   '{"environment_prefix": "Project", \
                    "environment_group_number": 4, \
                    "environment_capacity_score": 0.8}'}
    mock_plugin.db.get_lbaas_agents.return_value = [agent1_conf, agent2_conf]
    mock_ctx = mock.MagicMock(name='context')
    sched = agent_scheduler.TenantScheduler()
    sched.get_lbaas_agent_hosting_loadbalancer = mock.MagicMock(
        name='get_lbaas_agent_hosting_loadbalancer', return_value=None)
    res = sched.schedule(mock_plugin, mock_ctx, 'test_lb_id', 'Project')
    assert res == agent2_conf
