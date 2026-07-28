#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the pkill() mechanical guard (scripts/hooks/pkill-guard-lib.sh),
# built after plans/active/issues/pkill_broad_pattern_cross_slot_qg_kill_2026_07_28.md's
# "Recurrence #2" P1 todo (prose-only guidance failed to prevent the identical cross-slot
# kill twice in one day — enforcement must be mechanical). Proves:
#   1. a bare, unscoped pkill pattern is REFUSED and the victim process survives
#   2. a pattern scoped to the CALLER's own `.tabs/<N>/` worktree is ALLOWED and kills
#   3. a pattern scoped to a DIFFERENT slot's `.tabs/<M>/` worktree is still REFUSED
#      (one slot can't "safely" pattern-kill another slot's worktree either)
#   4. an exact -g PGID discriminator is ALLOWED and kills, with no worktree path needed
#   5. a bare `pkill` (no args) passes straight through untouched (real binary's own
#      usage error, not the guard's refusal)
#
# Markers are a PER-RUN-UNIQUE token ($$-based), never a real script name like
# "quality-gates.sh" — this host runs many real, live quality-gates.sh processes from
# OTHER slots concurrently, and an actual (unrelated) unscoped pkill from one of them
# would otherwise race-kill a same-named decoy here, producing a flaky false failure
# that has nothing to do with THIS guard (confirmed empirically: an earlier draft of this
# test used "quality-gates.sh" as the marker and got its decoys killed by real host
# activity mid-run).
#
# Run: bash unified-trading-pm/scripts/hooks/tests/test-pkill-guard.sh
set -uo pipefail

LIB="$(cd "$(dirname "$0")/.." && pwd)/pkill-guard-lib.sh"
# shellcheck source=/dev/null
source "$LIB"

LTMP="$(mktemp -d)"
trap 'rm -rf "$LTMP"' EXIT
FAILS=0
TOKEN="pkill-guard-selftest-$$-${RANDOM}" # unique to this run — never a real script name

spawn_marked() { # $1 = marker string (becomes argv0 → visible to `pkill -f`); echoes the PID
  (exec -a "$1" sleep 60) &
  echo $!
}

reap() { kill -9 "$1" 2>/dev/null; wait "$1" 2>/dev/null; true; }

assert_rc() { # <label> <expected> <actual>
  if [ "$2" -eq "$3" ]; then
    echo "PASS: $1 (rc=$3)"
  else
    echo "FAIL: $1 — expected rc=$2 got rc=$3"
    FAILS=$((FAILS + 1))
  fi
}

assert_alive() { # <pid> <label>
  if kill -0 "$1" 2>/dev/null; then
    echo "PASS: $2 (pid $1 still alive)"
  else
    echo "FAIL: $2 — pid $1 unexpectedly dead"
    FAILS=$((FAILS + 1))
  fi
}

assert_dead() { # <pid> <label> — waits for the (child-of-this-shell) pid to actually be
  # reaped before checking, so a not-yet-reaped zombie can't read as a false "still alive".
  wait "$1" 2>/dev/null
  if kill -0 "$1" 2>/dev/null; then
    echo "FAIL: $2 — pid $1 unexpectedly still alive"
    FAILS=$((FAILS + 1))
  else
    echo "PASS: $2 (pid $1 dead)"
  fi
}

# --- 1: bare unscoped pattern -> REFUSED, victim survives ---
victim1=$(spawn_marked "$LTMP/${TOKEN}-1-bare")
sleep 0.2
pkill -f "${TOKEN}-1-bare" >/dev/null 2>&1
rc=$?
assert_rc "1a. bare unscoped pattern refused" 1 "$rc"
assert_alive "$victim1" "1b. victim survives the refused bare pkill"
reap "$victim1"

# --- 2: own-slot cwd-scoped pattern -> ALLOWED, kills ---
mkdir -p "$LTMP/.tabs/5/mtds"
target2=$(spawn_marked "$LTMP/.tabs/5/mtds/${TOKEN}-2-own-slot")
sleep 0.2
(cd "$LTMP/.tabs/5/mtds" && pkill -f "$LTMP/.tabs/5/mtds/${TOKEN}-2-own-slot") >/dev/null 2>&1
rc=$?
assert_rc "2a. own-slot cwd-scoped pattern allowed" 0 "$rc"
assert_dead "$target2" "2b. target killed by scoped pkill"

# --- 3: pattern scoped to a DIFFERENT slot than caller's cwd -> still REFUSED ---
mkdir -p "$LTMP/.tabs/2/mtds"
victim3=$(spawn_marked "$LTMP/.tabs/2/mtds/${TOKEN}-3-other-slot")
sleep 0.2
(cd "$LTMP/.tabs/5/mtds" && pkill -f "$LTMP/.tabs/2/mtds/${TOKEN}-3-other-slot") >/dev/null 2>&1
rc=$?
assert_rc "3a. cross-slot-scoped pattern (caller=5, target=2) refused" 1 "$rc"
assert_alive "$victim3" "3b. other-slot victim survives"
reap "$victim3"

# --- 4: exact -g PGID discriminator -> ALLOWED, kills, no worktree path needed ---
victim4=$(spawn_marked "$LTMP/${TOKEN}-4-pgid")
sleep 0.2
pgid4=$(ps -o pgid= -p "$victim4" | tr -d ' ')
pkill -g "$pgid4" >/dev/null 2>&1
rc=$?
assert_rc "4a. numeric -g PGID discriminator allowed" 0 "$rc"
assert_dead "$victim4" "4b. target killed by -g scoped pkill"

# --- 5: bare pkill (no args) passes straight through, not the guard's refusal path ---
if pkill 2>&1 | grep -q "REFUSED: pkill pattern"; then
  echo "FAIL: 5. no-args pkill incorrectly hit the guard refusal path"
  FAILS=$((FAILS + 1))
else
  echo "PASS: 5. no-args pkill passed through to the real binary untouched"
fi

echo "────────────────────────────────────────"
if [ "$FAILS" -eq 0 ]; then echo "ALL PASSED"; else echo "FAILURES: $FAILS"; fi
[ "$FAILS" -eq 0 ]
