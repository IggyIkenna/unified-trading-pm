#!/bin/bash
#
# Enable Codex Compliance as BLOCKING Quality Gate
#
# Currently codex compliance is "warn only" - it can fail but doesn't block merges.
# This script makes codex compliance BLOCKING across all services for the cleanup.
#
# Changes:
# 1. Remove "warn only - not blocking" message
# 2. Add CODEX_STATUS to OVERALL_STATUS calculation
# 3. Make failures RED instead of YELLOW
#
# Usage:
#   bash enable-codex-compliance-blocking.sh
#

set -euo pipefail

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../../.." && pwd)}"

REPOS=(
  "execution-services"
  "strategy-service"
  "instruments-service"
  "unified-trading-library"
  "market-data-processing-service"
  "ml-training-service"
  "ml-inference-service"
  "features-delta-one-service"
  "features-volatility-service"
  "features-calendar-service"
  "features-onchain-service"
  "market-tick-data-handler"
  "unified-trading-deployment-v2"
)

echo -e "${BLUE}========================================"
echo "Enable Codex Compliance Blocking"
echo -e "========================================${NC}"
echo ""
echo "This will make codex compliance BLOCKING in all quality gates."
echo "Currently it's 'warn only' - failures don't block merges."
echo ""
echo "After this change:"
echo "  - Codex violations WILL block merges"
echo "  - Success criteria: full codex compliance"
echo "  - Align with cleanup project goals"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

UPDATED=0
SKIPPED=0

for repo in "${REPOS[@]}"; do
  QUALITY_GATES="$WORKSPACE_ROOT/$repo/scripts/quality-gates.sh"

  if [ ! -f "$QUALITY_GATES" ]; then
    echo -e "${YELLOW}⏭️  Skipping $repo (no quality-gates.sh)${NC}"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  # Check if already blocking
  if ! grep -q "warn only - not blocking" "$QUALITY_GATES"; then
    echo -e "${GREEN}✅ $repo (already blocking)${NC}"
    SKIPPED=$((SKIPPED + 1))
    continue
  fi

  echo -e "${BLUE}🔧 Updating $repo...${NC}"

  # Create backup
  cp "$QUALITY_GATES" "$QUALITY_GATES.backup"

  # Read the file
  CONTENT=$(cat "$QUALITY_GATES")

  # Replace warn-only with blocking
  NEW_CONTENT=$(echo "$CONTENT" | sed \
    -e 's/echo -e "Codex:    \${YELLOW}⚠️  FAILED (warn only - not blocking)\${NC}"/echo -e "Codex:    \${RED}❌ FAILED\${NC}"\n    OVERALL_STATUS=1/' \
    -e '/# Codex violations (print, os\.getenv, datetime\.now, etc\.) are non-blocking for now/d')

  # Write back
  echo "$NEW_CONTENT" >"$QUALITY_GATES"

  # Verify the change
  if grep -q "warn only - not blocking" "$QUALITY_GATES"; then
    echo -e "  ${RED}❌ Failed to update - restoring backup${NC}"
    mv "$QUALITY_GATES.backup" "$QUALITY_GATES"
    continue
  fi

  # Check if update was successful
  if grep -q "❌ FAILED" "$QUALITY_GATES" && ! grep -q "warn only" "$QUALITY_GATES"; then
    echo -e "  ${GREEN}✅ Updated successfully${NC}"
    rm "$QUALITY_GATES.backup"
    UPDATED=$((UPDATED + 1))
  else
    echo -e "  ${YELLOW}⚠️  Unexpected result - check manually${NC}"
    # Keep backup for manual review
    UPDATED=$((UPDATED + 1))
  fi
done

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Update Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Updated: $UPDATED services"
echo "Skipped: $SKIPPED services"
echo ""
echo "Next steps:"
echo "  1. Test locally: cd <service> && bash scripts/quality-gates.sh"
echo "  2. Verify codex failures now block: introduce a print() and re-run"
echo "  3. Commit changes: git add -A && git commit -m 'Enable codex compliance blocking'"
echo ""
echo "Codex standards: unified-trading-codex/06-coding-standards/README.md"
echo ""
