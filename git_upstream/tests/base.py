# Copyright 2010-2011 OpenStack Foundation
# Copyright (c) 2013-2016 Hewlett-Packard Enterprise Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import io
import logging
import os
from pprint import pformat
import re
import subprocess
import tempfile

import fixtures
import git
import loremipsum
import testtools
from testtools.content import text_content
import yaml


def _get_node_to_pick(node):
    m = re.search(r'(.*)(\d+)$', node)
    if m:
        # get copy of a another change
        node_number = int(m.group(2)) - 1
        node_name = m.group(1)
        if node_number > 0:
            node_name += str(node_number)
        return node_name
    return None


_NOT_VISITED = 0
_VISITED = 1
_FINISHED = 2


def reverse_toposort(data):

    # convert to dict for linear lookup times when returning
    data = dict(data)

    # keep track of nodes visited and processed
    # by checking if a child has been visited before but not processed you
    # can detect a back edge and abort since the graph is not acyclic
    visited = dict()

    # DFS algorithm with customization to handle use of '=' notation for merge
    # commits and also the additional dependency for cherry-picking
    nodes_to_visit = []
    for i in data.keys():
        if i not in visited:
            nodes_to_visit.append(i)

        while nodes_to_visit:
            node = nodes_to_visit.pop()
            if visited.get(node) is _VISITED:
                # already visited so just return it with it's deps
                yield (node, data[node])
                visited[node] = _FINISHED
                continue

            visited[node] = _VISITED
            nodes_to_visit.append(node)
            # special case for cherry-picking changes
            c_node = _get_node_to_pick(node)
            if c_node and c_node not in visited:
                nodes_to_visit.append(c_node)

            for d in data[node]:
                r_d = d.strip('=')
                if r_d not in visited:
                    nodes_to_visit.append(r_d)
                else:
                    # if we've already visited a dep but not processed it,
                    # then we have a back edge of some kind
                    if visited[r_d] is _VISITED:
                        message = ("Graph is not acyclic: %s is a dependency "
                                   "of %s, but has been visited without being "
                                   "processed before it." % (r_d, node))
                        raise RuntimeError(message)


def get_scenarios(scenarios_path):
    """Returns a list of scenarios, each scenario being describe
    by it's name, and a dict containing the parameters
    """

    scenarios = []
    for root, dirs, files in os.walk(scenarios_path):
        for f in files:
            if os.path.splitext(f)[-1] in ['.yaml', '.yml']:
                filename = os.path.join(root, f)
                with io.open(filename, 'r', encoding='utf-8') as yaml_file:
                    data = yaml.load(yaml_file)[0]
                # convert any keys with dashes to underscores for easy access
                data = {key.replace('-', '_'): value
                        for key, value in data.items()}
                test_name = os.path.splitext(
                    os.path.relpath(filename, scenarios_path))[0]
                data['name'] = test_name
                scenarios.append((filename, data))
    return scenarios


class DiveDir(fixtures.Fixture):
    """Dive into given directory and return back on cleanup.

    :ivar path: The target directory.
    """

    def __init__(self, path):
        super(DiveDir, self).__init__()
        self.path = path

    def _setUp(self):
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.path)


class GitRepo(fixtures.Fixture):
    """Create an empty git repo in which to operate."""

    def __init__(self, path=None):
        self.path = path

    def _setUp(self):
        self._file_list = set()
        if not self.path:
            tempdir = self.useFixture(fixtures.TempDir())
            self.path = os.path.join(tempdir.path, 'git')

        os.mkdir(self.path)
        g = git.Git(self.path)
        g.init()

        self.repo = git.Repo(self.path)
        self.repo.git.config('user.email', 'user@example.com')
        self.repo.git.config('user.name', 'Example User')
        self._create_file_commit()

    def _create_file(self, contents=None):
        if not contents:
            contents = "\n\n".join(loremipsum.get_paragraphs(3))

        # always want to ensure the files added to the repo are unique no
        # matter which branch they are added to, as otherwise there may
        # be conflicts caused by replaying local changes and performing
        # merges
        while True:
            tmpfile = tempfile.NamedTemporaryFile(dir=self.repo.working_dir,
                                                  delete=False)
            if tmpfile.name not in self._file_list:
                self._file_list.add(tmpfile.name)
                break
            tmpfile.close()
            os.remove(tmpfile.name)
        tmpfile.write(contents.encode('utf-8'))
        tmpfile.close()
        return tmpfile.name

    def _create_file_commit(self, change_id=None, message_prefix=None):
        filename = self._create_file()
        self.repo.git.add(filename)
        message = "Adding %s" % os.path.basename(filename)
        if message_prefix:
            message = "%s %s" % (message_prefix, message)
        if change_id:
            message = message + "\n\nChange-Id: %s" % change_id
        self.repo.git.commit(m=message)

    def add_commits(self, num=1, ref="HEAD", change_ids=[],
                    message_prefix=None):
        """Create the given number of commits using generated files"""
        if ref != "HEAD":
            self.repo.git.checkout(ref)

        num = max(num, len(change_ids))
        ids = list(change_ids) + [None] * (num - len(change_ids))

        for x in range(num):
            self._create_file_commit(ids[x], message_prefix=message_prefix)


class BuildTree(object):

    def __init__(self, gitrepo, tree, branches):
        self.graph = {}
        self.gitrepo = gitrepo
        self.repo = gitrepo.repo
        self.git = self.gitrepo.repo.git
        self._build_git_tree(tree, branches)

    def _commit(self, node):
        p_node = _get_node_to_pick(node)
        if p_node:
            self.git.cherry_pick(self.graph[p_node])
        else:
            # standard commit
            self.gitrepo.add_commits(1, ref="HEAD",
                                     message_prefix="[%s]" % node)

    def _merge_commit(self, node, parents):
        # merge commits
        parent_nodes = [p.lstrip("=") for p in parents]
        commits = [str(self.graph[p]) for p in parent_nodes[1:]]

        if any([p.startswith("=") for p in parents]):
            # special merge commit using inverse of 'ours' by
            # emptying the current index and then reading in any
            # trees of the nodes prefixed with '='
            use = [str(self.graph[p.lstrip("=")])
                   for p in parents if p.startswith("=")]
            self.git.merge(*commits, s="ours", no_commit=True)
            self.git.read_tree(empty=True)
            self.git.read_tree(*use, u=True, reset=True)
        elif len(commits) < 2:
            # standard merge
            self.git.merge(*commits, no_commit=True)
        else:
            # multi-branch merge, git is not great at handling
            # merging multiple orphaned branches
            self.git.merge(*commits, s="ours", no_commit=True)
            self.git.read_tree(empty=True)
            self.git.read_tree("HEAD", *commits)
            self.git.checkout("--", ".")
        self.git.commit(m="[%s] Merging %s into %s" %
                        (node, ",".join(parent_nodes[1:]),
                            parent_nodes[0]))
        self.git.clean(f=True, d=True, x=True)

    def _build_git_tree(self, graph_def, branches=[]):
        """Helper function to build a git repository from a graph definition
        of nodes and their parent nodes. A list of branches may be provided
        where each element has two members corresponding to the name and the
        target node it references.

        Supports unordered graphs, only requirement is that there is a commit
        defined with no parents, which will become the root commit.

        Root commits can specified by an empty list as the second member:

            ('NodeA', [])

        Merge commits are specified by multiple nodes:

            ('NodeMerge', ['Node1', 'Node2'])


        As the import subcommand to git-upstream supports a special merge
        commit that ignores all previous history from the other tree being
        merged in using the 'ours' strategy. You specify this by defining
        a parent node as '=<Node>'. The resulting merge commit contains just
        the contents of the tree from the specified parent while still
        recording the parents.

        Following will result in a merge commit 'C', with parents 'P1' and
        'P2', but will have the same tree as 'P1'.

            ('C', ['=P1', 'P2'])


        The tree building code can handle a graph definition being out of
        order but will fail to find certain circular dependencies and may
        result in an infinite loop.

        Examples:

            [('A', []), ('B', ['A']), ('C', ['B'])]
            [('A', []), ('C', ['B']), ('B', ['A'])]
        """

        # require that graphs must have at least 1 node with no
        # parents, which is a root commit in git
        if not any([True for _, parents in graph_def if not parents]):
            assert("No root commit defined in test graph")

        for node, parents in reverse_toposort(graph_def):
            if not parents:
                # root commit
                self.git.symbolic_ref("HEAD", "refs/heads/%s" % node)
                self.git.rm(".", r=True, cached=True)
                self.git.clean(f=True, d=True, x=True)
                self.gitrepo.add_commits(1, ref="HEAD",
                                         message_prefix="[%s]" % node)
                # only explicitly listed branches should exist afterwards
                self.git.checkout(self.repo.commit())
                self.git.branch(node, D=True)

            else:
                # checkout the dependent node
                self.git.checkout(self.graph[parents[0].lstrip('=')])
                if len(parents) > 1:
                    # merge commits
                    self._merge_commit(node, parents)
                else:
                    self._commit(node)
            self.graph[node] = self.repo.commit()

        for name, node in branches:
            self.git.branch(name, str(self.graph[node]), f=True)

        # return to master
        self.git.checkout("master")

    def _commits_from_nodes(self, nodes=[]):

        return [self.graph[n] for n in nodes]


class BaseTestCase(testtools.TestCase):
    """Base Test Case for all tests."""

    logging.basicConfig()

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.logger = self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))
        self.testrepo = self.useFixture(GitRepo())
        repo_path = self.testrepo.path
        self.useFixture(DiveDir(repo_path))

        self.repo = self.testrepo.repo
        self.git = self.repo.git

        self.addOnException(self.attach_graph_info)

        # _testMethodDoc is a hidden attribute containing the docstring for
        # the given test, useful for some tests where description is not
        # yet defined.
        if getattr(self, '_testMethodDoc', None):
            self.addDetail('description', text_content(self._testMethodDoc))

        self.gittree = None
        if hasattr(self, 'tree'):
            self.gittree = BuildTree(
                self.testrepo, self.tree, self.branches.values())

        if hasattr(self, 'pre_script'):
            self.run_pre_script()

        # enable logging of GitPython if not already set
        if os.environ.get("GIT_PYTHON_TRACE") is None:
            type(self.git).GIT_PYTHON_TRACE = "1"

    def run_pre_script(self):
        """
        Run custom pre-script for test

        Method which executes the pre-script defined for the test to perform
        custom manipulation to the git tree to be tested before the test is
        executed.
        """
        # ensure we execute within context of the git repository
        with DiveDir(self.testrepo.path):
            try:
                output = subprocess.check_output(
                    ["python", "-c", self.pre_script],
                    stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.addDetail('pre-script-output',
                               text_content(e.output.decode('utf-8')))
                raise

        self.addDetail('pre-script-output',
                       text_content(output.decode('utf-8')))

    def run_post_script(self):
        """
        Run custom post-script for test

        Method which executes the post-script defined for the test to perform
        steps needed after initial execution of git-upstream has completed.

        Generally it is only required where testing use cases involving
        conflicts requiring simulating manual intervention to verify that
        subsequent finish steps complete and result in the expected state.
        """
        # ensure we execute within context of the git repository
        with DiveDir(self.testrepo.path):
            try:
                output = subprocess.check_output(
                    ["python", "-c", self.post_script],
                    stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                self.addDetail('post-script-output',
                               text_content(e.output.decode('utf-8')))
                raise

        self.addDetail('post-script-output',
                       text_content(output.decode('utf-8')))

    def attach_graph_info(self, exc_info):
        # appears to be an odd bug where this method is called twice
        # if registered with addOnException so make sure to guard
        # that the path actually exists before running
        if not (hasattr(self.testrepo, 'path') and
                os.path.exists(self.testrepo.path)):
            return

        if not self.gittree or not self.gittree.graph:
            return
        self.addDetail('graph-dict', text_content(pformat(self.gittree.graph)))

        self.addDetail(
            'git-log-with-graph',
            text_content(self.repo.git.log(graph=True, oneline=True,
                                           decorate=True, all=True,
                                           parents=True)))
