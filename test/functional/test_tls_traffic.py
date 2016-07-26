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

# Note: symbols_data provided through commandline json file.
from pytest import symbols as symbols_data

import decorator
import paramiko
import pytest
import time
import sys, re

import f5_os_test
from f5.bigip import BigIP
from f5.bigip import ManagementRoot
from pprint import pprint as pp
from neutronclient.v2_0 import client
from f5_os_test.polling_clients import NeutronClientPollingManager
from f5_os_test.polling_clients import MaximumNumberOfAttemptsExceeded
from barbicanclient import client
from f5_openstack_agent.lbaasv2.drivers.bigip import ssl_profile
from f5_openstack_agent.lbaasv2.drivers.bigip import barbican_cert
from keystoneauth1 import identity
from keystoneauth1 import session
print "Imports complete..."


def log_test_call(func):
    def wrapper(func, *args, **kwargs):
        print("\nRunning %s" % func.func_name)
        return func(*args, **kwargs)
    return decorator.decorator(wrapper, func)


class ExecTestEnv(object):

    def __init__(self):
        self.symbols = {}
        self.symbols['bigip_public_mgmt_ip']      = symbols_data.bigip_ip
        self.symbols['client_public_mgmt_ip']     = symbols_data.client_ip
        self.symbols['server_public_mgmt_ip']     = symbols_data.server_ip
        self.symbols['openstack_auth_url']        = symbols_data.auth_url
        self.symbols['lbaas_version']             = symbols_data.lbaas_version
        self.symbols['debug']                     = True
        self.symbols['bigip_username']            = symbols_data.bigip_username
        self.symbols['bigip_password']            = symbols_data.bigip_password
        self.symbols['provider']                  = ('f5' if symbols_data.lbaas_version < 2 \
                                                      else symbols_data.provider)
        self.symbols['admin_name']                = symbols_data.admin_name
        self.symbols['admin_username']            = symbols_data.admin_username
        self.symbols['admin_password']            = symbols_data.admin_password
        self.symbols['tenant_name']               = symbols_data.tenant_name
        self.symbols['tenant_username']           = symbols_data.tenant_username
        self.symbols['tenant_password']           = symbols_data.tenant_password
        self.symbols['client_subnet']             = symbols_data.tenant_name + '-client-v4-subnet'
        self.symbols['guest_username']            = symbols_data.guest_username
        self.symbols['guest_password']            = symbols_data.guest_password
        self.symbols['server_http_port']          = symbols_data.server_http_port
        self.symbols['server_client_ip']          = symbols_data.server_client_ip


def nclientmanager(symbols):
    nclient_config = {
        'username':      symbols['tenant_username'],
        'password':      symbols['tenant_password'],
        'tenant_name':   symbols['tenant_name'],
        'auth_url':      symbols['openstack_auth_url']
    }
    return NeutronClientPollingManager(**nclient_config)


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
                        #'lb_method':  'ROUND_ROBIN',
                        'tenant_id':   sn['tenant_id'],
                        'provider':    self.symbols['provider'],
                        'name':        lb_name}}
        return self.ncm.create_loadbalancer(lb_conf)['loadbalancer']

    def delete_loadbalancer(self, lb):
        self.ncm.delete_loadbalancer(lb['id'])

    def wait_for_object_state(self, field, value, method, key, *args):
        '''
        This method provides an abstract way to poll any arbitrary object, such
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
            pp(current_state)
            current_value = current_state[field]
            time.sleep(self.polling_interval)
            attempts = attempts + 1
            if attempts >= self.max_attempts:
                raise MaximumNumberOfAttemptsExceeded

    def create_listener(self, lb_id, tls_container_ref, sni_container_refs=[]):
        listener_name = f5_os_test.random_name('test_listener_', 6)
        listener_config =\
        {'listener': {'name': listener_name,
                      'loadbalancer_id': lb_id,
                      'protocol': 'TERMINATED_HTTPS',
                      'protocol_port': 443,
                      'default_tls_container_ref': tls_container_ref,
                      'sni_container_refs': sni_container_refs}}
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
            if 'server-v4' in sn['name']:
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
        sni_container_refs = []
        if symbols_data.include_SNI_test:
            sni_container_refs = [container_ref2]
        proxy.listener = self.create_listener(proxy.loadbalancer['id'], container_ref1, sni_container_refs)
        proxy.pool = self.create_lbaas_pool(proxy.listener['id'])
        proxy.members.append(self.create_lbaas_member(proxy.pool['id']))
        # lbaasv2 bug: lbaas_show_member does not return status attribute to
        # know when member comes online.
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
        print "clearing proxies..."
        print "    healthmonitors"
        self.ncm.delete_all_lbaas_healthmonitors()
        print "    lbaas pools"
        self.ncm.delete_all_lbaas_pools()
        print "    listeners"
        self.ncm.delete_all_listeners()
        print "    loadbalancers"
        self.ncm.delete_all_loadbalancers()
        print "    complete"
        if self.symbols['debug']:
            self.debug()

    def debug(self):
        print '----- loadbalancers -----'
        pp(self.ncm.list_loadbalancers())
        print '----- listeners -----'
        pp(self.ncm.list_listeners())
        print '----- pools -----'
        pp(self.ncm.list_lbaas_pools())
        print '----- members -----'
        for p in self.ncm.list_lbaas_pools()['pools']:
            pp(self.ncm.list_lbaas_members(p['id']))
        print '----- health monitors -----'
        pp(self.ncm.list_lbaas_healthmonitors())


@pytest.fixture
def tst_setup(request, symbols):
    testenv = ExecTestEnv()

    def tst_teardown():
        # pool delete sometimes get stuck in pending due to one or more of the
        # following objects existing on BIG-IP:
        # selfip, snat, route-domain, vxlan tunnel, gre tunnel
        testenv.lbm.clear_proxies()
        if testenv.webserver_started:
            exec_command(testenv.server_ssh, 'pkill -f SimpleHTTPServer')
        testenv.client_ssh.close()
        testenv.server_ssh.close()

    print "\ncreate SSH conn to client"
    testenv.client_ssh = paramiko.SSHClient()
    testenv.client_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    testenv.client_ssh.connect(testenv.symbols['client_public_mgmt_ip'],
                               username=testenv.symbols['guest_username'],
                               password=testenv.symbols['guest_password'])
    print "create SSH conn to server"
    testenv.server_ssh = paramiko.SSHClient()
    testenv.server_ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    testenv.server_ssh.connect(testenv.symbols['server_public_mgmt_ip'],
                               username=testenv.symbols['guest_username'],
                               password=testenv.symbols['guest_password'])
    print "bigip object"
    testenv.bigip = BigIP(testenv.symbols['bigip_public_mgmt_ip'],
                          testenv.symbols['bigip_username'],
                          testenv.symbols['bigip_password'])
    testenv.request = request
    print "LBaaSv2 with symbols"
    testenv.lbm = LBaaSv2(testenv.symbols)
    print "clear proxies"
    # > testenv.lbm.clear_proxies()
    print "test setup complete"
    #request.addfinalizer(tst_teardown)
    return testenv


def exec_command(ssh, command):
    stdin, stdout, stderr = ssh.exec_command(command)
    stdin.close()
    status = stdout.channel.recv_exit_status()
    output = stdout.read()
    if status:
        print '----- sterr -----'
        print stderr
        pp(stderr.channel.__dict__)
        error = stderr.read()
        print error
    assert status == 0
    return output.strip()


class Config(object):
    def __init__(self):
        self.os_username            = symbols_data.os_username
        self.os_user_domain_name    = "default"
        self.os_password            = symbols_data.os_password
        self.os_project_domain_name = "default"
        self.os_project_name        = symbols_data.os_tenant_name
        self.auth_version           = symbols_data.os_auth_version.strip()
        m = re.search("(?P<url_base>https?.*)/", symbols_data.auth_url)
        self.os_auth_url            = m.group('url_base') + "/" + self.auth_version


def read_file(file_name):
    file = open(file_name, 'rb')
    return file.read()


def create_container(name, container_name, cert_payload, key_payload):
    conf = Config()
    auth = identity.v3.Password(auth_url=conf.os_auth_url,
                                username=conf.os_username,
                                user_domain_name='default',
                                project_domain_name='default',
                                password=conf.os_password,
                                project_name=conf.os_project_name)
    print "auth object created..."
    sess = session.Session(auth=auth)
    print "session started..."
    barbican = client.Client(session=sess)
    print "barbican instance started..."
    secret_cert = barbican.secrets.create(name + '.crt', payload=cert_payload)
    print "secret cert created..."
    secret_cert.store()
    print "secret cert stored..."
    secret_key = barbican.secrets.create(name + '.key', payload=key_payload)
    print "secret key created..."
    secret_key.store()
    print "secret key stored..."
    container = barbican.containers.create_certificate(name=container_name,
                                                       certificate=secret_cert,
                                                       private_key=secret_key)
    print "container created... " + container_name + "\n" + str(container)
    container_ref = container.store()
    print "container stored... ref: " + container_ref
    assert container_ref.startswith("http")
    retrieved_container = barbican.containers.get(container_ref)
    print "container retrieved by ref:\n" + str(retrieved_container)
    return container_ref


# Create containers and have refs available
def test_create_containers():
    global cert_payload1
    global key_payload1
    global container_ref1
    global cert_payload2
    global key_payload2
    global container_ref2
    cert_payload1  = read_file('server.crt')
    key_payload1   = read_file('server.key')
    container_ref1 = create_container('container1', "tls container cert1", cert_payload1, key_payload1)
    assert container_ref1.startswith("http")
    print "container1 created...ref: " + container_ref1
    cert_payload2  = read_file('server2.crt')
    key_payload2   = read_file('server2.key')
    container_ref2 = create_container('container2', "tls container cert2", cert_payload2, key_payload2)
    assert container_ref2.startswith("http")
    print "container2 created...ref: " + container_ref2


def test_cert_manager():
    conf = Config()
    print "Test Cert Manager, container1..."
    cert_manager = barbican_cert.BarbicanCertManager(conf)
    print "cert manager started..."
    cert = cert_manager.get_certificate(container_ref1)
    print "container1 cert retrieved... \n" +  cert
    assert cert == cert_payload1

    key = cert_manager.get_private_key(container_ref1)
    print "container1 key retrieved... \n" + key
    assert key == key_payload1


def test_configure_bigip():
    bigip = ManagementRoot(symbols_data.bigip_ip, symbols_data.bigip_username, symbols_data.bigip_password)
    print "BigIP object created..."
    ssl_profile.SSLProfileHelper.create_client_ssl_profile(bigip, 'server', cert_payload1, key_payload1)
    print "SSL profile created..."


@log_test_call
def test_solution(tst_setup):
    te = tst_setup
    te.webserver_started = False
    print "create proxy"
    proxy = te.lbm.create_proxy()

    print "start web server"
    command = ('python -m SimpleHTTPServer %s >/dev/null 2>&1 & echo $!' %
               te.symbols['server_http_port'])
    exec_command(te.server_ssh, command)
    te.webserver_started = True

    # wait for health monitor to show server as up
    print 'waiting for member to become active...',
    # lbaasv2 bug: lbaas_show_member does not return status attribute to
    # know when member comes online.
    #te.lbm.wait_for_object_state('status', 'ACTIVE',
    #                             te.lbm.ncm.show_lbaas_member, 'member',
    #                             proxy.members[0]['id'], proxy.pool['id'])

    # HACK workaround until openstack supports the status field
    folders = te.bigip.sys.folders.get_collection()
    for f in folders:
        if f.name.startswith('Project_'):
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
        if attempts >= 15:
            raise MaximumNumberOfAttemptsExceeded
        member.refresh()
    print 'COMPLETE'

    # send requests from client
    print 'sending request from client....',
    url = 'https://%s:%s' % (proxy.loadbalancer['vip_address'],
                                proxy.listener['protocol_port'])
    output = exec_command(te.client_ssh, '$HOME/get.py %s' % url)
    assert output == '200'
    print 'SUCCESS'

