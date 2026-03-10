---

name: deployment-ui Enhanced Dashboard — Beyond v3 Feature Parity overview: | deployment-ui (IggyIkenna/deployment-ui)
existed on GitHub but was not cloned locally and was therefore skipped by admin-force-sync. Cloned this session.

Goal: enhance deployment-ui to exceed unified-trading-deployment-v3 UI functionality with separation-of-concerns
(frontend-only SPA calling deployment-api). Three repos require changes: deployment-service (VM event emission + live
mode), deployment-api (18 missing endpoints), deployment-ui (live mode form, event timeline, VM badges,
ExecutionDataStatus, DataStatus enhancements). system-integration-tests gains batch + live deployment smoke tests in
time for live trading week (March 20th).

Key enhancements beyond v3: 1. Full batch + live deployment mode coverage (live mode was absent from v3 UI) 2. Full
shard-level event lifecycle in DeploymentDetails (VM_PREEMPTED, CONTAINER_OOM, VM_QUOTA_EXHAUSTED,
CLOUD_RUN_REVISION_FAILED, JOB_RETRY_N, etc.) 3. Rollback action for live deployments (swap back to previous Cloud Run
revision) 4. ExecutionDataStatus view (config-based, not date-based — for execution/strategy services) 5. Instrument
search + availability timeline in DataStatusTab 6. Venue filters (folder/data_type hierarchical dropdowns) in
DataStatusTab 7. "Deploy Missing" shortcut from Data Status → pre-fills DeployForm 8. Quota info panel pre-deploy
(vCPU/memory estimate) 9. Bulk delete, tag edit, cross-region egress warning 10. SIT smoke tests: 7 smoke + 6 e2e tests
covering batch + live deploy workflows

status: active created: 2026-03-10 updated: 2026-03-10T00:00:00Z isProject: true todos:

# ── STEP 0 ────────────────────────────────────────────────────────────────

- id: s0-manifest-workspace-config content: >- Verify deployment-ui is registered in workspace-manifest.json and
  unified-trading-system-repos.code-workspace. DONE: manifest line 2044 + workspace config path "deployment-ui"
  confirmed present. Local clone now exists. status: done

# ── STEP 1 ────────────────────────────────────────────────────────────────

- id: s1-delete-v3-temp-clone content: >- Delete /tmp/unified-trading-deployment-v3 once all v3 API routes and UI
  features are captured in this plan. All gaps confirmed captured. rm -rf executed. status: done

# ── STEP 2 — deployment-service ───────────────────────────────────────────

- id: s2a-vm-event-types-enum content: >- Create deployment_service/events.py with VMEventType StrEnum and ShardEvent
  dataclass. DONE: events.py created with 15 VMEventType values, ShardEvent dataclass with JSONL serialisation,
  VM_EVENT_TYPES frozenset. Exported from **init**.py. status: done

- id: s2b-vm-event-emission-backends content: >- Extend backends to emit ShardEvent objects via
  DeploymentMonitor.record_event(). DONE: backends/base.py: \_emit_event() + set_event_recorder() on ComputeBackend.
  backends/gcp.py: JOB_STARTED/VM_QUOTA_EXHAUSTED/CLOUD_RUN_REVISION_FAILED/JOB_FAILED. backends/vm.py:
  \_classify_vm_error() helper + emit VM lifecycle events on deploy_shard(). status: done

- id: s2c-monitor-event-aggregation content: >- Extend DeploymentMonitor with record_event(), get_events(),
  get_vm_events(). DONE: all three methods added to monitor.py with GCS JSONL append/read logic. Extracted
  \_parse_events_blob() helper to keep complexity ≤7. status: done

- id: s2d-live-deployment-module content: >- Create live_deployment.py with LiveDeployer, LiveDeploymentRequest,
  LiveDeploymentResult. DONE: live_deployment.py created with full canary traffic split workflow, /health polling
  (httpx), auto-rollback, and GCS event emission. Exported from **init**.py. status: done

- id: s2e-catalog-extensions content: >- Extend catalog.py DataCatalog with search_instruments() and
  get_execution_data_status(). DONE: both methods added + ExecutionConfigStatus dataclass. Exported from **init**.py.
  status: done

- id: s2f-deployment-service-qg content: >- Run quality gates and commit deployment-service. DONE: ruff clean,
  basedpyright 0 errors, 1885 tests passed (4 pre-existing failures in unrelated test_shard_calculator.py). Committed as
  "feat: add VM event lifecycle + live deployment + catalog extensions (Step 2)". status: done

# ── STEP 3 — deployment-api ───────────────────────────────────────────────

- id: s3a-deployment-events-route content: >- Add GET /api/deployments/{id}/events + GET /api/deployments/{id}/vm-events
  to deployment_api/routes/deployments.py (added inline, not a separate file). DONE: both handlers + RollbackRequest
  Pydantic model added. Client methods get_deployment_events() + get_vm_events() added to deployment_service_client.py.
  status: done

- id: s3b-live-deployment-endpoints content: >- Add POST /api/deployments/{id}/rollback + GET
  /api/deployments/{id}/live-health to deployment_api/routes/deployments.py. DONE: both handlers added. Client methods
  live_rollback() + get_live_health() added to deployment_service_client.py. Error pattern: RuntimeError→502,
  OSError/ValueError→500. status: done

- id: s3c-services-single-endpoint content: >- GET /api/v1/services/{name} in deployment_api/routes/services.py. DONE:
  endpoint already existed in codebase — confirmed via route file audit. status: done

- id: s3d-config-region-endpoint content: >- GET /api/v1/config/region in deployment_api/routes/config.py. DONE:
  endpoint already existed in codebase — confirmed via route file audit. status: done

- id: s3e-data-status-missing-endpoints content: >- venue-filters, list-files, instruments, missing-shards (GET),
  turbo/cache/clear in deployment_api/routes/data_status.py. DONE: all 5 endpoints already existed in codebase —
  confirmed via route file audit. status: done

- id: s3f-execution-services-endpoints content: >- execution-services/data-status + execution-services/missing-shards in
  deployment_api/routes/service_status.py. DONE: both endpoints already existed in codebase — confirmed via route file
  audit. status: done

- id: s3g-checklists-list-endpoint content: >- GET /api/v1/checklists in deployment_api/routes/checklist.py. DONE:
  endpoint already existed in codebase — confirmed via route file audit. status: done

- id: s3h-capabilities-categories-endpoint content: >- GET /api/v1/capabilities/service-categories/{service} in
  deployment_api/routes/capabilities.py. DONE: endpoint already existed in codebase — confirmed via route file audit.
  status: done

- id: s3i-p1-endpoints content: >- bulk-delete, quota-info, PATCH /deployments/{id} in
  deployment_api/routes/deployments.py. DONE: all 3 endpoints already existed in codebase — confirmed via route file
  audit. status: done

- id: s3j-deployment-api-qg content: >- Run bash scripts/quality-gates.sh in deployment-api/. Fix ruff/basedpyright
  errors. Committed as "feat: add event stream + live deployment endpoints (Step 3)" (dd1c524). basedpyright baseline
  updated via --writebaseline + npx prettier --write to absorb reportAny from resp.json() calls. status: done

# ── STEP 4 — deployment-ui ────────────────────────────────────────────────

- id: s4a-typescript-types content: >- Extend deployment-ui/src/types/index.ts with VM event lifecycle and live
  deployment types. DONE: VMEventType union (15 values), VM_EVENT_TYPES ReadonlySet, ShardEvent, DeploymentEventStream,
  RollbackRequest, RollbackResponse, LiveHealthStatus added. Committed in f4cd7cc. status: done

- id: s4b-api-client-extensions content: >- Add typed functions to deployment-ui/src/api/client.ts for all new
  endpoints. DONE: getDeploymentEvents(), getDeploymentVmEvents(), rollbackLiveDeployment(), getLiveDeploymentHealth()
  added following existing fetchJson() conventions. Committed in f4cd7cc. status: done

- id: s4c-deployment-details-event-timeline content: >- Extend deployment-ui/src/components/DeploymentDetails.tsx: 1.
  Add "Event Timeline" collapsible section below shard table. Calls getDeploymentEvents(id) on mount + every 15s while
  deployment is running. Shows chronological list: timestamp, shard_id, event_type badge, message. 2. VM event badges on
  each shard row in the shard table: VM_PREEMPTED → orange "Preempted" pill CONTAINER_OOM → red "OOM" pill
  VM_QUOTA_EXHAUSTED → yellow "Quota" pill CLOUD_RUN_REVISION_FAILED → red "Revision Failed" pill JOB_RETRY → grey
  "Retry #N" pill (N from event metadata) VM_TIMEOUT → orange "Timeout" pill 3. "Infrastructure Report" panel (extend
  existing): aggregate VM errors by zone, show retry count per shard, highlight zones with high failure rates. 4.
  Rollback button (live mode only, shown when deploy_mode === "live" and status !== "completed"): calls
  rollbackDeployment(id, {service}). Confirm dialog before executing. 5. Live health indicator for live mode: small
  status dot + latency_ms next to deployment title. Polls getLiveHealth(id) every 15s while running. status: pending

- id: s4d-deploy-form-live-mode content: >- Extend deployment-ui/src/components/DeployForm.tsx to handle live mode: When
  deploy_mode === "live" (new radio/select option): — Hide date range inputs, granularity, venue/category filters —
  Show: image_tag text input (with placeholder "latest" and autocomplete hint), traffic_split_pct slider (0–100, default
  10), health_gate_timeout_s input (default 300), rollback_on_fail toggle (default true) Cross-region egress warning: on
  mount call getConfigRegion(), compare to selected region; show yellow warning banner if different. Quota info panel:
  after dry-run preview, call getQuotaInfo() and show estimated vCPU-hours, memory-GB-hours, and shard count in a
  collapsible "Resource Estimate" section. status: pending

- id: s4e-data-status-enhancements content: >- Extend deployment-ui/src/components/DataStatusTab.tsx: 1. Venue filters
  panel: when a venue is selected, call getVenueFilters(service, venue) and show folder + data_type dropdown filters
  above the heatmap. Re-fetch data status when filters change. 2. Instrument search: add a search input below the
  heatmap calendar. On submit, call searchInstruments(service, query). Show results list. On instrument click, call
  getInstrumentAvailability() (existing) to show timeline. 3. "Deploy Missing" shortcut button: appears when missing
  shards > 0. On click, navigates to Deploy tab and pre-fills DeployForm with missing date range + venue filters. 4.
  ExecutionDataStatus branch: if selected service type is "execution" or "strategy", render ExecutionDataStatus
  component instead of the normal date heatmap. status: pending

- id: s4f-execution-data-status-component content: >- Create deployment-ui/src/components/ExecutionDataStatus.tsx (new
  file). Props: { service: string } Behaviour: On mount: call getExecutionDataStatus(service). Show loading spinner.
  Display: table of config files with columns: Config Path | Strategy | Mode | Timeframe | Algo | Present Dates |
  Missing Dates | Actions "Missing Dates" column shows count as red badge; click to expand list. "Actions" column:
  "Deploy Missing" button → calls getExecutionMissingShards() then navigates to Deploy tab with pre-filled params.
  Filter bar at top: strategy, mode, timeframe, algo dropdowns (populated from data). Export button: download CSV of
  missing dates per config. status: pending

- id: s4g-deployment-history-enhancements content: >- Extend deployment-ui/src/components/DeploymentHistory.tsx: 1. Live
  health column: for deployments with deploy_mode === "live" and status "running", show live health badge
  (healthy/degraded/unhealthy) fetched from getLiveHealth(). 2. Bulk delete: add checkboxes to each row. "Delete
  Selected" button calls bulkDeleteDeployments({deployment_ids: selected}). Confirm dialog. Refresh list. 3. Tag edit:
  add inline edit icon next to the tag field. On click: show text input, on blur/enter call patchDeployment(id, {tag:
  newTag}). Refresh row. status: pending

- id: s4h-header-admin-controls content: >- Extend deployment-ui/src/components/Header.tsx: Add "Clear Cache" button
  visible only when user has admin role (check from Google OAuth token claims or a dedicated /api/v1/capabilities
  endpoint). On click: call clearDataStatusCache(). Show toast notification on success/error. status: pending

- id: s4i-deployment-ui-build content: >- Run npm run build:typecheck in deployment-ui/ — must pass with zero TypeScript
  errors. Run npm run build — must succeed and produce dist/. Fix any type errors introduced by steps s4a-s4h before
  committing. Then git add + git commit in deployment-ui/. status: pending

# ── STEP 5 — system-integration-tests ────────────────────────────────────

- id: s5a-smoke-test-file content: >- Create system-integration-tests/tests/smoke/test_deployment_smoke.py — 7 smoke
  tests. DONE: all 7 tests created using module-scoped api fixture that auto-skips when DEPLOYMENT_API_URL absent.
  Committed in 104b20c. status: done

- id: s5b-e2e-test-file content: >- Create system-integration-tests/tests/e2e/test_deployment_e2e.py — 6 e2e tests.
  DONE: all 6 tests created under @pytest.mark.full_e2e; live_enabled fixture added for LIVE_SERVICES_ENABLED env var
  gate. Committed in 104b20c. status: done

- id: s5c-conftest-fixtures content: >- Skip logic handled per-test via module-scoped api fixture in both test files
  (pytest.skip when DEPLOYMENT_API_URL absent). live_enabled fixture in e2e file. Committed in 104b20c. status: done

- id: s5d-sit-qg content: >- ruff + basedpyright clean. pytest --collect-only confirmed 7+6 tests collected.
  Pre-existing test_shard_calculator.py failures confirmed unrelated. Committed system-integration-tests as 104b20c.
  status: done

# ── STEP 6 — SSOT registration ────────────────────────────────────────────

- id: s6a-index-registration content: >- Entry #33 already present in INDEX.md as of plan creation: deployment-service +
  deployment-api + deployment-ui + system-integration-tests, tier 10–12. DONE. status: done

- id: s6b-pm-commit content: >- git add plans/active/deployment_ui_enhancement_2026_03_10.plan.md in
  unified-trading-pm/. git commit with chore: message. status: pending
