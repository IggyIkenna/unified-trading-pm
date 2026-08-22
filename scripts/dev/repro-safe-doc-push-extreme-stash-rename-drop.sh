#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA (re-run to verify a fix to autostash_guard_bound_backlog /
#   autostash_guard_quarantine_stale_pop closes this gap; keep until
#   /plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md
#   todo 2 is resolved and verified)
#
# repro-safe-doc-push-extreme-stash-rename-drop.sh -- reproduces (or refutes) the mechanism
# hypothesised in
# plans/active/issues/safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md:
# safe-doc-push.sh's "24+ entries is extreme" quarantine branch (autostash_guard_bound_backlog,
# scripts/dev/tree-wip-guard.sh) silently drops a `git mv`'d rename's content when the caller's
# named --files pass through it, on a checkout carrying a large pre-existing autostash/
# safety-snapshot stash pile.
#
# WHAT THIS DOES (mirrors the established pattern in repro-safe-doc-push-stale-local-clobber.sh):
#   1. Bare origin + one worker clone, seeded with a plan file at an "active" path.
#   2. Seed >=10 stash entries whose messages match autostash_guard_bound_backlog's own detection
#      regex ('autostash' or 'safety-snapshot.*stale reapplied') -- this is what flips the
#      guard's ">=10 entries is extreme" branch without needing 24 real autostash cycles.
#   3. `git mv` the active-path file to an archive path (the exact operation
#      plan-completion-and-archival-discipline.md mandates for every plan closeout), plus one
#      unrelated small edit to a second tracked file bundled in the same push (mirrors the
#      original incident's "bundled with 3 unrelated small edits").
#   4. Run safe-doc-push.sh --files "<old> <new> <other>" with SDP_ISOLATED=0 (shared-index path
#      -- the mode both original invocations fell through to) and separately with isolation left
#      at its default, since the issue doc reports the failure reproduced on BOTH.
#   5. Check, independent of the script's own exit code/stdout claims: does origin/live-defi-rollout
#      actually carry the NEW path with the mv'd content and NOT carry the OLD path afterward?
#
# USAGE: bash scripts/dev/repro-safe-doc-push-extreme-stash-rename-drop.sh
# Exit 0 + "RENAME DROP REPRODUCED" if either mode loses the rename (new path absent from origin,
# OR old path still present on origin, OR the script errored before landing anything).
# Exit 1 + "NO DROP -- rename landed cleanly in both modes" if both modes carry the rename intact.

set -uo pipefail

SCRATCH_DIR="$(mktemp -d -t sdp-rename-drop-repro-XXXXXX)"
if [[ "${SDP_REPRO_KEEP_SCRATCH:-0}" == "1" ]]; then
  echo "SDP_REPRO_KEEP_SCRATCH=1 -- leaving $SCRATCH_DIR in place for inspection (clean it up yourself)."
else
  trap 'command rm -rf -- "$SCRATCH_DIR"' EXIT
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"

git clone -q --bare "$REPO_ROOT" "$BARE"

STASH_COUNT_THRESHOLD=10 # matches autostash_guard_bound_backlog's own ">= 10" extreme bar

run_mode() {
  local mode_name="$1" isolated_env="$2"
  local wt="$SCRATCH_DIR/worker-$mode_name"
  local old_path="plans/active/repro_extreme_stash_rename_${mode_name}.md"
  local new_path="plans/archive/2026_08/repro_extreme_stash_rename_${mode_name}.md"
  local other_path="plans/active/repro_extreme_stash_rename_${mode_name}_sibling.md"

  git clone -q "$BARE" "$wt"
  (cd "$wt" && git checkout -q live-defi-rollout)

  mkdir -p "$wt/$(dirname "$old_path")" "$wt/$(dirname "$other_path")"
  printf '# archived-later plan (%s)\n\ncontent before archival.\n' "$mode_name" >"$wt/$old_path"
  printf '# sibling doc (%s)\n\nunrelated content.\n' "$mode_name" >"$wt/$other_path"
  (
    cd "$wt" || exit 90
    git add "$old_path" "$other_path"
    git -c user.email=t@t.t -c user.name=t commit -q -m "seed: active plan + sibling doc ($mode_name)"
    git push -q origin live-defi-rollout
  )

  # Seed >= STASH_COUNT_THRESHOLD stash entries matching the guard's own detection regex --
  # a dummy file is touched and re-stashed each round so `git stash push` always has something
  # to park (an empty working tree refuses to stash).
  (
    cd "$wt" || exit 90
    dummy="scratch_stash_seed_${mode_name}.txt"
    for i in $(seq 1 "$STASH_COUNT_THRESHOLD"); do
      echo "seed-$i" >"$dummy"
      git stash push -q -u -m "autostash: seed entry $i ($mode_name)" -- "$dummy" 2>/dev/null || true
    done
    rm -f "$dummy"
    echo "  [$mode_name] seeded stash list: $(git stash list | wc -l | tr -d ' ') entries"
  )

  # The archival op the SSOT mandates: git mv the active plan to its archive path, plus one
  # unrelated small edit bundled in, exactly as the original incident's --files call did.
  (
    cd "$wt" || exit 90
    mkdir -p "$(dirname "$new_path")"
    git mv "$old_path" "$new_path"
    printf '# sibling doc (%s)\n\nunrelated content -- edited.\n' "$mode_name" >"$other_path"
  )

  echo "  [$mode_name] running safe-doc-push.sh (SDP_ISOLATED=$isolated_env) ..."
  (
    cd "$wt" || exit 90
    SDP_ISOLATED="$isolated_env" bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" \
      "test(rename-drop-repro): archive $mode_name plan" \
      --files "$old_path $new_path $other_path" \
      >"$SCRATCH_DIR/${mode_name}.log" 2>&1
  )
  local rc=$?
  echo "  [$mode_name] safe-doc-push.sh exit=$rc (log: $SCRATCH_DIR/${mode_name}.log)"

  # Ground truth: what does origin ACTUALLY carry, independent of the script's own claims.
  local new_on_origin old_on_origin
  new_on_origin="$(git -C "$BARE" cat-file -e "live-defi-rollout:$new_path" 2>/dev/null && echo yes || echo no)"
  old_on_origin="$(git -C "$BARE" cat-file -e "live-defi-rollout:$old_path" 2>/dev/null && echo yes || echo no)"
  echo "  [$mode_name] origin has new path ($new_path): $new_on_origin"
  echo "  [$mode_name] origin still has old path ($old_path): $old_on_origin"

  if [[ "$new_on_origin" == "yes" && "$old_on_origin" == "no" ]]; then
    echo "  [$mode_name] RESULT: rename landed cleanly"
    return 0
  fi
  echo "  [$mode_name] RESULT: rename DROPPED (see $SCRATCH_DIR/${mode_name}.log)"
  return 1
}

overall_dropped=0
run_mode "shared-index" 0 || overall_dropped=1
run_mode "isolated-default" 1 || overall_dropped=1

echo
if [[ "$overall_dropped" -eq 1 ]]; then
  echo "RENAME DROP REPRODUCED"
  exit 0
else
  echo "NO DROP -- rename landed cleanly in both modes"
  exit 1
fi
