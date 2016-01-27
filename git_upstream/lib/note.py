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

from git import GitCommandError

from git_upstream.errors import GitUpstreamError


class NoteAlreadyExistsError(GitUpstreamError):
    """Exception thrown by note related commands"""
    pass


def add_note(self, message, force=False, note_ref='refs/notes/commits'):
    """
    Add a note to an object, tossing a NoteError exception if the object is
    already annotated.
    :param message:     note message
    :param force:       if true, any existing note will be overwritten
    :param note_ref:    ref to use for notes. Defaults to refs/notes/commits
    """
    if force:
            self.repo.git.notes('--ref', note_ref, 'add', '-f', '-m', message,
                                str(self))
    else:
        try:
            self.repo.git.notes('--ref', note_ref, 'add', '-m', message,
                                str(self))
        except GitCommandError as e:
            if e.status == 1:
                raise NoteAlreadyExistsError(e.message)
            else:
                raise e


def append_note(self, message, note_ref='refs/notes/commits'):
    """Add a note to an object
    :param message:     note message
    :param note_ref:    ref to use for notes. Defaults to refs/notes/commits
    """
    self.repo.git.notes('--ref', note_ref, 'append', '-m', message, str(self))


def note_message(self, note_ref='refs/notes/commits'):
    """
    Return note message
    :param note_ref:    ref to use for notes. Defaults to refs/notes/commits
    """
    try:
        return self.repo.git.notes('--ref', note_ref, 'show', str(self))
    except GitCommandError as e:
        if e.status == 1:
            return None
        else:
            raise e
