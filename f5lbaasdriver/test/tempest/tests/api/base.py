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

    _lbs_to_delete = []

    @classmethod
    def resource_setup(cls):
        """Setup the clients and fixtures for test suite."""
        super(F5BaseTestCase, cls).resource_setup()

        cls.bigip_client = BigIpClient(
            CONF.f5_lbaasv2_driver.icontrol_hostname,
            CONF.f5_lbaasv2_driver.icontrol_username,
            CONF.f5_lbaasv2_driver.icontrol_password)

        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )


class F5BaseAdminTestCase(base.BaseTestCase):
    """This class picks admin credentials and run the tempest tests."""

    @classmethod
    def resource_setup(cls):
        """Initialize the client objects."""
        super(F5BaseAdminTestCase, cls).resource_setup()
        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )
