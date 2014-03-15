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


"""
Command-line tool for tracking upstream revisions

Main parser module, which after parsing the top level options will hand
off to the collected subcommands parsers.
"""

import git_upstream.commands as commands
from git_upstream.errors import GitUpstreamError
import git_upstream.log as log
import git_upstream.version
from git_upstream.lib import utils

import subcommand
import argparse
from argparse import ArgumentParser
try:
    import argcomplete
    argparse_loaded = True
except ImportError:
    argparse_loaded = False
import logging
import sys


def get_parser():
    parser = ArgumentParser(
        description=__doc__.strip(),
        epilog='See "%(prog)s help COMMAND" for help on a specific command.',
        add_help=False)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + git_upstream.version.version)
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

    return subcommand_parsers, parser


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

    if argparse_loaded:
        argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if args.func == help:
        help(parser, args, cmds)
        return 0

    args.log_level = getattr(logging, args.log_level.upper(), logging.NOTSET)
    console_log_level = getattr(logging, log.get_increment_level(args.verbose),
                                logging.NOTSET)
    if args.quiet:
        console_log_level = logging.NOTSET

    # determine maximum logging requested for file and console provided they
    # are not disabled, and including stderr which is fixed at ERROR
    main_log_level = min([value
                          for value in args.log_level, console_log_level
                          if value != logging.NOTSET
                          ] + [logging.ERROR])
    logger = log.get_logger()
    logger.setLevel(main_log_level)

    if not args.quiet:
        # configure logging to console for verbose/quiet messages
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(console_log_level)
        console.addFilter(log.LevelFilterIgnoreAbove(logging.ERROR))
        console.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console)

    # make sure error and critical messages go to stderr and aren't suppressed
    err_con = logging.StreamHandler(sys.stderr)
    err_con.setLevel(logging.ERROR)
    err_con.addFilter(log.LevelFilterIgnoreBelow(logging.ERROR))
    err_con.setFormatter(logging.Formatter("%(levelname)-8s: %(message)s"))
    logger.addHandler(err_con)

    if args.log_file:
        filehandler = logging.FileHandler(args.log_file)
        filehandler.setLevel(args.log_level)
        _format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
        filehandler.setFormatter(logging.Formatter(_format))
        logger.addHandler(filehandler)

    if not utils.check_git_version(1, 7, 5):
        logger.fatal("Git-Upstream requires git version 1.7.5 or later")
        sys.exit(1)

    try:
        args.func(args)
    except GitUpstreamError, e:
        logger.fatal("%s", e[0])
        logger.debug("Git-Upstream: %s", e[0], exc_info=e)
        sys.exit(1)

# vim:sw=4:sts=4:ts=4:et:
