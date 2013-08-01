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
Command line editor for modifying git rebase instructions file through use
of the interactive mode. Will in turn launch an editor in turn if the user
wished to use the interactive mode of git-rebase.

Script will replace all occurances of 'pick' or any other instruction entry
with a list of instructions read from the given input file.

Avoid use of stdin for passing such information as many editors have problems
if exec'ed and stdin is a pipe.
"""

from argparse import ArgumentParser
import fileinput
import os
import sys


def rebase_replace_insn(path, istream):
    """
    Function replaces the current instructions listed in the rebase
    instructions (insn) file with those read from the given istream.
    """
    echo_out = False
    for line in fileinput.input(path, inplace=True):
        stripped = line.strip()
        # first blank line indicates end of rebase instructions
        if not stripped:
            if not echo_out:
                while True:
                    replacement = istream.readline().strip()
                    if not replacement:
                        break
                    if not replacement.startswith("#"):
                        print replacement
                print ""
                echo_out = True
            continue
        if echo_out:
            print stripped


if __name__ == '__main__':
    parser = ArgumentParser(
        description=__doc__.strip(),
    )
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Enable verbose mode')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Enable interactive mode, where the user can edit '
                             'the list of commits before being applied')
    parser.add_argument('ifile', metavar='<new-list>',
                        help='File containing the new list of instructions to '
                             'be placed into the rebase instructions file.')
    parser.add_argument('extra_args', metavar='<args>', nargs='?', default=[],
                        help='Additional arguments to be passed to the '
                             'subsequent editor')
    parser.add_argument('ofile', metavar='<todo-list>',
                        help='Filename containing the list of instructions to'
                             'be edited.')

    args = parser.parse_args()
    VERBOSE = args.verbose

    # don't attempt to use stdin to pass the information between the parent
    # process through 'git-rebase' and this script, as many editors will
    # have problems if stdin is a pipe.
    if VERBOSE:
        print "rebase-editor: Replacing contents of rebase instructions file"
    rebase_replace_insn(args.ofile, open(args.ifile, 'r'))

    # if interactive mode, attempt to exec the editor defined by the user
    # for use with git
    if not args.interactive:
        if VERBOSE:
            print "rebase-editor: Interactive mode not enabled"
        sys.exit(0)

    # calling code should only override one of the two editor variables,
    # starting with the one with the highest precedence
    env = os.environ
    for var in ['GIT_SEQUENCE_EDITOR', 'GIT_EDITOR']:
        editor = env.get('HPGIT_' + var, None)
        if editor:
            del env['HPGIT_' + var]
            env[var] = editor
            break

    if editor:
        editor_args = [editor]
        editor_args.extend(args.extra_args)
        editor_args.append(args.ofile)
        sys.stdin.flush()
        sys.stdout.flush()
        sys.stderr.flush()
        #os.dup2(sys.stdin.fileno(), 0)
        #os.dup2(sys.stdout.fileno(), 1)
        #os.dup2(sys.stderr.fileno(), 2)
        os.execvpe(editor, editor_args, env=env)

    sys.stderr.write("rebase-editor: No git EDITOR variables defined in "
                     "environment to call as requested by the "
                     "--interactive option.\n")
    sys.exit(2)
