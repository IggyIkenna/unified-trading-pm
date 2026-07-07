---
doc_type: issue
title: 'DeFi lending protocols need a real A_TOKEN/DEBT_TOKEN (supply/borrow) instrument split for correct P&L — AAVE_V3/SPARK already split but mislabeled, COMPOUND_V3 splits into invalid enum values (crash risk), MORPHO has no split at all'
summary:
  'Operator flagged (reviewing the drilldown mockup): AAVE-style lending protocols mint a supply-side
  interest-bearing token (a-token) and a borrow-side debt token per reserve — economically distinct
  instruments, same relationship as SPOT_ASSET vs SPOT_PAIR in CeFi, and essential for correct P&L
  attribution (supply position earns yield, borrow position accrues interest — collapsing them into one
  instrument makes correct PnL impossible). Investigated against the real production catalogue
  (7,223-row instruments-store-defi-prd catalog.parquet) and found three different real states: (1)
  AAVE_V3 (171 rows: 113 A_TOKEN + 58 DEBT_TOKEN) and SPARK (14 rows: 8+6) already emit two separate
  InstrumentRecords per reserve with correct instrument_id keys, but every row is mislabeled
  instrument_type=LENDING instead of A_TOKEN/DEBT_TOKEN (a documented, half-finished migration — low
  severity since downstream ledger resolution parses the key, not the field); (2) COMPOUND_V3 (26 rows:
  13 SUPPLY + 13 BORROW) uses SUPPLY/BORROW as its instrument_type, which are not valid InstrumentType
  enum members at all — a real crash risk (UnknownInstrumentTypeError, by design "never mask with
  UNKNOWN") if this data ever reaches the ledger writer; (3) MORPHO (465 rows, all LENDING_MARKET) has
  NO supply/borrow split whatsoever — this is the real structural gap the operator described, and
  LENDING_MARKET is also not a valid InstrumentType (same crash-risk class as Compound). Confirmed the
  strategy/execution layer already ASSUMES the A_TOKEN/DEBT_TOKEN split exists
  (defi_position.py is_supply/is_borrow, PositionPortfolio.net_value = total_supply_value -
  total_borrow_value) — Compound V3 and Morpho currently violate that assumption in production. The
  lending_indices data_type schema itself is fine (already carries both supply+borrow rate/index fields
  per reserve on one row) — this is an instrument-identity gap, not a market-data schema gap.'
status: open
nature: notes
asset_group: [defi]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    lending,
    a-token,
    debt-token,
    aave,
    compound,
    morpho,
    instrument-identity,
    pnl-attribution,
    honest-coverage,
  ]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md,
  ]
created: 2026-07-07
parent_epic: instruments_master
priority: P1
source: 'Drilldown mockup review, 2026-07-07 — operator: "AAVE (and all borrowing and lending venues) have
  debt tokens and a-tokens... this is essential for accurate P&L... the mockup currently doesnt show
  lending and debt tokens for all of the lending and debt venues." Verified via direct read of the real
  production instrument catalogue + code trace across instruments-service/unified-api-contracts, not
  guessed.'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
last_updated: 2026-07-07
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **NOTIFY-OPERATOR class finding — P&L-correctness risk, cross-repo, one real crash path.** Compound V3
> and Morpho lending positions currently have no valid, distinct instrument identity for
> supply-vs-borrow — the strategy layer already assumes this split exists
> (`PositionPortfolio.net_value = total_supply_value - total_borrow_value`) and will misbehave (Compound:
> raise `UnknownInstrumentTypeError`; Morpho: silently have nowhere to represent a borrow position
> distinct from a supply position in the same market) the moment either protocol's positions are read
> for real P&L.

## What was actually found (real production catalogue read, 2026-07-07)

Read `gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet` (7,223 rows) directly
and traced the writer code in `instruments-service/instruments_service/reference_data/adapters/defi/`.

### 1. AAVE_V3 + SPARK — already split, mislabeled (cheap fix)

- AAVE_V3: 171 real rows = 113 `A_TOKEN` + 58 `DEBT_TOKEN` (e.g. `AAVE_V3-ARBITRUM:A_TOKEN:AWETH` vs
  `AAVE_V3-ARBITRUM:DEBT_TOKEN:DEBTWETH`) — `aave_v3.py:421-436` already emits two separate
  `InstrumentRecord`s per reserve, correctly keyed.
- SPARK: 14 real rows = 8 `A_TOKEN` + 6 `DEBT_TOKEN`, same pattern.
- **The bug**: every one of these rows is stamped `instrument_type=LENDING` (100%, verified), even though
  `InstrumentType.A_TOKEN`/`DEBT_TOKEN` already exist as real enum members
  (`unified_api_contracts/_instrument_enums.py:56-57`) and `aave_v3.py:400` hardcodes `LENDING` for both
  record types. This is a **known, documented, half-finished migration** —
  `unified_api_contracts/internal/schemas/contracts.py:522-524` literally says: "Handlers currently emit
  `instrument_type=LENDING` while the long-term canonical is `a_token` — both keys point to the same
  contract." **Low severity in practice**: `ledger_asset_resolution.py:172-197`
  (`derive_ledger_asset_fields`) parses the KEY's middle segment (`A_TOKEN`/`DEBT_TOKEN`), not the stored
  `instrument_type` field, so downstream ledger resolution already works correctly today despite the
  mislabel.

### 2. COMPOUND_V3 — split into invalid enum values (real crash risk)

- 26 real rows = 13 `SUPPLY` + 13 `BORROW` (`compound_v3.py:263,272`) as the `instrument_type` value.
- **`SUPPLY`/`BORROW` are not `InstrumentType` enum members at all.** `asset_class_for_instrument_type()`
  (`ledger_asset_resolution.py:161-165`) does `InstrumentType(instrument_type)` and raises
  `UnknownInstrumentTypeError` on anything unrecognized — by explicit design ("never mask with UNKNOWN").
  Any real Compound V3 supply/borrow position reaching the determinism-spine ledger writer today would
  **fail loud**, not silently misattribute — which is the correct failure mode, but it means Compound V3
  lending positions cannot currently be P&L-attributed in production at all.
- **Fix scope**: rename the instrument_type AND the key segment to `A_TOKEN`/`DEBT_TOKEN` (matching
  AAVE_V3/SPARK's pattern) — this changes the instrument_id key shape, so it needs a GCS partition
  migration, not just a field edit.

### 3. MORPHO — no split at all (the real structural gap)

- All 465 real rows are `LENDING_MARKET` (`morpho.py:191`), one row per (collateral, loan, marketId)
  triple — **zero supply/borrow distinction**. A strategy holding a Morpho supply position and a borrow
  position in the same market has nowhere to represent them as distinct instruments today.
- `LENDING_MARKET` is also not a valid `InstrumentType` — same `UnknownInstrumentTypeError` crash-risk
  class as Compound.
- **Fix scope**: an actual model change, not a relabel — two records per market
  (`MORPHO-{CHAIN}:A_TOKEN:{coll}-{loan}:{key8}` / `:DEBT_TOKEN:...`), following the AAVE_V3 pattern.

### 4. What's NOT broken

- `lending_indices`' schema already carries both supply-side (`liquidity_index`) and borrow-side
  (`variable_borrow_index`) fields on ONE row per reserve, regardless of protocol
  (`DEFI_AAVE_V3_LENDING_INDICES`; `lending_indices_handler.py:855`). The market-data rate/index time
  series was never the gap — this is purely an instrument-IDENTITY gap (can we name/track a supply
  position distinctly from a borrow position), not a market-data schema gap.
- The strategy/execution layer already codes to the A_TOKEN/DEBT_TOKEN split as the correct model —
  `unified_api_contracts/internal/domain/execution_service/defi_position.py:97-109` (`is_supply`/
  `is_borrow`), `strategy_service/position.py:31-34` (cites `AAVE_V3_ETH:A_TOKEN:AUSDT@ETHEREUM` as the
  canonical example), `PositionPortfolio.net_value = total_supply_value - total_borrow_value`. This
  confirms the operator's framing is exactly right — the fix target already exists in the strategy layer,
  the reference-data layer just hasn't caught up for 2 of 3 protocols checked.

## Not yet checked — same verification needed

FLUID, VENUS, BENQI, RADIANT, EULER_V2 (lending protocols shown in the mockup) and MARGINFI/SOLEND/KAMINO
(Solana lending) have NOT been checked against this same A_TOKEN/DEBT_TOKEN pattern — do not assume they
follow AAVE_V3's pattern or MORPHO's gap; each needs the same real-catalogue read before conclusions.

## Todos

- [ ] [FIX] P1. **AAVE_V3 + SPARK: fix the `instrument_type` mislabel** — change
      `aave_v3.py:400` (and SPARK's equivalent) to stamp `InstrumentType.A_TOKEN`/`DEBT_TOKEN` instead of
      the hardcoded `LENDING`, now that the enum members exist. Low-risk since the key already encodes
      the correct split and downstream ledger resolution already reads the key, not this field — mostly a
      cleanup to stop the field from lying, but confirm no consumer reads the raw `instrument_type` field
      directly for these two protocols before shipping (if one does, this becomes a coordinated
      migration, not a solo fix).
- [ ] [FIX] P0. **COMPOUND_V3: fix the invalid-enum crash risk** — rename `SUPPLY`/`BORROW` (not real
      `InstrumentType` members) to `A_TOKEN`/`DEBT_TOKEN` in `compound_v3.py:263,272`, matching AAVE_V3's
      pattern, including the key-segment rename. This is a P0 because it's a live
      `UnknownInstrumentTypeError` waiting to fire, not just a hygiene issue — needs a GCS partition
      migration for the existing 26 rows (key shape changes), plan the migration before flipping the
      writer.
- [ ] [CODE] P1. **MORPHO: add the missing A_TOKEN/DEBT_TOKEN split** — replace the flat 465
      `LENDING_MARKET` rows with two records per (collateral, loan, marketId) triple
      (`MORPHO-{CHAIN}:A_TOKEN:{coll}-{loan}:{key8}` / `:DEBT_TOKEN:...`), following `aave_v3.py`'s
      pattern for emitting two `InstrumentRecord`s per position-bearing entity. This is a real model
      change, not a relabel — size accordingly.
- [ ] [VERIFY] P1. **Check FLUID/VENUS/BENQI/RADIANT/EULER_V2 (EVM) and MARGINFI/SOLEND/KAMINO (Solana)**
      against the real production catalogue for the same A_TOKEN/DEBT_TOKEN pattern — do not assume any
      of them match AAVE_V3 or MORPHO without checking; each protocol's real tokenomics differ (some may
      have no separate debt token at all, e.g. isolated-pool designs with internal balance tracking only
      — report what's REALLY true per protocol, not an assumed uniform fix).
- [ ] [CODE] P2. **Update the drilldown mockup's DeFi lending nodes** to show the real A_TOKEN/DEBT_TOKEN
      split (target end-state) per protocol, with each protocol's current implementation status (already
      correct / mislabeled / crash-risk / missing) as an explicit note — this doc's findings are the
      source for that mockup update.

## Progress Log

- **2026-07-07** — Filed after the operator flagged (reviewing the drilldown mockup) that lending
  protocols need a real a-token/debt-token instrument split for correct P&L, same relationship as
  SPOT_ASSET vs SPOT_PAIR. Verified against the real production catalogue + code trace: AAVE_V3/SPARK
  already split but mislabeled (cheap fix), COMPOUND_V3 splits into invalid enum values (real crash
  risk, P0), MORPHO has no split at all (the real structural gap, needs a model change). Confirmed the
  strategy/execution layer already assumes the split exists — this is a reference-data layer catch-up,
  not a new architectural decision. No code changed yet; this is the findings ledger.
