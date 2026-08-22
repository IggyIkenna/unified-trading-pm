#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# provision-defi-testnet.sh — Stub documenting what Terraform would need for DeFi testnet infra.
#
# SSOT: unified-trading-pm/codex/02-data/defi-venue-protocol-catalogue.md (venue + testnet details, folded 2026-07-27)
# Plan: deploy-defi-testnet task in live-defi-rollout
#
# This script is a placeholder. Actual provisioning is done via Terraform in
# deployment-service/terraform/gcp/ and deployment-service/terraform/aws/.
#
# What Terraform would provision for DeFi testnet:
#
#   1. VPC + Subnet
#      - Dedicated VPC for testnet RPC traffic (isolated from mainnet)
#      - Private subnet with NAT gateway for outbound RPC calls
#
#   2. VM / Cloud Run instances
#      - market-tick-data-service DeFi adapter instances (testnet feeds)
#
#   3. Secret Manager entries
#      - TESTNET_RPC_URL_SEPOLIA    (Sepolia Ethereum testnet)
#      - TESTNET_RPC_URL_HOLESKY    (Holesky for staking protocols)
#      - TESTNET_RPC_URL_ARB_SEPOLIA (Arbitrum Sepolia for Hyperliquid)
#      - TESTNET_WALLET_ADDRESS      (funded testnet wallet)
#      - TESTNET_PRIVATE_KEY         (testnet-only signing key)
#
#   4. GCS buckets (testnet data sinks)
#      - ${PROJECT_ID}-defi-testnet-market-data
#      - ${PROJECT_ID}-defi-testnet-execution-logs
#      - ${PROJECT_ID}-defi-testnet-positions
#
#   5. PubSub topics (testnet event bus)
#      - defi-testnet-trades
#      - defi-testnet-positions
#      - defi-testnet-alerts
#
#   6. BigQuery dataset
#      - defi_testnet (for testnet analytics)
#
#   7. Monitoring
#      - Testnet health dashboard (separate from prod)
#      - Alert on testnet wallet balance < 0.1 ETH
#
# Testnet RPC endpoints (from codex/02-data/defi-venue-protocol-catalogue.md):
#   Sepolia:          https://rpc.sepolia.org
#   Holesky:          https://rpc.holesky.ethpandaops.io
#   Arbitrum Sepolia: https://sepolia-rollup.arbitrum.io/rpc
#
# Usage:
#   This is documentation only. For actual provisioning:
#     cd deployment-service/terraform/gcp
#     terraform apply -var="environment=testnet" -var="project_id=${PROJECT_ID}"

set -euo pipefail

echo "provision-defi-testnet.sh is a documentation stub."
echo ""
echo "To provision DeFi testnet infrastructure:"
echo "  cd deployment-service/terraform/gcp"
echo "  terraform apply -var=\"environment=testnet\" -var=\"project_id=\${PROJECT_ID}\""
echo ""
echo "See: unified-trading-pm/codex/02-data/defi-venue-protocol-catalogue.md for venue details."
echo "See: deployment-service/docs/dev-environment.md for Terraform usage."
exit 0
