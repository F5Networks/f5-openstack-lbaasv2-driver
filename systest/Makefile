.PHONY: all systest functest tempest_tests tempest_tests-setup \
tempest_tests-install tempest_tests-run \
tempest_tests-teardown

PROJECT := f5-openstack-agent
repo := https://github.com/F5Networks/$(PROJECT).git

# name/location config for BAHAMAS

BAHAMAS := bahamas.int.lineratesystems.com
SCRIPTDIR := /home/builder/tempest_sessions/dev-test/bbot_integration

# - <nearest reachable tag>-<num commits since>-g<abbreviated commit id>
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
CUTVERSION := $(shell git describe --long)
TIMESTAMP ?= $(shell date +"%Y%m%d-%H%M%S")
export TIMESTAMP   # Only eval TIMESTAMP in the top make.
RESULTSDIR := test_results/$(PROJECT)

TESTSESSION := $(BRANCH)_$(CUTVERSION)_$(TIMESTAMP)
tempest_session := tempest_$(CUTVERSION)_$(TIMESTAMP)

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
    

tempest_tests-install:
	@echo "installing system tests ..."
	scp -rp -F $(ssh_conf) testenv_symbols/ bastion:~/
	scp -F $(ssh_conf) ./scripts/install_systests.sh bastion:~/
	ssh -AF $(ssh_conf) bastion "~/install_systests.sh $(repo) $(BRANCH)"

tempest_tests-run:
	@echo "running disconnected tests ..."
	scp -F $(ssh_conf) ./scripts/run_neutronlesstests.sh bastion:~/
	ssh -tF $(ssh_conf) bastion \
		"~/run_neutronlesstests.sh $(tempest_session)" || true

tempest_tests-teardown:
	@echo "downloading functional test results ..."
	if [ ! -e $(tempest_results) ]; then mkdir -p $(tempest_results); fi
	scp -rp -F $(ssh_conf) \
		bastion:~/test_results/$(tempest_session)/* $(tempest_results)
	testenv delete --name $(tempest_session) --config $(testenv_config)
