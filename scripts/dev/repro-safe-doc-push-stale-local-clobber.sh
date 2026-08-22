#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA (re-run to verify a fix to `_sdp_reconcile_caller_duplicates` closes this gap;
#   keep until /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md's
#   "stale-local-copy clobbers a peer's landed content" todo is resolved and verified)
#
# repro-safe-doc-push-stale-local-clobber.sh -- reproduces a REAL, measured data-loss mechanism
# distinct from every other prek/isolation race tested in this doc's investigation (cross-worktree
# patches-dir race: clean; same-file single-shot concurrent edits, overlapping and not: clean).
# This one is NOT about prek at all -- it is a gap in `_sdp_reconcile_caller_duplicates`
# (scripts/dev/safe-doc-push.sh): that function only refreshes a caller's LOCAL copy of a named
# file when the local content is "the same words, differently wrapped" as what just landed
# (`_sdp_same_content`, a prosewrap/prettier-reflow detector). It does NOT refresh the local copy
# when origin has genuinely DIFFERENT content (a peer's real, distinct concurrent addition) -- by
# design, since that function's whole job is narrower than "always sync my local copy to origin".
#
# THE CONSEQUENCE: a caller whose local copy of a file goes stale across several ship rounds
# (because nothing re-syncs it) can, on a LATER round, submit a diff against a freshly-fetched
# origin that looks like -- and IS committed as -- a wholesale REPLACEMENT of a peer's
# already-landed lines with the caller's own stale-but-locally-consistent accumulation. Every
# individual push succeeds, every entry-hash landed-check passes (it only verifies the CALLER's
# own diff landed, never whether a peer's content survived), and the git commit HISTORY stays
# fully intact (nothing is missing from `git log -p`) -- but the file's CURRENT TREE CONTENT
# silently drops the peer's most recent additions from anyone reading HEAD.
#
# MEASURED 2026-08-12: 4 workers x 6 rounds each (24 ship attempts) against ONE shared file, no
# re-pull between a worker's own rounds (worker-loop below). 12 of 18 markers from a clean,
# uninterrupted run vanished from the final tree despite being individually reported LANDED;
# `git log -p` on the file showed later commits' diffs literally removing a prior worker's whole
# marker set and adding the new worker's own, in one commit -- not a subtle line-level collision.
#
# CAVEAT: this repro's worker loop deliberately never re-pulls between its own rounds, which is
# more aggressive than a real editing workflow (an agent normally reads a file fresh before
# editing it). It is not a perfect analog of any specific real incident -- but it is the closest
# REAL, reproducible mechanism found across 3 investigation sessions, and it directly matches the
# risk profile of a file under heavy, frequent, unrelated peer commit traffic (exactly the
# situation the file in the original report was under).
#
# USAGE: bash scripts/dev/repro-safe-doc-push-stale-local-clobber.sh [n_workers] [rounds]
# Exit 0 + "CLOBBER REPRODUCED" if any worker's own successfully-landed marker later vanishes from
# the file's final tree content; exit 1 + "NO CLOBBER" if every landed marker survives.

set -uo pipefail
N="${1:-4}"
ROUNDS="${2:-6}"

SCRATCH_DIR="$(mktemp -d -t sdp-clobber-repro-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"
F="scripts/plan-hygiene/.conctest/clobber_probe.txt"
RESULTS="$SCRATCH_DIR/confirmed_markers.txt"
: > "$RESULTS"

git clone -q --bare "$REPO_ROOT" "$BARE"

for i in $(seq 1 "$N"); do
  git clone -q "$BARE" "$SCRATCH_DIR/worker$i"
  (cd "$SCRATCH_DIR/worker$i" && git checkout -q live-defi-rollout)
done

mkdir -p "$SCRATCH_DIR/worker1/$(dirname "$F")"
printf 'baseline\n' > "$SCRATCH_DIR/worker1/$F"
(
  cd "$SCRATCH_DIR/worker1" || exit 91
  git add "$F"
  git -c user.email=t@t.t -c user.name=t commit -q -m "seed clobber probe"
  git push -q origin live-defi-rollout
)
for i in $(seq 2 "$N"); do
  (cd "$SCRATCH_DIR/worker$i" && git pull -q origin live-defi-rollout)
done

worker_loop() {
  local i="$1"
  cd "$SCRATCH_DIR/worker$i" || return 90
  local round marker rc
  for round in $(seq 1 "$ROUNDS"); do
    marker="MARKER-W${i}-R${round}-$RANDOM"
    echo "$marker" >> "$F"
    bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" "test(clobber-repro): worker$i round$round" \
      --files "$F" > "$SCRATCH_DIR/w${i}_r${round}.log" 2>&1
    rc=$?
    if [ "$rc" -eq 0 ]; then
      echo "$marker" >> "$RESULTS"
      echo "worker$i round$round: LANDED $marker"
    else
      echo "worker$i round$round: FAILED $marker (rc=$rc)"
    fi
    sleep "0.$((RANDOM % 7))"
  done
}

pids=()
for i in $(seq 1 "$N"); do
  worker_loop "$i" > "$SCRATCH_DIR/worker${i}_summary.log" 2>&1 &
  pids+=($!)
done
for p in "${pids[@]}"; do wait "$p"; done

cat "$SCRATCH_DIR"/worker*_summary.log

git -C "$BARE" show "live-defi-rollout:$F" > "$SCRATCH_DIR/final_content.txt" 2>/dev/null

missing=0
while IFS= read -r marker; do
  grep -qF "$marker" "$SCRATCH_DIR/final_content.txt" || {
    echo "MISSING (was reported LANDED, absent from final tree): $marker"
    missing=$((missing + 1))
  }
done < "$RESULTS"

total="$(wc -l <"$RESULTS" | tr -d ' ')"
echo
echo "== $missing / $total confirmed-landed markers missing from the final tree =="

if [ "$missing" -gt 0 ]; then
  echo "CLOBBER REPRODUCED"
  exit 0
else
  echo "NO CLOBBER"
  exit 1
fi
