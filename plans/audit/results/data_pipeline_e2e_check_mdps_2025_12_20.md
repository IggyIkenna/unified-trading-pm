---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2025-12-20)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2025-12-20: total=30 passed=0 failed=7 ambiguous=0 skipped=23"
status: fail
nature: record
asset_group: [sports]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-08-01
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2025-12-20, legs=force,skip"
date: 2026-08-01
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2025-12-20
generated_at: 2026-08-01T11:58:00.634865+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2025-12-20)

**Legs:** force, skip **Started:** 2026-08-01T11:50:06.363503+00:00 **Finished:** 2026-08-01T11:58:00.599653+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2025-12-20: total=30 passed=0 failed=7 ambiguous=0
skipped=23

**IAM fix CONFIRMED WORKING**: no 403/PERMISSION_DENIED anywhere in this run (the baseline attempt earlier the same day,
before `bucket_iam_group_a_market_data_tick_prefix_missing_asset_group_2026_08_01.md`'s two per-AG IAM fixes landed,
403'd on every write). Every FAILED/SKIPPED verdict below is a genuine, non-infra finding.

## Results

| Shard                            | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                                                                                                                                                                                   |
| -------------------------------- | ----- | ------- | -------------- | ---- | ------- | --------------- | ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPORTS:*:arbitrage_opportunity   | force | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:arbitrage_opportunity   | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:odds_horizon_bucket:15m | force | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:1h  | force | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:4h  | force | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:24h | force | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:15m | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:1h  | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:4h  | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_horizon_bucket:24h | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | duplicate_in_flight: mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067 is already RUNNING this shard — skipped to avoid a duplicate billable VM (issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md) |
| SPORTS:*:odds_movement           | force | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:odds_movement           | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:odds_snapshot           | force | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:odds_snapshot           | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:trades:15s              | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=15s; manifest data_type=trades timeframe=15s)                                            |
| SPORTS:*:trades:1m               | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=1m; manifest data_type=trades timeframe=1m)                                              |
| SPORTS:*:trades:5m               | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=5m; manifest data_type=trades timeframe=5m)                                              |
| SPORTS:*:trades:15m              | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=15m; manifest data_type=trades timeframe=15m)                                            |
| SPORTS:*:trades:1h               | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=1h; manifest data_type=trades timeframe=1h)                                              |
| SPORTS:*:trades:4h               | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=4h; manifest data_type=trades timeframe=4h)                                              |
| SPORTS:*:trades:24h              | force | failed  | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=24h; manifest data_type=trades timeframe=1d)                                             |
| SPORTS:*:trades:15s              | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades:1m               | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades:5m               | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades:15m              | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades:1h               | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades:4h               | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades:24h              | skip  | skipped | genuine        | 0    | 0       | -               | not_checked | no_force_candle_object_to_fingerprint (honest-empty tf?)                                                                                                                                                                                 |
| SPORTS:*:trades_inplay           | force | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |
| SPORTS:*:trades_inplay           | skip  | skipped | not_applicable | -    | 0       | -               | not_checked | no_captured_input_for_cell                                                                                                                                                                                                               |

## Bucket paths (where each write/read actually landed)

| Shard                            | Leg   | Parquet bucket                                        | Manifest bucket                                       | Same bucket? |
| -------------------------------- | ----- | ----------------------------------------------------- | ----------------------------------------------------- | ------------ |
| SPORTS:*:arbitrage_opportunity   | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:arbitrage_opportunity   | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:15m | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:1h  | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:4h  | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:24h | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:15m | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:1h  | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:4h  | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_horizon_bucket:24h | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_movement           | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_movement           | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_snapshot           | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:odds_snapshot           | skip  | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:trades:15s              | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:1m               | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:5m               | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:15m              | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:1h               | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:4h               | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:24h              | force | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:15s              | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:1m               | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:5m               | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:15m              | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:1h               | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:4h               | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades:24h              | skip  | `market-data-tick-sports-test-central-element-323112` | `market-data-tick-sports-test-central-element-323112` | yes          |
| SPORTS:*:trades_inplay           | force | `-`                                                   | `-`                                                   | -            |
| SPORTS:*:trades_inplay           | skip  | `-`                                                   | `-`                                                   | -            |

## Failed cells

| Shard               | Leg   | Status | Skip proof     | Exit | Parquet | Manifest        | Content     | Reason                                                                                                                                                                                        |
| ------------------- | ----- | ------ | -------------- | ---- | ------- | --------------- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SPORTS:*:trades:15s | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=15s; manifest data_type=trades timeframe=15s) |
| SPORTS:*:trades:1m  | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=1m; manifest data_type=trades timeframe=1m)   |
| SPORTS:*:trades:5m  | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=5m; manifest data_type=trades timeframe=5m)   |
| SPORTS:*:trades:15m | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=15m; manifest data_type=trades timeframe=15m) |
| SPORTS:*:trades:1h  | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=1h; manifest data_type=trades timeframe=1h)   |
| SPORTS:*:trades:4h  | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=4h; manifest data_type=trades timeframe=4h)   |
| SPORTS:*:trades:24h | force | failed | not_applicable | 0    | 0       | no_matching_row | not_checked | no_candle_under:gs://market-data-tick-sports-test-central-element-323112/processed/by_date/day=2025-12-20/ (measured data_type=trades timeframe=24h; manifest data_type=trades timeframe=1d)  |

## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus genuinely-malformed objects. These are NOT
passes and the declared template is deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really writes) and still appear here (the
emitted path is not the declared one). Each row is migration work: bring the object path / input shard atom onto the
declared template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_

## Root-cause analysis (added post-run, this session)

Both non-infra failure classes are now root-caused, not just observed:

1. **`odds_horizon_bucket` (4 timeframes, both legs) — correctly de-duped**, not a bug in this run. A concurrent slot-7
   session was already running the identical `(SPORTS, odds_horizon_bucket)` shard (VM
   `mdps-backfill-sports-pipelinecheck-20260801-114120-2bf067`, targeting day=2025-12-24 as part of the
   separately-tracked `odds_horizon_bucket` MDPS reprocess / league_id-migration Step 7 work — see
   `plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md`). The pipeline_e2e_check driver's own dedup
   guard (`issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md`) correctly skipped rather
   than launching a duplicate billable VM. This shard's genuine verdict needs a follow-up run once no concurrent session
   holds it.
2. **`trades` (7 timeframes, force leg) — a real, deterministic enumeration/reality mismatch, root-caused and fixed this
   session.** MDPS's own runtime (`process_handler.py::_process_one_category`) applies a 3-stage filter — asset_group
   membership, `needs_candle_processing(dt)`, AND `CandleAdapterRegistry.has_adapter()` — and correctly bypasses
   `sports:trades` (no registered candle adapter; raw trades are consumed directly by features-onchain, same as DeFi
   `liquidations`). `pipeline_e2e_check.py`'s `enumerate_mdps_shards()` / `_add_reference_ag_shards()` only checked
   `needs_candle_processing(dt)` (which defaults/declares `True` for `trades` globally) and never consulted
   `CandleAdapterRegistry.has_adapter()` — so it enumerated a shard MDPS was always going to bypass, producing a
   deterministic false `no_candle_under` failure on every single run, for every day. **Fixed**:
   `market-data-processing-service@<see plan citation>` — `_add_reference_ag_shards()` now also requires
   `CandleAdapterRegistry.has_adapter(ag, dt)`, mirroring the runtime's own filter.
