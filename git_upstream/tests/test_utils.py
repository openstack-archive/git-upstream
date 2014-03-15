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

"""Tests for then 'utils' module"""

from git_upstream.lib import utils as u

import testtools

from subprocess import check_output


class TestCheckGitVersion(testtools.TestCase):
    """Test case for check_git_version function"""

    @classmethod
    def get_current_git_version(cls):
        """
        Retrieve system git version, quick and dirty method but need
        to be different from the one used in the actual function tested
        """

        output = check_output(['git', 'version'])
        ver = output.split(' ')[2]
        (_major_s, _minor_s, _revision_s) = ver.split('.')[:3]

        return (int(_major_s), int(_minor_s), int(_revision_s))

    def test_greater_major(self):
        """
        Test failure with a _major version requirement greater than the current
        one
        """

        result = u.check_git_version(999, 0, 0)
        self.assertEquals(False, result)

    def test_greater_minor(self):
        """
        Test failure with a _minor version requirement greater than the current
        one
        """

        _maj = TestCheckGitVersion.get_current_git_version()[0]
        result = u.check_git_version(_maj, 999, 0)
        self.assertEquals(False, result)

    def test_greater_revision(self):
        """
        Test failure with a _revision version requirement greater than the
        current one
        """

        (_maj, _min) = TestCheckGitVersion.get_current_git_version()[:2]
        result = u.check_git_version(_maj, _min, 999)
        self.assertEquals(False, result)

    def test_equal(self):
        """
        Test success failure with a version requirement that equals the current
        one
        """

        (_maj, _min, _rev) = TestCheckGitVersion.get_current_git_version()
        result = u.check_git_version(_maj, _min, _rev)
        self.assertEquals(True, result)

    def test_lesser_major(self):
        """
        Test success with a _major version requirement lesser than the current
        one
        """

        result = u.check_git_version(0, 999, 999)
        self.assertEquals(True, result)

    def test_lesser_minor(self):
        """
        Test success with a _minor version requirement lesser than the current
        one
        """

        _maj = TestCheckGitVersion.get_current_git_version()[0]
        result = u.check_git_version(_maj, 0, 999)
        self.assertEquals(True, result)

    def test_lesser_revision(self):
        """
        Test success with a _revision version requirement lesser than the
        current one
        """

        (_maj, _min) = TestCheckGitVersion.get_current_git_version()[:2]
        result = u.check_git_version(_maj, _min, 0)
        self.assertEquals(True, result)
