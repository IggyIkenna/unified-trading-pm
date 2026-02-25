#!/usr/bin/env bats
# test_sync_push.bats — tests for sync-rules-push.sh
#
# Run: bats tests/test_sync_push.bats

load "helpers/setup_workspace"

PUSH_SCRIPT=""

setup() {
    setup_fake_workspace
    PUSH_SCRIPT="$FAKE_PM/scripts/sync-rules-push.sh"
}

teardown() {
    teardown_fake_workspace
}

# ── Happy path ────────────────────────────────────────────────────────────────

@test "sync-rules-push: copies .mdc files from .cursor/rules/ to cursor-rules/" {
    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(count_mdc "$FAKE_PM_CURSOR_RULES")" -eq 3 ]
}

@test "sync-rules-push: each rule file exists in destination" {
    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    [ -f "$FAKE_PM_CURSOR_RULES/rule-one.mdc" ]
    [ -f "$FAKE_PM_CURSOR_RULES/rule-two.mdc" ]
    [ -f "$FAKE_PM_CURSOR_RULES/rule-three.mdc" ]
}

@test "sync-rules-push: copies .cursorrules to cursor-configs/" {
    echo "test cursorrules content" > "$FAKE_WORKSPACE/.cursorrules"
    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    [ -f "$FAKE_PM_CURSOR_CONFIGS/cursorrules" ]
    grep -q "test cursorrules content" "$FAKE_PM_CURSOR_CONFIGS/cursorrules"
}

@test "sync-rules-push: updates .last-sync timestamp" {
    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    [ -f "$FAKE_PM/.last-sync" ]
    content=$(cat "$FAKE_PM/.last-sync")
    [[ "$content" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T ]]
}

@test "sync-rules-push: overwrites existing rule in destination" {
    # Pre-seed destination with stale content
    echo "# stale content" > "$FAKE_PM_CURSOR_RULES/rule-one.mdc"
    echo "# updated content" > "$FAKE_CURSOR_RULES/rule-one.mdc"

    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    grep -q "updated content" "$FAKE_PM_CURSOR_RULES/rule-one.mdc"
}

@test "sync-rules-push: adds new rule not previously in destination" {
    echo "# brand new rule" > "$FAKE_CURSOR_RULES/brand-new.mdc"

    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    [ -f "$FAKE_PM_CURSOR_RULES/brand-new.mdc" ]
}

# ── Dry run ───────────────────────────────────────────────────────────────────

@test "sync-rules-push --dry-run: does not copy any files" {
    run bash "$PUSH_SCRIPT" --dry-run
    [ "$status" -eq 0 ]
    [ "$(count_mdc "$FAKE_PM_CURSOR_RULES")" -eq 0 ]
}

@test "sync-rules-push --dry-run: prints files that would be copied" {
    run bash "$PUSH_SCRIPT" --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY RUN"* ]]
}

@test "sync-rules-push --dry-run: does not create .last-sync" {
    run bash "$PUSH_SCRIPT" --dry-run
    [ ! -f "$FAKE_PM/.last-sync" ]
}

# ── Error cases ───────────────────────────────────────────────────────────────

@test "sync-rules-push: fails with clear error when .cursor/rules/ missing" {
    rm -rf "$FAKE_WORKSPACE/.cursor/rules"
    run bash "$PUSH_SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == *"ERROR"* ]] || [[ "$output" == *"not found"* ]]
}

@test "sync-rules-push: fails with clear error when .cursor/ missing entirely" {
    rm -rf "$FAKE_WORKSPACE/.cursor"
    run bash "$PUSH_SCRIPT"
    [ "$status" -ne 0 ]
}

@test "sync-rules-push: fails when PM is workspace root (wrong clone location)" {
    # Simulate cloning PM as the root instead of a sibling
    BAD_WORKSPACE="$BATS_TMPDIR/bad-workspace"
    mkdir -p "$BAD_WORKSPACE/.git"
    mkdir -p "$BAD_WORKSPACE/scripts"
    cp "$FAKE_PM/scripts/_workspace-lib.sh" "$BAD_WORKSPACE/scripts/"
    cp "$FAKE_PM/scripts/sync-rules-push.sh" "$BAD_WORKSPACE/scripts/"
    chmod +x "$BAD_WORKSPACE/scripts/"*.sh

    run bash "$BAD_WORKSPACE/scripts/sync-rules-push.sh"
    [ "$status" -ne 0 ]
    [[ "$output" == *"ERROR"* ]]

    rm -rf "$BAD_WORKSPACE"
}

# ── Idempotency ───────────────────────────────────────────────────────────────

@test "sync-rules-push: running twice produces same result (idempotent)" {
    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    count_after_first=$(count_mdc "$FAKE_PM_CURSOR_RULES")

    run bash "$PUSH_SCRIPT"
    [ "$status" -eq 0 ]
    count_after_second=$(count_mdc "$FAKE_PM_CURSOR_RULES")

    [ "$count_after_first" -eq "$count_after_second" ]
}
