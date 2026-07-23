---
doc_type: codex-ssot
title: Backfill & Live Startup Architecture
summary:
  Backfill-then-live startup — pipeline orchestrator reads seed_spec.yaml per-service min/recommended lookback (features
  30-90d, ml-training 180-365d, execution cold-start), runs batch in topological order, then switches to live with a
  lookback ring-buffer; downtime-gap recovery bands.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    deployment-service,
    execution-service,
    features-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: [backfill, pipeline, features, ml, live-trading, infrastructure]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/backtest-groups.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-03-27
authoritative_for: [backfill-then-live startup and lookback warm-up sequencing]
referenced_by: [/codex/15-runbooks/backfill-completion-playbook.md]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Backfill & Live Startup Architecture

## Problem

When starting a live deployment or recovering from downtime, every service needs historical data to function:

- **Feature services** need 30-90 days of candle history for lookback windows (RSI 14, SMA 200, etc.)
- **ML training** needs 180-365 days of feature history to train models
- **ML inference** needs a trained model (which needs training data)
- **Strategy service** needs recent feature snapshots + model predictions
- **Execution service** can cold-start (no history needed)
- **Risk service** needs current positions (loaded from position-balance-monitor)

Without a structured backfill, live mode fails silently — features return NaN for the first N candles, ML models have no
training data, strategies generate no signals.

## Architecture: Backfill-Then-Live

```
                    BACKFILL PHASE                         LIVE PHASE
                    (batch mode, historical)               (streaming, real-time)

instruments    ──── batch(T-N..T) ─────────────────────── live(T+)
                         │
market-tick    ──── batch(T-N..T) ─────────────────────── live(T+) via WebSocket
                         │
features       ──── batch(T-N..T) lookback warm-up ────── live(T+) via PubSub
                         │
ml-training    ──── batch(T-365..T) train model ───────── (retrain on schedule)
                         │
ml-inference   ──── load model ────────────────────────── live(T+) predict on new features
                         │
strategy       ──── batch(T-1..T) generate signals ────── live(T+) on new predictions
                         │
execution      ──── (cold start) ──────────────────────── live(T+) execute signals
```

## Backfill Specification (per-service)

Defined in `seed_spec.yaml` → read by pipeline orchestrator:

```yaml
backfill:
  instruments-service:       { min_days: 0,   recommended_days: 0,   cold_start: true }
  market-tick-data-service:  { min_days: 1,   recommended_days: 7,   cold_start: false }
  features-service (delta-one family):{ min_days: 30,  recommended_days: 90,  cold_start: false }
  features-service (calendar family): { min_days: 0,   recommended_days: 365, cold_start: true }
  ml-training-service:       { min_days: 180, recommended_days: 365, cold_start: false }
  ml-inference-service:      { min_days: 0,   recommended_days: 0,   cold_start: true, requires: [ml-training-service] }
  strategy-service:          { min_days: 1,   recommended_days: 30,  cold_start: false }
  execution-service:         { min_days: 0,   recommended_days: 0,   cold_start: true }
```

`BackfillSpec` schema defined in `unified_api_contracts.internal.domain.ml.schemas`.

## How It Works

### 1. Pipeline Orchestrator Calculates Backfill Window

```python
today = date.today()
for service in topological_order(services):
    spec = load_backfill_spec(service.name)
    start_date = today - timedelta(days=spec.recommended_lookback_days)

    if spec.cold_start and no_history_available(service):
        logger.info(f"{service.name} supports cold start — skipping backfill")
        continue

    # Run batch mode for backfill window
    run_service(
        service=service.name,
        operation=service.default_operation,
        mode="batch",
        start_date=start_date,
        end_date=today,
    )
```

### 2. Batch Backfill Runs in Dependency Order

Same pipeline as production batch, just for the backfill window:

```
Layer 1: instruments-service  --operation instruments --mode batch --start-date T-365 --end-date T
Layer 2: market-tick-data     --operation download    --mode batch --start-date T-90  --end-date T
Layer 3: features-delta-one   --operation compute     --mode batch --start-date T-90  --end-date T
         features-calendar    --operation compute     --mode batch --start-date T-365 --end-date T  (cold-start OK)
         features-volatility  --operation compute     --mode batch --start-date T-90  --end-date T
         ... (all feature services in parallel)
Layer 4: ml-training          --operation train       --mode batch --start-date T-365 --end-date T
Layer 5: ml-inference         --operation predict     --mode batch --start-date T-1   --end-date T
Layer 6: strategy-service     --operation backtest    --mode batch --start-date T-1   --end-date T
```

### 3. Switch to Live Mode

Once backfill is complete:

```
instruments-service  --operation instruments --mode live
market-tick-data     --operation live        --mode live
features-delta-one   --operation compute-live --mode live
strategy-service     --operation trade       --mode live
execution-service    --operation live_execution --mode live
```

Live services read the last N candles from the batch output (GCS) as their lookback buffer, then subscribe to PubSub for
new data. The lookback buffer seamlessly transitions from historical to real-time.

### 4. How Lookback Buffer Works

Each feature calculator declares its `max_lookback_periods` (e.g., RSI needs 14, SMA 200 needs 200). The orchestration
layer loads `lookback_days` of historical candles BEFORE the live subscription starts:

```python
# In live mode startup:
lookback_candles = get_date_range(today - lookback_days, today)  # from GCS
buffer = RingBuffer(size=max_lookback_periods)
buffer.extend(lookback_candles)

# Then subscribe to live candles
async for candle in pubsub_subscription:
    buffer.append(candle)
    features = calculator.compute(buffer.to_dataframe())
    publish(features)
```

## Recovery from Downtime

If a service crashes and restarts:

1. **Check last processed timestamp** from GCS event log or DataSink
2. **Calculate gap**: `gap = now() - last_processed`
3. **If gap < lookback buffer**: Resume live mode (buffer still valid)
4. **If gap > lookback buffer but < recommended_lookback**: Backfill the gap, then resume live
5. **If gap > recommended_lookback**: Full backfill required

## Mock → Live Transition

The mock pipeline uses the SAME backfill architecture:

1. `CLOUD_MOCK_MODE=true` → mock providers generate synthetic historical data
2. Switch to `CLOUD_MOCK_MODE=false` → same services read from real GCS
3. The data format, path conventions, and service interfaces are IDENTICAL

The only difference is the data SOURCE — synthetic vs real. The code path is the same.

## Deployment Service Integration

The deployment-service's pipeline orchestrator reads `backfill` from `seed_spec.yaml` and runs services in topological
order with calculated date ranges. This is the entry point for:

- **Initial deployment**: Full backfill (365 days features, 365 days ML training)
- **Category bootstrap**: Deploy a new category (e.g., SPORTS) with its own backfill
- **Recovery**: Backfill the gap since last successful run
- **Scheduled retraining**: ML models retrained weekly/monthly with rolling window
