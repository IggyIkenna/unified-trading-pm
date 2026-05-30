#!/usr/bin/env bash
# import.sh — generate `terraform import` commands for the EXISTING rulesets so adopting
# this module does NOT recreate them (which would briefly drop branch protection).
#
# github_repository_ruleset import id format: "<repository>:<ruleset_id>".
# Run from this directory after `terraform init`. Prints commands; pipe to sh to execute:
#   bash import.sh            # print
#   bash import.sh | sh       # execute
set -euo pipefail
ORG="${GITHUB_OWNER:-IggyIkenna}"

repos=(
  alerting-service batch-live-reconciliation-service client-reporting-api
  deployment-api deployment-service deployment-ui execution-service ibkr-gateway-infra
  instruments-service market-data-processing-service market-tick-data-service strategy-service
  system-integration-tests trading-agent-service unified-api-contracts unified-trading-library
  unified-trading-pm
)

for repo in "${repos[@]}"; do
  while IFS=$'\t' read -r name id; do
    case "$name" in
      require-quality-gates)
        echo "terraform import 'github_repository_ruleset.require_quality_gates[\"${repo}\"]' '${repo}:${id}'"
        ;;
      require-staging-lock-check)
        [ "$repo" = "unified-trading-pm" ] && continue
        echo "terraform import 'github_repository_ruleset.require_staging_lock_check[\"${repo}\"]' '${repo}:${id}'"
        ;;
    esac
  done < <(gh api "repos/${ORG}/${repo}/rulesets" --jq '.[] | select(.target=="branch") | "\(.name)\t\(.id)"' 2>/dev/null)
done
