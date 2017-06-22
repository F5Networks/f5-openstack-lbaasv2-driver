#!/usr/bin/env bash

set -ex

# - write Jenkins build info to disk
mkdir -p $CI_RESULTS_DIR
echo "id: $BUILD_ID" > $CI_BUILD_SUMMARY
echo "url: ${BUILD_URL}consoleFull" >> $CI_BUILD_SUMMARY
echo "commit: $(git rev-parse HEAD)" >> $CI_BUILD_SUMMARY
echo "start_dt: $(date +"%Y%m%d-%H%M%S")" >> $CI_BUILD_SUMMARY
