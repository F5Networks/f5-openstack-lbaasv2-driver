# coding=utf-8
u"""F5 Networks® LBaaSv2 plugin_rpc client for tempest tests."""
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

from f5lbaasdriver.v2.bigip import constants_v2 as f5_const

from neutron import context
import oslo_messaging as messaging
from tempest import config


CONF = config.CONF


class F5PluginRPCClient(object):
    """F5 LBaaS plugin RPC client."""

    def __init__(self):
        """Initialize the driver plugin RPC client."""
        self.environment_prefix = 'Project'
        self.topic = '%s_%s' % (f5_const.TOPIC_PROCESS_ON_HOST_V2,
                                self.environment_prefix)

        messaging.set_transport_defaults('neutron')
        self.transport = messaging.get_transport(
            CONF,
            url=CONF.f5_lbaasv2_driver.transport_url)
        self.target = messaging.Target(topic=self.topic)
        self.client = messaging.RPCClient(self.transport, self.target)
        self.context = context.get_admin_context().to_dict()

    def get_client(self):
        """Return a client that can connect to the plugin_rpc.py API."""
        return self.client

    def get_context(self):
        """Return a context object that can be used for RPC."""
        return self.context
