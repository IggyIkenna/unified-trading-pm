#!/usr/bin/env bats
# test_tab_worktrees.bats — smoke + idempotency tests for setup-tab-worktrees.sh
#   and teardown-tab-worktrees.sh.
#
# These are HERMETIC tests that DO NOT touch real worktrees in $WORKSPACE_ROOT.
# We exercise --help / arg-parsing / idempotency-shape only; the heavy --init
# path is validated by the Phase 0 spike + the operator's real --init run on
# their workstation (see plans/active/per_agent_worktrees_2026_05_10.md).
#
# Run: bats tests/test_tab_worktrees.bats
# Run all: bats tests/


# Resolve paths relative to the workspace root, so this test passes whether
# invoked from PM root or workspace root.
setup() {
    # ABSOLUTE, derived from this file's own location. The paths were workspace-root-relative,
    # so every invocation depended on the cd below landing exactly right — and
    # `git rev-parse --show-toplevel` returning empty (a subprocess, run alongside ~200 other
    # tests spawning git) silently falls through to `cd ..` from wherever bats started. Passed
    # 5/5 serially, failed ~1 in 3 parallel, surfacing as a bug in the rollup script.
    _TAB_PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    SETUP="${_TAB_PM_ROOT}/scripts/dev/setup-tab-worktrees.sh"
    TEARDOWN="${_TAB_PM_ROOT}/scripts/dev/teardown-tab-worktrees.sh"
    REBASE="${_TAB_PM_ROOT}/scripts/dev/slot-master-rebase.sh"
    ROLLUP="${_TAB_PM_ROOT}/scripts/agents/rollup_resolved_pings.py"
    cd "${_TAB_PM_ROOT}/.." || cd ..
}

# ── Bash syntax + help text ───────────────────────────────────────────────────

@test "setup-tab-worktrees.sh has valid bash syntax" {
    run bash -n "$SETUP"
    [ "$status" -eq 0 ]
}

@test "teardown-tab-worktrees.sh has valid bash syntax" {
    run bash -n "$TEARDOWN"
    [ "$status" -eq 0 ]
}

@test "slot-master-rebase.sh has valid bash syntax" {
    run bash -n "$REBASE"
    [ "$status" -eq 0 ]
}

@test "setup-tab-worktrees.sh --help renders" {
    run bash "$SETUP" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"setup-tab-worktrees.sh"* ]]
    [[ "$output" == *"--init"* ]]
    [[ "$output" == *"--add-slot"* ]]
    [[ "$output" == *"--reset-slot"* ]]
    [[ "$output" == *"--list"* ]]
}

@test "teardown-tab-worktrees.sh --help renders" {
    run bash "$TEARDOWN" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"teardown-tab-worktrees.sh"* ]]
    [[ "$output" == *"--slot"* ]]
}

@test "slot-master-rebase.sh --help renders" {
    run bash "$REBASE" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"slot-master-rebase.sh"* ]]
    [[ "$output" == *"--all"* ]]
}

# ── Argument validation ───────────────────────────────────────────────────────

@test "setup-tab-worktrees.sh rejects missing mode" {
    run bash "$SETUP"
    [ "$status" -ne 0 ]
    [[ "$output" == *"one of --init"* ]]
}

@test "setup-tab-worktrees.sh --init requires --slots" {
    run bash "$SETUP" --init
    [ "$status" -ne 0 ]
    [[ "$output" == *"--init requires --slots"* ]]
}

@test "setup-tab-worktrees.sh rejects unknown arg" {
    run bash "$SETUP" --bogus
    [ "$status" -ne 0 ]
    [[ "$output" == *"Unknown arg"* ]]
}

@test "teardown-tab-worktrees.sh requires --slot" {
    run bash "$TEARDOWN"
    [ "$status" -ne 0 ]
    [[ "$output" == *"--slot <N> required"* ]]
}

@test "teardown-tab-worktrees.sh rejects unknown arg" {
    run bash "$TEARDOWN" --bogus
    [ "$status" -ne 0 ]
    [[ "$output" == *"Unknown arg"* ]]
}

# ── --list idempotency ────────────────────────────────────────────────────────
# --list is read-only and harmless: should always exit 0 + emit configured-slots
# summary or "(none — run --init first)".

@test "setup-tab-worktrees.sh --list exits cleanly" {
    run bash "$SETUP" --list
    [ "$status" -eq 0 ]
    [[ "$output" == *"Slots configured under"* ]]
}

# ── teardown on missing slot is no-op (idempotent) ───────────────────────────

@test "teardown-tab-worktrees.sh on non-existent slot is no-op" {
    # Use a slot number far beyond any plausible provisioned slot.
    run bash "$TEARDOWN" --slot 9999
    [ "$status" -eq 0 ]
    [[ "$output" == *"Nothing to do"* ]]
}

# ── rollup_resolved_pings.py tests ───────────────────────────────────────────
# These tests verify the read-time rollup helper without touching real ping files.


@test "rollup_resolved_pings.py has valid python3 syntax" {
    run python3 -m py_compile "$ROLLUP"
    [ "$status" -eq 0 ]
}

@test "rollup_resolved_pings.py --help renders" {
    run python3 "$ROLLUP" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"rollup"* ]]
    [[ "$output" == *"ping_file"* ]]
    [[ "$output" == *"--dry-run"* ]]
}

@test "rollup_resolved_pings.py errors on missing file" {
    run python3 "$ROLLUP" /nonexistent/slot_99.md
    [ "$status" -ne 0 ]
    [[ "$output" == *"not found"* ]]
}

@test "rollup_resolved_pings.py dry-run on file with no stale entries returns 0" {
    # Create a temp ping file with only a recent active entry.
    local tmp_ping
    tmp_ping="$(mktemp /tmp/slot_test_XXXX.md)"
    printf '[%s UTC] slot-N — STARTED\n' "$(date -u +'%Y-%m-%d %H:%M')" > "${tmp_ping}"
    run python3 "$ROLLUP" --dry-run "${tmp_ping}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"would roll up 0"* ]]
    rm -f "${tmp_ping}"
}

@test "rollup_resolved_pings.py dry-run rolls up old resolved entries" {
    # Create a temp ping file with a stale ✅ DONE entry (timestamp 2 days ago).
    local tmp_ping stale_ts
    tmp_ping="$(mktemp /tmp/slot_test_XXXX.md)"
    stale_ts="$(date -u -d '2 days ago' +'%Y-%m-%d %H:%M' 2>/dev/null || date -u -v -2d +'%Y-%m-%d %H:%M')"
    printf '[%s UTC] slot-N — ✅ DONE everything\n' "${stale_ts}" > "${tmp_ping}"
    run python3 "$ROLLUP" --dry-run "${tmp_ping}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"would roll up 1"* ]]
    rm -f "${tmp_ping}"
}
