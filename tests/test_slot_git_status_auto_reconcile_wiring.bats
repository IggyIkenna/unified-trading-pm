#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_slot_git_status_auto_reconcile_wiring.bats — unit tests for the auto-reconcile-before-page
# wiring added to slot-git-status-report.sh's check_starvation_for_slot() (2026-08-19).
#
# Isolates the WIRING from the reconcile decision-making itself (that logic has its own full
# coverage in tests/test_auto_reconcile_starved_repo.bats) — STARVE_DETECTOR and
# AUTO_RECONCILE_SCRIPT are both replaced with tiny stub scripts here, so these tests only prove:
# a starved repo's ping is suppressed and the marker cleared when auto-reconcile reports silent
# success; a starved repo still pages, but with the auto-reconcile script's OWN payload (not the
# bare starve message), when auto-reconcile declines/fails; and AUTO_RECONCILE_STARVED=0 restores
# the pre-2026-08-19 behavior exactly (pages with the original starve payload, auto-reconcile
# never invoked).
#
# HERMETIC: mirrors test_slot_git_status_dirty_count.bats's sourcing pattern — the real script is
# sourced with an EMPTY --workspace so its main slot-walking loop is a no-op, then
# check_starvation_for_slot is called directly against a hand-built slot dir.
#
# Run: bats tests/test_slot_git_status_auto_reconcile_wiring.bats

REPORTER="unified-trading-pm/scripts/dev/slot-git-status-report.sh"

setup() {
    WS_ROOT="$(git rev-parse --show-toplevel)/.."
    cd "${WS_ROOT}" || cd ..
    REPORTER_ABS="$(cd "$(dirname "${REPORTER}")" && pwd)/$(basename "${REPORTER}")"
    EMPTY_WS="${BATS_TEST_TMPDIR}/empty_ws_$$_${RANDOM}"
    mkdir -p "${EMPTY_WS}/.tabs"

    # A minimal real git repo to stand in for the starved repo -- content is irrelevant since
    # STARVE_DETECTOR is stubbed; only its existence as a `.git`-containing dir matters (the real
    # check_starvation_for_slot's for-loop requires it).
    REPO_DIR="${BATS_TEST_TMPDIR}/slotdir/some-repo"
    mkdir -p "${REPO_DIR}"
    ( cd "${REPO_DIR}" && git init -q && git config user.email t@t.t && git config user.name t )
    SLOT_DIR="${BATS_TEST_TMPDIR}/slotdir/"

    PING_LOG="${BATS_TEST_TMPDIR}/pings.log"
    : > "${PING_LOG}"

    STUB_DETECTOR="${BATS_TEST_TMPDIR}/stub_detector.sh"
    printf '#!/usr/bin/env bash\necho "ORIGINAL STARVE PAYLOAD for some-repo"\n' > "${STUB_DETECTOR}"
    chmod +x "${STUB_DETECTOR}"
}

# $1 = stub auto-reconcile script's stdout+exit ("" = silent success; non-empty = its payload)
# $2 = AUTO_RECONCILE_STARVED value ("1" or "0")
_run_check_starvation() {
    local recon_output="$1" toggle="$2"
    local stub_reconcile="${BATS_TEST_TMPDIR}/stub_reconcile.sh"
    if [[ -n "${recon_output}" ]]; then
        printf '#!/usr/bin/env bash\nprintf %%s %s\n' "$(printf '%q' "${recon_output}")" > "${stub_reconcile}"
    else
        printf '#!/usr/bin/env bash\nexit 0\n' > "${stub_reconcile}"
    fi
    chmod +x "${stub_reconcile}"

    local harness="${BATS_TEST_TMPDIR}/harness.sh"
    {
        echo "source '${REPORTER_ABS}' --workspace '${EMPTY_WS}' --quiet"
        echo "STARVE_DETECTOR='${STUB_DETECTOR}'"
        echo "AUTO_RECONCILE_SCRIPT='${stub_reconcile}'"
        echo "AUTO_RECONCILE_STARVED=${toggle}"
        echo "resolve_token_for_slot() { printf 'dummy-token'; return 0; }"
        echo "post_starve_ping() {"
        echo "  printf '%s\t%s\t%s\n' \"\$1\" \"\$2\" \"\$3\" >> '${PING_LOG}'"
        echo "  return 0"
        echo "}"
        echo "check_starvation_for_slot 99 '${SLOT_DIR}'"
    } > "${harness}"
    bash "${harness}"
}

@test "auto-reconcile silent success -> no ping sent, success logged" {
    marker="${EMPTY_WS}/.tabs/.ff-starve-state/slot-99__some-repo.starved"
    mkdir -p "$(dirname "${marker}")"
    : > "${marker}"   # pre-existing marker from a prior episode -- must be cleared on success

    run _run_check_starvation "" "1"

    [ "$status" -eq 0 ]
    [[ "$output" == *"[auto-reconcile-ok]"* ]]
    [[ "$output" == *"slot 99/some-repo"* ]]
    [ ! -s "${PING_LOG}" ]      # no ping was posted
    [ ! -f "${marker}" ]       # marker cleared
}

@test "auto-reconcile declines -> pages with ITS payload, not the bare starve message" {
    run _run_check_starvation "ORIGINAL STARVE PAYLOAD for some-repo

AUTO-RECONCILE: declined -- pre-existing unresolved conflict markers" "1"

    [ "$status" -eq 0 ]
    [ -s "${PING_LOG}" ]
    run cat "${PING_LOG}"
    [[ "$output" == *"AUTO-RECONCILE: declined"* ]]
    [[ "$output" == *"some-repo"* ]]
}

@test "AUTO_RECONCILE_STARVED=0 restores prior behavior -- pages with the bare starve payload, auto-reconcile never runs" {
    # A stub reconcile script that would fail loudly if ever invoked -- proves the toggle
    # actually short-circuits the call, not just that its output happens to look right.
    poison="${BATS_TEST_TMPDIR}/poison.sh"
    printf '#!/usr/bin/env bash\necho SHOULD_NEVER_RUN >&2\nexit 1\n' > "${poison}"
    chmod +x "${poison}"

    local harness="${BATS_TEST_TMPDIR}/harness_off.sh"
    {
        echo "source '${REPORTER_ABS}' --workspace '${EMPTY_WS}' --quiet"
        echo "STARVE_DETECTOR='${STUB_DETECTOR}'"
        echo "AUTO_RECONCILE_SCRIPT='${poison}'"
        echo "AUTO_RECONCILE_STARVED=0"
        echo "resolve_token_for_slot() { printf 'dummy-token'; return 0; }"
        echo "post_starve_ping() {"
        echo "  printf '%s\t%s\t%s\n' \"\$1\" \"\$2\" \"\$3\" >> '${PING_LOG}'"
        echo "  return 0"
        echo "}"
        echo "check_starvation_for_slot 99 '${SLOT_DIR}'"
    } > "${harness}"
    run bash "${harness}"

    [ "$status" -eq 0 ]
    [[ "$output" != *"SHOULD_NEVER_RUN"* ]]
    [ -s "${PING_LOG}" ]
    run cat "${PING_LOG}"
    [[ "$output" == *"ORIGINAL STARVE PAYLOAD"* ]]
    [[ "$output" != *"AUTO-RECONCILE"* ]]
}

@test "slot-git-status-report.sh still has valid bash syntax after the wiring change" {
    run bash -n "${REPORTER_ABS}"
    [ "$status" -eq 0 ]
}
