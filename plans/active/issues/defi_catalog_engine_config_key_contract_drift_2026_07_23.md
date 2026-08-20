---
doc_type: issue
title:
  strategy-service catalog/engine config-key contract has no validation — 14 archetypes workspace-wide cannot execute a
  single real trade (DeFi, sports/ML-directional, market-making, vol-options)
summary:
  A mechanical pre-flight sweep (catalog-emitted config keys vs each engine's actual params.get/str_param reads),
  followed by a systemic parametrized guardrail test covering all 32 catalogued archetypes across both catalog surfaces,
  found 14 archetypes total are functionally dead in every environment today — three distinct bug classes (a crashing
  config-key mismatch, a silent config-key mismatch, and an intentionally-stubbed unbuilt dependency). 9 DeFi archetypes
  were found and mostly fixed first; the guardrail test itself then found 5 more entirely outside DeFi
  (sports/ML-directional, market-making, vol-options), correctly held as visible xfail rather than force-fixed.
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
author: unknown
parent_epic: strategy_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days:
  1.8 # corrected 2026-07-25 (plan-reconcile): was 2.4 (the infra 0.8x multiplier, not
  # design's 0.6x); design 3.0 x 0.6 = 1.8, per /codex/08-workflows/estimation-calibration.md and matching the sibling
  # doc's correctly-applied design calibration (defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md).
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: agent-discovered (orphaned-archetype build, mechanical pre-flight sweep, 2026-07-23)
depends_on: []
context_scope:
  [
    /plans/active/issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md,
    /plans/active/issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/,
    strategy-service/strategy_service/engine/strategies/v2/orchestrator.py,
    strategy-service/tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py,
    strategy-service/strategy_service/engine/strategies/v2/target_universe/catalog.py,
    /plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md,
  ]
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

| Archetype                               | Verdict                                                                                                  | Bug class                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| --------------------------------------- | -------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CARRY_STAKED_BASIS` (already-drivable) | ✅ CLEAN, shipped this session                                                                           | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `strategy-service@e93902d8`                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `CARRY_STAKED_BASIS_DATED`              | ✅ FIXED, shipped this session                                                                           | Was: config-key mismatch (`lst_protocol`/`dated_venue`/`dated_expiry` vs engine's real `REQUIRED_PARAMS` = `{staking_protocol, native_asset, lst_asset, perp_venue, perp_instrument, spot_venue}`) — but NOT a simple key rename: the archetype's whole point is a QUARTERLY-DATED Deribit future that must ROLL FORWARD as expiry approaches, which a static `perp_instrument` literal can never express. Fixed by (1) renaming `catalog_staked_basis.py::build_carry_staked_basis_dated()`'s config to the engine's real key names (`lst_protocol`→`staking_protocol`, `dated_venue`→`perp_venue`, added `spot_venue`/`start_token`) while DROPPING a static `perp_instrument` entirely — `dated_expiry`+`roll_on_dte` are emitted instead; (2) making `perp_instrument` an either/or requirement in `CarryStakedBasisEngine.__init__` (static literal for the plain archetype, OR `dated_expiry`+`roll_on_dte` for the DATED variant — a single flat `REQUIRED_PARAMS` set can't express "either A or B+C"); (3) a new pure `resolve_current_dated_contract(native_asset, dated_expiry_tag, now_utc, roll_on_dte)` (`carry_and_yield/dated_contract_resolver.py`) implementing Deribit's REAL quarterly-expiry rule (last Friday of Mar/Jun/Sep/Dec, `{ASSET}-{DD}{MON}{YY}` symbol grammar) — verified against 4 independent real dated-future symbols (`ETH-27MAR20`, `ETH-26JUN20`, the 2026-07-15 `DERIBIT:FUTURE:ETH-USD@INV-20260925` wire object, execution-service's own `BTC-29DEC23` example), not assumed from convention alone; wired into `_extract_config`/`on_tick`/`declare_leg_portfolio_state`/`react_to_equity_change` so the held contract is re-resolved every tick (rolling to next quarter within `roll_on_dte` days of expiry), pure + deterministic (paper vs batch-rerun re-derive the identical symbol for the identical day). Plain `CARRY_STAKED_BASIS`'s static-literal path is byte-for-byte unchanged (gated on `dated_expiry` presence).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | `strategy-service@606f2fb5`; golden-value + roll-boundary + determinism tests for the resolver plus a real-catalog construction/on_tick proof — `tests/unit/engine/strategies/v2/test_carry_staked_basis_dated_contract_resolution.py`. Paper-replay tick-loader wiring (the original Phase 1 task) remains a SEPARATE, not-yet-attempted follow-on — this fix only resolves the config-shape blocker Phase 1 held on; see the curtailment doc's Phase 1 line. |
| `CARRY_RECURSIVE_STAKED`                | ✅ CLEAN, shipped this session                                                                           | n/a                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `strategy-service@23bd8b76`                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY`   | 🔴 TOTAL BLOCK — silent stub                                                                             | `staking_yield_enabled=false` → `CarryRecursiveStakedEngine.on_tick()` unconditionally `return []`s, pending an execution-service `RecursiveLoopOrchestrator` integration that isn't wired from the strategy side                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | `recursive_staked.py:194-199`; orchestrator itself DOES exist (`execution-service/.../recursive_loop_orchestrator.py`) but strategy-side stub never calls out to it                                                                                                                                                                                                                                                                                            |
| `CARRY_BASIS_PERP_INV`                  | 🔴 TOTAL BLOCK — silent stub                                                                             | Same as above (shares the engine)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Same                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `CARRY_BASIS_DATED`                     | ✅ FIXED, shipped this session                                                                           | Was: config-key mismatch — catalog emitted `cash_venue`/`dated_venue`/`instrument` (or `cash_instrument`); engine (`basis_dated.py`) requires `spot_venue`+`future_venue`+`spot_instrument`+`future_instrument` — `if not (...): return []`, every row, forever. Fixed by renaming the catalog side (the engine's naming is more precise — it distinguishes spot vs future for both venue AND instrument) across all 6 sub-family loops in `build_carry_basis_dated()`: commodity (`cash_venue`→`spot_venue`; single `instrument`→ both `spot_instrument`+`future_instrument`), equity-index (`cash_venue`→`spot_venue`, `cash_instrument`→`spot_instrument`), crypto (`dated_venue`→`future_venue`; `instrument`→ both), Phase-9 ETF-vs-CME-micro + intra-Deribit + ETF-vs-future-commodity-placeholder (same two patterns respectively). Confirmed no other engine-read keys (`entry_basis_bps`/`exit_basis_bps`/`stake_fraction`/`hedge_deadline_ms`/`min_mid_price`) are set by the catalog — left on engine defaults (not ambiguous, just not yet catalog-tuned; a follow-up if per-row economics are wanted).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | `strategy-service@b5d293d0`; new regression test asserts, for every one of the 16 catalogued `CARRY_BASIS_DATED` rows (11 live + 5 `databento_pending` placeholders), `CarryBasisDatedEngine.on_tick()` now emits a real instruction (not `[]`) — `tests/unit/engine/strategies/v2/test_basis_dated_catalog_config_contract.py`                                                                                                                                |
| `CARRY_BASIS_DATED_INV`                 | ✅ FIXED, shipped this session                                                                           | Same engine, same mismatch — same rename pattern applied to both `build_carry_basis_dated_inv()` sub-families (crypto: `dated_venue`→`future_venue`, `instrument`→ both `spot_instrument`+`future_instrument`; commodity: `cash_venue`→`spot_venue`, `instrument`→ both).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | `strategy-service@b5d293d0`; same test file covers all 3 `CARRY_BASIS_DATED_INV` rows                                                                                                                                                                                                                                                                                                                                                                          |
| `YIELD_ROTATION_LENDING`                | 🟡 FUNCTIONAL but drifted                                                                                | Real gate (`candidate_protocols`) IS correctly wired and catalog supplies it — the strategy WILL fire. But `rotation_min_delta_apy_bps` (catalog, per-row 30/40/40bps) is never read; engine silently uses its own default `min_apy_advantage_bps=25` for every row instead, ignoring the catalog author's differentiated per-row economics. Also `chain` (catalog) vs `current_chain`/`protocol_chains` (engine) don't align, but these don't gate execution (bridge logic degrades gracefully, single-chain rows unaffected).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | `rotation_lending.py:94-97,189` vs `catalog_yield_defi.py` `build_yield_rotation_lending()`                                                                                                                                                                                                                                                                                                                                                                    |
| `YIELD_STAKING_SIMPLE`                  | ✅ CLEAN                                                                                                 | `staking_protocol`/`asset` (the two hard-required keys) match exactly between catalog and engine                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | `staking_simple.py:58-59` vs catalog                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `LIQUIDATION_CAPTURE`                   | 🟡 PARTIALLY FIXED — config-key mismatch resolved, STILL BLOCKED on a missing live-injection integration | Renamed `lending_venue`→`protocol`, `asset`→`collateral_asset`, `health_factor_trigger`→`max_health_factor` in **both** `catalog_yield_defi.py::build_liquidation_capture()` (7 rows) **and** a second, previously-undocumented parallel catalog source with the IDENTICAL drift — `archetype_slots_defi.py`'s `DEFI_SLOTS["LIQUIDATION_CAPTURE"]` (v5 slot table feeding `V2BatchHarness`/`archetype_slot_resolver.py`; this doc's original sweep only grepped `target_universe/{catalog_carry.py,catalog_yield_defi.py}` and missed it — that row was ALSO missing `chain` entirely). Empirically verified the fix (constructed the engine from the real post-fix catalog row + realistic features → emits 1 instruction; same test against the pre-fix key set → emits 0, confirming the bug was real). **NOT fully fixed**: `debt_asset`/`underwater_address` remain deliberately unset — both are genuinely per-event runtime facts (which position is underwater, what it borrowed) that no static catalog row can encode. Exhaustively checked for a live-injection mechanism that could supply them at tick time and **found none**: no params-mutation API exists on `BaseArchetypeEngineV2`/`V2EngineOrchestrator` (`self.params` is set once in `register_instance()` and never rewritten; `on_allocation_directive` only carries `target_equity`); execution-service's `health_factor_monitor.py` watches OUR OWN wallets' HF for risk alerting, not third-party liquidation targets; `defi_liquidation_capture_decision_trace.py` is a batch analytics CLI, not a live wiring path. This is the SAME unbuilt-dependency class as `CARRY_RECURSIVE_BORROW_LENDING_ONLY`/`CARRY_BASIS_PERP_INV`'s `RecursiveLoopOrchestrator` gap. **Confirmed the sibling MEV archetype shares it**: `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`'s catalog leaves `candidate_ids: ""` permanently empty ("liquidation-feed orchestrator wires them in") and its engine hard-gates on `candidate_ids`+`cand_<id>_*` params that are never populated — so BOTH liquidation-family archetypes need one real, not-yet-scoped follow-on: a live on-chain liquidation-opportunity feed injecting per-event identity params into a running engine instance. Building that is out of scope here (a genuine new integration, not a catalog fix) — new todo: scope + build the liquidation-feed live-injection integration for `LIQUIDATION_CAPTURE` + `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, and sweep `archetype_slots_{cefi,tradfi,sports}.py` for the same catalog/engine key drift this row exposed in the parallel v5 slot-table surface. | `strategy-service@267a224f`; `liquidation_capture.py:110-117`; `mev/liquidation_bundle.py:140-142,255-276` (`_candidate_from_features`, identical `return []`-forever pattern); `orchestrator.py` (`register_instance`/`on_tick` — no params-mutation path); `execution-service/execution_service/defi_execution/monitors/health_factor_monitor.py` (own-wallet HF alerting, not a liquidation-candidate feed)                                                 |

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
2. **Systemic**: ✅ SHIPPED 2026-07-24 — see "Systemic guardrail shipped" section below for the full closure writeup
   (`strategy-service@238fb797` + `@03310bdf`). add a cheap CI-level or QG-level check that, for every
   `StrategyArchetype` with a catalog builder, constructs the engine against a real catalog spec and asserts it doesn't
   immediately no-op/raise — this is the kind of test gap that let 5 archetypes silently rot. A single parametrized test
   over `specs_for_archetype(a)` for every catalogued archetype, asserting the engine can be constructed AND that
   `on_tick` doesn't universally `return []` given plausible feature data, would have caught all 5 of these at
   write-time.
3. **Sweep the remaining unchecked archetypes** (the 3 MEV + the 6 other already-"drivable" ones) with the same cheap
   mechanical check before assuming they're fine just because they have a working tick-loader — a working tick-loader
   proves ticks get built, not that the engine does anything useful with them. ✅ DONE 2026-07-24 as a side effect of
   the systemic test (§2 above) — all 3 MEV archetypes confirmed construction-clean (allow-listed for firing, by
   design); `CARRY_BASIS_PERP` (170 rows across `target_universe/` + `DEFI_SLOTS`), `CARRY_FUNDING_DISPERSION` (78
   rows), `ARBITRAGE_PRICE_DISPERSION` (30 rows, already fixed earlier in this doc), `DEFI_LP_CONCENTRATED`/`_POOL`/
   `_VAULT` (3 rows each) all confirmed firing cleanly, zero silent-degradation found. The sweep additionally found 5
   MORE broken archetypes outside this original "6 already-drivable" list (CeFi/TradFi/Sports directional + vol +
   market-making archetypes never previously checked by anyone) — see "Systemic guardrail shipped" section below.

## Evidence

All findings above were verified directly against source (`grep`/`sed` reads of the actual catalog builder functions in
`strategy_service/engine/strategies/v2/target_universe/{catalog_carry.py,catalog_yield_defi.py}` and the actual engine
`on_tick`/`__init__` methods in `strategy_service/engine/strategies/v2/{carry_and_yield,arbitrage_structural}/*.py`),
not inferred from names or comments. `factory.py:59-92` (`ARCHETYPE_ENGINE_REGISTRY`) confirms every archetype above has
ONE production engine registered — there is no separate "paper" vs "live" engine class.

## Second-surface sweep: `archetype_slots_defi.py` (2026-07-23, full pass)

While fixing `LIQUIDATION_CAPTURE`'s entry in `archetype_slots_defi.py` above, a build agent discovered this file is a
**second, previously-unknown catalog surface** — a separate `DEFI_SLOTS: dict[str, ArchetypeSlotMapping]` registry
(module docstring: "the canonical v2 construction surface") feeding `V2BatchHarness` / `archetype_slot_resolver.py` /
`STRATEGY_TYPE_TO_SLOT`, distinct from the `target_universe/` catalog builders this doc's original sweep checked. That
agent fixed only the one `LIQUIDATION_CAPTURE` row it found broken while working the tick-loader task; nobody had
checked the other 27 entries in this file against this doc's same mechanical technique. This section closes that gap —
every entry in `DEFI_SLOTS` was cross-checked against its registered v2 engine's real `str_param`/`decimal_param`/
`REQUIRED_PARAMS`/`_extract_*` reads (`strategy_service/engine/strategies/v2/factory.py`'s `ARCHETYPE_ENGINE_REGISTRY`
resolves the engine class per archetype).

### Full classification (28 entries)

| Slot key                             | Archetype                    | Verdict                                        | Notes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------------------ | ---------------------------- | ---------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `AAVE_LENDING`                       | `YIELD_ROTATION_LENDING`     | ✅ CLEAN                                       | `asset`/`candidate_protocols` match `YieldRotationLendingEngine`'s reads exactly; `hold_policy` is a dead key (no engine anywhere reads it — pure catalog documentation).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `ETH_LENDING`                        | `YIELD_ROTATION_LENDING`     | ✅ CLEAN                                       | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `BTC_LENDING`                        | `YIELD_ROTATION_LENDING`     | ✅ CLEAN                                       | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `SOL_LENDING`                        | `YIELD_ROTATION_LENDING`     | ✅ CLEAN                                       | Same as above.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `MULTICHAIN_LENDING`                 | `YIELD_ROTATION_LENDING`     | ✅ CLEAN                                       | `cross_chain_aware` is a dead key (not read); doesn't gate execution.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `BASIS_TRADE`                        | `CARRY_BASIS_PERP`           | ✅ CLEAN (no required params)                  | `CarryBasisPerpEngine.on_tick` only reads `entry_funding_bps`/`exit_funding_bps`/`stake_fraction`/`min_mid_price` (all optional, defaulted) — venue/instrument come from the tick call (resolved from `slot_label` by `V2BatchHarness._derive_venue_and_instrument`, not from `initial_config`). `spot_venue`/`perp_venue`/`spot_instrument`/`perp_instrument`/`hold_policy` are catalog-side documentation only; engine fires on defaults regardless.                                                                                                                                                                                                                                                                         |
| `BTC_BASIS`                          | `CARRY_BASIS_PERP`           | ✅ CLEAN (no required params)                  | Same as `BASIS_TRADE`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `SOL_BASIS`                          | `CARRY_BASIS_PERP`           | ✅ CLEAN (no required params)                  | Same.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `L2_BASIS`                           | `CARRY_BASIS_PERP`           | ✅ CLEAN (no required params)                  | Same.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `ENHANCED_BASIS_MULTI_VENUE`         | `CARRY_BASIS_PERP`           | ✅ CLEAN (no required params)                  | `mode`/`venues`/`bidirectional_funding` are dead keys — same simplification as the other `CARRY_BASIS_PERP` rows.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `ENHANCED_BASIS_MULTI_COIN`          | `CARRY_BASIS_PERP`           | ✅ CLEAN (no required params)                  | Same.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `STAKED_BASIS`                       | `CARRY_STAKED_BASIS`         | ✅ CLEAN                                       | All of `CarryStakedBasisEngine.REQUIRED_PARAMS` (`staking_protocol`/`native_asset`/`lst_asset`/`perp_venue`/`spot_venue`) + a static `perp_instrument` are present.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `SOL_STAKED_BASIS`                   | `CARRY_STAKED_BASIS`         | ✅ CLEAN                                       | Same; `staking_protocol=marinade` resolves to `chain=solana` ∈ `_ALLOWED_CHAINS`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `carry_staked_basis` (alias)         | `CARRY_STAKED_BASIS`         | ✅ CLEAN                                       | Identical config to `STAKED_BASIS`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `ACTIVE_LP_ETH_USDC`                 | `MARKET_MAKING_CONTINUOUS`   | ✅ CLEAN (no required params)                  | `MarketMakingContinuousEngine` has no `REQUIRED_PARAMS`; `pool_fee_bps`/`range_policy`/`gas_aware_rebalance` are dead keys (the engine is a simplified generic reference-price quoter, not a concentrated-liquidity range manager — a known simplification per the module docstring, not a contract bug). Fires every tick on `half_spread_bps`/`max_inventory_abs`/`refresh_cadence_ms`/`min_mid_price` defaults.                                                                                                                                                                                                                                                                                                             |
| `ACTIVE_LP_SOL_USDC`                 | `MARKET_MAKING_CONTINUOUS`   | ✅ CLEAN (no required params)                  | Same; `pool_type`/`range_width_pct` dead keys.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `AMM_LP`                             | `MARKET_MAKING_CONTINUOUS`   | ✅ CLEAN (no required params)                  | Same; `pool_fee_bps`/`range_width_pct`/`rebalance_trigger` dead keys.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `SOL_CONCENTRATED_LP`                | `MARKET_MAKING_CONTINUOUS`   | ✅ CLEAN (no required params)                  | Same; `pool_type`/`range_width_pct` dead keys.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `APD` (alias)                        | `ARBITRAGE_PRICE_DISPERSION` | ✅ CLEAN                                       | `dispersion_type="funding-rate-dispersion"` explicitly set + `venue_universe` populated — bypasses the `candidate_venues` constructor gate entirely (that gate only fires on the default `price-dispersion` mode).                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| `arbitrage_price_dispersion` (alias) | `ARBITRAGE_PRICE_DISPERSION` | ✅ CLEAN                                       | Identical config to `APD`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| `LIQUIDATION_CAPTURE`                | `LIQUIDATION_CAPTURE`        | 🟡 Already fixed this session (unchanged here) | Re-verified against `LiquidationCaptureEngine.on_tick`'s real reads (`protocol`/`chain`/`debt_asset`/`collateral_asset`/`underwater_address`/`max_health_factor`) — confirmed still correctly renamed per the row's own NOTE comment; still structurally blocked on `debt_asset`/`underwater_address` (unchanged, no new finding here).                                                                                                                                                                                                                                                                                                                                                                                        |
| **`RECURSIVE_STAKED_BASIS`**         | `CARRY_RECURSIVE_STAKED`     | 🔴 **BROKEN → FIXED**                          | Config had `lending_venue`/`staking_venue` (not read); `CarryRecursiveStakedEngine._extract_protocols` requires `staking_protocol`/`lending_protocol`/`native_asset`/`lst_asset` — **all four absent** → `on_tick` silently returned `[]` every tick, forever, in every environment. **Fixed**: added `lending_protocol="AAVE_V3_ETHEREUM"`, `staking_protocol="ETHERFI"`, `native_asset="ETH"`, `lst_asset="weETH"` alongside the kept `lending_venue`/`staking_venue` (mirrors the exact both-key-sets-present precedent already shipped in `catalog_carry.py::build_carry_recursive_staked()`, and matches `tests/unit/engine/strategies/v2/test_recursive_staked_governance_params.py`'s `_BASE_PARAMS` fixture verbatim). |
| **`UNHEDGED_RECURSIVE`**             | `CARRY_RECURSIVE_STAKED`     | 🔴 **BROKEN → FIXED**                          | Identical bug + identical fix as `RECURSIVE_STAKED_BASIS`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **`CROSS_CHAIN_YIELD_ARB`**          | `ARBITRAGE_PRICE_DISPERSION` | 🔴 **BROKEN (crashing) → FIXED**               | `ArbitragePriceDispersionEngine.__init__` hard-requires `candidate_venues` (≥ 2 tokens) whenever `dispersion_type` is unset (defaults to `"price-dispersion"`); this row only set `chains` → **constructor RAISED `ValueError`** on every registration attempt, not a silent no-op. **Fixed**: added `candidate_venues="ethereum,arbitrum,base,optimism,polygon"` (reusing the chain tokens as the dispersion venue set) + `dispersion_bps="100"` (carrying over the catalog author's `min_yield_diff_bps` intent, since the engine reads `dispersion_bps` not `min_yield_diff_bps`); `chains`/`protocol`/`min_yield_diff_bps` kept as-is (documentation).                                                                     |
| **`LENDING_PROTOCOL_ARB`**           | `ARBITRAGE_PRICE_DISPERSION` | 🔴 **BROKEN (crashing) → FIXED**               | Same crashing gap — only `long_protocol`/`short_protocol`/`chain`/`min_spread_bps` set, no `candidate_venues`. **Fixed**: added `candidate_venues="aave,compound"` (protocol names as venue tokens) + `dispersion_bps="200"` (from `min_spread_bps`). `long_protocol`/`short_protocol` kept (read by `paper_universe_metrics.py` + `scripts/trace_all_carry_archetypes.py` — a real second consumer, confirmed by grep).                                                                                                                                                                                                                                                                                                       |
| **`LENDING_PROTOCOL_ARB_ETH`**       | `ARBITRAGE_PRICE_DISPERSION` | 🔴 **BROKEN (crashing) → FIXED**               | Same crashing gap; no `min_spread_bps` on this row so `dispersion_bps` left at engine default (30bps) rather than inventing a value. **Fixed**: added `candidate_venues="aave,compound"`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| **`LENDING_PROTOCOL_ARB_ARB`**       | `ARBITRAGE_PRICE_DISPERSION` | 🔴 **BROKEN (crashing) → FIXED**               | Same crashing gap. **Fixed**: added `candidate_venues="aave,morpho"`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| **`ETHENA_BENCHMARK`**               | `YIELD_STAKING_SIMPLE`       | 🔴 **BROKEN → FIXED**                          | Config had only `staked_token` (not read at all — the engine's LST-identity key is `lst_asset`) + `role`; `YieldStakingSimpleEngine._resolve_context` hard-requires `staking_protocol` + `asset` — **both absent** → `on_tick` silently returned `[]` every tick, forever. **Fixed**: renamed `staked_token`→`lst_asset` (no other consumer reads `staked_token` — confirmed by grep) and added `staking_protocol="ethena"`/`asset="USDE"`, mirroring the already-clean `catalog_yield_defi.py::build_yield_staking_simple()` ethena row exactly.                                                                                                                                                                              |

**NOT PRESENT in this file** (no entry at all — confirmed by grepping every `archetype=StrategyArchetype.*` line):
`CARRY_STAKED_BASIS_DATED`, `CARRY_BASIS_DATED`, `CARRY_BASIS_DATED_INV`, `CARRY_RECURSIVE_BORROW_LENDING_ONLY`,
`CARRY_BASIS_PERP_INV` — the five archetypes with the deepest problems in the original sweep (4 already-fixed + 1
orchestrator-stub) simply have no row in this second catalog surface at all, so
`V2BatchHarness`/`archetype_slot_resolver` cannot batch-test them via a `DEFI_SLOTS` key (only via `target_universe/`
specs). This mirrors the note already on `LIQUIDATION_CAPTURE`'s row about `V2BatchHarness` coverage gaps but wasn't
independently confirmed until this pass.

### Summary: 7 of 28 entries were broken, 100% fixed

- **4 crashing** (`ArbitragePriceDispersionEngine.__init__` raised `ValueError` at registration):
  `CROSS_CHAIN_YIELD_ARB`, `LENDING_PROTOCOL_ARB`, `LENDING_PROTOCOL_ARB_ETH`, `LENDING_PROTOCOL_ARB_ARB`.
- **3 silent** (`on_tick` returned `[]` every tick, forever, no error/warning): `RECURSIVE_STAKED_BASIS`,
  `UNHEDGED_RECURSIVE`, `ETHENA_BENCHMARK`.
- **18 clean** (fire correctly; several carry dead/unused catalog keys that are simplifications, not contract bugs).
- **1 already fixed this session** (`LIQUIDATION_CAPTURE`, re-verified unchanged).
- **5 archetypes have no row in this file at all**
  (`CARRY_STAKED_BASIS_DATED`/`CARRY_BASIS_DATED`/`CARRY_BASIS_DATED_INV`/
  `CARRY_RECURSIVE_BORROW_LENDING_ONLY`/`CARRY_BASIS_PERP_INV`).

All 7 fixes were empirically verified: constructed the real registered engine (`get_archetype_engine_class`) from the
PRE-fix `DEFI_SLOTS` config → confirmed the exact failure mode (4× `ValueError` at construction, 3× `on_tick()` → `[]`
with favorable feature data); re-ran identically against the POST-fix config → all 7 now emit exactly 1 real
`StrategyInstructionEnvelope` (a 30-leg `AtomicInstruction` for the two recursive-loop rows, a 2-leg `LEADER_HEDGE`
`AtomicInstruction` for the four dispersion rows, a `StakeInstruction` for `ETHENA_BENCHMARK`).

### New finding (out of this task's scope, flagged not silently fixed): `target_universe/catalog_trading.py` has the SAME crashing bug

While reading `ArbitragePriceDispersionEngine` to fix the 4 crashing `archetype_slots_defi.py` rows above, discovered
that `strategy_service/engine/strategies/v2/target_universe/catalog_trading.py::build_arbitrage_price_dispersion()` —
the **other**, not-yet-checked-in-this-doc catalog surface for this same archetype (flagged as unchecked in the "Not yet
checked" section above: `ARBITRAGE_PRICE_DISPERSION` was one of the 7 already-`_ENGINE_DRIVABLE_ARCHETYPES` never
re-verified) — has the **identical class of bug**, and worse, at larger scale:

- **"Lending protocol arb" rows** (3 chains × 2 protocol-pairs = 6 rows): config sets `chain`/`long_protocol`/
  `short_protocol`/`min_spread_bps`/`supports_flash_loans` — no `candidate_venues`. **Crashes at construction.**
- **"Cross-chain yield arb" rows** (3 chain-pairs = 3 rows): config sets `protocol`/`long_chain`/`short_chain`/
  `min_yield_diff_bps` — no `candidate_venues`. **Crashes at construction.**
- **"CEX-CEX spot/perp spread arb" rows** (3 rows): config sets `venues` (not `candidate_venues`) + `instrument` (not
  read — the tick's own `instrument` arg is used) + `min_spread_bps` (not `dispersion_bps`). **Crashes at construction**
  (no `candidate_venues` key at all).

That's **12 additional `ARBITRAGE_PRICE_DISPERSION` catalog rows in `target_universe/`** (the catalog the LIVE/batch
promote path actually reads via `specs_for_archetype()`) that would raise `ValueError` at registration today, in every
environment — the same bug class as the 4 crashing rows just fixed above, just in the sibling catalog surface. Confirmed
by direct read of `catalog_trading.py:25-90`; NOT fixed here (out of this task's explicit scope, which named
`archetype_slots_defi.py` only) — **new follow-up todo**: apply the identical `candidate_venues` fix (protocol/chain
names as venue tokens, matching the fix pattern above) to all 12 rows in
`catalog_trading.py::build_arbitrage_price_dispersion()`, plus re-run the "7 already-drivable, not yet checked" sweep
this doc's Recommendation §3 calls for (`CARRY_FUNDING_DISPERSION`, `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`,
`DEFI_LP_VAULT` remain fully unchecked against either catalog surface).

### Evidence

`strategy-service@27e3456f` — `strategy_service/engine/strategies/v2/archetype_slots_defi.py` (7 rows fixed, in-code
NOTE comments on each explaining the drift + fix + evidence source). Verification method: constructed
`get_archetype_engine_class(archetype)(identity=..., target_equity=..., params=dict(initial_config))` directly from each
`DEFI_SLOTS` row (pre- and post-fix) and called `on_tick(...)` with realistic feature data — same empirical
prove-the-bug / prove-the-fix pattern as `LIQUIDATION_CAPTURE`'s fix (`strategy-service@267a224f`). Cross-referenced
against `tests/unit/engine/strategies/v2/test_recursive_staked_governance_params.py` (`_BASE_PARAMS` fixture confirms
the `CARRY_RECURSIVE_STAKED` fix's key names/values independently) and
`catalog_yield_defi.py::build_yield_staking_ simple()` (confirms the `ETHENA_BENCHMARK` fix's `staking_protocol`/`asset`
values independently). Quality gates: `bash scripts/quality-gates.sh --no-fix` — no new violations from this change
(pre-existing unrelated repo-wide findings: a `pip-audit` CVE in a transitive `pyasn1` dependency, `Pydantic BaseModel`
domain-contract violations in `signal_broadcast/transport.py` + `api/operational_mode_router.py` +
`api/restriction_profile_router.py`, inline HF/LTV literals in `risk/v2/greek_model.py` +
`vol_trading/analog_execution_gate.py`, and a Production Readiness Validators failure tied to the sibling
`unified-trading-pm` checkout's in-flight uncommitted doc-link-normalization sweep — none touch
`archetype_slots_defi.py` and none were introduced by this change). Shipped via
`quickmerge.sh --agent --files 'strategy_service/engine/strategies/v2/archetype_slots_defi.py'`, landed on
`live-defi-rollout` at `27e3456f88cadb2c5756716bc2af77c4a2c89aa1`.

### `catalog_trading.py` finding — FIXED (2026-07-24), and it was bigger than the 12 rows flagged above

The 12-row `catalog_trading.py::build_arbitrage_price_dispersion()` follow-up flagged above is now fixed — **and a
same-file, same-bug-class sweep of the REST of this function during the fix found 5 MORE broken rows the original "12
additional rows" count missed** (the flagging pass above stopped after the 3 named sub-families and didn't check the
other loops later in the same function, which use the identical archetype/engine): "Sports cross-book arb" (2 rows,
`venues="unity,betfair,matchbook"`, no `candidate_venues`), "Prediction market arb Polymarket vs sports books" (1 row,
`venues="polymarket,betfair"`, no `candidate_venues`), and the Phase-9 "cross-venue dated futures arb" CME-vs- Deribit
rows (2 rows, `long_venue`/`short_venue`, no `candidate_venues`). Verified empirically (constructed
`ArbitragePriceDispersionEngine` directly from every one of the 30 rows `build_arbitrage_price_dispersion()` emits,
pre-fix): **17 of 30 rows raised `ValueError` at construction**, not 12 — the 10-row "DEX cross-venue spot dispersion"
sub-family (already correct) and the 3-row "cross-venue prediction dispersion" sub-family
(`dispersion_type="cross-venue-prediction-dispersion"`, bypasses the `candidate_venues` gate entirely) were the only 13
clean rows.

**Fix** (mirrors the exact `archetype_slots_defi.py` convention, `strategy-service@27e3456f`, ADD not rename — a real
second consumer, `scripts/trace_all_carry_archetypes.py::_resolve_arbitrage_price_dispersion`, reads the original
`venues`/`long_chain`/`short_chain`/`long_protocol`/`short_protocol` keys directly off `slot.initial_config`):

- Lending-protocol-arb (6 rows): `candidate_venues=f"{long_protocol},{short_protocol}"` + `dispersion_bps` from this
  row's own `min_spread_bps` ("100" for all 6).
- Cross-chain-yield-arb (3 rows): `candidate_venues=f"{long_chain},{short_chain}"` (the row's own 2-chain pair, not a
  5-chain list — unlike the `archetype_slots_defi.py` `CROSS_CHAIN_YIELD_ARB` row, this catalog surface's rows each
  scope a single chain pair) + `dispersion_bps` from `min_yield_diff_bps` ("50").
- CEX-CEX spread-arb (3 rows): `candidate_venues` = the row's own already-computed `venues` value (added, not renamed) +
  `dispersion_bps` from `min_spread_bps` ("3").
- Sports cross-book arb (2 rows, newly discovered): `candidate_venues` = the row's own `venues` value. No
  `dispersion_bps` added — `min_margin_pct` is a fraction/different edge-method metric (overround, not a two-venue bps
  spread), left unconverted rather than inventing a value from an incompatible unit (engine falls back to its 30bps
  default).
- Prediction-market arb (1 row, newly discovered): same pattern as sports rows — `candidate_venues` from `venues`, no
  `dispersion_bps` (`min_edge_pct` is a fraction, incompatible unit).
- CME-vs-Deribit dated-futures arb (2 rows, newly discovered): `candidate_venues=f"{long_venue},{short_venue}"` (=
  `"cme,deribit"`) + `dispersion_bps` from `min_spread_bps` ("20", a compatible unit).

**Verified empirically, both directions**: pre-fix, 17/30 rows raised `ValueError` at `ArbitragePriceDispersionEngine`
construction; post-fix, all 30 rows construct cleanly, and all 27 rows on the default price-dispersion path (the 3
cross-venue-prediction-dispersion rows use a different feature shape) emit exactly 1 real instruction from `on_tick()`
given a plausible, generously-dispersed `mid_price_<venue>` feature set. New regression test:
`tests/unit/engine/strategies/v2/test_arbitrage_price_dispersion_catalog_config_contract.py` (mirrors
`test_basis_dated_catalog_config_contract.py`'s pattern — constructs every real catalogued price-dispersion-path spec
via `specs_for_archetype()` and asserts non-crashing construction + real instruction emission).

**Side effect found and handled**: `strategy_service/cli/handlers/paper_universe.py`'s static
`_dex_dispersion_config_satisfiable()` gate (used by `resolve_paper_universe()` to decide which specs the paper-replay
harness runs) checks config SHAPE only (`candidate_venues` + a top-level `instrument` key + `dispersion_type`), not data
SOURCE — it does not distinguish "dex" vs "cex" venues. Since the 3 CEX-CEX rows already carried a top-level
`instrument` key and now carry `candidate_venues` too, they newly pass this gate and are selected into the paper
universe (previously they were statically skipped as `non_dex_dispersion_config`). Verified this is safe, not a
silent-wrong-data risk: per `paper_run_handler.py::_load_dex_dispersion_ticks`, the real tick loader reads the canonical
`dex-pools` corpus filtered by DEX venue names — a CEX-CEX row's `candidate_venues` (e.g. `"binance,okx"`) will never
match any `dex_pool_state` observation's venue, so every day honestly runtime-skips (`< 2 candidate-venue mids`) rather
than fabricating data; this only means the 3 CEX-CEX rows get selected into `sel.selected` and then produce zero ticks
at runtime (wasted static-gate pass, not a correctness bug). Updated
`tests/unit/cli/handlers/test_paper_universe.py::test_dex_pool_archetypes_are_drivable_and_selected` (and the
`test_non_drivable_archetypes_are_honestly_skipped_not_faked` comment) to assert the new, correct partition (10
DEX-spot + 3 CEX-CEX rows selected; the other 14 rows — lending/cross-chain-yield/sports/prediction/cme-deribit, which
lack a top-level `instrument` key — remain skipped). Whether the paper-replay tick-loader wiring should be extended with
a real CEX mid-price provider for these 3 rows is a separate, not-yet-scoped follow-on (same category as the
"Paper-replay tick-loader wiring... SEPARATE, not-yet-attempted follow-on" already noted elsewhere in this doc) — not
addressed here.

Quality gates: `bash scripts/quality-gates.sh --no-fix` (repo `.venv`) — full suite green (5407 passed, 206 skipped, 0
failed, re-confirmed on two consecutive clean runs) plus a scoped, isolated re-run of every
`arbitrage_price_dispersion`-adjacent test file (80 passed) to rule out cross-contamination from a concurrent sibling
agent's live, uncommitted WIP on `paper_run_handler.py`/`batch_rerun.py`/`paper_run_attribution.py`/
`paper_run_passive.py` in the same shared checkout during this fix (that WIP was left untouched — staged and shipped
only this fix's 3 files, by name). Shipped via
`quickmerge.sh --agent --files 'strategy_service/engine/strategies/v2/target_universe/catalog_trading.py tests/unit/cli/handlers/test_paper_universe.py tests/unit/engine/strategies/v2/test_arbitrage_price_dispersion_catalog_config_contract.py'`,
landed on `live-defi-rollout` at `strategy-service@05c0b2edb6397dcc5fa97ea08b6bcb675ea47272`.

Still open from the original Recommendation §3 sweep: the "7 already-drivable, not yet checked" archetypes
(`CARRY_FUNDING_DISPERSION`, `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT`) remain fully unchecked against
either catalog surface.

## Live liquidation-candidate feed: exhaustive workspace search (2026-07-24, investigation-only, no code changed)

Continuation task, read-only investigation across `execution-service`, `market-tick-data-service`, `features-service`,
`market-data-processing-service`, `strategy-service` (incl. `config.py`), `unified-api-contracts`, and the
`unified-trading-pm/plans/` corpus, answering whether the `LIQUIDATION_CAPTURE` / `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`
live-injection gap (documented above) is genuinely unbuilt anywhere, or was missed.

### Verdict: no live third-party liquidation-candidate feed exists anywhere in the workspace — confirmed, with one addition

The prior sweep's conclusion stands. Every "liquidation"-adjacent artifact found this pass is one of three things, none
of which is a live feed of third-party positions approaching liquidation:

1. **Our-own-wallet risk monitors** (confirms the prior finding, does not change it):
   `execution-service/execution_service/defi_execution/monitors/health_factor_monitor.py` (already known) +
   `execution-service/.../position_tracker.py`/`services/position_tracker.py` (`get_health_factor()` —
   `overall_health_factor` over OUR tracked `DeFiPosition`s) +
   `execution-service/.../orchestrators/recursive_loop_orchestrator.py:620` (`_read_health_factor` — polls HF mid-loop
   for OUR OWN recursive-borrow position, abort-on-low-HF).
   `features-service/features_service/onchain/engine/orchestrator.py:605-616` `_process_health_factor` — docstring:
   "Polls Aave `getUserAccountData()` **for tracked wallets**... Used by strategy-service for risk gating (defensive
   mode when health_factor < threshold)" — this is the features-service-side twin of `health_factor_monitor.py`, same
   own-wallet scope, not third-party. `strategy_service/config.py:78,700` (`DefiRiskConfig.health_factor_monitoring`)
   and `config.py:75-78,701-703` (`CexRiskConfig.liquidation_monitoring`) are both feature-flags for OUR OWN
   DeFi-position / CEX-margin-account risk gating — not candidate detection.

2. **Batch historical liquidation-EVENT collectors** (after-the-fact, not predictive) — confirms and details the prior
   "batch analytics CLI" framing at a data-pipeline level:
   `market-tick-data-service/market_tick_data_service/cli/handlers/liquidations_handler.py` (Aave V3/Compound
   V3/Morpho/Fluid/Spark/GMX — `data_type=liquidations`) and the sibling `liquidation_events_handler.py` (Aave V3/Morpho
   — `data_type=liquidation_events`) both run ONCE PER DAY (`BatchPayload.date` → a single UTC day window
   `[day_start, day_end)`), query subgraphs for `LiquidationCall`/`liquidationEvents` that **already occurred** that
   day, and write to GCS parquet — there is no polling loop, no sub-day cadence, no "candidates approaching liquidation"
   filter (the query is `timestamp_gte/lt`, not `healthFactor_lt`). `features-service/.../orchestrator.py:625-641`
   `_process_liquidation_events` + `orchestrator_calculators.py:383-401` `_calculate_liquidation_features` derive only
   aggregate stats (`liquidation_count`, `liquidated_collateral_amount`, `debt_to_cover`, `liquidator_address`) from
   this same batch data — a market-level regime/risk feature, not a per-address opportunity signal.
   `market-data-processing-service`'s `liquidation_buy_volume_sum`/`liquidation_sell_volume_sum`/etc. are CEFI
   candle-level aggregates of exchange-forced-liquidation TRADE volume (from Tardis `trades`, `trade_type=liquidation`)
   — a CEFI microstructure feature, unrelated to on-chain candidate identity.
   `unified-api-contracts/unified_api_contracts/normalize_utils/liquidations.py` normalizes CEFI liquidation-order WS
   streams (Binance `!forceOrder@arr`, Bybit `allLiquidation`, OKX, Deribit, Hyperliquid) — real-time, but these are
   ALREADY-EXECUTED forced-liquidation prints on centralized exchanges, not Aave/Compound on-chain underwater-position
   detection (and the two archetypes in scope here are DeFi-only per their engine code — `protocol`/`chain`/`debt_asset`
   params — confirmed by reading `arbitrage_structural/liquidation_capture.py` directly, not inferred).

3. **Protocol/reserve-level governance parameters**, not per-position:
   `market-tick-data-service/.../adapters/defi/aave_positions.py` (`_download_risk_params` —
   LTV/`liquidationThreshold`/`liquidationBonus` per RESERVE, i.e. per-asset protocol config, not per-user);
   `risk_params_handler.py` (same, `data_type=risk_params`).

### New finding (correction/addition, not a reversal): `market-tick-data-service/.../cli/handlers/position_data_handler.py`

This file was **not checked by the prior sweep** and is the closest thing anywhere in the workspace to third-party
underwater-position data. `_fetch_aave_positions()` (lines ~230-300) queries the Aave V3 subgraph for the **top 500
users ordered by `totalCurrentVariableDebt` DESC**, and for each user's each reserve, captures exactly the identity +
risk facts the two blocked engines need:

```graphql
users(first: 500, orderBy: totalCurrentVariableDebt, orderDirection: desc) {
  id                # → would map to underwater_address / cand_<id>_borrower
  healthFactor      # → would map to max_health_factor gate / liq_candidate_health_factor_<id>
  reserves { currentTotalDebt currentATokenBalance reserve { underlyingAsset } }  # → debt_asset/collateral_asset
}
```

`_DATA_TYPE = "position_data"`, written to
`gs://{tick-defi-bucket}/raw_tick_data/by_date/day={date}/category=defi/venue={VENUE}-{CHAIN}/instrument_type=lending/data_type=position_data/ticks.parquet`.
**This does NOT change the "no live feed exists" verdict**, for three independently-confirmed reasons:

- **Batch, once/day** — invoked via `process(payload: BatchPayload)` → one `target_date`, no live/streaming/polling
  loop, same cadence family as the two liquidation-event handlers above.
- **Wrong sort order for candidate detection** — ordered by debt SIZE, not by `healthFactor` ascending /
  `healthFactor_lt` threshold; a small position at `healthFactor=0.98` (an ideal liquidation-capture target) can be
  absent from the top-500-by-debt entirely while a large, perfectly healthy position (`healthFactor=3.5`) occupies a
  slot.
- **Zero downstream consumers** — grepped `position_data` across every repo in the workspace
  (`execution-service`/`strategy-service`/`features-service`/`market-tick-data-service`/`instruments-service`); every
  hit is either this handler's own writer code, unrelated OUR-OWN-position persistence layers
  (`execution_service/engine/live/positions.py` et al. — a same-named but semantically unrelated concept), or test
  fixtures. Nothing reads the MTDS DeFi `data_type=position_data` parquet for any purpose today — it is captured (for
  data-completeness / honest-coverage reasons) and then orphaned.

**Also confirmed independently** (direct read, `mev/liquidation_bundle.py:140-142,255-277`): the engine-side contract is
dangling on BOTH ends, not just the `candidate_ids` end already documented above — `_candidate_from_features()`
additionally requires three DYNAMICALLY-KEYED per-candidate FEATURES (`liq_candidate_debt_amount_<id>`,
`liq_candidate_health_factor_<id>`, `liq_candidate_liq_bonus_pct_<id>`) that exist ONLY in this engine file's own
docstring and in two test files' hardcoded mocks (`tests/integration/test_phase8_archetype_factory_smoke.py:260-262`,
`tests/unit/engine/strategies/v2/test_mev_engines.py:114-120`) — grepped `liq_candidate` across `features-service` and
`strategy-service`: zero calculators, zero production emitters. Even a `candidate_ids`-populating fix alone would still
starve on missing per-candidate features.

### Scope of the real, unbuilt integration (rough shape, not a full design — per-repo)

Because `position_data_handler.py`'s subgraph-query pattern already exists, this is smaller than a from-scratch build,
but still spans three repos and one architectural gap:

1. **market-tick-data-service** — extend/fork `position_data_handler.py`'s Aave V3 query (+ add the Compound V3/
   Morpho/Spark equivalents already covered by the batch liquidation-event handlers, for parity) to (a) query/sort by
   `healthFactor` ascending or `where: {healthFactor_lt: "<threshold>"}` instead of debt-desc, surfacing the positions
   actually close to liquidation, and (b) run on a live/high-frequency cadence (subgraph polling every N seconds/
   blocks) publishing through the UTL `EventTransport` facade (`InMemoryTransport` paper / Pub/Sub live — the
   live-data-persistence-and-event-log spine, `/codex/02-data/live-data-persistence-and-event-log.md`) rather than (or
   in addition to) once-daily GCS parquet.
2. **features-service** — a new onchain calculator (or an extension of the existing `health_factor`/
   `liquidation_events` feature groups) that consumes that live feed and emits the dynamically-keyed
   `liq_candidate_debt_amount_<id>`/`liq_candidate_health_factor_<id>`/`liq_candidate_liq_bonus_pct_<id>` features the
   MEV bundle engine already expects, plus the `debt_asset`/`collateral_asset`/`underwater_address` identity fields
   `LiquidationCaptureEngine` expects. **Open design question worth flagging to a human**: today's features-service
   schema is one column per STATIC feature name; per-candidate DYNAMIC feature naming (`_<id>` suffix, cardinality
   varying tick-to-tick) is a new shape not seen elsewhere in the codebase — may need its own small design decision
   before scoping this as an AO-dispatchable todo.
3. **strategy-service** — the piece both engines agree is missing (unchanged from the prior finding): a live
   params-mutation path on `V2EngineOrchestrator`/`BaseArchetypeEngineV2` (today `self.params` is set once in
   `register_instance()` and never rewritten) so `candidate_ids`/`cand_<id>_*`/`debt_asset`/`underwater_address` can be
   updated on a running engine instance as candidates appear/expire between ticks — a genuine orchestrator-level design
   decision (push-on-every-tick from the live feature stream vs. a separate pollable "candidate registry"), not a
   mechanical fix.

This is a `design`-class, multi-repo, multi-day build — not a quick fix, and not (per the finding above) something a
single AO-dispatched todo can scope end-to-end without a human first picking the design direction in item 2 and item 3.

### Not tracked elsewhere in the plans corpus — confirmed, with one adjacent-but-distinct plan flagged

Grepped `unified-trading-pm/plans/` for `liquidation` broadly (200+ hits — overwhelmingly data-pipeline completeness
docs about the batch `liquidations`/`liquidation_events` DATA TYPE, unrelated to this specific gap) and narrowly for
`underwater`/`liquidation_candidate`/`candidate_ids`/`liquidation feed`/`liquidation scanner`/`liquidation orchestrator`.
The only hits for the narrow set are this doc and its already-`related:` sibling
`defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` (which flags, in passing, that
`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`/`ARBITRAGE_MEV_BACKRUN` have no catalog-declared currency universe because they are
"opportunistic mempool/liquidation-feed driven" — same gap, no new detail). **No duplicate tracking found.**

One **adjacent but genuinely distinct** plan worth flagging so it isn't confused with this gap:
`plans/archive/mempool_feed_integration_2026_06_01.plan.md` (status `paused`, `locked_by: live-defi-rollout`) is a stub
for wiring a PENDING-mempool feed (Flashbots Protect / MEV-share / Alchemy private mempool), explicitly gated behind a
business-case profitability threshold ("theoretical sandwich profit... exceeds mempool subscription cost by ≥3x for two
consecutive months"). It targets `ARBITRAGE_MEV_SANDWICH` (pending-tx front-running) and precision for
`ArbitrageMevJitLiquidityEngine` — **not** `LIQUIDATION_CAPTURE`/`ARBITRAGE_MEV_LIQUIDATION_BUNDLE`. Its own text states
the original design assumption plainly: "The DeFi pipeline extension landed live engines for liquidation-bundle, JIT
liquidity, and backrun (**all derivable from confirmed-block data**)" — i.e., liquidation-bundle was assumed NOT to need
a mempool feed, because it was assumed the confirmed-block candidate-scanning mechanism would be trivial/already
covered. Reading the plan that actually built these engines (`plans/archive/defi_pipeline_extension_2026_05_01.plan.md`,
its Phase 5.1 task `p5-1-liquidation-bundle-engine`) confirms that assumption was never actually checked: the plan
scopes the ENGINE build (flash-loan bundle construction, gas budget curve) and separately tracks "liquidation-event
capture" (the batch historical collectors above) as a data-completeness item, but **no task anywhere in that plan scopes
"how do we identify, in real time, which specific position is currently underwater"** — the live-candidate-detection gap
documented in this section was never deliberately deferred, it was an unstated assumption gap from the original design.

### Evidence (this section)

Read directly (not grep-concluded):
`execution-service/execution_service/defi_execution/{position.py,position_tracker.py,orchestrators/recursive_loop_orchestrator.py,monitors/health_factor_monitor.py}`;
`execution-service/execution_service/services/position_tracker.py`;
`market-tick-data-service/market_tick_data_service/cli/handlers/{liquidations_handler.py,liquidation_events_handler.py,position_data_handler.py,risk_params_handler.py}`;
`market-tick-data-service/.../market_interface/adapters/defi/aave_positions.py`;
`features-service/features_service/onchain/engine/{orchestrator.py,orchestrator_calculators.py}`;
`strategy_service/config.py:60-90,685-703`; `strategy_service/engine/strategies/v2/mev/liquidation_bundle.py:120-280`;
`unified-api-contracts/unified_api_contracts/normalize_utils/liquidations.py`;
`plans/archive/{mempool_feed_integration_2026_06_01.plan.md, defi_pipeline_extension_2026_05_01.plan.md}`. Grepped (then
read every promising hit, per workspace grep-then-READ discipline): `underwater`, `health_factor`,
`liquidation_candidate`, `candidate_ids`, `liq_candidate`, `position_data` across `execution-service`,
`strategy-service`, `features-service`, `market-tick-data-service`, `market-data-processing-service`,
`unified-api-contracts`, `instruments-service`, and `unified-trading-pm/plans/`.

## `CARRY_RECURSIVE_BORROW_LENDING_ONLY` / `CARRY_BASIS_PERP_INV` orchestrator-stub: exhaustive investigation, scoped not built (2026-07-24)

Continuation of the `staking_yield_enabled=false` finding above (`recursive_staked.py:194-199`). Read-only + design
investigation across `strategy-service`, `execution-service`, `unified-api-contracts`, `unified-trading-library`, and
the `unified-trading-pm/plans/` corpus. **No code changed** — this closes with a precise scope, not a build, per the
explicit "scope, don't invent" branch for this exact class of gap.

### Step 1 finding: the real dispatch pattern, and where it does/doesn't reach

The UAC shared contract (`unified_api_contracts/internal/architecture_v2/schemas.py` + `enums.py`) has no dedicated
"open/unwind a recursive loop" `InstructionActionV2` — the established archetype models a recursive loop as an
`AtomicInstruction` (`execution_mode=ATOMIC_ON_CHAIN`) whose `legs: list[AtomicLeg]` walk the loop steps. This is
exactly what the plain `CARRY_RECURSIVE_STAKED` path already builds via `_build_loop_legs`/`_build_instruction`
(STAKE→LEND→BORROW, repeated).

Execution-service's real, working dispatch for this shape is **generic and mode-agnostic**, not archetype-specific:

- `V2InstructionRouter` (`execution_service/v2/router.py`) dispatches by `instruction.action` to
  `ACTION_HANDLER_REGISTRY` (`execution_service/v2/handlers.py`). `InstructionActionV2.ATOMIC` → `AtomicHandler`, which
  handles `ATOMIC_ON_CHAIN`/`LEADER_HEDGE`/`SEQUENCED_WITH_PACING` identically — thin bookkeeping (leg description
  strings + a benchmark-mode mapping), explicitly deferring "real execution... to the existing engine/handlers/
  implementations... or later, to a v2-native algo."
- The paper=batch determinism-spine settlement path
  (`execution_service/backtest_v2/action_handlers.py::resolve_settlement()`, docstring: "P1.4 — the linchpin") resolves
  **any** `AtomicInstruction` (any `execution_mode`) to a benchmark fill generically — `_atomic_notional()` just sums
  `leg.size_units` across legs. It does not special-case recursive-loop vs. any other atomic bundle.

So for **PAPER/BATCH**, this is genuinely the "real integration point already exists, archetype-agnostic" branch — the
exact same path the already-shipped, "CLEAN" plain `CARRY_RECURSIVE_STAKED` relies on. No execution-service change is
needed there for whatever legs strategy-side emits.

For **LIVE on-chain execution** specifically, `RecursiveLoopOrchestrator.open()/.unwind()`
(`execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py`) is real, unit-tested, but **completely
unwired** — grepped every reference to `RecursiveLoopOrchestrator` across all of `execution-service`: it appears only in
its own module, its own unit test (`tests/defi_execution/unit/test_recursive_loop_orchestrator.py`), and one **prose
docstring mention** in `execution_service/matching_engine/defi/gas_cost_model.py` ("The caller (batch backtest replay /
RecursiveLoopOrchestrator) passes `gas_price_gwei`...") — not an actual call site. Nothing in `v2/router.py`,
`v2/handlers.py`, or anywhere under `defi_execution/` constructs a `RecursiveLoopRequest` and calls `.open()`/
`.unwind()`. This is true even for the **already-"CLEAN" plain `CARRY_RECURSIVE_STAKED` archetype** — its "CLEAN"
verdict above only ever assessed the catalog/engine config-key contract (does `on_tick()` emit a non-empty instruction
list), never live-execution wiring to a real on-chain connector.

Critically, `RecursiveLoopOrchestrator`'s actual input — `RecursiveLoopRequest`
(`unified_api_contracts/internal/architecture_v2/recursive_loop_orchestrator.py`) — is **not** a
`StrategyInstructionEnvelope`/`AtomicInstruction` variant at all (never part of the `StrategyInstructionV2` union). It
is a separate, purpose-built Pydantic model: `correlation_id`, `start_amount`, `share_class_coin`, `n_loops` (int,
1-15), `ltv_per_loop` (numeric decimal), `slippage_tolerance_bps`, `opening_mode` (`PERSISTENT`/`FLASH` enum),
`lending_protocol` (enum `AAVE_V3`/`SPARK`/`MORPHO_BLUE`/`COMPOUND_V3`), and for Family 2 an optional `perp_leg_config`
(`perp_venue`, `perp_pair`, `target_net_delta`, `usdc_margin_buffer_min_pct`). It never flows through
`V2InstructionRouter`. So even a working LIVE dispatcher would need a **translation layer** (atomic legs →
`RecursiveLoopRequest` fields), not a drop-in new registry case — this is exactly the "execution-service needs a new
case, out of scope" branch this task anticipated.

### Step 2 finding: the strategy-side design itself is also genuinely undecided, not just unwired — escalating rather than inventing

This is the deciding factor for BUILD vs. SCOPE. The catalog config for both archetypes
(`strategy_service/engine/strategies/v2/target_universe/catalog_carry.py:476-574`) already carries fields that closely
mirror `RecursiveLoopRequest`'s shape (`lending_protocol`, `chain`, `collateral_asset`, `debt_asset`, and for Family 2
`perp_venue`/`perp_pair`/`target_net_delta`/`usdc_margin_buffer_min_pct` — verbatim matches), suggesting the catalog was
authored anticipating this exact integration. But three concrete, load-bearing pieces of that shape are **absent
everywhere in strategy-service, with zero prior design decision**:

1. **No numeric LTV resolution.** The catalog sets `ltv_mode` (a label: `"emode_eth"` / `"market_0945"` /
   `"market_086"`), not `RecursiveLoopRequest`'s numeric `ltv_per_loop`. Grepped `ltv_mode` across `strategy-service`:
   it is read NOWHERE (not in `recursive_staked.py`, not in `param_schema.py`, not anywhere).
   `unified_trading_library.governance_params.read_governance_params_asof(protocol, chain, asset, asof)` (the plain
   archetype's own LTV-override mechanism) has no e-mode/isolated-market axis at all — read its full signature,
   confirmed. Resolving `"emode_eth"` → a numeric LTV requires either extending that governance-params contract or
   hand-picking a reviewed constant — a design decision, not a rename.
2. **No recursion-depth (`n_loops`) convention.** The plain path never configures a loop count either — it derives one
   algorithmically from `target_leverage` + `effective_ltv` via a capped convergence loop in `_build_loop_legs`
   (`max_loops=10`). Family 1/2's catalog sets neither `target_leverage` nor any depth signal, and `param_schema.py` has
   no `"CARRY_RECURSIVE_BORROW_LENDING_ONLY"`/`"CARRY_BASIS_PERP_INV"` entries at all (only a shared
   `"CARRY_RECURSIVE_STAKED"` entry, which both engines read via `staking_yield_enabled` but which was never extended
   for Family 1/2's actual params). The pure closed-form tracer helpers
   (`carry_and_yield/defi_carry_recursive_staked_decision_trace.py::net_apr_recursive`/`net_apr_with_perp_funding`,
   exercised only by `tests/unit/engine/strategies/v2/test_carry_recursive_borrow_archetypes.py`'s formula-arithmetic
   tests) already take `ltv`/`n_loops` as direct numeric args — confirming these values were always meant to be resolved
   somewhere — but grepped every call site: none exist in production code.
3. **No acquisition/hedge-sizing precedent for the non-staking case.** Family 1/2 has no `staking_protocol`, so the
   plain path's SWAP→STAKE bootstrap (turning starting capital into the held LST) has no analogue — modelling how equity
   denominated in the share-class coin becomes the held `collateral_asset` (wstETH/weETH/cbETH/sUSDe) is an
   unprecedented shape. For Family 2's perp-short leg, the one existing basis-hedge precedent in this codebase
   (`staked_basis.py::compute_dynamic_hedge_ratio`) is explicitly LST-native-rate-based (staking-specific) and has no
   non-staking equivalent.

**Confirmed the `on_tick()==[]` stub is a deliberate, tracked placeholder, not an oversight**:
`test_carry_recursive_borrow_archetypes.py`'s own docstring calls it "Phase 5 stub"; the original build plan
(`plans/archive/2026_05/defi_recursive_borrow_archetypes_2026_05_10.md`, Phase 5/9/12) and its successor
(`..._post_cutover_2026_06_01.md`) show the INTENDED validation path for these two archetypes was always a _separate_
harness (Tenderly-fork + "slot 6 PoolMatcher fixtures", Phase 12), not the generic
`AtomicInstruction`/`V2InstructionRouter`/Group-C path every other archetype uses. That harness was never built:
`tests/integration/test_recursive_borrow_scenarios.py::test_cell_scenario` is
`@pytest.mark.skip(reason="... BLOCKED-CREDENTIALS: Tenderly fork + PoolMatcher fixtures required ...")`, and its runner
`_run_backtest_stub()` literally `raise NotImplementedError(...)`. This is the same "money-path archetype is
architecturally incomplete, not just missing a key rename" pattern already documented for the liquidation-feed gap above
— not this task's key-rename bug class.

**Why this is SCOPE, not BUILD**: writing leg-construction code now would require inventing (1) a numeric
LTV-per-mode-label mapping, (2) a recursion-depth policy, and (3) an unprecedented acquisition + (Family 2) hedge-sizing
shape — three real design decisions on a leveraged DeFi money-path archetype, none of them a mechanical rename. A
wrong-but-non-empty instruction here is worse than the current honest `[]`: it could pass a shallow "does `on_tick` emit
something" check while being economically incorrect, whereas `[]` is at least visibly inert. Per the
SUB_AGENT_MANDATORY_RULES escalation clause for a money-path architectural ambiguity, this is reported rather than
guessed.

**Minor incidental finding (not fixed, outside this task's file scope)**:
`tests/integration/test_recursive_borrow_scenarios.py` imports `_build_carry_recursive_staked` (the **plain**
archetype's catalog builder) aliased as `_build_carry_recursive_borrow_perp_hedged` for its Family-2 registry, instead
of `build_carry_basis_perp_inv` — so that file's `FAMILY_2_CELL_IDS` is actually built from the wrong catalog (10
plain-archetype rows, not `CARRY_BASIS_PERP_INV`'s real 10-row catalog). Harmless today (both happen to satisfy the same
`len(...) >= 5` assertion) but should be fixed alongside whichever future work actually touches this test file.

### What's still needed (new scoped follow-up, not built here)

1. **Human design decision, strategy-service**: numeric LTV resolution per lending-market mode (extend
   `read_governance_params_asof`'s governance-params store with an e-mode/isolated-market axis, or hand-pick a reviewed
   constant table), a recursion-depth policy for Family 1/2, and a Family-2 perp-hedge sizing formula. Only once these
   are decided does "mirror `_build_loop_legs`'s established SUPPLY→BORROW→[SWAP-if-cross-asset] pattern into a real
   `AtomicInstruction`" become a mechanical, AO-dispatchable todo (and, per Step 1, needs no new execution-service code
   to settle correctly in PAPER/BATCH once built).
2. **Execution-service (out of this task's scope regardless of #1's outcome)**: `RecursiveLoopOrchestrator` needs a real
   caller — none exists today for ANY archetype, staking or not — and since `RecursiveLoopRequest` is
   schema-incompatible with `AtomicInstruction`/`AtomicLeg`, that caller needs an explicit translation layer, not a
   registry-case addition.
3. The already-scoped Phase 9 (matching-engine DeFi gas-cost model, appears shipped) + Phase 12 (Tenderly-fork +
   PoolMatcher backtest harness, `BLOCKED-CREDENTIALS`, `NotImplementedError` stub) remain the original plan's own
   stated intended validation path for these two archetypes and are unrelated to strategy-service's `on_tick` gap above
   — surfaced here for completeness, not re-scoped.

### Evidence (this section)

Read directly: `unified_api_contracts/internal/architecture_v2/{schemas.py,enums.py,recursive_loop_orchestrator.py}`;
`execution_service/v2/{router.py,handlers.py,atomic_leg_executor.py}`;
`execution_service/backtest_v2/action_handlers.py`;
`execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py`;
`execution_service/matching_engine/defi/gas_cost_model.py`; `unified_trading_library/governance_params.py`;
`strategy_service/engine/strategies/v2/{param_schema.py,carry_and_yield/{recursive_staked.py,staked_basis.py,defi_carry_recursive_staked_decision_trace.py},target_universe/{catalog.py,catalog_carry.py}}`;
`tests/unit/engine/strategies/v2/test_carry_recursive_borrow_archetypes.py`;
`tests/integration/test_recursive_borrow_scenarios.py`;
`plans/archive/2026_05/{defi_recursive_borrow_archetypes_2026_05_10.md,defi_recursive_borrow_archetypes_post_cutover_2026_06_01.md}`.
Grepped (then read every promising hit): `RecursiveLoopOrchestrator`, `RecursiveLoopRequest`, `ATOMIC_ON_CHAIN`,
`ltv_mode`, `n_loops` across `execution-service` and `strategy-service`. No code changed in either repo; this section is
investigation + scoping only.

## Systemic guardrail shipped (2026-07-24) — Recommendation §2 closed, plus 7 more NEW archetype bugs found

Built the single comprehensive parametrized test Recommendation §2 asked for:
`tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py` (`strategy-service@03310bdf`). It
enumerates **every one of the 32 archetypes** in `target_universe/catalog.py`'s `_BUILDERS_BY_ARCHETYPE` dispatch
registry (not just the DeFi ones this doc's original sweep covered — the doc's own Recommendation §2 asked for "every
`StrategyArchetype` with a catalog builder", which spans CeFi/TradFi/Sports too) — 531 total catalog rows — **plus** all
28 entries in `archetype_slots_defi.py`'s `DEFI_SLOTS` (the second catalog surface this doc's earlier section
discovered). For every row: constructs the real registered engine (`factory.py`'s `ARCHETYPE_ENGINE_REGISTRY`) from that
row's actual `initial_config`, asserts construction doesn't raise, then calls `on_tick` with a plausible,
engine-appropriate synthetic tick (feature keys derived from the row's own config where the engine keys them
per-venue/per-protocol/per-outcome) and asserts a real, non-empty instruction — unless the archetype is on one of two
small, explicit, named allow-lists:

- **`_ALLOWED_EMPTY_ARCHETYPES`** (6 archetypes, legitimate + permanent, construction-only) — exactly the set this doc
  already named: `CARRY_RECURSIVE_BORROW_LENDING_ONLY` + `CARRY_BASIS_PERP_INV` (orchestrator-stub,
  `staking_yield_enabled=false`), `LIQUIDATION_CAPTURE` + `ARBITRAGE_MEV_LIQUIDATION_BUNDLE` (no live
  liquidation-candidate feed exists anywhere, confirmed above), `ARBITRAGE_MEV_JIT_LIQUIDITY` + `ARBITRAGE_MEV_BACKRUN`
  (opportunistic/mempool-driven by design, no static currency universe).
- **`_KNOWN_BROKEN_ARCHETYPES`** (5 archetypes — see "NEW bugs found" below) — wired via
  `pytest.mark.xfail(strict=True, ...)`, one line of reason each. `strict=True` means the row is asserted to fail TODAY
  (visible XFAIL in the test report, not a silent pass) — the moment a future fix makes it pass, the suite turns that
  into an XPASS **failure**, forcing whoever fixes the archetype to also delete its allow-list entry, so this file can
  never quietly drift stale in either direction.

Any row not on either list that returns `[]` fails the test outright — the guardrail this doc's Recommendation §2 asked
for.

**Wiring**: `strategy-service/scripts/quality-gates.sh` sets `PYTEST_UNIT_DIR="tests/"` (confirmed by reading the
script, not assumed) — the new file lives under `tests/unit/engine/strategies/v2/`, so it is automatically part of every
future `quality-gates.sh` run, no extra wiring needed.

### 2 mechanical catalog fixes shipped alongside (same bug class, found by this test's own construction)

While building the test, its OWN construction run found 2 more archetypes silently no-op'ing forever via the exact same
catalog/engine config-key-drift bug class — but these two were unambiguous, same-file renames (no design judgment
required), so fixed immediately per the same triage this doc already used for the DeFi fixes above
(`strategy-service@238fb797`, `target_universe/catalog_trading.py`):

- **`STAT_ARB_PAIRS_FIXED`** (7 rows) — catalog set `leg_a`/`leg_b`/`venue`; `StatArbPairsFixedEngine._load_pair_config`
  reads `long_instrument`/`short_instrument`/`long_venue` (confirmed by grep: no other consumer reads `leg_a`/`leg_b`
  for this catalog surface — kept as documentation). Added the real keys alongside.
- **`STAT_ARB_CROSS_SECTIONAL`** (3 rows) — catalog set `basket`; `StatArbCrossSectionalEngine._parse_universe` reads
  `universe`. Added `universe` (same value) alongside `basket`.

Both verified empirically (constructed the real engine from the pre-fix row → confirmed `on_tick` returned `[]` forever;
post-fix → real instruction). Both now covered by the systemic test's must-fire assertion (not allow-listed).

### 5 NEW, still-unfixed bugs found (NOT silently allow-listed — flagged per the sub-agent task's explicit instruction)

The remaining 5 broken rows this test's construction found require real trading-parameter/design judgment to fix
correctly (which threshold values, which outcome-id convention, which option strike/expiry rule) — not a mechanical
rename — so they were **not** fixed here, and are **not** silently swept into the legitimate allow-list. Each is
`xfail(strict=True)` with a one-line reason in the test file itself (also summarized here for visibility):

| Archetype                         | Rows | Catalog sets                                                                               | Engine actually reads                                                                                     | Why not mechanical                                                                                                                                                                                                                                    |
| --------------------------------- | ---- | ------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `RULES_DIRECTIONAL_CONTINUOUS`    | 19   | `entry_zscore`/`exit_zscore`/`window_size`/`signal`                                        | `long_feature`/`long_threshold`/`short_feature`/`short_threshold`                                         | Catalog encodes z-score mean-reversion (distinct entry/exit); engine is a single static-threshold rule model with no reversion/exit concept — no mechanical mapping exists.                                                                           |
| `RULES_DIRECTIONAL_EVENT_SETTLED` | 9    | `edge_method`/`min_drift_edge`/`features`, or `staking_method`/`stake_size`, or `category` | dynamically-named `rule_<name> = "<feat>:<op>:<val>,...\|<outcome>\|<stake_frac>\|<max_odds>"` DSL string | Needs real per-row threshold/outcome/stake values invented, not renamed.                                                                                                                                                                              |
| `ML_DIRECTIONAL_EVENT_SETTLED`    | 15   | `venue`/`league`/`market`/`edge_method`/`staking_method`                                   | `outcome_order` (comma-sep outcome_ids indexed by `predicted_class`)                                      | `market` (1X2/halftime_1x2/match_winner/moneyline) suggests a plausible ordering, but the exact outcome-id strings the upstream ML model + features pipeline emit is a convention decision on a money-path archetype — escalated rather than guessed. |
| `MARKET_MAKING_EVENT_SETTLED`     | 6    | `venue`/`league`/`market`/`spread_ticks`                                                   | `back_instrument`+`lay_instrument`                                                                        | Real per-exchange market/selection instrument ids, not derivable from league+market alone.                                                                                                                                                            |
| `VOL_TRADING_OPTIONS`             | 14   | `underlying`/`expression`/`edge_method`/`iv_percentile_*`                                  | `call_instrument`+`put_instrument`                                                                        | Needs an actual strike+expiry selection rule (ATM straddle selection) — a genuine build task, same class of gap as `CARRY_STAKED_BASIS_DATED`'s dated-contract resolver, not a rename.                                                                |

**Total new-bug footprint found by this systemic test**: 66 rows across these 5 archetypes, on top of the 5 archetypes
(across ~40 rows) already fixed earlier in this doc — confirming the doc's own prediction that this bug class was
systemic, not DeFi-specific. **Follow-up needed** (new, not yet scoped as todos elsewhere): a human design decision per
archetype above (rule-threshold values / outcome-id convention / option strike-expiry rule), after which the mechanical
catalog fix + removing the corresponding `xfail` entry is a scoped, AO-dispatchable todo.

**Verification**: `bash scripts/quality-gates.sh --no-fix` — full suite green: 5510 passed, 206 skipped, **5 xfailed**
(exactly the 5 archetypes above, confirmed by name in the pytest summary — zero unexpected failures, zero XPASS).
Re-confirmed via a plain-python dry-run harness mirroring the exact same construct+fire logic across all 531 catalog
rows + 28 `DEFI_SLOTS` rows (0 unexpected failures, 0 unexpected passes) before and after shipping.

**Shipped**: `strategy-service@03310bdf` (new test file, 540 lines) + `strategy-service@238fb797` (the 2 mechanical
`catalog_trading.py` fixes — landed as a separate follow-up commit after a quickmerge stash-interaction in a heavily
concurrent shared checkout dropped it from the first attempt; verified both commits are on `origin/live-defi-rollout`
and the working tree matches origin exactly with zero drift).

**Incidental fix, unblocked shipping fleet-wide**: while shipping, `run_validators.py`'s plans/active/\*.md link checker
(which every repo's `quickmerge.sh` re-gate runs regardless of target repo) was failing on a stale link in
`master_to_live_defi_2026_05_23.md` → a `/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md` deleted
by an unrelated, in-flight 3-way plan split that missed updating this one referrer — blocking every repo's quickmerge,
not just this one. Fixed via the sanctioned path (re-ran `scripts/plans/regenerate_active_plan_inventory.py`, the
auto-generated section's own owner script, rather than hand-editing the table) — `unified-trading-pm@1e13d425a`.

## Todos

> **na-eligibility-audit 2026-08-01**: KEEP-NA-STALE-ITEMS — item 1 (human design decision) stays KEEP-NA valid
> (textbook judgment call, escalated rather than guessed). Item 2 (7-archetype sweep) closed as stale, see inline note.
> Doc stays `assigned_vm: NA` — item 1's real work remains open.

- [x] ✅ [DESIGN] P0. **Human design decision for 5 broken archetypes (66 rows)** — `RULES_DIRECTIONAL_CONTINUOUS`,
      `RULES_DIRECTIONAL_EVENT_SETTLED`, `ML_DIRECTIONAL_EVENT_SETTLED`, `MARKET_MAKING_EVENT_SETTLED`,
      `VOL_TRADING_OPTIONS` each need a real trading-parameter/design ruling (threshold values, outcome-id convention,
      option strike/expiry rule) before the mechanical catalog fix can ship; currently held as visible
      `xfail(strict=True)`. **RULED (operator, 2026-08-08)**, per-archetype (split below): -
      `RULES_DIRECTIONAL_CONTINUOUS`: build real reversion-exit support in the engine (not a static-threshold
      approximation) — filed as `[SCRIPT] P1` below. - `ML_DIRECTIONAL_EVENT_SETTLED`: extend the existing 2-market-type
      test-fixture `outcome_order` precedent to all 4 market types — filed as `[SCRIPT] P2` below. -
      `VOL_TRADING_OPTIONS`: ATM straddle, nearest weekly expiry ≥ 7 DTE — filed as `[SCRIPT] P2` below. -
      `RULES_DIRECTIONAL_EVENT_SETTLED` (9 rows) and `MARKET_MAKING_EVENT_SETTLED` (6 rows): stay `xfail` — genuinely
      need real per-row rule DSL strings / real per-exchange instrument IDs only the operator has; not derivable, not
      guessed.
- [x] ✅ [SCRIPT] P1. **`RULES_DIRECTIONAL_CONTINUOUS` (19 rows) — build reversion-exit support in the rule engine**
      (per the 2026-08-08 ruling above): the engine today is a single static-threshold long/short rule with no
      exit-on-reversion concept; the catalog's `entry_zscore`/`exit_zscore`/`window_size`/`signal` config needs a real
      engine-level mechanism to enter at `entry_zscore`, hold, and exit at `exit_zscore` (mean-reversion, not a second
      independent threshold rule). A genuine build task, not a config rename — scope the engine change before
      estimating. — strategy-service@4e3262d70 (dual-mode engine: z-score reversion mode + legacy rule mode;
      `signal`/`entry_zscore`/`exit_zscore` wired for all 19 catalog rows + 8 v5 slot-table rows; 18 regression tests;
      QG green)
- [x] ✅ [SCRIPT] P2. **`ML_DIRECTIONAL_EVENT_SETTLED` (15 rows) — wire `outcome_order` for all 4 market types** (per
      the 2026-08-08 ruling above): `1X2`/`halftime_1x2` → `"home,draw,away"` (3-way), `match_winner`/`moneyline` →
      `"home,away"` (2-way) — the same convention the existing test fixture already uses for 2 of the 4 market types,
      promoted to the production catalog and extended to cover the other 2. Verify against the real upstream ML model's
      `predicted_class` indexing before shipping (money-path archetype). — strategy-service@2667e967d
- [x] ✅ [SCRIPT] P2. **`VOL_TRADING_OPTIONS` (14 rows) — wire the ATM-straddle strike/expiry resolver** (per the
      2026-08-08 ruling above): select the strike nearest to spot (at-the-money) and the nearest weekly expiry with ≥ 7
      days to expiry; resolve `call_instrument`/`put_instrument` from that pair. Same class of gap as
      `CARRY_STAKED_BASIS_DATED`'s dated-contract resolver — reuse that pattern if applicable. —
      strategy-service@4b9e01fbf (atm_straddle_resolver.py pure-function resolver; options.py wired; VOL_SURFACE_BTC
      slot missing underlying/venue fixed; systemic test xfail removed; resolver unit tests added; QG green)
- [x] ✅ [SCRIPT] P2. **Sweep the remaining 7 already-drivable archetypes** — `CARRY_FUNDING_DISPERSION`,
      `DEFI_LP_CONCENTRATED`, `DEFI_LP_POOL`, `DEFI_LP_VAULT` remain fully unchecked against either catalog surface for
      the same config-key-contract drift bug class this doc found everywhere else. **na-eligibility-audit 2026-08-01:
      CLOSED — already covered by this doc's own later section.** "Systemic guardrail shipped (2026-07-24)" above
      (`strategy-service@03310bdf`,
      `tests/unit/engine/strategies/v2/test_all_catalogued_archetypes_construct_and_fire.py`) enumerates all 32
      `target_universe/catalog.py` archetypes + all 28 `DEFI_SLOTS` entries and asserts construction + non-empty
      `on_tick` firing unless allow-listed; CARRY_FUNDING_DISPERSION/DEFI_LP_CONCENTRATED/DEFI_LP_POOL/DEFI_LP_VAULT are
      on neither the 6-item `_ALLOWED_EMPTY_ARCHETYPES` nor the 5-item `_KNOWN_BROKEN_ARCHETYPES` xfail list; suite
      green with "5 xfailed (exactly the 5 archetypes above ... zero unexpected failures, zero XPASS)" — matches this
      doc's own earlier Recommendation §3 update: "✅ DONE 2026-07-24 ... CARRY_FUNDING_DISPERSION (78 rows) ...
      DEFI_LP_CONCENTRATED/_POOL/_VAULT (3 rows each) all confirmed firing cleanly, zero silent-degradation found." This
      checkbox predated that confirmation and was never flipped.
- [ ] [DESIGN] P2. **RULED 2026-08-09 (operator): pollable-candidate-registry design (not push-on-tick)** for the live
      liquidation-candidate feed integration (`LIQUIDATION_CAPTURE` + `ARBITRAGE_MEV_LIQUIDATION_BUNDLE`, both currently
      `_ALLOWED_EMPTY_ARCHETYPES`). The transport-shape decision is resolved — **still NOT AO-dispatchable**: a second
      design sub-decision remains open (features-service's `liq_candidate_*_<id>` dynamically-keyed calculator is an
      unprecedented per-candidate feature-naming shape needing its own design call, per the "Scope of the real, unbuilt
      integration" section above), and the 3-repo build (market-tick-data-service forking `position_data_handler.py` to
      poll candidates sorted by `healthFactor` ascending via the UTL `EventTransport` facade; features-service's new
      calculator; strategy-service's live params-mutation path on `V2EngineOrchestrator`/`BaseArchetypeEngineV2`, which
      today sets `self.params` once and never rewrites it) still needs to be broken into bounded, AO-dispatchable todos
      against this now-resolved direction. Next step: a LOCAL/human design pass that resolves the feature-naming
      sub-decision and scopes the pollable-registry build into concrete todos — not yet actioned.
- [x] ✅ [DESIGN] P2. **`RecursiveLoopOrchestrator` translation layer for `CARRY_RECURSIVE_BORROW_LENDING_ONLY` /
      `CARRY_BASIS_PERP_INV`** (both currently `_ALLOWED_EMPTY_ARCHETYPES`, gated on `staking_yield_enabled=false`).
      **RULED 2026-08-09 (operator, interactive, recorded in this doc's own DRAFT PROPOSAL 2026-08-09 subsection below
      and implemented per `/plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md`): all 3 numbers in
      the 2026-08-09 DRAFT PROPOSAL below are ADOPTED as-is** — (a) LTV-per-lending-market-mode: adopt the codex table
      (Aave e-mode `ETH_CORRELATED`=0.93, Morpho `market_0945`=0.945, `market_086`=0.86, formula
      `ltv_target = liquidation_threshold - 0.05` for any untabled mode); (b) recursion-depth: keep the already-shipped
      `recursion_depth_max=5` for both archetypes, chain-uniform — the codex doc's per-chain 8/10/12 figures are
      explicitly NOT adopted at this time, revisit only after live track record; (c) Family-2 perp-hedge rebalance
      sizing: use `net_underlying_delta`/`residual_hedge_size` (`unified_trading_library/risk/net_delta.py`) as-is for
      the ongoing rebalance leg — the SEPARATE initial acquisition/bootstrap-sizing question remains open, not ruled
      here. Per the "orchestrator-stub: exhaustive investigation, scoped not built" section above:
      `RecursiveLoopOrchestrator` has no caller for ANY archetype today, and `RecursiveLoopRequest` is
      schema-incompatible with `AtomicInstruction`/`AtomicLeg`, so a real caller needs an explicit translation layer,
      not a registry-case addition. **RESOLVED 2026-08-09**: a code-landscape mapping pass confirmed exact file/function
      targets, and the actual translation-layer build is now tracked as its own AO-dispatched plan:
      `/plans/archive/2026_08/recursive_loop_orchestrator_wiring_2026_08_09.md` (8 todos, `sequential: true`, gated
      finalize companion `recursive_loop_orchestrator_wiring_finalize_2026_08_09.md`). **DONE 2026-08-09** — the wiring
      plan's finalize companion independently re-verified all 8 todos (commit existence confirmed as ancestors of
      `origin/live-defi-rollout`, full `quality-gates.sh` re-run green on all 3 touched repos, not just the recorded
      evidence lines trusted): `unified-api-contracts@547b1d1b` (ltv_mode resolver, `resolve_ltv_mode()` in
      `defi_reserve_params.py` — 0.93/0.945/0.86 asserted, re-run green); `strategy-service@b98f74fb` (`ltv_per_loop` +
      `n_loops` catalog wiring in `catalog_carry.py`, both Family-1/2 builders); `strategy-service@817bb4e0` (Family-1
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY` real `on_tick()` leg construction, STAKE→TRANSFER→LEND→BORROW ×5 loops);
      `strategy-service@f2ac7fdf` (Family-2 `CARRY_BASIS_PERP_INV` real `on_tick()`, lending loop + perp-hedge leg via
      `residual_hedge_size()`); `execution-service@2352a17e` (`recursive_loop_runner.py` —
      `RecursiveLoopOrchestrator.open()`/`.unwind()`'s first real production caller); `strategy-service@d6c86f44`
      (removed both archetypes' `_ALLOWED_EMPTY_ARCHETYPES` exemptions — confirmed absent from the dict on re-read).
      Full `quality-gates.sh` (`--no-fix`) re-ran green on all 3 repos independently this session: unified-api-contracts
      (396s), strategy-service (5836 passed, 199s), execution-service (7895 passed, 226s). Todo 7 (Family-2 hedge-poller
      audit, no code — outcome (b) no suitable poller exists) re-verified via the exact same greps: results match
      verbatim; follow-up `[DESIGN]` todo already filed on the finalize plan (see below). Two minor (non-blocking)
      evidence-line inaccuracies found on re-verification, noted for the record only: the Family-1 `on_tick()` test file
      (`test_recursive_borrow_lending_only_family1_on_tick.py`) has 5 tests, not the "6 tests" the parent plan's
      Progress Log claims; `test_recursive_loop_runner.py` has 11 tests, not "13" — both files exist, are correctly
      scoped, and pass; only the recorded test-count narrative was off. Full re-verification detail:
      `/plans/archive/2026_08/recursive_loop_orchestrator_wiring_finalize_2026_08_09.md` todo 1's evidence trail.

      ---

          ### DRAFT PROPOSAL 2026-08-09 (recording agent, for operator review — NOT yet approved)

          Operator asked the recording agent to draft first-pass candidate numbers/formulas for the 3 decisions, grounded
          in what already exists in the codebase, explicitly as a starting point for review/adjustment — not a ruling.
          This todo stays open pending the operator's actual review. Real leveraged DeFi money-path decision; every number
          below is either a DIRECT citation of already-shipped code/config or an already-written codex design doc, not
          invented from scratch — confidence and remaining gaps are flagged per item, not overstated.

          **(a) Numeric LTV-per-lending-market-mode resolution.**

          A fully worked answer to this already exists as a codex SSOT
          (`/codex/09-strategy/architecture-v2/archetypes/carry-recursive-borrow-lending-only.md`, `implementation_status:
          design`, `authoritative_for: [CARRY_RECURSIVE_BORROW_LENDING_ONLY archetype specification]` — i.e. it IS this
          workspace's designated SSOT for this archetype's numbers, it just hasn't been wired into the catalog/engine
          code yet). Its per-cell table (lines 96-104): Aave V3 e-mode `ETH_CORRELATED` = **0.93 LTV**; Morpho
          `market_0945` = **0.945 LTV**; Morpho `market_086` = **0.86 LTV**; general rule `ltv_target =
          liquidation_threshold - 0.05` (a fixed 5-point safety buffer below the protocol's own liquidation threshold).
          This is corroborated by LIVE data, not just the design doc: `market-tick-data-service/market_tick_data_service/
          market_interface/adapters/defi/aave_lending.py:127-128` fetches real `ltv`/`liquidation_threshold` from Aave's
          own subgraph at runtime, and `aave_utils.py:54-60`'s hardcoded fallback table independently states the same
          e-mode figures (0.93 LTV / 0.95 liquidation threshold) for the same wstETH/weETH/ETH pairs — two independent
          sources agree. Proposed: adopt the codex table's LTV values directly, with the `ltv_target = liq_threshold -
          0.05` rule as the resolution formula for any lending mode not explicitly tabled. **Confidence: HIGH** on the
          Aave e-mode figure (0.93, corroborated live); **MEDIUM** on the two Morpho figures (design-doc only, not
          independently corroborated by a second live source in this pass). Gap: UAC's shipped
          `ArchetypeConfig.safety_buffer_ltv=0.05` (both archetypes, `archetype_config.py:272,304`) already matches the
          codex rule's buffer — so this piece may be closer to "already decided, just not consumed by the catalog
          builder" than "undecided."

          **(b) Recursion-depth policy.**

          **Found a real, unresolved discrepancy — flagging rather than picking a side.** The same codex SSOT
          (`carry-recursive-borrow-lending-only.md:123`) specifies PER-CHAIN depths: `recursion_depth_max`: **8 (ethereum)
          / 10 (arbitrum) / 12 (base)** — cheaper L2 gas justifying deeper loops. The sibling `carry-basis-perp-inv.md:132`
          states a flat `max_recursion_depth: 8`. But the ALREADY-SHIPPED UAC config
          (`archetype_config.py:271,299`) sets `recursion_depth_max=5` for BOTH archetypes, chain-uniform — verified
          directly in the source, not secondhand. These disagree by a wide margin (5 vs. 8-12), and 5 is the materially
          MORE conservative choice (each additional loop compounds leverage and liquidation-cascade risk). Proposed,
          conservatively: **keep the shipped `recursion_depth_max=5` as the initial live value for BOTH archetypes**,
          overriding the codex doc's more aggressive per-chain figures, specifically BECAUSE Family 1/2 are explicitly
          annotated "not yet live-tested" in the codex doc itself (line 116's own comment on `position_cap_usd`) — a
          first live deployment is not the place to run the most aggressive depth in the design doc. The per-chain 8/10/12
          figures could be revisited as a follow-on increase once Family 1/2 have live track record. **This is the one
          item of the three I have real reservations about proposing a specific alternative number for beyond "start at
          the already-shipped conservative 5"** — the codex doc's higher figures may reflect real risk/reward analysis
          the recording agent hasn't fully reconstructed; the operator (or whoever wrote that codex table) may have
          context this pass doesn't. **Confidence: MEDIUM** on "5 is a safe starting point"; **LOW** on whether 8/10/12
          is actually the "right" eventual target vs. just an unvetted design-time guess — genuinely the operator's call.

          **(c) Family-2 perp-hedge sizing formula.**

          **This one may already be effectively answered by shipped code** — the issue doc's own earlier investigation
          (line ~574-576 above) says "no non-staking hedge-sizing precedent exists," but that claim is about the INITIAL
          acquisition/bootstrap sizing (turning starting equity into the held collateral asset — genuinely still
          unprecedented, not resolved by anything found this pass), NOT the ONGOING rebalance-sizing formula, which
          already exists, is canonical, and is a direct match for what Family 2 needs: UTL
          `unified_trading_library/risk/net_delta.py:33-70` — `net_underlying_delta(collateral_qty, debt_qty,
          lst_exchange_rate) = collateral_qty * lst_exchange_rate - debt_qty` (net ETH-equivalent exposure, `E_actual`)
          and `residual_hedge_size(E_actual, target_net_delta, floor_zero=True) = max(0, E_actual - target_net_delta)`
          (hedge notional to drive net delta to target). Both functions' own docstrings say they are the "canonical
          extraction of execution-service `PerpHedgeSizer.read_e_from_aave_data`/`compute_rebalance`"
          (`execution-service/execution_service/defi_execution/helpers/perp_hedge_sizer.py:90-99`) — i.e. this formula was
          built FOR this exact archetype family, already runs in execution-service, and matches the codex SSOT
          (`carry-basis-perp-inv.md:87,159`: `perp_short_size = max(0, E_actual - target_net_delta)`, rebalance trigger
          `|perp_short_size - E_actual| > 5% x E_actual`) — three independent sources (UTL, execution-service, codex)
          agree on the same formula. Proposed: use `net_underlying_delta` + `residual_hedge_size` as-is for the ONGOING
          rebalance leg of the `RecursiveLoopOrchestrator` translation layer; the INITIAL acquisition/bootstrap sizing
          (Family 1/2's SWAP→STAKE-equivalent first leg) is a SEPARATE, still-genuinely-open design gap this pass did not
          resolve — do not conflate the two. **Confidence: HIGH** on the rebalance formula (already shipped, 3-source
          agreement); the acquisition-sizing gap is unaddressed, not drafted here (out of scope for "perp-hedge sizing
          formula" as literally asked, but flagged so it isn't silently assumed solved).

          **What this draft does NOT resolve**: the initial acquisition/bootstrap-sizing shape for Family 1/2 (turning
          starting capital into the held collateral asset) remains genuinely undesigned; the codex doc's per-chain
          recursion-depth figures (8/10/12) vs. the shipped conservative 5 needs an explicit operator pick, not just my
          conservative default; and none of the above resolves the SEPARATE `RecursiveLoopOrchestrator` translation-layer
          / schema-incompatibility build this todo's own first paragraph describes — that remains its own follow-on once
          these numbers are ratified.

## Progress Log

- **na-corpus-digest-closeout 2026-08-08**: operator ruled interactively on the 5-broken-archetype design decision,
  per-archetype: `RULES_DIRECTIONAL_CONTINUOUS` gets a real engine-level reversion-exit build (not an approximation);
  `ML_DIRECTIONAL_EVENT_SETTLED` extends the existing test-fixture `outcome_order` precedent to all 4 market types;
  `VOL_TRADING_OPTIONS` gets an ATM-straddle/nearest-weekly-≥7DTE resolver; `RULES_DIRECTIONAL_EVENT_SETTLED` and
  `MARKET_MAKING_EVENT_SETTLED` stay `xfail` — genuinely need real per-row values only the operator has. Filed 3 new
  `[SCRIPT]` implementation todos, flipped `assigned_vm: NA` → `planning`.
- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **na-eligibility-audit 2026-08-03**: KEEP-NA valid — re-confirmed independently. Item 2 (7-archetype sweep) is now
  checked off (`[x]`), so the doc's only remaining open item is item 1, the P0 human design decision for 5 broken
  archetypes — a textbook judgment call (trading-parameter/outcome-id/option-strike rulings), correctly held as visible
  `xfail(strict=True)` pending a human ruling, not a bounded worker task. Only diff since the 2026-08-01 marker was the
  context-scout metadata backfill (no content change). Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) — still accurate against the doc's only remaining
  open item (the P0 design decision on `catalog_trading.py`'s 5 broken archetypes, all under `target_universe/`).
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — re-confirmed independently;
  only diff since 2026-08-03 was a context-scout metadata-only touch. Sole open checkbox (5 broken archetypes needing
  human trading-parameter rulings, `xfail(strict=True)`) independently re-verified live against strategy-service's test
  file — still unfixed, still accurate; no active planning doc has claimed it
  (`defi_satellite_ao_dispatch_ batch3_2026_07_26.md` explicitly says leave xfail'd, don't force-fix). Incidental, not
  actioned: 2 untracked prose-only design items (RecursiveLoopOrchestrator translation-layer build; 3-repo
  liquidation-feed integration), both independently spot-checked live and confirmed still real/unbuilt; 1 stale prose
  fragment (archetype_slots sweep already done 2026-07-27 via batch3, doc text not updated) — hygiene notes only. Doc
  stays `assigned_vm: NA`.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — re-confirmed independently; no content change
  since the 2026-08-06 audit (context-scout metadata only, per git log). Sole open checkbox (P0 human design decision
  for 5 broken archetypes, 66 rows, held `xfail(strict=True)`) remains a textbook trading-parameter/design-judgment
  call, not a bounded worker task. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **2026-08-09 (operator ruling)**: RULED on the liquidation-candidate feed's transport-shape design decision —
  pollable-candidate-registry, not push-on-tick. Retagged `[OPERATOR]` → `[DESIGN]` and reworded to record the resolved
  direction while keeping the todo open: a second sub-decision (features-service's per-candidate feature-naming shape)
  and the actual 3-repo scoping pass remain outstanding before this is AO-dispatchable. Doc stays `assigned_vm: NA` — no
  bounded worker-determinable outcome yet.
- **slot-17 2026-08-09**: dispatched this doc's `[DESIGN]` pollable-candidate-registry checkbox as an AO backlog task
  despite the checkbox's own text stating it's still not AO-dispatchable — found frontmatter `assigned_vm: planning`
  (left over from the 2026-08-08 ruling that filed 3 unrelated `[SCRIPT]` todos on the SAME doc) contradicted every
  Progress Log entry since 2026-08-01, all of which state "Doc stays `assigned_vm: NA`". Corrected
  `assigned_vm: planning` → `NA` + `execution_scope: orchestrator-agent` → `local-only` to match the doc's own
  consistently-stated intent and stop future redispatch of this genuinely-not-worker-determinable item. Did not attempt
  the feature-naming sub-decision or the 3-repo scoping pass myself — per
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility", an open-ended
  design/judgment call on a production money-path schema decision is a human decision, not a worker todo; filed
  `/blocked` with options + a recommendation so the operator can rule on it the same way the 2026-08-08 5-archetype
  ruling was made (interactive session, not autonomous worker judgment). Checkbox left unflipped — the item is not
  actually done.
- **RULED 2026-08-09 (operator)**: "I draft a first-pass proposal." Operator asked the recording agent to draft concrete
  candidate numbers/formulas for the 3 open trading-parameter decisions on this todo (LTV-per-mode, recursion-depth
  policy, Family-2 perp-hedge sizing), grounded in the existing codebase, as a DRAFT for operator review, not a ruling.
  Grepped strategy-service/market-tick-data-service/features-service plus the codex archetype SSOTs before drafting
  anything, per the ruling's own instruction not to invent from nothing. Found (a) a fully worked LTV table already
  exists as a codex SSOT (`carry-recursive-borrow-lending-only.md`), corroborated by live Aave subgraph data + a
  hardcoded fallback table in `market-tick-data-service`; (b) a real, unresolved numeric discrepancy between that same
  codex doc's per-chain recursion-depth figures (8/10/12) and the already-shipped UAC config's flat
  `recursion_depth_max=5` — flagged rather than silently picked, with a conservative recommendation (keep 5) explicitly
  caveated as the recording agent's own risk-averse bias, not a confident answer; (c) the Family-2 perp-hedge REBALANCE
  formula already exists, is shipped, and is used in production (`unified-trading-library/risk/net_delta.py`,
  `execution-service`'s `PerpHedgeSizer`, matching the codex SSOT) — three independent sources agree, so this piece may
  already be effectively answered, though the SEPARATE initial-acquisition/bootstrap-sizing question remains genuinely
  open and was not resolved here. Wrote the full draft, with per-item confidence levels and explicit gaps, into a new
  "DRAFT PROPOSAL 2026-08-09" subsection under the todo above. **Did NOT flip the todo done** — it stays open pending
  the operator's actual review/adjustment of these draft numbers, per the ruling's own instruction.
- **round9-reclassify-satellite-sweep 2026-08-09** (defi tranche): KEEP-NA, valid — re-confirmed independently, no
  whole-doc RECLASSIFY or per-item satellite-extraction found. Both open todos are freshly re-verified same-day as
  genuinely not-yet-dispatchable: the `[DESIGN]` pollable-candidate-registry item was itself DISPATCHED and then
  self-corrected back to `assigned_vm: NA` by a `slot-17` session earlier today (see that Progress Log entry above) — a
  second design sub-decision (features-service's per-candidate feature-naming shape) genuinely remains open; the
  `[OPERATOR]` RecursiveLoopOrchestrator item has a same-day draft proposal awaiting actual operator ruling, explicitly
  not yet approved (see the entry immediately above). No new fact from today's sweep (credential/webhook unblocks)
  touches either item. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-16** [body-hash:c40a1852d57966c9]: KEEP-NA, valid — 976-line issue doc: systemic strategy-service catalog/engine config-key-contract-drift audit spanning DeFi + CeFi/TradFi/Sports archetypes, almost entirely resolved (the P0 design-decision todo and its 3 filed [SCRIPT] implementation todos are all checked [x] with shipped SHAs).
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries) — unchanged, still accurate
- **context-scout 2026-08-20 (fingerprint cross-link)**: added `mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` (7 entries total) — independently documents the identical `liq_candidate_debt_amount_<id>`/`liq_candidate_liq_bonus_pct_<id>` missing-feature finding.
