#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Copy 18 repos with corruptions (after Stage 0 corrupt deletion).
# Git-corrupt repos: clone fresh at Code, then rsync working tree from iCloud.
# Others: rsync from iCloud to Code.
# Usage: ./copy-corrupt-repos.sh [ICLOUD_ROOT] [CODE_ROOT]

set -euo pipefail

ICLOUD="${1:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - Mac/repos/unified-trading-system-repos}"
CODE="${2:-$HOME/Code/unified-trading-system-repos}"
GITHUB_BASE="${GITHUB_BASE:-https://github.com/IggyIkenna}"

# Git-corrupt: need fresh clone
GIT_CORRUPT=(
  features-cross-instrument-service features-delta-one-service features-volatility-service
  system-integration-tests unified-trading-library
)

# All 17 corrupt repos
CORRUPT_REPOS=(
  archive execution-algo-library execution-analytics-ui execution-service
  features-cross-instrument-service features-delta-one-service features-volatility-service
  instruments-service live-health-monitor-ui market-data-processing-service
  market-tick-data-service matching-engine-library strategy-service
  system-integration-tests trading-analytics-ui
  unified-sports-execution-interface unified-trading-library
)

clone_repo() {
  local repo=$1
  local url="$GITHUB_BASE/$repo"
  if [[ -d "$CODE/$repo/.git" ]]; then
    echo "  Backup and clone fresh: $repo"
    mv "$CODE/$repo" "$CODE/${repo}.bak" 2>/dev/null || rm -rf "$CODE/$repo"
  fi
  git clone "$url" "$CODE/$repo" 2>/dev/null || echo "  Clone failed (repo may not exist): $repo"
}

for repo in "${CORRUPT_REPOS[@]}"; do
  src="$ICLOUD/$repo"
  dst="$CODE/$repo"
  if [[ ! -d "$src" ]] || [[ -L "$src" ]]; then
    echo "Skip (not in iCloud or symlink): $repo"
    continue
  fi
  echo "Processing: $repo"
  if [[ " ${GIT_CORRUPT[*]} " =~ " ${repo} " ]]; then
    clone_repo "$repo"
    if [[ -d "$dst" ]]; then
      rsync -av --delete --exclude='.git' --exclude='.gitignore' --exclude='.cursorignore' "$src/" "$dst/"
    fi
  else
    mkdir -p "$dst"
    rsync -av --delete --exclude='.git' --exclude='.gitignore' --exclude='.cursorignore' "$src/" "$dst/"
  fi
done

# Apply PM-aligned .gitignore and .cursorignore to each corrupt repo (not from iCloud)
PM="$CODE/unified-trading-pm"
if [[ -f "$PM/.gitignore" ]] && [[ -f "$PM/.cursorignore" ]]; then
  echo "Applying PM-aligned .gitignore and .cursorignore to corrupt repos..."
  for repo in "${CORRUPT_REPOS[@]}"; do
    dst="$CODE/$repo"
    if [[ -d "$dst" ]]; then
      cp "$PM/.gitignore" "$dst/.gitignore"
      cp "$PM/.cursorignore" "$dst/.cursorignore"
      echo "  Applied: $repo"
    fi
  done
fi

echo "Done."
