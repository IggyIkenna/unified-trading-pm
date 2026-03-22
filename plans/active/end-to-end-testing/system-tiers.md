# System Runtime Tiers — Startup & E2E Testing

## Core Invariant

**Mock is always the service running in mock mode.** The ONLY variable between tiers is **topology** — whether
calls are colocated (in-process) or cross network (HTTP). No feature creep between tiers. Same `MockDomainService`,
same `MockStateStore`, same seed data, same business logic. The topology changes; the engine never does.

Replace `CLOUD_MOCK_MODE=true` with `CLOUD_MOCK_MODE=false` at ANY tier to switch to real adapters. All 7 tiers
are operable in both mock and real modes.

---

## The 7 Tiers

### Local Tiers (developer machine, all processes on localhost)

| Tier | Name | Topology | What runs | Calls |
|------|------|----------|-----------|-------|
| **T0** | UI-only | Colocated | UI (Next.js) | No network. In-browser mock store mirrors MockDomainService behavior. |
| **T1** | UI + API | Network (UI↔API) | UI + `unified-trading-api` | UI → HTTP → API gateway. API uses internal MockStateStore. No downstream services. |
| **T2** | UI + API + Services | Network (UI↔API↔Services) | UI + API + all service processes | UI → HTTP → API → HTTP → services. Each service runs in mock mode locally. Full engine parity. |

### Cloud Tiers (progressive deployment, mock or real)

| Tier | Name | Topology | What runs where | Driven by |
|------|------|----------|-----------------|-----------|
| **T3** | UI in cloud | Cloud UI, local API+services | UI on Cloud Run/Vercel, API on localhost or cloud | Deployment UI |
| **T4** | UI + API in cloud | Cloud UI+API, local services | UI + API on Cloud Run, services on localhost or cloud | Deployment UI |
| **T5** | Full cloud (mock) | All cloud | UI + API + services on Cloud Run, all mock mode | Deployment UI |
| **T6** | Full cloud (real) | All cloud, real adapters | Same as T5 but `CLOUD_MOCK_MODE=false` — real venues, real data | Deployment UI |

### Tier progression rule

Each tier is **strictly more faithful** to production. You can develop at T0, demo at T1, integration-test at T2,
external-demo at T3, staging at T5, and go live at T6. The same code runs at every tier — only env vars change.

---

## Startup Script: `dev-tiers.sh`

Location: `unified-trading-system-ui/scripts/dev-tiers.sh`

```
Usage: bash scripts/dev-tiers.sh --tier <0|1|2> [--real] [--reset]

  --tier 0   UI-only (no Python processes)
  --tier 1   UI + unified-trading-api + auth-api + client-reporting-api
  --tier 2   UI + APIs + all services (full fleet)
  --real     Use CLOUD_MOCK_MODE=false (default: true/mock)
  --reset    POST /admin/reset after startup to re-seed
```

### Tier 0 — UI-only

```bash
NEXT_PUBLIC_MOCK_API=true \
NEXT_PUBLIC_UI_INTEGRATION=tier0_offline \
npm run dev
```

No Python. UI uses in-browser mock store. For product/design velocity.

### Tier 1 — UI + API gateways

```bash
# 1. unified-trading-api (port 8030)
cd unified-trading-api
CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local DISABLE_AUTH=true \
  .venv/bin/python -m uvicorn "unified_trading_api.main:create_app" --factory --port 8030 &

# 2. auth-api (port 8200)
cd auth-api
CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local \
  .venv/bin/python -m uvicorn auth_api.app:app --port 8200 &

# 3. client-reporting-api (port 8014)
cd client-reporting-api
CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local DISABLE_AUTH=true \
  .venv/bin/python -m uvicorn client_reporting_api.api.main:app --port 8014 &

# 4. UI (port 3000)
cd unified-trading-system-ui
NEXT_PUBLIC_MOCK_API=true NEXT_PUBLIC_UI_INTEGRATION=slim npm run dev
```

This is the **demo tier**. All domain data served by MockStateStore in the API gateway.

### Tier 2 — UI + APIs + Services (full fleet)

Same as Tier 1 PLUS start all downstream services from sibling repos:

```bash
# Per-service pattern (mock mode):
cd <service-repo>
CLOUD_MOCK_MODE=true CLOUD_PROVIDER=local \
  .venv/bin/python -m <service_module> --operation serve --mode live &
```

The API gateway's `LiveDomainService` routes to `localhost:<service-port>` instead of using MockStateStore.
This requires `GATEWAY_MODE=fleet` (or equivalent) on the API gateway.

Services and their ports are defined in `unified-trading-pm/scripts/dev/ui-api-mapping.json`.

---

## E2E Testing Per Tier

### T0 E2E: Contract compliance

- Verify in-browser mock store returns same shape as OpenAPI spec
- Snapshot test: T0 response vs T1 curl response for same endpoint
- No new functionality at T0 that doesn't exist at T1

### T1 E2E: API integration

- `curl` every endpoint on `:8030` — all return 200 with seed data
- `POST /admin/reset` → re-seed → verify data matches initial state
- WebSocket subscribe → receive ticks → positions PnL updates
- Auth flow: login → JWT → scoped data per persona
- Batch/live: `?mode=live` vs `?mode=batch` return different collections
- Health page: all connectors green

### T2 E2E: Fleet wiring

- Same as T1 plus: verify API gateway fans out to real service processes
- Service-level health: each service's `/health` endpoint returns OK
- Data flows end-to-end: instrument → tick-data → features → strategy → execution
- Cross-service: alerts from risk-service appear in API alerts endpoint
- Pipeline: run `procedure.md` per-service tests, then system-wide flow

### T3-T6 E2E: Cloud deployment

- Same functional tests as T1/T2 but against cloud URLs
- Network latency: all endpoints < 200ms p95
- Auth: real OAuth flow (not mock personas)
- TLS: all connections encrypted
- Driven by Deployment UI or CI/CD pipeline

---

## Relationship to Service E2E Tests

The per-service tests in `001_instruments_service.md` through `023_trading_agent_service.md` are **T2-level** tests.
They verify each service's CLI contract independently. The system tiers defined here compose those services into
the full graph and verify the wiring between them.

**Order of operations:**
1. Each service passes its own `bash scripts/quality-gates.sh` (unit + type check)
2. Each service passes its `procedure.md` E2E test (service-level, T2)
3. System E2E at T1 (API integration — no services needed)
4. System E2E at T2 (full fleet — all services + API + UI)
5. System E2E at T3-T6 (cloud deployment — driven by Deployment UI)

---

## Health Page as Tier Indicator

`/health` on the UI shows which tier is effectively running:

| What's green | Effective tier |
|-------------|---------------|
| Nothing | T0 (UI-only, or broken) |
| API gateway only | T1 |
| API + all domain endpoints + auth + reporting | T1 (full gateways) |
| API + services (once LiveDomainService wired) | T2 |
| Cloud URLs reachable | T3-T6 |

The health page detects tier automatically — no manual configuration needed.

---

## Deployment UI (T3-T6 Driver)

The Deployment UI (`unified-trading-deployment-ui` or the deployment section inside `unified-trading-system-ui`)
drives T3-T6:

- **T3**: Deploy UI to Cloud Run / Vercel. Point at local or cloud API.
- **T4**: Deploy API gateway to Cloud Run. Configure service URLs.
- **T5**: Deploy all services to Cloud Run (mock mode).
- **T6**: Flip `CLOUD_MOCK_MODE=false`. Real adapters, real venues.

The Deployment UI should be able to run **standalone** (independent of the main UI) for ops teams.
There's already a version inside `unified-trading-deployment-ui` — unify with the deployment section
in `unified-trading-system-ui/app/(platform)/services/manage/` or `app/(ops)/devops/`.
