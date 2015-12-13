#
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
#

from git_upstream.commands import GitUpstreamCommand
from git_upstream.lib.drop import Drop
from git_upstream.log import LogDedentMixin


class DropCommand(LogDedentMixin, GitUpstreamCommand):
    """Mark a commit as dropped.

    Marked commits will be skipped during the upstream rebasing process.
    See also the "git upstream import" command.
    """
    name = "drop"

    def __init__(self, *args, **kwargs):
        # make sure to correctly initialize inherited objects before performing
        # any computation
        super(DropCommand, self).__init__(*args, **kwargs)

        self.parser.add_argument(
            'commit', metavar='<commit>', nargs=None,
            help='Commit to be marked as dropped')
        self.parser.add_argument(
            '-a', '--author', metavar='<author>', dest='author', default=None,
            help='Git author for the mark')

    def execute(self):

        drop = Drop(git_object=self.args.commit, author=self.args.author)

        if drop.mark():
            self.log.notice("Drop mark created successfully")

# vim:sw=4:sts=4:ts=4:et:
