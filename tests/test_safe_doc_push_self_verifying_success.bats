#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's end-to-end success verification
# (safe_doc_push_reports_success_having_committed_nothing_2026_08_09.md, todo 2).
#
# THE GAP: every "✅ success" path in the script (the real `git commit` success, the
# "nothing to commit" fallback, the "already matches HEAD" fallback, and the final `git push`)
# trusted an intermediate git command's own exit code as proof the named files actually
# landed. Todo 1 (already shipped) closed the specific "untracked file read as already-landed"
# fallback bug, but the underlying trust-the-exit-code pattern was still present everywhere
# else -- a `git commit`/`git push` call that exits 0 without actually doing what it claims
# (a stub in a test harness, or some deeper git-state anomaly) would still be reported as
# success.
#
# THE FIX: verify_committed() (`git log --oneline -1 -- <path>` non-empty for every named
# file) and verify_pushed() (`git branch -r --contains HEAD` includes origin/$BRANCH) are
# now the actual ground-truth checks gating every "✅" line -- never an intermediate
# command's exit status alone.
#
# This test reproduces the "stubbed no-op commit" scenario directly: a fake `git` on PATH
# intercepts `git commit` and returns 0 without creating any commit, while every other git
# subcommand (add, push, log, branch, fetch, pull, ...) passes through to the real binary
# unchanged. Against the pre-fix script this reports "✅ Pushed ..." and exits 0 for content
# that was never committed; against the fix it must exit non-zero and never claim success.

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  REAL_GIT="$(command -v git)"

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

  # Fake `sleep` on PATH so the script's retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"

  # Stubbed `git` lives in its OWN directory, separate from the sleep-only bin dir above, so
  # only the test that explicitly opts in (by prepending stub_bin to PATH) gets the fake
  # commit -- the control test below must exercise the REAL git commit unmodified.
  mkdir -p "${WORK}/stub_bin"
  # `git commit ...` is a silent no-op that exits 0 without committing anything; every other
  # subcommand execs straight through to the real git binary.
  cat > "${WORK}/stub_bin/git" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == "commit" ]]; then
  exit 0
fi
exec "${REAL_GIT}" "\$@"
EOF
  chmod +x "${WORK}/stub_bin/git"
}

@test "a stubbed no-op git commit is never reported as success (end-to-end verification catches it)" {
  echo "brand new content" > new_doc.md

  PATH="${WORK}/stub_bin:${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  [ "$status" -ne 0 ]
  [[ "$output" != *"✅ Pushed"* ]]
  [[ "$output" != *"✅ Nothing to commit"* ]]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  [[ "$output" == *"verification failed"* ]]
  run git log --oneline -- new_doc.md
  [ -z "$output" ]
  run git ls-remote "${WORK}/origin.git" live-defi-rollout
  [[ "$output" != *"new_doc"* ]]
}

@test "a genuine commit+push still reports verified success (control case, fix must not break the happy path)" {
  echo "brand new content" > new_doc.md

  # No stubbing here -- the real git binary, unmodified PATH beyond the fake sleep.
  PATH="${WORK}/bin:$PATH" run bash "$SCRIPT" "docs: add new_doc" --files "new_doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git log --oneline -- new_doc.md
  [ -n "$output" ]
}
