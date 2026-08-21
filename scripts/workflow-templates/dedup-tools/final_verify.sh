#!/usr/bin/env bash
# Epic: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06
# Lifecycle: temporary
# Delete-when: fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md todo 9 ships
#
# Post-shipment sweep: directly reads each repo's origin/live-defi-rollout content (never
# trusts quickmerge's own success message -- see ship_repo.sh's header for why). REPOS/FILES
# below are todo-4's exact carrier list as of 2026-08-07 -- update both for todo 5's own
# carrier list (semver-agent.yml.tmpl's distribution per todo 1's findings) before reusing.
set -uo pipefail
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1

REPOS="agent-orchestrator alerting-service batch-live-reconciliation-service client-reporting-api deployment-api deployment-service deployment-ui e2e-testing execution-service features-service fund-administration-service greeks-service ibkr-gateway-infra instruments-service market-data-processing-service market-tick-data-service ml-service strategy-service system-integration-tests trading-agent-service unified-api-contracts unified-trading-api unified-trading-library unified-trading-system-ui"
FILES="main-backmerge-to-ldr.yml major-bump-issue-handler.yml request-major-bump.yml staging-backmerge-to-ldr.yml update-dependency-version.yml"
FAIL=0

for r in $REPOS; do
  ( cd "$r" && git fetch origin -q ) 2>/dev/null
  for f in $FILES; do
    content=$( cd "$r" && git show "origin/live-defi-rollout:.github/workflows/$f" 2>/dev/null )
    if [ -z "$content" ]; then
      echo "MISSING: $r/$f"
      FAIL=$((FAIL+1))
    elif ! printf '%s' "$content" | grep -q "uses: IggyIkenna/unified-trading-ci"; then
      echo "NOT CONVERTED: $r/$f"
      FAIL=$((FAIL+1))
    fi
  done
done

echo "=== PM (main-backmerge-to-ldr.yml only) ==="
( cd unified-trading-pm && git fetch origin -q )
pmcontent=$( cd unified-trading-pm && git show origin/live-defi-rollout:.github/workflows/main-backmerge-to-ldr.yml 2>/dev/null )
if ! printf '%s' "$pmcontent" | grep -q "uses: IggyIkenna/unified-trading-ci"; then
  echo "PM NOT CONVERTED"
  FAIL=$((FAIL+1))
fi

echo "=== trading-agent-service version-registry-notify.yml (todo 3) ==="
tascontent=$( cd trading-agent-service && git show origin/live-defi-rollout:.github/workflows/version-registry-notify.yml 2>/dev/null )
if ! printf '%s' "$tascontent" | grep -q "uses: IggyIkenna/unified-trading-ci"; then
  echo "todo-3 canary regressed"
  FAIL=$((FAIL+1))
fi

echo "TOTAL FAILURES: $FAIL"
