---
doc_type: issue
title: >-
  Sports MDPS instrument_type axis carries 30 real market-token values (ASIAN_HANDICAP_*, MATCH_ODDS, MATCH_ODDS_LAY,
  OVER_UNDER_*, SPORT) with no canonical registration — genuine detector/SSOT gap, same class as the defi swaps_ohlcv D6
  finding
summary: >-
  distinct_values_noncanonical_audit_2026_07_20.md's 2026-07-28 census refresh (dispatched via
  cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md's line-191 todo) found sports.instrument_types carrying 34
  non-canonical values, up from 3 on 2026-07-25. Traced the root: `market-data-processing-service`'s
  `canonical_writer_shaping.py::_type_token_from_canonical_id` (shipped fix for
  sports_closeout_batch1_ao_ready_2026_07_24.md todo 2) DELIBERATELY resolves the `instrument_type` for a sports MDPS
  candle row from the 3rd colon-segment of the canonical id (the MARKET, not the bookmaker) via
  `ODDS_API_MARKET_TO_CANONICAL` — so `ASIAN_HANDICAP_0_25`/`MATCH_ODDS`/`OVER_UNDER_2_5`/etc are real, correctly and
  deliberately produced MDPS output (the market-generalization branch decided by the operator's "branch the OHLCV
  mapping by instrument market type" ruling), not a writer bug or wrong-axis mis-stamp. They were simply never added to
  the `InstrumentType` enum or any accepted-exception set, so the distinct-values detector correctly badges them
  non-canonical every run. This is the SAME class of finding as
  `defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md` (D6) — real MDPS-produced values missing from a UAC
  canonical set, where a blind enum addition needs the denominator/blast-radius caution from that doc's own RESULT 4
  ("UAC canonical-set additions are NOT safe-code") applied first. NOT investigated further here (read-only audit
  scope); filed per this session's findings-closure requirement.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, market-data-processing-service, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    sports,
    honest-coverage,
    canonicalisation,
    instrument_types,
    candle-processing,
    mdps,
    manifest,
    distinct-values,
    denominator-blast-radius,
  ]
related:
  [
    /plans/archive/2026_07/distinct_values_noncanonical_audit_2026_07_20.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
  ]
created: "2026-07-28"
last_updated: "2026-07-28"
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
source: >-
  distinct_values_noncanonical_audit_2026_07_20.md line-191 todo (owning-plan reconciliation of every current
  non-canonical value), dispatched via cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    market-data-processing-service/market_data_processing_service/app/core/canonical_writer_shaping.py,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    unified-api-contracts/unified_api_contracts/_instrument_enums.py,
  ]
supersedes:
superseded_by:
resolved_by:
depends_on: []
---

# Sports MDPS instrument_type market-token SSOT gap

## What I found

Live `GET /distinct-values/sports` (`deployment-api`'s `_distinct_values.py`, called in-process today,
`source_date=2026-07-28`) badges 34 `instrument_types` non-canonical, up from 3 on the 2026-07-25 refresh cited in
`distinct_values_noncanonical_audit_2026_07_20.md`. Of those 34:

- **4 already tracked, no new action**: `odds` (operator ruling 2026-07-17, "closed as not-a-defect" —
  `unified_api_contracts/_instrument_enums.py:95-108`), `exchange_odds`/`fixed_odds` (owned by
  `sports_closeout_exchange_fixed_odds_fork_2026_07_25.md`, the fork target values), `ODDS` uppercase (owned by
  `sports_consolidated_closeout_2026_07_19.md` line 406's open `[DATA] P0` "Step (3) data migration" revert todo).
- **30 NEW, this finding**: `ASIAN_HANDICAP_-0`, `ASIAN_HANDICAP_0`, `ASIAN_HANDICAP_0_25`, `ASIAN_HANDICAP_0_5`,
  `ASIAN_HANDICAP_0_75`, `ASIAN_HANDICAP_1`, `ASIAN_HANDICAP_1_25`, `ASIAN_HANDICAP_1_5`, `ASIAN_HANDICAP_1_75`,
  `ASIAN_HANDICAP_2`, `ASIAN_HANDICAP_M0_25`, `ASIAN_HANDICAP_M0_5`, `ASIAN_HANDICAP_M0_75`, `ASIAN_HANDICAP_M1`,
  `ASIAN_HANDICAP_M1_25`, `ASIAN_HANDICAP_M1_5`, `ASIAN_HANDICAP_M1_75`, `ASIAN_HANDICAP_M2`, `MATCH_ODDS`,
  `MATCH_ODDS_LAY`, `OVER_UNDER_1_5`, `OVER_UNDER_1_75`, `OVER_UNDER_2`, `OVER_UNDER_2_25`, `OVER_UNDER_2_5`,
  `OVER_UNDER_2_75`, `OVER_UNDER_3`, `OVER_UNDER_3_25`, `OVER_UNDER_3_5`, `SPORT`.

Traced the writer: `market_data_processing_service/app/core/canonical_writer_shaping.py::_type_token_from_canonical_id`
(lines 258-283) resolves a sports MDPS candle row's `instrument_type` from the 3rd colon-segment of the canonical
instrument id (the MARKET token — `SPORT:BOOKMAKER:MARKET:LEAGUE:SEASON:HOME-AWAY::SELECTION`), canonicalised via
`ODDS_API_MARKET_TO_CANONICAL` (lower-cased key lookup, upper-cased fallback). This is the shipped, deliberate fix for
`sports_closeout_batch1_ao_ready_2026_07_24.md` todo 2 (the earlier bug where position 1, the BOOKMAKER, was wrongly
returned as `instrument_type`). The function comment confirms the market-token resolution is intentional, not a
regression.

## Why it matters

`InstrumentType` has no member for any of these 30 market tokens, and `_ACCEPTED_EXCEPTIONS` in `_distinct_values.py`
does not cover `("instrument_types", "sports")`, so every one of these genuinely-produced, correct MDPS rows badges as
drift on the distinct-values panel every single run — the exact "detector sees real output as false alarm" pattern this
audit's own D6 finding already documented for defi `swaps_ohlcv_*`. Left unresolved, this permanently inflates the
sports non-canonical count (currently the majority of the sports total: 30 of 45) and obscures genuine drift in the rest
of the axis.

## Recommended decision

Mirror the D6 disposition exactly: do NOT blindly add these 30 tokens to `InstrumentType` (that enum is a GLOBAL,
cross-asset-group universe — bloating it with sport-market-specific tokens is the same "canonical-bloat" concern
`defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md` raised for defi, and `InstrumentType` additions were already
flagged as "NOT safe-code" in this plan's own RESULT 4 — denominator/blast-radius needs measuring first). Two candidate
remediation paths, needing an operator/design call before either is executed:

1. **Accepted-exception set** (fastest, matches the `options_chain`/`futures_chain` precedent already shipped for
   tradfi/cefi in `_distinct_values.py`) — add `("instrument_types", "sports")` to `_ACCEPTED_EXCEPTIONS`, keyed off a
   new UAC export (e.g. `SPORTS_MARKET_TOKEN_ACCEPTED_NONCANONICAL_INSTRUMENT_TYPES`, derived from
   `ODDS_API_MARKET_TO_CANONICAL`'s value set) so the panel stops flagging real, deliberately-produced output without
   asserting these are `InstrumentType`-enum-shaped.
2. **Registry addition** — if the market tokens are meant to be first-class canonical `instrument_type` values (not just
   a detector-exception), add them to a sports-scoped canonical set analogous to
   `DATA_TYPES_BY_ASSET_GROUP`/`VENUES_BY_ASSET_GROUP`, then measure the denominator-expansion blast radius before
   shipping (same caution as D5/D6).

- [ ] [DESIGN] P2. Operator/design decision: accepted-exception (path 1, fast, matches shipped precedent) vs. registry
      addition (path 2, needs denominator-blast-radius measurement first) for the 30 sports market-token
      `instrument_type` values. Source: this doc.
- [ ] [BACKEND] P2. Execute the chosen path in `deployment-api`/`unified-api-contracts` once decided, unit-test the
      before/after (34 → ~4 non-canonical), and re-run `/distinct-values/sports` to confirm.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — todo 1 is a literal `[DESIGN]` 'operator/design
  decision' (accepted-exception set vs registry addition for 30 sports market tokens) and todo 2 is gated on it — the
  doc's own Recommended-decision section spells out why a blind `InstrumentType` enum addition is unsafe (D6
  canonical-bloat / denominator blast radius precedent)
