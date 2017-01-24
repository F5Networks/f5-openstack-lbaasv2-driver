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

set -ex

# Activate our tempest virtualenv
source ${TEMPEST_VENV_ACTIVATE}

# Navigate to the root of the repo, where the tox.ini file is found
cd ${MAKEFILE_DIR}/../
tox -e tempest -c tox.ini -- \
  -lvv --tb=line \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${DRIVER_TEMPEST_SESSION}

cd ${NEUTRON_LBAAS_DIR}
tox -e tempest -c tox.ini -- \
  -lvv --tb=line \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${API_SESSION}

cd ${NEUTRON_LBAAS_DIR}
# LBaaSv2 API test cases with F5 tox.ini file
tox -e apiv2 -c f5.tox.ini -- \
  -lvv --tb=line \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${API_SESSION}

# LBaaSv2 Scenario test cases with F5 tox.ini file
tox -e scenariov2 -c f5.tox.ini -- \
  -lvv --tb=line \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${SCENARIO_SESSION}
