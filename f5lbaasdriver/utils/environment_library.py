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

"""
.. module:: environment_library
    :synopsis: A library for generation of new "ENVIRONMENT" service_providers.

A library for generation of new "ENVIRONMENT" service_providers.

This is used by the "add_environment.py"" script with a single argument.

It modifies:

* "/etc/neutron/neutron_lbaas.conf"

and a module in:

** "{PYTHON_INSTALLED_PACKAGES}/neutron_lbaas/drivers/drivers/f5/"

It takes a single (positional) argument which is used as:

(0) the name of the F5LBaaSV2Driver subclass,
(1) the name of the service provider (visible with in the neutron database),
(2) and the name of the module that contains the custom class.

The utility writes the class string into the appropriate location (module) in
the Python namespace, (i.e. within the ** directory mentioned above).
"""

from __future__ import absolute_import

import inspect
import logging
import os
import shutil
import time

from neutron_lbaas.drivers.f5.driver_v2 import F5LBaaSV2Driver
from oslo_config.cfg import ConfigParser

rlogger = logging.getLogger()
rlogger.setLevel(logging.DEBUG)

DRIVER_DIR = os.path.dirname(inspect.getsourcefile(F5LBaaSV2Driver))
NEUTRON_LBAASCONFPATH = '/etc/neutron/neutron_lbaas.conf'
NEUTRON_LBAASCONF_BAK_PATH =\
    NEUTRON_LBAASCONFPATH + str(time.time()) + '_bak'

ENVMODULETEMPLATE = '''\
#!/usr/bin/env python

# Copyright 2014-2016 F5 Networks Inc.
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

from neutron_lbaas.drivers.f5.driver_v2 import F5LBaaSV2Driver


class {0}(F5LBaaSV2Driver):
    """Plugin Driver for {0} environment."""

    def __init__(self, plugin):
        super({0}, self).__init__(plugin, self.__class__.__name__)
'''


def backup_lbaas_config_file():
    """Backup the config file with a timestamped copy before manipulating.

    Whether or not a backup existed before create a new one. In the case of
    errors OTHER THAN a missing file when addressing backup path, bail out. As
    long as this utility runs less than once a microsecond backups should not
    collide.

    """
    try:
        os.remove(NEUTRON_LBAASCONF_BAK_PATH)
    except OSError as exc:
        if not exc.args[1] == 'No such file or directory':
            raise
    logging.debug('NEUTRON_LBAASCONFPATH: {0}'.format(NEUTRON_LBAASCONFPATH))
    logging.debug(
        'NEUTRON_LBAASCONF_BAK_PATH: {0}'.format(NEUTRON_LBAASCONF_BAK_PATH))
    shutil.copy(NEUTRON_LBAASCONFPATH, NEUTRON_LBAASCONF_BAK_PATH)


def add_env_confopt_value(env_serviceprovider_line):
    """Add a new service_provider opt = val to the service_provider section.

    This function parses an existing conf file and adds the new values to
    the appropriate dictionary in the resulting conf object.

    """
    conf = ConfigParser(NEUTRON_LBAASCONFPATH, {})
    conf.parse()
    conf.sections['service_providers']['service_provider']\
        .append(env_serviceprovider_line)
    return conf


def write_config_file(config_to_write):
    """Take an oslo.cfg config object to write an ini-style conf file.

    This function handles _writing_ the config file (the oslo_config
    ConfigParser doesn't appear to support this natively).

    """

    with open(NEUTRON_LBAASCONFPATH, 'w') as cfh:
        for section, options in config_to_write.sections.items():
            cfh.write('['+section+']\n')
            for opt, values in options.items():
                for value in values:
                    cfh.write(" ".join([opt, "=", value]) + '\n')


def insert_env_into_neutron_lbaas_conf(env_serviceprovider_line):
    """A high-level function that reconfigures the neutron_lbaas.conf file.

    This function first backs up the Neutron LBaaS configuration file, then
    produces a new neutron_lbaas.conf file that contains a service_provider
    entry for the new environment.

    It appends the new environment string to the F5Networks service_provider
    value, then creates an entry for the environment in the service_providers
    section of the neutron_lbaas.conf file.

    The function calls backup_lbaas_config_file() before mutating the config
    file.

    """

    backup_lbaas_config_file()
    new_config = add_env_confopt_value(env_serviceprovider_line)
    write_config_file(new_config)


def generate_driver(environment):
    """Given an environment string, produce a Python module.

    The product is a Python module named for the environment in the appropriate
    namespace, with a class of the same (environment name) that subclasses
    F5LBaaSV2Driver. The class name and path match the name and path
    written by the other functions in this utility.

    The form of the module can be understood by reading the ENVMODULETEMPLATE
    variable. This is the highest-level function in the utility. After
    manipulating the Python namespace, it then hands off the "environment"
    string to the insert_env_into_neutron_lbaas_conf function to handle
    mutation of the Neutron LBaaS config file ("neutron_lbaas.conf").

    """
    modname = "v2_" + environment
    modfilename = modname + '.py'
    drivermod_abspath = os.path.join(DRIVER_DIR, modfilename)

    if os.path.isfile(drivermod_abspath):
        raise OSError('"{0}": Python module already exists!'
                      .format(drivermod_abspath))

    with open(drivermod_abspath, 'w') as mf:
        mf.write(ENVMODULETEMPLATE.format(environment))

    confline = "LOADBALANCERV2:" + environment +\
               ":neutron_lbaas.drivers.f5." + modname +\
               "." + environment

    insert_env_into_neutron_lbaas_conf(confline)
