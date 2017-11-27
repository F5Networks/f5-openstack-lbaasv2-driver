#!/usr/bin/env python
# Copyright 2017 F5 Networks Inc.
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

import datetime
import json
import os
import subprocess

from collections import namedtuple
from time import sleep

"""Module for test-based interactions with the BIG-IP

    This module offers classes and methods that can be used to interact with
    the BIG-IP's configuration.  As a part of this, tests can peform necessary
    standup and teardown actions.

    Upon teardown, if the module discoves a diff between the snap-shotted copy
    of the BIG-IP's starting config and the post-test config, then a diff file
    is generated.  This diff file is generated using linux's `which diff` app.

    The format of the file and the file's location depends upon the test
    instance and the test's name as follows:
        /tmp/tempest_bigip_<test>_<year><month><day><hour><minute><second>.diff
    Example:
        /tmp/tempest_bigip_test_foo_20170703222336.diff
        or 2017/07/03 22:23:36 or 10:23:36 PM on Jul 3 2017
    The time is derived during compile time of the tests, not during runtime.
    This assures that all diff files generated during a single test run have
    the same timestamp in the filename; thus, it is expected that some files
    may not have the same creation date epoch as the timestamp in the filename.
"""

my_epoch = datetime.datetime.now().strftime('%Y%m%d%H%M%S')  # epoch


class BigIpInteraction(object):
    """BigIpInteraction class object used for BIG-IP test interaction

    This is a standard class with a list of useful methods that perform
    different stand up and teardown actions around storing and establishing a
    baseline for the BIG-IP's config and recalling it from memory.
    """
    config_file = "/tmp/tempest_bigip_{}.cfg"
    dirty_file = "/tmp/tempest_bigip_{}_{}.cfg"
    diff_file = "/tmp/tempest_bigip_diff_{}_{}.cfg"
    _lbs_to_delete = []
    __env_cfg = '{}/testenv_symbols/testenv_symbols.json'.format(
        os.environ.get('HOME'))
    __extract_cmd = '''{} << EOF
tmsh -c \"cd /;
list sys folder recursive one-line" | cut -d " " -f3 |
while read f; do echo \"====================\";
echo \"Folder $f\"; tmsh -c "cd /$f; list\"; done;
exit
EOF'''
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
    def __bigip(cls):
        """An internal method"""
        # anything more complex cls-wise should be an object instance...
        my_host = getattr(cls, 'my_host', '')
        my_uname = getattr(cls, 'my_uname', '')
        if not my_host or not my_uname:
            with open(cls.__env_cfg, 'r') as fh:
                env = json.load(fh)
            for key in env.keys():
                if key.endswith('BIGIP_MGMT_IP_PUBLIC'):
                    my_host = env[key]
                elif key.endswith('BIGIP_SSH_USERNAME'):
                    my_uname = env[key]
                if my_host and my_uname:
                    break
            else:
                raise EnvironmentError(
                    "Could not derive 'BIGIP_MGMT_IP_PUBLIC$' from {}".format(
                        cls.__env_cfg))
            cls.my_host = my_host
            cls.my_uname = my_uname
        return "ssh {}@{}".format(my_uname, my_host)

    @staticmethod
    def __check_results(results):
        if results.exit_status:
            raise RuntimeError(
                "Could not extract bigip data!\nstderr:'{}'"
                ";stdout'{}' ({})".format(results.stderr, results.stdout,
                                          results.exit_status))

    @classmethod
    def _get_current_bigip_cfg(cls):
        """Get and return the current BIG-IP Config

        This method will perform the action of collecting BIG-IP config data.
        """
        bigip_ssh = cls.__bigip()
        results = cls.__exec_shell(
            cls.__extract_cmd.format(bigip_ssh), shell=True)
        cls.__check_results(results)
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
    def __restore_from_backup(cls):
        """An internal method"""
        bigip_ssh = cls.__bigip()
        cls.__exec_shell(
            cls.__ucs_cmd_fmt.format(
                bigip_ssh, 'load'), shell=True)

    @classmethod
    def _resulting_bigip_cfg(cls, test_method):
        """Checks the resulting BIG-IP config as it stands against snap shot

        This method will raise upon discovery of a polluted config against snap
        shot.  Upon a raise, it will also:
            * restore from backup
            * Sleep 5 seconds to asssure the BIG-IP is ready for REST cmds
            * Generate a diff file against the polluted config
        """
        try:
            with open(cls.config_file) as fh:
                content = fh.read()
            diff_file = cls.__collect_diff(content, test_method)
            os.remove(diff_file)
        except AssertionError as err:
            cls.__restore_from_backup()
            sleep(5)  # after nuke, BIG-IP needs a delay...
            raise AssertionError(
                "BIG-IP cfg was polluted by test!! (diff: {})".format(err))

    @classmethod
    def _collect_diff(cls):
        """An accessible diff collection without a frame.

        This method can force the collection of a diff at any time during the
        testing process and does not necessarily require a difference between
        snapshot and current BIG-IP config.
        """
        result = cls._get_current_bigip_cfg()
        try:
            diff_file = cls.__collect_diff(result)
        except AssertionError as err:
            diff_file = str(err)
        return diff_file

    @classmethod
    def __collect_diff(cls, result, test_method):
        """An internal method"""
        dirty_file = cls.dirty_file.format(test_method, my_epoch)
        with open(dirty_file, 'w') as fh:
            fh.write(result)
        diff_file = cls.diff_file.format(test_method, my_epoch)
        cmd = "diff -u {} {} > {}".format(
            cls.config_file, dirty_file, diff_file)
        result = cls.__exec_shell(cmd, True)
        cls.__check_results(result)
        if os.path.getsize(diff_file) > 0:
            raise AssertionError(diff_file)
        return diff_file

    @classmethod
    def check_resulting_cfg(cls, test_method):
        """Check the current BIG-IP cfg agianst previous Reset upon Error

        This classmethod will check the current BIG-IP config and raise if
        there are any changes from the previous snap-shot.  Upon raise, the
        method will attempt to clear the BIG-IP back to the previous config
        """
        cls._resulting_bigip_cfg(test_method)

    @classmethod
    def store_config(cls):
        """Performs a backup at the UCS level of the BIG-IP"""
        bigip_ssh = cls.__bigip()
        cls.__exec_shell(cls.__ucs_cmd_fmt.format(bigip_ssh, 'save'), True)

    @classmethod
    def store_existing(cls):
        """Performs operation to store existing config state of BIG-IP"""
        cls._get_existing_bigip_cfg()

    @classmethod
    def force_clear(cls):
        """Forces a clear reload from back up of the BIG-IP's config.

        This method should only be used when it is assumed and known that the
        BIG-IP's config is polluted and a diff will be forcably taken with a
        forced reset of the BIG-IP to the snap-shot results.
        """
        diff_file = cls._collect_diff()
        cls.__restore_from_backup()
        return diff_file
