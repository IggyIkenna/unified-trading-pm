---
doc_type: plan
title: Narrow expected_coverage.py CME entry to match VENUE_DATA_TYPE_CAPABILITIES (operator-ruled 2026-08-16)
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 8) on
  tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md's [DESIGN] P3 question: option 1 —
  expected_coverage.py is a "currently fetchable" list, not an aspirational target list. Narrow
  expected_coverage.py["tradfi"]["CME"] from ["trades", "ohlcv_1s", "ohlcv_1m", "tbbo"] to ["ohlcv_1s",
  "ohlcv_1m"] to match VENUE_DATA_TYPE_CAPABILITIES["CME"] (mirrors the already-fixed KRX/ICE/YAHOO_FINANCE
  registry-vs-adapter mismatches) — MTDS structurally never attempts CME trades/tbbo today
  (VENUE_DATA_TYPE_CAPABILITIES filters them upstream), so leaving them in expected_coverage.py produces a
  permanent, non-self-healing false gap in deployment-api's tradfi completion-percentage denominator.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, deployment-api]
scope: [engineer]
tags: [tradfi, cme, expected-coverage, honest-coverage, registry-drift]
related:
  [
    /plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 8, 2026-08-16 — operator ruling option 1 on tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md"
locked_by:
context_scope:
  [
    /plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
    unified-api-contracts/unified_api_contracts/registry/expected_coverage.py,
    unified-api-contracts/unified_api_contracts/registry/market_data_categories.py,
    deployment-api/deployment_api/services/data_status/reference_scope.py,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
locked_since:
resolved_by:
---

# Narrow expected_coverage.py CME entry to match VENUE_DATA_TYPE_CAPABILITIES

## Todos

- [ ] [DATA] P3. **Narrow `expected_coverage.py`'s CME entry from `["trades", "ohlcv_1s", "ohlcv_1m", "tbbo"]` to
      `["ohlcv_1s", "ohlcv_1m"]`, matching `VENUE_DATA_TYPE_CAPABILITIES["CME"]`.** RULED 2026-08-16 (operator):
      option 1 — narrow. Change
      `unified-api-contracts/unified_api_contracts/registry/expected_coverage.py`'s
      `EXPECTED_COVERAGE_BY_ASSET_GROUP["tradfi"]["CME"]` as above. Verify
      `deployment-api/deployment_api/services/data_status/reference_scope.py`'s denominator math updates
      correctly (CME trades/tbbo drop out of the "expected but uncaptured" gap count). QG both repos. Repo:
      unified-api-contracts, deployment-api.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator ruling)**: extracted from
  `tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md` for AO dispatch, since the parent doc
  stays `assigned_vm: NA`.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
