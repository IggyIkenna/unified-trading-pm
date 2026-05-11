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

SETUP="unified-trading-pm/scripts/dev/setup-tab-worktrees.sh"
TEARDOWN="unified-trading-pm/scripts/dev/teardown-tab-worktrees.sh"
REBASE="unified-trading-pm/scripts/dev/slot-master-rebase.sh"

# Resolve paths relative to the workspace root, so this test passes whether
# invoked from PM root or workspace root.
setup() {
    cd "$(git rev-parse --show-toplevel)/.." || cd ..
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
