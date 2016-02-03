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
from git import Head

from git_upstream.errors import GitUpstreamError
from git_upstream import lib
from git_upstream.lib.pygitcompat import BadName
from git_upstream.lib.searchers import CommitMessageSearcher
from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin


class SupersedeError(GitUpstreamError):
    """Exception thrown by L{Supersede}"""
    pass


class Supersede(LogDedentMixin, GitMixin):
    """
    Mark a commit as superseded.

    The mark is applied by means of a note in upstream-merge namespace
    (refs/notes/upstream-merge).

    The note will contain one or more of the following headers:

    Superseded-by: I82ef79c3621dacf619a02404f16464877a06f158

    """

    CHANGE_ID_REGEX = '^I[0-9a-f]{6,40}$'
    CHANGE_ID_HEADER_REGEX_FMT = '^Change-Id:\s*%s'
    CHANGE_ID_HEADER_REGEX = '^Change-Id:\s*(I[0-9a-f]{6,40})$'

    def __init__(self, git_object=None, change_ids=list(),
                 upstream_branch=None, force=False, *args, **kwargs):

        # make sure to correctly initialize inherited objects before performing
        # any computation
        super(Supersede, self).__init__(*args, **kwargs)

        # test commit parameter
        if not git_object:
            raise SupersedeError("Commit should be provided")

        # test that we can use this git repo
        if self.is_detached():
            raise SupersedeError("In 'detached HEAD' state")

        # To Do: check if it possible and useful.
        if self.repo.bare:
            raise SupersedeError("Cannot add notes in bare repositories")

        if not upstream_branch:
            raise SupersedeError("Missing upstream_branch parameter")

        try:
            # test commit "id" presence
            self._commit = self.repo.commit(git_object)
        except (BadName, BadObject):
            raise SupersedeError("Commit '%s' not found (or ambiguous)" %
                                 git_object)

        # test change_ids parameter
        if len(change_ids) == 0:
            raise SupersedeError("At least one change id should be provided")

        self._upstream_branch = upstream_branch
        self._change_ids = change_ids
        git_branch = Head(self.repo, 'refs/heads/%s' % upstream_branch)
        for change_id in change_ids:
            # Check change id format
            if not re.match(Supersede.CHANGE_ID_REGEX, change_id,
                            re.IGNORECASE):
                raise SupersedeError("Invalid Change Id '%s'" % change_id)

            # Check if change id is actually present in some commit
            # reachable from <upstream_branch>
            try:
                change_commit = CommitMessageSearcher(
                    repo=self.repo, branch=git_branch,
                    pattern=Supersede.CHANGE_ID_HEADER_REGEX_FMT %
                    change_id).find()

                self.log.debug("Change-id '%s' found in commit '%s'" %
                               (change_id, change_commit))

            except RuntimeError:
                if force:
                    self.log.warn("Warning: change-id '%s' not found in '%s'" %
                                  (change_id, upstream_branch))
                else:
                    raise SupersedeError(
                        "Change-Id '%s' not found in branch '%s'" %
                        (change_id, upstream_branch))

    @property
    def commit(self):
        """Commit to be marked as superseded."""
        return self._commit

    @property
    def change_ids(self):
        """Change ids that make a commit obsolete."""
        return self._change_ids

    @property
    def change_ids_branch(self):
        """Branch to search for change ids"""
        return self._upstream_branch

    def check_duplicates(self):
        """
        Check if a supersede header is already present in the note containing
        one of change ids passed on the command line
        """
        new_note = self.commit.note(note_ref=lib.IMPORT_NOTE_REF)
        if new_note:
            pattern = '^%s\s?(%s)$' % (lib.SUPERSEDE_HEADER,
                                       '|'.join(self.change_ids))
            m = re.search(pattern, new_note, re.MULTILINE | re.IGNORECASE)
            if m:
                self.log.warning(
                    ("Change-Id '%s' already present in the note for commit" +
                     " '%s'") % (m.group(1), self.commit))
                return False
        return True

    def mark(self):
        """Create the note for the given commit with the given change-ids."""
        self.log.debug("Creating a note for commit '%s'", self.commit)

        if self.check_duplicates():
            git_note = ''
            for change_id in self.change_ids:
                git_note += '%s %s\n' % (lib.SUPERSEDE_HEADER, change_id)
            self.log.debug('With the following content:')
            self.log.debug(git_note)
            self.commit.append_note(git_note, note_ref=lib.IMPORT_NOTE_REF)
        else:
            self.log.warning('Note has not been added')
