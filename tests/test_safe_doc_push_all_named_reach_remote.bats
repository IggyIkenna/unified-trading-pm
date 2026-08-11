#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_all_named_reach_remote.bats -- the per-file REMOTE success gate in
# scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, the
# "Verify per-file" P1 todo). End-to-end against a real local origin/clone pair, SDP_ISOLATED=0.
#
# THE BUG: a `--files` invocation naming N paths must confirm ALL N reached the remote and fail
# naming the specific paths that did not. Before this fix, a branch-level push check
# (verify_pushed) and the local-HEAD gate (_sdp_assert_entry_change_landed) could both pass while
# one named file was missing from the commit that landed:
#   * a dropped MODIFICATION was caught by exit 13 (entry-change-landed checks local HEAD) --
#     but only for paths PRESENT at entry;
#   * a dropped DELETION (the create-only archival shape) had NO per-file check at all: ABSENT
#     paths are skipped by _sdp_assert_entry_change_landed, verify_committed sees the path's old
#     history and passes, and the run exited 0 with the old-path file still live on origin.
# THE FIX: _sdp_assert_all_named_on_remote reads origin/$BRANCH directly per named path --
# ABSENT-at-entry paths must no longer resolve there, real-diff paths must resolve to a blob that
# differs from the pre-run HEAD blob. On mismatch it names the specific paths and exits 14.
#
# Run: bats tests/test_safe_doc_push_all_named_reach_remote.bats

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
  echo "other" > other.md
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

@test "two named files both land on the remote and certify (control -- multi-file happy path)" {
  echo "change one" > doc.md
  echo "change two" > other.md

  run bash "$SCRIPT" "docs: two changes" --files "doc.md other.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"change one"* ]]
  run git show "origin/live-defi-rollout:other.md"
  [[ "$output" == *"change two"* ]]
}

@test "a deletion dropped from the commit exits 14 naming the path, not success" {
  # The create-only shape: a named deletion never lands because a hook (standing in for a
  # concurrent session) unstages it before commit. The push lands, every pre-existing check
  # passes, and the old-path file stays live on origin. Note the deletion is created with a
  # plain `rm -f` (NOT `git rm --cached`): the path must remain TRACKED in the index so
  # `git add -- <path>` stages the deletion, exactly the state a real archival `git mv` leaves
  # the source half in.
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
git restore --staged -- doc.md 2>/dev/null || true
echo "a peer's work" >> other.md
git add other.md
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  rm -f doc.md

  run bash "$SCRIPT" "docs: archive doc" --files "doc.md"

  [ "$status" -eq 14 ]
  [[ "$output" == *"PARTIAL LANDING"* ]]
  [[ "$output" == *"doc.md"* ]]
  [[ "$output" == *"deletion was dropped from the commit"* ]]
  # The old-path file really is still live on the remote -- the deletion did not land.
  run git rev-parse --verify "origin/live-defi-rollout:doc.md"
  [ "$status" -eq 0 ]
}

@test "a live deletion still certifies (control -- deletion happy path)" {
  # The real deletion shape: the named file is gone from the tree, `git add` stages the
  # deletion, and after the push it no longer resolves on origin -- exit 0.
  rm -f doc.md

  run bash "$SCRIPT" "docs: rm doc" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git rev-parse -q --verify "origin/live-defi-rollout:doc.md"
  [ "$status" -ne 0 ]
}
