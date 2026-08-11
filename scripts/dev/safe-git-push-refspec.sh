#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# safe-git-push-refspec.sh — refuse a `git push <remote> <local>:<remote>` where the
# local or remote side of the refspec is empty/unset, catching the exact bug class that
# produced `git push origin :live-defi-rollout` (branch deletion) during a commit-tree
# fallback retry loop (round-9 na-eligibility-audit sweep, 2026-08-09).
#
# Incident: plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md
# The primary fix (GitHub ruleset blocking deletion + non-fast-forward on live-defi-rollout
# fleet-wide) is already in place. This script is defense-in-depth — it catches the bug
# BEFORE it reaches `git push`, independent of the remote-side protection.
#
# Sourced (not executed) — defines `safe_git_push()` and `safe_commit_tree_push()` shell
# FUNCTIONS. This is a footgun-guard, not a security boundary: `command git push ...` or
# an absolute path (`/usr/bin/git push ...`) both deliberately bypass it, same as any
# bash wrapper function.
#
# Usage:
#   source scripts/dev/safe-git-push-refspec.sh
#
#   # Direct refspec guard:
#   safe_git_push origin "$COMMIT_SHA" live-defi-rollout
#
#   # Full commit-tree wrapper (builds tree + commit, then guarded push):
#   safe_commit_tree_push origin live-defi-rollout "feat(...): commit message"
#
# BLOCKED (refused with a one-line error + pointer to the incident doc):
#   - Empty/unset local refspec side — would produce `git push origin :<branch>`
#     (branch deletion).
#   - Empty/unset remote refspec side — would produce `git push origin <sha>:`
#     (delete-or-push-to-unqualified-ref, ambiguous and destructive).
#   - Empty/unset remote name.
#   - commit-tree producing an empty SHA (tree write failed, variable unset, etc.).

# ─── safe_git_push ────────────────────────────────────────────────────────────
# Guarded git push: validates that both sides of the refspec are non-empty before
# calling git push. Catches the unset-variable class of bug where
# `git push origin $SHA:$BRANCH` with an empty $SHA resolves to
# `git push origin :$BRANCH` — which DELETES the remote branch.
#
# $1: remote name (e.g. "origin")
# $2: local refspec side (SHA, branch, or tag — the left side of `:`)
# $3: remote refspec side (branch name — the right side of `:`)
# Returns the exit code of git push on success, 1 on guard refusal.
safe_git_push() {
    local remote="$1" local_ref="$2" remote_ref="$3"

    if [ -z "$remote" ]; then
        {
            echo "REFUSED: git push remote name is empty — nothing to push to."
            echo "  safe_git_push <remote> <local-ref> <remote-ref>"
            echo "  See plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md"
        } >&2
        return 1
    fi

    if [ -z "$local_ref" ]; then
        {
            echo "REFUSED: local side of refspec is empty/unset."
            echo "  Would execute: git push $remote :${remote_ref:-<empty>}"
            if [ -n "$remote_ref" ]; then
                echo "  This DELETES the remote branch '$remote_ref'."
            fi
            echo "  The unset-variable bug (commit-tree SHA empty → 'git push origin :<branch>')"
            echo "  is exactly how live-defi-rollout was briefly deleted on 2026-08-09."
            echo "  Fix: verify the variable holding the local ref is set before pushing,"
            echo "  or use safe_commit_tree_push() which validates this for you."
            echo "  See plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md"
            echo "  (deliberate bypass: \`command git push $remote :${remote_ref:-...}\` or"
            echo "  an absolute path to git)."
        } >&2
        return 1
    fi

    if [ -z "$remote_ref" ]; then
        {
            echo "REFUSED: remote side of refspec is empty/unset."
            echo "  Would execute: git push $remote ${local_ref}:"
            echo "  An empty remote refspec is ambiguous (delete or push-to-unqualified-ref)."
            echo "  See plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md"
            echo "  (deliberate bypass: \`command git push $remote ${local_ref}:\` or"
            echo "  an absolute path to git)."
        } >&2
        return 1
    fi

    git push "$remote" "${local_ref}:${remote_ref}"
}

# ─── safe_commit_tree_push ────────────────────────────────────────────────────
# Full commit-tree → guarded push wrapper. Builds a tree from the index (or a
# specified path), creates a commit on top of origin/<branch>, and pushes via
# safe_git_push (which refuses if any step produced an empty SHA).
#
# $1: remote name (e.g. "origin")
# $2: target branch (e.g. "live-defi-rollout")
# $3: commit message
# $4: (optional) path to build the tree from — defaults to "." (entire index)
# Returns the exit code of the final git push on success, non-zero on failure.
# On failure at any step, prints what failed and stops — no partial push.
safe_commit_tree_push() {
    local remote="$1" branch="$2" message="$3" path="${4:-.}"

    if [ -z "$remote" ] || [ -z "$branch" ] || [ -z "$message" ]; then
        {
            echo "REFUSED: missing required argument."
            echo "  Usage: safe_commit_tree_push <remote> <branch> <message> [path]"
            echo "  See plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md"
        } >&2
        return 1
    fi

    # Resolve the parent commit from origin/<branch> — fail loud if we can't.
    local parent
    if ! parent=$(git rev-parse "origin/$branch" 2>/dev/null); then
        echo "FAILED: cannot resolve origin/$branch — is the remote tracking branch available?" >&2
        return 1
    fi

    # Build the tree.
    local tree
    if ! tree=$(git write-tree --prefix="$path" 2>/dev/null); then
        echo "FAILED: git write-tree returned empty or non-zero — index may be dirty or path invalid." >&2
        return 1
    fi
    if [ -z "$tree" ]; then
        echo "FAILED: git write-tree produced an empty SHA — refusing to proceed." >&2
        return 1
    fi

    # Create the commit.
    local commit_sha
    if ! commit_sha=$(git commit-tree "$tree" -p "$parent" -m "$message" 2>/dev/null); then
        echo "FAILED: git commit-tree returned non-zero." >&2
        return 1
    fi
    if [ -z "$commit_sha" ]; then
        echo "FAILED: git commit-tree produced an empty SHA (unset variable, pipe failure, or"
        echo "  commit-tree exited 0 but wrote nothing to stdout). This is the exact bug that"
        echo "  produced 'git push origin :live-defi-rollout' on 2026-08-09 — refusing to push." >&2
        return 1
    fi

    # Guarded push — safe_git_push refuses if commit_sha or branch is empty.
    safe_git_push "$remote" "$commit_sha" "$branch"
}
