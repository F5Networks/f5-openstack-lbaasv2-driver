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

tox --sitepackages -e functional -- \
  -lvv \
  --autolog-outputdir ${RESULTS_DIR} \
  --autolog-session ${FROM_AGENT_SESSION} \
  ${TEST_DIR}/functional/from_agent

# Returning pass so that all tests run
exit 0
