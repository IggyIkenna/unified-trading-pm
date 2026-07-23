---
doc_type: codex-ssot
title: Data Flow Map -- Batch/Live Storage Topology
summary:
  "Batch/live GCS/S3 storage topology map: per-pipeline writer→bucket-path→reader across all services
  (execution/instruments/market-data/features/ML/risk/PnL/recon/alerting/deployment), orphan-path analysis, and the
  end-to-end data-flow summary."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-ui,
    execution-service,
  ]
scope: [engineer, admin]
tags: [data-flow, storage, gcs, pipeline, topology, orphan-paths]
related:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/strategy-service-architecture.md,
    /codex/06-coding-standards/strategy-identity-versioning.md,
  ]
created: 2026-03-27
authoritative_for: [batch-live GCS/S3 storage topology map (writer-bucket-reader wiring)]
referenced_by:
  [
    /codex/03-observability/coordination-events.md,
    /codex/03-observability/lifecycle-events.md,
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/data-ownership-principles.md,
  ]
owner:
last_reviewed: 2026-05-20
code_refs:
---

# Data Flow Map -- Batch/Live Storage Topology

> Generated 2026-03-14 by codebase analysis. This document maps GCS/S3 write and read paths across the Unified Trading
> System, identifying the service that writes, the bucket path, and the service(s) that read from it.

> **⚠️ Migration note (2026-05-20)**: `risk-and-exposure-service` → `strategy_service/risk/`,
> `position-balance-monitor-service` → `strategy_service/position/`, `pnl-attribution-service` →
> `strategy_service/pnl/`. Data paths and GCS layout unchanged; writer is now `strategy-service --operation <op>`. See
> [`strategy-service-architecture.md`](strategy-service-architecture.md).

## Conventions

- Bucket names use the template `{purpose}-{category}-{project_id}` (GCP) or equivalent (AWS).
- All storage access goes through UCI (`get_storage_client()`, `DataSink`, `DataSource`, `get_data_sink()`,
  `get_data_source()`).
- `{P}` = `$GCP_PROJECT_ID` / `$PROJECT_ID` throughout.

---

## 1. Execution Results Pipeline

```
execution-service
  writes -> execution-store-{P}/results/{venue}/{date}/*.parquet
  writes -> execution-store-{P}/results/{venue}/{date}/fills/{fill_id}.json
  writes -> execution-store-{P}/configs/*.json

execution-results-api
  reads  <- execution-store-{P}/results/**
  reads  <- execution-store-{P}/configs/**
  reads  <- strategy-store-{P}/** (strategy configs)
  serves -> execution-analytics-ui

execution-results-api also reads:
  reads  <- instruments-store-{category}-{P}/instrument_availability/**
```

### Fill Store

```
execution-service  -> execution-store-{P}/results/{venue}/{date}/fills/{fill_id}.json
execution-results-api <- (reads fills, 60s TTL cache)
  serves -> execution-analytics-ui (/api/v1/fills, /api/v1/stream/fills)
```

---

## 2. Instruments Pipeline

```
instruments-service
  writes -> instruments-store-{category}-{P}/instrument_availability/by_date/day-{date}/instruments.parquet
  (categories: cefi, tradfi, defi)

Readers:
  execution-service         <- instruments-store-{category}-{P}/ (instrument definitions)
  execution-results-api     <- instruments-store-{category}-{P}/ (instrument browsing)
  features-service (delta-one family) <- instruments-store-{category}-{P}/ (instrument defs for batch)
  deployment-api            <- instruments-store-{category}-{P}/ (data status dashboards)
```

---

## 3. Market Data Pipeline

```
market-tick-data-service
  writes -> market-data-tick-{category}-{P}/processed_candles/{instrument_type}/{venue}/{instrument}/{date}.parquet
  (categories: cefi, tradfi, defi)

Readers:
  features-service (delta-one family) <- market-data-tick-{category}-{P}/ (input for feature calculation)
  execution-results-api      <- market-data-tick-{category}-{P}/ (/api/v1/data/tick-data)
  deployment-api             <- market-data-tick-{category}-{P}/ (data status checks)
```

---

## 4. Features Pipeline

```
features-service (delta-one family)
  reads  <- market-data-tick-{category}-{P}/ (candle data)
  writes -> features-delta-one-{category}-{P}/{feature_group}/{date}/*.parquet

Other feature services (same pattern, different bucket prefix):
  features-service (calendar family)  -> calendar-features-{P}/ (via get_writer("calendar_features"))
  features-service (volatility family) -> features-volatility-{category}-{P}/
  features-service (commodity family)  -> features-commodity-{category}-{P}/
  features-service (cross-instrument family) -> features-cross-instrument-{category}-{P}/
  features-service (multi-timeframe family)  -> features-multi-timeframe-{category}-{P}/
  features-service (onchain family)   -> features-onchain-{P}/
  features-service (sports family)    -> features-sports-{P}/

Readers:
  ml-inference-service <- features-*-{P}/ (feature input for predictions)
  ml-training-service  <- features-*-{P}/ (training data)
```

---

## 5. ML Pipeline

```
ml-training-service
  writes -> ml-models-{P}/models/{model_id}/artifacts/
  writes -> ml-models-{P}/experiments/{run_id}/

ml-inference-service
  reads  <- ml-models-{P}/models/ (model artifacts via storage_adapter)
  reads  <- features-*-{P}/ (feature input)
  writes -> predictions-{P}/{mode}/{date}/*.parquet (via DataSink / prediction_publisher)

ml-training-api
  reads  <- ml-models-{P}/experiments/ (experiment metadata)
  serves -> ml-training-ui

ml-inference-api
  reads  <- ml-models-{P}/models/ (model registry)
  serves -> ml-training-ui (dual_base -- inference panel)
```

---

## 6. Risk & Position Pipeline

```
risk-and-exposure-service
  writes -> {P}-risk/risk/{client_id}/{date}/exposure_summary.json

position-balance-monitor-service
  writes -> positions-{P}/ (via PATH_REGISTRY / get_writer("positions"))
  reads  <- execution-store-{P}/results/ (fill events)

Readers:
  client-reporting-api <- (risk snapshots, indirectly)
```

---

## 7. PnL & Reporting Pipeline

```
pnl-attribution-service
  reads  <- execution-store-{P}/results/ (execution fills)
  writes -> pnl-{P}/pnl/{period_month}/{client_id}/*.parquet

client-reporting-api
  reads  <- pnl-{P}/pnl/{period_month}/{client_id}/ (via DataSource, routing_key="pnl")
  serves -> client-reporting-ui
```

---

## 8. Reconciliation Pipeline

```
batch-live-reconciliation-service
  reads  <- {P}-events/ (event logs)
  reads  <- execution-store-{P}/ (execution data)
  writes -> recon-{P}/recon/summary_{date}.json
  writes -> recon-{P}/recon/{stage}_recon_report_{date}.json
  writes -> recon-{P}/recon/agent_report_{date}.md
  writes -> recon-{P}/recon/index.json

unified-trading-api
  reads  <- recon-{P}/recon/** (all recon reports)
  serves -> unified-trading-system-ui (/recon/*)
```

---

## 9. Settlement & Fee Schedule Pipeline

```
unified-trading-api (self-contained read/write)
  reads/writes -> {TRADING_ANALYTICS_GCS_BUCKET}/settlements/records.ndjson
  reads/writes -> {TRADING_ANALYTICS_GCS_BUCKET}/fee-schedules/entries.ndjson
  reads/writes -> {TRADING_ANALYTICS_GCS_BUCKET}/fee-schedules/prime_brokers.ndjson
  reads/writes -> {TRADING_ANALYTICS_GCS_BUCKET}/fee-schedules/client_pb_links.ndjson
  serves -> unified-trading-system-ui (/settlements/*, /prime-brokers/*, /clients/*/fee-schedule)
  serves -> settlement-ui (/settlements/*)
```

---

## 10. Deployment State Pipeline

```
deployment-api (self-contained read/write for deployment state)
  reads/writes -> {STATE_BUCKET}/deployments/
  reads/writes -> {STATE_BUCKET}/service-status/
  reads         <- execution-store-{P}/ (EXECUTION_STORE_BUCKET -- data status)
  reads         <- strategy-store-cefi-{P}/ (STRATEGY_STORE_CEFI_BUCKET)
  reads         <- strategy-store-tradfi-{P}/ (STRATEGY_STORE_TRADFI_BUCKET)
  reads         <- strategy-store-defi-{P}/ (STRATEGY_STORE_DEFI_BUCKET)
  reads         <- ml-configs-store-{P}/ (ML_CONFIGS_STORE_BUCKET)
  reads         <- market-data-tick-*-{P}/ (data status checks)
  reads         <- instruments-store-*-{P}/ (data status checks)
  serves -> deployment-ui
  (Uses GCS FUSE mounts at /mnt/gcs/{bucket} in production for faster reads)
```

---

## 11. Audit Trail & Logs Pipeline

```
All services (via unified-trading-library)
  writes -> {P}-events/events/{service}/{date}/*.jsonl

batch-audit-api
  reads  <- {P}-events/events/ (audit trail, logs, compliance)
  reads  <- alerting/history/date={YYYY-MM-DD}/events.jsonl (alert history)
  serves -> batch-audit-ui
  serves -> logs-dashboard-ui (/api/v1/logs, /api/v1/services, /api/v1/audit/trail)
```

---

## 12. Alerting Pipeline

```
alerting-service
  writes -> {ALERTING_BUCKET}/alerting/history/date={YYYY-MM-DD}/events.jsonl (alert events)
  writes -> {ALERTING_BUCKET}/alerting/configs/ (routing rule snapshots, YAML)
  writes -> {ALERTING_BUCKET}/alerting/state/ (cooldown state, JSON)

batch-audit-api
  reads  <- {ALERTING_BUCKET}/alerting/history/ (alert history for logs-dashboard-ui AlertsView)
  serves -> logs-dashboard-ui (/api/v1/audit/trail with event_type filter)
  serves -> live-health-monitor-ui (via /api/v1/audit/trail alert queries)
```

---

## 13. Config Pipeline

```
config-api (self-contained)
  reads/writes -> in-memory / local state (no GCS in current implementation)
  serves -> onboarding-ui (/venues, /config)
```

---

## Orphan Path Analysis

> Updated 2026-03-15. Comprehensive audit of GCS write/read paths across all services.

### Orphan GCS Paths (written but no confirmed reader)

| Written By                                 | Path Pattern                                | Status                                                              |
| ------------------------------------------ | ------------------------------------------- | ------------------------------------------------------------------- |
| features-service (sports family)           | `features-sports-{P}/`                      | No API reader -- ML pipeline bulk consumes (by design)              |
| features-service (onchain family)          | `features-onchain-{P}/`                     | No API reader -- ML pipeline bulk consumes (by design)              |
| features-service (volatility family)       | `features-volatility-{category}-{P}/`       | No API reader -- ML pipeline bulk consumes (by design)              |
| features-service (commodity family)        | `features-commodity-{category}-{P}/`        | No API reader -- ML pipeline bulk consumes (by design)              |
| features-service (cross-instrument family) | `features-cross-instrument-{category}-{P}/` | No API reader -- ML pipeline bulk consumes (by design)              |
| features-service (multi-timeframe family)  | `features-multi-timeframe-{category}-{P}/`  | No API reader -- ML pipeline bulk consumes (by design)              |
| features-service (calendar family)         | `calendar-features-{P}/`                    | No API reader -- ML pipeline bulk consumes (by design)              |
| risk-and-exposure-service                  | `{P}-risk/risk/{client_id}/{date}/`         | No API reader -- client-reporting-api reads PnL, not risk snapshots |
| position-balance-monitor-service           | `positions-{P}/`                            | No API reader                                                       |
| ml-inference-service                       | `predictions-{P}/`                          | No direct API reader -- consumed by strategy-service via GCS/PubSub |
| alerting-service                           | `alerting/configs/`                         | No API reader -- internal config snapshots                          |
| alerting-service                           | `alerting/state/`                           | No API reader -- internal cooldown state                            |

### Orphan UI Pages (UI pages with no confirmed API backing)

| UI                     | Page/Route          | Status                                                                       |
| ---------------------- | ------------------- | ---------------------------------------------------------------------------- |
| live-health-monitor-ui | Position/Risk views | Calls `/api/positions` and `/api/risk` -- execution-results-api serves these |
| onboarding-ui          | Config page         | Backed by config-api (`/venues`, `/config`) -- WIRED                         |

### Confirmed Wiring (no orphans)

| Writer                            | GCS Path                       | Reader                | UI                                |
| --------------------------------- | ------------------------------ | --------------------- | --------------------------------- |
| execution-service                 | `execution-store-{P}/results/` | execution-results-api | execution-analytics-ui            |
| instruments-service               | `instruments-store-*-{P}/`     | execution-results-api | execution-analytics-ui            |
| market-tick-data-service          | `market-data-tick-*-{P}/`      | execution-results-api | execution-analytics-ui            |
| pnl-attribution-service           | `pnl-{P}/pnl/`                 | client-reporting-api  | client-reporting-ui               |
| batch-live-reconciliation-service | `recon-{P}/recon/`             | unified-trading-api   | unified-trading-system-ui         |
| unified-trading-api               | `{BUCKET}/settlements/`        | unified-trading-api   | settlement-ui                     |
| deployment-api                    | `{STATE_BUCKET}/deployments/`  | deployment-api        | deployment-ui                     |
| All services (UEI)                | `{P}-events/events/`           | batch-audit-api       | batch-audit-ui, logs-dashboard-ui |
| alerting-service                  | `alerting/history/`            | batch-audit-api       | logs-dashboard-ui                 |
| ml-training-service               | `ml-models-{P}/`               | ml-inference-api      | ml-training-ui                    |

**Notes on feature orphans:**

- All 8 feature service outputs (delta-one, calendar, volatility, commodity, cross-instrument, multi-timeframe, onchain,
  sports) are consumed by ml-inference-service and ml-training-service in bulk via GCS reads. No API serves raw features
  to UIs directly. This is by design -- features are intermediate data, not user-facing.
- The `predictions-{P}/` path written by ml-inference-service is consumed by strategy-service, which reads prediction
  parquet files and also receives real-time cascade predictions via direct PubSub subscription.
- Risk and position snapshots have no confirmed API reader. These paths should be verified during the next production
  audit to confirm they are not dead writes.

---

## Summary: End-to-End Data Flow

```
                    WRITE LAYER                          READ/SERVE LAYER
                    ----------                           ----------------

instruments-service ────────> instruments-store-*-{P}/
  (INSTRUMENTS_READY) ───────────────────────────────> market-tick-data-service (subscribed)

market-tick-data-service ──> market-data-tick-*-{P}/
  (DATA_READY pub) ──────────────────────────────────> (no subscriber -- GAP)
                                   │
                                   ├──> features-service (delta-one family) ──> features-delta-one-*-{P}/
                                   │     (FEATURES_READY pub) ─────> (no subscriber -- GAP)
                                   │                                          │
                                   │                                          └──> ml-inference-service ──> predictions-{P}/
                                   │                                                (PREDICTIONS_READY pub) ─> (no sub -- GAP)
                                   │
                                   └──> execution-results-api ──────────────> execution-analytics-ui
                                                │
instruments-service ────────> instruments-store-*-{P}/ ──> execution-service
                                                              │
execution-service ──────────> execution-store-{P}/ ──────> execution-results-api ──> execution-analytics-ui
                                   │
                                   ├──> pnl-attribution-service ──> pnl-{P}/ ──> client-reporting-api ──> client-reporting-ui
                                   │
                                   ├──> batch-live-reconciliation-service ──> recon-{P}/ ──> unified-trading-api ──> unified-trading-system-ui
                                   │
                                   └──> position-balance-monitor-service ──> positions-{P}/ (orphan)

strategy-service ──> (SIGNALS_READY pub) ──> (no subscriber -- GAP)

All services ──> {P}-events/ ──> batch-audit-api ──> batch-audit-ui / logs-dashboard-ui
alerting-service ──> alerting/history/ ──> batch-audit-api ──> logs-dashboard-ui (AlertsView)

deployment-api <──> {STATE_BUCKET} (self-contained) ──> deployment-ui
unified-trading-api <──> {TRADING_ANALYTICS_GCS_BUCKET} (self-contained) ──> unified-trading-system-ui / settlement-ui
config-api <──> (in-memory) ──> onboarding-ui
```

---

## Coordination Event Wiring (Live Mode)

See `03-observability/coordination-events.md` for detailed wiring map. Summary:

- 1/10 events fully wired: `INSTRUMENTS_READY` (instruments-service -> market-tick-data-service)
- 5/10 events publish-only: publishers emit but no subscriber consumes
- 4/10 events defined-only: in `STANDARD_COORDINATION_EVENTS` but not used in any service

---

## Cross-References

- Strategy-specific data flow: see `06-coding-standards/strategy-identity-versioning.md`
- Batch-live symmetry for strategies: see `04-architecture/batch-live-architecture.md` (single SSOT)
- Strategy data access rule: see cursor rule `strategy-data-access.mdc`
