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


# TLC path and python path requirements
export PATH := /tools/bin:$(PATH)
export PYTHONPATH := /tools/bin:/tools/lib:$(PYTHONPATH)
export USER := builder
export TEST_OPENSTACK_DISTRO := libery
export TEST_VE_IMAGE := os_ready-BIGIP-11.6.0.0.0.401.qcow2
export TEST_OPENSTACK_NODE_COUNT := 2
export TEST_OPENSTACK_DEPLOY := multinode
export TEST_OPENSTACK_CLOUD := overcloud
export TEST_COMMON_LIB := ${DEVTEST_DIR}/common
export GLANCE_COMPUTE_STORAGE := NFS
export TLC_FILE := ${DEVTEST_DIR}/traffic/undercloud/ve_undercloud.tlc
export TEST_SESSION := $(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP)

# Virtualenv & tempest requirements
export VENVDIR := /home/buildbot/virtualenvs
export TEMPEST_DIR := /home/buildbot/tempest
export TEMPEST_VENV_DIR := $(VENVDIR)/tempest
export TEMPEST_CONFIG_DIR := $(TEMPEST_VENV_DIR)/etc/tempest
export TEMPEST_VENV_ACTIVATE := $(TEMPEST_VENV_DIR)/bin/activate
export NEUTRON_LBAAS_DIR := /home/buildbot/neutron-lbaas
export DEVTEST_DIR := /home/buildbot/dev-test

# Results Directories
export RESULTS_DIR := $(MAKEFILE_DIR)/test_results/$(PROJECT)
export API_SESSION := api_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export API_RESULTS_DIR := $(RESULTS_DIR)/api
export SCENARIO_SESSION := scenario_$(SUBJECTCODE_ID)_$(TIMESTAMP)
export SCENARIO_RESULTS_DIR := $(RESULTS_DIR)/scenario

tlc-install:
	cd scripts && sudo -H ./install_tlc.sh

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
	cd scripts && ./tlc_session_setup.sh

tempest_tests-install:
	@echo "installing and configuring tempest tests..."
	cd scripts && ./tempest_setup.sh

tempest_tests-run:
	@echo "running the tempest test cases..."
	cd scripts && ./tempest_tests.sh

tempest_tests-teardown:
	@echo "tearing down the TLC session..."
	-cd scripts && ./tlc_session_cleanup.sh
