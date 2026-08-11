#!/usr/bin/env bats
# test_check_line_caps_content_subst_carveout.bats — regression tests for the content-substitution
# carve-out in scripts/plan-hygiene/check_line_caps.sh (operator ruling 2026-08-09,
# plan_hygiene_broken_link_gate_vs_line_cap_gate_deadlock_2026_08_08.md; broadened 2026-08-11,
# tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md item 3).
#
# The carve-out logic is replicated verbatim from check_line_caps.sh into a helper
# (the same pattern as test_check_line_caps_marker_carveout.bats) so tests run against an
# isolated temp git repo rather than the real PM index.
#
# Carve-out conditions (all three must hold in SCOPED mode, once the marker-append carve-out
# above it has NOT already fired):
#   (a) file is already over the hard cap (1000L) before this commit (implied: ADDED<=DELETED
#       means pre-commit lines >= post-commit lines, and post-commit is already over cap)
#   (b) staged diff's ADDED line count is <= its DELETED count (never grows the file)
#   (c) no added line matches a checkbox pattern (- [ ] or - [x])
#
# Run: bats tests/test_check_line_caps_content_subst_carveout.bats

SCRIPT="$(dirname "$BATS_TEST_DIRNAME")/scripts/plan-hygiene/check_line_caps.sh"

# ── replicated carve-out logic ────────────────────────────────────────────────
# Args: $1=git-repo-root  $2=absolute-path-to-staged-plan
# Returns 0 (CONTENT_SUBST_EDIT fires) or 1 (blocked).
_check_content_subst_edit() {
    local repo="$1" fpath="$2"
    local diff_numstat added deleted added_chk
    diff_numstat="$(git -C "$repo" diff --cached --numstat -- "$fpath" 2>/dev/null || true)"
    added="$(printf '%s' "$diff_numstat" | awk '{print $1}')"
    deleted="$(printf '%s' "$diff_numstat" | awk '{print $2}')"
    [ -n "$added" ] && [ -n "$deleted" ] || return 1
    [ "$deleted" -gt 0 ] 2>/dev/null || return 1
    [ "$added" -le "$deleted" ] 2>/dev/null || return 1
    added_chk="$(git -C "$repo" diff --cached -- "$fpath" 2>/dev/null \
        | grep -cE '^\+\s*-\s*\[.\]' || true)"
    added_chk="${added_chk:-0}"
    [ "$added_chk" = "0" ] || return 1
    return 0
}

# ── fixtures ──────────────────────────────────────────────────────────────────

_make_pm_repo() {
    local repo="${BATS_TEST_TMPDIR}/pm_$$_${RANDOM}"
    git init -q "$repo"
    git -C "$repo" config user.email "test@example.com"
    git -C "$repo" config user.name "Test"
    mkdir -p "$repo/plans/active"
    echo "$repo"
}

_write_plan() {
    local line_count="$1" path="$2"
    {
        printf -- '---\ndoc_type: plan\ntitle: Test\nstatus: active\nassigned_vm: NA\n---\n\n'
        local i=1
        while [ "$i" -le "$(( line_count - 9 ))" ]; do
            printf 'content line %d\n' "$i"
            i=$(( i + 1 ))
        done
        printf '\n## Progress Log\n\n'
    } > "$path"
}

# ── presence check ─────────────────────────────────────────────────────────────

@test "content-substitution carve-out is present in check_line_caps.sh" {
    run grep -c "CONTENT_SUBST_EDIT" "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

# ── carve-out fires ───────────────────────────────────────────────────────────

@test "carve-out fires for a same-line link-repoint edit on an over-cap plan" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/link_repoint.md"
    _write_plan 1005 "$plan"
    printf 'See [x](/plans/active/issues/foo_2026_08_06.md) for context.\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak 's#/plans/active/issues/foo_2026_08_06.md#/plans/archive/2026_08/issues/foo_2026_08_06.md#' "$plan"
    rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_subst_edit "$repo" "$plan"
    [ "$status" -eq 0 ]
}

@test "carve-out fires for a same-line table-cell prose correction on an over-cap plan (the tradfi case)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/table_cell.md"
    _write_plan 1005 "$plan"
    printf '| S&P index options | 66%% attempted_failed, not yet launched |\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak 's#66% attempted_failed, not yet launched#2020-2024 ~94.8-100%% covered, 2025 confirmed 0%% gap, 2026 73%% partial#' "$plan"
    rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_subst_edit "$repo" "$plan"
    [ "$status" -eq 0 ]
}

@test "carve-out fires when the substitution deletes more lines than it adds (net shrink)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/shrink.md"
    _write_plan 1005 "$plan"
    printf 'line A\nline B\nline C\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Replace 3 lines with 1 — net shrink, still a substitution
    sed -i.bak '/^line A$/,/^line C$/c\
line ABC combined' "$plan"
    rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_subst_edit "$repo" "$plan"
    [ "$status" -eq 0 ]
}

# ── carve-out does NOT fire ───────────────────────────────────────────────────

@test "carve-out does NOT fire when the diff grows the file (ADDED > DELETED)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/grows.md"
    _write_plan 1005 "$plan"
    printf 'one line\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Replace 1 line with 2 — grows the file
    sed -i.bak 's/^one line$/one line\ntwo line/' "$plan"
    rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_subst_edit "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when a changed line adds a checkbox" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/checkbox_subst.md"
    _write_plan 1005 "$plan"
    printf 'plain status line\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak 's/^plain status line$/- [ ] [SCRIPT] P3. New todo sneaked via substitution path./' "$plan"
    rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_subst_edit "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire on a pure deletion with zero additions (still deleted>0 but no add to check content of — degenerate but must not crash)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/pure_delete.md"
    _write_plan 1005 "$plan"
    printf 'removable line\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak '/^removable line$/d' "$plan"
    rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_subst_edit "$repo" "$plan"
    [ "$status" -eq 0 ]
}
