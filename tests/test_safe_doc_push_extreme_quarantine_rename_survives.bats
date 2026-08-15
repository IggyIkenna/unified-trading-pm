#!/usr/bin/env bats
# test_safe_doc_push_extreme_quarantine_rename_survives.bats — a named `--files` entry that is
#   the OLD (now-absent) side of an already-staged `git mv` rename must stage cleanly, not
#   fatal the whole staging call.
#
# The bug (measured 2026-08-15,
# safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md): the retry
# loop staged every named file with ONE combined `git add -- "${FILES[@]}"` call. The archival
# SSOT requires the caller to `git mv` the plan BEFORE invoking this script -- which means the
# rename is ALREADY staged (old.md removed from the index entirely, new.md added) by the time
# this script's first `git add` runs. `git add -- <path>` only stages a deletion for a path
# that is CURRENTLY tracked in the index; once the index already reflects the desired
# post-deletion state (no entry for old.md, matching disk), there is nothing left for `git add`
# to "add" -- it fatals with `pathspec '<path>' did not match any files`, EVEN THOUGH the
# deletion is already correct and the file would commit fine as-is. Reproduced directly below
# (empirically confirmed against a real repo, not simulated): `git mv old new; git commit`'s
# staged state, then `git add -- old new` on the very FIRST call, fatals verbatim with the
# incident transcript's exact error. Because the pre-fix call named every FILES entry in ONE
# command, that single already-staged path's failure aborted staging of every OTHER named file
# too -- so a plan carrying a `git mv` archival, bundled with any other named file, could NEVER
# stage at all, on any attempt, identically every time -- matching the incident's "6/6 attempts
# failed identically" across both invocations.
#
# A second, related defect fixed alongside this one: KNOWN_RENAME_SOURCES (which
# reassert_renames() uses to re-stage a rename's deletion half after a reconcile) was captured
# via `git diff --cached --name-status -M`, which requires the rename to ALREADY be staged at
# that exact point. True for the shared-index path (the caller `git mv`s before invoking this
# script) -- but FALSE for the isolated-worktree path (the default), whose copy loop only
# `cp`/`rm -f`s the caller's files onto disk and never runs `git add` before the child script
# re-execs and captures KNOWN_RENAME_SOURCES -- so it was silently EMPTY on every isolated-mode
# run, permanently disabling reassert_renames() on the very path the incident hit first.
#
# Both fixes are exercised here directly against REAL local git repos (hermetic: no network),
# replicating the exact staging/detection logic from safe-doc-push.sh rather than sourcing the
# whole script (mirrors the established pattern in
# test_safe_doc_push_isolated_deletion_propagates.bats and
# test_quickmerge_stage5_no_regression_guard.bats).
#
# Run: bats tests/test_safe_doc_push_extreme_quarantine_rename_survives.bats

# ── helpers: replicated verbatim from safe-doc-push.sh ─────────────────────────

# stage_named_files -- see safe-doc-push.sh for the full comment. $1: space-separated FILES.
_stage_named_files() {
  local files=($1) f rc=0
  for f in "${files[@]}"; do
    if [[ -e "$f" ]]; then
      git add -- "$f" || rc=1
      continue
    fi
    if git ls-files --error-unmatch -- "$f" >/dev/null 2>&1; then
      git add -- "$f" || rc=1
    elif git cat-file -e "HEAD:$f" 2>/dev/null; then
      :
    else
      echo "named path does not exist in the working tree, the index, or HEAD: $f" >&2
      rc=1
    fi
  done
  return "$rc"
}

# The PRE-FIX behaviour, for comparison: one combined `git add` naming every file.
_stage_named_files_prefix() {
  local files=($1)
  git add -- "${files[@]}"
}

# KNOWN_RENAME_SOURCES capture -- FILES-based (the fix), not `git diff --cached -M`-based.
# $1: space-separated FILES. Echoes each detected source, one per line.
_known_rename_sources_files_based() {
  local files=($1) f
  for f in "${files[@]}"; do
    if [[ ! -e "$f" ]] && git cat-file -e "HEAD:$f" 2>/dev/null; then
      echo "$f"
    fi
  done
}

# The PRE-FIX capture, for comparison: requires an already-staged R-status pair.
_known_rename_sources_diff_cached_based() {
  local files=($1) status src dst
  while IFS=$'\t' read -r status src dst; do
    [[ -z "$status" ]] && continue
    case "$status" in
      R*)
        for f in "${files[@]}"; do
          [[ "$f" == "$dst" ]] && echo "$src"
        done
        ;;
    esac
  done < <(git diff --cached --name-status -M 2>/dev/null)
}

setup() {
  TEST_ROOT="$(mktemp -d)"
  export TEST_ROOT
  git init -q -b main "$TEST_ROOT/repo"
  cd "$TEST_ROOT/repo" || return 1
  git config user.email "test@example.com"
  git config user.name "test"
  echo hi > old.md
  echo other > other.md
  git add -A
  git commit -qm init
}

teardown() {
  [ -n "$TEST_ROOT" ] && rm -rf "$TEST_ROOT"
}

@test "post-fix: a caller-completed git mv stages cleanly on the FIRST call (the real-world shape)" {
  cd "$TEST_ROOT/repo" || return 1
  git mv old.md new.md
  run _stage_named_files "old.md new.md"
  [ "$status" -eq 0 ]
  run git diff --cached --name-status
  [[ "$output" == *"R100"*"old.md"*"new.md"* ]]
}

@test "post-fix: staging the same already-staged rename a SECOND time (a retry) also succeeds" {
  cd "$TEST_ROOT/repo" || return 1
  git mv old.md new.md
  run _stage_named_files "old.md new.md"
  [ "$status" -eq 0 ]
  run _stage_named_files "old.md new.md"
  [ "$status" -eq 0 ]
  run _stage_named_files "old.md new.md"
  [ "$status" -eq 0 ]
  run git diff --cached --name-status
  [[ "$output" == *"R100"*"old.md"*"new.md"* ]]
}

@test "pre-fix: the combined git add fatals on a caller-completed git mv, reproducing the incident verbatim" {
  cd "$TEST_ROOT/repo" || return 1
  git mv old.md new.md
  run _stage_named_files_prefix "old.md new.md"
  [ "$status" -ne 0 ]
  [[ "$output" == *"pathspec"*"old.md"*"did not match any files"* ]]
}

@test "post-fix: a genuinely nonexistent named path is still a loud, real error" {
  cd "$TEST_ROOT/repo" || return 1
  run _stage_named_files "never_existed.md"
  [ "$status" -ne 0 ]
  [[ "$output" == *"never_existed.md"* ]]
}

@test "KNOWN_RENAME_SOURCES (files-based, the fix) detects the rename source BEFORE anything is staged" {
  cd "$TEST_ROOT/repo" || return 1
  # Replicates the isolated-worktree copy loop's state: filesystem-level rm/cp, no git add yet.
  rm old.md
  echo hi > new.md
  run _known_rename_sources_files_based "old.md new.md"
  [ "$status" -eq 0 ]
  [ "$output" = "old.md" ]
}

@test "KNOWN_RENAME_SOURCES (pre-fix, diff --cached -M based) is EMPTY before anything is staged" {
  cd "$TEST_ROOT/repo" || return 1
  # Same isolated-worktree-style state as above: nothing staged yet -- this is the exact gap
  # that permanently disabled reassert_renames() on the isolated-mode (default) path.
  rm old.md
  echo hi > new.md
  run _known_rename_sources_diff_cached_based "old.md new.md"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
}
