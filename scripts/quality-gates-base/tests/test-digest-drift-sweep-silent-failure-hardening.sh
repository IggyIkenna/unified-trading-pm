#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for digest-drift-sweep.yml's silent-failure hardening
# (issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md's remaining 3 of 4
# recommendations, plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md todo 3):
#   (2b) fetch HTTP status is captured and branched on: 404 = benign skip, 401/403 (or any other
#        unexpected status) = fail the step loudly instead of folding it into the benign skip.
#   (2c) the summary is self-auditing: Dispatched + Already fresh + Capped == 0 across a non-empty
#        IMAGE_REPOS list exits non-zero.
#   (3)  a --max-dispatches-equivalent cap bounds the fan-out per run.
#
# Like test-quickmerge-untracked-new-file-guard.sh, this EXTRACTS the REAL "Sweep stale repos and
# dispatch digest refresh" step's `run:` script from the live workflow (not a replica) and runs it
# in a subshell with a mocked `curl` function keyed by URL/repo, so a future edit that regresses any
# of the three behaviours fails here even if nobody re-reads the YAML by eye.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-digest-drift-sweep-silent-failure-hardening.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

HERE="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW="$(cd "$HERE/../../.." && pwd)/.github/workflows/digest-drift-sweep.yml"
[ -f "$WORKFLOW" ] || { echo "FATAL: digest-drift-sweep.yml not found at $WORKFLOW"; exit 2; }

# ── Extract the REAL "Sweep stale repos and dispatch digest refresh" step's run: script ──────────
SCRIPT_TEXT=$(python3 - "$WORKFLOW" <<'PYEOF'
import sys
import yaml

with open(sys.argv[1]) as f:
    doc = yaml.safe_load(f)

for step in doc["jobs"]["sweep"]["steps"]:
    if step.get("name") == "Sweep stale repos and dispatch digest refresh":
        sys.stdout.write(step["run"])
        break
else:
    sys.exit("step not found")
PYEOF
)
[ -n "$SCRIPT_TEXT" ] || { echo "FATAL: could not extract the sweep step's run: script"; exit 2; }

# Structural anchor: the extracted script must carry all three hardening elements, in order — so a
# future edit that removes/regresses any of them fails here even if the scenarios below don't.
case "$SCRIPT_TEXT" in
  *"HTTP_STATUS=\$(curl -s -o \"\$BODY_FILE\" -w '%{http_code}'"*"MAX_DISPATCHES"*"DISPATCHED + ALREADY_FRESH + CAPPED"*)
    pass "structural: extracted script carries the status-capturing fetch + MAX_DISPATCHES cap + self-audit assertion" ;;
  *)
    fail "structural: extracted script missing an expected hardening element"; echo "--- script ---"; echo "$SCRIPT_TEXT" ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# A minimal Dockerfile body carrying a stale ARG pin — served as the mocked 200 response body.
STALE_DOCKERFILE=$'FROM base\nARG BASE_IMAGE_DIGEST=sha256:b7e391f8b7e391f8b7e391f8b7e391f8b7e391f8b7e391f8b7e391f8b7e391f8\n'
FRESH_DIGEST="sha256:5122f7ab5122f7ab5122f7ab5122f7ab5122f7ab5122f7ab5122f7ab5122f7ab"
FRESH_DOCKERFILE="FROM base"$'\n'"ARG BASE_IMAGE_DIGEST=${FRESH_DIGEST}"$'\n'

# run_sweep MOCK_CURL_MODE — runs the extracted script in a subshell (its own `exit 1` only exits
# the subshell) with a `curl` bash function shadowing the real binary. The mock is a single
# dispatch table keyed on MOCK_CURL_MODE so each scenario below is fully isolated.
run_sweep() {
  local mode="$1"; shift
  (
    cd "$WORK" || exit 9
    GH_PAT="test-token"
    CURRENT_DIGEST="$FRESH_DIGEST"
    FORCE_ALL="${FORCE_ALL:-false}"
    MAX_DISPATCHES="${MAX_DISPATCHES:-5}"
    OWNER="TestOwner"
    MOCK_MODE="$mode"

    curl() {
      # Parse just enough of the real invocation to route the mock: is this the
      # contents-fetch GET or the dispatches POST, and which repo/branch.
      local url="" out="" is_post=false
      local args=("$@")
      local i=0
      while [ $i -lt ${#args[@]} ]; do
        case "${args[$i]}" in
          -o) out="${args[$((i+1))]}" ;;
          -X) [ "${args[$((i+1))]}" = "POST" ] && is_post=true ;;
          https://*) url="${args[$i]}" ;;
        esac
        i=$((i+1))
      done
      local repo; repo=$(echo "$url" | sed -E 's#.*/repos/[^/]+/([^/]+)/.*#\1#')

      if [ "$is_post" = "true" ]; then
        echo "204"
        return 0
      fi

      case "$MOCK_MODE" in
        all-fresh)
          echo "$FRESH_DOCKERFILE" > "$out"; echo "200" ;;
        stale-then-fresh)
          if [ "$repo" = "alerting-service" ]; then echo "$STALE_DOCKERFILE" > "$out"; else echo "$FRESH_DOCKERFILE" > "$out"; fi
          echo "200" ;;
        one-genuinely-absent)
          if [ "$repo" = "client-reporting-api" ]; then : > "$out"; echo "404";
          else echo "$FRESH_DOCKERFILE" > "$out"; echo "200"; fi ;;
        all-absent)
          : > "$out"; echo "404" ;;
        auth-failure-401)
          if [ "$repo" = "agent-orchestrator" ]; then echo '{"message":"Bad credentials"}' > "$out"; echo "401";
          else echo "$FRESH_DOCKERFILE" > "$out"; echo "200"; fi ;;
        auth-failure-403)
          if [ "$repo" = "agent-orchestrator" ]; then echo '{"message":"Forbidden"}' > "$out"; echo "403";
          else echo "$FRESH_DOCKERFILE" > "$out"; echo "200"; fi ;;
        all-stale-cap-test)
          echo "$STALE_DOCKERFILE" > "$out"; echo "200" ;;
        *)
          echo "500" ;;
      esac
    }

    eval "$SCRIPT_TEXT"
    echo "SUBSHELL_COMPLETED_EXIT_0"
  )
}

echo "── Case 1 (NEGATIVE TEST): one repo genuinely lacks a Dockerfile (404 on both branches) ──"
out1=$(run_sweep one-genuinely-absent 2>&1)
if printf '%s\n' "$out1" | grep -q "SUBSHELL_COMPLETED_EXIT_0" \
   && printf '%s\n' "$out1" | grep -qE "client-reporting-api: Dockerfile not found.*skipping"; then
  pass "case1: genuinely-absent Dockerfile is a benign skip, counted in SKIPPED_NO_ARG, run still exits 0"
else
  fail "case1: genuinely-absent Dockerfile did not skip benignly"; echo "--- output ---"; printf '%s\n' "$out1"
fi
if printf '%s\n' "$out1" | grep -qE "No ARG found:  *1$"; then
  pass "case1: SKIPPED_NO_ARG counter reflects exactly the one absent repo"
else
  fail "case1: SKIPPED_NO_ARG counter did not increment as expected"; echo "--- output ---"; printf '%s\n' "$out1"
fi

echo "── Case 2 (LOUD FAILURE — 401): an auth/permission failure must NOT be read as a benign skip ──"
out2=$(run_sweep auth-failure-401 2>&1)
if printf '%s\n' "$out2" | grep -q "SUBSHELL_COMPLETED_EXIT_0"; then
  fail "case2: script completed instead of failing loudly on HTTP 401"; echo "--- output ---"; printf '%s\n' "$out2"
elif printf '%s\n' "$out2" | grep -qE "HTTP 401 fetching Dockerfile.*auth/permission failure"; then
  pass "case2: HTTP 401 fails the step loudly with a diagnostic (not folded into 'Dockerfile not found')"
else
  fail "case2: unexpected output for HTTP 401 case"; echo "--- output ---"; printf '%s\n' "$out2"
fi

echo "── Case 3 (LOUD FAILURE — 403): same contract for 403 ──"
out3=$(run_sweep auth-failure-403 2>&1)
if printf '%s\n' "$out3" | grep -q "SUBSHELL_COMPLETED_EXIT_0"; then
  fail "case3: script completed instead of failing loudly on HTTP 403"; echo "--- output ---"; printf '%s\n' "$out3"
elif printf '%s\n' "$out3" | grep -qE "HTTP 403 fetching Dockerfile.*auth/permission failure"; then
  pass "case3: HTTP 403 fails the step loudly with a diagnostic"
else
  fail "case3: unexpected output for HTTP 403 case"; echo "--- output ---"; printf '%s\n' "$out3"
fi

echo "── Case 4 (DISPATCH CAP): 16 stale repos, MAX_DISPATCHES=3 — only 3 real dispatches fire ──"
out4=$(MAX_DISPATCHES=3 run_sweep all-stale-cap-test 2>&1)
dispatched4=$(printf '%s\n' "$out4" | grep -oE "Dispatched:    [0-9]+" | grep -oE "[0-9]+")
capped4=$(printf '%s\n' "$out4" | grep -oE "Capped \(deferred to next tick\): [0-9]+" | grep -oE "[0-9]+$")
if printf '%s\n' "$out4" | grep -q "SUBSHELL_COMPLETED_EXIT_0" && [ "$dispatched4" = "3" ] && [ "$capped4" = "13" ]; then
  pass "case4: dispatch cap bounds real dispatches to 3, defers the other 13 as CAPPED, exits 0"
else
  fail "case4: dispatch cap did not bound the fan-out as expected (dispatched=$dispatched4 capped=$capped4)"
  echo "--- output ---"; printf '%s\n' "$out4"
fi

echo "── Case 5 (SELF-AUDIT — negative): every repo genuinely absent — Dispatched+Fresh+Capped==0 must exit non-zero ──"
out5=$(run_sweep all-absent 2>&1)
if printf '%s\n' "$out5" | grep -q "SUBSHELL_COMPLETED_EXIT_0"; then
  fail "case5: all-absent sweep completed instead of tripping the self-audit assertion"; echo "--- output ---"; printf '%s\n' "$out5"
elif printf '%s\n' "$out5" | grep -qE "ERROR: Dispatched \+ Already fresh \+ Capped == 0"; then
  pass "case5: an all-empty sweep (nothing dispatched/fresh/capped) fails loudly via the self-audit assertion"
else
  fail "case5: unexpected output for the all-absent self-audit case"; echo "--- output ---"; printf '%s\n' "$out5"
fi

echo "── Case 6 (SELF-AUDIT — positive): a normal mixed run must NOT trip the assertion ──"
out6=$(run_sweep stale-then-fresh 2>&1)
if printf '%s\n' "$out6" | grep -q "SUBSHELL_COMPLETED_EXIT_0" && ! printf '%s\n' "$out6" | grep -q "ERROR: Dispatched"; then
  pass "case6: a normal run with real fresh/dispatched activity does not trip the self-audit assertion"
else
  fail "case6: a normal run incorrectly tripped the self-audit assertion or failed to complete"; echo "--- output ---"; printf '%s\n' "$out6"
fi

echo
echo "=== $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ]
