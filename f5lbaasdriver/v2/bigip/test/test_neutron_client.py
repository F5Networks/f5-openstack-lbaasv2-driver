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

from f5lbaasdriver.v2.bigip.neutron_client import F5NetworksNeutronClient

import mock
import pytest


@pytest.fixture
def f5_neutron_client():
    return F5NetworksNeutronClient(mock.MagicMock(name='plugin'))


def test_create_port_on_subnet(f5_neutron_client):
    mock_ctx = mock.MagicMock(name='context')
    f5_neutron_client.create_port_on_subnet(mock_ctx)
    assert not mock_ctx.session.begin.called


@mock.patch('f5lbaasdriver.v2.bigip.neutron_client.LOG')
def test_create_port_on_subnet_error(mock_log):
    mock_plugin = mock.MagicMock(name='plugin')
    mock_plugin.db._core_plugin.update_port.side_effect = Exception('error')
    nc = F5NetworksNeutronClient(mock_plugin)
    mock_ctx = mock.MagicMock(name='context')
    nc.create_port_on_subnet(mock_ctx, subnet_id='id')
    assert mock_log.error.call_args_list == [
        mock.call('Exception: create_port_on_subnet: %s', 'error')]
    assert not mock_ctx.session.begin.called


def test_delete_port(f5_neutron_client):
    mock_ctx = mock.MagicMock(name='context')
    f5_neutron_client.delete_port(mock_ctx, port_id='id')
    assert not mock_ctx.session.begin.called


@mock.patch('f5lbaasdriver.v2.bigip.neutron_client.LOG')
def test_delete_port_error(mock_log):
    mock_plugin = mock.MagicMock(name='plugin')
    mock_plugin.db._core_plugin.delete_port.side_effect = Exception('error')
    nc = F5NetworksNeutronClient(mock_plugin)
    mock_ctx = mock.MagicMock(name='context')
    with pytest.raises(Exception) as ex:
        nc.delete_port(mock_ctx, port_id='id')
    assert ex.value.message == 'error'
    assert not mock_ctx.session.begin.called
