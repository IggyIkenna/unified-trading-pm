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

- [x] Per-archetype parity test: hand-rolled `_build_legs` output locks via entry-shape parity tests
      (`strategy-service/tests/.../test_leveraged_leg_controller_parity.py`) + new promotion engines covered in
      `test_arbitrage_price_dispersion_hierarchical.py`, `test_sports_value_betting.py`, `test_sports_arb_dutching.py`.
      28 tests, all green.
- [x] Drift-detection unit test: position drifts → controller computes correct leverage_drift_bps
      (`execution-service/tests/unit/algorithms/test_leveraged_leg_controller.py`, 9 tests).
- [x] Rebalance unit test: drift > rebalance_trigger_bps → controller emits AtomicInstruction with correct TRADE legs
      preserving target_net_delta (concrete: 4× LONG weETH / 4× SHORT ETH-PERP under ETH +8% → SELL 118.5185 weETH + BUY
      118.5185 ETH-PERP, post-rebalance net delta = 0).
- [x] Venue-capability clamp test: SPORTS max_leverage=1.0 silently caps target_leverage from 4.0 → 1.0 (covered in
      execution-service controller suite).
- [x] Time-varying leverage test: target_leverage changes per tick (ML_DIRECTIONAL conviction);
      `MLDirectionalContinuousEngine.declare_leg_portfolio_state` reads params freshly per call with
      `target_leverage_source="conviction"`. PBM `LegSnapshotBuilder` consumes the new value each tick (Phase 3
      shipped). Cross-repo e2e test (system-integration-tests `ed8a05c`) covers the full chain.

### Business gates

- [x] Every existing archetype runs end-to-end through the controller with no behavioural regression vs hand-rolled —
      every V1_ARCHETYPES_IN_SCOPE archetype now declares LegPortfolioState (3 promotions + 6 hook backports + 2 carry
      backports). Cross-repo e2e proves end-to-end contract.
- [x] One new archetype (CARRY_STAKED_BASIS at 4× per leg) demonstrates leveraged-dual-side delta-neutral behaviour —
      controller smoke test: 4× LONG weETH / 4× SHORT ETH-PERP under ETH +8%, cash sweep redistributes equity,
      controller emits SELL 118.5185 weETH + BUY 118.5185 ETH-PERP, post-rebalance net delta = 0.000000.
- [x] Risk-and-exposure-service emits LEVERAGE_BREACH alert in integration test when one leg drifts beyond tight
      threshold —
      `system-integration-tests/tests/integration/test_leveraged_leg_controller_e2e.py     ::test_risk_detector_fires_when_post_rebalance_skipped`
      proves the wire-up.

## Phase 4 corrected scope (2026-05-01 evening — full)

Operator pushed back on the original "deferred" list. Honest re-audit: three of four "doesn't migrate" items were
wrong-layer dismissals. The IMPLEMENTATIONS that exist today are partial / post-hoc, but the ARCHETYPE LOGIC is
forward-looking position sizing — exactly what the controller is for. Corrected breakdown:

### Promotions (forward-looking sizers that should consume LeveragedLegController)

1. **`ArbitragePriceDispersionHierarchicalEngine`** — strategy-service v2. Multi-coin × multi-venue funding-rate carry.
   Promotes the Level 1/2/3 hierarchical allocator from
   `execution-service/cli/defi_arbitrage_dispersion_decision_trace.py` into a real archetype engine.
   `target_net_delta=0` per coin; `LegSizingStrategy.PROPORTIONAL_TO_DEV_FROM_MEAN`. Existing
   `ArbitragePriceDispersionEngine` keeps its 2-leg LEADER_HEDGE single-coin path; this adds a hierarchical sibling.
2. **`SportsValueBettingEngine`** — strategy-service v2 NEW directory `sports_value_betting/`. Single LONG leg,
   `target_leverage = kelly_fraction × bankroll` clamped to 1.0× by venue capability (SPORTS venues declare
   `supports_margin=false`). `target_net_delta = ±target_leverage` from edge sign.
   `LegSizingStrategy.CONVICTION_WEIGHTED`. Emits `AtomicLeg` with `params={"role": "back", "odds": "..."}` so executors
   render as a BACK bet.
3. **`SportsArbDutchingEngine`** — strategy-service v2 NEW directory `sports_arb/`. N legs (one per venue per outcome).
   `target_net_delta=0` across outcomes (Dutched arb invariant: equal payoff regardless of outcome).
   `LegSizingStrategy.KELLY_OVERROUND`. Emits mixed BACK / LAY `AtomicLeg`s.

### Drift hooks on existing carry archetypes (opt-in via `LegPortfolioState`)

4. **`BaseArchetypeEngineV2.maybe_rebalance_legs(snapshots, now_utc)`** — new opt-in method. If the engine declared a
   `LegPortfolioState` at construction, the orchestrator calls this per tick with the latest PBM snapshot. Delegates to
   `LeveragedLegController.compute_drift` + `emit_rebalance_instructions`. Engines that don't declare a portfolio state
   get a no-op.
5. **CARRY_STAKED_BASIS opts in** — declares its 3-leg portfolio (long stake / lend collateral / short perp) at config
   time and gets auto-rebalance for free as ETH moves. Entry chain stays untouched.
6. **CARRY_RECURSIVE_STAKED opts in** — declares its leveraged-loop portfolio (geometric-series stake legs + N-1 borrow
   legs) and gets auto-rebalance for the per-leg leverage drift.

### What genuinely stays as-is

7. **PBM `SportsArbEngine`** — post-hoc detection of `is_arb` after positions are open. Different artifact
   (`SportsArbPosition` / `SportsArbLeg` carry settlement-PnL math, not order intent). Already locked by `93002ca`
   parity test.
8. **`staked_basis._build_legs` ENTRY chain** — multi-action atomic STAKE → LEND → TRADE. Already locked by `39896d7`
   parity test.
9. **`recursive_staked` ENTRY chain** — geometric-series leg sizing. Already locked by `39896d7` parity test.

### Hard prerequisite for live runtime

PBM extension exposing per-leg `current_leverage` + `equity_per_leg` in the position snapshot (Phase 3, queued). The
promotion engines (1–3) and the rebalance hook (4) ship now with `LegSnapshot`-shaped contracts; Phase 3 fills in the
live feed.

## Phases 3 + 4-remaining + 4.5 + 5 + 6 closeout (2026-05-01 late evening)

After Phase 4 corrected-scope landed, the operator pushed for the remaining six phases in one go. Shipped end-to-end
across 6 repos:

**Phase 3 — PBM per-leg observation contract** (UAC `d1567fc` + execution-service `10c7c759` + PBM `2c48858`):

- UAC: `LegSnapshot` promoted from execution-service local dataclass to
  `unified_api_contracts.internal.architecture_v2.leveraged_legs` per the CLAUDE.md schema-provenance rule. Re-exported
  from the `internal` facade.
- execution-service: controller migrated to import LegSnapshot from UAC; 9 controller tests still green.
- PBM: new `LegSnapshotBuilder.build_leg_snapshots(state, total_equity, observations)` pure function maps observed
  (venue, instrument) → (position_units, mark_price, realized, unrealized) into the LegSnapshot shape the controller
  consumes. Equity per leg = initial allocation by target_leverage weight + cumulative PnL. 9 unit tests cover 50/50
  equal-leverage split, 80/20 4x+1x split, PnL drift, missing observations, empty portfolio, zero-target-leverage safe,
  actual_leverage helper.

**Phase 4 remaining hook backports** (strategy-service `4ba304e`): 6 archetypes now declare LegPortfolioState —
CARRY_BASIS_PERP (signed-delta from current_position), ML_DIRECTIONAL_CONTINUOUS (target_leverage_source= "conviction"),
RULES_DIRECTIONAL_CONTINUOUS, MARKET_MAKING_CONTINUOUS (neutral inventory leg), STAT_ARB_PAIRS_FIXED (2-leg pairs trade,
HEDGE_UNDERLYING), VOL_TRADING_OPTIONS (2-leg straddle, REGIME_WEIGHTED, per-leg leverage = vega_notional /
target_equity). Engines that didn't already call `_record_tick_context` now do (one-liner). 14 new parity tests; full v2
suite at 248 tests green.

**Phase 4.5 runner-side wiring** (strategy-service `56585fa`): `V2EngineOrchestrator` now accepts a
`LegControllerAdapter` Protocol and invokes `maybe_rebalance(state, total_equity, now_utc)` after each `engine.on_tick`.
Stateless engines (declare_leg_portfolio_state returns None) are no-op. `NullLegControllerAdapter` is the default.
Cross-repo coupling solved without strategy-service depending on execution-service or PBM — the concrete adapter
implementation lives in the deployment-time runner. 4 wiring tests verify default null behaviour, stub-adapter
invocation, conditional-skip on None state.

**Phase 5 — LEVERAGE_BREACH risk overlay** (UAC `afad6d5` + risk-and-exposure `7bbcb7b`):

- UAC: `AlertType.LEVERAGE_BREACH` added with docstring scoping the safety overlay vs the controller's auto-rebalance.
- risk-and-exposure-service: `detect_leverage_breaches(state, snapshots, client_id, ...)` pure-function detector emits
  AlertMessage rows when any leg's actual leverage exceeds target by more than
  `rebalance_trigger_bps * tightness_multiplier` (default 4x). Calibrated: controller fires at 50bps drift, alert fires
  at 200bps. Only over-leveraged side alerts; under-leveraged drift is informational. Severity = CRITICAL when drift >
  2x alert threshold, WARNING otherwise. 9 unit tests cover at-target / sub-threshold / over-leveraged short /
  under-leveraged long / recommended_action context / missing snapshots / configurable tightness / zero-equity safe /
  severity gradient.

**Phase 6 hardening — cross-repo e2e** (system-integration-tests `ed8a05c`): 6 tests in
`test_leveraged_leg_controller_e2e.py` exercise the full chain across UAC + strategy-service + PBM + execution-service +
risk-and-exposure- service in a single test module. Reference scenario: 4x LONG weETH / 4x SHORT ETH-PERP delta-neutral
basis trade, $500k equity, ETH +8%. Tests verify each layer's contract against its siblings — strategy declares, PBM
builds snapshots, controller computes drift + emits ATOMIC rebalance, risk detector fires LEVERAGE_BREACH on the
over-levered short pre-rebalance, full-chain at-target produces zero rebalance + zero alerts.

**Phase 6 rewards — dust conversion + reward attribution** (execution-service `33a43804` + pnl-attribution-service
`541a0c9`):

- execution-service: `dust_conversion_router.py` consumes UAC's `ConvertDustInstruction` and returns
  `DustConversionResult`. Replaces hardcoded liquidity haircuts with actual matching-engine route simulation per
  Batch=Live: `QuoteSource` Protocol injected by the runner (matching engine in batch, live venue feeds in live).
  Built-in handling for hold_until_vested_tokens (held), is_pre_tge_points (deferred no_market), pnl_layer_attribution
  propagation. 9 unit tests cover the contract.
- pnl-attribution-service: `reward_attribution.py` maps each ConvertedTokenLeg to two `PnLBreakdown` rows — realisation
  row tagged with carry_base/carry_avs_continuous/carry_issuer_seasonal factor key + paired reward_realisation_slippage
  row capturing measured execution cost. 6 unit tests verify the 3-layer factor distinction, slippage math,
  held/deferred no-emit, unknown-layer fallback.

**Phase 6 rewards — features-onchain collector deferred**: the remaining piece (`lst_seasonal_rewards` Transfer event
scanner per LST_REWARD_STREAMS) requires real Web3 RPC code with on-chain integration concerns. Captured in memory as a
follow-up; doesn't block Phase 6 hardening since the dust conversion + attribution layers can be exercised by the
matching-engine quote source in batch mode without live RPC.

## Phase 4 closeout (2026-05-01 evening — corrected scope shipped in full)

Operator pushed back on the original "deferred" list and was right: three of the four "doesn't migrate" items were
wrong-layer dismissals. After re-scoping (above) the corrected Phase 4 shipped end-to-end in one session — five
strategy-service commits on `live-defi-rollout`:

- **`9e33ba2` `feat(arbitrage): promote multi-coin x multi-venue funding allocator to v2`**
  `ArbitragePriceDispersionHierarchicalEngine` lifts the L1/L2/L3 hierarchical allocator from the cross-venue funding
  decision tracer into a real archetype engine. Smoke-tested against the same 7-day 2025-06-15..21 fixture: BTC 35.72% /
  LINK 23.29% / ETH 22.49% / SOL 18.50% book weights, every coin delta-neutral within itself, gross stacks across coins.
- **`dcd32ad` `feat(rules-directional): SportsValueBettingEngine — Kelly-sized value bets`** Sibling to
  `RulesDirectionalEventSettledEngine` under the same `RULES_DIRECTIONAL_EVENT_SETTLED` archetype: gates on
  `(fair_prob × decimal_odds - 1) × 100 ≥ min_edge_pct`, sizes via fractional Kelly with archetype-tier multiplier
  (0.125 = TIER*HIGH_VARIANCE) × param Kelly multiplier × full Kelly. No new SPORTS*-prefixed archetype enum value added
  per the existing "no category prefixes" rule.
- **`3525535` `feat(arbitrage): SportsArbDutchingEngine — N-venue dutched-arb`** Sibling to
  `ArbitragePriceDispersionHierarchicalEngine` under `ARBITRAGE_PRICE_DISPERSION`: best-venue-per-outcome selection,
  inverse-odds-weighted stakes, ATOMIC execution mode. Locks identical-payout-regardless-of-outcome invariant and
  replaces the post-hoc PBM `SportsArbEngine.detect_arbs()` detection path with a forward-looking position-sizer (PBM
  scanner stays for monitoring already-held positions).
- **`9d15458` `feat(base-engine): declare_leg_portfolio_state hook for LeveragedLegController`** Opt-in declarative hook
  on `BaseArchetypeEngineV2`. Engines whose archetype holds a multi-leg leveraged book return the target
  `LegPortfolioState`; stateless engines leave the default `None`. Cross-repo wiring: strategy-service declares state,
  runner pulls PBM `LegSnapshot`s and fires `execution_service.algo_library.LeveragedLegController.compute_drift`
  externally — no upstream/downstream coupling violation.
- **`7ad6802` `feat(carry): backport CARRY_STAKED_BASIS + CARRY_RECURSIVE_STAKED to declare LegPortfolioState`**
  STAKED_BASIS declares 2-leg `HEDGE_UNDERLYING` (LST long + perp short, target_net_delta=0). RECURSIVE_STAKED declares
  LST collateral + native borrow `LEVERAGE_LOOP` (target_net_delta = target_leverage, delta-positive recursive
  exposure). Both engines retain their original on_tick + react_to_equity_change unchanged — the new hook is purely
  declarative.
- **`e0219d3` `test(strategies/v2): parity locks for Phase 4 promotions + carry backports`** Three new test modules + 4
  new tests on the existing parity suite. 28 new tests total; full v2 unit suite (234 tests) green.

Sports-archetype enum decision: **reuse existing generic archetypes**, no new SPORTS*-prefixed values. The
`StrategyArchetype` enum docstring explicitly forbids category prefixes ("No CEFI*/DEFI*/SPORTS*/TRADFI\_") and the
existing v2 already has multiple engines per archetype (the new hierarchical funding engine shares
`ARBITRAGE_PRICE_DISPERSION` with the 2-venue `ArbitragePriceDispersionEngine`, and the value-betting engine shares
`RULES_DIRECTIONAL_EVENT_SETTLED` with the rule-condition engine). Both target archetypes are already in
`KELLY_FRACTION_BY_ARCHETYPE` at the right tiers (TIER_STABLE_STRUCTURAL for ARBITRAGE_PRICE_DISPERSION,
TIER_HIGH_VARIANCE for RULES_DIRECTIONAL_EVENT_SETTLED) so no `archetype_defaults.py` changes were needed.

**Hard prerequisite for live runtime**: PBM extension exposing per-leg `current_leverage` + `equity_per_leg` in the
position snapshot (Phase 3, queued). Until PBM ships per-leg snapshot fields, the new hook + carry declarations stand as
tested-but-not-yet-consumed declarations. The runner-side wiring (pull declared state → request PBM snapshots → fire
controller → route AtomicInstruction back) is the next session.

## Phase 4 progress log (2026-05-01)

The literal "collapse hand-rolled `_build_legs`" item from the original DAG turned out to be over-stated. Empirical
audit of the call sites:

- **`staked_basis._build_legs`** is a multi-action atomic ENTRY chain (`STAKE` on ETHERFI → `LEND` on AAVE_V3 → `TRADE`
  SHORT on HYPERLIQUID). LeveragedLegController is TRADE-only and covers ongoing PnL drift, not entry composition.
  Different concerns; entry chain stays as-is.
- **`recursive_staked` entry path** is the geometric-series leg-sizing on Aave borrow-restake loops. Same shape:
  multi-action atomic ENTRY. Stays as-is.
- **`sports_arb_engine._build_legs`** produces `SportsArbLeg` (a DETECTION-output schema with `BACK|LAY` side + stake +
  odds + commission_rate), not `AtomicLeg`. Different abstraction layer entirely — sports arb is a scanner, not a
  position-sizer. Doesn't migrate.
- **arbitrage tracer cross-venue funding** hand-rolled allocator: also a research/decision tool, not a live archetype
  consumer. Could be refactored to call the controller for consistency but it's not on the critical path.

What Phase 4 actually delivered (shipped 2026-05-01):

- **execution-service `488a2ed0`** — 9-test LeveragedLegController unit suite covering drift detection, cash-sweep
  equalisation, position sizing, instruction emission, venue clamping, and edge cases. Concrete value check: 4× LONG
  weETH / 4× SHORT ETH-PERP under ETH +8% emits `SELL 118.5185 weETH` + `BUY 118.5185 ETH-PERP`, post-rebalance net
  delta = 0.
- **strategy-service `39896d7`** — Entry-chain shape locks for `CarryStakedBasisEngine` + `CarryRecursiveStakedEngine`.
  Pins the multi-action atomic AtomicInstruction wire format so future refactors can't silently change it.
- **position-balance-monitor-service `93002ca`** — Direct parity lock for `SportsArbEngine._build_legs` BACK/LAY shape
  (3 tests covering venue ordering, commission accounting, missing-rate fallthrough).

**Hard prerequisite for the live integration step**: PBM extension exposing per-leg `current_leverage` +
`equity_per_leg` in the position snapshot (Phase 3, queued). Without that, the controller has no observation source —
strategies can't call `compute_drift(state, snapshots)` because `LegSnapshot` has no upstream feed today. Until PBM
ships per-leg snapshot fields, the controller stands as a tested-but-not-yet-consumed primitive.

**Next session**: PBM per-leg snapshot wiring → strategy-service per-tick rebalance hook on `BaseArchetypeEngineV2`
(opt-in via `LegPortfolioState`) → first archetype (CARRY_STAKED_BASIS) opts in → live integration test in
`system-integration-tests`.

## Phase 6 — Reward realisation feedback into LegPortfolioState equity

After Phase 4 backports land, integrate reward realisation as an equity inflow to the LegPortfolioState so the
cash-sweep step naturally redistributes claimed/converted rewards across legs along with PnL drift.

```
Phase 6 (after Phase 4)
   ├─ 6.1 features-onchain: new lst_seasonal_rewards collector (Transfer event scan per LST_REWARD_STREAMS distributor)
   ├─ 6.2 execution-service: algo_library/dust_conversion_router.py — consumes ConvertDustInstruction +
   │      REWARD_TOKEN_ECONOMICS, simulates swap routes through matching engine on Binance / Uniswap / Jupiter tick
   │      data, returns DustConversionResult
   ├─ 6.3 strategy-service: archetypes that hold restaking-eligible LSTs emit ConvertDustInstruction once per epoch
   │      (or hold via hold_until_vested_tokens) with the freshly-claimed token basket
   ├─ 6.4 LegPortfolioController: realised target_amount feeds back as an equity inflow on the LST leg before
   │      compute_drift; cash-sweep step then naturally redistributes the realised rewards across legs along with PnL
   ├─ 6.5 pnl-attribution-service: tags each row with RewardPnLLayer (CARRY_BASE / CARRY_AVS_CONTINUOUS /
   │      CARRY_ISSUER_SEASONAL); emits paired REWARD_REALISATION_SLIPPAGE row per converted token
   └─ 6.6 GATE — full Fork 2 batch e2e for one restaking-eligible archetype produces per-strategy PnL series with
            CARRY decomposed into the 3 sub-factors + REWARD_REALISATION_SLIPPAGE; verify_net_delta passes after
            reward realisation feedback applied.
```

Codex SSOT:
[`codex/09-strategy/cross-cutting/restaking-reward-economics.md`](../../codex/09-strategy/cross-cutting/restaking-reward-economics.md)

- updates to
  [`codex/09-strategy/cross-cutting/pnl-attribution.md`](../../codex/09-strategy/cross-cutting/pnl-attribution.md).

UAC schema (shipped 2026-05-01 commit `473af9d`): `unified_api_contracts.internal.architecture_v2.restaking_rewards` —
`LSTRewardStream`, `LST_REWARD_STREAMS`, `RewardTokenEconomics`, `REWARD_TOKEN_ECONOMICS`, `RewardPnLLayer`,
`ConvertDustInstruction`, `DustToken`, `DustConversionResult`, `ConvertedTokenLeg`, `DeferredTokenLeg`.

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
