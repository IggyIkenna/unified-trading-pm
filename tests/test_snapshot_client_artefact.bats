#!/usr/bin/env bats
# test_snapshot_client_artefact.bats — tests for scripts/dev/snapshot-client-artefact.sh,
# the pre-write safety snapshot for agent-authored client-artefact edits built for
# plans/active/cross_cutting_satellite_ao_dispatch_batch22_2026_08_21.md item 1
# (plans/active/issues/walkthrough_file_shared_checkout_repeated_content_loss_2026_08_20.md).
#
# HERMETIC: every test builds its own scratch git repo under BATS_TEST_TMPDIR and points
# SNAPSHOT_HOME at a scratch dir under BATS_TEST_TMPDIR — never touches the real
# $HOME/.cache/agent-artefact-snapshots or a real .tabs/<N> checkout.
#
# Run: bats tests/test_snapshot_client_artefact.bats

setup() {
    _SCA_PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    SCA="${_SCA_PM_ROOT}/scripts/dev/snapshot-client-artefact.sh"

    export SNAPSHOT_HOME="${BATS_TEST_TMPDIR}/snapshot-home"
    mkdir -p "${SNAPSHOT_HOME}"

    # Scratch repo standing in for a real client-artefact checkout.
    REPO="${BATS_TEST_TMPDIR}/testrepo"
    mkdir -p "${REPO}/codex/14-customer-journeys/commercial-model"
    git init -q "${REPO}"
    git -C "${REPO}" config user.email "test@example.com"
    git -C "${REPO}" config user.name "test"

    ARTEFACT="${REPO}/codex/14-customer-journeys/commercial-model/walkthrough.html"
    printf '<html>original contested content</html>\n' > "${ARTEFACT}"
    git -C "${REPO}" add -A
    git -C "${REPO}" commit -q -m "initial artefact"
}

@test "snapshot creates a content-hashed, timestamped object outside the working tree" {
    run bash "${SCA}" snapshot "${ARTEFACT}"
    [ "$status" -eq 0 ]
    # `run` merges stdout+stderr into $output; the returned path is the final
    # stdout line printed (the log line to stderr comes first).
    snap_path="${lines[-1]}"

    # Landed under SNAPSHOT_HOME, not under the repo's working tree.
    [[ "$snap_path" == "${SNAPSHOT_HOME}"/* ]]
    [ -f "$snap_path" ]

    # Manifest recorded one entry with a matching sha256.
    [ -f "${SNAPSHOT_HOME}/manifest.jsonl" ]
    expected_hash="$(shasum -a 256 "${ARTEFACT}" | cut -d' ' -f1)"
    grep -qF "\"sha256\":\"${expected_hash}\"" "${SNAPSHOT_HOME}/manifest.jsonl"

    # The identity is repo-name + repo-relative path, not an absolute path.
    grep -qF '"identity":"testrepo/codex/14-customer-journeys/commercial-model/walkthrough.html"' \
        "${SNAPSHOT_HOME}/manifest.jsonl"
}

@test "list shows the recorded snapshot for the file's identity" {
    bash "${SCA}" snapshot "${ARTEFACT}" >/dev/null

    run bash "${SCA}" list "${ARTEFACT}"
    [ "$status" -eq 0 ]
    [[ "$output" == *"testrepo/codex/14-customer-journeys/commercial-model/walkthrough.html"* ]]
}

@test "restore round-trips content byte-for-byte to an explicit destination" {
    bash "${SCA}" snapshot "${ARTEFACT}" >/dev/null

    dest="${BATS_TEST_TMPDIR}/recovered.html"
    run bash "${SCA}" restore "${ARTEFACT}" --to "${dest}"
    [ "$status" -eq 0 ]
    [ -f "${dest}" ]

    diff "${ARTEFACT}" "${dest}"
}

@test "restore recovers content even after the working-tree copy is destroyed" {
    bash "${SCA}" snapshot "${ARTEFACT}" >/dev/null
    original_content="$(cat "${ARTEFACT}")"

    # Simulate the exact incident this tool exists for: the working-tree file is
    # clobbered with no corresponding commit (a blind reset / a lost edit).
    printf 'CLOBBERED — simulated working-tree loss\n' > "${ARTEFACT}"

    dest="${BATS_TEST_TMPDIR}/recovered-after-loss.html"
    run bash "${SCA}" restore "${ARTEFACT}" --to "${dest}"
    [ "$status" -eq 0 ]

    recovered_content="$(cat "${dest}")"
    [ "$recovered_content" = "$original_content" ]
}

@test "restore refuses without an explicit --to destination" {
    bash "${SCA}" snapshot "${ARTEFACT}" >/dev/null

    run bash "${SCA}" restore "${ARTEFACT}"
    [ "$status" -eq 2 ]
}

@test "restore fails closed when no snapshot exists for the identity" {
    run bash "${SCA}" restore "${ARTEFACT}" --to "${BATS_TEST_TMPDIR}/nope.html"
    [ "$status" -eq 4 ]
}

@test "restore refuses a corrupted snapshot object instead of returning bad content" {
    run bash "${SCA}" snapshot "${ARTEFACT}"
    [ "$status" -eq 0 ]
    snap_path="${lines[-1]}"

    # Corrupt the stored object after the fact (simulates on-disk bit-rot / partial write).
    printf 'tampered' >> "$snap_path"

    run bash "${SCA}" restore "${ARTEFACT}" --to "${BATS_TEST_TMPDIR}/should-not-exist.html"
    [ "$status" -eq 5 ]
    [ ! -f "${BATS_TEST_TMPDIR}/should-not-exist.html" ]
}

@test "snapshot fails closed on a file outside any git repo" {
    outside="${BATS_TEST_TMPDIR}/not-a-repo.html"
    printf 'no git here\n' > "${outside}"

    run bash "${SCA}" snapshot "${outside}"
    [ "$status" -eq 3 ]
}

@test "two snapshots of the same identity keep both, restore defaults to the latest" {
    printf '<html>version one</html>\n' > "${ARTEFACT}"
    bash "${SCA}" snapshot "${ARTEFACT}" >/dev/null
    sleep 1
    printf '<html>version two</html>\n' > "${ARTEFACT}"
    bash "${SCA}" snapshot "${ARTEFACT}" >/dev/null

    dest="${BATS_TEST_TMPDIR}/latest.html"
    run bash "${SCA}" restore "${ARTEFACT}" --to "${dest}"
    [ "$status" -eq 0 ]
    grep -qF "version two" "${dest}"
}
