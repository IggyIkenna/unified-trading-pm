---
doc_type: plan
title: SIT Full Rollout + Orphaned Data Flow + Events/Config Standardisation
summary:
status: DONE
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    system-integration-tests,
  ]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-10
id: sit_events_observability_rollout_2026_03_10
priority: P1
owner: agent
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# SIT Full Rollout + Orphaned Data Flow + Events/Config Standardisation

## Context

Every service produces batch (GCS) and/or live (PubSub/SSE) data. Currently most of this data reaches no UI. Three
services have zero data consumers. Nine UEI events are not codex-canonical. One event name mismatch exists in UTL
(`SERVICE_MEMORY_CRITICAL` → `MEMORY_THRESHOLD_REACHED`). OTel is wired ad-hoc per service with no standard helper. SIT
covers only 4 HTTP APIs.

This plan closes all orphaned outputs, builds 3 missing API repos, establishes the complete batch + live data flow for
all services, standardises events/observability, and adds full SIT coverage across the 14-service estate.

## Standard Contracts

### Health Response Schema

```json
{
  "status": "ok | degraded | unhealthy",
  "service": "name",
  "version": "1.2.3",
  "checks": { "auth": "ok|fail", "config": "ok|fail", "upstream": { "gcs": "ok|fail" } },
  "data_freshness": { "last_processed_date": "2026-03-10", "stale": false }
}
```

`/docs` + `/openapi.json` must be enabled. `make_health_router()` factory in UTL implements this.

### Service-to-API Data Contract Types

- **GCS_READER** · **PUBSUB_SUBSCRIBER** · **HTTP_PROXY** · **SYNTHETIC** (stub only — flag for migration)

### Event Enforcement Rule

`STARTED` + `STOPPED` + `FAILED` required at every deployable entrypoint. QG rg-check added to
`quality-gates-service-template.sh` in codex (P0.4).

## Complete Data Flow Map

| Service                  | Batch → API → UI                                                                               | Live → API → UI                                                               |
| ------------------------ | ---------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| instruments-service      | instruments GCS + corporate actions → trading-analytics-api → trading-analytics-ui             | N/A                                                                           |
| market-data-processing   | processed_candles GCS → market-data-api (migrate from synthetic) → trading-analytics-ui        | N/A                                                                           |
| market-tick-data         | raw_tick_data/ + processed_candles GCS → market-data-api → trading-analytics-ui                | N/A                                                                           |
| features-\* (8 services) | features Parquet → ml-training-api (feature availability tab) → ml-training-ui                 | N/A                                                                           |
| ml-training-service Ph1  | feature_selection/{instrument}/{timeframe}/ → ml-training-api → ml-training-ui (Phase 1 tab)   | N/A                                                                           |
| ml-training-service Ph2  | hyperparam_tuning/{model_id}/best_params.json → ml-training-api → ml-training-ui (Phase 2 tab) | N/A                                                                           |
| ml-training-service Ph3  | models/{model_id}/ + BQ ml_training → ml-training-api → ml-training-ui (Phase 3 tab)           | N/A                                                                           |
| ml-inference-service     | predictions GCS + BQ ml_predictions → trading-analytics-api → trading-analytics-ui             | cascade_predictions PubSub → trading-analytics-api SSE → trading-analytics-ui |
| strategy-service         | signals GCS → trading-analytics-api → trading-analytics-ui (signals tab)                       | strategy-sports-signals PubSub → trading-analytics-api SSE                    |
| execution-service        | fills/orders GCS → trading-analytics-api → trading-analytics-ui (trades/slippage)              | execution UEI events → trading-analytics-api SSE                              |
| position-balance-monitor | DB-backed, no batch                                                                            | fill-events PubSub → SSE → CRA → client-reporting-ui                          |
| risk-and-exposure        | **ORPHANED** → P1.3 adds risk/{client_id}/{date}/ GCS → trading-analytics-api                  | internal only                                                                 |
| pnl-attribution          | **ORPHANED** → P1.4 adds pnl/{date}/{client_id}/ GCS → CRA → client-reporting-ui               | N/A                                                                           |
| alerting-service         | alert_store in-memory (BigQuery deferred) → CRA proxy → client-reporting-ui                    | /system-status → live-health-monitor-ui                                       |

## Todos

### Step 0 — PM Plan (this file)

- [x] Create this plan file
- [x] Register in INDEX.md canonical table (row 34)

### P0 — Library Changes (parallel; unblock P1)

- [x] **p0-1-utl-health-router**: UTL `health_router.py` created; `make_health_router()` exported (commit efac669)
- [x] **p0-2-utl-observability**: UTL `observability.py` created; `setup_service_observability()` exported (commit
      efac669)
- [x] **p0-3a-uei-cpu-event**: UEI `CPU_THRESHOLD_REACHED` added; 9 events promoted to codex-canonical (commit dc801e1,
      v0.2.23)
- [x] **p0-3b-utl-event-name-fix**: UTL `memory_monitor.py:243` fixed `SERVICE_MEMORY_CRITICAL` →
      `MEMORY_THRESHOLD_REACHED` (commit efac669)
- [x] **p0-4a-codex-promote-events**: codex `lifecycle-events.md` Security/Resource Monitoring Events section added
      (commit 2d67cfb)
- [x] **p0-4b-codex-qg-enforcement**: codex `quality-gates-service-template.sh` STARTED/STOPPED/FAILED rg check added
      (commit 2d67cfb)

### P1 — Service + API Changes (parallel; requires P0 merged)

- [x] **p1-1-pnl-health**: pnl-attribution-service `/health` + `/readiness` added via `make_health_router()` (commit
      638e1dd)
- [x] **p1-2-market-tick-health**: market-tick-data-service `/health` + `/readiness` added; `--serve` flag;
      HEALTH_PORT=8010 (commit 8900ed3)
- [x] **p1-3-risk-datasink**: risk-and-exposure-service `RiskSnapshotSink` created;
      `risk/{client_id}/{date}/exposure_summary.json` (commit 1b3bd49)
- [x] **p1-4-pnl-gcs-output**: pnl-attribution-service GCS output `pnl/{date}/{client_id}/pnl_attribution.parquet`
      (commit 869e8ba)
- [x] **p1-5-cra-extensions**: CRA `POST /api/reports/generate` + `GET /pnl` + `GET /alerts` proxy added (commit
      26d28bf)
- [x] **p1-6-multi-tf-audit**: features-multi-timeframe already writes via UCI DataSink — no changes needed
- [x] **p1-7-alerting-system-status**: alerting `GET /system-status` + 30s TTL cache; live-health-monitor-ui env updated
      (commit 2775718)
- [x] **p1-8-era-fills-gcs**: ERA fills migrated in-memory → GCS-backed TTL cache (commit b17b9c3)
- [x] **p1-9-mda-real-candles**: market-data-api synthetic → real GCS candles; `/data-contract` endpoint (commit
      c2ea9b4)

### P2 — Observability Standardisation (parallel; requires P0 merged)

- [x] **p2-1a-otel-remove-custom**: execution-service (822b39f6), risk-and-exposure-service (fd6876b),
      ml-inference-service (a0f5ead) — `otel_setup.py` deleted atomically; `setup_service_observability()` wired
- [x] **p2-1b-otel-add-missing**: strategy-service (7821088), market-data-processing (068572e), instruments-service
      (75b8b79), position-balance-monitor (dee5744), alerting-service (abca336), pnl-attribution-service (30ff4b1),
      market-tick-data-service (754b611)
- [x] **p2-2-performance-monitor-events**: UTL `performance_monitor.py` DISK/MEMORY/CPU_THRESHOLD_REACHED events (commit
      28e65e3)
- [x] **p2-3a-config-reloader-loaded**: UTL `config_reloader.py` CONFIG_LOADED on init (commit 8b88f45)
- [x] **p2-3b-config-codex-doc**: codex `config-reloader-pattern.md` created (commit 1895e14)

### P3 — SIT Full Coverage (requires P0 + P1 merged)

- [x] **p3-1-conftest**: conftest.py extended to 13 base_urls (commit 5b59315)
- [x] **p3-2-api-smoke-extend**: test_api_smoke.py extended to all 10 services with rich schema validation (commit
      5b59315)
- [x] **p3-3-layer1-extend**: test_layer1_services.py 12 new imports added (commit 904948e)
- [x] **p3-4-internal-smoke**: test_internal_services_smoke.py created (commit 5b59315)
- [x] **p3-5-cli-worker-smoke**: test_cli_worker_smoke.py created with UEI regression guard (commit 904948e)
- [x] **p3-6-cross-service-chains**: test_cross_service_chains.py created with chain contracts (commit 5b59315)
- [x] **p3-7-gcs-e2e**: test_pipeline_e2e.py extended with GCS output stubs + real candles check (commit 5b59315)
- [x] **p3-8-pyproject-cli-deps**: pyproject.toml 10 editable installs added (commit 904948e)

### P4 — New API Repos for UI Consumers (parallel with P3; after P1)

- [x] **p4-1-ml-inference-api**: new repo created — /models, /models/deploy, /predictions/recent; 22 tests (initial
      commit)
- [x] **p4-2-ml-training-api**: new repo created — /features, /experiments, 3-phase endpoints; 7 tests (initial commit)
- [x] **p4-3-trading-analytics-api**: new repo created — 16 routes including SSE streaming; all stubs with GCS/BQ/PubSub
      contract types (commit f31e2cb)
- [x] **p4-4-trading-analytics-ui**: `VITE_TRADING_ANALYTICS_API_URL` added to `.env.example` (commit 7d0e452)

## Dependencies

```
P0 (all parallel) → merge + venv update
                  → P1 + P2 (parallel)
                          → P3 + P4 (parallel; P3.3+P3.5 can start before P1)
```

Hard rules: P0.3 → P2.2; P0.1 → P1.1/P1.2; P0.2 → P2.1; P1.1+P1.2 → P3.1/P3.2/P3.4; P1.3+P1.4 → P3.7+P4.3; P1.5+P1.7 →
P3.6; P1.9 → P4.3 candles proxy; P2.1 removes otel_setup.py atomically — never leave half-migrated.

## File Change Summary

| Phase     | Repos                                                                    | Files    |
| --------- | ------------------------------------------------------------------------ | -------- |
| P0        | UTL, UEI, codex                                                          | ~8       |
| P1        | pnl, market-tick, risk, CRA, alerting, ERA, mda + live-health-monitor-ui | ~20      |
| P2        | UTL + ~10 services                                                       | ~24      |
| P3        | system-integration-tests                                                 | ~9       |
| P4        | 3 new API repos + trading-analytics-ui                                   | ~54      |
| **Total** | **~26 repos**                                                            | **~115** |

## SSOT References

- [unified-trading-/codex/03-observability/lifecycle-events.md](../../unified-trading-/codex/03-observability/lifecycle-events.md)
- [unified-trading-codex/06-coding-standards/quality-gates-service-template.sh](../../unified-trading-codex/06-coding-standards/quality-gates-service-template.sh)
- [unified-trading-library/unified_trading_library/core/memory_monitor.py](../../unified-trading-library/unified_trading_library/core/memory_monitor.py)
- [system-integration-tests/tests/conftest.py](../../system-integration-tests/tests/conftest.py)
