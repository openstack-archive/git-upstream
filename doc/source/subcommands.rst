Subcommands
===========

import
------

Description
~~~~~~~~~~~

Import code from specified upstream branch. Creates an import branch
from the specified upstream branch, and optionally merges additional
branches given as arguments. Current branch, unless overridden by the
``--into`` option, is used as the target branch from which a list of
changes to apply onto the new import is constructed based on the
specified strategy. Once complete it will merge and replace the contents
of the target branch with those from the import branch, unless
``--no-merge`` is specified.

By default, the import branch is named according to the following
format, unless overridden using ``--import-branch``:

::

    import/<tag-or-git-describe-commit>[-<additional-branch-git-describe-commit>]

For example, ``import/4.0.0.0rc1-8-geaec95b`` refers to an upstream
branch who's latest tag is ``4.0.0.0rc1``. 8 commits have been made
upstream ahead of this tag, and ``geaec95b`` is SHA1 of the tip before
import.

Usage
~~~~~

::

    git upstream import [-h] [-d] [-i] [-f] [--merge] [--no-merge]
                               [-s <strategy>] [--into <branch>]
                               [--import-branch <import-branch>]
                               [<upstream-branch>] [<branches> [<branches> ...]]

Arguments
~~~~~~~~~

::

    positional arguments:
      <upstream-branch>     Upstream branch to import. Must be specified if you
                            wish to provide additional branches.
      <branches>            Branches to additionally merge into the import branch
                            using default git merging behaviour

    optional arguments:
      -h, --help            show this help message and exit
      -d, --dry-run         Only print out the list of commits that would be
                            applied.
      -i, --interactive     Let the user edit the list of commits before applying.
      -f, --force           Force overwrite of existing import branch if it
                            exists.
      --merge               Merge the resulting import branch into the target
                            branch once complete
      --no-merge            Disable merge of the resulting import branch
      -s <strategy>, --strategy <strategy>
                            Use the given strategy to re-apply locally carried
                            changes to the import branch. (default: drop)
      --into <branch>       Branch to take changes from, and replace with imported
                            branch.
      --import-branch <import-branch>
                            Name of import branch to use

drop
----

Description
~~~~~~~~~~~

Mark a commit as dropped. Marked commits will be skipped during the
upstream rebasing process.

See also the "git upstream import" command.

Usage
~~~~~

::

    git upstream drop [-h] [-a <author>] <commit>

Arguments
~~~~~~~~~

::

    positional arguments:
      <commit>              Commit to be marked as dropped

    optional arguments:
      -h, --help            show this help message and exit
      -a <author>, --author <author>
                            Git author for the mark

Note
~~~~

Commits will be marked with git notes in the namespace
``refs/notes/upstream-merge``.

To list of commit id marked with a note, run
``git notes --ref refs/notes/upstream-merge``.

To show a specific note run
``git notes --ref refs/notes/upstream-merge show <marked commit sha1>``

As ``drop`` uses git notes to mark commits that have to be skipped
during import, notes should be present on the cloned copy of your
repository. Thus, if you are going to create notes on a system and
perform the actual import on a different system, **notes must be present
on the latter**.

You can push notes directly to git repository on the target system or
push them in a different repository and then pull notes from your target
system.

supersede
---------

Description
~~~~~~~~~~~

Mark a commit as superseded by a set of change-ids. Marked commits will
be skipped during the upstream rebasing process **only if all the
specified change-ids are present in ``<upstream-branch>`` during
import**. If you want to unconditionally drop a commit, use the ``drop``
command instead.

See also the "git upstream import" command.

Usage
~~~~~

::

    git upstream supersede [-h] [-f] [-u <upstream-branch>]
                           <commit> <change id> [<change id> ...]

Arguments
~~~~~~~~~

::

    positional arguments:
      <commit>              Commit to be marked as superseded
      <change id>           Change id which makes <commit> obsolete. The change id
                            must be present in <upstream-branch> to drop <commit>.
                            If more than one change id is specified, all must be
                            present in <upstream-branch> to drop <commit>

    optional arguments:
      -h, --help            show this help message and exit
      -f, --force           Apply the commit mark even if one or more change ids
                            could not be found. Use this flag carefully as commits
                            will not be dropped during import command execution as
                            long as all associated change ids are present in the
                            local copy of the upstream branch
      -u <upstream-branch>, --upstream-branch <upstream-branch>
                            Search change ids values in <upstream-branch> branch
                            (default: upstream/master)

Note
~~~~

*This command doesn't perform the actual drop*. Commits to be dropped
during the next import, will be marked with git notes in the namespace
``refs/notes/upstream-merge``. There is no need to retain notes after an
import dropped the correspondent commits, of course it doesn't harm
keeping them either.

To list of commit id marked with a note, run
``git notes --ref refs/notes/upstream-merge``.

To show a specific note run
``git notes --ref refs/notes/upstream-merge show <marked commit sha1>``.

As ``supersede`` uses git notes to mark commits that have to be skipped
during import, notes should be present on the cloned copy of your
repository. Thus, if you are going to create notes on a system and
perform the actual import on a different system, **notes must be present
on the latter**. You can push notes directly to git repository on the
target system or push them in a different repository and then pull notes
from your target system.
