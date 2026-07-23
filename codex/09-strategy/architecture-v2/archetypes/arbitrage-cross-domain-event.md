---
doc_type: codex-ssot
title: "Archetype: `ARBITRAGE_CROSS_DOMAIN_EVENT`"
summary: >-
  Archetype ARBITRAGE_CROSS_DOMAIN_EVENT: riskless cross-domain event arb spanning sports books, prediction CLOBs, and
  CME binaries priced on the same real-world outcome. ATOMIC fan-out across all legs (abort/unwind on partial fill),
  USD* share class, entry gated on net_edge > min_arb_edge_usd AND return > min_arb_return_pct with aligned expiries.
implementation_status: design
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, arbitrage, prediction, sports, odds, execution, archetype]
related:
  [
    ../families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-prediction.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
  ]
created: 2026-05-19
authoritative_for: [ARBITRAGE_CROSS_DOMAIN_EVENT archetype specification]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/archetypes/market-making-prediction.md,
    /codex/09-strategy/architecture-v2/families/arbitrage-structural.md,
  ]
owner:
last_reviewed:
code_refs:
archetype: ARBITRAGE_CROSS_DOMAIN_EVENT
family: ARBITRAGE_STRUCTURAL
venue_universe: [PINNACLE, POLYMARKET, KALSHI, PREDICTIT, CME]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 200
  min_sla_tier: premium
---

# Archetype: `ARBITRAGE_CROSS_DOMAIN_EVENT`

> **Family:** [Arbitrage / Structural](../families/arbitrage-structural.md) **Settlement model:** Event-settled — all
> positions settle on the same real-world event outcome; expiries must align across domains. **Code module (target):**
> `strategy-service/engine/strategies/v2/arbitrage_structural/cross_domain_event_engine.py`

## What it does

Cross-domain event arbitrage exploits pricing gaps when the same real-world event is listed across two or more venue
domains — sports books, prediction CLOBs, and exchange-traded binary options — where the implied probability of the same
outcome differs enough to create a riskless spread after fees. The core examples are: "Team A wins" priced
simultaneously at a sharp sports book (Pinnacle), a prediction CLOB (Polymarket), and a CME binary option; or a Fed
rate-decision outcome priced across Kalshi, Polymarket, and CME event contracts. When implied probabilities across
venues/domains produce a combined position with guaranteed positive payoff regardless of outcome, the strategy executes
simultaneously across all legs. Share class is always USD\* (the dominant fiat currency matching the binary outcome
payoff) to avoid cross-currency basis risk.

**Contrast with `ARBITRAGE_PRICE_DISPERSION`**: price dispersion arb trades the same event, same domain (e.g. two
prediction CLOBs), multiple venues. Cross-domain arb trades the same event, DIFFERENT domain types (sports book +
prediction CLOB + CME binary).

## Token / position flow

```
1. EVENT REGISTRY SCAN (per scheduled cadence or real-time feed):
   - Identify events with ≥2 domain listings (sports book + prediction CLOB + exchange binary)
   - Align on expiry: expiry_delta < max_expiry_mismatch_hours (all legs settle same event)
   - Canonical event ID links all legs via event_registry

2. IMPLIED PROBABILITY EXTRACTION:
   - Sports book: convert decimal/fractional odds to implied_prob (vig-free using P/(P+1) + normalization)
   - Prediction CLOB: take mid-price of YES contract as implied_prob
   - CME binary: extract settlement prob from binary option price

3. ARBITRAGE DETECTION:
   For two-outcome event (e.g. YES/NO or Team A wins / Team B wins):
   - sum_implied_probs across all domain positions constructed as arb = check vs 1.0
   - net_edge = max_payoff - min_cost_of_full_arb_position - total_fees
   - Entry: net_edge > min_arb_edge_usd AND net_edge / total_cost > min_arb_return_pct

4. POSITION CONSTRUCTION (simultaneous, all legs):
   - Leg 1 (sports book): back the underpriced outcome via API
   - Leg 2 (prediction CLOB): buy underpriced YES via CLOB limit order
   - Leg 3 (exchange binary): buy underpriced binary option contract
   - All legs sized to the same notional-equivalent probability unit

5. EXECUTION: ATOMIC fan-out across all venue domains
   - Timeout: if any leg not confirmed within fill_timeout_seconds, cancel remaining legs
   - Partial fill: abort and unwind; never carry a partial arb (leg risk = directional bet)

6. SETTLEMENT:
   - All legs settle on same event outcome
   - Win on all legs: guaranteed payoff (true arb)
   - One leg venue fails to settle: flag for manual reconciliation
```

## Entry conditions + signal

- `net_edge_usd > min_arb_edge_usd` (default 5.0 USD)
- `net_edge_return_pct > min_arb_return_pct` (default 0.5%)
- Expiry alignment: `|expiry_A - expiry_B| < max_expiry_mismatch_hours` (default 1.0h)
- All legs executable: API connectivity verified on all domain venues
- Event has clear binary resolution with defined settlement rules per venue

## Risk management

- Partial fill abort: if ANY leg fails within fill_timeout_seconds, cancel all remaining legs and unwind filled legs via
  market order — never carry partial arb
- Expiry mismatch risk: if expiry misalignment > max_expiry_mismatch_hours, reject the arb (one leg could settle before
  the event; creates directional risk)
- Venue settlement risk: sports book may void bet (e.g. event cancelled); prediction CLOB may have disputed resolution —
  position held in escrow; hedge via third leg
- Concentration limit: max_total_exposure_usd across all cross-domain arb positions
- Domain-specific restrictions: some jurisdictions prohibit certain domain combinations (sports book + financial
  exchange); compliance filter applied per operator region

## Config parameters

- `event_domains`: list of eligible domain types, e.g. `[sports_book, prediction_clob, cme_binary]`
- `venues_per_domain`: map of domain → list of venues to scan
- `min_arb_edge_usd`: minimum net riskless edge in USD to execute (default 5.0)
- `min_arb_return_pct`: minimum edge as fraction of total cost (default 0.5%)
- `max_expiry_mismatch_hours`: maximum allowed expiry misalignment across legs (default 1.0)
- `fill_timeout_seconds`: maximum time to get all leg fills; abort if exceeded (default 10)
- `max_total_exposure_usd`: maximum total USD across all live cross-domain arb positions (default 5000)
- `vig_normalisation`: method for sports book vig removal (`power` | `shin` | `additive`)
- `min_liquidity_usd_per_leg`: minimum CLOB/exchange liquidity at target price per leg (default 100)
- `settlement_confidence_required`: require explicit settlement rule documentation before entry (default true)
- `compliance_region_filter`: list of allowed domain-combination pairs per jurisdiction
- `share_class`: USD\* (always fiat-denominated to match binary payoff)
- `execution_policy_ref`: arb-cross-domain-v1

## When to use / market regime

- **Use when**: same high-profile event is listed across multiple domain types with sufficient liquidity on all legs;
  institutional-grade sports book (Pinnacle) disagrees on probability with retail prediction CLOB; CME binary event
  contracts active and liquid (Fed, NFP, elections)
- **Best events**: US elections (Kalshi + Polymarket + PredictIt + CME); Fed rate decisions (Kalshi + CME SOFR binary);
  major sports championships where Pinnacle + Polymarket both list the same outcome
- **Avoid**: illiquid legs (< min_liquidity_usd_per_leg); ambiguous settlement rules on any domain (sports book void
  conditions differ from CLOB resolution); events too close to resolution (< 2h) where liquidity dries up
- **Contrast with ARBITRAGE_PRICE_DISPERSION**: price dispersion = same domain, multiple venues (e.g. Polymarket vs
  Kalshi for same prediction); this archetype = different domain types for same event

## Example instances

```
ARBITRAGE_CROSS_DOMAIN_EVENT@pinnacle-polymarket-elections-usd-prod
ARBITRAGE_CROSS_DOMAIN_EVENT@kalshi-cme-fed-rate-usd-prod
ARBITRAGE_CROSS_DOMAIN_EVENT@pinnacle-polymarket-sports-usd-prod
```

## Not in this archetype

- Same-domain arb across multiple prediction CLOBs → `ARBITRAGE_PRICE_DISPERSION`
- Sports book cross-book arb (Pinnacle vs Betfair) → `ARBITRAGE_PRICE_DISPERSION`
- Market making on prediction CLOB → `MARKET_MAKING_PREDICTION`

## See also

- Family: [arbitrage-structural.md](../families/arbitrage-structural.md)
- Same-domain price dispersion arb: [arbitrage-price-dispersion.md](arbitrage-price-dispersion.md)
- Prediction market MM: [market-making-prediction.md](market-making-prediction.md)
- Sports event MM: [market-making-event-settled.md](market-making-event-settled.md)
