#!/usr/bin/env bats
# test_check_archive_candidates_flip_then_mv.bats — regression tests for the flip-then-mv
# two-commit archival pattern's `archive_exempt: true` bridge in
# scripts/plan-hygiene/check_archive_candidates.sh's `--only` precommit mode. See
# plans/active/issues/check_archive_candidates_only_mode_no_flip_then_mv_exemption_2026_08_09.md.
#
# `--only` mode unconditionally flags any staged plans/active/*.md doc that reaches 0 open todos +
# some done + unlocked + not archive_exempt. But plan-completion-and-archival-discipline.md
# mandates the checkbox-flip commit and the `git mv` archival commit stay SEPARATE (combining them
# makes the diff at the original path show only a file deletion, defeating the AO server's `/done`
# M3 checkbox-flip verification). For a doc whose own LAST todo is its archival trigger, that left
# no legal commit shape — `archive_exempt: true` is the sanctioned bridge: set on the flip-only
# commit, dropped on the immediately-following archival (`git mv`) commit.
#
# Run: bats tests/test_check_archive_candidates_flip_then_mv.bats

SCRIPT="$(dirname "$BATS_TEST_DIRNAME")/scripts/plan-hygiene/check_archive_candidates.sh"

# Args: $1=path  $2=optional extra frontmatter line (e.g. "archive_exempt: true")
_write_plan_two_todos_one_open() {
    local path="$1" extra="${2:-}"
    {
        printf -- '---\ndoc_type: issue\ntitle: Test doc\nstatus: open\nassigned_vm: NA\nlocked_by:\n'
        [ -n "$extra" ] && printf '%s\n' "$extra"
        printf -- '---\n\n# Test doc\n\n- [x] first todo, already done\n- [ ] second (and last) todo — flipping this is the docs own archival trigger\n'
    } > "$path"
}

# Flip the sole open todo to done — the doc's own archival trigger.
_flip_last_todo() {
    sed -i.bak 's/^- \[ \]/- [x]/' "$1" && rm -f "$1.bak"
}

@test "check_archive_candidates.sh has valid bash syntax" {
    run bash -n "$SCRIPT"
    [ "$status" -eq 0 ]
}

# The --only path-scope guard (check_archive_candidates.sh) requires the staged path to contain
# plans/active/ -- mirror that shape so these fixtures are actually in-scope for the check, not
# silently skipped.
_active_issues_dir() {
    local d="${BATS_TEST_TMPDIR}/plans/active/issues"
    mkdir -p "$d"
    printf '%s' "$d"
}

@test "--only flags a flip-only commit with no archive_exempt (the conflict this issue reports)" {
    plan="$(_active_issues_dir)/no_exempt.md"
    _write_plan_two_todos_one_open "$plan"
    _flip_last_todo "$plan"

    run bash "$SCRIPT" --quiet --only "$plan"
    [ "$status" -eq 1 ]
}

@test "--only tolerates the flip-only commit when archive_exempt: true is the bridge" {
    plan="$(_active_issues_dir)/with_exempt.md"
    _write_plan_two_todos_one_open "$plan" "archive_exempt: true"
    _flip_last_todo "$plan"

    run bash "$SCRIPT" --quiet --only "$plan"
    [ "$status" -eq 0 ]
}

@test "the immediately-following git-mv archival commit naturally clears --only's scope (old path gone)" {
    plan="$(_active_issues_dir)/archived_source.md"
    _write_plan_two_todos_one_open "$plan" "archive_exempt: true"
    _flip_last_todo "$plan"

    # Commit 2 of the sequence: git mv to plans/archive/[issues/], drop the now-moot bridge flag.
    archive_dir="${BATS_TEST_TMPDIR}/plans/archive/issues"
    mkdir -p "$archive_dir"
    archived="$archive_dir/archived_source.md"
    sed -i.bak '/^archive_exempt: true$/d' "$plan" && rm -f "$plan.bak"
    mv "$plan" "$archived"

    # --only is invoked with the STAGED (original) path per run_hygiene_sweep.sh's own convention
    # -- once the file no longer exists there, `[ -f "$f" ]` is false and the check is a no-op for
    # it. This locks in existing, unmodified behaviour as part of the two-commit sequence, not new
    # logic.
    run bash "$SCRIPT" --quiet --only "$plan"
    [ "$status" -eq 0 ]
}

@test "--only still exempts a doc reaching 0-open/done with an UNRELATED extra content change (not a bare bridge)" {
    # archive_exempt: true genuinely bridges the gap regardless of what else changed in the same
    # commit -- this test locks in that the exemption is content-agnostic (matches the existing,
    # unmodified grep-based mechanism), not a new narrower "pure checkbox transition only" rule.
    plan="$(_active_issues_dir)/exempt_plus_content.md"
    _write_plan_two_todos_one_open "$plan" "archive_exempt: true"
    _flip_last_todo "$plan"
    printf '\n## Progress Log\n\n- flipped + exempted in the same commit, extra content present\n' >> "$plan"

    run bash "$SCRIPT" --quiet --only "$plan"
    [ "$status" -eq 0 ]
}
