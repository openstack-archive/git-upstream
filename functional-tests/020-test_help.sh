#!/bin/bash

BASE_DIR=$(cd $(dirname $0); pwd -P)

# Include and run common test functions and initializations
source $BASE_DIR/libs/logging.lib
source $BASE_DIR/libs/utils.lib


function test_help_output() {
    local com="$1"
    log DEBUG "Starting $TEST_NAME::$FUNCNAME command $com"

    help1=$(git-upstream${com:+ }${com} --help)
    help2=$(git-upstream${com:+ }${com} -h)
    help3=$(git-upstream help${com:+ }${com})

    [ -z "$help1" -o -z "$help2" -o -z "$help3" -o \
      "$help1" != "$help2" -o "$help2" != "$help3" ] && return 1 || return 0
}

for com in "" "import" "drop" "supersede" ; do
  test_help_output $com && log INFO "test_help_output::${com:-null} passed." || \
                           log ERROR "test_help_output::${com:-null} failed!"
done
