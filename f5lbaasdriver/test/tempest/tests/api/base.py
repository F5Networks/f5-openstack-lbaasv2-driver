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
from f5lbaasdriver.test.tempest.tests.api.bigip_interaction import \
    BigIpInteraction

CONF = config.CONF

LOG = logging.getLogger(__name__)


class F5BaseTestCase(base.BaseTestCase):
    """This class picks non-admin credentials and run the tempest tests."""

    _lbs_to_delete = []

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
        BigIpInteraction.store_config()

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
        """Performs basic setup operations for inheriting test classes"""
        BigIpInteraction.store_existing()
        super(F5BaseTestCase, self).setUp()

    def tearDown(self):
        """Performs basic teardown operations for inheriting test classes"""
        BigIpInteraction.check_resulting_cfg()
        super(F5BaseTestCase, self).tearDown()


class F5BaseAdminTestCase(base.BaseTestCase):
    """This class picks admin credentials and run the tempest tests."""

    @classmethod
    def resource_setup(cls):
        """Initialize the client objects."""
        super(F5BaseAdminTestCase, cls).resource_setup()
        BigIpInteraction.store_config()
        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )

    def setUp(self):
        """Performs basic setup operation for inheriting test classes"""
        BigIpInteraction.store_existing()
        super(F5BaseAdminTestCase, self).setUp()

    def tearDown(self):
        """Performs basic teardown operation for inheriting test classes"""
        BigIpInteraction.check_resulting_cfg()
        super(F5BaseAdminTestCase, self).tearDown()
        
