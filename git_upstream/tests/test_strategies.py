#
# Copyright (c) 2014 Hewlett-Packard Development Company, L.P.
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

from base import BaseTestCase

import_command = __import__("git_upstream.commands.import", globals(),
                            locals(), ['LocateChangesWalk'], -1)
LocateChangesWalk = import_command.LocateChangesWalk


class TestStrategies(BaseTestCase):

    def _verify_expected(self, tree, branches, expected_nodes):
        self._build_git_tree(tree, branches.values())

        strategy = LocateChangesWalk(branch=branches['head'][0],
                                     search_refs=[branches['upstream'][0]])

        self.assertEquals(self._commits_from_nodes(expected_nodes),
                          [c for c in strategy.filtered_iter()])

    def test_locate_changes_walk_basic(self):
        """Construct a basic repo layout and validate that locate changes
        walker can find the expected changes.

        Repository layout being tested

          B           master
         /
        A---C---D     upstream/master

        """
        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['A']),
            ('D', ['C'])
        ]

        branches = {
            'head': ('master', 'B'),
            'upstream': ('upstream/master', 'D'),
        }

        expected_changes = ["B"]
        self._verify_expected(tree, branches, expected_changes)

    def test_locate_changes_walk_additional_branch(self):
        """Construct a repo layout where previously an additional branch has
        been included and validate that locate changes walker can find the
        expected changes

        Repository layout being tested

        B             example/packaging
         \
          C---D---E   master
         /
        A---F---G     upstream/master

        """
        tree = [
            ('A', []),
            ('B', []),
            ('C', ['A', 'B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['A']),
            ('G', ['F'])
        ]

        branches = {
            'head': ('master', 'E'),
            'upstream': ('upstream/master', 'G'),
        }

        expected_changes = ["D", "E"]
        self._verify_expected(tree, branches, expected_changes)

    def test_locate_changes_walk_additional_branch_multiple_imports(self):
        """Construct a repo layout where previously an additional branch has
        been included and validate that locate changes walker can find the
        right changes after an additional import

        Repository layout being tested

          B--                               example/packaging
           \ \
            C---D---E-------I---J---K       master
           /   \           /
          /     --H---D1--E1                import/next
         /       /
        A---F---G---L---M                   upstream/master

        """
        tree = [
            ('A', []),
            ('B', []),
            ('C', ['A', 'B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['A']),
            ('G', ['F']),
            ('H', ['G', 'B']),
            ('D1', ['H']),
            ('E1', ['D1']),
            ('I', ['E', '=E1']),
            ('J', ['I']),
            ('K', ['J']),
            ('L', ['G']),
            ('M', ['L'])
        ]

        branches = {
            'head': ('master', 'K'),
            'upstream': ('upstream/master', 'M'),
        }

        expected_changes = ["D1", "E1", "J", "K"]
        self._verify_expected(tree, branches, expected_changes)

    def test_locate_changes_walk_changes_prior_to_import(self):
        """Construct a repo layout where using a complex layout involving
        additional branches having been included, and a previous import from
        upstream having been completed, test that if a change was created on
        another branch before the previous import was created, and merged to
        the target branch after the previous import, can we find it correctly.
        i.e. will the strategy also include commit 'O' in the diagram below.

        Repository layout being tested

        B--                                     example/packaging
         \ \
          \ \         O----------------
           \ \       /                 \
            C---D---E-------I---J---K---P---Q   master
           /   \           /
          /     --H---D1--E1                    import/next
         /       /
        A---F---G---L---M                       upstream/master

        """

        tree = [
            ('A', []),
            ('B', []),
            ('C', ['A', 'B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['A']),
            ('G', ['F']),
            ('H', ['G', 'B']),
            ('D1', ['H']),
            ('E1', ['D1']),
            ('I', ['E', '=E1']),
            ('J', ['I']),
            ('K', ['J']),
            ('L', ['G']),
            ('M', ['L']),
            ('O', ['E']),
            ('P', ['K', 'O']),
            ('Q', ['P'])
        ]

        branches = {
            'head': ('master', 'Q'),
            'upstream': ('upstream/master', 'M'),
        }

        expected_changes = ["D1", "E1", "J", "K", "O", "Q"]
        self._verify_expected(tree, branches, expected_changes)
