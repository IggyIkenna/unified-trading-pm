#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# rollout-version-bump-staging-only.sh
#
# Updates version-bump.yml in all repos to trigger only on staging pushes
# (removes `main` from branches trigger). version-bump.yml on main was only
# needed for the hotfix path — all changes now go through staging first.
#
# Usage:
#   bash scripts/rollout-version-bump-staging-only.sh [--dry-run]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
WORKSPACE_ROOT="$(cd "${PM_DIR}/.." && pwd)"
MANIFEST="${PM_DIR}/workspace-manifest.json"

DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

REPOS=$(python3 -c "
import json
with open('${MANIFEST}') as f:
    m = json.load(f)
for name in m.get('repositories', {}).keys():
    if name != 'unified-trading-pm':
        print(name)
")

UPDATED=0
SKIPPED=0
NOT_FOUND=0
FAILED=0

while IFS= read -r REPO; do
  [[ -z "$REPO" ]] && continue
  REPO_PATH="${WORKSPACE_ROOT}/${REPO}"
  WF="${REPO_PATH}/.github/workflows/version-bump.yml"

  if [[ ! -d "$REPO_PATH" ]]; then
    echo "  NOT FOUND $REPO"
    NOT_FOUND=$((NOT_FOUND + 1))
    continue
  fi

  if [[ ! -f "$WF" ]]; then
    echo "  SKIP $REPO (no version-bump.yml)"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Check if already staging-only
  if grep -q "branches: \[staging\]" "$WF" && ! grep -q "branches: \[main, staging\]" "$WF"; then
    echo "  UP-TO-DATE $REPO"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if ! grep -q "branches: \[main, staging\]" "$WF"; then
    echo "  SKIP $REPO (branches line not in expected format — check manually)"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if $DRY_RUN; then
    echo "  [dry-run] Would update $REPO"
    UPDATED=$((UPDATED + 1))
    continue
  fi

  # Update branches line
  sed -i '' 's/branches: \[main, staging\]/branches: [staging]/' "$WF"

  # Commit
  cd "$REPO_PATH"
  if git diff --quiet "$WF"; then
    echo "  NO-CHANGE $REPO (sed made no change)"
    SKIPPED=$((SKIPPED + 1))
    cd "$WORKSPACE_ROOT"
    continue
  fi

  git add ".github/workflows/version-bump.yml"
  if git commit -m "chore(ci): version-bump.yml triggers on staging only — all changes go through staging [skip ci]" 2>/dev/null; then
    echo "  COMMITTED $REPO"
    UPDATED=$((UPDATED + 1))
  else
    echo "  FAILED $REPO (commit failed)"
    FAILED=$((FAILED + 1))
  fi
  cd "$WORKSPACE_ROOT"
done <<< "$REPOS"

echo ""
echo "Done: updated=${UPDATED} skipped=${SKIPPED} not_found=${NOT_FOUND} failed=${FAILED}"
