#!/bin/bash
# Note: NOT using set -e so script continues even if repos don't exist

# Add Runtime Verification Rule to All Per-Repo .cursorrules
# Created: 2026-02-21
# Purpose: Ensure P0 blocking gate is explicit at both workspace AND repo level

WORKSPACE_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

echo "Adding Runtime Verification Rule to Per-Repo .cursorrules"
echo "=========================================================="
echo ""

# UI repos get UI-specific text
UI_REPOS=(
  "onboarding-ui"
  "backtest-ui"
  "batch-audit-ui"
  "client-reporting-ui"
  "logs-dashboard-ui"
  "ml-deployment-ui"
  "ml-training-ui"
  "trading-analytics-ui"
  "live-health-monitor-ui"
)

# Backend/service repos get backend-specific text
BACKEND_REPOS=(
  "instruments-service"
  "market-tick-data-handler"
  "market-data-processing-service"
  "features-delta-one-service"
  "features-volatility-service"
  "features-onchain-service"
  "features-calendar-service"
  "ml-training-service"
  "ml-inference-service"
  "strategy-service"
  "risk-and-exposure-service"
  "pnl-attribution-service"
  "position-balance-monitor-service"
  "alerting-system"
)

# Library repos get library-specific text
LIBRARY_REPOS=(
  "unified-cloud-services"
  "unified-config-interface"
  "unified-events-interface"
  "unified-trade-execution-interface"
  "unified-market-interface"
  "unified-domain-services"
)

# Pattern to match "## Workspace Rules" section (documentation; used in add_verification_text logic)
# shellcheck disable=SC2034
WORKSPACE_RULES_PATTERN="## Workspace Rules"

# UI verification text
UI_VERIFICATION_TEXT='**⚠️ RUNTIME VERIFICATION (P0 BLOCKING GATE):** NEVER claim "done" without actual runtime verification. For UI: must run `npm run dev`, wait 8-10s, read terminal output, grep for errors, verify NO errors present. See `.cursor/rules/runtime-verification-required.mdc`.'

# Backend verification text
BACKEND_VERIFICATION_TEXT='**⚠️ RUNTIME VERIFICATION (P0 BLOCKING GATE):** NEVER claim "done" without actual runtime verification. For backend: must start service, wait 8-10s, check for import/startup errors, verify service starts cleanly. See `.cursor/rules/runtime-verification-required.mdc`.'

# Library verification text
LIBRARY_VERIFICATION_TEXT='**⚠️ RUNTIME VERIFICATION (P0 BLOCKING GATE):** NEVER claim "done" without actual runtime verification. For library: must install in clean env, test import, run tests (if exist), verify no import errors. See `.cursor/rules/runtime-verification-required.mdc`.'

updated_count=0
skipped_count=0
missing_count=0

# Function to add verification text after "Inherits all rules" line
add_verification_text() {
  local repo_path="$1"
  local verification_text="$2"
  local cursorrules_file="$repo_path/.cursorrules"
  
  if [ ! -f "$cursorrules_file" ]; then
    echo "  ⚠️  No .cursorrules file found"
    ((missing_count++))
    return 0
  fi
  
  # Check if verification text already exists
  if grep -q "RUNTIME VERIFICATION (P0 BLOCKING GATE)" "$cursorrules_file"; then
    echo "  ✓ Already has runtime verification rule"
    ((skipped_count++))
    return 0
  fi
  
  # Create backup
  cp "$cursorrules_file" "$cursorrules_file.bak"
  
  # Find the line after "Inherits all rules" and insert verification text
  awk -v text="$verification_text" '
    /Inherits all rules from workspace/ {
      print
      print ""
      print text
      print ""
      next
    }
    {print}
  ' "$cursorrules_file.bak" > "$cursorrules_file"
  
  echo "  ✅ Added runtime verification rule"
  ((updated_count++))
}

# Process UI repos
echo "Processing UI repos..."
for repo in "${UI_REPOS[@]}"; do
  repo_path="$WORKSPACE_ROOT/$repo"
  if [ -d "$repo_path" ]; then
    echo "Processing: $repo"
    add_verification_text "$repo_path" "$UI_VERIFICATION_TEXT"
  else
    echo "Skipping: $repo (directory not found)"
    ((missing_count++))
  fi
done

echo ""
echo "Processing Backend repos..."
for repo in "${BACKEND_REPOS[@]}"; do
  repo_path="$WORKSPACE_ROOT/$repo"
  if [ -d "$repo_path" ]; then
    echo "Processing: $repo"
    add_verification_text "$repo_path" "$BACKEND_VERIFICATION_TEXT"
  else
    echo "Skipping: $repo (directory not found)"
    ((missing_count++))
  fi
done

echo ""
echo "Processing Library repos..."
for repo in "${LIBRARY_REPOS[@]}"; do
  repo_path="$WORKSPACE_ROOT/$repo"
  if [ -d "$repo_path" ]; then
    echo "Processing: $repo"
    add_verification_text "$repo_path" "$LIBRARY_VERIFICATION_TEXT"
  else
    echo "Skipping: $repo (directory not found)"
    ((missing_count++))
  fi
done

echo ""
echo "========================================================"
echo "Summary:"
echo "  Updated: $updated_count repos"
echo "  Skipped: $skipped_count repos (already have rule)"
echo "  Missing: $missing_count repos (.cursorrules not found or repo doesn't exist)"
echo ""
echo "Backups created as .cursorrules.bak in each repo."
echo ""
echo "To verify changes:"
echo "  grep -r 'RUNTIME VERIFICATION' */\.cursorrules"
echo ""
echo "To revert a repo:"
echo "  mv {repo}/.cursorrules.bak {repo}/.cursorrules"
echo ""
