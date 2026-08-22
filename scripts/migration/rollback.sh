#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# rollback.sh — Helper for rolling back a repo to a target version
#
# Reads workspace-manifest.json and manifest_warnings.yaml. Checks if target
# is flagged DANGEROUS, finds git history state, compares dependency versions,
# and reports SAFE (deploy-only) vs UNSAFE (full snapshot needed).
#
# Usage:
#   ./rollback.sh <repo_name> <target_version>
#
# Example:
#   ./rollback.sh instruments-service 1.2.0
#
# Prerequisites: jq
#

set -euo pipefail

REPO_NAME="${1:?Usage: $0 <repo_name> <target_version>}"
TARGET_VERSION="${2:?Usage: $0 <repo_name> <target_version>}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CURSOR_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKSPACE_ROOT="$(cd "$CURSOR_DIR/.." && pwd)"
MANIFEST="$CURSOR_DIR/workspace-manifest.json"
WARNINGS="$CURSOR_DIR/manifest_warnings.yaml"

# --- Check jq ---
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq is required. Install with: brew install jq (macOS) or apt install jq (Linux)"
  exit 1
fi

if [ ! -f "$MANIFEST" ]; then
  echo "ERROR: Manifest not found: $MANIFEST"
  exit 1
fi

echo "=============================================="
echo "Rollback Helper"
echo "=============================================="
echo "Repo:   $REPO_NAME"
echo "Target: $TARGET_VERSION"
echo "=============================================="
echo

# --- Get current version from manifest ---
CURRENT_VERSION=$(jq -r --arg repo "$REPO_NAME" '
  .versions[$repo] // .repositories[$repo].version // empty
' "$MANIFEST")

if [ -z "$CURRENT_VERSION" ] || [ "$CURRENT_VERSION" = "null" ]; then
  echo "ERROR: Repo '$REPO_NAME' not found in manifest."
  exit 1
fi

echo "[1/5] Current version: $CURRENT_VERSION"
echo

# --- Check manifest_warnings.yaml for DANGEROUS ---
echo "[2/5] Checking manifest_warnings.yaml..."
if [ -f "$WARNINGS" ]; then
  # Check if this repo+version is flagged (structure: repo, version, status: DANGEROUS in same block)
  if grep -q "repo:.*$REPO_NAME" "$WARNINGS" 2>/dev/null && grep -q "version:.*$TARGET_VERSION" "$WARNINGS" 2>/dev/null; then
    if grep -A 20 "repo:.*$REPO_NAME" "$WARNINGS" | grep -q "status:.*DANGEROUS"; then
      echo "  ⚠️  WARNING: $REPO_NAME $TARGET_VERSION is flagged DANGEROUS in manifest_warnings.yaml"
      REASON=$(grep -A 20 "repo:.*$REPO_NAME" "$WARNINGS" | grep "reason:" | head -1 | sed 's/.*reason: *//;s/"//g')
      SAFE_ALT=$(grep -A 20 "repo:.*$REPO_NAME" "$WARNINGS" | grep "safe_alternative:" | head -1 | sed 's/.*safe_alternative: *//;s/"//g')
      [ -n "$REASON" ] && echo "  Reason: $REASON"
      [ -n "$SAFE_ALT" ] && echo "  Safe alternative: $SAFE_ALT"
      echo
      read -r -p "Proceed anyway? [y/N] " response
      if [[ ! "$response" =~ ^[yY]$ ]]; then
        echo "Aborted."
        exit 0
      fi
    fi
  fi
else
  echo "  (manifest_warnings.yaml not found, skipping)"
fi
echo

# --- Find git commit when repo was at target_version ---
echo "[3/5] Finding manifest state when $REPO_NAME was at $TARGET_VERSION..."
HISTORICAL_MANIFEST=""
PM_ROOT="$CURSOR_DIR"
COMMITS=$(git -C "$PM_ROOT" log --format="%H" -- "workspace-manifest.json" 2>/dev/null || true)
FOUND_COMMIT=""
for commit in $COMMITS; do
  VER=$(git -C "$PM_ROOT" show "$commit:workspace-manifest.json" 2>/dev/null | jq -r --arg repo "$REPO_NAME" '.versions[$repo] // .repositories[$repo].version // empty' 2>/dev/null || true)
  if [ "$VER" = "$TARGET_VERSION" ]; then
    FOUND_COMMIT="$commit"
    break
  fi
done

if [ -z "$FOUND_COMMIT" ]; then
  echo "  No git history found with $REPO_NAME at $TARGET_VERSION."
  echo "  (Manifest may not have been committed at that version)"
  echo
  echo "  Proceeding with version diff only..."
else
  echo "  Found at commit: $FOUND_COMMIT"
  HISTORICAL_MANIFEST=$(git -C "$PM_ROOT" show "$FOUND_COMMIT:workspace-manifest.json" 2>/dev/null)
fi
echo

# --- Compare dependency versions: historical vs current ---
echo "[4/5] Comparing dependency versions..."
MAJOR_BUMPS=()
NEED_FULL_SNAPSHOT=false

# Get dependencies for this repo from current manifest
DEPS=$(jq -r --arg repo "$REPO_NAME" '
  .repositories[$repo].dependencies[]? | .name
' "$MANIFEST" 2>/dev/null || true)

if [ -n "$DEPS" ] && [ -n "$HISTORICAL_MANIFEST" ]; then
  for dep in $DEPS; do
    CURR_VER=$(jq -r --arg d "$dep" '.versions[$d] // .repositories[$d].version // empty' "$MANIFEST")
    HIST_VER=$(echo "$HISTORICAL_MANIFEST" | jq -r --arg d "$dep" '.versions[$d] // .repositories[$d].version // empty')
    if [ -n "$HIST_VER" ] && [ -n "$CURR_VER" ]; then
      CURR_MAJOR=$(echo "$CURR_VER" | cut -d. -f1)
      HIST_MAJOR=$(echo "$HIST_VER" | cut -d. -f1)
      if [ "$CURR_MAJOR" != "$HIST_MAJOR" ] && [ "$CURR_MAJOR" -gt "$HIST_MAJOR" ] 2>/dev/null; then
        MAJOR_BUMPS+=("$dep: $HIST_VER -> $CURR_VER (MAJOR bump)")
        NEED_FULL_SNAPSHOT=true
      fi
    fi
  done
fi

if [ ${#MAJOR_BUMPS[@]} -gt 0 ]; then
  echo "  MAJOR version bumps in dependency chain:"
  for bump in "${MAJOR_BUMPS[@]}"; do
    echo "    - $bump"
  done
  echo "  -> UNSAFE: Full snapshot needed (dependencies have moved)"
else
  echo "  No MAJOR bumps in dependencies."
  echo "  -> SAFE: Deploy-only rollback"
fi
echo

# --- Report and show changes ---
echo "[5/5] Rollback plan"
echo "=============================================="

if [ "$NEED_FULL_SNAPSHOT" = true ]; then
  echo "UNSAFE: Full snapshot needed"
  echo
  echo "Required version changes (apply to WORKSPACE-MANIFEST.json and/or active_deployment.yaml):"
  echo
  if [ -n "$HISTORICAL_MANIFEST" ]; then
    echo "  Repo: $REPO_NAME -> $TARGET_VERSION"
    for dep in $DEPS; do
      HIST_VER=$(echo "$HISTORICAL_MANIFEST" | jq -r --arg d "$dep" '.versions[$d] // .repositories[$dep].version // empty')
      if [ -n "$HIST_VER" ]; then
        echo "  Dep:  $dep -> $HIST_VER"
      fi
    done
  else
    echo "  $REPO_NAME: $CURRENT_VERSION -> $TARGET_VERSION"
    echo "  (Dependencies: manually verify versions at target release)"
  fi
else
  echo "SAFE: Deploy-only rollback"
  echo
  echo "Change to make in WORKSPACE-MANIFEST.json (and active_deployment.yaml if used):"
  echo
  echo "  versions[\"$REPO_NAME\"]: \"$CURRENT_VERSION\" -> \"$TARGET_VERSION\""
  echo "  repositories[\"$REPO_NAME\"].version: \"$CURRENT_VERSION\" -> \"$TARGET_VERSION\""
  echo
  echo "  Or in active_deployment.yaml:"
  echo "  $REPO_NAME: $TARGET_VERSION"
fi

echo "=============================================="
echo
read -r -p "Apply changes now? [y/N] " response
if [[ "$response" =~ ^[yY]$ ]]; then
  echo "Manual edit required. Update WORKSPACE-MANIFEST.json with the version changes above."
  echo "Run: uv lock (if dependencies changed) and quality gates before committing."
else
  echo "No changes applied."
fi
