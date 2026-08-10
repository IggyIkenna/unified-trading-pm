#!/usr/bin/env bats
# test_autostash_chain_guard.bats — the autostash-CHAIN guard
#   (multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md,
#   2026-08-10 slot-1 finding).
#
# THE CHAIN: every `git pull --rebase --autostash` stashes the dirty tree and pops it back.
# If the tree already carries stale content (old versions that REVERT content committed on
# origin), each cycle re-applies and re-preserves it — the snapshot ages forward indefinitely
# and `git stash list` accumulates autostash entries. Measured: 107 files, 97 reverting
# committed content, 9 archived plans resurrected as untracked.
#
# The guard (`scripts/dev/autostash-chain-guard.sh`) runs right after the pop:
#   • autostash_chain_guard_quarantine_reverts <branch> [caller-files]
#       Detects stale reverts (tracked file whose working-tree blob is an ANCESTOR blob of
#       origin/<branch> at that path but != origin tip; a tracked file deleted though still
#       live on origin; an untracked file whose blob is reachable from origin = a resurrected
#       archived plan). Foreign files are quarantined to a NAMED stash and the working tree
#       returns to origin content. A CALLER-NAMED stale file is refused (returns 1) instead.
#   • autostash_chain_guard_bound_backlog <branch> [max]
#       Prunes git-generated `autostash` entries that are provably redundant (their diff
#       reverse-applies cleanly to the current tree), never a named stash or a non-redundant one.
#
# Replicates the established hermetic pattern (test_safe_doc_push_*): a bare "origin" is a
# second local repo, no network. Sourcing the REAL guard lib, not a copy.
#
# Run: bats tests/test_autostash_chain_guard.bats

setup() {
    GUARD_LIB="$(cd "$BATS_TEST_DIRNAME/../scripts/dev" && pwd)/autostash-chain-guard.sh"
    [ -f "$GUARD_LIB" ] || skip "guard lib missing"
    BRANCH="live-defi-rollout"
    TEST_ROOT="$(mktemp -d)"
    git init --bare -q "$TEST_ROOT/origin.git"
    git clone -q "$TEST_ROOT/origin.git" "$TEST_ROOT/work"
    cd "$TEST_ROOT/work" || return 1
    git config user.email "test@example.com"
    git config user.name "test"
    mkdir -p plans/archive/2026_08/issues plans/active/issues
    echo "content-v1" > plans/active/issues/doc.md
    echo "issue" > plans/archive/2026_08/issues/old.md
    git add -A
    git commit -qm "c1"
    git branch -M "$BRANCH"
    git push -q -u origin "$BRANCH"
    echo "content-v2" > plans/active/issues/doc.md
    echo "issue-v2" > plans/archive/2026_08/issues/old.md
    git add -A
    git commit -qm "c2"
    git push -q origin "$BRANCH"
    git fetch -q origin "$BRANCH"
}

teardown() {
    [ -n "$TEST_ROOT" ] && rm -rf "$TEST_ROOT"
}

_source_guard() {
    # shellcheck source=/dev/null
    source "$GUARD_LIB"
}

@test "quarantines a tracked file whose working-tree content reverts committed content" {
    echo "content-v1" > plans/active/issues/doc.md   # revert c2 -> c1 content
    _source_guard
    run autostash_chain_guard_quarantine_reverts "$BRANCH" ""
    [ "$status" -eq 0 ]
    [[ "$output" == *"quarantined 1 stale file"* ]]
    # tree restored to origin content (v2)
    run cat plans/active/issues/doc.md
    [ "$output" = "content-v2" ]
    # recoverable named stash
    run git stash list
    [[ "$output" == *"stale-autostash-revert:"* ]]
}

@test "quarantines a tracked deletion of a file still live on origin" {
    rm plans/archive/2026_08/issues/old.md
    _source_guard
    run autostash_chain_guard_quarantine_reverts "$BRANCH" ""
    [ "$status" -eq 0 ]
    [ -f plans/archive/2026_08/issues/old.md ]  # restored
    run git stash list
    [[ "$output" == *"stale-autostash-revert:"* ]]
}

@test "quarantines an untracked file resurrecting a committed blob (archived plan shape)" {
    echo "issue" > plans/active/issues/old.md   # resurrected copy of the archived v1 blob
    _source_guard
    run autostash_chain_guard_quarantine_reverts "$BRANCH" ""
    [ "$status" -eq 0 ]
    [ ! -f plans/active/issues/old.md ]  # untracked stale copy removed
    run git stash list
    [[ "$output" == *"stale-autostash-revert:"* ]]
}

@test "a caller-named stale revert is REFUSED (rc=1), never auto-quarantined" {
    echo "content-v1" > plans/active/issues/doc.md
    _source_guard
    run autostash_chain_guard_quarantine_reverts "$BRANCH" "plans/active/issues/doc.md"
    [ "$status" -eq 1 ]
    [[ "$output" == *"REFUSED"* ]]
    # caller's file left untouched for a deliberate decision
    run cat plans/active/issues/doc.md
    [ "$output" = "content-v1" ]
}

@test "a clean tree is a no-op (rc=0, no stash created)" {
    _source_guard
    run autostash_chain_guard_quarantine_reverts "$BRANCH" ""
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    run git stash list
    [ -z "$output" ]
}

@test "bound_backlog prunes only provably-redundant autostash entries, never named stashes" {
    _source_guard
    # Three REDUNDANT autostash entries: each stashes the SAME final content (working tree
    # resets to HEAD after each stash, so each entry is "v2 -> final"), then that content is
    # committed -- so every entry's diff reverse-applies cleanly against current HEAD.
    for _ in 1 2 3; do
        echo "final" > plans/active/issues/doc.md
        git stash push -q -m "autostash" -- plans/active/issues/doc.md
    done
    echo "final" > plans/active/issues/doc.md
    git add plans/active/issues/doc.md
    git commit -qm "commit-final"
    # One named stash (peer WIP) that must survive.
    echo "peer-wip" > plans/active/issues/doc.md
    git stash push -q -m "orchestrator-slot-9-peer-wip" -- plans/active/issues/doc.md
    # 3 autostash + 1 named = 4 entries
    run git stash list
    [[ "$output" == *"autostash"* ]]
    [[ "$output" == *"orchestrator-slot-9-peer-wip"* ]]

    run autostash_chain_guard_bound_backlog "$BRANCH" 1
    [ "$status" -eq 0 ]
    run git stash list
    # the named peer-WIP stash survives; the 3 redundant autostash entries are pruned to ≤1
    [[ "$output" == *"orchestrator-slot-9-peer-wip"* ]]
    run bash -c 'git stash list | grep -c ": autostash"'
    [ "$output" -le 1 ]
}
