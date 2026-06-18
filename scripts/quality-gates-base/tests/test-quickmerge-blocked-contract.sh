#!/usr/bin/env bash
# Regression test for the quickmerge STAGE 0.4 QUICKMERGE_BLOCKED structured error
# contract (qg_commit_quality_boundary_and_slot_ff_push_2026_06_03.md items 265/283).
#
# Contract (shipped 2026-06-17): when STAGE 0.4's not-behind gate finds the slot
# behind its remote AND the auto-rebase hits a conflict, quickmerge emits a
# machine-parseable block so an agent self-serves recovery without an operator paste:
#
#   QUICKMERGE_BLOCKED code=<BEHIND_DIVERGED_CONFLICT|AUTOSTASH_POP_CONFLICT> \
#     repo=… branch=… behind=… ahead=… conflicts="…"
#   RECOVERY: SUB_AGENT_MANDATORY_RULES.md § "Quickmerge behind-remote" — …
#
# The two codes are discriminated by `git rebase --abort` rc: 0 = a rebase was
# mid-flight (plain diverged-conflict; autostash pending) → BEHIND_DIVERGED_CONFLICT;
# !=0 = no rebase in progress (the autostash POP conflicted; local work in `git
# stash list`) → AUTOSTASH_POP_CONFLICT.
#
# Like test-ratchet-exit-code-aggregation.sh, this EXTRACTS the REAL block from
# quickmerge.sh (not a replica) and runs it against two synthesized git fixtures,
# asserting each emits its code — plus a structural anchor so the contract can't be
# silently removed/renamed. The two `git pull` attempts that TRIGGER the block are
# git-standard (mirroring quickmerge.sh lines 550 + 552); the block under test is the
# extracted real code.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-quickmerge-blocked-contract.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

QM="$(cd "$(dirname "$0")/../.." && pwd)/quickmerge.sh"
[ -f "$QM" ] || { echo "FATAL: quickmerge.sh not found at $QM"; exit 2; }

# ── Extract the REAL STAGE 0.4 BLOCKED-handling block ────────────────────────────
# From the `_QM_CONFLICTS=` capture line through the `fi` that follows `exit 1`
# (covers: conflicts-capture + the rebase-abort-rc discriminator + the emit).
# The block has exactly two standalone `fi` lines (the rebase-abort if/fi, then the
# QUICKMERGE_ALLOW_BEHIND if/exit/fi); capture from `_QM_CONFLICTS=` through the 2nd.
BLOCK=$(awk '
  /_QM_CONFLICTS="\$\(git diff/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+fi$/ { n++; if (n == 2) exit }
' "$QM")
[ -n "$BLOCK" ] || { echo "FATAL: could not extract STAGE 0.4 block from quickmerge.sh"; exit 2; }

# Structural anchor: the extracted block must carry the discriminator + both codes +
# the emit, in order — so a future edit that removes/renames the contract fails here.
case "$BLOCK" in
  *"git rebase --abort"*BEHIND_DIVERGED_CONFLICT*AUTOSTASH_POP_CONFLICT*"QUICKMERGE_BLOCKED code="*"RECOVERY:"*)
    pass "structural: extracted block carries the discriminator + both codes + QUICKMERGE_BLOCKED + RECOVERY" ;;
  *)
    fail "structural: extracted block missing a contract element"; echo "--- block ---"; echo "$BLOCK" ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

# Run the EXTRACTED block in a subshell (its `exit 1` exits only the subshell), with
# the STAGE 0.4 variables set + cwd = the repo already in the post-failed-pull state.
# Echoes the captured stdout.
run_block() {
  local repo="$1"
  (
    cd "$repo" || exit 9
    REPO_NAME="fixture-repo"
    _QM_REMOTE_REF="origin/main"
    _QM_REMOTE_BRANCH="main"
    _QM_BEHIND=1
    _QM_AHEAD=0
    # QUICKMERGE_ALLOW_BEHIND intentionally unset → takes the BLOCKED (exit 1) path.
    eval "$BLOCK"
  ) 2>&1
}

# ── Fixture A — BEHIND_DIVERGED_CONFLICT ─────────────────────────────────────────
# Local has a COMMITTED change to f.txt; remote has a different COMMITTED change to
# f.txt → behind + diverged + conflicting. `pull --rebase` leaves a rebase mid-flight
# → `git rebase --abort` rc 0 → BEHIND_DIVERGED_CONFLICT.
fixtureA() {
  local rem="$WORK/remA.git" loc="$WORK/locA" oth="$WORK/othA"
  $GIT init -q --bare "$rem"
  $GIT clone -q "$rem" "$loc" 2>/dev/null
  ( cd "$loc" && printf 'base\n' > f.txt && $GIT add f.txt && $GIT commit -qm base && $GIT push -q origin main )
  $GIT clone -q "$rem" "$oth"
  ( cd "$oth" && printf 'REMOTE-CHANGE\n' > f.txt && $GIT commit -qam remote && $GIT push -q origin main )
  ( cd "$loc" && printf 'LOCAL-CHANGE\n' > f.txt && $GIT commit -qam local && $GIT fetch -q origin main \
      && { $GIT pull --ff-only origin main --quiet >/dev/null 2>&1 || true; } \
      && { $GIT pull --rebase --autostash origin main --quiet >/dev/null 2>&1 || true; } )
  echo "$loc"
}

# ── Fixture B — AUTOSTASH_POP_CONFLICT ───────────────────────────────────────────
# Local has an UNCOMMITTED change to f.txt; remote has a COMMITTED change to f.txt.
# `pull --rebase --autostash` stashes the dirty change, fast-forwards (no local
# commits to rebase), then the autostash POP conflicts → NO rebase in progress →
# `git rebase --abort` rc!=0 → AUTOSTASH_POP_CONFLICT.
fixtureB() {
  local rem="$WORK/remB.git" loc="$WORK/locB" oth="$WORK/othB"
  $GIT init -q --bare "$rem"
  $GIT clone -q "$rem" "$loc" 2>/dev/null
  ( cd "$loc" && printf 'base\n' > f.txt && $GIT add f.txt && $GIT commit -qm base && $GIT push -q origin main )
  $GIT clone -q "$rem" "$oth"
  ( cd "$oth" && printf 'REMOTE-CHANGE\n' > f.txt && $GIT commit -qam remote && $GIT push -q origin main )
  ( cd "$loc" && $GIT fetch -q origin main \
      && printf 'LOCAL-DIRTY-UNCOMMITTED\n' > f.txt \
      && { $GIT pull --ff-only origin main --quiet >/dev/null 2>&1 || true; } \
      && { $GIT pull --rebase --autostash origin main --quiet >/dev/null 2>&1 || true; } )
  echo "$loc"
}

assert_code() {
  local label="$1" expected="$2" out="$3"
  local line; line=$(printf '%s\n' "$out" | grep -m1 'QUICKMERGE_BLOCKED code=' || true)
  if [ -z "$line" ]; then
    fail "$label: no QUICKMERGE_BLOCKED line emitted"; echo "--- output ---"; printf '%s\n' "$out"; return
  fi
  case "$line" in
    *"code=${expected} "*) pass "$label: emitted code=${expected}" ;;
    *) fail "$label: expected code=${expected}, got → $line" ;;
  esac
  # the contract carries repo/branch/behind/ahead/conflicts + a RECOVERY line
  case "$line" in *"repo=fixture-repo"*"branch=main"*"behind=1"*'conflicts="'*) : ;;
    *) fail "$label: QUICKMERGE_BLOCKED line missing repo/branch/behind/conflicts fields → $line" ;; esac
  printf '%s\n' "$out" | grep -q '^RECOVERY:' && pass "$label: RECOVERY line present" \
    || fail "$label: RECOVERY line missing"
}

echo "── Fixture A: behind + diverged-conflict (expect BEHIND_DIVERGED_CONFLICT) ──"
repoA=$(fixtureA); outA=$(run_block "$repoA"); assert_code "A/behind-diverged" "BEHIND_DIVERGED_CONFLICT" "$outA"

echo "── Fixture B: autostash-pop conflict (expect AUTOSTASH_POP_CONFLICT) ──"
repoB=$(fixtureB); outB=$(run_block "$repoB"); assert_code "B/autostash-pop" "AUTOSTASH_POP_CONFLICT" "$outB"

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
