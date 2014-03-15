#
# Copyright (c) 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

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
