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

# Create .pytest.rootdir files at the root of the driver.
touch ${PROJROOTDIR}f5lbaasdriver/test/tempest/tests/.pytest.rootdir

# Navigate to the root of the repo, where the tox.ini file is found
cd ${PROJROOTDIR}

# Remove smoke test rc file, in case someone is iterating on smoke tests
rm -rf ${SMOKE_RC_RESULT_FILE}

bash -c "tox -e tempest -c tox.ini --sitepackages -- \
      --meta ${EXCLUDE_DIR}/${EXCLUDE_FILE} \
        -lvv \
          --autolog-outputdir ${RESULTS_DIR} \
          --autolog-session ${API_SESSION} scenario/test_l7policies_and_rules.py::TestL7BasicRedirectToPool::test_policy_redirect_pool_cookie_contains" || echo $? > ${SMOKE_RC_RESULT_FILE}

if [ ! -f "${SMOKE_RC_RESULT_FILE}" ]; then
    echo 0 > ${SMOKE_RC_RESULT_FILE}
fi
