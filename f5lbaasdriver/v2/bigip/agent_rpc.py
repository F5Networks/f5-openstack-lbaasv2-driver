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

from neutron.common.rpc import get_client
from oslo_messaging import Target

from f5lbaasdriver.v2.bigip import constants


class LBaaSv2AgentRPC(object):

    def __init__(self, driver=None):
        self.driver = driver
        self.topic = constants.TOPIC_LOADBALANCER_AGENT
        self._create_rpc_publisher()

    def _create_rpc_publisher(self):
        self.topic = constants.TOPIC_PROCESS_ON_HOST
        if self.driver.env:
            self.topic = self.topic + "_" + self.driver.env

        target = Target(topic=self.topic,
                        version=constants.BASE_RPC_API_VERSION)
        self._client = get_client(target, version_cap=None)

    def make_msg(self, method, **kwargs):
        return {'method': method,
                'namespace': constants.RPC_API_NAMESPACE,
                'args': kwargs}

    def call(self, context, msg, **kwargs):
        return self.__call_rpc_method(
            context, msg, rpc_method='call', **kwargs)

    def cast(self, context, msg, **kwargs):
        self.__call_rpc_method(context, msg, rpc_method='cast', **kwargs)

    def fanout_cast(self, context, msg, **kwargs):
        kwargs['fanout'] = True
        self.__call_rpc_method(context, msg, rpc_method='cast', **kwargs)

    def __call_rpc_method(self, context, msg, **kwargs):
        options = dict(
            ((opt, kwargs[opt])
             for opt in ('fanout', 'timeout', 'topic', 'version')
             if kwargs.get(opt))
        )
        if msg['namespace']:
            options['namespace'] = msg['namespace']

        if options:
            callee = self._client.prepare(**options)
        else:
            callee = self._client

        func = getattr(callee, kwargs['rpc_method'])
        return func(context, msg['method'], **msg['args'])

    def assure_service(self, context, service, agent):
        return self.cast(
            context,
            self.make_msg('assure_service', service=service),
            topic='%s.%s' % (self.topic, agent['host'])
        )

    def service_stats(self, context, service, agent):
        return self.cast(
            context,
            self.make_msg('service_stats', service=service),
            topic='%s.%s' % (self.topic, agent['host'])
        )
