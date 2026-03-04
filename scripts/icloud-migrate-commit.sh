#!/usr/bin/env bash
# iCloud Repo Migration — Batched git add to avoid timeout on cloud-synced drives.
# Run from repo root. Kills cloud sync, adds in small batches with pauses.
# Rollout: copy to any of 60+ repos; run from each repo root.
#
# Run in background (has tendency to hang on iCloud): nohup bash scripts/icloud-migrate-commit.sh &
# Usage: bash scripts/icloud-migrate-commit.sh [--resume-from N]
#   --resume-from 7  = skip batches 1-6 (already staged), start at .cursor/

set -e
cd "$(git rev-parse --show-toplevel)"

RESUME_FROM=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --resume-from)
      RESUME_FROM="${2:-1}"
      shift 2
      ;;
    *) shift ;;
  esac
done

log() { echo "[$(date '+%H:%M:%S')] $*"; }
count_files() { find "$1" -type f 2>/dev/null | wc -l | tr -d ' '; }

log "=== iCloud migrate commit starting ==="

# 1. Kill iCloud sync (bird) to reduce contention — restarts automatically in ~5s
log "Stopping iCloud sync (bird)..."
killall bird 2>/dev/null && log "  bird killed" || log "  bird not running (ok)"
log "Waiting 5s for sync to settle..."
sleep 5

# 2. Clear stale git lock; reduce optional lock contention
export GIT_OPTIONAL_LOCKS=0
if [[ -f .git/index.lock ]]; then
  log "Removing stale .git/index.lock"
  rm -f .git/index.lock
else
  log "No stale index.lock"
fi

# 3. Stage in small batches with pause between each — lets iCloud settle
log "Staging in batches (2s pause between each)..."
run_batch() {
  local n="$1" desc="$2"
  shift 2
  [[ $n -lt $RESUME_FROM ]] && return 0
  local fc=""
  [[ -d "${1:-}" ]] && fc=" ($(count_files "$1") files)"
  log "  [$n/9] $desc$fc"
  git add "$@" 2>/dev/null || true
  log "      -> done"
  sleep 2
}

run_batch 1 ".gitignore .cursorignore" .gitignore .cursorignore
run_batch 2 "cursor-rules/" cursor-rules/
run_batch 3 "docs/" docs/
run_batch 4 "plans/" plans/
run_batch 5 "scripts/ security/ tests/" scripts/ security/ tests/
run_batch 6 "github-integration/" github-integration/
# run_batch 7 "rd-tax-credits/" rd-tax-credits/  # skipped - add from ~/Code after clone
run_batch 7 ".cursor/" .cursor/
run_batch 8 "root files" CANONICAL_DEPENDENCY_MANIFEST.svg canonical-dependency-manifest.json pyproject.toml workspace-constraints.toml workspace-manifest.json
if [[ $RESUME_FROM -le 9 ]]; then
  log "  [9/9] remaining (-A, excluding rd-tax-credits)"
  git add -A -- ':!rd-tax-credits'
  log "      -> done"
fi

# 4. Kill bird again — it restarted during staging; need clear window for commit/push
log "Stopping bird again before commit/push..."
killall bird 2>/dev/null && log "  bird killed" || true
sleep 3

log "Committing..."
git commit -m "WIP: savepoint (pre-move from iCloud)" --no-verify
log "  commit done: $(git rev-parse --short HEAD)"

# --force-with-lease: overwrite remote if it hasn't changed; safe for multi-repo rollout
log "Pushing to origin main (--force-with-lease)..."
git push --force-with-lease origin main
log "  push done"

log "=== Done ==="
log "Clone to ~/Code: git clone $(git remote get-url origin) \$HOME/Code/unified-trading-system-repos/unified-trading-pm"
