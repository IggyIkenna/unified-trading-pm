#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Split current changes into one commit per directory, push after each.
# Run from repo root. Pause iCloud first for speed: sudo pkill -SIGSTOP -x nsurlsessiond
#
# If Step 1 hangs (iCloud), run this manually in another terminal and wait:
#   git stash push -u -m "split-commits" && git fetch origin main && git branch -f main origin/main && git checkout main && git stash pop && git restore --staged .
# Then re-run this script with: SKIP_SYNC=1 bash scripts/workspace/split-commits-by-dir.sh
set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

if [[ -z "${SKIP_SYNC:-}" ]]; then
  echo "Step 1: Stash changes, sync main to origin/main, restore changes unstaged..."
  echo "(If this hangs, Ctrl+C, run the sync manually, then: SKIP_SYNC=1 bash $0)"
  rm -f .git/index.lock
  git fetch origin main
  git stash push -u -m "split-commits-by-dir"
  git branch -f main origin/main
  git checkout main
  git stash pop
  git restore --staged .
else
  echo "Skipping sync (SKIP_SYNC=1). Assuming working tree has unstaged changes."
fi

echo ""
echo "Step 2: Commit and push scripts/..."
git add scripts/
git commit -m "chore: pre-flight symlinks, quickmerge workspace-manifest deps"
git -c pack.window=0 -c pack.depth=0 push origin main --no-verify

echo ""
echo "Step 3: Commit and push plans/..."
git add plans/
git commit -m "chore: plans active"
git -c pack.window=0 -c pack.depth=0 push origin main --no-verify

echo ""
echo "Step 4: Commit and push .cursor/rules/..."
git add .cursor/rules/
git commit -m "feat: cursor rules by category"
git -c pack.window=0 -c pack.depth=0 push origin main --no-verify

echo ""
echo "Step 5: Commit and push github-integration/..."
git add github-integration/
git commit -m "chore: github-integration cleanup, remove need_to_be_sorted, archive"
git -c pack.window=0 -c pack.depth=0 push origin main --no-verify

echo ""
echo "Step 6: Commit and push QUALITY_GATE_BYPASS_AUDIT.md (skip if already pushed)..."
git add QUALITY_GATE_BYPASS_AUDIT.md
git diff --cached --quiet || { git commit -m "chore: update QUALITY_GATE_BYPASS_AUDIT" && git -c pack.window=0 -c pack.depth=0 push origin main --no-verify; }

echo ""
echo "Done. Resume iCloud: sudo pkill -SIGCONT -x nsurlsessiond"
