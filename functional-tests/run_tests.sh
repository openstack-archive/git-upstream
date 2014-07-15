#!/bin/bash

BASE_DIR=$(cd $(dirname $0); pwd -P)

INSTALL_DIR=$(dirname $BASE_DIR)
TIME_STAMP=$(date +%Y%m%d%H%M%S)
export BASE_TEST_DIR=$(mktemp -d $BASE_DIR/test-$TIME_STAMP-XXXX)

# Include and run common test functions and initializations
source $BASE_DIR/libs/logging.lib


export VERBOSITY="${VERBOSITY:-INFO}"
set_verbority $VERBOSITY

if [ -n "$LEAVE_DIR" -a "$LEAVE_DIR" == "yes" ]; then
  export LEAVE_DIR="yes"
else
  unset LEAVE_DIR
fi

function check_app() {
  if [ $# -ne 1 ]; then
    log ERROR "Invalid number of argument! \
      (${BASH_SOURCE[1]##*/} ${BASH_LINENO[0]}::check_app())"
    exit 127
  fi

  local app=$1

  if [ ! -x $(which $app) ]; then
    log ERROR "App '$app' not found"
    exit 127
  fi

  return 0
}

function _clean_up() {
  log DEBUG "Cleaning up"

  # Deactivate virtualenv
  log DEBUG "Deactivate virtualenv"
  deactivate >/dev/null 2>&1

  if [ -z "$LEAVE_DIR" ]; then
    log DEBUG "Removing base test directory"
    rm -rf $BASE_TEST_DIR
  fi

}

# Define an handler for clean_up
trap "_clean_up; exit 0" EXIT

# ----- Start

log DEBUG "Initializing testbed"

check_app virtualenv

log DEBUG "Creating virtualenv for git-upstream"
rm -rf $BASE_TEST_DIR/virtualenv >/dev/null 2>&1
virtualenv $BASE_TEST_DIR/virtualenv >/dev/null 2>&1
if [ $? -ne 0 ]; then
  log ERROR "Virtualenv creation failed"
  exit 1
fi

log DEBUG "Activating virtualenv for git-upstream"
source $BASE_TEST_DIR/virtualenv/bin/activate

if [ $? -ne 0 ]; then
  log ERROR "Virtualenv activation failed"
  exit 1
fi

log DEBUG "Installing git-upstream"
easy_install -q $INSTALL_DIR >/dev/null 2>&1
if [ $? -ne 0 ]; then
  log ERROR "git-upstream installation failed!"
  exit 1
fi

if [ "$#" -ge "1" ]; then
  for test_number in "$@"; do
    for test in $(ls $test_number-test*); do
      $BASE_DIR/$test
    done
  done
else
  for test in $(ls [[:digit:]][[:digit:]][[:digit:]]-test*); do
    $BASE_DIR/$test
  done
fi
