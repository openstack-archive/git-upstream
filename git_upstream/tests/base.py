# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os
import tempfile

import fixtures
import git
import testtools


LOREM_IPSUM = """\
Lorem ipsum dolor sit amet, consectetuer adipiscing elit, sed diam nonummy
nibh euismod tincidunt ut laoreet dolore magna aliquam erat volutpat. Ut wisi
enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit lobortis
nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure dolor in
hendrerit in vulputate velit esse molestie consequat, vel illum dolore eu
feugiat nulla facilisis at vero eros et accumsan et iusto odio dignissim qui
blandit praesent luptatum zzril delenit augue duis dolore te feugait nulla
facilisi.

Ut wisi enim ad minim veniam, quis nostrud exerci tation ullamcorper suscipit
lobortis nisl ut aliquip ex ea commodo consequat. Duis autem vel eum iriure
dolor in hendrerit in vulputate velit esse molestie consequat, vel illum
dolore eu feugiat nulla facilisis at vero eros et accumsan et iusto odio
dignissim qui blandit praesent luptatum zzril delenit augue duis dolore te
feugait nulla facilisi. Lorem ipsum dolor sit amet, consectetuer adipiscing
elit, sed diam nonummy nibh euismod tincidunt ut laoreet dolore magna aliquam
erat volutpat.

Duis autem vel eum iriure dolor in hendrerit in vulputate velit esse molestie
consequat, vel illum dolore eu feugiat nulla facilisis at vero eros et
accumsan et iusto odio dignissim qui blandit praesent luptatum zzril delenit
augue duis dolore te feugait nulla facilisi. Lorem ipsum dolor sit amet,
consectetuer adipiscing elit, sed diam nonummy nibh euismod tincidunt ut
laoreet dolore magna aliquam erat volutpat. Ut wisi enim ad minim veniam, quis
nostrud exerci tation ullamcorper suscipit lobortis nisl ut aliquip ex ea
commodo consequat."""


class DiveDir(fixtures.Fixture):
    """Dive into given directory and return back on cleanup.

    :ivar path: The target directory.
    """

    def __init__(self, path):
        self.path = path

    def setUp(self):
        super(DiveDir, self).setUp()
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.path)


class GitRepo(fixtures.Fixture):
    """Create an empty git repo in which to operate."""

    def __init__(self):
        self.repo = None
        self.path = ''
        self._file_list = set()

    def setUp(self):
        super(GitRepo, self).setUp()
        tempdir = fixtures.TempDir()
        self.addCleanup(tempdir.cleanUp)
        tempdir.setUp()
        self.path = os.path.join(tempdir.path, 'git')
        os.mkdir(self.path)
        g = git.Git(self.path)
        g.init()
        self.repo = git.Repo(self.path)
        self.repo.git.config('user.email', 'user@example.com')
        self.repo.git.config('user.name', 'Example User')
        self._create_file_commit()

    def _create_file(self, contents=None):
        if not contents:
            contents = LOREM_IPSUM

        # always want to ensure the files added to the repo are unique no
        # matter which branch they are added to, as otherwise there may
        # be conflicts caused by replaying local changes and performing
        # merges
        while True:
            tmpfile = tempfile.NamedTemporaryFile(dir=self.repo.working_dir,
                                                  delete=False)
            if tmpfile.name not in self._file_list:
                self._file_list.add(tmpfile.name)
                break
            tmpfile.close()
            os.remote(tmpfile.name)
        tmpfile.write(contents)
        tmpfile.close()
        return tmpfile.name

    def _create_file_commit(self, change_id=None):
        filename = self._create_file()
        self.repo.git.add(filename)
        message = "Adding %s" % os.path.basename(filename)
        if change_id:
            message = message + "\n\nChange-Id: %s" % change_id
        self.repo.git.commit(m=message)

    def add_commits(self, num=1, ref="HEAD", change_ids=None):
        """Create the given number of commits using generated files"""
        if ref != "HEAD":
            self.repo.git.checkout(ref)

        num = max(num, len(change_ids))
        ids = list(change_ids) + [None] * (num - len(change_ids))

        for x in range(num):
            self._create_file_commit(ids[x])


class BaseTestCase(testtools.TestCase):
    """Base Test Case for all tests."""

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.testrepo = self.useFixture(GitRepo())
        repo_path = self.testrepo.path
        self.useFixture(DiveDir(repo_path))
        self.repo = self.testrepo.repo
