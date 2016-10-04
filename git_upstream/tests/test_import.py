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

from git_upstream.tests import base

import_command = __import__("git_upstream.commands.import", globals(),
                            locals(), ['ImportUpstream'])
ImportUpstream = import_command.ImportUpstream


class TestImport(base.BaseTestCase):

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

        self.gittree = base.BuildTree(self.testrepo, tree, branches.values())
        iu = ImportUpstream("master", "upstream/master", "import")
        iu.finish()
        self.assertEqual("", self.git.status(porcelain=True),
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

        self.gittree = base.BuildTree(self.testrepo, tree, branches.values())
        iu = ImportUpstream("master", "upstream/master", "import")
        # create a dummy file
        open('dummy-file', 'a').close()
        iu.finish()
        self.assertEqual("?? dummy-file", self.git.status(porcelain=True),
                         "ImportUpstream.finish() failed to leave user "
                         "files not managed untouched.")

    def test_import_create_import_branch_from_tag(self):
        """Test that using a tag to import from uses the correct tag

        Repository layout being checked

          B---C             local/master
         /
        A---D---E           upstream/master (tags: tag-um-1, tag-um-2)

        """

        tree = [
            ('A', []),
            ('B', ['A']),
            ('C', ['B']),
            ('D', ['A']),
            ('E', ['D']),
        ]

        branches = {
            'head': ('master', 'C'),
            'upstream': ('upstream/master', 'E'),
        }

        self.gittree = base.BuildTree(self.testrepo, tree, branches.values())
        self.git.tag("tag-um-1", "upstream/master")
        self.git.tag("tag-um-2", "upstream/master")
        iu = ImportUpstream("master", "tag-um-1", "import/{describe}")
        # create import
        iu.create_import()
        self.assertEqual(iu.import_branch, "import/tag-um-1",
                         "ImportUpstream.create_import() failed to use the "
                         "tag 'tag-um-1' for the import branch name")
        # to confirm the tag being used is coming from the user, must
        # test with the other tag to ensure it will use what is given
        # to create the import branch, as 'git describe' can sometimes
        # simply return one of the two tags applied, while what is
        # desired is that only the tag given is used.
        iu = ImportUpstream("master", "tag-um-2", "import/{describe}")
        # create new import
        iu.create_import()
        self.assertEqual(iu.import_branch, "import/tag-um-2",
                         "ImportUpstream.create_import() failed to use the "
                         "tag 'tag-um-2' for the import branch name")
