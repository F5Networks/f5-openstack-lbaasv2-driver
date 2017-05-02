#!/usr/bin/env python
# Copyright 2017 F5 Networks Inc.
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
#

import os
import oslo_messaging
import pytest

from mock import Mock
from neutron.common import rpc


import f5lbaasdriver.v2.bigip.agent_rpc as agent_rpc

log = None
getpid = None


@pytest.fixture
def LOG(request):
    global log

    def fin():
        agent_rpc.LOG = log
    request.addfinalizer(fin)
    log = agent_rpc.LOG
    agent_rpc.LOG = Mock()
    return agent_rpc.LOG


@pytest.fixture
def agentrpc():
    agent = agent_rpc.LBaaSv2AgentRPC(Mock())
    agent.first_pid = 1
    return agent


@pytest.fixture
def isolation(request):
    global getpid
    getpid = os.getpid

    def fin():
        os.getpid = getpid
    request.addfinalizer(fin)
    os.getpid = Mock(side_effect=[1, 2])
    target = Mock()
    oslo_messaging.Target = Mock(return_value=target)
    client = Mock()
    rpc.get_client = Mock(return_value=client)


@pytest.fixture
def client():
    client = Mock()
    ret_from_prepare = Mock()
    ret_from_prepare.foodog = Mock(return_value=4)
    client.prepare = Mock(return_value=ret_from_prepare)
    client.foodog = Mock(return_value=2)
    return client


def test_create_rpc_publisher(agentrpc, isolation):
    agentrpc.driver.env = 'foo'
    agentrpc.topic = 'doo'
    result = agentrpc._create_rpc_publisher()
    client = rpc.get_client.return_value
    assert result is client, "get_client logical return"
    assert 'foo' in agentrpc.topic, 'topic transfer test'


def test_agetn_rpc__call_rpc_method(LOG, agentrpc, isolation, client):
    agentrpc._create_rpc_publisher = Mock(return_value=client)
    agentrpc._client = client
    agentrpc.first_pid = 1
    msg = dict(namespace=True, method='foo', args={})
    retval = agentrpc._LBaaSv2AgentRPC__call_rpc_method(Mock(), msg,
                                                        rpc_method='foodog')
    assert retval == 4
    assert not LOG.error.called, 'Same PID test'
    msg = dict(method='foo', args={}, namespace=None)
    agentrpc.driver.env = None
    retval = agentrpc._LBaaSv2AgentRPC__call_rpc_method(Mock(), msg,
                                                        rpc_method='foodog')
    assert LOG.error.called
    assert retval == 2
