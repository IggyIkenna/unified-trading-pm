---
doc_type: codex-ssot
title: "Archetype: `MARKET_MAKING_PREDICTION`"
summary: >-
  `MARKET_MAKING_PREDICTION` archetype — prediction-market CLOB MM on Polymarket / Kalshi binary YES/NO contracts; fair
  value blends sharp-book, base-rate prior, and model (weighted), quotes fair ± `half_spread_ticks` with inventory skew,
  cancels `event_blackout_hours` before resolution; positions settle at 0 or 1.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [market-making, prediction, polymarket, kalshi, event-driven]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-cross-domain-event.md,
    /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
  ]
created: 2026-05-19
authoritative_for: [MARKET_MAKING_PREDICTION archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-cross-domain-event.md,
    /codex/09-strategy/architecture-v2/families/market-making.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: MARKET_MAKING_PREDICTION
family: MARKET_MAKING
venue_universe: [POLYMARKET, KALSHI]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 40
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_PREDICTION`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Event-settled — quotes posted on
> binary outcome CLOB markets; positions settle at 0 or 1 on event resolution. **Code module (target):**
> `strategy-service/engine/strategies/v2/market_making/prediction_engine.py`

## What it does

Prediction market CLOB market making posts bid and ask quotes on YES/NO binary outcome contracts on Polymarket and
Kalshi. The strategy earns the bid-ask spread between matched fills while managing directional exposure from inventory
accumulation. Fair value for each contract is estimated from three sources: sharp-book calibration (implied probability
from liquid prediction exchanges), base-rate priors (historical frequency of similar events), and optionally a model
prediction. The goal is to price the binary outcome market fairly while collecting the spread, similar to
MARKET_MAKING_EVENT_SETTLED for sports markets but applied to political, economic, and other event-based contracts.

## Token / position flow

```
1. FAIR VALUE COMPUTATION (per market, per refresh):
   - sharp_prob: implied probability from the most liquid prediction exchange for this event
   - base_rate_prior: historical base rate for event category (e.g. Fed holds rate: 70%)
   - model_prob: ML model prediction if available (optional)
   - fair_value = w_sharp × sharp_prob + w_base × base_rate_prior + w_model × model_prob
     (weights sum to 1; sharp dominates when available)

2. QUOTE GENERATION:
   - bid_price = fair_value - half_spread_ticks × tick_size  (we buy YES at bid)
   - ask_price = fair_value + half_spread_ticks × tick_size  (we sell YES at ask)
   - Skew by inventory: long YES → widen bid, tighten ask (encourage YES sells to us)

3. QUOTE POSTING: submit LIMIT bid + LIMIT ask on prediction CLOB
   - Respect Polymarket/Kalshi API rate limits
   - Cancel and reprice when fair_value moves by > reprice_threshold

4. FILL HANDLING:
   - Bid fill: long YES position; inventory += fill_size
   - Ask fill: short YES position (hedged by NO); inventory -= fill_size
   - Recompute fair_value + skew; update quotes

5. INVENTORY MANAGEMENT:
   - max_exposure_usd: max total notional in any single market
   - Skew adjustment: proportional to inventory_ratio (same as INVENTORY_SKEW framework)
   - Hard cap: if |inventory| > inventory_hard_cap: market-order exit (accept taker fees)

6. SETTLEMENT HANDLING:
   - On event resolution: YES → 1.0, NO → 0.0
   - Reconcile settled positions vs outstanding quotes (cancel all remaining open orders)
   - Record realised P&L: spread_captured + inventory_pnl_on_settlement
```

## Entry conditions + signal

- `|fair_value - current_mid| < max_fair_value_deviation` (our estimate close to market)
- Market not in blackout period (event resolving in < event_blackout_hours)
- Sufficient market liquidity (existing volume > min_daily_volume_usd)
- Sharp-book reference available for this event OR model confidence > min_model_confidence

## Risk management

- Single-market concentration: max_exposure_usd per contract (prediction markets have binary payoff — full loss on wrong
  outcome)
- Event blackout: cancel all quotes min_hours_before_resolution before event resolves (avoid forced inventory into
  settlement)
- Sharp-book deviation kill: pause quoting if `|our_fair_value - sharp_mid| > max_deviation_from_sharp` (model drift vs
  market signal)
- Daily P&L stop: daily_stop_loss_usd across all prediction markets
- Inventory hard cap: market-order exit at inventory_hard_cap (USDC taker cost accepted)

## Config parameters

- `venue`: `POLYMARKET` | `KALSHI` | both
- `markets_eligible`: list of eligible event markets (event IDs or categories)
- `fair_value_weights`: `{sharp: 0.60, base_rate: 0.30, model: 0.10}` (operator-configured)
- `sharp_reference_venue`: venue used as sharp-book reference (default: `POLYMARKET` for Kalshi; cross-referenced)
- `half_spread_ticks`: half-spread in USDC ticks from fair value (default 0.01 = 1 cent on 0-1 scale)
- `max_fair_value_deviation`: max distance our fair value can be from sharp mid to quote (default 0.05)
- `reprice_threshold`: fair value move that triggers quote cancel + reprice (default 0.02)
- `max_exposure_usd`: maximum USDC exposure per single market (default 500)
- `inventory_hard_cap`: USDC notional above which forced market-order exit (default 1000)
- `skew_factor`: inventory-driven quote adjustment amplification (default 0.5)
- `event_blackout_hours`: hours before event resolution to cancel all quotes (default 2)
- `min_daily_volume_usd`: minimum market daily volume required to post (default 5000)
- `min_model_confidence`: minimum model probability confidence to use model weight (default 0.60)
- `daily_stop_loss_usd`: daily loss limit across all prediction markets (default 500)
- `share_class`: USDC
- `execution_policy_ref`: prediction-mm-v1

## When to use / market regime

- **Use when**: prediction market has sufficient liquidity and a reliable sharp-book reference; bid-ask spread is wide
  enough to absorb fees after maker/taker commissions; event is well-defined with clear resolution criteria
- **Best regime**: active political or economic event markets (elections, Fed decisions, major sports championships)
  where multiple sharp participants establish reliable fair-value references; markets with stable liquidity several days
  before resolution
- **Avoid**: markets with no sharp-book reference and no model signal (pure noise quoting); markets resolving in <
  event_blackout_hours; binary outcomes with non-standard resolution criteria (ambiguity risk)
- **Contrast with ARBITRAGE_CROSS_DOMAIN_EVENT**: this archetype earns spread on a single venue; cross-domain arb
  exploits pricing gaps across domains

## Example instances

```
MARKET_MAKING_PREDICTION@polymarket-elections-yesno-mm-usdc-prod
MARKET_MAKING_PREDICTION@kalshi-fed-rate-yesno-mm-usdc-prod
MARKET_MAKING_PREDICTION@polymarket-sports-championship-yesno-mm-usdc-prod
```

## Not in this archetype

- Sports exchange back-lay quoting (Betfair/Smarkets) → [`MARKET_MAKING_EVENT_SETTLED`](market-making-event-settled.md)
- Crypto CLOB continuous quoting → [`MARKET_MAKING_CONTINUOUS`](market-making-continuous.md)
- Cross-venue prediction market price dispersion arb → [`ARBITRAGE_CROSS_DOMAIN_EVENT`](arbitrage-cross-domain-event.md)
- Directional one-sided position on a prediction contract →
  [`ML_DIRECTIONAL_EVENT_SETTLED`](ml-directional-event-settled.md)

## See also

- Family: [market-making.md](../families/market-making.md)
- Sports event-settled MM: [market-making-event-settled.md](market-making-event-settled.md)
- Cross-domain event arbitrage: [arbitrage-cross-domain-event.md](arbitrage-cross-domain-event.md)
