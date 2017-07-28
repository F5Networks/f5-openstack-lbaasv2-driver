#!/usr/bin/env bash

set -x

: ${DOC_IMG:=f5devcentral/containthedocs:latest}

if [ $TRAVIS_BUILD_ID != "" ]; then
   exec docker run --rm -it \
   -v $TRAVIS_BUILD_DIR:$TRAVIS_BUILD_DIR --workdir $PWD \
   ${DOCKER_RUN_ARGS} \
   -e "LOCAL_USER_ID=$(id -u)" \
   ${DOC_IMG} "$@"
fi

exec docker run --rm -it \
  -v $PWD:$PWD --workdir $PWD \
  ${DOCKER_RUN_ARGS} \
  -e "LOCAL_USER_ID=$(id -u)" \
  ${DOC_IMG} "$@"