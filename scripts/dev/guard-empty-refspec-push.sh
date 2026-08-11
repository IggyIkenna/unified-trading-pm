#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# guard-empty-refspec-push.sh — refuse git push with an empty local refspec
#
# Lifecycle: permanent — defense-in-depth guard against the bug class that caused
# the live-defi-rollout near-miss deletion incident (2026-08-09, issue doc:
# /plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md).
#
# The git commit-tree fallback pattern (used for shared-checkout contention
# recovery) constructs commits via `git commit-tree` and pushes them with:
#   git push origin "$SHA:refs/heads/<branch>"
# A bug where the SHA variable is unset produces:
#   git push origin :refs/heads/<branch>  — which DELETES the remote branch.
#
# This wrapper scans every refspec argument and refuses the push if any refspec
# has an empty source (left) side. It is a defense-in-depth layer — the GitHub
# ruleset protecting live-defi-rollout (id 20616931) blocks the actual deletion at
# the server side, but this guard catches the bug BEFORE it reaches the network.
#
# Usage:
#   bash scripts/dev/guard-empty-refspec-push.sh origin <sha>:refs/heads/<branch>
#   bash scripts/dev/guard-empty-refspec-push.sh origin <sha>:<branch> <tag>
#
# This is NOT a replacement for git push — it only adds the empty-refspec check.
# All valid pushes pass through to `git push` unchanged.
# ──────────────────────────────────────────────────────────────────────────────
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: never — defense-in-depth guard, no expiration

set -euo pipefail

found_empty=false

for arg in "$@"; do
    # Skip flags (arguments starting with -) — they are never refspecs.
    if [[ "$arg" == -* ]]; then
        continue
    fi
    # A refspec contains ':' (source:destination).
    # Check that the source (left of the first ':') is non-empty.
    if [[ "$arg" == *:* ]]; then
        left="${arg%%:*}"
        if [[ -z "$left" ]]; then
            echo "guard-empty-refspec-push: REFUSING push — empty source in refspec '$arg'" >&2
            echo "  An empty left side of a refspec DELETES the remote ref." >&2
            echo "  This is the exact bug that caused the 2026-08-09 live-defi-rollout" >&2
            echo "  near-miss deletion incident (unset variable → empty refspec)." >&2
            echo "  If you genuinely intend to delete a remote ref, use the explicit form:" >&2
            echo "    git push --delete <remote> <branch>" >&2
            echo "  or set ALLOW_EMPTY_REFSPEC_PUSH=1 to bypass this guard." >&2
            found_empty=true
        fi
    fi
done

if $found_empty; then
    exit 1
fi

# All refspecs validated — delegate to the real git push.
exec git push "$@"
