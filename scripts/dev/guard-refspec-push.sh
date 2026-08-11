#!/usr/bin/env bash
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
#
# guard-refspec-push.sh — refuse a git push whose refspec's LOCAL side is empty/unset.
#
# WHY: the `git commit-tree` fallback for shared-checkout contention pushes by sha —
#   `git push origin "<sha>:<branch>"`. A retry-loop bug that leaves <sha> empty turns
#   that into `git push origin ":<branch>"`, which git interprets as a DELETE and removes
#   the remote branch. That exact bug briefly force-deleted live-defi-rollout during the
#   round-9 sweep (self-caught same-turn, no data lost) — see
#   plans/active/issues/live_defi_rollout_branch_has_no_delete_protection_2026_08_09.md.
#   This guard fails BEFORE `git push` runs; the protect-live-defi-rollout GitHub ruleset
#   (deletion + non_fast_forward) is the server-side second layer (defense in depth).
#
# Usage:
#   bash guard-refspec-push.sh --check <refspec> [<refspec>...]   # validate only; exit 0/1
#   bash guard-refspec-push.sh <remote> <refspec> [<refspec>...]  # validate, then exec git push
#
#   Any refspec with an empty/unset local side (":<branch>", ":", empty) is REFUSED with
#   exit 1 and nothing is executed — including an explicit `--delete`/`-d`.
#
# Commit-tree fallback usage (the shared-checkout contention recovery path):
#   NEW_COMMIT="$(git commit-tree "$NEW_TREE" -p <base> -m "$MSG")"
#   bash scripts/dev/guard-refspec-push.sh origin "$NEW_COMMIT:live-defi-rollout"
#   # if $NEW_COMMIT is empty/unset → guard exits 1, no push, remote branch untouched.

set -uo pipefail

_check_only=0
if [ "${1:-}" = "--check" ]; then
    _check_only=1
    shift
fi

if [ "$#" -eq 0 ]; then
    echo "guard-refspec-push: no refspec(s) given." >&2
    exit 2
fi

if [ "$_check_only" -eq 0 ]; then
    if [ "$#" -lt 2 ]; then
        echo "guard-refspec-push: exec mode needs <remote> then <refspec>... — got: $*" >&2
        exit 2
    fi
    _remote="$1"
    shift
fi

# $1 = one refspec. Returns 0 if it is the empty-local/delete form, 1 if safe.
_refspec_is_delete() {
    local body="${1#+}"   # strip a leading '+' force marker (force is a separate concern)
    if [[ "$body" == *:* ]]; then
        local local_side="${body%%:*}"
        [ -n "$local_side" ] && return 1
        return 0   # ":<dst>" — empty local side == branch delete
    fi
    [ -z "$body" ] && return 0
    return 1
}

for _arg in "$@"; do
    if [ "$_arg" = "--delete" ] || [ "$_arg" = "-d" ]; then
        echo "guard-refspec-push: REFUSED explicit branch deletion ('$_arg'). Nothing pushed." >&2
        exit 1
    fi
    # Skip git-push option flags (e.g. --force, --tags); they carry no local-side refspec.
    if [[ "$_arg" == -* ]]; then
        continue
    fi
    if _refspec_is_delete "$_arg"; then
        echo "guard-refspec-push: REFUSED refspec '$_arg' — empty/unset local side means DELETE, not push." >&2
        echo "  (Did a variable expand empty, e.g. \"\$SHA:branch\" -> \":branch\"? That is the exact" >&2
        echo "  round-9 near-miss that deleted live-defi-rollout. The GitHub ruleset blocks it too, but" >&2
        echo "  this guard stops it before git push runs.)" >&2
        exit 1
    fi
done

if [ "$_check_only" -eq 1 ]; then
    echo "guard-refspec-push: OK — all refspecs have a non-empty local side." >&2
    exit 0
fi

exec git push "$_remote" "$@"
