---
doc_type: codex-ssot
title: TradFi Bond Instrument-Type Decision (2026-04-21)
summary:
  Decision record — no bond instrument-type is added; treasury ETFs (TLT/IEF) on IBKR are spot equities covered by the
  existing STAT_ARB_PAIRS_FIXED×TRADFI×spot cell, resolving the Wave-5 audit TradFi·bond GAP without an enum change
  (actual Treasury futures stay dated_future).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, tradfi, catalogue, ssot-audit, instruments]
related:
  [
    /codex/09-strategy/architecture-v2/strategy-registry-v2.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/legacy-family-migration.md,
  ]
created: 2026-04-21
authoritative_for: [TradFi treasury-ETF bond instrument-type decision]
referenced_by: [/codex/09-strategy/architecture-v2/legacy-family-migration.md]
owner:
last_reviewed:
code_refs:
---

# TradFi Bond Instrument-Type Decision (2026-04-21)

**Context:** Audit driver — `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` Wave 6 Task C. The v1
strategy registry has one entry, `TRADFI_BOND_MEAN_REV_HUF_1D` (name: "Bond Mean Reversion"), that the Wave 5
equivalency audit flagged as **GAP (cell)** because UAC `archetype_capability_manifest.json` had no TradFi·bond
SUPPORTED cell under `STAT_ARB_PAIRS_FIXED`.

This note resolves that gap **without** introducing a `bond` instrument type enum value.

---

## 1. Decision

**No new `bond` instrument type is added. Treasury ETFs (TLT, IEF, SHY, …) traded on IBKR are `spot` equities by
instrument type. The existing `STAT_ARB_PAIRS_FIXED × TRADFI × spot` cell already covers them.**

## 2. Rationale

### 2.1 What does `TRADFI_BOND_MEAN_REV_HUF_1D` actually trade?

From `unified-trading-system-ui/lib/strategy-registry.ts:2762-2800`:

- `description: "Mean reversion strategy on treasury ETFs (TLT, IEF). Statistical arbitrage on yield curve."`
- Instruments: `IBKR:ETF:TLT` + `IBKR:ETF:IEF` — Vanguard/iShares treasury-duration ETFs.
- `strategyType: "Mean Reversion"`, `archetype: "MEAN_REVERSION"` (v1 archetype).

These are **cash-settled equity ETFs** — not zero-coupon bonds, not corporate bonds, not CME Treasury futures. They
trade like any other equity ticker on IBKR. Their `InstrumentType` in v2 is `spot`.

### 2.2 Why not add a `bond` instrument type?

- **No new execution path required.** TLT/IEF already flow through the existing IBKR spot adapter. The instrument-type
  axis exists to drive execution / margining / roll logic. None of those differ for treasury ETFs vs any other IBKR
  equity.
- **System-First rule** (`SUB_AGENT_MANDATORY_RULES.md` §0). v2 instrument-type vocabulary is deliberately narrow
  (`spot / perp / dated_future / option / lending / staking / lp / event_settled`). These are EXECUTION-layer
  categories, not asset-class labels. "Bond" is an asset-class label, not an execution primitive. If we needed a
  bond-specific execution primitive (e.g. on-the-run Treasury auctions through TreasuryDirect, or a fixed-income DMA
  venue with yield-quoted orders), we would add it. We don't.
- **Actual Treasury futures** (ZB / ZN / ZF / ZT on CME) are `dated_future` + `roll_mode: "rolling"` — already supported
  in v2 under `STAT_ARB_PAIRS_FIXED × TRADFI × dated_future`. Bond futures / cross-venue Treasury-yield-curve arb is
  already covered.

### 2.3 Why is the Wave-5 audit's "no TradFi·bond cell" verdict wrong?

The audit looked for a cell keyed on `(TRADFI, bond)`. Because `bond` is not an instrument-type vocabulary value, no
such key exists — and the audit concluded SUPPORTED was absent. The correct lookup is `(TRADFI, spot)`: the
`STAT_ARB_PAIRS_FIXED × TRADFI × spot` cell IS declared at `archetype_capability_manifest.json` with
`venue_ids: ["ibkr"]`, `signal_variants: ["zscore_reversion"]`, and a representative slot label. Treasury ETFs fit this
cell perfectly.

## 3. Implementation

No enum changes. No new cell. The Wave-6 Task C code change is **representative-slot-label discoverability** — add a
treasury-ETF example slot label under the existing `STAT_ARB_PAIRS_FIXED × TRADFI × spot` cell so operators can see this
use case at a glance. See `archetype_capability_manifest.json` delta in this wave.

## 4. Consumer-side mapping

v1 row retires with the rest of Wave 6 Task E. v2 equivalent:

| v1 strategy_id                | v2 archetype           | v2 category | v2 instrument_type | v2 venue | v2 signal variant  |
| ----------------------------- | ---------------------- | ----------- | ------------------ | -------- | ------------------ |
| `TRADFI_BOND_MEAN_REV_HUF_1D` | `STAT_ARB_PAIRS_FIXED` | `TRADFI`    | `spot`             | `ibkr`   | `zscore_reversion` |

Slot label (v2 canonical):

- `STAT_ARB_PAIRS_FIXED@ibkr-tlt-ief-daily-usd-prod`

## 5. Out of scope (explicit non-goals)

These are NOT addressed by this decision — if any become real, they get a follow-up plan:

- **Cash bonds / Corporates / Govies via TreasuryDirect or a dedicated fixed-income venue.** Would require a new venue
  in UAC + potentially an `InstrumentType.BOND` if execution differs materially from spot.
- **Yield-quoted orders.** IBKR API accepts yield-quote orders for eligible products, but we route everything
  price-quoted today. No change.
- **Roll logic on Treasury futures.** Already handled under `dated_future` + roll-service (BL-10).

## 6. Cross-references

- `/codex/09-strategy/architecture-v2/strategy-registry-v2.md` — v2 registry overview.
- `/codex/09-strategy/architecture-v2/category-instrument-coverage.md` — per-archetype cell matrix narrative.
- `/codex/09-strategy/architecture-v2/legacy-family-migration.md` § 2.2 — v1→v2 equivalency audit (post-Wave-6 zero-gap
  state).
