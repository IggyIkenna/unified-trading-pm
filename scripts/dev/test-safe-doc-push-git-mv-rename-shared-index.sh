#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# test-safe-doc-push-git-mv-rename-shared-index.sh -- regression test for
# safe_doc_push_extreme_stash_quarantine_drops_renamed_file_content_2026_08_15.md's ACTUAL root
# cause (confirmed by slot-19, independently re-confirmed by slot-25 via a minimal `git init`
# sandbox with zero stash entries involved): `git mv old new` removes `old` from the index
# outright (folded into `new`'s R100 rename pair) -- it is NOT the "tracked but missing from the
# working tree" shape `git add -- <path>` is documented to stage as a deletion. Naming that
# already-gone `old` path in `--files` and letting the shared-index retry loop's bulk
# `git add -- "${FILES[@]}"` call include it produces a hard, deterministic
# `fatal: pathspec '<old>' did not match any files` -- with ZERO stash entries required. The
# original issue's "24 entries is extreme" framing was a real but INCIDENTAL co-occurrence, not
# the trigger (see repro-safe-doc-push-extreme-stash-rename-drop.sh's own 0-stash-entry control).
#
# This test is deliberately the SIMPLEST possible reproduction of that exact shape: no stash
# seeding, no divergence, no concurrent peer -- just `git mv` + `safe-doc-push.sh --files "<old>
# <new>"` on a clean, non-diverged checkout. The fix under test excludes every
# KNOWN_RENAME_SOURCES path from the bulk `git add` call (safe-doc-push.sh); before the fix this
# fails on every run regardless of stash-pile size.
#
# USAGE: bash scripts/dev/test-safe-doc-push-git-mv-rename-shared-index.sh
# Exit 0 + "PASS" if the rename lands (new path on origin, old path gone); exit 1 + "FAIL"
# otherwise.

set -uo pipefail

SCRATCH_DIR="$(mktemp -d -t sdp-git-mv-rename-test-XXXXXX)"
trap 'rm -rf -- "$SCRATCH_DIR"' EXIT

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BARE="$SCRATCH_DIR/bare-origin.git"
OLD_PATH="scripts/plan-hygiene/.conctest/git_mv_rename_probe_old.md"
NEW_PATH="scripts/plan-hygiene/.conctest/git_mv_rename_probe_new.md"
EXPECTED_CONTENT="git-mv rename probe -- must land at the new path"

git clone -q --bare "$REPO_ROOT" "$BARE"
git clone -q "$BARE" "$SCRATCH_DIR/worker"
(cd "$SCRATCH_DIR/worker" && git checkout -q live-defi-rollout)

(
  cd "$SCRATCH_DIR/worker" || exit 90
  mkdir -p "$(dirname "$OLD_PATH")"
  printf '%s\n' "$EXPECTED_CONTENT" > "$OLD_PATH"
  git add "$OLD_PATH"
  git -c user.email=t@t.t -c user.name=t commit -q -m "seed git-mv rename probe"
  git push -q origin live-defi-rollout
)

# The exact shape: a clean checkout, no divergence, no stash pile -- just git mv, then invoke
# safe-doc-push.sh naming BOTH old and new paths, per the archival SSOT's own instruction.
(
  cd "$SCRATCH_DIR/worker" || exit 91
  git mv "$OLD_PATH" "$NEW_PATH"
  SDP_ISOLATED=0 bash "$REPO_ROOT/scripts/dev/safe-doc-push.sh" "test(git-mv-rename): probe" \
    --files "$OLD_PATH $NEW_PATH" > "$SCRATCH_DIR/run.log" 2>&1
)
RC=$?

echo "=== safe-doc-push.sh exit code: $RC ==="
echo "=== log ==="
cat "$SCRATCH_DIR/run.log"

new_landed="$(git -C "$BARE" show "live-defi-rollout:$NEW_PATH" 2>/dev/null)"
old_gone=1
git -C "$BARE" cat-file -e "live-defi-rollout:$OLD_PATH" 2>/dev/null && old_gone=0

if [ "$new_landed" = "$EXPECTED_CONTENT" ] && [ "$old_gone" -eq 1 ]; then
  echo
  echo "PASS -- rename landed cleanly (new path correct content, old path gone from origin)"
  exit 0
else
  echo
  echo "FAIL -- new_landed=[$new_landed] old_gone=$old_gone"
  exit 1
fi
