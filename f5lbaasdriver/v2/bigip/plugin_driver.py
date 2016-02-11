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
    """Plugin Driver for LBaaSv2.

        This class implements the methods found in the abstract
        parent class.

        This class interacts with the data model through the
        core plugin, creates messages to send to agents and then
        invokes the LoadBalancerAgentApi class methods to
        send the RPC messages.
    """
    def __init__(self, plugin=None, core_plugin=None, env=None):
        if not plugin and core_plugin:
            LOG.error('Required LBaaS Driver and Core Driver Missing')
            sys.exit(1)
        self.plugin = plugin
        self.core_plugin = core_plugin
        self.env = env

    def lb_create(self, context, lb):
        pass

    def lb_update(self, context, old_lb, lb):
        pass

    def lb_delete(self, context, lb):
        pass

    def lb_refresh(self, context, lb):
        pass

    def lb_stats(self, context, lb):
        pass

    def listener_create(self, context, listener):
        pass

    def listener_update(self, context, old_listener, listener):
        pass

    def listener_delete(self, context, listener):
        pass

    def pool_create(self, context, pool):
        pass

    def pool_update(self, context, old_pool, pool):
        pass

    def pool_delete(self, context, pool):
        pass

    def member_create(self, context, member):
        pass

    def member_update(self, context, old_member, member):
        pass

    def member_delete(self, context, member):
        pass

    def healthmonitor_create(self, context, hm):
        pass

    def healthmonitor_update(self, context, old_hm, hm):
        pass

    def healthmonitor_delete(self, context, hm):
        pass
