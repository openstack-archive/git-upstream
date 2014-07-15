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

import git
from git import Commit, Repo


class GitUpstreamCompatRepo(Repo):

    @property
    def git_dir(self):
        return self.path

if not hasattr(Repo, 'git_dir'):
    Repo = GitUpstreamCompatRepo
    # Monkey patch old python-git library to use GitUpstreamCompatRepo instead
    # of Repo
    git.Repo = GitUpstreamCompatRepo


class GitUpstreamCompatCommit(Commit):

    @classmethod
    def list_from_string(cls, repo, text):
        """
        Parse out commit information into a list of Commit objects

        This fixes the superclass behaviour in earlier versions of python-git
        where blank lines in commit messages weren't retained.

        :param repo: is the Repo
        :param text: is the text output from the git command (raw format)

        Returns
            Commit[]
        """
        lines = [l for l in text.strip().splitlines()]

        commits = []

        while lines:
            id = lines.pop(0).split()[1]
            tree = lines.pop(0).split()[1]

            parents = []
            while lines and lines[0].startswith('parent'):
                parents.append(lines.pop(0).split()[-1])
            author, authored_date = cls.actor(lines.pop(0))
            committer, committed_date = cls.actor(lines.pop(0))

            messages = []
            lines.pop(0)
            while lines and lines[0].startswith('    '):
                messages.append(lines.pop(0).strip())

            message = '\n'.join(messages)

            commits.append(GitUpstreamCompatCommit(
                repo, id=id, parents=parents,
                tree=tree, author=author,
                authored_date=authored_date,
                committer=committer,
                committed_date=committed_date,
                message=message))

            while lines:
                if not lines[0].strip():
                    lines.pop(0)
                else:
                    break
        return commits

    @property
    def hexsha(self):
        return self.id

    @classmethod
    def iter_items(cls, repo, ref, path='', **kwargs):
        """
        Wrap call to find_all method in older versions of python-git
        """
        results = cls.find_all(repo, ref, path='', **kwargs)
        if type(results) == list:
            # Callers are expecting a generator
            for item in results:
                yield item
        elif hasattr(results, '__iter__') and not hasattr(results, '__len__'):
            yield results
        else:
            raise RuntimeError("Unexpected type returned from 'find_all'")

if not hasattr(Commit, 'iter_items'):
    Commit = GitUpstreamCompatCommit
    # monkey patch class so that Repo will use the patched class
    git.commit.Commit = GitUpstreamCompatCommit
