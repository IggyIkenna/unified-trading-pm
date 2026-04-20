---
scope: [engineer, admin]
---

# Runtime Tiers & Deployment Orchestration

## Core Invariant

**Mock is always the service running in mock mode.** The ONLY variable between tiers is **topology** — whether calls are
colocated (in-process) or cross network (HTTP). No feature creep between tiers. Same `MockDomainService`, same
`MockStateStore`, same seed data, same business logic. The topology changes; the engine never does.

Replace `CLOUD_MOCK_MODE=true` with `CLOUD_MOCK_MODE=false` at ANY tier to switch to real adapters.

---

## The 7 Tiers

### Local Tiers (developer machine)

| Tier       | Name                 | What runs                                           | Calls                                                                                           | Port |
| ---------- | -------------------- | --------------------------------------------------- | ----------------------------------------------------------------------------------------------- | ---- |
| **static** | Static export        | Pre-built Next.js export via `npx serve`            | Zero — pure static HTML/JS. No dev server, no APIs.                                             | 3100 |
| **T0**     | UI-only              | UI (Next.js dev server, NEXT_PUBLIC_MOCK_API=true)  | No network. In-browser mock store.                                                              | 3100 |
| **T1**     | UI + API gateways    | UI + `unified-trading-api` + `client-reporting-api` | UI → HTTP → API. API uses MockStateStore internally. Auth is Firebase (VITE_SKIP_AUTH in mock). | 3000 |
| **T2**     | UI + APIs + Services | UI + APIs + all service processes                   | UI → HTTP → API → HTTP → Services. Full engine parity.                                          | 3000 |

**T-static** is for offline demos, screenshots, and visual regression. No API calls possible. Run:

```bash
bash scripts/dev-tiers.sh --tier static
# or build only:
bash scripts/static-mock-server.sh --build-only
```

**Auth** (all tiers): Authentication is Firebase-based. `VITE_SKIP_AUTH=true` in mock mode bypasses Firebase login.
`DISABLE_AUTH=true` on API gateways bypasses token validation. In real mode, Firebase OAuth provides JWT tokens and API
gateways validate them. User management routes are in unified-trading-api. The standalone auth-api repo is archived.

### Cloud Tiers (progressive deployment)

| Tier   | Name              | What runs where                      | Driven by           |
| ------ | ----------------- | ------------------------------------ | ------------------- |
| **T3** | UI in cloud       | UI on Cloud Run, APIs local or cloud | Deployment UI / CLI |
| **T4** | UI + API in cloud | UI + APIs on Cloud Run               | Deployment UI / CLI |
| **T5** | Full cloud (mock) | All on Cloud Run, mock mode          | Deployment UI / CLI |
| **T6** | Full cloud (real) | All on Cloud Run, real adapters      | Deployment UI / CLI |

### Startup

**SSOT script:** `unified-trading-system-ui/scripts/dev-tiers.sh`

```bash
bash scripts/dev-tiers.sh --tier static   # Static export (port 3100, zero deps)
bash scripts/dev-tiers.sh --tier 0        # UI-only (port 3100, dev server)
bash scripts/dev-tiers.sh --tier 1        # UI + API gateways (demo-ready, port 3000)
bash scripts/dev-tiers.sh --tier 2        # UI + APIs + services (full fleet, port 3000)
bash scripts/dev-tiers.sh --tier 1 --real # Tier 1 with real adapters
bash scripts/dev-tiers.sh --stop          # Stop everything
bash scripts/dev-tiers.sh --status        # What's running
```

### Health Page

`http://localhost:3000/health` — auto-detects current tier, shows all connector statuses with latency, gives startup
hints when services are down.

---

## Deployment Clusters

**SSOT:** `deployment-service/configs/clusters/*.yaml`

| Cluster      | Category   | Services | Use case                    |
| ------------ | ---------- | -------- | --------------------------- |
| `cefi`       | CEFI       | 17       | Crypto spot, perps, futures |
| `tradfi`     | TRADFI     | 18       | Equities, futures, options  |
| `defi`       | DEFI       | 12       | On-chain protocols (no ML)  |
| `sports`     | SPORTS     | 10       | Sports betting with ML      |
| `prediction` | PREDICTION | 6        | Prediction markets (subset) |
| `full`       | ALL        | 23       | Everything                  |

---

## 4 Operational Modes

### 1. Thermal Batch (one-shot pipeline)

Run the full pipeline once, end-to-end, with per-service version/category flexibility.

```bash
deploy-shards batch run --cluster cefi --as-of-date 2026-03-21
```

Pipeline DAG defined in `deployment-service/configs/dependencies.yaml`. T1Orchestrator handles dependency ordering and
cascade failure.

### 2. T+1 Batch Scheduling

Set up daily cascade: completion event from one service triggers the next.

```bash
deploy-shards schedule create --cluster cefi --cron "0 6 * * *"
```

### 3. Live Fleet Management

Stop/start individual running services.

```bash
deploy-shards live start --service instruments-service
deploy-shards live stop --service execution-service
deploy-shards live status --cluster cefi
```

### 4. Cluster Bootstrap

Spin up an entire deployment group in one action.

```bash
deploy-shards cluster bootstrap --cluster cefi --mode mock
deploy-shards cluster teardown --cluster cefi
deploy-shards cluster status --cluster cefi
```

---

## API Endpoints (Deployment UI)

**Base:** `deployment-service` FastAPI at `/deployment/*`

| Group    | Endpoints                                                                                                           |
| -------- | ------------------------------------------------------------------------------------------------------------------- |
| Cluster  | `GET /clusters`, `GET /clusters/{name}/status`, `POST /clusters/{name}/bootstrap`, `POST /clusters/{name}/teardown` |
| Batch    | `POST /batch/run`, `GET /batch/history`                                                                             |
| Live     | `POST /live/{service}/start`, `POST /live/{service}/stop`, `GET /live/status`                                       |
| Schedule | `POST /schedule`, `GET /schedule`, `DELETE /schedule/{cluster}`                                                     |

---

## Key Files

| What                          | Where                                                                |
| ----------------------------- | -------------------------------------------------------------------- |
| Tier startup script           | `unified-trading-system-ui/scripts/dev-tiers.sh`                     |
| Health page                   | `unified-trading-system-ui/app/health/page.tsx`                      |
| Tier plan (detailed)          | `.cursor/plans/end-to-end-testing/system-tiers.md`                   |
| Deployment orchestration plan | `.cursor/plans/end-to-end-testing/deployment-orchestration.md`       |
| Cluster configs               | `deployment-service/configs/clusters/*.yaml`                         |
| Service dependency DAG        | `deployment-service/configs/dependencies.yaml`                       |
| T1Orchestrator                | `deployment-service/deployment_service/orchestrator.py`              |
| Cluster orchestrator          | `deployment-service/deployment_service/cluster.py`                   |
| Local process backend         | `deployment-service/deployment_service/backends/local_process.py`    |
| CLI commands                  | `deployment-service/deployment_service/cli/commands/cluster.py`      |
| API routes                    | `deployment-service/deployment_service/api/routes/orchestration.py`  |
| Runtime topology              | `deployment-service/configs/runtime-topology.yaml` (symlink from PM) |

---

## Runtime Profiles (v7) — single axis for deployment-api

Tiers (T0-T6) describe **topology** — what processes are in the call graph. Runtime profiles describe **mode
composition** — which env vars are set. They are orthogonal: any tier can run any profile.

Before v7, a deployer set five env vars separately: `CLOUD_MOCK_MODE`, `MOCK_STATE_MODE`, `DISABLE_AUTH`,
`VITE_MOCK_API`, `VITE_SKIP_AUTH`. v7 collapses them into one `runtime_profile` axis consumed by deployment-api.

| Profile     | Use case                               | cloud_mock | auth_disabled | chaos_allowed | real venues   |
| ----------- | -------------------------------------- | ---------- | ------------- | ------------- | ------------- |
| `backtest`  | Historical replay with simulated fills | false      | true          | **yes**       | no            |
| `paper`     | Live data + simulated fills            | false      | false         | no            | no            |
| `mock-live` | Local dev / Tier-2 full fleet in mock  | **true**   | true          | yes           | no            |
| `staging`   | Real cloud + sandbox venues            | false      | false         | yes           | yes (sandbox) |
| `prod`      | Production                             | false      | false         | **no**        | yes           |

**Key invariant:** `chaos_allowed=false` ONLY in `prod`. Every other profile can be chaos-tested.

**Storage namespace** isolates profiles (`backtest/<run_id>/`, `paper/<client_id>/`, `mock/<run_id>/`, `staging/`,
`prod/`) so backtest writes never collide with live.

**SSOT:** `unified-trading-pm/codex/04-architecture/client-isolation-sla-and-runtime-profiles.md`. Schemas:
`unified_api_contracts.internal.domain.deployment_service.RuntimeProfile` / `RuntimeProfileSpec`.
