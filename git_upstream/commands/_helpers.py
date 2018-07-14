#
# Copyright (c) 2018 Hewlett Packard Enterprise Company LP
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

# module provides bash autocomplete helper methods

import os

from git import Repo


def upstream_completer(prefix, parsed_args, **kwargs):
    return branch_completer(prefix, parsed_args, include_remotes=True,
                            **kwargs)


def branch_completer(prefix, parsed_args, include_remotes=False,
                     **kwargs):
    repo = Repo(os.environ.get('GIT_UPSTREAM_REPO_PATH', "."))
    refs = repo.heads + repo.tags
    if include_remotes:
        for remote in repo.remotes:
            refs.extend(remote.refs)
    return [str(ref) for ref in refs]
