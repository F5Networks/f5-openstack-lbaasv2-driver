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

# - install testenv-all first because it has a bunch of pinned dependencies
sudo pip install git+ssh://git@gitlab.pdbld.f5net.com/bdo/testenv-all.git
sudo pip install git+ssh://git@gitlab.pdbld.f5net.com/tools/pytest-meta.git
sudo pip install git+ssh://git@gitlab.pdbld.f5net.com/tools/pytest-autolog.git
sudo pip install git+ssh://git@gitlab.pdbld.f5net.com/tools/pytest-symbols.git
sudo pip install tox virtualenv virtualenvwrapper

# Create a virtualenv
rm -rf ${TEMPEST_VENV_DIR}
virtualenv ${TEMPEST_VENV_DIR}
source ${TEMPEST_VENV_ACTIVATE}

# We need to clone the OpenStack devtest repo for our TLC files
rm -rf ${DEVTEST_DIR}
git clone -b ${BRANCH} ${DEVTEST_REPO} ${DEVTEST_DIR}

# This should be listed in requirement.test.txt also, but will not succeed
# from that location without sudo
sudo pip install git+https://github.com/F5Networks/f5-openstack-agent.git@${BRANCH}
# Install neutron at stable/mitaka because stable/liberty tests will not work
# because they use an upper contraints file in the installation script that
# neutron-lbaas uses for tox tests.
# The file that causes this to happen is: neutron-lbaas/tools/tox_install.sh
#
# The use of the liberty version of this file restricts the crpytography
# library to a low version which is not compatible with newer versions of
# OpenSSL (1.0.2g+) because of an API change in OpenSSL.
#
# See this issue for more details:
# https://github.com/pyca/cryptography/issues/2750
#
# TODO: Make a decision about not using the neutron-lbaas install script
#       and just installing from requirements files on newest versions
rm -rf ${NEUTRON_LBAAS_DIR}
git clone\
  -b ${NEUTRON_LBAAS_BRANCH} \
  --single-branch \
  ${NEUTRON_LBAAS_REPO} \
  ${NEUTRON_LBAAS_DIR}

# create directories for copying tempest.conf file
mkdir -p ${TEMPEST_CONFIG_DIR}

# Copy our tox.ini file to neutron so we can run py.test instead of testr
cp -f conf/neutron-lbaas.tox.ini ${NEUTRON_LBAAS_DIR}/f5.tox.ini
