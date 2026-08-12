#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_pretooluse_slot_collision_guard.bats — cursor-configs/hooks/pretooluse-slot-collision-guard.py
#
# Operator ruling 2026-08-12, option B in
# pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md: re-check slot occupancy at the
# MOMENT OF MUTATION, not only at session start. The session-start warning fires once and scrolls
# away; the measured incident had the peer arrive later and destroy uncommitted work twice inside
# 30 minutes.
#
# The operator explicitly accepted the cost that "a mid-task block is far more expensive per false
# positive than a skippable warning" — so the false-positive surface is what most of this file
# tests. The blocking cases are 6 of 17; the rest pin the things that must KEEP WORKING.
#
# Peer simulation is the same real-process technique as test_session_start_collision_check.bats
# (argv0 renamed so `pgrep -f claude` matches, cwd pointed at a fake slot) — the only way to
# exercise the detection rather than just the arg parsing.
#
# Run: bats tests/test_pretooluse_slot_collision_guard.bats

setup() {
    _PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    GUARD="${_PM_ROOT}/cursor-configs/hooks/pretooluse-slot-collision-guard.py"
    SCRATCH="${BATS_TEST_TMPDIR}/scratch"
    SLOT="${SCRATCH}/.tabs/77/unified-trading-pm"
    mkdir -p "${SLOT}"
    _PEER_PIDS=()
}

teardown() {
    local p
    for p in "${_PEER_PIDS[@]:-}"; do
        [ -n "${p}" ] && kill "${p}" 2>/dev/null || true
    done
}

_spawn_fake_peer() {
    ( cd "$1" && exec -a claude-bats-fake-peer sleep 20 ) &
    _PEER_PIDS+=("$!")
    sleep 0.3
}

# Feed the guard a PreToolUse payload. $1 command, $2 cwd.
_run_guard() {
    printf '{"tool_name":"Bash","tool_input":{"command":%s},"cwd":%s}' \
        "$(printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
        "$(printf '%s' "$2" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
        | python3 "${GUARD}"
}

# ── must BLOCK: a shared-index mutation with a live peer in the slot ───────────────────────────

@test "git commit is BLOCKED when a live peer occupies the slot" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'git commit -m "wip"' "${SLOT}"
    [ "$status" -eq 2 ]
    [[ "$output" == *"BLOCKED"* ]]
    [[ "$output" == *"another live Claude session"* ]]
    # The block must be actionable: name the remedy AND the escape hatch, or it is just a wall.
    [[ "$output" == *"ship-from-worktree.sh"* ]]
    [[ "$output" == *"SLOT_COLLISION_GUARD=0"* ]]
}

@test "quickmerge --no-isolated is BLOCKED (it commits from the shared index)" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'bash scripts/quickmerge.sh "msg" --agent --no-isolated --files x.py' "${SLOT}"
    [ "$status" -eq 2 ]
    [[ "$output" == *"shared index"* ]]
}

@test "safe-doc-push with SDP_ISOLATED=0 is BLOCKED" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'SDP_ISOLATED=0 bash scripts/dev/safe-doc-push.sh "msg" --files d.md' "${SLOT}"
    [ "$status" -eq 2 ]
    [[ "$output" == *"SDP_ISOLATED=0"* ]]
}

@test "git -C <path> commit is still recognised (option values are skipped, not mistaken for the subcommand)" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'git -C /some/path commit -m "wip"' "${SLOT}"
    [ "$status" -eq 2 ]
}

@test "a compound command hiding the commit is still recognised" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'cd /tmp && git add -A && git commit -m wip' "${SLOT}"
    [ "$status" -eq 2 ]
}

# ── must ALLOW: the false-positive surface the operator paid for ───────────────────────────────

@test "DEFAULT quickmerge is ALLOWED even with a live peer — it isolates, so it is the REMEDY" {
    # Blocking this would push an agent toward a bare `git commit`, which is strictly worse.
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'bash scripts/quickmerge.sh "msg" --agent --files x.py' "${SLOT}"
    [ "$status" -eq 0 ]
}

@test "DEFAULT safe-doc-push is ALLOWED even with a live peer" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'bash scripts/dev/safe-doc-push.sh "msg" --files d.md' "${SLOT}"
    [ "$status" -eq 0 ]
}

@test "git commit is ALLOWED when no peer occupies the slot" {
    run _run_guard 'git commit -m "wip"' "${SLOT}"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "SLOT_COLLISION_GUARD=0 as a COMMAND PREFIX allows the command even with a live peer" {
    # Matched in the command string, not this process's environment. The hook is a child of the
    # CLI, not of the user's command, so `VAR=0 cmd` never reaches its own environ — an env read
    # would have been an escape hatch that silently did nothing.
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'SLOT_COLLISION_GUARD=0 git commit -m "wip"' "${SLOT}"
    [ "$status" -eq 0 ]
}

@test "the escape hatch in the ENVIRONMENT alone does NOT unblock (it cannot be seen from here)" {
    _spawn_fake_peer "${SLOT}"
    run env SLOT_COLLISION_GUARD=0 bash -c "printf '%s' '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"git commit -m x\"},\"cwd\":\"${SLOT}\"}' | python3 '${GUARD}'"
    [ "$status" -eq 2 ]
}

@test "a cwd outside any .tabs/<N> slot is ALLOWED (no shared-checkout hazard modelled there)" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'git commit -m "wip"' "${SCRATCH}"
    [ "$status" -eq 0 ]
}

@test "read-only git commands are never matched" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'git log --grep=commit --oneline' "${SLOT}"
    [ "$status" -eq 0 ]
    run _run_guard 'git status --porcelain' "${SLOT}"
    [ "$status" -eq 0 ]
    run _run_guard 'git show HEAD:scripts/quickmerge.sh' "${SLOT}"
    [ "$status" -eq 0 ]
}

@test "the word 'commit' inside a quoted message does not self-match" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'echo "how do I commit this"' "${SLOT}"
    [ "$status" -eq 0 ]
}

@test "a non-Bash tool is ignored" {
    _spawn_fake_peer "${SLOT}"
    run bash -c "printf '%s' '{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"/x\"},\"cwd\":\"${SLOT}\"}' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
}

# ── fail-open: a guard that blocks on its own bug would wedge every commit ─────────────────────

@test "malformed JSON fails OPEN" {
    run bash -c "printf 'not json at all' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
}

@test "empty stdin fails OPEN" {
    run bash -c "printf '' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
}

@test "unbalanced quotes in the command fail OPEN (unparseable is not a verdict)" {
    _spawn_fake_peer "${SLOT}"
    run _run_guard 'git commit -m "unterminated' "${SLOT}"
    [ "$status" -eq 0 ]
}
