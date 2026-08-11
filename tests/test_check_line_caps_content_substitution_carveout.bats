#!/usr/bin/env bats
# test_check_line_caps_content_substitution_carveout.bats — regression tests for the
# net-zero-length content-substitution carve-out in scripts/plan-hygiene/check_line_caps.sh
# (tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md todo 3), the
# sibling to the marker-append (2026-08-02) and link-repoint (2026-08-09) carve-outs.
#
# The carve-out logic is replicated verbatim from check_line_caps.sh into a helper (same
# pattern as test_check_line_caps_marker_carveout.bats) so tests run against an isolated
# temp git repo rather than the real PM index.
#
# Carve-out conditions (all four must hold in SCOPED mode, and only when neither the
# marker-append nor link-repoint carve-outs already fired):
#   (a) file is already over the hard cap (1000L) before this commit (implied — ADDED==DELETED
#       means the line count is unchanged by this diff)
#   (b) staged diff is NET-ZERO-LENGTH: ADDED == DELETED
#   (c) staged diff touches no more than 10 lines (ADDED <= 10)
#   (d) no touched (+/-) line matches a checkbox pattern (- [ ] or - [x])
#
# Run: bats tests/test_check_line_caps_content_substitution_carveout.bats

SCRIPT="$(dirname "$BATS_TEST_DIRNAME")/scripts/plan-hygiene/check_line_caps.sh"
PLAN_HARD_CAP=1000

# ── replicated carve-out logic ────────────────────────────────────────────────
# Args: $1=git-repo-root  $2=absolute-path-to-staged-plan
# Returns 0 (CONTENT_SUBSTITUTION_EDIT fires) or 1 (blocked).
_check_content_substitution() {
    local repo="$1" fpath="$2"
    local diff_numstat added deleted touched_chk
    diff_numstat="$(git -C "$repo" diff --cached --numstat -- "$fpath" 2>/dev/null || true)"
    added="$(printf '%s' "$diff_numstat" | awk '{print $1}')"
    deleted="$(printf '%s' "$diff_numstat" | awk '{print $2}')"
    [ -n "$added" ] && [ -n "$deleted" ] || return 1
    [ "$added" -eq "$deleted" ] 2>/dev/null || return 1
    [ "$added" -ge 1 ] 2>/dev/null || return 1
    [ "$added" -le 10 ] 2>/dev/null || return 1
    touched_chk="$(git -C "$repo" diff --cached -- "$fpath" 2>/dev/null \
        | grep -cE '^[+-]\s*-\s*\[.\]' || true)"
    touched_chk="${touched_chk:-0}"
    [ "$touched_chk" = "0" ] || return 1
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

# ── syntax / presence checks ──────────────────────────────────────────────────

@test "check_line_caps.sh has valid bash syntax" {
    run bash -n "$SCRIPT"
    [ "$status" -eq 0 ]
}

@test "content-substitution carve-out is present in check_line_caps.sh" {
    run grep -c "CONTENT_SUBSTITUTION_EDIT" "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

# ── carve-out fires ───────────────────────────────────────────────────────────

@test "carve-out fires for a single-line table-cell content swap (the tradfi scenario)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/big.md"
    _write_plan 1004 "$plan"
    printf '| S&P index options | 66%% attempted_failed... not yet launched |\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak \
        's#66% attempted_failed... not yet launched#2020-2024 ~94.8-100% covered, 2025 confirmed 0% gap#' \
        "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 0 ]
}

@test "carve-out fires for a bounded multi-line net-zero swap (5 add + 5 delete)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/big5.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak '10,14s/content line/updated line/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 0 ]
}

@test "carve-out fires for the max-bound 10-line net-zero swap" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/big10.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak '10,19s/content line/updated line/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 0 ]
}

# ── carve-out does NOT fire ───────────────────────────────────────────────────

@test "carve-out does NOT fire when added != deleted (net growth)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/growth.md"
    _write_plan 1005 "$plan"
    printf 'OLDCELL\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # 1 deleted, 2 added — not net-zero
    sed -i.bak 's/OLDCELL/NEWCELL A\nNEWCELL B/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire for a pure append (deleted=0 — that's the marker-append carve-out's job)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/append.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    printf '\nappended line\n' >> "$plan"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when the net-zero swap exceeds the 10-line bound" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/toolarge.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak '10,20s/content line/updated line/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when an open checkbox is substituted in" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/sneaky_open.md"
    _write_plan 1005 "$plan"
    printf 'OLDCELL\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak 's/OLDCELL/- [ ] sneaky new todo/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when a closed checkbox is removed via the substitution" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/sneaky_closed.md"
    _write_plan 1005 "$plan"
    printf -- '- [x] an already-done item\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    sed -i.bak 's/- \[x\] an already-done item/plain replacement text/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_content_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}
