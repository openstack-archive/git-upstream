#
# Copyright (c) 2012 Hewlett-Packard
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

from ghp.errors import HpgitError
from ghp import subcommand
from git import Repo, GitCommandError

import git
import os

class ImportUpstreamError(HpgitError):
    """Exception thrown by L{ImportUpstream}"""
    pass


class ImportUpstream:
    """Import code and packaging branches from an upstream project
    and create a new branch unto which changes that are not upstream
    but are on the mainline branch are applied.

    """

    def __init__(self, branch=None, upstream=None, import_branch=None, packaging=None):
        self._branch = branch
        self._upstream = upstream
        self._import_branch = import_branch
        self._packaging = packaging

        self._repo = Repo(os.environ.get('GIT_WORK_TREE', os.path.curdir))
        self._git = self.repo.git


        if self.repo.bare:
            raise ImportUpstreamError("Cannot perform imports of upstream branches in bare repos")

        if self.branch == 'HEAD':
            self.branch = self.repo.active_branch

        branches = {
            'upstream': self.upstream,
            'branch': self.branch
        }

        if self.packaging:
            branches['packaging'] = self.packaging

        for branch_type, branch in branches.iteritems():
            if not any(head for head in self.repo.heads if head.name == branch):
                raise ImportUpstreamError("Specified %s branch not found: %s" % (branch_type, branch))

    @staticmethod
    def __setup__(self, argparser):
        pass

    @property
    def branch(self):
        """Branch to search for branch changes to apply when importing"""
        return self._branch

    @property
    def upstream(self):
        """Branch containing the upstream project code base to track"""
        return self._upstream

    @property
    def import_branch(self):
        """Pattern to use to generate the name, or user specified branch name to use for import"""
        return self._import_branch

    @property
    def packaging(self):
        """Branch containing the packaging data to be merged with the upstream when importing"""
        return self._packaging

    @property
    def repo(self):
        """Git repository object for performing operations"""
        return self._repo

    @property
    def git(self):
        """Git command object for performing direct git operations using python-git"""
        return self._git

    def create_import(self, commit=None, checkout=False, force=False):
        """Create the import branch from the specified commit.

        If the branch already exists abort if force is false
            If current branch, reset the head to the specified commit
            If checkout is true, switch and reset the branch to the commit
            Otherwise just reset the branch to the specified commit
        If the branch doesn't exist, create it and switch to it
        automatically if checkout is true.
        """

        # use describe directly in order to be certain about unique identifying the
        # commit
        if not commit:
            commit = self.upstream

        try:
            self.git.show_ref(commit, quiet=True, heads=True)

        except GitCommandError as e:
            raise ImportUpstreamError("Invalid commit specified as import point: {0}".format(e))

        import_describe = self.git.describe(commit)
        upstream_branches = self.git.branch("upstream/*", contains=commit, list=True).split('\n')
        self.import_branch = self.import_branch.format(import_describe)

        print "Creating and switching to import branch '{0}' created from '{1}' ({2})".format(
            self.import_branch, self.upstream, commit)

        if not self.git.show_ref("refs/heads/" + self.import_branch, verify=True, quiet=True,
                                 with_exceptions=False) and not force:
            raise ImportUpstreamError("Import branch '{0}' already exists, use force to replace"
                                      .format(self.import_branch))

        if self.repo.active_branch == self.import_branch:
            print "Resetting import branch '{0}' to specified commit '{1}'".format(
                self.import_branch, commit)
            self.git.reset(commit, hard=True)
        elif checkout:
            checkout_args = dict(b=True)
            if force:
                checkout_args = dict(B=True)

            print "Checking out import branch '{0}' using specified commit '{1}'".format(
                self.import_branch, commit)
            self.git.checkout(self.import_branch, commit, **checkout_args)
        else:
            print "Creating import branch '{0}' from specified commit '{1}'".format(
                self.import_branch, commit)
            self.git.branch(self.import_branch, commit, force=force)

        if self.packaging:
            print "Merging packaging branch '{0}' into new import branch '{1}'".format(
                self.packaging, self.import_branch)
            self.git.checkout(self.import_branch)
            self.git.merge(self.packaging)

    def find_changes(self):
        pass

    def start(self, args):
        "Start import of upstream"

        commit = args.get('upsteam-commit', args.get('upstream-branch', None))
        self.create_import(commit, checkout=args['checkout'], force=args['force'])

    def resume(self, args):
        print "Allow resuming of a partial import, required to make it easy for individuals to rework changes"

    def finish(self, args):
        print "Need to check if we are finished the import"



@subcommand.arg('-f', '--force', dest='force', required=False, action='store_true', default=False,
                help="Force overwrite of existing import branch if it already exists")
@subcommand.arg('--merge', dest='merge', required=False, action='store_true', default=False,
                help="Merge the resulting import branch into the target branch once complete")
@subcommand.arg('--no-merge', dest='merge', required=False, action='store_false',
                help="Disable merge of the resulting import branch")
@subcommand.arg('--packaging-branch', metavar='<packaging-branch>',
                help='Branch containing packaging code that should be merged when importing upstream')
@subcommand.arg('--import-branch', metavar='<import-branch>',
                help='Name of import branch to use', default='import/{0}')
@subcommand.arg('upstream_branch', metavar='<upstream-branch>', nargs='?',
                help='Upstream branch to import', default='upstream/master')
@subcommand.arg('branch', metavar='<branch>', nargs='?',
                help='Branch to take changes from, and replace with imported branch', default='HEAD')
def do_import_upstream(args):
    """Import code from specified upstream branches

    optionally merge given packaging branches to create an import branch, upon
    which to apply any locally carried changes. Once applied the resulting
    import branch is then merged into the target branch replacing all previous
    contents.
    """

    importupstream = ImportUpstream(branch=args.branch, upstream=args.upstream_branch,
                                    import_branch=args.import_branch, packaging=args.packaging_branch)

    commit = getattr(args, 'upstream_commit', None) or args.upstream_branch
    importupstream.create_import(commit,
                                 checkout=getattr(args, 'checkout', None),
                                 force=getattr(args, 'force', None))



# vim:sw=4:sts=4:ts=4:et:
