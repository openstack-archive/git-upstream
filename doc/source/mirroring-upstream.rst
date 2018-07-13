Mirroring Upstream
==================

Usually you reach this point shortly after you've decided that while
you could maintain an 'upstream' remote in your local clone, it would
be much more convenient if you could ensure that all developers on the
team had access to the upstream code as well as local changes carried
when they clone.


Manual
~~~~~~

To explain this usage of the git-upstream tool we are going to use a
real-world (but trivial) example, by performing some sample operations
on a project called ``jenkins-job-builder``.

In this example, we will take our local clone, that has already diverged,
pull in the upstream and then push under a new namespace to your local
mirror.

1. Start by setting the following environment variables:

   .. code:: bash

       export REPO_NAME="jenkins-job-builder"
       export UPSTREAM_REMOTE="https://github.com/openstack-infra/${REPO_NAME}.git"

2. Clone your local copy

   .. code:: bash

       git clone https://internal.example.net/team/${REPO_NAME}
       cd ${REPO_NAME}

3. Add the original remote

   We will name it *upstream* (for the sake of originality).

   .. code:: bash

       git remote add upstream $UPSTREAM_REMOTE

4. Fetch objects and refs from upstream remote

   .. code:: bash

       git fetch --all upstream

5. Push refs

   Push refs defined upstream to the ``origin`` remote (*i.e.*, the
   internal copy of the repository with local patches) using the string
   ``upstream`` as prefix, also pushing tags.

   .. code:: bash

       git for-each-ref refs/remotes/upstream --format "%(refname:short)" | \
         sed -e 's:\(upstream/\(.*\)\)$:\1\:refs/heads/upstream/\2:' | \
         xargs git push --tags origin

You may want to repeat the last two commands before starting any new
feature development or a bug fix.


At this point now, anyone looking to see what changes have happened
upstream need only pull from your internal mirror (or fork) and will
be able to inspect and view all differences.


Automated
~~~~~~~~~


The above is all good, but the next step is to configure a periodic job
in something like Jenkins (we did use jenkins-job-builder after all)
that will ensure it is kept up to date automatically.

There are obviously other options for this besides a period job, if the
upstream is hosted on a Gerrit instance you can easily subscribe to
changes merging in the upstream project to be more event based, but if
it's GitHub, unless you have admin access it's more likely to be poll
based. We'll focus on using polling but cover jobs for both remotes.

Within the contrib examples folder of the project source there is an
example of performing this mirroring via a jenkins job definition and
script.

Project:

    This creates two jobs one for git-upstream itself and another for
    Gerrit. The former uses a simple `<org>/<project>` pattern as it was
    common to perform this for many projects from the same host, while
    the latter uses a simple macro for an arbitrary git host.

    .. literalinclude:: ../../contrib/jjb/projects.yaml
       :language: yaml

Jenkins Job Definition:

    This includes the template that is expanded out based on the projects
    definition, and also makes references to some macros to make reuse
    across multiple jobs of these type easier.

    .. literalinclude:: ../../contrib/jjb/mirror.yaml
       :language: yaml

Macros and Defaults:

    .. literalinclude:: ../../contrib/jjb/macros.yaml
       :language: yaml

    .. literalinclude:: ../../contrib/jjb/defaults.yaml
       :language: yaml


Mirror Script

    Finally the script that performs the work, compared to the trivial
    one liner above this needs to perform a few other checks and steps
    to pick up all of the remote refs in a fully reusable manner.

    .. literalinclude:: ../../contrib/jjb/scripts/mirror-upstream.bash
       :language: bash