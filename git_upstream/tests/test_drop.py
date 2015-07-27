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

"""Tests the drop module"""

from git import GitCommandError

from git_upstream.lib.drop import Drop
from git_upstream.lib.drop import DropError
from git_upstream.tests import base


class TestDrop(base.BaseTestCase):
    """Test case for Drop class"""

    invalid_commit = "this_is_an_invalid_commit"
    author = "Walter White <heisenberg@hp.com>"
    note_ref = 'refs/notes/upstream-merge'

    def setUp(self):
        super(TestDrop, self).setUp()
        self.first_commit = self.repo.commit()

    def test_valid_parameters(self):
        """Test drop initialization and read properties"""

        automatic_author = '%s <%s>' % (self.repo.git.config('user.name'),
                                        self.repo.git.config('user.email'))
        t = Drop(git_object=self.first_commit)
        self.assertEqual(t.author, automatic_author)

        t = Drop(git_object=self.first_commit, author=self.author)
        self.assertEqual(t.author, self.author)

    def test_invalid_commit(self):
        """Test drop initialization with invalid commit"""

        self.assertRaises(DropError, Drop,
                          git_object=self.invalid_commit)

    def test_mark(self):
        """Test drop mark"""

        t = Drop(git_object=self.first_commit, author=self.author)

        try:
            # Older git versions don't support --ignore-missing so we need to
            # catch GitCommandError exception
            self.repo.git.notes('--ref', self.note_ref, 'remove',
                                self.first_commit)
        except GitCommandError:
            pass

        t.mark()

        self.assertRegexpMatches(
            '^Dropped: %s' % self.author,
            self.repo.git.notes('--ref', self.note_ref, 'show',
                                self.first_commit)
        )

        self.repo.git.notes('--ref', self.note_ref, 'remove',
                            self.first_commit)
