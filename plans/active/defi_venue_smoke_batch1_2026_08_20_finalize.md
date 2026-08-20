---
doc_type: plan
title: defi venue smoke-test batch 1 — finalize — 2026-08-20
summary: Gated review and archival companion for the DeFi venue smoke-test batch.
status: active
nature: process
asset_group: [defi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, defi, finalize]
related: [/plans/active/defi_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
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
depends_on: [defi_venue_smoke_batch1_2026_08_20]
gate_on_depends: true
sequential: true
effort: low
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
context_scope: [/plans/active/defi_venue_smoke_batch1_2026_08_20.md, /plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
---

# DeFi venue smoke-test batch 1 — finalize

- [ ] [REVIEW] P1. Prove the DeFi suite goes RED on a known no-data venue/data-type unit; Gate: the negative-control run exits non-zero for the missing capture and the log names the unit.
- [ ] [REVIEW] P2. Reconcile every DeFi row and testnet verdict into the W5 contract; Gate: cited evidence resolves and no row is counted from a stale denominator.
- [ ] [DOC] P2. Archive this batch and its finalize plan only after all todos are checked and the six-step archival ritual succeeds; Gate: archive paths and corpus referrers validate.
