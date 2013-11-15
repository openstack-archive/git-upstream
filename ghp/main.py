#!/usr/bin/env python
#
# Copyright (c) 2012, 2013 Hewlett-Packard Development Company, L.P.
#
# Confidential computer software. Valid license from HP required for
# possession, use or copying. Consistent with FAR 12.211 and 12.212,
# Commercial Computer Software, Computer Software Documentation, and
# Technical Data for Commercial Items are licensed to the U.S. Government
# under vendor's standard commercial license.
#

"""
Command-line tool for the HP Cloud workflow

Main parser module, which after parsing the top level options will hand
off to the collected subcommands parsers.
"""

import ghp.commands as commands
from ghp.errors import HpgitError
import ghp.log as log
import ghp.version

import subcommand
import argparse
from argparse import ArgumentParser
import argcomplete
import logging
import sys


def get_parser():
    parser = ArgumentParser(
        description=__doc__.strip(),
        epilog='See "%(prog)s help COMMAND" for help on a specific command.',
        add_help=False,
    )
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + ghp.version.version)
    parser.add_argument('-h', '--help', action='help',
                        help='show this help message and exit')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-q', '--quiet', action='store_true',
                       help='Suppress additional output except for errors, '
                            'conflicts with --verbose')
    group.add_argument('-v', '--verbose', action='count', default=1,
                       help='Increase verbosity from commands, conflicts '
                            'with --quiet. May be set more than once.')
    # support logging to files as hidden options until we can hide them in
    # normal help output, which showing them in extended help or generated
    # manpages and documentation.
    parser.add_argument('--log-level', dest='log_level', default='notset',
                        help=argparse.SUPPRESS)
    parser.add_argument('--log-file', dest='log_file', help=argparse.SUPPRESS)

    subparsers = parser.add_subparsers(title="commands", metavar='<command>',
                                       dest='subcommand')

    # it would be nicer if we could hide this help command
    desc = help.__doc__ or ''
    subparser = subparsers.add_parser(
        'help',
        help=desc.strip().split('\n')[0],
        description=desc,
    )
    for (args, kwargs) in getattr(help, 'arguments', []):
        subparser.add_argument(*args, **kwargs)
    subparser.set_defaults(func=help)

    subcommand_parsers = commands.get_subcommands(subparsers)

    return (subcommand_parsers, parser)


@subcommand.arg('command', metavar='<command>', nargs='?',
                help='Display help for <command>')
def help(parser, args, commands=None):
    """Display help about this program or one of its commands."""
    if getattr(args, 'command', None):
        if args.command in commands:
            commands[args.command].print_help()
        else:
            parser.error("'%s' is not a valid subcommand" %
                         args.command)
    else:
        parser.print_help()


def main(argv):
    (cmds, parser) = get_parser()

    if not argv:
        help(parser, argv)
        return 0

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if args.func == help:
        help(parser, args, cmds)
        return 0

    args.log_level = getattr(logging, args.log_level.upper(), logging.NOTSET)
    console_log_level = getattr(logging, log.getIncrementLevel(args.verbose),
                                logging.NOTSET)
    if args.quiet:
        console_log_level = logging.NOTSET

    # determine maximum logging requested for file and console provided they
    # are not disabled, and including stderr which is fixed at ERROR
    main_log_level = min([value
                          for value in args.log_level, console_log_level
                          if value != logging.NOTSET
                          ] + [logging.ERROR])
    logger = log.getLogger()
    logger.setLevel(main_log_level)

    if not args.quiet:
        # configure logging to console for verbose/quiet messages
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(console_log_level)
        console.addFilter(log.LevelFilterIgnoreAbove(logging.ERROR))
        console.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console)

    # make sure error and critical messages go to stderr and aren't suppressed
    errcon = logging.StreamHandler(sys.stderr)
    errcon.setLevel(logging.ERROR)
    errcon.addFilter(log.LevelFilterIgnoreBelow(logging.ERROR))
    errcon.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
    logger.addHandler(errcon)

    if args.log_file:
        filehandler = logging.FileHandler(args.log_file)
        filehandler.setLevel(args.log_level)
        format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
        filehandler.setFormatter(logging.Formatter(format))
        logger.addHandler(filehandler)

    try:
        args.func(args)
    except HpgitError, e:
        logger.fatal("%s", e[0])
        logger.debug("HpgitError: %s", e[0], exc_info=e)
        sys.exit(1)

# vim:sw=4:sts=4:ts=4:et:
