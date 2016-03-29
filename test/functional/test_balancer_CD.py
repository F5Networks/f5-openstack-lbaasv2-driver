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
import time

from f5.bigip import BigIP
from neutronclient.v2_0 import client
import pytest


hostname = '10.190.3.26'


@pytest.fixture
def bigip():
    b = BigIP(hostname=hostname, username='admin', password='admin')
    return b


@pytest.fixture
def neutronc():
    nclient_config = {
        'username': 'testlab',
        'password': 'changeme',
        'tenant_name': 'testlab',
        'auth_url': 'http://10.190.4.153:5000/v2.0'}

    neutronclient = client.Client(**nclient_config)
    return neutronclient


@pytest.fixture
def setup_with_neutronc(request, neutronc):
    def clear_lbs():
        for lb in neutronc.list_loadbalancers()['loadbalancers']:
            neutronc.delete_loadbalancer(lb['id'])
        while neutronc.list_loadbalancers()['loadbalancers']:
            time.sleep(1)
    clear_lbs()
    request.addfinalizer(clear_lbs)
    return neutronc


def wait_for_lb_state(lbid, state, client, polling_interval=1):
    time.sleep(polling_interval)
    current_state = client.show_loadbalancer(lbid)
    current_p_status = current_state['loadbalancer']['provisioning_status']
    while state != current_p_status:
        current_state = client.show_loadbalancer(lbid)
        current_p_status = current_state['laodbalancer']['provisioning_status']
        time.sleep(polling_interval)
    return current_state


def test_lb_CD(setup_with_neutronc, bigip):
    # setup
    neutronclient = setup_with_neutronc
    subnets = neutronclient.list_subnets()['subnets']
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
    init_lb = neutronclient.create_loadbalancer({'loadbalancer': lbconf})
    lbid = init_lb['loadbalancer']['id']
    active_lb = wait_for_lb_state(lbid, 'ACTIVE', neutronclient)

    # check that the OS system becomes aware of a correct lb on create
    assert active_lb['loadbalancer']['provisioning_status'] == 'ACTIVE'
    assert active_lb['loadbalancer']['provider'] == 'f5networkstest'
    pp(bigip._meta_data['uri'])
    active_folders = bigip.sys.folders.get_collection()

    # verify the creation of the appropriate partition on the bigip
    assert len(active_folders) == 3
    for sf in active_folders:
        assert sf.name == '/' or\
            sf.name == 'Common' or\
            sf.name.startswith('Test_')
    neutronclient.delete_loadbalancer(lbid)
    balancers = neutronclient.list_loadbalancers()['loadbalancers']
    while balancers:
        time.sleep(1)
        balancers = neutronclient.list_loadbalancers()['loadbalancers']

    # verify removal from OS on delete
    assert not balancers
    final_folders = bigip.sys.folders.get_collection()

    # verify removal of partition from bigip on delete
    assert len(final_folders) == 2
    for sf in final_folders:
        assert sf.name == '/' or sf.name == 'Common'
