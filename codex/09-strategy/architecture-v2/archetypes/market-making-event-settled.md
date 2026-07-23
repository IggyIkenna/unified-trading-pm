---
doc_type: codex-ssot
title: "Archetype: `MARKET_MAKING_EVENT_SETTLED`"
summary: >-
  `MARKET_MAKING_EVENT_SETTLED` archetype — posts back + lay quotes on sports exchanges (Betfair / Smarkets / Matchbook
  / Betdaq) and Polymarket, earning the spread on matched bets with inventory skew; cancels quotes
  `pre_event_cancel_minutes` before event start; positions settle discretely on event resolution.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [market-making, sports, prediction, odds, event-driven]
related:
  [
    ../families/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
    ../../../02-venues/unity-integration.md,
    ../category-instrument-coverage.md,
  ]
created: 2026-04-17
authoritative_for: [MARKET_MAKING_EVENT_SETTLED archetype specification]
referenced_by:
  [
    /codex/02-venues/unity-integration.md,
    /codex/09-strategy/_archived_pre_v2/sports/market-making.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-cross-domain-event.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-continuous.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-inventory-skew.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-passive-spread.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-prediction.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-queue-microstructure.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: MARKET_MAKING_EVENT_SETTLED
family: MARKET_MAKING
venue_universe: [BETFAIR, SMARKETS, MATCHBOOK, BETDAQ, POLYMARKET]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 40
  min_sla_tier: premium
---

# Archetype: `MARKET_MAKING_EVENT_SETTLED`

> **Family:** [Market Making](../families/market-making.md) **Settlement model:** Continuous quote lifecycle; positions
> settle on event resolution. **Code module (target):**
> `strategy-service/engine/strategies/market_making_event_settled_engine.py`

## What it does

Posts back + lay quotes on sports exchanges (Betfair, Smarkets, Matchbook, Betdaq) OR prediction-market exchanges
(Polymarket). Earns the bid-ask spread on matched bets while managing inventory exposure. Unlike CLOB MM (continuous),
each market settles discretely on event resolution.

## Token / position flow

```
1. THEO PRICE: compute fair price per outcome
   - Sharp-book reference (Smarkets pre-match)
   - Vig-free consensus across bookmakers
   - Model-derived fair (from ML if available)
   - Fitted exchange mid

2. QUOTE GENERATION: post back + lay around theo
   - back_price = theo - half_spread_ticks
   - lay_price = theo + half_spread_ticks
   - Skew by inventory: long backed → widen back / tighten lay

3. DELTA-PROXY REPRICER: when reference (sharp book, theo) moves, auto-update quotes
   without strategy re-emission

4. FILL HANDLING:
   - Matched back: we've backed at our back_price; inventory shifts positive
   - Matched lay: inventory shifts negative
   - Update skew; re-post quotes

5. INVENTORY MANAGEMENT:
   - Max exposure per selection
   - Kill switch on rapid price move (potential injury / red card in sport)
   - Cancel quotes near event start (configurable; don't carry MM book into match)

6. SETTLEMENT: on event resolution, all open positions auto-settle
   Inventory converts to cash (win) or is lost (lose)
```

## Supported venues

**Coverage matrix:** See
[`../category-instrument-coverage.md § 14. MARKET_MAKING_EVENT_SETTLED`](../category-instrument-coverage.md#14-market_making_event_settled)
for the authoritative sports + prediction-market venue table (Betfair direct + Unity, Smarkets, Matchbook, Betdaq,
Polymarket) with commission and liquidity notes.

## Expression options

- Back + lay pairs
- Spread-only positions (don't accumulate inventory, only fill-flip)

## Hold policies

- CONTINUOUS — quote lifecycle until match approach / event start
- Configurable cancel_on_event_start (pull all quotes N minutes before)

## Config schema

```yaml
venue: BETFAIR_DIRECT # or UNITY (routes to Betfair-via-Unity)
league: EPL
markets_eligible: ["1X2", "OVER_UNDER_2_5", "BTTS"]
theo_source: sharp_book # or consensus / model / hybrid
sharp_reference_venue: PINNACLE # used if theo_source = sharp_book
half_spread_ticks: 1
max_inventory_per_selection: 500 # in bankroll units
max_inventory_imbalance: 250
skew_factor: 0.5
commission_rate: 0.028 # Betfair via Unity 2.8%
min_spread_edge_pct: 0.5 # min net edge after commission
cancel_on_event_start: true
pre_event_cancel_minutes: 2
kill_switch_movement_pct: 10.0
refresh_interval_seconds: 5
share_class: GBP
execution_policy_ref: sports-mm-v2

# Leverage + net-delta controls (universal per StrategyInstanceDefinition; Stream D 2026-05-07):
target_leverage: 1.0 # [1, 10]; MM keeps 1.0 (inventory risk via max_inventory, not leverage)
target_net_delta: 0.0 # net directional delta (0 = balanced book target)
max_underlying_move_pct: 3.0 # vol-cap clamp: widen quotes rather than skip for MM
instrument_volatility_registry_lookup: true # use realized_vol_20 (1h candles) from FSS
```

## Execution semantics

- `QUOTE` action type — continuous quote lifecycle
- Delta-proxy repricer handles reference moves
- Fill stream → inventory update → skew recompute → quote cancel/replace
- `CANCEL` on event start

## P&L attribution

- **Spread captured**: (lay_price - back_price) × matched_size − commission
- **Inventory P&L on settlement**: realized when match resolves
- **Commission drag**: per filled bet
- **Execution alpha**: vs benchmark fills

## Risk profile

- Drawdowns: moderate; inventory carried into match resolution can go wrong
- Typical Sharpe: 1.5-3.0 for well-run sports MM
- Kill switches: rapid odds move (injury, red card, goal), venue outage, inventory breach

## Reaction to equity change

```python
def react_to_equity_change(new_equity):
    self.equity = new_equity
    self.max_inventory_per_selection = new_equity * self.config.max_inventory_pct_of_equity
    return self._rescale_quotes()
```

## Example instances

```
MARKET_MAKING_EVENT_SETTLED@betfair-epl-1x2-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@unity-betfair-epl-1x2-mm-usd-prod
MARKET_MAKING_EVENT_SETTLED@betfair-champions-league-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@smarkets-la-liga-1x2-mm-gbp-prod
MARKET_MAKING_EVENT_SETTLED@matchbook-nba-moneyline-mm-usd-prod
MARKET_MAKING_EVENT_SETTLED@polymarket-binary-mm-usdc-prod     (future — needs Polymarket MM review)
```

## Migration from legacy

| Legacy                          | Notes                              |
| ------------------------------- | ---------------------------------- |
| `sports/market-making.md`       | Direct match                       |
| Code: `sports/market_making.py` | → `MarketMakingEventSettledEngine` |

## Not in this archetype

- **Continuous-market quoting** (crypto CLOB, options CLOB) — `MARKET_MAKING_CONTINUOUS`
- **Directional sports bets** (one-sided placement on value or rule) — `ML_DIRECTIONAL_EVENT_SETTLED` or
  `RULES_DIRECTIONAL_EVENT_SETTLED`
- **Cross-book arbitrage** — `ARBITRAGE_PRICE_DISPERSION`
- **CLV capture via odds drift** — `RULES_DIRECTIONAL_EVENT_SETTLED`

## See also

- Family: [market-making.md](../families/market-making.md)
- Continuous (CLOB + AMM LP) variant: [market-making-continuous.md](market-making-continuous.md)
- Unity for sports MM routing: [../../../02-venues/unity-integration.md](../../../02-venues/unity-integration.md)
