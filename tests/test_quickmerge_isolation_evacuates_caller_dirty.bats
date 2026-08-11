#!/usr/bin/env bats
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
#
# test_quickmerge_isolation_evacuates_caller_dirty.bats -- quickmerge's --isolated must protect
# its INPUTS, not just the throwaway worktree it computes in
# (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo 1).
#
# THE ORIGINALLY-FILED HYPOTHESIS (unverified when the todo was written): STAGE 0.4's reconcile
# runs against the CALLER's checkout BEFORE isolation copies files in. Read the code instead of
# assuming: the isolated worktree is created `--detach`, and STAGE 5's _qm_checkout_ship_branch
# forces it to STAY detached for the whole run (QM_IN_ISOLATION short-circuits before the
# checkout). `git branch --show-current` is therefore empty at every
# `_qm_stage_0_4_not_behind_gate` call site inside the isolated child, so the reconcile --
# including `autostash_guard_bound_backlog`, the function that actually reverts foreign dirt --
# never runs there at all. The PARENT re-execs and exits before reaching STAGE 0.4 either. So
# the hypothesis is FALSE: isolation's own reconcile cannot be what moved the caller's tree.
#
# THE REAL GAP: isolation copies --files into the worktree but never touches the CALLER's own
# copy of those same paths -- they stay dirty on disk in the shared checkout for the run's
# entire duration, which is exactly the condition a CONCURRENT PEER's own
# autostash_guard_bound_backlog quarantine sweep (see
# test_autostash_guard_protects_caller_files.bats) acts on. The fix: evacuate the caller's
# dirty --files into a named stash for the duration, restore unconditionally on return.
#
# Hermetic: a real local git repo under BATS_TEST_TMPDIR (bats auto-cleans it), no network.
#
# Run: bats tests/test_quickmerge_isolation_evacuates_caller_dirty.bats

setup() {
  # Same rationale as the sibling autostash test: don't take the host-wide push-governor lock.
  export PUSH_GOV_DISABLE=true
  REPO_ROOT="$(cd "$(dirname "$BATS_TEST_FILENAME")/.." && pwd)"
  QM_SH="${REPO_ROOT}/scripts/quickmerge.sh"
  GUARD_SH="${REPO_ROOT}/scripts/dev/tree-wip-guard.sh"

  REPO="${BATS_TEST_TMPDIR}/repo"
  mkdir -p "$REPO"
  cd "$REPO" || return 1
  git init -q .
  git config user.email t@t.t && git config user.name t
  echo mine > mine.txt
  echo noise > noise.txt
  git add -A && git commit -qm init
  git branch upstream

  # Extract the THREE functions verbatim from quickmerge.sh -- not sourcing the whole script
  # (it has `set -e`, argument parsing, and real side effects on load).
  eval "$(sed -n '/^_qm_iso_evac_find() {/,/^}/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_iso_evacuate_caller_dirty() {/,/^}/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_iso_restore_caller_dirty() {/,/^}/p' "$QM_SH")"
  # The real quarantine sweep, to prove immunity against the ACTUAL hazard mechanism, not a
  # stand-in for it.
  eval "$(sed -n '/^autostash_guard_bound_backlog() {/,/^}/p' "$GUARD_SH")"
}

arm_extreme_backlog() {
  for i in $(seq 1 11); do
    echo "noise $i" > noise.txt
    git stash push -q -m "autostash" -- noise.txt
  done
  [ "$(git stash list | grep -ci autostash)" -ge 10 ]
}

@test "a dirty file is evacuated: stashed out, working tree reverts to HEAD" {
  echo "my in-flight edit" > mine.txt
  run _qm_iso_evacuate_caller_dirty "marker-1" "mine.txt"
  [ "$status" -eq 0 ]
  [ "$output" = "marker-1" ]
  # Working tree is clean again -- the evacuation is what makes it invisible to a dirty sweep.
  git diff --quiet -- mine.txt
  grep -qx "mine" mine.txt
  git stash list | grep -q "marker-1"
}

@test "nothing dirty means nothing evacuated -- not an error, no stash created" {
  run _qm_iso_evacuate_caller_dirty "marker-2" "mine.txt"
  [ "$status" -eq 0 ]
  [ -z "$output" ]
  ! git stash list | grep -q "marker-2"
}

@test "restore brings the exact evacuated content back" {
  echo "my in-flight edit" > mine.txt
  _qm_iso_evacuate_caller_dirty "marker-3" "mine.txt" >/dev/null
  grep -qx "mine" mine.txt   # confirms evacuation actually happened before we test restore

  run _qm_iso_restore_caller_dirty "marker-3"
  [ "$status" -eq 0 ]
  grep -qx "my in-flight edit" mine.txt
  ! git stash list | grep -q "marker-3"   # popped, not left behind
}

@test "restore is marker-based, not index-based -- survives OTHER stash activity in between" {
  echo "my in-flight edit" > mine.txt
  _qm_iso_evacuate_caller_dirty "marker-4" "mine.txt" >/dev/null

  # Simulate the isolated CHILD's own stash operations (STAGE 5's pre-branch-switch stash,
  # the commit-retry loop) landing on the SAME shared refs/stash while our evacuation sits in
  # the list -- this is what makes a stash@{N} index captured at evacuation time stale by the
  # time we come back to restore it.
  echo x > noise.txt && git stash push -q -m "unrelated-child-stash-1" -- noise.txt
  echo y > noise.txt && git stash push -q -m "unrelated-child-stash-2" -- noise.txt

  run _qm_iso_restore_caller_dirty "marker-4"
  [ "$status" -eq 0 ]
  grep -qx "my in-flight edit" mine.txt
  # The unrelated entries are untouched -- we popped ONLY ours.
  git stash list | grep -q "unrelated-child-stash-1"
  git stash list | grep -q "unrelated-child-stash-2"
}

@test "THE ACTUAL HAZARD: an evacuated file is immune to a peer's real extreme-backlog quarantine sweep" {
  arm_extreme_backlog
  echo "my in-flight edit" > mine.txt
  _qm_iso_evacuate_caller_dirty "marker-5" "mine.txt" >/dev/null
  grep -qx "mine" mine.txt   # clean now -- this IS the protection

  # A peer's OWN quickmerge run in this shared checkout, shipping something else entirely
  # (mine.txt is not in ITS --files) -- exactly the scenario measured live on 2026-08-11.
  run autostash_guard_bound_backlog "peer-own-file.txt" "upstream"
  [ "$status" -eq 0 ]

  # Evacuated file was invisible to the sweep (it wasn't dirty) -- still at HEAD content here,
  # our edit safe in its own stash, not reverted-and-lost.
  grep -qx "mine" mine.txt
  run _qm_iso_restore_caller_dirty "marker-5"
  [ "$status" -eq 0 ]
  grep -qx "my in-flight edit" mine.txt
}

@test "COUNTERFACTUAL: without evacuation, the same peer sweep reverts the in-flight edit" {
  arm_extreme_backlog
  echo "my in-flight edit" > mine.txt   # dirty, NOT evacuated -- the pre-fix shape

  run autostash_guard_bound_backlog "peer-own-file.txt" "upstream"
  [ "$status" -eq 0 ]

  # Reverted to HEAD -- this is the loss the fix exists to prevent, demonstrated without it.
  grep -qx "mine" mine.txt
}

@test "CONCURRENCY: evacuation retries past a transient .git/index.lock instead of failing outright" {
  # Answers the coordinator's question empirically rather than by reasoning alone: a real stress
  # test (15 concurrent same-checkout pairs, different files each side, outside this bats run --
  # see the session report) measured 15/30 (50%) of the losing side's FIRST `git stash push`
  # attempt failing on index.lock contention with the other side's simultaneous push. This proves
  # the retry actually closes that specific failure, deterministically: hold the real lock file
  # git itself uses, release it partway through the retry budget, and confirm evacuation still
  # succeeds instead of giving up on attempt 1.
  echo "my in-flight edit" > mine.txt
  touch .git/index.lock
  ( sleep 0.1; rm -f .git/index.lock ) &
  run _qm_iso_evacuate_caller_dirty "marker-lock" "mine.txt"
  [ "$status" -eq 0 ]
  [ "$output" = "marker-lock" ]
  git diff --quiet -- mine.txt
  grep -qx "mine" mine.txt
}

@test "restore of a missing marker returns rc=2 (idempotent no-op), not rc=1 (real failure)" {
  # (2026-08-11, coordinator review) rc must distinguish "nothing to do" (already restored, or
  # never evacuated) from "found it but the pop genuinely conflicted" -- callers, including the
  # EXIT/INT/TERM trap that ALWAYS fires even after a clean restore, must treat rc=2 as silent.
  run _qm_iso_restore_caller_dirty "marker-never-created"
  [ "$status" -eq 2 ]
}

@test "restore is idempotent: a second call with the SAME marker after a successful pop is rc=2, not rc=1" {
  echo "my in-flight edit" > mine.txt
  _qm_iso_evacuate_caller_dirty "marker-idem" "mine.txt" >/dev/null

  run _qm_iso_restore_caller_dirty "marker-idem"
  [ "$status" -eq 0 ]

  # This is exactly what the EXIT trap does after the normal path already restored -- must be
  # silent-safe (rc=2), never treated as a failure.
  run _qm_iso_restore_caller_dirty "marker-idem"
  [ "$status" -eq 2 ]
  grep -qx "my in-flight edit" mine.txt   # unchanged by the second, no-op call
}

@test "rc=1 (genuine conflict) is reserved for when the stash IS found but the pop fails" {
  echo "my in-flight edit, line one" > mine.txt
  _qm_iso_evacuate_caller_dirty "marker-conflict" "mine.txt" >/dev/null
  grep -qx "mine" mine.txt   # evacuated -- back at HEAD content

  # A NEW commit changes the SAME line on HEAD while the evacuation is outstanding (a peer
  # landing a change to the same file mid-run) -- the exact scenario the loud path exists for.
  echo "a peer's conflicting edit, line one" > mine.txt
  git add mine.txt && git commit -qm "peer edit lands while ours is evacuated"

  run _qm_iso_restore_caller_dirty "marker-conflict"
  [ "$status" -eq 1 ]
  # Never silently dropped -- the entry survives a failed pop for manual recovery.
  git stash list | grep -q "marker-conflict"
}

@test "CALL SITE: the isolation block evacuates before cd'ing into the worktree and restores after the child returns" {
  run grep -n '_qm_iso_evacuate_caller_dirty "\$_QM_ISO_EVAC_MARKER" "\$FILES_ARG"' "$QM_SH"
  [ "$status" -eq 0 ]
  run grep -n '_qm_iso_restore_caller_dirty "\$_QM_ISO_EVAC_MARKER"' "$QM_SH"
  [ "$status" -eq 0 ]
}

@test "CALL SITE: the normal restore path treats rc=2 as silent, not as the scary message" {
  run grep -n '2) : ;; # already restored / nothing to do' "$QM_SH"
  [ "$status" -eq 0 ]
}

@test "CALL SITE: cleanup is registered for EXIT, INT and TERM, not EXIT alone" {
  run grep -n "trap '_qm_iso_signal_cleanup EXIT' EXIT" "$QM_SH"
  [ "$status" -eq 0 ]
  run grep -n "trap '_qm_iso_signal_cleanup INT; exit 130' INT" "$QM_SH"
  [ "$status" -eq 0 ]
  run grep -n "trap '_qm_iso_signal_cleanup TERM; exit 143' TERM" "$QM_SH"
  [ "$status" -eq 0 ]
}

# ── the actual bite: killed mid-flight ────────────────────────────────────────────────────
#
# Everything above proves the FUNCTIONS are correct in isolation. This proves the WIRING: a
# real bash process that evacuates, registers the SAME trap quickmerge.sh registers, and is
# then killed with SIGTERM while its "isolated child" (a stand-in sleep) is still running --
# exactly the harness-TaskStop shape the coordinator hit live on this host. Before this fix,
# the only restore call site was reachable AFTER `bash "$_QM_SELF" ...` returns normally; a
# process killed before that point left the caller's --files stashed with a clean `git status`.

@test "KILLED MID-FLIGHT: SIGTERM during the isolated run still restores the caller's dirty --files" {
  eval "$(sed -n '/^_qm_cleanup_isolation() {/,/^}/p' "$QM_SH")"
  eval "$(sed -n '/^_qm_iso_signal_cleanup() {/,/^}/p' "$QM_SH")"

  echo "my in-flight edit" > mine.txt

  cat > harness.sh <<HARNESS
#!/usr/bin/env bash
set -u
cd "$REPO" || exit 2
$(sed -n '/^_qm_iso_evac_find() {/,/^}/p' "$QM_SH")
$(sed -n '/^_qm_iso_evacuate_caller_dirty() {/,/^}/p' "$QM_SH")
$(sed -n '/^_qm_iso_restore_caller_dirty() {/,/^}/p' "$QM_SH")
$(sed -n '/^_qm_cleanup_isolation() {/,/^}/p' "$QM_SH")
$(sed -n '/^_qm_iso_signal_cleanup() {/,/^}/p' "$QM_SH")
_QM_ISO_ROOT=""
_QM_ISO_EVAC_MARKER="qm-iso-evac-harness-\$\$"
trap '_qm_iso_signal_cleanup EXIT' EXIT
trap '_qm_iso_signal_cleanup INT; exit 130' INT
trap '_qm_iso_signal_cleanup TERM; exit 143' TERM
_qm_iso_evacuate_caller_dirty "\$_QM_ISO_EVAC_MARKER" "mine.txt" >/dev/null
echo "EVACUATED" > "$REPO/harness.evacuated"
# Stand-in for "the isolated child (a full quality-gates.sh re-gate) is running" -- long
# enough for the test to reliably deliver SIGTERM before this returns on its own.
sleep 10
HARNESS
  chmod +x harness.sh

  ./harness.sh &
  harness_pid=$!

  # Wait for evacuation to actually complete before killing -- otherwise the test would be
  # racing the harness's own setup, not exercising "killed mid-flight".
  for _ in $(seq 1 50); do
    [ -f harness.evacuated ] && break
    sleep 0.1
  done
  [ -f harness.evacuated ]
  # This is the protection actually working, mid-flight: the file reads clean at HEAD content
  # right now, BEFORE we kill anything -- proving it was genuinely evacuated, not left dirty.
  grep -qx "mine" mine.txt

  kill -TERM "$harness_pid"
  # bats runs test bodies under errexit-like trapping -- a bare `wait` that returns the
  # background job's nonzero exit status would abort the test right here instead of letting us
  # assert on it. The `&& ... || ...` form (same idiom quickmerge.sh itself uses for this)
  # keeps the compound statement's own status 0 while still capturing the real one.
  wait "$harness_pid" 2>/dev/null && harness_status=0 || harness_status=$?

  # 143 = 128+SIGTERM, the explicit re-raise the TERM trap performs after cleanup.
  [ "$harness_status" -eq 143 ]
  # The actual claim: the caller's in-flight edit is back, not stuck in a stash nobody restored.
  grep -qx "my in-flight edit" mine.txt
  ! git stash list | grep -q "qm-iso-evac-harness-"
}
