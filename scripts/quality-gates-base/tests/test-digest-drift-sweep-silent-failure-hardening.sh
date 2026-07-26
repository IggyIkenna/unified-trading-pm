#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for digest-drift-sweep.yml's silent-failure hardening
# (issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md
# § "Also fix the silent-failure class"; ci_satellite_ao_dispatch_batch1_2026_07_26.md todo 3).
#
# The workflow ran GREEN for ~110 runs / 27 days while never reaching a real Dockerfile: a
# cross-repo 404 (permission scope) and a genuine "no Dockerfile" 404 were indistinguishable
# because the HTTP status was discarded (`curl -sf ... || echo ""`). This test EXTRACTS the REAL
# bash blocks from the workflow's embedded `run:` script (not a replica — an edit that removes or
# weakens the fix fails here) and exercises them against a stubbed curl, proving all four states
# the fix must now distinguish:
#   (1) 404 on both branches           -> benign skip, SKIPPED_NO_ARG, no crash   (the doc's own
#                                          negative test — a repo genuinely without a Dockerfile
#                                          must stay a benign skip, not a false alarm)
#   (2) 401/403 on any attempt         -> step fails loudly (non-zero exit), never silently skipped
#   (3) 404 then 200 (LDR miss, main hit) -> content parsed, no error/skip counted
#   (4) unexpected status (e.g. 500)   -> counted as an error, never silently a benign skip
#   (5) dispatch cap reached           -> a STALE repo is deferred, not dispatched
#   (6) all-zero dispatched/fresh/cap  -> the self-audit assertion fails the step
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-digest-drift-sweep-silent-failure-hardening.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

WF="$(cd "$(dirname "$0")/../../.." && pwd)/.github/workflows/digest-drift-sweep.yml"
[ -f "$WF" ] || { echo "FATAL: digest-drift-sweep.yml not found at $WF"; exit 2; }

# ── Extract the REAL fetch-classification block: from `DOCKERFILE_CONTENT=""` through (but not
#    including) the next section's comment. Covers the inner BRANCH loop + the not-found handling. ──
FETCH_BLOCK=$(awk '
  /DOCKERFILE_CONTENT=""$/ { c = 1 }
  c && /# Extract pinned digest/ { exit }
  c { print }
' "$WF")
[ -n "$FETCH_BLOCK" ] || { echo "FATAL: could not extract the fetch-classification block"; exit 2; }
case "$FETCH_BLOCK" in
  *'http_code'*'404)'*'401 | 403)'*'exit 1'*)
    pass "structural: fetch block carries the http_code capture + 404 + 401/403-loud-exit branches" ;;
  *)
    fail "structural: fetch block missing an expected contract element"; echo "--- block ---"; echo "$FETCH_BLOCK" ;;
esac

# ── Extract the REAL dispatch-cap block ──────────────────────────────────────────────────────────
CAP_BLOCK=$(awk '
  /if \[ "\$DISPATCHED" -ge "\$MAX_DISPATCHES" \]; then/ { c = 1 }
  c { print }
  c && /^ *fi$/ { exit }
' "$WF")
[ -n "$CAP_BLOCK" ] || { echo "FATAL: could not extract the dispatch-cap block"; exit 2; }
case "$CAP_BLOCK" in
  *'DEFERRED_CAP'*)
    pass "structural: cap block increments DEFERRED_CAP" ;;
  *)
    fail "structural: cap block missing DEFERRED_CAP"; echo "--- block ---"; echo "$CAP_BLOCK" ;;
esac

# ── Extract the REAL self-audit assertion block ──────────────────────────────────────────────────
AUDIT_BLOCK=$(awk '
  /if \[ "\$\(\(DISPATCHED \+ ALREADY_FRESH \+ DEFERRED_CAP\)\)" -eq 0 \]/ { c = 1 }
  c { print }
  c && /^ *fi$/ { exit }
' "$WF")
[ -n "$AUDIT_BLOCK" ] || { echo "FATAL: could not extract the self-audit assertion block"; exit 2; }
case "$AUDIT_BLOCK" in
  *'exit 1'*)
    pass "structural: self-audit assertion block exits non-zero" ;;
  *)
    fail "structural: self-audit assertion block does not exit non-zero"; echo "--- block ---"; echo "$AUDIT_BLOCK" ;;
esac

VALID_DIGEST="sha256:$(printf 'a%.0s' $(seq 1 64))"

# Stubbed curl. Reads the scenario off $MOCK_MODE; mimics `curl -s -o FILE -w '%{http_code}' ... URL`
# by writing a fake body to the -o target and printing the status code to stdout, exactly as real
# curl does with -w after the transfer completes.
mock_curl() {
  local out_file="" url="" prev=""
  for a in "$@"; do
    if [ "$prev" = "-o" ]; then out_file="$a"; fi
    prev="$a"
  done
  url="${*: -1}"
  case "$MOCK_MODE" in
    all-404)
      [ -n "$out_file" ] && : > "$out_file"
      echo "404" ;;
    all-401)
      [ -n "$out_file" ] && printf '{"message":"Bad credentials"}' > "$out_file"
      echo "401" ;;
    all-403)
      [ -n "$out_file" ] && printf '{"message":"Forbidden"}' > "$out_file"
      echo "403" ;;
    ldr-404-main-200)
      if [[ "$url" == *"ref=live-defi-rollout"* ]]; then
        [ -n "$out_file" ] && : > "$out_file"
        echo "404"
      else
        [ -n "$out_file" ] && printf 'FROM x\nARG BASE_IMAGE_DIGEST=%s\n' "$VALID_DIGEST" > "$out_file"
        echo "200"
      fi ;;
    all-500)
      [ -n "$out_file" ] && printf 'internal error' > "$out_file"
      echo "500" ;;
    *)
      echo "000" ;;
  esac
}

echo "── Case 1 (doc's own negative test): repo genuinely without a Dockerfile — both branches 404 ──"
out1=$(bash -c '
  curl() { mock_curl "$@"; }
  '"$(declare -f mock_curl)"'
  RESP_BODY="$(mktemp)"; trap "rm -f \"$RESP_BODY\"" EXIT
  REPO="no-dockerfile-repo"; OWNER="x"; TOKEN="tok"; MOCK_MODE="all-404"; VALID_DIGEST="'"$VALID_DIGEST"'"
  SKIPPED_NO_ARG=0; ERRORS=0
  for _ in 1; do
  '"$FETCH_BLOCK"'
  done
  echo "AFTER_BLOCK content=[$DOCKERFILE_CONTENT] skipped=$SKIPPED_NO_ARG errors=$ERRORS"
' 2>&1)
if printf '%s\n' "$out1" | grep -q "AFTER_BLOCK content=\[\] skipped=1 errors=0"; then
  pass "case1: genuinely-absent Dockerfile is a benign skip (SKIPPED_NO_ARG=1), no crash — negative test preserved"
else
  fail "case1: genuinely-absent Dockerfile did not classify as a clean benign skip"; echo "--- output ---"; printf '%s\n' "$out1"
fi

echo "── Case 2: HTTP 401 on first attempt — must fail the step LOUDLY, not skip ──"
MOCK_MODE="all-401"
out2=$(bash -c '
  curl() { mock_curl "$@"; }
  '"$(declare -f mock_curl)"'
  RESP_BODY="$(mktemp)"; trap "rm -f \"$RESP_BODY\"" EXIT
  REPO="private-repo"; OWNER="x"; TOKEN="tok"; MOCK_MODE="all-401"; VALID_DIGEST="'"$VALID_DIGEST"'"
  SKIPPED_NO_ARG=0; ERRORS=0
  for _ in 1; do
  '"$FETCH_BLOCK"'
  done
  echo "AFTER_BLOCK — should never print"
' 2>&1)
rc2=$?
if [ "$rc2" -ne 0 ] && printf '%s\n' "$out2" | grep -q "::error::" && ! printf '%s\n' "$out2" | grep -q "AFTER_BLOCK"; then
  pass "case2: HTTP 401 fails the step loudly (exit $rc2) with an ::error:: line, never reaching past the fetch"
else
  fail "case2: HTTP 401 did not fail loudly as expected (rc=$rc2)"; echo "--- output ---"; printf '%s\n' "$out2"
fi

echo "── Case 3: HTTP 403 on first attempt — same loud-failure contract as 401 ──"
out3=$(bash -c '
  curl() { mock_curl "$@"; }
  '"$(declare -f mock_curl)"'
  RESP_BODY="$(mktemp)"; trap "rm -f \"$RESP_BODY\"" EXIT
  REPO="private-repo"; OWNER="x"; TOKEN="tok"; MOCK_MODE="all-403"; VALID_DIGEST="'"$VALID_DIGEST"'"
  SKIPPED_NO_ARG=0; ERRORS=0
  for _ in 1; do
  '"$FETCH_BLOCK"'
  done
  echo "AFTER_BLOCK — should never print"
' 2>&1)
rc3=$?
if [ "$rc3" -ne 0 ] && printf '%s\n' "$out3" | grep -q "::error::" && ! printf '%s\n' "$out3" | grep -q "AFTER_BLOCK"; then
  pass "case3: HTTP 403 fails the step loudly (exit $rc3) with an ::error:: line"
else
  fail "case3: HTTP 403 did not fail loudly as expected (rc=$rc3)"; echo "--- output ---"; printf '%s\n' "$out3"
fi

echo "── Case 4: LDR 404, main 200 — content parses, nothing counted as error/skip ──"
out4=$(bash -c '
  curl() { mock_curl "$@"; }
  '"$(declare -f mock_curl)"'
  RESP_BODY="$(mktemp)"; trap "rm -f \"$RESP_BODY\"" EXIT
  REPO="ok-repo"; OWNER="x"; TOKEN="tok"; MOCK_MODE="ldr-404-main-200"; VALID_DIGEST="'"$VALID_DIGEST"'"
  SKIPPED_NO_ARG=0; ERRORS=0
  for _ in 1; do
  '"$FETCH_BLOCK"'
  done
  echo "AFTER_BLOCK content=[$DOCKERFILE_CONTENT] skipped=$SKIPPED_NO_ARG errors=$ERRORS"
' 2>&1)
if printf '%s\n' "$out4" | grep -q "AFTER_BLOCK content=\[FROM x" && printf '%s\n' "$out4" | grep -q "skipped=0 errors=0"; then
  pass "case4: LDR-miss/main-hit fetches real content with zero skip/error miscounts"
else
  fail "case4: LDR-miss/main-hit fetch did not parse cleanly"; echo "--- output ---"; printf '%s\n' "$out4"
fi

echo "── Case 5: unexpected HTTP 500 on both branches — counted as an ERROR, never a silent benign skip ──"
out5=$(bash -c '
  curl() { mock_curl "$@"; }
  '"$(declare -f mock_curl)"'
  RESP_BODY="$(mktemp)"; trap "rm -f \"$RESP_BODY\"" EXIT
  REPO="flaky-repo"; OWNER="x"; TOKEN="tok"; MOCK_MODE="all-500"; VALID_DIGEST="'"$VALID_DIGEST"'"
  SKIPPED_NO_ARG=0; ERRORS=0
  for _ in 1; do
  '"$FETCH_BLOCK"'
  done
  echo "AFTER_BLOCK content=[$DOCKERFILE_CONTENT] skipped=$SKIPPED_NO_ARG errors=$ERRORS"
' 2>&1)
if printf '%s\n' "$out5" | grep -q "AFTER_BLOCK content=\[\] skipped=0 errors=1"; then
  pass "case5: unexpected HTTP 500 is tracked as ERRORS=1, not silently folded into SKIPPED_NO_ARG"
else
  fail "case5: unexpected HTTP 500 mis-tracked"; echo "--- output ---"; printf '%s\n' "$out5"
fi

echo "── Case 6: dispatch cap already reached — STALE repo is deferred, DISPATCHED unchanged ──"
out6=$(bash -c '
  DISPATCHED=3; MAX_DISPATCHES=3; DEFERRED_CAP=0
  REPO="capped-repo"; PINNED_DIGEST="sha256:old"; CURRENT_DIGEST="sha256:new"
  for _ in 1; do
    '"$CAP_BLOCK"'
  done
  echo "AFTER_BLOCK dispatched=$DISPATCHED deferred=$DEFERRED_CAP"
' 2>&1)
if printf '%s\n' "$out6" | grep -q "AFTER_BLOCK dispatched=3 deferred=1"; then
  pass "case6: dispatch cap reached correctly defers instead of dispatching"
else
  fail "case6: dispatch cap did not defer as expected"; echo "--- output ---"; printf '%s\n' "$out6"
fi

echo "── Case 7: self-audit assertion — all-zero dispatched/fresh/cap across a non-empty repo list must fail loudly ──"
out7=$(bash -c '
  DISPATCHED=0; ALREADY_FRESH=0; DEFERRED_CAP=0
  IMAGE_REPOS=(one two three)
  '"$AUDIT_BLOCK"'
  echo "AFTER_BLOCK — should never print"
' 2>&1)
rc7=$?
if [ "$rc7" -ne 0 ] && printf '%s\n' "$out7" | grep -q "::error::" && ! printf '%s\n' "$out7" | grep -q "AFTER_BLOCK"; then
  pass "case7: all-zero dispatched/fresh/cap-deferred fails the step loudly (exit $rc7) — the original 27-day bug is now caught"
else
  fail "case7: self-audit assertion did not fire on an all-zero sweep"; echo "--- output ---"; printf '%s\n' "$out7"
fi

echo "── Case 8: self-audit assertion — a healthy run (nonzero fresh/dispatched) must NOT fail ──"
out8=$(bash -c '
  DISPATCHED=2; ALREADY_FRESH=14; DEFERRED_CAP=0
  IMAGE_REPOS=(one two three)
  '"$AUDIT_BLOCK"'
  echo "AFTER_BLOCK — reached, run is healthy"
' 2>&1)
rc8=$?
if [ "$rc8" -eq 0 ] && printf '%s\n' "$out8" | grep -q "AFTER_BLOCK"; then
  pass "case8: a healthy sweep (nonzero dispatched+fresh) does not trip the self-audit assertion"
else
  fail "case8: self-audit assertion misfired on a healthy sweep (rc=$rc8)"; echo "--- output ---"; printf '%s\n' "$out8"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
