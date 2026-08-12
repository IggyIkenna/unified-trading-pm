#!/usr/bin/env bats
# test_check_todo_regression_merge_base.bats — regression coverage for the CI snapshot-race
# fix in scripts/plan-hygiene/check_todo_regression.sh: `--merge-base` compares each plan
# against the MERGE-BASE of HEAD and origin/live-defi-rollout (the stable fork point) instead
# of the MOVING tip, so a concurrent agent commit landing after this push forked can no longer
# add todos to an untouched plan and false-flag a "loss". SSOT:
# plans/active/issues/plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md
#
# Run: bats tests/test_check_todo_regression_merge_base.bats
#
# Each fixture reproduces the CI checkout shape: a shallow `--depth=2` clone of a PR head (the
# workflow's fetch-depth:2), with `origin/live-defi-rollout` re-fetched fresh (the moving tip).
# The real script is copied into the fixture repo so the full-baseline mode's PLANS_DIR
# resolves to the fixture, and each test `cd`s into that checkout so the script's git commands
# (git show / git merge-base / git fetch --deepen) run against the fixture repo — the same
# CWD==repo assumption every production caller (run_hygiene_sweep.sh, install_hooks.sh) relies
# on.

SCRIPT_SRC="$(dirname "$BATS_TEST_DIRNAME")/scripts/plan-hygiene/check_todo_regression.sh"

# Build the canonical race fixture. $1 = scratch root. Prints the checkout path.
# Scenario: planX genuinely loses a todo on the PR branch (5->4); planY is untouched by the
# PR but gains a todo on LDR after the fork (3->4). Comparing against the moving tip
# false-flags planY; comparing against the fork point flags only planX.
_build_race_fixture() {
    local root="$1"
    local up="$root/upstream" cl="$root/checkout"
    mkdir -p "$up"
    git -C "$up" init -q -b live-defi-rollout
    git -C "$up" config user.email t@t && git -C "$up" config user.name t
    mkdir -p "$up/plans/active"
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n- [ ] e\n' > "$up/plans/active/planX.md"
    printf -- '---\ntitle: Y\n---\n\n- [ ] p\n- [ ] q\n- [ ] r\n' > "$up/plans/active/planY.md"
    git -C "$up" add -A && git -C "$up" commit -qm "base: X has 5 todos, Y has 3"
    git -C "$up" checkout -q -b pr-branch
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n' > "$up/plans/active/planX.md"
    git -C "$up" add -A && git -C "$up" commit -qm "PR: planX loses 1 todo"
    git -C "$up" checkout -q live-defi-rollout
    printf -- '---\ntitle: Y\n---\n\n- [ ] p\n- [ ] q\n- [ ] r\n- [ ] s\n' > "$up/plans/active/planY.md"
    git -C "$up" add -A && git -C "$up" commit -qm "LDR: planY gains 1 todo after the fork"
    git clone -q --depth=2 --branch pr-branch --single-branch "file://$up" "$cl"
    git -C "$cl" fetch -q origin live-defi-rollout:refs/remotes/origin/live-defi-rollout
    mkdir -p "$cl/scripts/plan-hygiene"
    cp "$SCRIPT_SRC" "$cl/scripts/plan-hygiene/"
    echo "$cl"
}

@test "check_todo_regression.sh has valid bash syntax" {
    run bash -n "$SCRIPT_SRC"
    [ "$status" -eq 0 ]
}

@test "--merge-base flags only the genuinely-lost plan, not the untouched plan that gained todos on the moving tip" {
    local cl; cl="$(_build_race_fixture "$BATS_TEST_TMPDIR")"
    cd "$cl"
    run bash scripts/plan-hygiene/check_todo_regression.sh --merge-base --quiet
    # planX genuinely lost 1 vs the fork point -> flagged. planY is untouched by the PR and
    # only LDR's post-fork commit added a todo -> must NOT appear.
    [ "$status" -eq 1 ]
    echo "$output" | grep -q "planX.md"
    echo "$output" | grep -q "planY.md" && return 1
    return 0
}

@test "default mode still false-flags the untouched plan (the race --merge-base fixes)" {
    local cl; cl="$(_build_race_fixture "$BATS_TEST_TMPDIR")"
    cd "$cl"
    run bash scripts/plan-hygiene/check_todo_regression.sh --quiet
    # Without --merge-base the comparison is against the moving tip: planY (3 current vs 4 at
    # tip) reads as a "loss" even though the PR never touched it. Locks in that we are fixing a
    # live behavior, not adding a check for a non-event.
    [ "$status" -eq 1 ]
    echo "$output" | grep -q "planX.md"
    echo "$output" | grep -q "planY.md"
}

@test "--merge-base resolves the fork point through the deepen path (fork beyond the shallow depth-2 boundary)" {
    # A multi-commit PR: the fork sits beyond the fetch-depth:2 window, so git merge-base
    # cannot resolve on the plain shallow clone — the script's incremental `--deepen` must
    # converge to the TRUE fork point (planX lost=1 vs fork), not the moving tip (lost=2).
    local up="$BATS_TEST_TMPDIR/upstream" cl="$BATS_TEST_TMPDIR/checkout"
    mkdir -p "$up"
    git -C "$up" init -q -b live-defi-rollout
    git -C "$up" config user.email t@t && git -C "$up" config user.name t
    mkdir -p "$up/plans/active"
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n- [ ] e\n' > "$up/plans/active/planX.md"
    git -C "$up" add -A && git -C "$up" commit -qm "base: X has 5 todos"
    git -C "$up" checkout -q -b feature
    for i in 1 2 3 4; do echo "f$i" >> "$up/extra.txt"; git -C "$up" add -A; git -C "$up" commit -qm "f$i"; done
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n' > "$up/plans/active/planX.md"
    git -C "$up" add -A && git -C "$up" commit -qm "PR loses a todo"
    git -C "$up" checkout -q live-defi-rollout
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n- [ ] e\n- [ ] f\n' > "$up/plans/active/planX.md"
    git -C "$up" add -A && git -C "$up" commit -qm "LDR adds a todo after the fork"
    git clone -q --depth=2 --branch feature --single-branch "file://$up" "$cl"
    git -C "$cl" fetch -q origin live-defi-rollout:refs/remotes/origin/live-defi-rollout
    mkdir -p "$cl/scripts/plan-hygiene"
    cp "$SCRIPT_SRC" "$cl/scripts/plan-hygiene/"
    cd "$cl"
    run bash scripts/plan-hygiene/check_todo_regression.sh --merge-base --quiet
    # Genuine loss vs the fork point is exactly 1 (5 at fork vs 4 current). A base stuck on the
    # moving tip would read lost=2 (6 vs 4). The fixture's own loss line is the assertion.
    [ "$status" -eq 1 ]
    echo "$output" | grep -q "lost=1"
}

@test "--merge-base passes a promote-style PR merge ref (the dominant documented false positive)" {
    # A promote PR is a merge of (behind-main, an LDR snapshot) and the moving tip has since
    # gained commits. Default mode false-flags it; --merge-base must resolve the fork point
    # (the promote head itself) and pass — the promote carries LDR content, it does not author
    # a todo loss. (The quality_gates_quickmerge_timing_baseline origin=14 current=13 incident.)
    local up="$BATS_TEST_TMPDIR/upstream" cl="$BATS_TEST_TMPDIR/checkout"
    mkdir -p "$up"
    git -C "$up" init -q -b live-defi-rollout
    git -C "$up" config user.email t@t && git -C "$up" config user.name t
    mkdir -p "$up/plans/active"
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n- [ ] e\n' > "$up/plans/active/planX.md"
    git -C "$up" add -A && git -C "$up" commit -qm "base"
    local fork; fork=$(git -C "$up" rev-parse HEAD)
    # main behind at the fork; promote head = the fork snapshot; LDR then advances past it
    git -C "$up" branch main "$fork"
    git -C "$up" checkout -q live-defi-rollout
    printf -- '---\ntitle: X\n---\n\n- [ ] a\n- [ ] b\n- [ ] c\n- [ ] d\n- [ ] e\n- [ ] f\n' > "$up/plans/active/planX.md"
    git -C "$up" add -A && git -C "$up" commit -qm "LDR adds a todo after the promote head"
    git -C "$up" checkout -q main
    git -C "$up" -c user.email=t@t -c user.name=t merge -q --no-ff "$fork" -m "PR merge ref"
    local mrg; mrg=$(git -C "$up" rev-parse HEAD)
    git -C "$up" checkout -q live-defi-rollout
    git -C "$up" update-ref refs/pull/9/merge "$mrg"
    git clone -q --depth=2 "file://$up" "$cl"
    git -C "$cl" fetch -q origin "refs/pull/9/merge:refs/remotes/origin/pr9"
    git -C "$cl" checkout -q -B ci-head refs/remotes/origin/pr9
    git -C "$cl" fetch -q origin live-defi-rollout:refs/remotes/origin/live-defi-rollout
    mkdir -p "$cl/scripts/plan-hygiene"
    cp "$SCRIPT_SRC" "$cl/scripts/plan-hygiene/"
    cd "$cl"
    run bash scripts/plan-hygiene/check_todo_regression.sh --quiet
    [ "$status" -eq 1 ]   # default mode reproduces the false positive
    run bash scripts/plan-hygiene/check_todo_regression.sh --merge-base --quiet
    [ "$status" -eq 0 ]   # merge-base mode is race-free
}
