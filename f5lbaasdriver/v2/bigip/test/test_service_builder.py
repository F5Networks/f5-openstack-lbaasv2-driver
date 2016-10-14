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

from f5lbaasdriver.v2.bigip import exceptions as f5_exc
from f5lbaasdriver.v2.bigip.service_builder import LBaaSv2ServiceBuilder


class FakeDict(dict):
    def __init__(self, *args, **kwargs):
        super(FakeDict, self).__init__(*args, **kwargs)

    def to_api_dict(self):
        return self


@pytest.fixture
def listeners():
    return [FakeDict(id='e6ce8fd6-907f-11e6-ae22-56b6b6499611'),
            FakeDict(id='218b4f6f-1243-494e-96a6-aba55759da69')]


@pytest.fixture
def l7policies():
    return [FakeDict(id='2ea7511d-a911-484b-bf1a-8abc7b249d66',
                     listeners=[
                         FakeDict(id='e6ce8fd6-907f-11e6-ae22-56b6b6499611')]),
            FakeDict(id='f5f4e752-e54e-45b8-a093-4c7587391855',
                     listeners=[
                         FakeDict(id='218b4f6f-1243-494e-96a6-aba55759da69')])]


@pytest.fixture
def two_listener_l7policies():
    return [FakeDict(id='2ea7511d-a911-484b-bf1a-8abc7b249d66',
                     listeners=[
                         FakeDict(id='e6ce8fd6-907f-11e6-ae22-56b6b6499611'),
                         FakeDict(id='218b4f6f-1243-494e-96a6-aba55759da69')])]


@pytest.fixture
def l7rules():
    return [FakeDict(id='850bb3cb-731d-4215-b345-0787a02a5be5',
                     policies=[
                         FakeDict(id='2ea7511d-a911-484b-bf1a-8abc7b249d66')]),
            FakeDict(id='45bb4ac2-df90-4ea6-a2fb-1ff50477a9d5',
                     policies=[
                         FakeDict(id='f5f4e752-e54e-45b8-a093-4c7587391855')])]


@pytest.fixture
def two_policy_l7rules():
    return [FakeDict(id='850bb3cb-731d-4215-b345-0787a02a5be5',
                     policies=[
                         FakeDict(id='2ea7511d-a911-484b-bf1a-8abc7b249d66'),
                         FakeDict(id='f5f4e752-e54e-45b8-a093-4c7587391855')])]


@pytest.fixture
def service_builder():
    return LBaaSv2ServiceBuilder(mock.MagicMock())


def test_get_l7policies(listeners, l7policies):
    """Test that get_l7policies returns valid list of dict"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policies = mock.MagicMock(
        return_value=l7policies)

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

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policy_rules = mock.MagicMock(
        return_value=l7rules)

    rules = service_builder._get_l7policy_rules(context, l7policies)

    assert len(rules) > 0
    assert rules[0] is l7rules[0]


def test_get_l7policy_rules_filter(l7policies):
    """Test that get_l7policy_rules() is called with filter of l7policy IDs"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder._get_l7policy_rules(context, l7policies)

    assert service_builder.driver.plugin.db.get_l7policy_rules.call_args_list \
        == [mock.call(context, l7policies[0]['id']),
            mock.call(context, l7policies[1]['id'])]


def test_get_l7policy_rules_no_policies():
    """Test that an empty policies input list returns an empty rule list."""
    context = mock.MagicMock()
    driver = mock.MagicMock()
    l7policies = []

    service_builder = LBaaSv2ServiceBuilder(driver)
    rules = service_builder._get_l7policy_rules(context, l7policies)

    assert not rules


def test_get_l7policies_more_than_one_listener_error(
        listeners, two_listener_l7policies):
    """Exception is raised when > 1 listener for a policy."""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policies = mock.MagicMock(
        return_value=two_listener_l7policies)

    with pytest.raises(f5_exc.PolicyHasMoreThanOneListener) as ex:
        service_builder._get_l7policies(context, listeners)
    assert 'A policy should have only one listener, but found 2 for policy ' \
        '2ea7511d-a911-484b-bf1a-8abc7b249d66' in ex.value.message


def test_get_l7policy_rules_more_than_one_policy(
        l7policies, two_policy_l7rules):
    """Exception is raised when > 1 policy for a rule."""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policy_rules = mock.MagicMock(
        return_value=two_policy_l7rules)

    with pytest.raises(f5_exc.RuleHasMoreThanOnePolicy) as ex:
        service_builder._get_l7policy_rules(context, l7policies)
    assert 'A rule should have only one policy, but found 2 for rule ' \
        '850bb3cb-731d-4215-b345-0787a02a5be5' in ex.value.message
