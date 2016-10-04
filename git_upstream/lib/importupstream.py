#
# Copyright (c) 2012-2016 Hewlett-Packard Development Company, L.P.
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

from git import GitCommandError

from git_upstream.errors import GitUpstreamError
from git_upstream.lib.pygitcompat import Commit
from git_upstream.lib.rebaseeditor import RebaseEditor
from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin


class ImportUpstreamError(GitUpstreamError):
    """Exception thrown by L{ImportUpstream}"""
    pass


class ImportUpstream(LogDedentMixin, GitMixin):
    """Import code from an upstream project and merge in additional branches
    to create a new branch unto which changes that are not upstream but are
    on the local branch are applied.
    """

    def __init__(self, branch=None, upstream=None, import_branch=None,
                 extra_branches=None, *args, **kwargs):
        if not extra_branches:
            extra_branches = []
        self._branch = branch
        self._upstream = upstream
        self._import_branch = import_branch
        self._extra_branches = extra_branches

        # make sure to correctly initialise inherited objects before performing
        # any computation
        super(ImportUpstream, self).__init__(*args, **kwargs)

        if self.repo.bare:
            raise ImportUpstreamError("Cannot perform imports in bare repos")

        if self.branch == 'HEAD':
            self._branch = str(self.repo.active_branch)

        # validate branches exist and log all failures
        branches = [
            self.branch,
            self.upstream
        ]
        branches.extend(self.extra_branches)

        invalid_ref = False
        for branch in branches:
            if not self.is_valid_commit(branch):
                msg = "Specified commit(ish) does not exist: '%s'"
                self.log.error(msg, branch)
                invalid_ref = True

        if invalid_ref:
            raise ImportUpstreamError("Invalid branch/tag/sha1")

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
        """Pattern to use to generate the name, or user specified branch name
        to use for import.
        """
        return self._import_branch

    @property
    def extra_branches(self):
        """Branch containing the additional branches to be merged with the
        upstream when importing.
        """
        return self._extra_branches

    def _set_branch(self, branch, commit, checkout=False, force=False):

        if str(self.repo.active_branch) == branch:
            self.log.info(
                """
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
                """
                Checking out branch '%s' using specified commit '%s'
                    git checkout %s %s %s
                """, branch, commit, checkout_opt, branch, commit)
            self.git.checkout(checkout_opt, branch, commit)
        else:
            self.log.info(
                """
                Creating  branch '%s' from specified commit '%s'
                    git branch --force %s %s
                """, branch, commit, branch, commit)
            self.git.branch(branch, commit, force=force)

    def create_import(self, commit=None, import_branch=None, checkout=False,
                      force=False):
        """Create the import branch from the specified commit.

        If the branch already exists abort if force is false
            If current branch, reset the head to the specified commit
            If checkout is true, switch and reset the branch to the commit
            Otherwise just reset the branch to the specified commit
        If the branch doesn't exist, create it and switch to it
        automatically if checkout is true.
        """

        # test that we can use this git repo
        if self.is_detached():
            raise ImportUpstreamError("In 'detached HEAD' state")

        if not commit:
            commit = self.upstream

        try:
            self.git.rev_parse("%s^{commit}" % commit, verify=True)

        except GitCommandError as e:
            msg = "Invalid commit '%s' specified to import from"
            self.log.error(msg, commit)
            raise ImportUpstreamError((msg + ": %s"), commit, e)

        if not import_branch:
            import_branch = self.import_branch

        # determine if given a tag to import from and use as given, otherwise
        # convert the given branch/commit into a described commit based on
        # a recent tag.
        #
        # Create a describe string with the following format:
        #    <describe upstream>[-<extra branch abbref hash>]*
        #
        # Extra branch abbref hash is the 7 character ref abbreviation for each
        # extra branch joined with '-', in the order they are passed in to
        # uniquely describe the full import.

        if self.git.show_ref(commit, tags=True, with_exceptions=False):
            # if given upstream ref is a tag, no need to describe
            describe_commit = commit
        else:
            describe_commit = self.git.describe(commit, tags=True,
                                                with_exceptions=False)
            if not describe_commit:
                self.log.warning("No tag describes the upstream branch")
                describe_commit = self.git.describe(commit, always=True,
                                                    tags=True)

        self.log.info("""
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
            """
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
                """
                Merging additional branch(es) '%s' into import branch '%s'
                    git checkout %s
                    git merge %s
                """, ", ".join(self.extra_branches), base, base,
                " ".join(self.extra_branches))
            self.git.checkout(base)
            # use read-tree to handle multiple unrelated branches correctly
            # as normal merge (with octopus strategy) will refuse if you
            # are merging in more than one branch without a common
            # ancestor to the current tree.
            self.git.merge(*self.extra_branches, s="ours", no_commit=True)
            self.git.read_tree(empty=True)
            self.git.read_tree("HEAD", *self.extra_branches)
            self.git.checkout("--", ".")
            self.git.commit(no_edit=True)

    def _linearise(self, branch, sequence, previous_import):

        counter = len(sequence) - 1
        ancestors = set()

        self._set_branch(branch, previous_import, checkout=True, force=True)
        root = previous_import.hexsha
        while counter > 0:
            # add commit to list of ancestors to check
            ancestors.add(root)

            # look for merge commits that are not part of ancestry path
            for idx in xrange(counter - 1, -1, -1):
                commit = sequence[idx]
                # if there is only one parent, no need to check the others
                if len(commit.parents) < 2:
                    ancestors.add(commit.hexsha)
                elif any(p.hexsha not in ancestors for p in commit.parents):
                    self.log.debug("Rebase upto commit SHA1: %s",
                                   commit.hexsha)
                    idx = idx + 1
                    break
                else:
                    ancestors.add(commit.hexsha)
            tip = sequence[idx].hexsha

            self.log.info("Rebasing from %s to %s", root, tip)
            previous = self.git.rev_parse(branch)
            self.log.info("Rebasing onto '%s'", previous)
            if root == previous and idx == 0:
                # special case, we are already linear
                self.log.info("Already in a linear layout")
                return
            self._set_branch(branch, tip, force=True)
            try:
                self.log.debug(
                    """
                        git rebase -p --onto=%s \\
                            %s %s
                    """, previous, root, branch)
                self.git.rebase(root, branch, onto=previous, p=True)
            except Exception:
                self.git.rebase(abort=True, with_exceptions=False)
                raise
            counter = idx - 1
            # set root commit for next loop
            root = sequence[counter].hexsha

    def apply(self, strategy, interactive=False, resume_cmdline=None):
        """Apply list of commits given onto latest import of upstream"""

        commit_list = list(strategy.filtered_iter())
        if len(commit_list) == 0:
            self.log.notice("All carried changes gone upstream")
            self._set_branch(self.import_branch, self.upstream, force=True)
            # no resume_cmdline means to skip merge
            if resume_cmdline is None:
                return True
            # otherwise perform the finish
            return self.finish()

        self.log.debug(
            """
            Should apply the following list of commits
                %s
            """, "\n    ".join([c.hexsha for c in commit_list]))

        base = self.import_branch + "-base"

        self._set_branch(self.import_branch, self.branch, force=True)
        self.log.info(
            """
            Creating import branch '%s' from specified commit '%s' in prep to
            linearize the local changes before transposing to the new upstream:
                git branch --force %s %s
            """, self.import_branch, self.branch, self.import_branch,
            self.branch)

        self.log.notice("Attempting to linearise previous changes")
        # attempt to silently linearize the current carried changes as a branch
        # based on the previous located import commit. This provides a sane
        # abort result for if the user needs to abort the rebase of this branch
        # onto the new point upstream that was requested to import from.
        try:
            self._linearise(self.import_branch, strategy,
                            strategy.searcher.commit)
        except Exception:
            # Could ask user if they want to try and use the non clean route
            # provided they don't mind that 'git rebase --abort' will result
            # in a virtually useless local import branch
            self.log.warning(
                """

                Exception occurred during linearisation of local changes on to
                previous import to simplify behaviour should user need to abort
                the rebase that applies these changes to the latest import
                point. Attempting to tidy up state.

                Do not Ctrl+C unless you wish to need to clean up your git
                repository by hand.

                """)
            # reset head back to the tip of the changes to be rebased
            self._set_branch(self.import_branch, self.branch, force=True)

        # build the command line
        rebase = RebaseEditor(resume_cmdline, interactive, repo=self.repo)
        if len(commit_list):
            first = commit_list[0]

            self.log.info(
                """
                Rebase changes, dropping merges through editor:
                    git rebase --onto %s \\
                        %s %s
                """, base, first.parents[0].hexsha, self.import_branch)
            status, out, err = rebase.run(commit_list,
                                          first.parents[0].hexsha,
                                          self.import_branch,
                                          onto=base)
            if status:
                if err and err.startswith("Nothing to do"):
                    # cancelled by user
                    self.log.notice("Cancelled by user")
                    return False

                self.log.error("Rebase failed, will need user intervention to "
                               "resolve.")
                if out:
                    self.log.notice(out.decode('utf-8'))
                if err:
                    self.log.notice(err.decode('utf-8'))

                # once we support resuming/finishing add a message here to tell
                # the user to rerun this tool with the appropriate options to
                # complete
                return False

            self.log.notice("Successfully applied all locally carried changes")
            self.git.checkout(self.branch)
        else:
            self.log.warning("Warning, nothing to do: locally carried " +
                             "changes already rebased onto " + self.upstream)
        return True

    def resume(self, args):
        """Resume previous partial import"""
        raise NotImplementedError

    def finish(self):
        """Finish import

        Finish the import by merging the import branch to the target while
        performing suitable verification checks.
        """
        self.log.notice("Merging import to requested branch '%s'",
                        self.branch)
        self.log.info("No verification checks enabled")
        in_rebase = False
        if self.is_detached():
            # called via rebase exec
            target_sha = self.git.rev_parse("HEAD")
            in_rebase = True
        else:
            target_sha = self.import_branch
        self.git.checkout(self.branch)
        current_sha = self.git.rev_parse("HEAD")

        commit_message = (
            "Merge branch '{0}' into {1}\n\n"
            "Import of '{2}' into '{1}'."
        ).format(self.import_branch, self.branch, self.upstream)

        try:
            self.log.info(
                """
                Merging by inverting the 'ours' strategy discard all changes
                and replace existing branch contents with the new import.
                """)
            self.log.info(
                """
                Merging import branch (%s) to HEAD and ignoring changes:
                    git merge -s ours --no-commit %s
                """, self.import_branch, target_sha)
            self.git.merge('-s', 'ours', target_sha, no_commit=True)
            self.log.info(
                """
                Replacing tree contents with those from the import branch (%s):
                    git read-tree -u --reset %s
                """, self.import_branch, target_sha)
            self.git.read_tree(target_sha, u=True, reset=True)
            self.log.info(
                """
                Committing merge commit:
                    git commit -m "%s"
                """, commit_message.replace('\n', '\n' + ' ' * 4))
            self.git.commit(m=commit_message)
            # finally test that everything worked correctly by comparing if
            # the tree object id's match
            if self.git.rev_parse("HEAD^{tree}") != \
                    self.git.rev_parse("%s^{tree}" % target_sha):
                raise ImportUpstreamError(
                    "Resulting tree does not match import")
            if in_rebase:
                self.log.info("Code thinks we're in the middle of a rebase")
                self.git.checkout(target_sha)
        except (GitCommandError, ImportUpstreamError) as e:
            self.log.error(
                """
                Failed to finish import by merging branch: '%s'
                With commit: '%s'
                into and replacing the contents of: '%s'
                """, self.import_branch, target_sha, self.branch)
            self.log.error(str(e))
            self._set_branch(self.branch, current_sha, force=True)
            return False
        except Exception:
            self.log.exception("Unknown exception during finish")
            self._set_branch(self.branch, current_sha, force=True)
            raise
        return True

    def already_synced(self, strategy):
        """Check if already synced

        Check if we are already up to date or if there are changes to
        be applied.
        """

        # if last commit in the strategy was a merge, then the additional
        # branches that were merged in previously can be extracted based on
        # the commits merged.
        if len(strategy) > 0:
            prev_import_merge = strategy[-1]
        else:
            # no changes carried?
            prev_import_merge = None

        additional_commits = None
        if prev_import_merge and len(prev_import_merge.parents) > 1:
            additional_commits = {
                commit for commit in prev_import_merge.parents
                if commit.hexsha != strategy.previous_upstream.hexsha}

            if (additional_commits and
                    len(self.extra_branches) != len(additional_commits)):
                self.log.warning("""
                    **************** WARNING ****************
                    Previous import merged additional branches but none have
                    been specified on the command line for this import.\n""")

        # detect if nothing to do
        if (strategy.previous_upstream.hexsha ==
                self.git.rev_parse(self.upstream)):
            self.log.notice("%s already at latest upstream commit: '%s'",
                            self.branch, strategy.previous_upstream)
            if additional_commits is None:
                self.log.notice("Nothing to be imported")
                return True
            else:
                new_additional_commits = {Commit.new(self.repo, branch)
                                          for branch in self.extra_branches}
                if new_additional_commits == additional_commits:
                    self.log.notice(
                        """
                        No updated additional branch given, nothing to be done
                        """)
                    return True

        return False
