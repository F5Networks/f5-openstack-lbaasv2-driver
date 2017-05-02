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

from neutron.common import rpc as neutron_rpc
from neutron.db import agents_db

from oslo_log import log as logging
from oslo_service import service

from f5lbaasdriver.v2.bigip import constants_v2 as constants

LOG = logging.getLogger(__name__)


class F5RPCConsumer(service.Service):
    """Creates a RPC Consumer that will Return and Use the Driver For Calls

This is a standard, RPC service based upon the provided driver.  This should be
executed through its creation and use of standard oslo_service.Service actions.
    """
    def __init__(self, driver, **kargs):
        """Initializes the F5RPCConsumer object with attribute primatives"""
        super(F5RPCConsumer, self).__init__(**kargs)
        self.topic = constants.TOPIC_PROCESS_ON_HOST_V2
        self.driver = driver
        if self.driver.env:
            print(driver.env)
            self.topic = self.topic + "_" + self.driver.env

        self.endpoints = [driver.plugin_rpc,
                          agents_db.AgentExtRpcCallback(driver.plugin.db)]
        LOG.info("Created F5RPCConsumer (Driver: {}, PID: {})".format(
            driver, os.getpid()))
        self.conn = None

    def __create_connection(self):
        """__create_connection - Creates a Connection and Starts it in a Thread

This object method will attempt to create a neutron.common.rpc.Connection
object with the same topic as the f5-openstack-agent's transmitions.
        """
        msg = str("Started threaded F5RPCConsumer Connection "
                  "(Driver: {}, PID: {}, topic: {})").format(self.driver,
                                                             os.getpid(),
                                                             self.topic,
                                                             )
        self.conn = neutron_rpc.create_connection(new=True)
        self.conn.create_consumer(self.topic, self.endpoints, fanout=False)
        LOG.info(msg)
        self.conn.consume_in_threads()
        LOG.info(msg)

    def start(self):
        """Starts the Connection at the Child's Level"""
        super(F5RPCConsumer, self).start()
        self.__create_connection()

    def stop(self, graceful=False):
        """Stops the Connection and the Service from the Parent's Prospective

        """
        if self.conn:
            self.conn.close()
        super(F5RPCConsumer, self).stop(graceful=graceful)

    def reset(self):
        """Resets the Connection and the service."""
        LOG.info("Resetting F5RPCConsumer Connection")
        if self.conn:
            self.conn.stop()
        self.__create_connection()
        super(F5RPCConsumer, self).reset()
