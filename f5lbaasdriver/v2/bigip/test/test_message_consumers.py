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

import os
import pytest

from mock import Mock
from mock import patch

import neutron.common.rpc
import neutron.db
import oslo_config
import oslo_log
import oslo_messaging
import oslo_service

import f5lbaasdriver.v2.bigip.message_consumers
import f5lbaasdriver.v2.bigip.plugin_rpc

from f5lbaasdriver.v2.bigip.message_consumers import F5RPCConsumer


class Test_F5RPCConsumer(object):
    """Test class for F5RPCConsumer

This is a test class that should return all code-space globals back to normal.
This testing class is only meant for white-box-based, unit tests.
    """
    # om_ := oslo_messaging
    # oc_ := oslo_config
    # os_ := oslo_service
    getpid = os.getpid
    om_get_transport = oslo_messaging.get_transport
    om_Target = oslo_messaging.Target
    om_get_rpc_server = oslo_messaging.get_rpc_server
    os_service_Service = oslo_service.service.Service
    LBaaSv2PluginCallbacksRPC = \
        f5lbaasdriver.v2.bigip.plugin_rpc.LBaaSv2PluginCallbacksRPC
    oc_cfg = oslo_config.cfg
    getLogger = oslo_log.log.getLogger
    agents_db = neutron.db.agents_db
    preserve_log = f5lbaasdriver.v2.bigip.message_consumers.LOG

    def teardown(self):
        """A teardown object assigned to request.addfinalizer

This method performs a set of tasks to reset the global values back to what
they were originally within codespace memory.
        """
        os.getpid = self.getpid
        oslo_messaging.get_transport = self.om_get_transport
        oslo_messaging.Target = self.om_Target
        oslo_messaging.get_rpc_server = self.om_get_rpc_server
        oslo_service.service.Service = self.os_service_Service
        f5lbaasdriver.v2.bigip.plugin_rpc.LBaaSv2PluginCallbacksRPC = \
            self.LBaaSv2PluginCallbacksRPC
        oslo_config.cfg = self.oc_cfg
        oslo_log.log.getLogger = self.getLogger
        neutron.db.agents_db.AgentExtRpcCallback = self.agents_db
        f5lbaasdriver.v2.bigip.message_consumers.LOG = self.preserve_log

    @pytest.fixture
    def class_level_fixture(self, request):
        """A shared pytest fixture that is used throughout the class

This method simply sets global values to mock.Mock objects where it makes sense
in order to test the orchestration of the target object's code.
        """
        request.addfinalizer(self.teardown)
        os.getpid = Mock(return_value=2)
        oslo_config.cfg = Mock()
        oslo_config.cfg.ConfigOpts = Mock()
        builder = Mock()
        oslo_config.cfg.f5_loadbalancer_service_builder_v2 = builder
        oslo_config.cfg.ConfigOpts.f5_loadbalancer_service_builder_v2 = \
            Mock(return_value=builder)
        oslo_messaging.get_transport = Mock()
        oslo_messaging.Target = Mock()
        oslo_messaging.get_rpc_server = Mock()
        oslo_service.service.Service = Mock()
        self.callback = Mock()
        f5lbaasdriver.v2.bigip.plugin_rpc.LBaaSv2PluginCallbacksRPC = \
            Mock(return_value=self.callback)
        self.db_handle = Mock()
        neutron.db.agents_db.AgentExtRpcCallback = \
            Mock(return_value=self.db_handle)
        self.LOG = Mock()
        self.LOG.info = Mock()
        f5lbaasdriver.v2.bigip.message_consumers.LOG = self.LOG

    def test_init__(self, class_level_fixture):
        """Unit/White-Box Tests F5RPCConsumer's __init__ method

This tests only a positive case as there is no negative checking at this level.

This test is essentially to test the inner workings.  Other tests within this
test object will utilize this method to gain a copy of the target object.  This
is expected.
        """
        driver = Mock()
        driver.plugin_rpc = self.callback
        driver.env = 'foo'
        dummy = F5RPCConsumer(driver)
        assert driver == dummy.driver, 'driver set test'
        assert dummy.endpoints == [self.callback, self.db_handle], "Endpoints"
        assert self.LOG.info.called, "We informed everyone"
        self.LOG.info.reset_mock()

    def get_dummy(self):
        driver = Mock()
        driver.env = 'foo'
        agents_db = Mock()
        with patch('neutron.db.agents_db.AgentExtRpcCallback',
                   agents_db, create=True):
            dummy = F5RPCConsumer(driver)
        return dummy

    def test__create_connection(self):
        dummy = self.get_dummy()
        mock_conn = Mock()
        create_connection = Mock(return_value=mock_conn)
        mock_conn.create_consumer = Mock()
        mock_conn.consume_in_threads = Mock()
        with patch('neutron.common.rpc.create_connection', create_connection,
                   create=True):
            dummy._F5RPCConsumer__create_connection()
        assert create_connection.called, "Created connection called"
        assert mock_conn.create_consumer, "Created connection called"
        assert mock_conn.consume_in_threads, "Threaded off"
        mock_conn.create_consumer.assert_called_once_with(dummy.topic,
                                                          dummy.endpoints,
                                                          fanout=False)
        assert dummy.conn == mock_conn, "Connection object set as attr"

    def test_start(self, class_level_fixture):
        """Unit/White-Box Tests F5RPCConsumer's start method

This tests only a positive case as there is no negative checking at this level.
        """
        dummy = self.get_dummy()
        start_mock = Mock()
        mod = 'oslo_service.service.Service.start'
        connect_mod = \
            str('f5lbaasdriver.v2.bigip.message_consumers.F5RPCConsumer.'
                '_F5RPCConsumer__create_connection')
        create_connection_mock = Mock()
        with patch(mod, start_mock, create=True):
            with patch(connect_mod, create_connection_mock, create=True):
                dummy.start()
        assert create_connection_mock.called, "created connection"
        self.LOG.info.reset_mock()

    def test_stop(self, class_level_fixture):
        """Unit/White-Box Tests F5RPCConsumer's stop method

This tests only a positive case as there is no negative checking at this level.
        """
        dummy = self.get_dummy()
        dummy.conn = Mock()
        dummy.conn.close = Mock()
        mod = 'oslo_service.service.Service.stop'
        stop_mock = Mock()
        with patch(mod, stop_mock, create=True):
            dummy.stop(graceful=True)
        assert dummy.conn.close.called, "Closed connection"
        assert self.LOG.info.call_count == 1, \
            "We informed stop and graceful wait"
        self.LOG.info.reset_mock()

    def test_reset(self, class_level_fixture):
        """Unit/White-Box Tests F5RPCConsumer's reset method

This tests only a positive case as there is no negative checking at this level.
        """
        dummy = self.get_dummy()
        dummy.conn = Mock()
        dummy.conn.stop = Mock()
        dummy._F5RPCConsumer__create_connection = Mock()
        dummy.reset()
        assert dummy.conn.stop.called, "Called to stop conn"
        assert dummy._F5RPCConsumer__create_connection.called, \
            "Created new conn"


# Modeled after the following code:
# class OctaviaConsumer(service.Service):
#    def __init__(self, driver, **kwargs):
#        super(OctaviaConsumer, self).__init__(**kwargs)
#        topic = cfg.CONF.oslo_messaging.event_stream_topic
#        server = cfg.CONF.host
#        self.driver = driver
#        self.transport = messaging.get_transport(cfg.CONF)
#        self.target = messaging.Target(topic=topic, server=server,
#                                       exchange="common", fanout=False)
#        self.endpoints = [ConsumerEndPoint(self.driver)]
#        self.server = None
#
#    def start(self):
#        super(OctaviaConsumer, self).start()
#        LOG.info(_LI("Starting octavia consumer..."))
#        self.server = messaging.get_rpc_server(self.transport, self.target,
#                                               self.endpoints,
#                                               executor='eventlet')
#        self.server.start()
#
#    def stop(self, graceful=False):
#        if self.server:
#            LOG.info(_LI('Stopping consumer...'))
#            self.server.stop()
#            if graceful:
#                LOG.info(
#                    _LI('Consumer successfully stopped.  Waiting for final '
#                        'messages to be processed...'))
#                self.server.wait()
#        super(OctaviaConsumer, self).stop(graceful=graceful)
#
#    def reset(self):
#        if self.server:
#            self.server.reset()
#        super(OctaviaConsumer, self).reset()
# __END__
