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

FLAVOR_SNAT_MAP = {
    4: {
        1: 2, 2: 2, 3: 2, 4: 4, 5: 8, 6: 16, 7: 122, 8: 58,
        11: 1, 12: 1, 13: 1
    },
    6: {
        1: 1, 2: 1, 3: 1, 4: 3, 5: 7, 6: 15, 7: 121, 8: 57,
        11: 1, 12: 1, 13: 1
    }
}

FLAVOR_CONN_MAP = {
    "1": {
        'bandwidth': 200,
        'connection_limit': 5000,
        'rate_limit': 3000
    },
    "2": {
        'bandwidth': 500,
        'connection_limit': 50000,
        'rate_limit': 5000
    },
    "3": {
        'bandwidth': 1000,
        'connection_limit': 100000,
        'rate_limit': 10000
    },
    "4": {
        'bandwidth': 2000,
        'connection_limit': 200000,
        'rate_limit': 20000
    },
    "5": {
        'bandwidth': 5000,
        'connection_limit': 500000,
        'rate_limit': 50000
    },
    "6": {
        'bandwidth': 10000,
        'connection_limit': 1000000,
        'rate_limit': 100000
    },
    "7": {
        'bandwidth': 10000,
        'connection_limit': 8000000,
        'rate_limit': 100000
    },
    "8": {
        'bandwidth': 10000,
        'connection_limit': 4000000,
        'rate_limit': 500000
    },
    "11": {
        'bandwidth': 100,
        'connection_limit': 3000,
        'rate_limit': 1000
    },
    "12": {
        'bandwidth': 200,
        'connection_limit': 5000,
        'rate_limit': 3000
    },
    "13": {
        'bandwidth': 500,
        'connection_limit': 50000,
        'rate_limit': 5000
    }
}

CAPACITY_MAP = {
    "license": {
        "VE-200M": {
            "osr": 5,
            "bandwidth": 200,
            "lod": 2,
            "rod": 5000,
            "cod": 200000,
            "por": 1.00,
            "poc": 1.00
        },
        "VE-1G": {
            "osr": 5,
            "bandwidth": 1000,
            "lod": 10,
            "rod": 25000,
            "cod": 1000000,
            "por": 1.00,
            "poc": 1.00
        },
        "VE-10G": {
            "osr": 5,
            "bandwidth": 10000,
            "lod": 32,
            "rod": 100000,
            "cod": 5000000,
            "por": 1.00,
            "poc": 1.00
        },
        "default": {
            "osr": 1,
            "bandwidth": -1,
            "lod": -1,
            "rod": -1,
            "cod": -1,
            "por": 1.00,
            "poc": 1.00
        }
    }
}
