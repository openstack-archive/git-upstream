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
Command-line tool for the HP Cloud workflow
"""

import ghp.commands as commands
import ghp.version

import subcommand
from argparse import ArgumentParser

def get_parser():
    parser = ArgumentParser(
        description=__doc__.strip(),
        epilog='See "%(prog)s help COMMAND" for help on a specific command.',
        add_help=False,
    )
    parser.add_argument('--version', action='version', version='%(prog)s ' + ghp.version.version)
    parser.add_argument('-h', '--help', action='help', help='show this help message and exit')

    subparsers = parser.add_subparsers(title="commands", metavar='<command>', dest='subcommand')

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
def help(parser, args, commands = None):
    """
    Display help about this program or one of its commands.
    """
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

    args = parser.parse_args()
    if args.func == help:
        help(parser, args, cmds)
        return 0

    args.func(args)

# vim:sw=4:sts=4:ts=4:et:
