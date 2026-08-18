---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-06-28)"
summary: "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-06-28: total=12 passed=0 failed=12 ambiguous=0 skipped=0"
status: fail
nature: record
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-19
audited_scope:
  "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-06-28, legs=force,skip,canonical"
date: 2026-07-19
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: security_and_cross_cutting_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-06-28
generated_at: 2026-07-19T10:19:07.869737+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-06-28)

**Legs:** force, skip, canonical **Started:** 2026-07-19T09:51:16.972939+00:00 **Finished:**
2026-07-19T10:19:07.865467+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-06-28: total=12 passed=0 failed=12 ambiguous=0
skipped=0

## Results

| Shard                                 | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                                          |
| ------------------------------------- | --------- | ------ | -------------- | ---- | ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PREDICTION:POLYMARKET:trades          | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:POLYMARKET:trades          | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. POLYMARKET:PREDICTION_MARKET:46130022848920611732202507184264902690726361824951579816156441452797397798181 [None]: noncanonical-instrument_type:'None' |
| PREDICTION:POLYMARKET:trades          | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
| PREDICTION:POLYMARKET:book_snapshot_5 | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:POLYMARKET:book_snapshot_5 | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. POLYMARKET:PREDICTION_MARKET:51957749452952425148411923789673330395441266065580169554323593945478612691705 [None]: noncanonical-instrument_type:'None' |
| PREDICTION:POLYMARKET:book_snapshot_5 | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
| PREDICTION:KALSHI:trades              | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:KALSHI:trades              | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. KALSHI:PREDICTION_MARKET:KXMVESPORTSMULTIGAMEEXTENDED-S2026A0741A1D381-E00D66D4C4B [None]: noncanonical-instrument_type:'None'                         |
| PREDICTION:KALSHI:trades              | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
| PREDICTION:KALSHI:book_snapshot_5     | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:KALSHI:book_snapshot_5     | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. KALSHI:PREDICTION_MARKET:KXXRPD-26JUL0317-T0.6599 [None]: noncanonical-instrument_type:'None'                                                          |
| PREDICTION:KALSHI:book_snapshot_5     | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |

## Bucket paths (where each write/read actually landed)

| Shard                                 | Leg       | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ------------------------------------- | --------- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| PREDICTION:POLYMARKET:trades          | force     | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:POLYMARKET:trades          | canonical | `-`                                                 | `market-data-tick-pred-test-central-element-323112` | -            |
| PREDICTION:POLYMARKET:trades          | skip      | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:POLYMARKET:book_snapshot_5 | force     | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:POLYMARKET:book_snapshot_5 | canonical | `-`                                                 | `market-data-tick-pred-test-central-element-323112` | -            |
| PREDICTION:POLYMARKET:book_snapshot_5 | skip      | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:KALSHI:trades              | force     | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:KALSHI:trades              | canonical | `-`                                                 | `market-data-tick-pred-test-central-element-323112` | -            |
| PREDICTION:KALSHI:trades              | skip      | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:KALSHI:book_snapshot_5     | force     | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |
| PREDICTION:KALSHI:book_snapshot_5     | canonical | `-`                                                 | `market-data-tick-pred-test-central-element-323112` | -            |
| PREDICTION:KALSHI:book_snapshot_5     | skip      | `market-data-tick-pred-test-central-element-323112` | `market-data-tick-pred-test-central-element-323112` | yes          |

## Failed cells

| Shard                                 | Leg       | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                                                                                                                          |
| ------------------------------------- | --------- | ------ | -------------- | ---- | ------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| PREDICTION:POLYMARKET:trades          | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:POLYMARKET:trades          | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. POLYMARKET:PREDICTION_MARKET:46130022848920611732202507184264902690726361824951579816156441452797397798181 [None]: noncanonical-instrument_type:'None' |
| PREDICTION:POLYMARKET:trades          | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
| PREDICTION:POLYMARKET:book_snapshot_5 | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:POLYMARKET:book_snapshot_5 | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. POLYMARKET:PREDICTION_MARKET:51957749452952425148411923789673330395441266065580169554323593945478612691705 [None]: noncanonical-instrument_type:'None' |
| PREDICTION:POLYMARKET:book_snapshot_5 | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
| PREDICTION:KALSHI:trades              | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:KALSHI:trades              | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. KALSHI:PREDICTION_MARKET:KXMVESPORTSMULTIGAMEEXTENDED-S2026A0741A1D381-E00D66D4C4B [None]: noncanonical-instrument_type:'None'                         |
| PREDICTION:KALSHI:trades              | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
| PREDICTION:KALSHI:book_snapshot_5     | force     | failed | not_applicable | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/                                                                                                   |
| PREDICTION:KALSHI:book_snapshot_5     | canonical | failed | not_applicable | -    | 1       | -        | checked=1 canonical=0 raw=1 (checked per_vm_shard); e.g. KALSHI:PREDICTION_MARKET:KXXRPD-26JUL0317-T0.6599 [None]: noncanonical-instrument_type:'None'                                                          |
| PREDICTION:KALSHI:book_snapshot_5     | skip      | failed | genuine        | 0    | 0       | -        | no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-06-28/; skip_signal_not_found_in_run_log; object_signature_changed_or_missing                            |
