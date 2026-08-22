#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# setup-pre-flight-symlinks.sh — Symlink pre-flight-audit.sh (SSOT) to .cursor/scripts and all repos
#
# SSOT: unified-trading-pm/scripts/validation/pre-flight-audit.sh
# Repos can implement their own variations but inherit this template.
#
# Usage: bash unified-trading-pm/scripts/workspace/setup-pre-flight-symlinks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$PM_ROOT/.." && pwd)"
TARGET="$PM_ROOT/scripts/validation/pre-flight-audit.sh"

if [ ! -f "$TARGET" ]; then
  echo "[ERROR] SSOT not found: $TARGET"
  exit 1
fi

# 1. .cursor/scripts (for quickmerge)
mkdir -p "$WORKSPACE_ROOT/.cursor/scripts"
ln -sf "$TARGET" "$WORKSPACE_ROOT/.cursor/scripts/pre-flight-audit.sh"
echo "[OK] .cursor/scripts/pre-flight-audit.sh -> PM template"

# 2. All repos with scripts/
MANIFEST="$PM_ROOT/workspace-manifest.json"
repos=$(python3 -c "
import json
m = json.load(open('$MANIFEST'))
for r in m.get('repositories', {}):
    if r != 'unified-trading-pm':
        print(r)
" 2>/dev/null)

count=0
for repo in $repos; do
  scripts_dir="$WORKSPACE_ROOT/$repo/scripts"
  if [ -d "$scripts_dir" ]; then
    link="$scripts_dir/pre-flight-audit.sh"
    rm -f "$link"
    ln -sf "../unified-trading-pm/scripts/validation/pre-flight-audit.sh" "$link"
    echo "  $repo/scripts/pre-flight-audit.sh"
    ((count++)) || true
  fi
done
echo "[OK] $count repos linked"
