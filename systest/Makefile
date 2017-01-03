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

.PHONY: all systest functest \
tlc-install \
tempest-setup \
tempest_tests tempest_tests-setup \
tempest_tests-install tempest_tests-run \
tempest_tests-teardown

# - <nearest reachable tag>-<num commits since>-g<abbreviated commit id>
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
SUBJECTCODE_ID := $(shell git log -n 1 --format=%h)
TIMESTAMP ?= $(shell date +"%Y%m%d-%H%M%S")
export TIMESTAMP   # Only eval TIMESTAMP in the top make.
PROJECT := f5-openstack-lbaasv2-driver
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))

# Repos that are used for the tests and environment
# TLC
export TLC_DIR := /home/buildbot/tlc
export TLC_REPO := https://bldr-git.int.lineratesystems.com/openstack/tlc.git
export TLC_BRANCH := buildbot

# toolsbase (replicate internal directory structure for TLC install)
export TOOLSBASE_DIR := /toolsbase
export TOOLSBASE_REPO := https://bldr-git.int.lineratesystems.com/openstack/tlc-toolsbase.git

# dev-test (contains all of our TLC files for configuration)
export DEVTEST_DIR := /home/buildbot/dev-test
export DEVTEST_REPO := git@bldr-git.int.lineratesystems.com:openstack/dev-test.git

# tempest (OpenStack tempest test library)
export TEMPEST_DIR := /home/buildbot/tempest
export TEMPEST_REPO := http://git.openstack.org/openstack/tempest

# neutron-lbaas (OpenStack Neutron LBaaS repo for the test cases to run)
export NEUTRON_LBAAS_DIR := /home/buildbot/neutron-lbaas
export NEUTRON_LBAAS_REPO := https://github.com/F5Networks/neutron-lbaas.git
export NEUTRON_LBAAS_BRANCH := stable/mitaka

# TLC path and python path requirements
export PATH := /tools/bin:$(PATH)
export PYTHONPATH := /tools/lib:/tools/bin:$(PYTHONPATH)
export USER := buildbot
export TEST_OPENSTACK_DISTRO := liberty
export TEST_VE_IMAGE := os_ready-BIGIP-11.6.0.0.0.401.qcow2
export TEST_CIRROS_IMAGE := cirros-0.3.4-x86_64-disk.qcow2
export TEST_OPENSTACK_NODE_COUNT := 2
export TEST_OPENSTACK_DEPLOY := multinode
export TEST_OPENSTACK_CLOUD := overcloud
export TEST_COMMON_LIB := $(DEVTEST_DIR)/common
export GLANCE_COMPUTE_STORAGE := NFS
export TLC_FILE := ${DEVTEST_DIR}/traffic/$(TEST_OPENSTACK_CLOUD)/ve_$(TEST_OPENSTACK_CLOUD).tlc
export TEST_SESSION := $(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP)

# Virtualenv & tempest requirements
export VENVDIR := /home/buildbot/virtualenvs
export TEMPEST_VENV_DIR := $(VENVDIR)/tempest
export TEMPEST_CONFIG_DIR := $(TEMPEST_VENV_DIR)/etc/tempest
export TEMPEST_VENV_ACTIVATE := $(TEMPEST_VENV_DIR)/bin/activate

# Results Directories
export RESULTS_DIR := $(MAKEFILE_DIR)/test_results/$(PROJECT)
export API_SESSION := api_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export API_RESULTS_DIR := $(RESULTS_DIR)/api
export SCENARIO_SESSION := scenario_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export SCENARIO_RESULTS_DIR := $(RESULTS_DIR)/scenario

tlc-install:
	cd scripts && sudo -EH ./install_tlc.sh

functest:
	$(MAKE) -j -C . functest_all

functest_all: tempest_tests 

tempest_tests:
	@echo "automated functional tests..."
	$(MAKE) -C . tlc-install
	$(MAKE) -C . tempest_tests-setup
	$(MAKE) -C . tempest_tests-install
	$(MAKE) -C . tempest_tests-run
	$(MAKE) -C . tempest_tests-teardown

tempest_tests-setup:
	@echo "setting up tempest test TLC session..."
	cd scripts && ./tlc_session_setup.sh || $(MAKE) -C ../ tempest_tests-teardown

tempest_tests-install:
	@echo "installing and configuring tempest tests..."
	cd scripts && ./tempest_setup.sh || $(MAKE) -C ../ tempest_tests-teardown

tempest_tests-run:
	@echo "running the tempest test cases..."
	cd scripts && ./tempest_tests.sh || $(MAKE) -C ../ tempest_tests-teardown

tempest_tests-teardown:
	@echo "tearing down the TLC session..."
	-cd scripts && ./tlc_session_cleanup.sh
