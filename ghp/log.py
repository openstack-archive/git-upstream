#
# Copyright (c) 2013 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

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


# sorted in order of verbosity "['level', 'alias']"
_levels = [
    ['critical', 'fatal'],
    ['error'],
    ['warning', 'warn'],
    ['notice'],
    ['info'],
    ['debug']
]


def getIncrementLevel(count, default='warning'):
    """
    Given a default level to start from, and a count to increment the logging
    level by, return the associated level that is 'count' levels more verbose.
    """
    idx = next((idx for idx, sublist in enumerate(_levels) if default in sublist), None)
    return _levels[min(idx + count, len(_levels) - 1)][0].upper()


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
        for levelalias in _levels:
            level = levelalias[0]
            aliases = levelalias[1:]
            setattr(obj, level, cls.wrap()(getattr(obj, level)))
            for alias in aliases:
                setattr(obj, alias, getattr(obj, level))
        setattr(obj, 'log', cls.wrap(True)(getattr(obj, 'log')))
        return obj

    @staticmethod
    def wrap(with_level=False):
        def dedentlog(func):
            if with_level:
                def _dedent_log(self, level, msg, *args, **kwargs):
                    dedent = kwargs.pop('dedent', True)
                    if dedent:
                        msg = textwrap.dedent(msg)
                    func(self, level, msg, *args, **kwargs)
            else:
                def _dedent_log(self, msg, *args, **kwargs):
                    dedent = kwargs.pop('dedent', True)
                    if dedent:
                        msg = textwrap.dedent(msg)
                    func(self, msg, *args, **kwargs)
            return wraps(func)(_dedent_log)
        return dedentlog


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
