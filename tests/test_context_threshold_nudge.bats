#!/usr/bin/env bats
# test_context_threshold_nudge.bats — tests for cursor-configs/hooks/context-threshold-nudge.sh
#
# Regression for ao_dispatch_health_2026_07_26 / context-threshold-nudge-hook-crash: the
# SINCE-LAST-COMPACT windowing feature (2026-07-25) used `grep -abo ... | tail -1 | cut -d: -f1`
# in a variable assignment under `set -euo pipefail`. `grep` exits 1 (not an error -- "no
# match") for any session that has not yet compacted, which is the common case -- under
# pipefail that non-zero status aborted the WHOLE hook on every such prompt submission,
# surfacing as "UserPromptSubmit hook error" (confirmed live in a real AO worker's pane).
#
# Run: bats tests/test_context_threshold_nudge.bats

HOOK=""

setup() {
    HOOK="$BATS_TEST_DIRNAME/../cursor-configs/hooks/context-threshold-nudge.sh"
    WORKDIR="$(mktemp -d)"
}

teardown() {
    rm -rf "$WORKDIR"
}

_make_transcript() {
    # $1 = target line count, $2 = 1 to seed a compact_boundary marker at the top
    local n="$1"
    local seed_boundary="${2:-0}"
    local path="$WORKDIR/transcript.jsonl"
    if [ "$seed_boundary" -eq 1 ]; then
        printf '{"subtype":"compact_boundary"}\n' >"$path"
    fi
    for _ in $(seq 1 "$n"); do
        printf '{"type":"assistant","content":"%080d"}\n' 0 >>"$path"
    done
    echo "$path"
}

@test "context-threshold-nudge: exits 0 on a large uncompacted transcript (no compact_boundary marker)" {
    transcript="$(_make_transcript 50000 0)"
    run bash -c "echo '{\"session_id\":\"t1\",\"transcript_path\":\"$transcript\"}' | bash '$HOOK'"
    [ "$status" -eq 0 ]
}

@test "context-threshold-nudge: fires the nudge past threshold with no compact_boundary marker" {
    transcript="$(_make_transcript 50000 0)"
    run bash -c "echo '{\"session_id\":\"t2\",\"transcript_path\":\"$transcript\"}' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"UserPromptSubmit"* ]]
}

@test "context-threshold-nudge: exits 0 and emits nothing on a small transcript below threshold" {
    transcript="$(_make_transcript 100 0)"
    run bash -c "echo '{\"session_id\":\"t3\",\"transcript_path\":\"$transcript\"}' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "context-threshold-nudge: exits 0 and fires correctly when a compact_boundary marker IS present" {
    transcript="$(_make_transcript 50000 1)"
    run bash -c "echo '{\"session_id\":\"t4\",\"transcript_path\":\"$transcript\"}' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"UserPromptSubmit"* ]]
}

@test "context-threshold-nudge: exits 0 with no session_id (missing input, early-exit path)" {
    run bash -c "echo '{}' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}
