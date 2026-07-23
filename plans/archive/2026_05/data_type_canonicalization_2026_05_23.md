---
doc_type: plan
title: Data Type Canonicalization — Cross-Service Alignment
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-data-processing-service,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-23
last_updated: 2026-05-23
parent_epic: mtds_mdps_master
assigned_vm: vm-cross-cutting
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 1.2
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Data Type Canonicalization — Cross-Service Alignment

## Problem Statement

A cross-service audit (2026-05-23) found that data type string names are **not consistent** across the stack. MTDS
handlers write canonical UAC names to GCS/manifest; the YAML config, downstream service code (features, execution,
MDPS), and MTDS adapters all use old/divergent names. Result: deployment UI data status misses coverage, execution
service reads wrong GCS paths, features service loads from wrong paths.

## Root Cause Summary

Three-way name split for core DeFi types:

| UAC canonical     | venue_data_types.yaml | MTDS adapters  | Features         | Execution         |
| ----------------- | --------------------- | -------------- | ---------------- | ----------------- |
| `dex_swaps`       | `swaps`               | `swaps`        | `swaps`          | `swaps`           |
| `dex_pools`       | `liquidity`           | `liquidity`    | `dex_pool_state` | `liquidity`       |
| `lending_indices` | `rate_indices`        | `rate_indices` | `rate_indices`   | `lending_indices` |

Additional issues:

- MDPS scanner uses `mev_bundles`/`bridge_flows`/`flash_loans` instead of
  `mev_events`/`bridge_events`/`flash_loan_events`
- Legacy retired prediction types still in `_PER_INSTRUMENT_SHARD_DATA_TYPES`
- Missing DeFi types in venue_data_types.yaml (perp_funding, lst_rates, gas_fees, eigenlayer_rewards, vault_share_price,
  native_staking_rates, utilization, flash_loan_availability, vault_apy, vault_tvl)
- Prediction category entirely absent from venue_data_types.yaml
- TradFi reference types in YAML but not UAC
- deployment-api can't find venue_data_types.yaml (wrong path)
- Strategy script uses `"perp-funding"` hyphen form

## Codex SSOTs

- `/codex/02-data/contracts-scope-and-layout.md`
- `/codex/02-data/honest-absence-downstream-handling.md`
- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`

## Full Execution Criterion

All data types written to GCS by MTDS appear under the same canonical name in:

1. UAC `DATA_TYPES_BY_ASSET_GROUP`
2. `venue_data_types.yaml` (all 3 copies in sync)
3. MTDS adapter `SUPPORTED_DATA_TYPES` / `_default_data_types()`
4. Features service data type references
5. Execution service data type references
6. Deployment UI data status (visible via path_combinatorics loading YAML)

Verification: `grep -r "swaps\|liquidity\|rate_indices\|mev_bundles\|bridge_flows\|flash_loans\|perp-funding"` across
all service repos returns zero hits in non-test Python source.

---

## Phase 1 — UAC: Canonical source fixes [P0]

- [x] [SCRIPT] P0. Remove retired prediction types from `_PER_INSTRUMENT_SHARD_DATA_TYPES`: `prediction_trades`,
      `prediction_book_snapshot`, `prediction_market_metadata` — unified-api-contracts
- [x] [SCRIPT] P0. Add missing DeFi types to `DATA_TYPES_BY_ASSET_GROUP["defi"]`: `utilization`,
      `flash_loan_availability`, `vault_apy`, `vault_tvl` — unified-api-contracts
- [x] [SCRIPT] P0. Add TradFi reference types to `DATA_TYPES_BY_ASSET_GROUP["tradfi"]`: `corporate_action_confirmed`,
      `earnings_result`, `macro_result` — unified-api-contracts
- [x] [SCRIPT] P0. Add Sports YAML types to `DATA_TYPES_BY_ASSET_GROUP["sports"]`: `markets`, `outcomes`, `settlements`
      — unified-api-contracts
- [x] [SCRIPT] P0. Update `BASE_GRANULARITY_BY_DATA_TYPE` and `NEEDS_CANDLE_PROCESSING` for all new types —
      unified-api-contracts

## Phase 2 — venue_data_types.yaml: Config fixes [P0]

- [x] [SCRIPT] P0. Rename DeFi: `swaps`→`dex_swaps`, `liquidity`→`dex_pools`, `rate_indices`→`lending_indices` in YAML
      (all 3 copies) — deployment-service, unified-trading-pm, market-tick-data-service
- [x] [SCRIPT] P0. Add missing DeFi venue entries: perp_funding (HYPERLIQUID, ASTER), lst_rates, gas_fees,
      eigenlayer_rewards, vault_share_price, native_staking_rates, utilization, flash_loan_availability —
      deployment-service
- [x] [SCRIPT] P0. Add Sports processed data types to YAML: `odds_snapshot`, `odds_movement`, `arbitrage_opportunity`,
      `odds_horizon_bucket` — deployment-service
- [x] [SCRIPT] P0. Add Prediction category section to YAML — deployment-service
- [x] [SCRIPT] P0. Fix deployment-api path_combinatorics.py: `"configs"` → `"pm-configs"` so YAML loads at runtime —
      deployment-api

## Phase 3 — MTDS adapters: Old name fixes [P0]

- [x] [SCRIPT] P0. uniswapv2_adapter.py: `swaps`→`dex_swaps`, `liquidity`→`dex_pools` — market-tick-data-service
- [x] [SCRIPT] P0. uniswap_v3_adapter.py: same — market-tick-data-service
- [x] [SCRIPT] P0. uniswapv4_adapter.py: same — market-tick-data-service
- [x] [SCRIPT] P0. curve_adapter.py: same — market-tick-data-service
- [x] [SCRIPT] P0. balancer_adapter.py: same — market-tick-data-service
- [x] [SCRIPT] P0. morpho_adapter.py: `rate_indices`→`lending_indices` — market-tick-data-service
- [x] [SCRIPT] P0. base_defi_adapter.py: `rate_indices`→`lending_indices` — market-tick-data-service
- [x] [SCRIPT] P0. fluid_adapter.py: `rate_indices`→`lending_indices` — market-tick-data-service
- [x] [SCRIPT] P0. aave_positions.py: `rate_indices`→`lending_indices` — market-tick-data-service

## Phase 4 — MDPS scanner: Event type name fixes [P1]

- [x] [SCRIPT] P1. orchestration_scanner.py: `mev_bundles`→`mev_events`, `bridge_flows`→`bridge_events`,
      `flash_loans`→`flash_loan_events` — market-data-processing-service

## Phase 5 — Features service: Old name fixes [P0]

- [x] [SCRIPT] P0. delta_one/engine/orchestrator.py: `swaps`→`dex_swaps` in `DEFI_DATA_TYPE_OVERRIDES` —
      features-service
- [x] [SCRIPT] P0. delta_one/app/core/dependency_checker.py: `"swaps"`→`"dex_swaps"` in candle path check —
      features-service
- [x] [SCRIPT] P0. onchain/app/core/mtds_output_config.py: `rate_indices`→`lending_indices` as bypass key —
      features-service

## Phase 6 — Execution service: Old name fixes [P0]

- [x] [SCRIPT] P0. utils/instrument_resolver.py: `data_type=swaps`→`data_type=dex_swaps` in GCS paths —
      execution-service
- [x] [SCRIPT] P0. cli/multi_leg_config_gcs.py: `data_type=swaps`→`data_type=dex_swaps` — execution-service
- [x] [SCRIPT] P0. engine/validation/catalog_validator.py: AMM `["swaps", "liquidity"]`→`["dex_swaps", "dex_pools"]` —
      execution-service
- [x] [SCRIPT] P0. engine/validation/data_availability_validator.py: same — execution-service

## Phase 7 — Strategy script fix [P1]

- [x] [SCRIPT] P1. scripts/probe_funding_rate_dispersion_coverage.py: remove `"perp-funding"` hyphen form —
      strategy-service

## Phase 8 — Regression tests [P1]

- [x] [TEST] P1. UAC test: validate all venue_data_types.yaml data_types appear in DATA_TYPES_BY_ASSET_GROUP —
      unified-api-contracts
- [x] [TEST] P1. MTDS test: validate adapter SUPPORTED_DATA_TYPES all appear in UAC DATA_TYPES_BY_ASSET_GROUP —
      market-tick-data-service
- [x] [TEST] P1. Execution test: validate AMM book_type_requirements keys match UAC canonical names — execution-service

## Phase 9 — GCS partition rename: dex_pool_state → dex_pools [P2]

- [x] ✅ DEFERRED [GCS-MIGRATION-WINDOW: must bundle with next scheduled GCS migration window per single-walk
      discipline] [SCRIPT] P2. **DEFERRED** — Rename on-disk GCS hive partition segment `data_type=dex_pool_state` →
      `data_type=dex_pools` so the physical path matches the UAC canonical name. Must bundle into next scheduled GCS
      migration window (single-walk discipline — no standalone walk). Pre-migration drain REQUIRED (stop all DeFi MTDS
      VMs + run manifest consolidator before walk). After rename: remove `dex_pools`→`dex_pool_state` path-override
      mapping from `features-service/onchain/app/core/mtds_output_config.py` and update features-service parquet path
      resolution. Successor to archived `gcs_migration_bundle_pipeline_mode_2026_05_08.md`. — market-tick-data-service,
      features-service, unified-trading-pm

## Phase 10 — Remaining stale names found in 2026-05-24 audit [P0]

- [x] [SCRIPT] P0. engine/backtest/data_loader.py: `data_type == "swaps"`→`"dex_swaps"` — execution-service@c82f34825
- [x] [SCRIPT] P0. registry/processed_data_dependencies.py: remove stale `"rate_indices": "rate_ohlcv"` alias (canonical
      `"lending_indices": "lending_ohlcv"` already present on line 31) — unified-api-contracts@954ff6d3
- [x] [SCRIPT] P0. domain/validation.py `DATA_TYPE_SCHEMAS`: `"swaps"`→`"dex_swaps"`, `"liquidity"`→`"dex_pools"`,
      `"rate_indices"`→`"lending_indices"` — unified-trading-library@c63bb3ca
- [x] [SCRIPT] P0. schemas/domain/market_data_processing/candle_schema.py `DataType` enum:
      `SWAPS="swaps"`→`DEX_SWAPS="dex_swaps"`, `RATE_INDICES="rate_indices"`→`LENDING_INDICES="lending_indices"` —
      unified-trading-system-ui@79d3915d (Python-only; playwright gate does not apply)
- [x] [SCRIPT] P0. schemas/output_schemas.py `RATE_INDEX_SCHEMA`: `name="rate_indices"`→`name="lending_indices"` —
      market-data-processing-service@fa9d912
- [x] [SCRIPT] P0. scripts/seed_mock_data.py: `"rate_indices"`→`"lending_indices"` (4+ occurrences, function
      `_build_rate_indices_df` renamed to `_build_lending_indices_df`) — market-data-processing-service@fa9d912
- [x] [SCRIPT] P1. Codex docs audit: fix stale DeFi data type names across 4 codex docs (`pipeline-coverage-matrix.md`,
      `availability-manifest-and-data-status.md`, `partitioning.md`, `PARSER_FIXES_AND_BOOK_SNAPSHOT_CLARIFICATION.md`)
      — unified-trading-pm@c1687646f Intentional non-changes: TradFi `rate_indices` (distinct domain); AMM simulation
      `"liquidity"` field (pool state JSON payload, not data_type name).

## Temporary states + their canonical follow-up plans

- `dex_pool_state` on-disk GCS path segment for `dex_pools`: intentional legacy — GCS data is NOT re-keyed per
  single-walk discipline. Feature service mtds_output_config.py maintains the `dex_pools`→`dex_pool_state` path mapping.
  Named successor: Phase 9 above (this plan).

## Completion evidence (2026-05-23)

All 8 phases shipped and pushed to `live-defi-rollout`:

| Repo                               | SHA       |
| ---------------------------------- | --------- |
| unified-api-contracts              | 136e8623  |
| market-tick-data-service           | 16402c95  |
| execution-service                  | 091e0b21e |
| features-service                   | 6f662a6a  |
| market-data-processing-service     | e4309d8   |
| unified-trading-pm (config + plan) | 728578f70 |

UAC has two commits: `7511207a` (registry + prediction types) and `136e8623` (features/required_inputs.py
`liquidity`→`dex_pools` fix found in final verification grep). HEAD = `136e8623`.

QG status: execution-service — 3 pre-existing unrelated failures (orchestrator, config, coverage-gaps); MTDS — 37
pre-existing failures (native-staking, solana-defi, websocket streaming — all pre-date this PR); UAC cassette failures
pre-existing. New regression tests: all green.

## Codex SSOT updates

- Update `/codex/02-data/contracts-scope-and-layout.md` after Phase 1 (new UAC types section)
- No codex doc invalidated — this is additive + rename only
