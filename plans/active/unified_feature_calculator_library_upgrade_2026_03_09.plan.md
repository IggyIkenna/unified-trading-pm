---
name: Unified Feature Calculator Library — BaseFeatureService Upgrade
overview: |
  The 8 features-*-service repos (calendar, commodity, cross-instrument, delta-one, multi-timeframe,
  onchain, sports, volatility) each independently implement the same boilerplate: UnifiedCloudConfig
  loading, /health + /readiness endpoints, Prometheus metrics (RECORDS_PROCESSED Counter,
  PROCESSING_LATENCY Histogram), correlation_id propagation, UCI EventBus publishing, and
  startup/shutdown lifecycle. This plan upgrades unified-feature-calculator-library to absorb that
  shared logic into a BaseFeatureService abstract class and companion modules, then refactors each
  service to extend it — reducing per-service boilerplate and enforcing a single standards path.
  All new library code: no Any, no os.getenv, basedpyright strict, ruff line-length 120,
  MIN_COVERAGE=70 (library), >80% per service after refactor.
status: active
created: 2026-03-09
updated: 2026-03-09
isProject: false
todos:
  - id: audit-boilerplate
    content: >-
      Audit all 8 features-*-service repos for common boilerplate patterns. Document each pattern with the files where
      it appears: (a) UnifiedCloudConfig loading — singleton vs repeated instantiation; (b) /health + /readiness HTTP
      endpoints — FastAPI router or raw handler; (c) Prometheus metrics — Counter RECORDS_PROCESSED, Histogram
      PROCESSING_LATENCY — labels, namespaces, registration; (d) correlation_id propagation — header extraction,
      contextvars usage, log injection; (e) UCI EventBus publishing — setup_events, log_event call sites; (f)
      startup/shutdown lifecycle — async lifespan context, signal handlers; (g) error handling — uncaught exception
      logging, event emission. Produce a summary table of which patterns are duplicated across how many services.
    status: completed
    notes: |
      RESOLVED 2026-03-09: Audited all 8 features-*-service repos. Summary table:

      | Pattern                             | Services | Details |
      |-------------------------------------|----------|---------|
      | UnifiedCloudConfig loading          | 8/8      | All extend UnifiedCloudConfig subclass (no lru_cache singleton — each service defines a typed subclass like CalendarFeaturesConfig, CommodityFeaturesConfig, etc. in config.py) |
      | /health + /readiness endpoints      | 1/8      | Only features-delta-one-service has api/health.py; other 7 services have no HTTP health endpoints |
      | RECORDS_PROCESSED Counter           | 8/8      | Identical pattern in each metrics.py: Counter at module level with same variable name |
      | PROCESSING_LATENCY Histogram        | 8/8      | Identical pattern in each metrics.py: Histogram at module level with same variable name |
      | correlation_id propagation          | 7/8      | 6 services use str(uuid.uuid4()) in cli/main.py + pass as details dict; features-onchain passes via error model field; features-commodity has none |
      | UCI EventBus setup_events           | 5/8      | features-cross-instrument, commodity, sports wire setup_events() in cli/main.py; others use log_event only without setup_events at service level |
      | startup/shutdown lifecycle          | 4/8      | features-calendar, delta-one, onchain, volatility use GracefulShutdownHandler global; commodity, cross-instrument, multi-timeframe, sports have no explicit shutdown handler |

      All 8 services have duplicate metrics.py with identical RECORDS_PROCESSED/PROCESSING_LATENCY pattern.
      No service uses ContextVar for correlation_id — all pass as function arguments or dict details.
      No service has /readiness endpoint except delta-one (via api/health.py).

  - id: design-base-class
    content: >-
      Design `BaseFeatureService` abstract class API before writing code. Define: abstract methods `async
      compute_features(self, payload: FeatureRequestT) -> FeatureResultT`; concrete methods `async startup(self)`,
      `async shutdown(self)`, `build_health_router() -> APIRouter`, `build_metrics() -> FeatureServiceMetrics`. Design
      `FeatureServiceConfig` TypedDict or dataclass (no os.getenv fields — all from UnifiedCloudConfig). Confirm design
      with library-tier-architecture.mdc: unified-feature-calculator-library is Tier 2 (may use Tier 0 + Tier 1 deps —
      UCI, UTL, UMI, UEI — but no Tier 2→Tier 2 circular imports). Document design in a comment block before
      implementation begins.
    status: pending

  - id: implement-base-feature-service
    content: >-
      Add `BaseFeatureService` to unified-feature-calculator-library in
      src/unified_feature_calculator/service_base/base_service.py. Requirements: full type annotations — no Any;
      UnifiedCloudConfig via @lru_cache(maxsize=1) singleton; abstract compute_features() with TypeVar-bound generic
      signature; built-in startup() calls setup_events from unified_events_interface (no try/except fallback); built-in
      shutdown() flushes metrics and logs shutdown event; correlation_id propagated via contextvars; no os.getenv()
      anywhere. Export from src/unified_feature_calculator/__init__.py. Run `basedpyright
      src/unified_feature_calculator/` — zero errors before proceeding.
    status: completed
    notes: |
      RESOLVED 2026-03-09: base_service.py created; BaseFeatureServiceV2 with abstract
      compute_features(), startup()/shutdown() lifecycle, correlation_id_var via contextvars.
      Exported from service_base/__init__.py and top-level __init__.py. Commit e17f550.

  - id: implement-feature-service-metrics
    content: >-
      Add `FeatureServiceMetrics` to unified-feature-calculator-library in
      src/unified_feature_calculator/service_base/metrics.py. Contains: `RECORDS_PROCESSED` prometheus_client.Counter
      (labels: service_name, feature_group, status); `PROCESSING_LATENCY` prometheus_client.Histogram (labels:
      service_name, feature_group; buckets: .005 .01 .025 .05 .1 .25 .5 1 2.5 5). Factory function
      `build_feature_metrics(service_name: str) -> FeatureServiceMetrics` that registers and returns both metrics. No
      duplicate registration (use CollectorRegistry or handle ValueError). Export from __init__.py. Full type
      annotations, zero basedpyright errors.
    status: completed
    notes: |
      RESOLVED 2026-03-09: metrics.py created with RECORDS_PROCESSED Counter + PROCESSING_LATENCY
      Histogram; build_feature_metrics() factory with ValueError-safe duplicate registration.
      Exported from __init__.py. Commit e17f550.

  - id: implement-health-router-factory
    content: >-
      Add `build_health_router()` factory to unified-feature-calculator-library in
      src/unified_feature_calculator/service_base/health.py. Returns a FastAPI APIRouter with two routes: GET /health
      (liveness — returns `{"status": "ok", "service": service_name}`) and GET /readiness (readiness — checks UCI
      connectivity + config loaded, returns 200 or 503). No os.getenv; config from UnifiedCloudConfig. Export from
      __init__.py. Full type annotations, zero basedpyright errors. Add unit tests in tests/unit/test_health_router.py.
    status: completed
    notes: |
      RESOLVED 2026-03-09: health.py created with build_health_router() returning FastAPI
      APIRouter with /health (liveness) + /readiness (readiness) endpoints. Tests added.
      Exported from __init__.py. Commit e17f550.

  - id: bump-library-version
    content: >-
      Bump unified-feature-calculator-library version with semver minor bump (adding new public API —
      BaseFeatureService, FeatureServiceMetrics, build_health_router). Update version in pyproject.toml. Run `uv lock`
      from workspace root (venv active). Update CHANGELOG.md with new public API summary under new version heading. Run
      `bash scripts/quality-gates.sh` in unified-feature-calculator-library — all gates must pass before service
      refactors begin.
    status: pending

  - id: refactor-features-calendar-service
    content: >-
      Refactor features-calendar-service to extend BaseFeatureService. Remove duplicate boilerplate: UnifiedCloudConfig
      re-init, manual /health + /readiness routes, inline Prometheus metrics definitions, manual correlation_id
      extraction, manual startup/shutdown. Replace with BaseFeatureService inheritance and calls to
      build_health_router(), build_metrics(). Implement compute_features() abstract method with existing calendar logic.
      Run `bash scripts/quality-gates.sh`; fix any failures. Update coverage to >80%. Commit:
      `"refactor(features-calendar-service): extend BaseFeatureService from library"`.
    status: pending

  - id: refactor-features-commodity-service
    content: >-
      Refactor features-commodity-service to extend BaseFeatureService. Remove duplicate boilerplate (same categories as
      calendar). Implement compute_features() with existing commodity logic. Run `bash scripts/quality-gates.sh`; fix
      failures; update coverage >80%. Commit: `"refactor(features-commodity-service): extend BaseFeatureService from
      library"`.
    status: pending

  - id: refactor-features-cross-instrument-service
    content: >-
      Refactor features-cross-instrument-service to extend BaseFeatureService. Remove duplicate boilerplate. Implement
      compute_features() with existing cross-instrument logic. Run `bash scripts/quality-gates.sh`; fix failures; update
      coverage >80%. Commit: `"refactor(features-cross-instrument-service): extend BaseFeatureService from library"`.
    status: pending

  - id: refactor-features-delta-one-service
    content: >-
      Refactor features-delta-one-service to extend BaseFeatureService. Remove duplicate boilerplate. Implement
      compute_features() with existing delta-one logic. Run `bash scripts/quality-gates.sh`; fix failures; update
      coverage >80%. Commit: `"refactor(features-delta-one-service): extend BaseFeatureService from library"`.
    status: pending

  - id: refactor-features-multi-timeframe-service
    content: >-
      Refactor features-multi-timeframe-service to extend BaseFeatureService. Remove duplicate boilerplate. Implement
      compute_features() with existing multi-timeframe logic. Run `bash scripts/quality-gates.sh`; fix failures; update
      coverage >80%. Commit: `"refactor(features-multi-timeframe-service): extend BaseFeatureService from library"`.
    status: pending

  - id: refactor-features-onchain-service
    content: >-
      Refactor features-onchain-service to extend BaseFeatureService. Remove duplicate boilerplate. Implement
      compute_features() with existing onchain logic (note: onchain.py already exists in library — confirm no collision
      with BaseFeatureService namespace). Run `bash scripts/quality-gates.sh`; fix failures; update coverage >80%.
      Commit: `"refactor(features-onchain-service): extend BaseFeatureService from library"`.
    status: pending

  - id: refactor-features-sports-service
    content: >-
      Refactor features-sports-service to extend BaseFeatureService. Remove duplicate boilerplate. Implement
      compute_features() with existing sports/arb/vig logic. Confirm no regression with
      sports_migration_combined.plan.md in-progress todos (b1-scraper-adapters, b5-b6-deployment). Run `bash
      scripts/quality-gates.sh`; fix failures; update coverage >80%. Commit: `"refactor(features-sports-service): extend
      BaseFeatureService from library"`.
    status: pending

  - id: refactor-features-volatility-service
    content: >-
      Refactor features-volatility-service to extend BaseFeatureService. Remove duplicate boilerplate. Implement
      compute_features() with existing volatility logic. Run `bash scripts/quality-gates.sh`; fix failures; update
      coverage >80%. Commit: `"refactor(features-volatility-service): extend BaseFeatureService from library"`.
    status: pending

  - id: update-library-changelog
    content: >-
      Update unified-feature-calculator-library CHANGELOG.md under the new version heading with a full description of
      the BaseFeatureService API: class signature, abstract methods, concrete methods, exported symbols
      (BaseFeatureService, FeatureServiceMetrics, build_health_router, build_feature_metrics). Include migration guide:
      "Extend BaseFeatureService, remove manual /health routes, remove manual Prometheus definitions, implement
      compute_features()." Commit to unified-feature-calculator-library.
    status: pending

  - id: update-codex-feature-service-pattern
    content: >-
      Add feature service pattern documentation to unified-trading-codex/06-coding-standards/. Create
      unified-trading-codex/06-coding-standards/feature-service-pattern.md with: BaseFeatureService usage example,
      FeatureServiceMetrics setup, /health + /readiness router wiring, correlation_id propagation pattern, prohibited
      patterns (os.getenv, Any, manual duplicate endpoints). Reference library-tier-architecture.mdc (Tier 2 dependency
      rules). Commit to unified-trading-codex with message `"docs: add feature-service-pattern standard"`.
    status: pending
---

# Unified Feature Calculator Library — BaseFeatureService Upgrade

## Objective

Upgrade `unified-feature-calculator-library` (Tier 2) to provide `BaseFeatureService`, absorbing repeated boilerplate
from all 8 `features-*-service` repos. Each service will extend the base class rather than re-implement shared logic.

## Current State

`unified-feature-calculator-library/src/unified_feature_calculator/` already contains:

```
__init__.py
base.py
base_validation.py
onchain.py
service_base/
  __init__.py
  base.py        # existing base — will be extended or supplemented
  registry.py
time_series.py
transformations.py
validations.py
```

`BaseFeatureService` builds on the existing `service_base/` structure, adding health endpoint factory, metrics, and
lifecycle management as standalone modules.

## Target Shared Boilerplate (from audit)

| Pattern                             | Estimated Services with Duplication |
| ----------------------------------- | ----------------------------------- |
| UnifiedCloudConfig singleton        | 8 / 8                               |
| /health + /readiness endpoints      | 8 / 8                               |
| RECORDS_PROCESSED Counter           | 8 / 8                               |
| PROCESSING_LATENCY Histogram        | 8 / 8                               |
| correlation_id propagation          | 8 / 8                               |
| UCI EventBus publish (setup_events) | 8 / 8                               |
| startup/shutdown lifecycle          | 8 / 8                               |

## Services Being Refactored

1. features-calendar-service
2. features-commodity-service
3. features-cross-instrument-service
4. features-delta-one-service
5. features-multi-timeframe-service
6. features-onchain-service
7. features-sports-service
8. features-volatility-service

## Library Standards

- No `Any` types — use TypeVar, TypedDict, Protocol
- No `os.getenv()` — UnifiedCloudConfig via `@lru_cache(maxsize=1)`
- No `try/except ImportError` around library imports — fail loud
- `from unified_events_interface import setup_events, log_event` — no fallbacks
- `basedpyright src/unified_feature_calculator/` — zero errors
- `ruff` line-length 120
- MIN_COVERAGE=70 for library; >80% per service after refactor
- Files ≤900L; functions ≤100L; methods ≤50L; classes ≤500L

## Tier Architecture Compliance

Per `library-tier-architecture.mdc`: unified-feature-calculator-library is Tier 2. Allowed dependencies: Tier 0 (UMI,
UEI schemas) + Tier 1 (UCI, UTL, URDI). No Tier 2→Tier 2 imports. No circular imports.

## Dependency Notes

- Requires `prometheus_client` in library pyproject.toml (already present or add)
- Requires `fastapi` in library pyproject.toml for health router (already present or add as optional dep)
- After library version bump: run `uv lock` + `uv pip install -e unified-feature-calculator-library/` from workspace
  root
- All 8 services must pin the new minor version in their pyproject.toml after refactor

## Cross-Plan Notes

`features-sports-service` refactor (todo: refactor-features-sports-service) must not regress work tracked in
`sports_migration_combined.plan.md` (b1-scraper-adapters, b5-b6-deployment — both in_progress). Coordinate: only remove
boilerplate, do not touch scraper adapter code.
