#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# repro-prek-stash-restore-race.sh — deterministic reproduction of the prek stash/restore
# race described in plans/active/issues/prek_stash_restore_race_destroys_shared_checkout_wip_2026_08_08.md.
#
# Mechanism confirmed by this script: prek's pre-commit stash step snapshots every unstaged
# file to a patch BEFORE hooks run, then restores that patch AFTER hooks finish. If some OTHER
# process (a second interactive session, a second concurrent prek/quickmerge run, a human
# editor) writes a NEWER version of one of those files while the hook is still running, prek's
# before/after diff sees the working tree changed and treats that as "the hook modified files"
# -- it reverts to the ORIGINAL stashed snapshot, silently discarding the newer edit. No error,
# no conflict marker, no stash entry (`git stash list` stays empty), `git status` reports clean.
#
# This reproduces with the fleet's already-patched `IggyIkenna/prek` v0.4.12 fork binary (the
# fix shipped for plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md
# targeted a DIFFERENT mechanism -- a hook that itself modifies+restages files corrupting the
# git index) -- so this is a distinct, still-open hazard, not a regression of the fixed bug.
#
# Runs entirely inside a throwaway scratch repo (mktemp -d); never touches a real workspace repo.
#
# Usage:
#   repro-prek-stash-restore-race.sh              # run once, print PASS (bug present) / FAIL
#   repro-prek-stash-restore-race.sh --keep        # don't delete the scratch repo on exit
#
# Exit 0 + "BUG REPRODUCED" = the race fires (interleaved edit was silently lost).
# Exit 1 + "NOT REPRODUCED" = the interleaved edit survived (informational -- would mean the
#   race window closed on whatever prek build is on PATH; re-run a few times, this is a race).

set -euo pipefail

KEEP=0
for arg in "$@"; do
    case "$arg" in
        --keep) KEEP=1;;
        -h|--help) sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $arg" >&2; exit 2;;
    esac
done

REPO="$(mktemp -d "${TMPDIR:-/tmp}/prek-race-repro.XXXXXX")"
if [ "$KEEP" = "0" ]; then
    trap 'rm -rf "$REPO"' EXIT
else
    echo "Scratch repo kept at: $REPO"
fi

cd "$REPO"
git init -q
git config user.email "repro@example.com"
git config user.name "repro"

printf 'fileA v0\n' > fileA.txt
printf 'fileB v0\n' > fileB.txt
printf 'fileC v0 (HEAD)\n' > fileC.txt
git add -A
git commit -q -m "initial"

# A local hook that just sleeps -- widens the race window without needing to mutate any file
# itself (proving the loss does NOT require a fixer/formatter hook, only elapsed wall-clock
# time during which an external process can touch a stashed file).
cat > .pre-commit-config.yaml <<'EOF'
repos:
  - repo: local
    hooks:
      - id: slow-hook
        name: slow hook (widens the stash/restore race window)
        entry: bash -c 'sleep 3'
        language: system
        always_run: true
        pass_filenames: false
EOF
git add .pre-commit-config.yaml
git commit -q -m "add prek config"
prek install -q >/dev/null 2>&1

# Session 1's state: fileA is about to be committed (staged); fileB/fileC are unrelated
# in-progress edits, unstaged -- exactly the "other file mid-edit in the same checkout" shape
# from the issue doc.
printf 'fileA v1 (session1, about to commit)\n' > fileA.txt
printf 'fileB v1 (session1, unrelated in-progress edit)\n' > fileB.txt
printf 'fileC v1 (session1, unrelated in-progress edit -- pre-stash snapshot)\n' > fileC.txt
git add fileA.txt

COMMIT_LOG="$(mktemp)"
git commit -q -m "commit fileA" > "$COMMIT_LOG" 2>&1 &
COMMIT_PID=$!

# Give prek time to run its stash step (near-instant) before the hook's sleep dominates.
sleep 0.8

# Session 2's interleaved edit: writes a NEWER version of fileC while session 1's hook is
# still sleeping. This file was never staged by session 1 and session 2 has no idea a stash
# is in flight -- it is just editing its own in-progress work.
printf 'fileC v2 (session2, interleaved edit -- MUST SURVIVE)\n' > fileC.txt

wait "$COMMIT_PID" || true

FINAL_FILEC="$(cat fileC.txt)"
STASH_COUNT="$(git stash list | wc -l | tr -d ' ')"
DIRTY="$(git status --porcelain)"

echo "=== prek/commit log ==="
cat "$COMMIT_LOG"
rm -f "$COMMIT_LOG"
echo "=== final fileC content ==="
echo "$FINAL_FILEC"
echo "=== git stash list (entries) === $STASH_COUNT"
echo "=== git status --porcelain ==="
echo "$DIRTY"

if [[ "$FINAL_FILEC" == "fileC v2 (session2, interleaved edit -- MUST SURVIVE)" ]]; then
    echo "NOT REPRODUCED this run: session2's edit survived. This is a timing race -- re-run." >&2
    exit 1
fi

if [[ "$STASH_COUNT" != "0" ]]; then
    echo "NOT REPRODUCED (different shape): a stash entry exists to recover from -- the issue's" \
         "reported hazard is specifically the case with ZERO recovery path." >&2
    exit 1
fi

echo "BUG REPRODUCED: session2's interleaved edit to fileC was silently discarded." \
     "fileC now reads '${FINAL_FILEC}' instead of the survived edit, with an empty stash list" \
     "and a clean git status -- no error, no conflict marker, no recovery path."
exit 0
