#!/usr/bin/env bash

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

set -ex

# Copy over our default tempest files
cp -f conf/tempest.conf ${TEMPEST_CONFIG_DIR}/tempest.conf.orig
cp -f conf/accounts.yaml ${TEMPEST_CONFIG_DIR}/accounts.yaml

# Find the values for tempest.conf and substitute them
OS_CONTROLLER_IP=`cat ../session_symbols \
    | grep openstack_controller1ip_data_direct \
    | awk '{print $3}'`

ssh_cmd="ssh -o StrictHostKeyChecking=no testlab@${OS_CONTROLLER_IP}"

OS_PUBLIC_ROUTER_ID=`${ssh_cmd} "source ~/keystonerc_testlab && neutron router-list -F id -f value"`
OS_PUBLIC_NETWORK_ID=`${ssh_cmd} "source ~/keystonerc_testlab && neutron net-list -F name -F id -f value" \
    | grep external_network \
    | awk '{print $1}'`
OS_CIRROS_IMAGE_ID=`${ssh_cmd} "source ~/keystonerc_testlab && glance image-list" \
    | grep ${TEST_CIRROS_IMAGE} \
    | awk '{print $2}'`

cat ${TEMPEST_CONFIG_DIR}/tempest.conf.orig \
  | sed "s/{{ OS_CONTROLLER_IP }}/${OS_CONTROLLER_IP}/" \
  | sed "s/{{ OS_PUBLIC_ROUTER_ID }}/${OS_PUBLIC_ROUTER_ID}/" \
  | sed "s/{{ OS_PUBLIC_NETWORK_ID }}/${OS_PUBLIC_NETWORK_ID}/" \
  | sed "s/{{ OS_CIRROS_IMAGE_ID }}/${OS_CIRROS_IMAGE_ID}/" \
  > ${TEMPEST_CONFIG_DIR}/tempest.conf
