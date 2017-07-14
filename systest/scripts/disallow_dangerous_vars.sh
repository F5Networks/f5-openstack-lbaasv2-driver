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
#
# The jenkins worker has access to the lab NFS.
# It's possible that filesystem operations could have
# unintended consequences if "PATH" variables are
# incorrect.  This script restricts the "dangerous" path variables
# to predefined values.
# A developer must amend this list to insert new top-level path
# variables.
if [ "${TLC_DIR}" != "/home/jenkins/tlc" ];then
    echo TLC_DIR "${TLC_DIR}" not allowed!
    exit 31
fi
if [ "${TOOLSBASE_DIR}" != "/toolsbase" ];then
    echo TOOLSBASE_DIR "${TOOLSBASE_DIR}" not allowed!
    exit 31
fi
if [ "${DEVTEST_DIR}" != "/home/jenkins/dev-test" ];then
    echo DEVTEST_DIR "${DEVTEST_DIR}" not allowed!
    exit 31
fi
if [ "${TEMPEST_DIR}" != "/home/jenkins/tempest" ];then
    echo TEMPEST_DIR "${TEMPEST_DIR}" not allowed!
    exit 31
fi
if [ "${NEUTRON_LBAAS_DIR}" != "/home/jenkins/neutron-lbaas" ];then
    echo NEUTRON_LBAAS_DIR "${NEUTRON_LBAAS_DIR}" not allowed!
    exit 31
fi
if [ "${VENVDIR}" != "/home/jenkins/virtualenvs" ];then
    echo VENVDIR "${VENVDIR}" not allowed!
    exit 31
fi
