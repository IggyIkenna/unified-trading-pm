#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Pre-commit hook (commit-msg stage): block a raw `git commit` that changes SOURCE files
# without going through the sanctioned ship paths (scripts/quickmerge.sh, which stamps a
# `Quickmerge:` trailer, or scripts/dev/safe-doc-push.sh, which only ever touches non-source
# paths in the first place).
#
# WHY THIS EXISTS (2026-08-09): check_strict_quickmerge.py already enforces this exact rule
# — but only at PRE-PUSH time, on the whole range of commits about to leave the checkout. A
# raw local `git commit` that bypasses quickmerge.sh/safe-doc-push.sh is invisible to that
# gate until push time, so it can sit in a shared checkout for minutes, racing every OTHER
# concurrent session's pulls/rebases/autostashes on the SAME checkout — exactly the class of
# contention this session spent hours chasing tonight (a raw `git commit` retry-loop, built
# to get UNSTUCK from that same contention, was itself an instance of the very problem this
# hook exists to catch earlier). Catching it at COMMIT time instead of PUSH time means the
# bypass never gets a chance to become a live, racing, uncommitted (or freshly-committed but
# unpushed) source of contention in the first place.
#
# SSOT for the underlying rule: scripts/cicd/check_strict_quickmerge.py's `commit_violates()`
# / `_is_source()` / `NONSOURCE_DIR`. Duplicated here (not imported — this is a bash hook, that
# python module is a CLI script, and duplicating a ~2-line extension/dir list is far cheaper
# than plumbing a cross-language import at commit time) — keep the two lists in sync by hand;
# each carries a comment pointing at its sibling.
#
# git passes the commit-message FILE PATH as $1 for a commit-msg stage hook (NOT the message
# text itself) — read it fresh each time, never trust .git/COMMIT_EDITMSG by convention alone.
#
# ROLLOUT: WARN-only by default, mirroring check_strict_quickmerge.py's own
# STRICT_QUICKMERGE_BLOCK precedent (land unblocking, observe real traffic for false
# positives, THEN flip to enforcing — never ship a new fleet-wide commit-blocking gate
# pre-armed). Override: QUICKMERGE_PROVENANCE_BLOCK=1 to enforce.
#
# Install: add to .pre-commit-config.yaml as a local commit-msg-stage hook (see
# check-branch-drift.sh's neighbouring entry for the exact shape), or:
#   ln -sf ../../unified-trading-pm/scripts/hooks/check-quickmerge-provenance.sh .git/hooks/commit-msg

set -euo pipefail

[[ -n "${GITHUB_ACTIONS:-}" || -n "${CI:-}" ]] && exit 0

MSG_FILE="${1:-}"
[[ -n "$MSG_FILE" && -f "$MSG_FILE" ]] || exit 0

# Already carries the trailer (came through quickmerge.sh) -> pass.
grep -q '^Quickmerge:' "$MSG_FILE" && exit 0

# Merge/reconcile commit (git sets MERGE_HEAD before the commit-msg hook runs for one) -> pass;
# a reconciliation commit can only ever fold in already-provenanced history, never originate a
# fresh bypass. Same exemption check_strict_quickmerge.py applies via its own parents-count check.
git rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1 && exit 0

# Bot/automation commits (manifest bumps, release tags) -> pass, mirrors commit_violates()'s
# author-based exemption; there is no commit yet to read %an from at this hook stage, so this
# checks the configured committer identity instead (same signal, available pre-commit).
case "$(git config user.name 2>/dev/null || true)" in
    *"github-actions"*|*"[bot]"*) exit 0 ;;
esac

# SOURCE_EXT / NONSOURCE_DIR — kept byte-identical in spirit to
# scripts/cicd/check_strict_quickmerge.py's SOURCE_EXT=(".py",".ts",".tsx") and
# NONSOURCE_DIR=("scripts/","tests/","test/",".github/"). A staged path counts as "source" iff
# it has a source extension AND lives outside every non-source directory prefix — update BOTH
# copies together if this list ever changes.
_is_source_path() {
    local path="$1"
    case "$path" in
        *.py|*.ts|*.tsx) ;;
        *) return 1 ;;
    esac
    case "$path" in
        scripts/*|tests/*|test/*|.github/*) return 1 ;;
    esac
    return 0
}

SOURCE_TOUCHED=0
while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    if _is_source_path "$f"; then
        SOURCE_TOUCHED=1
        break
    fi
done < <(git diff --cached --name-only 2>/dev/null || true)

[[ "$SOURCE_TOUCHED" -eq 0 ]] && exit 0   # carve-out: no source file staged (docs/plans/scripts/tests fast path)

BLOCK="${QUICKMERGE_PROVENANCE_BLOCK:-0}"
{
    echo ""
    echo "⚠️  This commit changes SOURCE file(s) but carries no 'Quickmerge:' trailer."
    echo "   Direct/raw commits of code are not the sanctioned path here — ship via:"
    echo "     bash scripts/quickmerge.sh \"<msg>\" --agent --files '<paths>'"
    echo "   (docs/plans/scripts/tests-only changes: bash scripts/dev/safe-doc-push.sh instead)"
    if [[ "$BLOCK" = "1" ]]; then
        echo "   BLOCKED."
    else
        echo "   (WARN only for now — set QUICKMERGE_PROVENANCE_BLOCK=1 to enforce.)"
    fi
} >&2

[[ "$BLOCK" = "1" ]] && exit 1
exit 0
