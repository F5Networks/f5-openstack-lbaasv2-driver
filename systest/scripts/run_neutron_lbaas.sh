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

# Create .pytest.rootdir files at the root of the driver and neutron-lbaas
# respositories to make the results suite names be rooted at the top-level
# of the respective test repository
touch ${PROJROOTDIR}f5lbaasdriver/test/tempest/tests/.pytest.rootdir
touch ${NEUTRON_LBAAS_DIR}/neutron_lbaas/tests/tempest/v2/.pytest.rootdir


# The following tox commands will fail, if the ${EXCLUDE_FILE}
# doesn't exist in the ${EXCLUDE_DIR}.

# Navigate to the root of the repo, where the tox.ini file is found
cd ${PROJROOTDIR}

bash -c "tox -e tempest -c tox.ini --sitepackages -- \
  --meta ${EXCLUDE_DIR}/${EXCLUDE_FILE} \
  -lvv \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${API_SESSION}"

cd ${NEUTRON_LBAAS_DIR}

# LBaaSv2 API test cases with F5 tox.ini file
bash -c "tox -e apiv2 -c f5.tox.ini --sitepackages -- \
  --meta ${EXCLUDE_DIR}/${EXCLUDE_FILE} \
  -lvv \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${API_SESSION}"

# LBaaSv2 Scenario test cases with F5 tox.ini file
bash -c "tox -e scenariov2 -c f5.tox.ini --sitepackages -- \
  --meta ${EXCLUDE_DIR}/${EXCLUDE_FILE} \
  -lvv \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${SCENARIO_SESSION}"

exit 0
