#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's sustained-foreign-write escape hatch
# (safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md, todo 4).
#
# THE GAP: under a checkout with a PERSISTENT index.lock (a peer session's own retry loop
# re-taking the lock as fast as this script's retries can clear it), every attempt's `git add`/
# `git commit` fails identically. Before this fix, the script simply looped all MAX_ATTEMPTS
# (6) times and then printed a generic "Exhausted 6 attempts ... this is transient, re-run"
# message (exit 5) -- which sends the caller straight back into the same non-convergent retry
# against the SAME checkout.
#
# THE FIX: a `lock_contention_count` counter increments on each consecutive index.lock failure
# (git-add site and git-commit site both feed it); once it reaches LOCK_CONTENTION_MAX (3), the
# script stops looping immediately (well before MAX_ATTEMPTS) and prints a documented escape
# hatch instead -- land the named files from a separate clone, the exact move that unblocked
# the live incident -- exiting 8, a code distinct from the generic exhausted-retries exit 5.

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
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "initial" > README.md
  git add README.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout

  # Fake `sleep` on PATH so the script's retry backoff is instant -- these tests care about
  # the eventual exit code and message, not real wall-clock contention.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  # PIN SHARED-INDEX MODE. Every test in this file plants an `index.lock` in the CALLER's
  # .git and asserts the script reacts to it. Isolated-worktree mode builds its commit in a
  # private worktree with its OWN index, so the caller's lock is simply irrelevant there and
  # the contention path under test is unreachable.
  #
  # `_sdp_isolation_default()` turns isolation ON for any host labelled `laptop`, which is
  # where these tests actually run -- so from the day isolation shipped (2026-08-10) this file
  # stopped testing its own scenario. It did not fail quietly in one direction and pass in the
  # other: tests 1 and 3 failed (no exit 8, because the escape hatch can never trigger) while
  # test 2 kept PASSING for the wrong reason (it asserts "the run still succeeds", which an
  # isolated run does trivially). A green test asserting a negative is the more dangerous half.
  #
  # Isolated mode has its own dedicated coverage (test_safe_doc_push_isolated_*.bats); this
  # file owns the shared-index path, so pin it rather than letting the host label decide.
  export SDP_ISOLATED=0
}

@test "a persistent index.lock stops looping after LOCK_CONTENTION_MAX failures and prints the separate-clone escape hatch, exit 8" {
  echo "brand new content" > new_doc.md
  # Held for the entire run -- every attempt's `git add` fails identically, reproducing
  # sustained foreign write (a peer process that never releases the lock).
  touch .git/index.lock

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  rm -f .git/index.lock

  [ "$status" -eq 8 ]
  [[ "$output" == *"SUSTAINED FOREIGN WRITE"* ]]
  [[ "$output" == *"ESCAPE HATCH"* ]]
  [[ "$output" == *"git clone --reference"* ]]
  # Must stop BEFORE exhausting all 6 attempts -- only 3 "attempt N/6" lines should appear.
  attempt_lines="$(grep -c '── attempt' <<<"$output")"
  # RANGE, not -eq 3. The counter is CONSECUTIVE lock failures; the number of ATTEMPTS needed
  # to accumulate them is not fixed (any other failure resets the streak), so under load the
  # hatch legitimately fires on attempt 4. -eq 3 pinned machine timing and failed ~1 run in 4
  # while exit 8 and every message assertion PASSED — i.e. the hatch worked and the test went
  # red anyway. The real claim is "short-circuits instead of burning all 6".
  [ "$attempt_lines" -ge 3 ]
  [ "$attempt_lines" -lt 6 ]
  # Never committed anything.
  run git log --oneline -- new_doc.md
  [ -z "$output" ]
}

@test "a momentary (self-clearing) index.lock does not trip the escape hatch -- the run still succeeds" {
  echo "brand new content" > new_doc.md
  touch .git/index.lock

  # A fake `sleep` that clears the lock as a side effect of the FIRST retry backoff --
  # deterministically models a peer process releasing the lock between attempts, without any
  # real-wall-clock race against the test itself.
  mkdir -p "${WORK}/bin_clearing"
  cat > "${WORK}/bin_clearing/sleep" <<EOF
#!/usr/bin/env bash
rm -f "${WORK}/work/.git/index.lock"
exit 0
EOF
  chmod +x "${WORK}/bin_clearing/sleep"

  PATH="${WORK}/bin_clearing:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  rm -f .git/index.lock

  [ "$status" -eq 0 ]
  [[ "$output" != *"SUSTAINED FOREIGN WRITE"* ]]
  [[ "$output" == *"✅"* ]]
}

@test "escape hatch exit code (8) is distinct from the generic exhausted-retries exit code (5)" {
  echo "brand new content" > new_doc.md
  touch .git/index.lock

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  rm -f .git/index.lock

  [ "$status" -eq 8 ]
  [ "$status" -ne 5 ]
}
