#!/usr/bin/env bats
# test_quickmerge_isolated_branch_collision.bats — unit tests for the isolated-mode
#   branch-collision fix in scripts/quickmerge.sh
#   (ao_cli_assumes_200k_window_for_deepseek_2026_08_10.md, [SCRIPT] P2).
#
# The bug: quickmerge's isolated worktree is created `--detach` on purpose, but the shared
# branch-selection stage then ran `git checkout "$BRANCH"` INSIDE it. Git refuses to check out a
# branch another worktree already holds:
#     fatal: 'live-defi-rollout' is already used by worktree at '<main clone>'
# Since every agent ships to that one branch, isolated mode could never complete a ship — callers
# fell back to --no-isolated, which is exactly the shared-checkout mode where a peer's pull/rebase
# cycle can revert your working tree mid-ship.
#
# The fix mirrors safe-doc-push.sh, which has always been immune: stay detached, and push an
# explicit refspec (`HEAD:refs/heads/$BRANCH`) instead of `-u origin $BRANCH`.
#
# Replicates the helper's exact logic (not fragile against line-number changes in quickmerge.sh —
# mirrors the established pattern in test_quickmerge_stage5_no_regression_guard.bats), exercised
# against REAL local git repos (hermetic: no network, no GitHub — an "origin" is a second local repo).
#
# Run: bats tests/test_quickmerge_isolated_branch_collision.bats

# ── helper: replicated verbatim from quickmerge.sh ────────────────────────────

# Args: $1=repo dir  $2=BRANCH  $3=QM_IN_ISOLATION ("" or "1")
_run_checkout_ship_branch() {
    local repo_dir="$1" branch="$2" in_isolation="$3"
    (
        cd "$repo_dir" || exit 2
        REPO_NAME="test-repo"
        BRANCH="$branch"
        QM_IN_ISOLATION="$in_isolation"
        if [ -n "${QM_IN_ISOLATION:-}" ]; then
            echo "[$REPO_NAME] isolation: staying on detached HEAD (the shared clone holds $BRANCH); will push HEAD:$BRANCH"
            exit 0
        fi
        if git show-ref --verify --quiet "refs/heads/$BRANCH" 2>/dev/null; then
            git checkout "$BRANCH" --quiet
        elif git show-ref --verify --quiet "refs/remotes/origin/$BRANCH" 2>/dev/null; then
            git checkout -B "$BRANCH" "origin/$BRANCH" --quiet
        else
            git checkout -b "$BRANCH" origin/main --quiet 2>/dev/null || git checkout "$BRANCH" --quiet
        fi
    )
}

# ── fixtures ─────────────────────────────────────────────────────────────────

BRANCH_UNDER_TEST="live-defi-rollout"

setup() {
    TEST_ROOT="$(mktemp -d)"
    export TEST_ROOT

    # A bare "origin" so pushes are real, with no network.
    git init --bare -q "$TEST_ROOT/origin.git"

    # The main clone, checked out ON the shared branch — this is what holds the branch and
    # makes a second worktree's `git checkout $BRANCH` fatal.
    git clone -q "$TEST_ROOT/origin.git" "$TEST_ROOT/main-clone"
    cd "$TEST_ROOT/main-clone" || return 1
    git config user.email "test@example.com"
    git config user.name "test"
    echo "seed" > seed.txt
    git add seed.txt
    git commit -qm "seed"
    git branch -M "$BRANCH_UNDER_TEST"
    git push -q -u origin "$BRANCH_UNDER_TEST"

    # The isolated worktree, created --detach exactly as quickmerge does.
    git worktree add --detach -q "$TEST_ROOT/iso-wt" HEAD
}

teardown() {
    [ -n "$TEST_ROOT" ] && rm -rf "$TEST_ROOT"
}

# ── the bug this fix exists for ──────────────────────────────────────────────

@test "the collision is real: a detached worktree cannot check out a branch the main clone holds" {
    run git -C "$TEST_ROOT/iso-wt" checkout "$BRANCH_UNDER_TEST"
    [ "$status" -ne 0 ]
    [[ "$output" == *"already used by worktree"* ]]
}

# ── the fix ──────────────────────────────────────────────────────────────────

@test "in isolation the helper stays detached and succeeds instead of dying on the collision" {
    run _run_checkout_ship_branch "$TEST_ROOT/iso-wt" "$BRANCH_UNDER_TEST" "1"
    [ "$status" -eq 0 ]
    [[ "$output" == *"staying on detached HEAD"* ]]

    # Still detached — `symbolic-ref HEAD` fails on a detached HEAD.
    run git -C "$TEST_ROOT/iso-wt" symbolic-ref -q HEAD
    [ "$status" -ne 0 ]
}

@test "outside isolation the helper still checks the branch out normally" {
    run _run_checkout_ship_branch "$TEST_ROOT/main-clone" "$BRANCH_UNDER_TEST" ""
    [ "$status" -eq 0 ]

    run git -C "$TEST_ROOT/main-clone" rev-parse --abbrev-ref HEAD
    [ "$status" -eq 0 ]
    [ "$output" = "$BRANCH_UNDER_TEST" ]
}

@test "an explicit refspec pushes a detached-HEAD commit onto the shared branch" {
    cd "$TEST_ROOT/iso-wt" || return 1
    git config user.email "test@example.com"
    git config user.name "test"
    echo "shipped from isolation" > shipped.txt
    git add shipped.txt
    git commit -qm "fix: shipped from a detached isolated worktree"
    local iso_sha
    iso_sha="$(git rev-parse HEAD)"

    run git push origin "HEAD:refs/heads/$BRANCH_UNDER_TEST" --quiet
    [ "$status" -eq 0 ]

    # The commit is genuinely on the branch in origin — the claim quickmerge makes after push.
    run git -C "$TEST_ROOT/origin.git" merge-base --is-ancestor "$iso_sha" "refs/heads/$BRANCH_UNDER_TEST"
    [ "$status" -eq 0 ]
}

@test "the pre-fix push form would NOT have shipped the detached commit" {
    cd "$TEST_ROOT/iso-wt" || return 1
    git config user.email "test@example.com"
    git config user.name "test"
    echo "not shipped" > stray.txt
    git add stray.txt
    git commit -qm "fix: a commit that -u origin BRANCH would silently leave behind"
    local iso_sha
    iso_sha="$(git rev-parse HEAD)"

    # `git push -u origin <branch>` from a detached HEAD pushes the shared clone's stale
    # refs/heads/<branch>, NOT the commit just made here. It can even exit 0 having shipped
    # nothing of ours — which is why the refspec form is required.
    git push -u origin "$BRANCH_UNDER_TEST" --quiet 2>/dev/null || true

    run git -C "$TEST_ROOT/origin.git" merge-base --is-ancestor "$iso_sha" "refs/heads/$BRANCH_UNDER_TEST"
    [ "$status" -ne 0 ]
}
