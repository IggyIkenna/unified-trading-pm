# Runtime Tiers & Deployment Orchestration

## Core Invariant

**Mock is always the service running in mock mode.** The ONLY variable between tiers is **topology** — whether calls are
colocated (in-process) or cross network (HTTP). No feature creep between tiers. Same `MockDomainService`, same
`MockStateStore`, same seed data, same business logic. The topology changes; the engine never does.

Replace `CLOUD_MOCK_MODE=true` with `CLOUD_MOCK_MODE=false` at ANY tier to switch to real adapters.

---

## The 7 Tiers

### Local Tiers (developer machine)

| Tier   | Name                 | What runs                                                        | Calls                                                  |
| ------ | -------------------- | ---------------------------------------------------------------- | ------------------------------------------------------ |
| **T0** | UI-only              | UI (Next.js)                                                     | No network. In-browser mock store.                     |
| **T1** | UI + API gateways    | UI + `unified-trading-api` + `auth-api` + `client-reporting-api` | UI → HTTP → API. API uses MockStateStore internally.   |
| **T2** | UI + APIs + Services | UI + APIs + all service processes                                | UI → HTTP → API → HTTP → Services. Full engine parity. |

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
bash scripts/dev-tiers.sh --tier 0        # UI-only
bash scripts/dev-tiers.sh --tier 1        # UI + API gateways (demo-ready)
bash scripts/dev-tiers.sh --tier 2        # UI + APIs + services (full fleet)
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
