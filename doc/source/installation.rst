Installation
============

To install git-upstream from source, run:

.. code:: bash

  pip install git-upstream

A virtual environment is recommended for development.  For example,
git-upstream may be installed from the top level directory:

.. code:: bash

    virtualenv .venv
    source .venv/bin/activate
    pip install -r test-requirements.txt -e .

Alternatively, the current release can be installed systemwide from
pypi:

.. code:: bash

  sudo pip install git-upstream


Documentation
-------------

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
