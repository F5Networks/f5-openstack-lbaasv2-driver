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


class L7PolicyClientJSON(rest_client.RestClient):
    """Tests L7 Policies API."""

    def list_l7policies(self, params=None):
        """List all L7 policies."""
        url = 'v2.0/lbaas/l7policies.json'
        if params:
            url = "{0}?{1}".format(url, parse.urlencode(params))
        resp, body = self.get(url)
        body = jsonutils.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBodyList(resp, body['l7policies'])

    def get_l7policy(self, policy_id, params=None):
        """Get L7 policy."""
        url = 'v2.0/lbaas/l7policies/{0}'.format(policy_id)
        if params:
            url = '{0}?{1}'.format(url, parse.urlencode(params))
        resp, body = self.get(url)
        body = jsonutils.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body["l7policy"])

    def create_l7policy(self, **kwargs):
        """Create L7 policy."""
        url = 'v2.0/lbaas/l7policies.json'
        post_body = jsonutils.dumps({"l7policy": kwargs})
        resp, body = self.post(url, post_body)
        body = jsonutils.loads(body)
        self.expected_success(201, resp.status)
        return rest_client.ResponseBody(resp, body["l7policy"])

    def update_l7policy(self, policy_id, **kwargs):
        """Update L7 policy."""
        url = 'v2.0/lbaas/l7policies/{0}'.format(policy_id)
        put_body = jsonutils.dumps({"l7policy": kwargs})
        resp, body = self.put(url, put_body)
        body = jsonutils.loads(body)
        self.expected_success(200, resp.status)
        return rest_client.ResponseBody(resp, body["l7policy"])

    def delete_l7policy(self, policy_id):
        """Delete L7 policy."""
        url = 'v2.0/lbaas/l7policies/{0}'.format(policy_id)
        resp, body = self.delete(url)
        self.expected_success(204, resp.status)
