---
doc_type: plan
title: prediction venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 4 in-scope Prediction (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [prediction]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, prediction, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md]
created: "2026-08-20"
last_updated: "2026-08-21"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.8
estimate_calibrated_ai_days: 1.44
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
effort: high
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/06-coding-standards/integration-testing-layers.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# Prediction venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Filter the generator output to `asset_group=prediction`; the four-row count is re-measured at execution time.

## Todos

- [x] [BACKEND] P0. **Execution attempt complete — RED, not a false pass.** The canonical generator re-measured four current Prediction rows, and staging driver `pipeline-e2e-check-mtds-20260821-012839-18224b` completed with 12 leg cells: 1 passed, 7 failed, and 4 explicitly skipped. The green per-row gate remains open: both trades rows had zero parquet/capture proof, KALSHI canonical order-book had no matching rows, and the driver sampled a KALSHI instrument for the POLYMARKET trades row. Evidence: report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_prediction.json`, finished `2026-08-21T01:47:07Z`; issue `/plans/active/issues/prediction_smoke_checker_cross_venue_sampling_2026_08_21.md`.
- [ ] [BACKEND] P1. Record one testnet verdict for every Prediction venue, including matching-engine simulation where that is the honest answer; Gate: every distinct venue has a written verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: every attempted path has a measured terminal result.
- [ ] [BACKEND] P1. Track every failed or absent Prediction row with its source and data type; Gate: no expected-unattempted row is reported as captured.
- [ ] [BACKEND] P0. Verify source-scoped exemptions, canonical checks, and manifest atom checks with a negative control; Gate: an invalid path or missing capture exits non-zero.

## Progress Log

**2026-08-20 — forked from W5.** Prediction has its own small AG batch so its distinct market-data shape remains
visible while retaining W4's comparable five-todo structure.

- [ ] [BACKEND] P0. Fix the cross-venue sampler, add the regression control, and rerun the exact four-row generator-scoped contract with force/skip/canonical, canonical-path, manifest-atom, and genuine `capture_status` evidence; Gate: every current row has a valid venue-scoped terminal result.

**2026-08-21 — slot 7 execution attempt (RED).** The generator re-measured four in-scope rows: `KALSHI` and `POLYMARKET`, each for `trades` and `book_snapshot_5`. The staging MTDS driver `pipeline-e2e-check-mtds-20260821-012839-18224b` completed at `2026-08-21T01:47:07Z` with 12 leg cells: 1 passed, 7 failed, and 4 skipped. `POLYMARKET/book_snapshot_5` canonical was the sole pass (`checked=7 canonical=7 raw=0`); both trades force/skip paths had zero parquet and no skip signal, both trades canonical checks had no matching rows, and `KALSHI/book_snapshot_5` canonical had no matching rows. The run also exposed the cross-venue sampler defect: `POLYMARKET/trades` was launched with `KALSHI:PREDICTION_MARKET:FEDHIKE-26DEC31`. The batch is therefore recorded as RED and the P0 contract is not claimed green. See [/plans/active/issues/prediction_smoke_checker_cross_venue_sampling_2026_08_21.md](/plans/active/issues/prediction_smoke_checker_cross_venue_sampling_2026_08_21.md).
