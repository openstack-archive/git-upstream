#!/bin/bash

BASE_DIR=$(cd $(dirname $0); pwd -P)

# Include and run common test functions and initializations
source $BASE_DIR/libs/logging.lib
source $BASE_DIR/libs/utils.lib

REPO_NAME="empty-repo"
UPSTREAM_REPO=$(git rev-parse --show-toplevel)
TEST_BASE_REF="2c4bf67b5c416adfb162d9ca1fb4b0bf353fbb2a"
CHERRY_PICKS="19b89746d08fa224bb8aba12106dbc330cb5d019 \
              5d4fbe79037c3b2516216258a907d3a02f0b205c"
TEST_REBASE_REF="fd3524e1b7353cda228b6fb73c3a2d34a4fee4de"


function test_no_local_changes() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  prepare_for_git_upstream $TEST_DIR $REPO_NAME $UPSTREAM_REPO $TEST_BASE_REF \
                    $TEST_NAME

  pushd $TEST_DIR/$REPO_NAME >/dev/null

  log DEBUG "Cherry picking upstream commits"
  for cp in $CHERRY_PICKS; do
    log DEBUG "Cherry picking commit $cp"
    git cherry-pick $cp >/dev/null || return 1
  done

  git push -u origin master --quiet >/dev/null || return 1

  git checkout master --quiet || return 1

  log DEBUG "Rebasing local patches onto upstream version $TEST_REBASE_REF"
  git branch import/$TEST_NAME-new $TEST_REBASE_REF --quiet || return 1

  local result="$(git-upstream import import/$TEST_NAME-new)"

  echo "$result" | grep "There are no local changes to be applied!" >/dev/null

  if [ "$?" -ne 0 ]; then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

TESTS="test_no_local_changes"

for test in $TESTS; do
  $test && log INFO "$TEST_NAME::$test() passed." || \
           log ERROR "$TEST_NAME::$test() failed!"
done
