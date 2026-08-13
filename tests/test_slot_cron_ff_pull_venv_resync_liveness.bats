#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for slot-cron-ff-pull.sh's venv-resync liveness check
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo A).
#
# THE BUG: `_resync_venv_if_lock_moved` decided whether a test/gate was live in this
# directory via `pgrep -af 'pytest|quality-gates|basedpyright' 2>/dev/null | grep -qF
# "${PWD}"` — a SUBSTRING test against the matched process's full command-line TEXT,
# not "does this process's cwd equal here". The dangerous direction is a false
# NEGATIVE: a genuinely-live gate whose command line does not happen to literally spell
# out $PWD (invoked via a relative path, a wrapper, an alias) is invisible to this
# check, so `uv sync --frozen` proceeds concurrently with it — and this same issue doc
# already establishes that `uv sync --frozen` can PRUNE a live environment out from
# under a running process. Same pattern-only-matching class as the async-wait-and-poll
# SSOT's `_ens_persist.py` self-match incident.
#
# THE FIX: resolve each candidate PID's REAL cwd via `_cwd_of`
# (cursor-configs/hooks/lib/slot-collision-detect.sh, portable macOS/Linux) and require
# an EXACT match against $PWD, not a text-containment test against argv.
#
# This test exercises the fixed loop directly (stubbing pgrep + _cwd_of), rather than
# driving the full function through real uv/venv fixtures — the loop's match semantics
# are the thing that changed, and that is what a regression here would break.

setup() {
    REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    LIB="${REPO_ROOT}/cursor-configs/hooks/lib/slot-collision-detect.sh"
    [ -f "$LIB" ]
}

# Builds a harness that stubs `pgrep` to emit the given PIDs and `_cwd_of` to map each
# PID to a fixed cwd string (via a case statement baked from $1, "pid:cwd pid:cwd ..."),
# then runs the exact matching loop from _resync_venv_if_lock_moved against $PWD=$2.
run_liveness_loop() {
    local pid_cwd_map="$1" here="$2"
    local harness="${BATS_TEST_TMPDIR}/harness.sh"
    {
        echo "source '${LIB}'"
        echo "pgrep() { printf '%s\n' $(printf '%s' "$pid_cwd_map" | awk '{for(i=1;i<=NF;i++){split($i,a,":");printf "%s ", a[1]}}'); }"
        echo "_cwd_of() {"
        echo "  case \"\$1\" in"
        for pair in $pid_cwd_map; do
            local pid="${pair%%:*}" cwd="${pair#*:}"
            echo "    ${pid}) printf '%s' '${cwd}' ;;"
        done
        echo "  esac"
        echo "}"
        echo "PWD='${here}'"
        cat <<'LOOP'
_here_real="$(readlink -f "${PWD}" 2>/dev/null || echo "${PWD}")"
_gate_here=0
for _cand_pid in $(pgrep -f 'pytest|quality-gates|basedpyright' 2>/dev/null || true); do
    [[ "$(_cwd_of "${_cand_pid}")" == "${_here_real}" ]] && { _gate_here=1; break; }
done
echo "GATE=${_gate_here}"
LOOP
    } >"$harness"
    bash "$harness"
}

@test "a candidate process whose REAL cwd exactly matches here triggers the gate" {
    run run_liveness_loop "111:/repo/here" "/repo/here"
    [ "$status" -eq 0 ]
    [[ "$output" == *"GATE=1"* ]]
}

@test "a candidate process in a DIFFERENT directory that merely shares a path prefix does NOT trigger the gate (the old substring bug's false-positive direction)" {
    run run_liveness_loop "111:/repo/here/nested" "/repo/here"
    [ "$status" -eq 0 ]
    [[ "$output" == *"GATE=0"* ]]
}

@test "no candidate processes -> no gate" {
    run run_liveness_loop "" "/repo/here"
    [ "$status" -eq 0 ]
    [[ "$output" == *"GATE=0"* ]]
}

@test "multiple candidates, only one matching, still triggers the gate" {
    run run_liveness_loop "111:/repo/elsewhere 222:/repo/here 333:/repo/other" "/repo/here"
    [ "$status" -eq 0 ]
    [[ "$output" == *"GATE=1"* ]]
}

@test "the script still parses after the fix" {
    run bash -n "${REPO_ROOT}/scripts/dev/slot-cron-ff-pull.sh"
    [ "$status" -eq 0 ]
}

@test "the substring-only pattern is gone from the live matching path" {
    # Pin against regressing back to grep -qF "${PWD}" as the PRIMARY mechanism -- the
    # degraded fallback (lib missing) is allowed to keep it, so scope the check to the
    # exact-cwd line instead of a blanket absence assertion.
    run grep -c '_cwd_of' "${REPO_ROOT}/scripts/dev/slot-cron-ff-pull.sh"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}
