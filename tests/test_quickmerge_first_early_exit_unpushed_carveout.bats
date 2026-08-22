#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_quickmerge_first_early_exit_unpushed_carveout.bats -- regression test for
# quickmerge_first_early_exit_missing_unpushed_commits_carveout_2026_08_15.md.
#
# THE BUG: scripts/quickmerge.sh's FIRST "nothing to commit" early-exit (~line 1420) checked only
# working-tree-vs-origin/main content and exited 0 fast whenever they matched -- with no awareness
# of origin/live-defi-rollout at all. A clean tree whose content happens to converge back to
# origin/main (e.g. reverting an accidental duplicate commit) but that still carries committed,
# unpushed-to-LDR work silently never reached STAGE 5, and quickmerge reported success anyway. The
# SECOND, later early-exit (~line 2265) was fixed for exactly this scenario on 2026-06-10; this
# fix mirrors that same _UNPUSHED carve-out onto the first check via the extracted
# _qm_early_exit_nothing_to_commit() helper.
#
# Like test_quickmerge_landed_content_assertion.bats this EXTRACTS the real function from
# quickmerge.sh and evals it rather than replicating the logic, so the test cannot drift from the
# shipped implementation. Hermetic: two real local git repos under BATS_TEST_TMPDIR (a "local"
# clone and a bare "origin" acting as both origin/main and origin/live-defi-rollout refs), no
# network.
#
# Run: bats tests/test_quickmerge_first_early_exit_unpushed_carveout.bats

setup() {
  QM_SH="${BATS_TEST_DIRNAME}/../scripts/quickmerge.sh"
  ORIGIN="${BATS_TEST_TMPDIR}/origin.git"
  REPO="${BATS_TEST_TMPDIR}/repo"

  git init -q --bare "$ORIGIN"

  mkdir -p "$REPO"
  cd "$REPO" || return 1
  git init -q .
  git config user.email t@t.t && git config user.name t
  git remote add origin "$ORIGIN"

  echo base >doc.md
  git add doc.md && git commit -qm init
  git push -q origin HEAD:main
  git push -q origin HEAD:live-defi-rollout
  git fetch -q origin

  # Load the REAL function under test.
  eval "$(sed -n '/^_qm_early_exit_nothing_to_commit() {/,/^}/p' "$QM_SH")"
}

@test "clean tree, content matches origin/main, no unpushed commits: fast-exit is safe" {
  run _qm_early_exit_nothing_to_commit
  [ "$status" -eq 0 ]
}

@test "clean tree, content matches origin/main, but HEAD has commits unpushed to LDR: must NOT fast-exit" {
  # The exact bug scenario: revert working-tree content back to origin/main-identical while
  # origin/live-defi-rollout's tip still differs (a routine LDR-ahead-of-main state plus a local
  # commit that converges content back).
  echo diverge >doc.md
  git add doc.md && git commit -qm "diverge from main"
  git push -q origin HEAD:live-defi-rollout
  git fetch -q origin

  echo base >doc.md
  git add doc.md && git commit -qm "revert back to origin/main-identical content"
  # HEAD now content-matches origin/main again, but is 2 commits ahead of
  # origin/live-defi-rollout (never pushed there).

  run _qm_early_exit_nothing_to_commit
  [ "$status" -eq 1 ]
}

@test "dirty tree: must NOT fast-exit regardless of unpushed state" {
  echo dirty >doc.md
  run _qm_early_exit_nothing_to_commit
  [ "$status" -eq 1 ]
}

@test "clean tree, content differs from origin/main: must NOT fast-exit" {
  echo differs >doc.md
  git add doc.md && git commit -qm "diverge, unpushed to LDR too"

  run _qm_early_exit_nothing_to_commit
  [ "$status" -eq 1 ]
}
