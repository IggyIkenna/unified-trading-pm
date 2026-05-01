---
locked_by: live-defi-rollout
locked_since: 2026-05-01
plan_type: architecture
asset_group: ALL
owner: ikenna
created: 2026-05-01
---

# LeveragedLegController — generic delta-targeted, leveraged, multi-leg portfolio primitive

## Motivation

Every archetype currently rolls its own leg-builder + rebalance loop:

- `strategy-service/.../carry_and_yield/staked_basis.py:132` `_build_legs` — bespoke for stake+perp
- `strategy-service/.../carry_and_yield/recursive_staked.py` — bespoke for LST + Aave borrow loops
- `position-balance-monitor-service/.../sports_arb_engine.py:97` `_build_legs` — bespoke for sports outcome legs
- `execution-service/cli/defi_arbitrage_dispersion_decision_trace.py` — bespoke 50/50 short-rich/long-cheap split with
  `|deviation_from_mean|` weighting
- ML_DIRECTIONAL / RULES_DIRECTIONAL / MEAN_REVERSION / MARKET_MAKING / VOL_TRADING — each archetype's `on_tick`
  reimplements its own position sizing + rebalance logic

Every one of those solves the same shape of problem: _"given a venue universe with current rates/prices/positions and a
(target_leverage_per_leg, target_net_delta) tuple, produce the leg adjustments that maintain those targets as PnL
accrues."_

This violates CLAUDE.md "System-First Architecture / No Ad-Hoc Solutions". The fix is a **single generic controller**
every archetype consumes.

## Scope

A strategy-agnostic, asset_group-agnostic primitive that:

1. **Holds N legs** with per-leg `(side, target_leverage, venue, instrument)`
2. **Maintains target net delta** across legs (`0` = neutral, `1` = full long, `L−1` = recursive-leverage exposure,
   etc.)
3. **Auto-rebalances cash between legs** as PnL accrues to keep each leg at its target leverage
4. **Accepts time-varying `target_leverage`** (strategies publish `target_leverage_now` per tick; controller tracks it)
5. **Respects venue capability declarations** (`supports_margin`, `max_leverage`, `margin_mode`) from
   instruments-service — clamps target_leverage to venue ceilings without strategy code knowing or caring
6. **Emits rebalance instructions** through the existing AtomicInstruction pipeline — no new wire format
7. **Risk-service hookable** — leverage drift exposed as a metric so risk-and-exposure-service can emit
   `LEVERAGE_BREACH` alerts independently of the rebalance trigger

## Universal applicability across UAC StrategyArchetype

| Archetype family                                      | target_leverage source                         | target_net_delta                           | Notes                                                                                        |
| ----------------------------------------------------- | ---------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------------------------------------- |
| ML_DIRECTIONAL_CONTINUOUS                             | `base_lev × conviction_pct`                    | `±target_leverage` (from signal direction) | 1 leg, time-varying with prediction confidence                                               |
| RULES_DIRECTIONAL_CONTINUOUS                          | `base_lev × rule_strength`                     | `±target_leverage`                         | momentum/MACD/breakout                                                                       |
| MEAN_REVERSION / STAT_ARB_PAIRS                       | per-leg constant                               | `0` modulated by `hedge_ratio`             | 2 legs, both leveraged independently                                                         |
| MARKET_MAKING_CONTINUOUS / EVENT_SETTLED              | inventory leg leverage                         | `0` (skew bid/ask to mean-revert)          | inventory leg leveraged; quote engine handles bid/ask                                        |
| VOL_TRADING_OPTIONS                                   | `base_lev × regime_multiplier(realized_vol)`   | `0` for long-vol/short-vol structures      | each option leg has own leverage                                                             |
| EVENT_DRIVEN                                          | `base_lev × proximity_to_event(time_to_event)` | from signal                                | ramp into/out of events                                                                      |
| ARBITRAGE_PRICE_DISPERSION (cross-chain, cross-venue) | constant per leg                               | `0`                                        | N venue legs, all leveraged                                                                  |
| LIQUIDATION_CAPTURE                                   | `1.0` (single liquidation tx)                  | `1` (capture profit)                       | 1-shot, atomic                                                                               |
| CARRY_BASIS_PERP (single venue)                       | `base_lev`                                     | `1` (naked short to harvest funding)       | 1 leg, leverage on perp                                                                      |
| CARRY_STAKED_BASIS                                    | per-leg constant (often equal LONG/SHORT)      | `0`                                        | LST stake + perp short, leveraged each side                                                  |
| CARRY_RECURSIVE_STAKED                                | `base_lev × carry_quality(net_apy)`            | `target_leverage − 1` (delta-positive)     | LST + Aave borrow loop                                                                       |
| YIELD_ROTATION_LENDING                                | `1.0` (no leverage)                            | `1` (full long supply)                     | single supply leg                                                                            |
| REBASING_YIELD                                        | `1.0`                                          | `1`                                        | single hold leg                                                                              |
| SPORTS_VALUE_BETTING / SPORTS_ARB                     | Kelly-fraction × bankroll                      | per-outcome                                | venue declares `supports_margin=false`, max_leverage=1.0 — controller clamps; same code path |
| PORTFOLIO_RISK_PARITY / PORTFOLIO_FACTOR_ALLOCATION   | meta-allocator on top                          | aggregated                                 | each underlying instance has its own per-leg leverage                                        |

Every archetype's `on_tick` collapses to:

```python
def on_tick(self, ..., features) -> list[StrategyInstructionEnvelope]:
    target_leverage = self._compute_leverage(features)   # archetype-specific math
    target_delta    = self._compute_delta(features)       # archetype-specific math
    return self._leg_controller.update(
        target_leverage=target_leverage,
        target_net_delta=target_delta,
    )  # generic — emits rebalance / open / close instructions
```

All rebalance loops, cash sweeps, drift detection, leg sizing — gone. One implementation, used everywhere.

## Phased execution DAG

```
Phase 1 — UAC schema (PARALLEL within Phase 1)
   ├─ 1.1 internal/architecture_v2/leveraged_legs.py — LeveragedLeg, LegPortfolioState, LegDrift, CashSweepPolicy, LegSizingStrategy enums
   ├─ 1.2 Promote target_leverage from per-archetype configs to StrategyInstanceDefinition
   ├─ 1.3 Re-export from internal __init__.py
   └─ 1.4 GATE — UAC quality-gates.sh passes; all 4 fields importable from unified_api_contracts.internal

Phase 2 — execution-service controller (after Phase 1)
   ├─ 2.1 algo_library/leveraged_leg_controller.py — drift compute (per-leg actual_leverage vs target_leverage); rebalance emission (TRANSFER + TRADE legs through AtomicInstruction)
   ├─ 2.2 Venue-capability validator — clamps target_leverage to venue.max_leverage; SPORTS venues declare max_leverage=1.0 → silently caps
   ├─ 2.3 Cash sweep policies — ALWAYS_SWEEP_TO_LOSER / PERIODIC / THRESHOLD; rebalance_trigger_bps default 50 (0.50× drift from target)
   ├─ 2.4 Unit tests — per-archetype shape on parity with hand-rolled _build_legs (zero behavioural drift on identical inputs)
   └─ 2.5 GATE — execution-service quality-gates.sh passes; all 8 v2 archetypes have parity tests

Phase 3 — PBM extension (after Phase 1, parallel with Phase 2)
   ├─ 3.1 position_snapshot.parquet exposes per-leg current_leverage + equity_per_leg fields
   ├─ 3.2 PBM emits PositionSnapshotMessage with leg-level breakdown
   └─ 3.3 GATE — strategy-service can read per-leg leverage from PBM snapshot

Phase 4 — Strategy backports (PARALLEL within Phase 4 after Phases 2+3)
   ├─ 4.1 strategy-service/.../carry_and_yield/staked_basis.py — replace _build_legs with LegController.update
   ├─ 4.2 strategy-service/.../carry_and_yield/recursive_staked.py — replace _build_legs
   ├─ 4.3 strategy-service/.../carry_and_yield/basis_perp.py — replace
   ├─ 4.4 strategy-service/.../arbitrage_structural/price_dispersion.py — cross-venue allocator collapses to controller call
   ├─ 4.5 strategy-service/.../ml_directional/continuous.py — leverage scales with conviction_pct
   ├─ 4.6 strategy-service/.../rules_directional/continuous.py — leverage scales with rule_strength
   ├─ 4.7 strategy-service/.../mean_reversion/event_settled.py — 2-leg pairs trade
   ├─ 4.8 strategy-service/.../market_making/* — inventory leg leveraged
   ├─ 4.9 strategy-service/.../vol_trading/options.py — per-option-leg leverage
   ├─ 4.10 position-balance-monitor-service/.../sports_arb_engine.py — Kelly stakes via controller
   └─ 4.11 GATE — every archetype's parity test still green; quality-gates.sh on every modified repo

Phase 5 — Risk-and-exposure integration (after Phase 4)
   ├─ 5.1 risk-and-exposure-service subscribes to LegPortfolioState updates
   ├─ 5.2 Emit LEVERAGE_BREACH alert when leg drift exceeds tighter threshold than rebalance trigger
   └─ 5.3 GATE — risk-and-exposure quality-gates.sh passes

Phase 6 — Hardening (final)
   ├─ 6.1 quickmerge --agent on every modified repo (UAC, execution-service, position-balance-monitor-service, strategy-service, risk-and-exposure-service)
   ├─ 6.2 system-integration-test: full Fork 2 batch e2e with each archetype hitting LegController.update at least once over a 7-day window
   └─ 6.3 GATE — workspace-wide QG green; per-archetype parity tests green; integration test produces non-zero PnL with realised leverage drift + rebalance traces
```

## Success criteria

### Code gates

- [ ] UAC `quality-gates.sh` passes
- [ ] execution-service `quality-gates.sh` passes
- [ ] strategy-service `quality-gates.sh` passes
- [ ] position-balance-monitor-service `quality-gates.sh` passes
- [ ] risk-and-exposure-service `quality-gates.sh` passes
- [ ] basedpyright clean across all modified repos

### Test gates

- [ ] Per-archetype parity test: hand-rolled `_build_legs` output == `LegController.update` output on identical input
      (zero behavioural drift)
- [ ] Drift-detection unit test: position drifts X% → controller computes correct leverage_drift_bps
- [ ] Rebalance unit test: given drift > rebalance_trigger_bps, controller emits AtomicInstruction with correct
      TRANSFER + TRADE legs to restore target leverage on each leg AND target net delta
- [ ] Venue-capability clamp test: SPORTS venue declares max_leverage=1.0; controller clamps target_leverage from 4.0 →
      1.0 without erroring
- [ ] Time-varying leverage test: target_leverage changes per tick (ML_DIRECTIONAL conviction); controller adjusts
      position to track new target

### Business gates

- [ ] Every existing archetype runs end-to-end through the controller with no behavioural regression vs hand-rolled
- [ ] One new archetype (CARRY_STAKED_BASIS at 4× per leg) demonstrates leveraged-dual-side delta-neutral behaviour:
      gross 8× exposure, target net delta 0, controller cash-sweeps as PnL accrues
- [ ] Risk-and-exposure-service emits LEVERAGE_BREACH alert in integration test when one leg drifts beyond tight
      threshold

## Out of scope

- Greeks-aware delta management for OPTIONS (gamma/vega controller is a v2; v1 treats option legs as size-only)
- Cross-strategy leverage netting (each strategy's controller is independent; netting at the client level is for
  portfolio_allocator)
- Live cash-sweep execution latency optimisation (v1 is once-per-rebalance-trigger; high-freq sweep is a v2)
- Per-asset reserve_factor refinement in Aave APY synthesis (cosmetic — already documented as a follow-up in
  features-onchain `d586215`)

## Notes for resumption across sessions

- Active feature branch: `live-defi-rollout`
- Each phase commits + pushes to its repo's `live-defi-rollout` before next phase begins
- Per CLAUDE.md PM doc-only fast-path, this plan PRs to main directly when committed
- Backports in Phase 4 are PARALLEL — can be split across multiple agents if needed
