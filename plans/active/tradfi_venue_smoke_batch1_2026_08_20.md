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

- [x] ✅ [BACKEND] P0. Execute the canonical batch smoke contract for every current non-Databento TradFi row; Gate: each row proves capture, canonical path, manifest atom, and genuine capture status. Executed on real driver VM `pipeline-e2e-check-mtds-20260820-201322-1bf21a`; terminal report RED (`total=24`, `passed=0`, `failed=18`, `skipped=6`) because nested backfill launchers have no valid gcloud credentials. Tracked in [/plans/active/issues/tradfi_venue_smoke_nested_launcher_credentials_2026_08_20.md](/plans/active/issues/tradfi_venue_smoke_nested_launcher_credentials_2026_08_20.md).
- [ ] [BACKEND] P1. Record one testnet verdict for every TradFi venue, distinguishing non-Databento sourcing from the exempt cells; Gate: every distinct venue has a written verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage for provisionable credentials and record an honest unavailable result for accounts that cannot be provisioned; file an operator credential request when a credential gap is confirmed. Gate: no venue is silently omitted because it is TradFi.
- [ ] [BACKEND] P1. Track every failed or absent TradFi row with its resolved source and data type; Gate: a declared Databento exemption is never used to hide a non-Databento failure.
- [ ] [BACKEND] P0. Re-run the source resolver and prove the eight exemption cells are exactly CBOE/CME/NASDAQ/NYSE ohlcv_1m/ohlcv_1s; Gate: a non-exempt negative control fails.

## Progress Log

**2026-08-20 — forked from W5.** TradFi is deliberately split out because the exemption is source-scoped, not an
asset-group shortcut.

**2026-08-20 - execution evidence (slot-14):** driver `pipeline-e2e-check-mtds-20260820-201322-1bf21a` enumerated 8 rows and exited 1; report summary `total=24`, `passed=0`, `failed=18`, `skipped=6`. Phase-0 consolidation passed with 6 shards and 3328 rows in/out. Nested launcher credential failure is tracked in the issue above.
