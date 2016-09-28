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
import git
import os
import subprocess

from git_upstream.lib.utils import GitMixin
from git_upstream.log import LogDedentMixin
from git_upstream import PROJECT_ROOT

REBASE_EDITOR_SCRIPT = "rebase-editor"

# ensure name of file will match any naming filters used by editors to
# enable syntax highlighting
REBASE_EDITOR_TODO = "git-upstream/git-rebase-todo"


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

    def _todo_epilogue(self):
        if git.Git().version_info < (2, 6, 0):
            resource = 'todo_epilogue_1_7_5.txt'
        else:
            resource = 'todo_epilogue_2_6_0.txt'
        with open('%s/resources/%s' % (PROJECT_ROOT, resource),
                  'r') as epilogue:
            return epilogue.read()

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

            # if root isn't set at this point, then there were no commits
            if not root:
                todo.write("noop\n")

            todo.write(self._todo_epilogue() %
                       {'shortrevisions': "%s..%s" % (self._shorten(root),
                                                      self._shorten(commit)),
                        'shortonto': self._shorten(onto or root)})

        return todo_file

    def _insert_exec_to_todo(self):
        if not self.finish_args:
            # no need to insert, as asked not to perform a finish/merge
            return

        todo_file = os.path.join(self.repo.git_dir, REBASE_EDITOR_TODO)
        exec_line = "exec %s\n" % " ".join(self.finish_args)

        insn_data = None
        with codecs.open(todo_file, "r", "utf-8") as todo:
            insn_data = todo.readlines()

        # Cannot just append to file, as rebase appears to cut off
        # after the second blank line in a row is encountered.
        # Need to find the last instruction and insert afterwards,
        # or if we find noop replace.
        last = 0
        for idx, line in enumerate(insn_data):
            # comment line - ignore
            if line.startswith("#"):
                continue
            # found noop - just replace
            if line.rstrip() == "noop":
                insn_data[idx] = exec_line
                break
            # not an empty line
            if line.rstrip() != "":
                last = idx
        else:
            # didn't break so need to insert after last instruction
            insn_data.insert(last + 1, exec_line)

        # replace contents to include exec
        try:
            todo = codecs.open(todo_file, "w", "utf-8")
            todo.writelines(insn_data)
            # ensure the filesystem has the correct contents
            todo.stream.flush()
            os.fsync(todo.stream.fileno())
        finally:
            todo.close()

    def _shorten(self, commit):

        if not commit:
            return "<none>"

        return self.git.rev_parse(commit, short=True)

    def _set_editor(self, editor):

        env = os.environ.copy()
        # if git is new enough, we can edit the sequence without overriding
        # the editor, which allows rebase to call the correct editor if
        # reaches a 'reword' command before it has exited for the first time
        # otherwise the custom editor of git-upstream will executed with
        # the path to a commit message as an argument and will need to be able
        # to call the preferred user editor instead
        if self.git.version_info >= (1, 7, 8):
            env['GIT_SEQUENCE_EDITOR'] = editor
        else:
            env['GIT_UPSTREAM_GIT_EDITOR'] = self.git_editor
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

        # ensure that the finish will always be called
        self._insert_exec_to_todo()

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
        elif not self._interactive:
            # If in non-interactive mode use subprocess instead of exec
            #
            # This ensures that if no conflicts occur, that the calling
            # git-upstream process will be able to switch the current
            # branch after the git-rebase subprocess exits. This is not
            # possible when using exec to have git-rebase replace the
            # existing process. Since git-rebase performs checks once
            # it is completed running the instructions (todo file),
            # changing the current branch checked out in the git
            # repository via the final instruction (calling
            # `git-upstream import --finish ...`) results in git-rebase
            # exiting with an exception.
            #
            # For interactive mode it is impossible to perform a rebase
            # via subprocess and have it correctly attach an editor to
            # the console for users to edit/reword commits. The
            # consequence of using exec to support interactive usage
            # prevents correctly switching final branch to anything other
            # than the branch that git-rebase was started on (which will
            # be the import branch).
            #
            # As interactive mode involves user intervention it seems a
            # reasonable compromise to require manual switch of branches
            # after being finished until such time that an alternative
            # solution can be found.
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
