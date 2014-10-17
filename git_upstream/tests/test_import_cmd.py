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

import mock
from testtools.matchers import Equals

from git_upstream import main
from git_upstream.lib.pygitcompat import Commit
from git_upstream.tests.base import BaseTestCase

from string import lower


class SubstringMatcher():
    def __init__(self, containing):
        self.containing = lower(containing)

    def __eq__(self, other):
        return lower(other).find(self.containing) > -1

    def __unicode__(self):
        return 'a string containing "%s"' % self.containing

    def __str__(self):
        return unicode(self).encode('utf-8')

    __repr__ = __unicode__


class TestImportCommand(BaseTestCase):

    commands, parser = main.get_parser()

    def test_basic(self):
        """Test that default behaviour and options work

        Repository layout being checked (assumed already replayed)

              C---D               local/master
             /
        A---B---E---F             upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['C']),
            ('E', ['B']),
            ('F', ['E'])
        ]

        branches = {
            'head': ('master', 'D'),
            'upstream': ('upstream/master', 'F')
        }

        self._build_git_tree(tree, branches.values())
        self.git.tag(inspect.currentframe().f_code.co_name, 'upstream/master')
        args = self.parser.parse_args(['-q', 'import', 'upstream/master'])
        self.assertThat(args.func(args), Equals(True),
                        "import command failed to complete succesfully")

    def test_basic_additional(self):
        """Test that default behaviour and options work

        Repository layout being checked (assumed already replayed)

        C---D                     packaging/master
             \
              E---F               local/master
             /
        A---B---G---H             upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', []),
            ('D', ['C']),
            ('E', ['B', 'D']),
            ('F', ['E']),
            ('G', ['B']),
            ('H', ['G'])
        ]

        branches = {
            'head': ('master', 'F'),
            'upstream': ('upstream/master', 'H'),
            'packaging': ('packaging/master', 'D')
        }

        self._build_git_tree(tree, branches.values())
        self.git.tag(inspect.currentframe().f_code.co_name, 'upstream/master')
        args = self.parser.parse_args(['-q', 'import', 'upstream/master',
                                       'packaging/master'])
        self.assertThat(args.func(args), Equals(True),
                        "import command failed to complete succesfully")

    def test_basic_additional_missed(self):
        """Test that forgetting an additional branch that was previously
        included results in a warning to the user.

        Repository layout being checked (assumed already replayed)

        C---D                     packaging/master
             \
              E---F               local/master
             /
        A---B---G---H             upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', []),
            ('D', ['C']),
            ('E', ['B', 'D']),
            ('F', ['E']),
            ('G', ['B']),
            ('H', ['G'])
        ]

        branches = {
            'head': ('master', 'F'),
            'upstream': ('upstream/master', 'H'),
            'packaging': ('packaging/master', 'D')
        }

        self._build_git_tree(tree, branches.values())
        self.git.tag(inspect.currentframe().f_code.co_name, 'upstream/master')
        args = self.parser.parse_args(['import', 'upstream/master'])

        mock_logger = mock.MagicMock()
        with mock.patch('git_upstream.log.get_logger',
                        return_value=mock_logger):
            self.assertThat(args.func(args), Equals(True),
                            "import command failed to complete succesfully")

        mock_logger.warning.assert_called_with(
            SubstringMatcher(
                containing="Previous import merged additional"))

    def test_import_switch_branches_search(self):
        """Test that the import sub-command can correctly switch branches when
        importing from upstream when given a usable search-ref.

        Repository layout being checked (assumed already replayed)

                    E---F         local/master
                   /
              C---D               upstream/stable
             /
        A---B---G---H             upstream/master

        New branch to be tracked will be upstream/master, so the resulting
        commits found should just be E & F.

        Test that result is as follows

                      E---F---I   local/master
                     /       /
                C---D       /     upstream/stable
               /           /
              /       E1--F1
             /       /
        A---B---G---H             upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['E']),
            ('G', ['B']),
            ('H', ['G'])
        ]

        branches = {
            'head': ('master', 'F'),
            'upstream': ('upstream/master', 'H'),
            'stable': ('upstream/stable', 'D')
        }

        self._build_git_tree(tree, branches.values())
        self.git.tag(inspect.currentframe().f_code.co_name, 'upstream/master')
        args = self.parser.parse_args(['-q', 'import'])
        self.assertThat(args.func(args), Equals(True),
                        "import command failed to complete succesfully")
        changes = list(Commit.iter_items(
            self.repo, 'upstream/master..master^2'))
        self.assertThat(len(changes), Equals(2),
                        "should only have seen two changes, got: %s" %
                        ", ".join(["%s:%s" % (commit.hexsha,
                                              commit.message.splitlines()[0])
                                   for commit in changes]))
        for commit, node in zip(changes, ['F', 'E']):
            subject = commit.message.splitlines()[0]
            node_subject = self._graph[node].message.splitlines()[0]
            self.assertThat(subject, Equals(node_subject),
                            "subject '%s' of commit '%s' does not match "
                            "subject '%s' of node '%s'" % (
                                subject, commit.hexsha, node_subject, node))

    def test_import_switch_branches_fails_without_search_ref(self):
        """Test that the import sub-command finds additional changes when
        not given a search-ref to look under.

        Repository layout being checked (assumed already replayed)

                    E---F         local/master
                   /
              C---D               upstream/stable
             /
        A---B---G---H             upstream/master

        New branch to be tracked will be upstream/master, so the resulting
        commits found will be C, D, E & F because of not telling the searcher
        to look under all of the namespace.

        Test that result is as follows

                      E---F-------------I   local/master
                     /                 /
                C---D                 /     upstream/stable
               /                     /
              /       C1---D1---E1--F1
             /       /
        A---B---G---H                       upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['E']),
            ('G', ['B']),
            ('H', ['G'])
        ]

        # use 'custom/*' to ensure defaults are overriden correctly
        branches = {
            'head': ('master', 'F'),
            'upstream': ('custom/master', 'H'),
            'stable': ('custom/stable', 'D')
        }

        self._build_git_tree(tree, branches.values())

        self.git.tag(inspect.currentframe().f_code.co_name, 'custom/master')
        args = self.parser.parse_args(['-q', 'import',
                                       '--into=master', 'custom/master'])
        self.assertThat(args.func(args), Equals(True),
                        "import command failed to complete succesfully")
        changes = list(Commit.iter_items(
            self.repo, 'custom/master..master^2'))
        local_rebased = ['F', 'E', 'D', 'C']
        self.assertThat(len(changes), Equals(len(local_rebased)),
                        "should only have seen two changes, got: %s" %
                        ", ".join(["%s:%s" % (commit.hexsha,
                                              commit.message.splitlines()[0])
                                   for commit in changes]))
        for commit, node in zip(changes, local_rebased):
            subject = commit.message.splitlines()[0]
            node_subject = self._graph[node].message.splitlines()[0]
            self.assertThat(subject, Equals(node_subject),
                            "subject '%s' of commit '%s' does not match "
                            "subject '%s' of node '%s'" % (
                                subject, commit.hexsha, node_subject, node))

    def test_import_switch_branches_search_ref_custom_namespace(self):
        """Test that the import sub-command can correctly switch branches when
        importing from upstream when given a usable search-ref.

        Repository layout being checked (assumed already replayed)

                    E---F         local/master
                   /
              C---D               upstream/stable
             /
        A---B---G---H             upstream/master

        New branch to be tracked will be upstream/master, so the resulting
        commits found should just be E & F.

        Test that result is as follows

                      E---F---I   local/master
                     /       /
                C---D       /     upstream/stable
               /           /
              /       E1--F1
             /       /
        A---B---G---H             upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['C']),
            ('E', ['D']),
            ('F', ['E']),
            ('G', ['B']),
            ('H', ['G'])
        ]

        # use 'custom/*' to ensure defaults are overriden correctly
        branches = {
            'head': ('master', 'F'),
            'upstream': ('custom/master', 'H'),
            'stable': ('custom/stable', 'D')
        }

        self._build_git_tree(tree, branches.values())
        self.git.tag(inspect.currentframe().f_code.co_name, 'custom/master')
        args = self.parser.parse_args(['-q', 'import',
                                       '--search-refs=custom/*',
                                       '--search-refs=custom-d/*',
                                       '--into=master', 'custom/master'])
        self.assertThat(args.func(args), Equals(True),
                        "import command failed to complete succesfully")
        changes = list(Commit.iter_items(
            self.repo, 'custom/master..master^2'))
        self.assertThat(len(changes), Equals(2),
                        "should only have seen two changes, got: %s" %
                        ", ".join(["%s:%s" % (commit.hexsha,
                                              commit.message.splitlines()[0])
                                   for commit in changes]))
        for commit, node in zip(changes, ['F', 'E']):
            subject = commit.message.splitlines()[0]
            node_subject = self._graph[node].message.splitlines()[0]
            self.assertThat(subject, Equals(node_subject),
                            "subject '%s' of commit '%s' does not match "
                            "subject '%s' of node '%s'" % (
                                subject, commit.hexsha, node_subject, node))
