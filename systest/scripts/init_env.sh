#!/usr/bin/env bash

set -ex

# - JOB_NAME is provided by Jenkins
#   (eg. "openstack/driver/liberty/12.1.1-undercloud-vxlan")

git clone --single-branch --depth=1 -b stable/newton https://github.com/F5Networks/f5-openstack-agent.git /home/jenkins/agent_commit
export AGENT_HASH=$(cd /home/jenkins/agent_commit && git rev-parse HEAD | xargs)
export CI_PROGRAM=$(echo $JOB_NAME | cut -d "/" -f 1)
export CI_PROJECT=$(echo $JOB_NAME | cut -d "/" -f 2)
export CI_BRANCH=$(echo $JOB_NAME | cut -d "/" -f 3)

job_dirname="${CI_PROGRAM}.${CI_PROJECT}.${CI_BRANCH}.${JOB_BASE_NAME}"
build_dirname="${JOB_BASE_NAME}-${BUILD_ID}"
export CI_RESULTS_DIR="/home/jenkins/results/${job_dirname}/${build_dirname}"
export CI_BUILD_SUMMARY="${CI_RESULTS_DIR}/ci-build.yaml"
# The following logic enables combined coverage reporting.
export COVERAGEROOT=/testlab/openstack/testresults/coverage/agent/${CI_BRANCH}/${AGENT_HASH}
export AGENTCOVERAGEDIR=${COVERAGEROOT}/from_driver/${BUILD_ID}_${JOB_BASE_NAME}
export PYTHONDONTWRITEBYTECODE=1

# - source this job's environment variables
export CI_ENV_FILE=systest/${JOB_BASE_NAME}.env
if [ -e $CI_ENV_FILE ]; then
    . $CI_ENV_FILE
fi

# - print env vars
printenv | sort | grep -v OS_PASSWORD
