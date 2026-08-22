#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the `sit-gate/fleet-green` cancelled-run clobber fix
# (plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md todo 13a; source:
# plans/active/issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md
# "Distinct sub-finding").
#
# Bug: `.github/workflows/ldr-to-main-promote-fleet.yml` derives the `sit-gate/fleet-green`
# fleet-shared signal by `gh run list --workflow full-workspace-sit.yml` (ordered by run
# CREATION time, newest first) and picking `completed[0]` — but `status == "completed"` is
# ALSO true for `conclusion == "cancelled"`, so a run created after a real success but
# cancelled almost immediately could rank above it and get posted as `state=failure`,
# clobbering the real green result. Live-measured 2026-07-25: run 30158515857 reached
# conclusion=success at 12:50:49Z; run 30158518796 (created after it, cancelled) became
# completed[0] and posted state=failure at 12:51:02Z on the SAME commit.
#
# Like test-ldr-promote-provenance-rearm-gate.sh, this EXTRACTS the REAL SIT_FLEET_LINE
# python heredoc from the live workflow (not a replica) and feeds it synthetic `gh run list`
# JSON shaped exactly like the live incident, proving the fixed selection logic:
#   (1) skips a cancelled run that ranks first and picks the next real completed run instead
#       (the exact incident — must yield state=success, not failure)
#   (2) still reports failure for a genuinely-failed completed run (no false-positive from the
#       cancelled-filter swallowing real failures)
#   (3) fails closed when every completed run in the window is cancelled (no informative signal
#       at all is NOT the same as "success")
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-sit-fleet-green-cancelled-run-clobber.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

HERE="$(cd "$(dirname "$0")" && pwd)"
WF="$(cd "$HERE/../../.." && pwd)/.github/workflows/ldr-to-main-promote-fleet.yml"
[ -f "$WF" ] || { echo "FATAL: ldr-to-main-promote-fleet.yml not found at $WF"; exit 2; }

# ── Extract the REAL SIT_FLEET_LINE assignment block (heredoc + closing paren) ───────────────
# Raw-file extraction preserves the YAML's own structural indentation (10 spaces here), which the
# real GH Actions `run: |` block-scalar parser strips before executing (so the heredoc terminator
# lands at column 0 in the real run). Dedent by the block's own common leading whitespace so the
# extracted heredoc terminator (`PYEOF`) is recognised by bash exactly as GH Actions would render it
# — same technique this file's own case needs, not present in the simpler function-body extractions
# elsewhere (test-ldr-promote-provenance-rearm-gate.sh) because those don't contain a heredoc.
RAW_BLOCK=$(awk '
  /^[[:space:]]+SIT_FLEET_LINE=\$\(SIT_LAST_RUN_JSON=/ { c = 1 }
  c { print }
  c && /^[[:space:]]+\)$/ { exit }
' "$WF")
[ -n "$RAW_BLOCK" ] || { echo "FATAL: could not extract the SIT_FLEET_LINE block from $WF"; exit 2; }
BLOCK=$(printf '%s\n' "$RAW_BLOCK" | python3 -c "import sys, textwrap; sys.stdout.write(textwrap.dedent(sys.stdin.read()))")
[ -n "$BLOCK" ] || { echo "FATAL: dedent of extracted block produced empty output"; exit 2; }

# Structural anchor: the extracted block must carry the cancelled-run filter — a future edit
# that drops it must fail here even if the scenarios below somehow still pass by coincidence.
case "$BLOCK" in
  *'informative = [r for r in completed if r.get("conclusion") != "cancelled"]'*'r = informative[0]'*)
    pass "structural: SIT_FLEET_LINE block filters cancelled runs out of the informative set before selecting [0]" ;;
  *)
    fail "structural: SIT_FLEET_LINE block missing the cancelled-run filter"; echo "--- block ---"; echo "$BLOCK" ;;
esac

run_case() {
  local label="$1" json="$2"
  (
    SIT_LAST_RUN_JSON="$json"
    export SIT_LAST_RUN_JSON
    eval "$BLOCK"
    IFS=$'\t' read -r SIT_FLEET_STATE SIT_FLEET_DESC SIT_FLEET_URL <<< "$SIT_FLEET_LINE"
    echo "STATE=$SIT_FLEET_STATE"
    echo "DESC=$SIT_FLEET_DESC"
    echo "URL=$SIT_FLEET_URL"
  )
}

echo "── Case 1 (THE live-measured incident): a cancelled run ranks first (gh run list is creation-order,"
echo "   newest first) ahead of a real success — must select the success, not the cancelled run ──"
# gh run list returns newest-created first; the cancelled run (30158518796) was created AFTER the
# success run (30158515857) so it legitimately sorts first in the API response.
INCIDENT_JSON='[
  {"status": "completed", "conclusion": "cancelled", "createdAt": "2026-07-25T12:50:55Z", "url": "https://x/run/30158518796"},
  {"status": "completed", "conclusion": "success",   "createdAt": "2026-07-25T12:46:20Z", "url": "https://x/run/30158515857"}
]'
out1=$(run_case case1 "$INCIDENT_JSON")
if printf '%s\n' "$out1" | grep -q '^STATE=success$'; then
  pass "case1: fixed logic selects the real success run, not the newer cancelled one (incident fixed)"
else
  fail "case1: expected STATE=success, got:"; printf '%s\n' "$out1"
fi
if printf '%s\n' "$out1" | grep -q '30158515857'; then
  pass "case1: selected description/url points at the success run (30158515857), not the cancelled run"
else
  fail "case1: selected run does not reference the expected success run's identity"; printf '%s\n' "$out1"
fi

echo "── Case 2: a genuinely-failed completed run must still report failure (cancelled-filter must not"
echo "   swallow real failures) ──"
FAIL_JSON='[
  {"status": "completed", "conclusion": "failure", "createdAt": "2026-07-25T13:00:00Z", "url": "https://x/run/999"}
]'
out2=$(run_case case2 "$FAIL_JSON")
if printf '%s\n' "$out2" | grep -q '^STATE=failure$'; then
  pass "case2: a genuine failure is still reported as failure (no false-positive from the fix)"
else
  fail "case2: expected STATE=failure, got:"; printf '%s\n' "$out2"
fi

echo "── Case 3: every completed run in the window is cancelled — no informative signal at all must"
echo "   fail CLOSED (not be mistaken for success) ──"
ALL_CANCELLED_JSON='[
  {"status": "completed", "conclusion": "cancelled", "createdAt": "2026-07-25T13:05:00Z", "url": "https://x/run/1"},
  {"status": "completed", "conclusion": "cancelled", "createdAt": "2026-07-25T13:00:00Z", "url": "https://x/run/2"}
]'
out3=$(run_case case3 "$ALL_CANCELLED_JSON")
if printf '%s\n' "$out3" | grep -q '^STATE=failure$'; then
  pass "case3: all-cancelled window fails CLOSED (state=failure), never mistaken for success"
else
  fail "case3: expected STATE=failure (fail-closed), got:"; printf '%s\n' "$out3"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
