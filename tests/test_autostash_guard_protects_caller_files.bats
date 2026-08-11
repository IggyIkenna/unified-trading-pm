#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_autostash_guard_protects_caller_files.bats -- the caller's own --files must survive
# `autostash_guard_bound_backlog`'s extreme-backlog quarantine
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10, finding F8).
#
# THE BUG (measured live 2026-08-11): `autostash_guard_bound_backlog` takes ($1 protected paths,
# $2 remote ref). quickmerge.sh called it with ONLY the remote ref -- which landed in the
# PROTECTED slot. `protected` was therefore a branch name that matches no path, nothing was ever
# protected, and once the stash list passed the >=10-entry trigger the guard quarantined the
# caller's OWN --files and `git checkout <branch> --`'d them back to HEAD. The run then carried
# on and shipped the reverted content. On this host that day the stash list held 42 entries, so
# the trigger was permanently armed: a run shipping 5 files had all 5 reverted mid-flight.
#
# The guard's own header already stated the invariant -- "these are the work being SHIPPED and
# must NEVER be quarantined, even in the extreme case" -- so the function was right and only the
# call site was wrong. safe-doc-push.sh passed both arguments correctly throughout, which is why
# the loss only ever showed up through quickmerge.
#
# Two layers, because the defect was in the ARGUMENT ORDER rather than in the logic:
#   1. behavioural -- the extracted real function must leave protected paths alone;
#   2. call-site -- quickmerge.sh must pass --files FIRST. A behavioural test alone would have
#      stayed green through the entire incident.
#
# Hermetic: a real local git repo under BATS_TEST_TMPDIR (bats auto-cleans it), no network.
#
# Run: bats tests/test_autostash_guard_protects_caller_files.bats

setup() {
  # Tests must NOT take a host-wide lock. push-host-governor.sh hands out K=8 tokens PER HOST,
  # shared with real safe-doc-push runs, so under `bats -j` these contended with each other AND
  # with a peer session's genuine push — exit codes became a function of unrelated fleet
  # activity. One run green, the next red, the failure moving between tests.
  export PUSH_GOV_DISABLE=true
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  GUARD_SH="${REPO_ROOT}/scripts/dev/tree-wip-guard.sh"
  QM_SH="${REPO_ROOT}/scripts/quickmerge.sh"

  REPO="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$REPO"
  cd "$REPO" || return 1
  git init -q .
  git config user.email t@t.t && git config user.name t
  echo mine > mine.txt && echo theirs > theirs.txt && echo noise > noise.txt
  git add -A && git commit -qm init
  # A local ref standing in for origin/<branch>, so the guard's `git checkout <branch> -- <f>`
  # revert path resolves without a remote.
  git branch upstream

  eval "$(sed -n '/^autostash_guard_bound_backlog() {/,/^}/p' "$GUARD_SH")"
}

# Push the stash list past the guard's >=10 extreme-backlog trigger with entries whose subjects
# match what it counts ('autostash').
arm_extreme_backlog() {
  # noise.txt is TRACKED (committed in setup) -- `git stash push -- <pathspec>` silently does
  # nothing for an untracked path without -u, which would leave the trigger unarmed and every
  # behavioural test below vacuously green.
  for i in $(seq 1 11); do
    echo "noise $i" > noise.txt
    git stash push -q -m "autostash" -- noise.txt
  done
  [ "$(git stash list | grep -ci autostash)" -ge 10 ]
}

@test "a protected (--files) path survives the extreme-backlog quarantine; an unprotected one is parked" {
  arm_extreme_backlog
  echo "my shipped edit" > mine.txt
  echo "peer edit" > theirs.txt

  run autostash_guard_bound_backlog "mine.txt" "upstream"
  [ "$status" -eq 0 ]

  # The work being shipped is untouched...
  grep -qx "my shipped edit" mine.txt
  # ...and the unprotected file was quarantined and reverted (parked in a stash, not destroyed).
  grep -qx "theirs" theirs.txt
  git stash list | grep -q "pre-reconcile quarantine"
}

@test "THE BUG: passing only the remote ref leaves the caller's files unprotected" {
  # Reproduces the exact pre-fix call shape. This is what shipped reverted content.
  arm_extreme_backlog
  echo "my shipped edit" > mine.txt

  run autostash_guard_bound_backlog "upstream"
  [ "$status" -eq 0 ]

  # The caller's own file was reverted to HEAD -- the loss, demonstrated.
  grep -qx "mine" mine.txt
}

@test "every protected path in a multi-file --files list survives" {
  arm_extreme_backlog
  echo "a" > mine.txt && echo "b" > theirs.txt

  run autostash_guard_bound_backlog "mine.txt theirs.txt" "upstream"
  [ "$status" -eq 0 ]
  grep -qx "a" mine.txt
  grep -qx "b" theirs.txt
}

@test "CALL SITE: quickmerge.sh passes --files FIRST, not the remote ref" {
  # The behavioural tests above all passed throughout the incident; only this one would have
  # caught it. Anchored on the argument ORDER, which is what was wrong.
  run grep -n 'autostash_guard_bound_backlog "\$FILES_ARG" "\${_QM_REMOTE_REF}"' "$QM_SH"
  [ "$status" -eq 0 ]

  # ...and the pre-fix single-argument form must not come back.
  run grep -n 'autostash_guard_bound_backlog "\${_QM_REMOTE_REF}" ||' "$QM_SH"
  [ "$status" -ne 0 ]
}

@test "CALL SITE: safe-doc-push.sh also passes its named files first (the call site that was always right)" {
  run grep -n 'autostash_guard_bound_backlog "\${FILES\[\*\]}"' "${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  [ "$status" -eq 0 ]
}
