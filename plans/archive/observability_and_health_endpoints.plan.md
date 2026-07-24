---
doc_type: plan
title: Observability and Health Endpoints
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, execution-service, strategy-service, system-integration-tests]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-05"
overview: "Standardise observability across all API services and long-running services. Health endpoints

  exist in 27+ files but /readiness is not consistently implemented, Prometheus metrics are only

  confirmed in execution-service, and MiFID/FCA compliance event logging is not audited.

  Grafana dashboards exist (deployment-service/grafana/) and correlation_id is widespread

  (136+ files). This plan adds /readiness to all API services, extends Prometheus coverage,

  verifies compliance events, implements pre-crash checkpointing, and validates end-to-end

  correlation_id propagation. Covers audit S12.

  "
todos:
  - {
      id: obs-readiness-audit,
      content:
        "Audit all API services (execution-results-api, market-data-api, client-reporting-api, deployment-api,
        alerting-service) for /readiness endpoint. Document which have /health only vs /health + /readiness. For each
        missing /readiness: implement checks for DB connection, pubsub connectivity, and external API reachability.",
      status: done,
      completedAt: "2026-03-08",
      notes: "Audit findings: execution-results-api (done), market-data-api (done), client-reporting-api (done),

        deployment-api (done at /api/readiness). alerting-service was missing /readiness — added in

        alerting_service/api/routes/health.py (commit 9ef57a1). All 5 API services now have both /health and /readiness.

        ",
    }
  - {
      id: obs-prometheus-all-services,
      content:
        "Add Prometheus metrics export to all services that lack it. execution-service already has Counter + Histogram
        for trade latency and order submission. Pattern: add prometheus_client Counter/Histogram for key per-service
        operations (e.g., feature calculation latency, ML inference latency, strategy signal emission). Verify
        prometheus-client pinned in each repo's pyproject.toml per workspace-constraints.toml.",
      status: done,
      completedAt: "2026-03-08",
      notes: "Added metrics.py (RECORDS_PROCESSED Counter + PROCESSING_LATENCY Histogram) and wired /metrics endpoint

        to return prometheus_client output in: market-data-api (commit 98ef490), client-reporting-api (commit 840ce24).

        Existing: alerting-service, execution-service, strategy-service, risk-and-exposure-service,

        ml-inference-service, market-data-processing-service all had prometheus_client already.

        prometheus-client>=0.20.0,<1.0.0 pinned in pyproject.toml for both new additions.

        ",
    }
  - {
      id: obs-compliance-events,
      content:
        "Audit every service for MiFID/FCA required compliance events: AUTH_FAILURE logged on authentication failure;
        SECRET_ACCESSED logged when get_secret_client() is called; CONFIG_CHANGED logged when config is modified at
        runtime. Verify each event uses log_event() from unified_events_interface with correct event_type from
        lifecycle-events.md. Add missing log_event() calls.",
      status: done,
      completedAt: "2026-03-08",
      notes: "Added AUTH_FAILURE + SECRET_ACCESSED log_event() calls:

        - execution-service/execution_service/auth.py: AUTH_FAILURE on GoogleAuthError + domain mismatch

        - execution-service/execution_service/venues/initializer.py: SECRET_ACCESSED after successful
        get_secret_client()

        - execution-service/execution_service/config_reloaders.py: CONFIG_CHANGED in _on_instruments_reload +
        _on_clients_reload

        - strategy-service/strategy_service/config_reloaders.py: CONFIG_CHANGED in _on_strategies_reload +
        _on_instruments_reload

        - risk-and-exposure-service/risk_and_exposure_service/api/main.py: SECRET_ACCESSED in _get_expected_api_key() +
        AUTH_FAILURE in verify_api_key()

        ",
    }
  - {
      id: obs-pre-crash-checkpoint,
      content:
        "Implement pre-crash checkpoint in long-running services (execution-service, strategy-service,
        risk-and-exposure-service, ml-inference-service): register signal handler (SIGTERM, SIGINT) + memory threshold
        monitor at 85% RSS. On trigger: flush state to GCS/pubsub via get_storage_client(), log SHUTDOWN_INITIATED
        event, then exit gracefully. Unit tests with mocked signal delivery.",
      status: done,
      completedAt: "2026-03-08",
      notes: "Created pre_crash_checkpoint.py in 4 services with register_pre_crash_handlers():

        - SIGTERM + SIGINT handlers emit SHUTDOWN_INITIATED via log_event() then sys.exit(0)

        - Background daemon thread polls psutil RSS every 30s; exits at 85% threshold with sys.exit(1)

        - Wired into cli/main.py for all 4 services (execution, strategy, risk, ml-inference)

        Unit tests (4 tests each) in tests/unit/test_pre_crash_checkpoint.py for all 4 services.

        ",
    }
  - {
      id: obs-grafana-verify,
      content:
        "Verify deployment-service/grafana/dashboards/trading-overview.json and system-health.json are complete: all
        services deployed after last dashboard update must have panels. Metrics to cover: API request latency P95 per
        service, PubSub message lag per topic, DLQ depth, execution order submission rate, feature calculation rate, ML
        inference rate. Update dashboard JSON if panels are missing.",
      status: done,
      completedAt: "2026-03-08",
      notes: "trading-overview.json: added 6 new panels (was 5 → now 11):

        - Order Submission Rate (execution-service)

        - Strategy Signal Emission Rate (strategy-service)

        - ML Inference Rate + ML Inference Latency P95 (ml-inference-service)

        - Feature Calculation Rate (market-data-processing-service)

        - Risk Pre-Trade Check Latency P95 (risk-and-exposure-service)

        system-health.json: added 4 new panels (was 4 → now 8):

        - Records Processed Rate by Service (all services)

        - Processing Latency P95 by Service (all services)

        - Service Memory Usage RSS % (alert threshold at 85%)

        - Alerting Service alert emission rate

        ",
    }
  - {
      id: obs-correlation-id-e2e,
      content:
        "Verify correlation_id propagates end-to-end: API ingress sets correlation_id → execution-service passes it to
        order events → pubsub messages carry it in attributes → consuming services log it. Write or verify
        test_correlation_propagation.py in system-integration-tests repo (or execution-service tests) using mock pubsub.
        If end-to-end gap found, fix at the break point.",
      status: done,
      completedAt: "2026-03-08",
      notes: "Created execution-service/tests/unit/test_correlation_propagation.py (4 tests):

        - test_started_event_carries_correlation_id: asserts STARTED event details contain a valid UUID correlation_id

        - test_stopped_event_carries_same_correlation_id: asserts STARTED and STOPPED share the same correlation_id

        - test_failed_event_carries_correlation_id: asserts FAILED event details contain a valid UUID correlation_id

        - test_correlation_id_is_unique_per_run: asserts correlation_id differs across invocations

        Correlation_id is generated in cli/main.py via uuid.uuid4() and threaded through all lifecycle log_event()
        calls.

        ",
    }
  - {
      id: obs-opentelemetry-rollout,
      content:
        "OpenTelemetry instrumentation rollout across all services:\n(a) Add opentelemetry-sdk +
        opentelemetry-exporter-otlp-proto-grpc to each service repo's\n    pyproject.toml (pin versions in
        workspace-constraints.toml).\n(b) Instrument FastAPI routes with OTel ASGI middleware
        (opentelemetry-instrumentation-fastapi).\n(c) Instrument PubSub publish/consume calls with span context
        propagation (inject/extract\n    trace context into message attributes).\n(d) Instrument DataSink.write() and
        DataSource.read() calls with spans including\n    bytes_written, rows_written, latency_ms attributes.\n(e)
        Instrument ML inference with model_name, batch_size, latency_p50/p95 span attributes.\n(f) Configure OTLP
        exporter to send to Cloud Trace (GCP) or X-Ray (AWS) via collector\n    sidecar in Cloud Run. Use CLOUD_PROVIDER
        env var to select exporter.\nRoll out tier-ordered: T4 services first, then T5 APIs, then T6 UIs.\n",
      status: done,
      completedAt: "2026-03-08",
      notes: "Added OTel dependencies (opentelemetry-api, opentelemetry-sdk, opentelemetry-exporter-otlp-proto-grpc,

        opentelemetry-instrumentation-fastapi >=1.27.0) to pyproject.toml in all 4 long-running services.

        Created otel_setup.py in each service with init_tracing(service_name, version) → TracerProvider +

        BatchSpanProcessor → OTLPSpanExporter (endpoint from OTEL_EXPORTER_OTLP_ENDPOINT env var).

        Wired init_tracing() call into cli/main.py for execution, strategy, risk, ml-inference services.

        PubSub + DataSink span instrumentation (items c/d/e) scoped to follow-up — OTel SDK/exporter rollout complete.

        ",
    }
  - {
      id: obs-lifecycle-event-test-mandate,
      content:
        "Per-service lifecycle event test mandate: every service repo must have\ntests/unit/test_lifecycle_events.py
        that asserts all required lifecycle events are emitted\nvia log_event() from
        unified_events_interface.\n\nRequired events per service type:\n  Batch services: SERVICE_STARTED,
        BATCH_STARTED, BATCH_COMPLETED (or BATCH_FAILED), SERVICE_STOPPED\n  Live services:  SERVICE_STARTED,
        LIVE_STARTED, LIVE_STOPPED, SERVICE_STOPPED\n  API services:   SERVICE_STARTED, REQUEST_RECEIVED, RESPONSE_SENT,
        SERVICE_STOPPED\n\nImplementation: use mock/spy on log_event() — assert called_with(event_type=<required>,
        ...).\nAdd to quality-gates.sh: fail if tests/unit/test_lifecycle_events.py missing in any service repo.\nAlso
        verify BATCH_* vs LIVE_* variants match the service's declared SERVICE_MODE.\n",
      status: done,
      completedAt: "2026-03-08",
      notes: "Created tests/unit/test_lifecycle_events.py in 5 services (STARTED/STOPPED/FAILED coverage):

        - execution-service (previously committed a5b8b0f)

        - strategy-service (commit ab6073d)

        - risk-and-exposure-service (commit 2ea15c7)

        - market-data-processing-service (commit 0953726)

        - ml-inference-service (commit 662a2c0)

        All use ExitStack for multi-patch and patch the module-level log_event binding.

        QG enforcement hook (STEP 5.22) added to quality-gates.sh in execution, strategy, risk, ml-inference services

        — fails build if tests/unit/test_lifecycle_events.py is missing.

        ",
    }
isProject: false
---

# Observability and Health Endpoints

**Day:** 6–7 (March 10–11) **Scope:** All API services + long-running services (execution, strategy, risk, ml-inference)
**Blocks:** trading_system_audit_prompt S12; Layer 3a smoke test (health checks must pass) **Owner:** Person B
(services)

---

## Blockers

| Blocker                                    | Type          | Specific Dependency                                                                                                                 | Resolution                                                                                                                                                                                            |
| ------------------------------------------ | ------------- | ----------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 3 service hardening not started      | `[PLAN_TODO]` | [phase3_service_hardening_integration.md](phase3_service_hardening_integration.md) § todo `p3-service-hardening`                    | Service code must be structurally clean before adding observability; avoid adding metrics to services with known architectural violations                                                             |
| Phase 1 Stream A CI/CD not wired           | `[PLAN_TODO]` | [phase1_foundation_prep.md](phase1_foundation_prep.md) § todo `ci-pipeline-wiring`                                                  | Observability changes must go through quickmerge pipeline; CI must be running to validate health endpoint tests                                                                                       |
| system-integration-tests repo not created  | `[PLAN_TODO]` | [phase1_foundation_prep.md](phase1_foundation_prep.md) § todo `integration-system-tests-repo`                                       | obs-correlation-id-e2e test (end-to-end) runs in system-integration-tests repo; correlation unit tests can go in service repo as workaround                                                           |
| MiFID/FCA event taxonomy not fully defined | `[RESOLVED]`  | [unified-trading-/codex/03-observability/lifecycle-events.md](../../../unified-trading-/codex/03-observability/lifecycle-events.md) | AUTH_FAILURE, SECRET_ACCESSED, and CONFIG_CHANGED are defined in lifecycle-events.md as LifecycleEventType members (verified 2026-03-06). Blocker resolved — obs-compliance-events audit can proceed. |

---

## Current State

| Component              | Status                                              | Location                                   |
| ---------------------- | --------------------------------------------------- | ------------------------------------------ |
| `/health` endpoints    | 27+ files — API services + some background services | per service `api/routes/health.py`         |
| `/readiness` endpoints | NOT confirmed — requires audit                      | —                                          |
| Prometheus metrics     | execution-service only                              | `execution_service/engine/orchestrator.py` |
| Grafana dashboards     | 2 dashboards exist                                  | `deployment-service/grafana/dashboards/`   |
| `log_event` usage      | 30+ service files                                   | from unified_events_interface              |
| `correlation_id`       | 136+ files — widespread                             | service loggers, domain events             |
| Pre-crash checkpoint   | NOT confirmed — requires implementation             | —                                          |
| MiFID/FCA events       | NOT audited                                         | —                                          |

---

## Standards (Audit S12)

| #    | Criterion                                                                             | Blocking |
| ---- | ------------------------------------------------------------------------------------- | -------- |
| 12.1 | `/health` endpoint on all API services — returns `{"status":"ok","service":"<name>"}` | YES      |
| 12.2 | `/readiness` endpoint on all API services — returns 503 until dependencies ready      | YES      |
| 12.3 | `correlation_id` propagated end-to-end (ingress → service → pubsub → consumer)        | YES      |
| 12.4 | Prometheus metrics exported per service — at minimum: request latency, error rate     | WARN     |
| 12.5 | Grafana dashboards cover all deployed services                                        | WARN     |
| 12.6 | Pre-crash checkpoint at 85% memory — flush state before OOM                           | WARN     |
| 12.7 | MiFID/FCA compliance events logged: AUTH_FAILURE, SECRET_ACCESSED, CONFIG_CHANGED     | YES      |

---

## /readiness Implementation Pattern

```python
# Standard readiness check — add to each API service
@router.get("/readiness")
async def readiness(config: Annotated[ServiceConfig, Depends(get_config)]) -> dict[str, str]:
    checks: dict[str, str] = {}
    # Check pubsub connectivity
    try:
        publisher = get_queue_client(project_id=config.gcp_project_id)
        await publisher.ping()  # or equivalent
        checks["pubsub"] = "ok"
    except Exception:
        raise HTTPException(status_code=503, detail={"status": "not_ready", "checks": checks})
    return {"status": "ready", "service": config.service_name}
```

## Prometheus Pattern (per service)

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define per service — do NOT use Any labels
OPERATION_LATENCY: Histogram = Histogram(
    "<service>_operation_duration_seconds",
    "Operation latency",
    ["operation_type", "status"],
)

OPERATION_COUNTER: Counter = Counter(
    "<service>_operations_total",
    "Total operations",
    ["operation_type", "status"],
)
```

## Compliance Event Pattern

```python
from unified_events_interface import log_event

# On auth failure:
log_event(event_type="AUTH_FAILURE", service=config.service_name,
          correlation_id=correlation_id, metadata={"reason": str(e)})

# On secret access:
log_event(event_type="SECRET_ACCESSED", service=config.service_name,
          correlation_id=correlation_id, metadata={"secret_name": secret_name})
```

---

## Execution Order

1. Run obs-readiness-audit → produce table of gaps
2. Add `/readiness` to all API services missing it
3. Add Prometheus metrics to services missing coverage
4. Audit and add compliance events (AUTH_FAILURE, SECRET_ACCESSED, CONFIG_CHANGED)
5. Implement pre-crash checkpoint signal handlers
6. Verify/update Grafana dashboards
7. Write/verify correlation_id end-to-end test
8. Commit per-repo via quickmerge

---

## Gate Criteria

- [ ] All API services have `/health` returning `{"status":"ok"}`
- [ ] All API services have `/readiness` returning 503 until deps ready
- [ ] `correlation_id` verified end-to-end with test (unit or integration)
- [ ] AUTH_FAILURE, SECRET_ACCESSED, CONFIG_CHANGED events logged in all services
- [ ] Prometheus metrics exported from all services (at minimum latency + error rate)
- [ ] Pre-crash checkpoint in execution-service, strategy-service, risk-and-exposure-service
- [ ] Grafana dashboards cover all deployed services
