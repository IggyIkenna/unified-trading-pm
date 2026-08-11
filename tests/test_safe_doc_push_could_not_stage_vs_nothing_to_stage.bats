#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's staging-failure wording
# (safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md, todo 3).
#
# THE BUG: `git add -- "${FILES[@]}"`'s own exit code was never checked. Under index.lock
# contention (the exact incident mechanism -- a peer session's autostash sweep holding the
# lock while this script's `git add` ran), staging silently failed and the script fell
# straight into "nothing staged for the named files -- checking if content already matches
# HEAD" -- the SAME wording used for the genuinely benign case where staging succeeded but
# there was simply nothing new to add. A human (or a downstream agent trusting the log) reads
# that phrasing as "probably fine, checking a fallback" when it is actually a hard failure to
# stage at all.
#
# THE FIX: `git add`'s exit code is checked explicitly. An index.lock failure there now emits
# a distinct "could not stage named files ... HARD FAILURE" message and retries immediately,
# never reaching the ambiguous branch. Only a successful `git add` with nothing left to commit
# reaches the (now clearly-labeled) "nothing to stage ... staging completed cleanly" message.

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

  # Fake `sleep` on PATH so the script's retry backoff is instant -- these tests care about
  # the eventual exit code and message, not real wall-clock contention.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
}

@test "a persistent index.lock during 'git add' is reported as a hard could-not-stage failure, never the benign nothing-to-stage wording" {
  echo "brand new content" > new_doc.md
  # Reproduces the incident mechanism directly: the lock is held for the entire run, so
  # every attempt's `git add` fails.
  touch .git/index.lock

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  rm -f .git/index.lock

  [ "$status" -ne 0 ]
  [[ "$output" == *"could not stage named files"* ]]
  [[ "$output" == *"HARD FAILURE"* ]]
  # The old unconditional wording must never appear verbatim -- it always carried the
  # "nothing staged" phrasing regardless of whether staging failed or genuinely had nothing
  # to add; the fix replaces it with a "nothing to stage" message reached only when `git add`
  # itself succeeded.
  [[ "$output" != *"nothing staged for the named files"* ]]
  run git log --oneline -- new_doc.md
  [ -z "$output" ]
}

@test "a tracked file already identical to HEAD at entry no longer short-circuits to success (exit 12)" {
  # SUPERSEDED ASSERTION (2026-08-11, pm_repo_commit_rate_exceeds_precommit_hook_duration F8,
  # landed in 91d559ee19). This used to assert exit 0 on the reading that "working-tree content
  # matches HEAD" means "a peer already landed the identical edit". Measured 2026-08-10 disproved
  # that: the same state is produced when the caller's edit is REVERTED before the script hashes
  # it. The run now exits 12 (NOTHING OF YOURS SHIPPED); SDP_ALLOW_NOOP=1 restores idempotence
  # for callers that genuinely want it. Mirrors the pattern the same commit applied to
  # test_safe_doc_push_untracked_file_never_false_success.bats.
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout

  # Nothing changed on disk since the commit -- staging succeeds but has nothing new to add.
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"

  [ "$status" -eq 12 ]
  [[ "$output" == *"nothing to stage for the named files"* ]]
  [[ "$output" == *"staging completed cleanly"* ]]
  [[ "$output" != *"could not stage named files"* ]]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  [[ "$output" == *"NOTHING OF YOURS SHIPPED"* ]]

  # The fallback's ORIGINAL intent -- a peer genuinely landed the identical content -- is still
  # honoured, as an explicit opt-in rather than an inference.
  SDP_ALLOW_NOOP=1 PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"
  [ "$status" -eq 0 ]
  [[ "$output" == *"✅"* ]]
}

@test "could-not-stage and nothing-to-stage produce distinct exit codes for the same script" {
  # could-not-stage: persistent index.lock on a brand-new file -- must not succeed.
  echo "brand new content" > new_doc.md
  touch .git/index.lock
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"
  rm -f .git/index.lock
  stage_fail_status="$status"

  # nothing-to-stage: tracked file identical to HEAD at entry -- a deliberate no-op. Since the
  # 2026-08-11 landed-content certification gate (91d559ee19) this exits 12, not 0 -- but it is
  # still cleanly distinct from a hard staging failure.
  echo "shared content" > tracked.md
  git add tracked.md
  git commit -q -m "add tracked.md"
  git push -q origin HEAD:live-defi-rollout
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: no-op edit" --files "tracked.md"
  nothing_to_stage_status="$status"

  [ "$stage_fail_status" -ne 0 ]
  [ "$nothing_to_stage_status" -eq 12 ]
  [ "$stage_fail_status" -ne "$nothing_to_stage_status" ]
}
