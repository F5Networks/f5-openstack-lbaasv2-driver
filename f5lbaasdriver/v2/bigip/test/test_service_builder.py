# Copyright (c) 2016-2018, F5 Networks, Inc.
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

from f5lbaasdriver.v2.bigip import exceptions as f5_exc
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
def listeners():
    return [FakeDict(default_pool=FakeDict(),
                     l7_policies=[]),
            FakeDict(default_pool=FakeDict(),
                     l7_policies=[])]


@pytest.fixture
def l7policies():
    policies = []
    ids = [_uuid(), _uuid()]
    for i, id in enumerate(ids):
        policy = FakeDict(listener_id=id,
                          listeners=[FakeDict(id=id)])
        assert policy.listener_id == policy.listeners[0].id == id
        policies.append(policy)

    return policies


@pytest.fixture
def two_listener_l7policies():
    return [FakeDict(listeners=[FakeDict(), FakeDict()])]


@pytest.fixture
def l7rules():
    return [FakeDict(policies=[FakeDict()]),
            FakeDict(policies=[FakeDict()])]


@pytest.fixture
def two_policy_l7rules():
    return [FakeDict(policies=[FakeDict(), FakeDict()])]


@pytest.fixture
def loadbalancer():
    return FakeDict()


@pytest.fixture
def monitors():
    return [FakeDict(),
            FakeDict()]


@pytest.fixture
def pools(monitors):
    pools = []
    for monitor in monitors:
        pool = FakeDict(healthmonitor_id=monitor['id'])
        monitor['pool_id'] = pool['id']
        pools.append(pool)

    return pools


@pytest.fixture
def members():
    return [FakeDict(subnet_id=_uuid())]


def subnet():
    return FakeDict(network_id=_uuid())


def test_get_l7policies(listeners, l7policies):
    """Test that get_l7policies returns valid list of dict"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_l7policies = \
        mock.MagicMock(return_value=l7policies)
    policies = service_builder._get_l7policies(context, listeners)

    assert len(policies) > 0
    assert policies[0] is l7policies[0]


def test_get_l7policies_filter(listeners):
    """Test that get_l7policies() is called with filter of listener IDs"""
    context = mock.MagicMock()
    driver = mock.MagicMock()

    # construct an equivalent filter to what service_builder should use
    filters = {'listener_id': [_['id'] for _ in listeners]}

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
    assert rules[0] is l7rules[0].to_api_dict()


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
    assert 'A policy should have only one listener, but found 2 for policy ' +\
        two_listener_l7policies[0].id in ex.value.message


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
    assert 'A rule should have only one policy, but found 2 for rule ' + \
           two_policy_l7rules[0].id in ex.value.message


def test_get_listeners(loadbalancer, listeners):
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_listeners = mock.MagicMock(
        return_value=listeners)
    test_listeners = service_builder._get_listeners(context, loadbalancer)

    assert len(test_listeners) == len(listeners)
    assert test_listeners[0] == listeners[0].to_api_dict()
    assert test_listeners[1] == listeners[1].to_api_dict()


def test_get_pools(loadbalancer, pools, monitors):
    context = mock.MagicMock()
    driver = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db.get_pools_and_healthmonitors = \
        mock.MagicMock(return_value=(pools, monitors))

    test_pools, test_monitors = \
        service_builder._get_pools_and_healthmonitors(
            context, loadbalancer)

    for pool, test_pool, monitor in zip(pools, test_pools, monitors):
        assert test_pool is pool
        assert test_pool['healthmonitor_id'] == monitor['id']


def test_get_members(pools, members):
    context = mock.MagicMock()
    driver = mock.MagicMock()
    subnet_map = mock.MagicMock()
    network_map = mock.MagicMock()

    service_builder = LBaaSv2ServiceBuilder(driver)
    service_builder.driver.plugin.db._get_members = \
        mock.MagicMock(return_value=members)

    test_members = service_builder._get_members(context, pools,
                                                subnet_map, network_map)

    for test_member, member in zip(test_members, members):
        assert test_member is member


def test__pool_to_dict():
    '''Ensure function does not add listeners or listener_id to pool dict.'''
    driver = mock.MagicMock()
    fake_pool = FakeDict()
    fake_pool.members = []
    fake_pool.l7_policies = []

    sb = LBaaSv2ServiceBuilder(driver)
    pool_dict = sb._pool_to_dict(fake_pool)
    assert 'listener_id' not in pool_dict
    assert 'listeners' not in pool_dict
