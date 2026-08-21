---
doc_type: plan
title: defi-dev-testnet-data-rollout-2026-03-13
summary: 'DeFi dev environment rollout: real market data (batch + live from mainnet), simulated orders via mainnet fork
  (Anvil/Tenderly) or Hyperliquid testnet, VCR cassette recording for all DeFi venues, position routing through fork RPC
  so UPI/risk/strategy work unchanged. Venue-by-venue matrix SSOT in unified-api-contracts. Dev infra uses same GCP project
  (central-element-323112) with -dev annotated resources via Terraform.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-13'
todos:
- {id: create-defi-venue-matrix, content: 'Create unified-api-contracts/docs/DEFI_DATA_ORDER_STRATEGY_MATRIX.md — per-venue SSOT for market data source, dev order routing (Anvil fork / Tenderly fork / Hyperliquid testnet), VCR cassette targets, and Sepolia caveats. Referenced by elysium-defi-system and unified-defi-execution-interface READMEs.', status: pending}
- {id: create-dev-environment-doc, content: 'Create deployment-service/docs/dev-environment.md — canonical dev infra provisioning guide. Content: `terraform apply -var="environment=dev" -var="project_id=central-element-323112"` as the single SSOT for how dev GCS buckets, Pub/Sub topics, Scheduler jobs are created. Replaces the retired setup-dev-*.sh scripts.', status: pending}
- {id: retire-setup-dev-scripts, content: 'Add RETIRED header to three scripts in unified-trading-pm/scripts/dev/: setup-dev-bigquery.sh, setup-dev-pubsub.sh, seed-dev-project.sh. Header: "RETIRED 2026-03-13 — use deployment-service/terraform with environment=dev. See deployment-service/docs/dev-environment.md". Do NOT delete (git history); just header comment.', status: pending}
- {id: update-dev-onboarding-plan, content: 'Update unified-trading-pm/plans/active/ai/dev_environment_automated_onboarding_2026_03_10.md: (1) Remove seed-dev-project.sh step 8 from the setup script; (2) Change all GCP_PROJECT_ID references from unified-trading-dev to central-element-323112; (3) Note that setup-dev-*.sh scripts are retired; (4) Add step: terraform apply -var=environment=dev as canonical dev provisioning.', status: pending}
- {id: update-api-keys-plan-defi, content: 'Update unified-trading-pm/plans/ai/api_keys_and_auth.md — add DeFi VCR todos: thegraph_aave, thegraph_morpho, thegraph_uniswap_v3, alchemy_eth_call, defillama_tvl, defillama_yields. Add SM gap entries: alchemy-api-key-testnet (Sepolia RPC), tenderly-fork-rpc-url, hyperliquid-testnet-api-credentials, wallet-dev-private-key.', status: pending}
- {id: update-ssot-index, content: 'Update unified-trading-codex/00-SSOT-INDEX.md: (1) Add new row for this plan (defi_dev_testnet_data_rollout_2026_03_13); (2) Update Plan #52 (mock_data_dev_project_seeding) description to note "RETIRED — superseded by Terraform environment=dev"; (3) Update Plan #88 (dev_environment_automated_onboarding) description to note Terraform as canonical provisioning path.', status: pending}
- {id: add-fork-testnet-config, content: 'Add FORK_MODE and TESTNET_MODE fields to unified-config-interface/unified_config_interface/cloud_config.py. FORK_MODE: str = Field(default="", alias="FORK_MODE") — values: "anvil", "tenderly", "". TESTNET_MODE: bool = Field(default=False, alias="TESTNET_MODE"). DEFI_RPC_URL: str | None = Field(default=None, alias="DEFI_RPC_URL") — override for direct URL injection.', status: pending}
- {id: add-secret-names, content: 'Add to unified-cloud-interface/unified_cloud_interface/credentials_registry.py: alchemy_testnet_secret = "alchemy-api-key-testnet", tenderly_fork_rpc_secret = "tenderly-fork-rpc-url", tenderly_api_key_secret = "tenderly-api-key", hyperliquid_testnet_secret = "hyperliquid-testnet-api-credentials", wallet_dev_private_key_secret = "wallet-dev-private-key".', status: pending}
- {id: add-rpc-routing, content: 'Add get_defi_rpc_url() and get_hyperliquid_api_url() to unified-defi-execution-interface/unified_defi_execution_interface/protocols/base.py. get_defi_rpc_url(): if FORK_MODE=anvil → http://localhost:8545; if FORK_MODE=tenderly → SM secret; else → mainnet Alchemy URL. get_hyperliquid_api_url(): if TESTNET_MODE → testnet URL; else → mainnet. DEFI_RPC_URL env var overrides everything (for local override without SM). CRITICAL GUARD (2026-03-13 audit): Add production safety check — if FORK_MODE is empty/unset (production) AND DEFI_RPC_URL is set, FAIL LOUD: if not config.fork_mode and config.defi_rpc_url: raise RuntimeError( ''DEFI_RPC_URL is set but FORK_MODE is empty — this would route production DeFi '' ''trades to an override URL. Remove DEFI_RPC_URL or set FORK_MODE explicitly.'' ) This prevents accidental routing of live DeFi trades to a local Anvil fork or stale Tenderly URL due to a leftover env var.', status: pending}
- {id: wire-upi-defi-rpc, content: 'Wire get_defi_rpc_url() into unified-position-interface DeFi adapters (Aave, Morpho, Uniswap). Each adapter''s _build_w3() or equivalent Web3 constructor must call get_defi_rpc_url() instead of hardcoded/config Alchemy URL. This makes UPI read positions from the fork in FORK_MODE. Import get_defi_rpc_url from unified-defi-execution-interface/protocols/base.py OR move to UCI/UTL shared.', status: pending}
- {id: implement-defi-handlers, content: 'Implement 5 Phase 2 stub handlers in elysium-defi-system/src/execution/handlers/: StakeHandler → LidoConnector.submit() / EtherFiConnector.deposit(); LendHandler → AaveConnector.supply() / MorphoConnector.deposit(); BorrowHandler → AaveConnector.borrow(); SwapHandler → UniswapConnector.swap(); FlashLoanHandler → AaveConnector.flashLoan(). All use get_defi_rpc_url() for chain access. All stub-safe (dry-run log when FORK_MODE="").', status: pending}
- {id: add-defi-vcr-entries, content: 'Add DeFi entries to unified-api-contracts/unified_api_contracts/vcr_endpoints.py: thegraph_aave (POST GraphQL gateway), thegraph_morpho (POST free subgraph), thegraph_uniswap_v3 (POST), thegraph_uniswap_v4 (POST gateway), thegraph_instadapp (POST), thegraph_balancer (POST api-v3.balancer.fi), alchemy_eth_call (POST JSON-RPC), alchemy_eth_getlogs (POST JSON-RPC), aavescan (GET), defillama_tvl (GET), defillama_yields (GET), hyperliquid_testnet_rest (POST). Pattern: follow existing _post()/_get() helpers. key_env=THE_GRAPH_API_KEY / ALCHEMY_API_KEY where applicable.', status: pending}
- {id: update-dev-env-vars-doc, content: 'Update unified-trading-pm/docs/dev-environment-vars.md — add new variables: FORK_MODE=anvil|tenderly|"" (default ""), TESTNET_MODE=false (default false — only true for Hyperliquid testnet), DEFI_RPC_URL=<override> (optional; bypasses SM lookup for local Anvil), TENDERLY_FORK_RPC_URL=<tenderly virtual testnet URL> (for Tenderly mode). Also update GCP_PROJECT_ID reference from unified-trading-dev to central-element-323112.', status: pending}
- {id: human-alchemy-testnet-key, content: '[HUMAN] Create Alchemy Sepolia app at dashboard.alchemy.com → add secret alchemy-api-key-testnet to SM central-element-323112. Needed for Sepolia tx-mechanics testing only.', status: pending}
- {id: human-hyperliquid-testnet, content: '[HUMAN] Create Hyperliquid testnet account at testnet.hyperliquid.xyz → add hyperliquid-testnet-api-credentials JSON to SM central-element-323112. Needed for order placement tests.', status: pending}
- {id: human-tenderly, content: '[HUMAN] Create Tenderly account at app.tenderly.co (free tier) → add tenderly-api-key and tenderly-fork-rpc-url to SM central-element-323112. Needed for dev Cloud Run fork simulation. Free tier: 50 txns/day. Anvil covers local dev without Tenderly.', status: pending}
- {id: human-dev-wallet, content: '[HUMAN] Generate a fresh dev wallet private key (e.g. cast wallet new) → add as wallet-dev-private-key to SM central-element-323112. Fund with Sepolia ETH from sepoliafaucet.com. CRITICAL: never fund this wallet on mainnet.', status: pending}
- {id: human-terraform-dev, content: '[HUMAN] Run: cd deployment-service/terraform/gcp && terraform apply -var="environment=dev" -var="project_id=central-element-323112" This creates all -dev- GCS buckets, Pub/Sub topics, Scheduler jobs in the existing project. Verify: gcloud storage ls gs://*-dev-central-element-323112 shows new buckets.', status: pending}
isProject: false
---

# Plan: DeFi Dev Environment — Testnet, Data, Orders & VCR Rollout

## Context

The system needs a dev environment where the full DeFi trading stack runs with:

- **Real market data** — The Graph, Alchemy, DefiLlama pulling from Ethereum mainnet (read-only, no cost, no risk)
- **Simulated orders** — mainnet fork (Anvil locally, Tenderly for dev Cloud Run) so contract math is real but no
  capital is at risk
- **Accurate positions** — `unified-position-interface` reads from the same fork RPC as execution, so
  risk/exposure/strategy see consistent fork state
- **VCR cassettes** — DeFi HTTP endpoints recorded for CI use without live keys

The core insight: market data is always mainnet (read-only). Only the **RPC URL** for order execution and position
reading changes between prod (mainnet Alchemy) and dev (local Anvil or Tenderly fork). That single URL swap —
implemented in `get_defi_rpc_url()` — makes the entire system E2E testable without touching any downstream service
(risk, strategy, alerting).

Dev infra: same GCP project `central-element-323112`, `-dev` annotated resources via
`terraform apply -var="environment=dev"`. No separate project. The old `setup-dev-*.sh` scripts are retired.

---

## Why Sepolia Testnet Is NOT Recommended for E2E

Sepolia has different contract addresses, fake test-token prices, and synthetic rates. Orders sent to Sepolia Aave
produce positions on chain_id 11155111 — the position monitor would have to read from Sepolia RPC while market data
comes from mainnet (chain_id 1). These are unrelated numbers. **Sepolia is only valid for testing tx
signing/broadcast/event-parsing mechanics**, not for strategy or PnL validation.

Mainnet fork solves this: same chain_id, same addresses, same pool state. Position monitor sees real aUSDC balances,
market data sees real prices, PnL is accurate to fork-block conditions.

---

## Venue Matrix SSOT

See `unified-api-contracts/docs/DEFI_DATA_ORDER_STRATEGY_MATRIX.md` for the per-venue decision table: market data
source, dev order routing, VCR cassette targets, Sepolia availability.

---

## Dev Infra Provisioning SSOT

See `deployment-service/docs/dev-environment.md`. Canonical command:

```bash
cd deployment-service/terraform/gcp
terraform apply -var="environment=dev" -var="project_id=central-element-323112"
```

Creates `-dev-` annotated GCS buckets (Group B), Pub/Sub topics, Scheduler jobs alongside existing `-prod-` resources in
the same project.

---

## RPC Routing Architecture

```
get_defi_rpc_url() in unified-defi-execution-interface/protocols/base.py:

  FORK_MODE=anvil    → http://localhost:8545          (local Anvil fork)
  FORK_MODE=tenderly → SM: tenderly-fork-rpc-url      (hosted fork, dev Cloud Run)
  DEFI_RPC_URL set   → use that URL directly          (local override)
  (default/prod)     → SM: alchemy-api-key mainnet    (real chain)

Both execution and position interfaces call this function.
Downstream services (risk, strategy, alerting) are unchanged.
```

---

## Verification Gates

- `FORK_MODE=anvil pytest elysium-defi-system/tests/integration/test_defi_handlers.py` — all 5 handlers execute against
  Anvil fork, positions readable
- `TESTNET_MODE=true pytest unified-defi-execution-interface/tests/integration/test_hyperliquid_testnet.py` — places +
  cancels testnet order
- `cd unified-api-contracts && pytest tests/test_cassette_schema_parity.py` — new DeFi cassettes pass schema validation
- `pytest --block-network` passes for all DeFi unit tests in VCR playback mode
- `gcloud storage ls | grep "\-dev\-"` — dev GCS buckets exist in central-element-323112
