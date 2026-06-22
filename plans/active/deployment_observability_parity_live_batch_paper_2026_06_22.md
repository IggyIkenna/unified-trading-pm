---
title: "Deployment Observability Parity — live/batch/paper × GCP/AWS at /repos grade"
created: 2026-06-22
parent_epic: observability_master
assigned_vm: vm-cross-cutting
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 13
locked_by: live-defi-rollout
locked_since: 2026-06-22
related_plans:
  - deployment_ui_monitoring_pane_2026_06_19.md
  - vm_launcher_durable_log_observability_2026_06_19.md
  - ci_dashboard_deployment_ui_2026_06_10.md
  - monitoring_control_plane_master_2026_06_10.md
  - data_pipeline_hardening_self_monitoring_2026_06_22.md
  - data_feed_sla_registry_and_active_self_healing_2026_06_19.md
priority: P2
status: active
---

# Deployment Observability Parity — live / batch / paper × GCP / AWS

> **Operator intent (2026-06-22)**: "CI/CD observability across Slack + deployment-ui is already great for the `/repos`
> page — bring **live, batch, and paper deployments** to the SAME grade, where **every VM or Cloud Run job is tracked
> under one of those umbrellas** for **GCP and AWS, starting with GCP to completion, all documented and done.** Build it
> all, even the long hard stuff, drive to completion." Reuse what's there — no reinventing.

## Reuse, do NOT rebuild (the gold standard + the existing pieces)

| Capability                                      | Exists — reuse                                                                                                                           | Where                                                                                 |
| ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| Gold-standard surface grade                     | `/repos` CI matrix (overview/detail/stuck-PR/SIT/alerts)                                                                                 | `deployment-ui/src/pages/RepoCi.tsx` + `deployment-api` repos/ci routes               |
| Deployment-history backbone                     | `/vm-deployments` + Monitor tab (Backfill/Live/Experiments/Scheduled)                                                                    | `deployment-ui` `DeploymentHistory.tsx` / `MonitorTab.tsx`; `GET /api/vm-deployments` |
| Per-VM events + live log tail                   | `/ops/vms/:vm` `VmEventsTimeline` + `StreamingLogsPanel` (SSE)                                                                           | `deployment-ui`; `GET /api/vm/{vm}/events`, `/api/vm/logs/{vm}`                       |
| Unified alert ledger (has `data_pipeline` kind) | `/alerts` ← `GET /api/alerts`                                                                                                            | `deployment-ui/src/pages/Alerts.tsx`                                                  |
| VM classification                               | `VM_PREFIX_TO_BUCKET` → `VmPrefixSpec(lifecycle_class)` (EPHEMERAL_BATCH / LONG_LIVED_LIVE / SCHEDULED_RECURRING / EPHEMERAL_EXPERIMENT) | `deployment-service/scripts/vm/vm_zombie_watchdog.py`                                 |
| Durable VM logs (self-delete-proof)             | `gs://deployment-scripts-{pid}/vm-logs/{vm}/run.log` + `EXIT_STATUS`                                                                     | `vm-exec-with-gcs-tee.sh`                                                             |
| Deployment registry (heartbeat)                 | `/api/vm-deployments` + reconcile                                                                                                        | `deployment-api/routes/vm_*`                                                          |
| Cloud Run jobs (~20)                            | terraform schedulers                                                                                                                     | `deployment-service/terraform/gcp/*_scheduler.tf`                                     |

## The umbrella model (the classification the whole surface hangs off)

Every compute unit (a **VM** or a **Cloud Run job/execution**) classifies to exactly one **umbrella** × **cloud** ×
**service** × **asset_group**:

| Umbrella                                                      | Derives from                                                                                                           | Examples                                                                                                                       |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **batch**                                                     | `lifecycle_class ∈ {EPHEMERAL_BATCH, SCHEDULED_RECURRING}`                                                             | backfill VMs (`cefi-*`, `defi-backfill-*`, `api-football-backfill`), Cloud Run audits/consolidator/catalogue/expected-universe |
| **live**                                                      | `lifecycle_class = LONG_LIVED_LIVE`                                                                                    | live capture/trading VMs                                                                                                       |
| **paper**                                                     | the paper launchers (`launch-defi-paper-trading-vm.sh`, `launch-funding-ensemble-paper-cron-vm.sh`, paper-smoke-gated) | paper-trading VMs/crons                                                                                                        |
| **experiment** (4th, folded under batch in the UI by default) | `lifecycle_class = EPHEMERAL_EXPERIMENT`                                                                               | `exp-{ml,strategy,execution}-*`                                                                                                |

GCP first (operator), then AWS. Cloud Run jobs are GCP-only today; AWS equivalents are Batch Fargate + EventBridge.

---

## Phase 0 — Classification spine (the SSOT every surface reads)

- [x] [DESIGN] P0. ✅ `DeploymentUmbrella` StrEnum (`live|batch|paper|experiment`) + `DeploymentTarget` value-object
      `{name, kind: vm|cloud_run_job, umbrella, cloud: gcp|aws, service, asset_group, lifecycle_class}` in UAC. —
      **unified-api-contracts** — unified-api-contracts@34bb0f16 (`DeploymentUmbrella`/`DeploymentTarget`/`DeploymentCloud`/`DeploymentKind`/`UMBRELLA_FOR_LIFECYCLE_CLASS` in `canonical/crosscutting/lifecycle_class.py`; importable `from unified_api_contracts import DeploymentUmbrella`)
- [x] [CODE] P0. ✅ `classify_deployment_target(name, *, lifecycle_class=None, is_paper=None) -> DeploymentTarget` —
      derives umbrella from `lifecycle_class` + the paper-launcher set + VM-prefix; a single resolver both the watchdog
      and deployment-api call. Extend `VmPrefixSpec` with an explicit `umbrella` override where lifecycle_class is
      ambiguous (paper crons are SCHEDULED_RECURRING but umbrella=paper). — **unified-trading-library /
      deployment-service** — deployment-service@360678e (`deployment_service/deployment_classification.py` resolver + `PAPER_PREFIXES` + `UnclassifiedDeploymentError` no-silent-default) + unified-api-contracts@3c7dd51a (`VmPrefixSpec.umbrella: DeploymentUmbrella | None = None` field) + watchdog sets `umbrella=DeploymentUmbrella.PAPER` on the 3 paper prefixes
- [x] [CODE] P0. ✅ **Cloud Run job registry** — enumerate the ~20 `*_scheduler.tf` jobs into a classified inventory (name
      → umbrella/service/ag); a generator that reads terraform or a checked-in manifest so the surface knows every job,
      not just VMs. — **deployment-service** — deployment-service@360678e (`deployment_service/cloud_run_job_registry.py` `CLOUD_RUN_JOBS: Final[tuple[DeploymentTarget, ...]]` — 49 jobs from all 24 `*_scheduler.tf`: BATCH infra/consolidator/catalogue/expected-universe/monitors/digests/hygiene/rollups/t1-recon + 3 PAPER paper-week/paper-engine)
- [x] [TEST] P0. ✅ Every VM prefix + every Cloud Run job classifies to exactly one umbrella; paper launchers → paper; no
      `UNCLASSIFIED` (a CI check fails on an unclassified compute unit — the "added launcher, forgot to register" guard,
      extended to umbrellas). — **deployment-service** — deployment-service@360678e (`tests/unit/test_cloud_run_job_registry_guard.py`, 10 tests: every VmPrefixSpec prefix classifies, every `*_scheduler.tf` job stem ∈ `CLOUD_RUN_JOBS` + a vacuity-proof phantom-job test, 3 paper prefixes → PAPER, consolidator → BATCH, unknown lifecycle raises; QG-wired via repo `tests/unit/`)

## Phase 1 — deployment-api: unified deployment inventory at /repos grade (GCP first)

- [ ] [CODE] P0. `GET /api/deployments?umbrella=&cloud=&service=&asset_group=&status=` — unified inventory of VMs
      **and** Cloud Run executions, classified, with status/last-run/exit_code/heartbeat/captured-progress. Reuse
      `/api/vm-deployments` + add Cloud Run executions (GCP `run.googleapis.com` jobs list/executions). —
      **deployment-api**
- [ ] [CODE] P0. `GET /api/deployments/{umbrella}/summary` — per-umbrella rollup (counts by status, last failure, SLA
      breaches) — the /repos-overview equivalent. — **deployment-api**
- [ ] [CODE] P1. Cloud Run execution logs + events surfaced through the same `/api/vm/logs` / `/api/vm/events` shape (so
      the UI is uniform VM-vs-job). — **deployment-api**
- [ ] [CODE] P1. Wire the deployment lifecycle (STARTED/PROGRESS/COMPLETED/FAILED/EXIT_STATUS) + the umbrella into the
      `/api/alerts` ledger kind (a `deployment` kind alongside `data_pipeline`). — **deployment-api**

## Phase 2 — deployment-ui: the /repos-grade Deployments surface

- [ ] [UI] P0. A **Deployments** page at `/deployments` mirroring RepoCi grade: umbrella tabs (**Live / Batch /
      Paper**), each a matrix of VMs+Cloud-Run-jobs (status badge, last-run, exit_code, progress, cloud icon GCP/AWS),
      drill-down to per-target detail. Reuse `DeploymentHistory` + `VmEventsTimeline` + `StreamingLogsPanel`. `[UI]` +
      `pw:L2 ✓` + regression spec. — **deployment-ui**
- [ ] [UI] P0. Per-target detail (VM or Cloud Run job): live log tail + event timeline + exit_code + linked alerts + the
      durable `run.log` link — same grade as a repo's CI detail. — **deployment-ui**
- [ ] [UI] P1. Cloud filter (GCP/AWS) + status filter + asset_group filter, URL-param-backed (deep-linkable from an
      alert). — **deployment-ui**
- [ ] [UI] P1. Cross-link: an `/alerts` deployment/data_pipeline alert → its target's `/deployments` detail. —
      **deployment-ui**

## Phase 3 — Slack parity (deployments → channel at /repos grade)

- [ ] [CODE] P1. Deployment lifecycle events (STARTED/COMPLETED/FAILED/exit-nonzero) → Slack with the umbrella + cloud +
      deep-link to the `/deployments` detail (reuse the alerting router + the data-pipeline notifier pattern; a
      `#deployments` channel or fold into `#data-pipeline-alerts` per operator). — **alerting-service**
- [ ] [CODE] P2. Per-umbrella daily Slack digest (live up / batch completion / paper status) — reuse the daily-digest
      cron pattern. — **e2e-testing / deployment-service**

## Phase 4 — GCP completion (operator: GCP first, to completion + documented)

- [ ] [VERIFY] P0. Every GCP VM prefix + every GCP Cloud Run job appears in `/api/deployments`, classified, with live
      status — 0 unclassified, 0 untracked. Audit + close gaps. — **deployment-api, deployment-service**
- [ ] [CODE] P1. Backfill the durable-log streamer into the remaining bespoke GCP launchers (the open tail from
      `vm_launcher_durable_log_observability` — aave/amm/gcs-migration/sports/planning-vm) so every GCP target streams
      logs. — **deployment-service**

## Phase 5 — AWS parity (after GCP complete)

- [ ] [CODE] P1. AWS compute (EC2 backfill VMs + Batch Fargate) into `/api/deployments` under the same umbrellas;
      cloud=aws. Reuse the AWS launchers (`*-aws.sh`) + the AWS census. — **deployment-api, deployment-service**

## Phase 6 — Documentation (HARD: "all documented and done")

- [ ] [DOC] P1. New codex `codex/05-infrastructure/deployment-observability.md` — the umbrella model, the classification
      SSOT, the `/api/deployments` contract, the `/deployments` UI surface, the Slack parity, GCP-vs-AWS coverage. —
      **unified-trading-pm**
- [ ] [DOC] P2. One-liner + pointer in CLAUDE.md (new canonical contract: every compute unit is a classified deployment
      target). — **unified-trading-pm**

## Composed-with (tracked in `data_pipeline_hardening_self_monitoring_2026_06_22.md`)

- **(B) Alert enrichment (Tier 1)**: inline error trace + deep-links (data-status `/service/{svc}/data-status`, VM logs
  `/ops/vms/{vm}`, GCS run.log) in `#data-pipeline-alerts` — needs `deployment_ui_base_url` config in alerting-service +
  `details` keys at emit sites + `data_pipeline_slack.py` block formatting.
- **(C) Self-healing completion**: wire the DP\__ registry `escalation:` tiers to the existing Layer-0 recovery +
  `escalate-to-orchestrator`/AutoSpawn; add `data_pipeline_failure` to `WALL_TYPES`; actuators (consolidator/backfill-VM
  relaunch); schedule empty-reprobe+auto-flip; bucket-env parity preflight (DP-ENV-001); 429-aware key rotation +
  exhaustion alert; `RB-DATA-_` DR runbook.

## Success criteria

- Every GCP VM + Cloud Run job is classified to a live/batch/paper umbrella and visible in `/api/deployments` + the
  `/deployments` UI at /repos grade (status/history/logs/alerts/drill-down). 0 unclassified.
- Deployment failures (exit-nonzero / SLA breach) alert to Slack with umbrella + deep-link.
- AWS reaches the same parity after GCP.
- Documented in codex + CLAUDE.md.

## Progress Log (autonomous — append-only)

- **2026-06-22 created** (slot-0·human-planning, Opus 4.8) under `/autonomous`. Grounding: umbrellas derive from
  `lifecycle_class` (EPHEMERAL_BATCH/LONG_LIVED_LIVE/SCHEDULED_RECURRING/EPHEMERAL_EXPERIMENT in
  `vm_zombie_watchdog.VM_PREFIX_TO_BUCKET`) + paper launchers; ~20 Cloud Run jobs in `terraform/gcp/*_scheduler.tf` need
  classifying; AWS launchers (`*-aws.sh`) exist. Gold standard = `RepoCi.tsx`/`/api/repos`. Build order: Phase0 spine →
  Phase1 api → Phase2 ui → Phase3 slack → Phase4 GCP-complete → Phase5 AWS → Phase6 docs.
- **2026-06-22 Phase 0 COMPLETE** (deployment-service Step B). Shipped: `VmPrefixSpec.umbrella` override field
  (UAC@3c7dd51a) + `classify_deployment_target` resolver with `UnclassifiedDeploymentError` no-silent-default
  (deployment-service@360678e) + `CLOUD_RUN_JOBS` registry (49 jobs from all 24 `*_scheduler.tf`; BATCH for
  infra/consolidator/catalogue/expected-universe/monitors/digests/hygiene/rollups/t1-recon, PAPER for the 3
  paper-week/paper-engine jobs) + a 10-test guard (`tests/unit/test_cloud_run_job_registry_guard.py`) that asserts every
  VmPrefixSpec prefix classifies, every scheduler-tf job stem is registered (with a vacuity-proof phantom-job test),
  paper prefixes → PAPER, consolidator → BATCH, unknown lifecycle raises. `bash scripts/quality-gates.sh` exit 0
  (deployment-service 51s, UAC 38s). The [DESIGN] enums shipped earlier at UAC@34bb0f16. Phase 1 (deployment-api
  `/api/deployments`) is next — it imports `classify_deployment_target` + `CLOUD_RUN_JOBS` from these modules.
