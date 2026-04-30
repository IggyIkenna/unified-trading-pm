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

> **Missing-venv tolerance:** any Python service whose `.venv` isn't built is skipped with a warning instead of
> failing the tier. T1 boots fine without `client-reporting-api`'s venv (reports tab unavailable); T2 boots whatever
> service venvs exist. To build all venvs at once:
> `for d in $(find . -maxdepth 2 -name uv.lock -not -path "*/.extra/*" | xargs -n1 dirname); do (cd "$d" && rm -rf .venv && uv sync --frozen); done`

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

**Backfill / migration / smoke / forward-poll VMs** are a separate deployment pattern from T3-T6 (which are long-lived
Cloud Run services). They use the **tarball-from-GCS** path: `setup-data-pipeline-vm.sh` startup script + per-repo
tarballs at `gs://deployment-scripts-.../code/`. See `vm-tarball-deployment.md` for the architecture, invariants,
refresh flags (`--all` / `--asset-group` / `--include`), singleton-lock pattern, debug recipe, and **Observability &
Lifecycle** (streaming GCS log, `/api/vm-deployments`, self-delete — `deployment-service` `cc07649` + `beaa2e5`).

### Startup

**SSOT script:** `unified-trading-system-ui/scripts/dev-tiers.sh`

```bash
bash scripts/dev-tiers.sh --tier static   # Static export (port 3100, zero deps)
bash scripts/dev-tiers.sh --tier 0        # UI-only (port 3100, dev server)
bash scripts/dev-tiers.sh --tier 1        # UI + API gateways (demo-ready, port 3000)
bash scripts/dev-tiers.sh --tier 2        # UI + APIs + services (full fleet, port 3000)
bash scripts/dev-tiers.sh --tier 1 --real # Tier 1 with real adapters (requires ADC: gcloud auth application-default login)
bash scripts/dev-tiers.sh --stop          # Stop everything (process-group kill, sweeps T1/T2 + emulator ports)
bash scripts/dev-tiers.sh --status        # What's running
```

`--real` runs an ADC pre-flight before launching anything; the script exits with a remediation hint if `gcloud auth
application-default print-access-token` fails. `GCP_PROJECT_ID` defaults to `central-element-323112` (the data lake);
override at the shell to point elsewhere.

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

---

## Deployed-environment topology (prod / uat) — provisioned 2026-04-25

Orthogonal to the local-tier and runtime-profile axes above. Once code reaches a deployed environment:

### Frontend portal (`unified-trading-system-ui`)

| Env  | Public URL                      | Cloud Run service     | Compute project          | Firebase project (Auth + Firestore + Storage) | Regions                                                   |
| ---- | ------------------------------- | --------------------- | ------------------------ | --------------------------------------------- | --------------------------------------------------------- |
| prod | `https://www.odum-research.com` | `odum-portal`         | `central-element-323112` | `central-element-323112`                      | europe-west4 + us-central1 + asia-northeast1 (LB-fronted) |
| uat  | `https://uat.odum-research.com` | `odum-portal-staging` | `central-element-323112` | **`odum-staging`** (isolated)                 | europe-west4                                              |

**UAT data layer is fully isolated from prod** — separate Auth user pool, Firestore, and Storage on `odum-staging`. UAT
compute is still on `central-element-323112` because the Cloud Build / Artifact Registry / GHA deploy SA pipeline is
wired there. Moving UAT compute to `odum-staging` is a separate plan, not done today. The data isolation is the
meaningful guarantee: admin / owner on `odum-staging` does **not** grant any permission on `central-element-323112`.

⚠️ **Multi-region prod gotcha:** `scripts/deploy-cloud-run.sh --env=prod` only updates europe-west4. us-central1 and
asia-northeast1 are refreshed by a separate workflow. Verify with `gcloud run services list --region=…` after a prod
deploy that needs to reach all customer regions.

### Sibling backend services (each in its own repo)

| Repo                   | Cloud Run service      | Region(s)      | Purpose                                |
| ---------------------- | ---------------------- | -------------- | -------------------------------------- |
| `unified-trading-api`  | `unified-trading-api`  | varies per env | Main trading backend                   |
| `user-management-api`  | `user-management-api`  | us-central1    | Auth / role / entitlement `/authorize` |
| `client-reporting-api` | `client-reporting-api` | us-central1    | Client-facing reports                  |
| `deployment-api`       | `deployment-api`       | us-central1    | Deployment automation                  |

The portal calls these via `NEXT_PUBLIC_*_URL` env vars baked at build time. **They are NOT inside the UI repo.** UAT
today runs `NEXT_PUBLIC_MOCK_API=true` and never calls them. When UAT flips to `MOCK_API=false`, the API auth
middlewares will need to dual-verify Firebase ID tokens (`['central-element-323112', 'odum-staging']`) — the
cross-project IAM is already in place; only a small middleware change is needed. **Do NOT deploy a parallel
`user-management-api` on `odum-staging`** — dual-verify is much smaller.

### IAM admin matrix (humans only)

| Project                  | Owners (`roles/owner`) | Firebase admin (`roles/firebase.admin`) |
| ------------------------ | ---------------------- | --------------------------------------- |
| `central-element-323112` | `ikenna@`, `femi@`     | (implicit via owner — no direct grants) |
| `odum-staging`           | `ikenna@` (creator)    | `femi@`, `harshkantariya@`              |

`harshkantariya@odum-research.com` is staging-only by operator decree. Never grant `firebase.admin` on prod. Mirror
script at `unified-trading-system-ui/scripts/admin/grant-harsh-iam.sh` grants 14 prod operational roles + staging
firebase.admin and explicitly excludes prod firebase.admin.

### Mail (Resend)

- prod: `hello@mail.odum-research.com` — DKIM + SPF verified.
- uat: `hello@mail.uat.odum-research.com` ⚠️ subdomain not yet DNS-verified. Either set up the staging subdomain in
  Resend (4 DKIM + 1 SPF DNS records) or temporarily point the uat branch in `lib/email/resend.ts` `getMailDomain()` at
  the prod-domain sender.

### Full per-env reference

`unified-trading-system-ui/docs/core/DEPLOYMENT.md` is the SSOT for the portal-side build/deploy contract — local
Firebase Emulator Suite setup, Resend domain caveats, the exact `gcloud run` / `firebase deploy` commands per env, and
the API token-verification seam.
