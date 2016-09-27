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

from abc import ABCMeta
from abc import abstractmethod
import itertools
import re

from git_upstream import errors
from git_upstream import lib
from git_upstream.lib.pygitcompat import Commit
from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin


class Searcher(GitMixin):
    """
    Base class that needs to be extended with the specific searcher on how to
    locate changes.
    """
    __metaclass__ = ABCMeta

    def __init__(self, branch="HEAD", *args, **kwargs):

        self._branch = branch

        self.filters = []
        self.commit = None

        super(Searcher, self).__init__(*args, **kwargs)

    @property
    def branch(self):
        """
        Default branch in the git repository to search.
        """
        return self._branch

    def add_filter(self, filter):
        if filter not in self.filters:
            self.filters.append(filter)

    @abstractmethod
    def find(self):
        """
        Implementation of this method should return a commit SHA1 that will be
        used by the generic list() method as the start commit to list commits
        from, to the tip of the branch or commit given in the constructor.

        In additional it must save a 'Commit' object for the found SHA1 as the
        self.commit property.
        """
        pass

    def _check_merge_is_previous(self, mergecommit, parent, last_merge):
        """Check if merge commit and parent describes previous import

        Method checks if the given merge and parent commits describe a
        previous import merge commit and returns a tuple of the merge
        commit if it is the previous import merge, and a list of additional
        commits to be excluded from any history when looking for carried
        changes.
        """

        mergebase = self.git.merge_base(parent, self.commit,
                                        with_exceptions=False)
        self.log.debug(
            """
            previous upstream: %s
            merge-base: %s
            parent: %s
            """, self.commit, mergebase, parent.hexsha)

        # if not a valid response from merge-base, we have an additional
        # branch with unrelated history, and should ignore all parents
        if not mergebase:
            self.log.info(
                """
                Found merge of additional branch:
                    %s
                """, mergecommit)
            return None, ["^%s" % mp for mp in mergecommit.parents]

        # if the parent tree doesn't match the merge commit tree, we can
        # skip inspecting it as it and it's parent commit must be
        # included as it contributes changes to the tree.
        if (self.git.rev_parse("%s^{tree}" % parent) !=
                self.git.rev_parse("%s^{tree}" % mergecommit)):
            return None, []

        # otherwise we have a descendant commit with the same tree that
        # requires further inspection to determine if it is really the
        # previous import merge.

        # if the parent is not a descendent of the previous upstream, will
        # need to determine whether to exclude
        if mergebase != self.commit.hexsha:
            # if we're checking the last merge in the list, then looking at
            # the previous mainline that was replaced and should ignore
            if mergecommit == last_merge:
                # also means we've found the previous import
                return mergecommit, ["^%s" % parent]

            # otherwise this an unusual state where we are looking at the
            # merge of the previous import with a change that landed on the
            # previous target mainline but was not included in the changes
            # that where on the previous import. This can occur due to a
            # change being approved/landed after the import was performed
            return None, []

        # otherwise looking at the previous import merge commit and the parent
        # from the previous import branch, so exclude all other parents.
        return mergecommit, ["^%s" % ip
                             for ip in mergecommit.parents if ip != parent]

    def list(self, upstream=None):
        """
        Returns a list of Commit objects, between the '<commitish>' revision
        given in the constructor, and the commit object returned by the find()
        method. If given an upstream branch, uses --cherry-pick/--left-only to
        exclude commits that are identical to those already on the upstream
        branch.
        """
        if not self.commit:
            self.find()

        revision_spec = "{0}..{1}".format(self.commit.hexsha, self.branch)

        # search for previous import commit first, if found, wish to include
        # the discarded parents as part of the set of changes to ignore in the
        # final list.
        self.log.debug(
            """
            Searching for previous merges that exclude one side of the history
            since the last import.
                git rev-list --ancestry-path --merges %s
            """, revision_spec)

        merge_list = list(Commit.iter_items(self.repo, revision_spec,
                                            topo_order=True,
                                            ancestry_path=True, merges=True))
        extra_args = []
        previous_import = False
        for mergecommit, parent in ((mc, p)
                                    for mc in merge_list
                                    for p in mc.parents):
            # inspect each
            previous_import, ignores = self._check_merge_is_previous(
                mergecommit, parent, merge_list[-1])

            if ignores:
                self.log.debug(
                    """
                    Adding following to ignore list:
                        %s
                    """, "\n    ".join(ignores))
                extra_args.extend(ignores)

            if previous_import:
                self.log.info(
                    """
                    Found the previous import merge:
                        %s
                    """, mergecommit)
                break

        # walk the tree and find all commits that lie in the path between the
        # commit found by find() and head of the branch in two steps, to
        # ensure a deterministic order between what is from the previous
        # upstream to the last import, and from that import to what is on
        # the tip of the head to avoid inversion where older commits
        # started before the previous import merge and approved afterwards
        # are not sorted by 'rev-list' predictably.
        commit_list = []
        if upstream is None:
            if previous_import:
                search_list = [
                    (previous_import, self.branch, None),
                    (self.commit, previous_import, None),
                ]
            else:
                search_list = [(self.commit, self.branch, None)]
            rev_spec = "{0}..{1}"
            git_args = {}
        else:
            if previous_import:
                search_list = [
                    (self.branch, upstream, "^%s" % previous_import),
                    (previous_import, upstream, "^%s~1" % previous_import)
                ]
            else:
                search_list = [(self.branch, upstream, None)]
            rev_spec = "{0}...{1}"
            git_args = {'cherry_pick': True, 'left_only': True}
            extra_args.append("^%s" % self.commit)

        for start, end, exclude in search_list:
            extra = list(extra_args)
            if exclude:
                extra.append(exclude)
            extra.append("--")
            revision_spec = rev_spec.format(start, end)
            self.log.info(
                """
                Walking the changes between found commit and target, excluding
                those behind the previous import or merged as an additional
                branch during the previous import
                    git rev-list --topo-order %s %s %s
                """, self.git.transform_kwargs(**git_args), revision_spec,
                " ".join(extra))

            commit_list.append(
                Commit._iter_from_process_or_stream(
                    self.repo,
                    self.git.rev_list(revision_spec,
                                      *extra,
                                      as_process=True,
                                      topo_order=True,
                                      **git_args)))

        # chain the filters as generators so that we don't need to allocate new
        # lists for each step in the filter chain.
        commit_list = itertools.chain(*commit_list)
        for f in self.filters:
            commit_list = f.filter(commit_list)

        commits = list(commit_list)

        self.log.debug(
            """
            commits found:
                %s
            """, ("\n" + " " * 4).join([c.hexsha for c in commits]))

        return commits


class NullSearcher(Searcher):
    """
    This searcher returns an empty list
    """

    def list(self):
        return []


class UpstreamMergeBaseSearcher(LogDedentMixin, Searcher):
    """
    Searches upstream references for a merge base with the target branch. By
    default this will search the 'upstream/*' namespace but can be overridden
    to search any namespace pattern.

    If not restricted to search specific remotes, it will search all
    available remote references matching the pattern for the most recent merge
    base available.
    """

    def __init__(self, branch, patterns=None, search_tags=False, remotes=None,
                 *args, **kwargs):

        super(UpstreamMergeBaseSearcher, self).__init__(branch, *args,
                                                        **kwargs)

        if not patterns:
            patterns = ["upstream/*"]
        self._patterns = set()
        self._revs = set()
        for rev in patterns:
            if "*" in rev:
                self._patterns.add(rev)
            elif self.is_valid_commit(rev):
                self._revs.add(rev)
            else:
                raise errors.GitUpstreamError(
                    "'%s' not recognized as valid commit(ish) or pattern" %
                    rev)

        self._references = ["refs/heads/{0}".format(ref)
                            for ref in self.patterns]

        if not remotes:
            remotes = []

        if remotes:
            self._references.extend(
                ["refs/remotes/{0}/{1}".format(s, ref)
                 for s in remotes for ref in self.patterns])
        else:
            self._references.extend(
                ["refs/remotes/*/{0}".format(ref) for ref in self.patterns])

        if search_tags:
            self._references.extend(
                ["refs/tags/{0}".format(ref) for ref in self.patterns])

    @property
    def patterns(self):
        """
        Pattern to limit which references are searched when looking for a
        merge base commit.
        """
        return self._patterns

    def find(self):
        """
        Searches the git history including local and remote branches, and tags
        if tag searching is enabled. References are included in the list to be
        checked if they match the pattern that was specified in the
        constructor.
        While 'git rev-list' supports a glob option to check all references, it
        isn't possible to anchor the pattern, so 'upstream/*' would match all
        of the following:
            refs/remotes/origin/upstream/master
            refs/heads/upstream/master
            refs/remotes/origin/other/upstream/area <--- undesirable

        Additional since 'git rev-list' doesn't accept patterns as commit refs
        it's better to make use of 'git for-each-ref' and how it does pattern
        matching in order to generate a list of references to pass to rev-list
        to walk.

        After determining all the references to look at, because of the
        overhead in using 'git merge-base' to determine the last commit from
        one of the upstream refs that was merged into the target branch, it is
        worth going to the additional effort of removing any reference that is
        reachable from another so that the calls to merge-base are minimized.
        """

        self.log.info(
            "Searching for most recent merge base with upstream branches")

        # process pattern given to get a list of refs to check
        if self._references:
            rev_list_args = self.git.for_each_ref(
                *self._references, format="%(refname:short)").splitlines()
        else:
            rev_list_args = []
        rev_list_args.extend(self._revs)
        self.log.info(
            """
            Upstream refs:
                %s
            """, "\n    ".join(rev_list_args)
        )

        # get the sha1 for the tip of each of the upstream refs we are going to
        #  search
        self.log.info(
            """
            Construct list of upstream revs to search:
                git rev-list --min-parents=1 --no-walk \\
                    %s
            """, (" \\\n" + " " * 8).join(rev_list_args))
        rev_list_args.append("--")
        search_list = set(self.git.rev_list(*rev_list_args,
                                            min_parents=1,
                                            no_walk=True).splitlines())
        rev_list_args = list(search_list)

        # construct a list of the parents of each ref so that we can tell
        # rev-list to ignore in the anything reachable from the list commits
        # which reduces the amount of revs to be searched with merge-base
        prune_list = []
        for rev in search_list:
            # only root commits won't have at least one parent which have been
            # excluded by the previous search
            commit = self.git.rev_list(rev, "--", parents=True,
                                       max_count=1).split()
            parents = commit[1:]
            prune_list.extend(parents)

        # We want to stop walking the tree and ignore all commits after each
        # time we encounter one from the prune_list, so make sure to set the
        # --not option followed by the list of revisions to exclude. Since
        # python-git may reorder options if given by way or keyword args, use
        # strings in the required order as '*args' are not reordered, and
        # order is critical here to ensure rev-list applies the '--not'
        # behaviour to the correct set.
        rev_list_args.append("--not")
        rev_list_args.extend(prune_list)
        self.log.info(
            """
            Retrieve minimal list of revs to check with merge-base by excluding
            revisions that are in the reachable from others in the list:
                git rev-list \\
                    %s
            """, " \\\n        ".join(rev_list_args))
        rev_list_args.append("--")
        revsions = self.git.rev_list(*rev_list_args).splitlines()

        # Running 'git merge-base' is relatively expensive to pruning the list
        # of revs to search since it needs to construct and walk a large
        # portion of the tree for each call. If the constructed graph was
        # retained betweens we could likely remove much of the code above.
        self.log.info(
            """
            Running merge-base against each found upstream revision and target
                git merge-base %s ${upstream_rev}
            """, self.branch)
        merge_bases = set()
        for rev in revsions:
            # ignore exceptions as there may be unrelated branches picked up by
            # the searching which would result in merge-base returning an error
            base = self.git.merge_base(self.branch, rev, with_exceptions=False)
            if base:
                merge_bases.add(base)

        if len(merge_bases) == 0:
            self.log.notice("Merge-base couldn't be found: it seems there " +
                            "is no common ancestor for the involved branches")
        else:
            self.log.info(
                """
                Order the possible merge-base commits in descendent order, to
                find the most recent one used irrespective of date:
                    git rev-list --topo-order --max-count=1 --no-walk \\
                        %s
                """, (" \\\n" + " " * 8).join(merge_bases))
            args = list(merge_bases) + ["--"]
            sha1 = self.git.rev_list(*args, topo_order=True, max_count=1)
            # now that we have the sha1, make sure to save the commit object
            self.commit = self.repo.commit(sha1)
            self.log.debug("Most recent merge-base commit is: '%s'",
                           self.commit.hexsha)

        if not self.commit:
            raise RuntimeError("Failed to locate suitable merge-base")

        return self.commit.hexsha


class CommitMessageSearcher(LogDedentMixin, Searcher):
    """
    This searcher returns a list of commits based on looking for commit message
    containing a specific message in the current branch.
    """

    def __init__(self, pattern, *args, **kwargs):
        self._pattern = pattern

        super(CommitMessageSearcher, self).__init__(*args, **kwargs)

    @property
    def pattern(self):
        """
        Pattern to search commit messages in the target branch for a match.
        """
        return self._pattern

    def find(self):
        """
        Searches the git history of the target branch for a commit message
        containing the pattern given in the constructor. This is used as a base
        commit from which to return a list of commits since this point.
        """

        commits = Commit.iter_items(self.repo, self.branch, grep=self.pattern,
                                    max_count=1, extended_regexp=True)

        self.commit = next(commits, None)
        if not self.commit:
            raise RuntimeError("Failed to locate a pattern match")

        self.log.debug("Commit matching search pattern is: '%s'",
                       self.commit.hexsha)

        return self.commit.hexsha

    def list(self, upstream=None, include=True):
        """
        Override parent implementation to permit inclusion of the found commit
        to be returned in the list of changes. This will help in cases where
        then commit is a specific merge including the additionally merged
        branches that would be returned by the generic upstream searcher.
        """

        commits = super(CommitMessageSearcher, self).list(upstream)
        if include:
            commits.append(self.commit)

        return commits


class CommitFilter(object):
    """
    CommitFilter instances are used to perform arbitrary filtering of commits
    returned by searchers.
    """
    __metaclass__ = ABCMeta

    def __init__(self, *args, **kwargs):
        super(CommitFilter, self).__init__(*args, **kwargs)

    @abstractmethod
    def filter(self, commit_iter):
        pass


class SupersededCommitFilter(LogDedentMixin, GitMixin, CommitFilter):
    """
    Prunes all commits that have a note with the "Superseded-by:" header
    containing a Change-Id present in upstream tracking branch

    :param string search_ref: git reference to search for ChangeIds (required).
    :param Commit limit: commit object to ignore searching history after
                        (optional).
    """

    def __init__(self, search_ref, limit=None, *args, **kwargs):

        super(SupersededCommitFilter, self).__init__(*args, **kwargs)

        if not self.is_valid_commit(search_ref):
            raise ValueError("Invalid value for 'search_ref': %s" % search_ref)
        self.search_ref = search_ref

        if limit:
            if not hasattr(limit, 'hexsha'):
                raise ValueError(
                    "Invalid object: no hexsha attribute for 'limit'")
            if not self.is_valid_commit(limit.hexsha):
                raise ValueError(
                    "'limit' object does not contain a valid SHA1")
        self.limit = limit

        self._regex = None

    def _get_rev_range(self):

        if self.limit:
            return "%s..%s" % (self.limit.hexsha, self.search_ref)
        else:
            return self.search_ref

    def _get_change_id(self, commit):
        """
        Returns the Change-Id string from the footer of the given commit.

        Will ignore any instances outside of the footer section
        """
        # read the commit message in reverse to access the
        # footer first but ignore subject and first blank line
        for line in reversed(commit.message.splitlines()[1:]):
            line = line.strip()
            # exit on the first blank line found since that indicates
            # we're reached the top of the footer section
            if not line:
                break

            cid = re.search('^Change-Id:\s*(.+)$', line, re.IGNORECASE)
            if cid:
                return cid.group(1)
        return

    def filter(self, commit_iter):

        self.log.info(
            """
            Filtering out all commits marked with a Superseded-by Change-Id
            which is present in '%s'
            """, self.search_ref)

        supersede_re = re.compile('^%s\s*(.+)\s*$' %
                                  lib.SUPERSEDE_HEADER,
                                  re.IGNORECASE | re.MULTILINE)

        for commit in commit_iter:
            commit_note = commit.note(note_ref=lib.IMPORT_NOTE_REF)
            # include non-annotated commits
            if not commit_note:
                yield commit
                continue

            # include annotated commits which don't have a SUPERSEDE_HEADER
            superseding_change_ids = supersede_re.findall(commit_note)
            if not superseding_change_ids:
                yield commit
                continue

            # search for all the change-ids in matches (egrep regex)
            commits_grep_re = '^Change-Id:\\s*\(%s\)\\s*$' % \
                              '\|'.join(superseding_change_ids)

            # retrieve all matching commits because we need to check
            # each match for whether the changeId is actually in
            # the footer or just included as a reference.
            matching_commits = Commit.iter_items(self.repo,
                                                 self._get_rev_range(),
                                                 regexp_ignore_case=True,
                                                 grep=commits_grep_re)

            for possible in matching_commits:
                change_id = self._get_change_id(possible)
                if change_id:
                    superseding_change_ids.remove(change_id)

            # include commits which have some superseding change-ids not
            # present in upstream
            if superseding_change_ids:
                self.log.debug(
                    """
                Including commit '%s %s'
                    because the following superseding change-ids have not been
                    found:
                    %s
                """, commit.short, commit.message.splitlines()[0],
                    '\n    '.join(superseding_change_ids))
                yield commit
                continue

            self.log.debug(
                """
                Filtering out commit '%s %s'
                    because it has been marked as superseded by the following
                    note:
                    %s
                """, commit.short, commit.message.splitlines()[0],
                commit_note)


class DroppedCommitFilter(LogDedentMixin, CommitFilter):
    """
    Prunes all commits that have a note with the Dropped: header
    """

    def filter(self, commit_iter):
        for commit in commit_iter:
            commit_note = commit.note(note_ref=lib.IMPORT_NOTE_REF)
            if not commit_note:
                yield commit
            elif not re.match('^%s.+' % lib.DROP_HEADER,
                              commit_note, re.IGNORECASE | re.MULTILINE):
                yield commit
            else:
                self.log.debug("Dropping commit '%s' as requested:", commit)
                self.log.debug(commit_note)


class MergeCommitFilter(CommitFilter):
    """
    Includes only those commits that have more than one parent listed (merges)
    """

    def filter(self, commit_iter):
        for commit in commit_iter:
            if len(commit.parents) >= 2:
                yield commit


class NoMergeCommitFilter(CommitFilter):
    """
    Prunes all that have more than one parent listed (merges)
    """

    def filter(self, commit_iter):
        for commit in commit_iter:
            if len(commit.parents) < 2:
                yield commit


class DiscardDuplicateGerritChangeId(LogDedentMixin, GitMixin, CommitFilter):
    """
    Filter out commit objects where the message footer contains a ChangeId
    string that is already available in the history of commit object provided
    to the constructor.

    ChangeId's are used by the Gerrit Code Review software to track changes
    through multiple amendments, http://code.google.com/p/gerrit/.

    :param string search_ref: git reference to search for duplicate ChangeIds
                             (required).
    :param Commit limit: commit object to ignore searching history after
                        (optional).
    """

    def __init__(self, search_ref, limit=None, *args, **kwargs):

        super(DiscardDuplicateGerritChangeId, self).__init__(*args, **kwargs)

        if not self.is_valid_commit(search_ref):
            raise ValueError("Invalid value for 'search_ref': %s" % search_ref)
        self.search_ref = search_ref

        if limit:
            if not hasattr(limit, 'hexsha'):
                raise ValueError(
                    "Invalid object: no hexsha attribute for 'limit'")
            if not self.is_valid_commit(limit.hexsha):
                raise ValueError(
                    "'limit' object does not contain a valid SHA1")
        self.limit = limit

        self._regex = None

    @property
    def regex(self):
        # compile the regex object on first usage
        if not self._regex:
            self._regex = re.compile("^Change-Id: ", re.I)
        return self._regex

    def _get_rev_range(self):

        if self.limit:
            return "%s..%s" % (self.limit.hexsha, self.search_ref)
        else:
            return self.search_ref

    def _get_change_id(self, commit):
        """
        Returns the Change-Id string from the footer of the given commit.

        Will ignore any instances outside of the footer section
        """
        # read the commit message in reverse to access the
        # footer first but ignore subject and first blank line
        for line in reversed(commit.message.splitlines()[1:]):
            line = line.strip()
            # exit on the first blank line found since that indicates
            # we're reached the top of the footer section
            if not line:
                break
            if self.regex.match(line):
                return line
        return

    def filter(self, commit_iter):

        self.log.info(
            """
            Filtering out all commits that have a Change-Id that matches one
            found in the given search ref: %s
            """, self.search_ref)

        for commit in commit_iter:
            change_id = self._get_change_id(commit)
            # if there is no change_id to compare against, return the commit
            if not change_id:
                self.log.debug(
                    """
                    Including change missing 'Change-Id'
                        Commit: %s %s
                        Message: %s
                    """, commit.short, commit.message.splitlines()[0],
                    commit.message)
                yield commit
                continue

            # retrieve all matching commits because we need to check
            # each match for whether the changeId is actually in
            # the footer or just included as a reference.
            matching_commits = Commit.iter_items(self.repo,
                                                 self._get_rev_range(),
                                                 regexp_ignore_case=True,
                                                 grep="^%s$" % change_id)

            duplicate_change_id = None
            for possible in matching_commits:
                duplicate_change_id = self._get_change_id(possible)
                if duplicate_change_id == change_id:
                    break

            if duplicate_change_id and duplicate_change_id == change_id:
                self.log.debug(
                    """
                    Skipping duplicate Change-Id in search ref
                        %s
                        Commit: %s %s
                    """, change_id, commit.short,
                    commit.message.splitlines()[0])
                continue

            # no match in the search ref, so include commit
            self.log.debug(
                """
                Including unmatched change
                    %s
                    Commit: %s %s
                """, change_id, commit.short,
                commit.message.splitlines()[0])
            yield commit


class TransformCommitToSHA1(CommitFilter):
    """
    Discard 'Commit' objects and simply return the SHA1 id's
    """

    def filter(self, commit_iter):
        for commit in commit_iter:
            yield commit.hexsha


class ReverseCommitFilter(LogDedentMixin, CommitFilter):
    """
    Reverses the list of commits passed.

    As this needs the complete list to work, it is recommended to only use
    once all other filtering is complete as otherwise it will remove the
    memory benefits of using generator behaviour when chaining multiple
    filters.
    """

    def filter(self, commit_iter):
        self.log.debug("Consuming generators to reverse commit list")
        return reversed(list(commit_iter))
