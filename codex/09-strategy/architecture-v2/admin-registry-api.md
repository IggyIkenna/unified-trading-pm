---
doc_type: codex-ssot
title: Admin Registry API — SSOT
summary:
  SSOT for the three admin-only registry HTTP endpoints (GET /api/v1/registry/{ml-models,archetypes,features}) — owning
  services, response shapes, the X-Admin-Token hmac auth gate (503 when unconfigured), and the UI
  CatalogueTruthinessAdapter live/mock fallback contract.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-library, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, registry, uac, ui, features, verification]
related:
  [
    /codex/09-strategy/architecture-v2/dart-tab-structure.md,
    /codex/09-strategy/architecture-v2/strategy-catalogue-3tier.md,
  ]
created: 2026-04-21
authoritative_for: [admin registry API endpoints (ml-models/archetypes/features reconciliation)]
referenced_by: [/codex/09-strategy/README.md]
owner:
last_reviewed:
code_refs:
---

# Admin Registry API — SSOT

Phase 7 of `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` introduces three admin-only HTTP surfaces
that let the UI `CatalogueTruthinessAdapter` reconcile UAC canonical lists against what is actually registered in
backend services at runtime.

This file is the SSOT for their endpoint paths, response shapes, and owning services. If either of these diverge, fix
the code — do not re-document the drift here.

## Contract summary

| Endpoint                          | Owning service             | Source of truth                                                                                      |
| --------------------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------- |
| `GET /api/v1/registry/ml-models`  | strategy-service           | `StrategyArchetype` (UAC) ∩ `StrategyFamily.ML_DIRECTIONAL`, reconciled against active slot registry |
| `GET /api/v1/registry/archetypes` | strategy-service           | `StrategyArchetype` (UAC), reconciled against active `StrategyInstanceRegistry`                      |
| `GET /api/v1/registry/features`   | every `features-*-service` | `FeatureGroupRegistry` (UTL `feature_service_base`) scoped to the owning service key                 |

All three endpoints share the same admin auth gate: shared-secret compared against the `X-Admin-Token` request header
via `hmac.compare_digest`. Services without the secret configured return `503` for every call — the surface is
safe-by-default.

## Response shapes

All DTOs today live **locally** (strategy-service: `strategy_service/api/registry_router.py`; UTL:
`unified_trading_library/feature_service_base/admin_registry_router.py`). **Follow-up:** promote to
`unified_api_contracts.internal.admin_registry` in a dedicated pass once the UI adapter has landed and the shapes have
stabilised across one real client reconciliation cycle.

### `GET /api/v1/registry/archetypes`

```json
{
  "archetypes": [
    {
      "family": "ML_DIRECTIONAL",
      "archetype": "ML_DIRECTIONAL_CONTINUOUS",
      "status": "LIVE",
      "registered_strategies": ["ml-btc-perp-binance-10m"],
      "venues": []
    }
  ]
}
```

`status` is one of `LIVE` | `IN_DEVELOPMENT` | `RETIRED` | `PLANNED_NOT_IMPLEMENTED`. Today the router emits only `LIVE`
(at least one slot registered) or `PLANNED_NOT_IMPLEMENTED` (zero slots). `IN_DEVELOPMENT` and `RETIRED` are reserved
for explicit lifecycle wiring — deferred as a follow-up once the strategy-service availability watchdog exposes maturity
transitions here.

`venues` is an empty list today. Populating it requires reading the active `StrategyInstanceDefinition` rows' target
universes, which the v2 orchestrator holds per-engine. Scheduled as a follow-up once the orchestrator-level accessor
(see `strategy_service.engine.strategies.v2.active_registry`) learns to project venue sets.

### `GET /api/v1/registry/ml-models`

```json
{
  "models": [
    {
      "name": "ML_DIRECTIONAL_CONTINUOUS",
      "family": "ML_DIRECTIONAL",
      "status": "LIVE",
      "last_training_timestamp": null,
      "deployment_health": "unknown"
    }
  ]
}
```

`last_training_timestamp` and `deployment_health` return stable sentinels today (`null` / `"unknown"`). Populating them
requires a cross-service call to the UTL `ModelRegistry` GCS manifest — scheduled as a follow-up; the UI
`CatalogueTruthinessAdapter` should treat `"unknown"` as a non-fatal label and render it distinctly from `"healthy"` /
`"stale"` / `"unreachable"`.

### `GET /api/v1/registry/features`

```json
{
  "features": [
    {
      "name": "economic_calendar",
      "feature_group": "economic_calendar",
      "status": "LIVE",
      "last_computed_at": null,
      "consumers": []
    }
  ]
}
```

Each features-\* service mounts this router bound to its own `service_key` (one of `FeatureGroupRegistry.all_services()`
— `delta_one`, `cross_instrument`, `multi_timeframe`, `volatility`, `calendar`, `onchain`, `sports_derived`,
`sports_odds`, `sports_ml`). The router returns only the groups owned by that service key so the UI can reconcile per
service without cross-contamination.

`last_computed_at` and `consumers` are sentinels today. Populating `last_computed_at` requires a lookup against the
availability manifest (v5 honest-coverage). `consumers` requires querying the strategy-service archetype registry for
strategies that subscribe to the group — scheduled as a follow-up when the UI adapter needs the drill-down.

## Client config (unified-trading-system-ui)

The `CatalogueTruthinessAdapter` (`lib/admin/truthiness.ts`) reads three `NEXT_PUBLIC_*` env vars at call time. All
three must be present for live mode; any missing var triggers mock fallback with a tagged warning.

| Variable                            | Required        | Example                                        | Purpose                                                    |
| ----------------------------------- | --------------- | ---------------------------------------------- | ---------------------------------------------------------- |
| `NEXT_PUBLIC_ADMIN_API_TOKEN`       | Yes (live mode) | `…rotated-secret…`                             | Shared admin secret sent as the `X-Admin-Token` header.    |
| `NEXT_PUBLIC_STRATEGY_SERVICE_URL`  | Yes (live mode) | `http://localhost:8016`                        | Base URL for `/api/v1/registry/{archetypes,ml-models}`.    |
| `NEXT_PUBLIC_FEATURES_SERVICE_URLS` | Optional        | `{"features-onchain":"http://localhost:8012"}` | JSON map `{service_key: base_url}` for features-\* mounts. |

Rotation policy lives with Secret Manager — the token is a per-environment shared secret (staging vs production each get
their own). Rotate by bumping the value in SM, then redeploying the UI image (Cloud Run bakes `NEXT_PUBLIC_*` at image
build time per `config/docker-build.env.*`).

### Adapter fallback behaviour

The adapter catches and classifies all live-mode failures so the admin page never crashes:

| Situation                             | `snapshot.status` | `snapshot.mode` | `snapshot.mock` |
| ------------------------------------- | ----------------- | --------------- | --------------- |
| All three env vars set + fetch 200    | `LIVE`            | `live`          | `false`         |
| Env var(s) absent or CLOUD_MOCK_MODE  | `MOCK`            | `mock`          | `true`          |
| Token set but service rejects 401/403 | `AUTH_ERROR`      | `mock`          | `true`          |
| Network / DNS / CORS / timeout        | `UNREACHABLE`     | `mock`          | `true`          |

`AUTH_ERROR` and `UNREACHABLE` still return the mock seed data — consumers render distinct banners
(`catalogue-auth-error-banner`, `catalogue-unreachable-banner`) so operators see what failed rather than silently
treating mock as live.

## Auth

| Aspect               | Design                                                                                                                                                                |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Header               | `X-Admin-Token`                                                                                                                                                       |
| Compare              | `hmac.compare_digest` (constant-time)                                                                                                                                 |
| Missing header       | `401 Unauthorized` with `detail: missing X-Admin-Token header`                                                                                                        |
| Wrong token          | `403 Forbidden` with `detail: invalid X-Admin-Token`                                                                                                                  |
| Unconfigured service | `503 Service Unavailable` — surface disabled by default, requires operator to provision the secret                                                                    |
| Secret provenance    | strategy-service: `StrategyServiceConfig.admin_api_token` via `UnifiedCloudConfig` + Secret Manager. Features-\* services pass the same value from their own configs. |

**Rotation**: both routers use the factory pattern — a fresh router binds the new secret on next service restart. The
5-minute `ApiKeyReloader` cadence used elsewhere in the stack is deferred to follow-up (the admin surface is
infrequently-rotated by nature).

## Mounting guide

### strategy-service

`strategy_service/api/main.py` mounts the router alongside the existing health + restriction-profile + signal-broadcast
routers:

```python
from strategy_service.api.registry_router import make_registry_router
from strategy_service.config import get_config

app.include_router(make_registry_router(admin_api_token=get_config().admin_api_token))
```

Orchestrators publish their `StrategyInstanceRegistry` to the process-global accessor on boot:

```python
from strategy_service.engine.strategies.v2.active_registry import set_active_strategy_instance_registry

set_active_strategy_instance_registry(orchestrator.instance_registry)
```

Without this publish the router truthfully reports every archetype as `PLANNED_NOT_IMPLEMENTED`.

### features-\* services

Each `features-*-service/features_*_service/api/main.py` mounts:

```python
from unified_trading_library import build_admin_registry_router

app.include_router(
    build_admin_registry_router(
        service_key="calendar",          # or "onchain" / "volatility" / ...
        admin_api_token=<config>.admin_api_token,
    )
)
```

`service_key` must match one of `FeatureGroupRegistry.all_services()`; the factory raises `ValueError` on unknown keys.

## Follow-ups

- **UAC DTO promotion** — Move `ArchetypeEntry` / `MlModelEntry` / `FeatureEntry` (plus their envelopes) to
  `unified_api_contracts.internal.admin_registry`. Today's local-in-service declarations are deliberate per the plan
  scope.
- **ModelRegistry integration** — Wire strategy-service ML-models endpoint to call the UTL `ModelRegistry` GCS manifest
  so `last_training_timestamp` and `deployment_health` stop returning sentinels.
- **Availability manifest integration** — Wire features admin endpoint to the v5 availability manifest so
  `last_computed_at` reflects the most recent honest write.
- **Consumer-graph population** — Wire features → strategies resolution so `consumers` lists ML strategies that
  subscribe to each group.
- **Lifecycle status richness** — Surface `IN_DEVELOPMENT` / `RETIRED` from the strategy-service availability watchdog
  so `status` is not binary.
- **Venues projection** — Emit the union of target-universe venues per archetype in the archetype endpoint.
- **features-\*-service router mount** — UTL ships the factory; each features-\* service should adopt the mount in its
  own `api/main.py` commit. Not blocking on any one service — the UI adapter can treat absent endpoints as "unknown" per
  its standard fallback.

## SSOT cross-refs

- Plan: `plans/archive/ui_unification_v2_sanitisation_2026_04_20.plan.md` — todo `p7-admin-backend-reachability-audit`
  (this page is the artefact).
- Companion UI todo: `p7-admin-catalogue-backend-truthfulness`.
- Router factories:
  - `strategy-service/strategy_service/api/registry_router.py`
  - `unified-trading-library/unified_trading_library/feature_service_base/admin_registry_router.py`
- Accessor for the strategy-service active registry:
  `strategy-service/strategy_service/engine/strategies/v2/active_registry.py`
- Feature-group SSOT: `unified-trading-library/unified_trading_library/feature_service_base/feature_group_registry.py`.
