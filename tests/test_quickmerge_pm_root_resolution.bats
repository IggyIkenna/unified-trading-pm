#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_quickmerge_pm_root_resolution.bats -- quickmerge.sh must resolve its sibling PM checkout
# by CONTENT, not by assuming the checkout directory is literally named "unified-trading-pm"
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo 2).
#
# Measured 2026-08-11 shipping FROM a private worktree (the F6 mitigation for the shared-
# checkout revert hazard): STAGE 2 resolved pre-flight-audit.sh via a hardcoded
# "$WORKSPACE_ROOT/unified-trading-pm/..." and failed with a bare "not found at <path> --
# required" that named no assumption, purely because the worktree's leaf directory wasn't
# named that. STAGE 1.5's dependency-alignment check then FAILED (not skipped) because the
# worktree's parent held no sibling repos to compare pins against -- a workspace-shape problem
# reported as a content regression.
#
# Mirrors scripts/quality_gates/_pm_root.py's fix for the identical class in Python: resolve by
# CONTENT (a directory containing both plans/ and scripts/quality_gates/), never by name.
#
# Hermetic: real directories under BATS_TEST_TMPDIR, no git operations needed for the resolver
# itself (it is pure filesystem probing) -- a couple of tests add a `.git` marker to exercise
# the sibling-repo COUNT used by the STAGE 1.5 diagnosis.
#
# Run: bats tests/test_quickmerge_pm_root_resolution.bats

setup() {
  export PUSH_GOV_DISABLE=true
  REPO_ROOT_SELF="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  QM_SH="${REPO_ROOT_SELF}/scripts/quickmerge.sh"

  eval "$(sed -n '/^_qm_looks_like_pm_root() {/,/^}/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_resolve_pm_root() {/,/^}/p' "$QM_SH")"

  WS="${BATS_TEST_TMPDIR}/ws"
  mkdir -p "$WS"
}

# A minimal fixture with the two directories the content-check requires.
make_pm_shape() {
  mkdir -p "$1/plans" "$1/scripts/quality_gates"
}

@test "fast path: WORKSPACE_ROOT/unified-trading-pm exists and has the right shape" {
  make_pm_shape "$WS/unified-trading-pm"
  WORKSPACE_ROOT="$WS"
  REPO_ROOT="$WS/some-other-repo"
  mkdir -p "$REPO_ROOT"

  run _qm_resolve_pm_root
  [ "$status" -eq 0 ]
  [ "$output" = "$WS/unified-trading-pm" ]
}

@test "renamed worktree: this run's OWN repo IS the PM checkout, just not named that" {
  # No unified-trading-pm sibling at all -- REPO_ROOT itself has the shape (the worktree case).
  REPO_ROOT="$WS/wt-driftfix-96974/unified-trading-pm-really"
  make_pm_shape "$REPO_ROOT"
  WORKSPACE_ROOT="$(dirname "$REPO_ROOT")"

  run _qm_resolve_pm_root
  [ "$status" -eq 0 ]
  [ "$output" = "$REPO_ROOT" ]
}

@test "sibling search: a differently-named sibling has the right shape, found by content" {
  REPO_ROOT="$WS/market-tick-data-service"   # the repo actually being shipped -- NOT PM
  mkdir -p "$REPO_ROOT"
  make_pm_shape "$WS/pm-clone-renamed"
  WORKSPACE_ROOT="$WS"

  run _qm_resolve_pm_root
  [ "$status" -eq 0 ]
  [ "$output" = "$WS/pm-clone-renamed" ]
}

@test "unresolvable: no directory anywhere has the PM shape -- fails loud, not with a guess" {
  REPO_ROOT="$WS/market-tick-data-service"
  mkdir -p "$REPO_ROOT"
  mkdir -p "$WS/some-unrelated-dir"
  WORKSPACE_ROOT="$WS"

  run _qm_resolve_pm_root
  [ "$status" -eq 1 ]
  [ -z "$output" ]
}

@test "a directory with only ONE of the two required subdirs does not count as PM-shaped" {
  mkdir -p "$WS/unified-trading-pm/plans"   # scripts/quality_gates/ deliberately absent
  WORKSPACE_ROOT="$WS"
  REPO_ROOT="$WS/other"
  mkdir -p "$REPO_ROOT"

  run _qm_resolve_pm_root
  [ "$status" -eq 1 ]
}

@test "CALL SITE: PM_ROOT is resolved once near the top, before push-host-governor sourcing" {
  run grep -n 'PM_ROOT="\$(_qm_resolve_pm_root)"' "$QM_SH"
  [ "$status" -eq 0 ]
  pm_root_line="${lines[0]%%:*}"

  run grep -n '_QM_PUSH_GOV_FILE="\$PM_ROOT' "$QM_SH"
  [ "$status" -eq 0 ]
  gov_line="${lines[0]%%:*}"

  [ "$pm_root_line" -lt "$gov_line" ]
}

@test "CALL SITE: the literal 'unified-trading-pm' directory-name assumption is gone from the executed generate-manifest call" {
  # The EXECUTED form (assigned to _GEN_OUT and actually run) must use the resolved PM_ROOT.
  # A bare mention of the old literal path survives on purpose in the human-facing "run these
  # by hand" help text a few lines below (never executed by this script) -- so this checks the
  # specific executed line, not "no occurrence of the string anywhere in the file".
  run grep -n '_GEN_OUT="\$(python3 unified-trading-pm/scripts/manifest/generate-derived-manifest.py' "$QM_SH"
  [ "$status" -ne 0 ]
  run grep -n '_GEN_OUT="\$(python3 "\$PM_ROOT/scripts/manifest/generate-derived-manifest.py"' "$QM_SH"
  [ "$status" -eq 0 ]
}

@test "CALL SITE: STAGE 1.5 counts sibling repos and skips with a diagnosis instead of running alignment against none" {
  run grep -n '_qm_sibling_repo_count' "$QM_SH"
  [ "$status" -eq 0 ]
  run grep -n 'Dependency alignment SKIPPED' "$QM_SH"
  [ "$status" -eq 0 ]
}

@test "CALL SITE: STAGE 2 names the PM_ROOT assumption instead of a bare not-found when unresolved" {
  run grep -n 'Pre-flight audit requires a sibling unified-trading-pm checkout' "$QM_SH"
  [ "$status" -eq 0 ]
}
