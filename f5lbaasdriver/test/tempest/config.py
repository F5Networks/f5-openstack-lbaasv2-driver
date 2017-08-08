# Copyright 2015
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

from oslo_config import cfg

f5_lbaasv2_driver_group = cfg.OptGroup(
    name='f5_lbaasv2_driver',
    title="Configuration Options to run the F5 LBaaSv2 Driver tests")

f5_lbaasv2_driver_opts = [
    cfg.StrOpt(
        'icontrol_hostname',
        default="10.1.0.150",
        help='The hostname (name or IP address) to use for iControl access'
    ),
    cfg.StrOpt(
        'icontrol_username', default='admin',
        help='The username to use for iControl access'
    ),
    cfg.StrOpt(
        'icontrol_password', default='admin', secret=True,
        help='The password to use for iControl access'
    ),
    cfg.StrOpt(
        'transport_url',
        default="rabbit://guest:guest@10.190.4.156:5672/",
        help='The transport_url to use for messaging, see neutron.conf'
    ),
]
