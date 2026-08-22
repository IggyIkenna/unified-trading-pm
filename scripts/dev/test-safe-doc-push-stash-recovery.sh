#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# test-safe-doc-push-stash-recovery.sh -- regression test for
# safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15's fix:
# `sdp_recover_named_from_any_stash` (scripts/dev/safe-doc-push.sh) must recover a caller-named
# --files path that is missing from BOTH disk and the index at staging time, by finding it in
# whichever stash entry still holds it.
#
# WHY THIS SHAPE, NOT A LIVE REPEAT OF THE ORIGINAL TRIGGER. The original incident's exact
# trigger (a quarantine cycle's `protected` string match missing a caller-named rename path under
# a 24-entry autostash pile, during a live rebase reconcile) is racy and host/timing-dependent --
# scripts/dev/repro-safe-doc-push-extreme-stash-rename-loss.sh exercises that end-to-end scenario
# but a clean (non-conflicting) divergence did not reproduce the loss deterministically, and a
# conflicting one correctly hard-stops instead of losing content (that path was already safe).
# This test instead directly forces the FAILURE CONDITION the fix targets -- a named file
# entirely absent from disk+index with its content sitting only in a stash -- and proves the
# safety net recovers it. This is the right level to pin: it is agnostic to WHICH upstream
# quarantine mechanism drops the content, and it is deterministic (no timing/concurrency needed).
#
# USAGE: bash scripts/dev/test-safe-doc-push-stash-recovery.sh
# Exit 0 + "PASS" if the named file lands with its correct content; exit 1 + "FAIL" otherwise.

set -uo pipefail

SCRATCH_DIR="$(mktemp -d -t sdp-stash-recovery-test-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"
F="scripts/plan-hygiene/.conctest/stash_recovery_probe.md"
EXPECTED_CONTENT="stash-recovery probe content -- must survive"

git clone -q --bare "$REPO_ROOT" "$BARE"
git clone -q "$BARE" "$SCRATCH_DIR/worker"
(cd "$SCRATCH_DIR/worker" && git checkout -q live-defi-rollout)

(
  cd "$SCRATCH_DIR/worker" || exit 90
  mkdir -p "$(dirname "$F")"
  printf '%s\n' "$EXPECTED_CONTENT" > "$F"
  git add "$F"

  # Simulate exactly the failure the incident observed: the caller's own --files content ends
  # up ONLY in a stash, absent from both disk and the index, as if a quarantine cycle's
  # `protected` check had missed it. `git stash push` here removes it from disk AND unstages
  # it from the index -- the precise "gone, not merely unstaged" state the issue reported.
  git stash push -m "safety-snapshot: simulated errant quarantine of $F" -- "$F" >/dev/null 2>&1

  if [ -e "$F" ] || git ls-files --error-unmatch -- "$F" >/dev/null 2>&1; then
    echo "TEST SETUP FAILED: $F should be absent from disk+index before the run" >&2
    exit 92
  fi
)
setup_rc=$?
if [ "$setup_rc" -ne 0 ]; then
  echo "FAIL (setup)"
  exit 1
fi

(
  cd "$SCRATCH_DIR/worker" || exit 93
  SDP_ISOLATED=0 bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" "test(stash-recovery): probe" \
    --files "$F" > "$SCRATCH_DIR/run.log" 2>&1
)
RC=$?

echo "=== safe-doc-push.sh exit code: $RC ==="
echo "=== log ==="
cat "$SCRATCH_DIR/run.log"

landed="$(cd "$SCRATCH_DIR/worker" && git -C "$BARE" show "live-defi-rollout:$F" 2>/dev/null)"
if [ "$landed" = "$EXPECTED_CONTENT" ]; then
  echo
  echo "PASS -- $F recovered from stash and landed with correct content"
  exit 0
else
  echo
  echo "FAIL -- expected [$EXPECTED_CONTENT], landed [$landed]"
  exit 1
fi
