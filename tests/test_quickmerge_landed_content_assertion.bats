#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_quickmerge_landed_content_assertion.bats -- the post-push "did YOUR change actually land"
# gate in scripts/quickmerge.sh (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10,
# finding F8).
#
# THE BUG: quickmerge verified that A COMMIT reached the branch (post-push ancestry gate) and
# called that SHIPPED. It never checked that the commit carried the caller's --files. Measured
# 2026-08-10, twice: a comment edit staged and passing was dropped by the reconcile and the run
# reported success pushing the OTHER named files; and a scoped run pushed a commit containing
# NEITHER named file (only a peer's untracked test file) while both stayed dirty on disk. Both
# passed ancestry verification and exited 0. The second shape is invisible to revert-detection
# by construction -- nothing on disk changed, the file simply never got committed -- and
# quickmerge's own `_qm_content_vanished` was DEAD CODE with no call site at all.
#
# THE FIX: record HEAD's blob for each --files path AT ENTRY. After the push, any path that had
# a real diff at entry whose HEAD blob is STILL the entry one carries none of your work => exit
# 10 (the fleet-wide "recover before re-running" code), never a SHIPPED line.
#
# The assertion is deliberately "moved off the PRE-RUN HEAD blob", not "equals your entry blob":
# the prek hook chain rewrites files legitimately (prosewrap/prettier), so a landed change
# routinely differs from what the caller handed over. Test 3 pins that distinction.
#
# Like test_quickmerge_unstage_foreign_paths.bats this EXTRACTS the real functions from
# quickmerge.sh and evals them rather than replicating the logic, so the test cannot drift from
# the shipped implementation. Hermetic: a real local git repo under BATS_TEST_TMPDIR (bats
# auto-cleans it, so no teardown removal is needed), no network.
#
# Run: bats tests/test_quickmerge_landed_content_assertion.bats

setup() {
  QM_SH="${BATS_TEST_DIRNAME}/../scripts/quickmerge.sh"
  REPO="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$REPO"
  cd "$REPO" || return 1
  git init -q .
  git config user.email t@t.t && git config user.name t

  # Load the REAL functions under test. The two blob helpers are one-liners (no `^}` line of
  # their own), so they are extracted by exact line rather than by range.
  eval "$(sed -n '/^_qm_head_blob() {/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_blob_of() {/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_content_vanished() {/,/^}/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_assert_entry_change_landed() {/,/^}/p' "$QM_SH")"

  REPO_NAME=testrepo
  _QM_PUSHED_SHA=deadbeefdeadbeef
}

# fingerprint_now -- rebuild both entry fingerprints from the CURRENT state, in exactly the
# format quickmerge builds them at entry. Call this at the point the real script would start.
snapshot_entry() {
  _QM_ENTRY_FINGERPRINT=""
  _QM_ENTRY_HEAD_BLOBS=""
  for f in $FILES_ARG; do
    if [ -f "$f" ]; then
      _QM_ENTRY_FINGERPRINT="${_QM_ENTRY_FINGERPRINT}$(git hash-object -- "$f")  ${f}
"
    else
      _QM_ENTRY_FINGERPRINT="${_QM_ENTRY_FINGERPRINT}ABSENT  ${f}
"
    fi
    _QM_ENTRY_HEAD_BLOBS="${_QM_ENTRY_HEAD_BLOBS}$(_qm_head_blob "$f")  ${f}
"
  done
}

@test "a change that genuinely landed passes the assertion" {
  echo base > doc.md && git add doc.md && git commit -qm init
  echo mine > doc.md
  FILES_ARG="doc.md"
  snapshot_entry

  git add doc.md && git commit -qm "ship it"

  run _qm_assert_entry_change_landed
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "a named file DROPPED from the commit fails, even with the worktree untouched" {
  # The measured shape the old revert-detection was structurally blind to: nothing on disk
  # changed, the file simply never got committed. HEAD's blob for it is still the pre-run one.
  echo base > doc.md && echo other > other.md
  git add doc.md other.md && git commit -qm init
  echo mine > doc.md && echo theirs > other.md
  FILES_ARG="doc.md other.md"
  snapshot_entry

  # Only other.md makes it into the commit -- doc.md stays dirty on disk, exactly as measured.
  git add other.md && git commit -qm "peer's commit swallowed the index"

  run _qm_assert_entry_change_landed
  [ "$status" -eq 1 ]
  [[ "$output" == *"THE PUSH LANDED BUT YOUR CHANGE DID NOT"* ]]
  [[ "$output" == *"doc.md"* ]]
  # It must name the DROPPED path only -- other.md genuinely landed.
  [[ "$output" != *"     other.md"* ]]
  # Disk is intact, so it must route to the re-run-is-safe branch, not the recover-first one.
  [[ "$output" == *"DROPPED-FROM-THE-COMMIT shape"* ]]
  [[ "$output" == *"Do NOT cite"* ]]
}

@test "a hook that reformats the file on the way in is NOT a false positive" {
  # prosewrap/prettier legitimately rewrite named files during the commit, so what lands is
  # neither the pre-run HEAD blob nor the caller's entry blob. That must still pass.
  echo base > doc.md && git add doc.md && git commit -qm init
  echo mine > doc.md
  FILES_ARG="doc.md"
  snapshot_entry

  echo "mine (reformatted by a hook)" > doc.md
  git add doc.md && git commit -qm "ship it, reformatted"

  run _qm_assert_entry_change_landed
  [ "$status" -eq 0 ]
}

@test "a named file that had nothing to ship is not asserted on" {
  # Naming an already-committed file alongside real work is routine; it must not fail the run.
  echo base > doc.md && git add doc.md && git commit -qm init
  FILES_ARG="doc.md"
  snapshot_entry

  run _qm_assert_entry_change_landed
  [ "$status" -eq 0 ]
}

@test "a staged deletion is not asserted on (absent at entry is not expressible as a blob move)" {
  echo base > doc.md && git add doc.md && git commit -qm init
  rm doc.md
  FILES_ARG="doc.md"
  snapshot_entry

  git rm -q --cached doc.md && git commit -qm "remove doc.md"

  run _qm_assert_entry_change_landed
  [ "$status" -eq 0 ]
}

@test "unscoped mode (no --files) is left completely alone" {
  echo base > doc.md && git add doc.md && git commit -qm init
  FILES_ARG=""
  _QM_ENTRY_FINGERPRINT=""
  _QM_ENTRY_HEAD_BLOBS=""

  run _qm_assert_entry_change_landed
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}

@test "a change reverted on disk AND absent from HEAD routes to the recover-first branch" {
  echo base > doc.md && git add doc.md && git commit -qm init
  echo mine > doc.md
  FILES_ARG="doc.md"
  snapshot_entry

  # The reconcile/prek race: the edit is undone on disk and never committed.
  echo base > doc.md
  git commit -q --allow-empty -m "someone else's commit"

  run _qm_assert_entry_change_landed
  [ "$status" -eq 1 ]
  [[ "$output" == *"THE PUSH LANDED BUT YOUR CHANGE DID NOT"* ]]
  # _qm_content_vanished is the classifier -- this is the branch that proves it is WIRED IN and
  # no longer the dead code it was when the losses it was written for happened.
  [[ "$output" == *"YOUR NAMED FILE(S) CHANGED CONTENT DURING THIS QUICKMERGE RUN"* ]]
  [[ "$output" == *"recover from the stash"* ]]
}
