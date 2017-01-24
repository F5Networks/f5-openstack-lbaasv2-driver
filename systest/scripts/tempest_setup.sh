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

# Create a virtualenv
virtualenv ${TEMPEST_VENV_DIR}
source ${TEMPEST_VENV_ACTIVATE}

# Install tox
pip install tox

# Install tempest & its config files
git clone ${TEMPEST_REPO} ${TEMPEST_DIR}
pip install ${TEMPEST_DIR}

# We need to clone the OpenStack devtest repo for our TLC files
git clone ${DEVTEST_REPO} ${DEVTEST_DIR}

# Add tempest configuration options for running tempest tests in f5lbaasv2driver
BIGIP_IP=`ssh -i ~/.ssh/id_rsa_testlab testlab@${OS_CONTROLLER_IP} cat ve_mgmt_ip`
echo "[f5_lbaasv2_driver]" >> ${TEMPEST_CONFIG_DIR}/tempest.conf
echo "icontrol_hostname = ${BIGIP_IP}" >> ${TEMPEST_CONFIG_DIR}/tempest.conf
echo "transport_url = rabbit://guest:guest@${OS_CONTROLLER_IP}:5672/" >> ${TEMPEST_CONFIG_DIR}/tempest.conf

# Clone neutron-lbaas so we have the tests
git clone\
  -b ${NEUTRON_LBAAS_BRANCH} \
  --single-branch \
  ${NEUTRON_LBAAS_REPO} \
  ${NEUTRON_LBAAS_DIR}

# Copy our tox.ini file to neutron so we can run py.test instead of testr
cp conf/neutron-lbaas.tox.ini ${NEUTRON_LBAAS_DIR}/f5.tox.ini
