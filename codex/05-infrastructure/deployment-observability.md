# Deployment Observability — live/batch/paper × GCP/AWS at /repos grade (SSOT)

> Every compute unit (a **VM** or a **Cloud Run job**) is a **classified deployment target** tracked under a
> live/batch/paper umbrella, surfaced in deployment-ui `/deployments` + Slack at the same grade the CI/CD `/repos` page
> gives repos. GCP is complete; AWS rides the same contract (Phase 5). Plan:
> `plans/active/deployment_observability_parity_live_batch_paper_2026_06_22.md` (parent epic `observability_master`).

## The umbrella model (the classification everything reads)

`DeploymentUmbrella` (UAC `canonical/crosscutting/lifecycle_class.py`, StrEnum): **LIVE / BATCH / PAPER / EXPERIMENT**.
Each target classifies to exactly one umbrella × `DeploymentCloud{GCP,AWS}` × `DeploymentKind{VM,CLOUD_RUN_JOB}` ×
service × asset_group, materialised as a frozen `DeploymentTarget`.

| Umbrella       | Derives from                                                                                                                                                                                                   | Examples                                                                                                                              |
| -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| **LIVE**       | `lifecycle_class = LONG_LIVED_LIVE`                                                                                                                                                                            | live capture / trading / risk VMs                                                                                                     |
| **BATCH**      | `lifecycle_class ∈ {EPHEMERAL_BATCH, SCHEDULED_RECURRING}`                                                                                                                                                     | backfill VMs (`cefi-*`, `defi-backfill-*`, `api-football-*`) + the Cloud Run audits/consolidator/catalogue/expected-universe/monitors |
| **PAPER**      | **explicit override** (no single lifecycle_class — a paper cron is SCHEDULED_RECURRING): VM prefix `defi-paper-`/`funding-ensemble-paper-`/`strategy-paper-` or `is_paper`, carried on `VmPrefixSpec.umbrella` | paper-trading VMs + the `blrs-daily-determinism`/paper-week Cloud Run jobs                                                            |
| **EXPERIMENT** | `lifecycle_class = EPHEMERAL_EXPERIMENT`                                                                                                                                                                       | `exp-{ml,strategy,execution}-*` (folded under Batch in the UI by default)                                                             |

`UMBRELLA_FOR_LIFECYCLE_CLASS` (UAC) is the lifecycle→umbrella map; PAPER is absent from it (always an override).

## The classification SSOT (one resolver, one registry — never re-derive per surface)

- **`classify_deployment_target(name, *, lifecycle_class=None, cloud=GCP, kind=VM, is_paper=None, asset_group=None, service=None) -> DeploymentTarget`**
  — `deployment-service/deployment_service/deployment_classification.py`. PAPER if `is_paper`/a paper-prefix match; else
  `UMBRELLA_FOR_LIFECYCLE_CLASS[lifecycle_class]`; **raises `UnclassifiedDeploymentError` — never a silent default**.
  service/asset_group derive from the VM prefix (`VM_PREFIX_TO_BUCKET`) or job name.
- **`CLOUD_RUN_JOBS: Final[tuple[DeploymentTarget, ...]]`** —
  `deployment-service/deployment_service/cloud_run_job_registry.py`. **61 classified jobs** (58 BATCH / 3 PAPER)
  covering every `terraform/gcp/*_scheduler.tf`. A guard test (`test_every_scheduler_tf_job_is_registered`) **fails CI
  if a scheduler tf has no registry entry** — the "added a Cloud Run job, forgot to classify" catch (mirrors the
  VM_PREFIX_TO_BUCKET guard).
- **`VmPrefixSpec.umbrella`** (the override field) is set on the 3 paper prefixes in `vm_zombie_watchdog.py`.

## The API contract (deployment-api — the /repos-grade inventory)

deployment-api **depends on deployment-service** (sanctioned editable path dep — "deployment-api → deployment-service is
the real dependency direction"), so it imports the resolver + registry directly. Routes
(`routes/deployments_inventory.py`):

- **`GET /api/deployments/inventory?umbrella=&cloud=&service=&asset_group=&status=`** →
  `DeploymentInventoryResponse{items[], total, vm_count, cloud_run_job_count}`. Each
  `DeploymentItem = {name, kind, umbrella, cloud, service, asset_group, status, last_run_at, exit_code, heartbeat_age_seconds, captured_progress, run_log_uri}`.
  VMs come from the `DeploymentsRegistry` (same source as `/api/vm-deployments`); Cloud Run jobs come from
  `CLOUD_RUN_JOBS` enriched with their latest execution status via the GCP `run_v2` client
  (`routes/_cloud_run_executions.py`, the sanctioned `_gcp_sdk` seam). Status: `succeeded`(exit 0) / `failed`(non-zero
  incl. 137 OOM) / `running` / `stale`(heartbeat >15min) / `unknown`(GCP error → honest-degrade).
- **`GET /api/deployments/umbrella/{umbrella}/summary`** →
  `UmbrellaSummaryResponse{umbrella, total, counts_by_status, stale_count, last_failure}` — the /repos-overview
  equivalent.

(Note: bare `/api/deployments` was already owned by service-version deploys; the inventory lives at
`/api/deployments/inventory`.)

## The UI surface (deployment-ui `/deployments`)

`src/pages/Deployments.tsx` — **Live / Batch / Paper umbrella tabs** at RepoCi grade: a status-tone matrix of VMs +
Cloud Run jobs (kind icon, GCP/AWS cloud badge, status badge, exit_code with `137 (OOM)`/non-zero red,
captured-progress), a per-umbrella summary header, and URL-param-backed cloud/status/asset_group filters
(`useSearchParams` → deep-linkable). Drill-down `/deployments/:name` reuses `VmEventsTimeline` + `StreamingLogsPanel`
(live log tail + event timeline) + the GCS `run.log` link. pw:L2-gated (`tests/smoke/deployments-page.spec.ts`).

## Slack parity + alert enrichment

- **Deployment lifecycle** (`DEPLOYMENT_STARTED/COMPLETED/FAILED`, UTL events) routes via
  `alerting-service/rules/deployment_rules.py` → `#data-pipeline-alerts` with the **umbrella + cloud + a
  `/deployments/{name}` deep-link** (FAILED=CRITICAL pages; STARTED/COMPLETED=INFO).
- **Every DP\_\*/deployment alert is self-sufficient** (`notifiers/data_pipeline_slack.py`): a fenced-code **trace
  block** (the FetchEvidence dict / exit_code+run_log_tail / error_message, truncated to 3000 chars) + **deep-link
  buttons** — VM logs `{base}/ops/vms/{vm}`, Deployment `{base}/deployments/{vm}`, Data status
  `{base}/service/{svc}/data-status?asset_group={ag}`, and the GCS `run.log` console link. Base from config
  `deployment_ui_base_url` (SM/env `DEPLOYMENT_UI_BASE_URL`, hot-reloaded; `""` → links omitted, never broken).

## Durable logs (the substrate every surface reads)

Every GCP VM launcher streams run.log + heartbeat + `EXIT_STATUS` to `gs://deployment-scripts-{pid}/vm-logs/{VM_NAME}/`
(self-delete-proof) via `vm-exec-with-gcs-tee.sh` / `setup-data-pipeline-vm.sh` / `lc_log_upload_trap_block`. A coverage
guard (`tests/unit/test_vm_launcher_scripts.py::TestDurableLogStreamerCoverage`) **fails if a GCP `launch-*.sh` doesn't
stream** (whitelist for long-lived/systemd-logged service VMs + AWS + fan-out wrappers, each with a reason).

## Coverage status

- **GCP: COMPLETE** — every VM prefix + every Cloud Run job + every GCP launcher is classified/tracked/streamed,
  enforced by 3 guard tests (VM-prefix classify, scheduler-tf registry, launcher durable-log). 0 unclassified / 0
  untracked is a CI invariant, not a one-time audit.
- **AWS: Phase 5** — EC2 backfill VMs + Batch Fargate ride the same `DeploymentTarget`/`cloud=AWS` contract;
  `/api/deployments/inventory` returns `cloud=aws` items once the AWS census is wired.

## Anti-patterns (banned)

- A surface re-deriving umbrella/service/asset_group instead of reading `classify_deployment_target` / `CLOUD_RUN_JOBS`.
- A new Cloud Run scheduler tf or GCP launcher without a registry entry / durable-log streamer (the guards catch it —
  don't whitelist to dodge).
- A silent default umbrella (`classify_deployment_target` raises `UnclassifiedDeploymentError` — fix the classification,
  don't swallow).
