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

# Fixing branch to that specified in the public fork. This is necessary for build on PRs.
export BRANCH := stable/newton
export GIT_REMOTE_URL := $(shell git config --get remote.origin.url)
# The below operations are used for the builds on PR. The two variables are defined by the
# Github Pull Request Builder plugin for Jenkins. --> ghprb...
# https://wiki.jenkins.io/display/JENKINS/GitHub+pull+request+builder+plugin
ghprbAuthorRepoGitUrl?=$(GIT_REMOTE_URL)
ghprbActualCommit?=$(BRANCH)
export DRIVER_PIP_INSTALL_LOCATION := git+$(ghprbAuthorRepoGitUrl)@$(ghprbActualCommit)

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
export PROJROOTDIR := $(abspath $(MAKEFILE_DIR))/../
export TEST_DIR := $(abspath $(MAKEFILE_DIR))../test

# Test exclude directory
export EXCLUDE_DIR := $(MAKEFILE_DIR)/exclude/

# dev-test (contains all of our TLC files for configuration)
export DEVTEST_DIR := /home/jenkins/dev-test
export DEVTEST_REPO := git@gitlab.pdbld.f5net.com:openstack/dev-test.git

# tempest (OpenStack tempest test library)
export TEMPEST_DIR := $(PROJROOTDIR)tempest
export TEMPEST_REPO := http://git.openstack.org/openstack/tempest

# neutron-lbaas (OpenStack Neutron LBaaS repo for the test cases to run)
export NEUTRON_LBAAS_DIR := /home/jenkins/neutron-lbaas
export NEUTRON_LBAAS_REPO := https://github.com/F5Networks/neutron-lbaas.git
export NEUTRON_LBAAS_BRANCH := stable/newton
export UPPER_CONSTRAINTS_FILE := https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=$(NEUTRON_LBAAS_BRANCH)

# TLC path and python path requirements
export PATH := /tools/bin:$(PATH)
export PYTHONPATH := /tools/lib:/tools/bin:$(PYTHONPATH)
export USER := jenkins
export TEST_OPENSTACK_DISTRO := newton
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


microservice_setup_tlc_session:
	@echo "setting up TLC session..."
	sudo -E chown -Rf jenkins:jenkins $(PROJROOTDIR) && \
	cd scripts && ./$@.sh || $(MAKE) -C ../ cleanup_failed_tlc

configure_test_infra:
	@echo "injecting TLC symbol and openstack IDs into 'tempest' conf files..."
	cd scripts && ./$@.sh || $(MAKE) -C ../ cleanup_failed_tlc

run_neutron_lbaas:
	@echo "running tests extracted from 'neutron_lbaas' project..."
	cd scripts && ./$@.sh || $(MAKE) -C ../ cleanup_tlc_session

run_agent_transfers:
	@echo "running tests extracted from 'f5-openstack-agent' project..."
	cd scripts && ./$@.sh

run_smoke_tests:
	@echo "running smoke tests for build on PR..."
	cd scripts && ./$@.sh || $(MAKE) -C ../ cleanup_tlc_session

cleanup_tlc_session:
	@echo "running tlc --session TEST_SESSION --debug cleanup..."
	cd scripts && ./$@.sh

cleanup_failed_tlc:
	@echo "running tlc --session TEST_SESSION --debug cleanup && exit 1..."
	cd scripts && ./$@.sh

# BRANCH MAKE TARGETS:
#
# These make targets invoke OTHER targets defined in this file.  They are not
# used to invoke particular tests, rather they manage test infrastructure.
#
# Not using the tempest TLC files for liberty because they install barbican
# which causes the tests to lockup/hang

# Tempest Tests for 13.0.0 undercloud VE deployment
tempest_13.0.0_undercloud_vxlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-13.0.0.2.0.1671.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 11.5.x overcloud VE deployment
tempest_11.5.4_overcloud:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.5.4.2.0.291.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 11.6.x overcloud VE deployment
tempest_11.6.0_overcloud:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.0.0.0.401.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.6.1_overcloud:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.1.1.0.326.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 12.1.x overcloud VE deployment
tempest_12.1.2_overcloud:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.2.0.0.249.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=overcloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 11.5.4 undercloud VE deployment
tempest_11.5.4_undercloud_vxlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.5.4.2.0.291.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.5.4_undercloud_gre:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.5.4.2.0.291.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=gre ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.5.4_undercloud_vlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.5.4.2.0.291.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 11.6.x undercloud VE deployment
tempest_11.6.0_undercloud_vxlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.0.0.0.401.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.6.0_undercloud_gre:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.0.0.0.401.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=gre ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.6.0_undercloud_vlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.0.0.0.401.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 11.6.1 undercloud VE deployment
tempest_11.6.1_undercloud_vxlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.1.1.0.326.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.6.1_undercloud_gre:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.1.1.0.326.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=gre ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_11.6.1_undercloud_vlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-11.6.1.1.0.326.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

# Tempest Tests for 12.1.x undercloud VE deployment
tempest_12.1.2_undercloud_vxlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.2.0.0.249.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_12.1.2_undercloud_gre:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.2.0.0.249.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=gre ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests

tempest_12.1.2_undercloud_vlan:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.2.0.0.249.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_tests



# Default deployment for smoke is 12.1.2 undercloud vxlan
tempest_smoke_test:
	export PROJROOTDIR=$(PROJROOTDIR) ;\
	export TEST_VE_IMAGE=os_ready-BIGIP-12.1.2.0.0.249.qcow2 ;\
	export TEST_OPENSTACK_CLOUD=undercloud ;\
	export TLC_FILE=$(TLC_FILE_DIR)/$${TEST_OPENSTACK_CLOUD}/tempest_ve_$${TEST_OPENSTACK_CLOUD}.tlc ;\
	export GUMBALLS_PROJECT=$(CHANGESOURCE)_$(SANITIZED_BRANCH)-$@ ;\
	export RESULTS_DIR=$(MAKEFILE_DIR)/test_results/$${GUMBALLS_PROJECT} ;\
	export TEST_SESSION=$@_$(SANITIZED_BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP) ;\
	export TEST_TENANT_NETWORK_TYPE=vxlan ;\
	export EXCLUDE_FILE=$@.yaml ;\
	$(MAKE) -C . run_smoke

run_tests:
	$(MAKE) -C . microservice_setup_tlc_session
	$(MAKE) -C . configure_test_infra
	$(MAKE) -C . run_neutron_lbaas
	$(MAKE) -C . cleanup_tlc_session

run_smoke:
	$(MAKE) -C . microservice_setup_tlc_session
	$(MAKE) -C . configure_test_infra
	$(MAKE) -C . run_smoke_tests
	$(MAKE) -C . cleanup_tlc_session
