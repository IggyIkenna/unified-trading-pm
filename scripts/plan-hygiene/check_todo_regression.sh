#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Check that no plan in plans/active/ LOST a todo (line deleted/collapsed) vs
# origin/live-defi-rollout. Root-cause fix for the agent todo-collapse failure mode.
#
# IMPORTANT (2026-06-07): the invariant is on TOTAL todos (open `- [ ]` + done `- [x]`),
# NOT open-only. Flipping `- [ ]` → `- [x]` is the MANDATED Commit+Push+Flip operation —
# it COMPLETES a todo, it does not lose it. The earlier open-only count false-positived on
# every legitimate flip (it read "3 fewer open" as "3 lost"), which blocked the very
# checkbox-flip the workflow requires. A genuine collapse/deletion shrinks the TOTAL, which
# is what we gate on. (An all-done plan is then an archive candidate, handled elsewhere.)
#
# Usage: bash scripts/plan-hygiene/check_todo_regression.sh [--quiet]
#   bash scripts/plan-hygiene/check_todo_regression.sh --only <path> [<path> ...]
#   bash scripts/plan-hygiene/check_todo_regression.sh --merge-base [--quiet]
# Exit 0 = no regressions. Exit 1 = one or more plans lost todos (total shrank).
#
# ``--only <paths>`` (2026-08-09, precommit migration): checks ONLY the given staged files
# against their own origin/live-defi-rollout content — same shape as the other --only-scoped
# checks in this dir. This check does NOT need a network fetch (git show reads the local
# origin/live-defi-rollout ref, whatever it currently resolves to on disk) — the "NO origin
# fetch" precommit-exclusion comment in run_hygiene_sweep.sh described a real network call
# that this script never actually makes, so the exclusion was over-broad. Root-caused after a
# promote-PR full-QG run caught a plan that lost a todo hours after it landed via
# safe-doc-push.sh, which never ran this check at all (unified-trading-pm PR #2670,
# 2026-08-09) — the exact same fast-path-blind-to-full-gate pattern as the other checks
# migrated here today.
#
# ``--merge-base`` (2026-08-12, CI snapshot-race fix): the default full-baseline mode
# compares every plan's total todo count against origin/live-defi-rollout's CURRENT tip — a
# LIVE MOVING target, re-fetched fresh every CI run. A concurrent agent commit landing after
# this push forked adds todos to a plan this push never touched, and the stale snapshot then
# reads as "lost" todos, false-flagging the whole run
# (plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md). --merge-base
# instead compares against the MERGE-BASE of HEAD and origin/live-defi-rollout — the actual
# fork point, which is STABLE and measures exactly "did THIS push's own diff lose todos".
# Because the CI checkout is a shallow fetch-depth:2 PR ref, git merge-base cannot resolve
# without more history — it FAILS LOUDLY (never a silent grafted result; verified 2026-08-12),
# so we deepen incrementally (cumulative, connecting the LDR side to locally-present history)
# until it resolves. run_hygiene_sweep.sh passes --merge-base in --ci mode only; local
# interactive / pre-push / --only runs keep the origin-tip comparison unchanged.
#
# CANCELLED/SUPERSEDED disposition (2026-08-09): task_template.md's `/done`-time disposition
# markers document converting a dead/re-scoped `- [ ] <brief>` line into a bold, non-checkbox
# bullet (`- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`) — a legitimate
# closure, not a deletion. Count that pattern alongside checkbox lines so following the
# documented convention doesn't false-positive as a todo loss. Fix for
# todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md.

set -euo pipefail
ORIGIN="origin/live-defi-rollout"
CANCELLED_RE='^- \*\*\[[A-Z]+\] P[0-9]+\. CANCELLED'
BASE_REF="$ORIGIN"

# Resolve the comparison base ref — the merge-base of HEAD and origin/live-defi-rollout.
#   mode=merge (CI): deepen incrementally until the fork point is reachable, then fall back
#                   to the moving tip only if it genuinely can't be resolved.
#   mode=tip   (local/precommit): merge-base first-try only; fall back to the tip.
# Returns 0 with BASE_REF set on success; 1 (BASE_REF left at $ORIGIN) on fallback.
resolve_base_ref() {
  local mode="${1:-tip}"
  # First try — succeeds whenever HEAD's own local history reaches the fork (promote-head /
  # push-to-main / LDR-dispatch runs are ancestors of the tip, and a fresh PR's commits are
  # small). A result that is NOT a shallow-grafted boundary commit is reliable; git fails
  # merge-base LOUDLY while history is insufficient, so a success here is never a silent
  # wrong base.
  local mb
  if mb=$(git merge-base HEAD "$ORIGIN" 2>/dev/null) \
     && ! grep -qx "$mb" .git/shallow 2>/dev/null; then
    BASE_REF="$mb"
    return 0
  fi
  [ "$mode" = "merge" ] || return 1
  # CI: deepen incrementally (cumulative) until the fork point is reachable. Each deepen
  # re-negotiates and connects the LDR side to locally-present history, so the depth actually
  # fetched is bounded by the fork distance on the HEAD side (a PR's own commit count), not
  # the moving tip's age. 50/150/350/750 cumulative covers any realistic fork distance.
  local n=50
  while [ "$n" -le 400 ]; do
    git fetch --quiet --deepen="$n" origin 2>/dev/null || break
    if mb=$(git merge-base HEAD "$ORIGIN" 2>/dev/null) \
       && ! grep -qx "$mb" .git/shallow 2>/dev/null; then
      BASE_REF="$mb"
      return 0
    fi
    n=$(( n * 2 ))
  done
  return 1
}

_check_one() {
  # $1 = file path (may be staged working-tree path or corpus-glob path), $2 = repo-relative path
  local f="$1" rel="$2"
  local cur_checkbox cur_cancelled cur_total gh_total
  cur_checkbox=$(grep -cE "^- \[[ xX]\]" "$f" 2>/dev/null || true)
  cur_cancelled=$(grep -cE "$CANCELLED_RE" "$f" 2>/dev/null || true)
  gh_total=$(git show "${BASE_REF}:${rel}" 2>/dev/null | grep -cE "^- \[[ xX]\]" || true)
  cur_checkbox="${cur_checkbox:-0}"
  cur_cancelled="${cur_cancelled:-0}"
  gh_total="${gh_total:-0}"
  cur_total=$(( cur_checkbox + cur_cancelled ))
  if [ "$gh_total" -gt 0 ] && [ "$cur_total" -lt "$gh_total" ]; then
    local lost=$(( gh_total - cur_total ))
    echo "LOSS  $(basename "$f")  base=${gh_total}  current=${cur_total}  lost=${lost} (TOTAL todos open+done — a flip or a CANCELLED/SUPERSEDED conversion is conserved; a drop = deletion/collapse)"
    return 1
  fi
  return 0
}

QUIET=""
MERGE_MODE=0
ONLY_MODE=0
PATHS=()
for _a in "$@"; do
  case "$_a" in
    --merge-base) MERGE_MODE=1 ;;
    --only)       ONLY_MODE=1 ;;
    --quiet)      QUIET="--quiet" ;;
    *)            PATHS+=("$_a") ;;
  esac
done

if [ "$ONLY_MODE" = "1" ]; then
  PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
  FAILURES=0
  WARNINGS=()
  for f in "${PATHS[@]}"; do
    [ -f "$f" ] || continue
    # Resolve the repo-relative path robustly (staged paths may be absolute or relative) —
    # handles both plans/active/*.md and plans/active/issues/*.md without special-casing.
    rel="$(cd "$(dirname "$f")" && pwd)/$(basename "$f")"
    rel="${rel#"$PM_DIR"/}"
    if ! w=$(_check_one "$f" "$rel"); then
      WARNINGS+=("$w")
      FAILURES=$(( FAILURES + 1 ))
    fi
  done
  if [ "${#WARNINGS[@]}" -gt 0 ]; then
    echo "❌ check_todo_regression (--only): ${FAILURES} staged plan(s) lost todos vs ${BASE_REF}"
    for w in "${WARNINGS[@]}"; do echo "  $w"; done
    exit 1
  fi
  echo "✅ check_todo_regression (--only): 0 violation(s) in staged files"
  exit 0
fi

PLANS_DIR="$(cd "$(dirname "$0")/../.." && pwd)/plans/active"
if [ "$MERGE_MODE" = "1" ]; then
  if resolve_base_ref merge; then
    [ "$QUIET" != "--quiet" ] && echo "ℹ️  check_todo_regression: comparing vs merge-base $(git rev-parse --short "$BASE_REF") of ${ORIGIN} (stable fork point)"
  else
    [ "$QUIET" != "--quiet" ] && echo "ℹ️  check_todo_regression: merge-base unresolvable (shallow / no shared history) — comparing vs ${ORIGIN} tip"
  fi
fi
FAILURES=0
WARNINGS=()

for f in "$PLANS_DIR"/*.md; do
  name="$(basename "$f")"
  rel="plans/active/$name"
  if ! w=$(_check_one "$f" "$rel"); then
    WARNINGS+=("$w")
    FAILURES=$(( FAILURES + 1 ))
  fi
done

if [ "${#WARNINGS[@]}" -gt 0 ]; then
  echo "❌ check_todo_regression: ${FAILURES} plan(s) lost todos (total open+done shrank) vs ${BASE_REF}"
  for w in "${WARNINGS[@]}"; do
    echo "  $w"
  done
  echo ""
  echo "Fix: restore from the base ref — keep new frontmatter, restore base body:"
  echo "  FM=\$(head -N file); BODY=\$(git show ${BASE_REF}:plans/active/file | tail -n +M)"
  echo "  printf '%s\n%s\n' \"\$FM\" \"\$BODY\" > file"
  exit 1
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_todo_regression: all plans match or exceed ${BASE_REF} total todo count (flips conserved)"
  exit 0
fi
