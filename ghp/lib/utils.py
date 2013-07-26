#
# Copyright (c) 2012, 2013 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

from ghp.errors import HpgitError

from git import Repo
from git.errors import InvalidGitRepositoryError
import os
import sys


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
                raise HpgitError("Not a git repository", tb)

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
