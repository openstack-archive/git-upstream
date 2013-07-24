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
from functools import wraps
import textwrap


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


class DedentLoggerMeta(type):
    """
    Meta class to wrap all level functions in logging interface with dedent

    Classes created from this should be derived from the logging.Logger class
    as otherwise they will not contain the correct methods to be wrapped and
    trying to pass them as the default class to create Loggers from will fail.
    """

    def __new__(cls, name, bases, dict):
        # provide a more intelligent error instead of waiting for setattr/getattr
        # adding of a wrapper function to fail
        if logging.Logger not in bases:
            raise TypeError("%s not derived from logging.Logger" % name)

        obj = super(DedentLoggerMeta, cls).__new__(cls, name, bases, dict)
        for level in _levels:
            setattr(obj, level, cls.wrap_level(getattr(obj, level)))
        setattr(obj, 'log', cls.wrap(getattr(obj, 'log')))
        return obj

    @staticmethod
    def wrap(func):
        def _dedent_log(self, level, msg, *args, **kwargs):
            dedent = kwargs.pop('dedent', True)
            if dedent:
                msg = textwrap.dedent(msg)
            func(self, level, msg, *args, **kwargs)
        return wraps(func)(_dedent_log)

    @staticmethod
    def wrap_level(func):
        def _dedent_log(self, msg, *args, **kwargs):
            dedent = kwargs.pop('dedent', True)
            if dedent:
                msg = textwrap.dedent(msg)
            func(self, msg, *args, **kwargs)
        return wraps(func)(_dedent_log)


class DedentLogger(logging.Logger):
    __metaclass__ = DedentLoggerMeta


# override default logger class for everything that imports this module
logging.setLoggerClass(DedentLogger)


class LogDedentMixin(object):

    def __init__(self, *args, **kwargs):
        self.__log = getLogger('%s.%s' % (__name__, self.__class__.__name__))

        super(LogDedentMixin, self).__init__(*args, **kwargs)

    @property
    def log(self):
        return self.__log
