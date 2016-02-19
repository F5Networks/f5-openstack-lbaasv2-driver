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
from oslo_log import log as logging


LOG = logging.getLogger(__name__)

OPTS = [
    cfg.StrOpt('f5_loadbalancer_pool_scheduler_driver_v2',
               default=('f5.lbaas.drivers.agent_schedule.TenantScheduler'),
               help=('Driver to use for scheduling '
                     'pool to a default loadbalancer agent'))
]

cfg.CONF.register_opts(OPTS)


class F5DriverV2(object):
    def __init__(self, plugin=None, env=None):
        if not plugin:
            LOG.error('Required LBaaS Driver and Core Driver Missing')
            sys.exit(1)

        self.plugin = plugin
        self.core_plugin = plugin.db._core_plugin,
        self.env = env

        self.load_balancer = LoadBalancerManager(self)
        self.listener = ListenerManager(self)
        self.pool = PoolManager(self)
        self.member = MemberManager(self)
        self.health_monitor = HealthMonitorManager(self)


class LoadBalancerManager(object):
    def __init__(self, driver):
        self.driver = driver

    def create(self, context, load_balancer):
        pass

    def update(self, context, old_load_balancer, load_balancer):
        pass

    def delete(self, context, load_balancer):
        pass

    def refresh(self, context, load_balancer):
        pass

    def stats(self, context, load_balancer):
        pass


class ListenerManager(object):
    def __init__(self, driver):
        self.driver = driver

    def create(self, context, listener):
        pass

    def update(self, context, old_listener, listener):
        pass

    def delete(self, context, listener):
        pass


class PoolManager(object):
    def __init__(self, driver):
        self.driver = driver

    def create(self, context, pool):
        pass

    def update(self, context, old_pool, pool):
        pass

    def delete(self, context, pool):
        pass


class MemberManager(object):
    def __init__(self, driver):
        self.driver = driver

    def create(self, context, member):
        pass

    def update(self, context, old_member, member):
        pass

    def delete(self, context, member):
        pass


class HealthMonitorManager(object):
    def __init__(self, driver):
        self.driver = driver

    def create(self, context, health_monitor):
        pass

    def update(self, context, old_health_monitor, health_monitor):
        pass

    def delete(self, context, health_monitor):
        pass
