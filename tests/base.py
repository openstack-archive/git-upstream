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

import git
import fixtures
import testtools


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
    """Create a copy git repo in which to operate."""

    def __init__(self, repo):
        self.repo = repo
        self.path = ''

    def setUp(self):
        super(GitRepo, self).setUp()
        tempdir = fixtures.TempDir()
        self.addCleanup(tempdir.cleanUp)
        tempdir.setUp()
        self.path = os.path.join(tempdir.path, 'git')
        self.repo.clone(self.path)


class BaseTestCase(testtools.TestCase):
    """Base Test Case for all tests."""

    def setUp(self):
        super(BaseTestCase, self).setUp()
        
        repo_path = self.useFixture(GitRepo(git.Repo('.'))).path
        self.useFixture(DiveDir(repo_path))
        repo = git.Repo('.')
        repo.git.config('user.email', 'user@example.com')
        repo.git.config('user.name', 'Example User')
