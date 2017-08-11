# coding=utf-8
# Copyright 2017 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from f5.bigip import ManagementRoot
from f5.utils.testutils.registrytools import order_by_weights
from f5.utils.testutils.registrytools import register_device

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

URI_ORDER = {
    '/mgmt/tm/ltm/policy': 1,
    '/mgmt/tm/ltm/virtual': 2,
    '/mgmt/tm/ltm/pool': 3,
    '/mgmt/tm/ltm/node/': 4,
    '/mgmt/tm/ltm/monitor': 5,
    '/mgmt/tm/ltm/virtual-address': 6,
    '/mgmt/tm/net/self/': 7,
    '/mgmt/tm/net/fdb': 8,
    '/mgmt/tm/net/tunnels/tunnel/': 9,
    '/mgmt/tm/net/tunnels/vxlan/': 10,
    '/mgmt/tm/net/tunnels/gre': 11,
    '/mgmt/tm/net/vlan': 12,
    '/mgmt/tm/net/route': 13,
    '/mgmt/tm/ltm/snatpool': 14,
    '/mgmt/tm/ltm/snat-translation': 15,
    '/mgmt/tm/net/route-domain': 16,
    '/mgmt/tm/sys/folder': 17}


class BigIpClient(object):
    def __init__(self, hostname, username, password):
        self.bigip = ManagementRoot(hostname, username, password)

    def reset_device_to_pretest_snapshot(self):
        posttest_snapshot = register_device(self.bigip)
        test_diff = frozenset(posttest_snapshot) - \
            frozenset(self.pretest_snapshot)
        uris = order_by_weights(test_diff, URI_ORDER)

        # Delete all tunnel records, if any exist
        for t in self.bigip.tm.net.fdb.tunnels.get_collection():
            if t.name != 'http-tunnel' \
                    and t.name != 'socks-tunnel':
                t.modify(records=None)

        # Delete resources from device
        for selfLink in uris:
            if selfLink in test_diff:
                if 'fdb' in selfLink:
                    continue
                if 'snat-translation' in selfLink:
                    continue
                posttest_snapshot[selfLink].delete()

    def snapshot_device(self):
        self.pretest_snapshot = register_device(self.bigip)

    def folder_exists(self, folder):
        return self.bigip.tm.sys.folders.folder.exists(name=folder)

    def _policy_exists(self, name, partition):
        return self.bigip.tm.ltm.policys.policy.exists(
            name=name, partition=partition)

    def policy_exists(self, name, partition, should_exist=True):
        # The expectation here is that a policy should exist, but since
        # policy CUD operations in OpenStack do not change the lb status
        # to PENDING_UPDATE, we need to retry to check that the policy
        # exists on the BIG-IP device.
        attempts = 3
        for attempt in range(attempts):
            if self._policy_exists(name, partition) is should_exist:
                return should_exist
            if attempt == attempts-1:
                return not should_exist
            time.sleep(2)
        return not should_exist

    def rule_exists(self, policy_name, rule_name, partition):
        if self.policy_exists(policy_name, partition):
            policy = self.bigip.tm.ltm.policys.policy.load(
                name=policy_name, partition=partition)
            return policy.rules_s.rules.exists(
                name=rule_name, partition=partition)
        else:
            return False

    def rule_has_action(self, policy_name, rule_name, action, partition):
        if self.rule_exists(policy_name, rule_name, partition):
            policy = self.bigip.tm.ltm.policys.policy.load(
                name=policy_name, partition=partition)
            rule = policy.rules_s.rules.load(name=rule_name)

            if rule.actions_s.actions.exists(name='0'):
                rule_action = rule.actions_s.actions.load(name='0')
                if action == 'REJECT':
                    return getattr(rule_action, 'reset', False)
                elif action == 'REDIRECT_TO_URL':
                    return getattr(rule_action, 'redirect', False)
                elif action == 'REDIRECT_TO_POOL':
                    return getattr(rule_action, 'forward', False)

        return False

    def rule_is_reject(self, policy_name, rule_name, partition):
        return self.rule_has_action(
            policy_name, rule_name, 'REJECT', partition)

    def rule_is_redirect_to_pool(self, policy_name, rule_name, partition):
        return self.rule_has_action(
            policy_name, rule_name, 'REDIRECT_TO_POOL', partition)

    def rule_is_redirect_to_url(self, policy_name, rule_name, partition):
        return self.rule_has_action(
            policy_name, rule_name, 'REDIRECT_TO_URL', partition)

    def rule_conditions(self, policy_name, rule_name, partition):
        if self.rule_exists(policy_name, rule_name, partition):
            policy = self.bigip.tm.ltm.policys.policy.load(
                name=policy_name, partition=partition)
            rule = policy.rules_s.rules.load(name=rule_name)

            return rule.conditions_s.get_collection()
        return []

    def rule_has_condition(
            self, policy_name, rule_name, cond_name, value, partition):
        conditions = self.rule_conditions(policy_name, rule_name, partition)
        for cond in conditions:
            cond_val = getattr(cond, cond_name, None)
            assert len(cond.values) == 1
            value_str = cond.values[0]
            # Condition value should be set to True if condition type is
            # httpHost or condition comparison type is startsWith etc...
            # The values attribute should only contain one value and it
            # should be set to some string, even if it's empty
            if cond_val and value_str == value:
                return True
        return False

    def rule_has_starts_with(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'startsWith', value, partition)

    def rule_has_ends_with(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'endsWith', value, partition)

    def rule_has_contains(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'contains', value, partition)

    def rule_has_equals(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'equals', value, partition)

    def rule_has_host_name(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpHost', value, partition)

    def rule_has_path(self, policy_name, rule_name, value, partition):
        has_httpUri = self.rule_has_condition(
            policy_name, rule_name, 'httpUri', value, partition)
        has_path = self.rule_has_condition(
            policy_name, rule_name, 'path', value, partition)
        return has_httpUri and has_path

    def rule_has_file_type(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpUri', value, partition)

    def rule_has_header(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpHeader', value, partition)

    def rule_has_cookie(self, policy_name, rule_name, value, partition):
        return self.rule_has_condition(
            policy_name, rule_name, 'httpCookie', value, partition)

    def virtual_server_exists(self, name, partition):
        return self.bigip.tm.ltm.virtuals.virtual.exists(
            name=name, partition=partition)

    def virtual_server_has_policy(self, vs_name, policy_name, partition):
        vs = self.bigip.tm.ltm.virtuals.virtual.load(
            name=vs_name, partition=partition)

        policies = vs.policies_s.get_collection()
        for policy in policies:
            if policy.name == policy_name:
                return True

        return False

    def virtual_server_has_profile(self, vs_name, profile_name, partition):
        vs = self.bigip.tm.ltm.virtuals.virtual.load(
            name=vs_name, partition=partition)

        profiles = vs.profiles_s.get_collection()
        for profile in profiles:
            if profile.name == profile_name:
                return True

    def virtual_server_has_persist(self, vs_name, persist, partition):
        vs = self.bigip.tm.ltm.virtuals.virtual.load(
            name=vs_name, partition=partition)

        persist = getattr(vs, 'persist', None)
        return persist and persist[0]['name'] == persist

    def virtual_server_has_value(self, vs_name, attr, value, partition):
        vs = self.bigip.tm.ltm.virtuals.virtual.load(
            name=vs_name, partition=partition)

        return getattr(vs, attr, None) == value

    def virtual_server_has_pool(self, vs_name, partition, pool_name):
        vs = self.bigip.tm.ltm.virtuals.virtual.load(
            name=vs_name, partition=partition)
        expected_pool = '/' + partition + '/' + pool_name
        if not hasattr(vs, 'pool'):
            return False
        elif vs.pool == expected_pool:
            return True
        return False

    def pool_exists(self, pool_name, partition):
        return self.bigip.tm.ltm.pools.pool.exists(
            name=pool_name, partition=partition)

    def delete_pool(self, pool_name, partition):
        p = self.bigip.tm.ltm.pools.pool.load(
            name=pool_name, partition=partition)
        p.delete()

    def get_members(self, pool_name, partition):
        pool = self.bigip.tm.ltm.pools.pool.load(
            name=pool_name, partition=partition)
        return pool.members_s.get_collection()

    def delete_members(self, pool_name, partition):
        pool = self.bigip.tm.ltm.pools.pool.load(
            name=pool_name, partition=partition)
        for member in pool.members_s.get_collection():
            member.delete()
