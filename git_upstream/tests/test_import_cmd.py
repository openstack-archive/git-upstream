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
        with mock.patch('git_upstream.log.get_logger', return_value=mock_logger):
            self.assertThat(args.func(args), Equals(True),
                            "import command failed to complete succesfully")

        mock_logger.warning.assert_called_with(
            SubstringMatcher(
                containing="Previous import merged additional"))
