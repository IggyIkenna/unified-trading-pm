---
doc_type: codex-ssot
title: Prediction Markets — Cross-Cutting Concern
summary:
  "Prediction markets (Polymarket/Kalshi) as a three-role surface — feature source, execution venue, arb surface — plus
  a three-tier classification (use-case × domain × equivalent-instrument), the `canonical_question_group`
  recurring-market SSOT, and per-market lifecycle timestamps. Kalshi API host is now `api.elections.kalshi.com`."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags: [prediction, strategy, features, execution, arbitrage, instruments, uac]
related:
  [
    ../../operational/prediction-markets-codification-gaps.md,
    ../../../02-data/prediction-schema-paths.md,
    ../../../04-architecture/instruments-live-architecture.md,
  ]
created: 2026-03-27
authoritative_for:
  [prediction-markets three-role model (feature/execution/arb) + three-tier market classification framework]
referenced_by:
  [
    /codex/09-strategy/README.md,
    /codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    /codex/09-strategy/operational/prediction-markets-codification-gaps.md,
    plans/epics/predictions_master.md,
  ]
owner:
last_reviewed: 2026-08-14
code_refs:
---

> **[DELTA 2026-08-14 — KALSHI LIVE, NOT CREDENTIALS-BLOCKED]** **Current state:** Kalshi migrated its API to
> `api.elections.kalshi.com`. The old host `trading-api.kalshi.com` (and any examples using `api.kalshi.com`) returns
> HTTP 401. All 17 code sites across 5 repos were updated in Phase 1 of
> `kalshi_api_migration_to_elections_subdomain_2026_05_20.md` (UAC@`5729197`, IS@`79ad855`, MTDS@`28b84ce`,
> EXS@`8a3cbe48`, UI@`664c3992`). **Any inline code examples in this doc that reference `api.kalshi.com` or
> `trading-api.kalshi.com` are stale — use `api.elections.kalshi.com` instead.** The prior `BLOCKED-CREDENTIALS` framing
> for Phase 3 is stale: live capture has been running well past `day=2026-07-27`
> (`prediction_phase_ab_residuals_2026_07_24.md`), the dead-host regression was fixed and regression-guarded
> (`e2e-testing@371ac1b`, `kalshi_live_capture_regression_and_drift_2026_07_13.md`), and real
> `KALSHI:PREDICTION_MARKET:...` rows are landing in the manifest. The actual current gate is an **operator ruling on
> live-order verification** (not a credentials absence).

# Prediction Markets — Cross-Cutting Concern

Polymarket and Kalshi serve THREE distinct roles in the unified trading system. They are not just "another venue" — they
are simultaneously a data source, an execution venue, and an arbitrage surface.

## Three Use Cases

| Role                  | What                                                     | Example                                                                   |
| --------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------- |
| **Features source**   | Prediction market prices as signals for other strategies | Polymarket "BTC above $100k" at 72% → bullish signal for CeFi momentum    |
| **Execution venue**   | Trade prediction markets directly based on our models    | Our ML model says 90% BTC up, market says 50% → buy YES contracts         |
| **Arbitrage surface** | Cross-platform or cross-instrument arb                   | Same event on Polymarket at 55% and Kalshi at 48% → buy Kalshi, sell Poly |

## What Already Exists in the System

**Substantial infrastructure is already built:**

| Component                              | Status      | File                                                                                                           |
| -------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------- |
| Polymarket market data adapter         | IMPLEMENTED | `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py` |
| Kalshi market data adapter             | IMPLEMENTED | `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py`     |
| Polymarket schemas (Pydantic)          | IMPLEMENTED | `unified-api-contracts/external/polymarket/schemas.py`                                                         |
| Kalshi schemas (Pydantic)              | IMPLEMENTED | `unified-api-contracts/external/kalshi/schemas.py`                                                             |
| Polymarket arb schemas                 | IMPLEMENTED | `unified-api-contracts/external/polymarket/arb_schemas.py`                                                     |
| Polymarket CLOB execution              | IMPLEMENTED | `execution-service/adapters/exchanges/polymarket_clob.py`                                                      |
| Kalshi execution adapter               | IMPLEMENTED | `execution-service/adapters/exchanges/kalshi.py`                                                               |
| PredictionArbStrategy                  | IMPLEMENTED | `strategy-service/engine/strategies/prediction_arb/prediction_arb_strategy.py`                                 |
| Prediction mapping / categorisation    | IMPLEMENTED | `strategy-service/engine/strategies/prediction/prediction_mapping.py`                                          |
| Cross-venue arb schemas (UAC internal) | IMPLEMENTED | `unified-api-contracts/unified_api_contracts/internal/domain/prediction_market/prediction_market_arb.py`       |
| Polymarket crowd sentiment feature     | IMPLEMENTED | `features-service (cross-instrument family)/calculators/polymarket_crowd_sentiment_calculator.py`              |
| Execution handler                      | IMPLEMENTED | `execution-service/engine/handlers/prediction_handler.py`                                                      |
| VCR cassettes                          | EXIST       | `unified-api-contracts/tests/`                                                                                 |

**What's NOT wired:**

| Gap                                                 | Impact                                 |
| --------------------------------------------------- | -------------------------------------- |
| Not in `VENUE_REGISTRY` (in `PLANNED_VENUES`)       | `get_adapter()` can't instantiate them |
| No capability declarations                          | Mode/env validation not wired          |
| No instrument taxonomy entry for prediction markets | Instrument IDs not standardised        |
| Kalshi position tracking missing                    | Can't monitor Kalshi positions         |

## Market Classification Framework

### The Core Problem: Same Event, Different Wording

Polymarket: "Will gold price exceed $2,500 by June 2025?" Kalshi: "Gold spot price above $2,500 on June 30, 2025"
**These are the same event.** Cross-platform arb requires matching them.

### Existing: `PredictionMarketCategory` Enum

```python
class PredictionMarketCategory(StrEnum):
    POLITICS = "politics"
    FINANCIAL = "financial"
    SPORTS = "sports"
    CRYPTO = "crypto"
    WEATHER = "weather"
    ENTERTAINMENT = "entertainment"
    OTHER = "other"
```

SSOT: `strategy-service/engine/strategies/prediction/prediction_mapping.py`

### canonical_question_group SSOT (UAC `PREDICTION_GROUPS`)

Recurring market lifecycles (e.g. "BTC up/down hourly", "S&P up/down daily", "US presidential election 2028") cycle
through MULTIPLE `market_id`s over time. Polymarket creates a fresh `market_id` for each cycle: HOURLY = 24/day, DAILY =
1/day, ELECTION = 1 over months/years. The `canonical_question_group` is the workspace SSOT that ties these recurring
market_ids together for cross-instance analysis (volatility smiles across hourly bins, dispersion across daily strikes,
cross-platform arb pairing).

UAC SSOT: `unified_api_contracts.canonical.crosscutting.prediction_groups.PREDICTION_GROUPS` — closed-set enum mapping
each canonical question name to its component market_ids per cycle window.

### Per-market lifecycle timestamps

Every prediction-market `market_id` carries three lifecycle timestamps in instruments-service:

| Timestamp           | Meaning                                     |
| ------------------- | ------------------------------------------- |
| `market_created_at` | When the market was listed on the venue     |
| `resolution_time`   | When the outcome is determined (event-time) |
| `settlement_time`   | When payouts complete; market is closed     |

MTDS CLOB capture respects lifecycle bounds — NO ticks before `market_created_at`, NO new ticks after `settlement_time`.
A `LookaheadBiasError` at compute-time honours per-market lifecycle: a feature compute at time T can only consume ticks
where `tick.timestamp <= T` AND `tick.market_id`'s `market_created_at <= T`.

### Cluster validation per (canonical_question_group, day)

For BUNDLED prediction data_types, `ManifestWriter.record_captured` requires `expected_root_clusters` +
`cluster_extractor` per the workspace cluster-validation rule
([`../../../02-data/availability-manifest-and-data-status.md`](../../../02-data/availability-manifest-and-data-status.md)
§ "Cluster validation MANDATORY at record_captured"). Per `(canonical_question_group, day)`: HOURLY → 24 expected
market_ids, DAILY → 1, ELECTION → 1 spanning weeks/months. Under-coverage triggers `record_failed(ClusterCoverageError)`
instead of `record_captured`.

Lifecycle + canonical-group detail:
[`../../../02-data/prediction-schema-paths.md`](../../../02-data/prediction-schema-paths.md) +
[`../../../04-architecture/instruments-live-architecture.md`](../../../04-architecture/instruments-live-architecture.md).

### Proposed: Three-Tier Classification

Every prediction market should be classified along three dimensions:

**Tier 1 — Use case:**

| Use Case      | Description                            | Example                                     |
| ------------- | -------------------------------------- | ------------------------------------------- |
| `FEATURE`     | Signal for other strategies            | BTC sentiment → CeFi momentum model         |
| `TRADABLE`    | Direct execution target                | Buy YES on underpriced outcome              |
| `ARB_SURFACE` | Cross-platform or cross-instrument arb | Polymarket vs Kalshi, prediction vs options |
| `BOTH`        | Feature AND tradable                   | Most useful markets                         |

**Tier 2 — Domain mapping:**

| Domain      | Maps To                   | Cross-Reference                     |
| ----------- | ------------------------- | ----------------------------------- |
| `CRYPTO`    | CeFi/DeFi strategies      | BTC/ETH price, DeFi protocol events |
| `MACRO`     | TradFi strategies         | Fed rates, CPI, GDP, S&P levels     |
| `SPORTS`    | Sports strategies         | Match outcomes, player props        |
| `WEATHER`   | Features only (for now)   | Temperature, hurricane, rainfall    |
| `POLITICS`  | Features only (sentiment) | Election, policy outcomes           |
| `CORPORATE` | Features only             | Earnings, M&A, layoffs              |

**Tier 3 — Equivalent instrument mapping:**

| Prediction Market                        | Traditional Equivalent                   | Arb Possible?               |
| ---------------------------------------- | ---------------------------------------- | --------------------------- |
| "S&P above 5000 on Dec 31" (Kalshi)      | SPX binary call, strike 5000, exp Dec 31 | YES — compare implied probs |
| "Fed rate cut in March" (Kalshi)         | Fed Funds Futures (CME FedWatch)         | YES — compare implied probs |
| "BTC above $100k by June" (Polymarket)   | BTC binary option (Deribit)              | YES — compare implied probs |
| "Man Utd wins vs Arsenal" (Polymarket)   | Betfair back price for Man Utd           | YES — direct arb            |
| "Will it rain in NYC tomorrow?" (Kalshi) | No traditional equivalent                | NO — feature only           |

Codification gap:
[`prediction-markets-codification-gaps.md § G1 — Use-case classification`](../../operational/prediction-markets-codification-gaps.md#g1--use-case-classification).

## Instrument ID Convention

Prediction markets need a consistent instrument ID pattern:

```
{VENUE}:{MARKET_TYPE}:{EVENT_SLUG}@{OUTCOME}

Examples:
  POLYMARKET:BINARY:BTC_ABOVE_100K_DEC2025@YES
  POLYMARKET:BINARY:BTC_ABOVE_100K_DEC2025@NO
  KALSHI:BINARY:SP500_ABOVE_5000_DEC2025@YES
  KALSHI:BRACKET:HIGHNY_22NOV27@B58          (bracket = range market)
  POLYMARKET:CATEGORICAL:US_PRESIDENT_2028@HARRIS
```

Codification gap:
[`prediction-markets-codification-gaps.md § G2 — Instrument ID convention`](../../operational/prediction-markets-codification-gaps.md#g2--instrument-id-convention).

## Polymarket as a Feature Source

### How It Works Today

`polymarket_crowd_sentiment_calculator.py` in features-service (cross-instrument family):

- Polls Polymarket CLOB API for implied probabilities
- Feeds into cross-instrument feature signals
- No auth required (public endpoints)

### What's Valuable as Features

| Feature                                 | Source                    | Backtest-able? | Min History Needed         |
| --------------------------------------- | ------------------------- | -------------- | -------------------------- |
| BTC sentiment (implied prob of up/down) | Polymarket crypto markets | YES (~2yr)     | 1 year                     |
| Fed rate expectations                   | Kalshi fed rate series    | YES (~2yr)     | 6 months                   |
| Election/policy regime                  | Polymarket politics       | PARTIAL        | Not useful for backtesting |
| S&P range expectations                  | Kalshi S&P brackets       | YES (~1yr)     | 6 months                   |
| Weather (for commodities)               | Kalshi weather series     | YES (~2yr)     | 1 year                     |

### Semantic Grouping Problem

"Bitcoin above $95k on March 20" and "BTC price exceeds 95000 by end of March 20" are the SAME thing. Need NLP-based or
rule-based matching to group equivalent markets for stronger signals.

Codification gap:
[`prediction-markets-codification-gaps.md § G3 — Semantic market matching`](../../operational/prediction-markets-codification-gaps.md#g3--semantic-market-matching).

## Polymarket/Kalshi as Execution Venues

### The Alpha Opportunity

If our ML model predicts BTC goes up with 90% confidence and Polymarket prices "BTC up next hour" at 50% implied
probability:

- Buy YES at $0.50
- If correct: receive $1.00 → 100% return
- Expected value: 0.9 × $1.00 - $0.50 = $0.40 per contract (80% expected return!)

Compare to futures: same prediction might yield a few percent return on margin.

**This makes prediction markets potentially the highest-alpha execution venue** when our models have strong edge and the
market is mispriced.

### Short-Duration Markets

Kalshi and Polymarket both offer short-duration markets (hourly, daily):

- "BTC above $X in the next hour" (Polymarket)
- "S&P 500 daily high" (Kalshi daily series)
- These are directly tradable by our ML models

### Execution Flow

Same as any other strategy in the unified system:

```
features-service (publishes: ml_signal, prediction_market_price)
  → strategy-service receives event
    → if ml_confidence > threshold AND market_price < fair_value:
        → emit StrategyInstruction(PREDICTION_BET, side=YES, price=market_price)
          → execution-service/prediction_handler → Polymarket CLOB or Kalshi API
```

## Cross-Platform Arbitrage

### Types of Arb

**1. Intra-platform single-market:** YES + NO < $1.00 on same market (rare, <1%)

**2. Intra-platform multi-outcome:** Sum of all outcomes < $1.00 across categorical markets

**3. Cross-platform same-event:** Polymarket YES at 55%, Kalshi YES at 48% → buy Kalshi, sell Poly

- Minimum spread needed: ~2.5% after fees (Kalshi taker ~1.75%, Polymarket ~0%)
- Settlement timing difference risk: markets may resolve at slightly different times

**4. Prediction vs traditional instrument:** Kalshi "S&P above 5000" vs SPX binary option

- Compare implied probabilities
- Challenge: different settlement mechanisms, different liquidity, different fee structures

### PredictionArbStrategy (Full Strategy)

`PredictionArbStrategy` is a full strategy implementation, not just a feature surface:

**Strategy:** `strategy-service/engine/strategies/prediction_arb/prediction_arb_strategy.py` **Config:**
`prediction_arb_btc.yaml` (example config for BTC prediction arbitrage)

The strategy performs **outcome differential arbitrage** -- detecting when the same event is priced differently across
prediction market venues. It scans for:

- **Cross-venue arb:** YES_a + NO_b < 1.0 across Polymarket, Kalshi, and Betfair
- **Neg-risk bucket arb:** Probability buckets that sum to < 1.0 within a single venue
- **Prediction vs sportsbook arb:** Same event on Polymarket vs traditional bookmakers

**Execution path:** PredictionArbStrategy emits `StrategyInstruction` -> execution-service -> `prediction_handler.py` ->
Polymarket CLOB adapter (`polymarket_clob.py`) or Kalshi adapter (`kalshi.py`).

The Polymarket CLOB adapter uses `py-clob-client` for order placement on the CLOB (Central Limit Order Book) -- not the
legacy Gamma API. Kalshi adapter uses the Kalshi REST API with authenticated trading endpoints.

> **⚠️ This section describes the LEGACY `prediction_arb/` strategy — NOT the v2 archetype.** The v2 cross-venue
> detector is a separate, currently-shipping code path: `features-service` `cross_venue_arb_detector.py` +
> `strategy-service` `arbitrage_structural/prediction_venue_dispersion.py`. It differs in three ways that matter: (1) it
> is an **N-venue best-pair scan** over Kalshi / Polymarket / **Betfair** (odds de-vigged to probabilities), not a fixed
> venue pair; (2) it gates on **NET-of-fees** edge (`gross − fee(buy_leg) − fee(sell_leg) >= entry_threshold`), so the
> "~2.5% after fees" rule of thumb above is superseded by an explicit per-venue fee model; (3) Betfair is
> **BUY-YES-only** today because persisted odds are BACK-side only. **SSOT:**
> [`../../../04-architecture/cross-venue-prediction-arb-detection.md`](../../../04-architecture/cross-venue-prediction-arb-detection.md).

**Cross-platform matching** uses `CanonicalPredictionMarket` from `prediction_mapping.py` to normalize event
descriptions across venues into matchable canonical forms.

### Existing: UAC Internal Arb Schemas

Already implemented at
`unified-api-contracts/unified_api_contracts/internal/domain/prediction_market/prediction_market_arb.py`:

- `CrossVenueLink` — for same-event cross-platform arb
- `BucketMarket` + `ProbabilityBucket` — for neg-risk bucket arb
- `SportsbookLink` — Polymarket vs traditional sportsbooks

## Data Download & Research

### Getting Started: Pull Market Data

To understand what's available, pull a snapshot of all active markets:

```python
# Polymarket — all active events with markets
import requests
events = []
offset = 0
while True:
    resp = requests.get(
        "https://gamma-api.polymarket.com/events",
        params={"closed": "false", "limit": 50, "offset": offset}
    )
    batch = resp.json()
    if not batch: break
    events.extend(batch)
    offset += 50

# Kalshi — all active markets
markets = []
cursor = None
while True:
    params = {"status": "open", "limit": 100}
    if cursor: params["cursor"] = cursor
    resp = requests.get(
        "https://api.elections.kalshi.com/trade-api/v2/markets",  # Updated 2026-05-22: migrated from trading-api.kalshi.com per kalshi_api_migration_to_elections_subdomain_2026_05_20.md
        params=params, headers=kalshi_auth_headers()
    )
    data = resp.json()
    markets.extend(data["markets"])
    cursor = data.get("cursor")
    if not cursor: break
```

### Classification Output

For each market, determine:

1. **Category** (CRYPTO, MACRO, SPORTS, WEATHER, POLITICS, CORPORATE)
2. **Use case** (FEATURE, TRADABLE, ARB_SURFACE, BOTH)
3. **Equivalent traditional instrument** (if any)
4. **Cross-platform match** (if same event exists on other platform)
5. **Historical depth** (how long has this market/series existed?)
6. **Liquidity** (volume, open interest, bid-ask spread)

Codification gap:
[`prediction-markets-codification-gaps.md § G4 — Automated market classifier`](../../operational/prediction-markets-codification-gaps.md#g4--automated-market-classifier).

## Key Academic Research

| Paper                                                         | Finding                                           |
| ------------------------------------------------------------- | ------------------------------------------------- |
| "Unravelling the Probabilistic Forest" (arXiv:2508.03474)     | ~$40M arb profits on Polymarket Apr 2024-Apr 2025 |
| "Semantic Non-Fungibility" (arXiv:2601.01706)                 | Why equivalent markets trade at different prices  |
| "Price Discovery in Modern Prediction Markets" (SSRN:5331995) | Polymarket leads Kalshi in price discovery        |

## Open-Source Tools

| Tool                                   | Use                                       |
| -------------------------------------- | ----------------------------------------- |
| `py-clob-client` (Polymarket official) | Trading + market data                     |
| `kalshi-python` (Kalshi official)      | Trading + market data                     |
| `Polymarket/agents` (official)         | AI agent framework for autonomous trading |
| `polymarket-apis` (third-party)        | Unified wrapper with Pydantic validation  |
| `Dome API` (domeapi.io)                | Unified cross-platform API (YC-backed)    |
| EventArb, ArbBets                      | Cross-platform arb detection              |

## Integration gaps

Full gap register:
[`prediction-markets-codification-gaps.md`](../../operational/prediction-markets-codification-gaps.md). G1–G7 cover
use-case enum (G1), instrument ID convention (G2), semantic market matching (G3), automated classifier (G4), venue
registry wiring (G5), Kalshi testnet (G6), and historical data pipeline (G7).

## References

- **Polymarket adapters:**
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/polymarket_adapter.py`
- **Kalshi adapters:**
  `market-tick-data-service/market_tick_data_service/market_interface/adapters/prediction/kalshi_adapter.py`
- **Execution:** `execution-service/adapters/exchanges/polymarket_clob.py`
- **Strategy:** `strategy-service/engine/strategies/prediction_arb/prediction_arb_strategy.py`
- **Features:** `features-service (cross-instrument family)/calculators/polymarket_crowd_sentiment_calculator.py`
- **Arb schemas:**
  `unified-api-contracts/unified_api_contracts/internal/domain/prediction_market/prediction_market_arb.py`
- **Polymarket docs:** https://docs.polymarket.com/
- **Kalshi docs:** https://docs.kalshi.com/
