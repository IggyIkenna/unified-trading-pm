#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA (re-run to verify the PREK_HOME per-worktree isolation fix from
#   /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md
#   actually closes the CROSS-worktree variant of the race; keep as a standing
#   regression check, mirroring repro-prek-stash-restore-race.sh's role for the
#   classic shared-working-tree variant)
#
# repro-prek-cross-worktree-race.sh -- tests a DIFFERENT question than
# repro-prek-stash-restore-race.sh. That script proves the classic race: two
# processes sharing ONE working tree can clobber each other via prek's
# stash/restore cycle. It does NOT prove anything about two SEPARATE `git
# worktree`s of the same repo -- each has its own working-tree directory, its own
# victim file at its own absolute path, so the classic mechanism (A's restore
# re-applying its stale snapshot onto the SAME file B just committed) has no shared
# destination to collide on.
#
# The open question this script answers: does prek's patches/ cache being
# HOST-GLOBAL (not per-worktree) let a race cross that boundary anyway -- i.e. can
# worktree A's restore end up touching worktree B's file, purely because both
# funnel through the same ~/.cache/prek (or $PREK_HOME) directory? If the answer is
# no, then PREK_HOME-per-worktree scoping doesn't address the corruption anyone
# has actually observed INSIDE isolated worktrees, and a different mechanism must
# be responsible (candidates: something in the copy-then-stage sequence a caller
# script does before invoking prek, or contention on the git object database /
# refs worktrees DO still share, unrelated to prek's cache at all).
#
# WHAT THIS SCRIPT DOES: builds a disposable bare repo + a "main" checkout (both
# under mktemp -d), creates TWO `git worktree add` worktrees from it -- Worktree A
# (slow hook, 8s) and Worktree B (fast, --no-verify) -- each with its OWN victim
# file at its own path, seeded identically at HEAD. Runs both `git commit`s
# concurrently. Supports two modes:
#   --shared-prek-home   both worktrees use the SAME $PREK_HOME (the pre-fix
#                         shape: prek's cache defaults to one host-global dir)
#   --isolated-prek-home each worktree gets its OWN $PREK_HOME, mirroring the
#                         fix shipped in quickmerge.sh / safe-doc-push.sh
#                         (2026-08-12, unified-trading-pm@62d1a42613)
#
# USAGE: bash scripts/dev/repro-prek-cross-worktree-race.sh --shared-prek-home
#        bash scripts/dev/repro-prek-cross-worktree-race.sh --isolated-prek-home
# Exit 0 + "CROSS-WORKTREE RACE REPRODUCED" if worktree B's file lost its own
# committed content; exit 1 + "NO CROSS-WORKTREE CORRUPTION" if both worktrees'
# files independently hold their own session's edit (the worktree boundary held).

set -euo pipefail

MODE="${1:-}"
if [[ "$MODE" != "--shared-prek-home" && "$MODE" != "--isolated-prek-home" ]]; then
  echo "usage: $0 --shared-prek-home | --isolated-prek-home" >&2
  exit 64
fi

SCRATCH_DIR="$(mktemp -d -t prek-xwt-repro-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

BARE="$SCRATCH_DIR/repo.git"
MAIN="$SCRATCH_DIR/main"
WT_A="$SCRATCH_DIR/wt-a"
WT_B="$SCRATCH_DIR/wt-b"
SHARED_PREK_HOME="$SCRATCH_DIR/prek-home-shared"

git init -q --bare "$BARE"
git clone -q "$BARE" "$MAIN"
cd "$MAIN"
git config user.email "prek-xwt-repro@local"
git config user.name "prek-xwt-repro"

cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: local
    hooks:
      - id: slow-hook
        name: slow-hook
        entry: sh -c 'sleep 8'
        language: system
        pass_filenames: false
        always_run: true
EOF

echo "v0" > victim.txt
git add .pre-commit-config.yaml victim.txt
git commit -q -m init --no-verify
git push -q origin HEAD:main

git worktree add -q -b wt-a "$WT_A" main
git worktree add -q -b wt-b "$WT_B" main

if [[ "$MODE" == "--isolated-prek-home" ]]; then
  PREK_HOME_A="$SCRATCH_DIR/prek-home-a"
  PREK_HOME_B="$SCRATCH_DIR/prek-home-b"
else
  PREK_HOME_A="$SHARED_PREK_HOME"
  PREK_HOME_B="$SHARED_PREK_HOME"
fi

( cd "$WT_A" && PREK_HOME="$PREK_HOME_A" prek install -q )
( cd "$WT_B" && PREK_HOME="$PREK_HOME_B" prek install -q )

echo "== mode: $MODE"
echo "== PREK_HOME_A=$PREK_HOME_A  PREK_HOME_B=$PREK_HOME_B"
echo "== baseline victim.txt in both worktrees: $(cat "$WT_A/victim.txt") / $(cat "$WT_B/victim.txt")"

# --- Worktree A: unstaged edit to ITS OWN victim.txt, commits its own file (slow hook) ---
(
  cd "$WT_A"
  echo "vA-edit" > victim.txt
  echo "fileA" > fileA.txt
  git add fileA.txt
  PREK_HOME="$PREK_HOME_A" git commit -m "worktree A commit" > "$SCRATCH_DIR/A.log" 2>&1
) &
A_PID=$!
echo "== worktree A commit started (pid=$A_PID), hook sleeps 8s"

sleep 1.5
echo "== victim.txt in A after its stash-checkout (expect reset to v0): $(cat "$WT_A/victim.txt")"
echo "== victim.txt in B (untouched so far, expect v0): $(cat "$WT_B/victim.txt")"

# --- Worktree B: independent edit to ITS OWN victim.txt, commits fast ---
(
  cd "$WT_B"
  echo "vB-edit" > victim.txt
  echo "fileB" > fileB.txt
  git add fileB.txt
  PREK_HOME="$PREK_HOME_B" git commit -q -m "worktree B commit" --no-verify > "$SCRATCH_DIR/B.log" 2>&1
)
echo "== worktree B commit done (--no-verify, instant). B/victim.txt right after: $(cat "$WT_B/victim.txt")"

set +e
wait "$A_PID"
A_EXIT=$?
set -e
echo "== worktree A commit exit code: $A_EXIT"

FINAL_A="$(cat "$WT_A/victim.txt")"
FINAL_B="$(cat "$WT_B/victim.txt")"
echo "== FINAL A/victim.txt: $FINAL_A"
echo "== FINAL B/victim.txt: $FINAL_B"
echo "== worktree A's prek/git output:"
cat "$SCRATCH_DIR/A.log"

if [[ "$FINAL_A" == "vA-edit" && "$FINAL_B" == "vB-edit" ]]; then
  echo
  echo "NO CROSS-WORKTREE CORRUPTION: each worktree independently holds its own"
  echo "session's edit. The worktree boundary held under mode $MODE."
  exit 1
elif [[ "$FINAL_B" != "vB-edit" ]]; then
  echo
  echo "CROSS-WORKTREE RACE REPRODUCED: worktree B's committed edit ('vB-edit') did"
  echo "NOT survive in B's own working tree (found '$FINAL_B' instead) -- worktree"
  echo "A's restore crossed the boundary under mode $MODE."
  exit 0
else
  echo
  echo "UNEXPECTED: A='$FINAL_A' B='$FINAL_B' -- investigate manually."
  exit 2
fi
