#!/usr/bin/env bats
# test_slot_git_status_dirty_count.bats — unit tests for the dirty_files count-integrity
# fix in slot-git-status-report.sh's classify_repo()
#   (ao_remediation_b_code_chain_2026_07_23.md item 1;
#    git_health_phantom_dirty_flicker_ff_cron_race_2026_07_21.md).
#
# HERMETIC: builds throwaway git repos under BATS_TEST_TMPDIR; never touches real
# worktrees in $WORKSPACE_ROOT. Mirrors tests/test_ff_starvation_detect.bats structure.
#
# classify_repo() never calls curl (only post_snapshot does), so we exercise it
# directly: source the real script into a FRESH bash subprocess (via `run bash -c`,
# never the bats process itself) pointed at an empty --workspace, so the main
# slot-walking loop at the bottom has zero repos to find and never POSTs anything.
# classify_repo is then called against a hermetic repo built separately.
#
# Run: bats tests/test_slot_git_status_dirty_count.bats
# Run all: bats tests/

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    REPORTER_ABS="$(cd "$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"
}

# Source the reporter (functions only — the main loop is a no-op against
# EMPTY_WS, so this never calls curl), then call classify_repo directly on $1.
_classify() {
    local repo="$1"
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet
        classify_repo "'"${repo}"'"
    '
}

# TSV row: name<TAB>branch<TAB>state<TAB>dirty_files<TAB>ahead<TAB>behind<TAB>local_sha
#          <TAB>int_branch<TAB>dirty_oldest_iso<TAB>unpushed_plans<TAB>dirty_sample
_field() { # _field <tsv-row> <1-indexed-field>
    printf '%s' "$1" | cut -f"$2"
}

_make_repo() {
    local root="${BATS_TEST_TMPDIR}/repo_$$_${RANDOM}"
    mkdir -p "${root}"
    (
        cd "${root}"
        git init -q
        git config user.email t@t.t
        git config user.name t
        printf 'v1\n' > tracked.txt
        git add -A && git commit -qm init
    )
    echo "${root}"
}

@test "slot-git-status-report.sh has valid bash syntax" {
    run bash -n "$REPORTER_ABS"
    [ "$status" -eq 0 ]
}

@test "clean tree -> dirty_files=0 and empty sample (never independently non-zero)" {
    repo="$(_make_repo)"
    run _classify "${repo}"
    [ "$status" -eq 0 ]
    [ "$(_field "$output" 4)" = "0" ]
    [ -z "$(_field "$output" 11)" ]
}

@test "one modified tracked file -> dirty_files equals captured sample length (1)" {
    repo="$(_make_repo)"
    printf 'v2\n' > "${repo}/tracked.txt"
    run _classify "${repo}"
    [ "$status" -eq 0 ]
    df="$(_field "$output" 4)"
    sample="$(_field "$output" 11)"
    [ "$df" = "1" ]
    IFS='|' read -ra parts <<< "$sample"
    [ "${#parts[@]}" -eq "$df" ]
    [[ "$sample" == *"tracked.txt"* ]]
}

@test "three dirty files (modified + new tracked + untracked) -> dirty_files equals captured sample length (3)" {
    repo="$(_make_repo)"
    (cd "${repo}" && printf 'extra\n' > extra_tracked.txt && git add extra_tracked.txt && git commit -qm extra)
    printf 'v2\n' > "${repo}/tracked.txt"
    printf 'v3\n' > "${repo}/extra_tracked.txt"
    printf 'new\n' > "${repo}/untracked.txt"
    run _classify "${repo}"
    [ "$status" -eq 0 ]
    df="$(_field "$output" 4)"
    sample="$(_field "$output" 11)"
    [ "$df" = "3" ]
    IFS='|' read -ra parts <<< "$sample"
    [ "${#parts[@]}" -eq "$df" ]
}

@test "dirty_files can never exceed the captured sample length, however many files are dirty (7 > cap)" {
    repo="$(_make_repo)"
    for i in 1 2 3 4 5 6 7; do
        printf 'new %s\n' "$i" > "${repo}/untracked_${i}.txt"
    done
    run _classify "${repo}"
    [ "$status" -eq 0 ]
    df="$(_field "$output" 4)"
    sample="$(_field "$output" 11)"
    IFS='|' read -ra parts <<< "$sample"
    [ "${#parts[@]}" -eq "$df" ]
    [ "$df" -le 7 ]
}

# ── item 2: df>0-with-empty-sample tripwire instrumentation ─────────────────────
# classify_repo() can no longer produce this combination itself (item 1 made
# dirty_files := len(sample_list)), so we call the standalone
# log_df_sample_mismatch_if_any() directly with a FORCED, contrived pair —
# exactly what the todo's Gate asks for.
_call_mismatch_check() { # $1=df $2=raw-porcelain $3=sample_len
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet
        log_df_sample_mismatch_if_any "$1" "$2" "$3"
    ' _ "$1" "$2" "$3"
}

@test "forced df>0 + empty sample -> emits the raw-bytes anomaly log line" {
    run _call_mismatch_check "1" "$(printf ' \nM  x')" "0"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[anomaly]"* ]]
    [[ "$output" == *"dirty_files=1"* ]]
    [[ "$output" == *"empty dirty_files_sample"* ]]
    [[ "$output" == *"cat -A"* ]]
}

@test "consistent df/sample (both 0 or both non-zero) -> no anomaly log line" {
    run _call_mismatch_check "0" "" "0"
    [ "$status" -eq 1 ]
    [ -z "$output" ]

    run _call_mismatch_check "2" "M  a
M  b" "2"
    [ "$status" -eq 1 ]
    [ -z "$output" ]
}
