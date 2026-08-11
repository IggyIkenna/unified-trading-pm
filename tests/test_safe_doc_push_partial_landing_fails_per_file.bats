#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_partial_landing_fails_per_file.bats -- the per-file REMOTE verification gate
# in scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10,
# [SCRIPT] P1). End-to-end against a real local origin/clone pair.
#
# THE GAP (measured 2026-08-10): a multi-file `--files` invocation naming N paths can land a
# partial commit and still exit 0 with "✅ Pushed" -- one named path's intended change is dropped
# from the commit while the rest ship. The two existing verification layers are both blind to it:
#   * verify_pushed() is COMMIT-LEVEL: `git branch -r --contains HEAD` proves A commit reached
#     origin/$BRANCH, not that every named path's state reached it.
#   * _sdp_assert_entry_change_landed() (the F8 gate) deliberately SKIPS paths absent from disk
#     at entry -- a staged deletion or rename source -- because "your change" is not expressible
#     as a blob move there. So a dropped DELETION is invisible to it, and `git log -1 -- <path>`
#     stays non-empty for the old commit that ADDED the path, so verify_committed() passes too.
#
# THE FIX: verify_remote_per_file() compares what origin/$BRANCH actually carries against the
# state each named path was supposed to land in (derived from the entry fingerprints): a modify/
# create must now differ from the pre-run HEAD blob; a deletion/rename source must be gone from
# the remote. Any mismatch exits non-zero NAMING the specific paths that did not reach the
# remote, instead of a single commit-level check passing on a partial landing.
#
# Deletion staging note: the test deletes with a plain `rm` (the path stays in the index, so
# `git add -- <path>` stages a real D). `git rm` removes the index entry and `git add` then
# refuses with "pathspec did not match any files" -- that is a different, unrelated failure.
#
# Every test forces SDP_ISOLATED=0 (same rationale as the sibling certification test: the gate
# itself is identical on both paths, and the shared-index path keeps the harness unambiguous).
#
# Run: npx bats tests/test_safe_doc_push_partial_landing_fails_per_file.bats

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
  echo "old" > old.md
  git add README.md doc.md old.md
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

@test "a named DELETION dropped from the commit fails naming that path, not a green push" {
  # The partial-landing shape nothing existing catches: two named files, the modify lands and
  # the deletion does not. A plain `rm` keeps the path in the index so the staging step can
  # re-stage the D; the pre-commit hook then silently undoes it before the commit -- the same
  # window a peer session's bare `git commit` occupies in production. On disk nothing looks
  # wrong (old.md is never "reverted", it is simply never deleted).
  echo "modified" > doc.md
  rm old.md

  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
git checkout HEAD -- old.md 2>/dev/null || true
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  run bash "$SCRIPT" "docs: modify doc + delete old" --files "doc.md old.md"

  # Must NOT report success...
  [ "$status" -ne 0 ]
  [[ "$output" != *"✅ Pushed"* ]]
  [[ "$output" != *"✅ Nothing to commit"* ]]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  # ...and must name the SPECIFIC path that did not reach the remote.
  [[ "$output" == *"old.md"* ]]
  # The remote genuinely still carries old.md -- the deletion never landed.
  run git ls-tree --name-only "origin/live-defi-rollout" -- old.md
  [ -n "$output" ]
}

@test "a three-shape push (modify + delete + create) still certifies success (control)" {
  # All three named shapes land: the delete side of a plain `rm`, a modify, and a brand-new
  # file. verify_remote_per_file must not false-positive on any of them.
  echo "modified" > doc.md
  rm old.md
  echo "brand new" > new.md

  run bash "$SCRIPT" "docs: modify doc + delete old + add new" --files "doc.md old.md new.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # Modify reached the remote.
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"modified"* ]]
  # Deletion reached the remote (gone from origin).
  run git ls-tree --name-only "origin/live-defi-rollout" -- old.md
  [ -z "$output" ]
  # Create reached the remote.
  run git ls-tree --name-only "origin/live-defi-rollout" -- new.md
  [ -n "$output" ]
}
