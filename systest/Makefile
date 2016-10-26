.PHONY: all systest functest tempest_tests tempest_tests-setup \
tempest_tests-install tempest_tests-run \
tempest_tests-teardown

PROJECT := f5-openstack-lbaasv2-driver
repo := https://github.com/F5Networks/$(PROJECT).git

# name/location config for BAHAMAS

BAHAMAS := bahamas.int.lineratesystems.com
SCRIPTDIR := /home/builder/tempest_sessions/dev-test/bbot_integration

# - <nearest reachable tag>-<num commits since>-g<abbreviated commit id>
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
SUBJECTCODE_ID := $(shell git log -n 1 --format=%h)
TIMESTAMP ?= $(shell date +"%Y%m%d-%H%M%S")
export TIMESTAMP   # Only eval TIMESTAMP in the top make.
RESULTSDIR := test_results/$(PROJECT)

TESTSESSION := $(BRANCH)_$(SUBJECTCODE_ID)_$(TIMESTAMP)
tempest_session := tempest_$(SUBJECTCODE_ID)_$(TIMESTAMP)

tempest_results := $(RESULTSDIR)/$(tempest_session)

testenv_config := os-agent-disconnected.testenv.yaml

functest:
	$(MAKE) -j -C . functest_all

functest_all: tempest_tests 

tempest_tests:
	@echo "automated functional tests..."
	$(MAKE) -C . tempest_tests-setup
	$(MAKE) -C . tempest_tests-install
	$(MAKE) -C . tempest_tests-run
	$(MAKE) -C . tempest_tests-teardown

tempest_tests-setup:
	@echo "setting up tempest test environment ..."
	ssh -A builder@$(BAHAMAS) "$(SCRIPTDIR)/tempest_v2driver_setup.sh"\
	" $(BRANCH)"\
	" $(TESTSESSION)"
	echo export TLC_SESSION=builder_$(TESTSESSION) >> tlc_session
    
tempest_tests-install:
	. ./tlc_session && ./scripts/tempest_v2driver_install.sh $(BAHAMAS) $${TLC_SESSION} $(BRANCH) $(SUBJECTCODE_ID) builder

tempest_tests-run:
	docker run `cat registry_fullname` || true
	@echo "downloading functional test results ..."
	docker cp $$(docker ps -qn1):/home/buildbot/testrunner/test_results ./test_results
	docker commit $$(docker ps -qn1) `cat registry_fullname`_test_results
	docker push `cat registry_fullname`_test_results

tempest_tests-teardown:
	. tlc_session && ssh -A builder@$(BAHAMAS)  "/tools/bin/tlc --sid \
        $${TLC_SESSION} cleanup"
