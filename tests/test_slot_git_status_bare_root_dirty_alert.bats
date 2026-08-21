#!/usr/bin/env bats
# test_slot_git_status_bare_root_dirty_alert.bats — unit tests for the slot-0 bare-root
# dirty/untracked alert watchdog in slot-git-status-report.sh
# (check_bare_root_dirty_for_slot0), closing bare_root_repo_agent_writes_unenforced_2026_08_21.md's
# P1: a DIRTY/untracked verdict on a bare-root checkout previously reached only
# post_snapshot (passive dashboard telemetry, no alert) — this watchdog reuses the SAME
# dedup-per-episode ping pattern check_starvation_for_slot/check_stash_pile_for_slot
# already use for the numbered-slot loop.
#
# HERMETIC: no real network calls to the orchestrator. Mirrors
# tests/test_slot_git_status_token_expiry.bats's throwaway-HTTP-server pattern (spins up a
# python3 HTTP server on 127.0.0.1:0 that answers every POST with 200 and logs the body).
#
# Rows are HAND-BUILT via _row() (classify_repo's documented 14-field TSV shape) rather
# than routed through a real git repo: this suite tests check_bare_root_dirty_for_slot0's
# OWN parsing/dedup/ping logic in isolation, given a specific `state` verdict as input.
# classify_repo's own state-precedence correctness (incl. untracked files folding into
# "dirty") is already exhaustively covered by tests/test_slot_git_status_dirty_count.bats.
#
# Run: bats tests/test_slot_git_status_bare_root_dirty_alert.bats
# Run all: bats tests/

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup_file() {
    # ORDER-INDEPENDENT within a test, but shares one HTTP server + REQUESTS_LOG across
    # tests in this file (mirrors test_slot_git_status_token_expiry.bats) — keep serial
    # within the file so two tests' request counts never interleave.
    export BATS_NO_PARALLELIZE_WITHIN_FILE=true
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    REPORTER_ABS="$(cd "${WS_ROOT}/$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    echo "${REPORTER_ABS}" > "${BATS_FILE_TMPDIR}/reporter_abs"

    # Throwaway "always 200, log the body" HTTP server standing in for the real
    # orchestrator's /api/slots/0/message.
    SERVER_LOG="${BATS_FILE_TMPDIR}/server.log"
    REQUESTS_LOG="${BATS_FILE_TMPDIR}/requests.log"
    : > "${REQUESTS_LOG}"
    python3 -c '
import http.server, socketserver, sys

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        body = self.rfile.read(length) if length else b""
        with open(sys.argv[1], "a") as f:
            f.write(self.path + "\t" + body.decode("utf-8", "replace") + "\n")
        self.send_response(200)
        self.end_headers()

    def log_message(self, *_a):
        pass

socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
print(httpd.server_address[1], flush=True)
httpd.serve_forever()
' "${REQUESTS_LOG}" > "${SERVER_LOG}" 2>&1 &
    echo "$!" > "${BATS_FILE_TMPDIR}/server_pid"

    for _ in $(seq 1 40); do
        [[ -s "${SERVER_LOG}" ]] && break
        sleep 0.05
    done
    SERVER_PORT="$(head -1 "${SERVER_LOG}")"
    echo "${SERVER_PORT}" > "${BATS_FILE_TMPDIR}/server_port"
}

teardown_file() {
    if [[ -f "${BATS_FILE_TMPDIR}/server_pid" ]]; then
        kill "$(cat "${BATS_FILE_TMPDIR}/server_pid")" 2>/dev/null || true
    fi
}

setup() {
    REPORTER_ABS="$(cat "${BATS_FILE_TMPDIR}/reporter_abs")"
    SERVER_PORT="$(cat "${BATS_FILE_TMPDIR}/server_port")"
    ORCH_URL="http://127.0.0.1:${SERVER_PORT}"
    REQUESTS_LOG="${BATS_FILE_TMPDIR}/requests.log"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"
    # Harmless dummy — resolve_token_for_slot's _token_is_expired can't decode it as a JWT,
    # which per its own "can't tell = don't misread as an emergency" contract means "treat
    # as usable" (see decode_jwt_exp's header comment in the reporter). This keeps the test
    # from ever falling through to a real ~/.orch_token on this host.
    TOKEN_FILE="${BATS_TEST_TMPDIR}/orch_token_$$_${RANDOM}"
    printf 'test-token-do-not-use' > "${TOKEN_FILE}"
    : > "${REQUESTS_LOG}"
}

# Build one classify_repo()-shaped TSV row (14 tab-separated fields — see that function's
# own header comment for the canonical column order: name, branch, state, dirty_files,
# ahead, behind, local_sha, int_branch, dirty_oldest_iso, unpushed_plans, dirty_sample,
# repo_dirty_ticks, ahead_oldest_iso, behind_oldest_iso).
_row() { # _row <name> <state> <dirty_files> <dirty_sample (pipe-separated, may be empty)>
    local name="$1" state="$2" df="$3" sample="$4"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s' \
        "${name}" "live-defi-rollout" "${state}" "${df}" "0" "0" "abc123def456" \
        "live-defi-rollout" "" "" "${sample}" "0" "" ""
}

_marker() { # _marker <repo-name>
    printf '%s/.tabs/.ff-starve-state/slot-0__%s.dirty-warn' "${EMPTY_WS}" "$1"
}

# Source the reporter pointed at the throwaway HTTP server, override TOKEN_FILE to the
# harmless dummy above, then call check_bare_root_dirty_for_slot0 with the given rows_tsv.
_check_bare_root() {
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --orch-url "'"${ORCH_URL}"'" --quiet
        TOKEN_FILE="'"${TOKEN_FILE}"'"
        check_bare_root_dirty_for_slot0 "$1"
    ' _ "$1"
}

@test "slot-git-status-report.sh has valid bash syntax after the bare-root watchdog addition" {
    run bash -n "${REPORTER_ABS}"
    [ "$status" -eq 0 ]
}

@test "one dirty bare-root repo fires exactly one alert and creates its marker" {
    row="$(_row "execution-service" "dirty" "2" "M  order_adapter.py|?? scratch.py")"

    run _check_bare_root "${row}"$'\n'
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]
    grep -q "/api/slots/0/message" "${REQUESTS_LOG}"
    grep -q "BARE-ROOT DIRTY" "${REQUESTS_LOG}"
    grep -q "execution-service" "${REQUESTS_LOG}"
    grep -qi "NEVER a worker's assigned" "${REQUESTS_LOG}"
    [ -f "$(_marker execution-service)" ]
}

@test "a second consecutive run on the same dirty repo does not re-fire (dedup)" {
    row="$(_row "unified-trading-system-ui" "dirty" "1" "M  lib/architecture-v2/coverage.ts")"

    _check_bare_root "${row}"$'\n'
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]
    # NOTE: --quiet suppresses log_quiet's "[bare-root-dirty-dup]" line (mirrors
    # test_slot_git_status_token_expiry.bats's equivalent test, which asserts the same
    # way) — the request count is the load-bearing proof that dedup actually held.
    run _check_bare_root "${row}"$'\n'
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]
}

@test "repo going clean again clears the marker, and a fresh dirty episode re-fires" {
    dirty_row="$(_row "agent-orchestrator" "dirty" "1" "?? instruments-service/scripts/stray.py")"
    _check_bare_root "${dirty_row}"$'\n'
    [ -f "$(_marker agent-orchestrator)" ]

    clean_row="$(_row "agent-orchestrator" "clean" "0" "")"
    run _check_bare_root "${clean_row}"$'\n'
    [ "$status" -eq 0 ]
    [ ! -f "$(_marker agent-orchestrator)" ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]

    dirty_again_row="$(_row "agent-orchestrator" "dirty" "1" "M  foo.py")"
    run _check_bare_root "${dirty_again_row}"$'\n'
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 2 ]
    [ -f "$(_marker agent-orchestrator)" ]
}

@test "non-dirty states (clean, ahead, behind, diverged, detached, no-remote-ref) never fire" {
    for state in clean ahead behind diverged detached no-remote-ref; do
        row="$(_row "repo-${state}" "${state}" "0" "")"
        run _check_bare_root "${row}"$'\n'
        [ "$status" -eq 0 ]
    done
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 0 ]
    for state in clean ahead behind diverged detached no-remote-ref; do
        [ ! -f "$(_marker "repo-${state}")" ]
    done
}

@test "two dirty bare-root repos in one sweep each get their own independent alert + marker" {
    rows="$(_row "execution-service" "dirty" "2" "M  a.py")"$'\n'"$(_row "unified-trading-system-ui" "dirty" "1" "M  b.ts")"$'\n'

    run _check_bare_root "${rows}"
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 2 ]
    grep -q "execution-service" "${REQUESTS_LOG}"
    grep -q "unified-trading-system-ui" "${REQUESTS_LOG}"
    [ -f "$(_marker execution-service)" ]
    [ -f "$(_marker unified-trading-system-ui)" ]
}

@test "BARE_ROOT_DIRTY_WATCHDOG=0 disables the check entirely" {
    row="$(_row "execution-service" "dirty" "2" "M  a.py")"

    run bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --orch-url "'"${ORCH_URL}"'" --quiet
        TOKEN_FILE="'"${TOKEN_FILE}"'"
        BARE_ROOT_DIRTY_WATCHDOG=0
        check_bare_root_dirty_for_slot0 "$1"
    ' _ "${row}"$'\n'
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 0 ]
    [ ! -f "$(_marker execution-service)" ]
}
