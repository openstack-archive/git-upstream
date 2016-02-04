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

import codecs
import os
import subprocess

from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin

REBASE_EDITOR_SCRIPT = "rebase-editor"

# ensure name of file will match any naming filters used by editors to
# enable syntax highlighting
REBASE_EDITOR_TODO = "git-upstream/git-rebase-todo"

TODO_EPILOGUE = """

# Rebase %(shortrevisions)s onto %(shortonto)s
#
# All commands from normal rebase instructions files are supported
#
# If you remove a line, that commit will be dropped.
# Removing all commits will abort the rebase.
#
"""


class RebaseEditor(GitMixin, LogDedentMixin):

    def __init__(self, finish_args, interactive=False, *args, **kwargs):

        self._interactive = interactive

        super(RebaseEditor, self).__init__(*args, **kwargs)

        self._editor = REBASE_EDITOR_SCRIPT
        # interactive switch here determines if the script that is given
        # to git-rebase to run as it's editor, will in turn exec an editor
        # for the user to look through the instructions before rebase
        # applies them
        if interactive == 'debug':
            self.log.debug("Enabling interactive mode for rebase")
            self._editor = "%s --interactive" % self.editor

        self.finish_args = finish_args

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
        with codecs.open(todo_file, "w", "utf-8") as todo:
            for commit in commits:
                if not root:
                    root = commit.parents[0]
                subject = commit.message.splitlines()[0]
                todo.write("pick %s %s\n" % (self._shorten(commit), subject))

            if os.environ.get('TEST_GIT_UPSTREAM_REBASE_EDITOR', "") != "1":
                todo.write("exec %s" % " ".join(self.finish_args))
            # if root isn't set at this point, then there were no commits
            # and we are in test mode, so no exec to perform either
            elif not root:
                todo.write("noop\n")

            todo.write(TODO_EPILOGUE %
                       {'shortrevisions': "%s..%s" % (self._shorten(root),
                                                      self._shorten(commit)),
                        'shortonto': self._shorten(onto or root)})

        return todo_file

    def _shorten(self, commit):

        if not commit:
            return "<none>"

        return self.git.rev_parse(commit, short=True)

    def _set_editor(self, editor):

        env = os.environ.copy()
        if self.git_sequence_editor:
            env['GIT_SEQUENCE_EDITOR'] = editor
        else:
            env['GIT_EDITOR'] = editor
        return env

    def cleanup(self):
        todo_file = os.path.join(self.repo.git_dir, REBASE_EDITOR_TODO)
        if os.path.exists(todo_file):
            os.remove(todo_file)

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
            # It is not safe to redirect I/O channels as most editors will
            # be expecting that I/O is from/to proper terminal. YMMV
            user_editor = self.git_sequence_editor or self.git_editor
            status = subprocess.call("%s %s" % (user_editor, todo_file),
                                     shell=True)
            if status != 0:
                return status, None, "Editor returned non-zero exit code"

        editor = "%s %s" % (self.editor, todo_file)
        environ = self._set_editor(editor)

        cmd = ['git', 'rebase', '--interactive']
        cmd.extend(self.git.transform_kwargs(**kwargs))
        cmd.extend(args)
        mode = os.environ.get('TEST_GIT_UPSTREAM_REBASE_EDITOR', "")
        if mode.lower() == "debug":
            # In general it's not recommended to run rebase in direct
            # interactive mode because it's not possible to capture the
            # stdout/stderr, but sometimes it's useful to allow it for
            # debugging to check the final result.
            try:
                return subprocess.call(cmd), None, None
            finally:
                self.cleanup()
        elif mode == "1":
            # run in test mode to avoid replacing the existing process
            # to keep the majority of tests simple and only require special
            # launching code for those tests written to check the rebase
            # resume behaviour
            try:
                return 0, subprocess.check_output(
                    cmd, stderr=subprocess.STDOUT, env=environ), None
            except subprocess.CalledProcessError as e:
                return e.returncode, e.output, None
            finally:
                self.cleanup()
        else:
            cmd.append(environ)
            os.execlpe('git', *cmd)

    @property
    def git_sequence_editor(self):

        return os.environ.get('GIT_SEQUENCE_EDITOR',
                              self.git.config("sequence.editor",
                                              with_exceptions=False))

    @property
    def git_editor(self):

        return os.environ.get("GIT_EDITOR",
                              self.git.var("GIT_EDITOR",
                                           with_exceptions=False))
