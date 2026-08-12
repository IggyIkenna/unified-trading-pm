---
doc_type: codex-ssot
title: "Archetype: `ARBITRAGE_SPORTS_DUTCHING`"
summary: >-
  `ARBITRAGE_SPORTS_DUTCHING` archetype — N-venue dutched arbitrage on a complete set of mutually-exclusive sports-odds
  outcomes (e.g. HOME / DRAW / AWAY, or YES / NO): when the best decimal odds across N venues make the book
  overround-negative (`sum_over_outcomes(1/best_odds) < 1`), stake each outcome at its best venue in inverse-odds
  proportion to lock a positive return regardless of which outcome resolves. A structural sibling of
  `ARBITRAGE_PRICE_DISPERSION` (cross-venue funding) — same family, same price-dispersion primitive, different asset
  semantics (decimal odds vs funding APR).
implementation_status: live
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service]
scope: [engineer, admin]
tags: [strategy, arbitrage, sports, dutching, odds, bookmaking, execution, archetype]
related:
  [
    ../families/arbitrage-structural.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md,
    /codex/09-strategy/architecture-v2/archetypes/arbitrage-cross-domain-event.md,
    /codex/09-strategy/architecture-v2/archetypes/market-making-event-settled.md,
  ]
created: 2026-08-12
authoritative_for: [ARBITRAGE_SPORTS_DUTCHING archetype specification]
referenced_by: [/codex/09-strategy/architecture-v2/families/arbitrage-structural.md]
owner:
last_reviewed:
code_refs: [strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py]
archetype: ARBITRAGE_SPORTS_DUTCHING
family: ARBITRAGE_STRUCTURAL
venue_universe: [UNITY, BETFAIR, SMARKETS, MATCHBOOK, PINNACLE]
topology_requirements:
  isolation: { execution-service: isolated, strategy-service: isolated }
  co_location: [execution-service, strategy-service]
  latency_budget_ms: 500
  min_sla_tier: premium
---

# Archetype: `ARBITRAGE_SPORTS_DUTCHING`

> **Family:** [Arbitrage / Structural](../families/arbitrage-structural.md) **Settlement model:** Event-settled — every
> leg settles on the same real-world outcome. **Code module (target):**
> `strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/sports_arb_dutching.py`

## What it does

N-venue dutched arbitrage on a complete set of mutually exclusive outcomes (e.g. HOME / DRAW / AWAY, or YES / NO). For a
complete outcome set, if the best decimal odds across N venues satisfy `sum_over_outcomes(1 / best_odds[outcome]) < 1`,
the book is "overround-negative" and the bettor can stake each outcome at the venue offering its best price in
inverse-odds proportion, locking in a positive return regardless of which outcome resolves true.

**Contrast with `ARBITRAGE_PRICE_DISPERSION`**: price-dispersion arb trades a 2-leg BUY/SELL cross-venue pair on the
same instrument (funding APR / price). Dutching trades an **N-leg** complete outcome cover across the **same sports
event** (decimal odds). Both are delta-neutral _within_ the arb and stack gross across multiple arbs.

## Arb math

```
Dutched stake share for outcome i:
    share_i = (1 / odds_i) / sum_j( 1 / odds_j )

Net P&L (no commission):
    pnl = total_stake * (1 / sum_j (1/odds_j) - 1)      # positive iff sum_j(1/odds_j) < 1

Overround savings gate:
    overround_savings_pct = (1 - sum_j(1/odds_j)) * 100
```

The engine gates entry on `overround_savings_pct >= min_overround_savings_pct`.

## Token / position flow

```
On tick:
  1. OUTCOME SET: read outcome_set (complete mutually-exclusive set, >= 2) + candidate_venues (>= 2)
  2. BEST QUOTE: for each outcome, find the venue with the highest decimal odds (> 1.0)
  3. ARB SCAN: sum inverse odds across outcomes; require all outcomes quoted + book_sum < 1
  4. OVERROUND GATE: (1 - book_sum) * 100 >= min_overround_savings_pct
  5. SIZE: total_stake = target_equity * stake_fraction; each leg stake = total_stake * share_i
  6. EMIT: AtomicInstruction (ATOMIC, one BACK leg per outcome at its best venue)

On event settlement:
  - All outcomes settle on the same event; the dutched cover realises a guaranteed payout.
```

## Feature keys

Per outcome × venue, per UAC's `OddsFeaturesMixin`-derived naming scheme
(`sports_odds_feature_naming_canonicalization_2026_07_21.md`):

- `odds_decimal_<outcome_id>_<venue>`: float — best price to back the outcome.

## Config parameters

| Param                       | Default | Meaning                                                           |
| --------------------------- | ------- | ----------------------------------------------------------------- |
| `outcome_set`               | —       | Comma-separated outcome ids forming a complete set (required, ≥2) |
| `candidate_venues`          | —       | Comma-separated venues (required, ≥2)                             |
| `min_overround_savings_pct` | `1.0`   | Minimum `(1 - book_sum) * 100` to qualify                         |
| `stake_fraction`            | `0.05`  | Fraction of target_equity per arb                                 |
| `hedge_deadline_ms`         | `5000`  | Atomic-fill deadline for the dutched legs                         |

## Execution semantics

- `AtomicInstruction` with `AtomicExecutionMode.ATOMIC` — all legs must fill or the arb aborts.
- `CompensationPolicy.CLOSE_LEADER_IF_HEDGE_FAILS` — partial fill never carries directional leg risk.
- One BACK leg per outcome at the best venue; `hedge_deadline_ms` is the hard atomic-fill deadline.

## Leg portfolio state

- Per-arb `LegPortfolioState` at config time, one leg per outcome.
- Sizing strategy = `LegSizingStrategy.PROPORTIONAL_TO_DEV_FROM_MEAN` (mean = mean inverse odds; dev = inverse odds
  outcome − mean).
- Net delta within the arb = 0 (every outcome covered, identical payout).

## Venue patterns

- **Sports books via Unity** (primary, single-wallet access to 10 books) + direct Betfair / Smarkets / Matchbook for
  books not on Unity; Pinnacle as the sharp-book reference. Full venue table lives in the family doc
  [`../families/arbitrage-structural.md`](../families/arbitrage-structural.md) (sports cross-book row).

## Risk profile

- Riskless _within_ the arb (complete outcome cover) — the residual risks are execution-side: partial fill, venue
  settlement/void rules, and the atomic-fill deadline, not directional exposure.
- Drawdowns are low in percentage terms; most losses come from execution failures (partial fill, slippage, adverse move
  between leg fills).

## Not in this archetype

- **2-leg cross-venue price dispersion** (funding APR / same-instrument price) — `ARBITRAGE_PRICE_DISPERSION`
- **Cross-domain event arb** (sports book ↔ prediction CLOB ↔ CME binary) — `ARBITRAGE_CROSS_DOMAIN_EVENT`
- **Sports market making** (passive back+lay inventory) — `MARKET_MAKING_EVENT_SETTLED`

## See also

- Family: [arbitrage-structural.md](../families/arbitrage-structural.md)
- Same-domain price dispersion: [arbitrage-price-dispersion.md](arbitrage-price-dispersion.md)
- Cross-domain event arb: [arbitrage-cross-domain-event.md](arbitrage-cross-domain-event.md)
- Sports event MM: [market-making-event-settled.md](market-making-event-settled.md)
