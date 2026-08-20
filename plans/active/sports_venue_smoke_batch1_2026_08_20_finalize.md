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

- [ ] [REVIEW] P1. Prove the Sports suite goes RED on a no-data or pre-floor unit; Gate: the negative-control run exits non-zero and identifies the rejected unit.
- [ ] [REVIEW] P2. Reconcile every Sports row and testnet verdict into the W5 contract; Gate: the data-floor and current generator output are both cited.
- [ ] [DOC] P2. Archive this batch and finalize plan after all todos are checked; Gate: archival and referrer validation pass.
