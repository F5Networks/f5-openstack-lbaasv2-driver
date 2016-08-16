# Copyright 2106 F5 Networks Inc.
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

import decorator
import paramiko
import pytest
import sys
import time

from f5.bigip import BigIP
import f5_os_test
from f5_os_test.polling_clients import MaximumNumberOfAttemptsExceeded
from f5_os_test.polling_clients import NeutronClientPollingManager
from pprint import pprint as pp

# Note: symbols_data provided through commandline json file.
from pytest import symbols as symbols_data

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def log_test_call(func):
    def wrapper(func, *args, **kwargs):
        print("\nRunning %s" % func.func_name)
        return func(*args, **kwargs)
    return decorator.decorator(wrapper, func)


class ExecTestEnv(object):

    def __init__(self):
        self.symbols = {}
        self.symbols['bigip_public_mgmt_ip']  = symbols_data.bigip_ip
        self.symbols['client_public_mgmt_ip'] = symbols_data.client_ip
        self.symbols['server_public_mgmt_ip'] = symbols_data.server_ip
        self.symbols['openstack_auth_url']    = symbols_data.auth_url
        self.symbols['lbaas_version']         = symbols_data.lbaas_version
        self.symbols['debug']                 = symbols_data.debug
        self.symbols['bigip_username']        = symbols_data.bigip_username
        self.symbols['bigip_password']        = symbols_data.bigip_password
        self.symbols['provider']              = ('f5' if
                                                 symbols_data.lbaas_version < 2
                                                 else symbols_data.provider)
        self.symbols['partition_prefix']      = ('uuid' if
                                                 symbols_data.lbaas_version < 2
                                                 else
                                                 symbols_data.partition_prefix)
        self.symbols['admin_name']            = symbols_data.admin_name
        self.symbols['admin_username']        = symbols_data.admin_username
        self.symbols['admin_password']        = symbols_data.admin_password
        self.symbols['tenant_name']           = symbols_data.tenant_name
        self.symbols['tenant_username']       = symbols_data.tenant_username
        self.symbols['tenant_password']       = symbols_data.tenant_password
        self.symbols['client_subnet']         = (symbols_data.tenant_name +
                                                 '-client-v4-subnet')
        self.symbols['guest_username']        = symbols_data.guest_username
        self.symbols['guest_password']        = symbols_data.guest_password
        self.symbols['server_http_port']      = symbols_data.server_http_port
        self.symbols['server_client_ip']      = symbols_data.server_client_ip
        self.symbols['nc_interval']           = symbols_data.nc_interval


def nclientmanager(symbols):
    nclient_config = {
        'username': symbols['tenant_username'],
        'password': symbols['tenant_password'],
        'tenant_name': symbols['tenant_name'],
        'auth_url': symbols['openstack_auth_url'],
        'interval': symbols['nc_interval']
    }

    return NeutronClientPollingManager(**nclient_config)


# candidate for moving to f5-openstack-test as common utility to create a
# full proxy capable of sending traffic
class LBaaSv1(object):
    def __init__(self, symbols):
        self.polling_interval = 1
        self.symbols = symbols
        self.ncm = nclientmanager(self.symbols)
        self.proxies = []
        self.max_attempts = 60

    def create_pool(self):
        pool_name = f5_os_test.random_name('test_pool_', 6)
        pool_conf = {}
        for sn in self.ncm.list_subnets()['subnets']:
            if sn['name'] == self.symbols['client_subnet']:
                pool_conf = {'pool': {'tenant_id':  sn['tenant_id'],
                                      'lb_method':  'ROUND_ROBIN',
                                      'protocol':   'HTTP',
                                      'subnet_id':  sn['id'],
                                      'provider':   self.symbols['provider'],
                                      'name':       pool_name}}

        return self.ncm.create_pool(pool_conf)['pool']

    def wait_for_object_state(self, field, value, method, key, *args):
        """This method provides an abstract way to poll any arbitrary object,
         such as pool, member, vip, etc.

            :param field: the attribute in the object that you want to monitor
            :param value: the final value that you want to see
            :param method: the show method that returns the object containing
                    state
            :param key: the key to a aub-dict in the show method output that
                    contains the state
            :param args: necessary args that must be passed to the show method
            :return:  N/A, raise if 'value' is not seen within 60 seconds
            """

        time.sleep(self.polling_interval)
        current_state = method(*args)[key]
        current_value = current_state[field]
        attempts = 0
        while value != current_value:
            sys.stdout.flush()
            current_state = method(*args)[key]
            current_value = current_state[field]
            time.sleep(self.polling_interval)
            attempts = attempts + 1
            if attempts >= self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded

    def create_vip(self, pool_id, subnet_id):
        vip_name = f5_os_test.random_name('test_vip_', 6)
        vip_conf = {'vip': {'name': vip_name,
                            'pool_id': pool_id,
                            'subnet_id': subnet_id,
                            'protocol': 'HTTP',
                            'protocol_port': 80}}
        return self.ncm.create_vip(vip_conf)['vip']

    def create_member(self, pool_id):
        member_conf = {
            'member': {'pool_id': pool_id,
                       'address': self.symbols['server_client_ip'],
                       'protocol_port': int(self.symbols['server_http_port'])}}
        return self.ncm.create_member(member_conf)['member']

    def create_healthmonitor(self):
        hm_conf = {'health_monitor': {'type': 'HTTP',
                                      'delay': 5,
                                      'timeout': 3,
                                      'max_retries': 2}}
        return self.ncm.create_health_monitor(hm_conf)['health_monitor']

    def create_proxy(self):
        class Proxy(object):
            def __init__(self):
                self.pool = None
                self.vip = None
                self.members = []
                self.healthmonitors = []

        # create a fully-formed loadbalancer with VIP, members, etc. suitable
        # for passing traffic between client and server
        proxy = Proxy()
        proxy.pool = self.create_pool()
        time.sleep(1)
        proxy.vip = self.create_vip(proxy.pool['id'], proxy.pool['subnet_id'])
        time.sleep(1)
        proxy.members.append(self.create_member(proxy.pool['id']))
        time.sleep(1)
        proxy.healthmonitors.append(self.create_healthmonitor())
        time.sleep(1)
        hmconf = proxy.healthmonitors[0]
        hmconf = {'health_monitor': {'id': hmconf['id'],
                                     'tenant_id': hmconf['tenant_id']}}
        self.ncm.associate_health_monitor(proxy.pool['id'], hmconf)
        self.proxies.append(proxy)
        return proxy

    def delete_proxy(self, proxy):
        # destroy a proxy and all associated objects
        for healthmonitor in proxy.healthmonitors:
            self.ncm.disassociate_health_monitor(proxy.pool['id'],
                                                 proxy.healthmonitors[0]['id'])
            time.sleep(1)
            self.ncm.delete_health_monitor(healthmonitor['id'])
        for member in proxy.members:
            self.ncm.delete_member(member['id'])
        time.sleep(1)
        self.ncm.delete_vip(proxy.vip['id'])
        self.wait_for_object_state('vip_id', None, self.ncm.show_pool, 'pool',
                                   proxy.pool['id'])
        self.ncm.delete_pool(proxy.pool['id'])
        # workaround for bug? need to explicitly delete selfip and route domain
        # for the pool to be deleted, otherwise it is stuck in pending.

    def clear_proxies(self):
        if self.symbols['debug']:
            self.debug()
        for vip in self.ncm.list_vips()['vips']:
            self.ncm.delete_vip(vip['id'])
        time.sleep(1)
        for pool in self.ncm.list_pools()['pools']:
            for health_monitor in \
                    self.ncm.list_health_monitors()['health_monitors']:
                self.ncm.disassociate_health_monitor(pool['id'],
                                                     health_monitor['id'])
                time.sleep(1)
                self.ncm.delete_health_monitor(health_monitor['id'])
                time.sleep(1)
        for member in self.ncm.list_members()['members']:
            self.ncm.delete_member(member['id'])
        time.sleep(1)
        for pool in self.ncm.list_pools()['pools']:
            self.wait_for_object_state('vip_id', None,
                                       self.ncm.show_pool, 'pool', pool['id'])
            self.ncm.delete_pool(pool['id'])
        if self.symbols['debug']:
            self.debug()

    def debug(self):
        print('----- pools -----')
        pp(self.ncm.list_pools())
        print('----- vips -----')
        pp(self.ncm.list_vips())
        print('----- members -----')
        pp(self.ncm.list_members())
        print('----- health monitors -----')
        pp(self.ncm.list_health_monitors())


# candidate for moving to f5-openstack-test as common utility to create a
# full proxy capable of sending traffic
class LBaaSv2(object):
    def __init__(self, symbols):
        self.polling_interval = 1
        self.symbols = symbols
        self.ncm = nclientmanager(self.symbols)
        self.proxies = []

    def create_loadbalancer(self):
        lb_name = f5_os_test.random_name('test_lb_', 6)
        lb_conf = {}
        for sn in self.ncm.list_subnets()['subnets']:
            if sn['name'] == self.symbols['client_subnet']:
                lb_conf = {
                    'loadbalancer': {
                        'vip_subnet_id': sn['id'],
                        # 'lb_method':     'ROUND_ROBIN',
                        # 'protocol':      'HTTP',
                        'tenant_id':     sn['tenant_id'],
                        'provider':      self.symbols['provider'],
                        'name':          lb_name}}
        return self.ncm.create_loadbalancer(lb_conf)['loadbalancer']

    def delete_loadbalancer(self, lb):
        self.ncm.delete_loadbalancer(lb['id'])

    def wait_for_object_state(self, field, value, method, key, *args):
        '''This method provides an abstract way to poll any arbitrary object, such
        as pool, member, vip, etc.

        :param field: the attribute in the object that you want to monitor
        :param value: the final value that you want to see
        :param method: the show method that returns the object containing state
        :param key: the key to a aub-dict in the show method output that
                    contains the state
        :param args: necessary args that must be passed to the show method
        :return:  N/A, raise if 'value' is not seen within 60 seconds
        '''

        time.sleep(self.polling_interval)
        current_state = method(*args)[key]
        current_value = current_state[field]
        attempts = 0
        while value != current_value:
            sys.stdout.flush()
            current_state = method(*args)[key]
            current_value = current_state[field]
            time.sleep(self.polling_interval)
            attempts = attempts + 1
            if attempts >= self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded

    def create_listener(self, lb_id):
        listener_name = f5_os_test.random_name('test_listener_', 6)
        listener_config = {
            'listener': {'name': listener_name,
                         'loadbalancer_id': lb_id,
                         'protocol': 'HTTP',
                         'protocol_port': 80
                         }
        }
        return self.ncm.create_listener(listener_config)['listener']

    def create_lbaas_pool(self, l_id):
        pool_name = f5_os_test.random_name('test_pool_', 6)
        pool_config = {
            'pool': {
                'name': pool_name,
                'lb_algorithm': 'ROUND_ROBIN',
                'listener_id': l_id,
                'protocol': 'HTTP'}}
        return self.ncm.create_lbaas_pool(pool_config)['pool']

    def create_lbaas_member(self, p_id):
        subnet_id = None
        for sn in self.ncm.list_subnets()['subnets']:
            if 'client-v4' in sn['name']:
                subnet_id = sn['id']
                break

        member_config = {
            'member': {
                'subnet_id': subnet_id,
                'address': self.symbols['server_client_ip'],
                'protocol_port': int(self.symbols['server_http_port'])}}

        return self.ncm.create_lbaas_member(p_id, member_config)['member']

    def create_lbaas_healthmonitor(self, p_id):
        hm_config = {
            'healthmonitor': {
                'type': 'HTTP',
                'delay': 5,
                'timeout': 3,
                'pool_id': p_id,
                'max_retries': 2}}
        # direct call to client, missing polling layer
        return self.ncm.create_lbaas_healthmonitor(hm_config)['healthmonitor']

    def create_proxy(self):
        class Proxy(object):
            def __init__(self):
                self.loadbalancer = None
                self.listener = None
                self.lbaas_pool = None
                self.members = []
                self.healthmonitors = []

        # create a fully-formed loadbalancer with VIP, members, etc. suitable
        # for passing traffic between client and server
        proxy = Proxy()
        proxy.loadbalancer = self.create_loadbalancer()
        time.sleep(1)
        proxy.listener = self.create_listener(proxy.loadbalancer['id'])
        time.sleep(1)
        proxy.pool = self.create_lbaas_pool(proxy.listener['id'])
        time.sleep(1)
        proxy.members.append(self.create_lbaas_member(proxy.pool['id']))
        # lbaasv2 bug: lbaas_show_member does not return status attribute to
        # know when member comes online.
        time.sleep(1)
        proxy.healthmonitors.append(
            self.create_lbaas_healthmonitor(proxy.pool['id']))
        self.proxies.append(proxy)
        return proxy

    def delete_proxy(self, proxy):
        # destroy a loadbalancer and all associated objects
        for healthmonitor in proxy.healthmonitors:
            self.ncm.delete_lbaas_healthmonitor(healthmonitor['id'])
        for member in proxy.members:
            self.ncm.delete_lbaas_member(member['id'])
        self.ncm.delete_lbaas_pool(proxy.pool['id'])
        self.ncm.delete_listener(proxy.listener['id'])
        self.ncm.delete_loadbalancer(proxy.loadbalancer['id'])

    def clear_proxies(self):
        if self.symbols['debug']:
            self.debug()
        self.ncm.delete_all_lbaas_healthmonitors()
        time.sleep(1)
        self.ncm.delete_all_lbaas_pools()
        time.sleep(1)
        self.ncm.delete_all_listeners()
        time.sleep(1)
        self.ncm.delete_all_loadbalancers()
        if self.symbols['debug']:
            self.debug()

    def debug(self):
        print('----- loadbalancers -----')
        pp(self.ncm.list_loadbalancers())
        print('----- listeners -----')
        pp(self.ncm.list_listeners())
        print('----- pools -----')
        pp(self.ncm.list_lbaas_pools())
        print('----- members -----')
        for p in self.ncm.list_lbaas_pools()['pools']:
            pp(self.ncm.list_lbaas_members(p['id']))
        print('----- health monitors -----')
        pp(self.ncm.list_lbaas_healthmonitors())


@pytest.fixture
def tst_setup(request, symbols):
    print('test setup')
    testenv = ExecTestEnv()

    def tst_cleanup():
        print('test cleanup')
        testenv.lbm.clear_proxies()
        exec_command(testenv.server_ssh, 'pkill -f SimpleHTTPServer',
                     ignore_error=True)

    def tst_teardown():
        print('test teardown')
        if not testenv.lbm.symbols['debug']:
            tst_cleanup()
        testenv.client_ssh.close()
        testenv.server_ssh.close()

    # create SSH conn to client
    testenv.client_ssh = paramiko.SSHClient()
    testenv.client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    testenv.client_ssh.connect(testenv.symbols['client_public_mgmt_ip'],
                               username=testenv.symbols['guest_username'],
                               password=testenv.symbols['guest_password'])
    # create SSH conn to server
    testenv.server_ssh = paramiko.SSHClient()
    testenv.server_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    testenv.server_ssh.connect(testenv.symbols['server_public_mgmt_ip'],
                               username=testenv.symbols['guest_username'],
                               password=testenv.symbols['guest_password'])
    #
    testenv.bigip = BigIP(testenv.symbols['bigip_public_mgmt_ip'],
                          testenv.symbols['bigip_username'],
                          testenv.symbols['bigip_password'])
    testenv.request = request
    testenv.lbm = (LBaaSv1(testenv.symbols) if
                   testenv.symbols['lbaas_version'] == 1 else
                   LBaaSv2(testenv.symbols))
    tst_cleanup()
    request.addfinalizer(tst_teardown)
    return testenv


def exec_command(ssh, command, ignore_error=False):
    stdin, stdout, stderr = ssh.exec_command(command)
    stdin.close()
    status = stdout.channel.recv_exit_status()
    output = stdout.read()
    if not ignore_error:
        if status:
            print('----- sterr -----')
            print(stderr)
            pp(stderr.channel.__dict__)
            error = stderr.read()
            print(error)
        assert status == 0
    return output.strip()


@log_test_call
def test_solution(tst_setup):
    te = tst_setup
    te.webserver_started = False
    proxy = te.lbm.create_proxy()

    # start web server
    command = ('python -m SimpleHTTPServer %s >/dev/null 2>&1 & echo $!' %
               te.symbols['server_http_port'])
    exec_command(te.server_ssh, command)
    te.webserver_started = True

    # wait for health monitor to show server as up
    print('waiting for member to become active...',)
    if te.symbols['lbaas_version'] == 1:
        te.lbm.wait_for_object_state('status', 'ACTIVE',
                                     te.lbm.ncm.show_member, 'member',
                                     proxy.members[0]['id'])
    else:
        # lbaasv2 bug: lbaas_show_member does not return status attribute to
        # know when member comes online.
        # te.lbm.wait_for_object_state('status', 'ACTIVE',
        #                              te.lbm.ncm.show_lbaas_member, 'member',
        #                              proxy.members[0]['id'],
        #                              proxy.pool['id'])

        # HACK workaround until openstack supports the status field
        folders = te.bigip.sys.folders.get_collection()
        for f in folders:
            if f.name.startswith(te.symbols['partition_prefix']):
                break
        params = {'params': {'$filter': 'partition eq %s' % f.name}}
        pool = te.bigip.ltm.pools.pool.load(name=proxy.pool['name'],
                                            partition=f.name)
        members = pool.members_s.get_collection(request_params=params)
        found = False
        for member in members:
            if member.address.split('%')[0] == proxy.members[0]['address']:
                found = True
                break
        assert(found)
        attempts = 0
        while member.state != 'up':
            time.sleep(1)
            attempts = attempts + 1
            if attempts >= 20:
                raise MaximumNumberOfAttemptsExceeded
            member.refresh()
    print('COMPLETE')

    # send requests from client
    print('sending request from client....',)
    if te.symbols['lbaas_version'] == 1:
        url = 'http://%s:%s' % (proxy.vip['address'],
                                proxy.vip['protocol_port'])
    else:
        url = 'http://%s:%s' % (proxy.loadbalancer['vip_address'],
                                proxy.listener['protocol_port'])
    output = exec_command(te.client_ssh, '$HOME/get.py %s' % url)
    assert output == '200'
    print('SUCCESS')
