#! /usr/bin/env bash

set -ex

# Update the system and install required debian packages
ln -s /bin/bash /usr/local/bin/bash
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
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Pip install TLC requirements
pip install --upgrade pip
pip install argcomplete blessings configargparse prettytable

# Clone the toolsbase directory and setup the file system structure
git clone https://bldr-git.int.lineratesystems.com/talley/tlc-toolsbase.git /toolsbase
mkdir /toolsbase/independent/share
mkdir /toolsbase/Ubuntu-10-x86_64/share
rm -rf /toolsbase/independent/bin/*.pyc
rm -rf /toolsbase/independent/bin/tlc_pb2.py
ln -s /toolsbase/Ubuntu-10-x86_64 /tools

# Install TLC packages and binaries
git clone \
  -b openstack.bbot-tlc \
  --single-branch \
  https://bldr-git.int.lineratesystems.com/s.wormke/tlc.git \
  /home/buildbot/tlc

# Apply patches found for local changes to TLC on build server
# Should these patches be applied in the repo for real?
cp patches/* /tmp/
patch /home/buildbot/tlc/tlc/install.sh /tmp/tlc_install.sh.patch
patch /toolsbase/independent/create_softlinks /tmp/create_softlinks.patch
patch /home/buildbot/tlc/vmware/install.sh /tmp/vmware_install.patch

# Install all of the TLC sub-components
cd /home/buildbot/tlc
cd tlc && ./install.sh
cd ../tl3 && ./install.sh
cd ../vmware && ./install.sh
cd ../tlc_client && python setup.py install
cd ../bash_completion_feature && ./install_bash_completions.sh
