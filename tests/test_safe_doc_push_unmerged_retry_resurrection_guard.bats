#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the "third symptom" in
# safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md: a RETRIED safe-doc-push.sh
# invocation against a checkout an earlier attempt left with an UNMERGED (conflicted) index
# entry resurrects the OLD (deleted) side of a rename with STALE content instead of failing
# fast.
#
# ROOT CAUSE (confirmed by live reproduction, not inferred): when `git pull --rebase --autostash`
# hits a delete/modify conflict on the autostash pop (the caller's staged deletion of a rename's
# old path vs. origin's independent edit to that same path since the caller's last sync), git
# resolves the pop by leaving the CONFLICTING content on disk, UNMERGED in the index -- not the
# caller's intended deletion. That first run correctly hard-stops (autostash_rebase_reconcile's
# explicit-pop failure -> exit 3). The bug was what a SECOND invocation against that same tree did:
# the plain `git pull` in the pre-commit branch fails with git's own "Pulling is not possible
# because you have unmerged files" -- text that matched none of the divergent-branches/would-be-
# overwritten phrases routing into autostash_rebase_reconcile's conflict handling, so it fell into
# the GENERIC retriable branch, burned all MAX_ATTEMPTS attempts on a state no retry could fix, and
# exited 5 with "your named files are byte-identical ... re-running is safe" -- false for this
# case, with the resurrected content sitting on disk the whole time, one `git add` away from
# landing as a fresh, unintended commit.
#
# THE FIX: a guard at the very top of the script (before isolated-worktree setup, before the
# retry loop) checks for pre-existing unmerged index entries and hard-stops immediately (exit 3,
# naming the conflicted path(s)) rather than ever reaching stage_named_files()/git add on a
# corrupted tree.
#
# This test constructs the UD (unmerged, deleted-by-us / modified-by-them) index state directly
# via a real conflicting merge, rather than depending on the specific autostash-pop failure mode
# that originally produced it -- the guard's contract is "any pre-existing unmerged path", and a
# direct merge conflict is the more deterministic, faster way to reach exactly that index shape.
#
# Hermetic: no network (an "origin" is a second local repo), mirrors the established pattern in
# test_safe_doc_push_rename_source_goneless_add.bats / test_safe_doc_push_isolated_deletion_
# propagates.bats.
#
# Run: bats tests/test_safe_doc_push_unmerged_retry_resurrection_guard.bats

setup() {
  export PUSH_GOV_DISABLE=true
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  mkdir -p plans/active/issues plans/archive/issues
  printf 'status: open\nold content\n' > plans/active/issues/thing.md
  echo "sibling" > plans/active/issues/sibling.md
  git add -A
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  # Build a UD (unmerged, ours-deleted/theirs-modified) index entry directly: a real delete/modify
  # merge conflict is a faster, more deterministic way to reach the exact index shape the guard
  # must catch than re-driving the original autostash-pop failure end to end.
  git checkout -q -b theirs-edits-thing
  printf 'status: open\nold content\npeer touched this line\n' > plans/active/issues/thing.md
  git commit -q -am "theirs: edit thing.md"

  git checkout -q live-defi-rollout
  git rm -q plans/active/issues/thing.md
  git mv plans/active/issues/sibling.md plans/archive/issues/thing.md 2>/dev/null || true
  echo "archived content" > plans/archive/issues/thing.md
  git add plans/archive/issues/thing.md
  git commit -q -m "ours: delete thing.md (archival rename)"

  # Merge the two divergent branches -- a delete/modify conflict, deliberately left unresolved.
  run git merge -q theirs-edits-thing
  [ -f plans/active/issues/thing.md ]
  # Sanity: the conflicting merge really did leave an unmerged index entry before the guard is
  # exercised -- otherwise this test would pass for the wrong reason.
  [ -n "$(git ls-files -u)" ]

  # Fake `sleep` on PATH so any retry backoff (if the guard regresses) is instant, not slow.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
}

@test "a pre-existing unmerged path hard-stops immediately (exit 3), naming the path" {
  ENTRY_STATUS="$(git status --porcelain)"

  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=0 run bash "$SCRIPT" "docs(plans): archive thing.md" \
    --files "plans/active/issues/thing.md plans/archive/issues/thing.md"

  [ "$status" -eq 3 ]
  [[ "$output" == *"UNMERGED (conflicted) path"* ]]
  [[ "$output" == *"plans/active/issues/thing.md"* ]]

  # The pre-fix failure signature (6 attempts burned, misleading "safe to re-run" guidance) must
  # never appear -- proves the early guard actually engaged, not that some other path happened to
  # also return 3.
  [[ "$output" != *"attempt 2/6"* ]]
  [[ "$output" != *"byte-identical"* ]]
  [[ "$output" != *"Exhausted"* ]]
}

@test "the checkout is left untouched -- the guard never stages the resurrected content" {
  ENTRY_STATUS="$(git status --porcelain)"

  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=0 run bash "$SCRIPT" "docs(plans): archive thing.md" \
    --files "plans/active/issues/thing.md plans/archive/issues/thing.md"

  [ "$status" -eq 3 ]
  # Still unmerged, still exactly what it was before this script ever ran -- no git add, no
  # commit, no attempt to "resolve" it on the caller's behalf.
  [ -n "$(git ls-files -u)" ]
  [ "$(git status --porcelain)" = "$ENTRY_STATUS" ]

  # Ground truth: origin was never touched.
  run git -C "${WORK}/origin.git" cat-file -e "live-defi-rollout:plans/active/issues/thing.md"
  [ "$status" -eq 0 ]
}

@test "isolated mode also refuses on a pre-existing unmerged caller tree (guard runs before the copy loop)" {
  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=1 run bash "$SCRIPT" "docs(plans): archive thing.md" \
    --files "plans/active/issues/thing.md plans/archive/issues/thing.md"

  [ "$status" -eq 3 ]
  [[ "$output" == *"UNMERGED (conflicted) path"* ]]
  # Never reached the isolated-worktree setup at all.
  [[ "$output" != *"isolated-worktree mode"* ]]
}

@test "a clean checkout with no unmerged paths is unaffected by the guard" {
  git merge --abort 2>/dev/null || true
  # Reset to origin/live-defi-rollout, NOT the local live-defi-rollout branch tip: setup()'s
  # shared merge-conflict scaffolding leaves an "ours: delete thing.md (archival rename)" commit
  # on the local branch that was never pushed. Resetting to the LOCAL branch tip (the pre-fix
  # form of this line) left that commit sitting ahead of origin -- i.e. exactly the
  # "safe-doc-push_carries_unrelated_ahead_commits" shape safe_doc_push_carries_unrelated_ahead_commits_silently_2026_08_17.md's
  # new guard exists to catch, which is unrelated to what THIS test means by "clean" (no
  # unmerged paths). Reset to origin's ref for a checkout that is actually ahead=0.
  git reset -q --hard origin/live-defi-rollout
  [ -z "$(git ls-files -u)" ]
  mkdir -p plans/active/issues
  echo "new content" > plans/active/issues/fresh.md
  git add plans/active/issues/fresh.md

  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=0 run bash "$SCRIPT" "docs(plans): add fresh.md" \
    --files "plans/active/issues/fresh.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  [[ "$output" != *"UNMERGED (conflicted) path"* ]]
}
