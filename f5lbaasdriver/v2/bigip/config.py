# coding=utf-8
u"""F5 Networks® LBaaSv2 Driver Implementation."""
# Copyright 2016 F5 Networks Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import json
from oslo_config import cfg
from oslo_log import log as logging

LOG = logging.getLogger(__name__)

OPTS = [
    cfg.IntOpt(
            'f5_driver_perf_mode',
            default=0,
            help=('switch driver performance mode from 0 to 3')
        ),
    cfg.BoolOpt(
            'to_speedup_populate_logic',
            default=False,
            help=("If True, uses new fast populate logic,"
                  "If set to False, then revert to old behavior "
                  "just in case.")
        ),
    cfg.StrOpt(
            'loadbalancer_agent_scheduler',
            default=(
                'f5lbaasdriver.v2.bigip.agent_scheduler.AgentSchedulerNG'
            ),
            help=('Driver to use for scheduling '
                  'pool to a default loadbalancer agent')
        ),
    cfg.ListOpt(
            'agent_filters',
            default=[
                        'AvailabilityZoneFilter',
                        'EnvironmentFilter',
                        'RandomFilter'
                    ],
            help=('Filters of Agent scheduler')
        ),
    cfg.StrOpt(
            'loadbalancer_device_scheduler',
            default=(
                'f5lbaasdriver.v2.bigip.device_scheduler.DeviceSchedulerNG'
            ),
            help=('Driver to use for scheduling '
                  'a loadbalancer to a BIG-IP device')
        ),
    cfg.ListOpt(
            'device_filters',
            default=[
                        'AvailabilityZoneFilter',
                        'OfflineDeviceFilter',
                        'FlavorFilter',
                        'CapacityFilter',
                        'RandomFilter'
                    ],
            help=('Filters of device scheduler')
        ),
    cfg.StrOpt(
            'f5_loadbalancer_service_builder_v2',
            default=(
                'f5lbaasdriver.v2.bigip.service_builder.LBaaSv2ServiceBuilder'
            ),
            help=('Default class to use for building a service object.')
        ),
    cfg.StrOpt(
            'bwc_profile',
            default=None,
            help='bwc_profile name which is configured in bigip side'
        ),
    cfg.StrOpt(
            'special_lb_name_prefix',
            default="SPECIAL_",
            help=('if lb name starts with this prefix and ends with first '
                  '8 chars of an inactive device uuid, try scheduling to '
                  'this device before real onboarding.')
        ),
    cfg.StrOpt(
            'scheduler_constants',
            default="/etc/neutron/services/f5/scheduler.json",
            help=('Scheduler constant file')
        )
]

cfg.CONF.register_opts(OPTS)

file_path = cfg.CONF.scheduler_constants
cust_cfg = None
try:
    with open(file_path, 'r') as config_file:
        cust_cfg = json.load(config_file)
except Exception as err:
    msg = "cannot load customerized config " \
        "file %s\n error: %s\n" % (
            cfg.CONF.scheduler_constants,
            err
        )
    # use warning, not throw exception. exception is thrown by users
    LOG.warning(msg)


def merge_cfg_dict(cfg, *cust_cfgs):
    try:
        for nc in cust_cfgs:
            cfg.update(nc)
    except Exception as exc:
        msg = "update config dict with %s\n error: %s\n" % (
            nc, exc)
        raise Exception(msg)
