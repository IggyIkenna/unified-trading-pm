#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_noop_push_never_false_success.bats -- the nothing-staged discriminator in
# scripts/dev/safe-doc-push.sh (safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md,
# second-symptom P0 todo 1). End-to-end against a real local origin/clone pair.
#
# THE BUG (measured twice 2026-08-10): when nothing was staged, the script verified "already
# landed" against HEAD (`git diff --quiet -- <files>`). HEAD can match while the caller's payload
# sits quarantined in a stash and origin has NOTHING -- so the run printed "✅ Named files already
# match HEAD" and exited 0 for work that was never pushed. The quarantine restores origin's
# version into the tree, so a working-tree-vs-remote diff is ALSO fooled; the only sound check is
# the caller's ENTRY content (fingerprinted at run start) against the REMOTE ref itself.
#
# THE FIX: the nothing-staged branch now asks "does origin/$BRANCH carry the caller's entry
# content?" -- verified against the remote ref, never against HEAD:
#   * entry content IS on origin/$BRANCH  -> genuine "a concurrent session landed it" no-op,
#     verified + certified, exit 0.
#   * working tree matches HEAD but origin/$BRANCH does NOT carry the entry content -> the payload
#     was swept into a quarantine stash (or destroyed) this run; exit 14, loud, printing the
#     stash ref for recovery. NEVER a green "already landed".
#
# Every test forces SDP_ISOLATED=0 so the shared-index path is exercised deterministically (the
# gate itself is identical on the isolated path -- it runs in whichever checkout the commit would
# happen in).
#
# Run: bats tests/test_safe_doc_push_noop_push_never_false_success.bats

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
  # Point the bare origin's HEAD at live-defi-rollout so a peer `git clone -b` checks it out.
  git -C "${WORK}/origin.git" symbolic-ref HEAD refs/heads/live-defi-rollout

  # Fake `sleep` on PATH so retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
  export PATH="${WORK}/bin:$PATH"
  export SDP_ISOLATED=0
}

# A helper that opens a SECOND clone of origin on live-defi-rollout so a "peer session" can land
# commits between the caller's edit and the script run.
peer_clone() {
  git clone -q -b live-defi-rollout "${WORK}/origin.git" "${WORK}/peer" || return 1
  cd "${WORK}/peer" || return 1
  git config user.email "peer@example.com"
  git config user.name "peer"
  return 0
}

@test "a peer landing identical content mid-run is verified against the REMOTE and succeeds (genuine no-op, exit 0)" {
  # A concurrent session lands the EXACT content the caller is about to push.
  peer_clone
  echo "X" > doc.md
  git add doc.md
  git commit -q -m "peer lands identical content"
  git push -q origin HEAD:live-defi-rollout

  # Caller makes the same edit locally, then runs safe-doc-push.
  cd "${WORK}/work"
  echo "X" > doc.md

  run bash "$SCRIPT" "docs: my edit" --files "doc.md"

  # The no-op is genuine -- origin carries the caller's entry content -- so it certifies as
  # success, and the claim is made against the REMOTE ref, not HEAD.
  [ "$status" -eq 0 ]
  [[ "$output" == *"nothing to stage for the named files"* ]]
  [[ "$output" == *"already match origin/live-defi-rollout"* ]]
  [[ "$output" != *"already match HEAD"* ]]
  [[ "$output" != *"🛑 NOTHING STAGED"* ]]
  # The content really is on the remote.
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"X"* ]]
}

@test "a payload swept into a quarantine stash mid-run is a loud failure (exit 14) that names the stash ref, never success" {
  # A peer advances origin (touches only other.md, NOT doc.md) so the caller's pull is a real
  # merge that fires the post-merge hook -- which simulates the reconcile QUARANTINING the
  # caller's payload (the exact tree-wip-guard / autostash mechanism) by stashing it aside.
  peer_clone
  echo "peer" > other.md
  git add other.md
  git commit -q -m "peer changes other file"
  git push -q origin HEAD:live-defi-rollout

  cd "${WORK}/work"
  echo "MY EDIT" > doc.md
  cat > .git/hooks/post-merge <<'HOOK'
#!/usr/bin/env bash
git stash push -m "simulated-quarantine" -- doc.md 2>/dev/null || true
exit 0
HOOK
  chmod +x .git/hooks/post-merge

  run bash "$SCRIPT" "docs: my edit" --files "doc.md"

  # The working tree now matches HEAD (payload stashed) and origin does NOT carry it -- the
  # discriminator must fail loudly with the recovery ref, and never report a green push.
  [ "$status" -eq 14 ]
  [[ "$output" == *"NOTHING STAGED AND origin/live-defi-rollout DOES NOT CARRY YOUR CONTENT"* ]]
  [[ "$output" == *"RECOVER BEFORE RE-RUNNING"* ]]
  [[ "$output" == *"simulated-quarantine"* ]]
  [[ "$output" != *"✅"* ]]
  # Nothing reached the remote, and the caller's content is genuinely parked in the stash.
  run git show "origin/live-defi-rollout:doc.md"
  [[ "$output" == *"base"* ]]
  [[ "$output" != *"MY EDIT"* ]]
  run git stash list
  [[ "$output" == *"simulated-quarantine"* ]]
}

@test "a real edit still commits, pushes and certifies (control -- the fix must not break the happy path)" {
  cd "${WORK}/work"
  echo "my genuine change" > doc.md

  run bash "$SCRIPT" "docs: real change" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "HEAD:doc.md"
  [[ "$output" == *"my genuine change"* ]]
}

@test "payload staged before reconcile survives a quarantine stash and still lands (stage-before-quarantine, exit 0)" {
  # safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md (P0 todo 2): when a reconcile
  # quarantines the working tree into a stash, a payload that was staged FIRST survives in the
  # index and the commit still lands correctly. The old ordering (quarantine first, stage after)
  # would have lost the payload into the stash with nothing left to stage.
  peer_clone
  echo "peer" > other.md
  git add other.md
  git commit -q -m "peer changes other file"
  git push -q origin HEAD:live-defi-rollout

  cd "${WORK}/work"
  echo "SURVIVING EDIT" > doc.md
  # Simulate the reconcile quarantining the working tree: a post-merge hook that stashes doc.md.
  # The script now stages FIRST, so the payload is safe in the index when the hook fires.
  cat > .git/hooks/post-merge <<'HOOK'
#!/usr/bin/env bash
git stash push -m "simulated-quarantine" -- doc.md 2>/dev/null || true
exit 0
HOOK
  chmod +x .git/hooks/post-merge

  run bash "$SCRIPT" "docs: surviving edit" --files "doc.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # The change landed despite the quarantine — proof the staging-before-reconcile ordering works.
  run git show "HEAD:doc.md"
  [[ "$output" == *"SURVIVING EDIT"* ]]
  run git stash list
  [[ "$output" == *"simulated-quarantine"* ]]
}
