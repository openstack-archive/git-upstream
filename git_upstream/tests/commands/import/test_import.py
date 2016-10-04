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
                              "scenarios"))

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
        self.assertThat(args.cmd.run(args), Equals(True),
                        "import command failed to complete successfully")

        # assuming non-interactive we should *NOT* see the following message
        # appear in the logged output.
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

            # make sure the final state of merge is correct
            self.assertThat(
                self.repo.git.rev_parse("%s^{tree}" % self.target_branch),
                Equals(self.repo.git.rev_parse(
                    "%s^2^{tree}" % self.target_branch)),
                "--finish option failed to merge correctly")

        # allow additional test specific verification methods below
        extra_test_func = getattr(self, '_verify_%s' % self.name, None)
        if extra_test_func:
            extra_test_func()

    def test_command_with_sha1s(self):
        # convert branches/tags to sha1s and use sha1 instead of branch
        parser_args = [
            arg if (arg.startswith('-') or arg in ("import",))
            else self.git.rev_parse(arg)
            for arg in self.parser_args
        ]
        args = self.parser.parse_args(parser_args)
        self.assertThat(args.cmd.run(args), Equals(True),
                        "import command failed to complete successfully")

        self._check_tree_state()

    def test_command_with_tags(self):
        # add tag for each branch/ref and test with added tag
        parser_args = []
        for arg in self.parser_args:
            if (arg.startswith('-') or arg in ("import",)):
                parser_args.append(arg)
                continue

            tag_name = "tag-gu-%s" % arg.replace('~', '-')
            self.git.tag(tag_name, arg)
            parser_args.append(tag_name)

        args = self.parser.parse_args(parser_args)
        self.assertThat(args.cmd.run(args), Equals(True),
                        "import command failed to complete successfully")

        self._check_tree_state()

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

    def _verify_basic(self):

        self.assertThat(self.git.log(n=1), Contains("Merge branch 'import/"))
        # check we report to the user about the import branch created
        self.assertThat(
            self.logger.output,
            Contains("Created import branch 'import/"))

    def _verify_basic_additional_missed(self):
        """Additional verification that test produces a warning"""

        self.assertThat(self.logger.output,
                        Contains("Previous import merged additional"))

    def _verify_import_finish(self):
        """Additional verification for the finished results"""

        commit = self.git.rev_list('master', parents=True, max_count=1).split()
        parents = commit[1:]
        self.assertThat(parents, Equals([self.gittree.graph['D'].hexsha,
                                         self.gittree.graph['D1'].hexsha]),
                        "import --finish merge does contain the correct "
                        "parents")

    def _verify_import_same_as_previous_upstream(self):
        """Additional verification for the finished results"""
        self.assertThat(
            self.logger.output,
            Contains("already at latest upstream commit"))
        self.assertThat(
            self.logger.output,
            Contains("Nothing to be imported"))

    def _verify_same_previous_with_same_additional(self):
        """Additional verification for the finished results"""

        self.assertThat(
            self.logger.output,
            Contains("already at latest upstream commit"))
        self.assertThat(
            self.logger.output,
            Contains("No updated additional branch given, nothing to be done"))

    def _verify_import_everything_already_upstreamed(self):
        """Additional verification for the finished results"""

        self.assertThat(
            self.logger.output,
            Contains("All carried changes gone upstream"))
        self.assertThat(
            self.logger.output,
            Contains("Creating  branch 'import/test_command' from specified "
                     "commit 'upstream/master'"))
