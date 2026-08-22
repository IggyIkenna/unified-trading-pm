#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Blind copy 36-37 clean repos from iCloud to Code.
# Excludes .gitignore and .cursorignore from copy; applies PM-aligned versions after.
# Usage: ./copy-clean-repos.sh [ICLOUD_ROOT] [CODE_ROOT]

set -euo pipefail

ICLOUD="${1:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - Mac/repos/unified-trading-system-repos}"
CODE="${2:-$HOME/Code/unified-trading-system-repos}"
PM="$CODE/unified-trading-pm"

CLEAN_REPOS=(
  alerting-service batch-audit-ui client-reporting-api client-reporting-ui
  execution-results-api features-calendar-service features-multi-timeframe-service
  features-onchain-service features-sports-service ibkr-gateway-infra logs-dashboard-ui
  onboarding-ui pnl-attribution-service position-balance-monitor-service
  risk-and-exposure-service strategy-ui unified-api-contracts unified-cloud-interface
  unified-config-interface unified-defi-execution-interface unified-domain-client
  unified-trading-library unified-feature-calculator-library unified-internal-contracts
  unified-market-interface unified-ml-interface unified-position-interface
  unified-reference-data-interface unified-trade-execution-interface unified-trading-codex
  unified-trading-ui-auth execution-analytics-ui
)

# Skip symlinked repos (already at Code)
SKIP=(deployment-api deployment-service deployment-ui settlement-ui unified-trading-pm)

for repo in "${CLEAN_REPOS[@]}"; do
  if [[ " ${SKIP[*]} " =~ " ${repo} " ]]; then
    echo "Skip (symlinked): $repo"
    continue
  fi
  src="$ICLOUD/$repo"
  dst="$CODE/$repo"
  if [[ ! -d "$src" ]]; then
    echo "Skip (not in iCloud): $repo"
    continue
  fi
  if [[ -L "$src" ]]; then
    echo "Skip (symlink): $repo"
    continue
  fi
  echo "Copying: $repo"
  mkdir -p "$dst"
  rsync -av --delete \
    --exclude='.gitignore' --exclude='.cursorignore' \
    --exclude='.git' \
    "$src/" "$dst/"
done

echo "Applying PM-aligned .gitignore/.cursorignore to workspace root..."
if [[ -f "$PM/.gitignore" ]]; then
  cp "$PM/.gitignore" "$CODE/.gitignore" 2>/dev/null || true
fi
if [[ -f "$PM/.cursorignore" ]]; then
  cp "$PM/.cursorignore" "$CODE/.cursorignore" 2>/dev/null || true
fi

echo "Done. Run quality gates on a sample repo to verify."
