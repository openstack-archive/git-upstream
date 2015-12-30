# How to run functional tests

Just run

    run_tests.sh

That script will install a virtual env with git-upstream (from the current repo
clone) and will run every script which name match the following regex:

    ([0-9]{3})-test_(.+).sh

Order of execution is given by $1 and test name by $2.

It's also possible to run single tests creating a test directory and running

    BASE_TEST_DIR=<your base test dir> 0xx-test_<your test name>.sh

But that will need a git-upstream executable in your path.


# Creating more tests

Copy the following file

    sample-test_name_here.sh

giving it a name that matches the aforementioned regexp.

Then edit the file defining a function that performs the actual test

    function test_name1() {
      log DEBUG "Starting $TEST_NAME::$FUNCNAME"

      return 0
    }

Leave rest of the code as it is.

## Reference of global variables/functions available in this framework


logging.lib
-----------

set_verbority()     Set verbosity level. Available verbosities are:
                    "ERROR WARNING INFO DEBUG"

log()               Print the given string, with a decoration, if current
                    verbosity level is less or equal to the one passed as
                    an argument.

utils.lib
-----------

TEST_DIR            Testing directory. Objects pertaining a test should be
                    created under that directory.

TEST_NAME           The name of current test. Extracted from the test filename.

prepare_for_git_upstream() Using the current git-upstream repo, create an
                           initial configuration useful for testing
                           git-upstream.
                           After invoking it a  "$TEST_DIR/$REPO_NAME"

## Environment variable used by the test framework

VERBOSITY           Set tests verbosity. Valid verbosities are:
                    "ERROR WARNING INFO DEBUG"

LEAVE_DIR           If equals to "yes", testing framework won't remove testing
                    directory. Useful for debugging and to inspect tests
                    results.
