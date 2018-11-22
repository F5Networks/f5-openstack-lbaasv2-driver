# coding=utf-8
u"""F5 Networks® LBaaSv2 Driver Implementation."""
# Copyright (c) 2016-2018, F5 Networks, Inc.
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

import os
import sys

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from neutron.plugins.common import constants as plugin_constants
from neutron_lib import constants as q_const

from neutron_lbaas.db.loadbalancer import models
from neutron_lbaas.extensions import lbaas_agentschedulerv2

from f5lbaasdriver.v2.bigip import agent_rpc
from f5lbaasdriver.v2.bigip import driver_v2
from f5lbaasdriver.v2.bigip import exceptions as f5_exc
from f5lbaasdriver.v2.bigip import neutron_client
from f5lbaasdriver.v2.bigip import plugin_rpc

LOG = logging.getLogger(__name__)

class LoadBalancerManager(driver_v2.LoadBalancerManager):
    """LoadBalancerManager class handles Neutron LBaaS CRUD."""

    @log_helpers.log_method_call
    def create(self, context, loadbalancer):
        """Create a loadbalancer."""
        driver = self.driver
        self.loadbalancer = loadbalancer
        try:
            agent, service = self._schedule_agent_create_service(context)
            agent_host = agent['host']
            agent_config = agent.get('configurations', {})
            LOG.debug("agent configurations: %s" % agent_config)

            scheduler = self.driver.scheduler
            agent_config_dict = \
                scheduler.deserialize_agent_configurations(agent_config)

            if not agent_config_dict.get('nova_managed', False):
                # Update the port for the VIP to show ownership by this driver
                port_data = {
                    'admin_state_up': True,
                    'device_owner': 'network:f5lbaasv2',
                    'status': q_const.PORT_STATUS_ACTIVE
                }
                port_data[portbindings.HOST_ID] = agent_host
                port_data[portbindings.VNIC_TYPE] = "normal"
                port_data[portbindings.PROFILE] = {}
                driver.plugin.db._core_plugin.update_port(
                    context,
                    loadbalancer.vip_port_id,
                    {'port': port_data}
                )
            else:
                LOG.debug("Agent devices are nova managed")

            driver.agent_rpc.create_loadbalancer(
                context, loadbalancer.to_api_dict(), service, agent_host)

        except (lbaas_agentschedulerv2.NoEligibleLbaasAgent,
                lbaas_agentschedulerv2.NoActiveLbaasAgent) as e:
            LOG.error("Exception: loadbalancer create: %s" % e)
            driver.plugin.db.update_status(
                context,
                models.LoadBalancer,
                loadbalancer.id,
                plugin_constants.ERROR)
        except Exception as e:
            LOG.error("Exception: loadbalancer create: %s" % e.message)
            raise e


class ListenerManager(driver_v2.ListenerManager):
    """ListenerManager class handles Neutron LBaaS listener CRUD."""

    def __init__(self, plugin=None, env=None):
        super(ListenerManager, self).__init__(plugin, env)
        LOG.info("Do customized initializing.")


class ListenerManager(driver_v2.ListenerManager):
    pass


class PoolManager(driver_v2.PoolManager):
    pass


class MemberManager(driver_v2.MemberManager):
    pass


class HealthMonitorManager(driver_v2.HealthMonitorManager):
    pass


class L7PolicyManager(driver_v2.L7PolicyManager):
    pass


class L7RuleManager(driver_v2.L7RuleManager):
    pass
