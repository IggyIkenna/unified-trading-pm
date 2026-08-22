---
doc_type: plan
title: prediction venue smoke-test batch 1 — finalize — 2026-08-20
summary: Gated review and archival companion for the Prediction venue smoke-test batch.
status: complete
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

> **🗄️ ARCHIVED 2026-08-22 (slot 18, review) — all 3 todos done.** Findings are recorded durably in
> [`/plans/active/venue_smoke_test_bar_2026_08_16.md`](/plans/active/venue_smoke_test_bar_2026_08_16.md)'s
> 2026-08-22 (slot 18) Progress Log entry. `superseded_by`: none.

- [x] ✅ [REVIEW] P1. Prove the Prediction suite goes RED on a no-data unit; Gate: the negative-control run exits non-zero and names the missing capture. — Independently re-verified (not trusted from the batch plan's own copy): `market-tick-data-service`'s `TestPredictionBatchManifestNegativeControl` (4 tests: missing-capture, missing-manifest-atom, and both `expected_unattempted` variants) re-run this session, all 4 PASS, proving `_verify_batch_shard` returns `status="failed"` — never `"passed"` — for every PREDICTION no-data variant. Cross-checked against the real E2E driver report (`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_prediction.json`, fetched live via UTL `download_from_storage`): `total=12, passed=0, failed=8, skipped=4`, with reasons explicitly naming the missing capture, e.g. `no_parquet_under:gs://market-data-tick-pred-test-central-element-323112/raw_tick_data/by_date/day=2026-08-18/asset_group=prediction/venue=POLYMARKET/`. Gate confirmed both at the unit-negative-control level and the real terminal RED run.
- [x] ✅ [REVIEW] P2. Reconcile every Prediction row and testnet verdict into the W5 contract; Gate: cited evidence resolves against the current generator output. — Re-ran `generate_venue_smoke_test_work_list.py` live (347 in-scope rows this measurement); Prediction cell unchanged at exactly 4 rows (`KALSHI`/`POLYMARKET` × `trades`/`book_snapshot_5`), matching the batch's own citation. Added a reconciliation entry to `venue_smoke_test_bar_2026_08_16.md`'s Progress Log recording all 4 rows' terminal RED state + both venues' testnet verdicts (KALSHI: real testnet, credential gap filed `BLK-3d8c3d9e`; POLYMARKET: no testnet, matching-engine simulation is the honest answer) — `unified-trading-pm@<SHA>`.
- [x] ✅ [DOC] P2. Archive this batch and finalize plan after all todos are checked; Gate: archival and referrer validation pass. — Both docs `git mv`'d to `plans/archive/2026_08/`, archived banners added pointing at `venue_smoke_test_bar_2026_08_16.md` (where the durable findings live), and the two real `related:`/`context_scope:` referrers to the pre-archive path (`venue_smoke_test_bar_finalize_2026_08_16.md`, `issues/kalshi_demo_testnet_credential_request_2026_08_22.md`) repointed at the still-active W5 doc, not left pointing at the archived plan.
