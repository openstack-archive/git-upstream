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

import re

from git import BadObject

from git_upstream.errors import GitUpstreamError
from git_upstream import lib
from git_upstream.lib.pygitcompat import BadName
from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin


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
        except (BadName, BadObject):
            raise DropError(
                "Commit '%s' not found (or ambiguous)" % git_object)

        if not author:
            self._author = '%s <%s>' % (self.repo.git.config('user.name'),
                                        self.repo.git.config('user.email'))
        else:
            self._author = author

        # test that we can use this git repo
        if self.is_detached():
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
        note = self.commit.note(note_ref=lib.IMPORT_NOTE_REF)
        if note:
            pattern = '^%s\s*(.+)' % lib.DROP_HEADER
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
            git_note = '%s %s\n' % (lib.DROP_HEADER, self.author)
            self.log.debug('With the following content:')
            self.log.debug(git_note)
            self.commit.append_note(git_note, note_ref=lib.IMPORT_NOTE_REF)
        else:
            self.log.warning(
                "Drop note has not been added as '%s' already has one" %
                self.commit)
