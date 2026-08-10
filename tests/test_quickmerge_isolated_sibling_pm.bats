#!/usr/bin/env bats
# test_quickmerge_isolated_sibling_pm.bats — unit tests for the isolated-worktree
#   sibling-unified-trading-pm fix in scripts/quickmerge.sh
#   (quickmerge_isolated_worktree_missing_sibling_pm_checkout_2026_08_10.md, [SCRIPT] P1).
#
# The bug: quickmerge's isolated worktree is created at `$TMPDIR/qm-iso-$$/<repo>` with
# ONLY the shipped repo's worktree inside. `quality-gates.sh` for any non-PM repo sources
# shared base scripts via a path relative to the repo root:
#     ${REPO_DIR}/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh
# In the normal checkout every repo is a sibling under `.tabs/N/`, so `../unified-trading-pm`
# resolves; inside the isolated worktree's temp parent it did not, and STAGE 3 died with
#     Missing base quality-gates script: .../qm-iso-<pid>/unified-trading-pm/.../base-service.sh
#
# The fix symlinks EVERY sibling repo (with a `.git`) of the caller's workspace next to the
# isolated worktree, so the sibling-path derivation resolves for any non-PM repo (and for
# the PM repo the loop skips itself, so it never creates a self-symlink).
#
# Replicates the loop's exact logic (not fragile against line-number changes in
# quickmerge.sh — mirrors the established pattern in
# test_quickmerge_isolated_branch_collision.bats), exercised against REAL local git repos
# (hermetic: no network, no GitHub — "origin" is a second local repo).
#
# Run: bats tests/test_quickmerge_isolated_sibling_pm.bats

# ── helper: replicated verbatim from quickmerge.sh (lines ~560-567) ──────────

# Args: $1=caller repo dir (the repo being shipped)  $2=iso parent  $3=repo name under test
_run_sibling_symlink_setup() {
    local _qm_caller_repo="$1" _qm_iso_parent="$2" _qm_repo_name="$3"
    local _qm_ws_root _qm_sib _qm_sib_name
    _qm_ws_root="$(cd "$_qm_caller_repo/.." && pwd -P)"
    for _qm_sib in "$_qm_ws_root"/*; do
      [ -d "$_qm_sib" ] || continue
      [ -e "$_qm_sib/.git" ] || continue
      _qm_sib_name="$(basename "$_qm_sib")"
      [ "$_qm_sib_name" = "$_qm_repo_name" ] && continue   # the worktree IS this repo
      [ -e "$_qm_iso_parent/$_qm_sib_name" ] || ln -s "$_qm_sib" "$_qm_iso_parent/$_qm_sib_name" 2>/dev/null
    done
}

# ── fixtures ─────────────────────────────────────────────────────────────────

setup() {
    TEST_ROOT="$(mktemp -d)"
    export TEST_ROOT

    # A fake caller workspace: the shipped repo + a unified-trading-pm sibling, each a
    # real git repo (the shipped repo has a worktree added for it, like quickmerge does).
    mkdir -p "$TEST_ROOT/workspace"
    git init -q "$TEST_ROOT/workspace/deployment-service"
    git -C "$TEST_ROOT/workspace/deployment-service" config user.email "test@example.com"
    git -C "$TEST_ROOT/workspace/deployment-service" config user.name "test"
    echo "seed" > "$TEST_ROOT/workspace/deployment-service/seed.txt"
    git -C "$TEST_ROOT/workspace/deployment-service" add seed.txt
    git -C "$TEST_ROOT/workspace/deployment-service" commit -qm "seed"

    git init -q "$TEST_ROOT/workspace/unified-trading-pm"
    git -C "$TEST_ROOT/workspace/unified-trading-pm" config user.email "test@example.com"
    git -C "$TEST_ROOT/workspace/unified-trading-pm" config user.name "test"
    echo "seed" > "$TEST_ROOT/workspace/unified-trading-pm/seed.txt"
    git -C "$TEST_ROOT/workspace/unified-trading-pm" add seed.txt
    git -C "$TEST_ROOT/workspace/unified-trading-pm" commit -qm "seed"

    # Simulate the base-script that a non-PM repo's quality-gates.sh resolves through
    # the sibling path — the thing that must be reachable after the fix.
    mkdir -p "$TEST_ROOT/workspace/unified-trading-pm/scripts/quality-gates-base"
    echo "#!/bin/bash" > "$TEST_ROOT/workspace/unified-trading-pm/scripts/quality-gates-base/base-service.sh"

    # The isolated worktree's temp parent — created as quickmerge does.
    ISO_PARENT="$TEST_ROOT/qm-iso-123"
    mkdir -p "$ISO_PARENT"
    export ISO_PARENT

    # The worktree itself, mirroring `git worktree add --detach`.
    git -C "$TEST_ROOT/workspace/deployment-service" worktree add --detach -q "$ISO_PARENT/deployment-service" HEAD
}

teardown() {
    # Remove the worktree registration before wiping the tree (bats teardown rm is
    # fine here: TEST_ROOT is a mktemp dir created by this test, not shared).
    if [ -d "$TEST_ROOT/workspace/deployment-service" ]; then
        git -C "$TEST_ROOT/workspace/deployment-service" worktree remove --force "$ISO_PARENT/deployment-service" 2>/dev/null || true
    fi
    [ -n "$TEST_ROOT" ] && rm -rf "$TEST_ROOT"
}

# ── the fix ──────────────────────────────────────────────────────────────────

@test "the fix makes unified-trading-pm available as a sibling of the isolated worktree" {
    run _run_sibling_symlink_setup "$TEST_ROOT/workspace/deployment-service" "$ISO_PARENT" "deployment-service"
    [ "$status" -eq 0 ]

    # unified-trading-pm is now a sibling of the isolated worktree...
    [ -e "$ISO_PARENT/unified-trading-pm" ]
    [ -L "$ISO_PARENT/unified-trading-pm" ]
    # ...and the base-script path a non-PM repo's quality-gates.sh needs resolves through it.
    BASE_QG_SCRIPT="$ISO_PARENT/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
    [ -f "$BASE_QG_SCRIPT" ]
}

@test "the fix never symlinks the shipped repo itself into its own iso parent" {
    run _run_sibling_symlink_setup "$TEST_ROOT/workspace/deployment-service" "$ISO_PARENT" "deployment-service"
    [ "$status" -eq 0 ]

    # The shipped repo's own name must not appear as a symlink sibling (the loop skips it:
    # the worktree IS this repo — a self-symlink would be a loop).
    [ ! -L "$ISO_PARENT/deployment-service" ]
    # And it must be the real worktree directory, not a symlink.
    [ -d "$ISO_PARENT/deployment-service" ]
}

@test "a non-PM repo's quality-gates workspace-root derivation resolves through the sibling" {
    run _run_sibling_symlink_setup "$TEST_ROOT/workspace/deployment-service" "$ISO_PARENT" "deployment-service"
    [ "$status" -eq 0 ]

    # Mirror the exact derivation in deployment-service/scripts/quality-gates.sh:
    #   WORKSPACE_ROOT="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
    #   BASE_QG_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
    cd "$ISO_PARENT/deployment-service" || return 1
    local workspace_root base_qg_script
    workspace_root="$(cd "$(git rev-parse --show-toplevel)/.." && pwd)"
    base_qg_script="${workspace_root}/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
    [ -f "$base_qg_script" ]
}
