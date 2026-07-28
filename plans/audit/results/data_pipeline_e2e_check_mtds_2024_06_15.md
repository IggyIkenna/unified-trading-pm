---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2024-06-15)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2024-06-15: total=9 passed=1 failed=8 ambiguous=0 skipped=0"
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-28
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2024-06-15, legs=force"
date: 2026-07-28
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2024-06-15
generated_at: 2026-07-28T12:00:43.254317+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2024-06-15)

**Legs:** force **Started:** 2026-07-28T11:14:51.454838+00:00 **Finished:** 2026-07-28T12:00:43.249975+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2024-06-15: total=9 passed=1 failed=8 ambiguous=0 skipped=0

## Results

| Shard                                   | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                |
| --------------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:BITFINEX-FUTURES:trades            | force | passed | not_applicable | 0    | 1       | captured | -                                                                                                                                                                                     |
| CEFI:BITFINEX-FUTURES:book_snapshot_5   | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:derivative_ticker | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:liquidations      | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:options_chain     | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:futures_chain     | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:ohlcv_1m          | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:perp_funding      | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_kalshi_perp/asset_group=cefi/venue=BITFINEX-FUTURES/ |
| CEFI:BITFINEX-FUTURES:volatility_index  | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_deribit/asset_group=cefi/venue=BITFINEX-FUTURES/     |

## Bucket paths (where each write/read actually landed)

| Shard                                   | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| --------------------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:BITFINEX-FUTURES:trades            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:book_snapshot_5   | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:derivative_ticker | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:liquidations      | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:options_chain     | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:futures_chain     | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:ohlcv_1m          | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:perp_funding      | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:volatility_index  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard                                   | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                |
| --------------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI:BITFINEX-FUTURES:book_snapshot_5   | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2026-07-24/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:derivative_ticker | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:liquidations      | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:options_chain     | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:futures_chain     | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:ohlcv_1m          | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=BITFINEX-FUTURES/      |
| CEFI:BITFINEX-FUTURES:perp_funding      | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_kalshi_perp/asset_group=cefi/venue=BITFINEX-FUTURES/ |
| CEFI:BITFINEX-FUTURES:volatility_index  | force | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-cefi-test-central-element-323112/raw_tick_data/by_date/day=2024-06-15/pipeline_mode=batch_deribit/asset_group=cefi/venue=BITFINEX-FUTURES/     |
