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

import datetime
import os
import shlex
import subprocess

VERBOSE = os.environ.get('VERBOSE', False)


def run_command(cmd, status=False, env={}):
    if VERBOSE:
        print(datetime.datetime.now(), "Running:", cmd)
    cmd_list = shlex.split(str(cmd))
    newenv = os.environ
    newenv.update(env)
    p = subprocess.Popen(cmd_list, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, env=newenv)
    (out, nothing) = p.communicate()
    out = out.decode('utf-8')
    if status:
        return (p.returncode, out.strip())
    return out.strip()


def git_describe_version():
    try:
        v = run_command('git describe --tags --dirty')
    except RuntimeError:
        pass

    return v


def get_version():
    try:
        return git_describe_version()
    except:
        pass

    return 'unknown-version'


version = get_version()
