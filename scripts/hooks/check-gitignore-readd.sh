#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Gitignore re-add gate — pre-commit stage.
#
# Once a path is deliberately gitignored (e.g. a regenerated test artifact class
# like playwright-report/, blob-report/, test-results/ — see
# agent-orchestrator/server/worktree_clean_check/_artifacts.py's FM3 comment on why
# these must never be tracked), nothing should be able to silently re-add it. The
# ONLY way that normally happens is `git add -f` (or an editor that stages ignored
# files) — `git add -A`/`git add .` already skip ignored paths on their own, so a
# staged-but-ignored file is always a deliberate force-add, not an accident of a
# normal workflow.
#
# This hook checks every staged file against the repo's OWN current .gitignore
# (via `git check-ignore`, not a hardcoded pattern list) and blocks the commit if
# any staged path is currently ignore-matched. Fast (one `check-ignore` call per
# staged file, no history walk), and repo-agnostic — it enforces whatever each
# repo's own .gitignore already declares, nothing new to configure per repo.
set -euo pipefail

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)
[ -z "$STAGED_FILES" ] && exit 0

BLOCKED=()
while IFS= read -r f; do
  [ -z "$f" ] && continue
  if git check-ignore -q -- "$f" 2>/dev/null; then
    BLOCKED+=("$f")
  fi
done <<<"$STAGED_FILES"

if [ "${#BLOCKED[@]}" -gt 0 ]; then
  echo "❌ Blocked: staged file(s) match this repo's own .gitignore — looks like a"
  echo "   force-add (git add -f) of a path that was deliberately ignored:"
  for f in "${BLOCKED[@]}"; do
    echo "     - $f"
  done
  echo ""
  echo "   If this file genuinely needs to be tracked, remove it from .gitignore"
  echo "   first (in the same commit) rather than force-adding around it — a"
  echo "   silent re-add is exactly what this class of generated-artifact"
  echo "   .gitignore entry exists to prevent."
  exit 1
fi
exit 0
