---
doc_type: plan
title: defi venue batch smoke tests — batch 1 — 2026-08-20
summary: >-
  Per-asset-group smoke-test batch for the 232 in-scope DeFi (venue, data_type) rows produced by the canonical
  source-scoped work-list generator; Databento cells are excluded by source, never by asset group.
status: active
nature: process
asset_group: [defi]
stage: [data, execution]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, market-data-processing-service, features-service, execution-service]
scope: [engineer]
tags: [venue-readiness, smoke-test, defi, ao-dispatch, satellite-batch]
related: [/plans/active/venue_smoke_test_bar_2026_08_16.md, /plans/active/venue_smoke_test_bar_finalize_2026_08_16.md, /plans/active/defi_consolidated_closeout_2026_07_18.md]
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

# DeFi venue smoke-test batch 1

> **Parent**: [/plans/active/venue_smoke_test_bar_2026_08_16.md](/plans/active/venue_smoke_test_bar_2026_08_16.md).
> Row list: run `unified-api-contracts/scripts/generate_venue_smoke_test_work_list.py` and filter `asset_group=defi`;
> the measured 232-row count is evidence, not a hardcoded denominator.

## Todos

- [ ] [BACKEND] P0. Execute the canonical batch smoke contract for every current DeFi row, proving captured rows, canonical paths, manifest reconciliation, and genuine capture status; Gate: the live generator output and per-row evidence contain no silent zero-row pass.
- [ ] [BACKEND] P1. Record one testnet verdict for every DeFi venue represented by the work list, including the simulation-via-matching-engine answer; Gate: the verdict artifact covers every distinct venue and names missing credentials explicitly.
- [ ] [BACKEND] P1. Add or run testnet smoke coverage where credentials already exist or can be provisioned, while recording an honest unavailable result where they do not; retain the full path and file an operator credential request when a credential gap is confirmed. Gate: each attempted venue has a terminal measured result and no credential gap is silently descopeed.
- [ ] [BACKEND] P1. Convert every failed or absent DeFi row into a tracked follow-up with venue, data type, source, and owner rather than treating absence as success; Gate: every non-passing row has a linked plan todo or an explicit declared-absence reason.
- [ ] [BACKEND] P0. Confirm the batch preserves source-scoped Databento exemptions and does not bypass the canonical-path oracle or manifest atom checks; Gate: a rerun reports the same exemption rule and a negative-control path fails.

## Progress Log

**2026-08-20 — forked from W5.** Five dispatchable todos mirror W4's per-asset-group decomposition. The current
denominator is re-derived at execution time; the 232-row measurement is only the dispatch scope observed on authoring.
