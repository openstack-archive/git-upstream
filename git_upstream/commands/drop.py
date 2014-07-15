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

from git_upstream.errors import GitUpstreamError
from git_upstream.log import LogDedentMixin
from git_upstream.lib.utils import GitMixin
from git_upstream import subcommand, log

from git import BadObject

import inspect
import re


class DropError(GitUpstreamError):
    """Exception thrown by L{Drop}"""
    pass


class Drop(LogDedentMixin, GitMixin):
    """Mark a commit to be dropped on next import.

    Mark a commit as to be dropped.

    The mark is applied by means of a note in upstream-merge namespace
    (refs/notes/upstream-merge).

    The note will contain the following header:

    Dropped: Walter White <heisenberg@hp.com>

    """
    DROP_HEADER = 'Dropped:'
    NOTE_REF = 'refs/notes/upstream-merge'

    def __init__(self, git_object=None, author=None, *args, **kwargs):

        # make sure to correctly initialize inherited objects before performing
        # any computation
        super(Drop, self).__init__(*args, **kwargs)

        # test parameters
        if not git_object:
            raise DropError("Commit should be provided")

        try:
            # test commit "id" presence
            self._commit = self.repo.commit(git_object)
        except BadObject:
            raise DropError(
                "Commit '%s' not found (or ambiguous)" % git_object)

        if not author:
            self._author = '%s <%s>' % (self.repo.git.config('user.name'),
                                        self.repo.git.config('user.email'))
        else:
            self._author = author

        # test that we can use this git repo
        if not self.is_detached():
            raise DropError("In 'detached HEAD' state")

        # To Do: check if it possible and useful.
        if self.repo.bare:
            raise DropError("Cannot add notes in bare repositories")

    @property
    def commit(self):
        """Commit to be marked as dropped."""
        return self._commit

    @property
    def author(self):
        """Commit to be marked as dropped."""
        return self._author

    def check_duplicates(self):
        """Check if a dropped header is already present"""
        note = self.commit.note(note_ref=Drop.NOTE_REF)
        if note:
            pattern = '^%s\s*(.+)' % Drop.DROP_HEADER
            m = re.search(pattern, note, re.MULTILINE | re.IGNORECASE)
            if m:
                self.log.warning(
                    """Drop header already present in the note for commit '%s':
                       %s""" % (self.commit, m.group(1)))
                return False
        return True

    def mark(self):
        """
        Create the note for the given commit with the given change-ids.
        """
        self.log.debug("Creating a note for commit '%s'", self.commit)

        if self.check_duplicates():
            git_note = '%s %s\n' % (Drop.DROP_HEADER, self.author)
            self.log.debug('With the following content:')
            self.log.debug(git_note)
            self.commit.append_note(git_note, note_ref=Drop.NOTE_REF)
        else:
            self.log.warning(
                "Drop note has not been added as '%s' already has one" %
                self.commit)


@subcommand.arg('commit', metavar='<commit>', nargs=None,
                help='Commit to be marked as dropped')
@subcommand.arg('-a', '--author', metavar='<author>',
                dest='author',
                default=None,
                help='Git author for the mark')
def do_drop(args):
    """
    Mark a commit as dropped.
    Marked commits will be skipped during the upstream rebasing process.
    See also the "git upstream import" command.
    """

    logger = log.get_logger('%s.%s' % (__name__,
                                       inspect.stack()[0][0].f_code.co_name))

    drop = Drop(git_object=args.commit, author=args.author)

    if drop.mark():
        logger.notice("Drop mark created successfully")

# vim:sw=4:sts=4:ts=4:et:
