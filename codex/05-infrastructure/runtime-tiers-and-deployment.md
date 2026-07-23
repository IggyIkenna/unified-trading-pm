---
doc_type: codex-ssot
title: Runtime Tiers & Deployment Orchestration
summary:
  The 7-tier deployment topology (static/T0-T6) + the UI dev-stack startup decision table, deployment clusters, the
  live-pipeline VM topology, the 4 operational modes, and the deployed prod/uat environment topology; the
  runtime-profile v7 axis is owned by client-isolation-sla-and-runtime-profiles.md.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [client-reporting-api, deployment-api, deployment-service, deployment-ui, execution-service, features-service]
scope: [engineer, admin]
tags: [infrastructure, deployment, ui, tiers, orchestrator]
related:
  [
    /codex/05-infrastructure/ui-architecture.md,
    /codex/05-infrastructure/replay-subsystem.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/synthetic-data-benchmarking.md,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
  ]
created: 2026-03-27
authoritative_for: [7-tier deployment topology (static/T0-T6), UI/dev-stack startup decision table]
referenced_by:
  [
    /codex/02-data/sports-scheduling-and-sharding.md,
    /codex/04-architecture/client-isolation-sla-and-runtime-profiles.md,
    /codex/04-architecture/instruments-live-architecture.md,
    /codex/05-infrastructure/aws-iam-matrix.md,
    /codex/05-infrastructure/deployment-and-qg-strategy.md,
    /codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
    /codex/05-infrastructure/deployment-ui-architecture.md,
    /codex/05-infrastructure/deployment-ui-environment-tiers.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Runtime Tiers & Deployment Orchestration

## UI/dev-stack startup decision table (codified 2026-05-12)

> Single SSOT for "which UI startup script do I use when". Replaces the prior partial coverage scattered across
> `local-dev.md` + CLAUDE.md "Local Development" § + per-tier shorthand.

| Use case                                          | Startup script                                                    | Default mode                                                   | Ports        |
| ------------------------------------------------- | ----------------------------------------------------------------- | -------------------------------------------------------------- | ------------ |
| Consolidated portal (UI work, default)            | `bash unified-trading-system-ui/scripts/dev-tiers.sh --tier 0`    | Mock (Firebase emulators + Next dev + auto-seed)               | 3000 (UI)    |
| Portal + 2 API gateways (UI+gateway integration)  | `dev-tiers.sh --tier 1`                                           | Mock (MockStateStore in `unified-trading-api`)                 | 3000 + 8030  |
| Portal + APIs + Services (full local stack)       | `dev-tiers.sh --tier 2`                                           | Mock (full engine)                                             | 3000 + fleet |
| Static export (zero deps, browser-only)           | `dev-tiers.sh --tier static`                                      | N/A (pre-built HTML/JS)                                        | 3100         |
| Deployment-stack (deployment-api + deployment-ui) | `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh` | **REAL cloud** (`CLOUD_PROVIDER=gcp`, `CLOUD_MOCK_MODE=false`) | 8004 + 5183  |
| Backend service ad-hoc spin-up (8004-8016 range)  | `bash unified-trading-pm/scripts/dev/dev-start.sh` + flags        | Per `--mode ci\|mock\|api-real\|real`                          | per service  |

**Default mode rule (per-tier × mode matrix, codified 2026-05-12 per UI-10 audit)** — every script in this table runs in
**mock mode by default** EXCEPT `restart-deployment-stack.sh`, which hardcodes real cloud mode (operators inspecting
live cloud state). Both `dev-tiers.sh` and `dev-start.sh` accept explicit mode overrides via env / flags.

For full env-axis matrix + the `runtime_profile` v7 collapse: § "Runtime Profiles (v7)" below + § Mode axes in
[`local-dev.md`](/codex/08-workflows/local-dev.md).

---

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

> **Missing-venv tolerance:** any Python service whose `.venv` isn't built is skipped with a warning instead of failing
> the tier. T1 boots fine without `client-reporting-api`'s venv (reports tab unavailable); T2 boots whatever service
> venvs exist. To build all venvs at once:
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

`--real` runs an ADC pre-flight before launching anything; the script exits with a remediation hint if
`gcloud auth application-default print-access-token` fails. `GCP_PROJECT_ID` defaults to `central-element-323112` (the
data lake); override at the shell to point elsewhere.

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

## Live-pipeline VM topology (2026-05-08 cutover)

The live pipeline (MTDS → MDPS → features-service via Redis Streams) deploys as **three per-asset-group VM types plus
two singleton VMs**. Full architecture in [`live-pipeline-architecture.md`](live-pipeline-architecture.md). Launcher
SSOT under `deployment-service/scripts/vm/` per the VM launcher script SSOT rule.

| VM type                            | Launcher                                          | VM-name prefix        | Scope                                                                                                   | Watchdog dict entry                          |
| ---------------------------------- | ------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| **MTDS live**                      | `launch-mtds-live.sh --asset-group <ag>`          | `mtds-live-`          | Per asset_group; one VM per cluster (dispatched by `--asset-group` flag, single parameterised launcher) | `VM_PREFIX_TO_BUCKET["mtds-live-"]`          |
| **MDPS + features (asset-scoped)** | `launch-mdps-features-live.sh --asset-group <ag>` | `mdps-features-live-` | Per asset_group; one VM per cluster (dispatched by `--asset-group` flag, single parameterised launcher) | `VM_PREFIX_TO_BUCKET["mdps-features-live-"]` |
| **Features cross-cutting**         | `launch-features-cross-cutting.sh`                | `features-xc-`        | Singleton; subscribes to ALL asset_groups                                                               | `VM_PREFIX_TO_BUCKET["features-xc-"]`        |
| **Replay cascade**                 | `launch-replay-cascade.sh`                        | `replay-`             | Singleton; bridges batch→live on restart                                                                | `VM_PREFIX_TO_BUCKET["replay-"]`             |
| **Alerting service**               | unchanged batch-live wiring                       | n/a (existing)        | Singleton; consumes `StreamingHealthSnapshot` via Health-API                                            | n/a (existing)                               |

Per-asset-group expansion (5 asset_groups × 2 VM types = 10 VMs at full cluster bootstrap):

| asset_group  | MTDS VM                     | MDPS+features VM                     |
| ------------ | --------------------------- | ------------------------------------ |
| `cefi`       | `mtds-live-cefi-{ts}`       | `mdps-features-live-cefi-{ts}`       |
| `defi`       | `mtds-live-defi-{ts}`       | `mdps-features-live-defi-{ts}`       |
| `tradfi`     | `mtds-live-tradfi-{ts}`     | `mdps-features-live-tradfi-{ts}`     |
| `sports`     | `mtds-live-sports-{ts}`     | `mdps-features-live-sports-{ts}`     |
| `prediction` | `mtds-live-prediction-{ts}` | `mdps-features-live-prediction-{ts}` |

The MTDS + MDPS+features pair per asset_group is the unit of **per-asset-group live capture**. The cross-cutting VM
subscribes to every `streaming.{ag}.features_computed` stream and emits cross-instrument features (e.g.
`cross_instrument.lst_yield_vs_eth_spot`). The replay VM is a separate process (NOT folded into MTDS) that bridges batch
sources → Redis Streams on mid-day restart per the watermark-KV handoff in [`replay-subsystem.md`](replay-subsystem.md).

**Deployment-stack co-location.** Each per-asset-group VM pair shares the same project / network / region for sub-ms
Redis Stream latency. The cross-cutting VM lives in the same region but has fan-in latency budget (default 500ms grace
window per `WatermarkAlignmentFanin`). Region pinning per asset_group follows the workspace bucket-name SSOT
(`asia-northeast1` for GCP, `ap-northeast-1` for AWS — same-metro Tokyo for cross-cloud).

**Operational mode mapping.** Live-pipeline VMs run as mode-3 **Live Fleet Management** above —
`deploy-shards live start --service mtds-live-cefi` etc. Mode-4 **Cluster Bootstrap** spins all 10 per-asset-group VMs +
2 singletons in one action; mode-1 **Thermal Batch** is the batch-mode equivalent (no live VMs running, all parquet
writes via `pipeline_mode in {batch_databento, batch_tardis, ...}` per
[`/codex/02-data/pipeline-mode-partition.md`](/codex/02-data/pipeline-mode-partition.md)).

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

## Per-mode credential subset (added 2026-05-12 per Phase 7.A)

Per
[`api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
Phase 7.A, each pipeline mode (paper / batch / live) declares its required credential set. SSOT yaml:
[`unified-api-contracts/config/credentials_per_mode.yaml`](../../unified-api-contracts/unified_api_contracts/config/credentials_per_mode.yaml).

| Mode    | Custody                                                            | Venue scope                        | Data                      | Telegram                  |
| ------- | ------------------------------------------------------------------ | ---------------------------------- | ------------------------- | ------------------------- |
| `paper` | sandbox (`copper-sandbox-*` only)                                  | None (Tenderly fork fills)         | live read-only            | `telegram-bot-token-dev`  |
| `batch` | `mock`                                                             | read-scope (`<venue>-read-*` only) | live (historical sources) | `telegram-bot-token-dev`  |
| `live`  | `cloud_kms` (May-23 default) → `copper`/`fireblocks` (June-1 flip) | trade-scope (`<venue>-trade-*`)    | live                      | `telegram-bot-token-prod` |

Runtime-profile composition consumes this subset — e.g. `prod` profile implies `live` mode credential requirements;
`paper` profile implies `paper` mode credentials. The `credential-probe.sh` audit script
([`deployment-service/scripts/audit/credential-probe.sh`](../../deployment-service/scripts/audit/credential-probe.sh))
takes `--mode {paper|batch|live}` and verifies the subset against real Secret Manager / Secrets Manager state.

**Per-archetype subset** (Phase 7.B):
[`unified-api-contracts/config/credentials_per_archetype.yaml`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
— each cutover archetype (carry_staked_basis + ARBITRAGE_PRICE_DISPERSION) declares its specific wallet PKs + venue
trade keys + data sources. Operator runs `credential-probe.sh --mode live --archetype carry_staked_basis` to verify
per-archetype readiness.

**R9 sub-(a) RESOLVED 2026-05-12**: May-23 cutover defaults all wallets to `signing_surface=CLOUD_KMS_ENCRYPTED` (per
[`hsm-wallet-signing.md`](hsm-wallet-signing.md)). June-1 flips per-wallet to `COPPER_MPC` / `FIREBLOCKS_MPC` when
client provides custody credentials. The flip is config-only (no recompile, no service restart) per the
custody-providers § 1 factory pattern.

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

| Repo                   | Cloud Run service      | Region(s)      | Purpose                                                                    |
| ---------------------- | ---------------------- | -------------- | -------------------------------------------------------------------------- |
| `unified-trading-api`  | `unified-trading-api`  | varies per env | Main trading backend (now hosts user-management routes — see banner below) |
| `client-reporting-api` | `client-reporting-api` | us-central1    | Client-facing reports                                                      |
| `deployment-api`       | `deployment-api`       | us-central1    | Deployment automation                                                      |

> **`user-management-api` archived (2026-05-12 UI-8 reconciliation)** — the standalone `user-management-api` Cloud Run
> service + repo is **archived**. User management routes (`/authorize`, role/entitlement endpoints) are folded into
> `unified-trading-api`. The earlier "DO NOT deploy a parallel `user-management-api` on `odum-staging`" advisory is now
> structurally enforced — there is no `user-management-api` repo to deploy. The `user-management-ui` repo remains active
> (operator-facing console) and calls `unified-trading-api`. This row is removed from the table above to match the
> `ui-api-mapping.json` `user-management` stack `$note` ("ARCHIVED: auth-api removed. User management routes in
> unified-trading-api.") and `workspace-manifest.json` (no `user-management-api` entry).

The portal calls these via `NEXT_PUBLIC_*_URL` env vars baked at build time. **They are NOT inside the UI repo.** UAT
today runs `NEXT_PUBLIC_MOCK_API=true` and never calls them. When UAT flips to `MOCK_API=false`, the API auth
middlewares will need to dual-verify Firebase ID tokens (`['central-element-323112', 'odum-staging']`) — the
cross-project IAM is already in place; only a small middleware change is needed.

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
- uat: `hello@mail.uat.odum-research.com` ⚠️ subdomain not yet DNS-verified (status as of 2026-05-22). Either set up the
  staging subdomain in Resend (4 DKIM + 1 SPF DNS records) or temporarily point the uat branch in `lib/email/resend.ts`
  `getMailDomain()` at the prod-domain sender. Tracked under `plans/epics/deployment_and_user_management_master.md`.

### Full per-env reference

`unified-trading-system-ui/docs/core/DEPLOYMENT.md` is the SSOT for the portal-side build/deploy contract — local
Firebase Emulator Suite setup, Resend domain caveats, the exact `gcloud run` / `firebase deploy` commands per env, and
the API token-verification seam.

---

## Data-pipeline VM machine-type sizing — backed by the synthetic benchmark

The default machine type for a data-pipeline VM (`setup-data-pipeline-vm.sh`) should be the _smallest shape that keeps
the slowest cutover-pipeline stage inside the Group F item 18 "operationally-acceptable window"_, NOT a guessed
`e2-standard-N`. The per-stage profile + per-`(archetype, vm_shape)` recommendation matrix come from the synthetic-data
benchmark harness — see [`synthetic-data-benchmarking.md`](synthetic-data-benchmarking.md). Until that matrix is
populated (real-VM runs are blocked on the Phase-4-tail per
`plans/active/mock_data_pipeline_benchmarking_2026_05_10.md`), machine-type defaults remain hand-set; treat them as
provisional.
