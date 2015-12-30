#!/bin/bash

BASE_DIR=$(cd $(dirname $0); pwd -P)

# Include and run common test functions and initializations
source $BASE_DIR/libs/logging.lib
source $BASE_DIR/libs/utils.lib


function test_name1() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  return 0
}


function test_name2() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  return 0
}


TESTS="test_name1 test_name2"

for test in $TESTS; do
  $test && log INFO "$TEST_NAME::$test() passed." || \
           log ERROR "$TEST_NAME::$test() failed!"
done
