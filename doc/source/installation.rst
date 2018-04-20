Installation
============

To install git-upstream from pypi_, run:

.. code:: bash

  pip install --user git-upstream

Alternatively, the current release can be installed system-wide from
pypi_:

.. code:: bash

  sudo pip install git-upstream


Installing directly from source is possible, first clone and then
install using pip:

.. code:: bash

    git clone https://git.openstack.org/openstack/git-upstream.git
    cd git-upstream
    pip install .

Or setup.py:

.. code:: bash

    git clone https://git.openstack.org/openstack/git-upstream.git
    cd git-upstream
    python setup.py install

Or alternatively:

.. code:: bash

    git clone https://git.openstack.org/openstack/git-upstream.git
    cd git-upstream
    easy_install .


If you want command line completion (using tab), install the provided
"bash completion" file

.. code:: bash

    mkdir ~/bin && cp ./bash_completion/git-upstream ~/bin
    echo ". ~/bin/git-upstream" >> ~/.bash_profile


Verify your installation.

.. code:: bash

    pip show git-upstream
    ---
    Name: git-upstream
    Version: 0.12.1
    Summary: git tool to help manage upstream repositories
    Home-page: https://pypi.org/project/git-upstream
    Author: Darragh Bailey
    Author-email: dbailey@hpe.com
    License: Apache License (2.0)
    Location: /home/<username>/.local/lib/python2.7/site-packages
    Requires: argcomplete, pbr, six, GitPython

    git-upstream --help
    usage: git-upstream [--version] [-h] [-q | -v] <command> ...

    [...]

.. _pypi: https://pypi.org/project/git-upstream

Installing for Development
--------------------------

A virtual environment is recommended for development.  For example,
git-upstream may be installed from the top level directory:

.. code:: bash

    virtualenv .venv
    source .venv/bin/activate
    pip install -r test-requirements.txt -e .


Generating Documentation
------------------------

Documentation is included in the ``doc`` folder. To generate docs
locally execute the command::

    tox -e docs

The generated documentation is then available under
``doc/build/html/index.html``.


* Note: When behind a proxy it is necessary to use ``TOX_TESTENV_PASSENV``
  to pass any proxy settings for this test to be able to check links are
  valid.


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

Test Coverage
-------------

To measure test coverage, execute the command::

    tox -e cover
