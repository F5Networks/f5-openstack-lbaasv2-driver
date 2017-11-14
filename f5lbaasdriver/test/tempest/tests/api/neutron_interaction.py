# Copyright 2015, 2016 Rackspace Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import pdb
import re
import subprocess
import uuid

from collections import namedtuple
from time import sleep

from bigip_interaction import BigIpInteraction

"""Module for test-based interactions with the BIG-IP

    This module offers classes and methods that can be used to interact with
    the BIG-IP's configuration.  As a part of this, tests can peform necessary
    standup and teardown actions.
"""


class NeutronInteraction(object):
    """NeutronInteraction class object used for Neutron test interaction

    This is a standard class with a list of useful methods that perform
    different stand up and teardown actions around storing and establishing a
    baseline for the Neutron's config and recalling it from memory.
    """
    backup_file = "/tmp/neutron_db.sql"
    dirty_file = "/tmp/neutron_db_dirty_{}.sql"
    __ssh_cfg = "/home/ubuntu/testenv_symbols/testenv_ssh_config"
    __ssh_cmd = \
        "ssh -F {} openstack_master_0".format(__ssh_cfg)
    __extract_neutron_cfg = """{} << EOF
sudo grep -e '^connection' /etc/neutron/neutron.conf
exit
EOF
""".format(__ssh_cmd)
    __extract_cmd = '{} mysqldump -u {} -p{} -h {} {} > {}'
    # connection=mysql+pymysql://user:pw@host/db
    __line_parse = \
        re.compile('^connection=mysql\+pymysql://([^:]+):([^@]+)@([^/]+)/(\w+)')
    __Creds = namedtuple('Creds', 'username, password, hostname, database')
    __restore_cmd = "{} mysql -u {} -p{} -h {} {} < {}"

    @staticmethod
    def __exec_shell(stdin, shell=False):
        """An internal method"""
        Result = namedtuple('Result', 'stdout, stdin, stderr, exit_status')
        try:
            stdout = subprocess.check_output(stdin, shell=shell)
            stderr = ''
            exit_status = 0
        except subprocess.CalledProcessError as error:
            stderr = str(error)
            stdout = error.output
            exit_status = error.returncode

        return Result(stdout, stdin, stderr, exit_status)

    @staticmethod
    def _handle_results(results):
        """Handle simple results"""
        if results.exit_status:
            raise RuntimeError(
                "Could not extract bigip data!\nstderr:'{}'"
                ";stdout'{}' ({})".format(results.stderr, results.stdout,
                                          results.exit_status))

    @classmethod
    def __get_connection(cls):
        results = cls.__exec_shell(cls.__extract_neutron_cfg, shell=True)
        cls._handle_results(results)
        pdb.set_trace()
        for line in results.stdout.split("\n"):
            match = cls.__line_parse.search(line)
            if match:
                connection = cls.__Creds(*match.groups())
                break
        else:
            raise RuntimeError("Could not perform neutron action")
        return connection

    @classmethod
    def _get_current_neutron_cfg(cls, connection=None):
        """Get and return the current Neutron DB Config

        This method will perform the action of backing up the Neutron DB config
        data.
        """
        if not connection:
            connection = cls.__get_connection()
        results = \
            cls.__exec_shell(
                cls.__extract_cmd.format(
                    cls.__ssh_cmd, connection.username, connection.password,
                    connection.hostname, connection.database, cls.backup_file),
                True)
        cls._handle_results(results)
        return results.stdout

    @classmethod
    def _get_existing_neutron_cfg(cls):
        """Extracts the Neutron DB cfg and stores it within instance

        This method will hold a copy of the existing Neutron DB cfg for later
        comparison.
        """
        result = cls._get_current_neutron_cfg()
        with open(cls.backup_file, 'w') as fh:
            fh.write(result)

    @classmethod
    def __restore_neutron_db(cls, connection=None):
        if not connection:
            connection = cls.__get_connection()
        results = \
            cls.__exec_shell(
                cls.__restore_cmd.format(
                    cls.__ssh_cmd, connection.username, connection.password,
                    connection.hostname, connection.database, cls.backup_file),
                True)
        cls._handle_results(results)

    @classmethod
    def _extract_diff(cls, result):
        my_id = uuid.uuid4()
        dirty_file = cls.dirty_file.format(my_id)
        with open(dirty_file, 'w') as fh:
            fh.write(result)
        diff_file = "/tmp/{}.diff".format(my_id)
        cmd = \
            "diff -u {} {} > {}".format(cls.backup_file, dirty_file, diff_file)
        cls.__exec_shell(cmd, True)
        return diff_file

    @classmethod
    def _resulting_neutron_cfg(cls):
        connection = cls.__get_connection()
        result = cls._get_current_neutron_cfg(connection=connection)
        try:
            with open(cls.backup_file) as fh:
                content = fh.read()
            assert result == content, \
                "Test was unable to clean up Neutron cfg"
        except AssertionError as err:
            cls.__restore_neutron_db(connection=connection)
            my_diff_file = cls._extract_diff(content)
            bigip_diff_file = BigIpInteraction.force_clear()
            sleep(3)  # let all cfg propogate...
            raise AssertionError(
                "{} (diff: {}, bigip_diff: {})".format(
                    err, my_diff_file, bigip_diff_file))
        except (IOError, OSError):
            raise RuntimeError("Was unable to open backup file.  Perhaps "
                               "out-of-order extraction?")

    @classmethod
    def check_config(cls):
        cls._resulting_neutron_cfg()

    @classmethod
    def store_config(cls):
        if not os.path.isfile(cls.backup_file):
            cls._get_existing_neutron_cfg()
