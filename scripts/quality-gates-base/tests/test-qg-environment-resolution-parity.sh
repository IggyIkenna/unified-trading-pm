#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the standalone-vs-quickmerge ENVIRONMENT resolution parity fix
# (qg_sentinel_environment_blind_2026_07_23.md item 5, batch2 todo 1b).
#
# Bug: quickmerge.sh always forced ENVIRONMENT=development for any non-main branch
# (every slot, since every slot lives on live-defi-rollout); a standalone
# `quality-gates.sh` run left ENVIRONMENT unset and downstream resolvers (e.g. UTL's
# bucket_naming.py) default to prod — the two invocation paths silently diverged for
# the SAME branch context. Fix: quickmerge.sh's own block AND qg-common.sh (the
# standalone base-*.sh entrypoint, all four tiers) now both call the SAME shared
# qg_resolve_environment (qg-environment.sh) — this test proves they actually agree,
# not just that each individually "looks right".
#
# This test has three parts:
#   (1) structural anchors — quickmerge.sh's block and qg-common.sh both actually wire
#       into qg-environment.sh (so a future edit that silently re-forks the logic fails
#       here, not by drifting back into the original bug undetected)
#   (2) extract the REAL quickmerge.sh ENVIRONMENT AUTO-DETECT block and run it against
#       a fixture PM-sibling layout, for both a main-named and a non-main branch
#   (3) call the REAL qg_resolve_environment directly (the qg-common.sh call shape) for
#       the SAME two branch fixtures, and assert IDENTICAL resolution to (2)
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-qg-environment-resolution-parity.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

PM_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
QM="${PM_ROOT}/scripts/quickmerge.sh"
QG_ENV="${PM_ROOT}/scripts/quality-gates-base/qg-environment.sh"
QG_COMMON="${PM_ROOT}/scripts/quality-gates-base/qg-common.sh"
[ -f "$QM" ] || { echo "FATAL: quickmerge.sh not found at $QM"; exit 2; }
[ -f "$QG_ENV" ] || { echo "FATAL: qg-environment.sh not found at $QG_ENV"; exit 2; }
[ -f "$QG_COMMON" ] || { echo "FATAL: qg-common.sh not found at $QG_COMMON"; exit 2; }

# ── (1) structural anchors ────────────────────────────────────────────────────────
if grep -q 'quality-gates-base/qg-environment.sh' "$QM" && grep -q 'qg_resolve_environment' "$QM"; then
  pass "(1a) quickmerge.sh sources qg-environment.sh and calls qg_resolve_environment"
else
  fail "(1a) quickmerge.sh no longer wired to qg-environment.sh"
fi
if grep -q '"\${BASH_SOURCE\[0\]%/\*}/qg-environment.sh"' "$QG_COMMON" && grep -q 'qg_resolve_environment "\$PROJECT_ROOT"' "$QG_COMMON"; then
  pass "(1b) qg-common.sh sources qg-environment.sh and calls qg_resolve_environment \"\$PROJECT_ROOT\""
else
  fail "(1b) qg-common.sh no longer wired to qg-environment.sh"
fi

# ── Fixture: a PM-sibling layout mirroring .tabs/<slot>/{unified-trading-pm,<repo>} ──
WORK="$(mktemp -d)"
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"
mkdir -p "$WORK/unified-trading-pm/scripts/quality-gates-base"
cp "$QG_ENV" "$WORK/unified-trading-pm/scripts/quality-gates-base/qg-environment.sh"
$GIT init -q "$WORK/some-service"
( cd "$WORK/some-service" && printf 'x\n' > f.txt && $GIT add f.txt && $GIT commit -qm base )

# Extract the REAL quickmerge.sh ENVIRONMENT AUTO-DETECT block (both top-level `fi`s:
# the `.env`-load guard, then the branch-conditional block).
QM_BLOCK=$(awk '/^# ── ENVIRONMENT AUTO-DETECT/{c=1} c{print} c&&/^fi$/{n++; if(n==2) exit}' "$QM")
[ -n "$QM_BLOCK" ] || { echo "FATAL: could not extract ENVIRONMENT AUTO-DETECT block from quickmerge.sh"; exit 2; }

# Runs the extracted quickmerge block as quickmerge.sh itself would (REPO_DIR points at
# the fixture repo, cwd is the fixture repo — mirrors quickmerge's own `cd "$REPO_DIR"`
# ahead of this block). Prints the resolved ENVIRONMENT.
qm_resolve() {  # $1=branch
  ( cd "$WORK/some-service" && $GIT checkout -q -B "$1"
    cd "$WORK/some-service"
    REPO_NAME="fixture"
    REPO_DIR="$WORK/some-service"
    unset ENVIRONMENT GCP_PROJECT_ID
    eval "$QM_BLOCK" >/dev/null 2>&1
    echo "$ENVIRONMENT"
  )
}

# Runs the REAL qg_resolve_environment directly, as qg-common.sh's call shape does
# (qg_resolve_environment "$PROJECT_ROOT"). Prints the resolved ENVIRONMENT.
standalone_resolve() {  # $1=branch
  ( cd "$WORK/some-service" && $GIT checkout -q -B "$1"
    unset ENVIRONMENT
    # shellcheck disable=SC1090
    source "$WORK/unified-trading-pm/scripts/quality-gates-base/qg-environment.sh"
    qg_resolve_environment "$WORK/some-service"
    echo "$ENVIRONMENT"
  )
}

echo "── (2)+(3) main branch: both paths must resolve production ──"
qm_main=$(qm_resolve main)
sa_main=$(standalone_resolve main)
if [ "$qm_main" = "production" ] && [ "$sa_main" = "production" ]; then
  pass "main branch → both resolve production (quickmerge=$qm_main, standalone=$sa_main)"
else
  fail "main branch → mismatch or wrong value (quickmerge=$qm_main, standalone=$sa_main, want production/production)"
fi

echo "── (2)+(3) non-main branch (live-defi-rollout): both paths must resolve development ──"
qm_ldr=$(qm_resolve live-defi-rollout)
sa_ldr=$(standalone_resolve live-defi-rollout)
if [ "$qm_ldr" = "development" ] && [ "$sa_ldr" = "development" ]; then
  pass "live-defi-rollout → both resolve development (quickmerge=$qm_ldr, standalone=$sa_ldr)"
else
  fail "live-defi-rollout → mismatch or wrong value (quickmerge=$qm_ldr, standalone=$sa_ldr, want development/development)"
fi

echo "── (2)+(3) arbitrary feature branch: both paths must agree (parity, not just a specific value) ──"
qm_feat=$(qm_resolve some-random-feature-branch)
sa_feat=$(standalone_resolve some-random-feature-branch)
if [ "$qm_feat" = "$sa_feat" ] && [ -n "$qm_feat" ]; then
  pass "arbitrary branch → both resolve identically ($qm_feat)"
else
  fail "arbitrary branch → mismatch (quickmerge=$qm_feat, standalone=$sa_feat)"
fi

echo "── explicit ENVIRONMENT override is honoured identically by both paths ──"
qm_override=$(cd "$WORK/some-service" && REPO_NAME="fixture" REPO_DIR="$WORK/some-service" ENVIRONMENT="custom-preset" bash -c "eval \"\$1\"; echo \"\$ENVIRONMENT\"" _ "$QM_BLOCK")
sa_override=$(cd "$WORK/some-service" && ENVIRONMENT="custom-preset" bash -c "source '$WORK/unified-trading-pm/scripts/quality-gates-base/qg-environment.sh'; qg_resolve_environment '$WORK/some-service'; echo \"\$ENVIRONMENT\"")
if [ "$qm_override" = "custom-preset" ] && [ "$sa_override" = "custom-preset" ]; then
  pass "explicit ENVIRONMENT override preserved by both paths (never clobbered)"
else
  fail "explicit override not preserved (quickmerge=$qm_override, standalone=$sa_override, want custom-preset/custom-preset)"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
