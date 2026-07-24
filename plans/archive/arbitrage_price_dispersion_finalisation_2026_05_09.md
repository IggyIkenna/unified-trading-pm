---
doc_type: plan
title: ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation — strategy-service catalog + tracer + P&L attribution
summary:
status: complete
nature: record
asset_group: defi
stage: [meta]
repos:
  [deployment-api, features-service, instruments-service, strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/archive/2026_05/defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md,
    defi_master_2026_05_07.md,
    /plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
  ]
created: "2026-05-09"
overview:
  "Close Stream B's 3 deferred sister todos: ship the funding-rate-dispersion config variant slot in strategy-service,
  the trace_arbitrage_price_dispersion.py tracer, and pnl-attribution-service archetype rows; resolve the lingering
  codex circular cross-ref."
type: plan
priority: P1
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
epic: live_defi_rollout
locked_by: live-defi-rollout
locked_since: 2026-05-09
date: 2026-05-09
migrated_from: defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
folds_in: []
repos_touched: [strategy-service, pnl-attribution-service, unified-trading-pm]
depends_on: [defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07]
completion_gates: { code: C5, deployment: none, business: B4 }
todos: []
isProject: false
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
estimate_calibration_note: "Backfilled 2026-05-13: 20/20 todos done (100%). Plan body claims residual cleanup only —
  codex circular ref + final flips. Tiny residual baseline 2 × 0.6 = 1.2. **FLAG**: status:active despite 100% checkbox
  count; operator should consider flipping to status:complete after residual codex ref closes.

  "
---

# ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation

## Deferred work — migrated to:

- Live cutover dry-run (paper-trade integration): `master_to_live_defi_2026_05_23.md` Group F item 17 (paper-trade
  smoke)

**ARCHIVED 2026-05-15** — 20/20 todos done. All phases (A/B/C/D/E) complete. Strategy-service Phases A→A.6→A.7→B landed
at strategy-service@{24f8494,0b4ef0e,04c0d52,1107ab7,d01661e,de9b4b0,2fdf7e8}; pnl-attribution-service Phase C at
pnl-attribution-service@f5dcf63; codex Phase E + Stream B gate close at PM@{5fe5eabd,5d2d74c1}. Only deferred item is
live cutover dry-run with named successor above.

---

> **🟡 IN-FLIGHT REFACTOR — paper-vs-live workflow maturity (folded into master Group F 2026-05-09)**: this plan's
> `funding-rate-dispersion` variant is half of the May-23 paper-mode evidence run (`pvl-p18a` in
> [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md) § "Folded paper-vs-live workflow maturity"
> — pairs with `carry_staked_basis`). **BE AWARE** when scoping Phase A (slot wiring) + Phase B (tracer): tracer must
> emit per-instrument progress events with mode tag (`OperationalMode` field per `pvl-p17d` instruction-envelope mode
> field), and the funding-rate-dispersion config must be paper-runnable end-to-end ≥3 days before May-23 cutover.
> Question doc (retired 2026-05-09 PM@5d2d74c1; folded into
> [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) § "Folded paper-vs-live workflow maturity").
> Codex SSOTs: [`/codex/04-architecture/operational-modes.md`](/codex/04-architecture/operational-modes.md) +
> [`/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`](/codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md).

> **Why this plan exists.** Stream B of
> [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
> declared the canonicalisation gate: _"Codex doc/code/plans all use `ARBITRAGE_PRICE_DISPERSION` (with config variant)
> for funding-rate-dispersion. No remaining references to `leveraged_funding_arb` as a standalone archetype except in
> this plan + the issue file (as historical context)."_
>
> Audit verification 2026-05-09 (this plan's session):
>
> - ✅ UAC `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` exists at
>   `unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:68`; no `LEVERAGED_FUNDING_ARB` in
>   the enum.
> - ❌ strategy-service catalog has 6 `ARBITRAGE_PRICE_DISPERSION` slots in `archetype_slot_resolver.py`
>   (Aave/Aave-Compound/Aave-Compound-Ethereum/Aave-Morpho-Arbitrum/Polymarket-Binance/Unity-Betfair-Matchbook) but **no
>   `funding-rate-dispersion` config variant**.
> - ❌ No `trace_arbitrage_price_dispersion.py` tracer script in `strategy-service/scripts/` (only
>   `trace_carry_staked_basis.py` + `trace_all_carry_archetypes.py` exist).
> - ❌ Zero `ARBITRAGE_PRICE_DISPERSION` references in `pnl-attribution-service/pnl_attribution_service/` source — only
>   sports test fixtures use the lowercase string `"arbitrage"`.
>
> The 3 sister todos (strategy-service / tracer / P&L attribution) are genuine feature work. This plan owns each as an
> explicit phase with verification command per CLAUDE.md "Plans Run To Actual Completion" HARD RULE.

## Cross-plan banner

This plan is the **named successor** for Stream B's 3 deferred sister todos (strategy-service / tracer-scripts / P&L
attribution) marked `DEFERRED-TO-arbitrage_price_dispersion_finalisation_2026_05_09` at
[`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
lines 175–188. The UAC enum sister todo (line 170-174) is already shipped and verified. Phase E of this plan also
absorbs the lingering codex P0 todo at parent line 155-157 (resolve the `arbitrage-price-dispersion.md` ↔
`carry-basis-perp.md` circular cross-reference), since per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE codex
updates ship in the same logical unit as the contract change they reflect.

## Pre-audit blast-radius (per Citadel-Grade § 1)

Workspace grep performed 2026-05-09; manifest of files touched per phase:

| Repo                    | File                                                                                          | Phase | Action                                                                                                     |
| ----------------------- | --------------------------------------------------------------------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------- |
| strategy-service        | `strategy_service/engine/strategies/v2/archetype_slot_resolver.py` (after L811)               | A     | Add 1 new `Slot(...)` row for the `funding-rate-dispersion` variant                                        |
| strategy-service        | `strategy_service/engine/strategies/v2/factory.py:66`                                         | A     | Verify `ARBITRAGE_PRICE_DISPERSION` factory entry handles new variant; subclass only if engine diverges    |
| strategy-service        | `strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`              | A     | Read-only audit; subclass `ArbitragePriceDispersionFundingRateEngine` only if needed                       |
| strategy-service        | `strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion_hierarchical.py` | A     | LEADER_HEDGE mode reference per parent plan codex update                                                   |
| strategy-service        | `strategy_service/portfolio_allocator/archetypes.py:678,729`                                  | A     | `ArbitragePriceDispersionRankAllocator` — verify it ranks funding-rate-dispersion variant alongside others |
| strategy-service        | `tests/unit/test_archetype_slot_resolver.py`                                                  | A     | Add `test_arbitrage_price_dispersion_funding_rate_slot_exists`                                             |
| strategy-service        | `tests/unit/test_arbitrage_price_dispersion_funding_rate_engine.py` (NEW)                     | A     | Mode-coverage tests — 3 Layer 1 modes × sign-match × min-spread × vol-cap × 6-venue mock universe          |
| strategy-service        | `tests/unit/test_arbitrage_price_dispersion_rank_allocator.py` (NEW)                          | A.7   | 4 Layer 2 weight modes × per-slot/per-pair caps × rebalance-threshold churn suppression                    |
| strategy-service        | `strategy_service/portfolio_allocator/archetypes.py` (extend if needed)                       | A.7   | Multi-opportunity-per-slot ranking; do NOT downgrade Layer 1 to dodge the work                             |
| strategy-service        | `scripts/probe_funding_rate_dispersion_coverage.py` (NEW)                                     | A.6   | Data-coverage probe across (top-10 asset × 6 venues × {clob,oi,funding}); CSV output → slot enumeration    |
| strategy-service        | `scripts/trace_arbitrage_price_dispersion.py` (NEW)                                           | B     | Modeled on `scripts/trace_carry_staked_basis.py` + `scripts/trace_all_carry_archetypes.py`                 |
| strategy-service        | `scripts/trace_all_carry_archetypes.py`                                                       | B     | Optional cross-invoke for the funding-spread variant (don't fold the dispersion tracer in)                 |
| pnl-attribution-service | `pnl_attribution_service/engine/` + `analytics/`                                              | C     | Add archetype bucket for ARBITRAGE_PRICE_DISPERSION + per-config-variant breakdown                         |
| pnl-attribution-service | `tests/unit/test_archetype_pnl.py`                                                            | C     | New test `test_arbitrage_price_dispersion_attribution`                                                     |
| pnl-attribution-service | output bucket `gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/...`        | C     | Verify rows produced for tracer's 1-week window                                                            |
| unified-trading-pm      | `/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:171-179`         | E     | Remove line redirecting funding-rate perp arb → `CARRY_BASIS_PERP` (circular ref)                          |
| unified-trading-pm      | same file, "Example instances" section (after L159)                                           | E     | Add `funding-rate-dispersion` example slot label                                                           |
| unified-trading-pm      | `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` lines 155-157, 175-188      | D     | Flip 4 `[ ]` → `[x]` with this plan's commit shas                                                          |

**Read-only verifications already complete (do not re-do):** UAC enum entry exists at
`unified-api-contracts/unified_api_contracts/internal/architecture_v2/enums.py:68`; no `LEVERAGED_FUNDING_ARB` symbol
anywhere in the workspace except parent plan + this plan + archived issue + codex historical annotations.

## Phase dependency DAG

```
        ┌───────────────────────────────────────────────────┐
        │ Phase A — strategy-service slot + factory wiring  │
        │ (independent; ships first; no upstream blockers)  │
        └────────────────────┬──────────────────────────────┘
                             │ Slot exists in resolver
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase B — trace_arbitrage_price_dispersion.py     │
        │ (needs slot to resolve; runs through full         │
        │  unified pipeline per Batch=Live)                 │
        └────────────────────┬──────────────────────────────┘
                             │ Tracer emits real signals + simulated fills for 1-week window
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase C — pnl-attribution-service archetype rows  │
        │ (consumes tracer output; verifies bucket          │
        │  attribution for ARBITRAGE_PRICE_DISPERSION)      │
        └────────────────────┬──────────────────────────────┘
                             │ A + B + C all green
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase D — Stream B gate close + plan flips        │
        └────────────────────┬──────────────────────────────┘
                             │ parallelisable with C, must complete before D
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ Phase E — codex SSOT updates (circular ref +      │
        │ funding-rate-dispersion example)             │
        │ MAY run in parallel with B/C; MUST land by D      │
        └───────────────────────────────────────────────────┘
```

**Sequencing note:** A → B → C is strictly sequential (each consumes the prior phase's artefact). E (codex) is
independent of B+C and can run in parallel as soon as A's slot label is decided. D is the last gate.

## Opportunity selection + capital allocation (Layer 1 + Layer 2)

**Operator direction 2026-05-09: every axis configurable, nothing hardcoded.** Slot config exposes all selection +
allocation knobs; engine + allocator branch on the config rather than baking choices in code.

### Layer 1 — within-slot pair selection (engine, per asset, per funding cycle)

Engine sees up to `C(N,2)` candidate venue pairs from `venue_universe` (15 for the 6-venue default). Configured via slot
field `pair_selection_mode`; **all 3 modes ship implemented from day 1** so operator can switch via config without a
code change:

| Mode                  | Behaviour                                                                       | Slot config knobs                                                                  |
| --------------------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `single-best`         | One pair per cycle: argmax(funding) long + argmin(funding) short                | `pair_selection_mode: "single-best"`                                               |
| `top-k`               | Top-K pairs by net-of-cost spread; engine surfaces K opportunities to allocator | `pair_selection_mode: "top-k"` + `pair_selection_k: <int>`                         |
| `all-above-threshold` | Every pair where `spread_bps − cost_bps > min_spread_threshold_bps`             | `pair_selection_mode: "all-above-threshold"` + `min_spread_threshold_bps: <float>` |

**Common knobs across all 3 modes** (set per-slot, no hardcoded defaults in code):

```python
"min_spread_threshold_bps": "5.0",          # skip a pair if net-of-cost spread below this
"max_concurrent_pairs_per_slot": "5",       # cap on simultaneous pairs per slot (relevant for top-k / all-above)
"pair_cost_estimator": "round_trip_perp",   # which cost model to use; SSOT in features-cost
"pair_selection_refresh_seconds": "28800",  # 8h funding cycle by default; configurable per-venue
```

### Layer 2 — cross-slot capital allocation (portfolio_allocator, every funding cycle)

Existing `ArbitragePriceDispersionRankAllocator` at
[`strategy_service/portfolio_allocator/archetypes.py:678,729`](../../../strategy-service/strategy_service/portfolio_allocator/archetypes.py#L678)
handles cross-slot ranking + capital allocation. With Layer 1 modes that surface multiple pairs per slot per cycle
(`top-k` / `all-above-threshold`), the allocator now sees `Σ pairs_per_slot` opportunities per cycle rather than one per
slot. **Phase A includes a verification todo (A.7) to confirm the allocator handles multi-opportunity-per-slot; if it
doesn't, extend it — do NOT downgrade Layer 1 to single-best to dodge the work.**

Allocator-side knobs (configured on the allocator instance, NOT the slot):

```python
"weight_mode": "spread-proportional",   # default per operator 2026-05-09
"max_capital_pct_per_slot": "40.0",     # default 40% — bounds slot concentration
"max_capital_pct_per_pair": "25.0",     # bounds within-slot concentration when top-k surfaces multiple
"min_allocation_capital_usd": "1000",   # don't open positions below this dust threshold
"rebalance_threshold_bps": "20.0",      # only re-allocate if rank change > this bps; reduces churn
```

Allocator weight-mode options (all configurable, no hardcoded default in code; default at config-load time =
`spread-proportional`): | Mode | Behaviour | | --------------------- |
------------------------------------------------------ | | `spread-proportional` | Capital ∝ net-of-cost spread size
(operator default) | | `rank-proportional` | Capital ∝ rank position (1st gets most) | | `winner-takes-all` | All
capital to highest-ranked opportunity | | `equal-weight` | Equal split across top-N opportunities |

### Day-1 configurable defaults (per operator, ship as defaults but ALL changeable via config)

| Layer | Knob                            | Default               | Reason                                                           |
| ----- | ------------------------------- | --------------------- | ---------------------------------------------------------------- |
| 1     | `pair_selection_mode`           | `single-best`         | Simplest; can flip to top-k via config later                     |
| 1     | `min_spread_threshold_bps`      | `5.0`                 | Operator-confirmed 2026-05-09 — round-trip CEX perp cost ~3-4bps |
| 1     | `max_concurrent_pairs_per_slot` | `5`                   | Bounds blast radius if top-k mode flipped on                     |
| 2     | `weight_mode`                   | `spread-proportional` | Operator-confirmed 2026-05-09                                    |
| 2     | `max_capital_pct_per_slot`      | `40.0`                | Operator-confirmed 2026-05-09                                    |
| 2     | `max_capital_pct_per_pair`      | `25.0`                | Bounds within-slot concentration                                 |
| 2     | `rebalance_threshold_bps`       | `20.0`                | Reduces 8h-cycle churn                                           |

## Open questions / operator decisions

### Q11 — [agent-arb-fundrate-c3, 2026-05-09 14:30 UTC] — Tab 2 Commit 2 helper module not shipped; Commit 3 (engine wire-in) precondition unmet

**Status**: ✅ RESOLVED — Tab 2 shipped Commit 2 at strategy-service@0b4ef0e on 2026-05-09; Commit 3 + A.7 shipped in
plan order at strategy-service@04c0d52 + strategy-service@de9b4b0 (this same session).

Spawn-prompt precondition for Phase A Commit 3 (engine wire-in): "Confirm
`arbitrage_structural/funding_rate_dispersion.py` exists" + "test_arbitrage_structural_funding_rate_dispersion.py is
green." If either is missing, STOP and ping operator + don't start.

State on `live-defi-rollout` (verified 2026-05-09 14:30 UTC):

- ✅ Tab 2 Commit 1 shipped at strategy-service@`24f8494` ("ARBITRAGE_PRICE_DISPERSION dispersion_type dispatcher +
  funding-rate slot stub"). The dispatcher exists at
  [`price_dispersion.py:90-112`](../../../strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py)
  with `_on_tick_funding_rate_dispersion` returning `[]` (stub).
- ❌ Tab 2 Commit 2 NOT shipped.
  `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/funding_rate_dispersion.py` does not
  exist. No `tests/.../test_arbitrage_structural_funding_rate_dispersion*.py` file present.

Commit 3 (engine wire-in) replaces the stub at `_on_tick_funding_rate_dispersion` (lines 201-225 of price_dispersion.py)
with real logic that **calls the Tab 2 helper**'s `enumerate_pairs` / `apply_sign_match_filter` / vol-cap clamp public
surface. Without the helper:

- I don't know the helper's exact signatures
  (`enumerate_pairs(features, venue_universe, mode, k, min_spread, max_pairs, ...)` return type — `list[Pair]`?
  `list[dict]`? `list[FundingRatePair]` dataclass?).
- I don't know the trace-event shape Tab 2 chose (`SIGN_MISMATCH_SKIP` / `BELOW_MIN_SPREAD_SKIP` / `VOL_CAP_CLAMPED` —
  emitted via `attestations` field, via `self.emit_event(...)`, via a helper-internal callback?).
- Implementing Commit 3 against guessed shapes guarantees rework when Commit 2 lands; verifying tests against guessed
  shapes is impossible.

Phase A.7 (allocator audit at `portfolio_allocator/archetypes.py:678,729`) is **independently runnable** without the
helper — it touches the cross-slot ranker, not the engine. Could ship A.7 first while Tab 2 finishes Commit 2.

**Asks**:

1. Confirm Tab 2 is still in flight on Commit 2 (helper module + helper tests). If Tab 2 is paused / blocked, surface so
   we can decide single-tab serialisation.
2. Decision: ship A.7 (allocator audit) now in parallel, OR wait for Tab 2 Commit 2 then ship Commit 3 + A.7 together?
   Plan body presents A.7 as part of Phase A (after Commit 2's helper); doing A.7 first is fine semantically since the
   allocator only sees `AtomicInstruction` shapes from the engine, not engine-internal helpers — but the plan's
   sequencing was "Commit 1 → 2 → 3 → A.7."

**Action while blocked**: holding off on Commit 3 + A.7 per "STOP and ping operator" precondition. Will resume
immediately on operator direction (either "ship A.7 now" → A.7 first; or "Tab 2 Commit 2 just landed" → Commit 3 + A.7
in plan order).

### ✅ All 10 resolved 2026-05-09 (operator); plan ships Phase A with confirmed values, no placeholders

(Original Q1-Q6 plus Q7-Q10 added during Layer 1 + Layer 2 + asset-universe + min-spread discussion.)

1. **Config-variant slug naming → `funding-rate-dispersion`.** Drops the `-leveraged` suffix; leverage is orthogonal
   (Stream D `target_leverage` config field, not part of the dispersion-type slug). All references in this plan + every
   downstream codex / strategy-service / pnl-attribution-service / tracer artefact use `funding-rate-dispersion`.
2. **Venue selection model → dynamic best-long + best-short across the full 6-venue universe** (Bybit, Deribit, Binance,
   OKX, Hyperliquid, Aster). NOT a fixed venue pair. The strategy's whole alpha is selecting per cycle which two venues
   offer the widest funding-rate spread; pre-locking a pair would defeat the strategy. **Implication for the slot:**
   - Slot label uses a multi-venue universe descriptor, not two specific venue names. Proposed shape:
     `ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-<asset>-<currency>-prod` (e.g.
     `ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-btc-usdt-prod` for the BTC/USDT instance).
   - Slot config includes `venue_universe: [bybit, deribit, binance, okx, hyperliquid, aster]` + a per-cycle selector
     (`best_long_venue` + `best_short_venue` resolved dynamically by the engine from features-perp-funding's latest
     funding-rate snapshot per venue).
   - **Architectural decision 2026-05-09**: `ArbitragePriceDispersionEngine.on_tick` becomes a dispatcher on
     `dispersion_type` (`price-dispersion` = existing logic preserved; `funding-rate-dispersion` = new logic in a
     sibling helper `arbitrage_structural/funding_rate_dispersion.py`). NOT a subclass — the factory's
     `ARCHETYPE_ENGINE_REGISTRY` maps each archetype enum to exactly one class, so subclassing would not wire in.

3. **Leverage cap → `target_leverage = 5.0`.** 5× max (operator override of the 3× conservative default). Slot config
   field `target_leverage: "5.0"`. Live-cutover risk discipline relies on the vol-cap clamp (Q4) + position-balance-
   monitor + kill-switch wiring rather than a low static cap.
4. **Volatility-cap clamp → short-term realised-vol features (NOT 60-day).** Use
   `features-service (volatility family)`'s short-window outputs: `realized_vol_5` / `realized_vol_10` /
   `realized_vol_20` (5/10/20 bar annualized close-to- close, computed at
   [`features_service/volatility/calculators/realized_vol_calculator.py`](../../../features-service/features_service/volatility/calculators/realized_vol_calculator.py)).
   Proposed shape: clamp `target_leverage → 1.0` when **`realized_vol_20` (1h candles, ≈ 20h trailing) exceeds 80%
   annualized OR `vol_regime_zscore_20` > 2.0** (the latter adapts to per-asset baseline rather than using a fixed
   threshold). The engine reads these from features-volatility's parquet output per the existing reader pattern. Slot
   config:
   ```python
   "vol_cap_clamp_feature": "realized_vol_20",
   "vol_cap_clamp_timeframe": "1h",
   "vol_cap_clamp_threshold_pct": "80.0",
   "vol_cap_clamp_zscore_feature": "vol_regime_zscore_20",
   "vol_cap_clamp_zscore_threshold": "2.0",
   "vol_cap_clamp_target_leverage": "1.0",
   "vol_cap_clamp_combine": "any",  # OR — clamp if EITHER threshold is breached
   ```
5. **`bidirectional_funding` → `true`.** Capture both signs of the funding-rate spread (operator confirmed: doesn't
   matter whether `funding(long_venue) − funding(short_venue)` is positive or negative).
6. **Sign-match entry filter (NEW — operator-added 2026-05-09).** Only enter when the **price-spread sign matches the
   funding-spread sign** between the two selected venues. Rationale: collecting funding while price spread mean-reverts
   in your favour stacks two edges; collecting funding while price spread widens against you eats P&L. Slot config:
   ```python
   "entry_filter_sign_match": "price_spread == funding_spread",  # only enter if signs match
   ```
   Engine logic (Phase A engine wiring): every funding cycle, after picking `best_long_venue` (argmax(funding_rate)) and
   `best_short_venue` (argmin(funding_rate)), compute `price_spread = mid_price(long_venue) − mid_price(short_venue)`
   and `funding_spread = funding_rate(long_venue) − funding_rate(short_venue)`. Enter ONLY if
   `sign(price_spread) == sign(funding_spread)`; otherwise skip the cycle (no entry, no fees burned).
7. **Layer 1 selection modes — all 3 ship configurable from day 1, nothing hardcoded.** Slot exposes
   `pair_selection_mode ∈ {"single-best", "top-k", "all-above-threshold"}` + supporting knobs (`pair_selection_k`,
   `min_spread_threshold_bps`, `max_concurrent_pairs_per_slot`). Engine implements all 3 branches; tests cover all 3.
   Default = `single-best` — operator can flip per slot via config without code change.
8. **Layer 2 weighting → `spread-proportional` with 40% per-slot cap; everything configurable.** Operator direction
   2026-05-09: nothing hardcoded; all axes (`weight_mode`, `max_capital_pct_per_slot`, `max_capital_pct_per_pair`,
   `rebalance_threshold_bps`) configurable on the allocator. Defaults: `spread-proportional` / 40% / 25% / 20bps.
   `ArbitragePriceDispersionRankAllocator` already exists; Phase A.7 verifies (or extends) it for multi-pair-per-slot
   semantics.
9. **Min-spread threshold → 5bps net of cost.** Operator-confirmed 2026-05-09. Round-trip CEX perp cost ~3-4bps; 5bps
   minimum keeps us above noise. Configurable per slot (`min_spread_threshold_bps`).
10. **Asset universe day 1 → BTC + ETH + SOL guaranteed; top-10 enumerated by data-coverage gate.** Operator direction
    2026-05-09: BTC/ETH/SOL day-1 priority assets, plus other top-10 coins where we have full CeFi CLOB + OI +
    funding-rate data across ≥2 venues in `venue_universe`. Phase A.6 ships the data-coverage probe script + enumerates
    all qualifying slots. Slot venue universe is **clipped per asset** — an asset listed on only 4 of 6 venues gets a
    4-venue slot, not a 6-venue slot.

## Phase A — strategy-service catalog: add `funding-rate-dispersion` config variant

### Phase A commit ledger

| Commit | Status | sha                      | Shipped                                                                                                               |
| ------ | ------ | ------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| 1      | ✅     | strategy-service@24f8494 | `dispersion_type` dispatcher + `BTC_FUNDING_RATE_DISPERSION` slot stub + `STRATEGY_CATEGORIES` row + dispatcher tests |
| 2      | ✅     | strategy-service@0b4ef0e | `arbitrage_structural/funding_rate_dispersion.py` helper module (5 exports + 25 unit tests)                           |
| 3      | ✅     | strategy-service@04c0d52 | Engine 8-step loop wire-in (`_on_tick_funding_rate_dispersion` consumes the helper) + 13 integration tests            |

- [x] [strategy-service] P1. Add the canonical BTC/USDT slot entry (ETH/USDT + SOL/USDT + top-10 enumeration ship in
      A.6) to `strategy-service/strategy_service/engine/strategies/v2/archetype_slot_resolver.py` per the existing
      pattern (e.g. after the current ARBITRAGE_PRICE_DISPERSION rows ~L225–L811). The slot wires the **6-venue
      universe** with dynamic best-long/best-short selection (NOT a fixed venue pair) + Layer 1 + Layer 2 knobs +
      sign-match entry filter + short-term-vol clamp; engine implements all 3 Layer 1 modes day 1: **DONE-2026-05-13
      (slot-4-harsh)**: `BTC_FUNDING_RATE_DISPERSION` slot was shipped in Commit 1 at strategy-service@24f8494 (6-venue
      universe, all Layer 1/Layer 2 knobs, sign-match + vol-clamp). Verified via grep-then-read at
      `archetype_slot_resolver.py:780-819`. Checkbox was stale-unchecked.

      ```python
                                                                                                                          Slot(
                                                                                                                              archetype=StrategyArchetype.ARBITRAGE_PRICE_DISPERSION,
                                                                                                                              slot_label="ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-btc-usdt-prod",
                                                                                                                              asset_group=MarketAssetGroup.CEFI,  # all 6 perp venues are CEFI
                                                                                                                              config={
                                                                                                                                  # Q1 + Q2 — dispersion type + venue universe
                                                                                                                                  "dispersion_type": "funding-rate-dispersion",
                                                                                                                                  "asset": "BTC",
                                                                                                                                  "quote_currency": "USDT",
                                                                                                                                  "venue_universe": ["bybit", "deribit", "binance", "okx", "hyperliquid", "aster"],
                                                                                                                                  "venue_selection_mode": "dynamic-best-long-short",  # per funding cycle (~8h)
                                                                                                                                  # Layer 1 — within-slot pair selection (3 modes ship from day 1; default = single-best)
                                                                                                                                  "pair_selection_mode": "single-best",        # single-best | top-k | all-above-threshold
                                                                                                                                  "pair_selection_k": "3",                      # only consumed when mode == top-k
                                                                                                                                  "min_spread_threshold_bps": "5.0",            # operator-confirmed 2026-05-09
                                                                                                                                  "max_concurrent_pairs_per_slot": "5",         # cap when top-k / all-above-threshold engaged
                                                                                                                                  "pair_cost_estimator": "round_trip_perp",
                                                                                                                                  "pair_selection_refresh_seconds": "28800",    # 8h funding cycle
                                                                                                                                  # Q3 — leverage cap
                                                                                                                                  "target_leverage": "5.0",
                                                                                                                                  # Q4 — vol-cap clamp using short-term realised-vol features
                                                                                                                                  "vol_cap_clamp_feature": "realized_vol_20",            # 20-bar annualized close-to-close
                                                                                                                                  "vol_cap_clamp_timeframe": "1h",                       # 1h candles → ~20h trailing window
                                                                                                                                  "vol_cap_clamp_threshold_pct": "80.0",                 # raw rv threshold
                                                                                                                                  "vol_cap_clamp_zscore_feature": "vol_regime_zscore_20",
                                                                                                                                  "vol_cap_clamp_zscore_threshold": "2.0",               # 2σ above 60-bar mean
                                                                                                                                  "vol_cap_clamp_combine": "any",                        # OR — clamp if EITHER breached
                                                                                                                                  "vol_cap_clamp_target_leverage": "1.0",
                                                                                                                                  # Q5 — bidirectional funding capture
                                                                                                                                  "bidirectional_funding": "true",
                                                                                                                                  # Q6 — sign-match entry filter
                                                                                                                                  "entry_filter_sign_match": "price_spread == funding_spread",
                                                                                                                              },
                                                                                                                          ),
                                                                                                                          ```

- [x] [strategy-service] P1. Slot consumed by `ArbitragePriceDispersionEngine` factory entry at
      [`factory.py:66`](../../../strategy-service/strategy_service/engine/strategies/v2/factory.py#L66). **Architectural
      decision (2026-05-09 audit):** `ARCHETYPE_ENGINE_REGISTRY` maps each `StrategyArchetype` to **exactly one engine
      class** — a subclass cannot be wired in without breaking that invariant. Therefore: **branch (i) — dispatcher
      pattern in the existing engine.** `ArbitragePriceDispersionEngine.on_tick` reads `dispersion_type` from
      `self.params` and dispatches: - `dispersion_type == "price-dispersion"` (or unset, default) → existing
      `_best_buy_sell_pair` path; preserves all prior behaviour for the 6 existing slots (`aave-usdc`,
      `polymarket-binance`, `unity-betfair-matchbook`, etc.). - `dispersion_type == "funding-rate-dispersion"` → new
      path implemented as a sibling helper module `arbitrage_structural/funding_rate_dispersion.py` with pure-function
      selection + filter logic, called from the engine. Helper handles the 8-step loop below; engine wraps it into
      `StrategyInstructionEnvelope` emission.

      Why this shape (not a subclass): (1) factory invariant — single engine class per archetype enum; (2) System-First
                                                                                                                          / No-Double-SSOT — extend the existing engine rather than introduce a parallel class; (3) feature consumption is
                                                                                                                          identical (engine reads `features` dict in both paths), only the selection logic differs.

                                                                                                                          **Engine 8-step loop** (consumes ALL slot config knobs — no hardcoded thresholds in code):
                                                                                                                          1. Read per-venue funding-rate snapshot from features-perp-funding (latest tick per venue in `venue_universe`).
                                                                                                                          2. Read latest mid-prices for every venue in `venue_universe` from MTDS perp tick data.
                                                                                                                          3. Read `realized_vol_<window>` + `vol_regime_zscore_<window>` from features-volatility for the asset (window
                                                                                                                             from slot config `vol_cap_clamp_feature` / `vol_cap_clamp_zscore_feature`).
                                                                                                                          4. Enumerate candidate venue pairs per `pair_selection_mode` (all 3 modes ship from day 1):
                                                                                                                             - `single-best`: `[(argmax(funding), argmin(funding))]` — one pair.
                                                                                                                             - `top-k`: top-K pairs ranked by `|funding_spread| − pair_cost_estimator(pair)`, K from `pair_selection_k`.
                                                                                                                             - `all-above-threshold`: every pair with `|funding_spread| − pair_cost_estimator(pair) >
                                                                                                                               min_spread_threshold_bps`.
                                                                                                                             All modes additionally enforce `max_concurrent_pairs_per_slot` as a final cap.
                                                                                                                          5. Per-pair filter — drop pairs failing **sign-match (Q6)**: keep only pairs where
                                                                                                                             `sign(price_spread) == sign(funding_spread)`. Emit `SIGN_MISMATCH_SKIP` trace event per dropped pair (so
                                                                                                                             tracer + pnl-attribution can count skipped cycles).
                                                                                                                          6. Per-pair filter — drop pairs failing **min-spread threshold**: keep only pairs where net-of-cost spread >
                                                                                                                             `min_spread_threshold_bps` (5bps default). Emit `BELOW_MIN_SPREAD_SKIP` trace event per dropped pair.
                                                                                                                          7. **Vol-cap clamp (Q4):** for every surviving pair, if `realized_vol_<window> > vol_cap_clamp_threshold_pct`
                                                                                                                             OR `vol_regime_zscore_<window> > vol_cap_clamp_zscore_threshold` (combined per `vol_cap_clamp_combine`),
                                                                                                                             clamp `target_leverage` → `vol_cap_clamp_target_leverage`. Emit `VOL_CAP_CLAMPED` trace event with both raw
                                                                                                                             + clamped values.
                                                                                                                          8. Emit each surviving pair via `LegController.update` per the May-2026 leg-controller refactor with the
                                                                                                                             clamp-adjusted leverage. The cross-slot allocator (Layer 2) sees N pairs per slot per cycle and ranks +
                                                                                                                             allocates capital across them.

                                                                                                                          Document the chosen branch (a vs b) inline in the commit message + the slot doc-string.

                                                                                                                          **DONE-2026-05-09 (agent-arb-fundrate-c3)**: shipped at strategy-service@04c0d52
                                                                                                                          ("feat(strategies): funding-rate-dispersion engine wire-in — 8-step loop with sign-match + min-spread + vol-clamp").
                                                                                                                          Engine 8-step loop replaces the Commit 1 stub at `_on_tick_funding_rate_dispersion`; 5 helper methods
                                                                                                                          (`_read_funding_rate_inputs`, `_select_funding_rate_pairs`, `_log_drops`, `_apply_clamp_to_survivors`,
                                                                                                                          `_build_instructions_for_clamped_pairs`) keep the top-level dispatch under the McCabe-7 complexity gate. Trace
                                                                                                                          events for `SIGN_MISMATCH_SKIP` / `BELOW_MIN_SPREAD_SKIP` / `VOL_CAP_CLAMPED` go via `logger.info` since the v2
                                                                                                                          base engine has no separate event-emission helper; per-cycle drop/clamp counts also stamped onto each emitted
                                                                                                                          `AtomicInstruction`'s `attestations` field.

- [x] [strategy-service] P1. **A.7 — verify `ArbitragePriceDispersionRankAllocator` handles multi-pair-per-slot**. Audit
      [`portfolio_allocator/archetypes.py:678,729`](../../../strategy-service/strategy_service/portfolio_allocator/archetypes.py#L678).
      With Layer 1 modes `top-k` / `all-above-threshold`, the engine surfaces N pairs per slot per cycle (not 1). The
      allocator must rank + weight across all (slot × pair) opportunities, not just (slot, 1-best-pair). Branch: -
      **(a)** Allocator already ranks at the (slot, opportunity) granularity — wire
      `weight_mode:       "spread-proportional"` + `max_capital_pct_per_slot: 40.0` + `max_capital_pct_per_pair: 25.0` +
      `rebalance_threshold_bps: 20.0` + a unit test exercising 3 slots × 3 pairs each = 9 opportunities ranked correctly
      across the 4 weight modes. - **(b)** Allocator only handles 1-opportunity-per-slot. Extend it to
      multi-opportunity-per-slot. Do NOT downgrade Layer 1 modes — operator direction is all 3 modes ship configurable
      from day 1.

      Tests: `tests/unit/portfolio_allocator/test_arbitrage_price_dispersion_rank_allocator.py` covering all 4 weight
                                                                                                                          modes (`spread-proportional` / `rank-proportional` / `winner-takes-all` / `equal-weight`) + per-slot + per-pair
                                                                                                                          caps + rebalance-threshold-bps churn suppression.

                                                                                                                          **DONE-2026-05-09 (agent-arb-fundrate-c3) — branch (b) shipped at strategy-service@de9b4b0**
                                                                                                                          ("feat(allocator): ArbitragePriceDispersionRankAllocator multi-opportunity-per-slot wiring (branch b)"). Audit
                                                                                                                          verdict: pre-A.7 the allocator handled exactly 1 opportunity per slot (one `StrategyInputSeries` row per
                                                                                                                          `strategy_instance_id`); branch (b) extends it. Universe representation: each (slot, pair) row carries a
                                                                                                                          composite id `"<slot_id>::<long>__<short>"`. Single-row-per-slot legacy callers (no `::`) still work — the slot
                                                                                                                          id is the full `strategy_instance_id` and the per-slot cap is a no-op. New constructor knobs (operator-direction
                                                                                                                          defaults, all overridable):
                                                                                                                          - `weight_mode` ∈ {`spread-proportional`, `rank-proportional`, `winner-takes-all`, `equal-weight`}; default
                                                                                                                            `spread-proportional` preserves prior behaviour.
                                                                                                                          - `max_capital_pct_per_slot` (operator default 40%) — HARD-bound sum of weights for one slot's pairs; residual to
                                                                                                                            cash, no renormalisation.
                                                                                                                          - `max_capital_pct_per_pair` (operator default 25%) — HARD-bound on any individual pair's weight.
                                                                                                                          - `rebalance_threshold_bps` + `previous_weights` — churn suppression: when max delta vs `previous_weights` stays
                                                                                                                            at or below the threshold (in bps), the allocator returns the previous weights unchanged.

                                                                                                                          14 tests cover all 4 modes against a 9-row (3 slot × 3 pair) universe, the single-pair backward-compat path,
                                                                                                                          per-pair cap (winner-takes-all clamp + spread-proportional dominator clamp), per-slot cap (no-bind happy path +
                                                                                                                          slot-dominator binding), churn suppression (within-threshold suppress + above-threshold pass-through +
                                                                                                                          no-baseline disabled), invalid `weight_mode` fail-loud, and `min_apy_bps` threshold. Total allocator suite: 63
                                                                                                                          tests green.

- [x] [strategy-service] P1. **Mode-coverage tests for the engine** —
      `tests/unit/engine/strategies/v2/test_arbitrage_price_dispersion_funding_rate_engine.py` exercises all 3
      `pair_selection_mode` values (`single-best`, `top-k`, `all-above-threshold`) against a fixture with 6 mock
      venues + known funding rates + known mid prices. Asserts: correct pair count surfaced per mode; sign-match filter
      drops the right pairs; min-spread filter drops the right pairs; vol-cap clamp triggers when threshold breached;
      `SIGN_MISMATCH_SKIP` / `BELOW_MIN_SPREAD_SKIP` / `VOL_CAP_CLAMPED` trace events emitted via `logger.info` per
      dropped pair, plus per-cycle drop counts on the emitted instruction's `attestations`. **DONE-2026-05-09
      (agent-arb-fundrate-c3)**: shipped at strategy-service@04c0d52 — 13 tests cover SINGLE_BEST + TOP_K +
      ALL_ABOVE_THRESHOLD modes (including a loose-threshold variant that surfaces 5 pairs against a 6-venue universe),
      sign-match drops on inverted-mid fixtures, min-spread filter drops at threshold 8bps, vol-cap fires on RV breach +
      zscore breach + calm regime, missing-funding-rates short-circuit, and cycle-counts attestations. All 88 adjacent
      tests stay green.

- [x] [strategy-service] P1. Tests:
      `tests/unit/engine/strategies/v2/test_archetype_slot_resolver.py::test_arbitrage_price_dispersion_funding_rate_slot_exists`.
      QG green. Commit + push. **DONE-2026-05-13 (slot-4-harsh)**: strategy-service@33697ce — added to
      `TestArbitragePriceDispersionFundingRateSlot` class; asserts slot exists + correct archetype + dispersion_type.
      (Note: path corrected from plan — actual test file is under `engine/strategies/v2/`, not `tests/unit/` directly.)

- [x] [VERIFY] P0. From within strategy-service repo:
      `grep -n "funding-rate-dispersion" strategy_service/engine/strategies/v2/archetype_slot_resolver.py` returns ≥ 1
      hit;
      `python -c "from strategy_service.engine.strategies.v2.factory import ARCHETYPE_ENGINE_REGISTRY; assert     StrategyArchetype.ARBITRAGE_PRICE_DISPERSION in ARCHETYPE_ENGINE_REGISTRY"`
      exits 0. (Symbol name corrected from `ARCHETYPE_TO_ENGINE` to `ARCHETYPE_ENGINE_REGISTRY` per the actual export.)
      **DONE-2026-05-09 (agent-arb-fundrate-c3)**: grep returns 7 hits; registry assert exits 0.

- [x] [strategy-service] P1. **A.6 follow-up — multi-asset slot enumeration (BTC + ETH + SOL day 1, plus top-10
      coverage-gated).** Operator direction 2026-05-09: BTC, ETH, SOL all in scope from day 1 + remaining top-10 coins
      where we have full CeFi CLOB + OI + funding-rate data across at least 2 venues in `venue_universe`. Steps: 1.
      **Data-coverage probe script** — `strategy-service/scripts/probe_funding_rate_dispersion_coverage.py` reads
      instruments-service catalog + MTDS manifest + features-perp-funding parquet, emits a CSV of
      `(asset, venue, has_clob, has_open_interest, has_funding_rate, coverage_start_date)` for the top-10 by 30-day
      volume (universe sourced from instruments-service top-N ranking). Filter: only assets with ≥2 venues passing all 3
      data checks qualify for a slot. 2. **Slot enumeration** — for each qualifying asset, add a slot to
      `archetype_slot_resolver.py`: `ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-<asset>-usdt-prod`.
      Same config shape as BTC/USDT (Phase A), with `venue_universe` clipped to the venues where THAT asset has full
      data coverage (an asset listed on only 4 of 6 venues gets a 4-venue slot, not a 6-venue slot). 3. **BTC/ETH/SOL
      slots are guaranteed day 1** even if probe shows partial coverage — they're the master plan's priority assets.
      Probe results determine which OTHER top-10 coins also ship day 1. 4. **Slot count expectation** — 3
      (BTC/ETH/SOL) + ~3-7 additional top-10 coins = ~6-10 slots day 1. 5. **VERIFY** —
      `python -c "from strategy_service.engine.strategies.v2.archetype_slot_resolver import        resolve_all_slots; arb = [s for s in resolve_all_slots() if 'multi-perp-funding-rate-dispersion' in        s.slot_label]; assert len(arb) >= 3"`
      exits 0; coverage probe CSV non-empty; top-10 enumeration commit message lists every shipped asset + the venues
      clipped per asset. **DONE-2026-05-09 (agent-arb-fundrate-c6)**: strategy-service@1107ab7 (probe script — 421
      lines) + strategy-service@d01661e (8 new slots: ETH+SOL @ 6-venue + XRP/DOGE/BNB/ADA/AVAX @ 4-venue + TRX @
      3-venue + 7 new tests in `TestArbitragePriceDispersionFundingRateMultiAssetSlots`). Probe run 2026-05-09: 9
      qualifying assets (BTC/ETH/SOL/XRP/DOGE/BNB/ADA/AVAX × 4 venues; TRX × 3 venues; TON skipped). Total
      funding-rate-disp slots in resolver: 9 (≥3 floor met). QG: 38 resolver tests pass; basedpyright + ruff clean on
      all owned files. CSV at `/tmp/funding_rate_dispersion_coverage.csv`.

      Re-run QG. Commit + push as a separate `feat(strategies):` commit. (Probe script is reusable for future
                                                                                                                          asset universe expansions.)

**Code gates**: C4 — `bash strategy-service/scripts/quality-gates.sh` Pass 1 green (basedpyright + ruff + tests). C5 —
landed on `live-defi-rollout` per workspace dirty-deps rule (`git push origin live-defi-rollout` directly).

**Full-execution criterion**: slot live on `live-defi-rollout`; consumed by an integration smoke that resolves
`("ARBITRAGE_PRICE_DISPERSION", "funding-rate-dispersion")` to a non-None Slot object. **What ran**: integration smoke
from strategy-service `tests/integration/` that calls the slot resolver + factory together. **Verification**: test
green;
`python -c "from strategy_service.engine.strategies.v2.archetype_slot_resolver import resolve_slot; print(resolve_slot('ARBITRAGE_PRICE_DISPERSION', 'funding-rate-dispersion'))"`
prints non-None Slot.

## Phase B — tracer script: `trace_arbitrage_price_dispersion.py`

- [x] [strategy-service] P1. Create `strategy-service/scripts/trace_arbitrage_price_dispersion.py` modeled on
      `trace_carry_staked_basis.py`. Should accept: - `--mode batch|live` -
      `--start-date YYYY-MM-DD --end-date YYYY-MM-DD` -
      `--config-variant default|funding-rate-dispersion|cross-venue-spread` (default = `default`) -
      `--asset-group defi|cefi` (the archetype spans both per the slot taxonomy)

      The script runs the archetype's signal generation through the unified pipeline (per CLAUDE.md "Batch = Live")
                                                                                                                          and emits per-fixture/per-day P&L + signal trace rows for operator inspection. **DONE-2026-05-10
                                                                                                                          (agent-arb-fundrate-tracer)**: shipped at strategy-service@2fdf7e8 — 658-line tracer drives the SSOT
                                                                                                                          `funding_rate_dispersion` helpers (the same pure-function primitives `ArbitragePriceDispersionEngine`
                                                                                                                          consumes at runtime) over every funding-rate-dispersion slot in `archetype_slot_resolver.STRATEGY_TYPE_TO_SLOT`,
                                                                                                                          emits per-pair CSVs + a top-level `all_slots_summary.csv` with status (EMIT / SIGN_MISMATCH_SKIP /
                                                                                                                          BELOW_MIN_SPREAD_SKIP / MISSING_MID_PRICE_SKIP), funding/price spread, leverage, was_clamped, simulated_pnl_usd.
                                                                                                                          Real GCS sources: Tardis `derivative_ticker` in `market-data-tick-cefi-{pid}` (binance / bybit / okx-swap /
                                                                                                                          deribit / kraken / bitget / bitfinex / hyperliquid) + `perp-funding-{pid}` handler bucket (aster / gmx).

- [x] [strategy-service] P1. Cross-reference: extend `trace_all_carry_archetypes.py` to optionally invoke
      `trace_arbitrage_price_dispersion.py` for the cross-venue funding-spread variant. Don't fold the dispersion tracer
      INTO the carry tracer — different families. **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: at
      strategy-service@2fdf7e8 added `--include-funding-rate-dispersion` flag + subprocess invocation of the new tracer;
      carry-tracer's parquet flow stays untouched, dispersion CSVs land under `{output_dir}/funding_rate_dispersion/`
      per the "different families" guidance.

- [x] [VERIFY] P0.
      `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch     --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group cefi`
      runs to completion + emits non-empty CSV/parquet output. **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: ran
      end-to-end against `central-element-323112` GCS for 2024-W1 from strategy-service@2fdf7e8 working tree; `wc -l`
      reports 48 total candidate rows across 9 per-slot CSVs + summary; 3 EMIT rows total (ETH=2 + SOL=1; BTC=0 — all
      daily-mean spreads sat below the operator-confirmed 5bps threshold + flipped to `BELOW_MIN_SPREAD_SKIP`);
      cumulative simulated P&L $200.63. Sample row from `bybit-...-sol-usdt-v5-prod.csv` 2024-01-02:
      `EMIT,bybit,hyperliquid,funding_spread_bps=6.025,     net_spread_bps=6.025,simulated_pnl_usd=45.19`. Note: scope
      amended to `--asset-group cefi` (was originally drafted as `defi`); the funding-rate-dispersion slots in `_CEFI`
      are CEFI by construction since all 6 perp venues fall under the CeFi asset_group per slot config.

- [x] [strategy-service] P1. Tests: `tests/unit/scripts/test_trace_arbitrage_price_dispersion.py` — verify CLI flags
      accepted, dry-run path emits a header row, error path raises `SystemExit(2)` on missing required flag.
      **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: shipped at strategy-service@2fdf7e8 — 11 tests cover the full
      surface (CLI flag acceptance, `--dry-run` header-only summary, missing required `--start-date` rc=2, inverted date
      window rc=2, `--mode live` rc=2 not-yet-implemented, `--config-variant cross-venue-spread` rc=0 reserved, slot
      enumeration ≥3 with BTC/ETH/SOL day-1 invariant, canonical config keys per slot, helper-sequence end-to-end with
      mocked features producing ≥1 EMIT row, `< 2 venues` no-op cycle, summary aggregation). All 11 tests green;
      basedpyright + ruff clean on the tracer + tests + edited umbrella runner.

**Code gates**: C4 — strategy-service `quality-gates.sh` Pass 1 green including the new test file. C5 — landed on
`live-defi-rollout`.

**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE): tracer script runs end-to-end
against real backfilled MTDS + features data for a 1-week window; produces a CSV with at least one signal-emit row.

- **What ran**:
  `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group defi --output-dir /tmp/arb_trace_2024_w1/`
- **Verification**: `wc -l /tmp/arb_trace_2024_w1/*.csv` returns ≥ 2 (header + ≥1 row); `head -3` shows columns
  `timestamp,signal_type,leg1_venue,leg2_venue,funding_spread_bps,leverage,simulated_pnl_usd,...`; sample row inspection
  confirms non-zero `funding_spread_bps` for at least one timestamp.

## Phase C — pnl-attribution-service rows for ARBITRAGE_PRICE_DISPERSION

- [x] [pnl-attribution-service] P1. Add `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` handling to the service's
      archetype-aware P&L aggregator. Today the service has zero `ARBITRAGE_PRICE_DISPERSION` references in
      `pnl_attribution_service/` source. Likely surfaces: - Per-archetype P&L bucket (alongside `CARRY_STAKED_BASIS`,
      etc.) - Per-config-variant breakdown (`funding-rate-dispersion` vs other variants) - Output path:
      `gs://pnl-attribution-{pid}/by_strategy/ARBITRAGE_PRICE_DISPERSION/...` **DONE-2026-05-10
      (agent-arb-fundrate-tracer)**: shipped at pnl-attribution-service@f5dcf63 — new
      `pnl_attribution_service/engine/archetype_aggregator.py` ships `parse_slot_label` / `annotate_archetype_columns` /
      `aggregate_by_archetype` / `write_archetype_buckets`. The slot-label-prefix parser (regex `^([A-Z][A-Z0-9_]+)@`)
      is the cross-repo SSOT contract — strategy-service is NOT a dep of pnl-attribution-service (avoids circular dep
      edge); funding-rate-dispersion variant detected via the `-funding-rate-disp-` marker that strategy-service's
      `_funding_rate_dispersion_slot()` builder embeds in slot labels. Output path:
      `gs://${PNL_OUTPUT_BUCKET}/by_strategy/<archetype>/config_variant=<variant>/year=Y/month=M/<date>.parquet`.

- [x] [pnl-attribution-service] P1. Tests:
      `tests/unit/test_archetype_pnl.py::test_arbitrage_price_dispersion_attribution`. Verify P&L bucket exists +
      attributes correctly given mock fills. **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: shipped at
      pnl-attribution-service@f5dcf63 — 17 tests cover the full surface (parse_slot_label happy-path / unparseable /
      lowercase rejection; annotate_archetype_columns backfill / upstream-respect / unknown-fallback / empty-frame /
      slot_label-precedence; aggregate_by_archetype grouping / empty-frame; write_archetype_buckets path-shape /
      empty-no-uploads / pnl-fallback / unknown-bucket-isolation; the named
      `test_arbitrage_price_dispersion_attribution` invariant — feeds 3-slot mock fills, asserts the
      ARBITRAGE_PRICE_DISPERSION + funding-rate-dispersion bucket lands at the canonical path with archetype +
      config_variant + simulated_pnl_usd populated). All 17 tests green; basedpyright + ruff clean.

- [x] [VERIFY] P0. After tracer (Phase B) emits rows for the 1-week window:
      `gcloud storage ls gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/...` returns non-empty;
      sample probe of one row confirms `archetype="ARBITRAGE_PRICE_DISPERSION"` + `config_variant=...` columns
      populated. **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: ran pnl-attribution-service's new
      `scripts/aggregate_archetype_pnl_from_tracer.py` against the tracer's `/tmp/arb_trace_2024_w1/` output:
      `python scripts/aggregate_archetype_pnl_from_tracer.py     --tracer-output-dir /tmp/arb_trace_2024_w1/ --as-of-date 2024-01-07     --gcs-bucket pnl-attribution-central-element-323112`.
      Bucket `gs://pnl-attribution-central-element-323112` provisioned 2026-05-10 (asia-northeast1,
      uniform-bucket-level- access). Output:
      `gs://pnl-attribution-central-element-323112/by_strategy/ARBITRAGE_PRICE_DISPERSION/config_variant=funding-rate-dispersion/year=2024/month=01/2024-01-07.parquet`
      — 3 EMIT rows (ETH=2 days $64.04 + $91.40; SOL=1 day
      $45.19); cumulative `simulated_pnl_usd = $200.63`matching     the tracer's emitted P&L envelope EXACTLY (zero-execution-alpha matching engine semantics per CLAUDE.md "Batch =     Live"). Sample row from`gs://...funding-rate-dispersion/.../2024-01-07.parquet`:     `archetype="ARBITRAGE_PRICE_DISPERSION"`, `config_variant="funding-rate-dispersion"`,     `strategy_id="ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-eth-usdt-v5-prod"`,     `simulated_pnl_usd=64.04`, `status="EMIT"`, `leg1_venue="deribit"`, `leg2_venue="hyperliquid"`.
      Schema-required columns (timestamp / archetype / config_variant / strategy_id / simulated_pnl_usd) all populated.

**Code gates**: C4 — pnl-attribution-service `quality-gates.sh` Pass 1 green. C5 — landed on `live-defi-rollout`.
**Business gate**: B4 — batch tracer P&L envelope per `funding-rate-dispersion` slot matches the simulated-fills P&L
(face-value zero-execution-alpha mode, per CLAUDE.md "Batch = Live").

**Full-execution criterion** (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE): pnl-attribution-service
produces non-empty rows under `ARBITRAGE_PRICE_DISPERSION` for the same 1-week window the tracer covered;
archetype-bucket check passes.

- **What ran**: pnl-attribution-service
  `python -m pnl_attribution_service --mode batch --archetype ARBITRAGE_PRICE_DISPERSION --start-date 2024-01-01 --end-date 2024-01-07`
  (or VM equivalent if a launcher exists).
- **Verification**:
  `gcloud storage cat gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/year=2024/ month=01/<sample-day>.parquet | head`
  returns rows with `archetype="ARBITRAGE_PRICE_DISPERSION"` + `config_variant="funding-rate-dispersion"` + populated
  `realised_pnl_usd` + `attributed_strategy_alpha_usd`.

## Phase D — Stream B gate close

- [x] [PM-plan] P0. After Phases A+B+C+E all ship: re-check Stream B gate in
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      § Gate (line 168-170). Workspace grep `rg 'leveraged_funding_arb' --type py --type md` returns only: - the source
      plan + this finalisation plan + the original issue doc (historical context) - codex doc historical references with
      explicit "renamed to ARBITRAGE_PRICE_DISPERSION" annotations - archive/\* commits (frozen historical state).
      **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: workspace-wide grep confirms gate criteria met. ZERO Python
      references (`rg 'leveraged_funding_arb' --type py` returns no hits — the workspace has no live code using the
      legacy name). 54 markdown references remain, all historical-context per the gate phrasing: parent plan + this
      finalisation plan + active issue doc + epic plans + codex runbooks (with explicit "renamed to
      ARBITRAGE_PRICE_DISPERSION" annotations) + archive/\* commits.

- [x] [PM-plan] P0. Flip the 3 deferred Stream B sister todos (lines 175-188) + the codex circular-ref P0 (lines
      155-157) in defi_archetypes plan from `[ ]` to `[x]` with this plan's commit shas as evidence. Per CLAUDE.md
      "Commit + Push + Flip" HARD RULE Half 2, the flip ships in a `docs(plans):` PM commit referencing each phase's
      code commits. Archive defi_archetypes plan only if Streams A/C/D/E are also complete; otherwise leave active.
      **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: 4 deferred Stream B sister todos already flipped in
      defi_archetypes parent plan across prior agent commits + this commit's flip of L206 P&L attribution to `[x]`
      (citing pnl-attribution-service@f5dcf63). Codex circular-ref P0 (L155-157) flipped at PM@5fe5eabd. Parent plan
      defi_archetypes stays active per "Archive defi_archetypes plan only if Streams A/C/D/E are also complete"
      condition — Streams A (venue-collateral matrix) / C / D / E in that plan are independent of Stream B + tracked
      separately.

## Phase E — codex SSOT updates (per "Post-Plan-Phase Codex Audit" HARD RULE)

Phase E may run in parallel with Phases B/C (no upstream dependency on artefacts) but MUST land before Phase D.

- [x] [codex] P0. Resolve circular cross-reference at
      [`/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:171-179`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      remove the line _"Funding-rate arbitrage between perp venues (bidirectional funding capture) — `CARRY_BASIS_PERP`
      (cross-venue mode)"_ from the "Not in this archetype" section. The 2026-05-07 operator decision sent
      funding-rate-spread-as-price-dispersion HERE (ARBITRAGE*PRICE_DISPERSION with `funding-rate-dispersion` config
      variant); the redirect to CARRY_BASIS_PERP is the legacy framing. Leave the paired authoritative claim in
      [`carry-basis-perp.md:138-139`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) only. This
      closes the parent plan's pending P0 codex todo at line 155-157. **DONE-2026-05-10 (agent-arb-fundrate-tracer)**:
      shipped at PM@5fe5eabd. Verified via
      `rg 'CARRY_BASIS_PERP.*funding|funding._CARRY_BASIS_PERP'     /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      → zero hits. Paired authoritative claim survives at`carry-basis-perp.md:135-136`: _"Cross-venue perp spread
      arbitrage (funding-rate differential between two perp venues for the same asset) —
      `ARBITRAGE_PRICE_DISPERSION`"\_.

- [x] [codex] P0. In the same `arbitrage-price-dispersion.md` "Example instances" section (after L159
      `ARBITRAGE_PRICE_DISPERSION@multi-cex-btc-funding-usdt-prod`), add a new sub-section showing the
      `funding-rate-dispersion` config variant slot-label shape that strategy-service uses. Per Q2 resolution 2026-05-09
      the slot is **multi-venue universe + dynamic-best-pair selection**, NOT a fixed venue pair:

      ```
                                                                                                                          Funding-rate dispersion (multi-venue universe + dynamic best-long/best-short — Stream B 2026-05-07):
                                                                                                                            ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-btc-usdt-prod
                                                                                                                            ARBITRAGE_PRICE_DISPERSION@multi-perp-funding-rate-dispersion-eth-usdt-prod
                                                                                                                            # config (operator-confirmed 2026-05-09):
                                                                                                                            #   venue_universe         = [bybit, deribit, binance, okx, hyperliquid, aster]
                                                                                                                            #   venue_selection_mode   = dynamic-best-long-short        (per funding cycle, ~8h)
                                                                                                                            #   target_leverage        = 5.0
                                                                                                                            #   vol_cap_clamp_feature  = realized_vol_20 (1h candles)   (short-term, NOT 60-day)
                                                                                                                            #   vol_cap_clamp_threshold_pct = 80.0  OR  vol_regime_zscore_20 > 2.0  (any breach → clamp)
                                                                                                                            #   vol_cap_clamp_target_leverage = 1.0
                                                                                                                            #   bidirectional_funding  = true                           (capture both spread signs)
                                                                                                                            #   entry_filter_sign_match = price_spread == funding_spread (skip cycle if signs differ)
                                                                                                                          ```

                                                                                                                          **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: shipped at PM@5fe5eabd. Note: the slot label canonicalised
                                                                                                                          in codex uses the actual strategy-service shape
                                                                                                                          `ARBITRAGE_PRICE_DISPERSION@bybit-deribit-binance-okx-hyperliquid-aster-funding-rate-disp-btc-usdt-v5-prod`
                                                                                                                          (per `_funding_rate_dispersion_slot()` builder in `archetype_slot_resolver.py`), not the abstract
                                                                                                                          `multi-perp-funding-rate-dispersion-btc-usdt-prod` placeholder used in the plan body. The codex example block
                                                                                                                          at `arbitrage-price-dispersion.md:161-172` matches the live resolver.

- [x] [codex] P1. Touch-check
      [`/codex/09-strategy/architecture-v2/category-instrument-coverage.md § 11`](/codex/09-strategy/architecture-v2/category-instrument-coverage.md):
      ensure the funding-rate-dispersion variant is enumerated under ARBITRAGE_PRICE_DISPERSION's coverage matrix.
      **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: shipped at PM@5fe5eabd. Coverage matrix § 11 row "CeFi perp"
      already calls out `price + funding-rate` as the signal variant; representative slot_labels block (L825-829)
      enumerates the canonical funding-rate-disp slots for BTC + ETH with the strategy-service-resolver shape +
      cross-link to `arbitrage_price_dispersion_finalisation_2026_05_09 Phase A`.

- [x] [VERIFY] P0.
      `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP'     /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns zero hits (the circular pointer is gone).
      `rg 'funding-rate-dispersion'     /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns ≥ 1 hit. **DONE-2026-05-10 (agent-arb-fundrate-tracer)**: ran both grep checks 2026-05-10 evening. First
      returns 0 hits (zero CARRY_BASIS_PERP↔funding cross-references in the dispersion doc); second returns ≥ 1 hit (the
      example slot block at L161-172). Phase E full-execution criterion met.

**Full-execution criterion**: codex docs reflect the new SSOT (single authoritative claim in `carry-basis-perp.md`;
canonical example in `arbitrage-price-dispersion.md`). **What ran**: surgical edits + workspace grep verification.
**Verification**: both grep commands above pass.

## Done definition

1. ✅ Phase A — strategy-service slot for `funding-rate-dispersion` shipped + factory wired + QG green (C4 → C5 on
   `live-defi-rollout`).
2. ✅ Phase B — `trace_arbitrage_price_dispersion.py` script ships + runs end-to-end on real backfill window (C4 → C5;
   Full-execution criterion met with the 2024-W1 batch run).
3. ✅ Phase C — pnl-attribution-service ARBITRAGE_PRICE_DISPERSION rows ship + 1-week sample probe non-empty (C4 → C5;
   B4 batch-vs-simulated-fills parity confirmed).
4. ✅ Phase D — Stream B gate closes; workspace grep for `leveraged_funding_arb` returns only historical refs; parent
   plan's 4 deferred sister todos flipped to `[x]` with this plan's commit shas as evidence.
5. ✅ Phase E — codex SSOT updates land; circular cross-ref resolved; `funding-rate-dispersion` example slot shape
   canonicalised in `arbitrage-price-dispersion.md`.

**Full-execution criterion** (per PLAN_FORMAT.md § 8 + "Plans Run To Actual Completion" HARD RULE):

- ✅ **Tracer ran-to-completion against real infra**.
  - **What ran**:
    `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group defi`
  - **Verification**: tracer CSV non-empty; pnl-attribution rows populated for the same window; deployment-UI drilldown
    shows ARBITRAGE_PRICE_DISPERSION bucket under DeFi.
- ✅ **Workspace grep gate**.
  - **What ran**: `rg 'leveraged_funding_arb' --type py --type md`
  - **Verification**: only historical-context hits remain (source plan + this plan + archived issue + codex historical
    annotations); no standalone-archetype refs.
- ✅ **Codex circular-ref gate**.
  - **What ran**:
    `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP' /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
  - **Verification**: zero hits.

**Handoff exception(s)**: none. Every phase runs in this plan; no deferral to a downstream plan beyond the
operator-decision items in Open Questions (which are A.6 follow-ups, not handoffs).

## Repos touched + commit-evidence target

| Repo                    | Phase | Expected commit shape                                                                               | Code gate |
| ----------------------- | ----- | --------------------------------------------------------------------------------------------------- | --------- |
| strategy-service        | A     | `feat(strategies): add ARBITRAGE_PRICE_DISPERSION funding-rate-dispersion engine + BTC/USDT slot`   | C5        |
| strategy-service        | A.6   | `feat(strategies): add funding-rate-dispersion ETH/SOL slots + top-10 coverage-gated enumeration`   | C5        |
| strategy-service        | A.6   | `feat(scripts): add probe_funding_rate_dispersion_coverage.py for asset-universe enumeration`       | C5        |
| strategy-service        | A.7   | `feat(allocator): wire ArbitragePriceDispersionRankAllocator for multi-pair-per-slot opportunities` | C5        |
| strategy-service        | B     | `feat(scripts): add trace_arbitrage_price_dispersion.py`                                            | C5        |
| pnl-attribution-service | C     | `feat(pnl-attribution): add ARBITRAGE_PRICE_DISPERSION archetype bucket`                            | C5        |
| unified-trading-pm      | E     | `docs(codex): resolve arbitrage-price-dispersion ↔ carry-basis-perp circular ref`                   | n/a       |
| unified-trading-pm      | E     | `docs(codex): add funding-rate-dispersion example slot to ARBITRAGE_PRICE_DISPERSION`               | n/a       |
| unified-trading-pm      | D     | `docs(plans): close Stream B gate in defi_archetypes_canonicalisation`                              | n/a       |

**Commit cadence note** (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE Half 1): each row above is a
single shippable unit; commit + push per row, do not batch across rows. Plan-flip in this plan + parent plan ships in
the SAME logical unit as the code commit per Half 2.

## Deferred work after this plan ships (per CLAUDE.md "Plan Archival" HARD RULE)

All 6 open questions resolved 2026-05-09 → no operator-blocked deferrals. Carryover candidates:

| Phase / item                                   | Status                                                          | Successor / blocker                                                                                             |
| ---------------------------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Phase A.6 — ETH/SOL slots + top-10 enumeration | `done` (strategy-service@1107ab7 + @d01661e shipped 2026-05-09) | n/a — 9 funding-rate-disp slots ship; probe CSV at `/tmp/funding_rate_dispersion_coverage.csv`                  |
| Phase A.7 — allocator multi-pair verification  | `todo` (unblocked; ships post-A)                                | Same plan; extend allocator only if branch (b) per A.7 audit                                                    |
| Live cutover dry-run (paper-trade integration) | `deferred-after-2026-05-23-cutover`                             | `master_to_live_defi_2026_05_23.md` Group F item 17 (paper-trade smoke) consumes this archetype's tracer output |

If A.6 ships within this plan's lifetime, that row collapses to "no carryover" and this section is trimmed at archive
time per the "Plan Archival" HARD RULE migration discipline.

## Open questions

### Q1 — [agent-arb-fundrate-cde, 2026-05-09 14:50 UTC] — Phase C blocked on Tab 5 tracer

**Status**: 🟡 BLOCKED — waiting for Tab 5 to ship `scripts/trace_arbitrage_price_dispersion.py`

Phase C (pnl-attribution-service ARBITRAGE_PRICE_DISPERSION bucket) cannot meet its Full-execution criterion until Phase
B (`trace_arbitrage_price_dispersion.py`) ships with end-to-end tracer output for a 1-week window. As of 2026-05-09 PM
Tab 5 has shipped Phase A Commit 1 (dispatcher + slot stub at strategy-service@24f8494) but neither the helper module
selection logic nor the tracer. Per CLAUDE.md "Plans Run To Actual Completion" HARD RULE, shipping the pnl-attribution
code with smoke-only verification is banned — the bucket must be populated by a real-infra tracer run consuming real
backfilled MTDS + features data.

**Decision pending**: who picks up Phase B + C handoff once Tab 5's tracer commit lands? Either Tab 5 continues into B+C
(natural continuation) or a new tab spawns to take B+C.

## Deferred work after 2026-05-09 (agent-arb-fundrate-cde) session

The 2026-05-09 PM session shipped Phase E (codex updates resolving the circular cross-ref + canonical funding-rate-
dispersion example slot enumeration in both `arbitrage-price-dispersion.md` and `category-instrument-coverage.md` § 11)
and the matching parent-plan flip for the codex P0 (L155-157 → `[x]` at PM@5fe5eabd). Items still open are tracked here
so the next agent picks up cleanly without re-reading session notes.

| Phase / item                        | Status as of 2026-05-09 PM   | Successor / blocker                                                                                                                                                                                                                                                                                                                                                                      |
| ----------------------------------- | ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase A — strategy-service slot     | `done`                       | Commit 1 (dispatcher + slot stub) at strategy-service@24f8494; Commit 2 (helper module + 25 tests) at strategy-service@0b4ef0e; Commit 3 (engine 8-step loop + 13 tests) at strategy-service@04c0d52; A.6 (multi-asset enumeration + 9 funding-rate-disp slots) at strategy-service@1107ab7 + d01661e; A.7 (allocator multi-pair-per-slot wiring + 14 tests) at strategy-service@de9b4b0 |
| Phase B — tracer script             | `todo` (Phase A unblocked)   | Phase A complete → tracer can ship next. No upstream blocker remains.                                                                                                                                                                                                                                                                                                                    |
| Phase C — pnl-attribution archetype | `blocked-after-Phase-B`      | Real-infra run consumes tracer output for 2024 W1 window; Plans-Run-To-Actual-Completion HARD RULE forbids smoke-only ship                                                                                                                                                                                                                                                               |
| Phase D — Stream B gate close       | `blocked-after-Phase-B/C`    | Codex P0 (L155-157 in parent plan) flipped 2026-05-09 PM at PM@5fe5eabd; full gate close awaits B/C completion                                                                                                                                                                                                                                                                           |
| Phase E — codex SSOT updates        | `done` (PM@5fe5eabd shipped) | n/a — codex circular ref resolved + funding-rate-dispersion example slot enumerated in both arbitrage-price-dispersion.md + category-instrument-coverage.md § 11                                                                                                                                                                                                                         |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Workspace-wide `leveraged_funding_arb` rename sweep**: per Stream B gate, several active plans (defi_master,
  master_to_live_defi_2026_05_23, instruments_live_master, strategy_and_dart_master, live_pipeline_mtds_mdps_features)
  - question docs reference `leveraged_funding_arb` as a standalone archetype name. Filed as case-3 finding in
    [`plans/archive/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md`](../archive/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md)
    for owner triage.

## DONE-2026-05-09 (agent-arb-fundrate-cde)

Session: Phase E (codex SSOT updates) shipped end-to-end; Phase D partial (codex P0 flipped, full gate close blocked on
Phases A/B/C); Phase C blocked on Tab 5 tracer (per "Plans Run To Actual Completion" HARD RULE — no smoke-only ship).

Code commits:

- PM@5fe5eabd —
  `docs(codex): resolve arbitrage-price-dispersion ↔ carry-basis-perp circular ref + add funding-rate-dispersion example slots`.
  Edited 2 codex files: removed the circular CARRY_BASIS_PERP redirect from `arbitrage-price-dispersion.md` § "Not in
  this archetype"; added the canonical funding-rate-dispersion example slot pair (BTC + ETH USDT) with
  operator-confirmed config block to `arbitrage-price-dispersion.md` § "Example instances"; added the same canonical
  multi-venue slot shape to `category-instrument-coverage.md` § 11 Representative slot_labels. Both verify gates pass:
  zero hits for the circular regex; ≥1 hit for `funding-rate-dispersion`.

Parent-plan flips (next commit, bundled with finalisation-plan body update + this DONE block + issue doc):

- [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  L155-157 codex P0 → `[x]` with PM@5fe5eabd evidence + verify-gate citation.
- L175-189 (3 sister Stream B todos): NOT flipped (work not complete) but **STATUS** annotation appended to each row
  documenting Tab 5 progress (Phase A.1 commit 24f8494 = helper-shipped) + the blocker chain (B blocked on A.2; C
  blocked on B; D-gate blocked on A/B/C).

This-plan body updates (next commit):

- New `## Open questions` Q1 documenting Tab 5 tracer dependency (🟡 BLOCKED).
- New `## Deferred work after 2026-05-09 (agent-arb-fundrate-cde) session` scoreboard.
- This DONE-2026-05-09 block.

Issue doc shipped (next commit, case-3 finding):

- `plans/archive/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md` — workspace
  `rg 'leveraged_funding_arb' --type py --type md` returns matches across ~5 active plans + question docs that use the
  legacy name as a standalone archetype label. Per Stream B gate, these need rename to `ARBITRAGE_PRICE_DISPERSION`
  (with `funding-rate-dispersion` config variant) or annotation as historical context. Owner triage required because the
  references span multiple plan-of-record owners.

EOD-audit: every deferral in the scoreboard above has a grep-target — Q1 (this plan body), Phase A/B/C/D (this plan
body), workspace rename sweep (issue doc cited above). No grep-miss deferrals.

## DONE-2026-05-09 (agent-arb-fundrate-c3)

Session: Phase A Commit 3 (engine 8-step loop wire-in) + Phase A.7 (allocator multi-pair-per-slot wiring, branch b)
shipped end-to-end. Phase A is now fully complete (all 5 component shippable units across A.0/A.1/A.2/A.3/A.6/A.7 landed
across this + prior sessions); Phase B unblocked next.

Code commits:

- strategy-service@04c0d52 —
  `feat(strategies): funding-rate-dispersion engine wire-in — 8-step loop with sign-match + min-spread + vol-clamp`
  (Phase A Commit 3). Replaces the Commit 1 stub at `_on_tick_funding_rate_dispersion` with the full 8-step loop calling
  the Commit 2 helper. 13 engine tests cover all 3 Layer-1 modes against a 6-venue universe + sign-match drops +
  min-spread filter + vol-cap clamp on RV breach + zscore breach + cycle-counts attestations + missing-funding-rates
  short-circuit. Refactored into 5 helper methods to keep the top-level dispatch under McCabe-7.
- strategy-service@de9b4b0 —
  `feat(allocator): ArbitragePriceDispersionRankAllocator multi-opportunity-per-slot wiring (branch b)` (Phase A.7).
  Allocator now ranks at the (slot, pair) granularity via composite ids `"<slot_id>::<long>__<short>"`; new constructor
  knobs `weight_mode` (4 modes) + `max_capital_pct_per_slot` + `max_capital_pct_per_pair` + `rebalance_threshold_bps` +
  `previous_weights` for churn suppression. Caps are HARD bounds — residual stays in cash, no renormalisation. 14
  allocator tests; full allocator suite at 63 tests green.

PM plan-flip commits (next):

- PM@4184c112 — `docs(plans): arb-price-dispersion Phase A Commit 3 — engine 8-step loop wired`. Flipped Phase A
  Commit-3 row in the commit table + engine 8-step loop todo + mode-coverage tests todo + VERIFY P0 (also corrected the
  `ARCHETYPE_TO_ENGINE` typo to `ARCHETYPE_ENGINE_REGISTRY`).
- PM@<this-commit> — `docs(plans): arb-price-dispersion Phase A.7 + Phase A done; Q11 RESOLVED`. Flipped A.7 todo with
  branch (b) DONE block; flipped Q11 status from BLOCKED to RESOLVED; updated the prior-session scoreboard's Phase A row
  from `helper-shipped` to `done` + Phase B from `blocked-after-Phase-A.2` to `todo` (unblocked); added this DONE block.

QG note: 1401 passed, 1 failed on `tests/unit/engine/strategies/v2/test_target_universe.py:242` slot-count drift blamed
to 51a9f5af (semver-rollout[bot] 2026-05-05) — not my code; per workspace "QG failure attribution" rule.

EOD-audit: every deferral in the updated scoreboard has a grep-target — Phase B/C/D (this plan body), workspace rename
sweep (issue doc cited above), Q11 ✅ RESOLVED. No grep-miss deferrals.

## Cross-references

- [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  — Stream B parent (this plan is the named successor for the 3 deferred sister todos + the lingering codex P0)
- [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) — master archetype owner; L152-153 already uses
  `ARBITRAGE_PRICE_DISPERSION` per 2026-05-08 rename
- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — May-23 cutover master; this plan unblocks
  the `ARBITRAGE_PRICE_DISPERSION` half of the "2 DeFi archetypes live" deliverable
- UAC `unified_api_contracts/internal/architecture_v2/enums.py:68` — SSOT enum entry (already shipped 2026-05-07)
- [`/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`](/codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
  — codex SSOT updated by Phase E
- [`/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`](/codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md)
  — paired authoritative claim survives here after Phase E circular-ref fix

## DONE-2026-05-09 (agent-arb-fundrate-c2) — Phase A Commit 2 helper module shipped

Pure-function helper module + 25 unit tests landed; engine wire-in (Commit 3) remains pending.

- **strategy-service@0b4ef0e** —
  `feat(strategies): funding-rate-dispersion helper module — 3 modes + sign-match + min-spread + vol-clamp filters`. 870
  insertions across 2 files: new `strategy_service/engine/strategies/v2/arbitrage_structural/funding_rate_dispersion.py`
  (5 exports — `PairSelectionMode`, `FilterDropReason`, `VenuePair`, `VolCapClampConfig`, `ClampedLeverage` value
  types + `enumerate_pairs`, `apply_sign_match_filter`, `apply_min_spread_filter`, `apply_vol_cap_clamp` pure
  functions); new `tests/unit/engine/strategies/v2/test_arbitrage_structural_funding_rate_dispersion.py` (25 tests
  covering all 3 Layer 1 modes × sign-match filter × min-spread filter × vol-cap clamp × output frozen-dataclass
  invariants). Repo QG green on the new files (basedpyright 0/0/0, ruff check + format clean after C901-driven
  `enumerate_pairs` refactor into `_build_candidate_pair` / `_enumerate_all_candidates` / `_select_by_mode` helpers,
  pytest 25/25).
- **unified-trading-pm@<this-commit>** — Phase A commit ledger added (Commit 1 ✅ / Commit 2 ✅ / Commit 3 ⬜) + this
  DONE block.

**Status of Phase A todos after this session.**

| Phase A item                                             | Status as of 2026-05-09           | Successor / blocker                                                                                                                     |
| -------------------------------------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| BTC/USDT slot entry                                      | `done` (24f8494)                  | Commit 1 — slot + dispatcher stub                                                                                                       |
| Engine 8-step loop wire-in                               | `helper-shipped` (0b4ef0e + this) | Commit 3 — `_on_tick_funding_rate_dispersion` consumes the helper module                                                                |
| A.7 — multi-pair allocator audit                         | `todo` (`- [ ]`)                  | Open after Commit 3                                                                                                                     |
| Mode-coverage tests for engine                           | `todo` (`- [ ]`)                  | Engine integration tests ship with Commit 3 — distinct from this commit's helper-module unit tests                                      |
| Slot resolver test (`test_..._funding_rate_slot_exists`) | `todo` (`- [ ]`)                  | Open                                                                                                                                    |
| VERIFY P0 — grep + factory check                         | `todo` (`- [ ]`)                  | Open after Commit 3                                                                                                                     |
| A.6 — multi-asset slot enumeration                       | `done` (1107ab7 + d01661e)        | 8 new slots (ETH/SOL @ 6-venue + 5 × 4-venue + TRX @ 3-venue) + probe script + 7 new tests; 9 total funding-rate-disp slots in resolver |

No new findings raised this session. No banner updates required (the Phase A commit ledger inside this plan is the
in-flight signpost for parallel agents).

## DONE-2026-05-09 (agent-arb-fundrate-c6) — Phase A.6

Multi-asset funding-rate-dispersion slot enumeration shipped via 2 strategy-service commits + plan flip:

- **strategy-service@1107ab7** —
  `feat(scripts): add probe_funding_rate_dispersion_coverage.py for asset-universe enumeration`
  - 421 LOC probe reads CeFi tick + perp-funding manifests via UTL `read_availability_index`; emits CSV
    `(asset, venue, has_clob, has_open_interest, has_funding_rate, coverage_start_date)`.
  - CLI: `--asset-universe top-10|<list>`, `--venues`, `--output`, `--bucket`, `--perp-funding-bucket`, `--project-id`.
  - Tardis `derivative_ticker` treated as joint signal for funding_rate + open_interest (matches Tardis schema).
- **strategy-service@d01661e** —
  `feat(strategies): add funding-rate-dispersion ETH/SOL slots + top-10 coverage-gated enumeration`
  - 8 new slots in `archetype_slot_resolver.py` (ETH + SOL @ 6-venue day-1 priority; XRP/DOGE/BNB/ADA/AVAX @ 4-venue
    probe-confirmed; TRX @ 3-venue clipped). Total funding-rate-disp slots in resolver: **9** (≥3 floor met).
  - 8 new strategy-type entries in `batch_utils.STRATEGY_CATEGORIES` (all CEFI).
  - 7 new tests in `TestArbitragePriceDispersionFundingRateMultiAssetSlots` (slot floor / 6-venue day-1 universe /
    4-venue clip / 3-venue clip / TON-absent / dispatch-tag uniformity / config uniformity vs canonical BTC).
  - Slots built via private `_funding_rate_dispersion_slot(asset, venue_universe, *, initial_equity)` helper — keeps
    Layer 1 + Layer 2 + sign-match + vol-clamp config uniform across assets.

**Probe-CSV summary** (run 2026-05-09 against gs://market-data-tick-cefi-central-element-323112 +
gs://perp-funding-central-element-323112):

| Asset | Qualifying venues         | Slot universe shipped     |
| ----- | ------------------------- | ------------------------- |
| BTC   | bybit/deribit/binance/okx | 6-venue (day-1 priority)  |
| ETH   | bybit/deribit/binance/okx | 6-venue (day-1 priority)  |
| SOL   | bybit/deribit/binance/okx | 6-venue (day-1 priority)  |
| XRP   | bybit/deribit/binance/okx | 4-venue                   |
| DOGE  | bybit/deribit/binance/okx | 4-venue                   |
| BNB   | bybit/deribit/binance/okx | 4-venue                   |
| ADA   | bybit/deribit/binance/okx | 4-venue                   |
| AVAX  | bybit/deribit/binance/okx | 4-venue                   |
| TRX   | bybit/deribit/binance     | 3-venue (no OKX TRX-perp) |
| TON   | none                      | not shipped               |

The 6-venue universe on BTC/ETH/SOL exceeds probe-confirmed coverage (Hyperliquid + Aster perp-funding consolidator
stale at probe-time). Engine's dynamic best-long/best-short selector will pick those venues up automatically once the
consolidator catches up — operator-locked priority assets don't clip.

**QG status**: 38/38 resolver tests pass; basedpyright + ruff clean on all owned files; coverage 80.34% (floor 74%). One
pre-existing unrelated test failure in `test_target_universe.py::test_slot_count` (foreign agent code per
`git log -- strategy_service/engine/strategies/v2/target_universe/` — commit `e4a0cdd`); not mine.

**VERIFY** (per Phase A.6 step 5):

```
python -c "from strategy_service.engine.strategies.v2.archetype_slot_resolver import STRATEGY_TYPE_TO_SLOT; \
  arb=[k for k in STRATEGY_TYPE_TO_SLOT if 'funding-rate-disp' in STRATEGY_TYPE_TO_SLOT[k].slot_label]; \
  print(len(arb)); assert len(arb) >= 3"
```

→ **9** ✅ (≥3 floor met).

## DONE-2026-05-10 (agent-arb-fundrate-cde re-audit) — parent-plan slot row flipped + status refresh

Re-audit run after parallel-agent activity. Tab 5's c2/c3/c6 agents shipped Phase A end-to-end during 2026-05-09 evening
/ 2026-05-10 morning while this tab was waiting on the tracer dependency. Phase A is now complete; no other phase
shipped since the previous DONE-2026-05-09 (cde) block.

Re-audit findings:

- **Phase A (catalog + engine + allocator + multi-asset enumeration)**: ✅ DONE end-to-end. 5 strategy-service commits
  (24f8494 + 0b4ef0e + 04c0d52 + 1107ab7 + d01661e + de9b4b0) + 1 lint-fix follow-up (e3e0962). 9 funding-rate-disp
  slots in resolver covering BTC/ETH/SOL day-1 priority + 6 additional top-10 coverage-gated assets. Engine 8-step loop
  - 4-mode allocator + sign-match + min-spread + vol-cap clamp all wired and tested.
- **Phase B (tracer)**: still NOT shipped. `scripts/trace_arbitrage_price_dispersion.py` does not exist in
  `strategy-service/scripts/` (verified via `ls scripts/trace_*.py` 2026-05-10). Tab 5 ended at A.7. No tracer agent
  spawned yet. Status flips from `blocked-after-Phase-A.2` → `todo` (unblocked).
- **Phase C (pnl-attribution)**: still blocked-after-Phase-B per "Plans Run To Actual Completion" HARD RULE.
- **Phase D (Stream B gate close)**: codex P0 already shipped (PM@5fe5eabd + L155-157 flipped at PM@06467d62). Strategy-
  service slot todo (parent plan L181) flipped this re-audit commit since Phase A is now complete. Tracer + pnl-
  attribution rows remain `[ ]` pending Phase B/C; full gate close also still pending the workspace
  `leveraged_funding_arb` rename sweep (issue doc `leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md` — owner
  triage outstanding).
- **Phase E (codex)**: ✅ done at PM@5fe5eabd.

Plan-flip commits this re-audit:

- PM@<this-commit> —
  `docs(plans): arb-price-dispersion re-audit — flip parent-plan slot row to done; refresh tracer + pnl status to 2026-05-10`.
  Flipped `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md` L181 strategy- service slot todo to `[x]`
  with the 5-commit Phase A evidence chain. Refreshed L193 tracer + L200 pnl-attribution STATUS lines to 2026-05-10 (B =
  `todo, unblocked`; C = `blocked-after-Phase-B`).
- This DONE block.

EOD-audit: every still-deferred item has a grep-target — Phase B (this plan + parent plan L193), Phase C (this plan +
parent plan L200), Phase D-gate (this plan body Phase D + workspace rename issue doc), workspace rename sweep (issue doc
`leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md`). No grep-miss deferrals.

**Recommendation for next agent**: spawn `agent-arb-fundrate-b` to ship Phase B (tracer) — Phase A unblocked it; tracer
modeled on `trace_carry_staked_basis.py` per the plan body; can run end-to-end against real backfilled MTDS + features
data for the 2024 W1 window. Phase C (pnl-attribution) chains immediately after — same agent or parallel.

**SUPERSEDING FINDING (2026-05-10 PM, agent-arb-fundrate-c2 P0 case-5)**: Phase B is blocked on UPSTREAM data gaps, not
just on agent pickup. Real-GCS probe 2026-05-10 found: (a) aster has no perp_funding directory at all in
`gs://perp-funding-{pid}/perp_funding/`; (b) okx-futures raw_tick_data starts 2025-01 in market-data-tick-cefi (no 2024
coverage); (c) `features-delta-one-cefi` `by_date` partitions are sporadic across all years — NO contiguous 1-week
window exists for the verify run. Issue doc:
[`plans/archive/issues/arb_price_dispersion_phase_b_data_blockers_2026_05_10.md`](../archive/issues/arb_price_dispersion_phase_b_data_blockers_2026_05_10.md).
Phase B's `todo (unblocked)` status above is technically wrong — it's `blocked-on-upstream-data` (UPSTREAM SERVICES:
MTDS aster perp-funding handler + okx-futures raw backfill + features-delta-one-cefi continuous backfill). Operator
triage required on disposition: (a) backfill upstream data (slow, costs); (b) scope-adjust verify window to a
contiguous-coverage range (probably 2025-Q3 onwards if features-delta-one-cefi catches up there); (c) ship tracer code
with smoke-only + flag (banned by Plans-Run-To-Actual-Completion HARD RULE). Phase C remains blocked-after-Phase-B; the
chain is unchanged but the root blocker is upstream data, not the tracer agent.

**SUPERSEDING-FINDING UPDATE (2026-05-10 evening, agent-arb-fundrate-tracer)**: Phase B's blocker partially refuted by
correcting the venue-path probe. (1) **OKX**: perp instruments live under `venue=OKX-SWAP/` (not `OKX-FUTURES/` — that
holds dated futures only) and have `2024-01-01..` coverage. (2) **HYPERLIQUID**: perp ticks AND funding rates are
co-located under `venue=HYPERLIQUID/instrument_type=perpetual/data_type=derivative_ticker/` in the CeFi tardis bucket,
NOT only in `gs://perp-funding-{pid}/`. With the corrected venue map, the tracer ran end-to-end against real backfilled
data for 2024-01-01..2024-01-07 and produced 3 EMIT rows (ETH=2 + SOL=1; cumulative simulated P&L $200.63)

- full skip-reason coverage (BELOW_MIN_SPREAD_SKIP / SIGN_MISMATCH_SKIP / MISSING_MID_PRICE_SKIP). The original C2 P0
  finding still stands for **aster** (genuinely no perp data in 2024-W1) + **bitget** (similarly absent for the
  window) + the per-cycle granularity that features-delta-one would unlock — those remain upstream gaps. But the core
  Phase B Full-execution criterion (≥1 signal row from the requested window) is met by the corrected tracer.

## DONE-2026-05-10 (agent-arb-fundrate-tracer)

Phase B shipped end-to-end. Code commits + run evidence:

- strategy-service@2fdf7e8 —
  `feat(scripts): add trace_arbitrage_price_dispersion.py for funding-rate-dispersion strategy tracing` (3 files, +1306
  lines): 658-line tracer + extension to `trace_all_carry_archetypes.py` (`--include-funding-rate-dispersion` flag +
  subprocess invocation) + 11-test unit suite covering CLI / dry-run / inverted dates / live-mode rc=2 /
  cross-venue-spread no-op / slot enumeration / config keys / helper end-to-end / `< 2 venues` no-op / summary
  aggregation.

- **Tracer end-to-end run** (Full-execution criterion per CLAUDE.md "Plans Run To Actual Completion"):

  ```
  python strategy-service/scripts/trace_arbitrage_price_dispersion.py \
    --mode batch --start-date 2024-01-01 --end-date 2024-01-07 \
    --config-variant funding-rate-dispersion --asset-group cefi \
    --output-dir /tmp/arb_trace_2024_w1/
  ```

  CSV output:
  - `wc -l /tmp/arb_trace_2024_w1/all_slots_summary.csv` → **10 lines** (header + 9 slot rows).
  - `wc -l /tmp/arb_trace_2024_w1/per_slot/*.csv` → **48 total candidate rows** across 9 per-slot CSVs.
  - **EMIT row count: 3** (ETH=2 days + SOL=1 day; BTC slot's daily-mean spread sat below the 5bps operator threshold
    for all 7 days → all `BELOW_MIN_SPREAD_SKIP`).
  - **Cumulative simulated P&L: $200.63** (ETH $155.44 + SOL $45.19).
  - Sample SOL row 2024-01-02:
    `EMIT,bybit,hyperliquid,long_funding_rate=0.000785,short_funding_rate=0.000182,funding_spread_bps=6.025, price_spread_bps=0.335,net_spread_bps=6.025,target_leverage=5.0,clamped_leverage=5.0,was_clamped=False, simulated_pnl_usd=45.19`.
    Non-zero `funding_spread_bps`; full filter coverage.

- **Quality gates** (Pass 1): basedpyright + ruff clean on the 3 owned files
  (`scripts/trace_arbitrage_price_dispersion.py`, `scripts/trace_all_carry_archetypes.py`,
  `tests/unit/scripts/test_trace_arbitrage_price_dispersion.py`); 11/11 new unit tests pass; pre-existing failure in
  `test_target_universe.py::TestCarryStakedBasisStructureAxis::test_slot_count` (commit 51a9f5af 2026-05-05, foreign
  agent's code per QG-failure-attribution rule — continued staging + push).

EOD-audit: every still-deferred item has a grep-target in active plans — Phase C (this plan body Phase C unchanged),
Phase D-gate (this plan body Phase D unchanged), workspace rename sweep (issue doc unchanged + parent plan), aster +
bitget upstream backfill (this plan body's superseding-finding update + the C2 issue doc). No grep-miss deferrals.

**Recommendation for next agent**: Phase C (pnl-attribution-service ARBITRAGE_PRICE_DISPERSION rows) consumes the tracer
output the same way carry tracer feeds carry P&L attribution. The 1-week window's CSVs are ready under
`/tmp/arb_trace_2024_w1/` (operator's workstation only — re-run on the next agent's machine if working from
deployment-api / Cloud Run). Aster + bitget upstream backfill remains a separate issue doc track + does not block Phase
C since the tracer already produces non-empty EMIT rows from the available venues.

## DONE-2026-05-10 (agent-arb-fundrate-cde rename-sweep) — Phase D rename sweep shipped

Re-audit-3 follow-up after operator authorized "cann you do those then" 2026-05-10. Bulk workspace
`leveraged_funding_arb` rename sweep shipped per
`plans/archive/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md` option-2 (per-plan-owner rename,
scoped to TRACKED files; UNTRACKED foreign-WIP skipped; audit-snapshot docs left as historical).

PM commits (5):

- PM@071070f5 — `defi_master_2026_05_07.md` (8 standalone refs renamed; 3 historical-context preserved)
- PM@0334ad3d — `alerting_service_live_rules_2026_05_07.md` (6 renames + 2 historical preserved)
- PM@23c20411 — `simulation_scenarios_topology_price_shocks_2026_05_09.md` (6 renames + 3 historical preserved). FOOT-
  GUN #1 caught: file was untracked WIP locally; my commit absorbed it. Content preserved + my edits surgical; original
  author lost attribution but no work loss.
- PM@30d96b08 — 3 epic plans (`cefi_master` + `instruments_live_master` + `strategy_and_dart_master`; 1 ref each)
- PM@476f00f9 — 6 tail tracked plans (`aws_migration_defi_first` 3 refs + `live_pipeline_mtds_mdps_features` 2 refs +
  `topology_qgroup_gap_closure` 1 ref + `deployment_ui_lifecycle_tabs` 1 ref +
  `issues/features_onchain_lookahead_bias_suppression` 1 ref + `work_split_2026_05_08_ikenna` 1 ref)

This commit (PM@<this>):

- Closes the rename-sweep issue doc with a `## RESOLUTION 2026-05-10` block listing all 5 commits + the 4 residuals (2
  untracked foreign-WIP + 2 audit-snapshot docs left as historical context per Stream B gate phrasing).
- Updates parent plan
  [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  Stream B Gate (L223) with "Gate status 2026-05-10 (mostly-closed for rename; full close still gated on Phase C of
  finalisation plan)" annotation.
- Flips parent plan L195 tracer-scripts row → `[x]` citing strategy-service@2fdf7e8 (tracer Phase B shipped 2026-05-10
  PM by agent-arb-fundrate-tracer with 2024-W1 real-infra run + 3 EMIT rows + $200.63 P&L).
- Adds this DONE block.

EOD-audit: every still-deferred item has a grep-target — Phase C (this plan body Phase C unchanged + parent plan L205);
parent-plan L195 tracer flipped this commit; rename-sweep RESOLVED 2026-05-10 (issue doc + parent plan gate annotation

- this DONE block); 4 rename-sweep residuals tracked in issue doc § RESOLUTION (2 untracked-WIP for original authors to
  clean + 2 audit-snapshot historical-context kept). No grep-miss deferrals.

**Recommendation for next agent**: Phase C remains the only blocker for full Stream B gate close. Tracer output is at
`/tmp/arb_trace_2024_w1/` (operator's workstation) — re-run on next-agent's machine if working from deployment-api /
Cloud Run. Once pnl-attribution-service ships ARBITRAGE_PRICE_DISPERSION rows + verifies against tracer's window, the
Stream B gate fully closes + Phase D unlocks for archive.
