---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-07-05)"
summary: "data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-07-05: total=14 passed=0 failed=7 ambiguous=0 skipped=7"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mdps]
related: []
created: 2026-07-27
audited_scope: "data_pipeline_e2e_check_mdps real-VM force/skip/live pipeline check for day=2026-07-05, legs=force,skip"
date: 2026-07-27
auditor: data_pipeline_e2e_check_mdps (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mdps
run_date: 2026-07-05
generated_at: 2026-07-27T03:21:33.333370+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mdps (2026-07-05)

**Legs:** force, skip **Started:** 2026-07-27T03:05:22.934661+00:00 **Finished:** 2026-07-27T03:21:33.242724+00:00

**Summary:** data_pipeline_e2e_check_mdps pipeline-e2e-check 2026-07-05: total=14 passed=0 failed=7 ambiguous=0
skipped=7

## Results

| Shard                           | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                   |
| ------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | -------------------------------------------------------- |
| CEFI:BINANCE-FUTURES:trades:15s | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:1m  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:5m  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:15m | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:1h  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:4h  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:24h | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout                   |
| CEFI:BINANCE-FUTURES:trades:15s | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:1m  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:5m  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:15m | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:1h  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:4h  | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |
| CEFI:BINANCE-FUTURES:trades:24h | skip  | skipped | ambiguous      | -    | 0       | -        | no_force_candle_object_to_fingerprint (honest-empty tf?) |

## Bucket paths (where each write/read actually landed)

| Shard                           | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ------------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:BINANCE-FUTURES:trades:15s | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1m  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:5m  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:15m | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1h  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:4h  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:24h | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:15s | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1m  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:5m  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:15m | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:1h  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:4h  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades:24h | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |

## Failed cells

| Shard                           | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                 |
| ------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | -------------------------------------- |
| CEFI:BINANCE-FUTURES:trades:15s | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:1m  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:5m  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:15m | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:1h  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:4h  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |
| CEFI:BINANCE-FUTURES:trades:24h | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_timeout |

## Migration worklist (canonical-shape gaps)

Cells whose data EXISTS but diverges from the DECLARED SSOT template, plus genuinely-malformed objects. These are NOT
passes and the declared template is deliberately never relaxed to absorb them. Note these rows are INDEPENDENT of the
force/skip verdict: a cell can be force-green (the writer wrote where it really writes) and still appear here (the
emitted path is not the declared one). Each row is migration work: bring the object path / input shard atom onto the
declared template, then re-run. Grep: `non_canonical` / `content_check=non_canonical`.

_(none — every checked cell was canonically shaped)_

## ADDENDUM 2026-07-27 (slot-10) — todo 3 candle-schema-drift proof-sweep (other data_types)

Scoped `--legs force --require-captured --auto-day` per representative `(asset_group, venue, data_type)` cell, per
`/plans/archive/issues/mdps_derivative_ticker_candle_schema_violation_2026_07_20.md` todo 3 ("sweep the OTHER candle
data_types for the same class of contract drift"). `futures_chain` has **zero enumerated cells** under `--mvp-only` — it
is not a live MDPS MVP data_type today, so it is out of scope (not silently skipped — confirmed via `--dry-enumerate`).

| Shard                                                           | Leg   | Status                 | Result                                                                            |
| --------------------------------------------------------------- | ----- | ---------------------- | --------------------------------------------------------------------------------- |
| CEFI:BINANCE-FUTURES:book_snapshot_5 (day=2026-04-18, auto-day) | force | **passed**             | 9/9 success, 68,535 candles, 0 failed — VM `…-113343-52b6f9` run.log, exit_code=0 |
| CEFI:BINANCE-FUTURES:liquidations (day=2026-05-22, auto-day)    | force | **mostly passed**      | 485/489 success, 3,693,275 candles — 4 FUTURE-instrument_type failures, see below |
| CEFI:BINANCE-FUTURES:options_chain                              | force | skipped (inconclusive) | `no_captured_input_for_cell` — not reachable via `--auto-day`, not a bug verdict  |
| DEFI:AAVE-ETHEREUM:liquidations                                 | force | skipped (inconclusive) | `no_captured_input_for_cell`                                                      |
| DEFI:UNISWAP_V3-ETHEREUM:liquidations                           | force | skipped (inconclusive) | `no_captured_input_for_cell`                                                      |
| TRADFI:AMEX:trades                                              | force | skipped (inconclusive) | `no_captured_input_for_cell`                                                      |
| TRADFI:NASDAQ:trades (day=2026-05-07, auto-day)                 | force | **FAILED (new bug)**   | `vm_exit_nonzero=1` — 0/2 success, see below                                      |

**Two genuine NEW findings** (both filed as new issue docs, not the original derivative_ticker bug class):

1. `CEFI:BINANCE-FUTURES:liquidations` — 4/489 instruments (`ETH-USDT@LIN-20260925`, `BTC-USDT@LIN-20260925`,
   `BTCUSDT_260626`, `ETHUSDT_260626`) failed with
   `No SchemaContract registered for asset_group='cefi' instrument_type='FUTURE' data_type='liq_agg_1d' venue='BINANCE-FUTURES'`
   — a missing UAC contract registration for the `FUTURE` instrument_type dimension of liquidation candles (distinct
   from the original missing-COLUMNS bug). Filed:
   `issues/mdps_liq_agg_contract_missing_future_instrument_type_2026_07_27.md`.
2. `TRADFI:NASDAQ:trades` — both instruments in the scoped batch (`IBIT`, `ETHA`, both Bitcoin/Ethereum ETFs) failed ALL
   7 timeframes with `Out of bounds nanosecond timestamp: 58317-01-15 …` — a corrupted/garbage raw-tick timestamp
   overflowing pandas' `datetime64[ns]` range, crashing candle aggregation. Correctly non-zero exit (no observability
   gap here, unlike the original derivative_ticker incident). Filed:
   `issues/mdps_tradfi_nasdaq_timestamp_overflow_candle_crash_2026_07_27.md`.

**Disposition**: the original schema-violation class (missing perp columns, `mdps@d4052e20b`) does NOT reproduce on
`book_snapshot_5` or the 485 clean `liquidations` instruments — the fix holds broadly. `options_chain` and the two
non-CEFI representative venues tried (DEFI, TRADFI:AMEX) were inconclusive (no reachable captured input, not a failure)
rather than proven clean — a genuine gap, not silently closed. The sweep surfaced two DIFFERENT, real,
previously-unknown data-correctness bugs instead, both filed as actionable issue docs per the findings-closure rule.
