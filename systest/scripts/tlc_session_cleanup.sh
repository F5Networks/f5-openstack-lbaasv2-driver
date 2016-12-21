#!/usr/bin/env bash

# Cleanup the session. Should we be killing the barbican in Mesos too?
tlc --session ${TEST_SESSION} --debug cleanup
