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

# Inform make that targets are NOT files.
.PHONY: all functest \
install_tlc \
install_test_infra \
tempest_12.1.1_overcloud tempest_12.1.1_undercloud \
tempest_12.1.1_undercloud_gre tempest_12.1.1_undercloud_vlan

# - <nearest reachable tag>-<num commits since>-g<abbreviated commit id>
export BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
# The branch may contain the text 'stable/' before the OpenStack release name
# To allow this type of branch name and any other to work with the cloud deployment
# and with Jenkins, we should strip out the forward slash, leaving something like:
# stable/newton -> stablenewton
SANITIZED_BRANCH := $(subst /,,$(BRANCH))
SUBJECTCODE_ID := $(shell git log -n 1 --format=%h)
TIMESTAMP ?= $(shell date +"%Y%m%d-%H%M%S")
export TIMESTAMP   # Only eval TIMESTAMP in the top make.
CHANGESOURCE := f5-openstack-lbaasv2-driver
MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
export MAKEFILE_DIR := $(dir $(MAKEFILE_PATH))
export TEST_DIR := $(abspath $(MAKEFILE_DIR))/../test

# Test exclude directory
export EXCLUDE_DIR := $(MAKEFILE_DIR)/exclude/

# Repos that are used for the tests and environment
# TLC
export TLC_DIR := /home/jenkins/tlc
export TLC_REPO := https://gitlab.pdbld.f5net.com/openstack/tlc.git
export TLC_BRANCH := buildbot

# toolsbase (replicate internal directory structure for TLC install)
export TOOLSBASE_DIR := /toolsbase
export TOOLSBASE_REPO := https://gitlab.pdbld.f5net.com/openstack/tlc-toolsbase.git

# dev-test (contains all of our TLC files for configuration)
export DEVTEST_DIR := /home/jenkins/dev-test
export DEVTEST_REPO := git@gitlab.pdbld.f5net.com:openstack/dev-test.git

# tempest (OpenStack tempest test library)
export TEMPEST_DIR := /home/jenkins/tempest
export TEMPEST_REPO := http://git.openstack.org/openstack/tempest

# neutron-lbaas (OpenStack Neutron LBaaS repo for the test cases to run)
export NEUTRON_LBAAS_DIR := /home/jenkins/neutron-lbaas
export NEUTRON_LBAAS_REPO := https://github.com/F5Networks/neutron-lbaas.git
export NEUTRON_LBAAS_BRANCH := stable/mitaka
export UPPER_CONSTRAINTS_FILE := https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=$(NEUTRON_LBAAS_BRANCH)


# TLC path and python path requirements
export PATH := /tools/bin:$(PATH)
export PYTHONPATH := /tools/lib:/tools/bin:$(PYTHONPATH)
export USER := jenkins
# Because the sanitized branch may still contain the string 'stable',
# we must strip that out to get the OpenStack release name alone. This
# will be used in the current TLC deployment of the stack.
export TEST_OPENSTACK_DISTRO := $(subst stable,,$(SANITIZED_BRANCH))
export TEST_CIRROS_IMAGE := cirros-0.3.4-x86_64-disk.qcow2
export TEST_OPENSTACK_NODE_COUNT := 3
export TEST_OPENSTACK_DEPLOY := multinode
export TEST_COMMON_LIB := $(DEVTEST_DIR)/common
export GLANCE_COMPUTE_STORAGE := NFS
export TLC_FILE_DIR := $(DEVTEST_DIR)/traffic

# Virtualenv & tempest requirements
export VENVDIR := /home/jenkins/virtualenvs
export TEMPEST_VENV_DIR := $(VENVDIR)/tempest
export TEMPEST_CONFIG_DIR := $(TEMPEST_VENV_DIR)/etc/tempest
export TEMPEST_VENV_ACTIVATE := $(TEMPEST_VENV_DIR)/bin/activate

# Results Directories
export API_SESSION := api_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export SCENARIO_SESSION := scenario_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export DRIVER_TEMPEST_SESSION := driver.tempest_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export FROM_AGENT_SESSION := from.agent_$(SUBJECTCODE_ID)_$(TIMESTAMP)

# LEAF MAKE TARGETS:
#
# This section contains "leaf" make targets.  These targets do not call other
# targets.  Most of the core logic of each of these targets can be found in
# the scripts directory under the same name as the target, i.e.:
# ./scripts/TARGET_NAME.sh
# e.g:  ./scripts/install_test_infra.sh
# We intend to adhere to this convention as long as it's convenient.
# Our reasoning is that this makes it easier to read this file and understand
# how it relates to the rest of the test infrastructure.
# Notice that these "leaves" are generally the exit points from this file, and
# without exception, invoke the aforementioned scripts.
#

install_tlc:
	@echo "installing the tlc client on the worker..."
	cd scripts && ./disallow_dangerous_vars.sh && sudo -EH ./$@.sh

install_test_infra:
	@echo "installing tempest openstack interfaces and neutron_lbaas tests..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh

setup_tlc_session:
	@echo "setting up TLC session..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh || $(MAKE) -C ../ cleanup_failed_tlc

configure_test_infra:
	@echo "injecting TLC symbol and openstack IDs into 'tempest' conf files..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh || $(MAKE) -C ../ cleanup_failed_tlc

run_neutron_lbaas:
	@echo "running tests extracted from 'neutron_lbaas' project..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh || $(MAKE) -C ../ cleanup_tlc_session

run_agent_transfers:
	@echo "running tests extracted from 'f5-openstack-agent' project..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh

cleanup_tlc_session:
	@echo "running tlc --session TEST_SESSION --debug cleanup..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh

cleanup_failed_tlc:
	@echo "running tlc --session TEST_SESSION --debug cleanup && exit 1..."
	cd scripts && ./disallow_dangerous_vars.sh && ./$@.sh

# BRANCH MAKE TARGETS:
#
# Not using the tempest TLC files for liberty because they install barbican
# which causes the tests to lockup/hang

# Tempest Tests for 12.1.x undercloud VE deployment
tempest_12.1.1_undercloud_vxlan:
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.1.2.0.204.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

run_tests: install_tlc install_test_infra
	$(MAKE) -C . setup_tlc_session
	$(MAKE) -C . configure_test_infra
	$(MAKE) -C . run_neutron_lbaas
	$(MAKE) -C . run_agent_transfers
	$(MAKE) -C . cleanup_tlc_session
