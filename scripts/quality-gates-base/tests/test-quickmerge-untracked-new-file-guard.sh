#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Regression test for the quickmerge "EARLY EXIT: identical to main" guard
# (issues/quickmerge_untracked_new_files_silent_noop_2026_06_23.md,
# cicd_mvp_ldr_to_main_pipeline_2026_06_30.md P0).
#
# Bug (found 2026-06-23): `quickmerge --agent --files '<newfile>'` where every
# `--files` path is a brand-new UNTRACKED file printed "No differences from main —
# nothing to merge" and exited 0 having staged/committed/pushed NOTHING, because
# `git diff origin/main` (worktree-vs-commit) is blind to untracked files regardless
# of ref.
#
# Fix (2026-07-26, commit 04c0eef0e): the guard ALSO checks
# `git status --porcelain -- $FILES_ARG` (which DOES see untracked files) scoped to
# the supplied --files, so an untracked new file makes the guard fall through
# (proceed to STAGE 2+, i.e. actually ship) instead of silently no-opping. When
# --files is absent, or names only unchanged tracked paths, the guard is unchanged.
#
# Like test-quickmerge-blocked-contract.sh, this EXTRACTS the REAL guard from
# quickmerge.sh (not a replica) and runs it against synthesized git fixtures.
#
# Run: bash unified-trading-pm/scripts/quality-gates-base/tests/test-quickmerge-untracked-new-file-guard.sh
set -uo pipefail

PASS=0
FAIL=0
pass() { echo "PASS: $*"; PASS=$((PASS + 1)); }
fail() { echo "FAIL: $*"; FAIL=$((FAIL + 1)); }

QM="$(cd "$(dirname "$0")/../.." && pwd)/quickmerge.sh"
[ -f "$QM" ] || { echo "FATAL: quickmerge.sh not found at $QM"; exit 2; }

# ── Extract the REAL "no differences from main" guard ────────────────────────────
# From the `if git rev-parse origin/main` line through its own closing `fi` (the
# inner if nested inside `if [ "$NO_PR" != "true" ]; then` — 2-space indent).
BLOCK=$(awk '
  /if git rev-parse origin\/main/ { c = 1 }
  c { print }
  c && $0 ~ /^[[:space:]]+fi$/ { exit }
' "$QM")
[ -n "$BLOCK" ] || { echo "FATAL: could not extract the no-differences-from-main guard from quickmerge.sh"; exit 2; }

# Structural anchor: the extracted block must carry the git-diff check + the
# FILES_ARG-scoped git-status fallback + the exit message, in order — so a future
# edit that removes/renames the fix fails here even if the fixtures below don't.
case "$BLOCK" in
  *"git diff origin/main"*"FILES_ARG"*"git status --porcelain -- \$FILES_ARG"*"No differences from main"*)
    pass "structural: extracted block carries the git-diff check + FILES_ARG-scoped git-status fallback + exit message" ;;
  *)
    fail "structural: extracted block missing an expected contract element"; echo "--- block ---"; echo "$BLOCK" ;;
esac

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
GIT="git -c user.email=t@t.local -c user.name=test -c commit.gpgsign=false -c init.defaultBranch=main"

# Run the EXTRACTED block in a subshell (its `exit 0` exits only the subshell), with
# REPO_NAME + FILES_ARG set, cwd = the fixture repo. Prints a sentinel AFTER the
# block so callers can tell "fell through" (would proceed to ship) from "early-exited"
# (printed the no-op message and the subshell's `exit 0` fired first).
run_block() {
  local repo="$1" files_arg="$2"
  (
    cd "$repo" || exit 9
    REPO_NAME="fixture-repo"
    FILES_ARG="$files_arg"
    eval "$BLOCK"
    echo "SUBSHELL_FELL_THROUGH"
  )
}

# Common fixture: a bare "origin" with a main branch + one tracked file, a local
# clone tracking it with origin/main fetched (mirrors the real script's `git fetch
# origin main` immediately before this guard).
_make_fixture() {
  local rem="$WORK/rem_$1.git" loc="$WORK/loc_$1"
  $GIT init -q --bare "$rem"
  $GIT clone -q "$rem" "$loc" 2>/dev/null
  ( cd "$loc" && printf 'base\n' > tracked.txt && $GIT add tracked.txt && $GIT commit -qm base \
      && $GIT push -q origin main && $GIT fetch -q origin main )
  echo "$loc"
}

echo "── Case 1: brand-new UNTRACKED file named in --files (the bug) — must FALL THROUGH, not no-op ──"
repo1=$(_make_fixture case1)
( cd "$repo1" && printf 'new content\n' > newfile.txt )   # untracked, NOT git-added
out1=$(run_block "$repo1" "newfile.txt")
if printf '%s\n' "$out1" | grep -q "SUBSHELL_FELL_THROUGH"; then
  pass "case1: guard fell through for an untracked new --files file (no silent no-op)"
else
  fail "case1: guard incorrectly early-exited on an untracked new --files file"; echo "--- output ---"; printf '%s\n' "$out1"
fi

echo "── Case 2: clean tree, no --files, identical to origin/main — must STILL early-exit (no regression) ──"
repo2=$(_make_fixture case2)
out2=$(run_block "$repo2" "")
if printf '%s\n' "$out2" | grep -q "No differences from main"; then
  pass "case2: guard still early-exits on a genuinely clean, unchanged tree"
else
  fail "case2: guard failed to early-exit on a clean unchanged tree (regression)"; echo "--- output ---"; printf '%s\n' "$out2"
fi

echo "── Case 3: --files points at an EXISTING tracked file with no changes — must STILL early-exit ──"
repo3=$(_make_fixture case3)
out3=$(run_block "$repo3" "tracked.txt")
if printf '%s\n' "$out3" | grep -q "No differences from main"; then
  pass "case3: guard still early-exits when --files names an unchanged tracked file"
else
  fail "case3: guard failed to early-exit for an unchanged tracked --files file"; echo "--- output ---"; printf '%s\n' "$out3"
fi

echo "── Case 4: --files names an untracked new file, tree ALSO has an unrelated modified tracked file — must fall through via the pre-existing git-diff branch ──"
repo4=$(_make_fixture case4)
( cd "$repo4" && printf 'modified\n' >> tracked.txt && printf 'new content\n' > newfile.txt )
out4=$(run_block "$repo4" "newfile.txt")
if printf '%s\n' "$out4" | grep -q "SUBSHELL_FELL_THROUGH"; then
  pass "case4: guard falls through when the tree has a real diff vs origin/main (pre-existing path, still correct)"
else
  fail "case4: guard incorrectly early-exited despite a real diff vs origin/main"; echo "--- output ---"; printf '%s\n' "$out4"
fi

echo
echo "── result: ${PASS} passed / ${FAIL} failed ──"
[ "$FAIL" -eq 0 ] || exit 1
