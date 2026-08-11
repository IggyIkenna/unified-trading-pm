#!/usr/bin/env bats
# test_ship_from_worktree.bats — tests for scripts/dev/ship-from-worktree.sh,
# the worktree-first ship helper built for
# plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md's
# "Two interactive sessions in ONE slot checkout" P1.
#
# HERMETIC: every test builds its own scratch "origin" git repo + scratch
# "slot" clone under BATS_TEST_TMPDIR and never touches the real .tabs/<N>
# checkouts or the real $HOME/.cache/qm-iso-venv — no real fetch, no real
# network, no shared state with a concurrent session.
#
# Run: bats tests/test_ship_from_worktree.bats
# Run all: bats tests/

setup() {
    _SFW_PM_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
    SFW="${_SFW_PM_ROOT}/scripts/dev/ship-from-worktree.sh"

    SCRATCH="${BATS_TEST_TMPDIR}/scratch"
    mkdir -p "${SCRATCH}"

    # A scratch "origin" repo with one commit — stands in for
    # origin/live-defi-rollout without touching the network.
    ORIGIN="${SCRATCH}/origin.git"
    git init -q --bare "${ORIGIN}"

    # A scratch "slot" clone — stands in for .tabs/<N>/<repo>. Named
    # "testrepo" (deliberately NOT "unified-trading-pm") to prove the leaf
    # name is DERIVED from the repo, never hardcoded.
    SLOT_DIR="${SCRATCH}/slot1"
    mkdir -p "${SLOT_DIR}"
    REPO="${SLOT_DIR}/testrepo"
    git clone -q "${ORIGIN}" "${REPO}"
    (
        cd "${REPO}" &&
            git config user.email "test@example.com" &&
            git config user.name "test" &&
            echo "seed" >README.md &&
            git add README.md &&
            git commit -q -m "seed" &&
            git branch -M live-defi-rollout &&
            git push -q -u origin live-defi-rollout
    )

    DEST="${SCRATCH}/ws"
}

teardown() {
    # Best-effort: prune any worktree admin state this test's REPO accrued,
    # so a failed assertion mid-test never leaks into the next test's git
    # commands. Uses the same non-destructive primitives the script itself
    # uses (git worktree remove/prune), never rm -rf.
    if [ -d "${REPO:-}" ]; then
        for wt in "${REPO}"/../*/; do
            :
        done
        git -C "${REPO}" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2}' | while read -r wt; do
            [ "${wt}" = "${REPO}" ] && continue
            git -C "${REPO}" worktree remove --force "${wt}" 2>/dev/null || true
        done
        git -C "${REPO}" worktree prune 2>/dev/null || true
    fi
}

# ── syntax + help ─────────────────────────────────────────────────────────

@test "ship-from-worktree.sh has valid bash syntax" {
    run bash -n "$SFW"
    [ "$status" -eq 0 ]
}

@test "ship-from-worktree.sh --help renders and documents both subcommands" {
    run bash "$SFW" --help
    [ "$status" -eq 0 ]
    [[ "$output" == *"setup"* ]]
    [[ "$output" == *"cleanup"* ]]
    [[ "$output" == *"--dest"* ]]
    [[ "$output" == *"--with-venv"* ]]
}

@test "ship-from-worktree.sh with no command prints usage and exits non-zero" {
    run bash "$SFW"
    [ "$status" -ne 0 ]
}

@test "ship-from-worktree.sh rejects an unknown command" {
    run bash "$SFW" bogus
    [ "$status" -ne 0 ]
    [[ "$output" == *"Unknown command"* ]]
}

# ── setup: usage errors ──────────────────────────────────────────────────

@test "setup rejects an unknown flag" {
    run bash "$SFW" setup --bogus
    [ "$status" -eq 2 ]
    [[ "$output" == *"Unknown arg"* ]]
}

@test "setup outside a git repo with no --repo-root fails loudly (exit 3)" {
    run bash "$SFW" setup --repo-root "${SCRATCH}/nowhere" --dest "${DEST}"
    [ "$status" -eq 3 ]
    [[ "$output" == *"not inside a git repo"* ]]
}

# ── setup: the real path ─────────────────────────────────────────────────

@test "setup creates a detached linked worktree named after the repo (not hardcoded)" {
    run bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    [ "$status" -eq 0 ]
    [ -d "${DEST}/testrepo" ]
    [ -f "${DEST}/testrepo/.git" ]   # linked worktree marker: a FILE, not a dir

    run git -C "${DEST}/testrepo" rev-parse --abbrev-ref HEAD
    [ "$output" = "HEAD" ]  # detached

    run git -C "${DEST}/testrepo" log -1 --format=%s
    [ "$output" = "seed" ]
}

@test "setup's worktree is isolated: an edit there is invisible to the origin slot clone" {
    bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    echo "private edit" >"${DEST}/testrepo/SPIKE.md"

    run git -C "${DEST}/testrepo" status --porcelain
    [[ "$output" == *"SPIKE.md"* ]]

    run git -C "${REPO}" status --porcelain
    [ -z "$output" ]  # the slot clone's own index/working tree sees NOTHING
    [ ! -f "${REPO}/SPIKE.md" ]
}

@test "setup links sibling repos into --dest by default, excluding the leaf and .stale- dirs" {
    mkdir -p "${SLOT_DIR}/sibling-a/.git" "${SLOT_DIR}/sibling-b/.git" "${SLOT_DIR}/old.stale-20260101/.git"
    run bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}"
    [ "$status" -eq 0 ]
    [ -L "${DEST}/sibling-a" ]
    [ -L "${DEST}/sibling-b" ]
    [ ! -e "${DEST}/old.stale-20260101" ]
    [ ! -e "${DEST}/testrepo/testrepo" ]  # never symlinks the leaf into itself
}

@test "setup --no-siblings skips sibling symlinking entirely" {
    mkdir -p "${SLOT_DIR}/sibling-a/.git"
    run bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    [ "$status" -eq 0 ]
    [ ! -e "${DEST}/sibling-a" ]
}

@test "setup refuses to reuse an already-populated --dest leaf" {
    bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    run bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    [ "$status" -eq 2 ]
    [[ "$output" == *"already exists"* ]]
}

@test "setup rejects a nonexistent branch with a clear, actionable message (not a bare git error)" {
    run bash "$SFW" setup --repo-root "${REPO}" --branch does-not-exist --dest "${DEST}" --no-siblings
    [ "$status" -eq 4 ]
    [[ "$output" == *"does-not-exist"* ]]
    [ ! -e "${DEST}/testrepo" ]  # no half-built worktree left behind on failure
}

# ── cleanup ───────────────────────────────────────────────────────────────

@test "cleanup on a nonexistent dest is a no-op, not an error" {
    run bash "$SFW" cleanup "${SCRATCH}/never-created"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Nothing to do"* ]]
}

@test "cleanup removes the worktree, prunes it from the origin repo, and removes sibling symlinks" {
    mkdir -p "${SLOT_DIR}/sibling-a/.git"
    bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}"
    [ -d "${DEST}/testrepo" ]

    run bash "$SFW" cleanup "${DEST}"
    [ "$status" -eq 0 ]
    [ ! -e "${DEST}/testrepo" ]
    [ ! -e "${DEST}/sibling-a" ]
    [ ! -d "${DEST}" ]  # rmdir succeeded — nothing unexpected was left behind

    # The origin repo's own worktree list no longer references it (proves
    # `git worktree remove` ran against the ORIGIN repo, not a raw delete).
    run git -C "${REPO}" worktree list --porcelain
    [[ "$output" != *"${DEST}/testrepo"* ]]
}

@test "cleanup on a dest with an unrelated leftover file rmdir-fails loudly instead of deleting it" {
    bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    echo "unexpected" >"${DEST}/unexpected-file.txt"

    run bash "$SFW" cleanup "${DEST}"
    [ "$status" -eq 0 ]
    [ -d "${DEST}" ]                       # NOT force-removed
    [ -f "${DEST}/unexpected-file.txt" ]   # left untouched
    [ ! -e "${DEST}/testrepo" ]            # the worktree itself was still cleaned up

    rm -f "${DEST}/unexpected-file.txt"
    rmdir "${DEST}" 2>/dev/null || true
}

@test "cleanup refuses to guess when more than one linked worktree sits under dest" {
    bash "$SFW" setup --repo-root "${REPO}" --branch live-defi-rollout --dest "${DEST}" --no-siblings
    # Fabricate a second linked-worktree-shaped directory (a real second
    # worktree add off the same repo would also trigger this — this is the
    # cheapest hermetic way to construct the ambiguous shape).
    mkdir -p "${DEST}/otherrepo"
    printf 'gitdir: %s/.git/worktrees/otherrepo\n' "${REPO}" >"${DEST}/otherrepo/.git"

    run bash "$SFW" cleanup "${DEST}"
    [ "$status" -eq 5 ]
    [[ "$output" == *"refusing to guess"* ]]

    rm -f "${DEST}/otherrepo/.git"
    rmdir "${DEST}/otherrepo" 2>/dev/null || true
    bash "$SFW" cleanup "${DEST}" || true
}
