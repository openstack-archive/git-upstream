# Importing from upstream: using git-upstream

**Note**: this guide assumes that you are using a branch named *master* to
maintain your new features or bug fixes that sit on top of the upstream code of
some project (probably somewhat related to OpenStack).

It is also assumed you are tracking releases, which is only one of the possible
approaches to upstream tracking. Another approach would be tracking the master
tip of a project. Of course even other strategies are possible.

## Install git-upstream on a development workstation

Clone git-upstream from its git repository.

```bash
git clone https://git.openstack.org/openstack/git-upstream.git
cd git-upstream
# Install git-upstream itself
python setup.py install
```

Or

```bash
git clone https://git.openstack.org/openstack/git-upstream.git
cd git-upstream
easy_install .
```

If you want command line completion (using tab), install the argcomplete
package and source the provided "bash completion" file

```bash
mkdir ~/bin && cp ./bash_completion/git-upstream ~/bin
echo ". ~/bin/git-upstream" >> ~/.bash_profile
pip install argcomplete
```

Verify your installation.
```bash
pip show git-upstream
---
Name: git-upstream
Version: unknown-version
Location: ../ve-git-upstream/lib/python2.7/site-packages/git-upstream-unknown_version-py2.7.egg
Requires: GitPython

git-upstream --help
usage: git-upstream [--version] [-h] [-q | -v] <command> ...

[...]
```

## Initial import of an upstream project

To explain the usage of the git-upstream tool we are going to use a real-world
(but trivial) example, by performing some sample operations on a project called
``jenkins-job-builder``.

In this example, we will create a local file based Git repository to host our
mirror of jenkins-job-builder. You could also use an existing internal mirror,
a Github fork, etc.

Start by setting the following environment variables:

```bash
export REPO_NAME="jenkins-job-builder"
export INTERNAL_REMOTE="file:///tmp/jenkins-job-builder.git"
export UPSTREAM_REMOTE="https://github.com/openstack-infra/jenkins-job-builder.git"
export FIRST_IMPORT_REF="0.5.0"
```

1) Create two empty repositories, one to serve as your working copy, and one to
serve as the remote:

```bash
git init --bare /tmp/${REPO_NAME}.git
git init $REPO_NAME
cd $REPO_NAME
```

2) Add your remotes

We will name it *origin* and *upstream* (for the sake of originality).

```bash
git remote add origin $INTERNAL_REMOTE
git remote add upstream $UPSTREAM_REMOTE
```

3) Fetch objects and refs from upstream remote

```bash
git fetch --all
```

4) Push refs

Push refs defined upstream to the `origin` remote  (*i.e.*, the internal copy
of the repository with local patches) using the string `upstream` as prefix,
also pushing tags.

```bash
git for-each-ref refs/remotes/upstream --format "%(refname:short)" | \
  sed -e 's:\(upstream/\(.*\)\)$:\1\:refs/heads/upstream/\2:' | \
  xargs git push --tags origin
```

You may want to repeat the last two commands before starting any new feature
development or a bug fix.

5) Check-out the first import commit (*e.g.*, tag or SHA1)

This will be the starting point for the internal development.

```bash
git checkout -b import/$FIRST_IMPORT_REF $FIRST_IMPORT_REF
```

6) Create and switch to the master branch

```bash
git checkout -b master
```

Now the tips of master, `$FIRST_IMPORT_REF` and `import/$FIRST_IMPORT_REF`
should be pointing to the same commit.

Push local master branch to the remote origin, and make `origin master` the
default when pushing commits.

```bash
git push -u origin master
```

## Writing your patches/features

Now start to develop new feature or fix bugs on master, as usual.
For this example, we are going to change the .gitreview file in order to use a
local Gerrit server.

```bash
sed -i 's/review\.openstack\.org/gerrit\.my\.org/' .gitreview
```

Don’t forget to commit and push (after this step, you may want to use git
review as usual)

```bash
git commit -a -m "Set .gitreview content to use internal gating infra"
git push
```

Our master (local and remote) tip should be now pointing to the last commit.

## Importing single patches from upstream

Before implementing any feature or fixing any bug (in short, before reinventing
the wheel), check if someone has already implemented the required code
upstream.

If not, try not to develop code only for your specific needs, be ambitious and
try to develop something that could be useful for the whole community. This way
you can propose your patch upstream and save yourself a lot of trouble which
arise when there are many local changes to carry on the tip of upstream
releases.

In this example, we tried to use our code and we found out that the job
filtering isn’t working! Fortunately, Antoine Musso has already fixed this bug,
as we can see in the upstream repo.

```bash
git show --summary 2eca0d11669b55d4ab02ba609a15aa242fd80d14
commit 2eca0d11669b55d4ab02ba609a15aa242fd80d14
Author: Antoine Musso <hashar@free.fr>
Date:   Mon Jun 24 14:36:52 2013 +0200

    job filtering was not working properly

    When passing job names as arguments to 'update', the command is supposed
    to only retain this jobs.  Due to the job being a dict, the filter would
    never match and the none of the job would be updated.

    This has apparently always been broken since the feature got introduced
    in 85cf7a41.  Using job.['name'] fix it up.

    Change-Id: Icf4d5b0bb68777f7faff91ade04451d4c8501c6a
    Reviewed-on: https://review.openstack.org/34197
    Reviewed-by: Clark Boylan <clark.boylan@gmail.com>
    Approved: James E. Blair <corvus@inaugust.com>
    Reviewed-by: James E. Blair <corvus@inaugust.com>
    Tested-by: Jenkins
```

We are also interested in the following commit, which adds the Environment File
Plugin (finally!).

```bash
git show --summary bf4524fae25c11640ef839aa422ac81bd926ca20
commit bf4524fae25c11640ef839aa422ac81bd926ca20
Author: zaro0508 <zaro0508@gmail.com>
Date:   Mon Jul 1 11:21:24 2013 -0700

    add Environment File Plugin

    This commit adds the Environment File Plugin to JJB.
    https://wiki.jenkins-ci.org/display/JENKINS/Envfile+Plugin

    Change-Id: Id35a4d6ab25b0440303da02bb91007b459979243
    Reviewed-on: https://review.openstack.org/35170
    Reviewed-by: Arnaud Fabre <fabre.arnaud@gmail.com>
    Reviewed-by: James E. Blair <corvus@inaugust.com>
    Approved: Clark Boylan <clark.boylan@gmail.com>
    Reviewed-by: Clark Boylan <clark.boylan@gmail.com>
    Tested-by: Jenkins
```

Import those changes simply cherry-picking the two commits. Don’t forget to
push (review!) your changes.

```bash
git cherry-pick 2eca0d11669b55d4ab02ba609a15aa242fd80d14
git cherry-pick bf4524fae25c11640ef839aa422ac81bd926ca20
git push
```

## Importing new versions from upstream

Days passes and finally a new releases comes out.

```bash
git fetch --all
git for-each-ref refs/remotes/upstream --format "%(refname:short)" | \
  sed -e 's:\(upstream/\(.*\)\)$:\1\:refs/heads/upstream/\2:' | \
  xargs git push --tags origin
```

A lot of work has been done upstream and we need to rebase our master onto the
upstream master branch. In this process we must skip all the commits we already
cherry-picked some days ago, of course.

**Note**: the rebasing for this example is trivial but it is just to break the
ice. Later in this guide we will address rebasing conflicts that can occur in
the real world.

Create a new local branch with the new release tag as a starting point

```bash
git branch import/0.6.0 0.6.0
```
## Running git-upstream

Finally, it is time to run git-upstream! Before doing so make sure the current
branch is master

```bash
git checkout master
```

```bash
git-upstream import import/0.6.0
Searching for previous import
Starting import of upstream
Successfully created import branch
Attempting to linearise previous changes
Successfully applied all locally carried changes
Merging import to requested branch 'HEAD'
Successfully finished import:
target branch: 'HEAD'
upstream branch: 'import/0.6.0'
import branch: 'import/0.6.0'
```

***No errors***, we have been lucky!

What has just happened?

git-upstream has created a new branch named `import/0.6.0-base` which tip is
set to the commit pointed by the release tag `0.6.0`, and has rebased all
changes present in our local master which were not already present in the
upstream new release (`import/0.6.0-base`) onto `import/0.6.0-base`.

You can see that running the following command

```bash
git log --graph --oneline --all --decorate
```

For this trivial example, the only commit not present in the upstream release
was about the customisation of the .gitreview file.

The default strategy git-upstream uses to find duplicate entries is the
comparison of Change-id entries in commit messages.  Of course, it’s not
possible to compare directly the SHA1 for a commit because the cherry-picking
changes the information used for SHA1 calculation

---
**Note**: A git commit SHA1 is generated from the following information:

* commit message
* author signature (identity + timestamp)
* committer signature (identity + timestamp)
* tree SHA1 (hierarchy of directories and files within the commit)
* list of the SHA1's of the parent commits

---

The local branch `import/0.6.0` now contains our local changes rebased onto the
new upstream release. git-upstream has also merged this branch with the local
master branch (with "ours" strategy) to allow the normal workflow
(committing/merging to master for review).

**Note**: The "final" merging step is not mandatory. Of course you can keep a
separate branch for each new import. On one hand this strategy allows a
"cleaner" history as you will always have your local changes rebased on top of
the exact copy of the upstream repository. On the other hand you will be
creating a new branch every time you want to import upstream code.
You can customise the name of the import branch using the `--import-branch
<branch name>` option.

In principle, you could also replace your master branch (history) with the new
import branch created by git-upstream... Unfortunately there is no way to do
this without requiring ad-hoc intervention on cloned copies of the repository
(aka do-not-do-that(TM))

To disable automatic merging, just use the `--no-merge` flag

```bash
 git-upstream import --no-merge import/0.6.0
```

# Handling conflicts

Of course in the real world things are much more complicated. From time to time,
during import, you will get rebasing conflict (for instance due to changes from
both local and upstream repository to the same piece of code).

In case of rebasing conflict, git-upstream will stop allowing the user to fix
the conflict.

```bash
git-upstream import import/0.5.0 --into master
Searching for previous import
Starting import of upstream
Successfully created import branch
Attempting to linearise previous changes
ERROR   : Rebase failed, will need user intervention to resolve.
error: could not apply f9b4fca... Fixup for openstack review
When you have resolved this problem, run "git rebase --continue".
If you prefer to skip this patch, run "git rebase --skip" instead.
To check out the original branch and stop rebasing, run "git rebase --abort".
Could not apply f9b4fca... Fixup for openstack review
Import cancelled
```

Let's find out why git-upstream failed and let's try to continue the rebasing
manually.

```bash
git status
# HEAD detached from 8e6b9e9
# You are currently rebasing branch 'import/0.5.0' on '8e6b9e9'.
#   (fix conflicts and then run "git rebase --continue")
#   (use "git rebase --skip" to skip this patch)
#   (use "git rebase --abort" to check out the original branch)
#
# Unmerged paths:
#   (use "git reset HEAD <file>..." to unstage)
#   (use "git add <file>..." to mark resolution)
#
# both modified:      jenkins_jobs/cmd.py
# both modified:      jenkins_jobs/modules/hipchat_notif.py
#
no changes added to commit (use "git add" and/or "git commit -a")
```

Depending on the type of conflict, you will could:

* drop the local change

  Issuing `git rebase --skip`

* edit conflicting code

  Change conflicting code in order to accommodate local changes to the new
  upstream code.
  You can later resume rebasing process issuing `git rebase --continue`

Currently git-upstream can't resume the rebasing process. So, if needed, the
final "merging" steps have to be performed manually:

```bash
git merge -s ours --no-commit <import-xxxx>
```

Replacing tree contents with those from the import branch

```bash
git read-tree -u --reset <import-xxxx>
```

Committing merge commit

```bash
git commit --no-edit
```

**Note**: git-upstream performs exactly those steps in order to replace the
content of `master` branch with the import branch preserving the history.

# Integration with Gerrit

You may want to use review with Gerrit the output of git-upstream, in order to
perform tests, gating, etc.

You have 2 options for doing that:

## Re-review every new commit

In this case we want to review every new commit (since the last import). In
order to do so, use the `--no-merge` flag of git-upstream import command, and:

```bash
git checkout import-xxxxx
git push gerrit import-xxxxx-base:import-xxxxx
git review import-xxxxx
```

If there is more than one new commit, git-review will ask to confirm the
submission of multiple changes.

## Re-review only the final merge commit

This would be possible by using the `--import-branch` option of import command
and **pushing directly** (*i.e.*: bypassing Gerrit) the new branch to the local
repo. For instance:

```bash
TIMESTAMP=$(date +"%Y%m%d%H%M%s")
git upstream import --import-branch "import/import-$TIMESTAMP" upstream/master
git push gerrit import/import-$TIMESTAMP:import/import-$TIMESTAMP
```

Then, create a valid `Change-Id` for the merge commit

```bash
git commit --amend -C HEAD --no-edit
```

Locally, git-review will still complain about the presence of N+M commits which
would be committed BUT on the remote side all those commits will be recognised
as already present in one of the two branch involved in the merge.

```bash
git review -R -y master
```
