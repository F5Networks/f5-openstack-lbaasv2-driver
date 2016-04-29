from collections import OrderedDict
from functools import partial
from numbers import Number
from pprint import pprint as pp

from f5_os_test.polling_clients import NeutronClientPollingManager
from neutronclient.common.exceptions import BadRequest

from pytest import symbols as symbols_data


nclient_config = {
    'username':    symbols_data.tenant_username,
    'password':    symbols_data.tenant_password,
    'tenant_name': symbols_data.tenant_name,
    'auth_url':    symbols_data.auth_url
}


class UnexpectedTypeFromJson(TypeError):
    pass


class UpdateScanner(object):
    def __init__(self, component_config):
        self.ordered_config = OrderedDict(component_config.copy())
        self.keytuple = tuple(self.ordered_config.keys())
        self.param_vector = self._build_param_vector()

    def call_factory(self, ncpm, update_method, update_target):
        def call_method(**kwargs):
            cm = getattr(ncpm, update_method)
            pp(cm.__name__)
            partial_fixed = partial(cm, update_target)
            return partial_fixed(**kwargs)
        self.call_method = call_method

    def _build_param_vector(self):
        param_vector = []
        for k, v in self.ordered_config.iteritems():
            param_vector.append((k, self._toggle_state(v)))
        return param_vector

    def _toggle_state(self, config_value):
        # Note this doesn't handle reference cycles.
        if isinstance(config_value, basestring):
            return config_value+'_test'
        elif isinstance(config_value, bool):
            return not config_value
        elif isinstance(config_value, Number):
            return config_value+1
        elif isinstance(config_value, list):
            if config_value:
                return [self._toggle_state(i) for i in config_value]
            else:
                return [0]
        elif isinstance(config_value, dict):
            if config_value:
                t = config_value.copy()
                for k, v in t.iteritems():
                    t[k] = self._toggle_state(v)
                return t
            else:
                return {'test_key': 'test_val'}
        elif isinstance(config_value, type(None)):
            return 1
        else:
            raise UnexpectedTypeFromJson(config_value)


def pytest_generate_tests(metafunc):
    if 'update_lb_key' in metafunc.fixturenames:
        metafunc.parametrize('update_lb_key,update_value',
                             metafunc.cls.lb_param_vector)
    elif 'update_listener_key' in metafunc.fixturenames:
        metafunc.parametrize('update_listener_key,update_value',
                             metafunc.cls.listener_param_vector)
    elif 'update_pool_key' in metafunc.fixturenames:
        metafunc.parametrize('update_pool_key,update_value',
                             metafunc.cls.pool_param_vector)
    elif 'update_member_key' in metafunc.fixturenames:
        metafunc.parametrize('update_member_key,update_value',
                             metafunc.cls.member_param_vector)
    elif 'update_healthmonitor_key' in metafunc.fixturenames:
        metafunc.parametrize('update_healthmonitor_key,update_value',
                             metafunc.cls.healthmonitor_param_vector)


class UpdateScenarioBase(object):
    ncpm = NeutronClientPollingManager(**nclient_config)
    subnets = ncpm.list_subnets()['subnets']
    for sn in subnets:
        if 'client-v4' in sn['name']:
            lbconf = {'vip_subnet_id': sn['id'],
                      'tenant_id':     sn['tenant_id'],
                      'name':          'testlb_01'}
    # loadbalancer setup
    activelb =\
        ncpm.create_loadbalancer({'loadbalancer': lbconf})
    active_loadbalancer_config = activelb['loadbalancer']
    loadbalancer_updater = UpdateScanner(active_loadbalancer_config)
    lb_param_vector = loadbalancer_updater.param_vector
    # listener setup
    listener_config = {'listener':
                       {'name': 'test_listener',
                        'loadbalancer_id': activelb['loadbalancer']['id'],
                        'protocol': 'HTTP',
                        'protocol_port': 80}}
    active_listener = ncpm.create_listener(listener_config)
    active_listener_config = active_listener['listener']
    listener_updater = UpdateScanner(active_listener_config)
    listener_param_vector = listener_updater.param_vector
    # pool setup
    pool_config = {'pool': {
                   'name': 'test_pool_awieuver',
                   'lb_algorithm': 'ROUND_ROBIN',
                   'listener_id': active_listener['listener']['id'],
                   'protocol': 'HTTP'}}
    active_pool = ncpm.create_lbaas_pool(pool_config)
    active_pool_config = active_pool['pool']
    pool_updater = UpdateScanner(active_pool_config)
    pool_param_vector = pool_updater.param_vector
    # pool member setup
    for sn in ncpm.list_subnets()['subnets']:
        if 'server-v4' in sn['name']:
            address = sn['allocation_pools'][0]['start']
            subnet_id = sn['id']
            break
    member_config = {'member': {
                     'subnet_id': subnet_id,
                     'address': address,
                     'protocol_port': 80}}
    pool_id = active_pool_config['id']
    active_member = ncpm.create_lbaas_member(pool_id, member_config)
    active_member_config = active_member['member']
    member_updater = UpdateScanner(active_member_config)
    member_param_vector = member_updater.param_vector
    # healthmonitor setup
    monitor_config = {'healthmonitor': {
                      'delay': 3,
                      'pool_id': pool_id,
                      'type': 'HTTP',
                      'timeout': 13,
                      'max_retries': 7}}
    healthmonitor = ncpm.create_lbaas_healthmonitor(monitor_config)
    healthmonitorconfig = healthmonitor['healthmonitor']
    healthmonitor_updater = UpdateScanner(healthmonitorconfig)
    healthmonitor_param_vector = healthmonitor_updater.param_vector


class TestLoadBalancerUpdateScenarios(UpdateScenarioBase):

    def test_loadbalancer_update_configs(self,
                                         update_lb_key,
                                         update_value,
                                         setup_with_loadbalancer):
        ncpm, active_loadbalancer = setup_with_loadbalancer
        active_loadbalancer_id = active_loadbalancer['loadbalancer']['id']
        self.loadbalancer_updater.call_factory(
            ncpm, 'update_loadbalancer', active_loadbalancer_id
        )
        update_dict = {update_lb_key: update_value}
        try:
            updated = self.loadbalancer_updater.call_method(
                lbconf={'loadbalancer': update_dict}
            )
        except BadRequest as exc:
            exc_message_first_line = exc.message.split('\n')[0]
            expected_first_line =\
                'Cannot update read-only attribute %s' % update_lb_key
            assert exc_message_first_line == expected_first_line
            return
        assert updated['loadbalancer'][update_lb_key] == update_value


class TestListenerUpdateScenarios(UpdateScenarioBase):

    def test_listener_update_configs(self,
                                     update_listener_key,
                                     update_value,
                                     setup_with_listener):
        ncpm, active_listener = setup_with_listener
        active_listener_id = active_listener['listener']['id']
        self.listener_updater.call_factory(
            ncpm, 'update_listener', active_listener_id
        )
        if update_listener_key == 'default_tls_container_ref':
            update_value = 'string_for_read_only_fail'
        elif update_listener_key == 'sni_container_refs':
            # NOTE:  THIS TEST WILL ALWAYS SUCCEED
            return NotImplemented
        update_dict = {update_listener_key: update_value}
        try:
            updated = self.listener_updater.call_method(
                listener_conf={'listener': update_dict}
            )
        except BadRequest as exc:
            exc_message_first_line = exc.message.split('\n')[0]
            expected_first_line =\
                'Cannot update read-only attribute %s' % update_listener_key
            assert exc_message_first_line == expected_first_line
            return
        assert updated['listener'][update_listener_key] == update_value


class TestPoolUpdateScenarios(UpdateScenarioBase):

    def test_pool_update_configs(self,
                                 update_pool_key,
                                 update_value,
                                 setup_with_pool):
        ncpm, active_pool = setup_with_pool
        active_pool_id = active_pool['pool']['id']
        self.pool_updater.call_factory(
            ncpm, 'update_lbaas_pool', active_pool_id
        )
        if update_pool_key == 'lb_algorithm':
            if 'ROUND_ROBIN' in update_value:
                update_value = 'SOURCE_IP'
            else:
                update_value = 'ROUND_ROBIN'
        elif update_pool_key == 'session_persistence':
                update_value = None
        update_dict = {update_pool_key: update_value}
        try:
            updated = self.pool_updater.call_method(
                lbaas_pool_conf={'pool': update_dict}
            )
        except BadRequest as exc:
            exc_message_first_line = exc.message.split('\n')[0]
            expected_first_line =\
                'Cannot update read-only attribute %s' % update_pool_key
            assert exc_message_first_line == expected_first_line
            return
        assert updated['pool'][update_pool_key] == update_value


class TestMemberUpdateScenarios(UpdateScenarioBase):

    def test_member_update_configs(self,
                                   update_member_key,
                                   update_value,
                                   setup_with_pool_member):
        ncpm, active_pool, active_member = setup_with_pool_member
        active_member_id = active_member['member']['id']
        self.member_updater.call_factory(
            ncpm, 'update_lbaas_member', active_member_id
        )
        if update_member_key == 'lb_algorithm':
            if 'ROUND_ROBIN' in update_value:
                update_value = 'SOURCE_IP'
            else:
                update_value = 'ROUND_ROBIN'
        elif update_member_key == 'session_persistence':
                update_value = None
        update_dict = {update_member_key: update_value}
        try:
            updated = self.member_updater.call_method(
                pool_id=active_pool['pool']['id'],
                member_conf={'member': update_dict}
            )
        except BadRequest as exc:
            exc_message_first_line = exc.message.split('\n')[0]
            expected_first_line =\
                'Cannot update read-only attribute %s' % update_member_key
            assert exc_message_first_line == expected_first_line
            return
        assert updated['member'][update_member_key] == update_value


class TestHealthMonitorUpdateScenarios(UpdateScenarioBase):

    def test_healthmonitor_update_configs(self,
                                          update_healthmonitor_key,
                                          update_value,
                                          setup_with_healthmonitor):
        ncpm, active_healthmonitor, pool, member = setup_with_healthmonitor
        active_healthmonitor_id = active_healthmonitor['healthmonitor']['id']
        self.healthmonitor_updater.call_factory(
            ncpm, 'update_lbaas_healthmonitor', active_healthmonitor_id
        )
        if update_healthmonitor_key == 'expected_codes':
            update_value = '300'
        update_dict = {update_healthmonitor_key: update_value}
        try:
            updated = self.healthmonitor_updater.call_method(
                lbaas_healthmonitor_conf={'healthmonitor': update_dict}
            )
        except BadRequest as exc:
            exc_message_first_line = exc.message.split('\n')[0]
            expected_first_line =\
                'Cannot update read-only attribute %s' %\
                update_healthmonitor_key
            assert exc_message_first_line == expected_first_line
            return
        assert updated['healthmonitor'][update_healthmonitor_key] ==\
            update_value
