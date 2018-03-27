# Copyright (c) 2017,2018, F5 Networks, Inc.
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

import mock

from neutron.callbacks import events
from neutron.callbacks import registry
from neutron.callbacks import resources

from f5lbaasdriver.v2.bigip.driver_v2 import F5DriverV2


@mock.patch('f5lbaasdriver.v2.bigip.agent_rpc.LBaaSv2AgentRPC')
def test_neutron_registry_callback(mock_agent_rpc):
    """Test callback functions used for registering for RPC events in driver.

    Creates two drivers to simulate a differentiated environment
    deployment, then tests that each driver registers different functions
    to receive notification from Neutron after subscribing for events, and
    that the functions are called by the Neutron callback manager.

    Also, see related unit test,
    f5lbaasdriver/v2/bigip/test/test_bind_registry_callback.py

    :param mock_agent_rpc: Not used. Mock needed to create F5DriverV2.
    """
    plugin = mock.MagicMock()

    # start with empty Neutron RPC callback registry
    registry.clear()

    # create default driver
    default_driver = F5DriverV2(plugin)
    default_driver.plugin_rpc = mock.MagicMock()

    # create a differentiated environment driver
    dmz_driver = F5DriverV2(plugin, 'dmz')
    dmz_driver.plugin_rpc = mock.MagicMock()

    default_callback_func = default_driver._bindRegistryCallback()
    dmz_callback_func = dmz_driver._bindRegistryCallback()

    # two different callback functions created
    assert default_callback_func != dmz_callback_func

    # registry holds two callbacks
    callback_mgr = registry._get_callback_manager()
    assert len(
        callback_mgr._callbacks[resources.PROCESS][events.AFTER_CREATE]) == 2

    # both callbacks are in registry
    callbacks = callback_mgr._callbacks[resources.PROCESS][events.AFTER_CREATE]
    callback_iter = iter(callbacks)

    callback_name = next(callback_iter).split('.')[-1]
    assert callback_name == default_callback_func.__name__

    callback_name = next(callback_iter).split('.')[-1]
    assert callback_name == dmz_callback_func.__name__

    # callbacks can be called back
    with mock.patch('f5lbaasdriver.v2.bigip.driver_v2.LOG') as mock_log:
        # invoke callbacks from callback manager
        callback_mgr.notify(
            resources.PROCESS, events.AFTER_CREATE, mock.MagicMock())

        # create_rpc_listener called
        assert default_driver.plugin_rpc.create_rpc_listener.called
        assert dmz_driver.plugin_rpc.create_rpc_listener.called

        # debug messages logged
        log_iter = iter(mock_log.debug.call_args_list)
        args, kwargs = log_iter.next()
        assert str(args[0]).startswith("F5DriverV2 with env None received")

        args, kwargs = log_iter.next()
        assert str(args[0]).startswith("F5DriverV2 with env dmz received")
