#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Pre-commit hook: check if you're behind on your current branch.
# Blocks commit if origin has commits you haven't pulled.
# Skipped in CI. Override: SKIP_BRANCH_DRIFT=1 git commit ...
#
# Install: add to .pre-commit-config.yaml as a local hook, or:
#   ln -sf ../../unified-trading-pm/scripts/hooks/check-branch-drift.sh .git/hooks/pre-commit
#
# This is intentionally lightweight — no PM manifest fetch, just a git rev-list.
# The full version/dependency drift check runs in quality-gates.sh.

set -euo pipefail

[[ -n "${GITHUB_ACTIONS:-}" || -n "${CI:-}" ]] && exit 0
[[ "${SKIP_BRANCH_DRIFT:-0}" = "1" ]] && exit 0

# An in-progress merge commit can only ever REDUCE drift (it reconciles HEAD with the
# branch the hook would otherwise flag as ahead), so exempting it here cannot let an
# agent commit on top of an un-reconciled branch — the plain-commit path below, which is
# the case this hook exists for, is untouched. Without this, `git merge origin/$BRANCH`
# fires the hook BEFORE the merge commit exists (HEAD is still pre-merge), so it always
# reads the full drift and hard-blocks the exact operation that resolves it.
git rev-parse -q --verify MERGE_HEAD >/dev/null && exit 0

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || exit 0)
[[ -z "$BRANCH" || "$BRANCH" = "HEAD" ]] && exit 0

# Quick fetch (timeout 5s, fail silently)
git fetch origin "$BRANCH" --quiet 2>/dev/null || exit 0

BEHIND=$(git rev-list HEAD..origin/"$BRANCH" --count 2>/dev/null || echo "0")

if [ "$BEHIND" -gt 0 ] 2>/dev/null; then
    echo ""
    echo "⚠️  BRANCH DRIFT: You are $BEHIND commit(s) behind origin/$BRANCH"
    echo "   Someone pushed to your branch. Pull first: git pull origin $BRANCH"
    echo ""
    echo "   Override: SKIP_BRANCH_DRIFT=1 git commit ..."
    echo "   (Human-only — agents MUST NOT use this override)"
    exit 1
fi
