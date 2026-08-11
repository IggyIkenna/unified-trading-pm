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
  # Tests must NOT take a host-wide lock. push-host-governor.sh hands out K=8 tokens PER HOST,
  # shared with real safe-doc-push runs, so under `bats -j` these contended with each other AND
  # with a peer session's genuine push — exit codes became a function of unrelated fleet
  # activity. One run green, the next red, the failure moving between tests.
  export PUSH_GOV_DISABLE=true
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

# ── The re-wrap gap (2026-08-11) ────────────────────────────────────────────────────────────────
# The reconciler above keyed on BYTE-identity. prek runs prettier inside the isolated worktree, so
# for a prose `.md` the landed blob is RE-WRAPPED and byte-identity never holds — the check was a
# no-op on exactly the file class it was written for. Measured 3 times in one session, each a pure
# re-wrap with zero word-level difference, each costing a conflicted pull (and once a failed
# quality gate via the conflict-marker check).
#
# The end-to-end path cannot reproduce this deterministically (it needs prettier to fire inside the
# child), so these run the REAL `_sdp_same_content` extracted from the live script — a replica here
# would drift from what ships.

_extract_same_content() {
  sed -n '/^_sdp_same_content()/,/^}/p' "$SCRIPT"
}

@test "same words re-wrapped is recognised as the SAME content" {
  cd "${WORK}/.tabs/29/unified-trading-pm"
  # Committed: one long line. Working copy: identical words, wrapped. Exactly what prettier does.
  printf 'the quick brown fox jumps over the lazy dog and keeps going for a while\n' > wrap.md
  git add wrap.md && git commit -q -m "landed, one line"
  printf 'the quick brown fox jumps over\nthe lazy dog and keeps going\nfor a while\n' > wrap.md

  eval "$(_extract_same_content)"
  run _sdp_same_content wrap.md "HEAD:wrap.md"
  [ "$status" -eq 0 ]
}

@test "a REAL word change is NOT treated as the same content" {
  cd "${WORK}/.tabs/29/unified-trading-pm"
  printf 'alpha beta gamma\n' > real.md
  git add real.md && git commit -q -m "landed"
  printf 'alpha BETA gamma\n' > real.md

  eval "$(_extract_same_content)"
  run _sdp_same_content real.md "HEAD:real.md"
  [ "$status" -ne 0 ]
}

@test "non-markdown is refused even when only whitespace differs — indentation is semantic in code" {
  cd "${WORK}/.tabs/29/unified-trading-pm"
  printf 'if true; then\n  echo hi\nfi\n' > script.sh
  git add script.sh && git commit -q -m "landed"
  printf 'if true; then\n        echo hi\nfi\n' > script.sh

  eval "$(_extract_same_content)"
  run _sdp_same_content script.sh "HEAD:script.sh"
  [ "$status" -ne 0 ]
}

@test "a tracked doc whose content already landed is synced, not left to conflict" {
  # The other half of the gap: two of the three measured hits were TRACKED files, which the
  # untracked-only reconciler never looked at. Left alone, the next pull's autostash pop conflicts
  # on the caller's own doc.
  cd "${WORK}/.tabs/29/unified-trading-pm"
  printf 'shipped words here\n' > tracked.md
  git add tracked.md && git commit -q -m "tracked doc"
  git push -q origin HEAD:live-defi-rollout
  git fetch -q origin
  # Caller still holds the pre-formatter wrapping of the same words.
  printf 'shipped\nwords\nhere\n' > tracked.md

  FILES=(tracked.md)
  BRANCH=live-defi-rollout
  eval "$(_extract_same_content)"
  eval "$(sed -n '/^_sdp_reconcile_caller_duplicates()/,/^}/p' "$SCRIPT")"
  run _sdp_reconcile_caller_duplicates
  [ "$status" -eq 0 ]
  [[ "$output" == *"synced"* ]]
  # Working copy now matches what landed, so the next pull cannot conflict on it.
  run git diff --quiet -- tracked.md
  [ "$status" -eq 0 ]
}
