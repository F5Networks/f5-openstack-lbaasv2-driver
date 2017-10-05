#!/usr/bin/env bash

# This script combines and publishes the results of the tests run on a
# particular commit for the agent.

echo ${COVERAGEROOT}
ls -al ${COVERAGEROOT}
cd ${COVERAGEROOT} && mkdir -p coveragefiles && \
find . -iname ".coverage_*" -exec cp -f {} coveragefiles/ \; && \
coverage combine ${COVERAGEROOT}/coveragefiles/.coverage*
cp -f ${COVERAGEROOT}/.coverage ${COVERAGEROOT}/source_code
cp -f ${COVERAGEROOT}/.coveragerc ${COVERAGEROOT}/source_code
source /home/jenkins/coverallstoken

cd ${COVERAGEROOT}/source_code && coveralls -v
