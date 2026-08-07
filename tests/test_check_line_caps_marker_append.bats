#!/usr/bin/env bats
# test_check_line_caps_marker_append.bats — regression tests for the
#   small-marker-append carve-out in scripts/plan-hygiene/check_line_caps.sh.
#
# Carve-out rule (operator ruling 2026-08-02, codified in check_line_caps.sh header):
#   A commit to an already-over-cap LIVE plan is allowed through SCOPED mode when:
#     (a) the file is already over the 1000L hard cap BEFORE this commit,
#     (b) the staged diff has ZERO deleted lines,
#     (c) the staged diff adds NO MORE THAN 10 lines, and
#     (d) NONE of the added lines match a checkbox pattern (- [ ] / - [x]).
#   Outside these bounds the normal HARD failure still fires.
#
# SSOT: codex/12-agent-workflow/plan-completion-and-archival-discipline.md
#         § "The line-cap does NOT block a small audit-marker append to an
#           already-over-cap LIVE plan (RULED 2026-08-02)"
#       scripts/plan-hygiene/check_line_caps.sh (header policy comment)
#
# Issue filed: plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md
#
# HERMETIC: creates throw-away PM-like git repos under BATS_TEST_TMPDIR; never
# touches real worktrees in $WORKSPACE_ROOT. SCOPED mode is exercised by passing
# an explicit file path argument to check_line_caps.sh.
#
# Run: bats tests/test_check_line_caps_marker_append.bats
# Run all: bats tests/

CHECK="scripts/plan-hygiene/check_line_caps.sh"

# Resolve the absolute path to the script once per test.
setup() {
    PM_ROOT="$(git rev-parse --show-toplevel)"
    CHECK_ABS="$PM_ROOT/$CHECK"
}

# ── helper: build a minimal PM-like git repo containing a copy of the script
#            and a 1001-line over-cap plan file in plans/active/. ──────────────
#
# Layout inside the temp dir mirrors what PM_DIR computation in check_line_caps.sh
# expects:  <root>/scripts/plan-hygiene/check_line_caps.sh
#           <root>/scripts/plan-hygiene/line_caps_baseline.yaml
#           <root>/plans/active/<name>.md
# PM_DIR resolves to <root> when the copied script is invoked as
#   bash <root>/scripts/plan-hygiene/check_line_caps.sh <file>
# and git -C "$PM_DIR" diff ... operates on the temp repo.
#
# Returns the root directory path.
_make_over_cap_pm() {
    local root="${BATS_TEST_TMPDIR}/pm_$$_${RANDOM}"
    mkdir -p "$root/scripts/plan-hygiene" "$root/plans/active"

    cp "$CHECK_ABS" "$root/scripts/plan-hygiene/check_line_caps.sh"
    printf 'hard_count: 99\n' > "$root/scripts/plan-hygiene/line_caps_baseline.yaml"

    git init -q "$root"
    git -C "$root" config user.email test@t.t
    git -C "$root" config user.name Test

    # 1001-line plan file: frontmatter stub + 1000 numbered content lines.
    {
        printf '# Fake plan\n'
        seq 1 1000 | sed 's/^/- line /'
    } > "$root/plans/active/fake_plan.md"

    git -C "$root" add plans/active/fake_plan.md
    git -C "$root" commit -q -m "init: 1001L over-cap plan"

    echo "$root"
}

# ── syntax ────────────────────────────────────────────────────────────────────

@test "check_line_caps.sh has valid bash syntax" {
    run bash -n "$CHECK_ABS"
    [ "$status" -eq 0 ]
}

# ── carve-out FIRES: SCOPED mode exits 0, reports SOFT not HARD ───────────────

@test "small non-checkbox append to over-cap doc is SOFT (carve-out fires)" {
    root="$(_make_over_cap_pm)"
    plan="$root/plans/active/fake_plan.md"
    printf -- '- na-eligibility-audit 2026-08-07: KEEP-NA valid\n' >> "$plan"
    git -C "$root" add plans/active/fake_plan.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SOFT"* ]]
    [[ "$output" != *"HARD"* ]]
}

@test "up to 10 non-checkbox appended lines to over-cap doc is SOFT (carve-out fires)" {
    root="$(_make_over_cap_pm)"
    plan="$root/plans/active/fake_plan.md"
    seq 1 10 | sed 's/^/- marker-line /' >> "$plan"
    git -C "$root" add plans/active/fake_plan.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 0 ]
    [[ "$output" == *"SOFT"* ]]
    [[ "$output" != *"HARD"* ]]
}

# ── carve-out does NOT fire: append WITH deleted lines → HARD ─────────────────

@test "append that also deletes a line from over-cap doc is HARD (carve-out blocked by deletions)" {
    root="$(_make_over_cap_pm)"
    plan="$root/plans/active/fake_plan.md"
    # Remove the last line then add two new lines: net +1 but DELETED=1
    head -n 1000 "$plan" > "${plan}.tmp"
    printf -- '- marker 1\n- marker 2\n' >> "${plan}.tmp"
    mv "${plan}.tmp" "$plan"
    git -C "$root" add plans/active/fake_plan.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 1 ]
    [[ "$output" == *"HARD"* ]]
}

# ── carve-out does NOT fire: new checkbox line → HARD ─────────────────────────

@test "appending an open checkbox to over-cap doc is HARD (carve-out blocked by checkbox)" {
    root="$(_make_over_cap_pm)"
    plan="$root/plans/active/fake_plan.md"
    printf -- '- [ ] [SCRIPT] P2. sneaky new tracked work\n' >> "$plan"
    git -C "$root" add plans/active/fake_plan.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 1 ]
    [[ "$output" == *"HARD"* ]]
}

@test "appending a done checkbox to over-cap doc is HARD (carve-out blocked by checkbox)" {
    root="$(_make_over_cap_pm)"
    plan="$root/plans/active/fake_plan.md"
    printf -- '- [x] ✅ [SCRIPT] P2. sneaky close\n' >> "$plan"
    git -C "$root" add plans/active/fake_plan.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 1 ]
    [[ "$output" == *"HARD"* ]]
}

# ── carve-out does NOT fire: too many added lines → HARD ──────────────────────

@test "appending 11 lines to over-cap doc is HARD (carve-out blocked by line count)" {
    root="$(_make_over_cap_pm)"
    plan="$root/plans/active/fake_plan.md"
    seq 1 11 | sed 's/^/- marker /' >> "$plan"
    git -C "$root" add plans/active/fake_plan.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 1 ]
    [[ "$output" == *"HARD"* ]]
}

# ── carve-out does NOT fire: doc NOT already over cap → HARD ──────────────────

@test "doc newly crossing the cap in this commit is HARD (carve-out requires pre-existing over-cap)" {
    root="${BATS_TEST_TMPDIR}/pm2_$$_${RANDOM}"
    mkdir -p "$root/scripts/plan-hygiene" "$root/plans/active"
    cp "$CHECK_ABS" "$root/scripts/plan-hygiene/check_line_caps.sh"
    printf 'hard_count: 99\n' > "$root/scripts/plan-hygiene/line_caps_baseline.yaml"
    git init -q "$root"
    git -C "$root" config user.email test@t.t
    git -C "$root" config user.name Test

    plan="$root/plans/active/under_cap.md"
    # 998-line file: UNDER the 1000L hard cap
    { printf '# Fake plan\n'; seq 1 997 | sed 's/^/- line /'; } > "$plan"
    git -C "$root" add plans/active/under_cap.md
    git -C "$root" commit -q -m "init: 998L under-cap plan"

    # Add 5 lines: pushes to 1003L — crosses cap IN THIS COMMIT, not pre-existing
    seq 1 5 | sed 's/^/- new /' >> "$plan"
    git -C "$root" add plans/active/under_cap.md

    run bash "$root/scripts/plan-hygiene/check_line_caps.sh" "$plan"
    [ "$status" -eq 1 ]
    [[ "$output" == *"HARD"* ]]
}
