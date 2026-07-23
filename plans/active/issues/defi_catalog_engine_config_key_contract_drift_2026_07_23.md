---
doc_type: issue
title:
  strategy-service catalog/engine config-key contract has no validation — 6 of 9 checked DeFi archetypes cannot execute
  a single real trade
summary:
  A mechanical pre-flight sweep (catalog-emitted config keys vs each engine's actual params.get/str_param reads) across
  the "orphaned archetype" build found that most DeFi archetypes checked so far are functionally dead in every
  environment today — three distinct bug classes (a crashing config-key mismatch, a silent config-key mismatch, and an
  intentionally-stubbed unbuilt dependency), none of which any test or gate catches.
status: open
nature: issue
asset_group: defi
stage: strategy
repos: [strategy-service]
scope: engineer
tags: [defi, strategy-archetypes, catalog-engine-contract, silent-failure, test-gap, money-path]
related:
  [
    defi_archetype_universe_no_curtailment_mechanism_2026_07_23,
    pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21,
  ]
created: 2026-07-23
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: agent-discovered (orphaned-archetype build, mechanical pre-flight sweep, 2026-07-23)
depends_on: []
---

# strategy-service catalog/engine config-key contract has no validation — systemic, cross-archetype

## What this is

While wiring paper-replay tick builders for the 12 "orphaned" (`engine_tick_builder_unwired`) DeFi archetypes
(operator-approved build, see [[defi_archetype_universe_no_curtailment_mechanism_2026_07_23]]), a cheap mechanical check
— before dispatching a build agent for each archetype, compare its catalog builder's emitted `initial_config` dict keys
against what its registered v2 engine's `on_tick`/`__init__` actually reads (`str_param`/`decimal_param`/ `params.get`)
— found that **6 of the first 9 archetypes checked have a real defect that prevents them from ever emitting a real trade
instruction, in ANY environment (paper, batch, live), today.** This is bigger than the tick-builder-wiring effort it was
found inside — it's a pre-existing production gap, discovered as a side effect.

## Per-archetype status (9 checked so far)

| Archetype                               | Verdict                        | Bug class                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | Evidence                                                                                                                                                            |
| --------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CARRY_STAKED_BASIS` (already-drivable) | ✅ CLEAN, shipped this session | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `strategy-service@e93902d8`                                                                                                                                         |
| `CARRY_STAKED_BASIS_DATED`              | 🔴 TOTAL BLOCK — crashes       | Config-key mismatch (`lst_protocol`/`dated_venue`/`dated_expiry` vs engine's real `REQUIRED_PARAMS` = `{staking_protocol, native_asset, lst_asset, perp_venue, perp_instrument, spot_venue}`)                                                                                                                                                                                                                                                                                                                                   | `ValueError` at `register_instance()` in every env — reproduced empirically. See doc's Phase 1 addendum.                                                            |
| `CARRY_RECURSIVE_STAKED`                | ✅ CLEAN, shipped this session | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `strategy-service@23bd8b76`                                                                                                                                         |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY`   | 🔴 TOTAL BLOCK — silent stub   | `staking_yield_enabled=false` → `CarryRecursiveStakedEngine.on_tick()` unconditionally `return []`s, pending an execution-service `RecursiveLoopOrchestrator` integration that isn't wired from the strategy side                                                                                                                                                                                                                                                                                                               | `recursive_staked.py:194-199`; orchestrator itself DOES exist (`execution-service/.../recursive_loop_orchestrator.py`) but strategy-side stub never calls out to it |
| `CARRY_BASIS_PERP_INV`                  | 🔴 TOTAL BLOCK — silent stub   | Same as above (shares the engine)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Same                                                                                                                                                                |
| `CARRY_BASIS_DATED`                     | 🔴 TOTAL BLOCK — silent        | Config-key mismatch — catalog emits `cash_venue`/`dated_venue`/`instrument` (or `cash_instrument`); engine (`basis_dated.py`) requires `spot_venue`+`future_venue`+`spot_instrument`+`future_instrument` — `if not (...): return []`, every row, forever                                                                                                                                                                                                                                                                        | 11/11 catalog rows fail the check                                                                                                                                   |
| `CARRY_BASIS_DATED_INV`                 | 🔴 TOTAL BLOCK — silent        | Same engine, same mismatch                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | 3/3 catalog rows fail the check                                                                                                                                     |
| `YIELD_ROTATION_LENDING`                | 🟡 FUNCTIONAL but drifted      | Real gate (`candidate_protocols`) IS correctly wired and catalog supplies it — the strategy WILL fire. But `rotation_min_delta_apy_bps` (catalog, per-row 30/40/40bps) is never read; engine silently uses its own default `min_apy_advantage_bps=25` for every row instead, ignoring the catalog author's differentiated per-row economics. Also `chain` (catalog) vs `current_chain`/`protocol_chains` (engine) don't align, but these don't gate execution (bridge logic degrades gracefully, single-chain rows unaffected). | `rotation_lending.py:94-97,189` vs `catalog_yield_defi.py` `build_yield_rotation_lending()`                                                                         |
| `YIELD_STAKING_SIMPLE`                  | ✅ CLEAN                       | `staking_protocol`/`asset` (the two hard-required keys) match exactly between catalog and engine                                                                                                                                                                                                                                                                                                                                                                                                                                | `staking_simple.py:58-59` vs catalog                                                                                                                                |
| `LIQUIDATION_CAPTURE`                   | 🔴 TOTAL BLOCK — silent        | Config-key mismatch — catalog emits `lending_venue`/`asset`; engine requires `protocol`+`debt_asset`+`collateral_asset` (+ a legitimately-runtime `underwater_address`) — `if not all([...]): return []`                                                                                                                                                                                                                                                                                                                        | `liquidation_capture.py:110-115` vs `catalog_yield_defi.py` `build_liquidation_capture()`, all 7 rows fail                                                          |

**Not yet checked**: the 3 MEV archetypes (already known to be architecturally opportunistic, no static currency
universe — separate finding, see the linked curtailment doc) and the 7 already-`_ENGINE_DRIVABLE_ARCHETYPES` beyond
`CARRY_STAKED_BASIS` (`CARRY_BASIS_PERP`, `CARRY_FUNDING_DISPERSION`, `ARBITRAGE_PRICE_DISPERSION`,
`DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT`) — these already have live tick-loaders and presumably went
through some manual verification when they were built, but have NOT been re-verified against this specific
config-key-contract check in this pass; worth a follow-up sweep to confirm they're not silently degraded in the same
way.

## Why this matters (money-path, not just a backtest-coverage gap)

These are the SAME catalogs and the SAME engines the LIVE path uses (`specs_for_archetype()` → `factory.py`'s
`ArchetypeEngineFactory` → the registered engine class — there is no separate paper-only code path). A 100%-silent
`return []` doesn't just mean "paper replay produces no ticks" — it means if any of these 5 fully-blocked archetypes
were ever promoted to live capital, the strategy would deploy, register successfully (for the 4 silent ones — the 1
crashing one would at least fail loudly), and then simply never trade, for reasons invisible in any log a normal
operator would think to check (no error, no warning — just an engine quietly agreeing every tick is a no-op).

## Root cause

There is no shared, validated, or tested contract between a catalog builder's `initial_config` dict and its engine's
actual param reads. Nothing enforces that the keys line up — not a type system, not a schema, not a smoke test. Each
catalog builder and each engine were evidently written independently (possibly by different sessions/agents at different
times), each internally consistent with itself, but never cross-checked against the other.

## Recommendation

1. **Immediate, cheap**: for the 5 confirmed-total-block archetypes (`CARRY_STAKED_BASIS_DATED`, `CARRY_BASIS_DATED`,
   `CARRY_BASIS_DATED_INV`, `LIQUIDATION_CAPTURE`, plus the 2 orchestrator-stub ones once that's scoped), decide the fix
   direction per-archetype (rename the catalog's keys to match the engine, or vice versa — needs the archetype's
   original author/design intent, since either the catalog or the engine could be the "wrong" side) — this is real,
   scoped, mechanical work once each decision is made, not a design question.
2. **Systemic**: add a cheap CI-level or QG-level check that, for every `StrategyArchetype` with a catalog builder,
   constructs the engine against a real catalog spec and asserts it doesn't immediately no-op/raise — this is the kind
   of test gap that let 5 archetypes silently rot. A single parametrized test over `specs_for_archetype(a)` for every
   catalogued archetype, asserting the engine can be constructed AND that `on_tick` doesn't universally `return []`
   given plausible feature data, would have caught all 5 of these at write-time.
3. **Sweep the remaining unchecked archetypes** (the 3 MEV + the 6 other already-"drivable" ones) with the same cheap
   mechanical check before assuming they're fine just because they have a working tick-loader — a working tick-loader
   proves ticks get built, not that the engine does anything useful with them.

## Evidence

All findings above were verified directly against source (`grep`/`sed` reads of the actual catalog builder functions in
`strategy_service/engine/strategies/v2/target_universe/{catalog_carry.py,catalog_yield_defi.py}` and the actual engine
`on_tick`/`__init__` methods in `strategy_service/engine/strategies/v2/{carry_and_yield,arbitrage_structural}/*.py`),
not inferred from names or comments. `factory.py:59-92` (`ARCHETYPE_ENGINE_REGISTRY`) confirms every archetype above has
ONE production engine registered — there is no separate "paper" vs "live" engine class.
