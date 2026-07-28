---
doc_type: audit-result
title: "Pipeline E2E Check — data_pipeline_e2e_check_is (2026-03-15)"
summary: "data_pipeline_e2e_check_is pipeline-e2e-check 2026-03-15: total=26 passed=21 failed=1 ambiguous=0 skipped=4"
status: partial
nature: record
asset_group: [cefi]
stage: [data]
repos: [instruments-service, deployment-service]
scope: [engineer, admin]
tags: [pipeline-e2e-check, data_pipeline_e2e_check_is]
related: []
created: 2026-07-28
audited_scope: "data_pipeline_e2e_check_is real-VM force/skip/live pipeline check for day=2026-03-15, legs=live"
date: 2026-07-28
auditor: data_pipeline_e2e_check_is (real-VM automated run)
parent_epic: infrastructure_master
severity: P2
resulting_plan:
lib_version:
doc_versions_checked:
service: data_pipeline_e2e_check_is
run_date: 2026-03-15
generated_at: 2026-07-28T02:44:03.532386+00:00
---

# Pipeline E2E Check — data_pipeline_e2e_check_is (2026-03-15)

**Legs:** live **Started:** 2026-07-28T01:25:18.856851+00:00 **Finished:** 2026-07-28T02:44:03.532315+00:00

**Summary:** data_pipeline_e2e_check_is pipeline-e2e-check 2026-03-15: total=26 passed=21 failed=1 ambiguous=0 skipped=4

## Results

| Shard                             | Leg  | Status  | Skip proof     | Exit | Parquet | Manifest             | Reason                                                                                                                                                                                                                                          |
| --------------------------------- | ---- | ------- | -------------- | ---- | ------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI/BINANCE-SPOT/2026-03-15      | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/BINANCE-FUTURES/2026-03-15   | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/BINANCE-DELIVERY/2026-03-15  | live | skipped | not_applicable | -    | 0       | -                    | not_in_mvp_scope                                                                                                                                                                                                                                |
| CEFI/BYBIT/2026-03-15             | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/OKX/2026-03-15               | live | skipped | not_applicable | -    | 0       | -                    | not_in_mvp_scope                                                                                                                                                                                                                                |
| CEFI/OKX-SPOT/2026-03-15          | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/OKX-FUTURES/2026-03-15       | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/OKX-SWAP/2026-03-15          | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/DERIBIT/2026-03-15           | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/UPBIT/2026-03-15             | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/COINBASE-SPOT/2026-03-15     | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/BYBIT-SPOT/2026-03-15        | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/COINBASE-FUTURES/2026-03-15  | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/COINBASE-CDE/2026-03-15      | live | failed  | not_applicable | 0    | 0       | expected_unattempted | no_parquet_at:gs://instruments-store-cefi-test-central-element-323112/instrument_availability/by_date/day=2026-03-15/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=COINBASE-CDE/; manifest_status_invalid:expected_unattempted |
| CEFI/BITFINEX-SPOT/2026-03-15     | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/BITFINEX-FUTURES/2026-03-15  | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/BITGET-SPOT/2026-03-15       | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/BITGET-FUTURES/2026-03-15    | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/KRAKEN-SPOT/2026-03-15       | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/KRAKEN-FUTURES/2026-03-15    | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/HYPERLIQUID/2026-03-15       | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/ASTER/2026-03-15             | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/EXTENDED-STARKNET/2026-03-15 | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/LIGHTER-ZKSYNC/2026-03-15    | live | passed  | not_applicable | 0    | 1       | captured             | [NOTE: routed via launch-instruments-backfill-vm.sh, which currently always runs --mode batch under setup-data-pipeline-vm.sh -- this leg does not yet prove the true --mode live code path; see script module docstring]                       |
| CEFI/KALSHI-PERP/2026-03-15       | live | skipped | not_applicable | -    | 0       | -                    | not_in_mvp_scope                                                                                                                                                                                                                                |
| CEFI/POLYMARKET-PERP/2026-03-15   | live | skipped | not_applicable | -    | 0       | -                    | not_in_mvp_scope                                                                                                                                                                                                                                |

## Bucket paths (where each write/read actually landed)

| Shard                             | Leg  | Parquet bucket                                       | Manifest bucket                                      | Same bucket? |
| --------------------------------- | ---- | ---------------------------------------------------- | ---------------------------------------------------- | ------------ |
| CEFI/BINANCE-SPOT/2026-03-15      | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BINANCE-FUTURES/2026-03-15   | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BINANCE-DELIVERY/2026-03-15  | live | `-`                                                  | `-`                                                  | -            |
| CEFI/BYBIT/2026-03-15             | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/OKX/2026-03-15               | live | `-`                                                  | `-`                                                  | -            |
| CEFI/OKX-SPOT/2026-03-15          | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/OKX-FUTURES/2026-03-15       | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/OKX-SWAP/2026-03-15          | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/DERIBIT/2026-03-15           | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/UPBIT/2026-03-15             | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/COINBASE-SPOT/2026-03-15     | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BYBIT-SPOT/2026-03-15        | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/COINBASE-FUTURES/2026-03-15  | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/COINBASE-CDE/2026-03-15      | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BITFINEX-SPOT/2026-03-15     | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BITFINEX-FUTURES/2026-03-15  | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BITGET-SPOT/2026-03-15       | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/BITGET-FUTURES/2026-03-15    | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/KRAKEN-SPOT/2026-03-15       | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/KRAKEN-FUTURES/2026-03-15    | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/HYPERLIQUID/2026-03-15       | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/ASTER/2026-03-15             | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/EXTENDED-STARKNET/2026-03-15 | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/LIGHTER-ZKSYNC/2026-03-15    | live | `instruments-store-cefi-test-central-element-323112` | `instruments-store-cefi-test-central-element-323112` | yes          |
| CEFI/KALSHI-PERP/2026-03-15       | live | `-`                                                  | `-`                                                  | -            |
| CEFI/POLYMARKET-PERP/2026-03-15   | live | `-`                                                  | `-`                                                  | -            |

## Failed cells

| Shard                        | Leg  | Status | Skip proof     | Exit | Parquet | Manifest             | Reason                                                                                                                                                                                                                                          |
| ---------------------------- | ---- | ------ | -------------- | ---- | ------- | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CEFI/COINBASE-CDE/2026-03-15 | live | failed | not_applicable | 0    | 0       | expected_unattempted | no_parquet_at:gs://instruments-store-cefi-test-central-element-323112/instrument_availability/by_date/day=2026-03-15/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=COINBASE-CDE/; manifest_status_invalid:expected_unattempted |
