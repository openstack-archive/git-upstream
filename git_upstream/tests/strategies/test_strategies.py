#
# Copyright (c) 2014-2016 Hewlett-Packard Enterprise Development Company, L.P.
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
#

import os
from pprint import pformat

from testscenarios import TestWithScenarios
from testtools.content import text_content

from git_upstream.tests.base import BaseTestCase
from git_upstream.tests.base import get_scenarios

import_command = __import__("git_upstream.commands.import", globals(),
                            locals(), ['LocateChangesWalk'])
LocateChangesWalk = import_command.LocateChangesWalk


class TestStrategies(TestWithScenarios, BaseTestCase):

    scenarios = get_scenarios(os.path.join(os.path.dirname(__file__),
                              "scenarios"))

    def setUp(self):
        # add description in case parent setup fails.
        self.addDetail('description', text_content(self.desc))

        # builds the tree to be tested
        super(TestStrategies, self).setUp()

        # need the tree built at this point
        self.addDetail('expected-changes',
                       text_content(pformat(
                           list((c, self.gittree.graph[c].hexsha)
                                for c in self.expected_changes))))

    def test_search_changes(self):

        strategy = LocateChangesWalk(
            branch=self.branches['head'][0],
            search_refs=[self.branches['upstream'][0]])

        self.assertEqual(
            self.gittree._commits_from_nodes(self.expected_changes),
            [c for c in strategy.filtered_iter()])
