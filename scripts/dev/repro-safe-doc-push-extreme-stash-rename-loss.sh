#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA (re-run to verify the extreme-stash-pile quarantine fix stays closed; keep
#   until /plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md
#   is archived)
#
# repro-safe-doc-push-extreme-stash-rename-loss.sh -- reproduces
# safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md: a `git mv`
# rename's NEW-path content vanishing (not merely mis-staged) when safe-doc-push.sh's
# extreme-autostash-pile guard (autostash_guard_bound_backlog, tree-wip-guard.sh) fires while a
# concurrent peer commit forces the rebase-autostash reconcile path to run.
#
# MECHANISM UNDER TEST: autostash_guard_bound_backlog's pre-pull quarantine step (>=10 autostash
# entries) snapshots the CURRENT dirty tree via `git diff --name-only` (unstaged only) and, for
# any file NOT in the caller's protected --files set, `git stash push` it then restores the
# origin version. A staged `git mv` rename is invisible to that unstaged diff at the moment this
# guard fires -- but if a genuine divergence then forces `autostash_rebase_reconcile` to run its
# own `git pull --rebase --autostash`, THAT stash/pop cycle can decompose the staged rename into
# a staged add (new path) + unstaged delete (old path), same mechanism f76a03a995's
# KNOWN_RENAME_SOURCES/reassert_renames fix already targets for the "lands at both paths" bug --
# except here the extreme-pile guard's OWN quarantine, and autostash_guard_quarantine_stale_pop's
# post-pop stale-content quarantine, both run around the SAME window and may re-stash content
# their `protected` check should have exempted, or lose the new-path content entirely if it was
# never committed anywhere and the working copy gets swept without a restore path.
#
# USAGE: bash scripts/dev/repro-safe-doc-push-extreme-stash-rename-loss.sh
# Exit 0 + "CONTENT LOSS REPRODUCED" if the renamed file's new-path content is missing from disk,
# the index, AND git ls-files after safe-doc-push.sh runs (matching the issue's observed state).
# Exit 1 + "NO LOSS" if the rename lands cleanly (fix verified).

set -uo pipefail

SCRATCH_DIR="$(mktemp -d -t sdp-rename-loss-repro-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"
OLD_PATH="scripts/plan-hygiene/.conctest/rename_probe_old.md"
NEW_PATH="scripts/plan-hygiene/.conctest/rename_probe_new.md"

git clone -q --bare "$REPO_ROOT" "$BARE"

git clone -q "$BARE" "$SCRATCH_DIR/worker1"
(cd "$SCRATCH_DIR/worker1" && git checkout -q live-defi-rollout)
git clone -q "$BARE" "$SCRATCH_DIR/peer"
(cd "$SCRATCH_DIR/peer" && git checkout -q live-defi-rollout)

# Seed the baseline file both clones will race over.
mkdir -p "$SCRATCH_DIR/worker1/$(dirname "$OLD_PATH")"
printf 'baseline content -- rename probe\n' > "$SCRATCH_DIR/worker1/$OLD_PATH"
(
  cd "$SCRATCH_DIR/worker1" || exit 91
  git add "$OLD_PATH"
  git -c user.email=t@t.t -c user.name=t commit -q -m "seed rename probe"
  git push -q origin live-defi-rollout
)
(cd "$SCRATCH_DIR/peer" && git pull -q origin live-defi-rollout)

# worker1: an unrelated LOCAL-ONLY commit first so `ahead>0` pre-commit -- this forces the
# script's own "else" branch (autostash_rebase_reconcile unconditionally) rather than relying on
# a real working-tree conflict to trigger it.
(
  cd "$SCRATCH_DIR/worker1" || exit 92
  echo "local-only" > local_ahead_probe.txt
  git add local_ahead_probe.txt
  git -c user.email=t@t.t -c user.name=t commit -q -m "worker1: local-only commit (ahead>0)"
)

# worker1: stage the rename (this is the content that must survive) -- NOT part of the local commit.
(
  cd "$SCRATCH_DIR/worker1" || exit 96
  git mv "$OLD_PATH" "$NEW_PATH"
  printf 'baseline content -- rename probe\nrenamed by worker1\n' > "$NEW_PATH"
  git add "$NEW_PATH"
)

# Seed >=10 autostash-tagged stash entries in worker1's repo so
# autostash_guard_bound_backlog's ">=10 is extreme" branch fires (matches the issue's reported
# 24-entry pile). Each entry stashes an unrelated scratch file so it never touches OLD_PATH/NEW_PATH.
(
  cd "$SCRATCH_DIR/worker1" || exit 93
  for i in $(seq 1 12); do
    echo "scratch $i" > "scratch_stash_seed_$i.txt"
    git stash push -u -m "On live-defi-rollout: autostash" -- "scratch_stash_seed_$i.txt" >/dev/null 2>&1
  done
)

# peer: push an UNRELATED commit (does not touch OLD_PATH/NEW_PATH at all) so worker1's rebase
# has genuinely nothing to conflict with -- isolates whether the extreme-quarantine machinery
# alone (not a real content conflict) is what drops the rename's content.
(
  cd "$SCRATCH_DIR/peer" || exit 94
  echo "peer unrelated change" > peer_unrelated.txt
  git add peer_unrelated.txt
  git -c user.email=p@p.p -c user.name=peer commit -q -m "peer: unrelated concurrent commit"
  git push -q origin live-defi-rollout
)

# Run safe-doc-push.sh against this scratch origin -- SDP_ISOLATED=0 to match the issue's second
# (shared-index) invocation, which failed identically to the isolated-mode first invocation.
(
  cd "$SCRATCH_DIR/worker1" || exit 95
  SDP_ISOLATED=0 \
    bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" "test(rename-loss-repro): worker1" \
    --files "$OLD_PATH $NEW_PATH" > "$SCRATCH_DIR/worker1_run.log" 2>&1
)
RC=$?

echo "=== safe-doc-push.sh exit code: $RC ==="
echo "=== log ==="
cat "$SCRATCH_DIR/worker1_run.log"
echo "=== post-run git status (worker1) ==="
(cd "$SCRATCH_DIR/worker1" && git status --porcelain)
echo "=== post-run ls-files for NEW_PATH ==="
(cd "$SCRATCH_DIR/worker1" && git ls-files -- "$NEW_PATH")
echo "=== post-run disk state ==="
[ -f "$SCRATCH_DIR/worker1/$NEW_PATH" ] && echo "NEW_PATH present on disk" || echo "NEW_PATH ABSENT from disk"
[ -f "$SCRATCH_DIR/worker1/$OLD_PATH" ] && echo "OLD_PATH still present on disk (rename incomplete)" || echo "OLD_PATH absent from disk (expected)"

new_on_disk=0; new_tracked=0
[ -f "$SCRATCH_DIR/worker1/$NEW_PATH" ] && new_on_disk=1
(cd "$SCRATCH_DIR/worker1" && git ls-files --error-unmatch -- "$NEW_PATH" >/dev/null 2>&1) && new_tracked=1

if [ "$new_on_disk" -eq 0 ] && [ "$new_tracked" -eq 0 ]; then
  echo
  echo "CONTENT LOSS REPRODUCED"
  exit 0
else
  echo
  echo "NO LOSS"
  exit 1
fi
