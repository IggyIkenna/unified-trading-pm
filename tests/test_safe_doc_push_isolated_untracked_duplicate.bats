#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test: after an ISOLATED push of a file that was UNTRACKED in the caller's tree,
# the caller can still fast-forward.
#
# THE BUG (reported live 2026-08-10 by a peer session, minutes after isolation shipped):
# isolated mode commits from a private worktree, so a NEW file never becomes tracked in the
# caller's own checkout. The caller is left holding an untracked file at a path that origin now
# tracks, and the next `git merge --ff-only` refuses:
#
#     error: The following untracked working tree files would be overwritten by merge:
#            <file>   Please move or remove them before you merge.
#
# which reads like a merge conflict and is not one — the two copies are byte-identical.
#
# THE FIX: after a successful isolated push, remove exactly the copies that are untracked here
# AND byte-identical to the blob that landed. Anything that differs is left alone and warned
# about.
#
# COVERAGE NOTE, stated rather than implied: the "content differs" branch is NOT exercised here.
# Reaching it requires the caller to edit the file while the child process is mid-flight, which
# is a genuine race and not deterministically reproducible in a test. Its behaviour is the safe
# default (touch nothing, warn), so an untested branch cannot destroy content — but it is
# untested, and this comment exists so nobody reads a green run as covering it.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  mkdir -p "${WORK}/.tabs/29"
  git clone -q "${WORK}/origin.git" "${WORK}/.tabs/29/unified-trading-pm"
  cd "${WORK}/.tabs/29/unified-trading-pm"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "initial" > README.md
  git add README.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  export SLOT_CANON_NAME="test"
  export SLOT_CANON_EMAIL="test@example.com"
  export ORCHESTRATOR_VM_ID="planning"
}

@test "isolated push of a NEW file leaves the caller able to fast-forward" {
  cd "${WORK}/.tabs/29/unified-trading-pm"
  echo "brand new content" > newplan.md

  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=1 run bash "$SCRIPT" "docs(plans): new untracked file" --files "newplan.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  [[ "$output" == *"isolated-worktree mode"* ]]
  [[ "$output" == *"removed now-redundant untracked copy"* ]]

  # The redundant copy is gone...
  [ ! -f newplan.md ]
  # ...so the ff-pull that used to refuse now succeeds, and the file arrives TRACKED.
  run git pull --ff-only origin live-defi-rollout
  [ "$status" -eq 0 ]
  [ -f newplan.md ]
  [ "$(cat newplan.md)" = "brand new content" ]
  run git ls-files -- newplan.md
  [ "$output" = "newplan.md" ]
}

@test "shared-index mode is untouched — the file becomes tracked locally, nothing is removed" {
  cd "${WORK}/.tabs/29/unified-trading-pm"
  echo "shared mode content" > sharedplan.md

  PATH="${WORK}/bin:$PATH" SDP_ISOLATED=0 run bash "$SCRIPT" "docs(plans): shared index path" --files "sharedplan.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  [[ "$output" != *"removed now-redundant untracked copy"* ]]
  [ -f sharedplan.md ]
  run git ls-files -- sharedplan.md
  [ "$output" = "sharedplan.md" ]
}
