#!/bin/bash -ex

[ -z "${REPO_PATH}" ] && REPO_PATH="." || REPO_PATH=${REPO_PATH}

# The logic below is needed to preserve the old behaviour of the template
# while providing more flexibility around the git namespace selection
if [ -z "${GIT_NAMESPACE_PREFIX}" ];
then
    GIT_NAMESPACE_PREFIX="upstream/"
elif [ ${GIT_NAMESPACE_PREFIX} == '""' ];
then
    GIT_NAMESPACE_PREFIX=""
else
    GIT_NAMESPACE_PREFIX="${GIT_NAMESPACE_PREFIX}/"
fi

[ -z "${GERRIT_URL}" ] && { echo "Required var GERRIT_URL not set"; exit 2; }

cd ${REPO_PATH}

git remote prune origin
git fetch --tags
git remote set-head origin -d

if [[ -z "${UPSTREAM_REPO}" ]]
then
  # if using git < 1.7.5 then will need to replace the url extraction with
  # 'git config --get remote.origin.url', however this will ignore some of
  # how git allows control of the url.
  UPSTREAM_REPO="$(git ls-remote --get-url origin)"
  UPSTREAM_REPO="${UPSTREAM_REPO##*:}"
  UPSTREAM_REPO="${UPSTREAM_REPO##*/}"
fi

LOCAL_REPO=${LOCAL_REPO:-${UPSTREAM_REPO}}
[ -z "${LOCAL_TEAM}" ] && { echo "Required var LOCAL_TEAM not set"; exit 2; }
[ -z "${LOCAL_REPO}" ] && { echo "Required var LOCAL_REPO not set"; exit 2; }

DRY_RUN_FLAG=`[ "${DRY_RUN}" = "true" ] && echo -n "--dry-run"` || true
PUSH_URL="${GERRIT_URL}/${LOCAL_TEAM%% }/${LOCAL_REPO%% }.git"

FORCE_FLAG=
if [ "${FORCE_PUSH_ALL}" = "true" ]
then
  FORCE_FLAG="+"
fi

SPECIFIC_REFS=""

OPENSTACK_META=`git ls-remote origin refs/meta/openstack/*` || true
if [ -n "${OPENSTACK_META}" ]
then
    git fetch origin +refs/meta/openstack/*:refs/meta/openstack/*
    SPECIFIC_REFS="${SPECIFIC_REFS}${SPECIFIC_REFS:+ }${FORCE_FLAG}refs/meta/openstack/*:refs/meta/openstack/*"
fi

OPENSTACK_MILESTONE_PROPOSED=`git show-ref --verify refs/heads/milestone-proposed 2>/dev/null` || true
if [ -n "${OPENSTACK_MILESTONE_PROPOSED}" ]
then
    SPECIFIC_REFS="${SPECIFIC_REFS}${SPECIFIC_REFS:+ }+refs/remotes/origin/milestone-proposed:refs/heads/${GIT_NAMESPACE_PREFIX}milestone-proposed"
fi

git push $DRY_RUN_FLAG "$PUSH_URL" ${SPECIFIC_REFS} ${FORCE_FLAG}refs/remotes/origin/*:refs/heads/${GIT_NAMESPACE_PREFIX}*
git push $DRY_RUN_FLAG "$PUSH_URL" ${FORCE_FLAG}refs/tags/*:refs/tags/${GIT_NAMESPACE_PREFIX}*
