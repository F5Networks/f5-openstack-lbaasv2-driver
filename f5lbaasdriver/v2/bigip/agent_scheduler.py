# coding=utf-8
"""Schedule agent to bind to a load balancer."""
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

import json
import random

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from neutron_lbaas import agent_scheduler
from neutron_lbaas.extensions import lbaas_agentschedulerv2

LOG = logging.getLogger(__name__)


class AgentSchedulerNG(agent_scheduler.ChanceScheduler):
    """NextGen Agent Scheduler for LBaaSv2"""

    def __init__(self):
        """Initialze with the ChanceScheduler base class."""
        super(AgentSchedulerNG, self).__init__()
        self.filters = []
        names = cfg.CONF.agent_filters
        for name in names:
            filter_path = ".".join([AgentSchedulerNG.__module__, name])
            self.filters.append(importutils.import_object(filter_path, self))

    # TODO(qzhao): This function in ONLY for backward compatibility.
    # Need to remove it in the future.
    def deserialize_agent_configurations(self, agent_conf):
        """Return a dictionary for the agent configuration."""
        if not isinstance(agent_conf, dict):
            try:
                agent_conf = json.loads(agent_conf)
            except ValueError as ve:
                LOG.error("Can't decode JSON %s : %s"
                          % (agent_conf, ve.message))
                return {}
        return agent_conf

    def schedule(self, plugin, context, lb, env=None):
        # Load all LBaaS Agents
        candidates = []
        candidates = plugin.db.get_lbaas_agents(context, active=True)
        if len(candidates) <= 0:
            raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                loadbalancer_id=lb.id)

        # Select the desired Agent
        for filter in self.filters:
            LOG.debug("Before filter %s agent candidates are %s",
                      type(filter).__name__, [i["id"] for i in candidates])
            candidates = filter.select(context, plugin, lb, candidates,
                                       env=env)
            LOG.debug("After filter %s agent candidates are %s",
                      type(filter).__name__, [i["id"] for i in candidates])
            if len(candidates) <= 0:
                break

        if len(candidates) <= 0:
            raise lbaas_agentschedulerv2.NoEligibleLbaasAgent(
                loadbalancer_id=lb.id)
        else:
            return candidates[0]


class AgentFilter(object):

    def __init__(self, scheduler):
        """Initialze Agent Filter"""
        self.scheduler = scheduler

    def select(self, context, plugin, lb, candidates, **kwargs):
        raise NotImplementedError()


class RandomFilter(AgentFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        if len(candidates) > 0:
            return [random.choice(candidates)]
        else:
            return candidates


class EnvironmentFilter(AgentFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):

        env = kwargs.get("env", None)

        result = []
        for candidate in candidates:
            ac = self.scheduler.deserialize_agent_configurations(
                candidate["configurations"])
            if ac.get("environment_prefix", None) == env:
                result.append(candidate)

        return result


class AvailabilityZoneFilter(AgentFilter):

    def select(self, context, plugin, lb, candidates, **kwargs):
        if len(candidates) <= 0:
            return candidates

        subnet = plugin.db._core_plugin.get_subnet(
            context,
            lb.vip_subnet_id,
        )

        network = plugin.db._core_plugin.get_network(
            context,
            subnet["network_id"]
        )

        az = ""
        # NOTE(qzhao): Do NOT support multiple availability zones
        if len(network["availability_zones"]) > 0:
            az = network["availability_zones"][0]

        # NOTE(qzhao): Use AZ hints if AZ is empty
        if not az and len(network["availability_zone_hints"]) > 0:
            az = network["availability_zone_hints"][0]

        # NOTE(qzhao): Use default AZ if AZ hints is empty
        if not az and len(cfg.CONF.default_availability_zones) > 0:
            az = cfg.CONF.default_availability_zones[0]

        result = []
        if not az:
            for candidate in candidates:
                if not candidate["availability_zone"]:
                    result.append(candidate)
        else:
            for candidate in candidates:
                zones = []
                if candidate["availability_zone"]:
                    zones = candidate["availability_zone"].split(",")
                if az in zones:
                    result.append(candidate)

        return result
