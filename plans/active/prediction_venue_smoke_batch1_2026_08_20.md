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

- [ ] [BACKEND] P0. Execute the canonical batch smoke contract for every current Prediction row; Gate: each row proves capture, canonical path, manifest atom, and genuine capture status.
- [ ] [BACKEND] P1. Record one testnet verdict for every Prediction venue, including matching-engine simulation where that is the honest answer; Gate: every distinct venue has a written verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and mark unavailable accounts BLOCKED-CREDENTIALS; Gate: every attempted path has a measured terminal result.
- [ ] [BACKEND] P1. Track every failed or absent Prediction row with its source and data type; Gate: no expected-unattempted row is reported as captured.
- [ ] [BACKEND] P0. Verify source-scoped exemptions, canonical checks, and manifest atom checks with a negative control; Gate: an invalid path or missing capture exits non-zero.

## Progress Log

**2026-08-20 — forked from W5.** Prediction has its own small AG batch so its distinct market-data shape remains
visible while retaining W4's comparable five-todo structure.
