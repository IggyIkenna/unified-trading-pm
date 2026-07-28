---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)"
summary:
  "data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=468 passed=0 failed=124 ambiguous=0 skipped=344"
status: fail
nature: record
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_mtds]
related: []
created: 2026-07-28
audited_scope: "data_pipeline_e2e_check_mtds real-VM force/skip/live pipeline check for day=2026-03-15, legs=force,skip"
date: 2026-07-28
auditor: data_pipeline_e2e_check_mtds (real-VM automated run)
parent_epic: infrastructure_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_mtds
run_date: 2026-03-15
generated_at: 2026-07-28T05:08:01.992608+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_mtds (2026-03-15)

**Legs:** force, skip **Started:** 2026-07-28T04:20:22.871981+00:00 **Finished:** 2026-07-28T05:08:01.825864+00:00

**Summary:** data_pipeline_e2e_check_mtds pipeline-e2e-check 2026-03-15: total=468 passed=0 failed=124 ambiguous=0
skipped=344

## Results

| Shard                                    | Leg   | Status  | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                             |
| ---------------------------------------- | ----- | ------- | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------ |
| CEFI:BINANCE-SPOT:trades                 | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-SPOT:trades                 | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-SPOT:book_snapshot_5        | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-SPOT:book_snapshot_5        | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-SPOT:derivative_ticker      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:derivative_ticker      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:liquidations           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:liquidations           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:options_chain          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:options_chain          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:futures_chain          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:futures_chain          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:ohlcv_1m               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:ohlcv_1m               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:perp_funding           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:perp_funding           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:volatility_index       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-SPOT:volatility_index       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:trades              | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:trades              | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:book_snapshot_5     | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:book_snapshot_5     | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:derivative_ticker   | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:derivative_ticker   | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:liquidations        | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:liquidations        | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:options_chain       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:options_chain       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:futures_chain       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:futures_chain       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:ohlcv_1m            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:ohlcv_1m            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:perp_funding        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:perp_funding        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:volatility_index    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-FUTURES:volatility_index    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:trades             | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:trades             | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:book_snapshot_5    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:book_snapshot_5    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:derivative_ticker  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:derivative_ticker  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:liquidations       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:liquidations       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:options_chain      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:options_chain      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:futures_chain      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:futures_chain      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:ohlcv_1m           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:ohlcv_1m           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:perp_funding       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:perp_funding       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:volatility_index   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BINANCE-DELIVERY:volatility_index   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:trades                        | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:trades                        | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:book_snapshot_5               | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:book_snapshot_5               | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:derivative_ticker             | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:derivative_ticker             | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:liquidations                  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:liquidations                  | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:options_chain                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:options_chain                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:futures_chain                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:futures_chain                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:ohlcv_1m                      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:ohlcv_1m                      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:perp_funding                  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:perp_funding                  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:volatility_index              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT:volatility_index              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:trades                          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:trades                          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:book_snapshot_5                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:book_snapshot_5                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:derivative_ticker               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:derivative_ticker               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:liquidations                    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:liquidations                    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:options_chain                   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:options_chain                   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:futures_chain                   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:futures_chain                   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:ohlcv_1m                        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:ohlcv_1m                        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:perp_funding                    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:perp_funding                    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:volatility_index                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX:volatility_index                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:trades                     | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SPOT:trades                     | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SPOT:book_snapshot_5            | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SPOT:book_snapshot_5            | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SPOT:derivative_ticker          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:derivative_ticker          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:liquidations               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:liquidations               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:options_chain              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:options_chain              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:futures_chain              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:futures_chain              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:ohlcv_1m                   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:ohlcv_1m                   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:perp_funding               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:perp_funding               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:volatility_index           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SPOT:volatility_index           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:trades                  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-FUTURES:trades                  | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-FUTURES:book_snapshot_5         | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-FUTURES:book_snapshot_5         | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-FUTURES:derivative_ticker       | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-FUTURES:derivative_ticker       | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-FUTURES:liquidations            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:liquidations            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:options_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:options_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:futures_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:futures_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:ohlcv_1m                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:ohlcv_1m                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:perp_funding            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:perp_funding            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:volatility_index        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-FUTURES:volatility_index        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:trades                     | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:trades                     | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:book_snapshot_5            | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:book_snapshot_5            | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:derivative_ticker          | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:derivative_ticker          | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:liquidations               | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:liquidations               | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:options_chain              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:options_chain              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:futures_chain              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:futures_chain              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:ohlcv_1m                   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:ohlcv_1m                   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:perp_funding               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:perp_funding               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:volatility_index           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:OKX-SWAP:volatility_index           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:trades                      | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:trades                      | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:book_snapshot_5             | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:book_snapshot_5             | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:derivative_ticker           | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:derivative_ticker           | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:liquidations                | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:liquidations                | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:options_chain               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:options_chain               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:futures_chain               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:futures_chain               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:ohlcv_1m                    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:ohlcv_1m                    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:perp_funding                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:perp_funding                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:DERIBIT:volatility_index            | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:volatility_index            | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:UPBIT:trades                        | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:UPBIT:trades                        | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:UPBIT:book_snapshot_5               | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:UPBIT:book_snapshot_5               | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:UPBIT:derivative_ticker             | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:derivative_ticker             | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:liquidations                  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:liquidations                  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:options_chain                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:options_chain                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:futures_chain                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:futures_chain                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:ohlcv_1m                      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:ohlcv_1m                      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:perp_funding                  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:perp_funding                  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:volatility_index              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:UPBIT:volatility_index              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:trades                | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-SPOT:trades                | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-SPOT:book_snapshot_5       | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-SPOT:book_snapshot_5       | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-SPOT:derivative_ticker     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:derivative_ticker     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:liquidations          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:liquidations          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:options_chain         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:options_chain         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:futures_chain         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:futures_chain         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:ohlcv_1m              | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-SPOT:ohlcv_1m              | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-SPOT:perp_funding          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:perp_funding          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:volatility_index      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-SPOT:volatility_index      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:trades                   | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT-SPOT:trades                   | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT-SPOT:book_snapshot_5          | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT-SPOT:book_snapshot_5          | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT-SPOT:derivative_ticker        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:derivative_ticker        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:liquidations             | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:liquidations             | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:options_chain            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:options_chain            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:futures_chain            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:futures_chain            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:ohlcv_1m                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:ohlcv_1m                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:perp_funding             | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:perp_funding             | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:volatility_index         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BYBIT-SPOT:volatility_index         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:trades             | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-FUTURES:trades             | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-FUTURES:book_snapshot_5    | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-FUTURES:book_snapshot_5    | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-FUTURES:derivative_ticker  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-FUTURES:derivative_ticker  | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-FUTURES:liquidations       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:liquidations       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:options_chain      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:options_chain      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:futures_chain      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:futures_chain      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:ohlcv_1m           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:ohlcv_1m           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:perp_funding       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:perp_funding       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:volatility_index   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-FUTURES:volatility_index   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:trades                 | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-CDE:trades                 | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-CDE:book_snapshot_5        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:book_snapshot_5        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:derivative_ticker      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:derivative_ticker      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:liquidations           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:liquidations           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:options_chain          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:options_chain          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:futures_chain          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:futures_chain          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:ohlcv_1m               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:ohlcv_1m               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:perp_funding           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:perp_funding           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:volatility_index       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:COINBASE-CDE:volatility_index       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:trades                | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-SPOT:trades                | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-SPOT:book_snapshot_5       | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-SPOT:book_snapshot_5       | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-SPOT:derivative_ticker     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:derivative_ticker     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:liquidations          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:liquidations          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:options_chain         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:options_chain         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:futures_chain         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:futures_chain         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:ohlcv_1m              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:ohlcv_1m              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:perp_funding          | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:perp_funding          | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:volatility_index      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-SPOT:volatility_index      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:trades             | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:trades             | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:book_snapshot_5    | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:book_snapshot_5    | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:derivative_ticker  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:derivative_ticker  | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:liquidations       | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:liquidations       | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:options_chain      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:options_chain      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:futures_chain      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:futures_chain      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:ohlcv_1m           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:ohlcv_1m           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:perp_funding       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:perp_funding       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:volatility_index   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITFINEX-FUTURES:volatility_index   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:trades                  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-SPOT:trades                  | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-SPOT:book_snapshot_5         | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-SPOT:book_snapshot_5         | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-SPOT:derivative_ticker       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:derivative_ticker       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:liquidations            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:liquidations            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:options_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:options_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:futures_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:futures_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:ohlcv_1m                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:ohlcv_1m                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:perp_funding            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:perp_funding            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:volatility_index        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-SPOT:volatility_index        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:trades               | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:trades               | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:book_snapshot_5      | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:book_snapshot_5      | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:derivative_ticker    | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:derivative_ticker    | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:liquidations         | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:liquidations         | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:options_chain        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:options_chain        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:futures_chain        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:futures_chain        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:ohlcv_1m             | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:ohlcv_1m             | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:perp_funding         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:perp_funding         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:volatility_index     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:BITGET-FUTURES:volatility_index     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:trades                  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-SPOT:trades                  | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-SPOT:book_snapshot_5         | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-SPOT:book_snapshot_5         | skip  | failed  | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-SPOT:derivative_ticker       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:derivative_ticker       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:liquidations            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:liquidations            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:options_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:options_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:futures_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:futures_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:ohlcv_1m                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:ohlcv_1m                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:perp_funding            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:perp_funding            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:volatility_index        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-SPOT:volatility_index        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:trades               | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:trades               | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:book_snapshot_5      | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:book_snapshot_5      | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:derivative_ticker    | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:derivative_ticker    | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:liquidations         | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:liquidations         | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:options_chain        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:options_chain        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:futures_chain        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:futures_chain        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:ohlcv_1m             | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:ohlcv_1m             | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:perp_funding         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:perp_funding         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:volatility_index     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KRAKEN-FUTURES:volatility_index     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:trades                  | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:HYPERLIQUID:trades                  | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:HYPERLIQUID:book_snapshot_5         | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:HYPERLIQUID:book_snapshot_5         | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:HYPERLIQUID:derivative_ticker       | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:HYPERLIQUID:derivative_ticker       | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:HYPERLIQUID:liquidations            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:liquidations            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:options_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:options_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:futures_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:futures_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:ohlcv_1m                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:ohlcv_1m                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:perp_funding            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:perp_funding            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:volatility_index        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:HYPERLIQUID:volatility_index        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:trades                        | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:ASTER:trades                        | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:book_snapshot_5               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:book_snapshot_5               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:derivative_ticker             | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:ASTER:derivative_ticker             | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:liquidations                  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:liquidations                  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:options_chain                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:options_chain                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:futures_chain                 | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:futures_chain                 | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:ohlcv_1m                      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:ohlcv_1m                      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:perp_funding                  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:perp_funding                  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:volatility_index              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:ASTER:volatility_index              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:trades            | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:EXTENDED-STARKNET:trades            | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:derivative_ticker | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:EXTENDED-STARKNET:derivative_ticker | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:liquidations      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:liquidations      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:options_chain     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:options_chain     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:futures_chain     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:futures_chain     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:perp_funding      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:perp_funding      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:volatility_index  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:EXTENDED-STARKNET:volatility_index  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:trades               | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:trades               | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:book_snapshot_5      | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:book_snapshot_5      | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:derivative_ticker    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:derivative_ticker    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:liquidations         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:liquidations         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:options_chain        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:options_chain        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:futures_chain        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:futures_chain        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:ohlcv_1m             | force | failed  | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:LIGHTER-ZKSYNC:ohlcv_1m             | skip  | failed  | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:LIGHTER-ZKSYNC:perp_funding         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:perp_funding         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:volatility_index     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:LIGHTER-ZKSYNC:volatility_index     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:trades                  | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:trades                  | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:book_snapshot_5         | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:book_snapshot_5         | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:derivative_ticker       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:derivative_ticker       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:liquidations            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:liquidations            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:options_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:options_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:futures_chain           | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:futures_chain           | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:ohlcv_1m                | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:ohlcv_1m                | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:perp_funding            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:perp_funding            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:volatility_index        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:KALSHI-PERP:volatility_index        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:trades              | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:trades              | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:book_snapshot_5     | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:book_snapshot_5     | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:derivative_ticker   | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:derivative_ticker   | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:liquidations        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:liquidations        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:options_chain       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:options_chain       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:futures_chain       | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:futures_chain       | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:ohlcv_1m            | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:ohlcv_1m            | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:perp_funding        | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:perp_funding        | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:volatility_index    | force | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |
| CEFI:POLYMARKET-PERP:volatility_index    | skip  | skipped | not_applicable | -    | 0       | -        | no_captured_data_for_cell                                                                                          |

## Bucket paths (where each write/read actually landed)

| Shard                                    | Leg   | Parquet bucket                                      | Manifest bucket                                     | Same bucket? |
| ---------------------------------------- | ----- | --------------------------------------------------- | --------------------------------------------------- | ------------ |
| CEFI:BINANCE-SPOT:trades                 | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-SPOT:trades                 | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-SPOT:book_snapshot_5        | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-SPOT:book_snapshot_5        | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-SPOT:derivative_ticker      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:derivative_ticker      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:liquidations           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:liquidations           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:options_chain          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:options_chain          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:futures_chain          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:futures_chain          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:ohlcv_1m               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:ohlcv_1m               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:perp_funding           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:perp_funding           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:volatility_index       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-SPOT:volatility_index       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:trades              | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:trades              | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:book_snapshot_5     | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:book_snapshot_5     | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:derivative_ticker   | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:derivative_ticker   | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:liquidations        | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:liquidations        | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BINANCE-FUTURES:options_chain       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:options_chain       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:futures_chain       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:futures_chain       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:ohlcv_1m            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:ohlcv_1m            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:perp_funding        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:perp_funding        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:volatility_index    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-FUTURES:volatility_index    | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:trades             | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:trades             | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:book_snapshot_5    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:book_snapshot_5    | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:derivative_ticker  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:derivative_ticker  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:liquidations       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:liquidations       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:options_chain      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:options_chain      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:futures_chain      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:futures_chain      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:ohlcv_1m           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:ohlcv_1m           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:perp_funding       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:perp_funding       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:volatility_index   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BINANCE-DELIVERY:volatility_index   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:trades                        | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:trades                        | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:book_snapshot_5               | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:book_snapshot_5               | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:derivative_ticker             | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:derivative_ticker             | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:liquidations                  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:liquidations                  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT:options_chain                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:options_chain                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:futures_chain                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:futures_chain                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:ohlcv_1m                      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:ohlcv_1m                      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:perp_funding                  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:perp_funding                  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:volatility_index              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT:volatility_index              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:trades                          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:trades                          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:book_snapshot_5                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:book_snapshot_5                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:derivative_ticker               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:derivative_ticker               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:liquidations                    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:liquidations                    | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:options_chain                   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:options_chain                   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:futures_chain                   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:futures_chain                   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:ohlcv_1m                        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:ohlcv_1m                        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:perp_funding                    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:perp_funding                    | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:volatility_index                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX:volatility_index                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:trades                     | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SPOT:trades                     | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SPOT:book_snapshot_5            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SPOT:book_snapshot_5            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SPOT:derivative_ticker          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:derivative_ticker          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:liquidations               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:liquidations               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:options_chain              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:options_chain              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:futures_chain              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:futures_chain              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:ohlcv_1m                   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:ohlcv_1m                   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:perp_funding               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:perp_funding               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:volatility_index           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SPOT:volatility_index           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:trades                  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-FUTURES:trades                  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-FUTURES:book_snapshot_5         | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-FUTURES:book_snapshot_5         | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-FUTURES:derivative_ticker       | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-FUTURES:derivative_ticker       | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-FUTURES:liquidations            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:liquidations            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:options_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:options_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:futures_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:futures_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:ohlcv_1m                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:ohlcv_1m                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:perp_funding            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:perp_funding            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:volatility_index        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-FUTURES:volatility_index        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:trades                     | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:trades                     | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:book_snapshot_5            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:book_snapshot_5            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:derivative_ticker          | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:derivative_ticker          | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:liquidations               | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:liquidations               | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:OKX-SWAP:options_chain              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:options_chain              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:futures_chain              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:futures_chain              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:ohlcv_1m                   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:ohlcv_1m                   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:perp_funding               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:perp_funding               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:volatility_index           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:OKX-SWAP:volatility_index           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:trades                      | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:trades                      | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:book_snapshot_5             | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:book_snapshot_5             | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:derivative_ticker           | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:derivative_ticker           | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:liquidations                | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:liquidations                | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:options_chain               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:options_chain               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:futures_chain               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:futures_chain               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:ohlcv_1m                    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:ohlcv_1m                    | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:perp_funding                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:perp_funding                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:DERIBIT:volatility_index            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:DERIBIT:volatility_index            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:UPBIT:trades                        | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:UPBIT:trades                        | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:UPBIT:book_snapshot_5               | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:UPBIT:book_snapshot_5               | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:UPBIT:derivative_ticker             | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:derivative_ticker             | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:liquidations                  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:liquidations                  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:options_chain                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:options_chain                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:futures_chain                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:futures_chain                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:ohlcv_1m                      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:ohlcv_1m                      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:perp_funding                  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:perp_funding                  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:volatility_index              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:UPBIT:volatility_index              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:trades                | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-SPOT:trades                | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-SPOT:book_snapshot_5       | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-SPOT:book_snapshot_5       | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-SPOT:derivative_ticker     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:derivative_ticker     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:liquidations          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:liquidations          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:options_chain         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:options_chain         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:futures_chain         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:futures_chain         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:ohlcv_1m              | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-SPOT:ohlcv_1m              | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-SPOT:perp_funding          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:perp_funding          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:volatility_index      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-SPOT:volatility_index      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:trades                   | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT-SPOT:trades                   | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT-SPOT:book_snapshot_5          | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT-SPOT:book_snapshot_5          | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BYBIT-SPOT:derivative_ticker        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:derivative_ticker        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:liquidations             | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:liquidations             | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:options_chain            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:options_chain            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:futures_chain            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:futures_chain            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:ohlcv_1m                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:ohlcv_1m                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:perp_funding             | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:perp_funding             | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:volatility_index         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BYBIT-SPOT:volatility_index         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:trades             | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-FUTURES:trades             | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-FUTURES:book_snapshot_5    | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-FUTURES:book_snapshot_5    | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-FUTURES:derivative_ticker  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-FUTURES:derivative_ticker  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-FUTURES:liquidations       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:liquidations       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:options_chain      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:options_chain      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:futures_chain      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:futures_chain      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:ohlcv_1m           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:ohlcv_1m           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:perp_funding       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:perp_funding       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:volatility_index   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-FUTURES:volatility_index   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:trades                 | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-CDE:trades                 | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:COINBASE-CDE:book_snapshot_5        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:book_snapshot_5        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:derivative_ticker      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:derivative_ticker      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:liquidations           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:liquidations           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:options_chain          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:options_chain          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:futures_chain          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:futures_chain          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:ohlcv_1m               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:ohlcv_1m               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:perp_funding           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:perp_funding           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:volatility_index       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:COINBASE-CDE:volatility_index       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:trades                | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-SPOT:trades                | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-SPOT:book_snapshot_5       | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-SPOT:book_snapshot_5       | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-SPOT:derivative_ticker     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:derivative_ticker     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:liquidations          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:liquidations          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:options_chain         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:options_chain         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:futures_chain         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:futures_chain         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:ohlcv_1m              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:ohlcv_1m              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:perp_funding          | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:perp_funding          | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:volatility_index      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-SPOT:volatility_index      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:trades             | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:trades             | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:book_snapshot_5    | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:book_snapshot_5    | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:derivative_ticker  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:derivative_ticker  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:liquidations       | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:liquidations       | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITFINEX-FUTURES:options_chain      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:options_chain      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:futures_chain      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:futures_chain      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:ohlcv_1m           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:ohlcv_1m           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:perp_funding       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:perp_funding       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:volatility_index   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITFINEX-FUTURES:volatility_index   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:trades                  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-SPOT:trades                  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-SPOT:book_snapshot_5         | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-SPOT:book_snapshot_5         | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-SPOT:derivative_ticker       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:derivative_ticker       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:liquidations            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:liquidations            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:options_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:options_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:futures_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:futures_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:ohlcv_1m                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:ohlcv_1m                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:perp_funding            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:perp_funding            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:volatility_index        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-SPOT:volatility_index        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:trades               | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:trades               | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:book_snapshot_5      | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:book_snapshot_5      | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:derivative_ticker    | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:derivative_ticker    | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:liquidations         | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:liquidations         | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:BITGET-FUTURES:options_chain        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:options_chain        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:futures_chain        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:futures_chain        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:ohlcv_1m             | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:ohlcv_1m             | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:perp_funding         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:perp_funding         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:volatility_index     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:BITGET-FUTURES:volatility_index     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:trades                  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-SPOT:trades                  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-SPOT:book_snapshot_5         | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-SPOT:book_snapshot_5         | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-SPOT:derivative_ticker       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:derivative_ticker       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:liquidations            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:liquidations            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:options_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:options_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:futures_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:futures_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:ohlcv_1m                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:ohlcv_1m                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:perp_funding            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:perp_funding            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:volatility_index        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-SPOT:volatility_index        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:trades               | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:trades               | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:book_snapshot_5      | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:book_snapshot_5      | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:derivative_ticker    | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:derivative_ticker    | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:liquidations         | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:liquidations         | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:KRAKEN-FUTURES:options_chain        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:options_chain        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:futures_chain        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:futures_chain        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:ohlcv_1m             | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:ohlcv_1m             | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:perp_funding         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:perp_funding         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:volatility_index     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KRAKEN-FUTURES:volatility_index     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:trades                  | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:HYPERLIQUID:trades                  | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:HYPERLIQUID:book_snapshot_5         | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:HYPERLIQUID:book_snapshot_5         | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:HYPERLIQUID:derivative_ticker       | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:HYPERLIQUID:derivative_ticker       | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:HYPERLIQUID:liquidations            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:liquidations            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:options_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:options_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:futures_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:futures_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:ohlcv_1m                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:ohlcv_1m                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:perp_funding            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:perp_funding            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:volatility_index        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:HYPERLIQUID:volatility_index        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:trades                        | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:trades                        | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:book_snapshot_5               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:book_snapshot_5               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:derivative_ticker             | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:derivative_ticker             | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:ASTER:liquidations                  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:liquidations                  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:options_chain                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:options_chain                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:futures_chain                 | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:futures_chain                 | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:ohlcv_1m                      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:ohlcv_1m                      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:perp_funding                  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:perp_funding                  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:volatility_index              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:ASTER:volatility_index              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:trades            | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:trades            | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:book_snapshot_5   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:derivative_ticker | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:derivative_ticker | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:liquidations      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:liquidations      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:options_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:options_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:futures_chain     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:futures_chain     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:EXTENDED-STARKNET:perp_funding      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:perp_funding      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:volatility_index  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:EXTENDED-STARKNET:volatility_index  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:trades               | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:trades               | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:book_snapshot_5      | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:book_snapshot_5      | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:derivative_ticker    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:derivative_ticker    | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:liquidations         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:liquidations         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:options_chain        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:options_chain        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:futures_chain        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:futures_chain        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:ohlcv_1m             | force | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:LIGHTER-ZKSYNC:ohlcv_1m             | skip  | `market-data-tick-cefi-test-central-element-323112` | `market-data-tick-cefi-test-central-element-323112` | yes          |
| CEFI:LIGHTER-ZKSYNC:perp_funding         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:perp_funding         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:volatility_index     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:LIGHTER-ZKSYNC:volatility_index     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:trades                  | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:trades                  | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:book_snapshot_5         | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:book_snapshot_5         | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:derivative_ticker       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:derivative_ticker       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:liquidations            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:liquidations            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:options_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:options_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:futures_chain           | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:futures_chain           | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:ohlcv_1m                | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:ohlcv_1m                | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:perp_funding            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:perp_funding            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:volatility_index        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:KALSHI-PERP:volatility_index        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:trades              | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:trades              | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:book_snapshot_5     | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:book_snapshot_5     | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:derivative_ticker   | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:derivative_ticker   | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:liquidations        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:liquidations        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:options_chain       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:options_chain       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:futures_chain       | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:futures_chain       | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:ohlcv_1m            | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:ohlcv_1m            | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:perp_funding        | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:perp_funding        | skip  | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:volatility_index    | force | `-`                                                 | `-`                                                 | -            |
| CEFI:POLYMARKET-PERP:volatility_index    | skip  | `-`                                                 | `-`                                                 | -            |

## Failed cells

| Shard                                    | Leg   | Status | Skip proof     | Exit | Parquet | Manifest | Reason                                                                                                             |
| ---------------------------------------- | ----- | ------ | -------------- | ---- | ------- | -------- | ------------------------------------------------------------------------------------------------------------------ |
| CEFI:BINANCE-SPOT:trades                 | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-SPOT:trades                 | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-SPOT:book_snapshot_5        | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-SPOT:book_snapshot_5        | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:trades              | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:trades              | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:book_snapshot_5     | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:book_snapshot_5     | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:derivative_ticker   | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:derivative_ticker   | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BINANCE-FUTURES:liquidations        | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BINANCE-FUTURES:liquidations        | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:trades                        | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:trades                        | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:book_snapshot_5               | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:book_snapshot_5               | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:derivative_ticker             | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:derivative_ticker             | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT:liquidations                  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT:liquidations                  | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SPOT:trades                     | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SPOT:trades                     | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SPOT:book_snapshot_5            | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SPOT:book_snapshot_5            | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-FUTURES:trades                  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-FUTURES:trades                  | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-FUTURES:book_snapshot_5         | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-FUTURES:book_snapshot_5         | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-FUTURES:derivative_ticker       | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-FUTURES:derivative_ticker       | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:trades                     | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:trades                     | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:book_snapshot_5            | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:book_snapshot_5            | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:derivative_ticker          | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:derivative_ticker          | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:OKX-SWAP:liquidations               | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:OKX-SWAP:liquidations               | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:trades                      | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:trades                      | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:book_snapshot_5             | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:book_snapshot_5             | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:derivative_ticker           | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:derivative_ticker           | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:liquidations                | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:liquidations                | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:DERIBIT:volatility_index            | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:DERIBIT:volatility_index            | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:UPBIT:trades                        | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:UPBIT:trades                        | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:UPBIT:book_snapshot_5               | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:UPBIT:book_snapshot_5               | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-SPOT:trades                | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-SPOT:trades                | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-SPOT:book_snapshot_5       | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-SPOT:book_snapshot_5       | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-SPOT:ohlcv_1m              | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-SPOT:ohlcv_1m              | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT-SPOT:trades                   | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT-SPOT:trades                   | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BYBIT-SPOT:book_snapshot_5          | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BYBIT-SPOT:book_snapshot_5          | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-FUTURES:trades             | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-FUTURES:trades             | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-FUTURES:book_snapshot_5    | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-FUTURES:book_snapshot_5    | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-FUTURES:derivative_ticker  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-FUTURES:derivative_ticker  | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:COINBASE-CDE:trades                 | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:COINBASE-CDE:trades                 | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-SPOT:trades                | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-SPOT:trades                | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-SPOT:book_snapshot_5       | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-SPOT:book_snapshot_5       | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:trades             | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:trades             | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:book_snapshot_5    | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:book_snapshot_5    | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:derivative_ticker  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:derivative_ticker  | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITFINEX-FUTURES:liquidations       | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITFINEX-FUTURES:liquidations       | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-SPOT:trades                  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-SPOT:trades                  | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-SPOT:book_snapshot_5         | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-SPOT:book_snapshot_5         | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:trades               | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:trades               | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:book_snapshot_5      | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:book_snapshot_5      | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:derivative_ticker    | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:derivative_ticker    | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:BITGET-FUTURES:liquidations         | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:BITGET-FUTURES:liquidations         | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-SPOT:trades                  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-SPOT:trades                  | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-SPOT:book_snapshot_5         | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-SPOT:book_snapshot_5         | skip  | failed | ambiguous      | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:trades               | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:trades               | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:book_snapshot_5      | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:book_snapshot_5      | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:derivative_ticker    | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:derivative_ticker    | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:KRAKEN-FUTURES:liquidations         | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:KRAKEN-FUTURES:liquidations         | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:HYPERLIQUID:trades                  | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:HYPERLIQUID:trades                  | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:HYPERLIQUID:book_snapshot_5         | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:HYPERLIQUID:book_snapshot_5         | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:HYPERLIQUID:derivative_ticker       | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:HYPERLIQUID:derivative_ticker       | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:trades                        | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:ASTER:trades                        | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:ASTER:derivative_ticker             | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:ASTER:derivative_ticker             | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:trades            | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:EXTENDED-STARKNET:trades            | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:derivative_ticker | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:EXTENDED-STARKNET:derivative_ticker | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:EXTENDED-STARKNET:ohlcv_1m          | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
| CEFI:LIGHTER-ZKSYNC:ohlcv_1m             | force | failed | not_applicable | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1                                                                        |
| CEFI:LIGHTER-ZKSYNC:ohlcv_1m             | skip  | failed | genuine        | -    | 0       | -        | vm_not_success:launcher_script_nonzero_rc=1; skip_signal_not_found_in_run_log; object_signature_changed_or_missing |
