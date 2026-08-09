#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the prek/pre-commit serialization flock
# (prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md).
#
# `git commit` runs the prek/pre-commit hook chain synchronously, and prek's own
# stash-at-start/restore-at-end cycle is not concurrency-safe: two overlapping
# `git commit` calls in the SAME checkout can interleave those windows, and the
# first session's restore silently reverts a second session's newer edit to HEAD
# -- no error, no conflict marker, no stash entry to recover from (measured three
# times in one session on the same file, per the source issue doc). The fix wraps
# every `git commit` call in `scripts/dev/safe-doc-push.sh` (`locked_git_commit`)
# and `scripts/quickmerge.sh` (`_qm_locked_git_commit`) in a flock scoped to the
# checkout's own .git dir -- same FD-open/flock/unlock/FD-close shape and
# degrade-to-unlocked-if-flock-unavailable convention as the existing cascade lock
# (see test-quickmerge-cascade-lock.sh, a different critical section).
#
# Like test-quickmerge-cascade-lock.sh, this EXTRACTS the REAL functions from both
# scripts (not a replica) and runs them against a synthesized git fixture with a
# deliberately slow pre-commit hook (simulating prek's stash/restore window) --
# two concurrent invocations racing on the SAME checkout, asserting the second's
# hook never starts until the first's hook has fully finished (no interleaving),
# plus a same-process repeated-call check for the "does it deadlock on its own
# retries" requirement the source todo calls out explicitly (quickmerge's own
# commit-retry loop can call `git commit` up to 15 times in one run).
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-quickmerge-commit-lock.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
QM="$REPO_ROOT/quickmerge.sh"
SDP="$REPO_ROOT/dev/safe-doc-push.sh"
[ -f "$QM" ] || { echo "FATAL: quickmerge.sh not found at $QM"; exit 2; }
[ -f "$SDP" ] || { echo "FATAL: safe-doc-push.sh not found at $SDP"; exit 2; }

# ── Extract the REAL functions (not a replica) ───────────────────────────────────
QM_FN=$(sed -n '/^_qm_locked_git_commit() {/,/^}$/p' "$QM")
SDP_FN=$(sed -n '/^locked_git_commit() {/,/^}$/p' "$SDP")
[ -n "$QM_FN" ] || { echo "FATAL: could not extract _qm_locked_git_commit from quickmerge.sh"; exit 2; }
[ -n "$SDP_FN" ] || { echo "FATAL: could not extract locked_git_commit from safe-doc-push.sh"; exit 2; }

# Structural anchor: both extracted functions must carry the lock acquire/release +
# the degrade-gracefully branch -- so a future edit that removes/renames the guard
# fails here, not silently.
for pair in "quickmerge.sh:$QM_FN" "safe-doc-push.sh:$SDP_FN"; do
  name="${pair%%:*}"; fn="${pair#*:}"
  case "$fn" in
    *'flock "$lock_fd"'*'git commit "$@"'*'flock -u "$lock_fd"'*'flock(1) unavailable'*|*'flock "$lock_fd"'*'git commit "$@"'*'flock -u "$lock_fd"'*)
      pass "$name: extracted function carries lock acquire + commit + release" ;;
    *)
      fail "$name: extracted function missing a contract element"; echo "--- fn ---"; echo "$fn" ;;
  esac
done

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

# ── Fixture: one checkout, a slow pre-commit hook (simulates prek's stash/restore
#    window), two concurrent invocations of the REAL extracted function ──────────
setup_fixture() {
  local repo="$WORK/repo"
  $GIT init -q "$repo"
  (
    cd "$repo" || exit 9
    printf 'base\n' > f.txt
    $GIT add f.txt
    $GIT commit -qm base
    mkdir -p .git/hooks
    cat > .git/hooks/pre-commit <<'HOOKEOF'
#!/bin/sh
echo "start $$ $(date +%s.%N)" >> "$HOOK_LOG"
sleep 0.6
echo "end   $$ $(date +%s.%N)" >> "$HOOK_LOG"
exit 0
HOOKEOF
    chmod +x .git/hooks/pre-commit
  )
  echo "$repo"
}

run_commit() {
  local repo="$1" file="$2" msg="$3" fn_body="$4" log="$5"
  (
    cd "$repo" || exit 9
    export HOOK_LOG="$log"
    eval "$fn_body"
    printf 'x\n' >> "$file"
    git add "$file"
    if [ "$fn_body" = "$QM_FN" ]; then
      _qm_locked_git_commit -q -m "$msg"
    else
      locked_git_commit -q -m "$msg"
    fi
  ) 2>&1
}

echo "── Fixture: two concurrent commits (real quickmerge.sh fn vs real safe-doc-push.sh fn) on one checkout ──"
repo=$(setup_fixture)
hooklog="$WORK/hook.log"
: > "$hooklog"

run_commit "$repo" "a.txt" "commit from quickmerge-side" "$QM_FN" "$hooklog" > "$WORK/outA.log" 2>&1 &
pidA=$!
sleep 0.15   # let A acquire the lock and enter the hook's sleep first, deterministically
run_commit "$repo" "b.txt" "commit from safe-doc-push-side" "$SDP_FN" "$hooklog" > "$WORK/outB.log" 2>&1 &
pidB=$!
wait "$pidA"; wait "$pidB"

if grep -q "flock(1) unavailable" "$WORK/outA.log" "$WORK/outB.log" 2>/dev/null; then
  echo "SKIP: flock(1) unavailable on this host -- lock-serialization assertion not meaningful here"
else
  # No-interleaving assertion: read the hook log's start/end pairs in emitted
  # order and confirm each "start" is immediately followed by its OWN "end"
  # (never a second "start" before the first "end") -- i.e. the two hook
  # invocations (one from EACH real script's own commit path) never overlapped.
  interleaved=0
  awk '
    /^start/ { if (open) { bad=1 }; open=1 }
    /^end/   { open=0 }
    END { exit bad ? 1 : 0 }
  ' "$hooklog" || interleaved=1
  if [ "$interleaved" -eq 1 ]; then
    fail "pre-commit hook invocations interleaved -- the exact race this lock exists to close"
    cat "$hooklog"
  else
    pass "cross-script commits serialized -- quickmerge.sh's and safe-doc-push.sh's hook invocations never overlapped"
  fi
fi

echo
echo "── Same-process repeat-call check (source todo's explicit deadlock concern: quickmerge's own"
echo "   commit-retry loop can call git commit up to 15x in one run) ──"
(
  cd "$repo" || exit 9
  export HOOK_LOG="$WORK/hook2.log"
  eval "$QM_FN"
  ok=1
  for i in 1 2 3; do
    printf 'y\n' >> "c.txt"
    git add c.txt
    if ! _qm_locked_git_commit -q -m "repeat $i"; then
      ok=0
    fi
  done
  exit $((1 - ok))
) &
repeat_pid=$!
if wait "$repeat_pid"; then
  pass "same-process repeated locked-commit calls completed without a self-deadlock (3x, no timeout)"
else
  fail "same-process repeated locked-commit calls failed"
fi

echo
echo "── todo 3 (\"make the loss loud\"): checksum-based silent-revert detection in safe-doc-push.sh ──"
RACE_SNAPSHOT_FN=$(sed -n '/^_prek_race_snapshot() {/,/^}$/p' "$SDP")
RACE_CHECK_FN=$(sed -n '/^_prek_race_check() {/,/^}$/p' "$SDP")
if [ -z "$RACE_SNAPSHOT_FN" ] || [ -z "$RACE_CHECK_FN" ]; then
  fail "could not extract _prek_race_snapshot / _prek_race_check from safe-doc-push.sh"
else
  race_work="$WORK/race"
  $GIT init -q "$race_work"
  (
    cd "$race_work" || exit 9
    printf 'line1\n' > f.txt
    $GIT add f.txt
    $GIT commit -qm base
    eval "$RACE_SNAPSHOT_FN"
    eval "$RACE_CHECK_FN"

    # Positive case: f.txt has real unstaged WIP, then gets silently reverted to a
    # STALE snapshot underneath us (the exact signature this todo detects) -- must
    # be flagged.
    printf 'line1-edited-by-session-A\n' > f.txt
    before="$(_prek_race_snapshot)"
    printf 'line1-STALE-race\n' > f.txt
    if changed="$(_prek_race_check "$before")"; then
      echo "FAIL: race case -- _prek_race_check reported no change (expected f.txt flagged)"
      exit 1
    else
      case "$changed" in
        f.txt) exit 0 ;;
        *) echo "FAIL: race case -- unexpected changed-file output: $changed"; exit 1 ;;
      esac
    fi
  )
  if [ "$?" -eq 0 ]; then
    pass "_prek_race_check flags a file silently reverted to a stale snapshot"
  else
    fail "_prek_race_check did not correctly flag the silent-revert case"
  fi

  (
    cd "$race_work" || exit 9
    eval "$RACE_SNAPSHOT_FN"
    eval "$RACE_CHECK_FN"
    # Negative case: same unstaged content before and after -- must NOT be flagged
    # (a hook-quiet commit / no interleaving race must never false-positive).
    printf 'line1-edited-by-session-A\n' > f.txt
    before="$(_prek_race_snapshot)"
    if _prek_race_check "$before" >/dev/null; then
      exit 0
    else
      exit 1
    fi
  )
  if [ "$?" -eq 0 ]; then
    pass "_prek_race_check reports no change when the unstaged file is untouched (no false positive)"
  else
    fail "_prek_race_check false-positived on an untouched unstaged file"
  fi
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
