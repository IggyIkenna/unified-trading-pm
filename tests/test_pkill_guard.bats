#!/usr/bin/env bats
# test_pkill_guard.bats — tests for scripts/hooks/pkill-guard.sh
#
# Run: bats tests/test_pkill_guard.bats
# Run all: bats tests/
#
# Deliberately exercises only the internal decision function
# (_pkill_guard_check) rather than the wrapped pkill()/pgrep() functions —
# the decision logic is what needs coverage, and calling the real functions
# would either send a real signal (pkill) or need the wrapped call itself to
# be the assertion target. `run` captures stdout/stderr + exit status either
# way, so testing the internal function is equivalent and avoids ever
# touching a real process from CI.

setup() {
    PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    # shellcheck source=/dev/null
    source "$PM_ROOT/scripts/hooks/pkill-guard.sh"
}

# ── _pkill_guard_has_numeric_target ──────────────────────────────────────────

@test "has_numeric_target: -g with numeric value" {
    run _pkill_guard_has_numeric_target -g 12345
    [ "$status" -eq 0 ]
}

@test "has_numeric_target: -g attached numeric value" {
    run _pkill_guard_has_numeric_target -g12345
    [ "$status" -eq 0 ]
}

@test "has_numeric_target: -g with comma-separated numeric list" {
    run _pkill_guard_has_numeric_target -g 111,222,333
    [ "$status" -eq 0 ]
}

@test "has_numeric_target: -g with non-numeric value fails" {
    run _pkill_guard_has_numeric_target -g abc
    [ "$status" -ne 0 ]
}

@test "has_numeric_target: no matching flag at all fails" {
    run _pkill_guard_has_numeric_target -f "some-pattern"
    [ "$status" -ne 0 ]
}

@test "has_numeric_target: -P (parent pid) numeric also allowed" {
    run _pkill_guard_has_numeric_target -P 6789
    [ "$status" -eq 0 ]
}

# ── _pkill_guard_extract_pattern ─────────────────────────────────────────────

@test "extract_pattern: finds bare trailing pattern" {
    result="$(_pkill_guard_extract_pattern quality-gates.sh)"
    [ "$result" = "quality-gates.sh" ]
}

@test "extract_pattern: finds pattern after -f" {
    result="$(_pkill_guard_extract_pattern -f "quality-gates.sh --no-fix")"
    [ "$result" = "quality-gates.sh --no-fix" ]
}

@test "extract_pattern: ignores a signal flag like -9" {
    result="$(_pkill_guard_extract_pattern -9 -f "quality-gates.sh")"
    [ "$result" = "quality-gates.sh" ]
}

@test "extract_pattern: skips the value of a consuming flag (-g)" {
    result="$(_pkill_guard_extract_pattern -g 12345 -f "quality-gates.sh")"
    [ "$result" = "quality-gates.sh" ]
}

# ── _pkill_guard_check — the end-to-end gate ────────────────────────────────

@test "check: refuses a bare -f pattern with no discriminator" {
    cd /tmp
    run _pkill_guard_check pkill -f "quality-gates.sh --no-fix"
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
    [[ "$output" == *"lacks a slot-specific discriminator"* ]]
}

@test "check: refuses a bare name-only pattern" {
    cd /tmp
    run _pkill_guard_check pkill quality-gates.sh
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
}

@test "check: allows a numeric -g target regardless of cwd" {
    cd /tmp
    run _pkill_guard_check pkill -g 999999999
    [ "$status" -eq 0 ]
}

@test "check: allows a pattern containing the caller's own .tabs/<N>/ substring" {
    fake_slot_dir="$BATS_TEST_TMPDIR/.tabs/7/market-tick-data-service"
    mkdir -p "$fake_slot_dir"
    cd "$fake_slot_dir"
    run _pkill_guard_check pkill -f "${fake_slot_dir}.*quality-gates"
    [ "$status" -eq 0 ]
}

@test "check: refuses a pattern containing a DIFFERENT slot's .tabs/<N>/ substring" {
    fake_slot_dir="$BATS_TEST_TMPDIR/.tabs/7/market-tick-data-service"
    mkdir -p "$fake_slot_dir"
    cd "$fake_slot_dir"
    run _pkill_guard_check pkill -f "/some/other/.tabs/3/market-tick-data-service.*quality-gates"
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
}

@test "check: message points at the incident issue doc" {
    cd /tmp
    run _pkill_guard_check pkill -f "quality-gates.sh"
    [[ "$output" == *"pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md"* ]]
}

@test "check: same rules apply to pgrep as pkill" {
    cd /tmp
    run _pkill_guard_check pgrep -f "quality-gates.sh"
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
}

# ── pkill()/pgrep() wrapper functions — refuse path never execs the real binary ──

@test "wrapper: pkill() refuses without invoking the real binary" {
    cd /tmp
    run pkill -f "quality-gates.sh --no-fix"
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
}

@test "wrapper: pgrep() refuses without invoking the real binary" {
    cd /tmp
    run pgrep quality-gates.sh
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
}

# ── export -f survives exec into a non-shell process (recurrence #3 regression) ──
#
# tmux_spawn.py's worker-spawn path sources this file then immediately `exec`s
# into the `claude` binary; every later Bash-tool call is a FRESH `bash -c`
# child of that (non-shell) process. A non-exported function only lives in the
# shell that defined it and is silently discarded across `exec` into a
# different program — confirmed live (pkill_broad_pattern_vite_cross_slot_kill_
# recurrence3_2026_08_14.md): `type pkill` in a real worker's Bash-tool shell
# resolved straight to /usr/bin/pkill despite the guard having been sourced in
# its ancestor shell. These tests simulate that exact source -> exec -> child
# chain (using `bash -c` as the exec target instead of the real `claude`
# binary, which is unavailable in CI) to prove the guard actually survives it.

@test "export: pkill survives source -> exec -> fresh bash -c child" {
    run bash -c '. "'"$PM_ROOT"'/scripts/hooks/pkill-guard.sh"; exec bash -c "type pkill"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"pkill is a function"* ]]
}

@test "export: pkill in a fresh bash -c child still refuses a bare pattern" {
    run bash -c '. "'"$PM_ROOT"'/scripts/hooks/pkill-guard.sh"; exec bash -c "pkill -f quality-gates.sh"'
    [ "$status" -ne 0 ]
    [[ "$output" == *"REFUSED"* ]]
}
