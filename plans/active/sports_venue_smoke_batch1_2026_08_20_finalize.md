---
doc_type: plan
title: sports venue smoke-test batch 1 — finalize — 2026-08-20
summary: Gated review and archival companion for the Sports venue smoke-test batch.
status: active
nature: process
asset_group: [sports]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, sports, finalize]
related: [/plans/active/sports_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
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
depends_on: [sports_venue_smoke_batch1_2026_08_20]
gate_on_depends: true
sequential: true
effort: low
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
context_scope: [/plans/active/sports_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
---

# Sports venue smoke-test batch 1 — finalize

- [x] ✅ [REVIEW] P1. Prove the Sports suite goes RED on a no-data or pre-floor unit; Gate: the negative-control run exits non-zero and identifies the rejected unit. — Verified against `sports_venue_smoke_batch1_2026_08_20.md`'s own execution-attempt-#2 evidence, independently re-fetched (not trusted from the batch plan's copy): the real VM run `pipeline-e2e-check-mtds-20260821-154512-a0ace0` (`--generator-scoped-sports`) finished with overall `EXIT_STATUS=1` (RED). Re-downloaded the cited report `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-08-20/data_pipeline_e2e_check_mtds_2026_08_20_sports.md` this session via UTL's `get_storage_client()` (never a subprocess `gsutil`, per the storage-code hard rule) and confirmed its frontmatter (`status: fail`, `total=99 passed=0 failed=75 ambiguous=0 skipped=24`) plus its per-shard Results table, which names the exact rejected unit and reason per row — e.g. `SPORTS:BET888SPORT:odds | force | failed | ... | no_parquet_under:gs://market-data-tick-sports-test-central-element-323112/raw_tick_data/by_date/day=2026-08-20/.../venue=BET888SPORT/` and `SPORTS:BET888SPORT:odds | canonical | failed | ... | canonical_no_matching_objects_in_test_bucket` for a no-data unit. This satisfies the Gate literally: a real (not simulated) negative-control run exited non-zero and identified the rejected unit by name and reason. Separately, `unified-api-contracts@25bcebdd` (content-verified this session) added `test_negative_control_path_fails_canonical_oracle` + the exemption-scoping tests, confirming the canonical-oracle negative control is source-scoped and asserts (pytest non-zero on failure) rather than silently passing.
- [x] ✅ [REVIEW] P2. Reconcile every Sports row and testnet verdict into the W5 contract; Gate: the data-floor and current generator output are both cited. — Appended a full reconciliation Progress Log entry to `/plans/active/venue_smoke_test_bar_2026_08_16.md` (2026-08-22, slot 19, review): cites the current generator output (`generate_venue_smoke_test_work_list.py`, 39 in-scope Sports rows) and the 2020-06-06 data floor (`/codex/02-data/sports-2020-06-data-floor.md` + the batch's slot-4 floor/oracle verification), reconciles the row-level RED execution result (VM `pipeline-e2e-check-mtds-20260821-154512-a0ace0`, 99 cells / 0 passed / 75 fail-closed / 24 skipped) and the full 33-venue testnet verdict table (0 real testnets; Groups A/B/C) into the shared W5 contract.
- [ ] [DOC] P2. Archive this batch and finalize plan after all todos are checked; Gate: archival and referrer validation pass.
