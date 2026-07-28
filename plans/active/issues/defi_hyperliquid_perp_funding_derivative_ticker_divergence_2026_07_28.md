---
doc_type: issue
title:
  HYPERLIQUID perp_funding vs derivative_ticker funding_rate materially diverge — 2026-07-08 retirement's
  "byte-identical" premise not supported by measured data
summary: >-
  The re-scoped cross-source funding-parity check (defi_satellite_ao_dispatch_batch1_2026_07_25.md) measured
  HYPERLIQUID's realized perp_funding.funding_rate against derivative_ticker's embedded funding_rate field over 10 days
  sampled across the full 2023-05..2025-01 historical overlap window: only 60.7% of 2,640 compared rows matched within a
  2e-5 absolute tolerance, with a p90 divergence of 5.6e-5 and a worst-case divergence of 1.2e-3 (an order of magnitude
  larger than typical funding-rate values). This directly contradicts the 2026-07-08 registry-retirement comment's claim
  that "a live-fetch probe confirmed byte-identical/same-source funding data" for HYPERLIQUID/ASTER. Root cause
  identified: derivative_ticker.funding_rate is sourced from the S3 asset_ctxs archive's per-minute "funding" column (a
  continuously-updating live snapshot), while perp_funding.funding_rate is the REALIZED value from Hyperliquid's
  dedicated hourly-settlement `/fundingRates` endpoint — these are plausibly-related but NOT proven identical signals.
status: open
nature: process
asset_group: [defi, cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [defi, cefi, perp-funding, derivative-ticker, data-correctness, parity, hyperliquid]
related:
  [
    plans/active/issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md,
    plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
  ]
created: 2026-07-28
parent_epic: defi_master
priority: P1
source: [defi_satellite_ao_dispatch_batch1_2026_07_25.md re-scoped funding-parity todo, slot-6 data_engineering worker]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
locked_since:
---

# HYPERLIQUID perp_funding vs derivative_ticker funding_rate divergence (2026-07-28)

## What I found

Ran a read-only cross-source funding-parity check
(`market-tick-data-service/scripts/one_offs/defi_perp_funding_derivative_ticker_parity_check_2026_07_28.py`), per the
`[SCRIPT] P1` todo in `defi_satellite_ao_dispatch_batch1_2026_07_25.md` (source:
`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`).

**Step 1 — literal registry check.** Queried
`unified_api_contracts.registry.market_data_categories.VENUE_DATA_TYPE_CAPABILITIES` live: **0 venues** currently
declare BOTH `perp_funding` and `derivative_ticker`. DRIFT-SOLANA/PACIFICA-SOLANA (removed 2026-07-16) and
GMX-ARBITRUM/GMX-AVALANCHE (removed 2026-07-25) are confirmed absent; HYPERLIQUID/ASTER/LIGHTER-ZKSYNC had their
standalone `perp_funding` capability declaration RETIRED 2026-07-08 (`market_data_categories.py:168-186`) in favor of
`derivative_ticker`'s embedded `funding_rate` field, on the strength of a "live-fetch probe confirmed
byte-identical/same-source funding data" comment.

**Step 2 — historical manifest comparison (what the task actually needed).** Since the registry-declared-both set is
empty, checked the availability manifest for HISTORICAL captured rows of both data_types per candidate venue
(HYPERLIQUID, ASTER, EXTENDED-STARKNET, LIGHTER-ZKSYNC — every venue currently declaring `derivative_ticker`):

| Venue             | perp_funding captured dates               | derivative_ticker captured dates          | Comparable?                        |
| ----------------- | ----------------------------------------- | ----------------------------------------- | ---------------------------------- |
| HYPERLIQUID       | 209 (2023-05-12..2026-06-09, defi bucket) | 357 (2023-05-20..2026-07-17, cefi bucket) | YES — 169 overlapping days         |
| ASTER             | 0                                         | 948                                       | NO — no perp_funding ever captured |
| EXTENDED-STARKNET | 0                                         | 7                                         | NO — no perp_funding ever captured |
| LIGHTER-ZKSYNC    | 0                                         | 0                                         | NO — no perp_funding ever captured |

Only HYPERLIQUID has real historical data for both sides. Sampled 10 days evenly spread across the 169-day overlap
window, up to 8 coins/day, matched each `perp_funding` hourly-settlement row against the NEAREST `derivative_ticker` row
within a ±3 minute window (funding intervals are ≥1h, so this window cannot cross an hour boundary):

- **2,640 rows compared, match_pct = 60.7%** at a 2e-5 absolute tolerance
- divergence distribution: min=0, p50=1.47e-5, p90=5.55e-5, **max=1.20e-3**
- worst offenders cluster on BANANA (2023-09-20, diffs up to 1.2e-3) and CRV/BCH (diffs ~7e-4) — i.e. genuinely
  different values, not float-precision noise (funding rates here are O(1e-4) at the largest, so a 1.2e-3 divergence
  is >10x the signal's own typical magnitude)

**Root cause** (`market_tick_data_service/adapters/hyperliquid_s3.py::_parse_asset_ctxs_csv`, lines ~740-785):
`derivative_ticker.funding_rate` = the S3 `asset_ctxs` archive's raw `funding` CSV column, sampled ~once per minute —
Hyperliquid's continuously-updating LIVE funding-rate snapshot. `perp_funding.funding_rate` (captured separately, via
the dedicated `/fundingRates` REST endpoint, `_migrated_hyperliquid_*`/per-coin files in the defi bucket) is the
REALIZED value Hyperliquid actually charged at each hourly settlement. These are related (both derive from Hyperliquid's
premium-based funding formula) but are **not proven to be the same number** — the parity check shows they materially
diverge on a meaningful fraction of hours, particularly during periods where the intra-hour premium moved significantly
between snapshots.

## Why it matters

This directly undermines the evidentiary basis for two decisions:

1. The 2026-07-08 registry retirement of standalone `perp_funding` for HYPERLIQUID/ASTER/LIGHTER-ZKSYNC (in favor of
   `derivative_ticker`'s embedded field) — its stated justification ("byte-identical... confirmed") does not hold up
   under a real historical comparison for HYPERLIQUID, the one venue with data to check.
2. The still-open `[DESIGN] P1` "demote perp_funding to a derived view" todo in
   `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`, which is explicitly gated on this
   parity evidence ("If parity FAILS, this todo closes as 'keep both — parity report explains why'"). Parity does NOT
   hold for HYPERLIQUID at the sampled scale — the DESIGN todo should close on that basis, not proceed to demote.

Per the data-pipeline-correctness HARD RULE, a real cross-source divergence on a canonical DeFi funding data_type is a
data-correctness finding, not a rounding footnote — flagging per findings-triage rather than resolving inline (the
script's own instruction: "File any genuine divergence via standard findings-triage — do not resolve inline").

## Recommended decision

- [x] [PM] P1. This issue doc itself (filed + cross-referenced) satisfies the "file any genuine divergence" instruction
      from the parity-check todo. DONE 2026-07-28 (slot-6, data_engineering).
- [ ] [OPERATOR] P1. Decide whether the 2026-07-08 HYPERLIQUID/ASTER/LIGHTER-ZKSYNC `perp_funding` retirement should be
      REVERSED (re-declare `perp_funding` as a live capability and resume capturing it going forward) given the measured
      60.7% match rate, or whether `derivative_ticker`'s embedded funding_rate is an ACCEPTABLE proxy for downstream
      consumers despite the divergence (e.g. if features/strategy consumers only need the live/estimate signal, not the
      realized-settlement value). This is a genuine judgment call about what "funding rate" should mean downstream — not
      a worker-determinable fact.
- [ ] [DESIGN] P1. Close the `[DESIGN] P1` "demote perp_funding to a derived view" todo in
      `defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md` citing this doc: parity FAILS for
      HYPERLIQUID (the only venue with comparable historical data), so the todo should resolve as "keep both — parity
      report explains why" per its own stated closing condition, pending the operator decision above.
- [ ] [DIAG] P2. Determine whether `derivative_ticker.predicted_funding_rate` (the asset_ctxs `premium` column,
      currently unused in this comparison) tracks `perp_funding.funding_rate` more closely than `funding_rate` does — if
      Hyperliquid's realized hourly rate is actually closer to a smoothed/clamped function of the premium than to the
      raw per-minute funding snapshot, this would change which derivative_ticker column is the right proxy. Repo:
      market-tick-data-service (read-only re-run of the same parity script with `--dt-column predicted_funding_rate` or
      an ad-hoc variant).

## Progress log

- 2026-07-28 (slot-6, data_engineering): Filed from the `defi_satellite_ao_dispatch_batch1_2026_07_25.md` funding-parity
  todo's own findings-triage instruction. Script:
  `market-tick-data-service/scripts/one_offs/defi_perp_funding_derivative_ticker_parity_check_2026_07_28.py` (read-only,
  lifecycle-marked). Full report appended to the source issue doc's Progress log
  (`defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`).
