# coding=utf-8
u"""F5 Networks® LBaaSv2 Driver Implementation."""
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

import os
import sys

from oslo_config import cfg
from oslo_log import helpers as log_helpers
from oslo_log import log as logging
from oslo_utils import importutils

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources
from neutron.plugins.common import constants as plugin_constants
from neutron_lib.api.definitions import portbindings
from neutron_lib import constants as q_const

from neutron_lbaas.db.loadbalancer import models
from neutron_lbaas.extensions import lbaas_agentschedulerv2

from f5lbaasdriver.v2.bigip import agent_rpc
from f5lbaasdriver.v2.bigip import exceptions as f5_exc
from f5lbaasdriver.v2.bigip import neutron_client
from f5lbaasdriver.v2.bigip import plugin_rpc
# from neutron.api.v2 import attributes
from neutron_lib import constants as n_const
from time import time

LOG = logging.getLogger(__name__)

OPTS = [
    cfg.IntOpt(
        'f5_driver_perf_mode',
        default=0,
        help=('switch driver performance mode from 0 to 3')
    ),
    cfg.StrOpt(
        'f5_loadbalancer_pool_scheduler_driver_v2',
        default=(
            'f5lbaasdriver.v2.bigip.agent_scheduler.TenantScheduler'
        ),
        help=('Driver to use for scheduling '
              'pool to a default loadbalancer agent')
    ),
    cfg.StrOpt(
        'f5_loadbalancer_service_builder_v2',
        default=(
            'f5lbaasdriver.v2.bigip.service_builder.LBaaSv2ServiceBuilder'
        ),
        help=('Default class to use for building a service object.')
    ),
    cfg.StrOpt(
        'bwc_profile',
        default=None,
        help='bwc_profile name which is configured in bigip side'
    ),
    cfg.StrOpt(
        'unlegacy_setting_placeholder_driver_side',
        default=None,
        help=('used in certain hpb cases to differenciate legacy scenarios')
    )
]

cfg.CONF.register_opts(OPTS)


class F5NoAttachedLoadbalancerException(f5_exc.F5LBaaSv2DriverException):
    """Exception thrown when an LBaaSv2 object has not parent Loadbalancer."""

    message = "Entity has no associated loadbalancer"

    def __str__(self):
        return self.message


class F5DriverV2(object):
    u"""F5 Networks® LBaaSv2 Driver."""

    def __init__(self, plugin=None, env=None):
        """Driver initialization."""
        if not plugin:
            LOG.error('Required LBaaS Driver and Core Driver Missing')
            sys.exit(1)

        self.plugin = plugin
        self.env = env

        self.loadbalancer = LoadBalancerManager(self)
        self.listener = ListenerManager(self)
        self.pool = PoolManager(self)
        self.member = MemberManager(self)
        self.healthmonitor = HealthMonitorManager(self)
        self.l7policy = L7PolicyManager(self)
        self.l7rule = L7RuleManager(self)

        self.unlegacy_setting_placeholder_driver_side = \
            cfg.CONF.unlegacy_setting_placeholder_driver_side

        # what scheduler to use for pool selection
        self.scheduler = importutils.import_object(
            cfg.CONF.f5_loadbalancer_pool_scheduler_driver_v2)

        self.service_builder = importutils.import_object(
            cfg.CONF.f5_loadbalancer_service_builder_v2, self)

        self.agent_rpc = agent_rpc.LBaaSv2AgentRPC(self)
        self.plugin_rpc = plugin_rpc.LBaaSv2PluginCallbacksRPC(self)

        self.q_client = \
            neutron_client.F5NetworksNeutronClient(self.plugin)

        # add this agent RPC to the neutron agent scheduler
        # mixins agent_notifiers dictionary for it's env
        self.plugin.agent_notifiers.update(
            {q_const.AGENT_TYPE_LOADBALANCER: self.agent_rpc})

        registry.subscribe(self._bindRegistryCallback(),
                           resources.PROCESS,
                           events.AFTER_INIT)

    def _bindRegistryCallback(self):
        # Defines a callback function with name tied to driver env. Need to
        # enusre unique name, as registry callback manager references callback
        # functions by name.
        def post_fork_callback(resources, event, trigger):
            LOG.debug("F5DriverV2 with env %s received post neutron child "
                      "fork notification pid(%d) print trigger(%s)" % (
                          self.env, os.getpid(), trigger))
            self.plugin_rpc.create_rpc_listener()

        post_fork_callback.__name__ += '_' + str(self.env)
        return post_fork_callback

    def _handle_driver_error(self, context, loadbalancer,
                             loadbalancer_id, status):
        pass


class EntityManager(object):
    '''Parent for all managers defined in this module.'''

    def __init__(self, driver):
        self.driver = driver

    def _log_entity(self, entity):
        LOG.debug("Log the entity: %s", entity.to_api_dict())

    def _call_rpc(self, context, loadbalancer, entity, api_dict,
                  rpc_method, **kwargs):
        '''Perform operations common to create and delete for managers.'''

        try:
            agent_host, service = self._setup_crud(
                context, loadbalancer, entity, **kwargs)
            rpc_callable = getattr(self.driver.agent_rpc, rpc_method)
            rpc_callable(
                context, api_dict, service, agent_host,
                **kwargs
            )
        except (lbaas_agentschedulerv2.NoEligibleLbaasAgent,
                lbaas_agentschedulerv2.NoActiveLbaasAgent) as e:
            LOG.error("Exception: %s: %s" % (rpc_method, e))
        except Exception as e:
            LOG.error("Exception: %s: %s" % (rpc_method, e))
            raise e

    def _setup_crud(self, context, loadbalancer, entity, **kwargs):
        '''Setup CRUD operations for managers to make calls to agent.

        :param context: auth context for performing CRUD operation
        :param entity: neutron lbaas entity -- target of the CRUD operation
        :returns: tuple -- (agent object, service dict)
        :raises: F5NoAttachedLoadbalancerException
        '''

        if entity.attached_to_loadbalancer() and loadbalancer:
            (agent, service) = self._schedule_agent_create_service(
                context, loadbalancer, entity, **kwargs)
            return agent['host'], service

        raise F5NoAttachedLoadbalancerException()

    def _schedule_agent_create_service(self, context, loadbalancer,
                                       entity=None, **kwargs):
        '''Schedule agent and build service--used for most managers.

        :param context: auth context for performing crud operation
        :returns: tuple -- (agent object, service dict)
        '''

        agent = self.driver.scheduler.schedule(
            self.driver.plugin,
            context,
            loadbalancer.id,
            self.driver.env
        )
        service = self.driver.service_builder.build(
            context, loadbalancer, agent, **kwargs)
        return agent, service

    @log_helpers.log_method_call
    def _append_listeners(self, context, service, listener):

        if not listener:
            return

        def get_db_listener():
            if cfg.CONF.f5_driver_perf_mode == 3:
                return listener
            else:
                return self.driver.plugin.db.get_listener(
                    context, listener.id)

        db_listener = get_db_listener()
        listener_dict = db_listener.to_dict(
            loadbalancer=False,
            default_pool=False,
            l7_policies=False
        )

        # Listener may have l7policies or default pool
        listener_dict['l7_policies'] = \
            [{'id': l7_policy.id} for l7_policy in listener.l7_policies]
        if listener.default_pool:
            listener_dict['default_pool_id'] = listener.default_pool.id

        LOG.debug("append listener %s", listener_dict)
        service['listeners'].append(listener_dict)

    @log_helpers.log_method_call
    def _append_pools_monitors(self, context, service, pool):

        if not pool:
            return

        def get_db_pool():
            if cfg.CONF.f5_driver_perf_mode == 3:
                return pool
            else:
                return self.driver.plugin.db.get_pool(
                    context, pool.id)

        db_pool = get_db_pool()

        pool_dict = db_pool.to_dict(
            healthmonitor=False,
            listener=False,
            listeners=False,
            loadbalancer=False,
            l7_policies=False,
            members=False,
            session_persistence=False
        )

        pool_dict['members'] = [{'id': member.id} for member in pool.members]
        pool_dict['l7_policies'] = [
            {'id': l7_policy.id} for l7_policy in pool.l7_policies]

        if pool.session_persistence:
            pool_dict['session_persistence'] = (
                pool.session_persistence.to_api_dict()
            )

        LOG.debug("append pool %s", pool_dict)
        service['pools'].append(pool_dict)

        if not pool.healthmonitor:
            return

        def get_db_healthmonitor():
            if cfg.CONF.f5_driver_perf_mode == 3:
                return pool.healthmonitor
            else:
                return self.driver.plugin.db.get_healthmonitor(
                    context,
                    pool.healthmonitor.id
                )

        healthmonitor = get_db_healthmonitor()
        healthmonitor_dict = healthmonitor.to_dict(pool=False)
        healthmonitor_dict['pool_id'] = pool.id

        LOG.debug("append healthmonitor_dict %s", healthmonitor_dict)
        service['healthmonitors'].append(healthmonitor_dict)


class LoadBalancerManager(EntityManager):
    """LoadBalancerManager class handles Neutron LBaaS CRUD."""

    @log_helpers.log_method_call
    def create(self, context, loadbalancer):
        """Create a loadbalancer."""

        self._log_entity(loadbalancer)

        driver = self.driver
        try:
            agent, service = self._schedule_agent_create_service(
                context, loadbalancer)
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
                if driver.unlegacy_setting_placeholder_driver_side:
                    LOG.debug('setting to normal')
                    port_data[portbindings.VNIC_TYPE] = "normal"
                else:
                    LOG.debug('setting to baremetal')
                    port_data[portbindings.VNIC_TYPE] = "baremetal"
                port_data[portbindings.PROFILE] = {}
                driver.plugin.db._core_plugin.update_port(
                    context,
                    loadbalancer.vip_port_id,
                    {'port': port_data}
                )
                # agent, service = self._schedule_agent_create_service(context)
                if driver.unlegacy_setting_placeholder_driver_side:
                    LOG.debug('calling extra build():')
                    service = self.driver.service_builder.build(
                        context, loadbalancer, agent)
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

    @log_helpers.log_method_call
    def update(self, context, old_loadbalancer, loadbalancer):
        """Update a loadbalancer."""

        self._log_entity(old_loadbalancer)
        self._log_entity(loadbalancer)

        driver = self.driver
        try:
            agent, service = self._schedule_agent_create_service(
                context, loadbalancer)
            agent_host = agent['host']

            driver.agent_rpc.update_loadbalancer(
                context,
                old_loadbalancer.to_api_dict(),
                loadbalancer.to_api_dict(),
                service,
                agent_host
            )
        except (lbaas_agentschedulerv2.NoEligibleLbaasAgent,
                lbaas_agentschedulerv2.NoActiveLbaasAgent) as e:
            LOG.error("Exception: loadbalancer update: %s" % e)
            driver._handle_driver_error(context,
                                        models.LoadBalancer,
                                        loadbalancer.id,
                                        plugin_constants.ERROR)
        except Exception as e:
            LOG.error("Exception: loadbalancer update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, loadbalancer):
        """Delete a loadbalancer."""

        self._log_entity(loadbalancer)

        driver = self.driver
        try:
            agent, service = self._schedule_agent_create_service(
                context, loadbalancer)
            agent_host = agent['host']

            # becuase the api calls is synchronized, here we try to
            # tell if the lb is the last lb in the project.
            # then we can delete partition and routedomain

            # from the cherry pick
            # there is no self.loadbalancer anymore, so modify this
            lbs = driver.plugin.db.get_loadbalancers(
                context,
                {"project_id": [loadbalancer.tenant_id]}
            )

            lb_dict = loadbalancer.to_api_dict()
            lb_dict["last_one"] = True

            for lb in lbs:
                # from the cherry pick
                # there is no self.loadbalancer anymore, so modify this
                if lb.id != loadbalancer.id:
                    if lb.provisioning_status in [
                        "ACTIVE", "ERROR",
                        "PENDING_CREATE", "PENDING_UPDATE"
                    ]:
                        lb_dict["last_one"] = False
                        break

            driver.agent_rpc.delete_loadbalancer(
                context, lb_dict, service, agent_host)

        except (lbaas_agentschedulerv2.NoEligibleLbaasAgent,
                lbaas_agentschedulerv2.NoActiveLbaasAgent) as e:
            LOG.error("Exception: loadbalancer delete: %s" % e)
            driver.plugin.db.delete_loadbalancer(context, loadbalancer.id)
        except Exception as e:
            LOG.error("Exception: loadbalancer delete: %s" % e)
            raise e

    @log_helpers.log_method_call
    def refresh(self, context, loadbalancer):
        """Refresh a loadbalancer."""
        pass

    @log_helpers.log_method_call
    def stats(self, context, loadbalancer):
        driver = self.driver
        try:
            agent = driver.scheduler.schedule(
                driver.plugin,
                context,
                loadbalancer.id,
                driver.env
            )
            service = driver.service_builder.build(context,
                                                   loadbalancer,
                                                   agent)
            driver.agent_rpc.update_loadbalancer_stats(
                context,
                loadbalancer.to_api_dict(),
                service,
                agent['host']
            )
        except (lbaas_agentschedulerv2.NoEligibleLbaasAgent,
                lbaas_agentschedulerv2.NoActiveLbaasAgent) as e:
            LOG.error("Exception: update_loadbalancer_stats: %s" % e.message)
            driver._handle_driver_error(context,
                                        models.LoadBalancer,
                                        loadbalancer.id,
                                        plugin_constants.ERROR)
        except Exception as e:
            LOG.error("Exception: update_loadbalancer_stats: %s" % e.message)
            raise e


class ListenerManager(EntityManager):
    """ListenerManager class handles Neutron LBaaS listener CRUD."""

    @log_helpers.log_method_call
    def create(self, context, listener):
        """Create a listener."""

        self._log_entity(listener)

        lb = listener.loadbalancer
        api_dict = listener.to_dict(loadbalancer=False, default_pool=False)

        def append_listeners(context, loadbalancer, service):
            self._append_listeners(context, service, listener)

        def append_pools_monitors(context, loadbalancer, service):
            if listener.default_pool:
                for pool in loadbalancer.pools:
                    if pool.id == listener.default_pool.id:
                        self._append_pools_monitors(context, service, pool)
                        break

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Listener may have default pool who are already created.
            # Utilize default behavior to append members
            # Listener does not have l7policies.
            self._call_rpc(
                context, lb, listener, api_dict, 'create_listener',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors,
                append_l7policies_rules=lambda *args: None
            )
        else:
            self._call_rpc(context, lb, listener, api_dict, 'create_listener')

    @log_helpers.log_method_call
    def update(self, context, old_listener, listener):
        """Update a listener."""

        self._log_entity(old_listener)
        self._log_entity(listener)

        driver = self.driver
        lb = listener.loadbalancer
        try:
            agent_host, service = self._setup_crud(context, lb, listener)
            driver.agent_rpc.update_listener(
                context,
                old_listener.to_dict(loadbalancer=False,
                                     default_pool=False),
                listener.to_dict(loadbalancer=False, default_pool=False),
                service,
                agent_host
            )
        except Exception as e:
            LOG.error("Exception: listener update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, listener):
        """Delete a listener."""

        self._log_entity(listener)

        lb = listener.loadbalancer
        api_dict = listener.to_dict(loadbalancer=False, default_pool=False)

        def append_listeners(context, lb, service):
            self._append_listeners(context, service, listener)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # L7policy should already be deleted.
            # Needn't modify pool.
            self._call_rpc(
                context, lb, listener, api_dict, 'delete_listener',
                append_listeners=append_listeners,
                append_pools_monitors=lambda *args: None,
                append_members=lambda *args: None,
                append_l7policies_rules=lambda *args: None
            )
        else:
            self._call_rpc(context, lb, listener, api_dict, 'delete_listener')


class PoolManager(EntityManager):
    """PoolManager class handles Neutron LBaaS pool CRUD."""

    def _get_pool_dict(self, pool):
        pool_dict = pool.to_dict(
            healthmonitor=False,
            listener=False,
            listeners=False,
            loadbalancer=False,
            l7_policies=False,
            members=False,
            session_persistence=False)
        pool_dict['provisioning_status'] = pool.provisioning_status
        pool_dict['operating_status'] = pool.operating_status
        return pool_dict

    @log_helpers.log_method_call
    def create(self, context, pool):
        """Create a pool."""

        self._log_entity(pool)

        lb = pool.loadbalancer
        api_dict = self._get_pool_dict(pool)

        def append_listeners(context, loadbalancer, service):
            for listener in loadbalancer.listeners:
                if listener.default_pool:
                    if listener.default_pool.id == pool.id:
                        LOG.debug("listener %s has default pool %s",
                                  listener.id, pool.id)
                        self._append_listeners(context, service, listener)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(context, service, pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Pool and l7plicies ???
            # Pool may be associated with listener, maybe not.
            # Pool has no members
            # Listener may have l7policies. Utilize default behavior.
            self._call_rpc(
                context, lb, pool, api_dict, 'create_pool',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors,
                append_members=lambda *args: None
            )
        else:
            self._call_rpc(context, lb, pool, api_dict, 'create_pool')

    @log_helpers.log_method_call
    def update(self, context, old_pool, pool):
        """Update a pool."""

        self._log_entity(old_pool)
        self._log_entity(pool)

        driver = self.driver
        lb = pool.loadbalancer
        try:
            agent_host, service = self._setup_crud(context, lb, pool)
            driver.agent_rpc.update_pool(
                context,
                self._get_pool_dict(old_pool),
                self._get_pool_dict(pool),
                service,
                agent_host
            )
        except Exception as e:
            LOG.error("Exception: pool update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, pool):
        """Delete a pool."""

        self._log_entity(pool)

        lb = pool.loadbalancer
        api_dict = self._get_pool_dict(pool)

        def append_listeners(context, loadbalancer, service):
            for listener in loadbalancer.listeners:
                if listener.default_pool:
                    if listener.default_pool.id == pool.id:
                        LOG.debug("listener %s has default pool %s",
                                  listener.id, pool.id)
                        self._append_listeners(context, service, listener)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(context, service, pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Pool may be associated with a listener
            # Utilize default behavior to load member, l7policy and rule
            self._call_rpc(
                context, lb, pool, api_dict, 'delete_pool',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors
            )
        else:
            self._call_rpc(context, lb, pool, api_dict, 'delete_pool')


class MemberManager(EntityManager):
    """MemberManager class handles Neutron LBaaS pool member CRUD."""

    @log_helpers.log_method_call
    def create(self, context, member):
        """Create a member."""

        self._log_entity(member)

        lb = member.pool.loadbalancer

        the_port_id = None
        driver = self.driver

        filters = {
            'device_owner': ['network:f5lbaasv2'],
            'fixed_ips': {'subnet_id': [member.subnet_id]}
        }
        LOG.debug('fetching certain ports details:')
        all_ports = driver.plugin.db._core_plugin.get_ports(
            context, filters
        )
        LOG.debug("all_ports details: %s" % all_ports)

        if len(all_ports) < 1:
            subnet = driver.plugin.db._core_plugin.get_subnet(
                context, member.subnet_id
            )

            # agent_host, service = self._setup_crud(context, lb, member)
            agent_host = 'temp'
            LOG.info('running here')
            if member.attached_to_loadbalancer() and lb:
                LOG.info('scheduing here instead')
                this_agent = self.driver.scheduler.schedule(
                    self.driver.plugin,
                    context,
                    lb.id,
                    self.driver.env
                )
                LOG.info(this_agent)
                agent_host = this_agent.get('host')
                LOG.info(agent_host)

            p = driver.plugin.db._core_plugin.create_port(context, {
                'port': {
                    'tenant_id': subnet['tenant_id'],
                    'network_id': subnet['network_id'],
                    'mac_address': n_const.ATTR_NOT_SPECIFIED,
                    'fixed_ips': n_const.ATTR_NOT_SPECIFIED,
                    'device_id': member.id,
                    'device_owner': 'network:f5lbaasv2',
                    'admin_state_up': member.admin_state_up,
                    'name': 'pool_port_' + member.id,
                    portbindings.HOST_ID: agent_host}})
            LOG.debug('the port created here is: %s' % p)
            the_port_id = p['id']

        api_dict = member.to_dict(pool=False)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(context, service, member.pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to append all members
            self._call_rpc(
                context, lb, member, api_dict, 'create_member',
                append_listeners=lambda *args: None,
                append_pools_monitors=append_pools_monitors,
                append_l7policies_rules=lambda *args: None,
                the_port_id=the_port_id
            )
        else:
            self._call_rpc(
                context, lb, member, api_dict, 'create_member',
                the_port_id=the_port_id
            )

    # only for MIGU
    @log_helpers.log_method_call
    def create_bulk(self, context, members):
        """Create members."""
        start_time = time()
        subnets = []
        p_list = []

        LOG.info("inside create_bulk for members: %s" % members)

        if not members:
            LOG.error("no members found in members. Just return.")
            return

        for member in members:
            if member.subnet_id not in subnets:
                lb = member.pool.loadbalancer
                driver = self.driver
                subnet = driver.plugin.db._core_plugin.get_subnet(
                    context, member.subnet_id
                )

                LOG.info("time for subnet  %.5f secs" % (time() - start_time))

                agent = self.driver.scheduler.schedule(
                    self.driver.plugin, context, lb.id, self.driver.env
                )
                LOG.info("time for agent  %.5f secs" % (time() - start_time))
                LOG.info(agent)

                agent_host = agent['host']
                p = driver.plugin.db._core_plugin.create_port(context, {
                    'port': {
                        'tenant_id': subnet['tenant_id'],
                        'network_id': subnet['network_id'],
                        'mac_address': n_const.ATTR_NOT_SPECIFIED,
                        'fixed_ips': n_const.ATTR_NOT_SPECIFIED,
                        'device_id': member.id,
                        'device_owner': 'network:f5lbaasv2',
                        'admin_state_up': member.admin_state_up,
                        'name': 'fake_pool_port_' + member.id,
                        portbindings.HOST_ID: agent_host}})
                p_list.append(p)
                LOG.info('the port created here is: %s' % p)

                api_dict = member.to_dict(pool=False)
                subnets.append(member.subnet_id)

        self._call_rpc(context, lb, member, api_dict, 'create_member')

        for port in p_list:
            LOG.info('p_list details: %s' % p_list)
            driver.plugin.db._core_plugin.delete_port(context, port["id"])

        LOG.info("create_bulk for members end.")

    @log_helpers.log_method_call
    def update(self, context, old_member, member):
        """Update a member."""

        self._log_entity(old_member)
        self._log_entity(member)

        driver = self.driver
        lb = member.pool.loadbalancer
        try:
            agent_host, service = self._setup_crud(context, lb, member)
            driver.agent_rpc.update_member(
                context,
                old_member.to_dict(pool=False),
                member.to_dict(pool=False),
                service,
                agent_host
            )
        except Exception as e:
            LOG.error("Exception: member update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, member):
        """Delete a member."""

        self._log_entity(member)

        lb = member.pool.loadbalancer
        driver = self.driver
        try:
            def append_pools_monitors(context, loadbalancer, service):
                self._append_pools_monitors(context, service, member.pool)

            if cfg.CONF.f5_driver_perf_mode in (2, 3):
                # Utilize default behavior to append all members
                agent_host, service = self._setup_crud(
                    context, lb, member,
                    append_listeners=lambda *args: None,
                    append_pools_monitors=append_pools_monitors,
                    append_l7policies_rules=lambda *args: None
                )
            else:
                agent_host, service = self._setup_crud(context, lb, member)

            driver.agent_rpc.delete_member(
                context, member.to_dict(pool=False), service, agent_host)
        except Exception as e:
            LOG.error("Exception: member delete: %s" % e.message)
            raise e

    # only for MIGU
    @log_helpers.log_method_call
    def delete_bulk(self, context, members_list):
        """Delete members."""
        LOG.info("inside delete_bulk for members: %s:" % members_list)

        if not members_list:
            LOG.error("no members found in members_list. Just return.")
            return

        member = members_list[0]

        lb = member.pool.loadbalancer
        driver = self.driver

        try:
            agent_host, service = self._setup_crud(context, lb, member)

            driver.agent_rpc.delete_member(
                context, member.to_dict(pool=False), service, agent_host)
        except Exception as e:
            LOG.error("Exception: member delete: %s" % e.message)
            raise e

        LOG.info("delete_bulk for members end.")


class HealthMonitorManager(EntityManager):
    """HealthMonitorManager class handles Neutron LBaaS monitor CRUD."""

    @log_helpers.log_method_call
    def create(self, context, health_monitor):
        """Create a health monitor."""

        self._log_entity(health_monitor)

        lb = health_monitor.pool.loadbalancer
        api_dict = health_monitor.to_dict(pool=False)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(context, service, health_monitor.pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to append all members
            self._call_rpc(
                context, lb, health_monitor, api_dict, 'create_health_monitor',
                append_listeners=lambda *args: None,
                append_pools_monitors=append_pools_monitors,
                append_l7policies_rules=lambda *args: None
            )
        else:
            self._call_rpc(context, lb, health_monitor, api_dict,
                           'create_health_monitor')

    @log_helpers.log_method_call
    def update(self, context, old_health_monitor, health_monitor):
        """Update a health monitor."""

        self._log_entity(old_health_monitor)
        self._log_entity(health_monitor)

        driver = self.driver
        lb = health_monitor.pool.loadbalancer
        try:
            agent_host, service = self._setup_crud(context, lb, health_monitor)
            driver.agent_rpc.update_health_monitor(
                context,
                old_health_monitor.to_dict(pool=False),
                health_monitor.to_dict(pool=False),
                service,
                agent_host
            )
        except Exception as e:
            LOG.error("Exception: health monitor update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, health_monitor):
        """Delete a health monitor."""

        self._log_entity(health_monitor)

        lb = health_monitor.pool.loadbalancer
        api_dict = health_monitor.to_dict(pool=False)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(context, service, health_monitor.pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to append all members
            self._call_rpc(
                context, lb, health_monitor, api_dict, 'delete_health_monitor',
                append_listeners=lambda *args: None,
                append_pools_monitors=append_pools_monitors,
                append_l7policies_rules=lambda *args: None
            )
        else:
            self._call_rpc(context, lb, health_monitor, api_dict,
                           'delete_health_monitor')


class L7PolicyManager(EntityManager):
    """L7PolicyManager class handles Neutron LBaaS L7 Policy CRUD."""

    @log_helpers.log_method_call
    def create(self, context, policy):
        """Create an L7 policy."""

        self._log_entity(policy)

        lb = policy.listener.loadbalancer
        api_dict = policy.to_dict(listener=False, rules=False)

        def append_listeners(context, loadbalancer, service):
            self._append_listeners(context, service, policy.listener)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(
                context, service, policy.listener.default_pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to load policies and rules
            # Listener may have default pool
            # Utilize default behavior to load members
            self._call_rpc(
                context, lb, policy, api_dict, 'create_l7policy',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors
            )
        else:
            self._call_rpc(context, lb, policy, api_dict, 'create_l7policy')

    @log_helpers.log_method_call
    def update(self, context, old_policy, policy):
        """Update a policy."""

        self._log_entity(old_policy)
        self._log_entity(policy)

        driver = self.driver
        lb = policy.listener.loadbalancer
        try:
            agent_host, service = self._setup_crud(context, lb, policy)
            driver.agent_rpc.update_l7policy(
                context,
                old_policy.to_dict(listener=False),
                policy.to_dict(listener=False),
                service,
                agent_host
            )
        except Exception as e:
            LOG.error("Exception: l7policy update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, policy):
        """Delete a policy."""

        self._log_entity(policy)

        lb = policy.listener.loadbalancer
        api_dict = policy.to_dict(listener=False, rules=False)

        def append_listeners(context, loadbalancer, service):
            self._append_listeners(context, service, policy.listener)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(
                context, service, policy.listener.default_pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to load policies and rules
            # Listener may have default pool
            # Utilize default behavior to load members
            self._call_rpc(
                context, lb, policy, api_dict, 'delete_l7policy',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors
            )
        else:
            self._call_rpc(context, lb, policy, api_dict, 'delete_l7policy')


class L7RuleManager(EntityManager):
    """L7RuleManager class handles Neutron LBaaS L7 Rule CRUD."""

    @log_helpers.log_method_call
    def create(self, context, rule):
        """Create an L7 rule."""

        self._log_entity(rule)

        lb = rule.policy.listener.loadbalancer
        api_dict = rule.to_dict(policy=False)

        def append_listeners(context, loadbalancer, service):
            self._append_listeners(context, service, rule.policy.listener)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(
                context, service, rule.policy.listener.default_pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to load policies and rules
            # Listener may have default pool
            # Utilize default behavior to load members
            self._call_rpc(
                context, lb, rule, api_dict, 'create_l7rule',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors
            )
        else:
            self._call_rpc(context, lb, rule, api_dict, 'create_l7rule')

    @log_helpers.log_method_call
    def update(self, context, old_rule, rule):
        """Update a rule."""

        self._log_entity(old_rule)
        self._log_entity(rule)

        driver = self.driver
        lb = rule.policy.listener.loadbalancer
        try:
            agent_host, service = self._setup_crud(context, lb, rule)
            driver.agent_rpc.update_l7rule(
                context,
                old_rule.to_dict(policy=False),
                rule.to_dict(policy=False),
                service,
                agent_host
            )
        except Exception as e:
            LOG.error("Exception: l7rule update: %s" % e.message)
            raise e

    @log_helpers.log_method_call
    def delete(self, context, rule):
        """Delete a rule."""

        self._log_entity(rule)

        lb = rule.policy.listener.loadbalancer
        api_dict = rule.to_dict(policy=False)

        def append_listeners(context, loadbalancer, service):
            self._append_listeners(context, service, rule.policy.listener)

        def append_pools_monitors(context, loadbalancer, service):
            self._append_pools_monitors(
                context, service, rule.policy.listener.default_pool)

        if cfg.CONF.f5_driver_perf_mode in (2, 3):
            # Utilize default behavior to load policies and rules
            # Listener may have default pool
            # Utilize default behavior to load members
            self._call_rpc(
                context, lb, rule, api_dict, 'delete_l7rule',
                append_listeners=append_listeners,
                append_pools_monitors=append_pools_monitors
            )
        else:
            self._call_rpc(context, lb, rule, api_dict, 'delete_l7rule')
