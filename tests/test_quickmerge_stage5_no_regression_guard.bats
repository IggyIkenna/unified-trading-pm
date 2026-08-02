#!/usr/bin/env bats
# test_quickmerge_stage5_no_regression_guard.bats — unit tests for the STAGE 5
#   no-regression guard in scripts/quickmerge.sh
#   (quickmerge_agent_regate_resets_branch_loses_local_commit_2026_07_31.md).
#
# The guard fires when STAGE 5's branch-selection block (`checkout -B $BRANCH
# origin/$BRANCH` in its `elif` arm) lands somewhere that no longer contains the
# QG-certified commit captured just before STAGE 4 (_QM_PRE_STAGE5_HEAD /
# _QM_PRE_STAGE5_BRANCH) — it preserves the lost commit to a
# refs/wip-preserve/quickmerge-stage5-regate-<sha12> ref and hard-fails instead of
# silently proceeding to push.
#
# Replicates the guard's exact conditional (not fragile against line-number
# changes in quickmerge.sh — mirrors the tier-gate bats file's established
# pattern), exercised against REAL local git repos (hermetic: no network, no
# GitHub — an "origin" is just a second local repo).
#
# Run: bats tests/test_quickmerge_stage5_no_regression_guard.bats

# ── helper: the guard logic, replicated verbatim from quickmerge.sh ────────────

# Args: $1=repo dir (already checked out on the branch under test)
#       $2=_QM_PRE_STAGE5_HEAD  $3=_QM_PRE_STAGE5_BRANCH  $4=BRANCH (post-checkout)
# Echoes the preserve ref name on regression detection; exit 1. Exit 0 (silent) otherwise.
_run_stage5_no_regression_guard() {
    local repo_dir="$1" pre_head="$2" pre_branch="$3" branch="$4"
    (
        cd "$repo_dir" || exit 2
        if [ -n "$pre_head" ] && [ "$branch" = "$pre_branch" ] \
           && ! git merge-base --is-ancestor "$pre_head" HEAD 2>/dev/null; then
            preserve_ref="refs/wip-preserve/quickmerge-stage5-regate-${pre_head:0:12}"
            git update-ref "$preserve_ref" "$pre_head" 2>/dev/null || true
            echo "$preserve_ref"
            exit 1
        fi
        exit 0
    )
}

# ── fixtures ─────────────────────────────────────────────────────────────────

# Bare "origin" + a working clone, both under BATS_TEST_TMPDIR. Returns the
# working clone's path (origin lives alongside it, same tmpdir).
_make_fixture_repo() {
    local origin="${BATS_TEST_TMPDIR}/origin_$$_${RANDOM}.git"
    local work="${BATS_TEST_TMPDIR}/work_$$_${RANDOM}"
    git init --bare -q "$origin"
    git clone -q "$origin" "$work"
    (
        cd "$work" || exit 1
        git config user.email "test@example.com"
        git config user.name "Test"
        git checkout -q -b live-defi-rollout
        echo "base" > file.txt
        git add file.txt
        git commit -q -m "base commit"
        git push -q origin live-defi-rollout
    )
    echo "$work"
}

# ── tests ────────────────────────────────────────────────────────────────────

@test "quickmerge.sh has valid bash syntax after the STAGE 5 guard addition" {
    run bash -n "$(dirname "$BATS_TEST_DIRNAME")/scripts/quickmerge.sh"
    [ "$status" -eq 0 ]
}

@test "STAGE 5 no-regression guard block is present in quickmerge.sh" {
    run grep -c "STAGE5_REGATE\|No-regression guard" \
        "$(dirname "$BATS_TEST_DIRNAME")/scripts/quickmerge.sh"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "guard FIRES when checkout -B resets the same-named branch away from the certified commit" {
    work="$(_make_fixture_repo)"
    (
        cd "$work" || exit 1
        # The QG-certified commit: a real local commit ahead of origin.
        echo "certified change" > new.txt
        git add new.txt
        git commit -q -m "certified work"
    )
    pre_head="$(cd "$work" && git rev-parse HEAD)"
    pre_branch="live-defi-rollout"

    # Reproduce the exact destructive call: checkout -B <branch> origin/<branch>.
    (cd "$work" && git checkout -B live-defi-rollout origin/live-defi-rollout --quiet)
    post_branch="$(cd "$work" && git branch --show-current)"

    run _run_stage5_no_regression_guard "$work" "$pre_head" "$pre_branch" "$post_branch"
    [ "$status" -eq 1 ]
    [[ "$output" == *"refs/wip-preserve/quickmerge-stage5-regate-${pre_head:0:12}"* ]]

    # The certified commit must be durably recoverable via the preserve ref.
    run bash -c "cd '$work' && git rev-parse '$output'"
    [ "$status" -eq 0 ]
    [ "$output" = "$pre_head" ]
}

@test "guard is SILENT when the branch still contains the certified commit (plain checkout, no reset)" {
    work="$(_make_fixture_repo)"
    (
        cd "$work" || exit 1
        echo "certified change" > new.txt
        git add new.txt
        git commit -q -m "certified work"
    )
    pre_head="$(cd "$work" && git rev-parse HEAD)"
    pre_branch="live-defi-rollout"

    # The SAFE path: refs/heads/$BRANCH already exists -> plain checkout, no -B.
    (cd "$work" && git checkout -q live-defi-rollout)
    post_branch="$(cd "$work" && git branch --show-current)"

    run _run_stage5_no_regression_guard "$work" "$pre_head" "$pre_branch" "$post_branch"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "guard is SILENT on a genuinely new PR branch (different branch name, no regression)" {
    work="$(_make_fixture_repo)"
    (
        cd "$work" || exit 1
        echo "certified change" > new.txt
        git add new.txt
        git commit -q -m "certified work"
    )
    pre_head="$(cd "$work" && git rev-parse HEAD)"
    pre_branch="live-defi-rollout"

    # A genuinely new auto-generated PR branch off origin/main -- not the same
    # branch we snapshotted, so its not containing pre_head is expected, not a bug.
    (cd "$work" && git checkout -q -b "auto/20260731-000000-1" live-defi-rollout)
    # Simulate it being freshly created off a DIFFERENT base than pre_head by
    # resetting to the origin tip (pre-certified-commit state) -- mirrors
    # "git checkout -b BRANCH origin/main" landing before the certified commit existed.
    (cd "$work" && git reset -q --hard origin/live-defi-rollout)
    post_branch="$(cd "$work" && git branch --show-current)"

    run _run_stage5_no_regression_guard "$work" "$pre_head" "$pre_branch" "$post_branch"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "guard is SILENT when pre_head is empty (nothing captured, e.g. detached HEAD at snapshot time)" {
    work="$(_make_fixture_repo)"
    run _run_stage5_no_regression_guard "$work" "" "live-defi-rollout" "live-defi-rollout"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}
