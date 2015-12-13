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
from git_upstream.lib.supersede import Supersede
from git_upstream.log import LogDedentMixin


class SupersedeCommand(LogDedentMixin, GitUpstreamCommand):
    """Mark a commit as superseded by a set of change-ids.

    Marked commits will be skipped during the upstream rebasing process.
    See also the "git upstream import" command.
    """
    name = "supersede"

    def __init__(self, *args, **kwargs):

        # make sure to correctly initialize inherited objects before performing
        # any computation
        super(SupersedeCommand, self).__init__(*args, **kwargs)

        self.parser.add_argument(
            'commit', metavar='<commit>', nargs=None,
            help='Commit to be marked as superseded')
        self.parser.add_argument(
            'change_ids', metavar='<change id>', nargs='+',
            help='Change id which makes <commit> obsolete. The change id must '
                 'be present in <upstream-branch> to drop <commit>. If more '
                 'than one change id is specified, all must be present in '
                 '<upstream-branch> to drop <commit>')
        self.parser.add_argument(
            '-f', '--force', dest='force', required=False, action='store_true',
            default=False,
            help='Apply the commit mark even if one or more change ids could '
                 'not be found. Use this flag carefully as commits will not '
                 'be dropped during import command execution as long as all '
                 'associated change ids are present in the local copy of the '
                 'upstream branch')
        self.parser.add_argument(
            '-u', '--upstream-branch', metavar='<upstream-branch>',
            dest='upstream_branch', required=False, default='upstream/master',
            help='Search change ids values in <upstream-branch> branch '
                 '(default: %(default)s)')

    def execute(self):

        supersede = Supersede(git_object=self.args.commit,
                              change_ids=self.args.change_ids,
                              upstream_branch=self.args.upstream_branch,
                              force=self.args.force)

        if supersede.mark():
            self.logger.notice("Supersede mark created successfully")

# vim:sw=4:sts=4:ts=4:et:
