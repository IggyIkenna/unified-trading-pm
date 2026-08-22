#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's entry-hash comparison (F4,
# pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10).
#
# THE BUG: twice on 2026-08-10, an exhausted-retries run (SCRIPT_EXIT=5, "this is transient,
# not a defect. Re-run.") left the caller's uncommitted edits to a TRACKED file reverted to
# HEAD content, with nothing in the exit path suggesting the tree was touched. The content was
# only recoverable by explicitly going and looking in the stash.
#
# THE FIX: `_sdp_fingerprint_named()` hashes every named file the moment the script starts
# (`_SDP_ENTRY_FINGERPRINT`); before printing the transient/exhausted message,
# `_sdp_warn_if_content_vanished()` re-hashes and compares. A mismatch means the caller's
# content is no longer on disk as handed over, so the script prints the stash-recovery
# instructions and the run exits 10 (distinct from plain exhausted-retries exit 5) instead of
# claiming "transient, just re-run" over a tree that already lost the edit.
#
# This test exercises the two pure functions directly (via a sed-extracted harness, the same
# pattern as test_safe_doc_push_failure_classification.bats) against a real git repo, rather
# than driving the full retry loop -- reproducing genuine prek/push contention is not needed to
# prove the comparison itself is correct.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$WORK"
  cd "$WORK"
  git init -q .
  git config user.email t@t
  git config user.name t
  printf 'original head content\n' >plan.md
  git add plan.md
  git commit -q -m seed

  # Harness, split in two so the test controls WHEN the entry fingerprint is captured
  # (before the simulated revert) versus when the comparison runs (after it) -- sourcing
  # both in one process would capture "entry" from the already-reverted disk state.
  FINGERPRINT="${BATS_TEST_TMPDIR}/fingerprint.sh"
  {
    echo 'FILES=(plan.md)'
    sed -n '/^_sdp_fingerprint_named() {/,/^}/p' "$SCRIPT"
    echo '_sdp_fingerprint_named'
  } >"$FINGERPRINT"

  COMPARE="${BATS_TEST_TMPDIR}/compare.sh"
  {
    echo 'FILES=(plan.md)'
    sed -n '/^_sdp_fingerprint_named() {/,/^}/p' "$SCRIPT"
    sed -n '/^_sdp_blob_of() {/p' "$SCRIPT"
    sed -n '/^_sdp_warn_if_content_vanished() {/,/^}/p' "$SCRIPT"
    echo '_sdp_warn_if_content_vanished; echo "RC=$?"'
  } >"$COMPARE"
}

@test "unchanged named file: comparison passes (rc=0, no warning)" {
  cd "$WORK"
  printf 'my uncommitted edit\n' >plan.md
  entry_fp="$(bash "$FINGERPRINT")"

  run env _SDP_ENTRY_FINGERPRINT="$entry_fp" bash "$COMPARE"
  [ "$status" -eq 0 ]
  [[ "$output" == *"RC=0"* ]]
  [[ "$output" != *"YOUR EDITS ARE NO LONGER ON DISK"* ]]
}

@test "named file reverted to HEAD mid-run: comparison fails loudly and names the recovery ref" {
  cd "$WORK"
  printf 'my uncommitted edit\n' >plan.md
  entry_fp="$(bash "$FINGERPRINT")"

  # Simulate an autostash-pop race reverting the tracked file back to HEAD content AFTER the
  # entry fingerprint was captured -- exactly the F4 sequence.
  git stash push -q -m "safety-snapshot: pre-reconcile quarantine" -- plan.md
  printf 'original head content\n' >plan.md

  run env _SDP_ENTRY_FINGERPRINT="$entry_fp" bash "$COMPARE"
  [ "$status" -eq 0 ] # the harness itself always exits 0; RC= line carries the real result
  [[ "$output" == *"RC=1"* ]]
  [[ "$output" == *"YOUR EDITS ARE NO LONGER ON DISK"* ]]
  [[ "$output" == *"parked in a stash entry"* ]]
  [[ "$output" == *"git show 'stash@{0}:<path>'"* ]]
}

@test "named file deleted mid-run: comparison fails (ABSENT is not the entry blob)" {
  cd "$WORK"
  printf 'my uncommitted edit\n' >plan.md
  entry_fp="$(bash "$FINGERPRINT")"

  git stash push -q -- plan.md
  # plan.md is now ABSENT on disk (stash removed it, and stash didn't restore HEAD's copy).

  run env _SDP_ENTRY_FINGERPRINT="$entry_fp" bash "$COMPARE"
  [[ "$output" == *"RC=1"* ]]
  [[ "$output" == *"YOUR EDITS ARE NO LONGER ON DISK"* ]]
}
