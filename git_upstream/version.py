#
# Copyright (c) 2011, 2012 OpenStack LLC.
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

import datetime
import os
import subprocess

VERBOSE = os.environ.get('VERBOSE', False)


class CommandException(Exception):
    pass


# following function is taken from git-review
def run_command(cmd, status=False, env=None):
    if not env:
        env = {}
    if VERBOSE:
        print(datetime.datetime.now(), "Running:", cmd)
    new_env = os.environ
    new_env.update(env)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=new_env)
    (out, nothing) = p.communicate()
    if p.returncode:
        raise CommandException
    out = out.decode('utf-8')
    if status:
        return (p.returncode, out.strip())
    return out.strip()


def git_describe_version():
    try:
        v = run_command(['git', 'describe', '--tags', '--dirty'])
    except CommandException:
        raise

    return v


def git_upstream_version():
    try:
        from git_upstream import git_upstream_version
    except ImportError:
        raise
    return git_upstream_version.version


def write_version_file():
    try:
        v = git_describe_version()
    except:
        return
    print __name__
    with open(os.path.join(os.path.dirname(__file__),
                           "git_upstream_version.py"), 'w') as f:
        f.write("# Auto-generated file, do not edit by hand")
        f.write("version = %s" % v)


def get_version():
    for vfunc in git_upstream_version, git_describe_version:
        try:
            return vfunc()
        except:
            pass

    return 'unknown-version'


version = get_version()
