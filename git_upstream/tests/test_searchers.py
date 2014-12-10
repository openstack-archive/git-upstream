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
from git_upstream.lib.searchers import UpstreamMergeBaseSearcher


class TestUpstreamMergeBaseSearcher(BaseTestCase):

    def _verify_expected(self, tree, branches, expected_nodes, pattern=None):
        self._build_git_tree(tree, branches.values())

        if pattern:
            pattern = [pattern]
        searcher = UpstreamMergeBaseSearcher(branch=branches['head'][0],
                                             patterns=pattern, repo=self.repo)

        self.assertEquals(self._commits_from_nodes(reversed(expected_nodes)),
                          searcher.list())

    def test_search_basic(self):
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

    def test_search_additional_branch(self):
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

        expected_changes = ["C", "D", "E"]
        self._verify_expected(tree, branches, expected_changes)

    def test_search_old_style_merge_replace_first(self):
        """Construct a repo layout using an old approach where the mainline
        would be replaced with the upstream and then local changes replayed
        on top. Check to see if we can correctly convert from this approach.

        Repository layout being tested

          B-----------G                     packaging
           \           \
            C---D---E---H--D1--E1           master
           /           /
          /           /
         /           /
        A---F-----------I---J               upstream/master

        """
        tree = [
            ('A', []),
            ('B', []),
            ('C', ['A', 'B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['A']),
            ('G', ['B']),
            ('H', ['E', '=F', '=G']),
            ('D1', ['H']),
            ('E1', ['D1']),
            ('I', ['F']),
            ('J', ['I']),
        ]

        branches = {
            'head': ('master', 'E1'),
            'upstream': ('upstream/master', 'I'),
            'packaging': ('packaging', 'B')
        }

        expected_changes = ["H", "D1", "E1"]
        self._verify_expected(tree, branches, expected_changes)

    def test_search_additional_branch_multiple_imports(self):
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

        expected_changes = ["H", "D1", "E1", "I", "J", "K"]
        self._verify_expected(tree, branches, expected_changes)

    def test_search_changes_upload_prior_to_import(self):
        """Construct a repo layout where using a complex layout involving
        additional branches having been included, and a previous import from
        upstream having been completed, test that if a change was created on
        another branch before the previous import was created, and merged to
        the target branch after the previous import, can we find it correctly.
        i.e. will the strategy also include commit 'O' in the diagram below.

        Repository layout being tested

        B--
         \ \
          \ \         O----------------
           \ \       /                 \
            C---D---E-------I---J---K---P---Q   master
           /   \           /
          /     --H---D1--E1
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

        expected_changes = ["H", "D1", "E1", "I", "J", "K", "O", "P", "Q"]
        self._verify_expected(tree, branches, expected_changes)

    def test_search_multi_changes_upload_prior_to_import(self):
        """Construct a repo layout where using a complex layout involving
        additional branches having been included, and a previous import from
        upstream having been completed, test that if a change was created on
        another branch before the previous import was created, and merged to
        the target branch after the previous import, can we find it correctly.
        i.e. will the strategy also include commit 'O' in the diagram below.

        Repository layout being tested

        B--        L-------------
         \ \      /              \
          \ \    /    J---------  \
           \ \  /    /          \  \
            C---D---E-------I---K---M---O---P   master
           /   \           /
          /     --H---D1--E1
         /       /
        A---F---G---Q---R                       upstream/master

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
            ('J', ['E']),
            ('K', ['I', 'J']),
            ('L', ['D']),
            ('M', ['K', 'L']),
            ('O', ['M']),
            ('P', ['O']),
            ('Q', ['G']),
            ('R', ['Q'])
        ]

        branches = {
            'head': ('master', 'P'),
            'upstream': ('upstream/master', 'R'),
        }

        expected_changes = ["H", "D1", "E1", "I", "J", "K", "L", "M", "O", "P"]
        self._verify_expected(tree, branches, expected_changes)

    def test_search_switch_tracked_branches(self):
        """Search a repository layout where previously was tracking a
        difference branch to the one that the user now wishes to import

        Repository layout being tested

              B-----------J         master
             /           /
            /           B1
           /           /
          /       E---I             upstream/stable
         /       /
        A---C---D---F---G---H       upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['A']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['D']),
            ('G', ['F']),
            ('H', ['G']),
            ('I', ['E']),
            ('B1', ['I']),
            ('J', ['B', '=B1'])
        ]

        branches = {
            'head': ('master', 'J'),
            'stable': ('upstream/stable', 'I'),
            'upstream': ('upstream/master', 'H')
        }

        expected_changes = ['B1', 'J']
        self._verify_expected(tree, branches, expected_changes,
                              pattern="upstream/*")

    def test_search_switch_tracked_branches_incorrect(self):
        """Search a repository layout where previously was tracking a
        difference branch to the one that the user now wishes to import based
        on using the new branch as the basis to search on.

        This shows the additional changes that are picked up by mistake

        Repository layout being tested

              B-----------J         master
             /           /
            /           B1
           /           /
          /       E---I             upstream/stable
         /       /
        A---C---D---F---G---H       upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['A']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['D']),
            ('G', ['F']),
            ('H', ['G']),
            ('I', ['E']),
            ('B1', ['I']),
            ('J', ['B', '=B1'])
        ]

        branches = {
            'head': ('master', 'J'),
            'stable': ('upstream/stable', 'I'),
            'upstream': ('upstream/master', 'H')
        }

        expected_changes = ['E', 'I', 'B1', 'J']
        self._verify_expected(tree, branches, expected_changes,
                              pattern='upstream/master')

    def test_search_changes_approved_after_import_merge(self):
        """Construct a repo layout where using a complex layout involving
        additional branches having been included, and a previous import from
        upstream having been completed, test that if a change was created on
        another branch before the previous import was created, and merged to
        the target branch before the previous import was merged, can we find
        it correctly.
        i.e. will the searcher also include commit 'O' in the diagram below.

        Repository layout being tested

                    O----
                   /     \
              B---C---D---H---I---J---K     master
             /         \     /
            /           ----G
           /               /
          /       B1--C1--D1                import/next
         /       /
        A---E---F---L---M                   upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['C']),
            ('E', ['A']),
            ('F', ['E']),
            ('B1', ['F']),
            ('C1', ['B1']),
            ('D1', ['C1']),
            ('G', ['D', '=D1']),
            ('O', ['C']),
            ('H', ['D', 'O']),
            ('I', ['H', 'G']),
            ('J', ['I']),
            ('K', ['J']),
            ('L', ['F']),
            ('M', ['L'])
        ]

        branches = {
            'head': ('master', 'K'),
            'upstream': ('upstream/master', 'M'),
        }

        expected_changes = ["B1", "C1", "D1", "G", "O", "H", "I", "J", "K"]
        self.expectFailure(
            "Should fail to find change 'O'",
            self._verify_expected, tree, branches, expected_changes)
