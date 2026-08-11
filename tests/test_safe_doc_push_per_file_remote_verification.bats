#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_per_file_remote_verification.bats -- the per-file remote-verification gate in
# scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, todo:
# "Verify per-file: a `--files` invocation naming N paths must confirm all N reached the remote
# and fail naming the specific paths that did not, instead of succeeding on a partial landing").
# End-to-end against a real local origin/clone pair, mirroring
# test_safe_doc_push_landed_content_certification.bats.
#
# THE BUG: a multi-file --files push landed ONE of two named paths (the untracked CREATE went
# through, the tracked MODIFY did not) and still exited 0 -- per-file partial success inside a
# single "successful" invocation. The branch-level check (verify_pushed) proves the COMMIT reached
# the branch; it cannot see a path the commit silently dropped. The entry-change gate
# (_sdp_assert_entry_change_landed, exit 13) deliberately SKIPS paths absent at entry -- the exact
# DELETION shape of a `git mv` whose delete half drops out of the commit (the create-only-archival
# class this issue documents) -- so a dropped delete half slips through every existing check:
# `git log --oneline -1 -- <path>` returns the last historical commit that touched the path
# (non-empty, reads as "committed") and origin contains the commit (reads as "pushed").
#
# THE FIX: verify_pushed_per_file walks the FILES list and asserts each path's intended state
# against origin/$BRANCH: a deletion at entry (absent on disk, tracked in HEAD) must be ABSENT on
# origin; a create/modify must resolve on origin to the blob HEAD carries. Routed through
# _sdp_certify_success so no success path can bypass it. Exit 14 on violation, naming the specific
# paths that did not land.
#
# Every test forces SDP_ISOLATED=0 (same rationale as the landed-content-certification suite: the
# gate is identical on both paths, and a shared-index checkout makes the pre-commit hook that
# simulates the drop unambiguous).
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

@test "a normal multi-file push (modify + deletion) certifies: exit 0, both verified on origin" {
  # `rm -f`, not `git rm`: a working-tree-only deletion (index intact) is the input the script's
  # `git add -- <path>` stages as a deletion for an explicitly named tracked path. `git rm` stages
  # the deletion itself, which makes `git add`'s pathspec matching refuse it ("did not match any
  # files") -- that is the git-mv source case the script's reassert_renames handles instead.
  echo "my genuine change" > doc.md
  rm -f other.md

  run bash "$SCRIPT" "docs: change doc and delete other" --files "doc.md other.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # The modify reached the remote with the new content.
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"my genuine change"* ]]
  # The deletion reached the remote: the path is gone from origin.
  run git rev-parse -q --verify "origin/live-defi-rollout:other.md"
  [ -z "$output" ]
}

@test "a lone archival deletion certifies: exit 0, path gone from origin" {
  rm -f doc.md

  run bash "$SCRIPT" "docs: archive doc" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git rev-parse -q --verify "origin/live-defi-rollout:doc.md"
  [ -z "$output" ]
}

@test "a deletion dropped from the commit exits 14 naming the path -- the partial landing is loud" {
  # The multi-file partial landing: doc.md's modify is staged for real, other.md's deletion is
  # silently dropped from the index by a pre-commit hook (simulating the window where a peer's
  # bare `git commit` or an isolation copy-drop loses the delete half). The commit then carries
  # ONE of two named paths -- and every pre-existing check passes: the commit reached origin, and
  # `git log -1 -- other.md` still resolves (history contains the path). Only the per-file gate
  # sees that the delete half never reached the remote.
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
git restore --staged -- other.md 2>/dev/null || true
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  echo "my genuine change" > doc.md
  rm -f other.md

  run bash "$SCRIPT" "docs: change doc and delete other" --files "doc.md other.md"

  [ "$status" -eq 14 ]
  [[ "$output" == *"deletion of named file did not reach"* ]]
  # The summary must name ONLY the path that did not land, not the one that did.
  [[ "$output" == *"these specific paths did not: other.md"* ]]
  # The failure is true: origin really does still carry other.md...
  run git rev-parse -q --verify "origin/live-defi-rollout:other.md"
  [ -n "$output" ]
  # ...while the one path that DID land is genuinely there with the new content.
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"my genuine change"* ]]
}
