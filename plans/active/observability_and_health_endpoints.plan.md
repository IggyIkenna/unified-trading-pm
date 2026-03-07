---
name: Observability and Health Endpoints
overview: |
  Standardise observability across all API services and long-running services. Health endpoints
  exist in 27+ files but /readiness is not consistently implemented, Prometheus metrics are only
  confirmed in execution-service, and MiFID/FCA compliance event logging is not audited.
  Grafana dashboards exist (deployment-service/grafana/) and correlation_id is widespread
  (136+ files). This plan adds /readiness to all API services, extends Prometheus coverage,
  verifies compliance events, implements pre-crash checkpointing, and validates end-to-end
  correlation_id propagation. Covers audit S12.
todos:
  - id: obs-readiness-audit
    content:
      "Audit all API services (execution-results-api, market-data-api, client-reporting-api, deployment-api,
      alerting-service) for /readiness endpoint. Document which have /health only vs /health + /readiness. For each
      missing /readiness: implement checks for DB connection, pubsub connectivity, and external API reachability."
    status: pending
  - id: obs-prometheus-all-services
    content:
      "Add Prometheus metrics export to all services that lack it. execution-service already has Counter + Histogram for
      trade latency and order submission. Pattern: add prometheus_client Counter/Histogram for key per-service
      operations (e.g., feature calculation latency, ML inference latency, strategy signal emission). Verify
      prometheus-client pinned in each repo's pyproject.toml per workspace-constraints.toml."
    status: pending
  - id: obs-compliance-events
    content:
      "Audit every service for MiFID/FCA required compliance events: AUTH_FAILURE logged on authentication failure;
      SECRET_ACCESSED logged when get_secret_client() is called; CONFIG_CHANGED logged when config is modified at
      runtime. Verify each event uses log_event() from unified_events_interface with correct event_type from
      lifecycle-events.md. Add missing log_event() calls."
    status: pending
  - id: obs-pre-crash-checkpoint
    content:
      "Implement pre-crash checkpoint in long-running services (execution-service, strategy-service,
      risk-and-exposure-service, ml-inference-service): register signal handler (SIGTERM, SIGINT) + memory threshold
      monitor at 85% RSS. On trigger: flush state to GCS/pubsub via get_storage_client(), log SHUTDOWN_INITIATED event,
      then exit gracefully. Unit tests with mocked signal delivery."
    status: pending
  - id: obs-grafana-verify
    content:
      "Verify deployment-service/grafana/dashboards/trading-overview.json and system-health.json are complete: all
      services deployed after last dashboard update must have panels. Metrics to cover: API request latency P95 per
      service, PubSub message lag per topic, DLQ depth, execution order submission rate, feature calculation rate, ML
      inference rate. Update dashboard JSON if panels are missing."
    status: pending
  - id: obs-correlation-id-e2e
    content:
      "Verify correlation_id propagates end-to-end: API ingress sets correlation_id → execution-service passes it to
      order events → pubsub messages carry it in attributes → consuming services log it. Write or verify
      test_correlation_propagation.py in system-integration-tests repo (or execution-service tests) using mock pubsub.
      If end-to-end gap found, fix at the break point."
    status: pending

  - id: obs-opentelemetry-rollout
    content: |
      OpenTelemetry instrumentation rollout across all services:
      (a) Add opentelemetry-sdk + opentelemetry-exporter-otlp-proto-grpc to each service repo's
          pyproject.toml (pin versions in workspace-constraints.toml).
      (b) Instrument FastAPI routes with OTel ASGI middleware (opentelemetry-instrumentation-fastapi).
      (c) Instrument PubSub publish/consume calls with span context propagation (inject/extract
          trace context into message attributes).
      (d) Instrument DataSink.write() and DataSource.read() calls with spans including
          bytes_written, rows_written, latency_ms attributes.
      (e) Instrument ML inference with model_name, batch_size, latency_p50/p95 span attributes.
      (f) Configure OTLP exporter to send to Cloud Trace (GCP) or X-Ray (AWS) via collector
          sidecar in Cloud Run. Use CLOUD_PROVIDER env var to select exporter.
      Roll out tier-ordered: T4 services first, then T5 APIs, then T6 UIs.
    status: pending
    activeForm: "Rolling out OpenTelemetry instrumentation across all services"

  - id: obs-lifecycle-event-test-mandate
    content: |
      Per-service lifecycle event test mandate: every service repo must have
      tests/unit/test_lifecycle_events.py that asserts all required lifecycle events are emitted
      via log_event() from unified_events_interface.

      Required events per service type:
        Batch services: SERVICE_STARTED, BATCH_STARTED, BATCH_COMPLETED (or BATCH_FAILED), SERVICE_STOPPED
        Live services:  SERVICE_STARTED, LIVE_STARTED, LIVE_STOPPED, SERVICE_STOPPED
        API services:   SERVICE_STARTED, REQUEST_RECEIVED, RESPONSE_SENT, SERVICE_STOPPED

      Implementation: use mock/spy on log_event() — assert called_with(event_type=<required>, ...).
      Add to quality-gates.sh: fail if tests/unit/test_lifecycle_events.py missing in any service repo.
      Also verify BATCH_* vs LIVE_* variants match the service's declared SERVICE_MODE.
    status: pending
    activeForm: "Adding per-service lifecycle event test requirement to quality gates"
isProject: false
---

# Observability and Health Endpoints

**Day:** 6–7 (March 10–11) **Scope:** All API services + long-running services (execution, strategy, risk, ml-inference)
**Blocks:** trading_system_audit_prompt S12; Layer 3a smoke test (health checks must pass) **Owner:** Person B
(services)

---

## Blockers

| Blocker                                    | Type          | Specific Dependency                                                                                                               | Resolution                                                                                                                                                                                            |
| ------------------------------------------ | ------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 3 service hardening not started      | `[PLAN_TODO]` | [phase3_service_hardening_integration.plan.md](phase3_service_hardening_integration.plan.md) § todo `p3-service-hardening`        | Service code must be structurally clean before adding observability; avoid adding metrics to services with known architectural violations                                                             |
| Phase 1 Stream A CI/CD not wired           | `[PLAN_TODO]` | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `ci-pipeline-wiring`                                      | Observability changes must go through quickmerge pipeline; CI must be running to validate health endpoint tests                                                                                       |
| system-integration-tests repo not created  | `[PLAN_TODO]` | [phase1_foundation_prep.plan.md](phase1_foundation_prep.plan.md) § todo `integration-system-tests-repo`                           | obs-correlation-id-e2e test (end-to-end) runs in system-integration-tests repo; correlation unit tests can go in service repo as workaround                                                           |
| MiFID/FCA event taxonomy not fully defined | `[RESOLVED]`  | [unified-trading-codex/03-observability/lifecycle-events.md](../../../unified-trading-codex/03-observability/lifecycle-events.md) | AUTH_FAILURE, SECRET_ACCESSED, and CONFIG_CHANGED are defined in lifecycle-events.md as LifecycleEventType members (verified 2026-03-06). Blocker resolved — obs-compliance-events audit can proceed. |

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
