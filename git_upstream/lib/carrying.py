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

from git_upstream.errors import GitUpstreamError
from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin


class CarryingError(GitUpstreamError):
    """Exception thrown by L{Carrying}"""
    pass


class Carrying(LogDedentMixin, GitMixin):
    """Show list of commits carried that are not upstream.

    """

    def __init__(self, upstream, unknownargs=None, *args, **kwargs):

        # make sure to correctly initialize inherited objects before performing
        # any computation
        super(Carrying, self).__init__(*args, **kwargs)

        # test that we can use this git repo
        if self.is_detached():
            raise CarryingError("In 'detached HEAD' state")

        self.upstream = upstream

        self.log.notice(self.git.log('--dense',
                                     unknownargs,
                                     '{0}..HEAD'.format(self.upstream),
                                     '--',
                                     '.'))

# vim:sw=4:sts=4:ts=4:et:
