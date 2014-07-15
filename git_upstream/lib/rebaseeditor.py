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

from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin

from subprocess import call
import os

REBASE_EDITOR_SCRIPT = "rebase-editor"

# insure name of file will match any naming filters used by editors to
# enable syntax highlighting
REBASE_EDITOR_TODO = "git-upstream/git-rebase-todo"

TODO_EPILOGUE = """\

# Rebase %(shortrevisions)s onto %(shortonto)s
#
# All commands from normal rebase instructions files are supported
#
# If you remove a line, that commit will be dropped.
# Removing all commits will abort the rebase.
#
"""


class RebaseEditor(GitMixin, LogDedentMixin):

    def __init__(self, interactive=False, *args, **kwargs):

        self._interactive = interactive

        super(RebaseEditor, self).__init__()

        self._editor = REBASE_EDITOR_SCRIPT
        # interactive switch here determines if the script that is given
        # to git-rebase to run as it's editor, will in turn exec an editor
        # for the user to look through the instructions before rebase
        # applies them
        if interactive == 'debug':
            self.log.debug("Enabling interactive mode for rebase")
            self._editor = "%s --interactive" % self.editor

    @property
    def editor(self):
        return self._editor

    def _write_todo(self, commits, *args, **kwargs):
        todo_file = os.path.join(self.repo.git_dir, REBASE_EDITOR_TODO)
        if os.path.exists(todo_file):
            os.remove(todo_file)

        if not os.path.exists(os.path.dirname(todo_file)):
            os.mkdir(os.path.dirname(todo_file))

        # see if onto is set in the args or kwargs
        onto = kwargs.get('onto', None)
        for idx, arg in enumerate(args):
            if arg.startswith("--onto"):
                # either onto is after the option in this arg, or it's the
                # next arg, or not providing it is an exception
                onto = arg[7:] or args[idx + 1]
                break

        root = None
        with open(todo_file, "w") as todo:
            for commit in commits:
                if not root:
                    root = commit.parents[0].hexsha
                subject = commit.message.splitlines()[0]
                todo.write("pick %s %s\n" % (commit.hexsha[:7], subject))

            # if root isn't set at this point, then there were no commits
            if not root:
                todo.write("noop\n")

            todo.write(TODO_EPILOGUE %
                       {'shortrevisions': self._short_revisions(root,
                                                                commit.hexsha),
                        'shortonto': self._short_onto(onto or root)})

        return todo_file

    def _short_revisions(self, root, commit):

        if not root:
            return "<none>"

        return "%s..%s" % (root[:7], commit[:7])

    def _short_onto(self, onto):

        if not onto:
            return "<none>"

        return self.git.rev_parse(onto)[:7]

    def _set_editor(self, editor):

        if self.git_sequence_editor:
            self._saveeditor = self.git_sequence_editor
            if self._interactive == 'debug':
                os.environ['GIT_UPSTREAM_GIT_SEQUENCE_EDITOR'] = \
                    self._saveeditor
            os.environ['GIT_SEQUENCE_EDITOR'] = editor
        else:
            self._saveeditor = self.git_editor
            if self._interactive == 'debug':
                os.environ['GIT_UPSTREAM_GIT_EDITOR'] = self._saveeditor
            os.environ['GIT_EDITOR'] = editor

    def _unset_editor(self):

        for var in ['GIT_SEQUENCE_EDITOR', 'GIT_EDITOR']:
            # GIT_UPSTREAM_* variations should only be set if script was in a
            # debug mode.
            if os.environ.get('GIT_UPSTREAM_' + var, None):
                del os.environ['GIT_UPSTREAM_' + var]
            # Restore previous editor only if the environment var is set. This
            # isn't perfect since we should probably unset the env var if it
            # wasn't previously set, but this shouldn't cause any problems.
            if os.environ.get(var, None):
                os.environ[var] = self._saveeditor
                break

    def run(self, commits, *args, **kwargs):
        """
        Reads the list of commits given, and constructions the instructions
        file to be used by rebase.
        Will spawn an editor if the constructor was told to be interactive.
        Additional arguments *args and **kwargs are to be passed to 'git
        rebase'.
        """

        todo_file = self._write_todo(commits, *args, **kwargs)
        if self._interactive:
            # spawn the editor
            user_editor = self.git_sequence_editor or self.git_editor
            status = call("%s %s" % (user_editor, todo_file), shell=True)
            if status:
                return status, None, "Editor returned non-zero exit code"

        editor = "%s %s" % (self.editor, todo_file)
        self._set_editor(editor)

        try:
            if self._interactive == 'debug':
                # In general it's not recommended to run rebase in direct
                # interactive mode because it's not possible to capture the
                # stdout/stderr, but sometimes it's useful to allow it for
                # debugging to check the final result.
                #
                # It is not safe to redirect I/O channels as most editors will
                # be expecting that I/O is from/to proper terminal. YMMV
                cmd = ['git', 'rebase', '--interactive']
                cmd.extend(self.git.transform_kwargs(**kwargs))
                cmd.extend(args)
                return call(cmd), None, None
            else:
                return self.git.rebase(interactive=True, with_exceptions=False,
                                       with_extended_output=True, *args,
                                       **kwargs)
        finally:
            os.remove(todo_file)
            # make sure to remove the environment tweaks added so as not to
            # impact any subsequent use of git commands using editors
            self._unset_editor()

    @property
    def git_sequence_editor(self):

        return os.environ.get('GIT_SEQUENCE_EDITOR',
                              self.git.config("sequence.editor",
                                              with_exceptions=False))

    @property
    def git_editor(self):

        return os.environ.get("GIT_EDITOR", self.git.var("GIT_EDITOR"))
