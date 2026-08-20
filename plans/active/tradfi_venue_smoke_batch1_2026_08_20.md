---
doc_type: plan
title: tradfi venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 8 in-scope non-Databento TradFi (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [tradfi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, tradfi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/tradfi_consolidated_closeout_2026_07_18.md, /codex/02-data/tradfi-databento-sourcing-ssot.md]
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
context_scope: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /codex/02-data/tradfi-databento-sourcing-ssot.md, /codex/02-data/availability-manifest-and-data-status.md, unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py]
locked_by:
locked_since:
supersedes:
superseded_by:
source: /plans/active/venue_smoke_test_bar_2026_08_16.md
---

# TradFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Only the eight current non-Databento rows are in scope; the eight Databento cells remain explicit exemptions.

## Todos

- [ ] [BACKEND] P0. Execute the canonical batch smoke contract for every current non-Databento TradFi row; Gate: each row proves capture, canonical path, manifest atom, and genuine capture status.
- [ ] [BACKEND] P1. Record one testnet verdict for every TradFi venue, distinguishing non-Databento sourcing from the exempt cells; Gate: every distinct venue has a written verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: no venue is silently omitted because it is TradFi.
- [ ] [BACKEND] P1. Track every failed or absent TradFi row with its resolved source and data type; Gate: a declared Databento exemption is never used to hide a non-Databento failure.
- [ ] [BACKEND] P0. Re-run the source resolver and prove the eight exemption cells are exactly CBOE/CME/NASDAQ/NYSE ohlcv_1m/ohlcv_1s; Gate: a non-exempt negative control fails.

## Progress Log

**2026-08-20 — forked from W5.** TradFi is deliberately split out because the exemption is source-scoped, not an
asset-group shortcut.
