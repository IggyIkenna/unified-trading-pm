---
title:
  "MVP scope tagging — a rules-derived MVP subset of the could-exist universe (instruments + features + strategies +
  models), toggled in data-status so missing-data only counts what's in-scope"
created: 2026-06-08
author: ikenna
parent_epic: epics/instruments_master.md
assigned_vm: vm-cross-cutting
status: active
priority: P1
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-06-08
source:
  - operator 2026-06-08 ("we need a pre-migration MVP tag — tag the instrument catalogue with what's MVP (data_types +
    base ccys per venue, instrument types, fixtures, leagues, sources); rules not hardcode; UAC/IS process rules into
    MVP; deployment UI/API toggle MVP in data-status, on-the-fly not manifest-baked; same for strategy/features/models
    catalogues so missing-data only looks at what can exist")
  - composes with CF-14 (IS-catalogue could-exist root) + proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md
---

# MVP scope tagging — the third denominator (all ⊇ could-exist ⊇ MVP)

> **The problem**: data-status today shows "missing" for any catalogued instrument with no data — including far-dated
> futures, non-MVP venues, and instrument types we've enumerated but don't yet intend to capture. That floods the
> denominator with things we don't EXPECT data for yet, so coverage reads falsely RED.
>
> **The fix**: a third denominator tier. **ALL catalogued ⊇ could-exist (genesis/launch/coverage, CF-14) ⊇ MVP
> (rules-filtered).** MVP is a **rules-derived SUBSET** of the could-exist universe — not a hardcoded list (we don't
> know future expiries) and not a manifest column we re-bake (the MVP definition is essentially a **global UAC config**
> that changes often). Data-status gets an **MVP toggle**: on → denominator = MVP cells only; off → the full could-exist
> universe. Same idea extends to the **features / strategy / model** registries, so every "what's missing" surface only
> counts what's in MVP scope.

## Core design

### 1. MVP is a predicate over the catalogue, computed on-the-fly (NOT a manifest column)

- **Rules live in UAC** (a global `mvp_scope` config) — the SSOT for "what is MVP". They are applied to the **instrument
  catalogue** (which holds the actual enumerated instruments + expiries, from
  `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md`) to produce the MVP subset at read time.
- **Grain = everything-or-nothing per `(asset_group, venue, instrument_type, data_type[, base_ccy])`** (+ sports
  `league`, prediction market-group, the `source`). **NOT** per-strike / per-expiry / per-turn — if a
  `(venue, instrument_type)` is MVP, ALL its catalogued expiries/strikes are in-scope (we don't filter the leaves, we
  don't know future expiries; the catalogue enumerates them, MVP includes the whole family).
- **On-the-fly, not baked**: `is_mvp(cell)` is evaluated against the UAC rule + the catalogue when data-status renders.
  Changing the MVP definition is a UAC config edit, not a manifest re-walk (avoids re-marking millions of rows for what
  is a config). Optional: a cached materialised `mvp_view` (catalogue × rules) refreshed with the catalogue scheduler,
  for performance — but the manifest itself stays MVP-agnostic.

### 2. The UAC `mvp_scope` rule shape (illustrative — finalise in Phase 1)

```
mvp_scope:
  cefi:    { venues: [binance, bybit, okx, deribit, hyperliquid], instrument_types: [PERPETUAL, SPOT], data_types: [trades, book_snapshot_5, funding_rate], base_ccys: [BTC, ETH, SOL, USDT], sources: [tardis, <venue>] }
  defi:    { venues: [uniswap_v3, curve, ...], instrument_types: [DEX_PAIR, LST, LENDING], data_types: [dex_swaps, lst_rates, ...] }
  tradfi:  { venues: [CME], instrument_types: [FUTURE, OPTIONS_CHAIN], data_types: [trades, ohlcv_1m], underliers: [ES, NQ, VX] }
  sports:  { leagues: [NFL, NBA, EPL, ...], data_types: [odds, results] }
  prediction: { venues: [POLYMARKET], market_groups: [...], data_types: [prediction_cqg, ohlcv_*] }
```

A cell is MVP iff it matches its asset_group's rule on every declared axis. A `(venue, instrument_type)` not in the rule
→ catalogued + could-exist but **NOT MVP** → excluded from the MVP denominator (no false "missing").

### 3. Producer: UAC or IS resolves rules → MVP predicate/view

- `unified_api_contracts` owns the `mvp_scope` config + `is_mvp(asset_group, venue, instrument_type, data_type, **axes)`
  predicate (pure, rule-only).
- instruments-service applies the predicate over the catalogue → an **MVP-tagged catalogue view** (`mvp: bool` column in
  the served catalogue, or a `catalogue.filter(is_mvp)` endpoint). This is the only place the catalogue (real expiries)
  meets the rules (scope) — keeps the manifest clean.

### 4. Consumer: deployment-api/UI MVP toggle in data-status

- deployment-api computes coverage over the 4-state UNION (CF-14) but with a `scope=mvp|could_exist|all` param: MVP →
  denominator = `is_mvp` cells only. UI adds an **MVP toggle button** in data-status (default ON pre-launch, so the
  board reflects MVP readiness, not the full enumerated universe).
- Reuses the existing could-exist denominator machinery (the G3 union view) — MVP is just an extra predicate on the
  denominator, not a new data path.

### 5. The parallel MVP catalogues (same pattern, other registries)

| Registry               | SSOT today                                        | MVP tag                                                                                                                          |
| ---------------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Instruments / data** | IS catalogue (CF-14)                              | `mvp_scope` rules above → data-status MVP toggle                                                                                 |
| **Features**           | delta_one `registry.py` (1,382 specs / 34 groups) | `mvp_features` — the subset of feature groups in MVP scope; features data-status only counts MVP feature × MVP instrument cells  |
| **Strategy**           | the archetype registry                            | `mvp_strategies` — the MVP archetypes (carry_staked_basis, arbitrage_price_dispersion); strategy-output coverage scoped to these |
| **Models (ML)**        | the model registry                                | `mvp_models` — the MVP model set; ml-output coverage scoped to these                                                             |

All four resolve from a UAC `mvp_scope` config (one SSOT, per-registry sections) and feed the same `scope=mvp` toggle in
deployment-api/UI so EVERY "what's missing" surface (data, features, strategies, models) only counts in-scope cells.

## Phases

- [ ] [DESIGN] P1. **Finalise the `mvp_scope` rule schema in UAC** — the axes per asset_group (venue/instrument_type/
      data_type/base_ccy/league/market_group/source), the everything-or-nothing grain, and the per-registry sections
      (data/features/strategy/models). Operator sign-off on the actual MVP membership lists.
- [ ] [CODE] P1. **UAC `is_mvp(...)` predicate + `mvp_scope` config** (pure, rule-only) + unit tests (a non-MVP venue is
      excluded; all expiries of an MVP future are included; a config edit changes membership with no data touch).
- [ ] [CODE] P1. **IS MVP-tagged catalogue view** — apply `is_mvp` over the rolled-up catalogue; serve `mvp: bool` (or a
      filtered endpoint). On-the-fly; optional cached `mvp_view` refreshed with the catalogue scheduler.
- [ ] [CODE] P1. **deployment-api `scope=mvp|could_exist|all`** on the data-status coverage endpoint (denominator =
      `is_mvp` cells when mvp) — reuse the G3 union machinery.
- [ ] [UI] P2. **deployment-ui MVP toggle** in data-status (default ON pre-launch) — `[UI]` + `pw:L2 ✓` + regression
      spec per the playwright gate.
- [ ] [CODE] P2. **Features/strategy/model MVP sections** — extend `mvp_scope` + apply the same predicate to the feature
      registry / archetype registry / model registry; scope their data-status the same way.
- [ ] [DATA] P2. **Verify**: with MVP ON, data-status shows ~100% for captured MVP cells and does NOT count non-MVP
      catalogued instruments as missing; with MVP OFF, the full could-exist universe is shown (the gap is honest, not
      hidden).

## Open questions (operator)

1. **Rule home — UAC vs IS?** UAC (global config, IS applies it) keeps the rule SSOT with the contracts; IS owns the
   catalogue it's applied to. Recommend UAC-config + IS-applies. Confirm.
2. **On-the-fly vs cached `mvp_view`?** On-the-fly is simplest + always-fresh; a cached view helps if data-status
   renders over millions of cells. Recommend on-the-fly first, cache only if slow.
3. **Default toggle state** in data-status — ON (MVP-readiness view) pre-launch? Recommend ON.

## Composes with

CF-14 (could-exist root — MVP is its subset) · `proper_instrument_catalogue_lifecycle_rollup_2026_06_04.md` (the
catalogue MVP is filtered from) · `macro_micro_econ_data_capture_audit_2026_06_05.md` (capability vs backfill — MVP is
the "what we intend to capture for launch" cut) · the G3 deployment union view (the denominator machinery MVP refines).
