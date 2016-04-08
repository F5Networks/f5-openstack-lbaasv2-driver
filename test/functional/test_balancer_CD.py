# Copyright 2016 F5 Networks Inc.
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

from neutronclient.v2_0 import client
from pprint import pprint as pp
import pytest
import sys
import time


@pytest.fixture
def nclientmanager(polling_neutronclient):
    nclient_config = {
        'username': 'testlab',
        'password': 'changeme',
        'tenant_name': 'testlab',
        'auth_url': 'http://10.190.4.153:5000/v2.0'}

    neutronclient = client.Client(**nclient_config)
    pnc = polling_neutronclient(neutronclient)
    return pnc


@pytest.fixture
def setup_with_nclientmanager(request, nclientmanager):
    def finalize():
        pp('Entered setup/finalize.')
        nclientmanager.delete_all_lbaas_healthmonitors()
        nclientmanager.delete_all_lbaas_pools()
        nclientmanager.delete_all_listeners()
        nclientmanager.delete_all_loadbalancers()

    finalize()
    request.addfinalizer(finalize)
    return nclientmanager


def test_lb_CD(setup_with_nclientmanager, bigip):
    # set initial state
    nclientmanager = setup_with_nclientmanager
    subnets = nclientmanager.list_subnets()['subnets']
    for sn in subnets:
        if 'client-v4' in sn['name']:
            lbconf = {'vip_subnet_id': sn['id'],
                      'tenant_id':     sn['tenant_id'],
                      'name':          'testlb_01'}
    start_folders = bigip.sys.folders.get_collection()
    # check that the bigip partitions are correct pre-create
    assert len(start_folders) == 2
    for sf in start_folders:
        assert sf.name == '/' or sf.name == 'Common'
    # Initialize lb and wait for confirmation from neutron
    active_lb = nclientmanager.create_loadbalancer({'loadbalancer': lbconf})
    lbid = active_lb['loadbalancer']['id']
    assert active_lb['loadbalancer']['provisioning_status'] == 'ACTIVE'
    assert active_lb['loadbalancer']['provider'] == 'f5networkstest'
    # verify the creation of the appropriate partition on the bigip
    active_folders = bigip.sys.folders.get_collection()
    assert len(active_folders) == 3
    for sf in active_folders:
        assert sf.name == '/' or\
            sf.name == 'Common' or\
            sf.name.startswith('Test_')
    # delete
    nclientmanager.delete_loadbalancer(lbid)
    # verify removal from OS on delete
    assert not nclientmanager.list_loadbalancers()['loadbalancers']
    final_folders = bigip.sys.folders.get_collection()
    # verify removal of partition from bigip on delete
    assert len(final_folders) == 2
    for sf in final_folders:
        assert sf.name == '/' or sf.name == 'Common'


@pytest.fixture
def setup_with_loadbalancer(setup_with_nclientmanager):
    nclientmanager = setup_with_nclientmanager
    subnets = nclientmanager.list_subnets()['subnets']
    for sn in subnets:
        if 'client-v4' in sn['name']:
            lbconf = {'vip_subnet_id': sn['id'],
                      'tenant_id':     sn['tenant_id'],
                      'name':          'testlb_01'}
    activelb =\
        nclientmanager.create_loadbalancer({'loadbalancer': lbconf})
    return nclientmanager, activelb


def test_listener_CD(setup_with_loadbalancer, bigip):
    nclientmanager, loadbalancer = setup_with_loadbalancer
    listener_config =\
        {'listener': {'name': 'test_listener',
                      'loadbalancer_id': loadbalancer['loadbalancer']['id'],
                      'protocol': 'HTTP',
                      'protocol_port': 80}}
    init_virts = bigip.ltm.virtuals.get_collection()
    assert init_virts == []
    listener = nclientmanager.create_listener(listener_config)
    active_virts = bigip.ltm.virtuals.get_collection()
    assert active_virts[0].name == 'test_listener'
    nclientmanager.delete_listener(listener['listener']['id'])
    virts = bigip.ltm.virtuals.get_collection()
    assert virts == []


@pytest.fixture
def setup_with_listener(setup_with_loadbalancer):
    nclientmanager, activelb = setup_with_loadbalancer
    listener_config =\
        {'listener': {'name': 'test_listener',
                      'loadbalancer_id': activelb['loadbalancer']['id'],
                      'protocol': 'HTTP',
                      'protocol_port': 80}}
    listener = nclientmanager.create_listener(listener_config)
    return nclientmanager, listener


def test_pool_CD(setup_with_listener, bigip):
    nclientmanager, listener = setup_with_listener
    pool_config = {'pool': {
                   'name': 'test_pool_anur23rgg',
                   'lb_algorithm': 'ROUND_ROBIN',
                   'listener_id': listener['listener']['id'],
                   'protocol': 'HTTP'}}
    # The bigip starts life with 0 pools
    assert not bigip.ltm.pools.get_collection()
    pool = nclientmanager.create_lbaas_pool(pool_config)
    # The create_lbaas_pool call adds a pool to the bigip
    assert bigip.ltm.pools.get_collection()[0].name == 'test_pool_anur23rgg'
    nclientmanager.delete_lbaas_pool(pool['pool']['id'])
    assert not bigip.ltm.pools.get_collection()


@pytest.fixture
def setup_with_pool(setup_with_listener):
    nclientmanager, activelistener = setup_with_listener
    pool_config = {'pool': {
                   'name': 'test_pool_anur23rgg',
                   'lb_algorithm': 'ROUND_ROBIN',
                   'listener_id': activelistener['listener']['id'],
                   'protocol': 'HTTP'}}
    pool = nclientmanager.create_lbaas_pool(pool_config)
    return nclientmanager, pool


def test_member_CD(setup_with_pool, bigip):
    nclientmanager, pool = setup_with_pool
    poolname = pool['pool']['name']
    pool_id = pool['pool']['id']
    bigip_pool_members = bigip.ltm.pools.get_collection()[0].members_s
    assert not nclientmanager.list_lbaas_members(pool_id)['members']
    for sn in nclientmanager.list_subnets()['subnets']:
        if 'server-v4' in sn['name']:
            address = sn['allocation_pools'][0]['start']
            subnet_id = sn['id']
            break

    member_config = {'member': {
                     'subnet_id': subnet_id,
                     'address': address,
                     'protocol_port': 80}}
    member = nclientmanager.create_lbaas_member(pool_id, member_config)
    attempts = 0
    while not bigip_pool_members.get_collection():
        attempts = attempts + 1
        time.sleep(.5)
        if attempts > 8:
            sys.exit(9999)

    bigip_pool_member = bigip_pool_members.get_collection()[0]
    assert poolname in bigip_pool_member.selfLink
    address_plus_port =\
        '%s:%s' % (address, member_config['member']['protocol_port'])
    assert address_plus_port in bigip_pool_member.selfLink
    nclientmanager.delete_lbaas_member(member['member']['id'], pool_id)
    assert not bigip_pool_members.get_collection()


@pytest.fixture
def setup_with_pool_member(setup_with_pool):
    nclientmanager, activepool = setup_with_pool
    pool_id = activepool['pool']['id']
    for sn in nclientmanager.list_subnets()['subnets']:
        if 'server-v4' in sn['name']:
            address = sn['allocation_pools'][0]['start']
            subnet_id = sn['id']
            break

    member_config = {'member': {
                     'subnet_id': subnet_id,
                     'address': address,
                     'protocol_port': 80}}
    member = nclientmanager.create_lbaas_member(pool_id, member_config)
    return nclientmanager, activepool, member


def test_health_monitor_CD(setup_with_pool_member, bigip):
    nclientmanager, pool, member = setup_with_pool_member
    init_bip_http_monitors = bigip.ltm.monitor.https.get_collection()
    pp(init_bip_http_monitors)
    assert len(init_bip_http_monitors) == 2
    monitor_dict = {}
    for monitor in init_bip_http_monitors:
        monitor_dict[monitor.selfLink] = monitor
    monitor_config = {'healthmonitor': {
                      'delay': 3,
                      'pool_id': pool['pool']['id'],
                      'type': 'HTTP',
                      'timeout': 13,
                      'max_retries': 7}}
    monitor = nclientmanager.create_lbaas_healthmonitor(monitor_config)
    interval = .05
    total = 0
    while len(bigip.ltm.monitor.https.get_collection()) == 2:
        time.sleep(interval)
        total = total + interval
    pp(total)
    assert len(bigip.ltm.monitor.https.get_collection()) == 3
    nclientmanager.delete_lbaas_healthmonitor(monitor['healthmonitor']['id'])
    assert len(bigip.ltm.monitor.https.get_collection()) == 2
