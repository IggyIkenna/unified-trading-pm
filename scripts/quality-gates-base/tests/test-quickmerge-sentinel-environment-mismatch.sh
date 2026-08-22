#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the quickmerge --agent sentinel's configuration binding
# (qg_sentinel_environment_blind_2026_07_23.md item 2, batch2 todo 1a).
#
# Bug (reproduced deterministically in the issue doc): the recovery everyone used —
# "re-run `bash scripts/quality-gates.sh --no-fix`, then retry quickmerge" — writes
# `.qg_last_passed_sha` as a BARE SHA with no configuration dimension. A developer/agent
# running that recovery standalone (ENVIRONMENT unset → bucket resolver defaults to
# prod) got a green sentinel that quickmerge's `--agent` fast-path then trusted even
# though quickmerge itself ships as ENVIRONMENT=development for every non-main branch —
# a suite that genuinely fails under quickmerge's real configuration shipped green,
# never actually re-verified under it.
#
# Like test-quickmerge-blocked-contract.sh, this EXTRACTS the REAL
# _qm_check_agent_sentinel function from quickmerge.sh (not a replica) and proves:
#   (a) a sentinel written under ENVIRONMENT=development does NOT satisfy a check
#       under ENVIRONMENT=production (the core regression bar for this todo)
#   (b) ...and the reverse direction
#   (c) a sentinel DOES satisfy a check under the SAME ENVIRONMENT (no false-negative
#       regression — the fast-path must still work for the common case)
#   (d) an OLD pre-fix bare-SHA sentinel (no config lines at all) is treated as a
#       mismatch — fails closed rather than silently trusting stale state
#   (e) a missing sentinel file still reports "missing", not "mismatch" (message
#       correctness for the pre-existing case, unaffected by this change)
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-quickmerge-sentinel-environment-mismatch.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

QM="$(cd "$(dirname "$0")/../.." && pwd)/quickmerge.sh"
[ -f "$QM" ] || { echo "FATAL: quickmerge.sh not found at $QM"; exit 2; }

# ── Extract the REAL _qm_check_agent_sentinel function ───────────────────────────
FN=$(awk '/^    _qm_check_agent_sentinel\(\) \{/{c=1} c{print} c&&/^    \}$/{exit}' "$QM")
[ -n "$FN" ] || { echo "FATAL: could not extract _qm_check_agent_sentinel from quickmerge.sh"; exit 2; }

# Structural anchor: the extracted function must carry the config-mismatch check + both
# env vars — so a future edit that removes the binding fails here, not silently.
case "$FN" in
  *'ENVIRONMENT='*'DEPLOYMENT_ENV='*'sentinel config mismatch'*)
    pass "structural: extracted _qm_check_agent_sentinel carries the config-mismatch check" ;;
  *)
    fail "structural: extracted _qm_check_agent_sentinel missing the config-mismatch check"
    echo "--- function ---"; echo "$FN" ;;
esac

WORK="$(mktemp -d)"
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"
$GIT init -q "$WORK/repo"
( cd "$WORK/repo" && printf 'content\n' > f.txt && $GIT add f.txt && $GIT commit -qm base )
SHA=$(cd "$WORK/repo" && git rev-parse HEAD)

# Run the extracted function in the fixture repo with a given sentinel-file content and
# a given "current run" ENVIRONMENT/DEPLOYMENT_ENV. Echoes stdout, returns its rc.
run_check() {  # $1=sentinel-file-content  $2=ENVIRONMENT  $3=DEPLOYMENT_ENV
  (
    cd "$WORK/repo" || exit 9
    REPO_NAME="fixture-repo"
    printf '%s' "$1" > .qg_last_passed_sha
    export ENVIRONMENT="$2" DEPLOYMENT_ENV="$3"
    eval "$FN"
    _qm_check_agent_sentinel
  )
}

SENT_DEV=$(printf '%s\nENVIRONMENT=development\nDEPLOYMENT_ENV=\n' "$SHA")
SENT_PROD=$(printf '%s\nENVIRONMENT=production\nDEPLOYMENT_ENV=\n' "$SHA")
SENT_OLD_BARE=$(printf '%s\n' "$SHA")

echo "── (a) dev-written sentinel checked under a prod-context run → MUST be invalid ──"
out=$(run_check "$SENT_DEV" "production" ""); rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'sentinel config mismatch'; then
  pass "(a) dev sentinel + prod-context check → rc=$rc, mismatch reported"
else
  fail "(a) dev sentinel + prod-context check → rc=$rc (expected non-zero + mismatch message)"; printf '%s\n' "$out"
fi

echo "── (b) prod-written sentinel checked under a dev-context run → MUST be invalid ──"
out=$(run_check "$SENT_PROD" "development" ""); rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'sentinel config mismatch'; then
  pass "(b) prod sentinel + dev-context check → rc=$rc, mismatch reported"
else
  fail "(b) prod sentinel + dev-context check → rc=$rc (expected non-zero + mismatch message)"; printf '%s\n' "$out"
fi

echo "── (c) sentinel and current run agree on config → MUST still satisfy (no false-negative) ──"
out=$(run_check "$SENT_DEV" "development" ""); rc=$?
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -q 'SHA sentinel verified'; then
  pass "(c) matching config → rc=0, SHA sentinel verified"
else
  fail "(c) matching config → rc=$rc (expected 0 + SHA-verified message)"; printf '%s\n' "$out"
fi

echo "── (d) OLD pre-fix bare-SHA sentinel (no config lines) → MUST be treated as mismatch ──"
out=$(run_check "$SENT_OLD_BARE" "development" ""); rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'sentinel config mismatch'; then
  pass "(d) old bare-SHA sentinel → rc=$rc, fails closed as a mismatch"
else
  fail "(d) old bare-SHA sentinel → rc=$rc (expected non-zero + mismatch message)"; printf '%s\n' "$out"
fi

echo "── (e) missing sentinel file → still reports 'missing', not 'mismatch' ──"
# Dedicated second fixture (never has .qg_last_passed_sha written to it) rather than
# creating-then-removing the file in the shared fixture — simpler and avoids any
# ordering dependency on the cases above.
$GIT init -q "$WORK/repo-no-sentinel"
( cd "$WORK/repo-no-sentinel" && printf 'content\n' > f.txt && $GIT add f.txt && $GIT commit -qm base )
out=$(
  cd "$WORK/repo-no-sentinel" || exit 9
  REPO_NAME="fixture-repo"
  export ENVIRONMENT="development" DEPLOYMENT_ENV=""
  eval "$FN"
  _qm_check_agent_sentinel
)
rc=$?
if [ "$rc" -ne 0 ] && printf '%s' "$out" | grep -q 'sentinel missing'; then
  pass "(e) missing sentinel → rc=$rc, 'missing' reported (not conflated with a config mismatch)"
else
  fail "(e) missing sentinel → rc=$rc (expected non-zero + 'missing' message)"; printf '%s\n' "$out"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
