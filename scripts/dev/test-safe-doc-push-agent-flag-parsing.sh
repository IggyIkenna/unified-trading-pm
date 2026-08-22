#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# test-safe-doc-push-agent-flag-parsing.sh -- regression test for
# safe_doc_push_unrecognized_flag_silently_becomes_branch_name_2026_08_18's fix:
# safe-doc-push.sh's argument parser (scripts/dev/safe-doc-push.sh) must (1) accept
# `--agent` as a no-op, matching the CLAUDE.md-documented convention shared with
# quickmerge.sh, and (2) reject any OTHER unrecognized flag (a token starting with
# `-`) with a clear usage error instead of silently adopting it as the target
# BRANCH, which previously corrupted every internal `git fetch/pull/push "$BRANCH"`
# call for the rest of the run.
#
# USAGE: bash scripts/dev/test-safe-doc-push-agent-flag-parsing.sh
# Exit 0 + "PASS" if both cases behave correctly; exit 1 + "FAIL" otherwise.

set -uo pipefail

SCRATCH_DIR="$(mktemp -d -t sdp-agent-flag-test-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"
F="scripts/plan-hygiene/.conctest/agent_flag_probe.md"
EXPECTED_CONTENT="agent-flag-parsing probe content"

git clone -q --bare "$REPO_ROOT" "$BARE"
git clone -q "$BARE" "$SCRATCH_DIR/worker"
(cd "$SCRATCH_DIR/worker" && git checkout -q live-defi-rollout)

FAILED=0

# --- Case 1: --agent must be accepted as a no-op and the commit must land on the
# real integration branch (live-defi-rollout), not a branch literally named "--agent".
(
  cd "$SCRATCH_DIR/worker" || exit 90
  mkdir -p "$(dirname "$F")"
  printf '%s\n' "$EXPECTED_CONTENT" > "$F"
  SDP_ISOLATED=0 bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" "test(agent-flag): probe" \
    --agent --files "$F" > "$SCRATCH_DIR/run1.log" 2>&1
)
RC1=$?
echo "=== Case 1 (--agent no-op): exit $RC1 ==="
cat "$SCRATCH_DIR/run1.log"

landed="$(git -C "$BARE" show "live-defi-rollout:$F" 2>/dev/null || true)"
if [ "$RC1" -eq 0 ] && [ "$landed" = "$EXPECTED_CONTENT" ]; then
  echo "Case 1 PASS -- --agent consumed as a no-op, commit landed on live-defi-rollout"
else
  echo "Case 1 FAIL -- exit=$RC1 landed=[$landed]"
  FAILED=1
fi

# --- Case 2: an unrecognized flag must produce a clear usage error (exit 2), never
# a silent BRANCH corruption that surfaces later as a confusing git-fetch failure.
OUT2="$(cd "$SCRATCH_DIR/worker" && SDP_ISOLATED=0 bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" \
  "test(agent-flag): probe2" --bogus-flag --files "$F" 2>&1)"
RC2=$?
echo "=== Case 2 (unrecognized flag): exit $RC2 ==="
echo "$OUT2"

if [ "$RC2" -eq 2 ] && echo "$OUT2" | grep -q "unrecognized flag"; then
  echo "Case 2 PASS -- unrecognized flag rejected with a usage error, not silently adopted as BRANCH"
else
  echo "Case 2 FAIL -- exit=$RC2, expected exit 2 with an 'unrecognized flag' message"
  FAILED=1
fi

echo
if [ "$FAILED" -eq 0 ]; then
  echo "PASS"
  exit 0
else
  echo "FAIL"
  exit 1
fi
