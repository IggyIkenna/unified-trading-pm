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
# CANCELLED/SUPERSEDED disposition (2026-08-09): task_template.md's `/done`-time disposition
# markers document converting a dead/re-scoped `- [ ] <brief>` line into a bold, non-checkbox
# bullet (`- **[TAG] P<n>. CANCELLED — SUPERSEDED <date> (<who>, per <ref>).**`) — a legitimate
# closure, not a deletion. Count that pattern alongside checkbox lines so following the
# documented convention doesn't false-positive as a todo loss. Fix for
# todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md.
#
# Ancestor guard (2026-08-10): the origin/live-defi-rollout ref is only a valid comparison
# BASE when it is an ancestor-or-equal of HEAD — i.e. when the working tree is genuinely on
# top of that ref (a PR/promote branch, or a local commit on LDR with the origin ref still at
# the pre-commit state). On a fast-moving shared branch the LOCAL origin ref can be a
# DESCENDANT of HEAD — a peer pushed after this checkout, or, in CI, a workflow_dispatch on
# live-defi-rollout re-fetches origin/live-defi-rollout after checkout while the branch keeps
# advancing. Comparing today's tree against a FUTURE state of the branch inverts the
# comparison and false-positives as a "todo lost". Seen 2026-08-10: a CI dispatch checked out
# c00f943f0c (deployment_api_unauthenticated_prod_p0_2026_08_10.md had 5 todos) while the
# mid-run-fetched origin had advanced to include 29aff230cd, which ADDED 3 todos to that plan
# → the check reported "origin=8 current=5 lost=3" for a plan whose todos only ever grew. When
# the base is not an ancestor, skip (matches the existing missing-ref no-op where gh_total
# falls back to 0); a genuine deletion committed at the tip is still caught by the next
# promote-PR run, whose origin base is a true ancestor.

set -euo pipefail
ORIGIN="origin/live-defi-rollout"
CANCELLED_RE='^- \*\*\[[A-Z]+\] P[0-9]+\. CANCELLED'

# Early-out guard — see docstring above. Both --only and full-sweep modes skip when the base
# ref is not an ancestor-or-equal of HEAD (or is absent locally).
if ! git merge-base --is-ancestor "${ORIGIN}" HEAD 2>/dev/null; then
  [ "${1:-}" != "--quiet" ] && \
    echo "⏭  check_todo_regression: ${ORIGIN} is not an ancestor-or-equal of HEAD (a peer/CI push moved the base past this checkout) — origin-compare is meaningless this run, skipping (no-op)"
  exit 0
fi

_check_one() {
  # $1 = file path (may be staged working-tree path or corpus-glob path), $2 = repo-relative path
  local f="$1" rel="$2"
  local cur_checkbox cur_cancelled cur_total gh_total
  cur_checkbox=$(grep -cE "^- \[[ xX]\]" "$f" 2>/dev/null || true)
  cur_cancelled=$(grep -cE "$CANCELLED_RE" "$f" 2>/dev/null || true)
  gh_total=$(git show "${ORIGIN}:${rel}" 2>/dev/null | grep -cE "^- \[[ xX]\]" || true)
  cur_checkbox="${cur_checkbox:-0}"
  cur_cancelled="${cur_cancelled:-0}"
  gh_total="${gh_total:-0}"
  cur_total=$(( cur_checkbox + cur_cancelled ))
  if [ "$gh_total" -gt 0 ] && [ "$cur_total" -lt "$gh_total" ]; then
    local lost=$(( gh_total - cur_total ))
    echo "LOSS  $(basename "$f")  origin=${gh_total}  current=${cur_total}  lost=${lost} (TOTAL todos open+done — a flip or a CANCELLED/SUPERSEDED conversion is conserved; a drop = deletion/collapse)"
    return 1
  fi
  return 0
}

if [ "${1:-}" = "--only" ]; then
  shift
  PM_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
  FAILURES=0
  WARNINGS=()
  for f in "$@"; do
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
    echo "❌ check_todo_regression (--only): ${FAILURES} staged plan(s) lost todos vs ${ORIGIN}"
    for w in "${WARNINGS[@]}"; do echo "  $w"; done
    exit 1
  fi
  echo "✅ check_todo_regression (--only): 0 violation(s) in staged files"
  exit 0
fi

QUIET="${1:-}"
PLANS_DIR="$(cd "$(dirname "$0")/../.." && pwd)/plans/active"
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
  echo "❌ check_todo_regression: ${FAILURES} plan(s) lost todos (total open+done shrank) vs ${ORIGIN}"
  for w in "${WARNINGS[@]}"; do
    echo "  $w"
  done
  echo ""
  echo "Fix: restore from GitHub — keep new frontmatter, restore GitHub body:"
  echo "  FM=\$(head -N file); BODY=\$(git show ${ORIGIN}:plans/active/file | tail -n +M)"
  echo "  printf '%s\n%s\n' \"\$FM\" \"\$BODY\" > file"
  exit 1
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_todo_regression: all plans match or exceed ${ORIGIN} total todo count (flips conserved)"
  exit 0
fi
