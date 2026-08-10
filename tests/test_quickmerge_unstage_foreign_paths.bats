#!/usr/bin/env bats
# test_quickmerge_unstage_foreign_paths.bats — the --files index-scoping guard in
#   scripts/quickmerge.sh (ao_context_pct_0_for_monitor_heavy_workers_2026_07_29).
#
# `--files` scopes what quickmerge STAGES, but its commit is a bare `git commit`, which
# commits the whole index. In a shared checkout a peer that stages between our `git add`
# and our commit gets absorbed into OUR commit. Measured 2026-08-10 in agent-orchestrator
# in BOTH directions: a peer's bare commit swallowed this session's three staged source
# files (shipping them under a commit titled "docs(context): record DeepSeek's measured
# ... ceiling", tests left behind), and a later quickmerge run named two files yet pushed a
# commit containing NEITHER — only a peer's untracked test file. Both reported success.
#
# Unlike the sibling bats files this does NOT replicate the logic — it EXTRACTS the real
# function out of quickmerge.sh and evals it, so the test cannot drift from the shipped
# implementation. Hermetic: a real local git repo under BATS_TEST_TMPDIR (auto-cleaned by
# bats, so no teardown removal is needed), no network.
#
# Run: bats tests/test_quickmerge_unstage_foreign_paths.bats

setup() {
  QM_SH="${BATS_TEST_DIRNAME}/../scripts/quickmerge.sh"
  REPO="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$REPO"
  cd "$REPO" || return 1
  git init -q .
  git config user.email t@t.t && git config user.name t
  echo mine > mine.txt && echo theirs > theirs.txt
  git add -A && git commit -qm init

  # Load the REAL function under test.
  eval "$(sed -n '/^_qm_unstage_foreign_paths() {/,/^}/p' "$QM_SH")"
  REPO_NAME=testrepo
}

@test "a foreign staged path is unstaged, the caller's own files survive" {
  echo change > mine.txt && git add mine.txt          # ours, named in --files
  echo peer > theirs.txt && git add theirs.txt        # a peer staged this mid-run

  FILES_ARG="mine.txt"
  run _qm_unstage_foreign_paths
  [ "$status" -eq 0 ]
  [[ "$output" == *"unstaging foreign path"* ]]
  [[ "$output" == *"theirs.txt"* ]]

  git diff --cached --name-only > staged.txt
  grep -qx "mine.txt" staged.txt
  ! grep -qx "theirs.txt" staged.txt
  # the peer's WORK is untouched — only its index entry was dropped
  grep -qx peer theirs.txt
}

@test "quickmerge's own chmod-staged script paths are never treated as foreign" {
  mkdir -p scripts && echo x > scripts/quickmerge.sh && echo y > scripts/quality-gates.sh
  git add scripts/quickmerge.sh scripts/quality-gates.sh
  echo change > mine.txt && git add mine.txt

  FILES_ARG="mine.txt"
  run _qm_unstage_foreign_paths
  [ "$status" -eq 0 ]
  [[ "$output" != *"unstaging foreign path"* ]]
  git diff --cached --name-only | grep -qx "scripts/quickmerge.sh"
}

@test "unscoped mode (no --files) is left completely alone" {
  echo change > mine.txt && echo peer > theirs.txt && git add -A

  FILES_ARG=""
  run _qm_unstage_foreign_paths
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  git diff --cached --name-only | grep -qx "theirs.txt"
}

@test "a staged DELETION of a caller file stays staged (not re-added)" {
  # The untrack-in-the-same-commit shape: removed from the index, still on disk. A pathspec
  # commit would silently re-add it; unstaging-the-extras must leave it as a deletion.
  git rm --cached -q mine.txt

  FILES_ARG="mine.txt"
  run _qm_unstage_foreign_paths
  [ "$status" -eq 0 ]
  git diff --cached --name-status | grep -q "^D.*mine.txt"
  [ -f mine.txt ]
}
