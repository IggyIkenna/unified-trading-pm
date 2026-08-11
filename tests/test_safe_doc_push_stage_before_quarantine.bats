#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_stage_before_quarantine.bats -- the payload is staged BEFORE the autostash
# chain-breaker's extreme-backlog quarantine, so the work being shipped can never be swept into
# the stash it is about to be compared against
# (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, P0 "Do not quarantine before
# staging").
#
# THE BUG (measured 2026-08-10, "Second symptom"): safe-doc-push.sh called
# autostash_guard_bound_backlog BEFORE its attempt loop staged the --files. With an extreme
# autostash backlog (>=10 entries) the guard quarantines the current dirty tree into a named
# stash -- and when the protected-match failed (quickmerge's argument-order bug proved it can,
# 2026-08-11), the caller's OWN payload was swept. The run then looked for changes to stage,
# found none (they were stashed), hit the "nothing to stage ... already matches HEAD" fallback,
# and exited 0 with the work gone while printing a green success.
#
# THE FIX UNDER TEST: stage the named files FIRST (they are the payload), then quarantine only
# what REMAINS unstaged. The guard's sweep reads `git diff --name-only` -- the UNSTAGED view of
# the tree -- so a staged payload is structurally invisible to it; the protected-path list is
# belt-and-suspenders, no longer load-bearing for the payload's survival.
#
# Run: bats tests/test_safe_doc_push_stage_before_quarantine.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work" || return 1
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "initial" > README.md
  echo "base" > doc.md
  echo "base" > other.md
  echo "base" > noise.md
  git add README.md doc.md other.md noise.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout >/dev/null 2>&1

  # Fake `sleep` on PATH so the script's retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
  export PATH="${WORK}/bin:$PATH"
  # Isolated mode re-execs inside a throwaway worktree; the guard + quarantine run identically
  # on the shared-index path, which is where the shared-checkout hazard actually lives.
  export SDP_ISOLATED=0
}

# Push the stash list past the guard's >=10 extreme-backlog trigger with entries whose subjects
# match what it counts ('autostash'). noise.md is TRACKED (committed in setup) -- `git stash
# push -- <pathspec>` silently does nothing for an untracked path without -u.
arm_extreme_backlog() {
  for i in $(seq 1 11); do
    echo "noise $i" > noise.md
    git stash push -q -m "autostash" -- noise.md
  done
  [ "$(git stash list | grep -ci autostash)" -ge 10 ]
}

@test "under an extreme backlog, the payload is staged first and ships; only the non-payload dirty file is quarantined" {
  arm_extreme_backlog
  echo "my genuine change" > doc.md   # the payload -- MUST survive the quarantine sweep
  echo "peer edit" > other.md         # NOT in --files -- the quarantine's legitimate target

  run bash "$SCRIPT" "docs: real change" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # The extreme-path actually ran (the incident's own log line), so the quarantine fired.
  [[ "$output" == *"current dirty tree quarantined"* ]]
  # The payload reached origin WITH its content -- not the "already matches HEAD" false-success.
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"my genuine change"* ]]
  run git show "HEAD:doc.md"
  [[ "$output" == *"my genuine change"* ]]
  # The non-payload dirty file was quarantined + restored to origin content, parked (not dropped).
  grep -qx "base" other.md
  run git stash list
  [[ "$output" == *"pre-reconcile quarantine"* ]]
  # The quarantine stash parked the non-payload file's edit...
  run git stash show -p 'stash@{0}'
  [[ "$output" == *"peer edit"* ]]
  # ...and ALSO records the payload's content -- NOT because the payload was swept (it was
  # committed and reached origin, above), but because `git stash push -- <pathspec>` records the
  # index tree verbatim and the payload was ALREADY IN THE INDEX when the quarantine ran. That
  # is the ordering under test: staged first, then quarantine only what remains. Before the fix
  # (quarantine ran before any staging) this diff showed only other.md.
  [[ "$output" == *"my genuine change"* ]]
}

@test "CALL SITE: safe-doc-push stages the named files before the chain-breaker quarantine" {
  # The ordering IS the fix -- stage the payload, then quarantine only what remains. Anchored on
  # the LINE ORDER (like the existing call-site test) so a future re-arrangement that puts the
  # guard call before staging is caught even though the behavioural test above stays green (the
  # protected-list hides the regression while it works).
  local add_line guard_line
  add_line=$(grep -n 'git add -- "\${FILES\[\@\]}"' "${REPO_ROOT}/scripts/dev/safe-doc-push.sh" | head -1 | cut -d: -f1)
  guard_line=$(grep -n 'autostash_guard_bound_backlog "\${FILES\[\*\]}"' "${REPO_ROOT}/scripts/dev/safe-doc-push.sh" | head -1 | cut -d: -f1)
  [ -n "$add_line" ] && [ -n "$guard_line" ]
  [ "$add_line" -lt "$guard_line" ]
}

@test "control: without an extreme backlog the payload still ships normally (fix must not break the happy path)" {
  echo "my genuine change" > doc.md

  run bash "$SCRIPT" "docs: real change" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"my genuine change"* ]]
}
