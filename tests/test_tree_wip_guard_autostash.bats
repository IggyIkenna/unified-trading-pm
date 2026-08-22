#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: the autostash CHAIN (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md).
#
# THE INCIDENT THIS REPRODUCES (2026-08-10 slot-1, 107 files). Every `git pull --rebase --autostash`
# stashes the dirty tree, rebases, and pops it back. If the tree already carried stale content from a
# PREVIOUS autostash cycle, each new cycle re-applies and re-preserves it; nothing ever compares the
# popped content against origin, so a revert is indistinguishable from an edit. After enough cycles
# the stash list holds dozens of autostash entries, each a snapshot of the same aging content.
#
# The fix under test:
#   1. autostash_guard_quarantine_stale_pop -- after a pop, files NOT in the caller's --files whose
#      working-tree content differs from origin are quarantined to a NAMED stash and the origin
#      version restored, so the next cycle does NOT re-stash them.
#   2. autostash_guard_bound_backlog -- BEFORE any reconcile, a large autostash backlog is warned on;
#      an extreme one is self-arrested by quarantining the dirty tree first so no new entry forms.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  GUARD="${REPO_ROOT}/scripts/dev/tree-wip-guard.sh"
  WORK="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$WORK"
  cd "$WORK"
  git init -q -b live-defi-rollout .
  git config user.email t@t
  git config user.name t
  printf 'original\n' > shipped.md
  printf 'original\n' > bystander.sh
  git add -A
  git commit -q -m seed
  # A local origin/live-defi-rollout ref that the guard compares working-tree content against.
  git update-ref refs/remotes/origin/live-defi-rollout HEAD
  # shellcheck source=/dev/null
  source "$GUARD"
}

# ── autostash_guard_quarantine_stale_pop ─────────────────────────────────────────────────────

@test "a stale non-named file is quarantined to a named stash and origin restored" {
  # The stale-content signature: the file's working-tree content differs from origin AND is not in
  # the caller's protected set. This is what an autostash pop re-applies from an aging snapshot.
  printf 'STALE REVERTED CONTENT\n' > bystander.sh

  run autostash_guard_quarantine_stale_pop "shipped.md" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]                      # advisory, never fails the run
  [[ "$output" == *"bystander.sh"* ]]      # names the quarantined file
  [[ "$output" == *"quarantined"* ]]
  [ "$(cat bystander.sh)" = "original" ]   # working tree restored to origin, chain broken
  run git stash list
  [[ "$output" == *"safety-snapshot: stale reapplied-autostash"* ]]  # named, recoverable
}

@test "the caller's NAMED files are never quarantined" {
  # A protected path is the caller's own intentional edit -- the guard must leave it alone even if
  # it differs from origin (it is about to be committed by the caller).
  printf 'MY REAL EDIT\n' > shipped.md
  printf 'STALE\n' > bystander.sh

  run autostash_guard_quarantine_stale_pop "shipped.md" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]
  [ "$(cat shipped.md)" = "MY REAL EDIT" ]        # protected file untouched
  [ "$(cat bystander.sh)" = "original" ]          # stale file still quarantined
}

@test "content that MATCHES origin is not quarantined" {
  # A clean pop restores content that matches origin (or the caller left a matching edit) -- that
  # is the benign case and must produce no stash entry.
  printf 'original\n' > bystander.sh
  run autostash_guard_quarantine_stale_pop "shipped.md" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  run git stash list
  [ -z "$output" ]
}

@test "untracked files are ignored" {
  # Autostash does not touch untracked files by default; the guard must not either.
  printf 'scratch\n' > notes.tmp
  run autostash_guard_quarantine_stale_pop "shipped.md" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

# ── autostash_guard_bound_backlog ────────────────────────────────────────────────────────────

@test "a large autostash backlog warns without blocking" {
  for i in 1 2 3 4 5; do
    printf 'base\n' > "f$i.md"
    git add "f$i.md"
    printf 'noise\n' > "f$i.md"          # tracked, dirty -- the real autostash shape
    git stash push -q -m "autostash $i" -- "f$i.md"
  done

  run autostash_guard_bound_backlog "" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]                      # advisory, never blocks the caller
  [[ "$output" == *"autostash"* ]]
  [[ "$output" == *"drop"* ]]              # hands over the recovery path
}

@test "an extreme backlog self-arrests: dirty tree quarantined before the pull" {
  for i in $(seq 1 10); do
    printf 'base\n' > "f$i.md"
    git add "f$i.md"
    printf 'noise\n' > "f$i.md"
    git stash push -q -m "autostash $i" -- "f$i.md"
  done
  printf 'my in-flight edit\n' > shipped.md

  run autostash_guard_bound_backlog "" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]
  [[ "$output" == *"extreme"* ]]
  run git stash list
  [[ "$output" == *"pre-reconcile quarantine"* ]]  # current tree parked before the pull
}

@test "a clean stash list is a no-op" {
  run autostash_guard_bound_backlog "" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "extreme backlog self-arrest does NOT quarantine the caller's protected files" {
  # Dogfooded live 2026-08-10 slot-9: the self-arrest quarantined the caller's OWN plan-flip
  # edit, and the ship then falsely reported "already matches HEAD". The protected list is
  # the work being SHIPPED and must survive untouched even in the extreme case.
  for i in $(seq 1 10); do
    printf 'base\n' > "f$i.md"
    git add "f$i.md"
    printf 'noise\n' > "f$i.md"
    git stash push -q -m "autostash $i" -- "f$i.md"
  done
  printf 'MY SHIPPED FLIP\n' > shipped.md          # protected -- the caller's own edit
  printf 'STALE OTHER\n' > bystander.sh            # non-protected dirty file

  run autostash_guard_bound_backlog "shipped.md" "origin/live-defi-rollout"
  [ "$status" -eq 0 ]
  [ "$(cat shipped.md)" = "MY SHIPPED FLIP" ]      # protected file survives intact
  [ "$(cat bystander.sh)" = "original" ]           # non-protected dirty file quarantined + restored
  run git stash list
  [[ "$output" == *"pre-reconcile quarantine"* ]]  # non-protected dirty files still parked
}
