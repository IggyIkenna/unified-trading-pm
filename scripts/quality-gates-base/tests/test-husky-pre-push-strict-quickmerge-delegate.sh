#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the husky UI repos' (deployment-ui, unified-trading-system-ui)
# strict-quickmerge pre-push guard
# (issues/provenance_gate_override_and_unenforced_quickmerge_hook_2026_07_17.md,
# ci_satellite_ao_dispatch_batch1_2026_07_26.md "The two husky UI repos carry no
# strict-quickmerge guard").
#
# Bug: every hooks installer/self-heal (install-hooks.sh, setup-tab-worktrees.sh,
# slot-cron-ff-pull.sh) SKIPS husky-managed repos entirely (core.hooksPath under
# .husky/, to avoid clobbering husky's own .husky/_/ shims) — so deployment-ui and
# unified-trading-system-ui were the only clones with NO provenance guard at all.
#
# Fix: a COMMITTED <repo>/.husky/pre-push delegate (mirrors .husky/pre-commit's prek
# delegation) that execs the fleet's canonical scripts/hooks/pre-push, so it ships via
# normal commits rather than a per-tick content-heal. slot-cron-ff-pull.sh's self-heal
# now RECOGNISES the install (warns loudly if the delegate is missing) instead of a
# silent no-signal skip.
#
# Like test-quickmerge-untracked-new-file-guard.sh, this runs the REAL committed
# delegate files + the REAL canonical guard (not replicas) against synthesized git
# fixtures, and EXTRACTS the real husky-recognition block from slot-cron-ff-pull.sh.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-husky-pre-push-strict-quickmerge-delegate.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

PM_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
WS_ROOT="$(dirname "$PM_ROOT")"
CANON_GUARD="$PM_ROOT/scripts/hooks/pre-push"
SELF_HEAL="$PM_ROOT/scripts/dev/slot-cron-ff-pull.sh"
[ -f "$CANON_GUARD" ] || { echo "FATAL: canonical guard not found at $CANON_GUARD"; exit 2; }
[ -f "$SELF_HEAL" ] || { echo "FATAL: self-heal script not found at $SELF_HEAL"; exit 2; }

UI_REPOS="deployment-ui unified-trading-system-ui"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

echo "── Structural: each UI repo carries a committed, executable .husky/pre-push delegate ──"
for _repo in $UI_REPOS; do
  _delegate="$WS_ROOT/$_repo/.husky/pre-push"
  if [ ! -f "$_delegate" ]; then
    fail "$_repo: .husky/pre-push delegate is missing at $_delegate"
    continue
  fi
  pass "$_repo: .husky/pre-push delegate exists"
  if [ -x "$_delegate" ]; then
    pass "$_repo: .husky/pre-push delegate is executable"
  else
    fail "$_repo: .husky/pre-push delegate is NOT executable"
  fi
  case "$(cat "$_delegate")" in
    *"scripts/hooks/pre-push"*"exec \"\$_guard\""*)
      pass "$_repo: delegate execs the canonical scripts/hooks/pre-push guard" ;;
    *)
      fail "$_repo: delegate does not exec the canonical guard as expected" ;;
  esac
done

# ── Functional: run the REAL committed delegate against synthesized git fixtures ────
# (skip gracefully if a UI repo isn't present as a sibling — e.g. a checkout that only
# has PM cloned; this mirrors the canonical guard's own graceful-degradation contract)
run_delegate_case() {
  # $1=fixture repo dir  $2=lsha  $3=rsha  $4=delegate path
  ( cd "$1" && printf '%s %s refs/heads/live-defi-rollout %s\n' "$2" "$2" "$3" | UNIFIED_TRADING_WORKSPACE_ROOT="$WS_ROOT" "$4" origin )
}

# Fresh fixture per case (never mutate/reset a shared one) — each is a new init'd repo
# with a base commit + the real delegate copied in, mirroring test-quickmerge-untracked-
# new-file-guard.sh's _make_fixture pattern.
_make_ui_fixture() {
  local delegate_src="$1"
  local tag="$2"
  local f="$WORK/${tag}"
  mkdir -p "$f/.husky" "$f/src"
  ( cd "$f" && $GIT init -q )
  cp "$delegate_src" "$f/.husky/pre-push"
  chmod +x "$f/.husky/pre-push"
  printf 'base\n' > "$f/README.md"
  ( cd "$f" && $GIT add -A && $GIT commit -qm base )
  echo "$f"
}

for _repo in $UI_REPOS; do
  _delegate_src="$WS_ROOT/$_repo/.husky/pre-push"
  [ -f "$_delegate_src" ] || { echo "SKIP: $_repo delegate not present — functional cases skipped"; continue; }

  echo "── $_repo Case A: synthetic non-quickmerge .ts source change — must BLOCK ──"
  fA=$(_make_ui_fixture "$_delegate_src" "${_repo}_caseA")
  RSHA_A="$( cd "$fA" && git rev-parse HEAD )"
  printf 'export const x = 1;\n' > "$fA/src/synthetic_test_file.ts"
  ( cd "$fA" && $GIT add -A && $GIT commit -qm "test: synthetic non-quickmerge source change" )
  LSHA_A="$( cd "$fA" && git rev-parse HEAD )"
  outA=$(run_delegate_case "$fA" "$LSHA_A" "$RSHA_A" ".husky/pre-push" 2>&1); rcA=$?
  if [ "$rcA" -ne 0 ] && printf '%s\n' "$outA" | grep -q "BLOCKED"; then
    pass "$_repo case A: non-quickmerge source push blocked (exit $rcA)"
  else
    fail "$_repo case A: expected a BLOCKED non-zero exit, got exit $rcA"; echo "--- output ---"; printf '%s\n' "$outA"
  fi

  echo "── $_repo Case B: quickmerged .ts source change — must PASS ──"
  fB=$(_make_ui_fixture "$_delegate_src" "${_repo}_caseB")
  RSHA_B="$( cd "$fB" && git rev-parse HEAD )"
  printf 'export const y = 2;\n' > "$fB/src/synthetic_test_file2.ts"
  ( cd "$fB" && $GIT add -A && $GIT commit -qm "$(printf 'feat: synthetic quickmerged source change\n\nQuickmerge: agent')" )
  LSHA_B="$( cd "$fB" && git rev-parse HEAD )"
  outB=$(run_delegate_case "$fB" "$LSHA_B" "$RSHA_B" ".husky/pre-push" 2>&1); rcB=$?
  if [ "$rcB" -eq 0 ] && printf '%s\n' "$outB" | grep -q "no bypassed code commits"; then
    pass "$_repo case B: quickmerged source push passes (exit 0)"
  else
    fail "$_repo case B: expected a clean pass, got exit $rcB"; echo "--- output ---"; printf '%s\n' "$outB"
  fi

  echo "── $_repo Case C: canonical guard unresolvable — must gracefully warn + exit 0 ──"
  fC=$(_make_ui_fixture "$_delegate_src" "${_repo}_caseC")
  outC=$(cd "$fC" && printf 'x x refs/heads/live-defi-rollout y\n' | UNIFIED_TRADING_WORKSPACE_ROOT=/nonexistent-workspace-root ./.husky/pre-push origin 2>&1); rcC=$?
  if [ "$rcC" -eq 0 ] && printf '%s\n' "$outC" | grep -q "canonical guard not found"; then
    pass "$_repo case C: missing canonical guard degrades gracefully (exit 0, warns)"
  else
    fail "$_repo case C: expected graceful degradation, got exit $rcC"; echo "--- output ---"; printf '%s\n' "$outC"
  fi
done

echo "── Self-heal: slot-cron-ff-pull.sh RECOGNISES husky installs (warns on missing, silent when present) ──"
# Extract the husky-branch case block (from `case "${_hooks_dir}" in` through its
# matching `esac`) so this test tracks the REAL shipped logic, not a replica.
BLOCK=$(awk '
  /case "\$\{_hooks_dir\}" in/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]*esac$/ { exit }
' "$SELF_HEAL")
[ -n "$BLOCK" ] || { echo "FATAL: could not extract the husky-recognition case block from slot-cron-ff-pull.sh"; exit 2; }

case "$BLOCK" in
  *"*/.husky/*"*"_husky_pp="*"hook-heal:WARN"*"continue"*)
    pass "structural: extracted block recognises husky hooks dirs, warns on a missing delegate, and continues (no prek/pre-push clobber)" ;;
  *)
    fail "structural: extracted husky-branch block missing an expected contract element"; echo "--- block ---"; echo "$BLOCK" ;;
esac

# Functional: eval the extracted block against a synthetic husky-shaped _hooks_dir, with
# `log` stubbed to capture output instead of the real cron's date-stamped printf.
run_husky_block() {
  local hooks_dir="$1" clone_dir="$2"
  (
    log() { echo "LOG: $*"; }
    _hooks_dir="$hooks_dir"
    _clone="$clone_dir"
    # The extracted block ends in `continue` (its real loop context in slot-cron-ff-pull.sh) —
    # a single-pass `for` here gives `continue` a real loop to target so it behaves normally
    # instead of a bare-`continue`-outside-a-loop warning.
    for _once in 1; do
      eval "$BLOCK"
    done
    echo "FELL_THROUGH_AFTER_CONTINUE_WOULD_NOT_PRINT_THIS"
  )
}

_synthetic_repo="$WORK/synthetic_husky_repo"
mkdir -p "$_synthetic_repo/.husky/_"
out_missing=$(run_husky_block "$_synthetic_repo/.husky/_" "$_synthetic_repo")
if printf '%s\n' "$out_missing" | grep -q "hook-heal:WARN.*husky-managed repo has NO .husky/pre-push"; then
  pass "self-heal: WARNs when a husky repo's .husky/pre-push delegate is missing"
else
  fail "self-heal: expected a hook-heal WARN for a missing husky delegate"; echo "--- output ---"; printf '%s\n' "$out_missing"
fi

touch "$_synthetic_repo/.husky/pre-push"
out_present=$(run_husky_block "$_synthetic_repo/.husky/_" "$_synthetic_repo")
if printf '%s\n' "$out_present" | grep -q "hook-heal:WARN"; then
  fail "self-heal: should NOT warn once the husky delegate is present"; echo "--- output ---"; printf '%s\n' "$out_present"
else
  pass "self-heal: silent (no WARN) once the husky delegate is present"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
