#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_stage_first_no_quarantine.bats -- the P0 ordering fix in
# scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10,
# "Second symptom, same mechanism", todo 2: "Do not quarantine before staging. Stage the
# named files FIRST (they are the payload), then quarantine only what remains, so the payload
# can never be swept into the stash it is about to be compared against.").
#
# THE BUG: the pre-commit reconcile (merge-pull divergence / ahead>0) ran
# `git pull --rebase --autostash` BEFORE the caller's files were staged. That stashes the
# ENTIRE dirty tree -- staged AND unstaged (a staged payload is swept and comes back
# UNSTAGED; verified empirically 2026-08-11) -- so the payload spent the rebase sitting in
# the autostash. If that pop failed, or a concurrent process interleaved, the payload was
# exactly the content a "nothing to stage -- already matches HEAD" check would read as
# landed when it was not.
#
# THE FIX: stage the named files FIRST and commit them BEFORE any stash-capable reconcile.
# Once committed, the payload lives in git history and no autostash can touch it; origin
# drift is handled by the post-commit push-race rebase, which then only ever sweeps foreign
# uncommitted work -- or nothing at all when the tree is clean.
#
# This test forces the divergence case (a local commit ahead of origin + a peer commit on
# origin, on non-overlapping files so the rebase is clean) and asserts the observable
# discriminator: the run must NOT print "Created autostash". The pre-fix script's pre-commit
# reconcile sweeps the dirty payload and prints it on every attempt; the fix commits the
# payload first, so by the time the push-race rebase runs the tree is clean and git has
# nothing to stash.
#
# Run: bats tests/test_safe_doc_push_stage_first_no_quarantine.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "base" > a.txt
  echo "base" > b.txt
  echo "base" > c.txt
  git add a.txt b.txt c.txt
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout >/dev/null 2>&1

  # A local commit ahead of origin (work's own, un-pushed) -- this is what puts work and
  # origin on divergent histories, forcing the stash-capable reconcile in the pre-fix code.
  echo "local" > a.txt
  git add a.txt
  git commit -q -m "local work commit"

  # A peer commit on origin -- on a DIFFERENT file (c.txt) so the eventual rebase is clean.
  git clone -q "${WORK}/origin.git" "${WORK}/peer"
  (
    cd "${WORK}/peer"
    git config user.email "peer@example.com"
    git config user.name "peer"
    git checkout -q -B live-defi-rollout origin/live-defi-rollout
    echo "peer" > c.txt
    git add c.txt
    git commit -q -m "peer commit"
    git push -q origin HEAD:live-defi-rollout
  )

  # Fake `sleep` on PATH so the script's retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  # Shared-index path: the staging-order fix lives in the shared-index retry loop. Isolated
  # mode re-execs in a private worktree (copying the file in), which does not exercise the
  # reconcile ordering this test guards.
  export SDP_ISOLATED=0
}

@test "a dirty payload in a diverged tree is committed before any stash-capable reconcile (no autostash is created)" {
  cd "${WORK}/work"
  echo "PAYLOAD" > b.txt

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: ship payload" --files "b.txt"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # The observable discriminator: the pre-fix script's pre-commit reconcile swept the dirty
  # payload with `git pull --rebase --autostash` and printed "Created autostash". The fix
  # commits the payload before any stash-capable reconcile, so by the time the push-race
  # rebase runs the tree is clean and git has nothing to autostash.
  [[ "$output" != *"Created autostash"* ]]
  # The payload genuinely landed on origin.
  run git -C "${WORK}/work" show "origin/live-defi-rollout:b.txt"
  [[ "$output" == *"PAYLOAD"* ]]
  # And nothing was left behind in the stash.
  run git -C "${WORK}/work" stash list
  [ -z "$output" ]
}
