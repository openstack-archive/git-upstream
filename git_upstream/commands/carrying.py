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
from git_upstream.lib.carrying import Carrying
from git_upstream.log import LogDedentMixin


class CarryingCommand(LogDedentMixin, GitUpstreamCommand):
    """Show list of commits carried that are not upstream.

    See also the "git log" command.
    """
    name = "carrying"

    def __init__(self, *args, **kwargs):
        # make sure to correctly initialize inherited objects before performing
        # any computation
        super(CarryingCommand, self).__init__(*args, **kwargs)

        self.parser.add_argument(
            'upstream_branch', metavar='<upstream-branch>', nargs='?',
            default='upstream/master',
            help='Upstream branch to compare against.')

    def execute(self):
        carrying = Carrying(self.args.upstream_branch, *self.unknownargs)

# vim:sw=4:sts=4:ts=4:et:
