---
doc_type: plan
title: cefi venue batch smoke tests — batch 1 — 2026-08-20
summary: Per-asset-group smoke-test batch for the 70 in-scope CeFi (venue, data_type) rows from the canonical work list.
status: active
nature: process
asset_group: [cefi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, cefi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/cefi_consolidated_closeout_2026_07_18.md]
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

# CeFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Filter the generator output to `asset_group=cefi`; re-run it before acting because 70 is a measured scope.

## Todos

- [ ] [BACKEND] P0. Execute the canonical batch smoke contract for every current CeFi row, proving captured rows, canonical paths, manifest reconciliation, and genuine capture status; Gate: no zero-row unit exits successfully.
- [ ] [BACKEND] P1. Record one testnet verdict for every CeFi venue, including simulation where no venue testnet exists; Gate: every distinct venue in the live work list has a verdict.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage where credentials are available or provisionable and mark the remainder BLOCKED-CREDENTIALS; Gate: every attempted path has a measured terminal result.
- [ ] [BACKEND] P1. Track every failed or absent CeFi row with its source and data type; Gate: no failure is hidden behind a declared-absence or expected-unattempted status.
- [ ] [BACKEND] P0. Verify source-scoped exemptions and canonical oracle/manifest checks with a negative control; Gate: an invalid path or missing capture fails loudly.

## Progress Log

**2026-08-20 — forked from W5.** This batch follows the five-todo W4 decomposition and keeps its denominator
re-runnable through the UAC generator.
