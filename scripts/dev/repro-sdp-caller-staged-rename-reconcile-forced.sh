#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA (regression harness for the residual-gap todo in
#   /plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md
#   -- keep until that doc archives)
#
# repro-sdp-caller-staged-rename-reconcile-forced.sh -- targets the residual-gap shape that
# repro-safe-doc-push-extreme-stash-rename-drop.sh does NOT exercise: that script's `git mv`
# lands into a checkout that never needs a REAL reconcile (fetch/pull is a clean fast-forward,
# so `stage_named_files`/`reassert_renames` only ever run once against an untouched index).
# The residual-gap todo's live report (2026-08-15, slot-2, "session resumption, post-fix")
# hit its failure specifically when the caller had ALREADY `git mv`'d the rename BEFORE
# invoking safe-doc-push.sh AND the run then had to go through a genuine reconcile cycle
# (autostash_rebase_reconcile -- stash push, rebase, pop, `git restore --staged .`) before
# staging ever ran. This script forces exactly that shape:
#   1. Bare origin + one worker clone, seeded with a plan file at an "active" path.
#   2. Seed >=10 stash entries (autostash_guard_bound_backlog's own ">=10 is extreme" bar).
#   3. Give the worker a LOCAL unpushed commit ahead of origin (a realistic "a prior attempt
#      already committed" shape, and the cheapest way to force `ahead != 0` on attempt 1,
#      which routes safe-doc-push.sh's retry loop through `autostash_rebase_reconcile`
#      unconditionally -- see safe-doc-push.sh's own "Defensive: shouldn't normally happen
#      pre-commit, but handle the same as the post-commit case if it does" comment).
#   4. THEN `git mv` the active-path file to an archive path (the caller-stages-first shape
#      the residual-gap todo specifically calls out), plus one unrelated edit bundled in.
#   5. A second clone pushes a genuinely unrelated commit, so the reconcile is a real
#      stash/rebase/pop cycle, not a no-op.
#   6. Run safe-doc-push.sh --files "<old> <new> <other>" with SDP_ISOLATED=0 (the AO-VM
#      default this host resolves to -- see safe-doc-push.sh's _sdp_isolation_default).
#   7. Check, independent of the script's own exit code/stdout claims: does origin actually
#      carry the NEW path and NOT carry the OLD path afterward.
#
# RESULT (2026-08-15, verified against unified-trading-pm@7e03ff2f01, the todo-2 fix commit):
# this reconcile-forced shape lands cleanly -- KNOWN_RENAME_SOURCES is captured FILES-based at
# script start (before any reconcile), and reassert_renames() re-asserts the deletion after
# every stage_named_files() call regardless of what shape the reconcile cycle left the index
# in, so the residual gap described in the todo does not reproduce against the current code.
# The todo's live report most likely predates a fresh pull of 7e03ff2f01 in that checkout.
#
# USAGE: bash scripts/dev/repro-sdp-caller-staged-rename-reconcile-forced.sh
# Exit 0 + "RECONCILE-FORCED RENAME LANDED CLEANLY" if the rename survives the reconcile.
# Exit 1 + "RENAME DROPPED UNDER FORCED RECONCILE" if it does not (the residual gap is real).

set -uo pipefail

SCRATCH_DIR="$(mktemp -d -t sdp-caller-mv-reconcile-repro-XXXXXX)"
cleanup() { command rm -rf -- "$SCRATCH_DIR"; }
trap cleanup EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"
git clone -q --bare "$REPO_ROOT" "$BARE"

WT="$SCRATCH_DIR/worker"
OLD="plans/active/repro_caller_mv_reconcile.md"
NEW="plans/archive/2026_08/repro_caller_mv_reconcile.md"
OTHER="plans/active/repro_caller_mv_reconcile_sibling.md"

git clone -q "$BARE" "$WT"
(cd "$WT" && git checkout -q live-defi-rollout)
mkdir -p "$WT/$(dirname "$OLD")"
printf '# archived-later plan\n\ncontent before archival.\n' >"$WT/$OLD"
printf '# sibling doc\n\nunrelated content.\n' >"$WT/$OTHER"
(cd "$WT" && git add "$OLD" "$OTHER" && git -c user.email=t@t.t -c user.name=t commit -q -m "seed: active plan + sibling doc" && git push -q origin live-defi-rollout)

# Seed >= 10 stash entries matching autostash_guard_bound_backlog's own detection regex.
(
  cd "$WT" || exit 90
  for i in $(seq 1 10); do
    echo "seed-$i" >scratch_seed.txt
    git stash push -q -u -m "autostash: seed entry $i" -- scratch_seed.txt 2>/dev/null || true
  done
  command rm -f scratch_seed.txt
  echo "  seeded stash list: $(git stash list | wc -l | tr -d ' ') entries"
)

# A prior-attempt-style local unpushed commit, BEFORE the git mv so it cannot accidentally
# absorb the (not-yet-staged) rename -- forces `ahead != 0` on attempt 1.
(
  cd "$WT" || exit 90
  echo "leftover" >leftover_local_commit.txt
  git add leftover_local_commit.txt
  git -c user.email=t@t.t -c user.name=t commit -q -m "leftover: simulates a prior unpushed local commit"
)

# The archival op the SSOT mandates, staged by the CALLER before ever invoking the script.
(
  cd "$WT" || exit 90
  mkdir -p "$(dirname "$NEW")"
  git mv "$OLD" "$NEW"
  printf '# sibling doc\n\nunrelated content -- edited.\n' >"$OTHER"
)

# A genuinely unrelated peer push, so the reconcile below is a real stash/rebase/pop cycle.
WT2="$SCRATCH_DIR/worker2"
git clone -q "$BARE" "$WT2"
(cd "$WT2" && git checkout -q live-defi-rollout && echo "concurrent" >concurrent_file.txt && git add concurrent_file.txt && git -c user.email=p@p.p -c user.name=peer commit -q -m "peer: concurrent unrelated commit" && git push -q origin live-defi-rollout)

echo "  worker git status before invoking safe-doc-push.sh:"
(cd "$WT" && git status --porcelain | sed 's/^/    /')

echo "  running safe-doc-push.sh (SDP_ISOLATED=0, the AO-VM default) ..."
(cd "$WT" && SDP_ISOLATED=0 bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" "test(caller-mv-reconcile-repro): archive plan" --files "$OLD $NEW $OTHER" >"$SCRATCH_DIR/run.log" 2>&1)
rc=$?
echo "  safe-doc-push.sh exit=$rc (log: $SCRATCH_DIR/run.log)"

new_on_origin="$(git -C "$BARE" cat-file -e "live-defi-rollout:$NEW" 2>/dev/null && echo yes || echo no)"
old_on_origin="$(git -C "$BARE" cat-file -e "live-defi-rollout:$OLD" 2>/dev/null && echo yes || echo no)"
echo "  origin has new path ($NEW): $new_on_origin"
echo "  origin still has old path ($OLD): $old_on_origin"

if [[ "${SDP_REPRO_KEEP_SCRATCH:-0}" == "1" ]]; then
  echo "  SDP_REPRO_KEEP_SCRATCH=1 -- leaving $SCRATCH_DIR in place for inspection (clean it up yourself)."
  trap - EXIT
fi

echo
if [[ "$new_on_origin" == "yes" && "$old_on_origin" == "no" ]]; then
  echo "RECONCILE-FORCED RENAME LANDED CLEANLY"
  exit 0
else
  echo "RENAME DROPPED UNDER FORCED RECONCILE (see $SCRATCH_DIR/run.log)"
  exit 1
fi
