#!/bin/bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Check COD-SIZE violations across all repos (files >1500 lines)
# Usage: bash check-codsize-violations.sh [--threshold LINES] [--repos "repo1 repo2"]

set -euo pipefail

# Navigate to workspace root (script is in unified-trading-pm/scripts/validation/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$WORKSPACE_ROOT"

THRESHOLD=1500
REPOS_ARG=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --threshold)
      THRESHOLD="$2"
      shift 2
      ;;
    --repos)
      REPOS_ARG="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--threshold LINES] [--repos 'repo1 repo2']"
      exit 1
      ;;
  esac
done

# Default to all repos from workspace-manifest.json if not specified
if [ -z "$REPOS_ARG" ]; then
  MANIFEST="$SCRIPT_DIR/../../workspace-manifest.json"
  if [ ! -f "$MANIFEST" ]; then
    echo "ERROR: workspace-manifest.json not found at $MANIFEST"
    exit 1
  fi
  if ! command -v jq &>/dev/null; then
    echo "ERROR: jq is required. Install with: brew install jq (macOS) or apt install jq (Linux)"
    exit 1
  fi
  mapfile -t REPOS < <(jq -r '.repositories | keys[]' "$MANIFEST")
else
  # Split repos string into array
  IFS=' ' read -ra REPOS <<<"$REPOS_ARG"
fi

echo "=== COD-SIZE Violation Scanner ==="
echo "Threshold: $THRESHOLD lines"
echo "Repos to scan: ${#REPOS[@]}"
echo "Workspace root: $WORKSPACE_ROOT"
echo ""

total_violations=0
repos_with_violations=0
violation_list=""

# Filter to existing repos for the rg call
existing_repos=()
for repo in "${REPOS[@]}"; do
  [ -d "$repo" ] && existing_repos+=("$repo")
done

if [ ${#existing_repos[@]} -eq 0 ]; then
  echo "No repos found."
  exit 0
fi

# Two-phase approach for speed:
# Phase 1: find with -prune (stops traversal of .venv/node_modules/etc, no content reads)
#           + -size pre-filter (stat-only metadata check, ~40KB ≈ 900 lines)
# Phase 2: wc -l only on the small subset of candidate large files (exact line count)
# This avoids reading file content for the vast majority of source files.
SIZE_BYTES=$(( THRESHOLD * 45 ))  # ~45 bytes/line heuristic for pre-filter
all_large=$(find "${existing_repos[@]}" \
  \( -name '.venv' -o -name '.venv-workspace' -o -name 'node_modules' \
     -o -name '__pycache__' -o -name 'htmlcov' -o -name 'build' \
     -o -name 'dist' -o -name 'tests' -o -name 'scripts' \
     -o -name '*.egg-info' -o -name '.git' \) -prune \
  -o -name "*.py" -type f -size "+${SIZE_BYTES}c" -print \
  2>/dev/null \
  | xargs -r wc -l 2>/dev/null \
  | awk -v thresh="$THRESHOLD" '$1 > thresh && $2 != "total" {printf "%4d lines: %s\n", $1, $2}' \
  | sort -rn)

# Group by repo for per-repo output
if [ -n "$all_large" ]; then
  declare -A repo_lines
  while IFS= read -r line; do
    filepath=$(echo "$line" | awk '{print $NF}')
    repo=$(echo "$filepath" | cut -d/ -f1)
    repo_lines["$repo"]+="$line"$'\n'
  done <<< "$all_large"

  for repo in "${!repo_lines[@]}"; do
    count=$(printf '%s' "${repo_lines[$repo]}" | grep -c .)
    total_violations=$((total_violations + count))
    repos_with_violations=$((repos_with_violations + 1))
    violation_list="$violation_list  - $repo: $count files\n"
    echo "=== $repo ==="
    echo "❌ $count files exceed $THRESHOLD lines:"
    printf '%s' "${repo_lines[$repo]}"
    echo ""
  done
fi

echo "=== Summary ==="
echo "Repos scanned: ${#REPOS[@]}"
echo "Repos with violations: $repos_with_violations"
echo "Total files exceeding $THRESHOLD lines: $total_violations"
echo ""

if [ $repos_with_violations -gt 0 ]; then
  echo "Repos with violations:"
  echo -e "$violation_list"
  echo "⚠️  COD-SIZE violations detected"
  exit 1
else
  echo "✅ No violations found!"
  exit 0
fi
