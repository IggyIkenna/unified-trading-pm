---
doc_type: issue
title:
  SportsArbDutchingEngine shares StrategyArchetype.ARBITRAGE_PRICE_DISPERSION with ArbitragePriceDispersionEngine but
  isn't in the factory dispatch table — a "sports arb" strategy instance silently gets the wrong (CEFI) engine
summary: >-
  strategy_service.engine.strategies.v2.factory.ARCHETYPE_ENGINE_REGISTRY maps
  StrategyArchetype.ARBITRAGE_PRICE_DISPERSION to ArbitragePriceDispersionEngine only. SportsArbDutchingEngine (a real,
  unit-tested, dutched N-venue sports-odds arbitrage engine) declares the SAME ARCHETYPE enum value but is never
  imported into factory.py, so register_instance() for any "sports arb" strategy instance (e.g. the SPORTS_ARBITRAGE
  archetype slot) silently instantiates ArbitragePriceDispersionEngine instead — a different engine expecting a
  different features shape (candidate_venues dispersion, not decimal_odds_{outcome}_{venue} books). Found while building
  a hermetic Group-B sports backtest smoke script.
status: open
nature: notes
asset_group: [sports]
stage: [strategy]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [strategy-service, sports, arbitrage, archetype, factory, engine-dispatch, wiring-gap]
related:
  [
    plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md,
    codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
  ]
created: "2026-07-21"
parent_epic: sports_master
priority: P2
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [sports_predictions_live_mode_and_backtest_execution_orphaned-006]
resolved_by:
locked_by:
depends_on: []
---

# SportsArbDutchingEngine is unreachable via the normal registration path

## What I found

`strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py:93`:

```python
class SportsArbDutchingEngine(BaseArchetypeEngineV2):
    ARCHETYPE = StrategyArchetype.ARBITRAGE_PRICE_DISPERSION
```

`strategy_service/engine/strategies/v2/factory.py`'s `ARCHETYPE_ENGINE_REGISTRY` — the sole
`StrategyArchetype → engine class` dispatch table `V2EngineOrchestrator.register_instance()` uses via
`ArchetypeEngineFactory.build()` — maps:

```python
StrategyArchetype.ARBITRAGE_PRICE_DISPERSION: ArbitragePriceDispersionEngine,
```

`SportsArbDutchingEngine` is exported from `arbitrage_structural/__init__.py`'s `__all__` (line 32) and has real,
passing unit tests (`tests/unit/engine/strategies/v2/test_sports_arb_dutching.py`, 9 tests, dutched-stake math,
best-venue-per-outcome selection, overround-savings filtering) — it is NOT dead code by any normal definition. But it is
never imported into `factory.py`, so `ARCHETYPE_ENGINE_REGISTRY` has no entry pointing to it. Since `StrategyArchetype`
is a flat enum with no asset-group axis, and the dispatch table is a strict 1:1 `archetype → engine class` map (no
asset-group-aware routing anywhere in `factory.py` or `V2EngineOrchestrator.register_instance()`), the two engines
collide on the identical enum value with no way for the factory to pick between them.

**Confirmed not a duplicate** — `ArbitragePriceDispersionEngine` (`price_dispersion.py`) has zero
`decimal_odds`/sports-book handling; it reads a `candidate_venues` price-dispersion shape (crypto/CEFI-oriented).
`SportsArbDutchingEngine` needs the `decimal_odds_{outcome}_{venue}` multi-venue sports-odds book
(`sports_arb_dutching.py`, confirmed via its own passing test suite). These are genuinely different engines for
genuinely different inputs, not redundant code.

**Concretely, right now**: `archetype_slots_sports.py`'s `SPORTS_ARBITRAGE` slot
(`ArchetypeSlotMapping(archetype=StrategyArchetype.ARBITRAGE_PRICE_DISPERSION, slot_label="ARBITRAGE_PRICE_DISPERSION@unity-betfair-matchbook-...")`)
is the ONLY sports-facing consumer of this archetype value today. Any code that calls `register_instance()` with that
slot's definition gets `ArbitragePriceDispersionEngine` — verified directly:

```
engines: {'ARBITRAGE_PRICE_DISPERSION@...': <...price_dispersion.ArbitragePriceDispersionEngine object ...>}
```

fed a real sports odds book (`decimal_odds_home_win_pinnacle` etc. in `features`), it silently returns `[]` — no error,
no warning, just zero instructions, because it's reading the wrong keys out of `features`.

## Why it matters

Anyone wiring up the `SPORTS_ARBITRAGE` slot for a real backtest or (eventually) live paper-run gets a **silently-inert
strategy instance** — no crash, no log warning, just an engine that never trades because it's the wrong engine reading
the wrong shape. This is exactly the "reports success while doing nothing" class of bug this workspace treats as
structurally unacceptable elsewhere. It also means `SportsArbDutchingEngine`'s real, tested logic has never actually run
inside `V2EngineOrchestrator` — only via direct unit-test instantiation
(`SportsArbDutchingEngine(identity=..., target_equity=..., params=...)`, bypassing the factory entirely).

## Recommended decision

Needs an architecture decision, not a mechanical fix — filing the facts + options rather than picking one:

- **Option A** — give `SportsArbDutchingEngine` its own `StrategyArchetype` enum value (e.g. `ARBITRAGE_SPORTS_DUTCHING`
  or similar) in UAC, update `archetype_slots_sports.py`'s `SPORTS_ARBITRAGE` slot to reference it, and add the factory
  entry. Cleanest long-term fix; requires a UAC schema addition (new enum member, not a breaking change) + updating the
  one slot definition.
- **Option B** — make `ARCHETYPE_ENGINE_REGISTRY` (or a wrapper around it) asset-group-aware, so the SAME archetype enum
  value can route to a different engine class per `StrategyInstanceDefinition`'s implied asset group (sports vs cefi).
  Bigger change — no other archetype needs this today, so it's new architecture for one case.
- **Option C** — if `SportsArbDutchingEngine` turns out to be superseded/unwanted (e.g. the sports-arbitrage product
  direction changed since it was written), delete it per the "no shims, delete deprecated code" rule instead of wiring
  it in. Needs an operator/quant call — the engine reads as complete + tested, not abandoned, so this seems unlikely but
  is listed for completeness.

## Todos

- [x] ✅ [BACKEND] P2. Operator picked Option A (dedicated archetype, unified-api-contracts@cf28a962 +
      strategy-service@545a527b). Added `StrategyArchetype.ARBITRAGE_SPORTS_DUTCHING` to UAC (`ARCHETYPE_TO_FAMILY` + a
      real 2-leg `archetype_leg_spec_seeds.py` structure citing the engine); `SportsArbDutchingEngine.ARCHETYPE`
      repointed from `ARBITRAGE_PRICE_DISPERSION` to the new value; `factory.py`'s `ARCHETYPE_ENGINE_REGISTRY` now maps
      it to `SportsArbDutchingEngine`; `archetype_slots_sports.py`'s `SPORTS_ARBITRAGE` slot re-pointed with
      `initial_config` keys matching the engine's real params (`outcome_set`/`candidate_venues`/
      `min_overround_savings_pct`, not the old `ArbitragePriceDispersionEngine` shape); `archetype_defaults.py` got a
      Kelly tier (`_TIER_STABLE_STRUCTURAL`, matching `ARBITRAGE_PRICE_DISPERSION`) + a `GREENFIELD_ARCHETYPES` entry
      (no legacy v0/v1 strategy to migrate); `target_universe/catalog_trading.py` got a new
      `build_arbitrage_sports_dutching()` builder (4 seed rows: epl/laliga/seriea 3-way + nba 2-way) wired into
      `catalog.py`'s `_BUILDERS_BY_ARCHETYPE`. Updated `test_sports_arb_dutching.py`'s identity fixture +
      `test_ml_directional_continuous.py`'s `family_map`/`_archetype_min_params` + `test_archetype_leg_spec.py`'s
      hardcoded real/not_registered counts (53→54) to match. (repo: strategy-service, unified-api-contracts)
      **Correction (2026-07-21) — strategy-service@28c534af**: `GREENFIELD_ARCHETYPES` classification above was wrong.
      `legacy_strategy_mapping.yaml`'s `SPORTS_ARB_CROSS_BOOK` row (venues `unity,betfair,matchbook`, identical to the
      live slot) was already tagged `ARBITRAGE_PRICE_DISPERSION` — a real legacy predecessor that was never re-pointed
      alongside the live slot, not a genuinely greenfield archetype. Re-pointed the row to `ARBITRAGE_SPORTS_DUTCHING`,
      updated its `initial_config` to the engine's real params (matching the live-slot fix — the old
      `venues`/`edge_method`/`min_margin_pct` keys were never read by `SportsArbDutchingEngine`), removed the
      `GREENFIELD_ARCHETYPES` entry, and regenerated the migration content-hash pin. Full test suite +
      `quality-gates.sh` green.
- [ ] [SCRIPT] P3. Once wired, extend or replace `strategy-service/scripts/run_sports_arb_backtest.py` (currently
      targets `SPORTS_VALUE_BETTING` / `ML_DIRECTIONAL_EVENT_SETTLED` as a workaround for this gap) to also exercise the
      real `SportsArbDutchingEngine` path with the multi-venue odds-book fixture shape already proven in
      `tests/unit/engine/strategies/v2/test_sports_arb_dutching.py`. (repo: strategy-service)

## Codex SSOTs

`codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md` (sibling archetype doc pattern to follow
if Option A ships a new archetype doc).
