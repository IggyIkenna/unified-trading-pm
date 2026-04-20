---
scope: [engineer, admin]
---

# Family: Market Making

> **Alpha source:** Bid-ask spread capture via two-sided quoting around a theoretical fair price. We provide liquidity;
> we earn spread minus adverse selection.
>
> **Primary edge method:** Spread capture, net of adverse selection + inventory risk + fees.
>
> **Typical hold policies:** CONTINUOUS (quote lifecycle is long-running; positions are transient, inventory-aware).
>
> **Archetype count:** 2 — distinguished by settlement model.

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

- Passive LP (Uniswap V2 style) — not really making markets; just supplying liquidity at a fixed curve
- One-shot quoting / RFQ — covered under dedicated action type; not a strategy family

## 2 Archetypes

| Archetype                                                                     | Settlement model                                                             | When to use                                                      |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| [`MARKET_MAKING_CONTINUOUS`](../archetypes/market-making-continuous.md)       | Continuous P&L; positions held, tracked, hedged continuously                 | CEX spot/perp MM, options MM, DeFi concentrated LP, cross-CEX MM |
| [`MARKET_MAKING_EVENT_SETTLED`](../archetypes/market-making-event-settled.md) | Quotes on markets that settle on an event (match result, prediction outcome) | Sports exchange MM (Betfair), prediction-market MM (future)      |

## Shared primitives (both archetypes)

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
| Theoretical fair price      | Consensus mid across eligible venues, Pinnacle (sports), sharp book reference, or fitted vol surface (options) |
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
- **Sharpe**: typically very high (2-5) in normal regimes; occasionally negative in blow-up regimes
- **Kill switches**: price move > N × recent ATR (e.g., 5× 1h ATR), spread blow-out (exchange book goes wide
  unexpectedly), inventory breach, latency spike, venue outage

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
- Optional **reference_price_source** — e.g., Pinnacle for sports, fitted IV surface for options
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

- Archetypes: [market-making-continuous](../archetypes/market-making-continuous.md),
  [market-making-event-settled](../archetypes/market-making-event-settled.md)
- Delta-proxy repricer:
  [../../../04-architecture/strategy-execution-protocol.md](../../../04-architecture/strategy-execution-protocol.md)
  (execution-layer fast-path)
- Inventory + kill switch:
  [../cross-cutting/venue-account-coordination.md](../cross-cutting/venue-account-coordination.md)
- Unity for sports MM: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
- Execution policy for MM quotes: [../cross-cutting/execution-policies.md](../cross-cutting/execution-policies.md)
