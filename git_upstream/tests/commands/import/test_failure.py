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

"""Tests for the 'import' command failures"""

import inspect
import os

import mock
from six import moves
from testtools import matchers

from git_upstream import main
from git_upstream.tests import base


class TestImportCommandFailure(base.BaseTestCase):

    tree = [
        ["A", []],
        ["B", ["A"]],
        ["C", ["B"]],
        ["D", ["C"]],
        ["E", ["B"]],
        ["F", ["E"]]
    ]

    branches = {
        'head': ["master", "D"],
        'upstream': ["upstream/master", "F"]
    }

    def setUp(self):
        self.commands, self.parser = main.build_parsers()

        script_cmdline = self.parser.get_default('script_cmdline')
        script_cmdline[-1] = os.path.join(os.getcwd(), main.__file__)
        self.parser.set_defaults(script_cmdline=script_cmdline)

        # builds the tree to be tested
        super(TestImportCommandFailure, self).setUp()

        self.upstream_branch = self.branches['upstream'][0]
        self.target_branch = self.branches['head'][0]

    def test_invalid_import_branch(self):
        """Test that a parser error is returned on an invalid import branch

        Checks that if an invalid import branch is passed as an argument
        when trying to use the --finish mode that the command will exit
        with a parser error.
        """
        self.git.tag(inspect.currentframe().f_code.co_name,
                     self.upstream_branch)

        args = self.parser.parse_args(
            ['import', '--finish', '--import-branch', 'invalid',
             'upstream/master'])
        with mock.patch('sys.stderr', new_callable=moves.StringIO) as console:
            self.assertRaises(SystemExit, args.cmd.run, args)
            self.assertThat(
                console.getvalue(),
                matchers.Contains("'invalid' not found!"))
