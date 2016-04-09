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

from pprint import pprint as pp
import pytest
import sys
import time


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


def test_loadbalancer_CLUDS(setup_with_nclientmanager, bigip):
    # NOTE:  list-on-agent is still untested
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
    assert active_lb['loadbalancer']['description'] == ''
    assert active_lb['loadbalancer']['provisioning_status'] == 'ACTIVE'
    assert active_lb['loadbalancer']['provider'] == 'f5networkstest'
    # Test show and update
    nclientmanager.update_loadbalancer(
        lbid, {'loadbalancer': {'description': 'as;iofnypq3489'}})
    shown_lb = nclientmanager.show_loadbalancer(lbid)
    assert shown_lb['loadbalancer']['description'] == 'as;iofnypq3489'
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


def test_listener_CLUDS(setup_with_loadbalancer, bigip):
    nclientmanager, loadbalancer = setup_with_loadbalancer
    listener_config =\
        {'listener': {'name': 'test_listener',
                      'loadbalancer_id': loadbalancer['loadbalancer']['id'],
                      'protocol': 'HTTP',
                      'protocol_port': 80}}
    init_virts = bigip.ltm.virtuals.get_collection()
    assert init_virts == []
    # Test list_listeners
    assert not nclientmanager.list_listeners()['listeners']
    listener = nclientmanager.create_listener(listener_config)
    listener_id = listener['listener']['id']
    assert listener['listener']['description'] == ''
    assert len(nclientmanager.list_listeners()['listeners']) == 1
    active_virts = bigip.ltm.virtuals.get_collection()
    assert active_virts[0].name == 'test_listener'
    # Test show and update
    nclientmanager.update_listener(
        listener_id, {'listener': {'description': 'awfoip8934'}})
    shown = nclientmanager.show_listener(listener_id)
    assert shown['listener']['description'] == 'awfoip8934'
    # Test delete
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


def test_pool_CLUDS(setup_with_listener, bigip):
    nclientmanager, listener = setup_with_listener
    pool_config = {'pool': {
                   'name': 'test_pool_anur23rgg',
                   'lb_algorithm': 'ROUND_ROBIN',
                   'listener_id': listener['listener']['id'],
                   'protocol': 'HTTP'}}
    # The bigip starts life with 0 pools
    # Test lbaas_list_pools
    assert not nclientmanager.list_lbaas_pools()['pools']
    assert not bigip.ltm.pools.get_collection()
    pool = nclientmanager.create_lbaas_pool(pool_config)
    pool_id = pool['pool']['id']
    assert pool['pool']['description'] == ''
    assert len(nclientmanager.list_lbaas_pools()['pools']) == 1
    # The create_lbaas_pool call adds a pool to the bigip
    assert bigip.ltm.pools.get_collection()[0].name == 'test_pool_anur23rgg'
    # Test Update, Show, 
    nclientmanager.update_lbaas_pool(
        pool_id, {'pool': {'description': '5978iuw34ghle'}})
    shown = nclientmanager.show_lbaas_pool(pool_id)
    assert shown['pool']['description'] == '5978iuw34ghle'
    # Test Delete
    nclientmanager.delete_lbaas_pool(pool_id)
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


def test_member_CLUDS(setup_with_pool, bigip):
    nclientmanager, pool = setup_with_pool
    poolname = pool['pool']['name']
    pool_id = pool['pool']['id']
    bigip_pool_members = bigip.ltm.pools.get_collection()[0].members_s
    # Test List
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
    member_id = member['member']['id']
    assert member['member']['weight'] == 1
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
    # Test Update, Show
    nclientmanager.update_lbaas_member(
        member_id, pool_id, {'member': {'weight': 5}})
    shown = nclientmanager.show_lbaas_member(member_id, pool_id)
    assert shown['member']['weight'] == 5
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


def test_healthmonitor_CLD(setup_with_pool_member, bigip):
    nclientmanager, pool, member = setup_with_pool_member
    # Test List
    assert not nclientmanager.list_lbaas_healthmonitors()['healthmonitors']
    init_bip_http_monitors = bigip.ltm.monitor.https.get_collection()
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
    healthmonitor = nclientmanager.create_lbaas_healthmonitor(monitor_config)
    healthmonitor_id = healthmonitor['healthmonitor']['id']
    assert healthmonitor['healthmonitor']['delay'] == 3
    assert\
        len(nclientmanager.list_lbaas_healthmonitors()['healthmonitors']) == 1
    interval = .05
    total = 0
    while len(bigip.ltm.monitor.https.get_collection()) == 2:
        time.sleep(interval)
        total = total + interval
    pp(total)
    assert len(bigip.ltm.monitor.https.get_collection()) == 3
    # Test show, update
    # nclientmanager.update_lbaas_healthmonitor(
    #    healthmonitor_id,
    #    {'healthmonitor': {'delay': 77}}
    # )
    # shown = nclientmanager.show_lbaas_healthmonitor(healthmonitor_id)
    # assert shown['healthmonitor']['delay'] == 77
    nclientmanager.delete_lbaas_healthmonitor(healthmonitor_id)
    assert len(bigip.ltm.monitor.https.get_collection()) == 2
