#!/usr/bin/env bats
# Epic: infrastructure_master
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

@test "a genuinely already-landed tracked file (content matches HEAD) still short-circuits to success" {
  # Control case: the fallback's ORIGINAL intended scenario -- an existing tracked file whose
  # working-tree content matches HEAD exactly (a peer already landed the identical edit) --
  # must still report success. The fix must not break this.
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout

  # Nothing changed on disk since the commit -- "no diff vs HEAD" is genuinely true here.
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅"* ]]
}
