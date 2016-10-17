# Copyright (c) 2016 Hewlett Packard Enterprise Company, L.P.
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

"""Tests for the 'help' command"""

import os

import mock
import testscenarios
import testtools
from testtools import matchers

from git_upstream import main


class TestHelpCommandExecute(testscenarios.TestWithScenarios,
                             testtools.TestCase):

    scenarios = [
        ('s1', dict(args=['help'],
                    failure="Cannot display basic help")),
        ('s2', dict(args=['help', 'help'],
                    failure="Cannot display help of help")),
        # argparse calls SystemExit with 0 when handling '--help' opts
        # instead of returning to the previous program
        ('s3', dict(args=['help', '--help'],
                    exception=SystemExit, exc_attr='code', exc_value=0,
                    failure="Cannot display help of help")),
        ('s4', dict(args=['help', 'import'],
                    failure="Cannot display help of import")),
        # test exit with error code of 2, indicating user input incorrect
        ('s5', dict(args=['help', 'invalid'],
                    exception=SystemExit, exc_attr='code', exc_value=2,
                    failure="Fail to detect invalid subcommand"))
    ]

    def setUp(self):
        super(TestHelpCommandExecute, self).setUp()
        self.commands, self.parser = main.build_parsers()

        script_cmdline = self.parser.get_default('script_cmdline')
        script_cmdline[-1] = os.path.join(os.getcwd(), main.__file__)
        self.parser.set_defaults(script_cmdline=script_cmdline)

        # must mock out setup_console_logging for any testing of main as it
        # will interfere with fixtures capturing logging in other test threads
        conlog_patcher = mock.patch('git_upstream.main.setup_console_logging')
        conlog_patcher.start()
        self.addCleanup(conlog_patcher.stop)

    def test_command(self):
        """Test that help command runs successfully"""

        with mock.patch.multiple('sys', stdout=mock.DEFAULT,
                                 stderr=mock.DEFAULT):
            if getattr(self, 'exception', None):
                e = self.assertRaises(self.exception, main.main, self.args)
                self.assertThat(getattr(e, self.exc_attr),
                                matchers.Equals(self.exc_value),
                                message=self.failure)
            else:
                self.assertThat(main.main(self.args), matchers.Equals(0),
                                message=self.failure)
