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

import datetime
import json

from oslo_log import log as logging

from neutron.db import agents_db
from neutron.db import models_v2 as core_db
from neutron.db import portbindings_db

from f5lbaasdriver.v2.bigip import constants

LOG = logging.getLogger(__name__)


class LBaaSv2ServiceBuilder(object):

    def __init__(self, driver=None):
        self.driver = driver
        self.net_cache = {}
        self.subnet_cache = {}

    def build(self, context, loadbalancer_id=None):
        """Get full service definition from loadbalancer id.

        :param context: neutron context
        :param loadbalancer_id:
        """

        # invalidate cache if it is too old
        if (datetime.datetime.now() - self.last_cache_update).seconds \
                > constants.NET_CACHE_SECONDS:
            self.net_cache = {}
            self.subnet_cache = {}

        service = {}
        with context.session.begin(subtransactions=True):
            LOG.debug('Building service definition entry for %s' %
                      loadbalancer_id)
            # Start with neutron pool definition
            try:
                loadbalancer = self.driver.plugin.get_loadbalancer(
                    context,
                    loadbalancer_id
                )
                LOG.debug('returned loadbalancer %s' % loadbalancer)
                loadbalancer_dict = self._get_extended_loadbalancer(
                    context,
                    loadbalancer
                )
                LOG.debug('returned loadbalancer dict %s' % loadbalancer_dict)
                loadbalancer_dict['listeners'] = []
                for listener in loadbalancer.listeners:
                    listener_dict = self._get_extended_listener(
                        context,
                        listener
                    )
                    pool = listener.default_pool
                    pool_dict = self._get_extended_pool(
                        context,
                        pool
                    )
                    listener_dict['default_pool'] = pool_dict
                    loadbalancer_dict['listeners'].append(listener_dict)
                service['loadbalancer'] = loadbalancer_dict

            # TODO(JL): figure out correct exception
            except Exception:
                LOG.error("Loadbalancer not found %s" %
                          loadbalancer_id)
                return {}
        LOG.debug('Built loadbalancer %s service: %s' %
                  (loadbalancer_id, service))
        return service

    def _make_loadbalancer_dict(self, loadbalancer):
        """Create a dictionary from the db loadbalanceer"""
        res = {'id': loadbalancer.id,
               'tenant_id': loadbalancer.tenant_id,
               'name': loadbalancer.name,
               'description': loadbalancer.description,
               'vip_subnet_id': loadbalancer.vip_subnet_id,
               'vip_port_id': loadbalancer.vip_port_id,
               'vip_address': loadbalancer.vip_address,
               'operating_status': loadbalancer.operating_status,
               'provisioning_status': loadbalancer.provisioning_status,
               'admin_state_up': loadbalancer.admin_state_up
               }
        return res

    def _get_extended_loadbalancer(self, context, loadbalancer):
        """Get Loadbalaner from Neutron and add extended data """
        loadbalancer_dict = self._make_loadbalancer_dict(loadbalancer)
        vip_subnet = self._get_subnet_cached(
            context,
            loadbalancer.vip_subnet_id
        )
        loadbalancer_dict['vip_subnet'] = vip_subnet
        vip_port = self.driver.core_plugin.get_port(
            context,
            loadbalancer.vip_port_id
        )
        loadbalancer_dict['vip_port'] = vip_port
        vip_port_network = self._get_network_cached(
            context,
            loadbalancer.vip_port['network_id']
        )
        loadbalancer_dict['vip_port']['network'] = vip_port_network
        return loadbalancer_dict

    def _make_listener_dict(self, context, listener):
        """Create a dictionary from the db listener"""
        res = {'id': listener.id,
               'tenant_id': listener.tenant_id,
               'name': listener.name,
               'description': listener.description,
               'protocol': listener.protocol,
               'protocol_port': listener.protocol_port,
               'connection_limit': listener.connection_limit,
               'loadbalancer_id': listener.loadbalancer_id,
               'default_pool_id': listener.default_pool_id,
               'admin_state_up': listener.admin_state_up,
               'provisioning_status': listener.provisioning_status,
               'operating_status': listener.operating_status,
               'default_tls_container_id': listener.default_tls_container_id
               }
        return res

    def _get_extended_listener(self, context, listener):
        """Get Listener from Neutron and add extended data """
        listener_dict = self._make_listener_dict(context, listener)
        # TODO(JL): Need to handle certificate
        return listener_dict

    def _make_healthmonitor_dict(self, context, healthmonitor):
        """Create a healthmonitor from db healthmonitor """
        res = {'id': healthmonitor.id,
               'tenant_id': healthmonitor.tenant_id,
               'type': healthmonitor.type,
               'delay': healthmonitor.delay,
               'timeout': healthmonitor.timeout,
               'max_retries': healthmonitor.max_retries,
               'http_method': healthmonitor.http_method,
               'url_path': healthmonitor.url_path,
               'expected_codes': healthmonitor.expected_codes,
               'admin_state_up': healthmonitor.admin_state_up,
               'provisioning_status': healthmonitor.provisioning_status
               }
        return res

    def _make_pool_dict(self, context, pool):
        """Create a pool from db pool """
        res = {'id': pool.id,
               'tenant_id': pool.tenant_id,
               'name': pool.name,
               'description': pool.description,
               'protocol': pool.protocol,
               'lb_algorithm': pool.lb_algorithm,
               'healthmonitor_id': pool.healthmonitor_id,
               'admin_state_up': pool.admin_state_up,
               'provisioning_status': pool.provisioning_status,
               'operating_status': pool.operating_status
               }
        return res

    def _make_member_dict(self, context, member):
        """Create a member from db member """
        res = {'id': member.id,
               'tenant_id': member.tenant_id,
               'pool_id': member.pool_id,
               'subnet_id': member.subnet_id,
               'address': member.address,
               'protocol_port': member.protocol_port,
               'weight': member.weight,
               'admin_state_up': member.admin_state_up,
               'provisioning_status': member.provisioning_status,
               'operating_status': member.operating_status
               }
        return res

    def _extend_member_dict_from_address(self, context, member_dict):
        """Get member networking from IP address """
        alloc_qry = context.session.query(core_db.IPAllocation)
        allocated = alloc_qry.filter_by(
            ip_address=member_dict['address']
        ).all()
        matching_keys = {
            'tenant_id': member_dict['tenant_id'],
            'subnet_id': member_dict['subnet_id'],
            'shared': None
        }
        return self._found_and_used_neutron_addr(
            context,
            member_dict,
            allocated,
            matching_keys
        )

    def _found_and_used_neutron_addr(
            self, context, member_dict, allocated, matching_keys):
        """Find a matching address that matches keys """
        member_dict['network'] = None,
        member_dict['subnet'] = None,
        member_dict['port'] = None,
        member_dict['vtep_address'] = None
        for alloc in allocated:
            if matching_keys['subnet_id'] and \
                    alloc['subnet_id'] != matching_keys['subnet_id']:
                continue

            try:
                net = self._get_network_cached(context,
                                               alloc['network_id'])
            except Exception:
                continue
            if matching_keys['tenant_id'] and \
                    net['tenant_id'] != matching_keys['tenant_id']:
                continue
            if matching_keys['shared'] and not net['shared']:
                continue

            member_dict['network'] = net
            member_dict['subnet'] = self._get_subnet_cached(
                context,
                alloc['subnet_id']
            )
            member_dict['port'] = self._core_plugin().get_port(
                context,
                alloc['port_id']
            )
            if member_dict['network']['provider:network_type'] in \
                    constants.TUNNEL_TYPES:
                member_dict['vtep_address'] = self._get_vtep_address(
                    context,
                    member_dict['port']['id']
                )
            else:
                member_dict['vtep_address'] = None
        return member_dict

    def _extend_member_dict(self, context, member_dict, subnet_id, address):
        member_subnet = self._get_subnet_cached(
            context,
            subnet_id
        )
        if member_subnet:
            member_dict['subnet'] = member_subnet
            member_network = self._get_network_cached(
                context,
                member_dict['subnet']['network_id']
            )
            member_dict['network'] = member_network
            if member_network:
                member_port = self._get_port(
                    context,
                    member_dict['network']['id'],
                    subnet_id,
                    address
                )
                if member_port:
                    member_dict['port'] = member_port
                    if member_dict['network']['provider:network_type'] in \
                            constants.TUNNEL_TYPES:
                        member_dict['vtep_address'] = self._get_vtep_address(
                            context,
                            member_port['id']
                        )
                    else:
                        member_dict['vtep_address'] = None
                else:
                    member_dict['port'] = None
                    member_dict['vtep_address'] = None
            else:
                member_dict['port'] = None
        else:
            member_dict['subnet'] = None
            member_dict['network'] = None
            member_dict['port'] = None
            member_dict['vtep_address'] = None
        return member_dict

    def _get_extended_pool(self, context, pool):
        """Get Pool drom Neutron and added extended data """
        pool_dict = self._make_pool_dict(context, pool)
        healthmonitor = self.driver.plugin.get_healthmonitor(
            context,
            pool.healthmonitor_id
        )
        healthmonitor_dict = self._make_healthmonitor_dict(
            context,
            healthmonitor
        )
        pool_dict['healthmonitor'] = healthmonitor_dict
        pool_dict['members'] = []
        for member in pool.members:
            member_dict = self._make_member_dict(context, member)
            if member_dict['subnet_id']:
                member_dict = self._extend_member_dict(
                    context,
                    member_dict,
                    member_dict['subnet_id'],
                    member_dict['address']
                )
            else:
                member_dict = self._extend_member_dict_from_address(
                    context,
                    member_dict
                )
            pool_dict['members'].append(member_dict)
        return pool_dict

    def _get_port(self, context, network_id, subnet_id, address):
        alloc_qry = context.session.query(core_db.IPAllocation)
        allocated = alloc_qry.filter_by(
            ip_address=address,
            subnet_id=subnet_id,
            network_id=network_id
        ).all()
        for alloc in allocated:
            port = self.driver.core_plugin.get_port(
                context,
                alloc['port_id']
            )
            return port
        return None

    def _get_vtep_address(self, context, port_id):
        if port_id:
            binding_qry = context.session.query(
                portbindings_db.PortBindingPort
            )
            bound = binding_qry.filter_by(
                port_id=port_id
            ).all()
            for binding in bound:
                host = binding['host']
                agent_qry = context.session.query(agents_db.Agent)
                agents = agent_qry.filter_by(
                    host=host
                ).all()
                for agent in agents:
                    agent_conf = json.loads(agent.configurations)
                    if 'tunneling_ip' in agent_conf:
                        return agent_conf['tunneling_ip']
            return None
        else:
            return None

    def _get_subnet_cached(self, context, subnet_id):
        """subnet from cache or get from neutron """
        if subnet_id not in self.subnet_cache:
            subnet_dict = self.driver.core_plugin.get_subnet(
                context,
                subnet_id
            )
            self.subnet_cache[subnet_id] = subnet_dict
        return self.subnet_cache[subnet_id]

    def _get_network_cached(self, context, network_id):
        """network from cache or get from neutron """
        if network_id not in self.net_cache:
            net_dict = self.driver.core_plugin.get_network(
                context,
                network_id
            )
            if 'provider:network_type' not in net_dict:
                net_dict['provider:network_type'] = 'undefined'
            if 'provider:segmentation_id' not in net_dict:
                net_dict['provider:segmentation_id'] = 0
            self.net_cache[network_id] = net_dict
        return self.net_cache[network_id]
