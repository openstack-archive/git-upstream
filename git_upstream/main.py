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
"""

import argparse
import logging
import os
import sys
import weakref

import git

from git_upstream import __version__
from git_upstream import commands
from git_upstream.errors import GitUpstreamError
from git_upstream import log

try:
    import argcomplete
    argparse_loaded = True
except ImportError:
    argparse_loaded = False


def build_parsers():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
        epilog='See "%(prog)s help COMMAND" for help on a specific command.',
        add_help=False)
    parser.add_argument('--version', action='version',
                        version='%(prog)s ' + __version__)
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
    # normal help output, while showing them in extended help or generated
    # man pages and documentation.
    parser.add_argument('--log-level', dest='log_level', default='notset',
                        help=argparse.SUPPRESS)
    parser.add_argument('--log-file', dest='log_file', help=argparse.SUPPRESS)

    subcommand_parsers = commands.get_subcommands(parser)

    # calculate the correct path to allow the program be re-executed
    program = sys.argv[0]
    if os.path.split(program)[-1] != 'git-upstream':
        script_cmdline = ['python', program]
    else:
        script_cmdline = [program]

    parser.set_defaults(script_cmdline=script_cmdline,
                        parent_parser=weakref.proxy(parser))

    return subcommand_parsers, parser


def setup_console_logging(options):

    options.log_level = getattr(logging, options.log_level.upper(),
                                logging.NOTSET)
    console_log_level = getattr(logging,
                                log.get_increment_level(options.verbose),
                                logging.NOTSET)
    if options.quiet:
        console_log_level = logging.NOTSET

    # determine maximum logging requested for file and console provided they
    # are not disabled, and including stderr which is fixed at ERROR
    main_log_level = min([value
                          for value in (options.log_level, console_log_level)
                          if value != logging.NOTSET
                          ] + [logging.ERROR])
    logger = log.get_logger()
    logger.setLevel(main_log_level)

    if not options.quiet:
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

    if options.log_file:
        filehandler = logging.FileHandler(options.log_file)
        filehandler.setLevel(options.log_level)
        _format = "%(asctime)s - %(name)s - %(levelname)s: %(message)s"
        filehandler.setFormatter(logging.Formatter(_format))
        logger.addHandler(filehandler)

    return logger


def main(argv=None):

    # We default argv to None and assign to sys.argv[1:] below because having
    # an argument default value be a mutable type in Python is a gotcha. See
    # http://bit.ly/1o18Vff
    if not argv:
        argv = sys.argv[1:]

    (cmds, parser) = build_parsers()

    if not argv:
        parser.print_help()
        return 0

    if argparse_loaded:
        argcomplete.autocomplete(parser)
    args = parser.parse_args(argv)

    logger = setup_console_logging(args)

    # allow help subcommand to be called before checking git version
    if args.cmd.name == "help":
        args.cmd.run(args)
        return 0

    if git.Git().version_info < (1, 7, 5):
        logger.fatal("Git-Upstream requires git version 1.7.5 or later")
        sys.exit(1)

    for arg in argv:
        if arg in args.subcommands:
            break
        args.script_cmdline.append(arg)

    try:
        args.cmd.run(args)
    except GitUpstreamError as e:
        logger.fatal("%s", e[0])
        logger.debug("Git-Upstream: %s", e[0], exc_info=e)
        sys.exit(1)


if __name__ == '__main__':
    main()

# vim:sw=4:sts=4:ts=4:et:
