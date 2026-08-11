#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's stage-before-quarantine ordering
# (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, P0 "do not quarantine before
# staging").
#
# THE BUG (measured 2026-08-10): with an extreme autostash backlog (>=10 entries), the
# pre-reconcile self-arrest (`autostash_guard_bound_backlog`) quarantines the current dirty
# tree into a named stash so the next pull produces no NEW autostash entry. When that
# quarantine ran BEFORE the caller's named files were staged, the payload itself could be
# swept into the stash (dogfooded live 2026-08-10 slot-9); staging then found "nothing to
# stage", and the run exited 0 with "Named files already match HEAD" -- a no-op push
# reported as a landed one. Nothing downstream distinguishes the two.
#
# THE FIX: safe-doc-push stages the caller's named files FIRST, before any quarantine step.
# Staging is what makes them invisible to `git diff --name-only` -- exactly the enumeration
# every quarantine path uses -- so the extreme-pile self-arrest can only quarantine what
# remains: genuinely foreign dirty files. The guard's protected-set check is belt; the
# staging-first ordering is suspenders.
#
# Run: bats tests/test_safe_doc_push_quarantine_after_staging.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  GUARD="${REPO_ROOT}/scripts/dev/tree-wip-guard.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  printf 'initial\n' > README.md
  printf 'payload v1\n' > payload.md
  printf 'bystander v1\n' > bystander.md
  git add README.md payload.md bystander.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  # Fake `sleep` on PATH so the script's retry backoff is instant -- these tests care about
  # the eventual exit code and messages, not real wall-clock contention.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
}

# Seed the stash list with 11 entries whose messages match the guard's 'autostash' grep, so
# autostash_guard_bound_backlog takes its extreme-pile (>=10) self-arrest path.
seed_extreme_backlog() {
  for i in $(seq 1 11); do
    printf 'seed change %s\n' "$i" >> README.md
    git stash push -q -m "WIP on live-defi-rollout: autostash backup $i" -- README.md
    git stash apply -q "stash@{0}"
  done
}

@test "extreme autostash pile: the payload ships to origin, quarantine sweeps only the bystander, no false already-match-HEAD" {
  seed_extreme_backlog
  printf 'payload v2\n' > payload.md
  printf 'bystander v2\n' > bystander.md

  # Shared-index path is where the bug lives (isolated mode commits from a private worktree
  # and never touches the caller's dirty tree).
  export SDP_ISOLATED=0
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: ship payload" --files "payload.md"

  [ "$status" -eq 0 ]
  # The extreme-pile self-arrest actually fired this run.
  [[ "$output" == *"current dirty tree quarantined"* ]]
  # The false-success marker must never appear -- the payload had a real diff at entry.
  [[ "$output" != *"already match HEAD"* ]]
  # The payload edit landed on origin...
  run git show origin/live-defi-rollout:payload.md
  [ "$output" = "payload v2" ]
  # ...and survives intact in the caller's working tree.
  [ "$(cat payload.md)" = "payload v2" ]
  # The bystander (dirty, non-payload) is what got quarantined: restored to origin.
  [ "$(cat bystander.md)" = "bystander v1" ]
}

@test "a STAGED payload is invisible to the extreme-backlog quarantine even with an empty protected set" {
  # The mechanism behind the fix: staging makes the payload invisible to `git diff --name-only`,
  # which is what autostash_guard_bound_backlog enumerates. Prove it with an EMPTY protected
  # set -- if staging alone weren't sufficient, the self-arrest would sweep the payload too.
  # shellcheck source=/dev/null
  source "$GUARD"

  for i in $(seq 1 10); do
    printf 'base\n' > "f$i.md"
    git add "f$i.md"
    printf 'noise\n' > "f$i.md"
    git stash push -q -m "autostash $i" -- "f$i.md"
  done
  printf 'MY PAYLOAD EDIT\n' > payload.md
  printf 'STALE OTHER\n' > bystander.md

  git add payload.md   # safe-doc-push's pre-staging, applied directly
  run autostash_guard_bound_backlog "" "origin/live-defi-rollout"

  [ "$status" -eq 0 ]
  [ "$(cat payload.md)" = "MY PAYLOAD EDIT" ]   # staged payload survives the self-arrest
  [ "$(cat bystander.md)" = "bystander v1" ]    # unstaged bystander quarantined + restored to origin
  run git stash list
  [[ "$output" == *"pre-reconcile quarantine"* ]]
}
