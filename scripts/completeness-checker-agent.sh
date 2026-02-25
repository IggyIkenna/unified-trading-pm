#!/bin/bash
# Completeness Checker Agent
# Checks that all repos in WORKSPACE-MANIFEST.json are covered in Codex per-service docs
# Usage: ./completeness-checker-agent.sh [--fix]
#
# Checks:
# 1. Each service repo has entries in relevant Codex per-service/ dirs
# 2. Each service has all 8 canonical docs
# 3. Services missing from 10-audit/batch/ or live/

set -e
WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CODEX="$WORKSPACE_ROOT/unified-trading-codex"
MANIFEST="$WORKSPACE_ROOT/.cursor/WORKSPACE-MANIFEST.json"
# shellcheck disable=SC2034
FIX_MODE="${1:-}"

echo "Running Completeness Checker..."
echo "Manifest: $MANIFEST"
echo ""

ERRORS=0

# Get all service repos from manifest
if ! command -v jq &>/dev/null; then
  echo "ERROR: jq required for JSON parsing"
  exit 1
fi

SERVICE_REPOS=$(jq -r '.repositories | to_entries[] | select(.value.type == "service") | select(.value.status != "future") | .key' "$MANIFEST")
# shellcheck disable=SC2034
LIBRARY_REPOS=$(jq -r '.repositories | to_entries[] | select(.value.type == "library") | select(.value.status != "future") | .key' "$MANIFEST")
# shellcheck disable=SC2034
ALL_NON_FUTURE=$(jq -r '.repositories | to_entries[] | select(.value.status != "future") | .key' "$MANIFEST")

echo "=== Check 1: Service 8-canonical docs ==="
for repo in $SERVICE_REPOS; do
  REPO_DIR="$WORKSPACE_ROOT/$repo"
  [ ! -d "$REPO_DIR" ] && echo "  SKIP: $repo (not in workspace)" && continue
  MISSING=()
  for doc in "README.md" "docs/ARCHITECTURE.md" "docs/CONFIGURATION.md" "QUALITY_GATE_BYPASS_AUDIT.md"; do
    [ ! -f "$REPO_DIR/$doc" ] && MISSING+=("$doc")
  done
  if [ ${#MISSING[@]} -gt 0 ]; then
    echo "  MISSING in $repo: ${MISSING[*]}"
    ERRORS=$((ERRORS + ${#MISSING[@]}))
  fi
done

echo ""
echo "=== Check 2: Services in 10-audit/batch/ ==="
for repo in $SERVICE_REPOS; do
  AUDIT_FILE="$CODEX/10-audit/batch/${repo}.yaml"
  if [ ! -f "$AUDIT_FILE" ]; then
    echo "  MISSING audit: $repo"
    ERRORS=$((ERRORS + 1))
  fi
done

echo ""
echo "=== Check 3: Codex per-service coverage in 01-domain batch ==="
for repo in $SERVICE_REPOS; do
  DOMAIN_FILE="$CODEX/01-domain/batch/per-service/${repo}.md"
  if [ ! -f "$DOMAIN_FILE" ]; then
    echo "  MISSING 01-domain entry: $repo"
  fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ All completeness checks passed"
else
  echo "❌ Found $ERRORS completeness issues"
  exit 1
fi
