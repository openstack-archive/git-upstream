#
# Copyright (c) 2012-2015 Hewlett-Packard Development Company, L.P.
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
from abc import abstractproperty
from collections import Sequence

from git_upstream.lib.searchers import DiscardDuplicateGerritChangeId
from git_upstream.lib.searchers import DroppedCommitFilter
from git_upstream.lib.searchers import NoMergeCommitFilter
from git_upstream.lib.searchers import ReverseCommitFilter
from git_upstream.lib.searchers import SupersededCommitFilter
from git_upstream.lib.searchers import UpstreamMergeBaseSearcher
from git_upstream.lib.utils import GitMixin


class ImportStrategiesFactory(object):
    __strategies = None

    @classmethod
    def create_strategy(cls, type, *args, **kwargs):
        if type in cls.list_strategies():
            return cls.__strategies[type](*args, **kwargs)
        else:
            raise RuntimeError("No class implements the requested strategy: "
                               "{0}".format(type))

    @classmethod
    def list_strategies(cls):
        cls.__strategies = {
            subclass._strategy: subclass
            for subclass in LocateChangesStrategy.__subclasses__()
            if subclass._strategy}
        return cls.__strategies.keys()


class LocateChangesStrategy(GitMixin, Sequence):
    """Base locate changes strategy class

    Needs to be extended with the specific strategy on how to handle changes
    that are not yet upstream.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, git=None, *args, **kwargs):
        """Initialize an empty filters list"""
        self.data = None
        self.searcher = None
        self.filters = []
        super(LocateChangesStrategy, self).__init__(*args, **kwargs)

    @abstractproperty
    def previous_upstream(self):
        raise NotImplemented

    def __getitem__(self, key):
        if not self.data:
            self.data = self._popdata()
        return self.data[key]

    def __len__(self):
        if not self.data:
            self.data = self._popdata()
        return len(self.data)

    @classmethod
    def get_strategy_name(cls):
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
        """Should return the list of commits from the searcher object"""
        return self.searcher.list(upstream=self.upstream)


class LocateChangesWalk(LocateChangesStrategy):

    _strategy = "drop"

    def __init__(self, branch="HEAD", upstream="upstream/master",
                 search_refs=None, *args, **kwargs):

        if not search_refs:
            search_refs = []
        search_refs.insert(0, upstream)
        self.upstream = upstream

        super(LocateChangesWalk, self).__init__(*args, **kwargs)

        self.searcher = UpstreamMergeBaseSearcher(
            branch=branch, patterns=search_refs, search_tags=True)

    @property
    def previous_upstream(self):
        if not self.searcher.commit:
            self.searcher.find()

        return self.searcher.commit

    def filtered_iter(self):
        # may wish to make class used to remove duplicate objects configurable
        # through git-upstream specific 'git config' settings
        self.filters.append(
            DiscardDuplicateGerritChangeId(self.upstream,
                                           limit=self.previous_upstream))
        self.filters.append(NoMergeCommitFilter())
        self.filters.append(ReverseCommitFilter())
        self.filters.append(DroppedCommitFilter())
        self.filters.append(
            SupersededCommitFilter(self.upstream,
                                   limit=self.previous_upstream))

        return super(LocateChangesWalk, self).filtered_iter()
