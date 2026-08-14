#!/usr/bin/env bash
# Epic: infrastructure_master (ci_satellite_ao_dispatch_batch13_2026_08_13)
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for hoisting the superseded-promote-PR cleanup ABOVE the SIT gate in
# scripts/cicd/ldr_to_main_fleet_promote.sh
# (plans/active/issues/sit_gate_treadmill_recurs_under_high_ldr_velocity_2026_08_08.md, todo 3).
#
# Bug: the ORIGINAL superseded-ref cleanup only ran after STEP 1's ref-freeze, ~200 lines past
# every SIT-gate `_done BLOCKED; return 0` in process_repo() -- so while the gate blocks (exactly
# when LDR is racing ahead and old promote refs go stale), the cleanup was unreachable. An
# orphaned, permanently-red promote PR (its head an immutable per-SHA ref that can never receive
# a fix landing on a later commit) then survived indefinitely and paged the lag monitor
# (confirmed live: PR #939, closed by hand 2026-08-10 because the bot itself could never reach the
# code that would have closed it).
#
# Fix (2026-08-14): a new `_close_ancestor_failed_promote_prs()` function runs immediately after
# $LDR_SHA/$PROMOTE_HEAD are computed -- before the content-identical skip and before the SIT
# differ/gate section, both of which can return/block first. Design constraint (do NOT loosen,
# per the source issue doc): it must not mass-close. A stale-headed PR is closed ONLY when BOTH
# (a) its head SHA is a STRICT ANCESTOR of the current LDR tip (compare-API verified, not inferred
# from ref-name mismatch alone -- an empty $LDR_SHA would otherwise make every open promote PR
# look superseded) and (b) quality-gates-v2 has already CONCLUDED failure on that exact head SHA
# (not pending/in-progress).
#
# Like test-ldr-promote-provenance-rearm-gate.sh / test-ldr-promote-arm-failed-tally.sh, this
# EXTRACTS the REAL `_close_ancestor_failed_promote_prs()` function body (not a replica) and:
#   (a) structurally asserts it is defined AND invoked strictly BEFORE both the content-identical
#       skip and the covered-repo SIT-gate block (the actual hoist, not just a function that
#       exists) -- and that the design constraint's empty-LDR_SHA guard is present verbatim;
#   (b) functionally runs the extracted function with a stubbed `gh`, proving: an ancestor PR with
#       quality-gates-v2 CONCLUDED failure is closed + its ref deleted (the fix); a non-ancestor PR
#       is left alone; an ancestor PR whose check has NOT concluded failure is left alone; an empty
#       $LDR_SHA short-circuits to a total no-op; DRY_RUN=true computes the same verdict but never
#       calls `gh pr close`/`gh api -X DELETE`.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-ldr-promote-ancestor-cleanup-hoist.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
PROMOTE_SCRIPT="$REPO_ROOT/scripts/cicd/ldr_to_main_fleet_promote.sh"
[ -f "$PROMOTE_SCRIPT" ] || { echo "FATAL: ldr_to_main_fleet_promote.sh not found at $PROMOTE_SCRIPT"; exit 2; }

echo "── Structural: the hoist is real (call site precedes both early-return paths) ──"

DEF_LINE=$(grep -n '^_close_ancestor_failed_promote_prs() {$' "$PROMOTE_SCRIPT" | head -1 | cut -d: -f1)
CALL_LINE=$(grep -n '^  _close_ancestor_failed_promote_prs$' "$PROMOTE_SCRIPT" | head -1 | cut -d: -f1)
PROMOTE_HEAD_LINE=$(grep -n 'PROMOTE_HEAD="promote/\$REPO/\${LDR_SHA:0:12}"' "$PROMOTE_SCRIPT" | head -1 | cut -d: -f1)
SKIP_LINE=$(grep -n 'SKIP \$REPO: main tree == LDR tree' "$PROMOTE_SCRIPT" | head -1 | cut -d: -f1)
SIT_BLOCK_LINE=$(grep -n 'not SIT-validated on this tree' "$PROMOTE_SCRIPT" | head -1 | cut -d: -f1)

if [ -n "$DEF_LINE" ] && [ -n "$CALL_LINE" ]; then
  pass "structural: _close_ancestor_failed_promote_prs() is both defined (L${DEF_LINE}) and invoked (L${CALL_LINE})"
else
  fail "structural: _close_ancestor_failed_promote_prs() must be both defined and invoked (def=${DEF_LINE:-missing}, call=${CALL_LINE:-missing})"
fi

if [ -n "$CALL_LINE" ] && [ -n "$PROMOTE_HEAD_LINE" ] && [ "$CALL_LINE" -gt "$PROMOTE_HEAD_LINE" ]; then
  pass "structural: call site (L${CALL_LINE}) is AFTER \$PROMOTE_HEAD is computed (L${PROMOTE_HEAD_LINE}) — LDR_SHA is available"
else
  fail "structural: call site must be after \$PROMOTE_HEAD is computed (call=${CALL_LINE:-missing}, promote_head=${PROMOTE_HEAD_LINE:-missing})"
fi

if [ -n "$CALL_LINE" ] && [ -n "$SKIP_LINE" ] && [ "$CALL_LINE" -lt "$SKIP_LINE" ]; then
  pass "structural (THE hoist, part 1): call site (L${CALL_LINE}) precedes the content-identical skip return (L${SKIP_LINE})"
else
  fail "structural (THE hoist, part 1): call site must precede the content-identical skip return (call=${CALL_LINE:-missing}, skip=${SKIP_LINE:-missing})"
fi

if [ -n "$CALL_LINE" ] && [ -n "$SIT_BLOCK_LINE" ] && [ "$CALL_LINE" -lt "$SIT_BLOCK_LINE" ]; then
  pass "structural (THE hoist, part 2 — the actual regression this closes): call site (L${CALL_LINE}) precedes the covered-repo SIT-gate BLOCK (L${SIT_BLOCK_LINE})"
else
  fail "structural (THE hoist, part 2): call site must precede the covered-repo SIT-gate BLOCK (call=${CALL_LINE:-missing}, sit_block=${SIT_BLOCK_LINE:-missing})"
fi

# ── Extract the REAL _close_ancestor_failed_promote_prs() function body ──────────────
FUNC=$(awk '
  /^_close_ancestor_failed_promote_prs\(\) \{$/ { c = 1 }
  c { print }
  c && $0 ~ /^\}$/ { exit }
' "$PROMOTE_SCRIPT")
[ -n "$FUNC" ] || { echo "FATAL: could not extract _close_ancestor_failed_promote_prs() from $PROMOTE_SCRIPT"; exit 2; }

case "$FUNC" in
  *'-z "$LDR_SHA"'*'compare/'*'"ahead"'*'quality-gates-v2.yml'*'conclusion==\"failure\"'*'gh pr close'*'-X DELETE'*)
    pass "structural: function carries the empty-LDR_SHA guard + strict-ancestor compare + concluded-failure check + close/delete contract" ;;
  *)
    fail "structural: function missing an expected design-constraint element"; echo "--- function ---"; echo "$FUNC" ;;
esac

# ── Functional harness: run the extracted function for real, network-free ────────────
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

run_case() {
  local label="$1" ldr_sha="$2" heads="$3" pr_json="$4" cmp_status="$5" v2_failed_count="$6" dry_run="$7"
  local log="$WORK/log_${label}.txt"
  rm -f "$log"
  (
    STUBBIN="$WORK/stubbin_$label"
    mkdir -p "$STUBBIN"
    cat > "$STUBBIN/gh" <<EOF
#!/usr/bin/env bash
LOG="$log"
case "\$*" in
  *"-X DELETE"*"refs/heads/"*)
    echo "DELETE \$*" >> "\$LOG" ;;
  *"pr close "*)
    echo "CLOSE \$*" >> "\$LOG" ;;
  *"--json headRefName --jq"*)
    printf '%s\n' "$heads" ;;
  *"--head "*"--json number,headRefOid"*)
    printf '%s' '$pr_json' ;;
  *"--workflow quality-gates-v2.yml"*)
    printf '%s' "$v2_failed_count" ;;
  *"/compare/"*)
    printf '%s' "$cmp_status" ;;
  *)
    echo "gh stub ($label): unexpected invocation: \$*" >&2; exit 1 ;;
esac
EOF
    chmod +x "$STUBBIN/gh"
    PATH="$STUBBIN:$PATH"
    export PATH
    REPO="test-repo"; OWNER="TestOwner"; LDR_SHA="$ldr_sha"
    PROMOTE_HEAD="promote/test-repo/${ldr_sha:0:12}"
    DRY_RUN="$dry_run"; GH_TOKEN="dummy-token-not-real"; GH_PAT_FOR_ARM="dummy-pat-not-real"
    export REPO OWNER LDR_SHA PROMOTE_HEAD DRY_RUN GH_TOKEN GH_PAT_FOR_ARM
    eval "$FUNC"
    _close_ancestor_failed_promote_prs >/dev/null 2>&1
  )
  if [ -s "$log" ]; then
    grep -q '^CLOSE ' "$log" && grep -q '^DELETE ' "$log" && echo "CLOSED_AND_DELETED" && return
    echo "PARTIAL:$(tr '\n' ';' < "$log")"
  else
    echo "UNTOUCHED"
  fi
}

STALE_HEAD="promote/test-repo/oldsha000001"
PR_JSON_OK='[{"number": 42, "headRefOid": "oldsha0000011111111111111111111111111"}]'

echo "── Case 1 (THE fix): strict ancestor + quality-gates-v2 CONCLUDED failure — MUST close + delete ──"
out1=$(run_case case1 "newsha0000022222222222222222222222222" "$STALE_HEAD" "$PR_JSON_OK" "ahead" "1" "false")
if [ "$out1" = "CLOSED_AND_DELETED" ]; then
  pass "case1: ancestor PR with concluded-failure check is closed and its ref deleted (the fix)"
else
  fail "case1: expected CLOSED_AND_DELETED, got $out1"
fi

echo "── Case 2: NOT a strict ancestor (compare status != ahead) — must NOT touch the PR ──"
out2=$(run_case case2 "newsha0000022222222222222222222222222" "$STALE_HEAD" "$PR_JSON_OK" "diverged" "1" "false")
if [ "$out2" = "UNTOUCHED" ]; then
  pass "case2: a non-ancestor head is left alone (mass-close guard)"
else
  fail "case2: expected UNTOUCHED, got $out2"
fi

echo "── Case 3: ancestor, but quality-gates-v2 has NOT concluded failure — must NOT touch the PR ──"
out3=$(run_case case3 "newsha0000022222222222222222222222222" "$STALE_HEAD" "$PR_JSON_OK" "ahead" "0" "false")
if [ "$out3" = "UNTOUCHED" ]; then
  pass "case3: an ancestor PR still viable/checking (no concluded failure) is left alone"
else
  fail "case3: expected UNTOUCHED, got $out3"
fi

echo "── Case 4 (THE naive-hoist risk this constraint closes): empty \$LDR_SHA — total no-op ──"
out4=$(run_case case4 "" "$STALE_HEAD" "$PR_JSON_OK" "ahead" "1" "false")
if [ "$out4" = "UNTOUCHED" ]; then
  pass "case4: empty LDR_SHA short-circuits to a no-op instead of mass-closing every open promote PR"
else
  fail "case4: expected UNTOUCHED (empty-LDR_SHA guard), got $out4"
fi

echo "── Case 5: DRY_RUN=true on an otherwise-closeable PR — must NOT call gh pr close / -X DELETE ──"
out5=$(run_case case5 "newsha0000022222222222222222222222222" "$STALE_HEAD" "$PR_JSON_OK" "ahead" "1" "true")
if [ "$out5" = "UNTOUCHED" ]; then
  pass "case5: dry-run computes the same ancestor+failed verdict without mutating anything"
else
  fail "case5: expected UNTOUCHED (dry-run), got $out5"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
