#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_pretooluse_bare_root_write_guard.bats — cursor-configs/hooks/pretooluse-bare-root-write-guard.py
#
# Measured incident (model_capability_aware_dispatch_audit_2026_08_21.md Progress Log,
# 2026-08-21): a confused sequence of backgrounded Bash commands left an interactive session
# believing it was editing `.tabs/13/agent-orchestrator` while several `Edit` calls actually
# landed in the BARE `agent-orchestrator` checkout (`orchestrator.service`'s live
# WorkingDirectory), wedging `ao-self-pull.sh` for 20+ minutes. This guard is a NEVER-BLOCK
# visibility backstop (`permissionDecision: allow` + `additionalContext`) for exactly that class
# of drift — so the false-positive surface is not "does this wrongly block a legitimate edit"
# (it structurally cannot), it is "does this warn on the right paths and stay silent everywhere
# else". Every test asserts `status -eq 0` — a non-zero exit would itself be a regression of the
# hook's own core contract.
#
# Run: bats tests/test_pretooluse_bare_root_write_guard.bats

setup() {
    _PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    GUARD="${_PM_ROOT}/cursor-configs/hooks/pretooluse-bare-root-write-guard.py"
    SCRATCH="${BATS_TEST_TMPDIR}/scratch"
    # workspace_root_for() looks for an ancestor that contains a `.tabs` dir — SCRATCH is that
    # ancestor here, mirroring the real /home/ubuntu/unified-trading-system-repos shape.
    mkdir -p "${SCRATCH}/.tabs/77/myrepo"
    mkdir -p "${SCRATCH}/myrepo/server"
    mkdir -p "${SCRATCH}/orphanrepo/server"   # bare checkout with NO .tabs sibling
}

# Feed the guard a PreToolUse payload. $1 tool_name, $2 file_path.
_run_guard() {
    printf '{"tool_name":"%s","tool_input":{"file_path":%s}}' \
        "$1" \
        "$(printf '%s' "$2" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')" \
        | python3 "${GUARD}"
}

# ── must WARN: a bare-root Edit/Write with a live slot sibling for the same repo ────────────────

@test "Edit to a bare-root path IS warned when a .tabs sibling exists for the repo" {
    run _run_guard "Edit" "${SCRATCH}/myrepo/server/autospawn.py"
    [ "$status" -eq 0 ]
    [[ "$output" == *"BARE-ROOT WRITE WARNING"* ]]
    [[ "$output" == *"myrepo"* ]]
    [[ "$output" == *"permissionDecision"* ]]
    [[ "$output" == *"\"allow\""* ]]
    [[ "$output" == *"additionalContext"* ]]
}

@test "Write to a bare-root path is ALSO warned (not just Edit)" {
    run _run_guard "Write" "${SCRATCH}/myrepo/server/new_module.py"
    [ "$status" -eq 0 ]
    [[ "$output" == *"BARE-ROOT WRITE WARNING"* ]]
}

@test "the warning names the correct .tabs slot path form, not just the repo" {
    run _run_guard "Edit" "${SCRATCH}/myrepo/server/autospawn.py"
    [ "$status" -eq 0 ]
    [[ "$output" == *".tabs/<N>/myrepo"* ]]
}

# ── must stay SILENT: the false-positive surface ────────────────────────────────────────────────

@test "an Edit already inside a .tabs/<N>/ slot is SILENT" {
    run _run_guard "Edit" "${SCRATCH}/.tabs/77/myrepo/server/autospawn.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a bare-root Edit for a repo with NO .tabs sibling is SILENT (never used the slot model)" {
    run _run_guard "Edit" "${SCRATCH}/orphanrepo/server/thing.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a non-Edit/Write tool (Bash) is ignored even with a bare-root-shaped path in its input" {
    run bash -c "printf '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"cat ${SCRATCH}/myrepo/server/x.py\"}}' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a non-Edit/Write tool (Read) is ignored" {
    run _run_guard "Read" "${SCRATCH}/myrepo/server/autospawn.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a path entirely outside any workspace-root-with-.tabs structure is SILENT" {
    run _run_guard "Edit" "/tmp/some-scratch-file-unrelated-to-any-repo.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

# ── fail-open: a guard that ever blocks on its own bug defeats its purpose ──────────────────────

@test "malformed JSON fails OPEN (never blocks, no output)" {
    run bash -c "printf 'not json at all' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "empty stdin fails OPEN" {
    run bash -c "printf '' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a missing file_path fails OPEN" {
    run bash -c "printf '{\"tool_name\":\"Edit\",\"tool_input\":{}}' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a non-string file_path fails OPEN" {
    run bash -c "printf '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":123}}' | python3 '${GUARD}'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "exit status is 0 even on the WARN path — this guard can never block" {
    run _run_guard "Edit" "${SCRATCH}/myrepo/server/autospawn.py"
    [ "$status" -eq 0 ]
}
