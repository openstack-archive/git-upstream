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

SUCCESS_SHA1="e1dfee279aa5b6b05296a97b4eba8dde0b6eea4b ?-"

function test_simple_rebase() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  prepare_for_git_upstream $TEST_DIR $REPO_NAME $UPSTREAM_REPO $TEST_BASE_REF \
                    $TEST_NAME

  pushd $TEST_DIR/$REPO_NAME >/dev/null

  log DEBUG "Creating a local patch"
  cat <<EOP | patch -tsp1 || return 1
diff --git a/setup.py b/setup.py
index 170ec46..251e1dd 100644
--- a/setup.py
+++ b/setup.py
@@ -28,6 +28,8 @@ setup(
     version=version.version,
     author="Darragh Bailey",
     author_email="dbailey@hp.com",
+    maintainer="Davide Guerri",
+    maintainer_email="davide.guerri@hp.com",
     description=("Tool supporting HPCloud git workflows."),
     license="Proprietary",
     keywords="git hpcloud workflow",
EOP

  # use smart quotes to test unicode characters in commit messages
  git commit -a -m "Add “Davide Guerri” as maintainer" --quiet || return 1
  git push -u origin master --quiet >/dev/null || return 1

  log DEBUG "Cherry picking upstream commits"
  for cp in $CHERRY_PICKS; do
    log DEBUG "Cherry picking commit $cp"
    git cherry-pick $cp >/dev/null || return 1
  done

  git push --quiet || return 1

  git checkout master --quiet || return 1

  log DEBUG "Rebasing local patches onto upstream version $TEST_REBASE_REF"
  git branch import/$TEST_NAME-new $TEST_REBASE_REF --quiet || return 1

  git-upstream import import/$TEST_NAME-new >/dev/null || return 1

  local test_sha1="$(git show --numstat | tail -9 | shasum -p -)"
  if [ "$test_sha1" != "$SUCCESS_SHA1" ]
  then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

TESTS="test_simple_rebase"

for test in $TESTS; do
  $test && log INFO "$TEST_NAME::$test() passed." || \
           log ERROR "$TEST_NAME::$test() failed!"
done
