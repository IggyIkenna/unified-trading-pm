#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# Replace iCloud repo dirs with symlinks to Code.
# Usage: ./symlink-icloud-to-code.sh [ICLOUD_ROOT] [CODE_ROOT]

set -euo pipefail

ICLOUD="${1:-$HOME/Library/Mobile Documents/com~apple~CloudDocs/Documents/Documents - Mac/repos/unified-trading-system-repos}"
CODE="${2:-$HOME/Code/unified-trading-system-repos}"

# All manifest repos (except root-level files)
REPOS=(alerting-service archive batch-audit-ui client-reporting-api client-reporting-ui
  deployment-api deployment-service deployment-ui execution-algo-library execution-analytics-ui
  execution-results-api execution-service features-calendar-service features-cross-instrument-service
  features-delta-one-service features-multi-timeframe-service features-onchain-service
  features-sports-service features-volatility-service ibkr-gateway-infra instruments-service
  market-tick-data-service matching-engine-library ml-inference-service ml-training-service
  ml-training-ui onboarding-ui pnl-attribution-service position-balance-monitor-service
  risk-and-exposure-service settlement-ui strategy-service strategy-ui
  system-integration-tests trading-analytics-ui unified-api-contracts unified-cloud-interface
  unified-config-interface unified-defi-execution-interface unified-domain-client
  unified-trading-library unified-feature-calculator-library unified-internal-contracts
  unified-market-interface unified-ml-interface unified-position-interface
  unified-reference-data-interface unified-sports-execution-interface unified-trade-execution-interface
  unified-trading-codex unified-trading-library unified-trading-pm
  unified-trading-ui-auth execution-analytics-ui)

for repo in "${REPOS[@]}"; do
  src="$ICLOUD/$repo"
  if [[ ! -e "$src" ]]; then continue; fi
  if [[ -L "$src" ]]; then
    echo "Already symlinked: $repo"
    continue
  fi
  if [[ ! -d "$CODE/$repo" ]]; then
    echo "Skip (no Code copy): $repo"
    continue
  fi
  echo "Symlinking: $repo"
  rm -rf "$src"
  ln -s "$CODE/$repo" "$src"
done

echo "Done. Verify with: ls -la $ICLOUD"
