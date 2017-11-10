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

    _lbs_to_delete = []
    try_cnt_max = 3
    sleep_seconds = 5

    @classmethod
    def assert_with_retry(cls, check, *args, **kwargs):
        """A assertion try/except handler for multiple re-tries

        This method will call the provided check method passing it the args
        provided.  It will then except on AssertionError alone and retry up to
        a maximum number of times with a time delay in between attempts.
        """
        try_cnt = 0
        try_cnt_max = cls.try_cnt_max
        sleep_seconds = cls.sleep_seconds
        while True:
            try:
                check(*args, **kwargs)
            except AssertionError:
                if try_cnt < try_cnt_max:
                    try_cnt += 1
                    sleep(sleep_seconds)
                    continue
                raise
            except TypeError as Err:
                raise TypeError("{}: ({})".format(Err, args))
            else:
                break

    @classmethod
    def assertion_check(cls, *args, **kwargs):
        """Looping assert check against the method and args provided

        This method will take one method and a group of args and test that the
        method, when passed provided args, returns as True.  As part of this
        check, a loop with an iterative time delay is provided with a max retry
        count.
        """
        def positive(method, *args, **kwargs):
            """Asserts that the method call evaluates as True"""
            assert method(*args, **kwargs)
        cls.assert_with_retry(positive, *args, **kwargs)

    @classmethod
    def neg_assertion_check(cls, *args, **kwargs):
        """Looping assert not check against the method and args provided

        This method will take one method and a group of args and test that the
        method, when passed provided args, returns as False.  As part of this
        check, a loop with an iterative time delay is provided with a max retry
        count.
        """
        def negative(method, *args, **kwargs):
            """Asserts that the method call evaluates as False"""
            assert not method(*args, **kwargs)
        cls.assert_with_retry(negative, *args, **kwargs)

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


class F5BaseAdminTestCase(base.BaseTestCase):
    """This class picks admin credentials and run the tempest tests."""

    @classmethod
    def resource_setup(cls):
        """Initialize the client objects."""
        super(F5BaseAdminTestCase, cls).resource_setup()
        cls.plugin_rpc = (
            plugin_rpc_client.F5PluginRPCClient()
        )
