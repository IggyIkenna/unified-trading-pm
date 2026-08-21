---
doc_type: plan
title: sports venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 39 in-scope Sports (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [sports]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, sports, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/sports_consolidated_closeout_2026_07_19.md]
created: "2026-08-20"
last_updated: "2026-08-20"
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
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/availability-manifest-and-data-status.md, /codex/02-data/sports-2020-06-data-floor.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# Sports venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Apply the Sports 2020-06 data floor; filter the generator output to `asset_group=sports` at execution time.

## Todos

- [ ] [BACKEND] P0. Execute the canonical batch smoke contract for every current Sports row above the 2020-06-06 data floor; Gate: rows, canonical paths, manifest atoms, and genuine capture statuses are measured per unit.
- [ ] [BACKEND] P1. Record one testnet verdict for every Sports venue, including matching-engine simulation where appropriate; Gate: every distinct venue has a written verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: no missing credential is treated as a wiring absence.
- [ ] [BACKEND] P1. Track every failed or absent Sports row with its source and data type; Gate: expected-unattempted is never presented as captured.
- [ ] [BACKEND] P0. Verify the Sports data floor and source-scoped Databento/canonical checks with a negative control; Gate: pre-floor or no-data probes fail rather than pass.

## Progress Log

**2026-08-20 — forked from W5.** Sports keeps the data-floor rule in its context scope and follows W4's five-todo
AG batch shape.
