#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's end-to-end self-verification
# (safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md, todo 2).
#
# THE BUG: every success claim in the script trusted an intermediate command's own exit code /
# message text (a real `git commit` returning 0, a "nothing to commit" message, a `git push`
# returning 0) instead of re-deriving the actual fact the caller cares about -- did the named
# file's content actually land in HEAD's history and reach the remote branch. A stubbed `git
# commit` that returns 0 without creating a real commit (simulating any bug/race upstream of
# this script's own commit call that makes the exit code lie) previously would have been
# indistinguishable from a genuine success once `committed=true` was set.
#
# THE FIX: after a real `git commit` succeeds, assert `git log --oneline -1 -- <file>` is
# non-empty for every named file (verify_files_in_history); after `git push` succeeds, assert
# `git branch -r --contains HEAD` lists the target branch (verify_push_landed). Either failing
# now exits 8, never a false ✅.

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

  # Fake `sleep` so retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
}

@test "a stubbed no-op 'git commit' (exit 0, creates no commit) is caught by self-verification, not reported as success" {
  echo "brand new content" > new_doc.md

  # A fake `git` on PATH ahead of the real one: forwards every subcommand to the real git
  # EXCEPT `commit`, which it swallows entirely -- simulating any upstream bug/race that makes
  # `git commit`'s own exit code lie about a commit actually having been created (the exact
  # gap this fix closes: no downstream code re-derives the fact from history).
  REAL_GIT="$(command -v git)"
  cat > "${WORK}/bin/git" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == "commit" ]]; then
  exit 0
fi
exec "${REAL_GIT}" "\$@"
EOF
  chmod +x "${WORK}/bin/git"

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  [ "$status" -eq 8 ]
  [[ "$output" == *"SELF-VERIFICATION FAILED"* ]]
  [[ "$output" != *"✅ Pushed"* ]]
  run git log --oneline -- new_doc.md
  [ -z "$output" ]
}

@test "a stubbed no-op 'git push' (exit 0, does not update the remote-tracking ref) is caught, not reported as success" {
  echo "brand new content" > new_doc2.md

  # Real git for everything except `push`, which is swallowed -- simulating a push whose exit
  # code lies about origin/<branch> actually having been updated.
  REAL_GIT="$(command -v git)"
  cat > "${WORK}/bin/git" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == "push" ]]; then
  exit 0
fi
exec "${REAL_GIT}" "\$@"
EOF
  chmod +x "${WORK}/bin/git"

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc2" --files "new_doc2.md"

  [ "$status" -eq 8 ]
  [[ "$output" == *"SELF-VERIFICATION FAILED"* ]]
  [[ "$output" != *"✅ Pushed"* ]]
}

@test "a genuine end-to-end success still verifies and reports the branch-contains proof" {
  echo "brand new content" > new_doc3.md

  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc3" --files "new_doc3.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"*"(verified: origin/live-defi-rollout contains HEAD)"* ]]
  run git log --oneline -1 -- new_doc3.md
  [ -n "$output" ]
}
