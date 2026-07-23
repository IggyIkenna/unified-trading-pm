---
doc_type: codex-ssot
title: Feature Service Pattern
summary:
  BaseFeatureServiceV2 pattern — the mandatory UTL base class for each features-service sub-package family; auto-wires
  UnifiedCloudConfig singleton, GCSEventSink + STARTED/STOPPED lifecycle, FeatureServiceMetrics, the health/readiness
  router factory, and the correlation_id ContextVar, so services implement only compute_features(). Includes the
  UAC-schema-first 'add a new feature_family' recipe and the prohibited-pattern list.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [features-service, instruments-service, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [features, feature-service, observability, prometheus-metrics, correlation-id, uac]
related:
  [
    /codex/04-architecture/features-service-architecture.md,
    /codex/06-coding-standards/prometheus-metrics.md,
    /codex/06-coding-standards/correlation-id.md,
  ]
created: 2026-03-27
authoritative_for: [BaseFeatureServiceV2 features sub-package base-class pattern]
referenced_by:
  [
    /codex/04-architecture/batch-live-architecture.md,
    /codex/04-architecture/features-service-architecture.md,
    /codex/06-coding-standards/prometheus-metrics.md,
    /codex/06-coding-standards/session-aware-feature-calculator-pattern.md,
    /codex/06-coding-standards/validation-and-errors.md,
    plans/epics/features_and_ml_master.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Feature Service Pattern

## Consolidation status

The pre-2026-05-08 layout had **8 separate** `features-*-service` repos (features-service (onchain family),
features-service (volatility family), features-service (cross-instrument family), features-service (sports family),
features-service (calendar family), features-service (commodity family), features-service (delta-one family),
features-service (multi-timeframe family)). The current target state is a single workspace repo `features-service` with
one sub-package per family
([`/codex/04-architecture/features-service-architecture.md`](/codex/04-architecture/features-service-architecture.md) —
canonical SSOT for the consolidated shape, the `--feature-family` CLI dispatcher, the Health-API aggregator, and the 7
UTL Phase 5 lifts). `BaseFeatureServiceV2` becomes the per-sub-package base class within `features-service`, not the
per-repo base class. The pattern below applies inside the consolidated repo: each sub-package owns its calculators; each
calculator extends `BaseFeatureServiceV2`. The deployment topology
([`/codex/05-infrastructure/deployment-clusters-live-vs-batch.md`](/codex/05-infrastructure/deployment-clusters-live-vs-batch.md))
splits the consolidated repo into one VM-per-asset_group (colocated with MDPS) plus one features-cross-cutting VM.

The `feature_family` axis (UAC enum) is the primary shard key inside the consolidated repo and surfaces in the data-
status drilldown — see [`/codex/02-data/data-status-drilldown.md`](/codex/02-data/data-status-drilldown.md) §
"Per-asset_group depth table".

### Adding a new feature_family

1. **UAC schema first.** Add the new family to
   `unified_api_contracts.canonical.crosscutting.feature_family.FeatureFamily` (StrEnum). Extend
   `FEATURE_GROUP_TO_FAMILY` with the family's owned `feature_group` keys. Ship UAC commit + bump.
2. **Sub-package skeleton.** Create `features-service/features_service/<family>/` with `__init__.py` exporting:

   ```python
   def run(argv: list[str]) -> int:
       """Entry-point invoked by the top-level CLI dispatcher.

       Receives every CLI flag except --feature-family (already consumed by the
       dispatcher). Must return an integer exit code.
       """
   ```

3. **Calculator class.** Add `features-service/features_service/<family>/calculators/<X>.py` extending
   `BaseFeatureServiceV2[Request, Result]` with the single `compute_features()` method.
4. **Health-API freshness callback.** Add `features-service/features_service/<family>/api.py` exposing
   `_data_freshness() -> FreshnessSnapshot`. The top-level
   [`features_service/api/main.py`](../../../features-service/features_service/api/main.py) aggregator discovers it via
   `importlib.util.find_spec` — no manual wiring.
5. **Manifest writer.** Use UTL `ManifestWriter.record_captured(feature_family=<FeatureFamily>, ...)` — the
   `feature_family` column is mandatory. Per-shard data lands at
   `gs://features-{asset_group}-{env}/feature_family={family}/feature_group={group}/...`.
6. **Tests.** Family-specific tests live under `features-service/tests/<family>/`. Cross-family integration tests (e.g.
   lookahead-bias gate enforcement) stay under `features-service/tests/integration/`.
7. **Launcher.** No new launcher needed — the consolidated `launch-features-vm.sh` accepts `--feature-family <new>`
   automatically once the UAC enum extension lands.

The dispatcher [`features_service/cli/main.py`](../../../features-service/features_service/cli/main.py) reads the UAC
enum at startup; no per-family registration is required.

## Overview

`BaseFeatureServiceV2` (exported from `unified-trading-library`, Tier 2) is the mandatory abstract base class for all
features sub-packages within `features-service`. It eliminates repeated boilerplate by providing:

- `UnifiedCloudConfig` singleton wiring (via `@lru_cache`)
- `GCSEventSink` setup and UEI lifecycle events (`STARTED` / `STOPPED`)
- `FeatureServiceMetrics` bundle (Prometheus `Counter` + `Histogram`) instantiated automatically
- FastAPI `/health` + `/readiness` router factory
- `correlation_id_var` `ContextVar` for request-level correlation ID propagation

Each service implements exactly one method — `compute_features()` — and removes all manually duplicated boilerplate.

---

## Extending BaseFeatureServiceV2

```python
from unified_feature_calculator.service_base import BaseFeatureServiceV2

class CalendarService(BaseFeatureServiceV2[CalendarRequest, CalendarResult]):
    """Concrete calendar feature service."""

    async def compute_features(self, payload: CalendarRequest) -> CalendarResult:
        start = time.monotonic()
        try:
            result = _compute(payload)
            self.metrics.records_processed.labels(
                service_name=self.service_name,
                feature_group="calendar",
                status="success",
            ).inc()
            return result
        finally:
            elapsed = time.monotonic() - start
            self.metrics.processing_latency.labels(
                service_name=self.service_name,
                feature_group="calendar",
            ).observe(elapsed)
```

Lifecycle wiring in FastAPI:

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

svc = CalendarService(service_name="features-service (calendar family)")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await svc.startup()
    yield
    await svc.shutdown()

app = FastAPI(lifespan=lifespan)
app.include_router(svc.build_health_router())
```

---

## FeatureServiceMetrics Setup via build_feature_metrics()

`BaseFeatureServiceV2.__init__` calls `build_feature_metrics(service_name)` automatically and exposes the result as
`self.metrics`. Services should not call `build_feature_metrics()` directly unless constructing metrics outside the base
class (e.g. in standalone scripts or tests).

```python
from unified_feature_calculator.service_base import build_feature_metrics, FeatureServiceMetrics

# Only needed outside BaseFeatureServiceV2 context:
metrics: FeatureServiceMetrics = build_feature_metrics("features-service (calendar family)")
```

`FeatureServiceMetrics` is a frozen dataclass:

| Field                | Type        | Labels                                    |
| -------------------- | ----------- | ----------------------------------------- |
| `records_processed`  | `Counter`   | `service_name`, `feature_group`, `status` |
| `processing_latency` | `Histogram` | `service_name`, `feature_group`           |

`status` label values: `"success"` or `"error"`.

Histogram latency buckets (seconds): `0.005 0.01 0.025 0.05 0.1 0.25 0.5 1.0 2.5 5.0`.

---

## /health and /readiness Router Wiring via build_health_router()

`svc.build_health_router()` (convenience wrapper on the service instance) or the standalone factory
`build_health_router(service_name)` both return a `fastapi.APIRouter` tagged `observability`.

```python
from unified_feature_calculator.service_base import build_health_router

router = build_health_router("features-service (calendar family)")
app.include_router(router)
```

Route behaviour:

| Route        | Success body                                                                       | Failure body                                                 | HTTP code |
| ------------ | ---------------------------------------------------------------------------------- | ------------------------------------------------------------ | --------- |
| `/health`    | `{"status": "ok", "service": "..."}` — always 200 while process runs               | —                                                            | 200       |
| `/readiness` | `{"status": "ready", "service": "...", "project_id": "...", "environment": "..."}` | `{"status": "not_ready", "service": "...", "detail": "..."}` | 200 / 503 |

`/readiness` internally calls `UnifiedCloudConfig` via the `lru_cache` singleton; returns 503 if config is not yet
loaded or raises.

Do not add manual `/health` or `/readiness` FastAPI route handlers in service code. Use this factory exclusively.

---

## correlation_id Propagation Pattern

`correlation_id_var` is a `ContextVar[str]` exported from `base_service.py`. Set it at the entry point of each request
or tick; reset it after the request completes.

```python
from unified_feature_calculator.service_base import correlation_id_var

async def handle_request(request: Request) -> Response:
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    token = correlation_id_var.set(cid)
    try:
        return await process(request)
    finally:
        correlation_id_var.reset(token)
```

`BaseFeatureServiceV2.startup()` and `shutdown()` read `correlation_id_var` automatically when emitting `STARTED` /
`STOPPED` UEI lifecycle events. No manual `details={"correlation_id": ...}` argument is needed in service code.

---

## Prohibited Patterns

| Pattern                                                             | Reason                                                                    |
| ------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| `os.getenv("PROJECT_ID")`                                           | Violates no-os-getenv rule — use `UnifiedCloudConfig`                     |
| `Any` type annotations                                              | Violates no-type-any rule — use TypeVar, TypedDict, or Protocol           |
| Manual `/health` endpoint in service code                           | Duplicates library-provided route — use `build_health_router()`           |
| Manual `/readiness` endpoint in service code                        | Same as above                                                             |
| Inline `Counter(...)` / `Histogram(...)` in service code            | Duplicates library-provided metrics — use `self.metrics`                  |
| `try/except ImportError` around `unified_feature_calculator` import | Violates no-empty-fallbacks rule — fail loud                              |
| `setup_events()` called directly in service code                    | Lifecycle managed by `BaseFeatureServiceV2.startup()` — do not call again |

---

## Tier Architecture Note

`unified-trading-library` is **Tier 2**. Its allowed upstream dependencies are:

| Tier | Libraries                                                                                                                   |
| ---- | --------------------------------------------------------------------------------------------------------------------------- |
| T0   | `unified_trading_library.events` (UEI), `unified_market_interface` (UMI)                                                    |
| T1   | `unified_config_interface` (UCI), `unified_trading_library` (UTL), `unified_reference_data_interface` (instruments-service) |

`BaseFeatureServiceV2` imports:

- `unified_config_interface.UnifiedCloudConfig` (T1/UCI)
- `unified_trading_library.events.{setup_events,log_event,close_events}` (T0/UEI)
- `unified_trading_library.GCSEventSink` (T1/UTL)

No Tier 2 → Tier 2 imports are permitted. No circular imports.

For the full dependency rule set, see `library-tier-architecture.mdc`.

---

## References

- Library source: `unified-trading-library/src/unified_feature_calculator/service_base/`
- Prometheus metrics standard: `unified-trading-pm/codex/06-coding-standards/prometheus-metrics.md`
- Correlation ID standard: `unified-trading-pm/codex/06-coding-standards/correlation-id.md`
- No-os-getenv rule: `.cursor/rules/no-type-any-use-specific.mdc`
- No-empty-fallbacks rule: `.cursor/rules/no-empty-fallbacks.mdc`
