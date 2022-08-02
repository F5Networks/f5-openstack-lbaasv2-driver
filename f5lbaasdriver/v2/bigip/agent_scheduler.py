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

from collections import defaultdict
import json
import random

from oslo_config import cfg
from oslo_log import log as logging
from oslo_utils import importutils

from neutron_lbaas import agent_scheduler
from neutron_lbaas.extensions import lbaas_agentschedulerv2
from neutron_lbaas.services.loadbalancer.data_models import LoadBalancer

LOG = logging.getLogger(__name__)

OPTS = [
    cfg.IntOpt(
        'f5_agent_group_number',
        default=1,
        help='F5 LBaaS Agent group number'
    )
]

cfg.CONF.register_opts(OPTS)


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

    def schedule(self, plugin, context, lb_id, env=None):

        # If LB is already hosted on an agent, return this agent
        agent = plugin.db.get_agent_hosting_loadbalancer(context, lb_id)

        if agent:
            if agent["agent"]["alive"] and \
               agent["agent"]["admin_state_up"]:
                return agent["agent"]
            else:
                # Agent is not active or BIG-IP state is wrong
                raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                    loadbalancer_id=lb_id)

        # It is a new LB, load LB content
        # TODO(qzhao): Driver should already have lb content.
        # Need to optimize it in the future.
        lb = plugin.db.get_loadbalancer(context, lb_id)
        lb = LoadBalancer(**lb) if type(lb) == dict else lb

        # Load all LBaaS Agents
        candidates = []
        candidates = plugin.db.get_lbaas_agents(context, active=True)
        if len(candidates) <= 0:
            raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                loadbalancer_id=lb_id)

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
                loadbalancer_id=lb_id)
        else:
            chosen_agent = candidates[0]
            binding = agent_scheduler.LoadbalancerAgentBinding()
            binding.agent = chosen_agent
            binding.loadbalancer_id = lb_id
            context.session.add(binding)
            LOG.info("LB %s is scheduled to agent %s",
                     lb_id, chosen_agent["id"])
            return chosen_agent


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

        result = []
        if not az:
            for candidate in candidates:
                if not candidate["availability_zone"]:
                    result.append(candidate)
        else:
            for candidate in candidates:
                if candidate["availability_zone"] == az:
                    result.append(candidate)

        return result


class TenantScheduler(agent_scheduler.ChanceScheduler):
    """Finds an available agent for the tenant/environment."""

    def __init__(self):
        """Initialze with the ChanceScheduler base class."""
        super(TenantScheduler, self).__init__()

    def get_lbaas_agent_hosting_loadbalancer(self, plugin, context,
                                             loadbalancer_id, env=None):
        """Return the agent that is hosting the loadbalancer."""
        LOG.debug('Getting agent for loadbalancer %s with env %s' %
                  (loadbalancer_id, env))

        with context.session.begin(subtransactions=True):
            # returns {'agent': agent_dict}
            lbaas_agent = plugin.db.get_agent_hosting_loadbalancer(
                context,
                loadbalancer_id
            )
            # if the agent bound to this loadbalancer is alive, return it
            if lbaas_agent is not None:
                if (not lbaas_agent['agent']['alive'] or
                        not lbaas_agent['agent']['admin_state_up']) and \
                        env is not None:
                    # The agent bound to this loadbalancer is not live
                    # or is not active. Find another agent in the same
                    # environment and environment group if possible
                    ac = self.deserialize_agent_configurations(
                        lbaas_agent['agent']['configurations']
                    )
                    # get a environment group number for the bound agent
                    if 'environment_group_number' in ac:
                        gn = ac['environment_group_number']
                    else:
                        gn = 1

                    reassigned_agent = self.rebind_loadbalancers(
                        context, plugin, env, gn, lbaas_agent['agent'])
                    if reassigned_agent:
                        lbaas_agent = {'agent': reassigned_agent}
                    else:
                        raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                            loadbalancer_id=loadbalancer_id)

            return lbaas_agent

    def rebind_loadbalancers(
            self, context, plugin, env, group, current_agent):
        env_agents = self.get_agents_in_env(context, plugin, env,
                                            group=group, active=True)
        if env_agents:
            reassigned_agent = env_agents[0]
            bindings = \
                context.session.query(
                    agent_scheduler.LoadbalancerAgentBinding).filter_by(
                        agent_id=current_agent['id']).all()
            for binding in bindings:
                binding.agent_id = reassigned_agent['id']
                context.session.add(binding)
            LOG.debug("%s Loadbalancers bound to agent %s now bound to %s" %
                      (len(bindings),
                       current_agent['id'],
                       reassigned_agent['id']))
            return reassigned_agent
        else:
            return None

    def get_dead_agents_in_env(
            self, context, plugin, env, group=None):
        return_agents = []
        all_agents = self.get_agents_in_env(context,
                                            plugin,
                                            env,
                                            group,
                                            active=None)

        for agent in all_agents:

            if not plugin.db.is_eligible_agent(active=True, agent=agent):
                agent_dead = plugin.db.is_agent_down(
                    agent['heartbeat_timestamp'])
                if not agent['admin_state_up'] or agent_dead:
                    return_agents.append(agent)
        return return_agents

    def scrub_dead_agents(self, context, plugin, env, group=None):
        dead_agents = self.get_dead_agents_in_env(context, plugin, env, group)
        for agent in dead_agents:
            self.rebind_loadbalancers(context, plugin, env, group, agent)

    def get_agents_in_env(
            self, context, plugin, env, group=None, active=None):
        """Get an active agents in the specified environment."""
        return_agents = []

        with context.session.begin(subtransactions=True):
            candidates = []
            try:
                candidates = plugin.db.get_lbaas_agents(context, active=active)
            except Exception as ex:
                LOG.error("Exception retrieving agent candidates for "
                          "scheduling: {}".format(ex))

            for candidate in candidates:
                ac = self.deserialize_agent_configurations(
                    candidate['configurations'])
                if 'environment_prefix' in ac:
                    if ac['environment_prefix'] == env:
                        if group:
                            if ('environment_group_number' in ac and
                                    ac['environment_group_number'] == group):
                                return_agents.append(candidate)
                        else:
                            return_agents.append(candidate)

        return return_agents

    def get_agents_hosts_in_env(
            self, context, plugin, env):
        """Get an active agents in the specified environment."""
        # TODO(xie)
        # maybe replace： get_agent-id-hosting-the-lb
        return_agents_hosts = []

        with context.session.begin(subtransactions=True):
            candidates = []
            try:
                candidates = plugin.db.get_lbaas_agents(context)
            except Exception as ex:
                LOG.error("Exception retrieving agent candidates for "
                          "scheduling: {}".format(ex))

            for candidate in candidates:
                ac = self.deserialize_agent_configurations(
                    candidate['configurations'])
                if 'environment_prefix' in ac:
                    if ac['environment_prefix'] == env:
                        return_agents_hosts.append(candidate['host'])
                        # TODO(xie) check form here later.
        return return_agents_hosts

    def get_capacity(self, configurations):
        """Get environment capacity."""
        if 'environment_capacity_score' in configurations:
            return configurations['environment_capacity_score']
        else:
            return 0.0

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

    def schedule(self, plugin, context, loadbalancer_id, env=None):
        """Schedule the loadbalancer to an active loadbalancer agent.

        If there is no enabled agent hosting it.
        """

        with context.session.begin(subtransactions=True):
            # If the loadbalancer is hosted on an active agent
            # already, return that agent or one in its env
            lbaas_agent = self.get_lbaas_agent_hosting_loadbalancer(
                plugin,
                context,
                loadbalancer_id,
                env
            )

            if lbaas_agent:
                lbaas_agent = lbaas_agent['agent']
                LOG.debug(' Assigning task to agent %s.'
                          % (lbaas_agent['id']))
                return lbaas_agent

            # moving this part here so that this db call basically only called
            # while creating lb. If it was for creating lb, then this call
            # returns immediately. For other ops, it should have returned
            # already above, so this db call is avoided.
            LOG.info('get_loadbalancer start inside schedule')
            loadbalancer = plugin.db.get_loadbalancer(context, loadbalancer_id)
            loadbalancer = LoadBalancer(**loadbalancer) \
                if type(loadbalancer) == dict else loadbalancer
            LOG.info('get_loadbalancer end inside schedule')

            # There is no existing loadbalancer agent binding.
            # Find all active agent candidates in this env.
            # We use environment_prefix to find F5® agents
            # rather then map to the agent binary name.
            candidates = self.get_agents_in_env(
                context,
                plugin,
                env,
                active=True
            )

            LOG.debug("candidate agents: %s", candidates)
            if len(candidates) == 0:
                LOG.error('No f5 lbaas agents are active for env %s' % env)
                raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                    loadbalancer_id=loadbalancer.id)

            # We have active candidates to choose from.
            # Qualify them by tenant affinity and then capacity.
            chosen_agent = None
            agents_by_group = defaultdict(list)
            capacity_by_group = {}

            for candidate in candidates:
                # Organize agents by their environment group
                # and collect each group's max capacity.
                ac = self.deserialize_agent_configurations(
                    candidate['configurations']
                )
                gn = 1
                if 'environment_group_number' in ac:
                    gn = ac['environment_group_number']
                agents_by_group[gn].append(candidate)

                # populate each group's capacity
                group_capacity = self.get_capacity(ac)
                if gn not in capacity_by_group:
                    capacity_by_group[gn] = group_capacity
                else:
                    if group_capacity > capacity_by_group[gn]:
                        capacity_by_group[gn] = group_capacity

                # ---------------------------------------------------------
                # NOTE(qzhao): Skip to evaluate tenant affinity, because it
                # cost much time to load loadbalancers from neutron db.
                # ---------------------------------------------------------
                # Do we already have this tenant assigned to this
                # agent candidate? If we do and it has capacity
                # then assign this loadbalancer to this agent.
                # assigned_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                #     context, candidate['id'])
                # for assigned_lb in assigned_lbs:
                #     if loadbalancer.tenant_id == assigned_lb.tenant_id:
                #         chosen_agent = candidate
                #         break

                if chosen_agent:
                    # Does the agent which had tenants assigned
                    # to it still have capacity?
                    if group_capacity >= 1.0:
                        chosen_agent = None
                    else:
                        break

            # If we don't have an agent with capacity associated
            # with our tenant_id, let's pick an agent based on
            # the group with the lowest capacity score.
            if not chosen_agent:
                # lets get an agent from the group with the
                # lowest capacity score
                lowest_utilization = 1.0
                selected_group = 1
                for group, capacity in capacity_by_group.items():
                    if capacity < lowest_utilization:
                        lowest_utilization = capacity
                        selected_group = group

                LOG.debug('%s group %s scheduled with capacity %s'
                          % (env, selected_group, lowest_utilization))
                if lowest_utilization < 1.0:
                    # Choose a agent in the env group for this
                    # tenant at random.
                    chosen_agent = random.choice(
                        agents_by_group[selected_group]
                    )

            # If there are no agents with available capacity, raise exception
            if not chosen_agent:
                LOG.warn('No capacity left on any agents in env: %s' % env)
                LOG.warn('Group capacity in environment %s were %s.'
                         % (env, capacity_by_group))
                raise lbaas_agentschedulerv2.NoEligibleLbaasAgent(
                    loadbalancer_id=loadbalancer.id)

            binding = agent_scheduler.LoadbalancerAgentBinding()
            binding.agent = chosen_agent
            binding.loadbalancer_id = loadbalancer.id
            context.session.add(binding)

            LOG.debug(('Loadbalancer %(loadbalancer_id)s is scheduled to '
                       'lbaas agent %(agent_id)s'),
                      {'loadbalancer_id': loadbalancer.id,
                       'agent_id': chosen_agent['id']})

            return chosen_agent


class MultiAgentScheduler(TenantScheduler):

    def __init__(self):
        super(MultiAgentScheduler, self).__init__()

    def schedule(self, plugin, context, loadbalancer_id, env=None):
        with context.session.begin(subtransactions=True):
            loadbalancer = plugin.db.get_loadbalancer(context, loadbalancer_id)
            # If the loadbalancer is hosted on an active agent
            # already, return that agent or one in its env
            lbaas_agent = self.get_lbaas_agent_hosting_loadbalancer(
                plugin,
                context,
                loadbalancer.id,
                env
            )
            if lbaas_agent:
                lbaas_agent = lbaas_agent['agent']
                LOG.debug(' Assigning task to agent %s.'
                          % (lbaas_agent['id']))
                return lbaas_agent

            if cfg.CONF.f5_agent_group_number <= 1:
                group = None
            else:
                # If driver configuration explicitly
                # declares two or more agent groups,
                # the driver will attempts to assign
                # request to a specific agent group
                # according to the hash value of router id.
                subnet = plugin.db._core_plugin.get_subnet(
                    context,
                    loadbalancer.vip_subnet_id
                )
                filters = {
                    'device_owner': ['network:router_interface'],
                    'network_id': [subnet['network_id']]
                }
                ports = plugin.db._core_plugin.get_ports(context, filters)
                # Assuming only one router is associated with a network
                if ports and ports[0]['device_id']:
                    group = ord(
                        ports[0]['device_id'][-1]
                    ) % cfg.CONF.f5_agent_group_number + 1
                    LOG.debug('Schedule agent in group %d', group)
                else:
                    LOG.error(
                        'Cannot find a router for subnet %s' %
                        loadbalancer.vip_subnet_id)
                    raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                        loadbalancer_id=loadbalancer.id)

            # There is no existing loadbalancer agent binding.
            # Find all active agent candidates in this env.
            # We use environment_prefix to find F5® agents
            # rather then map to the agent binary name.
            candidates = self.get_agents_in_env(
                context,
                plugin,
                env,
                group=group,
                active=True
            )

            LOG.debug("candidate agents: %s", candidates)
            if len(candidates) == 0:
                LOG.error('No f5 lbaas agents are active for env %s' % env)
                raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                    loadbalancer_id=loadbalancer.id)
            # We have active candidates to choose from.
            # Qualify them by tenant affinity and then capacity.
            chosen_agent = None
            agents_by_group = defaultdict(list)
            capacity_by_group = {}
            for candidate in candidates:
                # Organize agents by their environment group
                # and collect each group's max capacity.
                ac = self.deserialize_agent_configurations(
                    candidate['configurations']
                )
                gn = 1
                if 'environment_group_number' in ac:
                    gn = ac['environment_group_number']
                agents_by_group[gn].append(candidate)
                # populate each group's capacity
                group_capacity = self.get_capacity(ac)
                if gn not in capacity_by_group:
                    capacity_by_group[gn] = group_capacity
                else:
                    if group_capacity > capacity_by_group[gn]:
                        capacity_by_group[gn] = group_capacity

                # ---------------------------------------------------------
                # NOTE(qzhao): Skip to evaluate tenant affinity, because it
                # cost much time to load loadbalancers from neutron db.
                # ---------------------------------------------------------
                # Do we already have this tenant assigned to this
                # agent candidate? If we do and it has capacity
                # then assign this loadbalancer to this agent.
                # assigned_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                #     context, candidate['id'])
                # for assigned_lb in assigned_lbs:
                #     if loadbalancer.tenant_id == assigned_lb.tenant_id:
                #         chosen_agent = candidate
                #         break

                if chosen_agent:
                    # Does the agent which had tenants assigned
                    # to it still have capacity?
                    if group_capacity >= 1.0:
                        chosen_agent = None
                    else:
                        break
            # If we don't have an agent with capacity associated
            # with our tenant_id, let's pick an agent based on
            # the group with the lowest capacity score.
            if not chosen_agent:
                # lets get an agent from the group with the
                # lowest capacity score
                lowest_utilization = 1.0
                selected_group = 1
                for group, capacity in capacity_by_group.items():
                    if capacity < lowest_utilization:
                        lowest_utilization = capacity
                        selected_group = group
                LOG.debug('%s group %s scheduled with capacity %s'
                          % (env, selected_group, lowest_utilization))
                if lowest_utilization < 1.0:
                    # Choose a agent in the env group for this
                    # tenant at random.
                    chosen_agent = random.choice(
                        agents_by_group[selected_group]
                    )
            # If there are no agents with available capacity, raise exception
            if not chosen_agent:
                LOG.warn('No capacity left on any agents in env: %s' % env)
                LOG.warn('Group capacity in environment %s were %s.'
                         % (env, capacity_by_group))
                raise lbaas_agentschedulerv2.NoEligibleLbaasAgent(
                    loadbalancer_id=loadbalancer.id)
            binding = agent_scheduler.LoadbalancerAgentBinding()
            binding.agent = chosen_agent
            binding.loadbalancer_id = loadbalancer.id
            context.session.add(binding)
            LOG.debug(('Loadbalancer %(loadbalancer_id)s is scheduled to '
                       'lbaas agent %(agent_id)s'),
                      {'loadbalancer_id': loadbalancer.id,
                       'agent_id': chosen_agent['id']})
            return chosen_agent
