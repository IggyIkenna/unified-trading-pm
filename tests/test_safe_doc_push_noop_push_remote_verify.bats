#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# Regression test for safe-doc-push.sh's "nothing to stage" fallback
# (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, second symptom -- the P0
# "Never report success on a no-op push" todo).
#
# THE BUG (second symptom, reproduced live 2026-08-10 slot 1): when a run's reconcile swept the
# caller's edits into a stash BEFORE staging, nothing got staged, and the old fallback checked
# whether the working tree "already matches HEAD". After the sweep the tree matches HEAD ==
# origin, so every HEAD-based check passed while origin carried ZERO of the caller's content --
# the script printed "✅ ... treating as success" and exited 0. Nothing downstream distinguishes
# "pushed" from "silently pushed nothing". (The quarantine happened because the extreme-pile
# self-arrest stashed the dirty tree before staging; the then-current code did not protect the
# caller's --files -- fixed separately.)
#
# THE FIX: the fallback now verifies the caller's ENTRY content (captured in
# _SDP_ENTRY_FINGERPRINT before any reconcile) against origin/$BRANCH -- the remote ref, not
# HEAD. Content genuinely on the remote = a concurrent session landed identical content =
# legitimate success. Content NOT on the remote AND the on-disk copy no longer matches what the
# run was handed = the run's own reconcile swept the edits into a stash = a LOUD FAILURE (exit
# 10) printing the recovery refs, never a reported success.
#
# This test reproduces the incident's exact precondition directly: a fake `git` on PATH makes
# the script's `git add` first stash the named path (simulating the pre-reconcile quarantine)
# and then no-op, so staging genuinely has nothing to stage and the working tree matches HEAD.
# Every other git subcommand passes through to the real binary.

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
}

@test "nothing-staged + content swept into a stash is a LOUD FAILURE (exit 10), never a reported success" {
  # The caller's edit to a tracked file is the payload being shipped.
  echo "caller's brand-new content that must not be reported as landed" > README.md

  # Reproduce the incident's exact precondition: before the run's `git add` runs, the edit is
  # swept into a stash. Here a fake `git add` stashes the named path first and then no-ops,
  # simulating the pre-reconcile quarantine. Afterwards the working tree matches HEAD == origin,
  # so every HEAD-based check would pass -- the exact false-success trap this fix closes.
  mkdir -p "${WORK}/quarantine_bin"
  cat > "${WORK}/quarantine_bin/git" <<EOF
#!/usr/bin/env bash
if [[ "\$1" == "add" ]]; then
  "${REAL_GIT}" stash push -q -m "safety-snapshot: simulated pre-reconcile quarantine" -- "\${@:3}"
  exit 0
fi
exec "${REAL_GIT}" "\$@"
EOF
  chmod +x "${WORK}/quarantine_bin/git"

  SDP_ISOLATED=0 PATH="${WORK}/quarantine_bin:${WORK}/bin:$PATH" \
    run bash "$SCRIPT" "docs: edit that must NOT report success" --files "README.md"

  # Never a false green -- the exact output the incident produced is forbidden.
  [ "$status" -eq 10 ]
  [[ "$output" != *"treating as success"* ]]
  [[ "$output" != *"✅ Pushed"* ]]
  [[ "$output" != *"✅ Named files"* ]]
  [[ "$output" != *"✅ Nothing to commit"* ]]
  # A loud, actionable failure instead, pointing at the stash for recovery.
  [[ "$output" == *"NOT A SUCCESS"* ]]
  [[ "$output" == *"RECOVER"* ]]
  [[ "$output" == *"stash"* ]]
  # The caller's content is recoverable from the stash, not lost.
  run git stash list
  [[ "$output" == *"safety-snapshot: simulated pre-reconcile quarantine"* ]]
  # And origin really does NOT carry the edit.
  run git cat-file -p "origin/live-defi-rollout:README.md"
  [[ "$output" == "initial" ]]
}

@test "content genuinely already on the REMOTE (a concurrent session landed identical content) still succeeds" {
  # A second clone plays the concurrent session that lands the identical edit first.
  # The bare origin's HEAD points at a nonexistent ref (bare default is master), so the clone
  # has an unborn HEAD -- base the peer branch on the existing origin tip, not on nothing.
  git clone -q "${WORK}/origin.git" "${WORK}/peer"
  cd "${WORK}/peer"
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout origin/live-defi-rollout
  echo "shared-content-that-peer-lands" > README.md
  git add README.md
  git commit -q -m "peer lands identical edit"
  git push -q origin HEAD:live-defi-rollout
  cd "${WORK}/work"
  # The caller's edit is byte-identical to what the peer just pushed -- the ONLY legitimate
  # reading of "nothing to stage": the content genuinely reached the remote already.
  echo "shared-content-that-peer-lands" > README.md

  SDP_ISOLATED=0 PATH="${WORK}/bin:$PATH" \
    run bash "$SCRIPT" "docs: caller edit identical to peer" --files "README.md"

  [ "$status" -eq 0 ]
  [[ "$output" == *"nothing to stage for the named files"* ]]
  [[ "$output" == *"✅"* ]]
  [[ "$output" == *"origin/live-defi-rollout"* ]]
}
