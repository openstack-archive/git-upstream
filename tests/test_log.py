#
# Copyright (c) 2012, 2013, 2014 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

"""Tests for then 'log' module"""

import testtools
from git_upstream import log as l


class TestGetLogger(testtools.TestCase):
    """Test case for get_logger function"""

    def test_logger_name(self):
        """Test the default logger name"""

        logger = l.get_logger()
        self.assertIsNotNone(logger)
        self.assertEquals('git-upstream', logger.name)

    def test_logger_name_param(self):
        """Test custom logger name"""

        logger = l.get_logger('test')
        self.assertIsNotNone(logger)
        self.assertEquals('git-upstream.test', logger.name)


class TestGetIncrementLevel(testtools.TestCase):
    """Test case for get_increment_level function"""

    _levels = [
        ['critical', 'fatal'],
        ['error'],
        ['warning', 'warn'],
        ['notice'],
        ['info'],
        ['debug']
    ]

    def _test_increment_by_x(self, increment=1):
        """Utility function that tests a given increment"""
        levels = len(self._levels)
        for level_no in range(levels - increment):
            for level in self._levels[level_no]:
                result = l.get_increment_level(1, level)
                self.assertEquals(
                    self._levels[min(level_no + 1, levels - 1)][0].upper(),
                    result)

    def test_increments(self):
        """Test all possible increments for all possible default level"""
        for i in range(len(self._levels)):
            self._test_increment_by_x(i)
