#!/usr/bin/env bash
# Set GH_PAT repository secret for all unified-trading repos
#
# Usage:
#   # Interactive (prompts for token, never echoes it):
#   bash set-gh-pat-all-repos.sh
#
#   # From stdin (e.g. when rotating token):
#   echo 'YOUR_NEW_TOKEN' | bash set-gh-pat-all-repos.sh
#
#   # Dry-run (list repos only, no secret set):
#   bash set-gh-pat-all-repos.sh --dry-run
#
# Requires: gh CLI authenticated (gh auth login)
#
# Repos included: All repos with quality-gates or workflows that clone private deps.
# Same list as instruments-service setup.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOS=(
  execution-algo-library
  execution-services
  features-calendar-service
  features-delta-one-service
  features-onchain-service
  features-volatility-service
  instruments-service
  live-health-monitor-ui
  market-data-processing-service
  market-tick-data-handler
  ml-inference-service
  ml-training-service
  position-balance-monitor-service
  risk-and-exposure-service
  strategy-service
  unified-trading-services
  unified-config-interface
  unified-events-interface
  unified-market-interface
  unified-order-interface
  unified-trading-codex
  unified-trading-deployment-v2
)

ORG="${GH_ORG:-IggyIkenna}"

dry_run=false
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=true
fi

if [[ "$dry_run" == true ]]; then
  echo "Repos that would receive GH_PAT (${#REPOS[@]} total):"
  for repo in "${REPOS[@]}"; do
    echo "  - $repo"
  done
  echo ""
  echo "Run without --dry-run to set the secret (token from stdin or prompt)."
  exit 0
fi

# Read token from stdin or prompt
if [[ -t 0 ]]; then
  echo "Enter GH_PAT (token will not be echoed):"
  read -rs token
  echo ""
  if [[ -z "${token:-}" ]]; then
    echo "Error: No token provided"
    exit 1
  fi
else
  token="$(cat)"
  if [[ -z "${token:-}" ]]; then
    echo "Error: No token provided via stdin"
    exit 1
  fi
fi

echo "Setting GH_PAT for ${#REPOS[@]} repos in $ORG..."
failed=0
for repo in "${REPOS[@]}"; do
  if echo "$token" | gh secret set GH_PAT --repo="$ORG/$repo" 2>/dev/null; then
    echo "  OK $repo"
  else
    echo "  FAIL $repo"
    ((failed++)) || true
  fi
done

if [[ $failed -gt 0 ]]; then
  echo ""
  echo "Failed for $failed repo(s). Check: gh auth status"
  exit 1
fi

echo ""
echo "GH_PAT set successfully for all ${#REPOS[@]} repos."
