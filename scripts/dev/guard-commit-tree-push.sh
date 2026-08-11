#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# guard-commit-tree-push.sh -- refuse a `git push` whose refspec local side is empty/unset,
# catching the `git push origin :<branch>` remote-branch-DELETE bug class before it reaches git.
#
# THE INCIDENT THIS GUARDS (2026-08-09, round-9 satellite-extraction). Under shared-checkout
# write contention an agent built commits via `git commit-tree` against origin's HEAD directly
# (the workaround for a contended shared index), then pushed with
# `git push origin "$SHA:live-defi-rollout"`. A bug in its retry loop left `$SHA` unset, so the
# refspec became `:live-defi-rollout` -- an empty local side, which git interprets as
# DELETE the remote branch. The agent caught it in the same turn via `git ls-remote` and
# restored the exact prior tip; no data was lost. But nothing at the client layer structurally
# prevented it. Server-side rulesets now block deletion of live-defi-rollout on every repo
# (issue `live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md`), but that protects
# ONE named branch -- an empty-refspec push of ANY branch is the same bug. This script is the
# client-layer defense: it refuses the push when the local side is empty/unset, so the bug
# dies here instead of reaching `git push`.
#
# USAGE (the hardened commit-tree fallback -- replace the raw `git push` line with this):
#   TREE=$(git rev-parse 'HEAD^{tree}')
#   PARENT=$(git rev-parse origin/live-defi-rollout)
#   SHA=$(git commit-tree "$TREE" -p "$PARENT" -m "$MSG")
#   bash scripts/dev/guard-commit-tree-push.sh origin "$SHA:live-defi-rollout"
#
# Extra args after the refspec pass through to git (e.g. --dry-run).
#
# Exit codes: 0 = push executed; 1 = git rejected the push (normal git failure); 2 = refspec
# rejected by THIS guard (empty/unset or non-refspec argument) -- nothing was pushed.

set -uo pipefail

REMOTE="${1:-origin}"
REFSPEC="${2:-}"
shift 2 2>/dev/null || true

# Refuse BEFORE git: an empty refspec, or one whose local side is empty (`:branch`), is a
# remote-branch DELETE -- exactly the unset-variable bug class this guard exists to stop.
case "$REFSPEC" in
  "" | :*)
    echo "guard-commit-tree-push: REFUSED -- refspec '${REFSPEC}' has an empty/unset local side." >&2
    echo "  git push origin ':${REFSPEC#:}' would DELETE the remote branch." >&2
    echo "  In the commit-tree fallback this is the unset-\$SHA bug. Provide an explicit" >&2
    echo "  '<sha>:<branch>' refspec, e.g.  bash scripts/dev/guard-commit-tree-push.sh origin \"<sha>:live-defi-rollout\"." >&2
    exit 2
    ;;
esac

# The commit-tree fallback always pushes an explicit '<local>:<remote>' refspec -- a bare name
# (no colon) is a shortcut this wrapper should never silently expand.
case "$REFSPEC" in
  *:*) ;;
  *)
    echo "guard-commit-tree-push: REFUSED -- refspec '${REFSPEC}' has no '<local>:<remote>' form." >&2
    echo "  The commit-tree fallback requires an explicit refspec; use '<sha>:<branch>'." >&2
    exit 2
    ;;
esac

exec git push "$REMOTE" "$REFSPEC" "$@"
