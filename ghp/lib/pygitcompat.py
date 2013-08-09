#
# Copyright (c) 2012, 2013 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

from git import Commit


class HpgitCompatCommit(Commit):

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

            commits.append(HpgitCompatCommit(repo, id=id, parents=parents,
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
