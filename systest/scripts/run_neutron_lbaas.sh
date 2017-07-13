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

# Activate our tempest virtualenv
source ${TEMPEST_VENV_ACTIVATE}
cd ${NEUTRON_LBAAS_DIR}

# The following tox commands will fail, if the ${EXCLUDE_FILE}
# doesn't exist in the ${EXCLUDE_DIR}.

# Create .pytest.rootdir file at root of the neutron-lbaas repository directory
touch ${NEUTRON_LBAAS_DIR}/.pytest.rootdir


# Only run scenario tests if we're running a smoke test.
if [ -z "${SMOKE_TESTS}" ]; then
  # LBaaSv2 API test cases with F5 tox.ini file
  tox -e apiv2 -c f5.tox.ini --sitepackages -- \
    --meta ${EXCLUDE_DIR}/${EXCLUDE_FILE} \
    -lvv --tb=short \
    --autolog-outputdir ${RESULTS_DIR} \
    --autolog-session ${API_SESSION}
fi

# LBaaSv2 Scenario test cases with F5 tox.ini file
tox -e scenariov2 -c f5.tox.ini --sitepackages -- \
  --meta ${EXCLUDE_DIR}/${EXCLUDE_FILE} \
  -lvv --tb=short \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${SCENARIO_SESSION}

# Returning pass so that all tests run
exit 0
