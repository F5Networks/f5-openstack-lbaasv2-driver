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
from oslo_utils import importutils

from f5lbaasdriver.v2.bigip.agent_rpc import LBaaSv2AgentRPC
from f5lbaasdriver.v2.bigip.plugin_rpc import LBaaSv2PluginCallbacksRPC
from f5lbaasdriver.v2.bigip.service_builder import LBaaSv2ServiceBuilder


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

        # Service agent scheduler
        self.scheduler = importutils.import_object(
            cfg.CONF.f5_loadbalancer_pool_scheduler_driver_v2)
        # Registered RPC Callback call by agents
        self.plugin_rpc = LBaaSv2PluginCallbacksRPC(driver=self)
        # RPC Proxy to call agent queues
        self.agent_rpc = LBaaSv2AgentRPC(driver=self)
        # Service builder
        self.service_def = LBaaSv2ServiceBuilder(driver=self)

    def lb_create(self, context, lb):
        agent = self.scheduler.schedule(self.plugin, context, lb, self.env)
        service = self.service_def.build(self, lb['id'])
        self.agent_rpc.lb_create(context, agent, lb=lb, service=service)

    def lb_update(self, context, old_lb, lb):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            lb['id'],
            self.env
        )
        service = self.service_def.build(self, lb['id'])
        self.agent_rpc.lb_update(context, agent,
                                 old_lb=old_lb, lb=lb,
                                 service=service)

    def lb_delete(self, context, lb):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            lb['id'],
            self.env
        )
        service = self.service_def.build(self, lb['id'])
        self.agent_rpc.lb_delete(context, agent, lb=lb, service=service)

    def lb_refresh(self, context, lb):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            lb['id'],
            self.env
        )
        service = self.service_def.build(self, lb['id'])
        self.agent_rpc.lb_refresh(context, agent, lb=lb, service=service)

    def lb_stats(self, context, lb):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            lb['id'],
            self.env
        )
        self.agent_rpc.lb_stats(context, agent, lb=lb)

    def listener_create(self, context, listener):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            listener['loadbalancer_id'],
            self.env
        )
        service = self.service_def.build(
            self,
            listener['loadbalancer_id']
        )
        self.agent_rpc.listener_create(context, agent,
                                       listener=listener,
                                       service=service)

    def listener_update(self, context, old_listener, listener):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            listener['loadbalancer_id'],
            self.env
        )
        service = self.service_def.build(
            self,
            listener['loadbalancer_id']
        )
        self.agent_rpc.listener_update(context, agent,
                                       old_listener=old_listener,
                                       listener=listener,
                                       service=service)

    def listener_delete(self, context, listener):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            listener['loadbalancer_id'],
            self.env
        )
        service = self.service_def.build(
            self,
            listener['loadbalancer_id']
        )
        self.agent_rpc.listener_delete(context, agent,
                                       listener=listener,
                                       service=service)

    def pool_create(self, context, pool):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            pool['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            pool['root_loadbalancer']['id']
        )
        self.agent_rpc.pool_create(context, agent,
                                   pool=pool, service=service)

    def pool_update(self, context, old_pool, pool):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            pool['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            pool['root_loadbalancer']['id']
        )
        self.agent_rpc.pool_update(context, agent,
                                   old_pool=old_pool,
                                   pool=pool,
                                   service=service)

    def pool_delete(self, context, pool):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            pool['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            pool['root_loadbalancer']['id']
        )
        self.agent_rpc.pool_delete(context, agent,
                                   pool=pool,
                                   service=service)

    def member_create(self, context, member):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            member['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            member['root_loadbalancer']['id']
        )
        self.agent_rpc.member_create(context, agent,
                                     member=member,
                                     service=service)

    def member_update(self, context, old_member, member):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            member['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            member['root_loadbalancer']['id']
        )
        self.agent_rpc.member_update(context, agent,
                                     old_member=old_member,
                                     member=member,
                                     service=service)

    def member_delete(self, context, member):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            member['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            member['root_loadbalancer']['id']
        )
        self.agent_rpc.member_delete(context, agent, member, service=service)

    def healthmonitor_create(self, context, hm):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            hm['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            hm['root_loadbalancer']['id']
        )
        self.agent_rpc.healthmonitor_create(context, agent,
                                            healthmonitor=hm, service=service)

    def healthmonitor_update(self, context, old_hm, hm):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            hm['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            hm['root_loadbalancer']['id']
        )
        self.agent_rpc.healthmonitor_update(context, agent,
                                            old_healthmonitor=old_hm,
                                            healthmonitor=hm, service=service)

    def healthmonitor_delete(self, context, hm):
        agent = self.scheduler.get_lbaas_agent_hosting_loadbalancer(
            self.plugin,
            context,
            hm['root_loadbalancer']['id'],
            self.env
        )
        service = self.service_def.build(
            self,
            hm['root_loadbalancer']['id']
        )
        self.agent_rpc.healthmonitor_delete(context, agent,
                                            healthmonitor=hm, service=service)
