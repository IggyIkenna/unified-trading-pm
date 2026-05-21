#!/usr/bin/env bash
# Check that no plan in plans/active/ has fewer open todos than origin/live-defi-rollout.
# Root-cause fix for the agent todo-collapse failure mode.
# Usage: bash scripts/plan-hygiene/check_todo_regression.sh [--quiet]
# Exit 0 = no regressions. Exit 1 = one or more plans lost open todos.

set -euo pipefail
QUIET="${1:-}"
PLANS_DIR="$(cd "$(dirname "$0")/../.." && pwd)/plans/active"
ORIGIN="origin/live-defi-rollout"
FAILURES=0
WARNINGS=()

for f in "$PLANS_DIR"/*.md; do
  name="$(basename "$f")"
  rel="plans/active/$name"

  cur_open=$(grep -c "^- \[ \]" "$f" 2>/dev/null || true)
  gh_open=$(git show "${ORIGIN}:${rel}" 2>/dev/null | grep -c "^- \[ \]" || true)

  cur_open="${cur_open:-0}"
  gh_open="${gh_open:-0}"

  if [ "$gh_open" -gt 0 ] && [ "$cur_open" -lt "$gh_open" ]; then
    lost=$(( gh_open - cur_open ))
    WARNINGS+=("LOSS  $name  origin=${gh_open}  current=${cur_open}  lost=${lost}")
    FAILURES=$(( FAILURES + 1 ))
  fi
done

if [ "${#WARNINGS[@]}" -gt 0 ]; then
  echo "❌ check_todo_regression: ${FAILURES} plan(s) lost open todos vs ${ORIGIN}"
  for w in "${WARNINGS[@]}"; do
    echo "  $w"
  done
  echo ""
  echo "Fix: restore from GitHub — keep new frontmatter, restore GitHub body:"
  echo "  FM=\$(head -N file); BODY=\$(git show ${ORIGIN}:plans/active/file | tail -n +M)"
  echo "  printf '%s\n%s\n' \"\$FM\" \"\$BODY\" > file"
  exit 1
else
  [ "$QUIET" != "--quiet" ] && echo "✅ check_todo_regression: all plans match or exceed ${ORIGIN} open todo count"
  exit 0
fi
