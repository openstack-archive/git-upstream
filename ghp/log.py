#!/usr/bin/env python
#
# Copyright (c) 2013 Hewlett-Packard
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

"""
Custom logging for HP git tool

Adds new 'NOTICE' level to standard logging library and provides helper
functions for verbose/quiet CLI args to retreive the appropriate level
for logging output to the console.
"""

import logging


# Add new NOTICE logging level
NOTICE = (logging.INFO + logging.WARN) / 2
logging.NOTICE = NOTICE
logging.addLevelName(NOTICE, "NOTICE")


def notice(self, msg, *args, **kwargs):
    """
    Supports same arguments as default methods available from
    logging.Logger class
    """
    if self.isEnabledFor(NOTICE):
        self._log(NOTICE, msg, args, **kwargs)

logging.Logger.notice = notice


def getLogger(name=None):
    """
    Wrapper for standard logging.getLogger that ensures all loggers in this
    application will have their name prefixed with 'hpgit'.
    """
    name = ".".join([x for x in "hpgit", name if x])

    logger = logging.getLogger(name)
    return logger


# sorted in order of verbosity
_levels = [
    'critical',
    'error',
    'warning',
    'notice',
    'info',
    'debug'
]


def getIncrementLevel(count, default='warning'):
    """
    Given a default level to start from, and a count to increment the logging
    level by, return the associated level that is 'count' levels more verbose.
    """
    return _levels[min(_levels.index(default) + count, len(_levels) - 1)].upper()


class LevelFilterIgnoreAbove(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


class LevelFilterIgnoreBelow(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno >= self.level
