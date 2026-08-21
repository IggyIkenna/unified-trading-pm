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
- [x] ✅ [BACKEND] P0. Verify the Sports data floor and source-scoped Databento/canonical checks with a negative control; Gate: pre-floor or no-data probes fail rather than pass. — `unified-api-contracts@25bcebdd` + runtime evidence below.

## Progress Log

**2026-08-20 — forked from W5.** Sports keeps the data-floor rule in its context scope and follows W4's five-todo
AG batch shape.

**2026-08-21 — slot-4 verification.** The managed UAC quality gate completed with `ALL QUALITY GATES PASSED`
(390s). The runtime generator measured 364 declared pairs, 8 exact Databento exemptions, 356 in-scope rows, and 39
Sports rows. Direct assertions confirmed every Sports row resolves to a non-Databento source; each distinct resolved
source/data-type pair rejects the pre-floor `2020-06-05` window with the documented empty/inverted-range signal; and
the canonical-path negative control is rejected by `canonical_path_violations(require_pipeline_mode=True)`. The
source-scoped negative control `CBOE/ohlcv_24h -> yahoo` remains in scope and outside the eight-cell exemption set.
This closes only the floor/source/oracle verification todo; row-level production capture, manifest atoms, and genuine
capture statuses remain open under the first todo.
