#!/usr/bin/env bats
# test_slot_git_status_loopback_preference.bats — unit tests for the
# loopback-preference fix in slot-git-status-report.sh
#   (git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
#    orchestrator_jwt_secret_not_pinned_causes_fleet_git_status_outage_2026_07_24.md,
#    folded into /plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3).
#
# HERMETIC: no real network calls to the orchestrator. The "loopback reachable" cases
# spin up a throwaway python3 HTTP server bound to 127.0.0.1:0 (OS-assigned free port)
# that answers every GET with 200, and point LOOPBACK_ORCH_URL at it via the script's
# own override env var — never touches the real :8765 orchestrator. The "unreachable"
# case points at a closed local port so curl's connection-refused is near-instant.
#
# Mirrors tests/test_slot_git_status_dirty_count.bats's hermetic-source pattern: source
# the real script (functions + top-level loopback-probe logic run once) with --workspace
# pointed at an EMPTY .tabs/ dir + --quiet, so the main slot-walking loop at the bottom
# is a no-op and never POSTs anything real.
#
# Run: bats tests/test_slot_git_status_loopback_preference.bats
# Run all: bats tests/

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup_file() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    REPORTER_ABS="$(cd "${WS_ROOT}/$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    echo "${REPORTER_ABS}" > "${BATS_FILE_TMPDIR}/reporter_abs"

    # Throwaway "always 200" HTTP server on an OS-assigned free port — this stands in
    # for the real orchestrator's /api/healthz for the "loopback reachable" tests.
    HEALTH_LOG="${BATS_FILE_TMPDIR}/health_server.log"
    python3 -c '
import http.server, socketserver

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            self.rfile.read(length)
        self.send_response(200)
        self.end_headers()

    def log_message(self, *_a):
        pass

socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer(("127.0.0.1", 0), H)
print(httpd.server_address[1], flush=True)
httpd.serve_forever()
' > "${HEALTH_LOG}" 2>&1 &
    echo "$!" > "${BATS_FILE_TMPDIR}/health_pid"

    # Wait (max ~2s) for the server to print its assigned port.
    for _ in $(seq 1 40); do
        [[ -s "${HEALTH_LOG}" ]] && break
        sleep 0.05
    done
    head -n1 "${HEALTH_LOG}" > "${BATS_FILE_TMPDIR}/health_port"
}

teardown_file() {
    if [[ -f "${BATS_FILE_TMPDIR}/health_pid" ]]; then
        kill "$(cat "${BATS_FILE_TMPDIR}/health_pid")" 2>/dev/null || true
    fi
}

setup() {
    REPORTER_ABS="$(cat "${BATS_FILE_TMPDIR}/reporter_abs")"
    HEALTH_PORT="$(cat "${BATS_FILE_TMPDIR}/health_port")"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"
    FAKE_HOME="${BATS_TEST_TMPDIR}/fake_home_$$_${RANDOM}"
    mkdir -p "${FAKE_HOME}"
}

# Source the reporter with the given env + extra CLI args, then dump the resolved
# ORCH_URL / IS_LOOPBACK / _ORCH_URL_EXPLICIT globals. HOME is pinned to an empty
# fake dir so a real ~/.orch_token on the host never leaks into these assertions.
_probe() {
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet "$@"
        printf "ORCH_URL=%s\nIS_LOOPBACK=%s\nEXPLICIT=%s\n" \
            "${ORCH_URL}" "${IS_LOOPBACK}" "${_ORCH_URL_EXPLICIT}"
    ' _ "$@"
}

@test "no --orch-url, loopback reachable -> prefers loopback, IS_LOOPBACK=1" {
    LOOPBACK_ORCH_URL="http://127.0.0.1:${HEALTH_PORT}" run _probe
    [ "$status" -eq 0 ]
    [[ "$output" == *"ORCH_URL=http://127.0.0.1:${HEALTH_PORT}"* ]]
    [[ "$output" == *"IS_LOOPBACK=1"* ]]
    [[ "$output" == *"EXPLICIT=0"* ]]
}

@test "no --orch-url, loopback unreachable -> stays on public default, IS_LOOPBACK=0" {
    # Nothing is listening on this port — the reserved 127.0.0.1:1 requires a
    # privileged bind and refuses instantly, keeping the test fast.
    LOOPBACK_ORCH_URL="http://127.0.0.1:1" run _probe
    [ "$status" -eq 0 ]
    [[ "$output" == *"ORCH_URL=https://api.agent-orchestrator.odum-research.com"* ]]
    [[ "$output" == *"IS_LOOPBACK=0"* ]]
}

@test "explicit --orch-url flag wins even when loopback is reachable" {
    LOOPBACK_ORCH_URL="http://127.0.0.1:${HEALTH_PORT}" run _probe --orch-url "https://explicit.example.test"
    [ "$status" -eq 0 ]
    [[ "$output" == *"ORCH_URL=https://explicit.example.test"* ]]
    [[ "$output" == *"IS_LOOPBACK=0"* ]]
    [[ "$output" == *"EXPLICIT=1"* ]]
}

@test "explicit ORCH_URL env var wins even when loopback is reachable" {
    LOOPBACK_ORCH_URL="http://127.0.0.1:${HEALTH_PORT}" ORCH_URL="https://explicit-env.example.test" run _probe
    [ "$status" -eq 0 ]
    [[ "$output" == *"ORCH_URL=https://explicit-env.example.test"* ]]
    [[ "$output" == *"IS_LOOPBACK=0"* ]]
    [[ "$output" == *"EXPLICIT=1"* ]]
}

# ── resolve_token_for_slot: loopback tolerates a missing token, off-VM does not ──

_resolve_token() { # $1 = IS_LOOPBACK (0|1)
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet
        IS_LOOPBACK="$1"
        HOME="'"${FAKE_HOME}"'"
        TABS_DIR="'"${EMPTY_WS}"'/.tabs"
        TOKEN_FILE=""
        out=$(resolve_token_for_slot 99)
        rc=$?
        printf "rc=%s out=[%s]\n" "$rc" "$out"
    ' _ "$1"
}

@test "resolve_token_for_slot: loopback mode + no token anywhere -> succeeds with empty token" {
    run _resolve_token 1
    [ "$status" -eq 0 ]
    [[ "$output" == "rc=0 out=[]" ]]
}

@test "resolve_token_for_slot: off-VM mode + no token anywhere -> fails (unchanged behaviour)" {
    run _resolve_token 0
    [ "$status" -eq 0 ]
    [[ "$output" == "rc=1 out=[]" ]]
}

# ── post_snapshot: omits the Authorization header entirely when token is empty ──

@test "post_snapshot with an empty token sends no Authorization header (loopback, real POST to the fake server)" {
    # Point the reporter's ORCH_URL straight at the throwaway 200-server (no
    # /api/slots/.../git-status route on it, so it just answers 200 for anything —
    # good enough to prove the request is sent WITHOUT crashing on an empty header
    # and that curl doesn't error building the command).
    #
    # This test's own name says "loopback" -- resolve_token_for_slot()'s empty-token
    # success path only fires when IS_LOOPBACK=1 (its last fallback: `[[ "$IS_LOOPBACK"
    # -eq 1 ]] && return 0` with no token). Neither the original nor an earlier fix attempt
    # ever forced that -- IS_LOOPBACK was left to whatever the reporter's own source-time
    # probe against the REAL default orchestrator URL happened to resolve on the machine
    # running the test, which is not what "loopback" means here. Two ways this drifted:
    #   1. HOME left unpinned: resolve_token_for_slot() falls through to the AMBIENT $HOME
    #      and picks up a real operator's ~/.orch_token if one exists (it does on any laptop
    #      that has used the orchestrator locally), taking the non-empty-token branch --
    #      passed locally by accident, never exercising the empty-token path at all.
    #   2. IS_LOOPBACK unset: on a fresh CI runner (no ~/.orch_token, no /tmp/orch_token, no
    #      IS_LOOPBACK=1) resolve_token_for_slot() returns 1 (no token found ANYWHERE) and
    #      post_snapshot returns early with "[skip:no-token]" -- never reaching the curl
    #      POST this test exists to exercise, so "[ok] slot 99" never appeared.
    # Both found live 2026-08-13 contributing to a 12+ hour block of every PM promote-PR QG
    # slice. Pin HOME to the empty fake dir AND force IS_LOOPBACK=1 so the test deterministically
    # exercises the exact path its own name claims, regardless of the host's ambient state.
    run bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet
        HOME="'"${FAKE_HOME}"'"
        IS_LOOPBACK=1
        ORCH_URL="http://127.0.0.1:'"${HEALTH_PORT}"'"
        post_snapshot 99 "$(printf "repo\tmain\tclean\t0\t0\t0\tabc123\tlive-defi-rollout\t\t\t\n")"
    '
    [ "$status" -eq 0 ]
    [[ "$output" == *"[ok] slot 99"* ]]
}
