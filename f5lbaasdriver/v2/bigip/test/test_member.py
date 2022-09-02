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
from uuid import uuid4

from f5lbaasdriver.v2.bigip.service_builder import LBaaSv2ServiceBuilder


class FakeDict(dict):
    """Can be used as Neutron model object or as service builder dict"""
    def __init__(self, *args, **kwargs):
        super(FakeDict, self).__init__(*args, **kwargs)
        if 'id' not in kwargs:
            self['id'] = _uuid()

    def __getattr__(self, item):
        """Needed for using as a model object"""
        if item in self:
            return self[item]
        else:
            return None

    def to_api_dict(self):
        return self

    def to_dict(self, **kwargs):
        return self


def _uuid():
    """Create a random UUID string for model object IDs"""
    return str(uuid4())


@pytest.fixture
def member():
    return [FakeDict(subnet_id=_uuid())]


@mock.patch('f5lbaasdriver.v2.bigip.service_builder.LOG')
def test_get_extended_member_no_port(mock_log):
    context = mock.MagicMock()
    driver = mock.MagicMock()
    member = FakeDict()
    member.address = "10.2.2.10"
    driver.plugin.db._core_plugin.get_ports.return_value = []

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.disconnected_service = mock.MagicMock()
    service_builder.disconnected_service.get_network_segment.return_value = {}

    member_dict, subnet, net = \
        service_builder._get_extended_member(context, member)
    assert mock_log.warning.call_args_list == \
        [mock.call('Lbaas member 10.2.2.10 has no associated neutron port')]
    assert 'port' not in member_dict


@mock.patch('f5lbaasdriver.v2.bigip.service_builder.LOG')
def test_get_extended_member_one_port(mock_log):
    context = mock.MagicMock()
    driver = mock.MagicMock()
    member = FakeDict()
    driver.plugin.db._core_plugin.get_ports.return_value = [1]

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.disconnected_service = mock.MagicMock()
    service_builder.disconnected_service.get_network_segment.return_value = {}

    member_dict, subnet, net = \
        service_builder._get_extended_member(context, member)
    assert mock_log.warning.call_args_list == []
    assert 'port' in member_dict


@mock.patch('f5lbaasdriver.v2.bigip.service_builder.LOG')
def test_get_extended_member_several_ports(mock_log):
    context = mock.MagicMock()
    driver = mock.MagicMock()
    member = FakeDict()
    member.address = "10.2.2.10"
    driver.plugin.db._core_plugin.get_ports.return_value = [1, 2, 3, 4]

    service_builder = LBaaSv2ServiceBuilder(driver)
    member_dict, subnet, net = \
        service_builder._get_extended_member(context, member)
    assert mock_log.warning.call_args_list == \
        [mock.call("Multiple ports found for member: 10.2.2.10")]
    assert 'port' not in member_dict
