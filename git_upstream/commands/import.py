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

from git_upstream.commands import GitUpstreamCommand
from git_upstream.lib.importupstream import ImportUpstream
from git_upstream.lib.importupstream import ImportUpstreamError
from git_upstream.lib.strategies import ImportStrategiesFactory
from git_upstream.lib.strategies import LocateChangesWalk
from git_upstream.log import LogDedentMixin


class ImportCommand(LogDedentMixin, GitUpstreamCommand):
    """Import code from specified upstream branch.

    Creates an import branch from the specified upstream branch, and optionally
    merges additional branches given as arguments. Current branch, unless
    overridden by the --into option, is used as the target branch from which a
    list of changes to apply onto the new import is constructed based on the
    specified strategy.

    Once complete it will merge and replace the contents of the target branch
    with those from the import branch, unless --no-merge is specified.
    """
    name = "import"
    usage = """
    %(prog)s [-i] [options] [--onto <branch>]
        [--import-branch <import-branch>] [<upstream-branch>]
        [<branches> ...]
    %(prog)s [--finish] [options] [--onto <branch>]
        [--import-branch <import-branch>]
    """

    def __init__(self, *args, **kwargs):
        super(ImportCommand, self).__init__(*args, **kwargs)

        self.parser.add_argument(
            '-i', '--interactive', action='store_true', default=False,
            help='Let the user edit the list of commits before applying.')
        self.parser.add_argument(
            '-d', '--dry-run', dest='dry_run', action='store_true',
            default=False,
            help='Only print out the list of commits that would be applied.')
        self.parser.add_argument(
            '-f', '--force', dest='force', required=False,
            action='store_true', default=False,
            help='Force overwrite of existing import branch if it exists.')
        # finish options
        self.parser.add_argument(
            '--finish', dest='finish', required=False, action='store_true',
            default=False,
            help='Merge the specified import branch into the target')
        # result behaviour options
        self.parser.add_argument(
            '--merge', dest='merge', required=False, action='store_true',
            default=True,
            help='Merge the resulting import branch into the target branch '
                 'once complete')
        self.parser.add_argument(
            '--no-merge', dest='merge', required=False, action='store_false',
            help='Disable merge of the resulting import branch')
        # search/include options
        self.parser.add_argument(
            '--search-refs', action='append_replace', metavar='<pattern>',
            default=['upstream/*'], dest='search_refs',
            help='Refs to search for previous import commit. May be '
                 'specified multiple times.')
        self.parser.add_argument(
            '-s', '--strategy', metavar='<strategy>',
            choices=ImportStrategiesFactory.list_strategies(),
            default=LocateChangesWalk.get_strategy_name(),
            help='Use the given strategy to re-apply locally carried '
                 'changes to the import branch. (default: %(default)s)')
        self.parser.add_argument(
            '--into', dest='branch', metavar='<branch>', default='HEAD',
            help='Branch to take changes from, and replace with imported '
                 'branch.')
        self.parser.add_argument(
            '--import-branch', metavar='<import-branch>',
            default='import/{describe}', help='Name of import branch to use')
        # data args
        self.parser.add_argument(
            'upstream_branch', metavar='<upstream-branch>', nargs='?',
            default='upstream/master',
            help='Upstream branch to import. Must be specified if you wish to '
                 'provide additional branches.')
        self.parser.add_argument(
            'branches', metavar='<branches>', nargs='*',
            help='Branches to additionally merge into the import branch using '
                 'default git merging behaviour')

    def validate(self):
        """Perform more complex validation of args that cannot be mixed"""

        # check if --finish set with --no-merge
        if self.args.finish and self.args.merge is False:
            self.parser.error(
                "--finish cannot be used with '--no-merge'")

    def finalize(self):
        """Perform additional parsing of args"""

        if self.args.finish and not self.args.upstream_branch:
            self.args.real_upstream_branch = self.args.import_branch
        else:
            self.args.real_upstream_branch = self.args.upstream_branch

    def _finish_report(self, import_upstream):
        self.log.notice(
            """
            Successfully finished import:
                target branch: '%s'
                upstream branch: '%s'
                import branch: '%s'""",
            self.args.branch, self.args.real_upstream_branch,
            import_upstream.import_branch)
        if self.args.branches:
            for branch in self.args.branches:
                self.log.notice("    extra branch: '%s'", branch,
                                dedent=False)

    def execute(self):

        import_upstream = ImportUpstream(
            branch=self.args.branch,
            upstream=self.args.real_upstream_branch,
            import_branch=self.args.import_branch,
            extra_branches=self.args.branches)

        # perform additional checks requiring git operations
        if self.args.finish and not import_upstream.is_valid_commit(
                self.args.import_branch):
            self.parser.error(
                "Invalid ref for argument '--import-branch', '%s' not found!"
                % self.args.import_branch)

        self.log.notice("Searching for previous import")
        strategy = ImportStrategiesFactory.create_strategy(
            self.args.strategy, branch=self.args.branch,
            upstream=self.args.real_upstream_branch,
            search_refs=self.args.search_refs)

        if not strategy.previous_upstream:
            raise ImportUpstreamError("Cannot find previous import")

        if import_upstream.already_synced(strategy):
            if not self.args.force:
                return True
            self.log.notice("Forcing import on up to date branches (--force)")

        if self.args.dry_run:
            commit_list = [c.hexsha[:6] + " - " + c.summary[:60] +
                           (c.summary[60:] and "...")
                           for c in list(strategy.filtered_iter())]
            self.log.notice("""
                Requested a dry-run: printing the list of commit that should be
                rebased

                    %s
                """, "\n    ".join(commit_list))
            return True

        # finish and return if thats all
        if self.args.finish:
            if import_upstream.finish():
                self._finish_report(import_upstream)
                return True
            else:
                return False

        # otherwise perform fresh import
        self.log.notice("Starting import of upstream")
        import_upstream.create_import(force=self.args.force)
        self.log.notice("Created import branch '%s'" %
                        import_upstream.import_branch)

        # build suitable command line for interactive mode
        if self.args.merge:
            cmdline = self.args.script_cmdline + [
                self.name,
                '--finish',
                '--into=%s' % import_upstream.branch,
                '--import-branch=%s' % import_upstream.import_branch,
                import_upstream.upstream
            ] + import_upstream.extra_branches
        else:
            cmdline = None

        if not import_upstream.apply(strategy, self.args.interactive, cmdline):
            self.log.notice("Import cancelled")
            return False

        if not self.args.merge:
            self.log.notice(
                """
                Import complete, not merging to target branch '%s' as
                requested.
                """, self.args.branch)
            return True

        self._finish_report(import_upstream)
        return True

# vim:sw=4:sts=4:ts=4:et:
