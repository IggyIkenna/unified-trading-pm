#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA (re-run this to verify the flock/checksum fix from
#   plans/active/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md
#   actually closes the race; keep until that issue is fully resolved and verified)
#
# repro-prek-stash-restore-race.sh -- deterministic reproduction of the prek
# stash/restore data-loss race described in
# plans/active/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md.
#
# MECHANISM: prek's pre-commit hook (installed via `prek install`) stashes a repo's
# unstaged changes to a patch file BEFORE running hooks (so hooks only see staged
# content), then re-applies that patch AFTER hooks finish. If a SECOND process edits
# one of those unstaged files while the FIRST process's hooks are still running, the
# first process's restore re-applies its OWN stale snapshot on top of the second
# process's newer edit -- silently discarding it. `git stash list` stays empty (prek
# uses its own patch cache under ~/.cache/prek/patches/, not a real git stash) and
# `git status` reports nothing more alarming than an ordinary "modified" file, so the
# standard multi-agent recovery ritual (check status, check stash) actively confirms
# the wrong conclusion.
#
# WHAT THIS SCRIPT DOES: builds a disposable scratch git repo (under mktemp -d, never
# touches the real workspace checkout) with a deliberately slow local prek hook, then
# runs TWO genuinely concurrent `git commit`-triggered prek runs that each touch their
# own file while both racing on unstaged edits to a shared third file ("victim.txt").
# Session A commits first but has the slow hook (8s); Session B edits victim.txt AFTER
# A has already stashed-and-reset it, then commits its own change with --no-verify so
# its restore completes near-instantly. If the race reproduces, A's slower restore
# clobbers B's already-landed edit back to A's own stale snapshot once A's hook
# finally finishes -- exactly the "no error, no stash entry, no conflict marker"
# failure mode the issue reports.
#
# USAGE: bash scripts/dev/repro-prek-stash-restore-race.sh
# Exit 0 + "RACE REPRODUCED" if the data loss occurred; exit 1 + "RACE DID NOT
# REPRODUCE" if victim.txt ended up holding session B's edit (i.e. the race window
# closed -- useful as a regression check once the flock/checksum fix from the same
# issue doc lands).

set -euo pipefail

SCRATCH_DIR="$(mktemp -d -t prek-race-repro-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

REPO="$SCRATCH_DIR/repo"
mkdir -p "$REPO"
cd "$REPO"

git init -q
git config user.email "prek-race-repro@local"
git config user.name "prek-race-repro"

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

prek install -q

echo "== baseline victim.txt: $(cat victim.txt)"

# --- Session A: unstaged edit to victim.txt, then commit its OWN file (slow hook) ---
echo "vA-edit" > victim.txt
echo "fileA" > fileA.txt
git add fileA.txt
git commit -m "session A commit" > "$SCRATCH_DIR/A.log" 2>&1 &
A_PID=$!
echo "== session A commit started (pid=$A_PID), hook sleeps 8s"

sleep 1.5
echo "== victim.txt after A's stash-checkout (expect reset to baseline v0): $(cat victim.txt)"

# --- Session B: unaware of A, edits victim.txt then commits its own file fast ---
echo "vB-edit" > victim.txt
echo "fileB" > fileB.txt
git add fileB.txt
git commit -q -m "session B commit" --no-verify > "$SCRATCH_DIR/B.log" 2>&1
echo "== session B commit done (--no-verify, instant). victim.txt right after: $(cat victim.txt)"

set +e
wait "$A_PID"
A_EXIT=$?
set -e
echo "== session A commit exit code: $A_EXIT"

FINAL="$(cat victim.txt)"
echo "== FINAL victim.txt: $FINAL"
echo "== git stash list (expect empty -- no stash entry to recover from):"
git stash list
echo "== git status --short:"
git status --short
echo "== session A's prek/git output:"
cat "$SCRATCH_DIR/A.log"

if [ "$FINAL" = "vA-edit" ]; then
  echo
  echo "RACE REPRODUCED: session B's committed edit ('vB-edit') was silently reverted"
  echo "to session A's stale snapshot ('vA-edit') by A's delayed restore. git stash"
  echo "list is empty and git status shows only an ordinary 'modified' entry -- no"
  echo "signal that B's work was destroyed."
  exit 0
elif [ "$FINAL" = "vB-edit" ]; then
  echo
  echo "RACE DID NOT REPRODUCE: victim.txt still holds session B's edit."
  exit 1
else
  echo
  echo "UNEXPECTED final content ('$FINAL') -- neither session's edit survived cleanly."
  exit 2
fi
