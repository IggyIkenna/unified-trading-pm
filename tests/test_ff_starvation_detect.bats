#!/usr/bin/env bats
# test_ff_starvation_detect.bats — unit tests for ff-starvation-detect.sh
#   (Item 5b of workspace_config_drift_remediation_2026_06_01).
#
# HERMETIC: builds throwaway git repos under BATS_TEST_TMPDIR; never touches real
# worktrees in $WORKSPACE_ROOT. Mirrors tests/test_tab_worktrees.bats structure.
#
# Run: bats tests/test_ff_starvation_detect.bats
# Run all: bats tests/

DETECT="unified-trading-pm/scripts/dev/ff-starvation-detect.sh"
REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

# Resolve paths relative to the workspace root, so this test passes whether
# invoked from PM root or workspace root.
setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    DETECT_ABS="$(cd "$(dirname "${DETECT}")" && pwd)/$(basename "${DETECT}")"
}

# Build a local repo that is exactly 1 commit BEHIND origin/live-defi-rollout,
# where the single incoming commit modified `shared.txt`. Echoes the repo path.
# After this helper the working tree is CLEAN at the behind-by-1 state.
_make_behind_repo() {
    local root="${BATS_TEST_TMPDIR}/repo_$$_${RANDOM}"
    mkdir -p "${root}"
    git init -q --bare "${root}/remote.git"
    git init -q "${root}/local"
    (
        cd "${root}/local"
        git config user.email t@t.t
        git config user.name t
        git remote add origin ../remote.git
        printf 'v1\n' > shared.txt
        printf 'other\n' > other.txt
        git add -A && git commit -qm init
        git push -q origin HEAD:live-defi-rollout
        printf 'v2-remote\n' > shared.txt
        git add shared.txt && git commit -qm "remote change shared"
        git push -q origin HEAD:live-defi-rollout
        git reset -q --hard HEAD~1          # local now 1 behind
        git fetch -q origin live-defi-rollout
    )
    echo "${root}/local"
}

# ── Bash syntax + help text ───────────────────────────────────────────────────

@test "ff-starvation-detect.sh has valid bash syntax" {
    run bash -n "$DETECT"
    [ "$status" -eq 0 ]
}

@test "slot-git-status-report.sh has valid bash syntax" {
    run bash -n "$REPORTER"
    [ "$status" -eq 0 ]
}

@test "ff-starvation-detect.sh --help renders" {
    run bash "$DETECT" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"ff-starvation-detect.sh"* ]]
    [[ "$output" == *"STARVED"* ]]
}

# ── Argument validation ───────────────────────────────────────────────────────

@test "ff-starvation-detect.sh requires a repo dir" {
    run bash "$DETECT"
    [ "$status" -eq 2 ]
    [[ "$output" == *"usage"* ]]
}

@test "ff-starvation-detect.sh rejects a non-git dir" {
    run bash "$DETECT" "${BATS_TEST_TMPDIR}"
    [ "$status" -eq 2 ]
    [[ "$output" == *"not a git worktree"* ]]
}

# ── Core detection rule ───────────────────────────────────────────────────────

@test "collision (dirty file collides with incoming) → STARVATION signal" {
    repo="$(_make_behind_repo)"
    printf 'dirty-edit\n' > "${repo}/shared.txt"   # collides with the incoming change
    run env FF_STARVE_COMMIT_THRESHOLD=1 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [[ "$output" == *"FF-PULL STARVATION"* ]]
    [[ "$output" == *"shared.txt"* ]]
    [[ "$output" == *"slot 6"* ]]
}

@test "non-colliding dirty file → NO signal" {
    repo="$(_make_behind_repo)"
    printf 'dirty-other\n' > "${repo}/other.txt"   # NOT in the incoming change set
    run env FF_STARVE_COMMIT_THRESHOLD=1 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "collision below behind+age threshold → NO signal" {
    repo="$(_make_behind_repo)"
    printf 'dirty-edit\n' > "${repo}/shared.txt"    # collides, but behind=1 < threshold=5
    run env FF_STARVE_COMMIT_THRESHOLD=5 FF_STARVE_AGE_HOURS=999 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "clean worktree behind remote → NO signal (FF would succeed)" {
    repo="$(_make_behind_repo)"                      # left clean by the helper
    run env FF_STARVE_COMMIT_THRESHOLD=1 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "up-to-date worktree → NO signal" {
    repo="$(_make_behind_repo)"
    ( cd "${repo}" && git merge -q --ff-only origin/live-defi-rollout )   # now 0 behind
    printf 'dirty-edit\n' > "${repo}/shared.txt"
    run env FF_STARVE_COMMIT_THRESHOLD=1 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "detached HEAD behind remote → DETACHED HEAD signal (actor skips it)" {
    repo="$(_make_behind_repo)"
    ( cd "${repo}" && git checkout -q --detach HEAD )   # detached, 1 behind
    run env FF_STARVE_COMMIT_THRESHOLD=1 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [[ "$output" == *"FF-PULL DETACHED HEAD"* ]]
    [[ "$output" == *"slot 6"* ]]
}

@test "detached HEAD up-to-date → NO signal" {
    repo="$(_make_behind_repo)"
    ( cd "${repo}" && git checkout -q --detach origin/live-defi-rollout )   # detached at tip, 0 behind
    run env FF_STARVE_COMMIT_THRESHOLD=1 bash "$DETECT" "${repo}" --slot 6
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}
