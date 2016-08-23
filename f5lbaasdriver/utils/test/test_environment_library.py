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


from __future__ import absolute_import

import errno
import os
import pytest
import tempfile
import time

from f5lbaasdriver.utils import environment_library
from f5lbaasdriver.utils.environment_library import ENVMODULETEMPLATE


LBAASCONFDATA = open(os.path.join(os.path.dirname(__file__),
                     'exampleconfdata.txt')).read()

MODDEDLBAASCONFDATA = open(os.path.join(os.path.dirname(__file__),
                           'modifiedexampleconfdata.txt')).read()

GENDRDATA = open(os.path.join(os.path.dirname(__file__),
                              'gendriverconfdata.txt')).read()

FAKE_ENV = "a"*5


@pytest.fixture
def temp_files(monkeypatch):
    timestring = str(time.time())
    TEMPFILEDIRNAME = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   'temp_files',
                                   timestring)
    try:
        os.makedirs(TEMPFILEDIRNAME)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(TEMPFILEDIRNAME):
            pass
        else:
            raise
    tempprefixname = TEMPFILEDIRNAME + os.path.sep
    temp_conf = tempfile.NamedTemporaryFile(prefix=tempprefixname,
                                            delete=False)
    tempdriverdirname = tempfile.mkdtemp(prefix=tempprefixname)
    tempname = temp_conf.name
    tempname_bak = tempname + timestring + '_bak'
    monkeypatch.setattr(
        "f5lbaasdriver.utils.environment_library.NEUTRON_LBAASCONFPATH",
        tempname)
    monkeypatch.setattr(
        "f5lbaasdriver.utils.environment_library.NEUTRON_LBAASCONF_BAK_PATH",
        tempname_bak)
    monkeypatch.setattr(
        "f5lbaasdriver.utils.environment_library.DRIVER_DIR",
        tempdriverdirname)
    with open(tempname, 'w') as tempconfh:
        tempconfh.write(LBAASCONFDATA)
    return tempname, tempname_bak, tempdriverdirname


def test_backup_lbaas_config_file_initial_backup(temp_files):
    testconfname, testconfname_bak, _ = temp_files
    with pytest.raises(OSError) as OSEEIO:
        os.remove(testconfname_bak)
    assert OSEEIO.value.args[1] == 'No such file or directory'
    environment_library.backup_lbaas_config_file()
    with open(testconfname, 'r') as t, open(testconfname_bak, 'r') as tb:
        assert t.read() == tb.read()


def test_backup_lbaas_config_backup_is_directory(temp_files):
    testconfname, testconfname_bak, _ = temp_files
    os.makedirs(testconfname_bak)
    with pytest.raises(OSError) as OSEEIO:
        environment_library.backup_lbaas_config_file()
    assert OSEEIO.value.args[1] == 'Is a directory'


def test_backup_lbaas_config_backup_is_present(temp_files):
    testconfname, testconfname_bak, _ = temp_files
    with open(testconfname_bak, 'w') as tbh:
        tbh.write('TEST')
    environment_library.backup_lbaas_config_file()
    with open(testconfname, 'r') as t, open(testconfname_bak, 'r') as tb:
        assert t.read() == tb.read()


def test_add_env_confopt_value(temp_files):
    from oslo_config.cfg import ConfigParser
    testconfname, testconfname_bak, _ = temp_files
    testconf = ConfigParser(testconfname, {})
    testconf.parse()
    original_values = set()
    original_service_providers = set()
    for section in testconf.sections.values():
        for option, values in section.items():
            if option == 'service_provider':
                original_service_providers.update(set(values))
            original_values.update(set(values))

    new_config = environment_library.add_env_confopt_value(FAKE_ENV)
    new_values = set()
    new_service_providers = set()
    for section in new_config.sections.values():
        for option, values in section.items():
            if option == 'service_provider':
                new_service_providers.update(set(values))
            new_values.update(set(values))
    assert new_values == original_values | set([FAKE_ENV])
    assert new_service_providers ==\
        original_service_providers | set([FAKE_ENV])


def test_write_config_file(temp_files):
    testconfname, testconfname_bak, _ = temp_files
    new_config = environment_library.add_env_confopt_value(FAKE_ENV)
    environment_library.write_config_file(new_config)
    assert open(testconfname, 'r').read() == MODDEDLBAASCONFDATA


def test_insert_env_into_neutron_lbaas_conf(temp_files):
    testconfname, testconfname_bak, _ = temp_files
    environment_library.insert_env_into_neutron_lbaas_conf(FAKE_ENV)
    assert open(testconfname, 'r').read() == MODDEDLBAASCONFDATA


def test_generate_driver(temp_files):
    testconfname, testconfname_bak, testdriverdirname = temp_files
    environment_library.generate_driver(FAKE_ENV)
    assert open(testconfname, 'r').read() == GENDRDATA
    FAKEDMODULE = ENVMODULETEMPLATE.format(FAKE_ENV)
    FAKEMODULENAME = os.path.join(testdriverdirname, 'v2_' + FAKE_ENV + '.py')
    assert open(FAKEMODULENAME, 'r').read() == FAKEDMODULE


def test_generate_driver_module_collision(temp_files):
    testconfname, testconfname_bak, testdriverdirname = temp_files
    FAKEMODULENAME = os.path.join(testdriverdirname, 'v2_' + FAKE_ENV + '.py')
    open(FAKEMODULENAME, 'w').write('COLLISION!')
    with pytest.raises(OSError) as OSEIO:
        environment_library.generate_driver(FAKE_ENV)
    error_message = '"' + os.path.abspath(FAKEMODULENAME) + '"' +\
                    ': Python module already exists!'
    assert OSEIO.value.args[0] == error_message
