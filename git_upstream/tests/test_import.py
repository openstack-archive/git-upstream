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

"""Tests for the 'import' module"""

from base import BaseTestCase

import_command = __import__("git_upstream.commands.import", globals(),
                            locals(), ['ImportUpstream'], -1)
ImportUpstream = import_command.ImportUpstream


class TestImport(BaseTestCase):

    def test_import_finish_merge_clean(self):
        """Test that after finishing the import merge that the users working
        tree is correctly updated to avoid it looking like there are
        uncommitted changes

        Repository layout being checked (assumed already replayed)

            B---C           local/master
           /
          /       C1        import
         /       /
        A---D---E           upstream/master

        Test that ImportUpstream.finish() results in a clean working tree and
        index

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['A']),
            ('E', ['D']),
            ('C1', ['E'])
        ]

        branches = {
            'head': ('master', 'C'),
            'upstream': ('upstream/master', 'E'),
            'import': ('import', 'C1')
        }

        self._build_git_tree(tree, branches.values())
        iu = ImportUpstream("master", "upstream/master", "import")
        iu.finish()
        self.assertEquals("", self.git.status(porcelain=True),
                          "ImportUpstream.finish() failed to result in a "
                          "clean working tree and index")

    def test_import_finish_merge_extra_files(self):
        """Test that after finishing the import merge when the users working
        tree is updated that any additional files not being managed by git are
        left untouched

        Repository layout being checked (assumed already replayed)

            B---C           local/master
           /
          /       C1        import
         /       /
        A---D---E           upstream/master

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['A']),
            ('E', ['D']),
            ('C1', ['E'])
        ]

        branches = {
            'head': ('master', 'C'),
            'upstream': ('upstream/master', 'E'),
            'import': ('import', 'C1')
        }

        self._build_git_tree(tree, branches.values())
        iu = ImportUpstream("master", "upstream/master", "import")
        # create a dummy file
        open('dummy-file', 'a').close()
        iu.finish()
        self.assertEquals("?? dummy-file", self.git.status(porcelain=True),
                          "ImportUpstream.finish() failed to leave user "
                          "files not managed untouched.")
