---
doc_type: codex-ssot
title: "Family: Vol Trading"
summary:
  The Vol Trading strategy family — 19 archetypes trading a view on vol itself (IV/RV, skew, term structure, surface
  residuals, dispersion, variance) via delta-hedged options; edge is statistical vol-metric dislocation, distinct from
  mechanical cross-venue/no-arb vol dispersion which belongs in ARBITRAGE_PRICE_DISPERSION.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, vol-trading, options, deribit, defi, execution]
related:
  [
    /codex/09-strategy/architecture-v2/families/market-making.md,
    /codex/09-strategy/architecture-v2/families/stat-arb-pairs.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    ../archetypes/vol-trading-options.md,
    ../cross-cutting/risk-gates.md,
  ]
created: 2026-04-17
authoritative_for: [Vol Trading strategy family spec (alpha thesis + 19 archetypes)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-gamma-scalping.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-0dte-pin-risk.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-arb-rv-iv.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-carry.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-cross-asset-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/vol-leaps-convexity.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: Vol Trading

> **Alpha source:** Volatility-metric dislocation. Alpha is a view on _vol itself_ (IV vs RV, skew, term structure,
> cross-asset vol) — not a directional view on the underlying. Baseline positions are delta-hedged; P&L comes from vega,
> gamma, and theta. Variants may carry intentional delta, flagged in the strategy config.
>
> **Primary edge method:** Vol-metric dislocation vs fair (IV too rich/cheap vs realized; skew extreme vs historical;
> term structure bowed beyond no-arb bounds).
>
> **Hold policies:** CONTINUOUS (dynamic gamma scalping + vega exposure management) or HOLD_UNTIL_FLIP (event-bounded
> vol trades).
>
> **Archetype count:** 19 — `VOL_TRADING_OPTIONS` (legacy catch-all, retained for back-compat) + 18 granular variants
> added in the Phase 9 expansion (2026-04-25). SSOT: UAC `StrategyArchetype` (`enum-wins` governance rule per
> `strategy-summary.md:27`).

## Alpha thesis

Vol Trading captures alpha from volatility metrics dislocating from historical or model-implied norms. Key sub-patterns:

- **IV vs RV**: implied vol (market's forward expectation) diverges from realized vol (historical / recent) — long /
  short vol accordingly. Statistical view; not risk-free.
- **Skew dislocation** (soft): 25d put skew rich vs historical → sell puts / buy calls (risk reversal). Directional view
  on skew mean-reverting; not a no-arb violation.
- **Term structure** (soft): front-month IV richer than back-month vs typical carry-adjusted shape → calendar trades.
  Directional view; not a no-arb violation.
- **Soft surface residuals**: fitted IV surface (e.g., SVI) has residuals at specific strikes that suggest a strike is
  rich/cheap vs model-fair, but does NOT violate no-arb bounds. Directional view that the residual re-equilibrates.
- **Cross-asset vol (pair)**: BTC vol / ETH vol outside historical band → pair (but if this is the alpha source, this
  sits in Stat Arb / Pairs family as a vol-pair instance)

**Belongs in [`ARBITRAGE_PRICE_DISPERSION`](../archetypes/arbitrage-price-dispersion.md), NOT here:**

- Cross-venue vol arb (same option / same strike / same expiry quoted at different IVs on two venues, e.g., Deribit vs
  OKX options) — mechanical dispersion of the same instrument.
- Hard no-arb violations within a single venue's surface (butterfly convexity violation, calendar arbitrage where
  front > back beyond carry, put-call parity violations) — mechanical, near-risk-free.

**The distinguishing test:** is the edge _mechanical_ (guaranteed conditional on correct execution; cross-venue
same-option dispersion or a no-arb bound violation) or _statistical_ (profitable on average with spread risk; vol metric
expected to mean-revert)? Mechanical → Arbitrage. Statistical → Vol Trading.

Delta-hedged implementation is essential: the strategy takes a vol view, not a directional view. Delta hedging removes
directional exposure (or maintains a specific delta target).

**Not in this family:**

- Directional option trade (long call because bullish BTC) → ML Directional with options expression
- MM on options (earn spread, no vol view) → Market Making
- Options MM on vol mispricing (vol edge is primary alpha, spread capture secondary) → Vol Trading (this family)
- Cross-asset vol ratio mean-reversion → Stat Arb / Pairs (vol-pair variant)

## 19 Archetypes

The 2026-04-17 baseline shipped a single catch-all (`VOL_TRADING_OPTIONS`), on the theory that one engine (surface
fitter + dislocation detector + delta-hedge + greeks management) covers every vol pattern as config. The Phase 9
expansion (2026-04-25) split that into 18 explicit code paths because the distinct vol expressions diverge materially in
position construction, roll/expiry handling, sizing semantics, latency profile, and risk gates — too much to keep as one
engine's config branches. `VOL_TRADING_OPTIONS` is retained as the legacy back-compat value for old Firestore/GCS
records; new strategies use the granular variants.

| Archetype                                                                   | Vol expression / edge                                                               | Settlement / hold             |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | ----------------------------- |
| [`VOL_TRADING_OPTIONS`](../archetypes/vol-trading-options.md) _(legacy)_    | Catch-all single-venue vol trading (IV/RV, skew, term, surface) pre-Phase-9 split   | Continuous                    |
| [`VOL_ARB_RV_IV`](../archetypes/vol-arb-rv-iv.md)                           | Times IV−RV spread breakdowns (mean-reversion in the gap); long or short vol        | Continuous, rolled at expiry  |
| [`VOL_SPREAD_STRUCTURES`](../archetypes/vol-spread-structures.md)           | Calendar + butterfly spreads on term-structure shape and smile; vega-neutral entry  | Expiry-driven per leg         |
| [`VOL_CARRY`](../archetypes/vol-carry.md)                                   | Harvests structural IV-over-RV premium by selling short-tenor options (theta)       | Continuous, roll at expiry    |
| [`VOL_OVERLAY_COVERED_CALLS`](../archetypes/vol-overlay-covered-calls.md)   | Writes OTM calls against an existing delta-1 long for premium income                | Expiry-driven, rewrite/roll   |
| [`VOL_OVERLAY_PROTECTIVE_PUT`](../archetypes/vol-overlay-protective-put.md) | Buys OTM puts (or collar) as tail-risk insurance on a delta-1 long                  | Expiry-driven, rolled         |
| [`VOL_STRADDLE`](../archetypes/vol-straddle.md)                             | Long/short ATM straddle for a pure vol view around catalysts or IV extremes         | Event-driven or expiry        |
| [`VOL_SYNTHETIC_DELTA`](../archetypes/vol-synthetic-delta.md)               | Replicates delta-1 via long call + short put (avoids perp funding; defined risk)    | Expiry-driven, rolled         |
| [`VOL_MARKET_MAKING`](../archetypes/vol-market-making.md)                   | Two-sided options quoting with vol edge primary; SVI fair-value, hedged inventory   | Continuous quote lifecycle    |
| [`VOL_ML_LEAN`](../archetypes/vol-ml-lean.md)                               | ML-forecast RV vs IV tilts vol position size and direction                          | Continuous, rolled at expiry  |
| [`VOL_0DTE_GAMMA_SCALPING`](../archetypes/vol-0dte-gamma-scalping.md)       | Buys 0DTE straddles; captures realised gamma via frequent intraday delta-hedge      | Same-day expiry               |
| [`VOL_0DTE_PIN_RISK`](../archetypes/vol-0dte-pin-risk.md)                   | Manages extreme near-expiry gamma/pin risk at high-OI strikes (carry/flatten/roll)  | Same-/next-day expiry         |
| [`VOL_TERM_STRUCTURE_ARB`](../archetypes/vol-term-structure-arb.md)         | Dual-expiry calendar on term-structure slope z-score mean-reversion                 | Dual-expiry calendar          |
| [`VOL_TERM_STRUCTURE_SLOPE`](../archetypes/vol-term-structure-slope.md)     | Trades the fitted term-structure slope parameter (front vs back); continuous roll   | Continuous, rolling expiry    |
| [`VOL_DISPERSION`](../archetypes/vol-dispersion.md)                         | Short index vol / long component vol; harvests implied-vs-realised correlation      | Continuous, multi-expiry      |
| [`VOL_VARIANCE_SWAP`](../archetypes/vol-variance-swap.md)                   | Replicates a variance swap via a 1/K² option strip + daily delta hedge              | Expiry-driven                 |
| [`VOL_LEAPS_CONVEXITY`](../archetypes/vol-leaps-convexity.md)               | Long long-dated (180d+) options for cheap convexity; asymmetric vol-spike payoff    | Expiry-driven, quarterly roll |
| [`VOL_CROSS_ASSET_SPREAD`](../archetypes/vol-cross-asset-spread.md)         | Trades the vol spread between correlated assets (e.g. BTC/ETH IV) at matched tenors | Continuous, matched expiries  |
| [`VOL_RATIO_SPREAD`](../archetypes/vol-ratio-spread.md)                     | Ratio spread (e.g. 1×2) harvesting rich OTM skew premium; net-credit entry          | Expiry-driven                 |

The shared primitives below (surface fitter, RV computer, greeks + delta-hedge engine, vol-trade constructors,
expiry/time-decay manager) are common to all 19 — each archetype is a distinct composition of them plus its own
entry/exit logic and risk gates.

## Shared primitives

- **IV surface fitter**: fit SVI / SSVI / arbitrage-free surface to current market option prices; residuals =
  dislocations
- **Realized vol computer**: rolling RV estimators (close-to-close, Parkinson, Garman-Klass, Yang-Zhang)
- **Greeks computer**: delta, gamma, vega, theta, rho per position + portfolio-level
- **Delta-hedge engine**: dynamic hedging via underlying (spot, perp, future); configurable hedge band + frequency
- **Gamma-scalping engine**: long gamma strategies harvest realized vol by rehedging as underlying moves
- **Vol-trade constructors**: straddle, strangle, butterfly, calendar, risk reversal, skew trades — reusable payoff
  primitives
- **Expiry / time-decay manager**: close positions before ultra-short-expiry gamma spike; roll calendars at expiry
- **Cross-underlier correlation tracker** (for cross-asset vol)

## Typical signal sources

| Signal                                          | Source                                |
| ----------------------------------------------- | ------------------------------------- |
| IV surface grid                                 | Deribit mark IV per (strike, expiry)  |
| Realized vol                                    | Tick/minute history of underlying     |
| IV / RV ratio                                   | Computed continuously                 |
| Skew (25d put IV - 25d call IV)                 | Surface fitter output                 |
| Term structure (front vs back month)            | Surface fitter output                 |
| Put-call ratio                                  | Option flow feed                      |
| Historical vol percentiles                      | Rolling 90d / 1y histograms           |
| Event-upcoming indicator (for vol-event trades) | Event calendar + vol-surface reaction |

## Typical edge methods

- **IV/RV divergence**: `|IV - RV| > threshold` and persistent across observation window
- **Skew percentile extreme**: current skew < 5th or > 95th historical percentile
- **Term structure inversion**: front > back beyond no-arb + carry bounds
- **Soft surface residual**: per-strike IV residual from fitted surface > fit error threshold, but WITHIN no-arb bounds
  (statistical bet on residual re-equilibrating). Hard no-arb violations belong in `ARBITRAGE_PRICE_DISPERSION`.
- **Vol regime prediction**: ML-classified "vol expanding" or "vol contracting" state

## Position structure

- Option positions (long or short depending on vol view)
- Underlying hedge (delta-neutral by default; can target non-zero delta if strategy includes directional overlay)
- Multi-leg: straddles, strangles, butterflies, calendars, risk reversals
- Rolling: positions replaced before expiry, calendars rolled at front-month expiry

## Typical staking methods

| Method              | When used                                                                  |
| ------------------- | -------------------------------------------------------------------------- |
| Vega-notional cap   | Default — limit total vega exposure relative to equity                     |
| Gamma-notional cap  | Complementary — limit convexity exposure                                   |
| Notional-scaled     | Similar to cash-and-carry, scale with equity proportionally                |
| Scenario-PnL-capped | Limit worst-case P&L under scenario grid (e.g., ±10% move × ±20% IV shift) |

## Venue patterns

- **Deribit**: primary crypto options (BTC, ETH); portfolio margin available; tight spreads on ATM
- **CBOE**: SPY options (US equity index); via IBKR routing
- **CME**: options on futures (ES options, CL options, etc.); dated expiries
- **OKX options** (secondary): backup or for specific strikes

## Expression options

- Straddle (ATM long/short) — pure vol expression
- Strangle (OTM long/short) — cheaper pure vol with wider breakeven
- Butterfly — pure convexity view
- Calendar (buy back-month / sell front-month) — term structure view
- Risk reversal (sell put / buy call or vice versa) — skew view
- Iron condor / iron butterfly — spread combinations
- Delta-hedged single leg (e.g., long call, hedged) — gamma-scalping, vol-long

## Risk profile

- **Drawdowns**: can be sharp during vol explosions (short vol blown up); well-managed long vol is rarely catastrophic
- **Tail risks**:
  - Short vol regime change (VIX-style explosion)
  - Deribit settlement mechanics (perpetual vs dated)
  - Liquidity drying up on far OTM strikes
  - Cross-expiry roll timing (calendar P&L jumps on roll)
- **Sharpe**: wide range; well-executed vol strategies 1.5-3.0
- **Kill switches**: vol spike > N × regime, position greeks breach, IV > configured ceiling (indicates regime
  disruption)

## Latency Requirements

**Category: `Medium`** — seconds-scale decision cycle, live mode only (batch mode has no latency requirements; it
replays historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table — SUPERSEDED as a doc, but its **Volatility Arb** row (Tick-to-Signal <10 s / Signal-to-Order <5 s / Total E2E <15
s, Category **Medium**) is the operative baseline and is **confirmed, not corrected**, here. **Derivation reasoning**
(per the 2026-08-10 audit rubric at
[`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`](/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md)):
the operator's ms-realm ruling did NOT name vol-trading, so the family inherits the archived doc's closest analog —
Volatility Arb at Medium. The family's own content does not contradict that at the decision level: the dominant
archetypes (IV-vs-RV, skew, term-structure, surface-residual dislocations) fire off surface-fitter + RV-computer outputs
that update on a seconds-scale cadence, not a tick-to-signal race. The doc DOES indicate intra-family variance at the
_execution_ level — `VOL_MARKET_MAKING` (two-sided options quoting) and `VOL_0DTE_GAMMA_SCALPING` (frequent intraday
delta-hedge) sit closer to the market-making Low profile — but that is the inter-leg execution gap, not the decision
budget (see below).

| Segment         | Budget     | Notes                                                                                                                                                               |
| --------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tick-to-Signal  | < 10 s     | IV surface fit + realized-vol compute + dislocation detector → signal. Surface updates on quote/tick flow but the dislocation-threshold decision tolerates seconds. |
| Signal-to-Order | < 5 s      | StrategyInstruction → routing → algo → venue submit (option order construction + optional underlying hedge instruction).                                            |
| Order-to-Fill   | Venue-dep. | Deribit 15–40 ms order submission / 10–25 ms fill; CBOE FIX 2–8 ms (archived venue-baselines table). Not a budget we control.                                       |
| **Total E2E**   | **< 15 s** | Baseline: archived Volatility Arb row.                                                                                                                              |

**Deployment implication:** `Medium` ⇒ the `distributed` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping, referencing
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6. The current `topology_requirements` row for `VOL_TRADING` (execution `isolated`, strategy `shared OK`, co-location
`no`, min SLA `standard`) is **consistent** with a distributed profile — unlike the `Low` families, this is not a
discrepancy the derivation todo needs to resolve. It SHOULD, however, note the intra-family fast subset
(`VOL_MARKET_MAKING`, `VOL_0DTE_GAMMA_SCALPING`): those two behave like market-making and may warrant a
co-located/`premium` carve-out when instantiated, which the
[`/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md`](/plans/active/strategy_archetype_latency_deployment_profile_audit_2026_08_10.md)
deployment-derivation todo 8 should call out.

### Decision latency vs. inter-leg execution gap

The <15 s Medium figures are the **decision budget**. The separate binding constraint for the delta-hedged archetypes is
the **inter-leg execution gap** (2026-08-10 operator ruling: "we are executing two legs of a trade... how are we
ensuring the lag leg followed by the lead leg is ms timing"):

- **Delta-hedged option positions** (the family baseline): the option leg is the lead leg; the underlying delta-hedge
  (spot/perp/future) is the lag leg. The hedge must follow the option fill at ms timing — an unhedged delta left for
  seconds during a vol spike is exactly the gamma/pin risk the `VOL_0DTE_*` kill switches are built to contain. This
  makes the _inter-leg_ requirement for the delta-hedged majority ms-realm even though the _decision_ budget is
  seconds-scale — same structure as carry-and-yield (slow decision, fast legs), the difference being vol-trading's
  decision cadence is faster than carry's rates-driven cycle.
- **`VOL_MARKET_MAKING`**: two-sided options quoting + inventory delta-hedge — effectively market-making with a vol
  edge; inherits the MM family's <100 ms decision and ms-realm hedge timing
  ([`/codex/09-strategy/architecture-v2/families/market-making.md`](/codex/09-strategy/architecture-v2/families/market-making.md)).
- **`VOL_0DTE_GAMMA_SCALPING`**: captures realised gamma by frequent intraday delta-hedging — the hedge cadence IS the
  strategy; its inter-leg timing is the tightest in the family (sub-second re-hedge target, ms-realm gap).
- **`VOL_CROSS_ASSET_SPREAD` / `VOL_DISPERSION`**: multi-leg expressions (two correlated underliers / index-vs-
  components) — the legs are paired for correlation capture; inter-leg timing matters when rebalancing, though less
  tightly than a hedge-follows-fill.

So "Medium" for this family means a seconds-scale **decision** budget with an **ms-realm inter-leg execution** target
for the delta-hedged and MM-like archetypes — the derivation todo should keep the family at `distributed` while flagging
the fast subset for a potential `co_located_vm` carve-out.

## UI dashboard

- IV surface grid (with overlaid fitted surface)
- IV percentile rank per strike
- Realized vol rolling
- Current greeks + portfolio scenario P&L grid
- Delta-hedge event log (when + why hedged)
- Vol P&L attribution (vega, gamma, theta, delta-hedge-slippage)
- Surface residuals heatmap (for surface arb)

## Required subscriptions

Config references:

- **venue_capability_ref** (Deribit typically)
- **feature_group_refs** — IV surface, RV, historical vol percentiles
- **surface_model_ref** — fitted surface model artifact (SVI, SSVI)
- **vol_edge_model_ref** (optional) — ML model predicting IV/RV divergence
- **execution_policy_ref** — options-specific execution policy (iceberg for size, mid-price for tight spreads)

## Typical instance examples

```
Deribit BTC vol trading:
  VOL_TRADING_OPTIONS@deribit-btc-straddle-usdt-prod       (IV vs RV divergence)
  VOL_TRADING_OPTIONS@deribit-btc-skew-usdt-prod           (skew extreme)
  VOL_TRADING_OPTIONS@deribit-btc-surface-usdt-prod        (surface residuals)
  VOL_TRADING_OPTIONS@deribit-btc-calendar-usdt-prod       (term structure)

Deribit ETH vol trading:
  VOL_TRADING_OPTIONS@deribit-eth-straddle-usdt-prod
  VOL_TRADING_OPTIONS@deribit-eth-skew-usdt-prod
  VOL_TRADING_OPTIONS@deribit-eth-surface-usdt-prod

CBOE SPY vol:
  VOL_TRADING_OPTIONS@cboe-spy-vol-ml-usd-prod
  VOL_TRADING_OPTIONS@cboe-spy-gamma-scalping-usd-prod
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    self.max_vega_notional = new_equity_usd * self.config.max_vega_pct
    self.max_gamma_notional = new_equity_usd * self.config.max_gamma_pct
    return self._rescale_positions_to_vega_bound()
```

## Rebalancing triggers

- Delta drift > band → emit hedge TRADE on underlying
- IV surface changes → re-evaluate entries/exits
- New vol dislocation detected → enter new position
- Vol dislocation closes → exit position
- Expiry approaching → roll / close
- Equity change → rescale vega / gamma bounds

## Migration from legacy docs

| Legacy                                          | Mapping                                                                                                             | Notes                          |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `tradfi/options-ml.md`                          | `VOL_TRADING_OPTIONS` (if vol alpha) OR `ML_DIRECTIONAL_CONTINUOUS` (if delta alpha)                                | Config disambiguates           |
| `tradfi/market-making-options.md`               | `MARKET_MAKING_CONTINUOUS` (if spread-capture primary) OR `VOL_TRADING_OPTIONS` (if vol alpha primary)              | Config disambiguates           |
| Code: `strategy-service/.../options_ml_*.py`    | Split: delta-ML → `MLDirectionalContinuousEngine`, vol-ML → `VolTradingOptionsEngine`, strike-ML → depends on alpha | Per strategy                   |
| Code: `strategy-service/.../vol_surface_btc.py` | `VolTradingOptionsEngine`                                                                                           | Surface arb as vol edge method |

## Cross-references

- Archetypes (19): [vol-trading-options](../archetypes/vol-trading-options.md) _(legacy)_,
  [vol-arb-rv-iv](../archetypes/vol-arb-rv-iv.md), [vol-spread-structures](../archetypes/vol-spread-structures.md),
  [vol-carry](../archetypes/vol-carry.md), [vol-overlay-covered-calls](../archetypes/vol-overlay-covered-calls.md),
  [vol-overlay-protective-put](../archetypes/vol-overlay-protective-put.md),
  [vol-straddle](../archetypes/vol-straddle.md), [vol-synthetic-delta](../archetypes/vol-synthetic-delta.md),
  [vol-market-making](../archetypes/vol-market-making.md), [vol-ml-lean](../archetypes/vol-ml-lean.md),
  [vol-0dte-gamma-scalping](../archetypes/vol-0dte-gamma-scalping.md),
  [vol-0dte-pin-risk](../archetypes/vol-0dte-pin-risk.md),
  [vol-term-structure-arb](../archetypes/vol-term-structure-arb.md),
  [vol-term-structure-slope](../archetypes/vol-term-structure-slope.md),
  [vol-dispersion](../archetypes/vol-dispersion.md), [vol-variance-swap](../archetypes/vol-variance-swap.md),
  [vol-leaps-convexity](../archetypes/vol-leaps-convexity.md),
  [vol-cross-asset-spread](../archetypes/vol-cross-asset-spread.md),
  [vol-ratio-spread](../archetypes/vol-ratio-spread.md)
- Options MM distinction: [market-making.md](market-making.md) (spread capture as primary alpha)
- Cross-asset vol pair: [stat-arb-pairs.md](stat-arb-pairs.md) (if alpha is ratio mean-reversion)
- Greeks / risk: [../cross-cutting/risk-gates.md](../cross-cutting/risk-gates.md)
