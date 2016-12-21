#!/usr/bin/env bash

set -ex

# Activate our tempest virtualenv
source ${TEMPEST_VENV_ACTIVATE}
cd ${NEUTRON_LBAAS_DIR}

# LBaaSv2 API test cases with F5 tox.ini file
tox -e apiv2 -c f5.tox.ini -- \
  -lvv --tb=line \
  --autolog-outputdir ${API_RESULTS_DIR} \
  --autolog-session ${API_SESSION}

# LBaaSv2 Scenario test cases with F5 tox.ini file
tox -e scenariov2 -c f5.tox.ini -- \
  -lvv --tb=line \
  --autolog-outputdir ${SCENARIO_RESULTS_DIR} \
  --autolog-session ${SCENARIO_SESSION}
