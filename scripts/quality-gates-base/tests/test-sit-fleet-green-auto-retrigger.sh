#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for the `sit-gate/fleet-green` auto-retrigger fix
# (plans/active/issues/sit_gate_fleet_green_auto_retrigger_stuck_2026_07_27.md).
#
# Bug: `.github/workflows/ldr-to-main-promote-fleet.yml` computed the fleet-shared
# `sit-gate/fleet-green` signal each tick and POSTED it as a commit status, but had NO
# code path that reacted to a RED/stale reading by re-driving `full-workspace-sit`. The
# ONLY existing `full-workspace-sit` repository_dispatch in the file (inside
# `process_repo`) fires for a SIT-covered repo's own unvalidated BREAKING/unknown delta —
# a condition entirely independent of the fleet-green signal's state. A transient
# `full-workspace-sit` failure with no repo currently carrying a pending BREAKING delta
# therefore left the gate stuck RED for hours across multiple promoter ticks with zero new
# SIT runs (confirmed live 2026-07-27 and again 2026-07-28).
#
# Fix: `sit_fleet_green_auto_retrigger()` dispatches a fresh `full-workspace-sit` run
# whenever `SIT_FLEET_STATE=failure`, debounced by skipping the dispatch when a
# full-workspace-sit run is already queued/in_progress.
#
# Like test-ldr-promote-provenance-rearm-gate.sh, this EXTRACTS the REAL
# `sit_fleet_green_auto_retrigger()` function body from the live workflow (not a replica)
# and:
#   (a) structurally asserts it is both DEFINED and CALLED in the file (a future edit that
#       defines it but forgets to invoke it — or vice versa — must fail here);
#   (b) functionally runs the extracted function with a stubbed `curl`, proving:
#       (1) SIT_FLEET_STATE=success never dispatches;
#       (2) SIT_FLEET_STATE=failure + no in-flight run DOES dispatch (the fix);
#       (3) SIT_FLEET_STATE=failure + an in-flight (queued/in_progress) run does NOT
#           dispatch again (the debounce);
#       (4) DRY_RUN=true never actually calls curl, even when RED with nothing in flight.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-sit-fleet-green-auto-retrigger.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

HERE="$(cd "$(dirname "$0")" && pwd)"
WF="$(cd "$HERE/../../.." && pwd)/.github/workflows/ldr-to-main-promote-fleet.yml"
[ -f "$WF" ] || { echo "FATAL: ldr-to-main-promote-fleet.yml not found at $WF"; exit 2; }

# ── Extract the REAL sit_fleet_green_auto_retrigger() function body ──────────────────
# Raw-file extraction preserves the YAML's own structural indentation (10 spaces here),
# which the real GH Actions `run: |` block-scalar parser strips before executing — so the
# embedded `python3 -c '...'` body inside the function would land at column 0 at runtime
# but keeps its literal 10-space prefix here (an IndentationError waiting to happen if not
# dedented). Same technique as test-sit-fleet-green-cancelled-run-clobber.sh.
RAW_FUNC=$(awk '
  /^[[:space:]]+sit_fleet_green_auto_retrigger\(\) \{$/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+\}$/ { exit }
' "$WF")
[ -n "$RAW_FUNC" ] || { echo "FATAL: could not extract sit_fleet_green_auto_retrigger() from $WF"; exit 2; }
FUNC=$(printf '%s\n' "$RAW_FUNC" | python3 -c "import sys, textwrap; sys.stdout.write(textwrap.dedent(sys.stdin.read()))")
[ -n "$FUNC" ] || { echo "FATAL: dedent of extracted function produced empty output"; exit 2; }

# Structural anchor #1: the function carries the load-bearing contract elements.
case "$FUNC" in
  *'"$SIT_FLEET_STATE" != "failure"'*'status") != "completed"'*'"${SIT_INFLIGHT:-0}" != "0"'*'system-integration-tests/dispatches'*'full-workspace-sit'*)
    pass "structural: sit_fleet_green_auto_retrigger() carries the red-check + in-flight-debounce + dispatch-call contract" ;;
  *)
    fail "structural: sit_fleet_green_auto_retrigger() missing an expected contract element"; echo "--- function ---"; echo "$FUNC" ;;
esac

# Structural anchor #2 (THE regression guard): the function must be both DEFINED and
# actually CALLED (a future edit could define it and forget the invocation, leaving the
# fix dead code that still passes anchor #1).
CALL_COUNT=$(grep -c '^\s*sit_fleet_green_auto_retrigger\s*$' "$WF" || true)
if [ "${CALL_COUNT:-0}" -ge 1 ]; then
  pass "structural: sit_fleet_green_auto_retrigger is invoked (not just defined) — ${CALL_COUNT} call site(s)"
else
  fail "structural (THE dead-code guard): sit_fleet_green_auto_retrigger is defined but never called"
fi

# ── Functional harness: run the extracted function for real, network-free ────────────
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

run_case() {
  local label="$1" state="$2" inflight_json="$3" dry_run="$4"
  local curl_log="$WORK/curl_${label}.log"
  rm -f "$curl_log"
  (
    STUBBIN="$WORK/stubbin_$label"
    mkdir -p "$STUBBIN"
    # `curl` stub: record that a dispatch was attempted; never touch the network.
    cat > "$STUBBIN/curl" <<EOF
#!/usr/bin/env bash
echo "CALLED \$*" >> "$curl_log"
exit 0
EOF
    chmod +x "$STUBBIN/curl"
    PATH="$STUBBIN:$PATH"
    export PATH
    SIT_FLEET_STATE="$state"
    SIT_LAST_RUN_JSON="$inflight_json"
    DRY_RUN="$dry_run"
    GH_TOKEN="dummy-token-not-real"
    OWNER="TestOwner"
    export SIT_FLEET_STATE SIT_LAST_RUN_JSON DRY_RUN GH_TOKEN OWNER
    eval "$FUNC"
    sit_fleet_green_auto_retrigger >/dev/null 2>&1
  )
  if [ -s "$curl_log" ]; then
    echo "DISPATCHED"
  else
    echo "NOT_DISPATCHED"
  fi
}

echo "── Case 1: SIT_FLEET_STATE=success — must NOT dispatch (nothing to self-heal) ──"
out1=$(run_case case1 "success" '[]' "false")
if [ "$out1" = "NOT_DISPATCHED" ]; then
  pass "case1: green signal never triggers a dispatch"
else
  fail "case1: expected NOT_DISPATCHED, got $out1"
fi

echo "── Case 2 (THE fix): SIT_FLEET_STATE=failure + no in-flight run — MUST dispatch ──"
out2=$(run_case case2 "failure" '[{"status":"completed","conclusion":"failure"}]' "false")
if [ "$out2" = "DISPATCHED" ]; then
  pass "case2: red signal with nothing in flight dispatches a fresh full-workspace-sit run (the fix)"
else
  fail "case2: expected DISPATCHED, got $out2"
fi

echo "── Case 3 (THE debounce): SIT_FLEET_STATE=failure + an in_progress run — must NOT pile on another dispatch ──"
out3=$(run_case case3 "failure" '[{"status":"in_progress","conclusion":null},{"status":"completed","conclusion":"failure"}]' "false")
if [ "$out3" = "NOT_DISPATCHED" ]; then
  pass "case3: an in-flight run debounces a duplicate dispatch"
else
  fail "case3: expected NOT_DISPATCHED (debounced), got $out3"
fi

echo "── Case 4: SIT_FLEET_STATE=failure + nothing in flight + DRY_RUN=true — must NOT actually call curl ──"
out4=$(run_case case4 "failure" '[{"status":"completed","conclusion":"failure"}]' "true")
if [ "$out4" = "NOT_DISPATCHED" ]; then
  pass "case4: dry-run reports what it would do without calling curl"
else
  fail "case4: expected NOT_DISPATCHED (dry-run), got $out4"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
