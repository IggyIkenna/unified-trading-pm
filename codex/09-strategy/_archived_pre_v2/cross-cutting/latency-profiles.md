---
scope: [engineer, admin]
---

> **[SUPERSEDED]** This document describes pre-v2 strategy architecture. Current canonical design:
> `codex/09-strategy/architecture-v2/`. Do not use this document for implementation decisions.

# Latency Profiles — Cross-Cutting Concern

## Hard Rules

### 1. Latency requirements are per-strategy-archetype, not global

There is no system-wide latency SLA. A funding rate harvest strategy tolerating 5-second signal-to-order is fine. A
market-making strategy needing sub-100ms is a different class entirely. Each archetype declares its latency profile in
config, and the system validates that the deployment topology can meet it.

### 2. Batch mode has no latency requirements

Batch mode replays historical data through the same `EventDrivenStrategyEngine`. There are no latency constraints — the
system processes events as fast as compute allows. Latency profiles apply exclusively to live mode.

### 3. Latency is measured end-to-end in three segments

```
SEGMENT 1: Tick-to-Signal
  Market event (WebSocket tick, block confirmation, odds update)
    → market-tick-data-service (normalization)
      → features-*-service (feature computation)
        → strategy-service (signal generation)
          = StrategyInstruction emitted

SEGMENT 2: Signal-to-Order
  StrategyInstruction
    → execution-service (instruction routing)
      → algorithm selection + child order generation
        → venue adapter (UTEI / UDEI)
          = Order submitted to venue

SEGMENT 3: Order-to-Fill
  Order submitted
    → venue matching engine / blockchain confirmation
      → fill notification received
        → execution-service (fill processing)
          = CanonicalFill recorded
```

## Venue Latency Baselines

### CeFi Venues

| Venue       | WebSocket Tick | REST Round-Trip | Order Submission | Fill Notification | Notes                          |
| ----------- | -------------- | --------------- | ---------------- | ----------------- | ------------------------------ |
| Binance     | 10–30 ms       | 50–150 ms       | 20–50 ms         | 10–30 ms          | Co-location available          |
| Deribit     | 10–25 ms       | 40–120 ms       | 15–40 ms         | 10–25 ms          | Options + futures              |
| Hyperliquid | 15–40 ms       | 30–80 ms        | 20–60 ms         | 15–40 ms          | L1 order book, on-chain settle |
| OKX         | 10–30 ms       | 50–200 ms       | 20–60 ms         | 10–30 ms          | Multi-product                  |
| Bybit       | 15–40 ms       | 60–200 ms       | 25–70 ms         | 15–40 ms          | Derivatives focused            |

**Measurement point:** From the UMI WebSocket adapter receiving bytes to the application processing the parsed message.
Network latency to the venue is the dominant factor and depends on deployment region (asia-northeast1 for most CeFi
venues).

### DeFi Venues

| Chain/Protocol | Block Time | Tx Confirmation | Finality     | Notes                      |
| -------------- | ---------- | --------------- | ------------ | -------------------------- |
| Ethereum L1    | 12 seconds | 12–24 seconds   | ~15 minutes  | Slot-based, post-merge     |
| Arbitrum       | 250 ms     | 250 ms–1 s      | ~7 days (L1) | Soft finality near-instant |
| Optimism       | 2 seconds  | 2–4 seconds     | ~7 days (L1) | Sequencer-based            |
| Base           | 2 seconds  | 2–4 seconds     | ~7 days (L1) | OP Stack                   |
| Polygon        | 2 seconds  | 2–4 seconds     | ~30 minutes  | PoS finality               |

**Key insight:** DeFi latency is dominated by block time, not network latency. A swap on Ethereum L1 takes a minimum of
12 seconds regardless of how fast the system submits the transaction. This makes DeFi strategies fundamentally different
from CeFi strategies in latency sensitivity.

### TradFi Venues

| Venue/Protocol | Protocol | Order Latency | Fill Latency | Notes                |
| -------------- | -------- | ------------- | ------------ | -------------------- |
| CME Globex     | FIX 4.2  | 1–5 ms        | 1–5 ms       | Co-location required |
| CBOE           | FIX 4.2  | 2–8 ms        | 2–8 ms       | Options market       |
| LSE            | FIX 5.0  | 3–10 ms       | 3–10 ms      | Equities             |
| LMAX           | FIX 4.4  | 1–3 ms        | 1–3 ms       | FX, streaming prices |

**Note:** The system does NOT compete at HFT latencies (sub-microsecond). TradFi strategies target medium-frequency
(seconds to minutes), where 5–50ms order latency is acceptable.

### Sports / Prediction

| Source     | API Latency | Odds Update Frequency | Notes                         |
| ---------- | ----------- | --------------------- | ----------------------------- |
| Betfair    | 50–200 ms   | 50–500 ms             | Exchange model, streaming API |
| Pinnacle   | 100–300 ms  | 1–5 seconds           | Sharp book, REST polling      |
| Polymarket | 50–150 ms   | Event-driven          | On-chain settlement           |
| Kalshi     | 50–200 ms   | Event-driven          | Regulated US exchange         |

## End-to-End Latency by Strategy Archetype

### Latency Profiles Table

| Archetype             | Tick-to-Signal | Signal-to-Order | Order-to-Fill | Total E2E | Category |
| --------------------- | -------------- | --------------- | ------------- | --------- | -------- |
| Market Making         | < 50 ms        | < 50 ms         | Venue-dep.    | < 100 ms  | Low      |
| Statistical Arb       | < 100 ms       | < 100 ms        | Venue-dep.    | < 200 ms  | Low      |
| Cross-Exchange Arb    | < 200 ms       | < 100 ms        | Venue-dep.    | < 300 ms  | Low      |
| Delta-One Basis       | < 5 s          | < 2 s           | < 30 s        | < 37 s    | Medium   |
| Mean Reversion        | < 2 s          | < 1 s           | Venue-dep.    | < 3 s     | Medium   |
| Momentum              | < 5 s          | < 2 s           | Venue-dep.    | < 7 s     | Medium   |
| Calendar Spread       | < 5 s          | < 2 s           | Venue-dep.    | < 7 s     | Medium   |
| Volatility Arb        | < 10 s         | < 5 s           | Venue-dep.    | < 15 s    | Medium   |
| DeFi Recursive Basis  | < 30 s         | < 5 s           | 12–24 s (L1)  | < 60 s    | High     |
| Funding Rate Harvest  | < 60 s         | < 10 s          | Venue-dep.    | < 70 s    | High     |
| Yield Optimization    | < 300 s        | < 30 s          | 12–24 s (L1)  | < 360 s   | High     |
| Liquidation Sniper    | < 1 s          | < 500 ms        | 12 s (L1)     | < 14 s    | Special  |
| Sports Arbitrage      | < 500 ms       | < 200 ms        | < 1 s         | < 2 s     | Low      |
| Prediction Contrarian | < 60 s         | < 10 s          | < 5 s         | < 75 s    | High     |

### Latency Categories

| Category | Description                       | Deployment Implication                     |
| -------- | --------------------------------- | ------------------------------------------ |
| Low      | Sub-second total E2E              | Co-located or same-region as venue         |
| Medium   | Seconds to tens of seconds        | Standard Cloud Run deployment sufficient   |
| High     | Minutes acceptable                | Batch-adjacent, can tolerate cold starts   |
| Special  | Mixed — fast detection, slow fill | Fast signal path, fill bound by blockchain |

## Internal Service Latency Budget

### Feature Computation Pipeline

```
market-tick-data-service:
  WebSocket message received → normalized CanonicalTick
  Budget: < 5 ms per tick

market-data-processing-service:
  CanonicalTick → candle aggregation → publish
  Budget: < 10 ms per candle close

features-*-service (7 services):
  Candle/tick event → feature vector computation → publish to pub/sub
  Budget: < 100 ms per feature update (single instrument)
  Budget: < 500 ms per feature update (full universe scan)

ml-inference-api:
  Feature vector → model inference → ML signal
  Budget: < 50 ms per prediction (warm model)
  Budget: < 500 ms per prediction (cold start, model load)
```

### Strategy Decision Pipeline

```
strategy-service:
  Feature/signal event received → generate_signal() → StrategyInstruction
  Budget: < 20 ms per strategy evaluation (single archetype)
  Budget: < 200 ms per strategy evaluation (complex multi-leg)

  Includes:
    - CostEstimator.estimate(): < 2 ms
    - RiskMonitor.check(): < 5 ms
    - ExposureMonitor.get_exposure(): < 2 ms (cached)
    - Signal logic: < 10 ms
```

### Execution Pipeline

```
execution-service:
  StrategyInstruction → route → algo → child orders → submit
  Budget: < 50 ms (simple market/limit order)
  Budget: < 200 ms (TWAP/VWAP first child)
  Budget: < 500 ms (SOR with multi-venue quote comparison)
  Budget: < 2 s (DeFi atomic bundle construction + gas estimation)
```

## Circuit Breaker Thresholds

Circuit breakers trigger when latency exceeds safe operating bounds. The execution-service owns the 3-state circuit
breaker machine (CLOSED / OPEN / HALF-OPEN).

### Per-Venue Circuit Breakers

| Condition                   | Action             | Recovery                         |
| --------------------------- | ------------------ | -------------------------------- |
| API response > 5x baseline  | OPEN — stop orders | HALF-OPEN after 30s, probe order |
| 3 consecutive timeouts      | OPEN — stop orders | HALF-OPEN after 60s              |
| WebSocket disconnect        | OPEN — stop orders | HALF-OPEN on reconnect           |
| Fill latency > 10x baseline | WARN — reduce size | Auto-recover when latency drops  |

### Feature Freshness Circuit Breakers

| Condition                          | Action                               | Recovery                    |
| ---------------------------------- | ------------------------------------ | --------------------------- |
| Feature age > 2x expected interval | WARN — log stale feature             | Auto-clear on fresh feature |
| Feature age > 5x expected interval | OPEN — strategy generates no signals | Clear on fresh feature      |
| No features for > 10 minutes       | CRITICAL — alert, pause strategy     | Manual intervention         |

**Integration:** `FreshnessMonitor` in strategy-service tracks feature timestamps. If the latest feature for a
subscribed source is older than `max_feature_age_seconds` (from strategy config), the strategy returns no-op and emits a
`FEATURE_STALE` event via unified-trading-library.

### DeFi-Specific Circuit Breakers

| Condition                        | Action                       | Recovery                      |
| -------------------------------- | ---------------------------- | ----------------------------- |
| Gas price > `max_gas_price_gwei` | SKIP — do not submit tx      | Auto-resume when gas drops    |
| RPC node latency > 2s            | Failover to backup RPC       | Return to primary after 5 min |
| 3 consecutive tx reverts         | OPEN — pause DeFi operations | Manual review required        |
| Block reorg detected             | CRITICAL — halt all DeFi     | Manual confirmation of state  |

## Monitoring and Observability

### Latency Metrics (Prometheus)

Every service emits latency histograms:

```
# market-tick-data-service
market_tick_processing_seconds{venue, instrument}

# features-*-service
feature_computation_seconds{feature_set, instrument}

# strategy-service
signal_generation_seconds{strategy_id, client_id}

# execution-service
order_submission_seconds{venue, algo}
order_fill_seconds{venue, order_type}
```

### End-to-End Latency Tracing

`correlation_id` propagates through the entire pipeline:

```
tick received (t0)
  → correlation_id = f"{venue}:{instrument}:{timestamp_ns}"
    → feature computed (t1) — segment_1 = t1 - t0
      → signal generated (t2) — segment_2 = t2 - t1
        → order submitted (t3) — segment_3 = t3 - t2
          → fill received (t4) — segment_4 = t4 - t3

Total E2E = t4 - t0
```

Each segment is logged with the correlation_id, enabling latency attribution across services.

### Latency Alerting Rules

| Metric                   | WARN Threshold | CRITICAL Threshold | Action                       |
| ------------------------ | -------------- | ------------------ | ---------------------------- |
| tick_to_signal (Low cat) | > 200 ms       | > 1 s              | Investigate feature pipeline |
| signal_to_order          | > 500 ms       | > 2 s              | Check execution-service load |
| feature_computation      | > 1 s          | > 5 s              | Scale features service       |
| venue_api_latency        | > 3x baseline  | > 5x baseline      | Circuit breaker may trigger  |

## Algo Benchmarking: AlgoComparisonRunner

The `AlgoComparisonRunner` in `execution-service/execution_service/algo_library/algo_comparison.py` provides a pure
simulation framework for comparing execution algorithms. It never submits live orders.

**Use cases:**

- **Pre-trade algo selection:** Pick the best algo for a given order profile before live execution
- **Backtesting:** Compare TWAP vs VWAP vs POV vs Almgren-Chriss on historical data
- **CI regression:** Assert that algorithm improvements are additive (no performance regression)

**How it works:**

```
runner = AlgoComparisonRunner()
runner.register("TWAP-10min", TWAPAlgorithm, TWAPConfig(...))
runner.register("VWAP-10min", VWAPAlgorithm, VWAPConfig(...))
runner.register("AlmgrenChriss", AlmgrenChrissAlgorithm, AlmgrenChrissConfig(...))
report = runner.run()
# report.recommended_algo = "AlmgrenChriss"
# report.recommendation_reason = "highest slice count (60 orders, avg_interval=10s)"
```

Each registered algorithm's `get_child_orders()` method is called (NOT `execute()`). The runner compares:

| Metric                     | Measured From                                 |
| -------------------------- | --------------------------------------------- |
| `num_child_orders`         | Total slices generated                        |
| `total_quantity_scheduled` | Sum of all child order quantities             |
| `avg_interval_seconds`     | Average time between consecutive child orders |
| `estimated_slippage_bps`   | Estimated market impact (from cost metrics)   |
| `participation_rate_pct`   | Order size relative to expected volume        |

**Current recommendation heuristic:** Prefers the algo with the most child orders (finest granularity), as more slices
generally means lower market impact for large orders. Future: replace with Almgren-Chriss cost minimisation model.

The runner is fault-tolerant: errors from individual algo runs are captured in the result (`AlgoRunResult.error`) rather
than propagating.

**SSOT:** `execution-service/execution_service/algo_library/algo_comparison.py`

## SSOT References

| Concept            | SSOT                     | Location                                                                                       |
| ------------------ | ------------------------ | ---------------------------------------------------------------------------------------------- |
| Circuit breaker    | execution-service        | `execution-service/execution_service/engine/`                                                  |
| WebSocket adapters | UMI                      | `market-tick-data-service/market_tick_data_service/market_interface/unified_market_interface/` |
| Feature freshness  | strategy-service         | `strategy-service/strategy_service/monitors/`                                                  |
| Latency metrics    | Per-service Prometheus   | Each service's `/metrics` endpoint                                                             |
| Correlation ID     | unified-trading-library  | `unified_trading_library.events/correlation.py`                                                |
| RPC URL templates  | UAC registry             | `unified-api-contracts/registry/capability_declarations/`                                      |
| DeFi block times   | features-onchain-service | Chain-specific feature calculators                                                             |
