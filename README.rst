README
======

What is git-upstream?
---------------------

git-upstream is an open source Python application that can be used to
keep in sync with upstream open source projects, mainly OpenStack.

The main usecase for this tool is for people who are doing active
contributions to repositories that are mirrors of OpenStack
repositories, with the intention that most of those contributions will
be submitted to review.openstack.org at some point. If you are running a
public cloud based on OpenStack, having local changes needed to use it
in your environment, you can use git-upstream to stay up to date with
the upstream master in a easier way (with respect to using raw git
commands).

git-upstream provides new git subcommands to support rebasing of
local-carried patches on top of upstream repositories. It provides
commands to ease the use of git for who needs to integrate big upstream
projects in their environment. The operations are performed using Git
commands.

.. note:: currently git-upstream can be used only for projects that are
   maintained with Gerrit as it relies on the presence of Change-IDs.
   Nevertheless, the code is quite modular and can be extended to use
   any part of commit message (e.g., other headers).


Git-upstream currently supports the following features

-  **Single upstream branch import**

Your repository is tracking an upstream project and has local changes
applied and no other branch is merged in. This can also be applied to
tracking upstream packaging branches: *e.g.*, ubuntu/master =>
ubuntu/saucy-proposed/nova + local packaging changes.

-  **Multi branch import (upstream branch + additional branches)**

In this case, your project tracks an upstream repository, merges in an
arbitrary number of branches and applies local carried changes.

-  **Re-reviewing**

Reviewing (w/ Gerrit) of all locally applied changes if desired.
git-upstream creates an import branch in a manner that allows it to be
fully re-reviewed or merged into master and pushed.

-  **Detailed logging**

git-upstream can output to both console and log file simultaneously.
Multiple log levels are supported, and these are managed separately for
log file and console output. This means jobs run by Jenkins can save a
detailed log file separately as an artefact while printing status
information to the console if those running the jobs don’t wish to have
the console spammed with the details.

-  **Dropping of changes that appear upstream**

Compares Change-Id's of changes applied since previous import with those
that have appeared on the upstream branch since the last import point.

-  **Interactive mode**

Once the list of changes to be re-applied has been determined (and those
to be dropped have been pruned), the tool can open an editor (controlled
by a user's git editor settings) for users to review those changes to be
made and allow them to perform further operations such as re-ordering,
dropping of obsolete changes, and squashing.

-  **Dropping local changes**

It’s always possible for local changes to be superseded by upstream
changes, so when these are identified and marked as such, we should drop
them.

This can also occur where a change was applied locally, modified when
being upstreamed based on review feedback and the resulting differences
were ported to the internal as well. While the original change will be
automatically dropped, also useful to drop the additional ported changes
automatically if possible, rather than have it cause conflicts.

Installation
============

At the time of writing, there are two ways to install git-upstream:
cloning its git repository or using pip.

Installing from git repository
------------------------------

.. code:: bash

    git clone https://git.openstack.org/openstack/git-upstream.git
    cd git-upstream
    # Install git-upstream itself
    python setup.py install

Installing from PyPI
--------------------

.. code:: bash

    pip install git-upstream

See also https://pypi.python.org/pypi/git-upstream

Using git-upstream
==================

Please see `workflows <doc/source/workflows.rst>`_

Available commands
==================

Please see `subcommands <doc/source/subcommands.rst>`_

Authors
=======

git-upstream was written by Darragh Bailey dbailey@hpe.com.

Acknowledgements
================

Thanks to *Aleksander Korzynski* and *Stanisław Pitucha* for taking the
original design spec and some basic manual steps and experimenting with
initial implementations.

To *Davide Guerri*, for picking up a rough python tool and turning it
into something that was actually usable.

Also to *Jon Paul Sullivan* and *Monty Taylor* to listening and
providing a sounding board for different approaches.

And finally to *Coleman Corrigan* among numerous others who acted as
willing guinea pigs for the original manual approach.

Hope this eventually helped save you time and some hair.
