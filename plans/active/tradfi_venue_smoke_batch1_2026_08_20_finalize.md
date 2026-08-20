---
doc_type: plan
title: tradfi venue smoke-test batch 1 — finalize — 2026-08-20
summary: Gated review and archival companion for the non-Databento TradFi venue smoke-test batch.
status: active
nature: process
asset_group: [tradfi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, tradfi, finalize]
related: [/plans/active/tradfi_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/tradfi_consolidated_closeout_2026_07_18.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
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
depends_on: [tradfi_venue_smoke_batch1_2026_08_20]
gate_on_depends: true
sequential: true
effort: low
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
context_scope: [/plans/active/tradfi_venue_smoke_batch1_2026_08_20.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
---

# TradFi venue smoke-test batch 1 — finalize

- [ ] [REVIEW] P1. Prove the non-Databento TradFi suite goes RED on a no-data unit; Gate: the negative-control run exits non-zero and names the row.
- [ ] [REVIEW] P2. Reconcile all eight in-scope rows, all eight exemptions, and testnet verdicts into the W5 contract; Gate: source resolution is re-run, not copied from a stale count.
- [ ] [DOC] P2. Archive this batch and finalize plan after all todos are checked; Gate: archival and referrer validation pass.
