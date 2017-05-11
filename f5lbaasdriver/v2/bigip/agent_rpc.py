# coding=utf-8
u"""RPC Calls to Agents for F5® LBaaSv2."""
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
#

from oslo_log import helpers as log_helpers
from oslo_log import log as logging
import oslo_messaging as messaging

from neutron.common import rpc

from f5lbaasdriver.v2.bigip import constants_v2 as constants

LOG = logging.getLogger(__name__)


class LBaaSv2AgentRPC(object):

    def __init__(self, driver=None):
        self.driver = driver
        self.topic = constants.TOPIC_LOADBALANCER_AGENT_V2
        self._create_rpc_publisher()

    def _create_rpc_publisher(self):
        self.topic = constants.TOPIC_LOADBALANCER_AGENT_V2
        if self.driver.env:
            self.topic = self.topic + "_" + self.driver.env
        target = messaging.Target(topic=self.topic,
                                  version=constants.BASE_RPC_API_VERSION)
        self._client = rpc.get_client(target, version_cap=None)

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

    @log_helpers.log_method_call
    def create_loadbalancer(self, context, loadbalancer, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_loadbalancer',
                loadbalancer=loadbalancer,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_loadbalancer(
            self,
            context,
            old_loadbalancer,
            loadbalancer,
            service,
            host
    ):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_loadbalancer',
                old_loadbalancer=old_loadbalancer,
                loadbalancer=loadbalancer,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_loadbalancer(self, context, loadbalancer, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_loadbalancer',
                loadbalancer=loadbalancer,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_loadbalancer_stats(
            self,
            context,
            loadbalancer,
            service,
            host
    ):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_loadbalancer_stats',
                loadbalancer=loadbalancer,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def create_listener(self, context, listener, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_listener',
                listener=listener,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_listener(self, context, old_listener, listener, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_listener',
                old_listener=old_listener,
                listener=listener,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_listener(self, context, listener, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_listener',
                listener=listener,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def create_pool(self, context, pool, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_pool',
                pool=pool,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_pool(self, context, old_pool, pool, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_pool',
                old_pool=old_pool,
                pool=pool,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_pool(self, context, pool, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_pool',
                pool=pool,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def create_member(self, context, member, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_member',
                member=member,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_member(self, context, old_member, member, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_member',
                old_member=old_member,
                member=member,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_member(self, context, member, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_member',
                member=member,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def create_health_monitor(self, context, health_monitor, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_health_monitor',
                health_monitor=health_monitor,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_health_monitor(
            self,
            context,
            old_health_monitor,
            health_monitor,
            service,
            host
    ):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_health_monitor',
                old_health_monitor=old_health_monitor,
                health_monitor=health_monitor,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_health_monitor(self, context, health_monitor, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_health_monitor',
                health_monitor=health_monitor,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def create_l7policy(self, context, l7policy, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_l7policy',
                l7policy=l7policy,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_l7policy(self, context, old_l7policy, l7policy, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_l7policy',
                old_l7policy=old_l7policy,
                l7policy=l7policy,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_l7policy(self, context, l7policy, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_l7policy',
                l7policy=l7policy,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def create_l7rule(self, context, l7rule, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'create_l7rule',
                l7rule=l7rule,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def update_l7rule(self, context, old_l7rule, l7rule, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'update_l7rule',
                old_l7rule=old_l7rule,
                l7rule=l7rule,
                service=service
            ),
            topic=topic)

    @log_helpers.log_method_call
    def delete_l7rule(self, context, l7rule, service, host):
        topic = '%s.%s' % (self.topic, host)
        return self.cast(
            context,
            self.make_msg(
                'delete_l7rule',
                l7rule=l7rule,
                service=service
            ),
            topic=topic)
