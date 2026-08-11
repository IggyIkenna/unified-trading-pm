#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_per_file_remote_verification.bats -- the per-file REMOTE verification gate
# in scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, P1).
# End-to-end against a real local origin/clone pair.
#
# THE GAP: verify_pushed proves the COMMIT reached the branch; it does not prove every named file
# in a multi-file `--files` invocation reached it. The create-only archival class is the concrete
# failure: a DELETION dropped from the commit sails past _sdp_assert_entry_change_landed (which
# deliberately skips ABSENT-at-entry files, so the pre-run HEAD blob can never "move" for them) and
# past verify_committed (the ORIGINAL commit that added the path still appears in `git log -- path`),
# so the file stays live on the remote while the run prints success. Measured 2026-08-10: a
# multi-file push landed one of two named paths and still exited 0.
#
# THE FIX: _sdp_verify_pushed_per_file compares origin/$BRANCH's tree against the pre-run HEAD
# blob for every named file that had a real diff at entry:
#   * a create/modify whose change did not reach the remote -> exit 14 naming the path;
#   * a deletion that is STILL present at origin/$BRANCH -> exit 14 naming the path.
# Runs inside _sdp_certify_success, the single gate every success path passes through.
#
# Every test forces SDP_ISOLATED=0 (same reason as test_safe_doc_push_landed_content_certification.bats:
# isolated mode re-execs in a throwaway worktree, making a deliberately-installed pre-commit hook's
# checkout ambiguous; the gate is identical on both paths).
#
# Run: bats tests/test_safe_doc_push_per_file_remote_verification.bats

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
  git add README.md doc.md other.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout >/dev/null 2>&1

  # Fake `sleep` on PATH so retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
  export PATH="${WORK}/bin:$PATH"
  export SDP_ISOLATED=0
}

@test "a real multi-file edit (create + modify) still commits, pushes and certifies (control)" {
  echo "brand new content" > new_doc.md
  echo "modified" > other.md

  run bash "$SCRIPT" "docs: add new + modify other" --files "new_doc.md other.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "origin/live-defi-rollout:new_doc.md"
  [[ "$output" == *"brand new content"* ]]
  run git show "origin/live-defi-rollout:other.md"
  [[ "$output" == *"modified"* ]]
}

@test "a genuine deletion still lands and certifies (control -- fix must not break the happy path)" {
  rm doc.md

  run bash "$SCRIPT" "docs: delete doc" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # The path must actually be GONE from origin, not just from the local tree.
  run git cat-file -e "origin/live-defi-rollout:doc.md"
  [ "$status" -ne 0 ]
}

@test "a deletion dropped from the commit exits 14 naming the path (create-only archival shape)" {
  # The measured create-only failure: the commit lands and verifies end-to-end, but carries a
  # sibling file's change and NOT the named deletion -- so the deleted path survives on origin.
  # Reproduced with a pre-commit hook that restores the deleted file into the index, the same
  # window a peer session's index tampering occupies. The deletion is ABSENT at entry, so
  # _sdp_assert_entry_change_landed cannot see it; only the per-file remote check can.
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
echo "base" > doc.md
git add doc.md
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  rm doc.md
  echo "modified" > other.md

  run bash "$SCRIPT" "docs: delete doc, modify other" --files "doc.md other.md"

  [ "$status" -eq 14 ]
  [[ "$output" == *"PARTIAL LANDING"* ]]
  [[ "$output" == *"doc.md"* ]]
  # The sibling file's change DID land -- this is a per-file partial failure, not a total one.
  run git show "origin/live-defi-rollout:other.md"
  [[ "$output" == *"modified"* ]]
  # ...but the deletion did not: the path is still live on origin.
  run git cat-file -e "origin/live-defi-rollout:doc.md"
  [ "$status" -eq 0 ]
}

@test "per-path precision: only the dropped deletion is named, a genuinely-deleted sibling is not" {
  # Two named deletions in one invocation. The hook restores ONLY doc.md into the index, so
  # doc.md's deletion is dropped (must be named, exit 14) while other.md's deletion genuinely
  # lands (must NOT be named). This is the multi-file per-file partial-success case from the issue.
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
echo "base" > doc.md
git add doc.md
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  rm doc.md
  rm other.md

  run bash "$SCRIPT" "docs: delete doc + other" --files "doc.md other.md"

  [ "$status" -eq 14 ]
  [[ "$output" == *"PARTIAL LANDING"* ]]
  [[ "$output" == *"doc.md"* ]]
  [[ "$output" != *"other.md"* ]]
  run git cat-file -e "origin/live-defi-rollout:doc.md"
  [ "$status" -eq 0 ]
  run git cat-file -e "origin/live-defi-rollout:other.md"
  [ "$status" -ne 0 ]
}
