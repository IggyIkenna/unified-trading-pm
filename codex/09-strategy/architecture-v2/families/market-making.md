---
doc_type: codex-ssot
title: "Family: Market Making"
summary:
  The Market Making strategy family — 10 archetypes (CeFi continuous/passive/inventory-skew/ML-lean/queue-micro,
  event-settled sports, prediction CLOB, + 3 DeFi LP variants); edge is bid-ask spread capture net of adverse selection,
  inventory risk, and fees. All LP (V3 concentrated, pool, ERC-4626 vault) lives here.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, market-making, defi, cefi, options, prediction, execution]
related:
  [
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/families/vol-trading.md,
    ../archetypes/market-making-continuous.md,
    ../archetypes/defi-lp-concentrated.md,
  ]
created: 2026-04-17
authoritative_for: [Market Making strategy family spec (alpha thesis + 10 archetypes incl. DeFi LP)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/defi/active-defi-mm.md,
    /codex/09-strategy/architecture-v2/README.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-concentrated.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-pool.md,
    /codex/09-strategy/architecture-v2/archetypes/defi-lp-vault.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Family: Market Making

> **Alpha source:** Bid-ask spread capture via two-sided quoting around a theoretical fair price. We provide liquidity;
> we earn spread minus adverse selection.
>
> **Primary edge method:** Spread capture, net of adverse selection + inventory risk + fees.
>
> **Typical hold policies:** CONTINUOUS (quote lifecycle is long-running; positions are transient, inventory-aware).
>
> **Archetype count:** 10 — `MARKET_MAKING_CONTINUOUS` (legacy CeFi catch-all) + `MARKET_MAKING_EVENT_SETTLED` (sports
> exchange back/lay — **not** legacy) + 5 granular CeFi/prediction variants + 3 DeFi LP variants, all added in the Phase
> 9 expansion (2026-04-25). SSOT: UAC `StrategyArchetype` (`enum-wins` governance rule per `strategy-summary.md:27`).
> DeFi LP variants sit in `MARKET_MAKING` because the alpha is fee earnings for _providing_ liquidity, not directional
> or dispersion edge.

## Alpha thesis

Market Making captures the bid-ask spread by continuously posting two-sided quotes around a theoretical fair price. The
edge is the average spread earned on filled quotes, minus:

- Adverse selection (informed traders pick us off)
- Inventory risk (we carry unwanted delta between fills)
- Fees / commissions

This family covers:

- CEX spot/perp market making (Binance, OKX, Bybit, Hyperliquid, Deribit)
- Options market making (Deribit, CBOE SPY)
- DeFi active LP (Uniswap V3 concentrated liquidity, Orca on Solana)
- Sports exchange market making (Betfair, Smarkets, Matchbook — via Unity or direct)
- Cross-venue MM (quote across multiple venues sharing a reference price)

**Not in this family:**

- One-shot quoting / RFQ — covered under a dedicated action type; not a strategy family
- DEX price-dispersion / arbitrage across pools — alpha is the spread, not LP fee earnings →
  `ARBITRAGE_PRICE_DISPERSION`

> **LP of every kind belongs here.** Concentrated V3 LP (`DEFI_LP_CONCENTRATED`), full-range / passive pool LP such as
> Curve stableswap and Balancer weighted (`DEFI_LP_POOL`), and ERC-4626 yield vaults (`DEFI_LP_VAULT`) are all
> `MARKET_MAKING` archetypes — the alpha is fee earnings for providing liquidity. (Earlier drafts excluded "passive
> Uniswap V2-style LP"; corrected 2026-05-20 — passive pool LP is `DEFI_LP_POOL`, in this family.)

## 10 Archetypes

The 2026-04-17 baseline shipped two MM archetypes (`MARKET_MAKING_CONTINUOUS`, `MARKET_MAKING_EVENT_SETTLED`). The Phase
9 expansion (2026-04-25) split CeFi continuous-quoting into explicit strategy variants (the quote-generation logic,
latency profile, and risk gates differ enough to be separate code paths) and added the prediction-CLOB and DeFi-LP
archetypes. `MARKET_MAKING_CONTINUOUS` is retained as the legacy back-compat value for old records; new CeFi MM
strategies use the granular variants. `MARKET_MAKING_EVENT_SETTLED` is **not** legacy — it is the canonical archetype
for the sports exchange (back/lay) family.

| Archetype                                                                                   | Edge mechanism / venue                                                       | Settlement              |
| ------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ----------------------- |
| [`MARKET_MAKING_CONTINUOUS`](../archetypes/market-making-continuous.md) _(legacy)_          | Back-compat CeFi continuous-quoting catch-all (spot/perp/options/cross-CEX)  | Continuous              |
| [`MARKET_MAKING_EVENT_SETTLED`](../archetypes/market-making-event-settled.md)               | Sports exchange back/lay quoting (Betfair, Smarkets, Matchbook, Betdaq)      | Event-settled           |
| [`MARKET_MAKING_PASSIVE_SPREAD`](../archetypes/market-making-passive-spread.md)             | Symmetric two-sided quoting; near-zero inventory target; repost on each fill | Continuous              |
| [`MARKET_MAKING_INVENTORY_SKEW`](../archetypes/market-making-inventory-skew.md)             | Avellaneda-Stoikov inventory-skewed quotes (self-correcting inventory)       | Continuous              |
| [`MARKET_MAKING_ML_LEAN`](../archetypes/market-making-ml-lean.md)                           | Short-horizon ML directional tilt layered on inventory skew                  | Continuous              |
| [`MARKET_MAKING_QUEUE_MICROSTRUCTURE`](../archetypes/market-making-queue-microstructure.md) | Queue-position + VPIN toxicity-aware quoting (FIFO time-priority venues)     | Continuous              |
| [`MARKET_MAKING_PREDICTION`](../archetypes/market-making-prediction.md)                     | Binary YES/NO CLOB MM on prediction venues (Polymarket, Kalshi)              | Event-settled           |
| [`DEFI_LP_CONCENTRATED`](../archetypes/defi-lp-concentrated.md)                             | Uniswap V3 (clones) concentrated-liquidity range; fee capture + rebalance    | Atomic mint/burn        |
| [`DEFI_LP_POOL`](../archetypes/defi-lp-pool.md)                                             | Full-range pool LP (Curve stableswap, Balancer weighted); hold-or-exit       | Atomic deposit/withdraw |
| [`DEFI_LP_VAULT`](../archetypes/defi-lp-vault.md)                                           | ERC-4626 vault deposit (Yearn V3, MetaMorpho, Aave Vaults); APY-gated        | ERC-4626 deposit/redeem |

## Shared primitives (all archetypes)

- **Theoretical price model**: fair-value computer per instrument (consensus mid, sharp-book reference, vig-free,
  model-derived, hybrid)
- **Quote generator**: two-sided quotes at theo ± half-spread, with inventory-aware skewing
- **Inventory manager**: track position per (instrument, venue), compute skew, impose bounds
- **Delta-proxy repricer**: when underlying reference price moves, auto-adjust quotes without new strategy instruction
  (fast path)
- **Kill switch**: rapid price move, spread blow-out, venue outage, inventory limit breach
- **Adverse-selection monitor**: detect patterns indicating informed flow; widen spread / pull quotes
- **Fee/commission tracker**: net spread after fees is the real alpha
- **Position reconciliation**: local shadow for sub-ms quoting + periodic PBMS sync

## Typical signal sources

| Signal                      | Source                                                                                                         |
| --------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Current orderbook (bid/ask) | Venue L2 book feed                                                                                             |
| Theoretical fair price      | Consensus mid across eligible venues, Smarkets (sports), sharp book reference, or fitted vol surface (options) |
| Realized vol (recent)       | Computed from tick/candle history                                                                              |
| Inventory state             | PBMS + local shadow                                                                                            |
| Reference price movements   | Venue feeds subscribed for ref-price tracking                                                                  |
| Funding rate (perp MM)      | Funding rate tick feed                                                                                         |
| Greeks (options MM)         | Options pricing engine                                                                                         |
| Book fragmentation          | Spread across venues                                                                                           |

## Typical edge methods

- **Net spread capture**: `half_spread − commission − adverse_selection_cost > 0`
- **Inventory-skewed edge**: widen the side you're long on, tighten the side you want filled to reduce inventory
- **Theo-minus-mid**: quote relative to theo (not mid) when theo differs from mid by more than a threshold (exploit
  mispriced mids)
- **Delta-proxy fast-path**: quotes adjust to underlying without new instruction; faster reaction, tighter spreads
  sustainable

## Position structure

- **Continuous**: inventory oscillates around target (often zero); paired with underlying hedge for delta-neutral
  options MM; quotes refresh continuously on book changes and theo changes
- **Event-settled**: back + lay quotes on exchange markets; inventory closes at match settlement

## Typical staking methods

| Method                          | When used                                                        |
| ------------------------------- | ---------------------------------------------------------------- |
| Fixed quote size per instrument | Default                                                          |
| Size scaled by inventory skew   | Default — smaller offer when long, larger when short             |
| Size scaled by realized vol     | Widen / shrink quotes during regime shifts                       |
| Per-venue allocation            | Cross-venue MM splits capital by venue liquidity / fee structure |

## Venue patterns

- **MARKET_MAKING_CONTINUOUS**: Binance (spot + perp), OKX (spot + perp), Bybit (spot + perp), Hyperliquid (spot +
  perp), Deribit (perp + options), Uniswap V3 (concentrated LP), Orca (Solana concentrated LP)
- **MARKET_MAKING_EVENT_SETTLED**: Unity (for Betfair/Betdex/Matchbook exposure with single wallet), direct Betfair,
  Smarkets, Matchbook, Betdaq

## Expression options

- **CEX spot/perp MM**: pure spot quotes or pure perp quotes
- **Options MM**: options quotes + delta hedge on underlying
- **DeFi LP**: concentrated liquidity range (Uniswap V3)
- **Sports MM**: back + lay on exchange book

## Risk profile

- **Drawdowns**: modest but frequent (inventory left on wrong side during adverse move); recovered via spread capture
  over time
- **Tail risks**:
  - Flash crash (rapid move; inventory clears against us)
  - Informed flow burst (adverse selection spike)
  - Venue outage mid-inventory (can't exit / hedge)
  - Competitor tighter spread (our fills drop to zero; no alpha until we adjust)
- **Sharpe (normal regime)**: 2–5. Sharpe turns negative in blow-up regimes; kill switches are what keep the tail from
  dominating the distribution.
- **Kill switches**: price move > N × recent ATR (e.g., 5× 1h ATR), spread blow-out (exchange book goes wide
  unexpectedly), inventory breach, latency spike, venue outage

## Latency Requirements

**Category: `Low`** — sub-second total E2E, live mode only (batch mode has no latency requirements; it replays
historical data at compute speed). Baseline: the archived
[`/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md`](/codex/09-strategy/_archived_pre_v2/cross-cutting/latency-profiles.md)
table — SUPERSEDED as a doc, but its **Market Making** row is the operative baseline and is **confirmed, not
corrected**, here: nothing in this family doc's existing (informal) latency content contradicts it. The doc's
`sub-ms quoting` local shadow + delta-proxy repricer fast path (Shared primitives) are exactly what keeps the
tick-to-signal and signal-to-order segments inside these budgets, and the `latency spike` kill switch (Risk profile)
enforces them operationally.

| Segment         | Budget       | Notes                                                                                                                                                                                     |
| --------------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tick-to-Signal  | < 50 ms      | Market event → normalized tick → feature → signal.                                                                                                                                        |
| Signal-to-Order | < 50 ms      | StrategyInstruction → routing → algo → venue submit, incl. cancel/replace on book change.                                                                                                 |
| Order-to-Fill   | Venue-dep.   | Matching-engine latency per venue (archived venue-baselines table: Binance 20–50 ms order submission / 10–30 ms fill notification; Deribit 15–40 ms / 10–25 ms). Not a budget we control. |
| **Total E2E**   | **< 100 ms** | Baseline: archived Market Making row. `Latency distribution (quote post → exchange ack → any fill)` in the UI dashboard is the monitor for this number.                                   |

**Deployment implication:** `Low` ⇒ the `co_located_vm` deployment profile per the `/configs/runtime-topology.yaml`
`deployment_profiles` category mapping, matching
[`/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`](/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md)
§ 6's `MARKET_MAKING_CONTINUOUS` `topology_requirements` row (execution + strategy co-located on the same VM, min SLA
tier `premium`).

### Decision latency vs. inter-leg execution gap

The `< 100 ms` figures above are the **decision budget** — tick → a single quote instruction. They are NOT the whole
requirement for this family's multi-leg expressions, where the binding constraint is the **inter-leg execution gap**
(2026-08-10 operator ruling: "we are executing two legs of a trade... how are we ensuring the lag leg followed by the
lead leg is ms timing"):

- **Options MM** (Deribit options): the option quote is the lead leg; the **delta hedge on the underlying** is the lag
  leg. The hedge must follow the fill at ms timing — an unhedged inventory delta left for seconds is exactly the
  adverse-move exposure the Risk profile section warns about.
- **Cross-venue / cross-CEX MM** (shared reference price): the second venue's quote refresh is the "leg" that must
  follow the reference move at ms timing, so no venue quotes stale against another.

So for multi-leg MM, "Low" means the **inter-leg execution timing budget is ms-realm**, not merely a sub-100ms
decision-to-signal number.

## UI dashboard (shared)

- Inventory per (instrument, venue) over time
- Quote fill rate (fills / quotes posted) per side
- Spread captured per fill — distribution + rolling average
- Adverse-selection estimate (fills-before-move-vs-fills-favoring-us)
- Kill-switch event log
- Latency distribution (quote post → exchange ack → any fill)
- Quote cancel/replace rate
- Net P&L decomposed (spread capture, inventory P&L, fees, adverse selection)

## Required subscriptions

Config references:

- **venue_capability_refs** — venues where we quote (with fee schedule, tick size, min size, etc.)
- **feature_group_refs** — orderbook / theo / realized-vol features
- **execution_policy_ref** — MM-specific policy (e.g., CONTINUOUS_QUOTE_WITH_DELTA_PROXY algo)
- Optional **reference_price_source** — e.g., Smarkets for sports, fitted IV surface for options
- Optional **model_id** — ML-predicted fair-value adjustment, adverse-selection classifier

## Typical instance examples

```
CEX MM:
  MARKET_MAKING_CONTINUOUS@binance-btc-usdt-mm-prod                (spot MM)
  MARKET_MAKING_CONTINUOUS@binance-btc-usdt-perp-mm-prod           (perp MM)
  MARKET_MAKING_CONTINUOUS@hyperliquid-eth-usdt-perp-mm-prod
  MARKET_MAKING_CONTINUOUS@okx-sol-usdt-spot-mm-prod
  MARKET_MAKING_CONTINUOUS@cross-cex-btc-usdt-mm-prod              (cross-CEX with shared ref)

Options MM:
  MARKET_MAKING_CONTINUOUS@deribit-btc-options-mm-usdt-prod
  MARKET_MAKING_CONTINUOUS@deribit-eth-options-mm-usdt-prod

DeFi active LP:
  MARKET_MAKING_CONTINUOUS@uniswap-v3-eth-usdc-active-lp-prod
  MARKET_MAKING_CONTINUOUS@orca-sol-usdc-active-lp-prod

Sports MM:
  MARKET_MAKING_EVENT_SETTLED@betfair-epl-1x2-mm-gbp-prod          (direct Betfair)
  MARKET_MAKING_EVENT_SETTLED@unity-epl-1x2-mm-usd-prod            (via Unity if we MM on Unity child exchanges)
  MARKET_MAKING_EVENT_SETTLED@smarkets-la-liga-1x2-mm-gbp-prod
```

## Reaction to capital flow events

```python
def react_to_equity_change(self, new_equity_usd: Decimal) -> list[StrategyInstruction]:
    self.equity_usd = new_equity_usd
    self.target_quote_size_usd = new_equity_usd * self.config.inventory_size_pct
    self.max_inventory_usd = new_equity_usd * self.config.max_inventory_pct_of_equity
    # Re-emit quotes with new sizes (cancel + replace, or update in place)
    return self._rescale_quotes()
```

## Rebalancing triggers

- Reference price moves → delta-proxy repricer adjusts quotes (fast path; no new instruction)
- Fill received → inventory updates → skew recomputed → quotes cancel/replace
- Theo model update → quote refresh
- Equity change → rescale target sizes
- Regime change (vol spike, adverse-selection burst) → widen / pull
- Kill-switch → cancel all quotes, close inventory at market

## Migration from legacy docs

| Legacy                                               | Mapping                                                                                      | Notes                                     |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------- | ----------------------------------------- |
| `cefi/market-making.md`                              | `MARKET_MAKING_CONTINUOUS`                                                                   | Generic CEX MM                            |
| `defi/market-making-lp.md`                           | `MARKET_MAKING_CONTINUOUS` (concentrated LP variant)                                         | Shares inventory-skew primitives          |
| `defi/sol-concentrated-lp.md`                        | `MARKET_MAKING_CONTINUOUS`                                                                   | Solana LP variant                         |
| `sports/market-making.md`                            | `MARKET_MAKING_EVENT_SETTLED`                                                                | Now uses same engine as CeFi MM           |
| `tradfi/market-making-options.md`                    | `MARKET_MAKING_CONTINUOUS` (if spread-capture alpha) OR `VOL_TRADING_OPTIONS` (if vol alpha) | Config disambiguates                      |
| Code: `strategy-service/.../cefi_market_making.py`   | `MarketMakingContinuousEngine`                                                               | Already has position reconciliation       |
| Code: `strategy-service/.../sports/market_making.py` | `MarketMakingEventSettledEngine`                                                             | Shares delta-proxy + inventory primitives |
| Code: `strategy-service/.../active_defi_mm.py`       | `MarketMakingContinuousEngine` (LP variant)                                                  |                                           |

## Cross-references

- Archetypes (10): [market-making-continuous](../archetypes/market-making-continuous.md) _(legacy)_,
  [market-making-event-settled](../archetypes/market-making-event-settled.md),
  [market-making-passive-spread](../archetypes/market-making-passive-spread.md),
  [market-making-inventory-skew](../archetypes/market-making-inventory-skew.md),
  [market-making-ml-lean](../archetypes/market-making-ml-lean.md),
  [market-making-queue-microstructure](../archetypes/market-making-queue-microstructure.md),
  [market-making-prediction](../archetypes/market-making-prediction.md),
  [defi-lp-concentrated](../archetypes/defi-lp-concentrated.md), [defi-lp-pool](../archetypes/defi-lp-pool.md),
  [defi-lp-vault](../archetypes/defi-lp-vault.md)
- Delta-proxy repricer:
  [../../../04-architecture/strategy-execution-protocol.md](../../../04-architecture/strategy-execution-protocol.md)
  (execution-layer fast-path)
- Inventory + kill switch:
  [../cross-cutting/venue-account-coordination.md](../cross-cutting/venue-account-coordination.md)
- Unity for sports MM: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- Execution policy for MM quotes: [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
- **Subdir → family enforcement**: `strategy-service/strategy_service/engine/strategies/v2/defi_lp/` archetypes map to
  `MARKET_MAKING`; enforced by `tests/unit/engine/strategies/v2/test_subdir_family_alignment.py`
  (strategy-service@f01d12d).
