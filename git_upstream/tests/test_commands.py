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

from argparse import ArgumentParser
import os
import subprocess
import tempfile

import mock
import testtools
from testtools import content
from testtools import matchers

from git_upstream import commands as c
from git_upstream import main
from git_upstream.tests import base


class TestGetSubcommands(testtools.TestCase):
    """Test case for get_subcommands function"""

    _available_subcommands = ('help', 'import', 'supersede', 'drop')

    def test_available_subcommands(self):
        """Test available subcommands"""
        parser = ArgumentParser()
        subcommands = c.get_subcommands(parser)
        self.assertEqual(len(TestGetSubcommands._available_subcommands),
                         len(subcommands.keys()))
        for command in subcommands.keys():
            self.assertIn(command, TestGetSubcommands._available_subcommands)


class TestMainParser(testtools.TestCase):
    """Test cases for main parser"""

    def test_logging_options_kept(self):

        argv = ["-v", "--log-level", "debug", "import"]
        with mock.patch(
                'git_upstream.commands.GitUpstreamCommand.run') as mock_import:
            main.main(argv)
            self.assertThat(mock_import.call_args[0][0].script_cmdline[2:],
                            matchers.Equals(argv[:3]))


class TestLoggingOptions(base.BaseTestCase):
    """Test cases for logging options behaviour"""

    def setUp(self):
        _, self.parser = main.build_parsers()

        script_cmdline = self.parser.get_default('script_cmdline')
        script_cmdline[-1] = os.path.join(os.getcwd(), main.__file__)
        self.parser.set_defaults(script_cmdline=script_cmdline)

        # builds the tree to be tested
        super(TestLoggingOptions, self).setUp()

    def test_logfile_contains_finish(self):
        """Confirm that logger calls in 'finish' phase recorded

        Repository layout being checked

          B---C             local/master
         /
        A---D---E           upstream/master

        """
        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['A']),
            ('E', ['D']),
        ]

        branches = {
            'head': ('master', 'C'),
            'upstream': ('upstream/master', 'E'),
        }

        self.gittree = base.BuildTree(self.testrepo, tree, branches.values())

        cmdline = self.parser.get_default('script_cmdline')

        tfile = None
        try:
            tfile = tempfile.NamedTemporaryFile(delete=False)
            # need to close to allow reopen to write
            tfile.close()

            cmdline.extend(['-v', '--log-file', tfile.name, '--log-level',
                            'debug', 'import', '--into', 'master',
                            'upstream/master'])
            try:
                output = subprocess.check_output(cmdline,
                                                 stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as cpe:
                self.addDetail(
                    'subprocess-output',
                    content.text_content(cpe.output.decode('utf-8')))
                raise
            self.addDetail(
                'subprocess-output',
                content.text_content(output.decode('utf-8')))

            logfile_contents = open(tfile.name, 'r').read()
        finally:
            if tfile and os.path.exists(tfile.name):
                os.remove(tfile.name)

        self.assertThat(
            logfile_contents,
            matchers.Contains("Merging by inverting the 'ours' strategy"))
        self.assertThat(
            logfile_contents,
            matchers.Contains("Replacing tree contents with those from"))
