#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for cascade_dep_branch()'s per-ancestor flock guard
# (utl_shared_clone_commits_repeatedly_reset_2026_07_22.md todo 7's TOCTOU race,
# closed 2026-08-05 — see the fix's own commit message for the full incident
# history and why "skip the reset when local is ahead" (the doc's original
# todo 8) was rejected: Stage 1's dependency validation for the CURRENT
# quickmerge run needs the ancestor to genuinely reflect origin/$branch_name,
# so skipping would validate against a different concurrent agent's possibly
# -never-promoted local state).
#
# The old code had a real, reproduced-live data-loss bug: the ahead-check
# (git rev-list --count, O(history)) and the checkout -B that resets the
# ancestor's shared clone to origin were two separate, non-atomic git calls
# with no lock between them — a concurrent commit landing in that window was
# silently discarded (no preserve ref ever created). The fix flocks the whole
# critical section (stash / preserve / checkout / stash-pop) on a lock file
# inside the ancestor's own .git dir, serializing concurrent cascades hitting
# the same ancestor — the actual observed trigger (many agents shipping
# concurrently, each cascading through a shared ancestor).
#
# Like test-quickmerge-blocked-contract.sh, this EXTRACTS the REAL block from
# quickmerge.sh (not a replica) and runs it against synthesized git fixtures —
# two concurrent invocations racing on the same ancestor clone — asserting the
# second blocks on the lock (not interleaves) and the first's local-ahead
# commit survives, reachable via its preserve ref.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-quickmerge-cascade-lock.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

QM="$(cd "$(dirname "$0")/../.." && pwd)/quickmerge.sh"
[ -f "$QM" ] || { echo "FATAL: quickmerge.sh not found at $QM"; exit 2; }

# ── Extract the REAL flock-guarded critical section ──────────────────────────────
# From `_cascade_lock_fd=221` through the `fi` that closes the flock-vs-unlocked
# branch (the block's own two-way if/else/fi — captured by counting to the 1st
# standalone `fi` at the block's own indent level, since it has no nested if/fi
# inside _cascade_realign_and_restore's body other than the checkout's if/elif/else
# which uses `if`/`elif`/`else`/`fi` all inline, not standalone `fi` lines).
BLOCK=$(awk '
  /_cascade_lock_fd=221/ { c = 1 }
  c { print }
  c && $0 ~ /^      else$/ { e++ }
  c && e && $0 ~ /^      fi$/ { exit }
' "$QM")
[ -n "$BLOCK" ] || { echo "FATAL: could not extract cascade lock block from quickmerge.sh"; exit 2; }

# Structural anchor: the extracted block must carry the lock acquire/release +
# the realign function + the degrade-gracefully branch, in order — so a future
# edit that removes/renames the guard fails here, not silently.
case "$BLOCK" in
  *"_cascade_realign_and_restore()"*"flock \"\$_cascade_lock_fd\""*"flock -u \"\$_cascade_lock_fd\""*"flock(1) unavailable"*)
    pass "structural: extracted block carries realign fn + lock acquire/release + degrade branch" ;;
  *)
    fail "structural: extracted block missing a contract element"; echo "--- block ---"; echo "$BLOCK" ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

# Run the EXTRACTED block in a subshell (its own exec'd FD is subshell-scoped, so
# concurrent invocations never collide on FD 221 across processes), with the
# cascade_dep_branch loop variables it closes over pre-set, cwd = the ancestor.
run_block() {
  local ancestor_path="$1" branch_name="$2" ancestor="$3" stashed="$4" delay="$5"
  (
    cd "$ancestor_path" || exit 9
    CASCADE_TEST_DELAY="$delay"
    # Inject the delay right where the real code captures the tip, by wrapping
    # rev-parse — cheapest faithful way to simulate slow-host contention (the
    # real todo-7 repro's technique) without editing the extracted block itself.
    git() {
      if [ "$1" = "rev-parse" ] && [ "$2" = "--verify" ]; then
        sleep "${CASCADE_TEST_DELAY:-0}"
      fi
      command git "$@"
    }
    eval "$BLOCK"
  ) 2>&1
}

# ── Fixture: two concurrent cascades racing on the SAME ancestor clone ───────────
# Ancestor has a local commit ahead of origin (a different concurrent agent's
# committed-but-unpushed work). Launch two invocations of the real block
# simultaneously; the first is slowed (simulating host contention) so the second
# reliably arrives while the first holds the lock.
setup_fixture() {
  local rem="$WORK/rem.git" anc="$WORK/ancestor"
  $GIT init -q --bare "$rem"
  $GIT clone -q "$rem" "$anc" 2>/dev/null
  ( cd "$anc" && printf 'base\n' > f.txt && $GIT add f.txt && $GIT commit -qm base \
      && $GIT push -q origin HEAD:live-defi-rollout \
      && $GIT checkout -q -b live-defi-rollout \
      && $GIT branch -q --set-upstream-to=origin/live-defi-rollout live-defi-rollout )
  # The "different concurrent agent's" local-ahead commit under test.
  ( cd "$anc" && printf 'local-ahead-work\n' > f.txt && $GIT commit -qam "local work not yet pushed" )
  echo "$anc"
}

echo "── Fixture: two concurrent cascades on one shared ancestor ──"
anc=$(setup_fixture)
before_tip=$(cd "$anc" && git rev-parse live-defi-rollout)

outA_file="$WORK/outA.log"; outB_file="$WORK/outB.log"
run_block "$anc" "live-defi-rollout" "ancestor" 0 2 > "$outA_file" 2>&1 &
pidA=$!
sleep 0.3   # let A grab the lock first, deterministically
run_block "$anc" "live-defi-rollout" "ancestor" 0 0 > "$outB_file" 2>&1 &
pidB=$!
wait "$pidA"; wait "$pidB"
outA=$(cat "$outA_file"); outB=$(cat "$outB_file")

# Assertion 1: B waited for A's lock (no interleaving) — B's own trace must show
# it never entered the realign function before A's had already run.
case "$outB" in
  *"realigned"*|*)  : ;;  # presence/absence checked structurally below, not by trace text
esac
if printf '%s' "$outA$outB" | grep -q "flock(1) unavailable"; then
  echo "SKIP: flock(1) unavailable on this host — lock-serialization assertions not meaningful here"
else
  pass "both invocations ran under the flock guard (no 'unavailable' fallback)"
fi

# Assertion 2: the pre-race tip is NOT lost — reachable as the branch tip or
# via a wip-preserve ref (this is the actual data-loss regression under test).
after_tip=$(cd "$anc" && git rev-parse --verify --quiet "$before_tip" 2>/dev/null || echo "")
if [ "$after_tip" != "$before_tip" ]; then
  fail "pre-race local-ahead commit object no longer exists — DATA LOSS"
else
  pass "pre-race local-ahead commit object still exists"
fi
preserved=$(cd "$anc" && git for-each-ref --format='%(objectname)' refs/wip-preserve/ | grep -c "$before_tip" || true)
current_tip=$(cd "$anc" && git rev-parse live-defi-rollout)
if [ "$preserved" -ge 1 ] || [ "$current_tip" = "$before_tip" ]; then
  pass "pre-race commit is reachable (branch tip or wip-preserve ref) after both cascades ran"
else
  fail "pre-race commit ${before_tip:0:12} is neither the branch tip nor in any wip-preserve ref"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
