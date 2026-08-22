#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# create-staging-branches.sh
#
# Creates a 'staging' branch from current 'main' in every repo listed in
# workspace-manifest.json. Safe to re-run: repos that already have a
# 'staging' branch are skipped.
#
# Run from workspace root (parent of unified-trading-pm).
#
# Usage:
#   bash unified-trading-pm/scripts/repo-management/create-staging-branches.sh [--dry-run] [--repo REPO_NAME]
#
# Options:
#   --dry-run   Show what would be done without creating branches
#   --repo      Only process a specific repo name
#
# Requires: gh CLI authenticated (for remote push), git

set -euo pipefail

WORKSPACE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
MANIFEST="$WORKSPACE_ROOT/unified-trading-pm/workspace-manifest.json"

DRY_RUN=false
REPO_FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=true ;;
    --repo) REPO_FILTER="$2"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
  shift
done

if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required. Install with: brew install jq"
  exit 1
fi

REPOS=$(jq -r '.repositories | keys[]' "$MANIFEST")

CREATED=0
SKIPPED=0
NOT_FOUND=0
ERRORS=0

for REPO in $REPOS; do
  # Apply filter if set
  if [[ -n "$REPO_FILTER" && "$REPO" != "$REPO_FILTER" ]]; then
    continue
  fi

  REPO_PATH="$WORKSPACE_ROOT/$REPO"

  if [[ ! -d "$REPO_PATH/.git" ]]; then
    echo "  NOT FOUND  $REPO (no .git at $REPO_PATH)"
    NOT_FOUND=$((NOT_FOUND + 1))
    continue
  fi

  # Check if staging already exists locally or remotely
  LOCAL_HAS=$(git -C "$REPO_PATH" branch --list staging)
  REMOTE_HAS=$(git -C "$REPO_PATH" ls-remote --heads origin staging 2>/dev/null || true)

  if [[ -n "$LOCAL_HAS" || -n "$REMOTE_HAS" ]]; then
    echo "  SKIP       $REPO (staging already exists)"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  if $DRY_RUN; then
    echo "  [dry-run]  Would create staging from main in $REPO"
    CREATED=$((CREATED + 1))
    continue
  fi

  # Fetch latest main, create staging from it, push
  if git -C "$REPO_PATH" fetch origin main --quiet 2>/dev/null && \
     git -C "$REPO_PATH" branch staging origin/main 2>/dev/null && \
     git -C "$REPO_PATH" push origin staging --quiet 2>/dev/null; then
    echo "  CREATED    $REPO (staging → pushed to origin)"
    CREATED=$((CREATED + 1))
  else
    echo "  ERROR      $REPO (failed to create/push staging)"
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""
ACTION="Would create"
$DRY_RUN || ACTION="Created"
echo "$ACTION $CREATED staging branches, skipped $SKIPPED, not found $NOT_FOUND, errors $ERRORS."

if [[ $ERRORS -gt 0 ]]; then
  exit 1
fi
