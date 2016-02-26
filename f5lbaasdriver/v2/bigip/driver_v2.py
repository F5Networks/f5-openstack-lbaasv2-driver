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

import sys

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import importutils

from neutron.common import constants as q_const

from f5lbaasdriver.v2.bigip.agent_rpc import LBaaSv2AgentRPC
from f5lbaasdriver.v2.bigip.plugin_rpc import LBaaSv2PluginCallbacksRPC

LOG = logging.getLogger(__name__)

OPTS = [
    cfg.StrOpt(
        'f5_loadbalancer_pool_scheduler_driver_v2',
        default=('f5lbaasdriver.v2.bigip.agent_scheduler.TenantScheduler'),
        help=('Driver to use for scheduling '
              'pool to a default loadbalancer agent')),
    cfg.StrOpt(
        'f5_loadbalancer_service_builder_v2',
        default=(
            'f5lbaasdriver.v2.bigip.service_builder.LBaaSv2ServiceBuilder'),
        help=('Default class to use for building a service object.'))
]

cfg.CONF.register_opts(OPTS)


class F5DriverV2(object):
    def __init__(self, plugin=None, env=None):
        if not plugin:
            LOG.error('Required LBaaS Driver and Core Driver Missing')
            sys.exit(1)

        self.plugin = plugin
        self.env = env

        self.loadbalancer = LoadBalancerManager(self)
        self.listener = ListenerManager(self)
        self.pool = PoolManager(self)
        self.member = MemberManager(self)
        self.health_monitor = HealthMonitorManager(self)

        # what scheduler to use for pool selection
        self.scheduler = importutils.import_object(
            cfg.CONF.f5_loadbalancer_pool_scheduler_driver_v2)

        self.agent_rpc = LBaaSv2AgentRPC(self)
        self.plugin_rpc = LBaaSv2PluginCallbacksRPC(self)

        # add this agent RPC to the neutron agent scheduler
        # mixins agent_notifiers dictionary for it's env
        self.plugin.agent_notifiers.update(
            {q_const.AGENT_TYPE_LOADBALANCER: self.agent_rpc})


class LoadBalancerManager(object):
    def __init__(self, driver):
        self.driver = driver

    @log_helpers.log_method_call
    def create(self, context, loadbalancer):
        service = {}
        driver = self.driver

        agent = driver.scheduler.schedule(
            driver.plugin.db,
            context,
            loadbalancer,
            driver.env
        )
        if agent:
            LOG.debug("Found agent for loadbalancer create: %s", agent['host'])

        driver.agent_rpc.create_loadbalancer(
            context,
            loadbalancer.to_api_dict(),
            service,
            agent['host']
        )

    @log_helpers.log_method_call
    def update(self, context, old_loadbalancer, loadbalancer):
        pass

    @log_helpers.log_method_call
    def delete(self, context, loadbalancer):
        pass

    @log_helpers.log_method_call
    def refresh(self, context, loadbalancer):
        pass

    @log_helpers.log_method_call
    def stats(self, context, loadbalancer):
        pass


class ListenerManager(object):
    def __init__(self, driver):
        self.driver = driver

    @log_helpers.log_method_call
    def create(self, context, listener):
        pass

    @log_helpers.log_method_call
    def update(self, context, old_listener, listener):
        pass

    @log_helpers.log_method_call
    def delete(self, context, listener):
        pass


class PoolManager(object):
    def __init__(self, driver):
        self.driver = driver

    @log_helpers.log_method_call
    def create(self, context, pool):
        pass

    @log_helpers.log_method_call
    def update(self, context, old_pool, pool):
        pass

    @log_helpers.log_method_call
    def delete(self, context, pool):
        pass


class MemberManager(object):
    def __init__(self, driver):
        self.driver = driver

    @log_helpers.log_method_call
    def create(self, context, member):
        pass

    @log_helpers.log_method_call
    def update(self, context, old_member, member):
        pass

    @log_helpers.log_method_call
    def delete(self, context, member):
        pass


class HealthMonitorManager(object):
    def __init__(self, driver):
        self.driver = driver

    @log_helpers.log_method_call
    def create(self, context, health_monitor):
        pass

    @log_helpers.log_method_call
    def update(self, context, old_health_monitor, health_monitor):
        pass

    @log_helpers.log_method_call
    def delete(self, context, health_monitor):
        pass
