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
    """Import code from an upstream project and merge in additional branches
    to create a new branch unto which changes that are not upstream but are
    on the local branch are applied.
    """

    def __init__(self, branch=None, upstream=None, import_branch=None, extra_branches=None):
        self._branch = branch
        self._upstream = upstream
        self._import_branch = import_branch
        self._extra_branches = extra_branches

        self._repo = Repo(os.environ.get('GIT_WORK_TREE', os.path.curdir))
        self._git = self.repo.git


        if self.repo.bare:
            raise ImportUpstreamError("Cannot perform imports in bare repos")

        if self.branch == 'HEAD':
            self.branch = self.repo.active_branch

        branches = {
            'upstream': self.upstream,
            'branch': self.branch
        }

        if self.extra_branches != []:
            branches.update({'extra branch %d' % idx: value
                                for (idx, value) in enumerate(self.extra_branches, 1)})

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
    def extra_branches(self):
        """Branch containing the additional branches to be merged with the upstream when importing"""
        return self._extra_branches

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

        if self.git.show_ref("refs/heads/" + self.import_branch, verify=True,
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

        if self.extra_branches:
            print "Merging additional branch(es) '{0}' into new import branch '{1}'".format(
                ", ".join(self.extra_branches), self.import_branch)
            self.git.checkout(self.import_branch)
            self.git.merge(*self.extra_branches)

    def find_changes(self):
        pass

    def start(self, args):
        "Start import of upstream"

        commit = args.get('upstream-commit', args.get('upstream-branch', None))
        self.create_import(commit, checkout=args['checkout'], force=args['force'])

    def resume(self, args):
        print "Allow resuming of a partial import, required to make it easy for " \
            "individuals to rework changes"

    def finish(self, args):
        print "Need to check if we are finished the import"



@subcommand.arg('-f', '--force', dest='force', required=False, action='store_true',
                default=False,
                help='Force overwrite of existing import branch if it exists.')
@subcommand.arg('--merge', dest='merge', required=False, action='store_true',
                default=False,
                help='Merge the resulting import branch into the target branch '
                     'once complete')
@subcommand.arg('--no-merge', dest='merge', required=False, action='store_false',
                help="Disable merge of the resulting import branch")
@subcommand.arg('--into', dest='branch', metavar='<branch>', default='HEAD',
                help='Branch to take changes from, and replace with imported branch.')
@subcommand.arg('--import-branch', metavar='<import-branch>',
                help='Name of import branch to use', default='import/{0}')
@subcommand.arg('upstream_branch', metavar='<upstream-branch>', nargs='?',
                default='upstream/master',
                help='Upstream branch to import. Must be specified if '
                     'you wish to provide additional branches.')
@subcommand.arg('branches', metavar='<branches>', nargs='*',
                help='Branches to additionally merge into the import branch '
                     'using default git merging behaviour')
def do_import_upstream(args):
    """Import code from specified upstream branch.

    Creates an import branch from the specified upstream branch, and optionally
    merges additional branches given as arguments. Current branch, unless
    overridden by the --into option, is used as the target branch from which a
    list of changes to apply onto the new import is constructed based on the
    the specificed strategy.

    Once complete it will merge and replace the contents of the target branch
    with those from the import branch, unless --no-merge is specified.
    """

    importupstream = ImportUpstream(branch=args.branch,
                                    upstream=args.upstream_branch,
                                    import_branch=args.import_branch,
                                    extra_branches=args.branches)

    commit = getattr(args, 'upstream_commit', None) or args.upstream_branch
    importupstream.create_import(commit,
                                 checkout=getattr(args, 'checkout', None),
                                 force=getattr(args, 'force', None))



# vim:sw=4:sts=4:ts=4:et:
