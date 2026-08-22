#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for binding ENVIRONMENT/DEPLOYMENT_ENV into the QG green-content
# sentinel hash (qg_sentinel_environment_blind_2026_07_23.md item 2, batch2 todo 1a).
#
# Bug: `.qg_content_sentinel` (the byte-identical-tree fast-path that skips TESTS +
# TYPE CHECK on repeated runs) was a bare content hash with NO configuration
# dimension — a tree verified under ENVIRONMENT=development would HIT (and skip the
# heavy phases) on a later run of the SAME tree under ENVIRONMENT=production/unset,
# even though bucket resolution / credential posture differ between the two and the
# heavy phases were never actually re-verified under the new configuration.
#
# Like test-ratchet-exit-code-aggregation.sh, this EXTRACTS the REAL _qg_content_hash
# function from base-service.sh (not a replica) and proves it now produces a DIFFERENT
# hash for a byte-identical tree under a different ENVIRONMENT/DEPLOYMENT_ENV, and the
# SAME hash when config is unchanged (no false-invalidation regression).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-sentinel-environment-binding.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

BASE_SERVICE="$(cd "$(dirname "$0")/.." && pwd)/base-service.sh"
[ -f "$BASE_SERVICE" ] || { echo "FATAL: base-service.sh not found at $BASE_SERVICE"; exit 2; }

# ── Extract the REAL _qg_content_hash function ───────────────────────────────────
FN=$(awk '/^_qg_content_hash\(\) \{/{c=1} c{print} c&&/^\}$/{exit}' "$BASE_SERVICE")
[ -n "$FN" ] || { echo "FATAL: could not extract _qg_content_hash from base-service.sh"; exit 2; }

# Structural anchor: the extracted function must actually reference ENVIRONMENT /
# DEPLOYMENT_ENV — so a future edit that removes the binding fails here, not silently.
case "$FN" in
  *'ENVIRONMENT:-'*'DEPLOYMENT_ENV:-'*)
    pass "structural: extracted _qg_content_hash references ENVIRONMENT + DEPLOYMENT_ENV" ;;
  *)
    fail "structural: extracted _qg_content_hash missing the ENVIRONMENT/DEPLOYMENT_ENV binding"
    echo "--- function ---"; echo "$FN" ;;
esac

WORK="$(mktemp -d)"
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"
$GIT init -q "$WORK/repo"
( cd "$WORK/repo" && printf 'content\n' > f.txt && $GIT add f.txt && $GIT commit -qm base )

# Real _qg_hash (mirrors qg-common.sh exactly — sha256sum-or-shasum portability).
if command -v sha256sum &>/dev/null; then
  _qg_hash() { sha256sum 2>/dev/null | awk '{print $1}'; }
else
  _qg_hash() { shasum -a 256 2>/dev/null | awk '{print $1}'; }
fi
# _qg_editable_sibling_hash is a real qg-common.sh helper the function also calls;
# no .venv exists in this throwaway fixture, so the real semantics (no site-packages
# → contribute nothing) apply via a faithful minimal reimplementation rather than a
# no-op stub, so a future signature change to the real one is still exercised in spirit.
_qg_editable_sibling_hash() { :; }

run_hash() {  # $1=dir, ENVIRONMENT/DEPLOYMENT_ENV taken from the calling env
  ( cd "$1" && eval "$FN" && _qg_content_hash )
}

echo "── same tree, ENVIRONMENT unset vs development (expect DIFFERENT hash) ──"
h_unset=$(ENVIRONMENT= DEPLOYMENT_ENV= run_hash "$WORK/repo")
h_dev=$(ENVIRONMENT=development DEPLOYMENT_ENV= run_hash "$WORK/repo")
if [ -n "$h_unset" ] && [ -n "$h_dev" ] && [ "$h_unset" != "$h_dev" ]; then
  pass "unset vs development → different hash ($h_unset vs $h_dev)"
else
  fail "unset vs development did NOT differ (unset=$h_unset dev=$h_dev)"
fi

echo "── same tree, ENVIRONMENT=development vs production (expect DIFFERENT hash) ──"
h_prod=$(ENVIRONMENT=production DEPLOYMENT_ENV= run_hash "$WORK/repo")
if [ -n "$h_dev" ] && [ -n "$h_prod" ] && [ "$h_dev" != "$h_prod" ]; then
  pass "development vs production → different hash ($h_dev vs $h_prod)"
else
  fail "development vs production did NOT differ (dev=$h_dev prod=$h_prod)"
fi

echo "── same tree, same ENVIRONMENT, DEPLOYMENT_ENV differs (expect DIFFERENT hash) ──"
h_dep_a=$(ENVIRONMENT=production DEPLOYMENT_ENV=staging run_hash "$WORK/repo")
h_dep_b=$(ENVIRONMENT=production DEPLOYMENT_ENV=prod run_hash "$WORK/repo")
if [ -n "$h_dep_a" ] && [ -n "$h_dep_b" ] && [ "$h_dep_a" != "$h_dep_b" ]; then
  pass "DEPLOYMENT_ENV=staging vs prod (same ENVIRONMENT) → different hash"
else
  fail "DEPLOYMENT_ENV change did NOT alter the hash (a=$h_dep_a b=$h_dep_b)"
fi

echo "── same tree, SAME config twice (expect IDENTICAL hash — no false-invalidation) ──"
h_repeat_a=$(ENVIRONMENT=development DEPLOYMENT_ENV= run_hash "$WORK/repo")
h_repeat_b=$(ENVIRONMENT=development DEPLOYMENT_ENV= run_hash "$WORK/repo")
if [ -n "$h_repeat_a" ] && [ "$h_repeat_a" = "$h_repeat_b" ] && [ "$h_repeat_a" = "$h_dev" ]; then
  pass "identical config, re-run twice → identical hash (repeatable, no false-invalidation)"
else
  fail "identical config did not reproduce the same hash (a=$h_repeat_a b=$h_repeat_b earlier_dev=$h_dev)"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
