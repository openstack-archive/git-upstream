What is git-upstream?
=====================

Git-upstream is an open source Python application that can be used to
keep in sync with upstream open source projects. Its goal is to help
manage automatically dropping carried patches when syncing with the
project upstream, in a manner transparent to local developers.

It was initially developed as a tool for people who are doing active
contributions to local mirrors of projects hosted using Gerrit for code
review, with the intention that the local changes would be submitted to
the upstream Gerrit instance (review.openstack.org for OpenStack) in
the future, and would subsequent appear in the upstream mainline.

As it uses git plumbing commands, it can identify identical patches
exactly the same as how ``git-rebase`` works, and is not limited to
working with Gerrit hosted projects. It can be used with projects
hosted in GitHub or any other git repo hosting software.

Online documentation:

* http://git-upstream.readthedocs.io/en/latest/

To install:

.. code:: bash

    pip install git-upstream

See also https://pypi.python.org/pypi/git-upstream


You can also install directly from source:

.. code:: bash

    git clone https://git.openstack.org/openstack/git-upstream.git
    cd git-upstream
    pip install .

Developers
----------

Bug reports:

* https://bugs.launchpad.net/git-upstream

Repository:

* https://git.openstack.org/cgit/openstack/git-upstream

Cloning:

.. code:: bash

    git clone https://git.openstack.org/cgit/openstack/git-upstream

or

.. code:: bash

    git clone https://github.com/openstack/git-upstream

A virtual environment is recommended for development.  For example,
git-upstream may be installed from the top level directory:

.. code:: bash

    virtualenv .venv
    source .venv/bin/activate
    pip install -r test-requirements.txt -e .


Patches are submitted via Gerrit at:

* https://review.openstack.org/

Please do not submit GitHub pull requests, they will be automatically closed.

More details on how you can contribute is available on our wiki at:

* http://docs.openstack.org/infra/manual/developers.html

Writing a patch
---------------

All code submissions must be pep8_ and pyflakes_ clean. CI will
automatically reject them if they are not. The easiest way to do
that is to run tox_ before submitting code for review in Gerrit.
It will run ``pep8`` and ``pyflakes`` in the same manner as the
automated test suite that will run on proposed patchsets.

Unit Tests
----------

Unit tests have been included and are in the ``git_upstream/tests``
folder. Many unit tests samples are included as example scenarios in
our documentation to help explain how git-upstream handles various use
cases. To run the unit tests, execute the command:

.. code:: bash

    tox -e py34,py27

* Note: View ``tox.ini`` to run tests on other versions of Python,
  generating the documentation and additionally for any special notes
  on building one of the scenarios to allow direct inspection and
  manual execution of ``git-upstream`` with various scenarios.

The unit tests can in many cases be better understood as being closer
to functional tests.

Support
-------

The git-upstream community is found on the `#git-upstream channel on
chat.freenode.net <irc://chat.freenode.net/#git-upstream>`_

You can also join via this `IRC URL
<irc://chat.freenode.net/#git-upstream>`_ or use the `Freenode IRC
webchat <https://webchat.freenode.net/>`_.


.. _pep8: https://pypi.python.org/pypi/pep8
.. _pyflakes: https://pypi.python.org/pypi/pyflakes
.. _tox: https://testrun.org/tox

What does git-upstream do?
--------------------------

git-upstream provides new git subcommands to support rebasing of
local-carried patches on top of upstream repositories. It provides
commands to ease the use of git for who needs to integrate big upstream
projects in their environment. The operations are performed using Git
commands.

.. note:: Currently git-upstream works best for projects that are
   maintained with Gerrit because the presence of Change-Ids allows
   for fully automated dropping of changes that appear upstream.
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

Using git-upstream
==================

Please see `workflows <doc/source/workflows.rst>`_

Available commands
==================

Please see `subcommands <doc/source/subcommands.rst>`_

Authors
=======

git-upstream was initially written by Darragh Bailey dbailey@hpe.com.
See AUTHORS file for other contributors.

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
