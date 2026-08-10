#!/usr/bin/env bats
# test_quickmerge_isolated_pm_sibling.bats — unit tests for the isolated-worktree PM-sibling fix
#   in scripts/quickmerge.sh
#   (quickmerge_isolated_worktree_missing_sibling_pm_checkout_2026_08_10.md, [SCRIPT] P1).
#
# The bug: quickmerge's isolated-worktree mode creates a `git worktree add --detach` for ONLY the
# repo being shipped, placed at `$TMPDIR/qm-iso-$$/<repo>`. But quality-gates.sh for any non-PM
# repo sources shared base scripts via a path RELATIVE to the repo root:
#     ${REPO_DIR}/../unified-trading-pm/scripts/quality-gates-base/{qg-environment,base-service}.sh
# In the normal `.tabs/N/` checkout layout every repo is a sibling under the same parent, so
# `../unified-trading-pm` resolves. Inside the isolated worktree the temp parent contained only the
# one worktree, so every isolated quickmerge for a non-PM repo failed at STAGE 3 with
# "Missing base quality-gates script: .../qm-iso-<pid>/unified-trading-pm/scripts/quality-gates-base/base-service.sh".
#
# The fix (landed with the isolation "miniature workspace", 2026-08-10): symlink every sibling repo
# of the caller's workspace next to the worktree in `$TMPDIR/qm-iso-$$/` — including
# unified-trading-pm — so the `../unified-trading-pm` relative derivation resolves. QG only ever
# READS from the PM sibling (sources scripts, never writes), so sharing the caller's real checkout
# via a symlink is safe (this is the issue's option (b)).
#
# Replicates the helper's exact logic (not fragile against line-number changes in quickmerge.sh —
# mirrors the established pattern in test_quickmerge_isolated_branch_collision.bats), exercised
# against REAL local git repos (hermetic: no network, no GitHub — an "origin" is a second local repo).
#
# Run: bats tests/test_quickmerge_isolated_pm_sibling.bats

# ── helper: replicated verbatim from quickmerge.sh (lines ~546-567) ──────────

# Args: $1=workspace root (parent of all sibling repos)  $2=repo name being shipped
#       $3=isolation parent (the $TMPDIR/qm-iso-$$ equivalent)
# Emits the list of sibling symlinks created, one per line: "<basename>:<abs-target>"
_qm_setup_isolated_siblings() {
    local ws_root="$1" repo_name="$2" iso_parent="$3"
    local _qm_sib _qm_sib_name
    for _qm_sib in "$ws_root"/*; do
      [ -d "$_qm_sib" ] || continue
      [ -e "$_qm_sib/.git" ] || continue
      _qm_sib_name="$(basename "$_qm_sib")"
      [ "$_qm_sib_name" = "$repo_name" ] && continue   # the worktree IS this repo
      [ -e "$iso_parent/$_qm_sib_name" ] || ln -s "$_qm_sib" "$iso_parent/$_qm_sib_name" 2>/dev/null
      [ -e "$iso_parent/$_qm_sib_name" ] && echo "$_qm_sib_name:$(readlink "$iso_parent/$_qm_sib_name")"
    done
}

# ── fixtures ─────────────────────────────────────────────────────────────────

setup() {
    TEST_ROOT="$(mktemp -d)"
    export TEST_ROOT

    # A workspace root holding two sibling git repos: the repo being shipped + the PM sibling.
    mkdir -p "$TEST_ROOT/ws"

    # The repo being shipped (a stand-in for deployment-service / any non-PM repo).
    git init -q "$TEST_ROOT/ws/deployment-service"
    git -C "$TEST_ROOT/ws/deployment-service" config user.email "test@example.com"
    git -C "$TEST_ROOT/ws/deployment-service" config user.name "test"
    echo "seed" > "$TEST_ROOT/ws/deployment-service/seed.txt"
    git -C "$TEST_ROOT/ws/deployment-service" add seed.txt
    git -C "$TEST_ROOT/ws/deployment-service" commit -qm "seed"

    # The PM sibling, carrying the quality-gates-base scripts the gate sources.
    git init -q "$TEST_ROOT/ws/unified-trading-pm"
    git -C "$TEST_ROOT/ws/unified-trading-pm" config user.email "test@example.com"
    git -C "$TEST_ROOT/ws/unified-trading-pm" config user.name "test"
    echo "seed" > "$TEST_ROOT/ws/unified-trading-pm/seed.txt"
    git -C "$TEST_ROOT/ws/unified-trading-pm" add seed.txt
    git -C "$TEST_ROOT/ws/unified-trading-pm" commit -qm "seed"
    mkdir -p "$TEST_ROOT/ws/unified-trading-pm/scripts/quality-gates-base"
    touch "$TEST_ROOT/ws/unified-trading-pm/scripts/quality-gates-base/base-service.sh"
    touch "$TEST_ROOT/ws/unified-trading-pm/scripts/quality-gates-base/qg-environment.sh"

    # The isolation parent + detached worktree, exactly as quickmerge does.
    export ISO_PARENT="$TEST_ROOT/qm-iso-$$"
    mkdir -p "$ISO_PARENT"
    git -C "$TEST_ROOT/ws/deployment-service" worktree add --detach -q "$ISO_PARENT/deployment-service" HEAD
}

teardown() {
    [ -n "$TEST_ROOT" ] || return 0
    # Hermetic temp tree — safe to remove; worktree metadata lives inside it, not the parent clone.
    git -C "$TEST_ROOT/ws/deployment-service" worktree remove --force "$ISO_PARENT/deployment-service" 2>/dev/null || true
    git -C "$TEST_ROOT/ws/deployment-service" worktree prune 2>/dev/null || true
    rm -rf "$TEST_ROOT"
}

# ── the bug this fix exists for ──────────────────────────────────────────────

@test "the bug is real: without the sibling symlink the PM base-script path is missing in the worktree" {
    # No sibling symlinks have been created yet (fresh isolation parent holds only the worktree).
    [ ! -e "$ISO_PARENT/unified-trading-pm" ]
    [ ! -f "$ISO_PARENT/deployment-service/../unified-trading-pm/scripts/quality-gates-base/base-service.sh" ]
    [ ! -f "$ISO_PARENT/deployment-service/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh" ]
}

# ── the fix ──────────────────────────────────────────────────────────────────

@test "the sibling loop symlinks unified-trading-pm (and the shipped repo is skipped) into the isolation parent" {
    run _qm_setup_isolated_siblings "$TEST_ROOT/ws" "deployment-service" "$ISO_PARENT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"unified-trading-pm:"* ]]
    # The shipped repo itself is NOT re-symlinked (the worktree IS it).
    [[ "$output" != *"deployment-service:"* ]]
}

@test "after the sibling loop, the PM quality-gates-base scripts resolve from inside the worktree" {
    _qm_setup_isolated_siblings "$TEST_ROOT/ws" "deployment-service" "$ISO_PARENT"
    # The exact path quality-gates.sh sources for a non-PM repo (quickmerge.sh line ~1728).
    [ -f "$ISO_PARENT/deployment-service/../unified-trading-pm/scripts/quality-gates-base/base-service.sh" ]
    [ -f "$ISO_PARENT/deployment-service/../unified-trading-pm/scripts/quality-gates-base/qg-environment.sh" ]
}

@test "the sibling symlink targets the caller's real unified-trading-pm checkout (read-only sharing)" {
    _qm_setup_isolated_siblings "$TEST_ROOT/ws" "deployment-service" "$ISO_PARENT"
    local resolved
    resolved="$(readlink "$ISO_PARENT/unified-trading-pm")"
    [ "$resolved" = "$TEST_ROOT/ws/unified-trading-pm" ]
    # And it resolves to the SAME content the caller's checkout has.
    [ "$(readlink -f "$ISO_PARENT/unified-trading-pm/scripts/quality-gates-base/base-service.sh")" = "$TEST_ROOT/ws/unified-trading-pm/scripts/quality-gates-base/base-service.sh" ]
}
