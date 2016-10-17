#
# Copyright (c) 2012-2015 Hewlett-Packard Development Company, L.P.
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

from git_upstream.commands import GitUpstreamCommand
from git_upstream.log import LogDedentMixin


class HelpCommand(LogDedentMixin, GitUpstreamCommand):
    """Display help about this program or one of its commands."""
    name = "help"

    def __init__(self, *args, **kwargs):
        super(HelpCommand, self).__init__(*args, **kwargs)

        self.parser.add_argument('command', metavar='<command>', nargs='?',
                                 help="command to display help about")

    def execute(self):
        if getattr(self.args, 'command', None):
            if self.args.command in self.args.subcommands:
                self.args.subcommands[self.args.command].print_help()
            else:
                self.parser.error("'%s' is not a valid subcommand" %
                                  self.args.command)
        else:
            self.args.parent_parser.print_help()
