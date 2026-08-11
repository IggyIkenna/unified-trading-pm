#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_per_file_remote_verification.bats -- the per-file REMOTE-surface gate in
# scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, the
# "Verify per-file" todo). End-to-end against a real local origin/clone pair.
#
# THE GAP THIS CLOSES: a `--files` invocation naming N paths could land a commit that carried
# FEWER than N paths and still report success. The dropped path passes every prior check:
# verify_committed's `git log -1 -- <path>` matches a PRIOR commit (non-empty), verify_pushed
# only checks HEAD reached the branch, and _sdp_assert_entry_change_landed (exit 13) `continue`s
# past ABSENT/MISSING paths -- so a DELETION (the old side of a `git mv` rename) that got dropped
# produced a create-only commit with zero failures. That is the archival bug this issue documents.
#
# THE FIX: _sdp_verify_named_reached_remote, wired into _sdp_certify_success as exit 14, checks
# each named path's state ON origin/$BRANCH after the push:
#   * deletion / rename-source (absent at entry)  -> must be ABSENT on the remote;
#   * modify (diff at entry)                      -> remote blob must differ from the pre-run HEAD blob;
#   * net-new create (absent in entry HEAD)       -> remote must contain the path at all.
# A failing path names the specific path(s) that did not reach the remote.
#
# Every test forces SDP_ISOLATED=0 for the same reason as the landed-content file: isolated mode
# re-execs inside a throwaway worktree, which makes "which checkout a purpose-installed
# pre-commit hook runs against" ambiguous. The gate itself runs in whichever checkout commits.
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
  echo "base" > doc.md
  echo "base" > other.md
  git add doc.md other.md
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

@test "a dropped deletion among 2 named paths exits 14 naming that path, not the landed sibling" {
  # The measured archival shape: caller names N=2 paths -- a deleted source (the old side of a
  # rename) and a modified sibling. `rm` (not `git rm`) keeps the path TRACKED but absent from
  # the working tree, which is exactly the state `git add` needs to stage a deletion. A
  # pre-commit hook reinstates the deleted path in the index, so the commit carries the sibling's
  # change but NOT the deletion. Every pre-existing check passes (verify_committed sees the init
  # commit for doc.md; exit 13 skips ABSENT paths) -- only the per-file remote gate catches that
  # doc.md is still live on origin.
  rm doc.md
  echo "my change" > other.md

  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
git restore --staged -- doc.md 2>/dev/null || true
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  run bash "$SCRIPT" "docs: archive doc, change other" --files "doc.md other.md"

  [ "$status" -eq 14 ]
  [[ "$output" == *"PARTIAL LANDING"* ]]
  [[ "$output" == *"doc.md"* ]]     # the specific dropped path is named
  # The dropped deletion really did not land -- origin still carries doc.md.
  run git cat-file -e "origin/live-defi-rollout:doc.md"
  [ "$status" -eq 0 ]
}

@test "a legitimate deletion + modify (N=2, both land) certifies -- no false positive" {
  rm doc.md
  echo "my change" > other.md

  run bash "$SCRIPT" "docs: archive doc, change other" --files "doc.md other.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # Both landed: doc.md is gone from the remote, other.md carries the change. (cat-file -e on a
  # missing path exits non-zero, but git does not guarantee exactly 1, so assert != 0.)
  run git cat-file -e "origin/live-defi-rollout:doc.md"
  [ "$status" -ne 0 ]
  run git show "origin/live-defi-rollout:other.md"
  [[ "$output" == *"my change"* ]]
}

@test "a net-new file certifies -- the CREATE path is not flagged" {
  echo "net new" > new.md

  run bash "$SCRIPT" "docs: add new" --files "new.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "origin/live-defi-rollout:new.md"
  [[ "$output" == *"net new"* ]]
}
