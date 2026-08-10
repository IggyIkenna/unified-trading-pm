#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_landed_content_certification.bats -- the success-certification gate in
# scripts/dev/safe-doc-push.sh (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10,
# finding F8). End-to-end against a real local origin/clone pair.
#
# THE BUG (two shapes, both measured 2026-08-10, both exiting 0):
#   * The script exited 0 printing "✅ Named files already match HEAD (a concurrent session
#     landed identical content)" for a todo whose content had been REVERTED before the script
#     ever hashed it. "Matches HEAD" was true -- for the exact opposite reason to the one being
#     reported. That heuristic cannot distinguish "a peer already pushed your content" from
#     "your content was destroyed", and resolved both to success.
#   * A push verified end-to-end (verify_committed + verify_pushed both green) whose commit did
#     not carry the caller's change at all. Every existing check passes: a commit really did
#     reach the branch, and history really does contain the path -- just not your work.
#
# THE FIX: record HEAD's blob per named path AT ENTRY, and route every success path through one
# gate (_sdp_certify_success):
#   * exit 12 -- every named file was ALREADY identical to HEAD at entry, so this run had
#     nothing of yours to ship and cannot certify what is in HEAD is what you intended. The two
#     causes are indistinguishable from inside the process, so it resolves to neither.
#     SDP_ALLOW_NOOP=1 accepts it as a deliberate idempotent re-run.
#   * exit 13 -- a named file that HAD a real diff at entry is still byte-identical to the
#     PRE-RUN HEAD after the push: your change is not in what shipped.
#
# Every test forces SDP_ISOLATED=0. Isolated-worktree mode is the default in production, but it
# re-execs the script inside a throwaway worktree, which makes "which checkout does the hook
# run against" ambiguous for a test that installs a pre-commit hook on purpose. The gate itself
# is identical on both paths (it runs in whichever checkout the commit happens in).
#
# Run: bats tests/test_safe_doc_push_landed_content_certification.bats

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

@test "a real edit still commits, pushes and certifies (control -- the fix must not break the happy path)" {
  echo "my genuine change" > doc.md

  run bash "$SCRIPT" "docs: real change" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "HEAD:doc.md"
  [[ "$output" == *"my genuine change"* ]]
}

@test "every named file already identical to HEAD at entry is NOT reported as success" {
  # Nothing changed on disk since the last commit. Indistinguishable, from inside this process,
  # between "a peer landed it first" and "your edit was destroyed before we started" -- which is
  # exactly how a destroyed todo was reported green on 2026-08-10.
  run bash "$SCRIPT" "docs: no-op edit" --files "doc.md"

  [ "$status" -eq 12 ]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  [[ "$output" != *"✅ Nothing to commit"* ]]
  [[ "$output" == *"NOTHING OF YOURS SHIPPED, AND THIS SCRIPT CANNOT TELL YOU WHY"* ]]
  # It must hand over the command that resolves the ambiguity, not just refuse.
  [[ "$output" == *"git log -1 --format="* ]]
  [[ "$output" == *"doc.md"* ]]
}

@test "SDP_ALLOW_NOOP=1 accepts the no-op-at-entry case as a deliberate idempotent re-run" {
  SDP_ALLOW_NOOP=1 run bash "$SCRIPT" "docs: no-op edit" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"SDP_ALLOW_NOOP=1"* ]]
  [[ "$output" == *"✅"* ]]
}

@test "a push whose commit dropped the named file exits 13 instead of reporting success" {
  # The measured shape: the commit lands and verifies end-to-end, but carries someone else's
  # file instead of yours. Reproduced with a pre-commit hook that swaps the index out from under
  # the staging step -- the same window a peer session's bare `git commit` occupies in
  # production, and one no revert-detection can see (doc.md is never touched on disk).
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
git restore --staged -- doc.md 2>/dev/null || true
echo "a peer's work" >> other.md
git add other.md
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  echo "my genuine change" > doc.md

  run bash "$SCRIPT" "docs: change doc" --files "doc.md"

  [ "$status" -eq 13 ]
  [[ "$output" == *"THE PUSH LANDED BUT YOUR CHANGE DID NOT"* ]]
  [[ "$output" == *"doc.md"* ]]
  # Disk is untouched, so it must route to the re-run-is-safe branch...
  [[ "$output" == *"DROPPED-FROM-THE-COMMIT shape"* ]]
  # ...and the claim must be true: HEAD really does not carry the change.
  run git show "HEAD:doc.md"
  [[ "$output" != *"my genuine change"* ]]
}

@test "a hook that reformats the named file on the way in is not a false positive" {
  # prosewrap/prettier legitimately rewrite named files during the commit, so what lands equals
  # neither the pre-run HEAD blob nor the caller's entry blob. That must still certify.
  cat > .git/hooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
echo "my genuine change (reflowed by a hook)" > doc.md
git add doc.md
exit 0
HOOK
  chmod +x .git/hooks/pre-commit

  echo "my genuine change" > doc.md

  run bash "$SCRIPT" "docs: change doc" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "HEAD:doc.md"
  [[ "$output" == *"reflowed by a hook"* ]]
}
