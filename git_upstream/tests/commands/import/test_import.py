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

from git_upstream.lib.pygitcompat import Commit
from git_upstream import main
from git_upstream.tests.base import BaseTestCase
from git_upstream.tests.base import get_scenarios


class TestImportCommand(TestWithScenarios, BaseTestCase):

    commands, parser = main.build_parsers()
    scenarios = get_scenarios(os.path.join(os.path.dirname(__file__),
                              "scenarios"))

    def setUp(self):
        # add description in case parent setup fails.
        self.addDetail('description', text_content(self.desc))

        # builds the tree to be tested
        super(TestImportCommand, self).setUp()

    def test_command(self):
        upstream_branch = self.branches['upstream'][0]
        target_branch = self.branches['head'][0]

        self.git.tag(inspect.currentframe().f_code.co_name, upstream_branch)
        args = self.parser.parse_args(self.parser_args)
        self.assertThat(args.cmd.run(args), Equals(True),
                        "import command failed to complete successfully")

        expected = getattr(self, 'expect_rebased', [])
        if expected:
            changes = list(Commit.iter_items(
                self.repo, '%s..%s^2' % (upstream_branch, target_branch)))
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
                subject = commit.message.splitlines()[0]
                node_subject = self._graph[node].message.splitlines()[0]
                self.assertThat(subject, Equals(node_subject),
                                "subject '%s' of commit '%s' does not match "
                                "subject '%s' of node '%s'" % (
                                    subject, commit.hexsha, node_subject,
                                    node))

        # allow additional test specific verification methods below
        extra_test_func = getattr(self, '_verify_%s' % self.name, None)
        if extra_test_func:
            extra_test_func()

    def _verify_basic_additional_missed(self):
        """Additional verification that test produces a warning"""

        self.assertThat(self.logger.output,
                        Contains("Previous import merged additional"))

    def _verify_import_finish(self):
        """Additional verification for the finished results"""

        self.assertThat(self.repo.git.rev_parse('master^{tree}'),
                        Equals(self.repo.git.rev_parse('import/F^{tree}')),
                        "--finish option failed to merge correctly")
        commit = self.git.rev_list('master', parents=True, max_count=1).split()
        parents = commit[1:]
        self.assertThat(parents, Equals([self._graph['D'].hexsha,
                                         self._graph['D1'].hexsha]),
                        "import --finish merge does contain the correct "
                        "parents")
