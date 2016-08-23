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
from fabric.api import hosts, run, env, execute
from pprint import pprint as pp
import pytest
import random
import requests
import string

requests.packages.urllib3.disable_warnings()


def _generate_env():
    return\
        ''.join([
            string.ascii_lowercase[
                int(random.uniform(0, len(string.ascii_lowercase)))]
            for _ in range(12)]
        )


def add_diff_env_to_controller(differentiated_environment):
    env.host_string = ''.join([pytest.symbols.tenant_name,
                           '@',
                           pytest.symbols.controller_ip,
                           ':22'])

    @hosts(env.host_string)
    def setup_env_oncontroller(diff_env):
        env.password = pytest.symbols.tenant_password
        execute(lambda: run('sudo ls -la'))

        # Stop existing agent
        execute(lambda: run('sudo systemctl stop f5-openstack-agent'))
        # Stop neutron server / f5_plugin
        execute(lambda: run('sudo systemctl stop neutron-server'))
        # Edit agent configuration to use new environment
        sedtempl = '''sed -i "s/^\(environment_prefix = \)\(.*\)$/\1%s/"''' +\
                   ''' /etc/neutron/services/f5/f5-openstack-agent.ini'''
        sedstring = 'sudo ' + sedtempl % diff_env
        execute(lambda: run(sedstring))
        # Add diff env to neutron_lbaas.conf and installed Python package 
        add_string = 'sudo add_f5agent_environment %s' % diff_env
        execute(lambda: run(add_string))
        # Start neutron-server / f5_plugin
        execute(lambda: run('sudo systemctl start neutron-server'))
        # Start existing agent
        execute(lambda: run('source keystonerc_testlab && sudo systemctl start f5-openstack-agent'))

    setup_env_oncontroller(differentiated_environment)


@pytest.fixture
def setup_with_nclientmanager(request, nclientmanager):
    return nclientmanager


def test_loadbalancer_CLUS(setup_with_nclientmanager, bigip):
    TESTENV = _generate_env()
    add_diff_env_to_controller(TESTENV)
    # XXX TODO(za@f5.com) run the script on the controller
    nclientmanager = setup_with_nclientmanager
    subnets = nclientmanager.list_subnets()['subnets']
    for sn in subnets:
        if 'client-v4' in sn['name']:
            lbconf = {'vip_subnet_id': sn['id'],
                      'tenant_id':     sn['tenant_id'],
                      'name':          'testlb_%s' % TESTENV,
                      'provider':      TESTENV}
    active_lb = nclientmanager.create_loadbalancer({'loadbalancer': lbconf})
    lbid = active_lb['loadbalancer']['id']
    assert active_lb['loadbalancer']['description'] == ''
    assert active_lb['loadbalancer']['provisioning_status'] == 'ACTIVE'
    assert active_lb['loadbalancer']['provider'] == TESTENV
    # Test show and update
    nclientmanager.update_loadbalancer(
        lbid, {'loadbalancer': {'description': 'as;iofnypq3489'}})
    shown_lb = nclientmanager.show_loadbalancer(lbid)
    assert shown_lb['loadbalancer']['description'] == 'as;iofnypq3489'
    # verify the creation of the appropriate partition on the bigip
    folder_names =\
        [folder.name for folder in bigip.tm.sys.folders.get_collection()]
    assert lbconf['provider'] + '_' + lbconf['tenant_id'] in folder_names
    # delete
    nclientmanager.delete_loadbalancer(lbid)
    # verify removal from OS on delete
    # assert not nclientmanager.list_loadbalancers()['loadbalancers']
    # verify removal of partition from bigip on delete
    # assert len(final_folders) == 2
    # for sf in final_folders:
    #    assert sf.name == '/' or sf.name == 'Common'
