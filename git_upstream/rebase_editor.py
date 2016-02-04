#!/usr/bin/env python
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
Command line editor for modifying git rebase instructions file through use
of the interactive mode. Will in turn launch an editor in turn if the user
wished to use the interactive mode of git-rebase.

Script will replace all occurrences of 'pick' or any other instruction entry
with a list of instructions read from the given input file.

Avoid use of stdin for passing such information as many editors have problems
if exec'ed and stdin is a pipe.
"""

import argparse
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
                        print(replacement)
                print("")
                echo_out = True
            continue
        if echo_out:
            print(stripped)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__.strip(),
    )
    parser.add_argument('-v', '--verbose', action='store_true', default=False,
                        help='Enable verbose mode')
    parser.add_argument('-i', '--interactive', action='store_true',
                        help='Enable interactive mode, where the user can edit'
                             ' the list of commits before being applied')
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

    # If called with a commit message file as the argument, skip this next
    # section, and try to spawn the user preferred editor. Should only be
    # needed if reword command is encountered by git-rebase before an edit
    # or conflict has occurred and git is older than 1.7.8, as otherwise
    # sequence.editor will be used instead , which will ensure the normal
    # editor is called by rebase for the commit message, and this editor is
    # limited to only modifying the instruction sequence.
    if os.path.basename(args.ofile) != "COMMIT_EDITMSG":
        # don't attempt to use stdin to pass the information between the parent
        # process through 'git-rebase' and this script, as many editors will
        # have problems if stdin is a pipe.
        if VERBOSE:
            print("rebase-editor: Replacing rebase instructions")
        rebase_replace_insn(args.ofile, open(args.ifile, 'r'))

        # if interactive mode, attempt to exec the editor defined by the user
        # for use with git
        if not args.interactive:
            if VERBOSE:
                print("rebase-editor: Interactive mode not enabled")
            sys.exit(0)

    # calling code should only override one of the two editor variables,
    # starting with the one with the highest precedence
    editor = None
    for var in ['GIT_SEQUENCE_EDITOR', 'GIT_EDITOR']:
        editor = os.environ.get('GIT_UPSTREAM_' + var, None)
        if editor:
            del os.environ['GIT_UPSTREAM_' + var]
            os.environ[var] = editor
            break

    if editor:
        editor_args = [editor]
        editor_args.extend(args.extra_args)
        editor_args.append(args.ofile)
        sys.stdin.flush()
        sys.stdout.flush()
        sys.stderr.flush()
        os.execvp(editor, editor_args)

    sys.stderr.write("rebase-editor: No git EDITOR variables defined in "
                     "environment to call as required.\n")
    sys.exit(2)

if __name__ == '__main__':
    main()
