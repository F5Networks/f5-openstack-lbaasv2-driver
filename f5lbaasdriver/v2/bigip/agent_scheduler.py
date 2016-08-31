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

from oslo_log import log as logging

from neutron_lbaas import agent_scheduler
from neutron_lbaas.extensions import lbaas_agentschedulerv2

LOG = logging.getLogger(__name__)


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

        lbaas_agent = None
        with context.session.begin(subtransactions=True):
            # returns {'agent': agent_dict}
            lbaas_agent = plugin.db.get_agent_hosting_loadbalancer(
                context,
                loadbalancer_id
            )
            # if the agent bound to this loadbalancer is alive, return it
            if lbaas_agent is not None:

                if not lbaas_agent['agent']['alive'] and env is not None:
                    # The agent bound to this loadbalancer is not live;
                    # find another agent in the same environment
                    # which environment group is the agent in
                    ac = self.deserialize_agent_configurations(
                        lbaas_agent['agent']['configurations']
                    )
                    # get a environment group number for the bound agent
                    if 'environment_group_number' in ac:
                        gn = ac['environment_group_number']
                    else:
                        gn = 1

                    # find all active agents matching the environment
                    # and group number.
                    env_agents = self.get_active_agents_in_env(
                        context,
                        plugin,
                        env,
                        gn
                    )
                    LOG.debug("Primary lbaas agent is dead, env_agents: %s",
                              env_agents)
                    if env_agents:
                        # return the first active agent in the
                        # group to process this task
                        lbaas_agent = {'agent': env_agents[0]}

            return lbaas_agent

    def get_active_agents_in_env(self, context, plugin, env, group=None):
        """Get an active agents in the specified environment."""
        return_agents = []

        with context.session.begin(subtransactions=True):
            candidates = []
            try:
                candidates = plugin.db.get_lbaas_agents(context, active=True)
            except Exception:
                LOG.error("Caught Exception: get_lbaas_agents")

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

    def get_agents_in_env(self, context, plugin, env, group=None):
        """Get all agents in the specified environment."""
        return_agents = []

        with context.session.begin(subtransactions=True):
            candidates = []
            try:
                candidates = plugin.db.get_lbaas_agents(context)
            except Exception:
                LOG.error("Caught Exception: get_lbaas_agents")

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

    def get_capacity(self, configurations):
        """Get environment capacity."""
        if 'environment_capacity_score' in configurations:
            return configurations['environment_capacity_score']
        else:
            return 0.0

    def deserialize_agent_configurations(self, configurations):
        """Return a dictionary for the agent configuration."""
        agent_conf = configurations
        if not isinstance(agent_conf, dict):
            try:
                agent_conf = json.loads(configurations)
            except ValueError as ve:
                LOG.error('can not JSON decode %s : %s'
                          % (agent_conf, ve.message))
                agent_conf = {}
        return agent_conf

    def schedule(self, plugin, context, loadbalancer_id, env=None):
        """Schedule the loadbalancer to an active loadbalancer agent.

        If there is no enabled agent hosting it.
        """
        with context.session.begin(subtransactions=True):
            # Get the loadbalancer
            loadbalancer = plugin.db.get_loadbalancer(
                context,
                loadbalancer_id
            )

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

            # There is no existing loadbalancer agent binding.
            # Find all active agent candidates in this env.
            # We use environment_prefix to find F5® agents
            # rather then map to the agent binary name.
            candidates = self.get_active_agents_in_env(
                context,
                plugin,
                env
            )

            LOG.debug("candidate agents: %s", candidates)
            if len(candidates) == 0:
                LOG.warn('No f5 lbaas agents are active for env %s' % env)
                raise lbaas_agentschedulerv2.NoActiveLbaasAgent(
                    loadbalancer_id=loadbalancer.id)

            # We have active candidates to choose from.
            # Qualify them by tenant affinity and then capacity.
            chosen_agent = None
            agents_by_group = {}
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
                if gn not in agents_by_group.keys():
                    agents_by_group[gn] = []
                agents_by_group[gn].append(candidate)

                # populate each group's capacity
                group_capacity = self.get_capacity(ac)
                if gn not in capacity_by_group.keys():
                    capacity_by_group[gn] = group_capacity
                else:
                    # take the highest capacity score for
                    # all candidates in this environment group
                    if group_capacity > capacity_by_group[gn]:
                        capacity_by_group[gn] = group_capacity

                # Do we already have tenants assigned to this
                # agent candidate? If we do and it has capacity
                # then assign this loadbalancer to this agent.
                assigned_lbs = plugin.db.list_loadbalancers_on_lbaas_agent(
                    context, candidate['id'])
                for assigned_lb in assigned_lbs:
                    if loadbalancer.tenant_id == assigned_lb.tenant_id:
                        chosen_agent = candidate
                        break
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
                lowest_capacity = 1.0
                selected_group = 1
                for group in capacity_by_group:
                    if capacity_by_group[group] < lowest_capacity:
                        lowest_capacity = capacity_by_group[group]
                        selected_group = group
                LOG.debug('%s group %s scheduled with capacity %s'
                          % (env, selected_group, lowest_capacity))
                if lowest_capacity < 1.0:
                    # Choose a agent in the env group for this
                    # tenant at random.
                    chosen_agent = random.choice(
                        agents_by_group[selected_group]
                    )

            # If there are no agents with available capacity, raise exception
            if not chosen_agent:
                LOG.warn('No capacity left on any agents in env: %s' % env)
                LOG.warn('Group capacity in %s were %s.'
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
