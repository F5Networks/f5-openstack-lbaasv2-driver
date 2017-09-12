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

set -x

set +e

runTLCSetup() {
  # Excecute the TLC setup command given.
  eval $1
  tlc_setup_rc=$?
}

doesTLCSessionExist() {
  # For the grep below, an rc of 1 means that the session does not exist.
  # With an rc of 0, the session does exist because the grep found it.
  tlc_exist_rc=1
  if [[ -n "$1" ]]; then
    /tools/bin/tlc sessions | grep $1
    tlc_exist_rc=$?
  fi
}

cleanupFailedTLCSession() {
  # Cleanup the failed TLC session, if necessary.
  typeset tlc_session_name=$1
  typeset failed_session_iteration=$2
  if [[ -n "${tlc_session_name}" ]]; then
    # When you perform a TLC setup, first the session directory is created in
    # /testlab/sessions directory. Then, eventually a TLC session is registered
    # with TLC based on the reservations that are done for those hosts. We need
    # to check both events to ensure we teardown properly, if a failure occurs.
    backup_loc="/testlab/sessions/failed_setup_session_backup"
    doesTLCSessionExist "${tlc_session_name}"

    # Check if tlc reservation exists
    if [[ $tlc_exist_rc == 0 ]]; then
      echo "Cleaning up failed TLC session because it does exist."
      /tools/bin/tlc --session ${tlc_session_name} cleanup
    fi

    # Check if tlc session directory exists on server
    if [[ -d "/testlab/sessions/${tlc_session_name}" ]]; then
      echo "Moving /testlab/sessions/${TEST_SESSION} directory to backup directory."
      sudo mkdir -p ${backup_loc}/${tlc_session_name}_${failed_session_iteration}
      sudo mv /testlab/sessions/${tlc_session_name} ${backup_loc}/${tlc_session_name}_${failed_session_iteration}
    else
      echo "Session directory does not exist."
    fi
  else
    echo "TEST_SESSION variable in this script is empty. It should not be."
    exit 1
  fi
}

tlc_setup_cmd="/tools/bin/tlc --session ${TEST_SESSION} --config ${TLC_FILE} --debug setup"
runTLCSetup "$tlc_setup_cmd"

# Run the TLC setup command, and retry up to three times if anything goes wrong.
for i in `seq 1 3`; do
  if [[ $tlc_setup_rc != 0 ]]; then
    echo "###################################################"
    echo "TLC setup command failed with rc=${tlc_setup_rc}. Retry number ${i}"
    echo "###################################################"
    cleanupFailedTLCSession "$TEST_SESSION" "$i"
    runTLCSetup "$tlc_setup_cmd"
  else
    break
  fi
done

if [[ $tlc_setup_rc != 0 ]]; then
  echo "###################################################"
  echo "All retries for TLC setup failed. Tearing down session and exiting."
  echo "###################################################"
  cleanupFailedTLCSession "$TEST_SESSION" "$i"
  exit 1
fi

set -e
## Run the setup & commands for the session
/tools/bin/tlc --session ${TEST_SESSION} --debug cmd ready
/tools/bin/tlc --session ${TEST_SESSION} --debug cmd test_env
/tools/bin/tlc --session ${TEST_SESSION} --debug cmd barbican

# Setup container mailbox for ansible playbooks
./prepare_controller.sh

# Optionally install heat plugins
if [[ ${HA_TYPE} == "pair" ]]; then
  ./ansible_install_heat_plugins.sh
  /tools/bin/tlc --session ${TEST_SESSION} --debug cmd configure_cluster
fi

# Install lbaas components
./ansible_install_lbaasv2.sh
/tools/bin/tlc --session ${TEST_SESSION} --debug cmd configure_lbaasv2
