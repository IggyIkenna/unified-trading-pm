---
doc_type: plan
title: prediction venue smoke-test batch 1 — finalize — 2026-08-20
summary: Gated review and archival companion for the Prediction venue smoke-test batch.
status: active
nature: process
asset_group: [prediction]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, prediction, finalize]
related: [/plans/active/prediction_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md]
created: "2026-08-20"
last_updated: "2026-08-20"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: review
drift_direction: none
depends_on: [prediction_venue_smoke_batch1_2026_08_20]
gate_on_depends: true
sequential: true
effort: low
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
context_scope: [/plans/active/prediction_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/prediction_consolidated_closeout_2026_07_18.md]
---

# Prediction venue smoke-test batch 1 — finalize

- [x] ✅ [REVIEW] P1. Prove the Prediction suite goes RED on a no-data unit; Gate: the negative-control run exits non-zero and names the missing capture. — Independently re-verified (not trusted from the batch plan's own copy): `market-tick-data-service`'s `TestPredictionBatchManifestNegativeControl` (4 tests: missing-capture, missing-manifest-atom, and both `expected_unattempted` variants) re-run this session, all 4 PASS, proving `_verify_batch_shard` returns `status="failed"` — never `"passed"` — for every PREDICTION no-data variant. Cross-checked against the real E2E driver report (`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_prediction.json`, fetched live via UTL `download_from_storage`): `total=12, passed=0, failed=8, skipped=4`, with reasons explicitly naming the missing capture, e.g. `no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-18/asset_group=prediction/venue=POLYMARKET/`. Gate confirmed both at the unit-negative-control level and the real terminal RED run.
- [ ] [REVIEW] P2. Reconcile every Prediction row and testnet verdict into the W5 contract; Gate: cited evidence resolves against the current generator output.
- [ ] [DOC] P2. Archive this batch and finalize plan after all todos are checked; Gate: archival and referrer validation pass.
