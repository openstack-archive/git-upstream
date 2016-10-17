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

from git import base

from git_upstream.lib import note

try:
    from git.objects.commit import Commit
except ImportError:
    from git import Commit

try:
    from git import BadName
except ImportError:
    BadName = object


class GitUpstreamCompatCommit(Commit):

    @property
    def short(self):
        return self.repo.git.rev_parse(self.hexsha, short=True)


base.Object.short = GitUpstreamCompatCommit.short
base.Object.add_note = note.add_note
base.Object.append_note = note.append_note
base.Object.note = note.note_message
