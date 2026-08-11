#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_noop_false_success.bats -- regression test for the SECOND symptom in
# safe_doc_push_isolation_drops_rename_deletions_2026_08_10.md: a MODIFICATION quarantined by
# the reconcile step and reported as a successful push.
#
# THE BUG (measured twice, 2026-08-10, both exiting 0):
#   "the run quarantines the dirty tree FIRST, then looks for changes to stage -- and finds
#    none, because it just stashed them. It then reaches the 'concurrent session landed
#    identical content' branch, which is a REASONABLE inference from a clean tree matching
#    HEAD, and exits 0."
#
#   The fallback verified "does the working tree match HEAD?" -- and answered "yes" for the
#   EXACT reason that meant the caller's edit had been swept away, not landed. Origin had
#   zero of the commit's content; the local file had all of it; the run exited 0 with
#   DOCPUSH_EXIT=0. Nothing downstream distinguishes "pushed" from "silently pushed nothing".
#
# THE FIX (todo 1): verify against the REMOTE ref, not HEAD.
#   * working tree matches origin/$BRANCH  -> genuinely landed -> certify (which itself
#     distinguishes landed / no-op-at-entry (12) / entry-had-a-diff-but-blob-never-moved (13,
#     the exact incident shape: entry diff reverted to HEAD while origin sat unchanged)).
#   * working tree matches HEAD but NOT origin, with a real diff at entry -> QUARANTINED
#     during reconcile -> loud exit 14 naming the stash and per-file recovery commands.
#
# Every test forces SDP_ISOLATED=0: this fallback is reachable only through the shared index
# (isolated mode copies the caller's files into a private worktree and cannot lose them).
# Reproduced with a `git pull` shim on PATH that simulates a reconcile step which stashes the
# caller's edit and -- in test 2 -- returns success WITHOUT pulling, leaving the working tree
# at the old HEAD while origin has moved ahead: the exact window a peer session's autostash
# sweep occupies in production, and one no revert-detection can see (doc.md is never touched
# on disk after the shim stashes it).
#
# Run: bats tests/test_safe_doc_push_noop_false_success.bats

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
  echo "base" > doc.md
  git add doc.md
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout >/dev/null 2>&1

  # Fake `sleep` on PATH so retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
  export SDP_ISOLATED=0
}

# install_pull_shim <body> -- place a `git` wrapper on PATH that runs <body> once on the first
# real `git pull`, then (unless the body exits) delegates to the real git. Used to simulate a
# reconcile step that quarantines the caller's edit mid-run.
install_pull_shim() {
  local body="$1"
  cat > "${WORK}/bin/git" <<EOF
#!/usr/bin/env bash
if [ "\$1" = "pull" ] && [ "\${_SDP_SHIM_DONE:-0}" = "0" ]; then
  export _SDP_SHIM_DONE=1
  $body
fi
exec /usr/bin/git "\$@"
EOF
  chmod +x "${WORK}/bin/git"
  export PATH="${WORK}/bin:$PATH"
}

# advance_origin -- push a distinct doc.md commit to origin from a throwaway peer clone, so
# origin/live-defi-rollout moves ahead of the work clone's HEAD. The bare origin's HEAD points
# at `master` (default), so a fresh clone checks out nothing and a bare `git push` of the peer
# branch is rejected non-fast-forward -- fetch + checkout the branch explicitly first.
advance_origin() {
  local content="$1"
  git clone -q "${WORK}/origin.git" "${WORK}/peer"
  (
    cd "${WORK}/peer"
    git config user.email "peer@example.com"
    git config user.name "peer"
    git fetch -q origin live-defi-rollout
    git checkout -q -B live-defi-rollout origin/live-defi-rollout
    echo "$content" > doc.md
    git add doc.md
    git commit -q -m "peer change"
    git push -q origin HEAD:live-defi-rollout
  )
}

@test "a caller edit quarantined by reconcile with origin unchanged is exit 13, never success" {
  # The exact incident shape: the caller edits doc.md, the reconcile step's autostash sweeps
  # that edit into a stash (working tree reverts to HEAD), and origin never moves. Old code
  # answered "does it match HEAD? yes -> a peer landed identical content" and exited 0 while
  # the content sat unrecoverable in the stash.
  echo "my genuine change" > doc.md

  # Simulate the reconcile's autostash: quarantine the edit, leaving the working tree at HEAD.
  # The real pull then runs (a no-op here), so the tree stays at HEAD == origin.
  install_pull_shim 'git stash push -q -m "sdp-test-quarantine" -- doc.md || true'

  run bash "$SCRIPT" "docs: my change" --files "doc.md"

  # NOT a success -- and not the benign "already landed" claim.
  [ "$status" -ne 0 ]
  [[ "$output" != *"✅ Pushed"* ]]
  [[ "$output" != *"✅ Named files already match HEAD"* ]]
  [[ "$output" != *"✅ Named files already match origin"* ]]
  [[ "$output" != *"✅ Nothing to commit"* ]]
  # Route through the certify gate: the entry had a real diff and the blob never moved.
  [ "$status" -eq 13 ]
  [[ "$output" == *"THE PUSH LANDED BUT YOUR CHANGE DID NOT"* ]]
  # The recovery guidance must point at the stash, not just refuse (the exit-13 message wraps
  # "recover from the" / "stash" across two lines, so match the stash reference loosely).
  [[ "$output" == *"stash"* ]]
}

@test "a caller edit quarantined while origin ALSO moved is exit 14 with stash recovery" {
  # Variant: origin moves independently (a peer pushes different content) and the reconcile
  # returns success WITHOUT pulling -- so the working tree sits at the old HEAD while the
  # (already-fetched) origin/$BRANCH points at the peer commit. That is the discriminator a
  # HEAD-based check cannot see: the tree "matches HEAD" for the exact reason the edit is
  # quarantined, not landed.
  echo "my genuine change" > doc.md
  advance_origin "peer content"

  # Simulate a reconcile that quarantines the edit and reports success without pulling: the
  # fetch (done by the script itself) has already advanced origin/$BRANCH to the peer commit.
  install_pull_shim 'git stash push -q -m "sdp-test-quarantine" -- doc.md; exit 0'

  run bash "$SCRIPT" "docs: my change" --files "doc.md"

  [ "$status" -eq 14 ]
  [[ "$output" == *"QUARANTINED DURING RECONCILE"* ]]
  # The todo's requirement: a loud FAILURE printing the quarantine ref for recovery. The
  # message prints the OUTPUT of `git stash list` (the ref line, tagged with our test message)
  # plus the per-file extraction command -- assert on what the message actually renders.
  [[ "$output" == *"sdp-test-quarantine"* ]]
  [[ "$output" == *"stash@{0}"* ]]
  [[ "$output" == *"git show 'stash@{0}:doc.md'"* ]]
}

@test "a true no-op at entry still exits 12 even when origin moved and was pulled in" {
  # Guard against regressing the pre-existing no-op contract: caller passes a file that is
  # byte-identical to HEAD at entry, and a peer then advances origin. The reconcile fast-
  # forwards the tree to origin (working == origin now), so branch 1 certifies -- and the
  # certify gate reports the entry no-op as exit 12 (tell-them-apart guidance), NOT as a
  # quarantine (the caller had no edit to quarantine).
  advance_origin "peer content"
  install_pull_shim 'git pull --ff-only -q origin live-defi-rollout 2>/dev/null || true'

  run bash "$SCRIPT" "docs: no-op" --files "doc.md"

  [ "$status" -eq 12 ]
  [[ "$output" == *"NOTHING OF YOURS SHIPPED, AND THIS SCRIPT CANNOT TELL YOU WHY"* ]]
}
