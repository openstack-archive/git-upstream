#
# Copyright (c) 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

"""Tests the drop module"""
import testtools
from git_upstream.commands import drop as d
from git import repo as r
from git import GitCommandError


class TestDrop(testtools.TestCase):
    """Test case for Drop class"""

    first_commit = "bd6b9eefe961abe8c15cb5dc6905b92e14714a4e"
    second_commit = "05fac847a5629e36050dcd69b9a782b2645d3cc7"
    invalid_commit = "this_is_an_invalid_commit"
    author = "Walter White <heisenberg@hp.com>"
    note_ref = 'refs/notes/upstream-merge'

    def test_valid_parameters(self):
        """Test drop initialization and read properties"""

        repo = r.Repo('.')
        automatic_author = '%s <%s>' % (repo.git.config('user.name'),
                                        repo.git.config('user.email'))
        t = d.Drop(git_object=TestDrop.first_commit)
        self.assertEquals(t.author, automatic_author)

        t = d.Drop(git_object=TestDrop.first_commit, author=TestDrop.author)
        self.assertEquals(t.author, TestDrop.author)

    def test_invalid_commit(self):
        """Test drop initialization with invalid commit"""

        self.assertRaises(d.DropError, d.Drop,
                          git_object=TestDrop.invalid_commit)

    def test_mark(self):
        """Test drop mark"""

        t = d.Drop(git_object=TestDrop.first_commit, author=TestDrop.author)

        repo = r.Repo('.')
        try:
            # Older git versions don't support --ignore-missing so we need to
            # catch GitCommandError exception
            repo.git.notes('--ref', TestDrop.note_ref, 'remove',
                           TestDrop.first_commit)
        except GitCommandError:
            pass

        t.mark()

        self.assertRegexpMatches(
            '^Dropped: %s' % TestDrop.author,
            repo.git.notes('--ref', TestDrop.note_ref, 'show',
                           TestDrop.first_commit)
        )

        repo.git.notes('--ref', TestDrop.note_ref, 'remove',
                       TestDrop.first_commit)
