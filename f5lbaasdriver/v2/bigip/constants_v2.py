# coding=utf-8
u"""Constants for F5® LBaaSv2 Driver."""
# coding=utf-8
# Copyright 2016 F5 Networks Inc.
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

# F5EnvironmentDriver provider name
F5ENVDRIVER_PROVIDER_NAME = 'f5env'

# RPC channel names
TOPIC_PROCESS_ON_HOST_V2 = 'f5-lbaasv2-process-on-controller'
TOPIC_LOADBALANCER_AGENT_V2 = 'f5-lbaasv2-process-on-agent'

BASE_RPC_API_VERSION = '1.0'
RPC_API_NAMESPACE = None

# service builder constants
VIF_TYPE = 'f5'
NET_CACHE_SECONDS = 1800

# SUPPORTED PROVIDERNET TUNNEL NETWORK TYPES
TUNNEL_TYPES = ['vxlan', 'gre']

FLAVOR_CONN_MAP = {
    "1": {
        'connection_limit': 5000,
        'rate_limit': 3000
    },
    "2": {
        'connection_limit': 50000,
        'rate_limit': 5000
    },
    "3": {
        'connection_limit': 100000,
        'rate_limit': 10000
    },
    "4": {
        'connection_limit': 200000,
        'rate_limit': 20000
    },
    "5": {
        'connection_limit': 500000,
        'rate_limit': 50000
    },
    "6": {
        'connection_limit': 1000000,
        'rate_limit': 100000
    },
    "7": {
        'connection_limit': 8000000,
        'rate_limit': 100000
    },
    "8": {
        'connection_limit': 4000000,
        'rate_limit': 500000
    },
    "11": {
        'connection_limit': 3000,
        'rate_limit': 1000
    },
    "12": {
        'connection_limit': 5000,
        'rate_limit': 3000
    },
    "13": {
        'connection_limit': 50000,
        'rate_limit': 5000
    }
}

CAPACITY_MAP = {
    "license": {
        "VE-1G": {
            "lod": 10,
            "rod": 25000,
            "cod": 1000000,
            "por": 1.00,
            "poc": 1.00
        },
        "VE-10G": {
            "lod": 32,
            "rod": 100000,
            "cod": 5000000,
            "por": 1.00,
            "poc": 1.00
        },
        "default": {
            "lod": -1,
            "rod": -1,
            "cod": -1,
            "por": 1.00,
            "poc": 1.00
        }
    }
}
