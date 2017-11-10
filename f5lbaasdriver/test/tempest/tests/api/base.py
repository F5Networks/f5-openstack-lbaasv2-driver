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

from collections import namedtuple
from time import sleep

from neutron_lbaas.tests.tempest.v2.api import base
from oslo_log import log as logging
from tempest import config

from f5lbaasdriver.test.tempest.services.clients.bigip_client \
    import BigIpClient
from f5lbaasdriver.test.tempest.services.clients import \
    plugin_rpc_client

CONF = config.CONF

LOG = logging.getLogger(__name__)


class F5BaseTestCase(base.BaseTestCase):
    """This class picks non-admin credentials and run the tempest tests."""

    config_file = "/tmp/tempest.bigip.cfg"
    _lbs_to_delete = []

    @staticmethod
    def __exec_shell(stdin, shell=False):
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
    def _get_exiting_neutron_cfg(cls):
        """Place holder for attaining neutron's current cfg before test"""
        pass

    @classmethod
    def _resulting_bigip_cfg(cls):
        result = cls._get_current_bigip_cfg()
        with open(cls.config_file) as fh:
            try:
                assert result == fh.read(), \
                    "Test was unable to clean up BIG-IP cfg"
            except AssertionError:
                cls.__exec_shell(cls.__ucs_cmd_fmt.format(cls.ssh_cmd, 'load'),
                                 shell=True)
                sleep(5)  # after nuke, BIG-IP needs a delay...
                raise

    @classmethod
    def _resulting_neutron_db(cls):
        """Place holder for sanity check code for pollutted neutron DB"""
        pass

    @classmethod
    def check_resulting_cfg(cls):
        """Check the current BIG-IP cfg agianst previous Reset upon Error

        This classmethod will check the current BIG-IP config and raise if
        there are any changes from the previous snap-shot.  Upon raise, the
        method will attempt to clear the BIG-IP back to the previous config
        """
        cls._resulting_bigip_cfg()
        cls._resulting_neutron_db()

    @classmethod
    def resource_setup(cls):
        """Setup the clients and fixtures for test suite.

        When testing BIG-IP clusters, CONF.f5_lbaasv2_driver.icontrol_hostname
        will be a comma delimited string of IP addresses. A list of clients is
        created, and test writers should iterate the list when validating
        BIG-IP operations. Test writers can choose to reference a single
        BIG-IP using self.bigip_client, which points to the client created
        with the first address in CONF.f5_lbaasv2_driver.icontrol_hostname.
        """
        super(F5BaseTestCase, cls).resource_setup()
        cls.__exec_shell(cls.__ucs_cmd_fmt.format(cls.ssh_cmd, 'save'), True)
        # Where the neutron db collection between resource setups goes

        cls.bigip_clients = []
        for host in CONF.f5_lbaasv2_driver.icontrol_hostname.split(","):
            cls.bigip_clients.append(BigIpClient(
                host,
                CONF.f5_lbaasv2_driver.icontrol_username,
                CONF.f5_lbaasv2_driver.icontrol_password))
        cls.bigip_client = cls.bigip_clients[0]

        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )

    def setUp(self):
        """Performs basic teardown operations for assocaited tests"""
        self._get_existing_bigip_cfg()
        self._get_exiting_neutron_cfg()
        super(F5BaseTestCase, self).setUp()

    def tearDown(self):
        """Performs basic teardown operations for assocaited tests"""
        self.check_resulting_cfg()
        super(F5BaseTestCase, self).tearDown()


class F5BaseAdminTestCase(base.BaseTestCase):
    """This class picks admin credentials and run the tempest tests."""

    @classmethod
    def resource_setup(cls):
        """Initialize the client objects."""
        super(F5BaseAdminTestCase, cls).resource_setup()
        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )
