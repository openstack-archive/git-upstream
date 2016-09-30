# Copyright (c) 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the 'import' command"""

import inspect
import os

from testscenarios import TestWithScenarios
from testtools.content import text_content
from testtools.matchers import Contains
from testtools.matchers import Equals
from testtools.matchers import Not

from git_upstream.lib.pygitcompat import Commit
from git_upstream import main
from git_upstream.tests.base import BaseTestCase
from git_upstream.tests.base import get_scenarios


class TestImportCommand(TestWithScenarios, BaseTestCase):

    scenarios = get_scenarios(os.path.join(os.path.dirname(__file__),
                              "conflict_scenarios"))

    def setUp(self):
        # add description in case parent setup fails.
        self.addDetail('description', text_content(self.desc))

        self.commands, self.parser = main.build_parsers()

        script_cmdline = self.parser.get_default('script_cmdline')
        script_cmdline[-1] = os.path.join(os.getcwd(), main.__file__)
        self.parser.set_defaults(script_cmdline=script_cmdline)

        # builds the tree to be tested
        super(TestImportCommand, self).setUp()

        self.upstream_branch = self.branches['upstream'][0]
        self.target_branch = self.branches['head'][0]

    def test_command(self):
        self.git.tag(inspect.currentframe().f_code.co_name,
                     self.upstream_branch)

        args = self.parser.parse_args(self.parser_args)
        # we should always fail here
        self.assertThat(args.cmd.run(args), Equals(False))

        if hasattr(self, 'post_script'):
            # simulate of manual resolving conflicts and completion of import
            self.run_post_script()

        # assuming non-interactive we should not see the following message
        # from appear in the logged output.
        self.assertThat(self.logger.output,
                        Not(Contains("Successfully rebased and updated")))

        # perform sanity checks on results
        self._check_tree_state()

        # allow disabling of checking the merge commit contents
        # as some tests won't result in an import
        if getattr(self, 'check_merge', True):
            commit_message = self.git.log(self.target_branch, n=1)
            self.assertThat(
                commit_message,
                Contains("of '%s' into '%s'" % (self.upstream_branch,
                                                self.target_branch)))
            # make sure the final state is actually correct
            self.assertThat(
                self.repo.git.rev_parse("%s^{tree}" % self.target_branch),
                Equals(self.repo.git.rev_parse(
                    "%s^2^{tree}" % self.target_branch)),
                "--finish option failed to merge correctly")

        # allow additional test specific verification methods below
        extra_test_func = getattr(self, '_verify_%s' % self.name, None)
        if extra_test_func:
            extra_test_func()

    def _check_tree_state(self):

        expected = getattr(self, 'expect_found', None)
        # even if empty want to confirm that find no changes applied,
        # otherwise confirm we find the expected number of changes.
        if expected is not None:
            if len(list(Commit.new(self.repo,
                                   self.target_branch).parents)) > 1:
                changes = list(Commit.iter_items(
                    self.repo,
                    '%s..%s^2' % (self.upstream_branch, self.target_branch),
                    topo_order=True))
            else:
                # allow checking that nothing was rebased
                changes = []
            self.assertThat(
                len(changes), Equals(len(expected)),
                "should only have seen %s changes, got: %s" %
                (len(expected),
                 ", ".join(["%s:%s" % (commit.hexsha,
                                       commit.message.splitlines()[0])
                           for commit in changes])))

            # expected should be listed in order from oldest to newest, so
            # reverse changes to match as it would be newest to oldest.
            changes.reverse()
            for commit, node in zip(changes, expected):
                if node == "MERGE":
                    continue
                subject = commit.message.splitlines()[0]
                node_subject = self.gittree.graph[node].message.splitlines()[0]
                self.assertThat(subject, Equals(node_subject),
                                "subject '%s' of commit '%s' does not match "
                                "subject '%s' of node '%s'" % (
                                    subject, commit.hexsha, node_subject,
                                    node))
