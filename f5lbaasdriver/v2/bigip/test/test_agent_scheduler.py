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

from neutron_lbaas.services.loadbalancer import data_models

from f5lbaasdriver.v2.bigip import agent_scheduler


def test_get_capacity(monkeypatch):

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
