#!/bin/bash

BASE_DIR=$(cd $(dirname $0); pwd -P)

# Include and run common test functions and initializations
source $BASE_DIR/libs/logging.lib
source $BASE_DIR/libs/utils.lib


function test_version_output() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  git-upstream --version >/dev/null 2>&1

  return $?
}


TESTS="test_version_output"

for test in $TESTS; do
  $test && log INFO "$TEST_NAME::$test() passed." || \
           log ERROR "$TEST_NAME::$test() failed!"
done
