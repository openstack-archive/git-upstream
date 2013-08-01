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
from ghp.log import LogDedentMixin
from ghp.lib.utils import GitMixin
from ghp.lib.rebaseeditor import RebaseEditor
from ghp import subcommand, log
from ghp.lib.searchers import UpstreamMergeBaseSearcher

from abc import ABCMeta, abstractmethod
from collections import Sequence
from git import GitCommandError

import inspect


class ImportUpstreamError(HpgitError):
    """Exception thrown by L{ImportUpstream}"""
    pass


class ImportUpstream(LogDedentMixin, GitMixin):
    """
    Import code from an upstream project and merge in additional branches
    to create a new branch unto which changes that are not upstream but are
    on the local branch are applied.
    """

    def __init__(self, branch=None, upstream=None, import_branch=None,
                 extra_branches=None, *args, **kwargs):
        self._branch = branch
        self._upstream = upstream
        self._import_branch = import_branch
        self._extra_branches = extra_branches

        # make sure to correctly initialise inherited objects before performing
        # any computation
        super(ImportUpstream, self).__init__(*args, **kwargs)

        # test that we can use this git repo
        if not self.is_detached():
            raise ImportUpstreamError("In 'detached HEAD' state")

        if self.repo.bare:
            raise ImportUpstreamError("Cannot perform imports in bare repos")

        if self.branch == 'HEAD':
            self._branch = self.repo.active_branch

        # validate branches exist and log all failures
        branches = [
            self.branch,
            self.upstream
        ]
        branches.extend(self.extra_branches)

        invalid_ref = False
        for branch in branches:
            if not any(head for head in self.repo.heads if head.name == branch):
                msg = "Specified ref does not exist: '%s'"
                self.log.error(msg, branch)
                invalid_ref = True

        if invalid_ref:
            raise ImportUpstreamError("Invalid ref")

    @property
    def branch(self):
        """Branch to search for branch changes to apply when importing."""
        return self._branch

    @property
    def upstream(self):
        """Branch containing the upstream project code base to track."""
        return self._upstream

    @property
    def import_branch(self):
        """
        Pattern to use to generate the name, or user specified branch name
        to use for import.
        """
        return self._import_branch

    @property
    def extra_branches(self):
        """
        Branch containing the additional branches to be merged with the
        upstream when importing.
        """
        return self._extra_branches

    def _set_branch(self, branch, commit, checkout=False, force=False):

        if self.repo.active_branch == branch:
            self.log.info(
                """\
                Resetting branch '%s' to specified commit '%s'
                    git reset --hard %s
                """, branch, commit, commit)
            self.git.reset(commit, hard=True)
        elif checkout:
            if force:
                checkout_opt = '-B'
            else:
                checkout_opt = '-b'

            self.log.info(
                """\
                Checking out branch '%s' using specified commit '%s'
                    git checkout %s %s %s
                """, branch, commit, checkout_opt, branch, commit)
            self.git.checkout(checkout_opt, branch, commit)
        else:
            self.log.info(
                """\
                Creating  branch '%s' from specified commit '%s'
                    git branch --force %s %s
                """, branch, commit, branch, commit)
            self.git.branch(branch, commit, force=force)

    def create_import(self, commit=None, import_branch=None, checkout=False,
                      force=False):
        """
        Create the import branch from the specified commit.

        If the branch already exists abort if force is false
            If current branch, reset the head to the specified commit
            If checkout is true, switch and reset the branch to the commit
            Otherwise just reset the branch to the specified commit
        If the branch doesn't exist, create it and switch to it
        automatically if checkout is true.
        """

        if not commit:
            commit = self.upstream

        try:
            self.git.show_ref(commit, quiet=True, heads=True)

        except GitCommandError as e:
            msg = "Invalid commit '%s' specified to import from"
            self.log.error(msg, commit)
            raise ImportUpstreamError((msg + ": %s"), commit, e)

        if not import_branch:
            import_branch = self.import_branch

        # use describe in order to be certain about unique identifying 'commit'
        # Create a describe string with the following format:
        #    <describe upstream>[-<extra branch abbref hash>]*
        #
        # Simply appends the 7 character ref abbreviation for each extra branch
        # prefixed with '-', for each extra branch in the order they are given.
        describe_commit = self.git.describe(commit, tags=True,
                                            with_exceptions=False)
        if not describe_commit:
            self.log.warning("No tag describes the upstream branch")
            describe_commit = self.git.describe(commit, always=True, tags=True)

        self.log.info("""\
                    Using '%s' to describe:
                        %s
                    """, describe_commit, commit)
        describe_branches = [describe_commit]

        describe_branches.extend([self.git.rev_parse(b, short=True)
                                  for b in self.extra_branches])
        import_describe = "-".join(describe_branches)
        self._import_branch = self.import_branch.format(
            describe=import_describe)

        self._import_branch = import_branch.format(describe=import_describe)
        base = self._import_branch + "-base"
        self.log.debug("Creating and switching to import branch base '%s' "
                       "created from '%s' (%s)", base, self.upstream, commit)

        self.log.info(
            """\
            Checking if import branch '%s' already exists:
                git branch --list %s
            """, base, base)
        if self.git.show_ref("refs/heads/" + base, verify=True,
                             with_exceptions=False) and not force:
            msg = "Import branch '%s' already exists, set 'force' to replace"
            self.log.error(msg, self.import_branch)
            raise ImportUpstreamError(msg % self.import_branch)

        self._set_branch(base, commit, checkout, force)

        if self.extra_branches:
            self.log.info(
                """\
                Merging additional branch(es) '%s' into import branch '%s'
                    git checkout %s
                    git merge %s
                """, ", ".join(self.extra_branches), base, base,
                " ".join(self.extra_branches))
            self.git.checkout(base)
            self.git.merge(*self.extra_branches)

    def apply(self, strategy, interactive=False):
        """Apply list of commits given onto latest import of upstream"""

        self.log.debug(
            """\
            Should apply the following list of commits
                %s
            """, "\n    ".join([c.id for c in strategy.filtered_iter()]))

        base = self.import_branch + "-base"

        first = next(strategy.filtered_iter())
        self._set_branch(self.import_branch, self.branch, force=True)

        rebase = RebaseEditor(interactive, repo=self.repo)

        self.log.info(
            """\
            Rebase changes, dropping merges through editor:
                git rebase --onto %s \\
                    %s %s
            """, base, first.parents[0].id, self.import_branch)
        status, out, err = rebase.run(strategy.filtered_iter(),
                                      first.parents[0].id, self.import_branch,
                                      onto=base)
        if status:
            if err and err.startswith("Nothing to do"):
                # cancelled by user
                self.log.notice("Cancelled by user")
                return

            self.log.error("Rebase failed, will need user intervention to "
                           "resolve.")
            if out:
                self.log.notice(out)
            if err:
                self.log.notice(err)

            # once we support resuming/finishing add a message here to tell the
            # user to rerun this tool with the appropriate options to complete
            return

        self.log.notice("Successfully applied all locally carried changes")

    def resume(self, args):
        """Resume previous partial import"""
        raise NotImplementedError

    def finish(self, args):
        """
        Finish merge according to the selected strategy while performing
        suitable verification checks.
        """
        raise NotImplementedError


class ImportStrategiesFactory(object):
    __strategies = None

    @classmethod
    def createStrategy(cls, type, *args, **kwargs):
        if type in cls.listStrategies():
            return cls.__strategies[type](*args, **kwargs)
        else:
            raise RuntimeError("No class implements the requested strategy: "
                               "{0}".format(type))

    @classmethod
    def listStrategies(cls):
        cls.__strategies = {subclass._strategy: subclass
                            for subclass in LocateChangesStrategy.__subclasses__()
                            if subclass._strategy}
        return cls.__strategies.keys()


from ghp.lib.searchers import NoMergeCommitFilter, ReverseCommitFilter


class LocateChangesStrategy(GitMixin, Sequence):
    """
    Base class that needs to be extended with the specific strategy on how to
    handle changes locally that are not yet upstream.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, git=None, *args, **kwargs):
        """
        Initialize an empty filters list
        """
        self.data = None
        self.filters = []
        super(LocateChangesStrategy, self).__init__(*args, **kwargs)

    def __getitem__(self, key):
        if not self.data:
            self.data = self._popdata()
        return self.data[key]

    def __len__(self):
        if not self.data:
            self.data = self._popdata()
        return len(self.data)

    @classmethod
    def getName(cls):
        return cls._strategy

    def filtered_iter(self):
        # chain the filters as generators so that we don't need to allocate new
        # lists for each step in the filter chain.
        commit_list = self
        for f in self.filters:
            commit_list = f.filter(commit_list)

        return commit_list

    def filtered_list(self):

        return list(self.filtered_iter())

    def _popdata(self):
        """
        Should return the list of commits from the searcher object
        """
        return self.searcher.list()


class LocateChangesWalk(LocateChangesStrategy):
    """
    """

    _strategy = "drop"

    def __init__(self, branch="HEAD", *args, **kwargs):
        self.searcher = UpstreamMergeBaseSearcher(branch=branch)
        super(self.__class__, self).__init__(*args, **kwargs)
        self.filters.append(NoMergeCommitFilter())
        self.filters.append(ReverseCommitFilter())


@subcommand.arg('-i', '--interactive', action='store_true', default=False,
                help='Let the user edit the list of commits before applying.')
@subcommand.arg('-f', '--force', dest='force', required=False, action='store_true',
                default=False,
                help='Force overwrite of existing import branch if it exists.')
@subcommand.arg('--merge', dest='merge', required=False, action='store_true',
                default=False,
                help='Merge the resulting import branch into the target branch '
                     'once complete')
@subcommand.arg('--no-merge', dest='merge', required=False, action='store_false',
                help="Disable merge of the resulting import branch")
@subcommand.arg('-s', '--strategy', metavar='<strategy>',
                choices=ImportStrategiesFactory.listStrategies(),
                default=LocateChangesWalk.getName(),
                help='Use the given strategy to re-apply locally carried changes '
                     'to the import branch. (default: %(default)s)')
@subcommand.arg('--into', dest='branch', metavar='<branch>', default='HEAD',
                help='Branch to take changes from, and replace with imported branch.')
@subcommand.arg('--import-branch', metavar='<import-branch>',
                help='Name of import branch to use', default='import/{describe}')
@subcommand.arg('upstream_branch', metavar='<upstream-branch>', nargs='?',
                default='upstream/master',
                help='Upstream branch to import. Must be specified if '
                     'you wish to provide additional branches.')
@subcommand.arg('branches', metavar='<branches>', nargs='*',
                help='Branches to additionally merge into the import branch '
                     'using default git merging behaviour')
def do_import_upstream(args):
    """
    Import code from specified upstream branch.

    Creates an import branch from the specified upstream branch, and optionally
    merges additional branches given as arguments. Current branch, unless
    overridden by the --into option, is used as the target branch from which a
    list of changes to apply onto the new import is constructed based on the
    the specificed strategy.

    Once complete it will merge and replace the contents of the target branch
    with those from the import branch, unless --no-merge is specified.
    """

    logger = log.getLogger('%s.%s' % (__name__,
                                      inspect.stack()[0][0].f_code.co_name))

    importupstream = ImportUpstream(branch=args.branch,
                                    upstream=args.upstream_branch,
                                    import_branch=args.import_branch,
                                    extra_branches=args.branches)

    logger.notice("Searching for previous import")
    strategy = ImportStrategiesFactory.createStrategy(args.strategy,
                                                      branch=args.branch)
    # if last commit in the strategy was a merge, then the additional branches that
    # were merged in previously can be extracted based on the commits merged.
    prev_import_merge = strategy[-1]
    if len(prev_import_merge.parents) > 1:
        idx = next((idx for idx, commit in enumerate(prev_import_merge.parents)
                    if commit.id == strategy.searcher.commit.id), None)

        if idx:
            additional_commits = prev_import_merge.parents[idx + 1:]
            if additional_commits and not args.branches:
                logger.warning("""\
                    **************** WARNING ****************
                    Previous import merged additional branches but non have
                    been specified on the command line for this import.\n""")

    logger.notice("Starting import of upstream")
    importupstream.create_import(force=args.force)
    logger.notice("Successfully created import branch")

    importupstream.apply(strategy, args.interactive)



# vim:sw=4:sts=4:ts=4:et:
