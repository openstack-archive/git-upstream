#!/usr/bin/env python
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

import os
from setuptools import setup, find_packages
from create_manpage import CreateManpage
from git_upstream import version


# following function is taken from setuptools example.
# https://pypi.python.org/pypi/an_example_pypi_project (BSD)
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

version.write_version_file()

setup(
    name="git-upstream",
    version=version.version,
    author="Darragh Bailey",
    author_email="dbailey@hp.com",
    maintainer="Davide Guerri",
    maintainer_email="davide.guerri@hp.com",
    description="Tool supporting import from upstream.",
    license="Apache Software License",
    keywords="git upstream workflow",
    url="",
    scripts=['git-upstream', os.path.join(os.path.dirname(__file__),
                                          'git_upstream', 'scripts',
                                          'rebase-editor.py')],
    packages=find_packages(exclude=['test']),
    install_requires=['GitPython'],
    long_description=read('README'),
    cmdclass={'create_manpage': CreateManpage},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Utilities",
        "License :: OSI Approved :: Apache Software License"
    ]
)

try:
    import argcomplete
    print('Make sure to copy bash_completion/git-upstream in appropriate ' +
          'location (e.g. ~/.bash_completion)')
except ImportError:
    print('Warning: argcomplete package is not installed, autocomplete will' +
          ' not work.')
