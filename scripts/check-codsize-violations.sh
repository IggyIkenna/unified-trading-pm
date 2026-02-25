#!/bin/bash
# Check COD-SIZE violations across all repos (files >1500 lines)
# Usage: bash check-codsize-violations.sh [--threshold LINES] [--repos "repo1 repo2"]

set -euo pipefail

# Navigate to workspace root (script is in unified-trading-codex/one-time-scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$WORKSPACE_ROOT"

THRESHOLD=1500
REPOS=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --threshold)
      THRESHOLD="$2"
      shift 2
      ;;
    --repos)
      REPOS="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--threshold LINES] [--repos 'repo1 repo2']"
      exit 1
      ;;
  esac
done

# Default to all repos if not specified
if [ -z "$REPOS" ]; then
  REPOS=(
    "instruments-service"
    "unified-cloud-services"
    "features-delta-one-service"
    "features-volatility-service"
    "features-calendar-service"
    "features-onchain-service"
    "features-sports-service"
    "ml-training-service"
    "ml-inference-service"
    "strategy-service"
    "execution-services"
    "unified-trading-deployment-v3"
    "unified-trading-codex"
    "market-tick-data-handler"
    "market-data-processing-service"
    "reconciliation-service"
    "pnl-attribution-service"
    "position-balance-monitor-service"
    "risk-monitor-service"
    "alerting-system"
    "exchange-interface-library"
    "live-health-monitor-ui"
    "batch-audit-ui"
    "logs-dashboard-ui"
    "ml-deployment-ui"
    "backtest-ui"
    "trading-analytics-ui"
    "settlement-ui"
    "client-reporting-ui"
    "corporate-actions"
  )
else
  # Split repos string into array
  IFS=' ' read -ra REPOS <<< "$REPOS"
fi

echo "=== COD-SIZE Violation Scanner ==="
echo "Threshold: $THRESHOLD lines"
echo "Repos to scan: ${#REPOS[@]}"
echo "Workspace root: $WORKSPACE_ROOT"
echo ""

total_violations=0
repos_with_violations=0
violation_list=""

for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo" ]; then
    continue
  fi

  # Find Python files exceeding threshold (excluding tests, scripts)
  violations=$(find "$repo" -name "*.py" -type f \
    ! -path "*/tests/*" \
    ! -path "*/scripts/*" \
    ! -path "*/.venv/*" \
    ! -path "*/node_modules/*" \
    ! -path "*/__pycache__/*" \
    ! -path "*/build/*" \
    ! -path "*/dist/*" \
    ! -path "*/htmlcov/*" \
    -exec wc -l {} \; 2>/dev/null | \
    awk -v thresh="$THRESHOLD" '$1 > thresh {printf "%4d lines: %s\n", $1, $2}' | \
    sort -rn)

  if [ -n "$violations" ]; then
    count=$(echo "$violations" | wc -l | tr -d ' ')
    total_violations=$((total_violations + count))
    repos_with_violations=$((repos_with_violations + 1))
    violation_list="$violation_list  - $repo: $count files\n"

    echo "=== $repo ==="
    echo "❌ $count files exceed $THRESHOLD lines:"
    echo "$violations"
    echo ""
  fi
done

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
