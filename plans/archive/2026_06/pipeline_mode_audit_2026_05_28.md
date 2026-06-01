---
name: pipeline_mode_audit
title: "pipeline_mode implementation audit — current state and derivation table"
parent_epic: batch_live_symmetry_master
parent: pipeline_mode_implementation_2026_05_28
priority: P2
status: active
model_tier: opus-required
thinking_tier: high
created: 2026-05-28
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
locked_by: live-defi-rollout
locked_since: 2026-05-28
---

# pipeline_mode Implementation Audit

> **✅ COMPLETE — ARCHIVED 2026-06-01.** Audit delivered the derivation table that drove
> `pipeline_mode_implementation_2026_05_28` (shipped: column-fill + 43.5M-row backfill + reconciliation consumer + QG
> STEP 5.85). This is the audit half of the audit→implementation pair; both close together.
>
> ## Deferred work — migrated to:
>
> - None. (The on-disk partition deferral lives on the implementation plan, not this audit.)

Comprehensive audit of `pipeline_mode` usage workspace-wide, supporting the implementation in
`pipeline_mode_implementation_2026_05_28.md`.

## Executive Summary

**Current state**: `PipelineMode` is already a typed StrEnum in UAC with 27 batch values + 1 live value, properly
exported in the public facade. However, the column is currently **NULL/empty on all ~38M manifest rows** despite
function signatures threading it through ~50+ files.

**Key finding**: The infrastructure exists (schema, enum, function args) but writers are not populating the value — it's
passed but not persisted.

## Phase 0 Audit Results

### (a) Manifest Writer Call-Sites

Analysis of 331 files containing `pipeline_mode` references reveals the following writer patterns:

#### MTDS Writers

- **Live streaming**: `market_tick_data_service/live/websocket_runner.py` — defaults to `PipelineMode.LIVE_WEBSOCKET`
- **Batch handlers**: 26 handler files in `market_tick_data_service/cli/handlers/`:
  - `dex_pools_handler.py`, `dex_swaps_handler.py`, `lending_indices_handler.py`
  - `liquidation_events_handler.py`, `liquidations_handler.py`, `lst_rates_handler.py`
  - `perp_funding_handler.py`, `position_data_handler.py`, `staking_yields_handler.py`
  - `oracle_prices_handler.py`, `gas_fee_handler.py`, `vault_share_price_handler.py`
  - `token_transfers_handler.py`, `native_staking_handler.py`, `mev_events_handler.py`
  - `protocol_outage_detector_handler.py`, `eigenlayer_rewards_handler.py`
  - `flash_loan_events_handler.py`, `governance_events_handler.py`, `governance_proposals_handler.py`
  - `aggregator_route_handler.py`, `bridge_events_handler.py`
  - `evm_defi_handler.py`, `solana_defi_handler.py`
  - `websocket_streaming_handler.py` (batch variant)
  - `data_manifest_handler.py`

#### Instruments-Service Writers

- `instruments_service/engine/orchestrator.py`
- Scripts: `aggregate_processed_options_to_chain_bundle.py`, `backfill_sports_per_entity_manifest.py`
- `full_polymarket_dump.py` — explicitly uses `PipelineMode.BATCH_POLYMARKET_GAMMA_API`

#### Features-Service Writers

- `features_service/volatility/cli/handlers/batch_handler.py`
- `features_service/cross_instrument/cli/handlers/batch_handler.py`
- `features_service/commodity/cli/handlers/batch_handler.py`
- `features_service/calendar/engine/calendar_orchestrator.py`

#### Strategy/Execution Service Writers

- `strategy_service/cli/handlers/batch_handler.py`
- (Execution-service appears to consume but not write manifest rows)

#### MDPS Writers

- `market_data_processing_service/app/core/`:
  - `canonical_writer.py`, `candle_write_mixin.py`
  - `orchestration_writer.py`, `orchestration_service.py`
  - `batch_workers.py`, `live_workers.py`

### (b) Readers/Consumers

#### Primary Consumers

1. **batch-live-reconciliation-service**: `stage0_manifest_reason_check.py`
   - Currently checks for `pipeline_mode` column presence
   - Falls back to absent if column missing or all NULL
   - Would GROUP BY pipeline_mode if values existed

2. **deployment-ui**: `src/api/client.ts`
   - Data status views could surface pipeline_mode
   - Currently not displayed as it's always NULL

3. **deployment-api**:
   - `deployment_api/services/shard_detail.py`
   - `deployment_api/routes/data_status.py`

### (c) Function-Arg Threading

The `pipeline_mode` argument is threaded through:

- **UTL ManifestWriter**: `record_captured()` accepts `pipeline_mode: PipelineMode` kwarg
- **UTL ManifestWriterNormalising**: explicitly requires `pipeline_mode` parameter
- **UTL streaming**: `parallel_per_symbol_runner.py`
- **UTL migrations**: `upgrade_manifest_to_v8.py` added the column

### (d) Current GROUP BY Consumers

Currently **zero effective GROUP BY pipeline_mode** consumers because the column is always NULL. However, these are
designed to use it:

- `batch-live-reconciliation-service/stage0_manifest_reason_check.py` — checks by mode when present
- Future: deployment-ui drilldowns, instrument catalogue matrices

## Derivation Table

Based on UAC `PipelineMode` enum members and workspace patterns:

### (asset_group, venue, service_name, written_at) → pipeline_mode

| asset_group    | venue                                                                             | service_name                                 | pipeline_mode                                           |
| -------------- | --------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------- |
| **cefi**       | binance, bybit, okx, deribit, kraken, gate, huobi, kucoin, mexc, bitget, coinbase | market-tick-data-service (batch)             | `batch_tardis`                                          |
| cefi           | hyperliquid                                                                       | market-tick-data-service (batch)             | `batch_hyperliquid_rest`                                |
| cefi           | databento sources                                                                 | market-tick-data-service (batch)             | `batch_databento`                                       |
| cefi           | any                                                                               | market-tick-data-service (live)              | `live_websocket`                                        |
| **defi**       | uniswap, curve, balancer, sushi, pancakeswap                                      | market-tick-data-service (batch)             | `batch_onchain_subgraph`                                |
| defi           | aave, compound                                                                    | market-tick-data-service (batch)             | `batch_onchain_rpc`                                     |
| defi           | chainlink oracles                                                                 | market-tick-data-service (batch)             | `batch_chainlink`                                       |
| defi           | pyth (Solana)                                                                     | market-tick-data-service (batch)             | `batch_pyth_hermes`                                     |
| defi           | solana DEXs (phoenix, orca, raydium, drift)                                       | market-tick-data-service (batch)             | `batch_helius_rpc` or `batch_solana_rpc`                |
| defi           | any                                                                               | market-tick-data-service (live)              | `live_websocket`                                        |
| **tradfi**     | CME, ICE, EUREX, SGX, ASX, JSE                                                    | market-tick-data-service (batch)             | `batch_databento`                                       |
| tradfi         | barchart                                                                          | market-tick-data-service (batch)             | `batch_barchart`                                        |
| tradfi         | yahoo                                                                             | market-tick-data-service (batch)             | `batch_yahoo`                                           |
| tradfi         | eia                                                                               | market-tick-data-service (batch)             | `batch_eia`                                             |
| **sports**     | footystats                                                                        | market-tick-data-service/instruments-service | `batch_footystats`                                      |
| sports         | api_football                                                                      | market-tick-data-service/instruments-service | `batch_api_football`                                    |
| sports         | odds_api                                                                          | market-tick-data-service                     | `batch_odds_api`                                        |
| sports         | open_meteo                                                                        | features-service                             | `batch_open_meteo`                                      |
| sports         | transfermarkt                                                                     | instruments-service                          | `batch_transfermarkt`                                   |
| sports         | understat                                                                         | instruments-service                          | `batch_understat`                                       |
| sports         | soccer_football_info                                                              | instruments-service                          | `batch_soccer_football_info`                            |
| **prediction** | polymarket                                                                        | market-tick-data-service                     | `batch_polymarket_clob` or `batch_polymarket_gamma_api` |
| **any**        | any                                                                               | instruments-service                          | `batch_instruments_service`                             |
| any            | any                                                                               | features-service                             | `batch_cross_instrument` or derived from input          |
| any            | any                                                                               | strategy-service                             | `batch_strategy_service`                                |
| any            | any                                                                               | execution-service                            | `batch_execution_service`                               |
| any            | any                                                                               | features-onchain-service                     | `batch_features_onchain_service`                        |
| any            | any                                                                               | market-data-processing-service               | `batch_mdps_odds_horizon_bucket`                        |

### Fallback Rules for Legacy/Sparse Rows

For rows where `service_name` is missing or ambiguous:

1. If `written_at` < 2026-01-01: default to primary batch source for (asset_group, venue) pair
2. If venue in Tardis coverage: `batch_tardis`
3. If venue in Databento coverage: `batch_databento`
4. If DeFi venue: check data_type — ticks/ohlcv → `batch_onchain_subgraph`, rates → `batch_onchain_rpc`
5. Otherwise: log warning and use `batch_<venue>` as placeholder

## Key Observations

1. **Enum already complete**: UAC has all 27 batch modes + live mode properly defined
2. **Schema v8 ready**: Column exists in manifest schema since v8 migration
3. **Writers not persisting**: Despite threading through functions, actual `record_captured()` calls are not passing
   pipeline_mode values
4. **No on-disk partition**: GCS paths lack `pipeline_mode=` segment (deferred per HARD RULE)
5. **Reconciliation blocked**: batch-live-reconciliation can't distinguish sources without values

## Recommendations for Implementation

1. **Phase 1 focus**: Contract test is the main gap — enum and facade already done
2. **Phase 2 critical**: UTL helper + writer sweep is where the actual fix happens
3. **Phase 3 scope**: ~38M rows across all buckets need backfill
4. **Phase 4 impact**: Consumers ready but waiting for non-NULL values

## Files Requiring Updates

### Phase 2 Writer Updates (Priority)

- All 26 MTDS batch handlers — add explicit `pipeline_mode=` to `record_captured()` calls
- MDPS canonical_writer — derive from source
- Instruments-service orchestrator — use `batch_instruments_service`
- Features-service handlers — pass through or derive
- Strategy-service handler — use `batch_strategy_service`

### Phase 3 Backfill Targets

- `gs://market-data-tick-cefi-prd-427895769566/_index/` (2.6M rows)
- `gs://market-data-tick-cefi-427895769566/_index/` (35.7M rows, legacy)
- `gs://market-data-tick-defi-prd-427895769566/_index/`
- `gs://market-data-tick-tradfi-prd-427895769566/_index/`
- `gs://market-data-tick-sports-prd-427895769566/_index/`
- `gs://market-data-tick-prediction-prd-427895769566/_index/`
- All corresponding `_index/per_vm/` shards

## Next Steps

With this audit complete, proceed to:

1. Phase 1 — Add UAC contract test (enum/facade already done)
2. Phase 2 — Create UTL helper and sweep all writers
3. Phase 3 — Backfill script implementation
4. Phase 4 — Consumer updates once values exist

> **🟡 DRAINED-WRITER DEPENDENCY (2026-06-01)** — the legacy-bucket SSOT remediation drained writer VMs
> `mdps-backfill-defi` / `mdps-prediction-2025` / `sports-scheduler`. They must NOT be relaunched until the
> legacy→canonical migration + manifest work complete. SSOT + relaunch gate:
> `plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` Phase 4.
