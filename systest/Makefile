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

.PHONY: all functest \
tlc-install \
tempest_tests-install tempest_tests-teardown \
tempest_11.5.4_overcloud tempest_11.5.4_undercloud \
tempest_11.6.0_overcloud tempest_11.6.0_undercloud \
tempest_11.6.1_overcloud tempest_11.6.1_undercloud \
tempest_12.1.1_overcloud tempest_12.1.1_undercloud

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
export TEST_CIRROS_IMAGE := cirros-0.3.4-x86_64-disk.qcow2
export TEST_OPENSTACK_NODE_COUNT := 2
export TEST_OPENSTACK_DEPLOY := multinode
export TEST_COMMON_LIB := $(DEVTEST_DIR)/common
export GLANCE_COMPUTE_STORAGE := NFS
export TLC_FILE_DIR := $(DEVTEST_DIR)/traffic

# Virtualenv & tempest requirements
export VENVDIR := /home/buildbot/virtualenvs
export TEMPEST_VENV_DIR := $(VENVDIR)/tempest
export TEMPEST_CONFIG_DIR := $(TEMPEST_VENV_DIR)/etc/tempest
export TEMPEST_VENV_ACTIVATE := $(TEMPEST_VENV_DIR)/bin/activate

# Results Directories
export API_SESSION := api_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export SCENARIO_SESSION := scenario_$(SUBJECTCODE_ID)_$(TIMESTAMP)

# Install the TLC application
tlc-install:
	cd scripts && sudo -EH ./install_tlc.sh

# Run all tests, this is what buildbot calls: make functest
functest:
	$(MAKE) -C . functest_all

# These are all of the functests that we want to run as part of bbot job
# We ignore the return value so that we run all of the tests
functest_all: tlc-install tempest_tests-install
	-$(MAKE) -C . tempest_11.5.4_overcloud
	-$(MAKE) -C . tempest_11.6.0_overcloud
	-$(MAKE) -C . tempest_11.6.1_overcloud
	-$(MAKE) -C . tempest_12.1.1_overcloud
	-$(MAKE) -C . tempest_11.5.4_undercloud
	-$(MAKE) -C . tempest_11.6.0_undercloud
	-$(MAKE) -C . tempest_11.6.1_undercloud
	-$(MAKE) -C . tempest_12.1.1_undercloud

# Not using the tempest TLC files for liberty because they install barbican
# which causes the tests to lockup/hang

# Tempest Tests for 11.5.x overcloud VE deployment
tempest_11.5.4_overcloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-11.5.4.2.0.291.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

# Tempest Tests for 11.6.x overcloud VE deployment
tempest_11.6.0_overcloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.0.0.0.401.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

tempest_11.6.1_overcloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.1.1.0.326.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

# Tempest Tests for 12.1.x overcloud VE deployment
tempest_12.1.1_overcloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.1.2.0.204.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

# Tempest Tests for 11.5.x undercloud VE deployment
tempest_11.5.4_undercloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-11.5.4.2.0.291.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

# Tempest Tests for 11.6.x undercloud VE deployment
tempest_11.6.0_undercloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.0.0.0.401.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

tempest_11.6.1_undercloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.1.1.0.326.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

# Tempest Tests for 12.1.x undercloud VE deployment
tempest_12.1.1_undercloud:
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.1.2.0.204.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(PROJECT)_$(BRANCH)_$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$(PROJECT)/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	$(MAKE) -C . tempest_tests

# Once we have the variables setup we can run the tempest tests on our env
tempest_tests:
	$(MAKE) -C . tempest_tests-setup
	$(MAKE) -C . tempest_tests-config
	$(MAKE) -C . tempest_tests-run
	$(MAKE) -C . tempest_tests-cleanup

tempest_tests-install:
	@echo "installing tempest tests..."
	cd scripts && ./tempest_install.sh || $(MAKE) -C ../ tempest_tests-cleanup

tempest_tests-setup:
	@echo "setting up tempest test TLC session..."
	cd scripts && ./tlc_session_setup.sh || $(MAKE) -C ../ tempest_tests-cleanup

tempest_tests-config:
	@echo "configuring tempest for the values in our TLC environment"
	cd scripts && ./tempest_config.sh || $(MAKE) -C ../ tempest_tests-cleanup

tempest_tests-run:
	@echo "running the tempest test cases..."
	cd scripts && ./tempest_tests.sh || $(MAKE) -C ../ tempest_tests-cleanup

tempest_tests-cleanup:
	@echo "cleaning up down the TLC session..."
	-cd scripts && ./tlc_session_cleanup.sh
