#!/usr/bin/env bash
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
# Exit 0 = no regressions. Exit 1 = one or more plans lost todos (total shrank).

set -euo pipefail
QUIET="${1:-}"
PLANS_DIR="$(cd "$(dirname "$0")/../.." && pwd)/plans/active"
ORIGIN="origin/live-defi-rollout"
FAILURES=0
WARNINGS=()

for f in "$PLANS_DIR"/*.md; do
  name="$(basename "$f")"
  rel="plans/active/$name"

  # Count TOTAL todos (open + done) — a flip moves a line between the two states but the
  # total is conserved; only a deletion/collapse shrinks it.
  cur_total=$(grep -cE "^- \[[ xX]\]" "$f" 2>/dev/null || true)
  gh_total=$(git show "${ORIGIN}:${rel}" 2>/dev/null | grep -cE "^- \[[ xX]\]" || true)

  cur_total="${cur_total:-0}"
  gh_total="${gh_total:-0}"

  if [ "$gh_total" -gt 0 ] && [ "$cur_total" -lt "$gh_total" ]; then
    lost=$(( gh_total - cur_total ))
    WARNINGS+=("LOSS  $name  origin=${gh_total}  current=${cur_total}  lost=${lost} (TOTAL todos open+done — a flip is conserved; a drop = deletion/collapse)")
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
