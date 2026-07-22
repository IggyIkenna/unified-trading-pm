---
doc_type: issue
title:
  DEFI_VENUE_PHASE "live" has two contradictory definitions, and 11 venues with real, months-long MTDS capture are
  mislabeled "pipeline"
summary:
  unified-api-contracts/unified_api_contracts/registry/defi_venues.py carries two conflicting definitions of
  phase=="live" (2026-05-07 UI-facing block comment vs 2026-06-29 IS-producibility invariant); a 2026-07-22 15-protocol
  capture survey found 11 venues with real, verified, months-long MTDS-handler-based data capture still labeled
  "pipeline", which per the 2026-05-07 definition hides them from deployment-ui's live DEFI panel and (if
  completeness_pct denominators key off phase) may undercount real coverage.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, deployment-ui, deployment-api, market-tick-data-service]
scope: [engineer]
tags: [defi, ssot-contradiction, phase, coverage]
related: [distinct_values_noncanonical_audit_2026_07_20.md]
created: "2026-07-22"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
source: sub-agent, distinct_values_noncanonical_audit_2026_07_20.md DeFi-venue-adapter-test-and-add workflow (wxmjyre65)
---

## Finding

`unified-api-contracts/unified_api_contracts/registry/defi_venues.py` carries two definitions of `DEFI_VENUE_PHASE`'s
`"live"` value that do not agree:

1. **Block comment, added 2026-05-07** (lines ~404-418): `"live"` = "MTDS backfill is shipping data; manifest has rows"
   — a **data-availability** definition. `"pipeline"` = "UAC declares the venue... not yet plumbed in MTDS; manifest has
   zero rows." The deployment-ui DEFI panel uses this to decide whether a venue renders in the main live-coverage
   section or a separate roadmap section.
2. **Invariant comment, referencing `instrument_universe_registry_consolidation_2026_06_29.md`** (line ~423):
   `INVARIANT: phase=="live" ⟺ venue is IS-producible (in _build_defi_venues())` — an **instruments-service-adapter**
   definition, enforced by `test_defi_venue_phase_coverage`.

These are different claims. A venue can satisfy (1) — MTDS is actively capturing real data, manifest has rows — while
failing (2) — no `instruments-service` reference-data adapter exists (e.g. a bare on-chain `eth_call` handler living
entirely in `market-tick-data-service`, never touching `instruments-service`).

## Evidence: 11 venues that satisfy (1) but are labeled "pipeline" (violating (1)'s own intent)

Per a 2026-07-22 real sample-day-backfill survey (`distinct_values_noncanonical_audit_2026_07_20.md`, "DeFi venue
additions" operator ruling — test-then-add), the following venues have real, verified, months-long MTDS capture and
`phase="pipeline"` in the current registry:

ANKR, FRAX, MAKER, STADER, STAKEWISE, SWELL, MANTLE, ACROSS, STARGATE, FLASHBOTS, ALCHEMY — each confirmed via a live
sample-day backfill against real on-chain/API data (row counts through 2026-06-21 cited in existing
`defi_venue_capabilities.py` comments, e.g. STADER 1,078 rows, SWELL 1,162 rows, STAKEWISE 937 rows). None of these have
a dedicated `instruments-service` reference-data adapter — all capture through `market-tick-data-service` handlers
(`lst_rates_handler.py`, `vault_share_price_handler.py`, `bridge_events_handler.py`, `mev_events_handler.py`,
`gas_fee_handler.py`) that call on-chain RPCs / REST APIs directly, never routing through IS.

(BLAZESTAKE, KAMINO_LENDING, MORPHOVAULTS were already correctly `"live"` or fixed this session. JUPITER is a separate
build-vs-drop judgment call, not part of this phase question — its swap volume already flows through directly-captured
pools.)

## Why this matters

- If deployment-ui's DEFI panel genuinely follows definition (1), these 11 venues are hidden from the main live-coverage
  section and shown only in "roadmap" — misrepresenting them as not-yet-captured when they have months of real data.
- If any `completeness_pct` / honest-coverage denominator calculation keys off `DEFI_VENUE_PHASE` (not yet checked as
  part of this finding — needs its own read of the consumer), the same 11 venues could be silently excluded from
  coverage math they should count toward.

## What was deliberately NOT done

Not flipping these 11 venues to `"live"` in this session — doing so would violate the enforced invariant test
(`test_defi_venue_phase_coverage`, definition (2)) without first resolving which definition is actually authoritative,
or extending `_build_defi_venues()`'s IS-producibility to cover them (a much larger, separate body of work: building 11
new instruments-service reference-data adapters for protocols that currently have no natural IS-adapter shape — LST-rate
and vault-share-price protocols query a single on-chain rate, not an instrument universe).

## Recommended next step (design decision needed, not a mechanical fix)

1. Read every real consumer of `DEFI_VENUE_PHASE` (deployment-ui DEFI panel render logic, any completeness_pct /
   honest-coverage denominator code) to determine which definition — (1) data-availability or (2) IS-producibility — the
   codebase actually NEEDS `"live"` to mean for each consumer. They may need to diverge into two separate flags rather
   than share one.
2. If (1) is what the UI panel needs: reconcile the invariant test/comment (deprecate or narrow it) and flip the 11
   venues.
3. If (2) is genuinely required for correctness (e.g. IS is the reference-data SSOT and something downstream needs a
   real instrument universe, not just a raw capture stream): the 11 venues stay `"pipeline"` under the CURRENT
   correct-as-designed semantics, and the fix is instead to correct the misleading 2026-05-07 block comment (and any
   docs/UI copy that describes "pipeline" as "not yet capturing data") to say what "pipeline" actually means today:
   "capturing data via MTDS, no dedicated IS reference-data adapter."

Either resolution requires reading the actual consumers first — do not guess.
