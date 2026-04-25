---
title: "Deployment UI E2E UAT — instruments-service Build & Deploy on AWS + GCP"
status: active
priority: P0
locked_by: live-defi-rollout
locked_since: 2026-04-01
type: mixed
epic: epic-deployment
completion_gates:
  code: C3
  deployment: D3
  business: B3
repo_gates:
  deployment-ui: C0
  deployment-api: C0
  deployment-service: C0
  instruments-service: C0
  unified-trading-library: C0
  unified-trading-pm: C0
---

# Deployment UI E2E UAT — instruments-service Build & Deploy on AWS + GCP

## Context

The deployment UI (port 5183) + deployment-api (port 8004) + deployment-service form the operational control plane for
launching services on cloud infrastructure. The goal is to bring this stack to a working state where:

1. instruments-service can be built, deployed (batch + live), monitored, and torn down via the UI
2. Both AWS (EC2/Batch) and GCP (VM/Cloud Run) backends work end-to-end
3. Deployments can be triggered from the `live-defi-rollout` branch
4. VMs are properly created, monitored, and deleted
5. Data status uses the manifest writer for completion tracking
6. Logs, events, and monitoring are visible in the UI
7. The user can perform intent testing and UAT

## Issues Found During Initial Audit (2026-04-01)

| #   | Issue                                                                                                                                       | Repo                   | Severity | Status                                                                           |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | -------- | -------------------------------------------------------------------------------- |
| 1   | `@vitejs/plugin-react@6.0.1` requires Vite 8, incompatible with Vite 6                                                                      | deployment-ui          | BLOCKER  | FIXED — pinned to `^4.3.4`                                                       |
| 2   | esbuild architecture mismatch (Rosetta 2 vs ARM64)                                                                                          | deployment-ui          | BLOCKER  | FIXED — `npm install` after arch alignment                                       |
| 3   | Missing linked packages (`@unified-trading/ui-kit`, `ui-auth`, `@unified-admin/core`)                                                       | deployment-ui          | BLOCKER  | FIXED — cloned and built repos                                                   |
| 4   | `PubSubEventSink` created at module load in mock mode → crashes on health check                                                             | deployment-api         | BLOCKER  | FIXED — conditional sink init based on `is_mock_mode()`                          |
| 5   | `deployment-service` HTTP API not implemented (CLI-only)                                                                                    | deployment-api/service | HIGH     | KNOWN — shard calculation uses CLI subprocess                                    |
| 6   | AWS CodeBuild integration returns 501 Not Implemented                                                                                       | deployment-api         | MEDIUM   | KNOWN — GCP Cloud Build works                                                    |
| 7   | Data status returns empty `sources: []` in mock mode                                                                                        | deployment-api         | LOW      | Mock data needs enrichment                                                       |
| 8   | Checklist shows 0% readiness for instruments-service                                                                                        | deployment-api         | LOW      | Codex readiness data not linked                                                  |
| 9   | Cloud Build `list_builds` uses wrong filter field (`build_trigger_id` not `trigger_id`) and wrong parent format (`parent` not `project_id`) | deployment-api         | BLOCKER  | FIXED — switched to `project_id` + `trigger_id` filter                           |
| 10  | instruments-service Dockerfile references non-existent `unified-trading-services` base image                                                | instruments-service    | BLOCKER  | FIXED — changed to `unified-trading-library`                                     |
| 11  | `uv sync --frozen --no-dev --system` fails (base image uv version + path deps)                                                              | instruments-service    | BLOCKER  | FIXED — switched to `uv pip install --system --no-deps -e .`                     |
| 12  | Cloud Build QG step fails: `quality-gates.sh` sources `base-service.sh` from PM workspace (not in Docker)                                   | instruments-service    | HIGH     | KNOWN — image still pushes via `images:` section; QG needs self-contained script |
| 13  | AR builds endpoint only checks legacy repo, not `unified-trading-system`                                                                    | deployment-api         | MEDIUM   | FIXED — now checks both legacy and CB repos                                      |
| 14  | AWS CodeBuild (buildspec.yml) not implemented — no parity with Cloud Build pipeline                                                         | deployment-api         | HIGH     | Phase 6 — needs canonical template in PM                                         |

## Pre-Audit Manifest

**Repos affected by this plan:**

| Repo                    | Files to modify                     | Reason                                        |
| ----------------------- | ----------------------------------- | --------------------------------------------- |
| deployment-ui           | `package.json`, possibly components | Version fix done; UI bugs TBD                 |
| deployment-api          | `main.py` (done), routes, mock_data | Mock mode fix, data status enrichment         |
| deployment-service      | backends/, configs/                 | VM lifecycle, sharding config verification    |
| instruments-service     | Dockerfile, CLI                     | Deployment target — verify build+deploy works |
| unified-trading-library | event_sink.py (if needed)           | Mock mode event handling                      |
| unified-trading-pm      | configs/, plans/                    | Sharding configs, this plan                   |

## Execution DAG

```
Phase 0 (DONE — Local Stack Validation)
  ├── 0A: Fix UI build (esbuild, plugin-react, linked packages)
  ├── 0B: Fix API mock mode (event sink crash)
  └── 0C: Verify UI↔API proxy connectivity
        │
        ▼  Gate: Both UI+API serve, proxy works, mock data flows
Phase 1 (PARALLEL — Mock Mode Hardening)
  ├── 1A: Enrich mock data (data status, service dimensions, deployments)
  ├── 1B: Test all UI tabs in mock mode (Deploy, Status, History, Builds, Data, Readiness, Config)
  └── 1C: Fix any broken UI components or API routes
        │
        ▼  Gate: All tabs render with meaningful mock data
Phase 2 (DONE — Real Mode: Service Discovery + Config)
  ├── 2A: ✓ API real mode working (16 services, GCP ADC)
  ├── 2B: ✓ 16 services discovered from workspace configs
  ├── 2C: ✓ 19 AR images for instruments-service (legacy + CB repos)
  └── 2D: ✓ 13 Cloud Build triggers with real last_build data
        │
        ▼  Gate: PASSED — all endpoints return real GCP data
Phase 3 (DONE — instruments-service Docker Build)
  ├── 3A: ✓ Dockerfile fixed (base image + uv install), build succeeds
  ├── 3B: ✓ Image pushed to unified-trading-system AR repo (52200d7 + latest)
  └── 3C: ✓ Image appears in /api/builds/instruments-service (19 total)
        │
        ▼  Gate: Image tagged with branch slug visible in AR and UI
Phase 4 (SEQUENTIAL — GCP Batch Deployment)
  ├── 4A: Dry-run deployment via UI (instruments-service, batch, CEFI, 1 date)
  ├── 4B: Review shard preview in UI (CLI command, dimensions, count)
  ├── 4C: Execute deployment (1-2 shards only)
  ├── 4D: Monitor deployment progress in UI (SSE updates, status transitions)
  ├── 4E: Verify VM/Cloud Run Job creation in GCP Console
  ├── 4F: Verify logs accessible from UI
  └── 4G: Verify VM self-deletes after completion
        │
        ▼  Gate: instruments-service batch runs, produces data in GCS, VM cleans up
Phase 5 (SEQUENTIAL — GCP Live Deployment)
  ├── 5A: Deploy instruments-service as live Cloud Run service
  ├── 5B: Verify health endpoint responds
  ├── 5C: Test rollback from UI
  └── 5D: Verify service status tab shows live service
        │
        ▼  Gate: Live service running on Cloud Run, rollback works
Phase 6 (SEQUENTIAL — AWS Deployment)
  ├── 6A: Configure AWS credentials and provider settings
  ├── 6B: Dry-run deployment with cloud_provider=aws
  ├── 6C: Execute batch deployment on AWS (EC2 or Batch)
  ├── 6D: Monitor and verify completion
  └── 6E: Verify instance cleanup
        │
        ▼  Gate: instruments-service runs on AWS, produces output, cleans up
Phase 7 (PARALLEL — Data Status + Manifest Writer)
  ├── 7A: Verify instruments-service writes availability manifest after batch run
  ├── 7B: Verify data-status endpoint reads manifest (not just GCS blob scan)
  └── 7C: Verify Data Status tab in UI shows completion % per category/venue
        │
        ▼  Gate: Data Status tab shows real completion data from manifests
Phase 8 (PARALLEL — Multi-Shard + Sharding Combinations)
  ├── 8A: Deploy with multiple categories (CEFI + TRADFI)
  ├── 8B: Deploy with venue sharding (per-venue within category)
  ├── 8C: Deploy with date range (7-day window)
  └── 8D: Verify parallel shard execution and progress tracking
        │
        ▼  Gate: Multi-shard deployments complete with correct data output
Phase 9 (SEQUENTIAL — Monitoring, Logs, Observability)
  ├── 9A: Verify deployment history tab shows all past deployments
  ├── 9B: Verify deployment details page shows per-shard status
  ├── 9C: Verify log links work (Cloud Logging / CloudWatch)
  ├── 9D: Verify error classification and retry logic for failed shards
  └── 9E: Test deployment cancellation
        │
        ▼  Gate: Full observability — history, details, logs, errors, cancel
Phase 10 (PARALLEL — Cleanup + UAT Prep)
  ├── 10A: Ensure all test VMs/instances are deleted
  ├── 10B: Document any remaining issues as GitHub issues
  ├── 10C: Run deployment-ui quality gates (npm test, build)
  ├── 10D: Run deployment-api quality gates (quality-gates.sh)
  └── 10E: Prepare UAT checklist for human testing
        │
        ▼  Gate: QG pass on both repos, all cloud resources cleaned up
```

## Success Criteria

### Code Gates

- [ ] deployment-ui: `npm run build` passes (VITE_MOCK_API=true)
- [ ] deployment-ui: `npm test` passes
- [ ] deployment-api: `bash scripts/quality-gates.sh` passes
- [ ] deployment-service: `bash scripts/quality-gates.sh` passes (no regressions)

### Deployment Gates

- [ ] D1: instruments-service Docker image builds from live-defi-rollout
- [ ] D2: instruments-service batch deployment completes on GCP (VM or Cloud Run Job)
- [ ] D3: instruments-service batch deployment completes on AWS (EC2 or Batch)
- [ ] D4: instruments-service live deployment works on Cloud Run
- [ ] D5: VM/instance cleanup verified (no orphaned resources)

### Business Gates

- [ ] B1: All UI tabs render with meaningful data (mock or real)
- [ ] B2: Dry-run → deploy → monitor → complete flow works end-to-end
- [ ] B3: Data status shows completion % from manifest writer
- [ ] B4: Deployment history and details pages work
- [ ] B5: Logs accessible from UI
- [ ] B6: User can perform intent testing and UAT

## Phase 0: Local Stack Validation (DONE)

### 0A: Fix UI Build

- [x] Pin `@vitejs/plugin-react` to `^4.3.4` (was `^6.0.1` requiring Vite 8)
- [x] Reinstall node_modules for correct ARM64 architecture
- [x] Clone and build linked packages (ui-kit, ui-auth, admin-ui)
- [x] Verify UI serves on port 5183

### 0B: Fix API Mock Mode

- [x] Fix `PubSubEventSink` crash in mock mode — use `setup_events(mode="local")` when `is_mock_mode()`
- [x] Verify `/api/health` returns 200 in mock mode

### 0C: Verify UI↔API Connectivity

- [x] Vite proxy `/api/*` → `http://localhost:8004` working
- [x] `/api/services` returns 5 services including instruments-service
- [x] `/api/deployments` returns mock deployment history
- [x] `/api/config/venues` returns venue categories
- [x] `/api/services/instruments-service` returns dimensions (category, venue, date)

## Phase 1: Mock Mode Hardening

### 1A: Enrich Mock Data

- [ ] [AGENT] P1. Add data-status mock responses with per-category/venue completion %
- [ ] [AGENT] P1. Add mock Cloud Build trigger data for instruments-service
- [ ] [AGENT] P1. Add mock Artifact Registry build images

### 1B: Test All UI Tabs

- [ ] [HUMAN] P0. Open http://localhost:5183 and verify each tab renders:
  - Deploy tab: service selector, dimension inputs, dry-run button
  - Status tab: service health status
  - History tab: past deployments with status badges
  - Builds tab: Cloud Build history (may need mock enrichment)
  - Data Status tab: completion % chart/table
  - Readiness tab: checklist items
  - Config tab: config file browser

### 1C: Fix Broken UI Components

- [ ] [AGENT] P0. Fix any components that crash or show errors in console
- [ ] [AGENT] P1. Ensure mock mode banner displays correctly

## Phase 2: Real Mode — Service Discovery + Config

### 2A: Switch to Real Mode

- [ ] [HUMAN] P0. Set `CLOUD_MOCK_MODE=false` with valid GCP credentials
- [ ] [AGENT] P0. Verify API starts without errors in real mode
- [ ] [AGENT] P0. Fix any import/config errors that arise

### 2B: Service Discovery

- [ ] [AGENT] P0. Verify sharding configs exist for instruments-service in pm-configs/
- [ ] [AGENT] P0. Verify dimension resolution (category→venue hierarchy from venues.yaml)

### 2C: Artifact Registry

- [ ] [AGENT] P0. Verify `/api/builds/instruments-service` lists real images from Artifact Registry
- [ ] [AGENT] P1. Verify image tag format matches semver + branch slug convention

### 2D: Cloud Build Triggers

- [ ] [AGENT] P1. Verify Cloud Build trigger listing works for instruments-service
- [ ] [AGENT] P1. Verify trigger run history is accessible

## Phase 3: Docker Build

### 3A: Build Image

- [ ] [HUMAN] P0. Build instruments-service Docker image locally or via Cloud Build
  ```bash
  cd instruments-service
  gcloud builds submit --config cloudbuild.yaml \
    --substitutions=_SERVICE_NAME=instruments-service,_BRANCH_NAME=live-defi-rollout
  ```

### 3B: Push to AR

- [ ] [AGENT] P0. Verify image pushed to
      `asia-northeast1-docker.pkg.dev/{project}/unified-trading-system/instruments-service`
- [ ] [AGENT] P0. Verify both `{version}-live-defi-rollout` and `latest` tags exist

### 3C: Verify in UI

- [ ] [HUMAN] P0. Open Builds tab, confirm instruments-service image appears with correct tag

## Phase 4: GCP Batch Deployment

### 4A: Dry-Run

- [ ] [HUMAN] P0. Select instruments-service in UI → Deploy tab
- [ ] [HUMAN] P0. Configure: mode=batch, category=CEFI, date=2026-03-31, compute=cloud_run
- [ ] [HUMAN] P0. Click "Dry Run" → verify shard preview

### 4B: Review Shards

- [ ] [HUMAN] P0. Verify shard preview shows correct CLI command:
  ```
  instruments-service --operation instruments --mode batch --asset-group CEFI --start-date 2026-03-31
  ```
- [ ] [HUMAN] P0. Verify shard count matches expected (1 shard for single date+category)

### 4C: Execute Deployment

- [ ] [HUMAN] P0. Click "Deploy" on reviewed dry-run
- [ ] [AGENT] P0. Verify deployment state transitions: pending → running → completed/failed

### 4D: Monitor Progress

- [ ] [HUMAN] P0. Verify SSE updates show real-time progress in UI
- [ ] [HUMAN] P0. Verify deployment details page shows per-shard status

### 4E: Verify Cloud Resources

- [ ] [HUMAN] P0. Check GCP Console: Cloud Run Job or VM created
- [ ] [HUMAN] P0. Verify correct Docker image and env vars

### 4F: Verify Logs

- [ ] [HUMAN] P0. Click log link in UI → opens Cloud Logging with correct filter

### 4G: Verify Cleanup

- [ ] [HUMAN] P0. After completion, verify VM/job is deleted
- [ ] [AGENT] P1. Verify zombie cleanup logic works if VM fails to self-delete

## Phase 5: GCP Live Deployment

### 5A: Deploy Live

- [ ] [HUMAN] P0. Deploy instruments-service as live Cloud Run service via UI
- [ ] [AGENT] P0. Verify Cloud Run service revision created

### 5B: Health Check

- [ ] [HUMAN] P0. Verify `/health` endpoint responds on deployed service

### 5C: Rollback

- [ ] [HUMAN] P1. Test rollback button in UI → reverts to previous revision

### 5D: Service Status

- [ ] [HUMAN] P1. Verify Service Status tab shows live service health

## Phase 6: AWS Deployment

### 6A: Configure AWS

- [ ] [HUMAN] P0. Set `CLOUD_PROVIDER=aws` with valid AWS credentials
- [ ] [AGENT] P0. Verify provider detection switches to AWS backends

### 6B: Dry-Run on AWS

- [ ] [HUMAN] P0. Dry-run instruments-service deployment with AWS backend
- [ ] [HUMAN] P0. Verify shard preview shows AWS-specific command

### 6C: Execute on AWS

- [ ] [HUMAN] P0. Deploy 1-2 shards on AWS (EC2 or Batch)
- [ ] [AGENT] P0. Verify job creation in AWS Console

### 6D: Monitor

- [ ] [HUMAN] P0. Verify deployment progress tracking works for AWS jobs

### 6E: Cleanup

- [ ] [HUMAN] P0. Verify EC2 instances or Batch jobs cleaned up after completion

## Phase 7: Data Status + Manifest Writer

### 7A: Manifest Write

- [ ] [AGENT] P0. Verify instruments-service writes availability manifest to GCS after batch run
- [ ] [AGENT] P0. Check manifest format: `gs://{bucket}/availability-index/` with Parquet files

### 7B: Manifest Read

- [ ] [AGENT] P0. Verify data-status endpoint reads from manifest (not blob scan)
- [ ] [AGENT] P0. Verify `source=manifest` parameter works

### 7C: UI Data Status

- [ ] [HUMAN] P0. Open Data Status tab → select instruments-service → verify completion % by category/venue

## Phase 8: Multi-Shard Deployments

### 8A: Multi-Category

- [ ] [HUMAN] P1. Deploy instruments-service with categories=CEFI,TRADFI simultaneously

### 8B: Venue Sharding

- [ ] [HUMAN] P1. Deploy with per-venue sharding within CEFI

### 8C: Date Range

- [ ] [HUMAN] P1. Deploy with 7-day date range → verify one shard per day

### 8D: Parallel Execution

- [ ] [HUMAN] P1. Verify multiple shards execute in parallel
- [ ] [HUMAN] P1. Verify progress bar shows overall + per-shard status

## Phase 9: Monitoring + Observability

### 9A: Deployment History

- [ ] [HUMAN] P1. Verify all test deployments appear in History tab
- [ ] [HUMAN] P1. Verify status badges (completed, failed, running, pending)

### 9B: Deployment Details

- [ ] [HUMAN] P1. Click a deployment → verify per-shard breakdown

### 9C: Log Links

- [ ] [HUMAN] P1. Verify Cloud Logging links for GCP deployments
- [ ] [HUMAN] P1. Verify CloudWatch links for AWS deployments

### 9D: Error Handling

- [ ] [AGENT] P1. Test failed shard scenario → verify error classification
- [ ] [AGENT] P1. Test retry-failed-shards endpoint

### 9E: Cancellation

- [ ] [HUMAN] P1. Test cancel button during running deployment

## Phase 10: Cleanup + UAT Prep

### 10A: Resource Cleanup

- [ ] [HUMAN] P0. Verify all test VMs/instances/jobs deleted from cloud
- [ ] [AGENT] P0. List any orphaned resources and clean up

### 10B: Issue Logging

- [ ] [AGENT] P1. Document remaining issues as GitHub issues on relevant repos

### 10C: UI Quality Gates

- [ ] [AGENT] P0. Run `cd deployment-ui && VITE_MOCK_API=true npx vite build` — must pass
- [ ] [AGENT] P0. Run `cd deployment-ui && CI=true npm test -- --run` — must pass

### 10D: API Quality Gates

- [ ] [AGENT] P0. Run `cd deployment-api && bash scripts/quality-gates.sh` — must pass

### 10E: UAT Checklist

- [ ] [AGENT] P1. Prepare human UAT checklist covering:
  - Single service deploy (batch + live)
  - Multi-shard deploy (2+ categories, date range)
  - Cross-cloud deploy (GCP + AWS)
  - VM lifecycle (create → run → complete → delete)
  - Data status verification
  - Log access
  - Deploy cancel + rollback
  - Error recovery (retry failed shards)
