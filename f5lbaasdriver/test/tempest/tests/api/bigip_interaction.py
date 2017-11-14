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

import subprocess
import os

from collections import namedtuple

"""Module for test-based interactions with the BIG-IP

    This module offers classes and methods that can be used to interact with the
    BIG-IP's configuration.  As a part of this, tests can peform necessary standup
    and teardown actions.
"""


class BigIpInteraction(object):
    """BigIpInteraction class object used for BIG-IP test interaction

    This is a standard class with a list of useful methods that perform
    different stand up and teardown actions around storing and establishing a
    baseline for the BIG-IP's config and recalling it from memory.
    """
    config_file = "/tmp/agent_only.bigip.cfg"
    _lbs_to_delete = []
    __ssh_cfg = '/home/ubuntu/testenv_symbols/testenv_ssh_config'
    __ssh_cmd = \
        str("ssh -F {} openstack_bigip").format(__ssh_cfg)
    __extract_cmd = '''{} << EOF
tmsh -c \"cd /;
list sys folder recursive one-line" | cut -d " " -f3 |
while read f; do echo \"====================\";
echo \"Folder $f\"; tmsh -c "cd /$f; list\"; done;
exit
EOF'''.format(__ssh_cmd)
    __ucs_cmd_fmt = "{} tmsh {} /sys ucs /tmp/backup.ucs"


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

    @classmethod
    def _get_current_bigip_cfg(cls):
        """Get and return the current BIG-IP Config

        This method will perform the action of collecting BIG-IP config data.
        """
        results = cls.__exec_shell(cls.__extract_cmd, shell=True)
        if results.exit_status:
            raise RuntimeError(
                "Could not extract bigip data!\nstderr:'{}'"
                ";stdout'{}' ({})".format(results.stderr, results.stdout,
                                          results.exit_status))
        return results.stdout

    @classmethod
    def _get_existing_bigip_cfg(cls):
        """Extracts the BIG-IP config and stores it within instance

        This method will hold a copy of the existing BIG-IP config for later
        comparison.
        """
        result = cls._get_current_bigip_cfg()
        with open(cls.config_file, 'w') as fh:
            fh.write(result)

    @classmethod
    def _resulting_bigip_cfg(cls):
        result = cls._get_current_bigip_cfg()
        with open(cls.config_file) as fh:
            try:
                assert result == fh.read(), \
                    "Test was unable to clean up BIG-IP cfg"
            except AssertionError:
                cls.__exec_shell(cls.__ucs_cmd_fmt.format(cls.__ssh_cmd, 'load'),
                                 shell=True)
                sleep(5)  # after nuke, BIG-IP needs a delay...
                raise

    @classmethod
    def check_resulting_cfg(cls):
        """Check the current BIG-IP cfg agianst previous Reset upon Error

        This classmethod will check the current BIG-IP config and raise if
        there are any changes from the previous snap-shot.  Upon raise, the
        method will attempt to clear the BIG-IP back to the previous config
        """
        cls._resulting_bigip_cfg()

    @classmethod
    def store_config(cls):
        """Performs a backup at the UCS level of the BIG-IP"""
        cls.__exec_shell(cls.__ucs_cmd_fmt.format(cls.__ssh_cmd, 'save'), True)

    @classmethod
    def store_existing(cls):
        """Performs operation to store existing config state of BIG-IP"""
        cls._get_existing_bigip_cfg()
