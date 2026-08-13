#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for check-branch-drift.sh's DRIFT_GATE_ADVISORY mode
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo 1 / F1).
#
# THE PROBLEM: run_hygiene_sweep.sh --precommit (118s measured) is 1.5-2x PM's own commit
# inter-arrival interval (60-80s measured), so a hard pre-commit drift gate fires on
# essentially every attempt from a reconciling wrapper (safe-doc-push.sh / quickmerge.sh),
# which then re-pays the full sweep on retry for an outcome fixed before it started. Both
# wrappers rebase onto origin and re-verify AFTER committing, so blocking the commit on drift
# buys nothing the post-commit rebase does not already provide.
#
# THE FIX: check-branch-drift.sh honours DRIFT_GATE_ADVISORY=1 by WARNING and exiting 0
# instead of hard-blocking. Scoped to the wrapper's own commit call: safe-doc-push.sh and
# quickmerge.sh export it immediately before `git commit` and unset it immediately after, so
# it cannot leak to a later, unrelated commit in the same shell. A bare human `git commit`
# (DRIFT_GATE_ADVISORY unset) still hard-fails -- that is the case this hook was written for.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  HOOK="${REPO_ROOT}/scripts/hooks/check-branch-drift.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/repo"
  cd "${WORK}/repo"
  git config user.email t@t
  git config user.name t
  git checkout -q -B live-defi-rollout
  echo "initial" >README.md
  git add README.md
  git commit -q -m init
  git push -q origin HEAD:live-defi-rollout

  # A second clone pushes one commit so this clone's HEAD is behind origin.
  git clone -q "${WORK}/origin.git" "${WORK}/peer"
  (
    cd "${WORK}/peer"
    git config user.email peer@t
    git config user.name peer
    git checkout -q live-defi-rollout
    echo "peer change" >>README.md
    git add README.md
    git commit -q -m "peer commit"
    git push -q origin HEAD:live-defi-rollout
  )
}

@test "not behind origin: exits 0 regardless of DRIFT_GATE_ADVISORY" {
  cd "${WORK}/repo"
  # HEAD already matches origin (no peer push landed on THIS clone's view before drift check
  # would fetch) -- fetch first so the hook sees a truly-caught-up state.
  git fetch -q origin live-defi-rollout
  git reset -q --hard origin/live-defi-rollout
  # The hook's own first line short-circuits `exit 0` whenever GITHUB_ACTIONS/CI is set
  # ("Skipped in CI" -- correct for the hook's real deployment, since agents' committing
  # shells always run outside a CI runner). This suite runs INSIDE quality-gates-v2's own
  # GitHub Actions job, so those vars are ambiently set there and were never set on a local
  # dev run -- every test below deterministically exercised the CI-skip early-exit (not the
  # hook logic under test) on every CI run while passing locally by accident, found live
  # 2026-08-13 blocking every PM promote-PR QG slice for 12+ hours. Strip both so the hook
  # always runs its real logic regardless of the ambient runner.
  run env -u GITHUB_ACTIONS -u CI bash "$HOOK"
  [ "$status" -eq 0 ]
}

@test "behind origin, DRIFT_GATE_ADVISORY unset: hard-blocks (the case this hook exists for)" {
  cd "${WORK}/repo"
  run env -u GITHUB_ACTIONS -u CI bash "$HOOK"
  [ "$status" -eq 1 ]
  [[ "$output" == *"BRANCH DRIFT"* ]]
  [[ "$output" == *"Human-only"* ]]
}

@test "behind origin, DRIFT_GATE_ADVISORY=1: warns and exits 0 (reconciling wrapper's own commit)" {
  cd "${WORK}/repo"
  DRIFT_GATE_ADVISORY=1 run env -u GITHUB_ACTIONS -u CI bash "$HOOK"
  [ "$status" -eq 0 ]
  [[ "$output" == *"ADVISORY"* ]]
}

@test "SKIP_BRANCH_DRIFT still wins over DRIFT_GATE_ADVISORY (human override untouched)" {
  cd "${WORK}/repo"
  SKIP_BRANCH_DRIFT=1 DRIFT_GATE_ADVISORY=0 run env -u GITHUB_ACTIONS -u CI bash "$HOOK"
  [ "$status" -eq 0 ]
}

@test "both wrapper scripts scope DRIFT_GATE_ADVISORY to their own commit call only" {
  # Static containment check: each wrapper must export it immediately before invoking
  # `git commit` and unset it before any later commit in the same process, so a livelocked
  # commit call cannot leave a later bare commit accidentally advisory too.
  for wrapper in "${REPO_ROOT}/scripts/dev/safe-doc-push.sh" "${REPO_ROOT}/scripts/quickmerge.sh"; do
    run grep -c "export DRIFT_GATE_ADVISORY=1" "$wrapper"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
    run grep -c "unset DRIFT_GATE_ADVISORY" "$wrapper"
    [ "$status" -eq 0 ]
    [ "$output" -ge 1 ]
  done
}
