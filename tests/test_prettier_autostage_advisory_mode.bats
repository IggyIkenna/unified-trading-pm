#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for prettier-autostage.sh's DRIFT_GATE_ADVISORY mirror
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, F3 / todo 1).
#
# THE PROBLEM (F3): prettier-autostage.sh mirrored check-branch-drift.sh's "behind origin"
# condition and skipped formatting entirely whenever the branch was behind, to avoid leaving
# reflow residue in front of a commit that the drift gate was about to block anyway. Once the
# drift gate gained DRIFT_GATE_ADVISORY (todo 2), that mirror went stale: PM is behind origin
# almost continuously (60-80s commit inter-arrival, measured), so under a reconciling wrapper
# (whose commit will NOT be blocked by drift) the fast path could never self-format --
# committing unformatted content, which the hygiene hook then autofixed, which then tripped
# F2's "files were modified by this hook" -- a closed loop with no exit.
#
# THE FIX: the skip-while-behind guard now also honours DRIFT_GATE_ADVISORY=1 -- when a
# reconciling wrapper is driving the commit, the residue concern does not apply (the wrapper's
# post-commit rebase reconciles regardless), so formatting proceeds even while behind. The
# residue protection is unchanged for a bare `git commit` (DRIFT_GATE_ADVISORY unset).

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  HOOK="${REPO_ROOT}/scripts/hooks/prettier-autostage.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/repo"
  cd "${WORK}/repo"
  git config user.email t@t
  git config user.name t
  git checkout -q -B live-defi-rollout
  echo "# doc" >README.md
  git add README.md
  git commit -q -m init
  git push -q origin HEAD:live-defi-rollout

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

  # Force "no prettier available" so the hook exits via its own graceful-skip path rather
  # than needing a real prettier binary -- irrelevant to what this test asserts (whether the
  # drift-skip fires BEFORE prettier is even located).
  PATH_NO_PRETTIER="${WORK}/bin-empty"
  mkdir -p "$PATH_NO_PRETTIER"
}

@test "behind origin, DRIFT_GATE_ADVISORY unset: skips formatting (residue protection intact for a bare commit)" {
  cd "${WORK}/repo"
  echo "content" >note.md
  git add note.md
  PATH="${PATH_NO_PRETTIER}:/usr/bin:/bin" run bash "$HOOK" note.md
  [ "$status" -eq 0 ]
  [[ "$output" == *"skipping format"* ]]
}

@test "behind origin, DRIFT_GATE_ADVISORY=1: does NOT skip (reconciling wrapper's own commit, F3 loop broken)" {
  cd "${WORK}/repo"
  echo "content" >note.md
  git add note.md
  PATH="${PATH_NO_PRETTIER}:/usr/bin:/bin" DRIFT_GATE_ADVISORY=1 run bash "$HOOK" note.md
  [ "$status" -eq 0 ]
  # The drift-skip's own wording, not the substring "skipping format" -- the no-prettier
  # fallback message below also happens to contain that substring ("skipping format pass").
  # NB: the "no prettier" positive marker is deliberately NOT asserted -- it only appears when
  # BOTH prettier AND npx are absent from PATH, and npx now ships in /usr/bin on the shared VM,
  # so the hook resolves the `npx -y prettier@…` branch and runs real prettier instead. The
  # drift-marker's ABSENCE (plus exit 0 above) is the npx-independent invariant: the hook did
  # not short-circuit on the drift gate.
  [[ "$output" != *"the drift gate will block this commit"* ]]
}
