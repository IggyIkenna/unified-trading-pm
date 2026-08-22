#!/usr/bin/env bats
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's "nothing staged -- does content already match HEAD?"
# fallback (safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md).
#
# THE BUG: the fallback compared the named files' working-tree content against the index via a
# plain `git diff --quiet -- <files>` and treated "quiet" as "already landed, identical content".
# That comparison is ALSO quiet for a file that was never staged at all -- an untracked path has
# no index entry, so a plain `git diff` says nothing about it, not "no difference". Under
# sustained concurrent write (a peer's autostash sweep holding `.git/index.lock`), `git add`
# for the named files fails silently (the script never checked its exit code), the fallback
# fired, and the script printed "✅ ... treating as success" and exited 0 for content that was
# never committed or pushed -- the exact false-progress class CLAUDE.md's Commit+Push+Flip rule
# exists to prevent.
#
# THE FIX: require every named file to already exist in HEAD's tree (`git cat-file -e
# HEAD:<path>`) before trusting the diff. A brand-new file can never satisfy that, so the
# fallback now falls through to a real commit attempt -- which, under the same sustained lock
# contention, keeps failing and the script correctly exhausts its retries and exits non-zero.
#
# This test reproduces the incident's actual mechanism (a stale `.git/index.lock` making `git
# add` fail while `git fetch`/`git pull --no-op` still succeed -- verified empirically, not
# assumed) end-to-end against a real local origin/clone pair, not just the classifier in
# isolation like test_safe_doc_push_failure_classification.bats does.

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

  # Fake `sleep` on PATH so the script's retry backoff is instant -- this test cares about the
  # eventual exit code and message, not real wall-clock contention.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  # Force the shared-index path. Test 1 below induces the incident by planting a stale
  # `.git/index.lock`, and that premise went inert when isolated-worktree mode became the
  # default: a linked worktree has its OWN index (`.git/worktrees/<name>/index`), so the
  # planted lock stops blocking `git add`, staging succeeds, the push lands and the test's
  # `[ "$status" -ne 0 ]` fails. Measured 2026-08-11 -- failing at HEAD, passing at HEAD under
  # SDP_ISOLATED=0, so the mechanism, not the fix, is what had gone stale. Scoping it here is
  # correct rather than a workaround: the false-success branch this file guards is reachable
  # only through the shared index, which is exactly what isolation exists to avoid.
  export SDP_ISOLATED=0
}

@test "a brand-new untracked file is NEVER reported as already-matching-HEAD, even when staging keeps failing" {
  echo "brand new content" > new_doc.md
  # Reproduces the incident: a concurrent process's index.lock is still held while this
  # script's own `git add` runs, so staging silently fails (add returns non-zero, script
  # doesn't check it) even though the file is genuinely new, on disk, and never committed.
  touch .git/index.lock

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  rm -f .git/index.lock

  [ "$status" -ne 0 ]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  [[ "$output" != *"✅ Nothing to commit"* ]]
  run git log --oneline -- new_doc.md
  [ -z "$output" ]
}

@test "a tracked file already identical to HEAD at entry no longer short-circuits to success" {
  # SUPERSEDED ASSERTION (2026-08-11, pm_repo_commit_rate_exceeds_precommit_hook_duration F8).
  # This test used to assert exit 0 here, on the reading that "working-tree content matches
  # HEAD" means "a peer already landed the identical edit". Measured 2026-08-10 disproved that
  # reading: the same state is produced when the caller's edit is REVERTED before this script
  # hashes it, and the script reported "✅ Named files already match HEAD (a concurrent session
  # landed identical content)" and exited 0 for a todo whose content had just been destroyed.
  # The two causes are indistinguishable from inside the process, so the run now refuses to
  # resolve them to a silent success and exits 12 with the command that tells them apart.
  # SDP_ALLOW_NOOP=1 restores the old behaviour for callers that genuinely want idempotence --
  # covered, with the rest of the gate, in
  # tests/test_safe_doc_push_landed_content_certification.bats.
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout

  # Nothing changed on disk since the commit -- "no diff vs HEAD" is genuinely true here.
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"

  [ "$status" -eq 12 ]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  [[ "$output" == *"NOTHING OF YOURS SHIPPED"* ]]

  # The fallback's ORIGINAL intent -- a peer genuinely landed the identical content -- is still
  # honoured, just as an explicit opt-in rather than an inference.
  SDP_ALLOW_NOOP=1 PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"
  [ "$status" -eq 0 ]
  [[ "$output" == *"✅"* ]]
}
