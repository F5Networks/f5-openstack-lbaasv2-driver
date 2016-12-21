#!/usr/bin/env bash

# We need to clone the OpenStack devtest repo for our TLC files
git clone git@bldr-git.int.lineratesystems.com:openstack/dev-test.git ${DEVTEST_DIR}

# Run the setup & commands for the session
tlc --session ${TEST_SESSION} --config ${TLC_FILE} --debug setup
tlc --session ${TEST_SESSION} --debug cmd ready
tlc --session ${TEST_SESSION} --debug cmd test_env
tlc --session ${TEST_SESSION} --debug cmd lbaasv2
