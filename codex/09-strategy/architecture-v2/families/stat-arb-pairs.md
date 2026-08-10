---
doc_type: codex-ssot
title: "Family: Stat Arb / Pairs"
summary:
  The Stat Arb / Pairs strategy family — 2 archetypes (fixed cointegration-tested basket vs dynamic cross-sectional
  ranking) trading a mean-reverting statistical spread; edge is spread z-score reversion with cointegration-p-value kill
  switches. Has spread risk (unlike risk-free price-dispersion arb).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, stat-arb, pairs, ml, execution, tradfi]
related:
  [
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
    ../archetypes/stat-arb-pairs-fixed.md,
  ]
created: 2026-04-17
authoritative_for: [Stat Arb / Pairs strategy family spec (alpha thesis + 2 archetypes)]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/stat-arb-cross-sectional.md,
    /codex/09-strategy/architecture-v2/archetypes/stat-arb-pairs-fixed.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/ml-directional.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: Stat Arb / Pairs

> **Alpha source:** Statistical spread between two or more underlyings that mean-reverts (or trends) against a
> historical relationship. Unlike price-dispersion arbitrage (which is risk-free), Stat Arb has spread risk — the
> relationship can break — and is statistically, not mechanically, profitable.
>
> **Primary edge method:** Spread z-score mean-reversion (or less commonly, spread momentum / divergence).
>
> **Typical hold policies:** HOLD_UNTIL_FLIP (close when spread reverts to entry band).
>
> **Archetype count:** 2 — distinguished by basket selection logic (fixed basket vs dynamic ranking).

## Alpha thesis

Stat Arb captures a _statistical relationship_ between underlyings that holds on average but dislocates from time to
time. We go long the underperformer + short the outperformer when the spread has deviated sufficiently from its
historical mean, expecting convergence.

Two fundamentally different basket selection approaches:

- **Fixed basket**: predetermined pairs or groups (e.g., GOOG-META, ES-NQ, BTC-ETH, XLE-SPY). Relationship is
  cointegration-tested or historically beta-stable. Positions are fixed members for the life of the strategy.
- **Cross-sectional**: dynamic basket — rank all assets in a universe by a signal (e.g., cross-sectional ML model), long
  top-N / short bottom-N. Members rotate as rankings shift.

These are different enough to warrant separate archetypes but share family primitives (paired legs, hedge ratio,
portfolio-level risk management).

**Not in this family:**

- Basis trading (spot vs same-underlying futures/perp) → Carry & Yield
- Price dispersion arb (same instrument, different venues) → Arbitrage / Structural
- Single-asset directional ML (no paired hedge) → ML Directional
- Portfolio of N independent ML strategies weighted by allocator → not one strategy; multiple ML Directional instances +
  Allocator

## 2 Archetypes

| Archetype                                                               | Basket selection                                                     | When to use                                                                     |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| [`STAT_ARB_PAIRS_FIXED`](../archetypes/stat-arb-pairs-fixed.md)         | Predetermined basket; cointegration-tested or historical-beta-stable | Long-term stable relationships — sector pairs, cross-index, crypto majors pairs |
| [`STAT_ARB_CROSS_SECTIONAL`](../archetypes/stat-arb-cross-sectional.md) | Dynamic — ranking-based, members vary                                | Universe ranking (Russell 1000 daily, crypto top-50 hourly); members rotate     |

## Shared primitives (both archetypes)

- **Spread computer**: given paired underlyings + hedge ratio, compute the spread (dollar-neutral, ratio, or
  cointegration residual)
- **Hedge-ratio estimator**: rolling OLS, Kalman filter, or cointegration vector estimation
- **Z-score monitor**: spread z-score against rolling mean ± std; entry on |z| > threshold; exit on |z| back to ≤
  threshold
- **Cointegration tester**: Engle-Granger or Johansen test (for FIXED); p-value rolling window, alert when p-value
  degrades
- **Paired leg tracker**: track both legs' positions; ensure dollar-neutral (or beta-neutral) at all times
- **Atomic multi-leg execution**: enter/exit both legs simultaneously via ATOMIC or near-atomic with tight timing
- **Spread mean-reversion / momentum classifier**: for mixed regimes (long when reverting, short when trending away
  further)

## Typical signal sources

| Signal                           | Source                                                                 |
| -------------------------------- | ---------------------------------------------------------------------- |
| Spread z-score                   | Computed continuously from pair prices + hedge ratio                   |
| Cointegration p-value            | Rolling Engle-Granger / Johansen                                       |
| Kalman-filter state              | Rolling hedge ratio + residual                                         |
| Cross-sectional rank             | ML model (for CROSS_SECTIONAL) ranking all universe members            |
| Factor exposure                  | Factor model (value, size, momentum, quality, vol) for cross-sectional |
| Sector / industry classification | Reference data (for constraining baskets to same sector)               |

## Typical edge methods

- **Z-score threshold**: enter when |z| > 2.0; exit at |z| ≤ 0.3 (configurable)
- **Half-life filter**: only trade spreads with Ornstein-Uhlenbeck half-life < threshold (fast enough to capture)
- **Cointegration-confirmed**: only trade when cointegration p-value remains stable
- **Cross-sectional ranking edge**: rank all N members; long top-M / short bottom-M (where M = basket size)

## Position structure

- **Paired fixed**: two positions — long leg and short leg — with dollar-neutral or beta-neutral sizing
- **Paired cross-sectional**: basket of long positions + basket of short positions; members may rotate each rebalance

## Typical staking methods

| Method                           | When used                                                  |
| -------------------------------- | ---------------------------------------------------------- |
| Dollar-neutral paired            | Equal notional on both legs                                |
| Beta-neutral paired              | Hedge ratio-weighted (typically β × notional)              |
| Cointegration-weighted           | Use cointegration vector for exact residual neutralization |
| Allocation-split cross-sectional | Equal weight across basket members OR rank-weighted        |
| Kelly per pair                   | For fixed pairs with reliable historical edge              |

## Venue patterns

- **Equity pairs**: IBKR (NYSE/NASDAQ/LSE via routing)
- **Index pairs**: CME futures (ES-NQ, ES-RTY)
- **Crypto pairs**: Binance / Bybit / OKX (same or cross-CEX for paired crypto legs)
- **Cross-asset**: IBKR + CME for oil-SPY etc.
- **Vol pairs**: Deribit options (cross-asset vol ratio)
- **Cross-sectional universe**: IBKR (equities), Binance / OKX (crypto top-N), same venue per-universe

## Expression options

- Spot (equities, crypto spot)
- Futures (index, commodity)
- Perp (crypto, for same-effective exposure without expiry management)
- Options (vol pairs)

Both legs can have same or different expression (long GOOG stock + short META stock; long BTC spot + short ETH perp;
etc.).

## Risk profile

- **Drawdowns**: spread-risk drawdowns when relationship breaks (e.g., cointegration fails, one leg diverges
  permanently)
- **Tail risks**:
  - Cointegration structural break (rare but severe; e.g., M&A on one of the pair members)
  - Liquidity asymmetry (one leg can't be closed without large slippage)
  - Factor reversal (in cross-sectional, factor regime change)
- **Sharpe (well-run stat arb)**: 1.0–2.5. Structural-break events (cointegration failure) produce the tail and warrant
  p-value kill switches.
- **Kill switches**: cointegration p-value breach (relationship broken), one-leg liquidity collapse, extreme z-score
  without reversion after hold period

## Latency Requirements

**Category: `Low`** — sub-second total E2E, live mode only (batch mode has no latency requirements; it replays
historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table — SUPERSEDED as a doc, but its **Statistical Arb** row (`< 100 ms` tick-to-signal / `< 100 ms` signal-to-order /
venue-dep. fill / `< 200 ms` total E2E, `Low`) is the operative baseline and is **confirmed, not corrected**, here: the
2026-08-10 operator correction (arbitrage-based archetypes must be in the ms realm) agrees with — rather than changes —
the archived doc's existing `Low` categorization.
[`arbitrage-structural.md`](/codex/09-strategy/architecture-v2/families/arbitrage-structural.md) § "Latency
Requirements" already notes this family shares that same archived Statistical Arb row as its baseline; this family's own
content carries the execution-side facts those numbers imply — the **Atomic multi-leg execution** shared primitive
("enter/exit both legs simultaneously via ATOMIC or near-atomic with tight timing") and the `execution_policy_ref`
("paired execution preference, e.g. leader-lagger for cross-venue") — so nothing here contradicts a sub-second budget.

| Expression                                                                         | Tick-to-Signal | Signal-to-Order | Order-to-Fill | Total E2E | Category |
| ---------------------------------------------------------------------------------- | -------------- | --------------- | ------------- | --------- | -------- |
| Fixed pairs, same-venue (equity pairs IBKR, index pairs CME, crypto pairs one CEX) | < 100 ms       | < 100 ms        | Venue-dep.    | < 200 ms  | Low      |
| Fixed pairs, cross-venue / cross-asset (crypto cross-CEX legs, IBKR + CME CL-ES)   | < 200 ms       | < 100 ms        | Venue-dep.    | < 300 ms  | Low      |
| Cross-sectional baskets (universe ranking, long / short baskets)                   | < 200 ms       | < 100 ms        | Venue-dep.    | < 300 ms  | Low      |

The cross-venue row borrows the archived **Cross-Exchange Arb** row's `< 300 ms` E2E as its decision ceiling — the legs
are two different underlyings on two different venues, so there is no venue-side atomicity to lean on. The
cross-sectional row's tick-to-signal is dominated by the **ranking-model leg** (cross-sectional ML ranks the universe),
and its decision cadence is rank-update-driven (crypto top-N hourly, Russell 1000 daily per the Typical instance
examples) rather than tick-driven — the `< 200 ms` figure applies to the execution-emission path once a rotation fires,
not to signal detection on every tick.

**Deployment implication:** `Low` ⇒ the `co_located_vm` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping (bundled services on one VM for low-latency handoff), matching the market-making
and arbitrage-structural families' derivation. Note this is NOT yet reflected in
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6's `STAT_ARB_PAIRS` `topology_requirements` row (execution isolated / strategy shared OK / co-location `no` / min SLA
`standard`), which predates this latency categorization — that row's `no` co-location + `standard` SLA tier conflicts
with the Low→`co_located_vm` rubric, a discrepancy this audit surfaces for the derivation todo that writes
`/codex/04-architecture/RUNTIME_TOPOLOGY_DECISIONS.md`.

### Decision latency vs. inter-leg execution gap

The `< 200–300 ms` figures above are the **decision budget** — dislocation detected (spread z-score crossing the entry
band) → a single paired instruction emitted. They are NOT the whole requirement. For this family the binding constraint
is the **inter-leg execution gap** (2026-08-10 operator ruling: "we are executing two legs of a trade... how are we
ensuring the lag leg followed by the lead leg is ms timing"), and the expressions split into two very different risk
surfaces:

- **Same-venue pairs / ATOMIC**: both legs enter on the same venue (equity pairs on IBKR, index pairs on CME, crypto
  pairs on one CEX), so the **Atomic multi-leg execution** primitive bounds the gap — enter/exit both legs
  simultaneously, ATOMIC or near-atomic with tight timing. There is no measurable cross-venue gap; the binding budget is
  the decision latency (`< 200 ms` per the archived Statistical Arb row).
- **Cross-venue / cross-asset pairs — the real risk surface**: two legs on **two different venues** (crypto cross-CEX
  pairs, CL-ES on IBKR + CME), and no venue supports a simultaneous cross-CEX fill, so execution runs leader-lagger —
  the lead leg fills on venue A, the lag leg chases on venue B (the `execution_policy_ref`'s "paired execution
  preference, e.g. leader-lagger for cross-venue"). The gap between the lead fill and the lag follow is where the edge
  lives or dies: if the lag leg falls beyond ms timing the spread can converge, or one leg can partially fill leaving a
  naked directional position on a single underlying — the partial-fill / one-leg liquidity-collapse tail risk the Risk
  profile section warns about. The operating target is ms-realm (well under 100 ms).
- **Cross-sectional baskets**: when a rank rotation fires, the long-basket and short-basket legs must move together — a
  rotation gap leaves the old and new baskets misaligned mid-transition. Same-venue-per-universe (IBKR equities, one CEX
  per crypto universe) keeps the rotation near-atomic; a cross-venue universe inherits the leader-lagger surface above.

So for Stat Arb / Pairs, "Low" means the **inter-leg execution timing budget is ms-realm for every cross-venue /
leader-lagger expression**, while same-venue ATOMIC pairs are bounded by the (still sub-second) decision budget.

## UI dashboard (shared)

- Spread time series with entry/exit bands
- Z-score distribution per pair (or cross-sectional aggregate)
- Hedge-ratio stability (Kalman trace)
- Cointegration p-value rolling (for FIXED)
- Factor exposure breakdown (for CROSS_SECTIONAL)
- Leg-by-leg P&L attribution
- Per-pair (or per-basket) accuracy

## Required subscriptions

Config references:

- **instrument_pair_refs** (for FIXED) or **universe_ref** (for CROSS_SECTIONAL)
- **hedge_ratio_model_ref** — Kalman / OLS / cointegration-vector model
- **feature_group_refs** — price / return features per underlying
- **ranking_model_ref** (for CROSS_SECTIONAL only)
- **execution_policy_ref** — paired execution preference (e.g., leader-lagger for cross-venue)

## Typical instance examples

```
Fixed pairs — equities:
  STAT_ARB_PAIRS_FIXED@ibkr-goog-meta-daily-usd-prod
  STAT_ARB_PAIRS_FIXED@ibkr-aapl-msft-daily-usd-prod
  STAT_ARB_PAIRS_FIXED@ibkr-xle-spy-daily-usd-prod         (sector vs index)

Fixed pairs — index:
  STAT_ARB_PAIRS_FIXED@cme-es-nq-daily-usd-prod
  STAT_ARB_PAIRS_FIXED@cme-es-rty-daily-usd-prod

Fixed pairs — crypto:
  STAT_ARB_PAIRS_FIXED@binance-btc-eth-1h-usdt-prod
  STAT_ARB_PAIRS_FIXED@binance-btc-sol-1h-usdt-prod
  STAT_ARB_PAIRS_FIXED@binance-eth-sol-1h-usdt-prod

Fixed pairs — cross-asset:
  STAT_ARB_PAIRS_FIXED@cme-cl-es-daily-usd-prod            (crude vs S&P)

Fixed pairs — vol (implemented as vol ratio between instruments):
  STAT_ARB_PAIRS_FIXED@deribit-btc-eth-vol-1h-usdt-prod

Cross-sectional:
  STAT_ARB_CROSS_SECTIONAL@ibkr-russell1000-daily-usd-prod
  STAT_ARB_CROSS_SECTIONAL@ibkr-sp500-daily-usd-prod
  STAT_ARB_CROSS_SECTIONAL@multi-cex-top50-crypto-1h-usdt-prod
  STAT_ARB_CROSS_SECTIONAL@multi-cex-top50-crypto-daily-usdt-prod
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    self.target_notional_per_pair = new_equity_usd * self.config.allocation_pct_per_pair
    # For cross-sectional: scale all basket members proportionally
    # For fixed: scale each pair's notional
    return self._rescale_positions()
```

## Rebalancing triggers

- Spread z-score crosses entry band → enter paired position
- Spread z-score crosses exit band → close paired position
- Cointegration p-value breach → exit and halt trading on that pair
- Rank change (cross-sectional) → rotate basket members: close exiting legs, open new legs
- Equity change → rescale paired positions

## Migration from legacy docs

| Legacy                                           | Mapping                    | Notes                          |
| ------------------------------------------------ | -------------------------- | ------------------------------ |
| Code: `strategy-service/.../rel_vol_btc_eth.py`  | `StatArbPairsFixedEngine`  | Vol-pair variant               |
| Code: `strategy-service/.../stat_arb_btc_eth.py` | `StatArbPairsFixedEngine`  | Crypto price-spread            |
| (No legacy doc for cross-sectional)              | `STAT_ARB_CROSS_SECTIONAL` | New archetype introduced in v2 |

No dedicated legacy docs — stat arb was primarily a code-level concept. v2 formalizes the family + two archetypes.

## Cross-references

- Archetypes: [stat-arb-pairs-fixed](../archetypes/stat-arb-pairs-fixed.md),
  [stat-arb-cross-sectional](../archetypes/stat-arb-cross-sectional.md)
- Paired-leg execution (leader-lagger policy):
  [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
- Cross-sectional ML signal source: [../axes/signal-sources.md](../axes/signal-sources.md)
- Portfolio of independent ML strategies (vs cross-sectional):
  [../cross-cutting/portfolio-allocator.md](../cross-cutting/portfolio-allocator.md) — Allocator-weighted multiple ML
  instances, not cross-sectional
