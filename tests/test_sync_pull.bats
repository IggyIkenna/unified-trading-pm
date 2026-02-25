#!/usr/bin/env bats
# test_sync_pull.bats — tests for sync-rules-pull.sh
#
# Run: bats tests/test_sync_pull.bats

load "helpers/setup_workspace"

PULL_SCRIPT=""

setup() {
    setup_fake_workspace
    PULL_SCRIPT="$FAKE_PM/scripts/sync-rules-pull.sh"
    # Seed the repo with rules to pull
    seed_repo_rules 4
}

teardown() {
    teardown_fake_workspace
}

# ── Happy path ────────────────────────────────────────────────────────────────

@test "sync-rules-pull --force: copies repo rules to .cursor/rules/" {
    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    # Should have original 3 local + 4 new from repo = 7
    [ "$(count_mdc "$FAKE_CURSOR_RULES")" -ge 4 ]
}

@test "sync-rules-pull --force: each repo rule is present in local" {
    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    [ -f "$FAKE_CURSOR_RULES/repo-rule-1.mdc" ]
    [ -f "$FAKE_CURSOR_RULES/repo-rule-4.mdc" ]
}

@test "sync-rules-pull --force: does NOT delete local-only rules" {
    # Local has rule-one/two/three; repo does not
    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    # Local-only rules should still be there
    [ -f "$FAKE_CURSOR_RULES/rule-one.mdc" ]
    [ -f "$FAKE_CURSOR_RULES/rule-two.mdc" ]
}

@test "sync-rules-pull --force: overwrites stale local rule with repo version" {
    echo "# stale local"  > "$FAKE_CURSOR_RULES/repo-rule-1.mdc"
    echo "# updated repo" > "$FAKE_PM_CURSOR_RULES/repo-rule-1.mdc"

    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    grep -q "updated repo" "$FAKE_CURSOR_RULES/repo-rule-1.mdc"
}

@test "sync-rules-pull --force: restores .cursorrules from cursor-configs/" {
    echo "# restored cursorrules" > "$FAKE_PM_CURSOR_CONFIGS/cursorrules"

    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    [ -f "$FAKE_WORKSPACE/.cursorrules" ]
    grep -q "restored cursorrules" "$FAKE_WORKSPACE/.cursorrules"
}

@test "sync-rules-pull --force: updates .last-sync timestamp" {
    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    [ -f "$FAKE_PM/.last-sync" ]
    content=$(cat "$FAKE_PM/.last-sync")
    [[ "$content" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}T ]]
}

@test "sync-rules-pull --force: creates .cursor/rules/ if it does not exist" {
    rm -rf "$FAKE_CURSOR_RULES"

    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    [ -d "$FAKE_CURSOR_RULES" ]
    [ "$(count_mdc "$FAKE_CURSOR_RULES")" -gt 0 ]
}

# ── Dry run ───────────────────────────────────────────────────────────────────

@test "sync-rules-pull --dry-run: does not copy any files" {
    local before
    before=$(count_mdc "$FAKE_CURSOR_RULES")

    run bash "$PULL_SCRIPT" --dry-run
    [ "$status" -eq 0 ]

    local after
    after=$(count_mdc "$FAKE_CURSOR_RULES")
    [ "$before" -eq "$after" ]
}

@test "sync-rules-pull --dry-run: prints rule counts" {
    run bash "$PULL_SCRIPT" --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"DRY RUN"* ]]
}

@test "sync-rules-pull --dry-run: shows rules only in repo" {
    run bash "$PULL_SCRIPT" --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"repo-rule"* ]]
}

# ── Error cases ───────────────────────────────────────────────────────────────

@test "sync-rules-pull: fails with clear error when cursor-rules/ missing from repo" {
    rm -rf "$FAKE_PM_CURSOR_RULES"

    run bash "$PULL_SCRIPT" --force
    [ "$status" -ne 0 ]
    [[ "$output" == *"ERROR"* ]] || [[ "$output" == *"not found"* ]]
}

@test "sync-rules-pull: fails when workspace structure is invalid" {
    rm -rf "$FAKE_WORKSPACE/unified-trading-codex"
    rm -rf "$FAKE_WORKSPACE/instruments-service"

    run bash "$PULL_SCRIPT" --force
    [ "$status" -ne 0 ]
    [[ "$output" == *"ERROR"* ]]
}

# ── Idempotency ───────────────────────────────────────────────────────────────

@test "sync-rules-pull: running twice produces same result (idempotent)" {
    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    count_first=$(count_mdc "$FAKE_CURSOR_RULES")

    run bash "$PULL_SCRIPT" --force
    [ "$status" -eq 0 ]
    count_second=$(count_mdc "$FAKE_CURSOR_RULES")

    [ "$count_first" -eq "$count_second" ]
}
