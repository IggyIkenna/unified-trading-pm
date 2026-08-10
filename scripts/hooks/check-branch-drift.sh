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

# DRIFT_GATE_ADVISORY=1 -- WARN instead of blocking. Set ONLY by a wrapper that
# provably reconciles AFTER committing (safe-doc-push.sh, quickmerge.sh: both rebase
# onto origin and re-verify before they push). For those callers this gate is not just
# redundant, it is actively harmful, and the numbers say so
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md):
#
#   run_hygiene_sweep.sh --precommit on ONE staged file  = 118s   (measured 2026-08-10)
#   origin/live-defi-rollout commit inter-arrival        = 60-80s (measured 2026-08-10)
#
# The hook chain is 1.5-2x longer than the gap between commits, so origin ALWAYS moves
# during it and this gate ALWAYS fires -- the caller then re-pays the full 118s sweep on
# the next attempt, which fails for the same structural reason. Six attempts is ~12min of
# hook CPU whose outcome was determined before it started. Blocking pre-commit does not
# even buy freshness: origin can move during the 118s regardless, so the corpus gates were
# evaluated against a moving baseline either way. The wrapper's post-commit rebase is what
# actually enforces "your commit sits on current origin", and it costs seconds.
#
# NOT a blanket relaxation: a bare `git commit` by a human still hard-blocks below (that is
# the case this hook was written for), and the human-only SKIP_BRANCH_DRIFT escape hatch is
# untouched. This flag is scoped to the wrapper's own commit call and unset immediately
# after, so it cannot leak to an unrelated commit in the same shell.
if [[ "${DRIFT_GATE_ADVISORY:-0}" = "1" ]]; then
    BRANCH_ADV=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || exit 0)
    [[ -z "$BRANCH_ADV" || "$BRANCH_ADV" = "HEAD" ]] && exit 0
    git fetch origin "$BRANCH_ADV" --quiet 2>/dev/null || exit 0
    BEHIND_ADV=$(git rev-list HEAD.."origin/$BRANCH_ADV" --count 2>/dev/null || echo "0")
    if [ "$BEHIND_ADV" -gt 0 ] 2>/dev/null; then
        echo "  ℹ️  branch drift: ${BEHIND_ADV} commit(s) behind origin/${BRANCH_ADV} — ADVISORY"
        echo "     (a reconciling wrapper is driving this commit and will rebase before pushing)"
    fi
    exit 0
fi

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
