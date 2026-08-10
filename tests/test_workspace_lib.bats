#!/usr/bin/env bats
# test_workspace_lib.bats — tests for validate_workspace_structure()
#
# Run: bats tests/test_workspace_lib.bats
# Run all: bats tests/

load "helpers/setup_workspace"

# Source the lib with our fake paths, not real ones
source_lib_with_fake_paths() {
    export SCRIPT_DIR="$FAKE_PM/scripts"
    export PM_ROOT="$FAKE_PM"
    export WORKSPACE_ROOT="$FAKE_WORKSPACE"
    # shellcheck source=/dev/null
    source "$FAKE_PM/scripts/_workspace-lib.sh"
}

setup() {
    setup_fake_workspace
}

teardown() {
    teardown_fake_workspace
}

# ── Happy path ────────────────────────────────────────────────────────────────

@test "validate_workspace_structure: passes with correct layout" {
    source_lib_with_fake_paths
    run validate_workspace_structure
    [ "$status" -eq 0 ]
    [[ "$output" == *"Workspace structure OK"* ]]
    [[ "$output" == *"Workspace root:"* ]]
}

@test "validate_workspace_structure: reports correct sibling count" {
    source_lib_with_fake_paths
    run validate_workspace_structure
    [ "$status" -eq 0 ]
    # 3 siblings: unified-trading-pm, unified-trading-codex, instruments-service
    [[ "$output" == *"Sibling repos:"* ]]
}

# ── PM_ROOT == WORKSPACE_ROOT ─────────────────────────────────────────────────

@test "validate_workspace_structure: fails when PM is workspace root" {
    export SCRIPT_DIR="$FAKE_PM/scripts"
    export PM_ROOT="$FAKE_WORKSPACE"   # same as workspace root
    export WORKSPACE_ROOT="$FAKE_WORKSPACE"
    source "$FAKE_PM/scripts/_workspace-lib.sh"

    run validate_workspace_structure
    [ "$status" -ne 0 ]
    [[ "$output" == *"unified-trading-pm appears to BE the workspace root"* ]]
}

@test "validate_workspace_structure: error message shows required structure" {
    export PM_ROOT="$FAKE_WORKSPACE"
    export WORKSPACE_ROOT="$FAKE_WORKSPACE"
    source "$FAKE_PM/scripts/_workspace-lib.sh"

    run validate_workspace_structure
    [[ "$output" == *"unified-trading-pm/"*"← this repo"* ]]
}

# ── Missing .cursor/ ──────────────────────────────────────────────────────────

@test "validate_workspace_structure: fails when .cursor/ is missing" {
    rm -rf "$FAKE_WORKSPACE/.cursor"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [ "$status" -ne 0 ]
    [[ "$output" == *"No .cursor/ directory found at workspace root"* ]]
}

@test "validate_workspace_structure: error suggests fix command" {
    rm -rf "$FAKE_WORKSPACE/.cursor"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [[ "$output" == *"mkdir -p"* ]]
}

# ── Missing .cursor/rules/ ────────────────────────────────────────────────────

@test "validate_workspace_structure: warns (not errors) when .cursor/rules/ missing" {
    rm -rf "$FAKE_WORKSPACE/.cursor/rules"
    source_lib_with_fake_paths

    run validate_workspace_structure
    # Should pass overall but warn
    [ "$status" -eq 0 ]
    [[ "$output" == *"WARNING"* ]] || [[ "$output" == *"does not exist"* ]]
}

# ── PM not a git repo ─────────────────────────────────────────────────────────

@test "validate_workspace_structure: fails when PM has no .git" {
    rm -rf "$FAKE_PM/.git"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [ "$status" -ne 0 ]
    [[ "$output" == *"not a git repository"* ]]
}

@test "validate_workspace_structure: error suggests git init fix" {
    rm -rf "$FAKE_PM/.git"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [[ "$output" == *"git init"* ]]
}

# ── No known siblings ─────────────────────────────────────────────────────────

@test "validate_workspace_structure: fails when no known sibling repos exist" {
    rm -rf "$FAKE_WORKSPACE/unified-trading-codex"
    rm -rf "$FAKE_WORKSPACE/instruments-service"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [ "$status" -ne 0 ]
    [[ "$output" == *"No known sibling repos found"* ]]
}

@test "validate_workspace_structure: error shows expected sibling names" {
    rm -rf "$FAKE_WORKSPACE/unified-trading-codex"
    rm -rf "$FAKE_WORKSPACE/instruments-service"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [[ "$output" == *"unified-trading-codex"* ]]
}

# ── Multiple errors ───────────────────────────────────────────────────────────

@test "validate_workspace_structure: reports error count in summary" {
    rm -rf "$FAKE_PM/.git"
    rm -rf "$FAKE_WORKSPACE/unified-trading-codex"
    rm -rf "$FAKE_WORKSPACE/instruments-service"
    source_lib_with_fake_paths

    run validate_workspace_structure
    [ "$status" -ne 0 ]
    [[ "$output" == *"error"* ]] && [[ "$output" == *"Aborting"* ]]
}

# ── Helper functions ──────────────────────────────────────────────────────────

@test "count_rules_local: returns correct count" {
    source_lib_with_fake_paths
    # setup created 3 rules in .cursor/rules/
    result=$(count_rules_local)
    [ "$result" -eq 3 ]
}

@test "count_rules_repo: returns 0 when cursor-rules/ is empty" {
    source_lib_with_fake_paths
    result=$(count_rules_repo)
    [ "$result" -eq 0 ]
}

@test "get_last_sync: returns 'never' when .last-sync missing" {
    source_lib_with_fake_paths
    result=$(get_last_sync)
    [ "$result" = "never" ]
}

@test "update_last_sync: writes ISO timestamp to .last-sync" {
    source_lib_with_fake_paths
    update_last_sync
    [ -f "$FAKE_PM/.last-sync" ]
    content=$(cat "$FAKE_PM/.last-sync")
    [[ "$content" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T ]]
}
