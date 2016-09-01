#!/usr/bin/env python

# Copyright 2014 F5 Networks Inc.
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
'''See environment_library for details.'''
import argparse

from fabric.api import env
from fabric.api import execute
from fabric.api import hosts
from fabric.api import run
import pytest

from f5lbaasdriver.utils.environment_library import generate_driver


def add_diff_env_to_controller(differentiated_environment):
    '''Add a differentiated environment remotely, and bounce services.

    This function is used in:

     *  test/functional/test_environment_add.py

    probably the quickest way to adapt is to examine that example.
    Given an appropriate host_string and password this function:

    (0) halts services on a neutron controller
    (1) reconfigures the relevant files to add an "environment"
        service_provider
    (2) restarts the services (CRITICAL NOTE: the relevant credentials are
    hardcoded via the 'source keystonerc_testlab' line.  NOT what you want
    unless you're testing inside f5.)
    '''
    env.host_string = ''.join(
        [pytest.symbols.tenant_name,
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
        sedtempl = '''sed -i "s/^\(environment_prefix = \)\(.*\)$/\\1%s/"''' +\
                   ''' /etc/neutron/services/f5/f5-openstack-agent.ini'''
        sedstring = 'sudo ' + sedtempl % diff_env
        execute(lambda: run(sedstring))
        # Add diff env to neutron_lbaas.conf and installed Python package
        add_string = 'sudo add_f5agent_environment %s' % diff_env
        execute(lambda: run(add_string))
        # Start neutron-server / f5_plugin
        execute(lambda: run('sudo systemctl start neutron-server'))
        # Start existing agent
        execute(lambda: run('source keystonerc_testlab && '
                            'sudo systemctl start f5-openstack-agent'))

    setup_env_oncontroller(differentiated_environment)


def main():
    parser = argparse.ArgumentParser(
        description='''This utility is designed to run on the neutron
        controller.  To remotely configure your controller with this utility
        use the f5lbaasdriver.utils.add_environment.add_diff_env_to_controller
        function.''')
    parser.add_argument("environment",
                        help="The name of the enviroment to generate.")
    args = parser.parse_args()
    generate_driver(args.environment)

if __name__ == '__main__':
    main()
