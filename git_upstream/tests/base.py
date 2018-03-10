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
import subprocess

import fixtures
import fixtures_git
import git
import testtools
from testtools.content import text_content
import yaml


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


class BaseTestCase(testtools.TestCase):
    """Base Test Case for all tests."""

    logging.basicConfig()

    def setUp(self):
        super(BaseTestCase, self).setUp()

        self.logger = self.useFixture(fixtures.FakeLogger(level=logging.DEBUG))

        # _testMethodDoc is a hidden attribute containing the docstring for
        # the given test, useful for some tests where description is not
        # yet defined.
        if getattr(self, '_testMethodDoc', None):
            self.addDetail('description', text_content(self._testMethodDoc))

        if hasattr(self, 'tree'):
            self.testrepo = self.useFixture(
                fixtures_git.GitFixture(
                    graph=self.tree,
                    branches=self.branches.values(),
                )
            )
        else:
            self.testrepo = self.useFixture(
                fixtures_git.GitFixture())

        self.gittree = self.testrepo.gittree

        self.useFixture(DiveDir(self.testrepo.path))

        self.repo = self.testrepo.repo
        self.git = self.repo.git

        self.addOnException(self.attach_repo_info)

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

    def attach_repo_info(self, exc_info):
        # appears to be an odd bug where this method is called twice
        # if registered with addOnException so make sure to guard
        # that the path actually exists before running
        if not os.path.exists(self.testrepo.path):
            return

        # in case we haven't setup yet
        if not self.gittree or not self.gittree.graph:
            return

        self.addDetail('graph-dict', text_content(pformat(self.gittree.graph)))

        self.addDetail(
            'git-log-with-graph',
            text_content(self.repo.git.log(graph=True, oneline=True,
                                           decorate=True, all=True,
                                           parents=True)))
