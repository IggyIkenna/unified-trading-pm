---
title: "ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation — strategy-service catalog + tracer + P&L attribution"
overview:
  "Close Stream B's 3 deferred sister todos: ship the funding-rate-dispersion config variant slot in strategy-service,
  the trace_arbitrage_price_dispersion.py tracer, and pnl-attribution-service archetype rows; resolve the lingering
  codex circular cross-ref."
type: plan
asset_group: defi
priority: P1
deadline: 2026-05-23
parent: master_to_live_defi_2026_05_23
epic: live_defi_rollout
locked_by: live-defi-rollout
locked_since: 2026-05-09
date: 2026-05-09
status: active
migrated_from: defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md # Stream B sister todos
folds_in: []
related:
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md
  - defi_master_2026_05_07.md
  - master_to_live_defi_2026_05_23.md
repos_touched:
  - strategy-service # Phase A (slot + factory) + Phase B (tracer)
  - pnl-attribution-service # Phase C (archetype-aware P&L bucket)
  - unified-trading-pm # Phase D (gate close + plan flips) + Phase E (codex)
depends_on:
  - defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07 # parent Stream B; we close 3 deferred sister todos
completion_gates:
  code: C5 # all 3 service repos green on QG + landed on live-defi-rollout
  deployment: none
  business: B4 # tracer batch run validates against expected funding-rate-dispersion P&L envelope
todos: []
isProject: false
---

# ARBITRAGE_PRICE_DISPERSION canonicalisation finalisation

> **🟡 IN-FLIGHT REFACTOR — paper-vs-live workflow maturity (folded into master Group F 2026-05-09)**: this plan's
> `funding-rate-dispersion` variant is half of the May-23 paper-mode evidence run (`pvl-p18a` in
> [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md) § "Folded paper-vs-live workflow maturity"
> — pairs with `carry_staked_basis`). **BE AWARE** when scoping Phase A (slot wiring) + Phase B (tracer): tracer must
> emit per-instrument progress events with mode tag (`OperationalMode` field per `pvl-p17d` instruction-envelope mode
> field), and the funding-rate-dispersion config must be paper-runnable end-to-end ≥3 days before May-23 cutover.
> Question doc:
> [`plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md`](../questions/paper_vs_live_workflow_maturity_2026_05_08.md).
> Codex SSOTs: [`codex/04-architecture/operational-modes.md`](../../codex/04-architecture/operational-modes.md) +
> [`codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md`](../../codex/09-strategy/architecture-v2/cross-cutting/archetype-paper-readiness.md).

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
| unified-trading-pm      | `codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:171-179`          | E     | Remove line redirecting funding-rate perp arb → `CARRY_BASIS_PERP` (circular ref)                          |
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

**Status**: 🟡 BLOCKED — waiting for Tab 2 to ship `arbitrage_structural/funding_rate_dispersion.py`

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
4. **Volatility-cap clamp → short-term realised-vol features (NOT 60-day).** Use `features-volatility-service`'s
   short-window outputs: `realized_vol_5` / `realized_vol_10` / `realized_vol_20` (5/10/20 bar annualized close-to-
   close, computed at
   [`features_volatility_service/calculators/realized_vol_calculator.py`](../../../features-volatility-service/features_volatility_service/calculators/realized_vol_calculator.py)).
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

| Commit | Status | sha                | Shipped                                                                                                              |
| ------ | ------ | ------------------ | -------------------------------------------------------------------------------------------------------------------- |
| 1      | ✅     | strategy-service@24f8494 | `dispersion_type` dispatcher + `BTC_FUNDING_RATE_DISPERSION` slot stub + `STRATEGY_CATEGORIES` row + dispatcher tests |
| 2      | ✅     | strategy-service@0b4ef0e | `arbitrage_structural/funding_rate_dispersion.py` helper module (5 exports + 25 unit tests)                          |
| 3      | ⬜     | _pending_          | Engine 8-step loop wire-in (`_on_tick_funding_rate_dispersion` consumes the helper) + integration tests              |

- [ ] [strategy-service] P1. Add the canonical BTC/USDT slot entry (ETH/USDT + SOL/USDT + top-10 enumeration ship in
      A.6) to `strategy-service/strategy_service/engine/strategies/v2/archetype_slot_resolver.py` per the existing
      pattern (e.g. after the current ARBITRAGE_PRICE_DISPERSION rows ~L225–L811). The slot wires the **6-venue
      universe** with dynamic best-long/best-short selection (NOT a fixed venue pair) + Layer 1 + Layer 2 knobs +
      sign-match entry filter + short-term-vol clamp; engine implements all 3 Layer 1 modes day 1:

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

- [ ] [strategy-service] P1. Slot consumed by `ArbitragePriceDispersionEngine` factory entry at
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

- [ ] [strategy-service] P1. **A.7 — verify `ArbitragePriceDispersionRankAllocator` handles multi-pair-per-slot**. Audit
      [`portfolio_allocator/archetypes.py:678,729`](../../../strategy-service/strategy_service/portfolio_allocator/archetypes.py#L678).
      With Layer 1 modes `top-k` / `all-above-threshold`, the engine surfaces N pairs per slot per cycle (not 1). The
      allocator must rank + weight across all (slot × pair) opportunities, not just (slot, 1-best-pair). Branch: -
      **(a)** Allocator already ranks at the (slot, opportunity) granularity — wire
      `weight_mode:       "spread-proportional"` + `max_capital_pct_per_slot: 40.0` + `max_capital_pct_per_pair: 25.0` +
      `rebalance_threshold_bps: 20.0` + a unit test exercising 3 slots × 3 pairs each = 9 opportunities ranked correctly
      across the 4 weight modes. - **(b)** Allocator only handles 1-opportunity-per-slot. Extend it to
      multi-opportunity-per-slot. Do NOT downgrade Layer 1 modes — operator direction is all 3 modes ship configurable
      from day 1.

      Tests: `tests/unit/test_arbitrage_price_dispersion_rank_allocator.py` covering all 4 weight modes
      (`spread-proportional` / `rank-proportional` / `winner-takes-all` / `equal-weight`) + per-slot + per-pair caps
      + rebalance-threshold-bps churn suppression.

- [ ] [strategy-service] P1. **Mode-coverage tests for the engine** —
      `tests/unit/test_arbitrage_price_dispersion_funding_rate_engine.py` exercises all 3 `pair_selection_mode` values
      (`single-best`, `top-k`, `all-above-threshold`) against a fixture with 6 mock venues + known funding rates + known
      mid prices. Asserts: correct pair count surfaced per mode; sign-match filter drops the right pairs; min-spread
      filter drops the right pairs; vol-cap clamp triggers when threshold breached; `SIGN_MISMATCH_SKIP` /
      `BELOW_MIN_SPREAD_SKIP` / `VOL_CAP_CLAMPED` trace events emitted in the right places.

- [ ] [strategy-service] P1. Tests:
      `tests/unit/test_archetype_slot_resolver.py::test_arbitrage_price_dispersion_funding_rate_slot_exists`. QG green.
      Commit + push.

- [ ] [VERIFY] P0. From within strategy-service repo:
      `grep -n "funding-rate-dispersion" strategy_service/engine/strategies/v2/archetype_slot_resolver.py` returns ≥ 1
      hit;
      `python -c "from strategy_service.engine.strategies.v2.factory import ARCHETYPE_TO_ENGINE; assert     StrategyArchetype.ARBITRAGE_PRICE_DISPERSION in ARCHETYPE_TO_ENGINE"`
      exits 0.

- [ ] [strategy-service] P1. **A.6 follow-up — multi-asset slot enumeration (BTC + ETH + SOL day 1, plus top-10
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
      clipped per asset.

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

- [ ] [strategy-service] P1. Create `strategy-service/scripts/trace_arbitrage_price_dispersion.py` modeled on
      `trace_carry_staked_basis.py`. Should accept: - `--mode batch|live` -
      `--start-date YYYY-MM-DD --end-date YYYY-MM-DD` -
      `--config-variant default|funding-rate-dispersion|cross-venue-spread` (default = `default`) -
      `--asset-group defi|cefi` (the archetype spans both per the slot taxonomy)

      The script runs the archetype's signal generation through the unified pipeline (per CLAUDE.md "Batch = Live")
      and emits per-fixture/per-day P&L + signal trace rows for operator inspection.

- [ ] [strategy-service] P1. Cross-reference: extend `trace_all_carry_archetypes.py` to optionally invoke
      `trace_arbitrage_price_dispersion.py` for the cross-venue funding-spread variant. Don't fold the dispersion tracer
      INTO the carry tracer — different families.

- [ ] [VERIFY] P0.
      `python strategy-service/scripts/trace_arbitrage_price_dispersion.py --mode batch     --start-date 2024-01-01 --end-date 2024-01-07 --config-variant funding-rate-dispersion --asset-group defi`
      runs to completion + emits non-empty CSV/parquet output.

- [ ] [strategy-service] P1. Tests: `tests/unit/test_trace_arbitrage_price_dispersion.py` — verify CLI flags accepted,
      dry-run path emits a header row, error path raises `SystemExit(2)` on missing required flag.

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

- [ ] [pnl-attribution-service] P1. Add `StrategyArchetype.ARBITRAGE_PRICE_DISPERSION` handling to the service's
      archetype-aware P&L aggregator. Today the service has zero `ARBITRAGE_PRICE_DISPERSION` references in
      `pnl_attribution_service/` source. Likely surfaces: - Per-archetype P&L bucket (alongside `CARRY_STAKED_BASIS`,
      etc.) - Per-config-variant breakdown (`funding-rate-dispersion` vs other variants) - Output path:
      `gs://pnl-attribution-{pid}/by_strategy/ARBITRAGE_PRICE_DISPERSION/...`

- [ ] [pnl-attribution-service] P1. Tests:
      `tests/unit/test_archetype_pnl.py::test_arbitrage_price_dispersion_attribution`. Verify P&L bucket exists +
      attributes correctly given mock fills.

- [ ] [VERIFY] P0. After tracer (Phase B) emits rows for the 1-week window:
      `gcloud storage ls gs://${PID}-pnl-attribution/by_strategy/ARBITRAGE_PRICE_DISPERSION/...` returns non-empty;
      sample probe of one row confirms `archetype="ARBITRAGE_PRICE_DISPERSION"` + `config_variant=...` columns
      populated.

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

- [ ] [PM-plan] P0. After Phases A+B+C+E all ship: re-check Stream B gate in
      [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
      § Gate (line 168-170). Workspace grep `rg 'leveraged_funding_arb' --type py --type md` returns only: - the source
      plan + this finalisation plan + the original issue doc (historical context) - codex doc historical references with
      explicit "renamed to ARBITRAGE_PRICE_DISPERSION" annotations - archive/\* commits (frozen historical state)

- [ ] [PM-plan] P0. Flip the 3 deferred Stream B sister todos (lines 175-188) + the codex circular-ref P0 (lines
      155-157) in defi_archetypes plan from `[ ]` to `[x]` with this plan's commit shas as evidence. Per CLAUDE.md
      "Commit + Push + Flip" HARD RULE Half 2, the flip ships in a `docs(plans):` PM commit referencing each phase's
      code commits. Archive defi_archetypes plan only if Streams A/C/D/E are also complete; otherwise leave active.

## Phase E — codex SSOT updates (per "Post-Plan-Phase Codex Audit" HARD RULE)

Phase E may run in parallel with Phases B/C (no upstream dependency on artefacts) but MUST land before Phase D.

- [ ] [codex] P0. Resolve circular cross-reference at
      [`codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md:171-179`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md):
      remove the line _"Funding-rate arbitrage between perp venues (bidirectional funding capture) — `CARRY_BASIS_PERP`
      (cross-venue mode)"_ from the "Not in this archetype" section. The 2026-05-07 operator decision sent
      funding-rate-spread-as-price-dispersion HERE (ARBITRAGE_PRICE_DISPERSION with `funding-rate-dispersion` config
      variant); the redirect to CARRY_BASIS_PERP is the legacy framing. Leave the paired authoritative claim in
      [`carry-basis-perp.md:138-139`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md) only. This
      closes the parent plan's pending P0 codex todo at line 155-157.

- [ ] [codex] P0. In the same `arbitrage-price-dispersion.md` "Example instances" section (after L159
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

- [ ] [codex] P1. Touch-check
      [`codex/09-strategy/architecture-v2/category-instrument-coverage.md § 11`](../../codex/09-strategy/architecture-v2/category-instrument-coverage.md):
      ensure the funding-rate-dispersion variant is enumerated under ARBITRAGE_PRICE_DISPERSION's coverage matrix.

- [ ] [VERIFY] P0.
      `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP'     codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns zero hits (the circular pointer is gone).
      `rg 'funding-rate-dispersion'     codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
      returns ≥ 1 hit.

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
    `rg 'CARRY_BASIS_PERP.*funding|funding.*CARRY_BASIS_PERP' codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`
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
| unified-trading-pm      | E     | `docs(codex): resolve arbitrage-price-dispersion ↔ carry-basis-perp circular ref`                  | n/a       |
| unified-trading-pm      | E     | `docs(codex): add funding-rate-dispersion example slot to ARBITRAGE_PRICE_DISPERSION`               | n/a       |
| unified-trading-pm      | D     | `docs(plans): close Stream B gate in defi_archetypes_canonicalisation`                              | n/a       |

**Commit cadence note** (per CLAUDE.md "Commit + Push + Flip Plan Checkboxes" HARD RULE Half 1): each row above is a
single shippable unit; commit + push per row, do not batch across rows. Plan-flip in this plan + parent plan ships in
the SAME logical unit as the code commit per Half 2.

## Deferred work after this plan ships (per CLAUDE.md "Plan Archival" HARD RULE)

All 6 open questions resolved 2026-05-09 → no operator-blocked deferrals. Carryover candidates:

| Phase / item                                   | Status                              | Successor / blocker                                                                                             |
| ---------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Phase A.6 — ETH/SOL slots + top-10 enumeration | `todo` (unblocked; ships post-A)    | Same plan; data-coverage probe + slot enumeration commits after BTC/USDT slot is green                          |
| Phase A.7 — allocator multi-pair verification  | `todo` (unblocked; ships post-A)    | Same plan; extend allocator only if branch (b) per A.7 audit                                                    |
| Live cutover dry-run (paper-trade integration) | `deferred-after-2026-05-23-cutover` | `master_to_live_defi_2026_05_23.md` Group F item 17 (paper-trade smoke) consumes this archetype's tracer output |

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

| Phase / item                          | Status as of 2026-05-09 PM   | Successor / blocker                                                                                                                                                       |
| ------------------------------------- | ---------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase A — strategy-service slot       | `helper-shipped`             | Tab 5 in-flight; Commit 1 (dispatcher + slot stub) at strategy-service@24f8494; remaining: helper module selection logic + 6 unit tests + A.6 multi-asset + A.7 allocator |
| Phase B — tracer script               | `blocked-after-Phase-A.2`    | Tab 5 ongoing per Phase A.2 (helper module). Tracer ships once selection logic exists                                                                                     |
| Phase C — pnl-attribution archetype   | `blocked-after-Phase-B`      | Real-infra run consumes tracer output for 2024 W1 window; Plans-Run-To-Actual-Completion HARD RULE forbids smoke-only ship                                                |
| Phase D — Stream B gate close         | `blocked-after-Phase-A/B/C`  | Codex P0 (L155-157 in parent plan) flipped this session at PM@5fe5eabd + parent-plan annotation commit; full gate close awaits A/B/C completion                           |
| Phase E — codex SSOT updates          | `done` (PM@5fe5eabd shipped) | n/a — codex circular ref resolved + funding-rate-dispersion example slot enumerated in both arbitrage-price-dispersion.md + category-instrument-coverage.md § 11          |

Cross-plan items NOT addressed this session (still open in their own plans-of-record):

- **Workspace-wide `leveraged_funding_arb` rename sweep**: per Stream B gate, several active plans (defi_master,
  master_to_live_defi_2026_05_23, instruments_live_master, strategy_and_dart_master, live_pipeline_mtds_mdps_features)
  + question docs reference `leveraged_funding_arb` as a standalone archetype name. Filed as case-3 finding in
  [`plans/active/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md`](issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md)
  for owner triage.

## DONE-2026-05-09 (agent-arb-fundrate-cde)

Session: Phase E (codex SSOT updates) shipped end-to-end; Phase D partial (codex P0 flipped, full gate close blocked on
Phases A/B/C); Phase C blocked on Tab 5 tracer (per "Plans Run To Actual Completion" HARD RULE — no smoke-only ship).

Code commits:

- PM@5fe5eabd — `docs(codex): resolve arbitrage-price-dispersion ↔ carry-basis-perp circular ref + add
  funding-rate-dispersion example slots`. Edited 2 codex files: removed the circular CARRY_BASIS_PERP redirect from
  `arbitrage-price-dispersion.md` § "Not in this archetype"; added the canonical funding-rate-dispersion example slot
  pair (BTC + ETH USDT) with operator-confirmed config block to `arbitrage-price-dispersion.md` § "Example instances";
  added the same canonical multi-venue slot shape to `category-instrument-coverage.md` § 11 Representative slot_labels.
  Both verify gates pass: zero hits for the circular regex; ≥1 hit for `funding-rate-dispersion`.

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

- `plans/active/issues/leveraged_funding_arb_workspace_rename_sweep_2026_05_09.md` — workspace `rg
  'leveraged_funding_arb' --type py --type md` returns matches across ~5 active plans + question docs that use the
  legacy name as a standalone archetype label. Per Stream B gate, these need rename to `ARBITRAGE_PRICE_DISPERSION`
  (with `funding-rate-dispersion` config variant) or annotation as historical context. Owner triage required because
  the references span multiple plan-of-record owners.

EOD-audit: every deferral in the scoreboard above has a grep-target — Q1 (this plan body), Phase A/B/C/D (this plan
body), workspace rename sweep (issue doc cited above). No grep-miss deferrals.

## Cross-references

- [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
  — Stream B parent (this plan is the named successor for the 3 deferred sister todos + the lingering codex P0)
- [`defi_master_2026_05_07.md`](defi_master_2026_05_07.md) — master archetype owner; L152-153 already uses
  `ARBITRAGE_PRICE_DISPERSION` per 2026-05-08 rename
- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — May-23 cutover master; this plan unblocks
  the `ARBITRAGE_PRICE_DISPERSION` half of the "2 DeFi archetypes live" deliverable
- UAC `unified_api_contracts/internal/architecture_v2/enums.py:68` — SSOT enum entry (already shipped 2026-05-07)
- [`codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
  — codex SSOT updated by Phase E
- [`codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md)
  — paired authoritative claim survives here after Phase E circular-ref fix
