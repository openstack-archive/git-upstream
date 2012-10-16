#!/usr/bin/env python
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


import os
from setuptools import setup, find_packages
from ghp import version

# taken from setuptools example.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "hpgit",
    version = version.version,
    author = "Darragh Bailey",
    author_email = "dbailey@hp.com",
    description = ("Tool supporting HPCloud git workflows."),
    license = "Apache License (2.0)",
    keywords = "git hpcloud workflow",
    url = "https://wiki.hpcloud.net/display/auto/hpgit",
    scripts = ['git-hp'],
    packages = find_packages(exclude=['test']),
    long_description=read('README'),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache License",
    ],
)
