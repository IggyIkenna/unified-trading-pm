#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_safe_doc_push_stages_before_quarantine.bats — the payload MUST be staged BEFORE the
# autostash-backlog quarantine runs
# (safe_doc_push_isolation_drops_rename_deletions_2026_08_10, second symptom).
#
# THE BUG (measured live 2026-08-10, reproduced twice): `autostash_guard_bound_backlog` ran
# FIRST and quarantined the dirty tree, which swept the caller's own --files into a stash
# alongside foreign WIP. The loop then staged "nothing to stage" (the edits were in the stash),
# fell into the "already matches HEAD" heuristic, and exited 0 printing "✅ Named files already
# match HEAD (a concurrent session landed identical content)" — for content that was NOT on
# origin at all. The protected-path argument (the --files list passed to the guard) already
# rotted once at quickmerge's call site the same day, so robustness on both layers matters.
#
# THE FIX: `git add` the payload FIRST, so the guard's `git diff --name-only` (UNSTAGED only)
# is structurally blind to it. The quarantine then only ever touches foreign dirty work, never
# the payload. The in-loop `git add` is retained (a pre-commit hook may have rewritten a named
# file between here and commit, and re-staging lets `git diff --cached --quiet` see the
# autofixed content).
#
# Three layers, because the fix is in the ORDERING, not in the guard logic:
#   1. call-site — the `git add` must appear BEFORE the `autostash_guard_bound_backlog` call;
#   2. structural — the guard's `git diff --name-only` does not see staged content, so even
#      with a BROKEN (empty) protected-path argument, a pre-staged payload survives the
#      ≥10-entry quarantine trigger — the ordering is what keeps the payoff alive, not the
#      path argument;
#   3. end-to-end — through safe-doc-push itself, with an extreme backlog, a genuine edit
#      commits, pushes, and lands correctly.
#
# Hermetic: a real local git repo under BATS_TEST_TMPDIR (bats auto-cleans it), no network.
# Forces SDP_ISOLATED=0 so the inner re-exec does not create a worktree.
#
# Run: bats tests/test_safe_doc_push_stages_before_quarantine.bats

setup() {
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  SCRIPT="${REPO_ROOT}/scripts/dev/safe-doc-push.sh"
  GUARD_SH="${REPO_ROOT}/scripts/dev/tree-wip-guard.sh"

  WORK="${BATS_TEST_TMPDIR}"
  git init -q --bare "${WORK}/origin.git"
  git clone -q "${WORK}/origin.git" "${WORK}/work"
  cd "${WORK}/work" || return 1
  git config user.email "test@example.com"
  git config user.name "test"
  git checkout -q -B live-defi-rollout
  echo "initial" > README.md
  echo "base" > mine.txt
  echo "base" > theirs.txt
  echo "base" > noise.txt
  git add README.md mine.txt theirs.txt noise.txt
  git commit -q -m "init"
  git push -q origin HEAD:live-defi-rollout
  git branch --set-upstream-to=origin/live-defi-rollout live-defi-rollout >/dev/null 2>&1

  # Fake `sleep` on PATH so retry backoff is instant.
  mkdir -p "${WORK}/bin"
  printf '#!/usr/bin/env bash\nexit 0\n' > "${WORK}/bin/sleep"
  chmod +x "${WORK}/bin/sleep"
  export PATH="${WORK}/bin:$PATH"
  export SDP_ISOLATED=0

  # Extract the guard function into this shell so the structural tests can call it directly.
  eval "$(sed -n '/^autostash_guard_bound_backlog() {/,/^}/p' "$GUARD_SH")"
}

# Push the stash list past the guard's >=10 extreme-backlog trigger.
arm_extreme_backlog() {
  for i in $(seq 1 11); do
    echo "noise $i" > noise.txt
    git stash push -q -m "autostash" -- noise.txt
  done
  [ "$(git stash list | grep -ci autostash)" -ge 10 ]
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 1 — call-site ordering (anchors the structural fix)
# ═══════════════════════════════════════════════════════════════════════════════

@test "CALL SITE: 'git add -- FILES' appears BEFORE the autostash_guard_bound_backlog call" {
  # The staging must happen BEFORE the quarantine. The in-loop `git add` (inside the retry
  # loop) is a separate occurrence — this asserts the PRE-LOOP one, which is what the fix
  # introduced. Verifying that the quarantine call comes AFTER the `_sdp_staged_payload=true`
  # line is the precise assertion: the guard call is gated on the staging having succeeded.
  local pre_stage_line quarantine_line
  pre_stage_line="$(grep -n '_sdp_staged_payload=true' "$SCRIPT" | head -1 | cut -d: -f1)"
  quarantine_line="$(grep -n 'autostash_guard_bound_backlog "\${FILES\[\*\]}"' "$SCRIPT" | head -1 | cut -d: -f1)"
  [ -n "$pre_stage_line" ] && [ -n "$quarantine_line" ]
  [ "$pre_stage_line" -lt "$quarantine_line" ]
}

@test "CALL SITE: the quarantine is GATED on _sdp_staged_payload==true" {
  # The guard call must be inside `[[ "$_sdp_staged_payload" == true ]]` — not unconditional.
  # A bare call without this gate means the quarantine can still fire while the payload is
  # unstaged (when the pre-stage `git add` hit a transient index.lock and degraded).
  run grep -c '\[\[ "\$_sdp_staged_payload" == true \]\]' "$SCRIPT"
  [ "$status" -eq 0 ]
  [ "$output" -ge 1 ]
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 2 — structural: the guard is blind to staged content
# ═══════════════════════════════════════════════════════════════════════════════

@test "STRUCTURAL: staged payload is invisible to the guard's git diff --name-only" {
  # The guard's dirty-set computation uses `git diff --name-only` — UNSTAGED changes only. A
  # staged payload produces zero lines from that command. This is the property the ordering
  # fix relies on; if it ever stops being true, the fix is structurally broken regardless of
  # call-site correctness.
  echo "my edit" > mine.txt
  git add mine.txt
  run git diff --name-only
  # mine.txt is NOT in the unstaged diff — the stage made it invisible.
  [[ "$output" != *"mine.txt"* ]]
}

@test "STRUCTURAL: a pre-staged payload survives the guard EVEN WITH a broken (empty) protected-path argument" {
  # The protected-path argument is the belt. The ordering is the suspenders. Staging the
  # payload first (so `git diff --name-only` doesn't see it) must keep it safe even when the
  # protected-path argument is empty or wrong — because that's exactly what happened to
  # quickmerge the same day, and the ordering fix is what keeps a recurrence impossible.
  arm_extreme_backlog
  echo "my shipped edit" > mine.txt
  git add mine.txt  # <-- this is what the fix does before the guard runs
  # theirs.txt is dirty (unstaged) so the quarantine actually fires — if no file is dirty,
  # the guard's `git diff --name-only` returns empty and nothing is quarantined, which is
  # vacuously correct but not what this test is proving.
  echo "peer edit" > theirs.txt

  # Deliberately pass NO protected paths — the empty string, not the file name. If the guard
  # still quarantines mine.txt, the ordering property is vacuous.
  run autostash_guard_bound_backlog "" "upstream"
  [ "$status" -eq 0 ]

  # mine.txt must survive: it was STAGED, so `git diff --name-only` never saw it.
  grep -qx "my shipped edit" mine.txt
  # theirs.txt was unprotected AND unstaged — the guard legitimately quarantined it.
  grep -qx "base" theirs.txt
  git stash list | grep -q "pre-reconcile quarantine"
}

# ═══════════════════════════════════════════════════════════════════════════════
# LAYER 3 — end-to-end through safe-doc-push with extreme backlog
# ═══════════════════════════════════════════════════════════════════════════════

@test "END-TO-END: with extreme backlog, a genuine edit commits, pushes and lands correctly" {
  arm_extreme_backlog
  echo "my genuine change" > mine.txt

  run bash "$SCRIPT" "docs: genuine change" --files "mine.txt"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  run git show "HEAD:mine.txt"
  [[ "$output" == *"my genuine change"* ]]
  # The payload must have landed as a commit, not as a "nothing to commit" no-op.
  [[ "$output" != *"already matches HEAD"* ]]
}

@test "END-TO-END: with extreme backlog, a no-op-at-entry still correctly exits 12 (not false-success 0)" {
  # This is the existing exit-12 gate from test_safe_doc_push_landed_content_certification.
  # It must still fire correctly with the pre-stage in place — the `_SDP_ENTRY_HEAD_BLOBS`
  # fingerprint is captured at entry, before any staging, so the pre-stage must not defeat it.
  arm_extreme_backlog

  run bash "$SCRIPT" "docs: no-op edit" --files "mine.txt"

  [ "$status" -eq 12 ]
  [[ "$output" == *"NOTHING OF YOURS SHIPPED, AND THIS SCRIPT CANNOT TELL YOU WHY"* ]]
}

@test "END-TO-END: with extreme backlog and a peer editing a different file, the payload is untouched" {
  arm_extreme_backlog
  echo "my shipped edit" > mine.txt
  echo "peer edit" > theirs.txt

  run bash "$SCRIPT" "docs: my edit" --files "mine.txt"

  [ "$status" -eq 0 ]
  [[ "$output" == *"✅ Pushed"* ]]
  # mine.txt is the payload — must have landed.
  run git show "HEAD:mine.txt"
  [[ "$output" == *"my shipped edit"* ]]
  # theirs.txt was foreign WIP, not in --files, and should have been quarantined (not
  # committed).
  run git show "HEAD:theirs.txt"
  [[ "$output" == *"base"* ]]
}
