#!/usr/bin/env bats
# test_safe_doc_push_isolated_deletion_propagates.bats — the isolated copy loop must propagate a
#   DELETION, not silently skip it.
#
# The bug (measured 2026-08-10): safe-doc-push's isolated copy loop skipped any named path absent
# from the caller tree ('[[ ! -f $_f ]] -> continue'). A file deleted by `git mv` IS absent, so an
# archival move landed its ADD and silently dropped its DELETE — and the push still reported
# success. A resolved issue was left sitting in plans/active/ beside its archived copy, where the
# orchestrator would have kept dispatching it. Archiving a completed plan is a mandated routine
# operation, so this misfired quietly every time anyone did it from isolated mode.
#
# The distinction that makes the fix safe: absent-and-tracked-on-origin is a DELETION; absent-and-
# untracked is a caller typo, and must still warn rather than silently do nothing.
#
# Replicates the loop's exact decision (mirrors the established pattern in
# test_quickmerge_stage5_no_regression_guard.bats), exercised against REAL local git repos
# (hermetic: no network — an "origin" is just a second local repo).
#
# Run: bats tests/test_safe_doc_push_isolated_deletion_propagates.bats

# ── helper: the loop's decision, replicated verbatim from safe-doc-push.sh ─────

# Args: $1=caller repo dir  $2=worktree dir  $3=BRANCH  $4=path
# Echoes the branch taken: "deleted" | "copied" | "skipped".
_run_iso_copy_decision() {
    local caller="$1" wt="$2" branch="$3" f="$4"
    (
        cd "$caller" || exit 2
        if [[ ! -f "$f" ]]; then
            if git rev-parse -q --verify "origin/${branch}:${f}" >/dev/null 2>&1; then
                rm -f -- "$wt/$f"
                echo "deleted"
                exit 0
            fi
            echo "skipped"
            exit 0
        fi
        mkdir -p "$wt/$(dirname "$f")" 2>/dev/null || true
        cp "$f" "$wt/$f"
        echo "copied"
    )
}

setup() {
    TEST_ROOT="$(mktemp -d)"
    export TEST_ROOT
    BRANCH="live-defi-rollout"

    git init --bare -q "$TEST_ROOT/origin.git"
    git clone -q "$TEST_ROOT/origin.git" "$TEST_ROOT/caller"
    cd "$TEST_ROOT/caller" || return 1
    git config user.email "test@example.com"
    git config user.name "test"
    mkdir -p plans/active/issues
    echo "an issue" > plans/active/issues/thing.md
    echo "seed" > seed.txt
    git add -A
    git commit -qm "seed"
    git branch -M "$BRANCH"
    git push -q -u origin "$BRANCH"

    # The isolated worktree, detached at origin/$BRANCH exactly as safe-doc-push creates it.
    git worktree add --detach -q "$TEST_ROOT/wt" "origin/$BRANCH"
}

teardown() {
    [ -n "$TEST_ROOT" ] && rm -rf "$TEST_ROOT"
}

@test "a path deleted in the caller but tracked on origin propagates as a deletion" {
    cd "$TEST_ROOT/caller" || return 1
    git rm -q plans/active/issues/thing.md

    run _run_iso_copy_decision "$TEST_ROOT/caller" "$TEST_ROOT/wt" "$BRANCH" "plans/active/issues/thing.md"
    [ "$status" -eq 0 ]
    [ "$output" = "deleted" ]

    # Gone from the worktree, so `git add -- <path>` there stages a real deletion.
    [ ! -f "$TEST_ROOT/wt/plans/active/issues/thing.md" ]
    run git -C "$TEST_ROOT/wt" add -- plans/active/issues/thing.md
    [ "$status" -eq 0 ]
    run git -C "$TEST_ROOT/wt" diff --cached --name-status
    [[ "$output" == D*"plans/active/issues/thing.md" ]]
}

@test "a path absent AND untracked is still a caller typo, not a deletion" {
    run _run_iso_copy_decision "$TEST_ROOT/caller" "$TEST_ROOT/wt" "$BRANCH" "plans/active/issues/never_existed.md"
    [ "$status" -eq 0 ]
    [ "$output" = "skipped" ]
}

@test "an ordinary present file is still copied, not touched by the deletion path" {
    cd "$TEST_ROOT/caller" || return 1
    echo "edited" > plans/active/issues/thing.md

    run _run_iso_copy_decision "$TEST_ROOT/caller" "$TEST_ROOT/wt" "$BRANCH" "plans/active/issues/thing.md"
    [ "$status" -eq 0 ]
    [ "$output" = "copied" ]
    run cat "$TEST_ROOT/wt/plans/active/issues/thing.md"
    [ "$output" = "edited" ]
}

@test "the pre-fix loop would have dropped the deletion entirely" {
    cd "$TEST_ROOT/caller" || return 1
    git rm -q plans/active/issues/thing.md

    # Pre-fix behaviour: absent -> skip, unconditionally.
    if [[ ! -f "plans/active/issues/thing.md" ]]; then :; fi

    # The worktree copy survives, so the commit carries no deletion and the file stays on the
    # branch -- while the push still reports success. That is the silent half-completed move.
    [ -f "$TEST_ROOT/wt/plans/active/issues/thing.md" ]
    run git -C "$TEST_ROOT/wt" diff --cached --name-status
    [ -z "$output" ]
}
