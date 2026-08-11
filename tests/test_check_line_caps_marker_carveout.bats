#!/usr/bin/env bats
# test_check_line_caps_marker_carveout.bats — regression tests for the small-marker-append
# carve-out in scripts/plan-hygiene/check_line_caps.sh (operator ruling 2026-08-02,
# over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md).
#
# The carve-out logic is replicated verbatim from check_line_caps.sh into a helper
# (the same pattern as test_quickmerge_stage5_no_regression_guard.bats) so tests run
# against an isolated temp git repo rather than the real PM index.
#
# Carve-out conditions (all four must hold in SCOPED mode):
#   (a) file is already over the hard cap (1000L) before this commit
#   (b) staged diff has ZERO deleted lines
#   (c) staged diff adds no more than 10 lines
#   (d) no added line matches a checkbox pattern (- [ ] or - [x])
#
# Run: bats tests/test_check_line_caps_marker_carveout.bats

SCRIPT="$(dirname "$BATS_TEST_DIRNAME")/scripts/plan-hygiene/check_line_caps.sh"
PLAN_HARD_CAP=1000

# ── replicated carve-out logic ────────────────────────────────────────────────
# Args: $1=git-repo-root  $2=absolute-path-to-staged-plan  $3=current-line-count
# Returns 0 (SMALL_MARKER_APPEND fires) or 1 (blocked).
_check_small_marker_append() {
    local repo="$1" fpath="$2" lines="$3"
    local diff_numstat added deleted pre_commit_lines added_chk
    diff_numstat="$(git -C "$repo" diff --cached --numstat -- "$fpath" 2>/dev/null || true)"
    added="$(printf '%s' "$diff_numstat" | awk '{print $1}')"
    deleted="$(printf '%s' "$diff_numstat" | awk '{print $2}')"
    [ -n "$added" ] && [ -n "$deleted" ] || return 1
    [ "$deleted" = "0" ] || return 1
    [ "$added" -le 10 ] 2>/dev/null || return 1
    pre_commit_lines=$(( lines - added ))
    [ "$pre_commit_lines" -ge "$PLAN_HARD_CAP" ] || return 1
    added_chk="$(git -C "$repo" diff --cached -- "$fpath" 2>/dev/null \
        | grep -cE '^\+\s*-\s*\[.\]' || true)"
    added_chk="${added_chk:-0}"
    [ "$added_chk" = "0" ] || return 1
    return 0
}

# ── fixtures ──────────────────────────────────────────────────────────────────

# Create a git repo with plans/active/ under BATS_TEST_TMPDIR.
_make_pm_repo() {
    local repo="${BATS_TEST_TMPDIR}/pm_$$_${RANDOM}"
    git init -q "$repo"
    git -C "$repo" config user.email "test@example.com"
    git -C "$repo" config user.name "Test"
    mkdir -p "$repo/plans/active"
    echo "$repo"
}

# Write a plan file with exactly $1 lines to $2.
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

@test "small-marker-append carve-out is present in check_line_caps.sh" {
    run grep -c "SMALL_MARKER_APPEND" "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

# ── carve-out fires ───────────────────────────────────────────────────────────

@test "carve-out fires for a 4-line audit marker on an over-cap plan (pure append)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/big_plan.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Pure append: 2 lines, no checkboxes
    printf '\n- **na-eligibility-audit 2026-08-07**: KEEP-NA valid.\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 0 ]
}

@test "carve-out fires for a marker append on a plan sitting at EXACTLY the hard cap (boundary bug regression)" {
    # Regression for the PRE_COMMIT_LINES -gt vs -ge boundary bug (2026-08-09): a file
    # compliant at exactly 1000L making its first 1-line marker append crossed to 1001L,
    # PRE_COMMIT_LINES computed back to 1000 (not -gt 1000), so the carve-out never fired
    # and the file was permanently unverdictable on any future marker touch.
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/at_cap.md"
    _write_plan 1000 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    printf '\n- **na-eligibility-audit 2026-08-09**: KEEP-NA valid.\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 0 ]
}

@test "carve-out fires for a 10-line (max) marker on an over-cap plan" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/big10.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Append exactly 10 lines, no checkboxes
    printf 'line1\nline2\nline3\nline4\nline5\nline6\nline7\nline8\nline9\nline10\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 0 ]
}

# ── carve-out does NOT fire ───────────────────────────────────────────────────

@test "carve-out does NOT fire when file was under cap before this commit" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/under_cap.md"
    _write_plan 997 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Append 5 lines → 1002L, but PRE_COMMIT_LINES=997 which is <= 1000
    printf 'line1\nline2\nline3\nline4\nline5\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when diff has deletions" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/deletions.md"
    _write_plan 1005 "$plan"
    printf 'OLD MARKER\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Edit an existing line (1 delete + 1 add)
    sed -i.bak 's/OLD MARKER/NEW MARKER/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when more than 10 lines are added" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/big_append.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # 11 appended lines — exceeds the 10-line guard
    printf 'l1\nl2\nl3\nl4\nl5\nl6\nl7\nl8\nl9\nl10\nl11\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when an added line is a checkbox" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/checkbox.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Append an open checkbox — the guard must block this
    printf '\n- [ ] [SCRIPT] P3. New todo sneaked via marker path.\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 1 ]
}

@test "carve-out does NOT fire when a closed checkbox is added" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/closed_chk.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    printf '\n- [x] Done item retroactively added.\n' >> "$plan"
    git -C "$repo" add "$plan"
    lines="$(wc -l < "$plan")"

    run _check_small_marker_append "$repo" "$plan" "$lines"
    [ "$status" -eq 1 ]
}

# ── replicated net-zero-substitution carve-out logic ─────────────────────────
# Args: $1=git-repo-root  $2=absolute-path-to-staged-plan
# Returns 0 (NET_ZERO_SUBSTITUTION fires) or 1 (blocked).
_check_net_zero_substitution() {
    local repo="$1" fpath="$2"
    local diff_numstat added deleted changed_chk
    diff_numstat="$(git -C "$repo" diff --cached --numstat -- "$fpath" 2>/dev/null || true)"
    added="$(printf '%s' "$diff_numstat" | awk '{print $1}')"
    deleted="$(printf '%s' "$diff_numstat" | awk '{print $2}')"
    [ -n "$added" ] && [ -n "$deleted" ] || return 1
    [ "$deleted" -gt 0 ] 2>/dev/null || return 1
    [ "$added" -ge 1 ] 2>/dev/null || return 1
    [ "$added" -le "$deleted" ] 2>/dev/null || return 1
    changed_chk="$(git -C "$repo" diff --cached -- "$fpath" 2>/dev/null \
        | grep -cE '^[+-]\s*-\s*\[.\]' || true)"
    changed_chk="${changed_chk:-0}"
    [ "$changed_chk" = "0" ] || return 1
    return 0
}

@test "net-zero-substitution carve-out is present in check_line_caps.sh" {
    run grep -c "NET_ZERO_SUBSTITUTION" "$SCRIPT"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
}

@test "net-zero substitution fires for a same-line content fix on an over-cap plan (1 del, 1 add)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/subst.md"
    _write_plan 1005 "$plan"
    printf 'stale MVP row: 66%% attempted_failed\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Same-line content substitution (1 delete + 1 add), no checkboxes
    sed -i.bak 's/stale MVP row: 66% attempted_failed/accurate MVP row: 94.8-100% covered/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_net_zero_substitution "$repo" "$plan"
    [ "$status" -eq 0 ]
}

@test "net-zero substitution fires for a multi-line shrink on an over-cap plan (3 added, 5 deleted)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/shrink.md"
    _write_plan 1005 "$plan"
    printf 'verbose line A\nverbose line B\nverbose line C\nverbose line D\nverbose line E\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Replace 5 verbose lines with 3 concise ones (ADDED=3, DELETED=5), no checkboxes
    sed -i.bak 's/verbose line A/concise line 1/' "$plan" && rm -f "$plan.bak"
    sed -i.bak 's/verbose line B/concise line 2/' "$plan" && rm -f "$plan.bak"
    sed -i.bak 's/verbose line C/concise line 3/' "$plan" && rm -f "$plan.bak"
    sed -i.bak '/verbose line D/d' "$plan" && rm -f "$plan.bak"
    sed -i.bak '/verbose line E/d' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_net_zero_substitution "$repo" "$plan"
    [ "$status" -eq 0 ]
}

@test "net-zero substitution does NOT fire when a checkbox is in the diff (added checkbox)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/subst_chk_add.md"
    _write_plan 1005 "$plan"
    printf 'OLD LINE\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Substitute, but the added side includes a checkbox
    sed -i.bak 's/OLD LINE/- [ ] [SCRIPT] P3. Sneaked todo via substitution./' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_net_zero_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "net-zero substitution does NOT fire when a checkbox is in the diff (removed checkbox)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/subst_chk_del.md"
    _write_plan 1005 "$plan"
    printf -- '- [x] old todo: done\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Substitute, removing a checkbox line
    sed -i.bak 's/- \[x] old todo: done/updated note (todo gone)/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_net_zero_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "net-zero substitution does NOT fire when the diff GROWS the file (ADDED > DELETED)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/grow.md"
    _write_plan 1005 "$plan"
    printf 'one line\n' >> "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Replace 1 line with 2 lines (ADDED=2, DELETED=1) — grows the file
    sed -i.bak 's/one line/expanded line 1\nexpanded line 2/' "$plan" && rm -f "$plan.bak"
    git -C "$repo" add "$plan"

    run _check_net_zero_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}

@test "net-zero substitution does NOT fire when there are no deletions (pure append — wrong carve-out)" {
    repo="$(_make_pm_repo)"
    plan="$repo/plans/active/pure_add.md"
    _write_plan 1005 "$plan"
    git -C "$repo" add "$plan"
    git -C "$repo" commit -q -m "base"

    # Pure append (ADDED=2, DELETED=0) — should fail this carve-out (no deletions)
    printf 'new line 1\nnew line 2\n' >> "$plan"
    git -C "$repo" add "$plan"

    run _check_net_zero_substitution "$repo" "$plan"
    [ "$status" -eq 1 ]
}
