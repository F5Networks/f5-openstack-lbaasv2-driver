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

from f5lbaasdriver.v2.bigip.driver_v2 import F5DriverV2


@mock.patch('f5lbaasdriver.v2.bigip.agent_rpc.LBaaSv2AgentRPC')
def test_bind_registry_callback(mock_agent_rpc):
    """Test creating callback functions for registering RPC events in driver.

    Simulates multiple drivers in differentiated environments, testing
    that two drivers create two distinct callback functions to register
    with Neutron callback manager.

    Also, see related functional test,
    f5_openstack_lbaasv2_driver/test/functional/test_registry_callback.py

    :param mock_agent_rpc: Not used. Needed satisfy creating F5DriverV2.
    """
    plugin = mock.MagicMock()

    # create default driver
    default_driver = F5DriverV2(plugin)

    # create a differentiated environment driver
    dmz_driver = F5DriverV2(plugin, 'dmz')

    # get callback functions for each
    default_callback_func = default_driver._bindRegistryCallback()
    dmz_callback_func = dmz_driver._bindRegistryCallback()

    # two different callback functions created
    assert default_callback_func != dmz_callback_func

    # callback functions have diffent names
    assert default_callback_func.__name__ != dmz_callback_func.__name__

    # expected function names
    assert default_callback_func.__name__ == 'post_fork_callback_None'
    assert dmz_callback_func.__name__ == 'post_fork_callback_dmz'
