"""Service Module for F5 LBaaSv2."""
# Copyright 2014 F5 Networks Inc.
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
import datetime

from oslo_log import helpers as log_helpers
from oslo_log import log as logging

from f5lbaasdriver.v2.bigip import constants_v2

LOG = logging.getLogger(__name__)


class LBaaSv2ServiceBuilder(object):
    """The class creates a service definition from neutron database.

    A service definition represents all the information required to
    construct a load-balancing service on BigIP.

    Requests come in to agent as full service definitions, not incremental
    changes. The driver looks up networks, mac entries, segmentation info,
    etc and places all information in a service object (which is a python
    dictionary variable) and passes that to the agent.

    """

    def __init__(self, driver):
        """Get full service definition from loadbalancer id."""
        self.driver = driver

        self.net_cache = {}
        self.subnet_cache = {}
        self.last_cache_update = datetime.datetime.fromtimestamp(0)
        self.plugin = self.driver.plugin

    def build(self, context, loadbalancer):
        """Get full service definition from loadbalancer ID."""
        # Invalidate cache if it is too old
        if ((datetime.datetime.now() - self.last_cache_update).seconds >
                constants_v2.NET_CACHE_SECONDS):
            self.net_cache = {}
            self.subnet_cache = {}

        service = {}
        with context.session.begin(subtransactions=True):
            LOG.debug('Building service definition entry for %s'
                      % loadbalancer.id)

            # Start with the neutron loadbalancer definition
            service['loadbalancer'] = self._get_extended_loadbalancer(
                context,
                loadbalancer
            )

            LOG.debug('returned ladbalancer %s' % service['loadbalancer'])

            service['subnets'] = []
            subnet = self._get_subnet_cached(
                context,
                loadbalancer.vip_subnet_id
            )
            service['subnets'].append(subnet)

            service['networks'] = []
            vip_port = service['loadbalancer']['vip_port']
            network = self._get_network_cached(
                context,
                vip_port['network_id']
            )
            service['networks'].append(network)

            service['listeners'] = []
            service['pools'] = []
            listeners = self.plugin.db.get_listeners(
                context,
                filters={'loadbalancer_id': [loadbalancer.id]}
            )
            for listener in listeners:
                listener_dict = listener.to_dict(
                    loadbalancer=False,
                    default_pool=False
                )
                if listener.default_pool:
                    listener_dict['default_pool_id'] = listener.default_pool.id

                service['listeners'].append(listener_dict)

                if listener.default_pool:
                    pool = self.plugin.db.get_pool(
                        context,
                        listener.default_pool.id)
                    pool_dict = pool.to_api_dict()
                    pool_dict['provisioning_status'] = pool.provisioning_status
                    pool_dict['operating_status'] = pool.operating_status
                    service['pools'].append(pool_dict)

            service['members'] = []
            service['healthmonitors'] = []
            for pool in service['pools']:
                pool_id = pool['id']
                members = self.plugin.db.get_pool_members(
                    context,
                    filters={'pool_id': [pool_id]}
                )
                for member in members:
                    service['members'].append(member.to_dict(pool=False))

                healthmonitor_id = pool['healthmonitor_id']
                if healthmonitor_id:
                    healthmonitor = self.plugin.db.get_healthmonitor(
                        context,
                        healthmonitor_id)
                    if healthmonitor:
                        healthmonitor_dict = healthmonitor.to_dict(pool=False)
                        healthmonitor_dict['pool_id'] = pool_id
                        service['healthmonitors'].append(
                            healthmonitor_dict)

        return service

    @log_helpers.log_method_call
    def _get_extended_loadbalancer(self, context, loadbalancer):
        """Get loadbalancer dictionary and add extended data(e.g. VIP)."""
        loadbalancer_dict = loadbalancer.to_api_dict()
        vip_port = self.plugin.db._core_plugin.get_port(
            context,
            loadbalancer.vip_port_id
        )
        loadbalancer_dict['vip_port'] = vip_port

        return loadbalancer_dict

    @log_helpers.log_method_call
    def _get_subnet_cached(self, context, subnet_id):
        """Retrieve subnet from cache if available; otherwise, from Neutron."""
        if subnet_id not in self.subnet_cache:
            subnet = self.plugin.db._core_plugin.get_subnet(
                context,
                subnet_id
            )
            self.subnet_cache[subnet_id] = subnet
        return self.subnet_cache[subnet_id]

    @log_helpers.log_method_call
    def _get_network_cached(self, context, network_id):
        """Retrieve network from cache or from Neutron."""
        if network_id not in self.net_cache:
            network = self.plugin.db._core_plugin.get_network(
                context,
                network_id
            )
            if 'provider:network_type' not in network:
                network['provider:network_type'] = 'undefined'
            if 'provider:segmentation_id' not in network:
                network['provider:segmentation_id'] = 0
            self.net_cache[network_id] = network

        return self.net_cache[network_id]

    @log_helpers.log_method_call
    def _get_listener(self, context, listener_id):
        """Retrieve listener from Neutron db."""
        listener = self.plugin.db.get_listener(
            context,
            listener_id
        )
        return listener.to_api_dict()
