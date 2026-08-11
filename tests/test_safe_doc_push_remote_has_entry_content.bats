#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Unit test for _sdp_assert_remote_has_entry_content in scripts/dev/safe-doc-push.sh
# (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, P0: "Never report success on
# a no-op push ... verify against the remote ref, not HEAD"). The function + its two
# blob-lookup helpers are extracted from the script into a harness (the same pattern as
# test_safe_doc_push_failure_classification.bats), the harness runs against a real local
# origin/clone pair, and the caller drives the return code.
#
# THE GAP IT CLOSES: the "nothing to stage"/"nothing to commit" fallbacks previously reported
# "already landed" success whenever the branch moved for the named path (F8's exit 13 covers
# only "the branch did NOT move"). When this run's own reconcile parked the caller's edit in
# a stash while a DIFFERENT commit advanced the branch, the fallback exited 0 -- a false green
# for content that never reached the remote. The function verifies the caller's ENTRY content
# is genuinely at origin/$BRANCH; if not, it prints the quarantine/stash ref and returns 1
# (the caller exits 14).
#
# The identical-at-entry case (F8 exit 12) and the branch-did-not-move case (F8 exit 13) are
# deliberately NOT this function's job -- it returns 0 (defer) for both, and the two
# end-to-end tests in test_safe_doc_push_landed_content_certification.bats own those gates.
#
# Run: bats tests/test_safe_doc_push_remote_has_entry_content.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  HARNESS="${BATS_TEST_TMPDIR}/harness.sh"
  {
    grep -m1 '^_sdp_head_blob()' "$SCRIPT"
    grep -m1 '^_sdp_blob_of()' "$SCRIPT"
    awk '/^_sdp_assert_remote_has_entry_content\(\) \{/ {p=1} p {print} p && /^}/ {exit}' "$SCRIPT"
  } >"$HARNESS"
  cat >>"$HARNESS" <<'EOF'
FILES=(doc.md)
BRANCH=live-defi-rollout
_SDP_ENTRY_FINGERPRINT="${ENTRY_DISK}  doc.md"
_SDP_ENTRY_HEAD_BLOBS="${ENTRY_HEAD}  doc.md"
if _sdp_assert_remote_has_entry_content; then
  echo "REMOTE_OK"
else
  echo "REMOTE_MISSING"
fi
EOF

  # A real origin/clone pair so HEAD:<path> and origin/<branch>:<path> resolve truthfully.
  WORK="${BATS_TEST_TMPDIR}/repo"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/clone"
  cd "${WORK}/clone"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "base" > doc.md
  git add doc.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
}

run_check() {
  ENTRY_DISK="$1" ENTRY_HEAD="$2" bash "$HARNESS"
}

@test "branch converged to the caller's entry content (peer landed identical) -> REMOTE_OK" {
  # Local HEAD advances to the peer's commit; entry content == what origin now holds.
  echo "my genuine change" > doc.md
  git add doc.md
  git commit -q -m "peer: land identical"
  git push -q origin HEAD:live-defi-rollout

  entry_disk="$(printf 'my genuine change' | git hash-object --stdin)"
  entry_head="$(git rev-parse HEAD~1:doc.md 2>/dev/null || git rev-parse HEAD:doc.md)"

  run run_check "$entry_disk" "$entry_head"
  [ "$status" -eq 0 ]
  [[ "$output" == *"REMOTE_OK"* ]]
  [[ "$output" != *"REMOTE_MISSING"* ]]
}

@test "branch moved for the path but NOT to the caller's content -> REMOTE_MISSING (exit 14 class)" {
  # The quarantine-with-peer-move shape the P0 exists to catch: a DIFFERENT commit advanced
  # the branch, the caller's entry content is nowhere on origin -- the fallback must NOT
  # report success. The harness proves the function returns 1 (script exits 14); the
  # quarantine-ref message goes to stderr.
  echo "peer content v1" > doc.md
  git add doc.md
  git commit -q -m "peer: different change"
  git push -q origin HEAD:live-defi-rollout

  entry_disk="$(printf 'my genuine change' | git hash-object --stdin)"
  entry_head="$(printf 'base' | git hash-object --stdin)"

  run run_check "$entry_disk" "$entry_head"
  [ "$status" -eq 0 ]   # the harness itself must run cleanly
  [[ "$output" == *"REMOTE_MISSING"* ]]
  [[ "$output" != *"REMOTE_OK"* ]]
  [[ "$output" == *"NOTHING OF YOURS IS ON THE REMOTE"* ]]
  [[ "$output" == *"git stash show -p"* ]]
}

@test "no real diff at entry (identical to HEAD at entry) defers to exit 12 -> REMOTE_OK" {
  # No change since the committed base: this is F8's exit-12 ambiguity, not this function's
  # job. It must return 0 so the caller reaches _sdp_certify_success and exits 12 (or 0 under
  # SDP_ALLOW_NOOP=1).
  entry_disk="$(printf 'base' | git hash-object --stdin)"
  entry_head="$(printf 'base' | git hash-object --stdin)"

  run run_check "$entry_disk" "$entry_head"
  [ "$status" -eq 0 ]
  [[ "$output" == *"REMOTE_OK"* ]]
}

@test "branch did NOT move for the path defers to exit 13 -> REMOTE_OK" {
  # The caller had a real diff at entry, but HEAD:doc.md is unchanged from the pre-run HEAD:
  # F8's exit 13 owns that ("your change simply never landed"). The remote check must defer.
  entry_disk="$(printf 'my genuine change' | git hash-object --stdin)"
  entry_head="$(git rev-parse HEAD:doc.md 2>/dev/null || printf 'base' | git hash-object --stdin)"

  run run_check "$entry_disk" "$entry_head"
  [ "$status" -eq 0 ]
  [[ "$output" == *"REMOTE_OK"* ]]
}

@test "both fallback success paths in the script call the remote check and exit 14" {
  # Wiring gate (mirrors failure_classification's "script documents exit code 6" test): the
  # two fallbacks that may report "already landed" success must route through the check.
  grep -q "_sdp_assert_remote_has_entry_content || exit 14" "$SCRIPT"
  grep -q "14 the \"nothing to stage\"/\"nothing to commit\" fallback" "$SCRIPT"
}
