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
from git_upstream.lib.pygitcompat import Repo
from git import Git

import re
import os
import sys

try:
    from git.exc import InvalidGitRepositoryError
except ImportError:
    from git.errors import InvalidGitRepositoryError


class GitMixin(object):

    def __init__(self, *args, **kwargs):
        repo = kwargs.pop('repo', None)
        if repo:
            self.__repo = repo
        else:
            try:
                self.__repo = Repo(os.environ.get('GIT_WORK_TREE',
                                                  os.path.curdir))
            except InvalidGitRepositoryError:
                exc_class, exc, tb = sys.exc_info()
                raise GitUpstreamError("Not a git repository", tb)

        self.__git = self.repo.git
        super(GitMixin, self).__init__(*args, **kwargs)

    @property
    def repo(self):
        return self.__repo

    @property
    def git(self):
        return self.__git

    def is_detached(self):
        return self.git.symbolic_ref("HEAD", q=True, with_exceptions=False)

    def get_name(self, sha1, pattern=None):
        """
        Return a symbolic name corresponding to a SHA1

        Will return reference names using the commit revision modifier strings
        to identify the given SHA1. Or will return nothing if SHA1 cannot be
        identified relative to any existing reference.
        """
        if pattern:
            return self.git.name_rev(sha1, name_only=False, refs=pattern,
                                     with_exceptions=False)
        else:
            return self.git.name_rev(sha1, name_only=False,
                                     with_exceptions=False)

    def is_valid_commit(self, sha1):
        """
        Check if given SHA1 refers to a commit object on a valid ref.

        This can be used to test if any name or SHA1 refers to a commit
        reachable by walking any of the refs under the .git/refs.
        """

        # get_name will return a string if the sha1 is reachable from an
        # existing reference.
        return bool(self.get_name(sha1))


def check_git_version(major, minor, revision):
    """
    Check git version PythonGit (and git-upstream) will be using is greater of
    equal than major.minor.revision)
    """

    regex = re.compile("^git version ([0-9]+)\.([0-9]+)\.([0-9]+)(\.(.+))*$")
    git = Git()

    groups = regex.search(git.version()).groups()
    if int(groups[0]) > major:
        return True
    elif int(groups[0]) == major:
        if int(groups[1]) > minor:
            return True
        elif int(groups[1]) == minor:
            if int(groups[2]) >= revision:
                return True

    return False
