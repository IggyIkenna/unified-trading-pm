# Deployment Orchestration — Batch, Live & Cloud Clusters

## Context

The deployment service (`deployment-service`) and deployment UI need to handle 4 operational modes:

1. **Thermal batch** — run the full pipeline once, start-to-finish, with version/code-version flexibility per service
2. **T+1 batch scheduling** — set up the daily cascade: one finishes → triggers next → cascading chain
3. **Live fleet management** — stop/start individual services that are currently running
4. **Cluster bootstrap** — spin up an entire deployment group in one action

All 4 must work at T2 (local fleet), T3-T6 (cloud), and in both mock and real modes.

---

## 1. Thermal Batch (One-Shot Pipeline Run)

**What:** Run the full data→features→ML→strategy→execution pipeline once, end-to-end.

**Flow:**

```
instruments-service (download)
  → market-tick-data-service (download per venue)
    → market-data-processing-service (OHLCV aggregation)
      → features-* services (7 feature services, parallel where independent)
        → ml-training-service (train models)
          → ml-inference-service (generate signals)
            → strategy-service (generate orders)
              → pnl-attribution-service (reconcile)
                → risk-and-exposure-service (aggregate)
                  → batch-live-reconciliation-service (compare)
```

**CLI interface:**

```bash
# Run full thermal batch
python -m deployment_service batch run \
  --cluster defi \
  --as-of-date 2026-03-21 \
  --mode mock \
  --cloud-provider local

# Run single service in batch
python -m deployment_service batch run \
  --service instruments-service \
  --operation download \
  --category DEFI \
  --as-of-date 2026-03-21
```

**Per-service flexibility:**

- Code version (git SHA / tag) per service
- Category filter (CEFI, TRADFI, DEFI, SPORTS, PREDICTION)
- Operation override
- Dry-run flag
- Each service's CLI args injected from deployment config

**Execution model:**

- Services run sequentially within the pipeline DAG
- Each service checks previous service's output before starting (readiness probe)
- Failure at any step: log error, alert, stop cascade (configurable: continue-on-error)
- On success: emit completion event → next service picks it up

---

## 2. T+1 Batch Scheduling (Daily Cascade)

**What:** Set up a scheduler that runs the thermal batch daily at a fixed time, with cascading dependencies.

**Implementation options:**

- **Cloud Scheduler + Pub/Sub** (GCP): Cloud Scheduler triggers first service → completion event triggers next
- **EventBridge + Step Functions** (AWS): EventBridge rule → Step Functions state machine
- **Cloud Run Jobs** (GCP) or **CodeBuild** (AWS): each service is a job, chained by completion triggers

**Setup CLI:**

```bash
# Set up daily T+1 batch schedule
python -m deployment_service schedule create \
  --cluster defi \
  --cron "0 6 * * *" \
  --as-of "yesterday" \
  --cloud-provider gcp

# List active schedules
python -m deployment_service schedule list

# Disable a schedule
python -m deployment_service schedule disable --cluster defi
```

**Cascade contract:** Each service, on completion:

1. Writes a completion marker: `{service}/batch/{date}/COMPLETE`
2. Emits a Pub/Sub event: `batch.{service}.complete` with `{date, status, duration, output_path}`
3. Next service in the DAG subscribes to this event and starts when all upstream markers are present

**The dependency chain is defined in deployment config, not hardcoded:**

```yaml
# deployment-service/configs/clusters/defi.yaml
cluster: defi
category: DEFI
schedule: "0 6 * * *"
pipeline:
  - service: instruments-service
    operation: download
    depends_on: []
  - service: market-tick-data-service
    operation: download
    depends_on: [instruments-service]
  - service: market-data-processing-service
    operation: compute
    depends_on: [market-tick-data-service]
  - service: features-onchain-service
    operation: compute
    depends_on: [market-data-processing-service]
  # ... rest of pipeline
```

---

## 3. Live Fleet Management (Stop/Start Running Services)

**What:** Target existing deployments, stop and start them individually, like managing jobs in batch mode.

**CLI interface:**

```bash
# List running services
python -m deployment_service live status --cluster defi

# Stop a specific service
python -m deployment_service live stop --service execution-service

# Start a specific service
python -m deployment_service live start --service execution-service --mode live

# Restart with new version
python -m deployment_service live restart \
  --service strategy-service \
  --version v0.5.2

# Scale a service
python -m deployment_service live scale \
  --service ml-inference-service \
  --replicas 3
```

**Services are async — order doesn't matter for startup:**

- Each service waits for its dependencies' readiness endpoints before processing
- Services register health at `GET /health` and readiness at `GET /readiness`
- Readiness = health + upstream dependencies healthy
- Bootstrap: start all services → they each poll their upstreams → processing begins when all ready

---

## 4. Cluster Bootstrap (Spin Up Everything)

**What:** One command to launch an entire deployment group.

**Deployment groups (clusters):**

| Cluster      | Services included                                                                                                                                                                | Notes                                 |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- |
| `cefi`       | instruments, tick-data, processing, features-delta-one, features-cross-instrument, features-multi-timeframe, ml-training, ml-inference, strategy, execution, pnl, risk, alerting | Full CeFi pipeline                    |
| `tradfi`     | Same as cefi + features-volatility, features-calendar                                                                                                                            | Adds options/futures features         |
| `defi`       | instruments, tick-data, processing, features-onchain, strategy, execution, pnl, risk                                                                                             | Skips ML for now                      |
| `sports`     | instruments, features-sports, ml-training, ml-inference, strategy, execution, pnl                                                                                                | Sports-specific pipeline              |
| `prediction` | instruments, features-sports, strategy, execution, pnl                                                                                                                           | Prediction markets (subset of sports) |
| `full`       | All services                                                                                                                                                                     | Everything                            |

**CLI:**

```bash
# Bootstrap entire cluster
python -m deployment_service cluster bootstrap \
  --cluster defi \
  --mode mock \
  --cloud-provider local

# Bootstrap with specific versions
python -m deployment_service cluster bootstrap \
  --cluster cefi \
  --versions versions.yaml \
  --cloud-provider gcp

# Tear down cluster
python -m deployment_service cluster teardown --cluster defi
```

**versions.yaml:**

```yaml
services:
  instruments-service: v0.4.1
  market-tick-data-service: v0.3.8
  strategy-service: v0.5.2
  # omitted = use latest
```

---

## 5. Cloud Deployment (T3-T6)

**The same 4 operations work against cloud targets:**

| Operation           | Local (T2)         | Cloud (T3-T6)                         |
| ------------------- | ------------------ | ------------------------------------- |
| `batch run`         | subprocess         | Cloud Run Job / CodeBuild             |
| `schedule create`   | cron job           | Cloud Scheduler / EventBridge         |
| `live start/stop`   | kill/spawn process | Cloud Run service revision / ECS task |
| `cluster bootstrap` | spawn all          | Deploy all Cloud Run services         |

**Cloud provider abstraction:**

```python
# deployment-service already has:
# - GCPCloudBuildClient (unified-cloud-interface)
# - AWSCloudBuildClient (unified-cloud-interface)
# These handle the deploy/build mechanics.
# What's needed: orchestration layer on top.
```

---

## 6. UI Integration

**Deployment UI (standalone or inside unified-trading-system-ui) provides:**

1. **Cluster dashboard** — shows all clusters, their status (running/stopped/scheduled)
2. **Pipeline view** — DAG visualization of the batch pipeline, current step highlighted
3. **Service cards** — per-service version, status, start/stop buttons, log link
4. **Version selector** — dropdown per service to pick code version for next deploy
5. **Schedule manager** — create/edit/disable T+1 schedules
6. **Batch history** — timeline of past batch runs with success/failure per step

**The Deployment UI calls the deployment-service API:**

```
POST /deployment/cluster/bootstrap   { cluster, mode, versions }
POST /deployment/batch/run           { cluster, as_of_date }
POST /deployment/schedule/create     { cluster, cron, as_of }
POST /deployment/live/start          { service, mode }
POST /deployment/live/stop           { service }
GET  /deployment/cluster/status      { cluster }
GET  /deployment/batch/history       { cluster, limit }
```

---

## 7. Relationship to Tiers

| Tier | Batch                         | Schedule           | Live               | Cluster            |
| ---- | ----------------------------- | ------------------ | ------------------ | ------------------ |
| T0   | N/A                           | N/A                | N/A                | N/A                |
| T1   | N/A (API uses MockStateStore) | N/A                | N/A                | N/A                |
| T2   | ✅ local processes            | ✅ local cron      | ✅ local processes | ✅ local processes |
| T3   | ✅ cloud jobs                 | ✅ cloud scheduler | ✅ cloud services  | ✅ cloud deploy    |
| T4   | ✅                            | ✅                 | ✅                 | ✅                 |
| T5   | ✅ (mock)                     | ✅ (mock)          | ✅ (mock)          | ✅ (mock)          |
| T6   | ✅ (real)                     | ✅ (real)          | ✅ (real)          | ✅ (real)          |

T0 and T1 don't need deployment orchestration — they're for UI development and API demos. T2+ is where deployment
orchestration becomes relevant.

---

## 8. What Exists Today

- `deployment-service/` — has `deploy.py`, Cloud Build/Run clients, basic deployment flows
- `deployment-service/configs/` — sharding configs (symlinks from PM)
- `unified-cloud-interface/` — `GCPCloudBuildClient`, `AWSCloudBuildClient`
- Deployment UI pages in `unified-trading-system-ui/app/(ops)/devops/` and `app/(platform)/services/manage/`

**What needs to be built:**

- Pipeline DAG definition (cluster YAML configs)
- Cascade orchestration (completion events → next service trigger)
- Schedule CRUD (Cloud Scheduler / EventBridge integration)
- Cluster bootstrap/teardown commands
- Deployment API endpoints (for UI)
- Version selector integration with existing CI/CD (semver-agent, workspace-manifest)
