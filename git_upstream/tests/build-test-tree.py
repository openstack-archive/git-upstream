# Copyright (c) 2016 Hewlett-Packard Enterprise Development Company, L.P.
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

# simple tool to read in a scenario in yaml and reproduce the test
# tree to allow for experimentation and investigation.

import io
import os
import shutil
import subprocess
import sys

import yaml

from git_upstream.tests import base

TREE_DIR = ".git-test-trees"


def build_test_tree(basedir, filename):
    data = {}
    with io.open(filename, 'r', encoding='utf-8') as yaml_file:
        data = yaml.load(yaml_file)[0]
    data['name'] = os.path.splitext(os.path.basename(filename))[0]
    test_dir = os.path.join(basedir, data['name'])
    if os.path.exists(test_dir):
        print("Removing previous test tree: '%s'" % test_dir)
        shutil.rmtree(test_dir)

    with base.GitRepo(path=test_dir) as testrepo:
        with base.DiveDir(testrepo.path):

            if 'tree' in data:
                base.BuildTree(testrepo, data['tree'],
                               data['branches'].values())

            if 'pre-script' in data:
                output = subprocess.check_output(data['pre-script'],
                                                 stderr=subprocess.STDOUT,
                                                 shell=True)
                print("pre-script output:\n%s" % output)

    return data


def main():

    if len(sys.argv[1:]) < 1:
        print("Error: must pass the path of the yaml file containing the "
              "test scenario tree to be constructed")
        sys.exit(1)

    scenario_files = sys.argv[1:]

    for f in scenario_files:
        if not os.path.exists(f):
            print("'%s' not found" % f)

    if not os.path.exists(TREE_DIR):
        os.mkdir(TREE_DIR)

    for filename in scenario_files:
        t = build_test_tree(TREE_DIR, filename)
        print("Created test tree: %s" %
              os.path.join(TREE_DIR, t['name']))

if __name__ == '__main__':
    main()
