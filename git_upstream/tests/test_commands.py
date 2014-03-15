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

"""Tests for the 'commands' module"""

import testtools
from argparse import ArgumentParser

from git_upstream import commands as c


class TestGetSubcommands(testtools.TestCase):
    """Test case for get_subcommands function"""

    _available_subcommands = ('import', 'supersede', 'drop')

    def test_available_subcommands(self):
        """Test available subcommands"""
        parser = ArgumentParser()
        subparsers = parser.add_subparsers()
        subcommands = c.get_subcommands(subparsers)
        self.assertEqual(len(TestGetSubcommands._available_subcommands),
                         len(subcommands.keys()))
        for command in subcommands.keys():
            self.assertIn(command, TestGetSubcommands._available_subcommands)
