#!/usr/bin/env bats
# test_slot_git_status_token_expiry.bats — unit tests for the token-near-expiry early
# warning in slot-git-status-report.sh (decode_jwt_exp / check_token_expiry_for_slot)
#   (git_status_reporter_stale_public_url_token_expiry_2026_07_24.md option (a),
#    /plans/active/ao_satellite_ao_dispatch_batch16_2026_08_09.md todo 1).
#
# HERMETIC: no real network calls to the orchestrator. Mirrors
# tests/test_slot_git_status_loopback_preference.bats's throwaway-HTTP-server pattern:
# spins up a python3 HTTP server bound to 127.0.0.1:0 that answers every POST with 200
# and logs each request body to a file, then points --orch-url at it explicitly (so the
# loopback auto-probe never fires and this never touches the real :8765 orchestrator).
# Also mirrors tests/test_slot_git_status_dirty_count.bats's hermetic-source pattern:
# source the real script with --workspace pointed at an EMPTY .tabs/ dir + --quiet, so
# the main slot-walking loop is a no-op, then call the functions under test directly.
#
# Run: bats tests/test_slot_git_status_token_expiry.bats
# Run all: bats tests/

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup_file() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    REPORTER_ABS="$(cd "${WS_ROOT}/$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    echo "${REPORTER_ABS}" > "${BATS_FILE_TMPDIR}/reporter_abs"

    # Throwaway "always 200, log the body" HTTP server standing in for the real
    # orchestrator's /api/slots/<N>/message.
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
    STATE_DIR="${BATS_TEST_TMPDIR}/token-expiry-state_$$_${RANDOM}"
    TOKEN_FILE="${BATS_TEST_TMPDIR}/orch_token_$$_${RANDOM}"
    : > "${REQUESTS_LOG}"
}

# Build a throwaway (unsigned, structurally-valid) JWT with an `exp` claim
# `offset_secs` seconds from now (negative = already expired). Signature segment is
# arbitrary — decode_jwt_exp only reads the middle (payload) segment, never verifies.
_make_jwt() {
    local offset_secs="$1"
    python3 -c '
import base64, json, sys, time

def b64(d):
    return base64.urlsafe_b64encode(d).rstrip(b"=").decode()

offset = int(sys.argv[1])
header = b64(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
payload = b64(json.dumps({"sub": "test", "exp": int(time.time()) + offset}).encode())
print(f"{header}.{payload}.testsig")
' "${offset_secs}"
}

_check_expiry() {
    local slot_id="$1"
    bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --orch-url "'"${ORCH_URL}"'" --quiet
        TOKEN_EXPIRY_STATE_DIR="'"${STATE_DIR}"'"
        TOKEN_FILE="'"${TOKEN_FILE}"'"
        check_token_expiry_for_slot "'"${slot_id}"'"
    '
}

@test "decode_jwt_exp extracts the exp claim from a well-formed JWT" {
    now_plus_1h=$(( $(date -u +%s) + 3600 ))
    jwt=$(python3 -c '
import base64, json, sys, time
def b64(d): return base64.urlsafe_b64encode(d).rstrip(b"=").decode()
header = b64(json.dumps({"alg":"HS256"}).encode())
payload = b64(json.dumps({"exp": '"${now_plus_1h}"'}).encode())
print(f"{header}.{payload}.sig")
')
    run bash -c 'source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet; decode_jwt_exp "'"${jwt}"'"'
    [ "$status" -eq 0 ]
    [ "$output" = "${now_plus_1h}" ]
}

@test "decode_jwt_exp fails closed (empty output, non-zero) on a malformed token" {
    run bash -c 'source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --quiet; decode_jwt_exp "not-a-jwt"'
    [ "$status" -ne 0 ]
    [ -z "$output" ]
}

@test "near-expiry token (exp ~2 days out) fires exactly one warning event" {
    jwt=$(_make_jwt $(( 2 * 86400 )))
    printf '%s' "${jwt}" > "${TOKEN_FILE}"
    run _check_expiry 42
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]
    grep -q "/api/slots/42/message" "${REQUESTS_LOG}"
    grep -qi "near expiry" "${REQUESTS_LOG}"
    [ -f "${STATE_DIR}/slot-42.near-expiry" ]
}

@test "a second consecutive run with the same near-expiry exp does not re-fire" {
    jwt=$(_make_jwt $(( 2 * 86400 )))
    printf '%s' "${jwt}" > "${TOKEN_FILE}"
    _check_expiry 43
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]
    run _check_expiry 43
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 1 ]
}

@test "a run after a re-mint (exp far in the future) clears the near-expiry state" {
    jwt_near=$(_make_jwt $(( 2 * 86400 )))
    printf '%s' "${jwt_near}" > "${TOKEN_FILE}"
    _check_expiry 44
    [ -f "${STATE_DIR}/slot-44.near-expiry" ]

    jwt_far=$(_make_jwt $(( 30 * 86400 )))
    printf '%s' "${jwt_far}" > "${TOKEN_FILE}"
    run _check_expiry 44
    [ "$status" -eq 0 ]
    [ ! -f "${STATE_DIR}/slot-44.near-expiry" ]

    # And a fresh near-expiry episode after that re-warns (marker cleared, not permanent).
    printf '%s' "${jwt_near}" > "${TOKEN_FILE}"
    run _check_expiry 44
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 2 ]
    [ -f "${STATE_DIR}/slot-44.near-expiry" ]
}

@test "a token well outside the warn window never fires and never creates a marker" {
    jwt=$(_make_jwt $(( 30 * 86400 )))
    printf '%s' "${jwt}" > "${TOKEN_FILE}"
    run _check_expiry 45
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 0 ]
    [ ! -f "${STATE_DIR}/slot-45.near-expiry" ]
}

@test "TOKEN_EXPIRY_WATCHDOG=0 disables the check entirely" {
    jwt=$(_make_jwt $(( 2 * 86400 )))
    printf '%s' "${jwt}" > "${TOKEN_FILE}"
    run bash -c '
        source "'"${REPORTER_ABS}"'" --workspace "'"${EMPTY_WS}"'" --orch-url "'"${ORCH_URL}"'" --quiet
        TOKEN_EXPIRY_STATE_DIR="'"${STATE_DIR}"'"
        TOKEN_FILE="'"${TOKEN_FILE}"'"
        TOKEN_EXPIRY_WATCHDOG=0
        check_token_expiry_for_slot 46
    '
    [ "$status" -eq 0 ]
    [ "$(wc -l < "${REQUESTS_LOG}")" -eq 0 ]
}
