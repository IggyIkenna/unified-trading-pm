---
name: archetype-paper-readiness
overview:
  Per-archetype 4-state taxonomy (paper-runnable / paper-shippable / backtest-only / stub) for every entry in the
  canonical strategy archetype catalogue (UAC `StrategyArchetype` enum = 57 archetypes; full coverage matrix at
  `codex/09-strategy/architecture-v2/category-instrument-coverage.md`). Pins the closed-set gate set every strategy
  archetype must clear before being eligible for `OperationalMode.PAPER`.
type: codex-ssot
status: complete
created: 2026-05-09
last_verified: 2026-06-15
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/active/master_to_live_defi_2026_05_23.md # Group F items 18.A / 18.B
---

# Archetype paper-mode readiness

> **Source file note (corrected 2026-05-12 per `codex_audit_strategy_2026_05_12.md` ST-4)**: the 4-state taxonomy is for
> **strategy archetypes** per UAC `StrategyArchetype` (57 members) — the same set documented in
> `codex/09-strategy/architecture-v2/README.md` "57 Archetypes" + the matrix in `category-instrument-coverage.md`. It is
> NOT a taxonomy of `strategy_service/portfolio_allocator/archetypes.py`, which holds the 8 **PortfolioAllocator
> archetype engines** (risk-parity / factor / tactical-overlay / multi-strategy / etc.) — those are allocator engines, a
> different concept. An earlier version of this doc pointed at the allocator file by mistake.

## 4-state taxonomy

Every archetype lands in exactly one of four states for `OperationalMode.PAPER` readiness:

| State                  | Meaning                                                                                                                                                        |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **paper-runnable**     | Has run paper-mode end-to-end against real venues + real data, P&L attribution clean, recon green. **The only state that counts as ready for live promotion.** |
| **paper-shippable**    | Code exists + tests exist + matching engine wired; never executed paper end-to-end on real infra. Plumbing ready; evidence pending.                            |
| **backtest-only**      | Only batch-mode evidence exists; paper plumbing not wired. Most archetypes today.                                                                              |
| **stub / placeholder** | Archetype name exists in catalogue but no engine code, or engine code is sketch-only. Not eligible for paper-mode.                                             |

**Downstream consumer of this taxonomy**: `<BacktestComparisonPanel>` in the Signal Broadcast Counterparty dashboard
reads paper-readiness state to decide which archetypes surface their backtest comparisons. Cross-ref:
[`signal-broadcast-architecture.md`](../../../14-customer-journeys/shared-core/signal-broadcast-architecture.md) §
"Counterparty dashboard" (ST-20 cross-ref, added 2026-05-13 per
`codex_doc_currency_and_consolidation_post_cutover_2026_05_12.md` Sweep 3).

## Paper-runnable gate set (closed set)

An archetype graduates from `paper-shippable` → `paper-runnable` only when ALL of the following are met:

1. **End-to-end run completed** for ≥3 continuous days against real venues + real data + matching engine (or testnet per
   `paper_target_registry`).
2. **Event stream verified** per CLAUDE.md "no fire-and-forget VM launches" rule — STARTED / per-instrument progress /
   STOPPED with non-empty metadata.
3. **P&L attribution decomposed** by source (strategy alpha vs execution alpha vs financing) per
   `09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`.
4. **Recon green** for paper-vs-live (where live coverage exists) and batch-vs-paper for the run window per
   `pvl-p21a-three-way-recon`.
5. **Lookahead-bias clean** — `LookaheadBiasError` not raised over the run window; `available_at` semantics correct per
   `02-data/availability-manifest-and-data-status.md`.
6. **Risk + alerting wired** — risk-and-exposure pre-flight checks fired correctly; alerting-service rules consumed the
   mode-tagged events per `pvl-p22a`.
7. **Position-balance reconciled** — PBM dual projection matches actual venue/chain state after each fill.

Archetypes that fail ANY gate stay in `paper-shippable` until the gap closes.

## Per-archetype matrix (populated 2026-05-17 by slot-5 per `pvl-p18b`)

Source of truth for engine registration: `strategy_service/engine/strategies/v2/factory.py` `ARCHETYPE_ENGINE_REGISTRY`
(**29 archetypes registered; 28 not-engine-backed** — verified live 2026-06-15 via `strategy-service/.venv` probe;
supersedes the stale 2026-05-22 "26 registered / 31 stub", which predated `CARRY_STAKED_BASIS_DATED` /
`CARRY_BASIS_DATED_INV` / `ARBITRAGE_CROSS_DOMAIN_EVENT` being registered).

**Legend**: paper-runnable ✅ | paper-shippable ◐ | backtest-only ◯ | stub/placeholder ☐

### CARRY_AND_YIELD family

| Archetype                             | State             | Evidence / owning plan                                                                                                              |
| ------------------------------------- | ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `CARRY_STAKED_BASIS`                  | ◐ paper-shippable | Engine: `carry_and_yield/staked_basis.py`. Dynamic hedge wired (strategy-service@`6431955`). B-015 paper run pending — `pvl-p18a`.  |
| `CARRY_BASIS_DATED`                   | ◯ backtest-only   | Engine: `carry_and_yield/basis_dated.py`. No paper plumbing. Post-cutover.                                                          |
| `CARRY_BASIS_PERP`                    | ◯ backtest-only   | Engine: `carry_and_yield/basis_perp.py`. No paper plumbing. Post-cutover.                                                           |
| `CARRY_RECURSIVE_STAKED`              | ◯ backtest-only   | Engine: `carry_and_yield/recursive_staked.py`. No paper plumbing. Post-cutover.                                                     |
| `CARRY_RECURSIVE_BORROW_LENDING_ONLY` | ◯ backtest-only   | Reuses `CarryRecursiveStakedEngine`. `defi_recursive_borrow_archetypes_2026_05_10.md`. No paper plumbing. Post-cutover.             |
| `CARRY_BASIS_PERP_INV`                | ◯ backtest-only   | Reuses `CarryRecursiveStakedEngine` (renamed from `CARRY_RECURSIVE_BORROW_PERP_HEDGED` 2026-05-18). Post-cutover.                   |
| `CARRY_STAKED_BASIS_DATED`            | ◯ backtest-only   | Engine: `CarryStakedBasisEngine` (registered in `ARCHETYPE_ENGINE_REGISTRY`, verified 2026-06-15). No paper plumbing. Post-cutover. |
| `CARRY_BASIS_DATED_INV`               | ◯ backtest-only   | Engine: `CarryBasisDatedEngine` (registered in `ARCHETYPE_ENGINE_REGISTRY`, verified 2026-06-15). No paper plumbing. Post-cutover.  |
| `YIELD_ROTATION_LENDING`              | ◯ backtest-only   | Engine: `carry_and_yield/rotation_lending.py`. No paper plumbing. Post-cutover.                                                     |
| `YIELD_STAKING_SIMPLE`                | ◯ backtest-only   | Engine: `carry_and_yield/staking_simple.py`. No paper plumbing. Post-cutover.                                                       |

### ARBITRAGE_STRUCTURAL family

| Archetype                          | State             | Evidence / owning plan                                                                                                                             |
| ---------------------------------- | ----------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ARBITRAGE_PRICE_DISPERSION`       | ◐ paper-shippable | Engine: `arbitrage_structural/price_dispersion.py`. `arbitrage_price_dispersion_finalisation_2026_05_09.md`. B-015 paper run pending — `pvl-p18a`. |
| `LIQUIDATION_CAPTURE`              | ◯ backtest-only   | Engine: `arbitrage_structural/liquidation_capture.py`. DeFi-only. Post-cutover.                                                                    |
| `ARBITRAGE_MEV_SANDWICH`           | ☐ stub            | File: `mev/sandwich_theoretical.py` (theoretical; NOT in `ARCHETYPE_ENGINE_REGISTRY`). Post-cutover.                                               |
| `ARBITRAGE_MEV_JIT_LIQUIDITY`      | ◯ backtest-only   | Engine: `mev/jit_liquidity.py`. In factory. MEV simulation requires Tenderly. Post-cutover.                                                        |
| `ARBITRAGE_MEV_BACKRUN`            | ◯ backtest-only   | Engine: `mev/backrun.py`. In factory. Post-cutover.                                                                                                |
| `ARBITRAGE_MEV_LIQUIDATION_BUNDLE` | ◯ backtest-only   | Engine: `mev/liquidation_bundle.py`. In factory. Post-cutover.                                                                                     |
| `ARBITRAGE_CROSS_DOMAIN_EVENT`     | ◯ backtest-only   | Registered in `ARCHETYPE_ENGINE_REGISTRY` (verified 2026-06-15). PREDICTION×SPORTS cross-domain. No paper plumbing. Post-cutover.                  |

### MARKET_MAKING family

| Archetype                            | State           | Evidence / owning plan                                                                         |
| ------------------------------------ | --------------- | ---------------------------------------------------------------------------------------------- |
| `MARKET_MAKING_CONTINUOUS`           | ◯ backtest-only | Legacy engine: `market_making/continuous.py`. In factory. No updated paper path. Post-cutover. |
| `MARKET_MAKING_EVENT_SETTLED`        | ◯ backtest-only | Legacy engine: `market_making/event_settled.py`. In factory. Post-cutover.                     |
| `MARKET_MAKING_PASSIVE_SPREAD`       | ☐ stub          | Not in factory. Phase 9 expansion 2026-04-25. Post-cutover.                                    |
| `MARKET_MAKING_INVENTORY_SKEW`       | ☐ stub          | Not in factory. Post-cutover.                                                                  |
| `MARKET_MAKING_ML_LEAN`              | ☐ stub          | Not in factory. Post-cutover.                                                                  |
| `MARKET_MAKING_QUEUE_MICROSTRUCTURE` | ☐ stub          | Not in factory. Post-cutover.                                                                  |
| `MARKET_MAKING_PREDICTION`           | ☐ stub          | Not in factory. Prediction markets MM. Post-cutover.                                           |

### DEFI_LP family

| Archetype              | State           | Evidence / owning plan                                                        |
| ---------------------- | --------------- | ----------------------------------------------------------------------------- |
| `DEFI_LP_CONCENTRATED` | ◯ backtest-only | Engine: `defi_lp/concentrated.py`. In factory. No paper wiring. Post-cutover. |
| `DEFI_LP_POOL`         | ◯ backtest-only | Engine: `defi_lp/pool.py`. In factory. Post-cutover.                          |
| `DEFI_LP_VAULT`        | ◯ backtest-only | Engine: `defi_lp/vault.py`. In factory. Post-cutover.                         |

### EVENT_DRIVEN family

| Archetype      | State           | Evidence / owning plan                                            |
| -------------- | --------------- | ----------------------------------------------------------------- |
| `EVENT_DRIVEN` | ◯ backtest-only | Engine: `event_driven/event_driven.py`. In factory. Post-cutover. |

### ML_DIRECTIONAL family

| Archetype                      | State           | Evidence / owning plan                                                                           |
| ------------------------------ | --------------- | ------------------------------------------------------------------------------------------------ |
| `ML_DIRECTIONAL_CONTINUOUS`    | ◯ backtest-only | Engine: `ml_directional/continuous.py`. ML model dependency (ml-training-service). Post-cutover. |
| `ML_DIRECTIONAL_EVENT_SETTLED` | ◯ backtest-only | Engine: `ml_directional/event_settled.py`. ML model dependency. Post-cutover.                    |

### RULES_DIRECTIONAL family

| Archetype                         | State           | Evidence / owning plan                                                                    |
| --------------------------------- | --------------- | ----------------------------------------------------------------------------------------- |
| `RULES_DIRECTIONAL_CONTINUOUS`    | ◯ backtest-only | Engine: `rules_directional/continuous.py`. In factory. Post-cutover.                      |
| `RULES_DIRECTIONAL_EVENT_SETTLED` | ◯ backtest-only | Engine: `rules_directional/event_settled.py`. Sports value betting variant. Post-cutover. |

### STAT_ARB_PAIRS family

| Archetype                  | State           | Evidence / owning plan                                                 |
| -------------------------- | --------------- | ---------------------------------------------------------------------- |
| `STAT_ARB_PAIRS_FIXED`     | ◯ backtest-only | Engine: `stat_arb_pairs/pairs_fixed.py`. In factory. Post-cutover.     |
| `STAT_ARB_CROSS_SECTIONAL` | ◯ backtest-only | Engine: `stat_arb_pairs/cross_sectional.py`. In factory. Post-cutover. |

### VOL_TRADING family (18 archetypes, Phase 9 expansion 2026-04-25)

| Archetype                    | State           | Evidence / owning plan                                                                       |
| ---------------------------- | --------------- | -------------------------------------------------------------------------------------------- |
| `VOL_TRADING_OPTIONS`        | ◯ backtest-only | Legacy engine: `vol_trading/options.py`. In factory. Retained for back-compat. Post-cutover. |
| `VOL_ARB_RV_IV`              | ☐ stub          | Not in factory. Phase 9 granular expansion. Post-cutover.                                    |
| `VOL_SPREAD_STRUCTURES`      | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_CARRY`                  | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_OVERLAY_COVERED_CALLS`  | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_OVERLAY_PROTECTIVE_PUT` | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_STRADDLE`               | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_SYNTHETIC_DELTA`        | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_MARKET_MAKING`          | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_ML_LEAN`                | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_0DTE_GAMMA_SCALPING`    | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_0DTE_PIN_RISK`          | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_TERM_STRUCTURE_ARB`     | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_TERM_STRUCTURE_SLOPE`   | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_DISPERSION`             | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_VARIANCE_SWAP`          | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_LEAPS_CONVEXITY`        | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_CROSS_ASSET_SPREAD`     | ☐ stub          | Not in factory. Post-cutover.                                                                |
| `VOL_RATIO_SPREAD`           | ☐ stub          | Not in factory. Post-cutover.                                                                |

### PORTFOLIO family (cross-category, Phase 9 2026-04-25)

| Archetype                     | State  | Evidence / owning plan                        |
| ----------------------------- | ------ | --------------------------------------------- |
| `PORTFOLIO_MULTI_STRATEGY`    | ☐ stub | Not in factory. Cross-category. Post-cutover. |
| `PORTFOLIO_RISK_PARITY`       | ☐ stub | Not in factory. Post-cutover.                 |
| `PORTFOLIO_FACTOR_ALLOCATION` | ☐ stub | Not in factory. Post-cutover.                 |
| `PORTFOLIO_TACTICAL_OVERLAY`  | ☐ stub | Not in factory. Post-cutover.                 |

### Summary counts (2026-06-15)

| State              | Count  | Notes                                                                                              |
| ------------------ | ------ | -------------------------------------------------------------------------------------------------- |
| ✅ paper-runnable  | 0      | No archetype has completed ≥3-day paper run yet                                                    |
| ◐ paper-shippable  | 2      | CARRY_STAKED_BASIS + ARBITRAGE_PRICE_DISPERSION (B-015 pending)                                    |
| ◯ backtest-only    | 27     | In `ARCHETYPE_ENGINE_REGISTRY`; paper plumbing not yet wired (+3 since 2026-05-22, now registered) |
| ☐ stub/placeholder | 28     | Not in factory; Phase 9 expansion names or theoretical — the **ratified `not_available`** set      |
| **Total**          | **57** | 2026-06-15 live-probe reconcile: 29 registered / 28 not-engine-backed (was 26/31 on 2026-05-22)    |

### Phase C ratification — engineless archetypes + unbuildable venues stay honestly `not_available` (2026-06-15)

Per `plans/active/engine_findings_remediation_2026_06_15.md` Phase C (operator BUILD-SUBSET / VENUE-TOKEN-ADD left empty
→ RATIFY-ONLY): the **28 not-engine-backed archetypes** (the `☐ stub/placeholder` rows above) and the **11 unbuildable
slot-venues** are ratified to remain honestly `not_available` in the capability verdict matrix — post-MVP, no engine /
no venue-token planned. This is the intended DONE state, not a gap: building an empty engine or adding an unbacked venue
token would re-create the over-claim Phase B's F47/F48 surface fix removed.

- **Verdict-matrix verdicts (already honest, unchanged by ratification — RATIFY is documentation-only):**
  `not_registered(no_v2_engine)` for the 22 archetypes with leg structure but no engine;
  `not_registered(missing_registry)` for the 6 with no leg structure (the 4 `PORTFOLIO_*`, `VOL_0DTE_PIN_RISK`,
  `ARBITRAGE_MEV_SANDWICH`); `blocked(unbuildable_slot_venue)` for the 11 venues whose alnum-folded slot-token ∉
  `architecture_v2.venue_tokens` `KNOWN_VENUE_TOKENS`.
- **Counts (deterministic, committed `unified-api-contracts/openapi/capability-verdict-matrix.json`):** total 21600 /
  available 12977 / blocked 8175 / not_registered 448 (96 `missing_registry` + 352 `no_v2_engine`); 186 of the blocked
  cells are `unbuildable_slot_venue`.
- **Ratified venues (11):** `gmx_v2` (66 cells), `betfair_direct` (48), `smarkets_direct` (36), `pancakeswap_v3` (10),
  `sushiswap_v3` (10), `jupiter` (6), `balancer_v2` (2), `balancer_v3` (2), `matchbook_direct` (2), `sommelier` (2),
  `trader_joe` (2) — alt DEXes / sports betting exchanges / a yield-vault protocol, none wired end-to-end (adapter +
  collateral + capability); the live MVP DeFi venues are tokenised + supported.
- A future build/support effort for any of these is a **new plan item**, never a Phase-C gap.

## Solana-specific addendum

`carry_staked_basis` has Solana legs (jitoSOL / mSOL / bSOL); per
[`../../../05-infrastructure/per-venue-paper-policy.md`](../../../05-infrastructure/per-venue-paper-policy.md), Solana
paper-mode uses devnet (or localnet / surfnet) — picked by `pvl-p20c`. `carry_staked_basis` graduating to
`paper-runnable` requires the Solana paper wiring to ship.

## Composes with

- [`../../../04-architecture/operational-modes.md`](../../../04-architecture/operational-modes.md) — the canonical mode
  SSOT.
- [`../../../04-architecture/paper-vs-live-execution-seam.md`](../../../04-architecture/paper-vs-live-execution-seam.md)
  — execution-only seam principle.
- [`../../../05-infrastructure/per-venue-paper-policy.md`](../../../05-infrastructure/per-venue-paper-policy.md) —
  `paper_target_registry`.
- [`pnl-attribution.md`](pnl-attribution.md) — P&L decomposition per source.
- [`../../../14-customer-journeys/dart/mode-toggle.md`](../../../14-customer-journeys/dart/mode-toggle.md) — DART
  visualization of paper-runnable archetypes.
