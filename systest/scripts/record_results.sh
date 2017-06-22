#!/usr/bin/env bash

set -ex

# - copy results files to nfs (note that the nfs results directory is mounted
#    inside the CI worker's home directory)
cp -r $WORKSPACE/systest/test_results/* $CI_RESULTS_DIR/
