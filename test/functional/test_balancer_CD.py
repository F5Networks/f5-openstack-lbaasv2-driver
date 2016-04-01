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


@pytest.fixture
def nclientmanager(polling_neutronclient):
    nclient_config = {
        'username': 'testlab',
        'password': 'changeme',
        'tenant_name': 'testlab',
        'auth_url': 'http://10.190.4.153:5000/v2.0'}

    neutronclient = client.Client(**nclient_config)
    return polling_neutronclient(neutronclient)


@pytest.fixture
def setup_with_nclientmanager(request, nclientmanager):
    def teardown():
        pp('Entered clear_listeners')
        nclientmanager.delete_all_listeners()
        nclientmanager.delete_all_loadbalancers()

    teardown()
    request.addfinalizer(teardown)
    return nclientmanager


def test_lb_CD(setup_with_nclientmanager, bigip):
    # set initial state
    nclientmanager = setup_with_nclientmanager
    pp('test started')
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
    pp('folders start correct')
    # Initialize lb and wait for confirmation from neutron
    active_lb = nclientmanager.create_loadbalancer({'loadbalancer': lbconf})
    lbid = active_lb['loadbalancer']['id']
    assert active_lb['loadbalancer']['provisioning_status'] == 'ACTIVE'
    assert active_lb['loadbalancer']['provider'] == 'f5networkstest'
    # verify the creation of the appropriate partition on the bigip
    pp(bigip._meta_data['uri'])
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
    pp(active_virts[0].raw)
    assert active_virts[0].name == 'test_listener'
    nclientmanager.delete_listener(listener['listener']['id'])
    virts = bigip.ltm.virtuals.get_collection()
    pp(virts)
    assert virts == []
