#! /usr/bin/env bash

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

# Copy the testlab key and make sure it has right owner/permissions
cp -f /home/jenkins/.ssh/id_rsa /home/jenkins/.ssh/id_rsa_testlab
chmod 600 /home/jenkins/.ssh/id_rsa_testlab
chown jenkins:jenkins /home/jenkins/.ssh/id_rsa_testlab

# Update the system and install required debian packages
ln -fs /bin/bash /usr/local/bin/bash
apt-get update
apt-get -y install \
    vim \
    git \
    python-pip \
    python-pexpect \
    python-paramiko \
    nfs-common \
    ipmitool \
    python-protobuf \
    protobuf-compiler \
    gosu

# Pip install TLC requirements
pip install --upgrade pip
pip install argcomplete blessings configargparse prettytable

# Clone the toolsbase directory and setup the file system structure
rm -rf ${TOOLSBASE_DIR}
git clone ${TOOLSBASE_REPO} ${TOOLSBASE_DIR}
mkdir ${TOOLSBASE_DIR}/independent/share
mkdir ${TOOLSBASE_DIR}/Ubuntu-10-x86_64/share
rm -rf ${TOOLSBASE_DIR}/independent/bin/*.pyc
rm -rf ${TOOLSBASE_DIR}/independent/bin/tlc_pb2.py
rm -rf ${TOOLSBASE_DIR}/independent/lib/*.pyc
rm -rf ${TOOLSBASE_DIR}/Ubuntu-10-x86_64/bin/*.pyc
rm -rf ${TOOLSBASE_DIR}/Ubuntu-10-x86_64/lib/*.pyc
ln -sf ${TOOLSBASE_DIR}/Ubuntu-10-x86_64 /tools

# Remove all of the stale libs that are for some reason is toolsbase/bin
libs="file_access.py
file_reservation.py
interactive.py
ipaddr.py
serialcons.py
switch_lacp_config.py
switch_vlan_config.py
switches.py
testlab_adapter.py
tlc_util.py
tlc_autocomplete.py
utils.py
"
for lib in $libs; do
  rm -f ${TOOLSBASE_DIR}/independent/bin/$lib
  rm -f ${TOOLSBASE_DIR}/Ubuntu-10-x86_64/bin/$lib
done

# Install TLC packages and binaries
rm -rf ${TLC_DIR}
git clone \
  -b ${TLC_BRANCH} \
  --single-branch \
  ${TLC_REPO} \
  ${TLC_DIR}

# Apply patches found for local changes to TLC on build server
# Should these patches be applied in the repo for real?
cp -f patches/* /tmp/
patch ${TLC_DIR}/tlc/install.sh /tmp/tlc_install.sh.patch
patch ${TOOLSBASE_DIR}/independent/create_softlinks /tmp/create_softlinks.patch
patch ${TLC_DIR}/vmware/install.sh /tmp/vmware_install.patch

# Install all of the TLC sub-components
cd ${TLC_DIR}
cd tlc && ./install.sh
cd ../tl3 && ./install.sh
cd ../vmware && ./install.sh
cd ../tlc_client && python setup.py install
cd ../bash_completion_feature && ./install_bash_completions.sh
