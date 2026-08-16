---
doc_type: issue
title:
  CME trades/tbbo declared "expected" in expected_coverage.py but excluded from VENUE_DATA_TYPE_CAPABILITIES —
  data-status denominator vs MTDS fetch-gate drift
summary: >-
  Verifying `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s "CME mbp_10/trades/tbbo billing-gated
  declaration" todo found `VENUE_DATA_TYPE_CAPABILITIES["CME"]` (unified-api-contracts) correctly excludes
  mbp_10/trades/tbbo entirely (only ohlcv_1s/ohlcv_1m declared) — so no false "full-history-available" claim exists, and
  the actual billing-entitlement guard (`databento_subscription_allowlist.py`) is independently correct. But a SEPARATE
  registry, `expected_coverage.py::EXPECTED_COVERAGE_BY_ASSET_GROUP["tradfi"]["CME"]`, still lists `["trades",
  "ohlcv_1s", "ohlcv_1m", "tbbo"]` — trades/tbbo included, mbp_10 excluded. `get_expected_data_types_for_venue` (the
  function `venue_fetch.py` uses to gate actual MTDS fetch attempts) reads only `VENUE_DATA_TYPE_CAPABILITIES`, not
  `expected_coverage.py` — so MTDS will never attempt CME trades/tbbo, but deployment-api's data-status denominator (the
  only confirmed consumer of `EXPECTED_COVERAGE_BY_ASSET_GROUP`) may still count them as expected-but-uncaptured,
  producing a permanent false gap in tradfi's completion percentage.
status: open
nature: notes
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, deployment-api]
scope: [engineer, admin]
tags: [tradfi, registry-drift, expected-coverage, venue-data-type-capabilities, honest-coverage, databento]
related:
  [
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
    /plans/archive/2026_08/issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md,
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
  ]
created: 2026-08-15
author: slot-29 (backend_engineer)
source: ["tradfi_satellite_ao_dispatch_batch13-4de61ec21884, VERIFY CME mbp_10/trades/tbbo billing-gated declaration"]
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
estimate_class: research
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
last_updated: 2026-08-15
parent_epic: tradfi_master
priority: P2
---

> **✅ ARCHIVED 2026-08-16** (na-eligibility-audit, tradfi tranche) — sole todo ruled + extracted to
> `/plans/active/tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md` (+ finalize); checkbox flip was missed
> when that extraction landed, fixed in the same pass as this archival. 0 open todos, `locked_by` empty.

# CME trades/tbbo: expected_coverage.py vs VENUE_DATA_TYPE_CAPABILITIES drift

## What I found

Live-read (2026-08-15) of `unified-api-contracts/unified_api_contracts/registry/market_data_categories.py`:

```python
"CME": {
    "ohlcv_1s": "2019-01-01",
    "ohlcv_1m": "2019-01-01",
},
```

`mbp_10`/`trades`/`tbbo` are absent — not declared "billing-gated", not declared "full-history-available", simply not
present at all. This matches the 2026-05-15 OHLCV-only-MVP scope decision (`_mvp_scope_rules.py` comment: "Still NO
trades/tbbo (billing-gated L1/L2 microstructure)... not MVP") and the 2026-07-15 archived issue's own finding that the
post-cutover registry restoration was never re-applied. `get_expected_data_types_for_venue("CME")`
(`market_data_categories.py:3105`) reads `VENUE_DATA_TYPE_CAPABILITIES.get("CME").data_types` directly (non-empty, so no
fallback) → returns `["ohlcv_1m", "ohlcv_1s"]` only. This is the function `venue_fetch.py`'s per-shard dispatch
intersects every fetch request against — so CME `trades`/`tbbo`/`mbp_10` can never reach the Databento fetch call today,
by design.

Separately, `unified-api-contracts/unified_api_contracts/registry/expected_coverage.py`:

```python
"CME": ["trades", "ohlcv_1s", "ohlcv_1m", "tbbo"],
```

`trades`/`tbbo` ARE listed here (mbp_10 is not). Grepped every consumer of `EXPECTED_COVERAGE_BY_ASSET_GROUP`
(unified-api-contracts internal + `deployment-api/deployment_api/services/data_status/reference_scope.py`) —
deployment-api's data-status reference scope is the only cross-repo consumer found. That means the data-status page's
completion/denominator math likely still counts CME `trades`/`tbbo` as expected coverage, but MTDS structurally never
attempts them (filtered upstream by `VENUE_DATA_TYPE_CAPABILITIES`) — a permanent, non-self-healing gap in that metric,
the same failure shape as the already-fixed KRX/ICE/YAHOO_FINANCE registry-vs-adapter mismatches, but on the
`expected_coverage.py` axis instead of the capabilities axis.

## Why it matters

If deployment-api's tradfi completion percentage / "missing_data_types" surfaces CME `trades`/`tbbo` as an open gap,
that reading is misleading — no code path exists to ever close it while `VENUE_DATA_TYPE_CAPABILITIES["CME"]` stays at
its current OHLCV-only scope. Anyone triaging a tradfi completion shortfall could burn time chasing an
unfetchable-by-design cell.

## Recommended decision

Not fixed here — this is the same class of judgment call already resolved for KRX/ICE/YAHOO_FINANCE (narrow the registry
to match reality vs. build the missing wiring), and it interacts with the still-open post-cutover restoration question
(`tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`, archived `status: complete` but its own Phase 1-2 registry
re-merge was never actually re-applied). Two options, either legitimate:

1. **Narrow** `expected_coverage.py["tradfi"]["CME"]` to `["ohlcv_1s", "ohlcv_1m"]` (matches current fetch reality,
   mirrors the KRX/ICE precedent) — low-risk, but abandons `expected_coverage.py`'s apparent role as the "eventual
   restoration target" list.
2. **Leave as-is** if `expected_coverage.py` is intentionally the aspirational/target list (distinct from
   `VENUE_DATA_TYPE_CAPABILITIES`'s "currently fetchable" list) — but then deployment-api's denominator math needs to be
   confirmed to NOT penalize completion% for cells in this intentionally-aspirational gap, which was not verified in
   this pass.

## Open work (tracked todos)

- [x] ✅ [DESIGN] P3. **RULED + EXTRACTED 2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator ruling) →
      `/plans/active/tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md` (+ finalize).** Checkbox flip was
      missed when the Progress Log entry below was written (na-eligibility-audit 2026-08-16, dispatch agt-45ad7b,
      caught this citing-not-flipped gap). Operator/architecture decision: is `expected_coverage.py` a "currently
      fetchable" list (in which case narrow CME to drop trades/tbbo, matching `VENUE_DATA_TYPE_CAPABILITIES`) or an
      "eventual target" list? **Ruled: option 1** — narrow CME to drop trades/tbbo. (repos: unified-api-contracts,
      deployment-api)

## Progress Log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **ARCHIVE — 0 open todos.** The sole
  todo's ruling + extraction was already recorded in the entry below, but the checkbox itself was never flipped to
  cite it — fixed above. This doc now has zero open todos; running the 6-step archival ritual in the same pass.
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator ruling)**: option 1 — "currently fetchable"
  list, narrow CME to drop trades/tbbo. Extracted to
  `/plans/active/tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md` (+ finalize) for AO dispatch,
  since this doc stays `assigned_vm: NA`.
