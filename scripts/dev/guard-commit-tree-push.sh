#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# guard-commit-tree-push.sh -- refuse a push whose refspec local side is empty/unset.
#
# THE HOLE THIS CLOSES (incident 2026-08-09, live_defi_rollout_branch_has_no_delete_protection).
# The shared-checkout write-contention fallback builds a commit with `git commit-tree` against
# origin's HEAD directly, then pushes it with `git push origin <sha>:<branch>`. A bug in that
# fallback -- an unset commit-message variable producing an empty SHA -- turned the refspec into
# `git push origin :live-defi-rollout`: an EMPTY local side in a refspec is a remote-branch
# DELETION, silently destructive on the shared integration branch every slot pulls against. The
# branch was restored to its exact prior tip the same turn only because the same agent caught it
# in-process; GitHub rulesets (`protect-live-defi-rollout`: deletion + non_fast_forward) are the
# layer-1 backstop added by todos 1-2 of that issue. This guard is layer-2: it catches the empty
# refspec BEFORE it reaches `git push`, so the two fixes address different layers (defense in
# depth), independent of the rulesets.
#
# WHAT IT DOES. Replaces the bare `git push` in the commit-tree fallback with:
#
#   bash scripts/dev/guard-commit-tree-push.sh <remote> '<sha>:<branch>' [extra git push args...]
#
# It validates the refspec, then `exec git push` with the SAME arguments (never adds/removes
# args). It exits 1 BEFORE running anything when:
#   - fewer than 2 arguments (missing remote or refspec)
#   - the refspec has no ':' (the fallback always uses '<sha>:<branch>')
#   - either side of the refspec is empty/unset (' :<branch>' is a deletion; '<sha>:' is not the
#     fallback contract)
#   - the local side does not resolve to a git object/ref (catches an unset-but-nonempty or
#     typo'd SHA that git itself would otherwise reject only after connecting to the remote)
#
# SCOPE. This guard is for the commit-tree FALLBACK pattern only. A deliberate
# `git push origin :<branch>` (intentionally deleting a remote branch) is a different, planned
# operation and must NOT be routed through this wrapper -- keep it out of promote/backmerge
# workflows that delete refs on purpose.
#
# SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Commit-tree fallback push guard".
set -uo pipefail

die() { echo "guard-commit-tree-push: ERROR: $*" >&2; exit 1; }

[ $# -ge 2 ] || die "usage: guard-commit-tree-push.sh <remote> '<sha>:<branch>' [extra git push args...]"

REMOTE="$1"
REFSPEC="$2"
shift 2

case "$REFSPEC" in
  *:*) ;;                    # has both sides -- proceed
  *)
    die "refspec '$REFSPEC' has no ':' -- the commit-tree fallback always pushes '<sha>:<branch>'; got a bare '$REFSPEC'"
    ;;
esac

LOCAL="${REFSPEC%%:*}"
REMOTE_REF="${REFSPEC#*:}"

# Empty local side == deletion (`:branch`). This is the exact incident bug.
if [ -z "$LOCAL" ]; then
  die "refspec '$REFSPEC' has an EMPTY local side -- this is 'git push origin :$REMOTE_REF', a remote-branch DELETION. An unset/empty SHA produced exactly this in the 2026-08-09 live-defi-rollout incident. Refusing."
fi

# Empty remote side is not a deletion, but the fallback contract is always '<sha>:<branch>'.
if [ -z "$REMOTE_REF" ]; then
  die "refspec '$REFSPEC' has an empty remote side -- the commit-tree fallback always names the target branch explicitly ('<sha>:<branch>')"
fi

# The local side must resolve to a real commit object. The commit-tree fallback always pushes a
# commit, so peel to ^{commit} -- this binds harder than a bare `rev-parse --verify`, which
# treats ANY 40-hex string as a plausible object id and resolves bogus/nonexistent SHAs
# (measured: `rev-parse --verify deadbeef0…` exits 0 in a repo where that object does not
# exist; `deadbeef0…^{commit}` exits 1). Catches an unset-but-nonempty or typo'd SHA BEFORE git
# contacts the remote, keeping the guard independent of network/repo state.
if ! git rev-parse --verify --quiet "${LOCAL}^{commit}" >/dev/null 2>&1; then
  die "refspec local side '$LOCAL' does not resolve to a real commit object -- refusing to push (a commit-tree SHA, HEAD, or branch name is expected)"
fi

echo "guard-commit-tree-push: OK -- pushing <${LOCAL}:${REMOTE_REF}> to remote '$REMOTE'"
exec git push "$REMOTE" "$REFSPEC" "$@"
