#!/bin/bash

BASE_DIR=$(cd $(dirname $0); pwd -P)

# Include and run common test functions and initializations
source $BASE_DIR/libs/logging.lib
source $BASE_DIR/libs/utils.lib

REPO_NAME="empty-repo"
UPSTREAM_REPO=$(git rev-parse --show-toplevel)
TEST_BASE_REF="2c4bf67b5c416adfb162d9ca1fb4b0bf353fbb2a"
TEST_REBASE_REF="fd3524e1b7353cda228b6fb73c3a2d34a4fee4de"
VALID_CHID="I82ef79c3621dacf619a02404f16464877a06f158"
VALID_CHID2="I2492200f8e6fb0cc470cc376eb17a39b4b3033ff"
INVALID_CHID="I0123456789abcdef0123456789abcdef01234567"

SUCCESS_SHA1="b8c16b3dd8883d02b4b65882ad5467c9f5e7beb9 ?-"

function _common() {
  prepare_for_git_upstream $TEST_DIR $REPO_NAME $UPSTREAM_REPO $TEST_BASE_REF \
                    $TEST_NAME

  pushd $TEST_DIR/$REPO_NAME >/dev/null

  log DEBUG "Creating a local patches"
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
  git commit -a -m "Add maintainer info" --quiet || return 1

  cat <<EOP | patch -tsp1 || return 1
diff --git a/nothing b/nothing
new file mode 100644
index 0000000..9dafe9b
--- /dev/null
+++ b/nothing
@@ -0,0 +1 @@
+nothing
EOP
  git add nothing
  git commit -a -m "Add nothing" --quiet || return 1
  git push -u origin master --quiet >/dev/null || return 1

  git checkout master --quiet || return 1

  log DEBUG "Rebasing local patches onto upstream version $TEST_REBASE_REF"
  git branch import/$TEST_NAME-new $TEST_REBASE_REF --quiet || return 1
}

function test_existing_changeid() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  _common || return 1

  local commit_sha1=$(git log -1 --format='%H')

  git-upstream supersede $commit_sha1 $VALID_CHID -u import/$TEST_NAME-new \
                                                        >/dev/null || return 1

  git-upstream import import/$TEST_NAME-new >/dev/null || return 1

  git show --numstat | grep '0\s\s*1\s\s*nothing' >/dev/null
  if [ "$?" -ne 0 ]; then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

function test_non_existing_changeid() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  _common || return 1

  local commit_sha1=$(git log -1 --format='%H')

  git-upstream supersede $commit_sha1 $INVALID_CHID -u import/$TEST_NAME-new 2>&1 | \
        grep "CRITICAL: Change-Id '$INVALID_CHID' not found in branch \
'import/$TEST_NAME-new'" >/dev/null
  if [ "$?" -ne 0 ]; then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

function test_non_existing_changeid_force() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  _common || return 1

  local commit_sha1=$(git log -1 --format='%H')

  git-upstream supersede $commit_sha1 $INVALID_CHID -u import/$TEST_NAME-new -f \
                                                          >/dev/null || return 1

  git-upstream -vv import import/$TEST_NAME-new | \
            grep -e "Including commit '[0-9a-f][0-9a-f]* Add nothing'" \
            >/dev/null
  if [ "$?" -ne 0 ]; then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

function test_multiple_changeids() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  _common || return 1

  local commit_sha1=$(git log -1 --format='%H')

  git-upstream supersede $commit_sha1 $VALID_CHID $VALID_CHID2 \
                                -u import/$TEST_NAME-new >/dev/null || return 1

  git-upstream -vv import import/$TEST_NAME-new >/dev/null || return 1

  git show --numstat | grep '0\s\s*1\s\s*nothing' >/dev/null
  if [ "$?" -ne 0 ]; then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

function test_one_non_exsisting_changeid() {
  log DEBUG "Starting $TEST_NAME::$FUNCNAME"

  _common || return 1

  local commit_sha1=$(git log -1 --format='%H')

  git-upstream supersede $commit_sha1 $VALID_CHID $INVALID_CHID \
      -u import/$TEST_NAME-new 2>&1 | \
      grep "CRITICAL: Change-Id '$INVALID_CHID' not found in branch \
'import/$TEST_NAME-new'" >/dev/null
  if [ "$?" -ne 0 ]; then
    popd >/dev/null
    return 1
  fi

  popd >/dev/null
}

TESTS="test_existing_changeid test_non_existing_changeid \
       test_non_existing_changeid_force test_multiple_changeids \
       test_one_non_exsisting_changeid"

for test in $TESTS; do
  $test && log INFO "$TEST_NAME::$test() passed." || \
           log ERROR "$TEST_NAME::$test() failed!"
done
