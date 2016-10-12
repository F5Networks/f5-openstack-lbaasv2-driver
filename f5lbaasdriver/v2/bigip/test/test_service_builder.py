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

from f5lbaasdriver.v2.bigip.service_builder import LBaaSv2ServiceBuilder


@pytest.fixture
def listeners():
    return [{'id': 'e6ce8fd6-907f-11e6-ae22-56b6b6499611'},
            {'id': '218b4f6f-1243-494e-96a6-aba55759da69'}]


@pytest.fixture
def l7policies():
    return [{'id': '2ea7511d-a911-484b-bf1a-8abc7b249d66'},
            {'id': 'f5f4e752-e54e-45b8-a093-4c7587391855'}]


@pytest.fixture
def l7rules():
    return [{'id': '850bb3cb-731d-4215-b345-0787a02a5be5'},
            {'id': '45bb4ac2-df90-4ea6-a2fb-1ff50477a9d5'}]


@pytest.fixture
def service_builder():
    return LBaaSv2ServiceBuilder(mock.MagicMock())


def test_get_l7policies(listeners, l7policies):
    """Test that get_l7policies returns valid list of dict"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    # mock an L7 policy object with a to_dict() method
    mock_policy = mock.MagicMock()
    mock_policy.to_dict.return_value = l7policies[0]

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policies = mock.MagicMock(
        return_value=[mock_policy])

    policies = service_builder._get_l7policies(context, listeners)

    assert len(policies) > 0
    assert policies[0] is l7policies[0]


def test_get_l7policies_filter(listeners):
    """Test that get_l7policies() is called with filter of listener IDs"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    # construct an equivalent filter to what service_builder should use
    filters = {'listener_id': [l['id'] for l in listeners]}

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder._get_l7policies(context, listeners)

    # assert that the expected filter was used
    service_builder.driver.plugin.db.get_l7policies.assert_called_with(
        context, filters=filters)


def test_get_l7policies_no_listeners():
    """Test that an empty listener list input returns an empty policy list."""
    context = mock.MagicMock()
    driver = mock.MagicMock()
    listeners = []

    service_builder = LBaaSv2ServiceBuilder(driver)
    l7policies = service_builder._get_l7policies(context, listeners)

    assert not l7policies


def test_get_l7policy_rules(l7policies, l7rules):
    """Test that get_l7policies returns valid list of dict"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    # mock an L7 rule object with a to_dict() method
    mock_rule = mock.MagicMock()
    mock_rule.to_dict.return_value = l7rules[0]

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policy_rules = mock.MagicMock(
        return_value=[mock_rule])

    rules = service_builder._get_l7policy_rules(context, l7policies)

    assert len(rules) > 0
    assert rules[0] is l7rules[0]


def test_get_l7policy_rules_filter(l7policies):
    """Test that get_l7policy_rules() is called with filter of l7policy IDs"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    # construct an equivalent filter to what service_builder should use
    filters = {'l7_policy_id': [l7['id'] for l7 in l7policies]}

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder._get_l7policy_rules(context, l7policies)

    # assert that the expected filter was used
    service_builder.driver.plugin.db.get_l7policy_rules.assert_called_with(
        context, filters=filters)


def test_get_l7policy_rules_no_policies():
    """Test that an empty policies input list returns an empty rule list."""
    context = mock.MagicMock()
    driver = mock.MagicMock()
    l7policies = []

    service_builder = LBaaSv2ServiceBuilder(driver)
    rules = service_builder._get_l7policy_rules(context, l7policies)

    assert not rules
