# coding=utf-8
u"""F5 Networks® LBaaSv2 L7 rules client for tempest tests."""
# Copyright 2016 F5 Networks Inc.
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

from oslo_serialization import jsonutils
from six.moves.urllib import parse
from tempest.lib.common import rest_client


class L7RuleClientJSON(rest_client.RestClient):
    """Tests L7 Rules API."""

    def list_l7rules(self, policy_id, params=None):
        """List all L7 rules."""
        url = 'v2.0/lbaas/l7policies/{0}/rules.json'.format(policy_id)
        if params:
            url = "{0}?{1}".format(url, parse.urlencode(params))
        resp, body = self.get(url)
        body = jsonutils.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyList(resp, body['rules'])

    def get_l7rule(self, policy_id, rule_id, params=None):
        """Get L7 rule."""
        url = 'v2.0/lbaas/l7policies/{0}/rules/{1}'.format(policy_id, rule_id)
        if params:
            url = '{0}?{1}'.format(url, parse.urlencode(params))
        resp, body = self.get(url)
        body = jsonutils.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body["rule"])

    def create_l7rule(self, policy_id, **kwargs):
        """Create L7 rule."""
        url = 'v2.0/lbaas/l7policies/{0}/rules.json'.format(policy_id)
        post_body = jsonutils.dumps({"rule": kwargs})
        resp, body = self.post(url, post_body)
        body = jsonutils.loads(body)
        self.expected_success(201, resp.status)
        return rest_client.ResponseBody(resp, body["rule"])

    def update_l7rule(self, policy_id, rule_id, **kwargs):
        """Update L7 rule."""
        url = 'v2.0/lbaas/l7policies/{0}/rules/{1}'.format(policy_id,
                                                           rule_id)
        put_body = jsonutils.dumps({"rule": kwargs})
        resp, body = self.put(url, put_body)
        body = jsonutils.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body["rule"])

    def delete_l7rule(self, policy_id, rule_id):
        """Delete L7 rule."""
        url = 'v2.0/lbaas/l7policies/{0}/rules/{1}.json'.format(policy_id,
                                                                rule_id)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
