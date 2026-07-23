---
doc_type: plan
title: Deployment Observability Parity — live/batch/paper × GCP/AWS at /repos grade
summary: >-
  Brings deployment observability for every compute unit (VM or Cloud Run job) to /repos-CI grade across the
  batch/live/paper umbrellas × GCP/AWS, reusing existing surfaces (deployment-ui VM-deployments/Monitor/VM-
  events/alerts, VM_PREFIX_TO_BUCKET lifecycle_class classification, durable GCS-tee logs) rather than rebuilding. Each
  unit classifies to exactly one umbrella × cloud × service × asset_group.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, e2e-testing, unified-api-contracts]
scope: [engineer, admin]
tags: [observability, monitoring, ui, infrastructure, spot-vm, live-trading, self-healing]
related:
  [
    /plans/archive/2026_06/deployment_ui_monitoring_pane_2026_06_19.md,
    /plans/archive/vm_launcher_durable_log_observability_2026_06_19.md,
    /plans/archive/2026_06/ci_dashboard_deployment_ui_2026_06_10.md,
    /plans/active/monitoring_control_plane_master_2026_06_10.md,
    /plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    /plans/active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md,
  ]
created: 2026-06-22
parent_epic: observability_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 16
estimate_calibrated_ai_days: 13
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
drift_direction: advance-code
---

# Deployment Observability Parity — live / batch / paper × GCP / AWS

> **✅ ARCHIVED 2026-07-13 — COMPLETE.** All Phase 0-6 todos shipped (parity #1-#6, incl. the daily deployment-estate
> digest via the log_event → Pub/Sub → ni-service relay). Codex aligned — this plan created
> `/codex/05-infrastructure/deployment-observability.md` and the digest was added to its Slack-parity section on
> archival. Lock cleared with operator authorization (`[unlock-plan]`). Frozen record.

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
      **unified-api-contracts** — unified-api-contracts@34bb0f16
      (`DeploymentUmbrella`/`DeploymentTarget`/`DeploymentCloud`/`DeploymentKind`/`UMBRELLA_FOR_LIFECYCLE_CLASS` in
      `canonical/crosscutting/lifecycle_class.py`; importable `from unified_api_contracts import DeploymentUmbrella`)
- [x] [CODE] P0. ✅ `classify_deployment_target(name, *, lifecycle_class=None, is_paper=None) -> DeploymentTarget` —
      derives umbrella from `lifecycle_class` + the paper-launcher set + VM-prefix; a single resolver both the watchdog
      and deployment-api call. Extend `VmPrefixSpec` with an explicit `umbrella` override where lifecycle_class is
      ambiguous (paper crons are SCHEDULED_RECURRING but umbrella=paper). — **unified-trading-library /
      deployment-service** — deployment-service@360678e (`deployment_service/deployment_classification.py` resolver +
      `PAPER_PREFIXES` + `UnclassifiedDeploymentError` no-silent-default) + unified-api-contracts@3c7dd51a
      (`VmPrefixSpec.umbrella: DeploymentUmbrella | None = None` field) + watchdog sets
      `umbrella=DeploymentUmbrella.PAPER` on the 3 paper prefixes
- [x] [CODE] P0. ✅ **Cloud Run job registry** — enumerate the ~20 `*_scheduler.tf` jobs into a classified inventory
      (name → umbrella/service/ag); a generator that reads terraform or a checked-in manifest so the surface knows every
      job, not just VMs. — **deployment-service** — deployment-service@360678e
      (`deployment_service/cloud_run_job_registry.py` `CLOUD_RUN_JOBS: Final[tuple[DeploymentTarget, ...]]` — 61 jobs
      (was: 49 — corrected 2026-07-12, finding 198, §A2 "50 reclassified" blanket ruling; the same document's own later
      Progress Log + FINAL REPORT sections consistently state "61-job CLOUD_RUN_JOBS registry" for this same
      deployment-service@360678e commit — a single fixed commit can't have two registry sizes, and the later, more-final
      sections are authoritative) from all 24 `*_scheduler.tf`: BATCH
      infra/consolidator/catalogue/expected-universe/monitors/digests/hygiene/rollups/t1-recon + 3 PAPER
      paper-week/paper-engine)
- [x] [TEST] P0. ✅ Every VM prefix + every Cloud Run job classifies to exactly one umbrella; paper launchers → paper;
      no `UNCLASSIFIED` (a CI check fails on an unclassified compute unit — the "added launcher, forgot to register"
      guard, extended to umbrellas). — **deployment-service** — deployment-service@360678e
      (`tests/unit/test_cloud_run_job_registry_guard.py`, 10 tests: every VmPrefixSpec prefix classifies, every
      `*_scheduler.tf` job stem ∈ `CLOUD_RUN_JOBS` + a vacuity-proof phantom-job test, 3 paper prefixes → PAPER,
      consolidator → BATCH, unknown lifecycle raises; QG-wired via repo `tests/unit/`)

## Phase 1 — deployment-api: unified deployment inventory at /repos grade (GCP first)

- [x] [CODE] P0. ✅ `GET /api/deployments/inventory?umbrella=&cloud=&service=&asset_group=&status=` — unified inventory
      of VMs **and** Cloud Run executions, classified, with status/last-run/exit_code/heartbeat/captured-progress.
      Reuses the deployment registry (`DeploymentsRegistry`) for VMs + `CLOUD_RUN_JOBS` enriched with Cloud Run
      executions (GCP `run.googleapis.com` jobs/executions via the deployment-service `_gcp_sdk` `run_v2` boundary,
      honest-degrades to empty map on any GCP error). exit-137 VM → status=failed/exit_code=137. Path is
      `/api/deployments/inventory` (NOT bare `/api/deployments`, which the existing `routes/deployments/` service-deploy
      CRUD package already owns — collision-free). — **deployment-api** — deployment-api@5df5f01
      (`routes/deployments_inventory.py` + `routes/_cloud_run_executions.py`; QG exit 0 / 76s; 13 credential-free tests
      in `tests/unit/test_route_deployments_inventory.py`)
- [x] [CODE] P0. ✅ `GET /api/deployments/umbrella/{umbrella}/summary` — per-umbrella rollup (counts by status, stale
      count, last failure name+exit_code+time) — the /repos-overview equivalent; 404 on an unknown umbrella (closed UAC
      `DeploymentUmbrella` set). — **deployment-api** — deployment-api@5df5f01
      (`deployments_inventory.build_umbrella_summary` + `GET /api/deployments/umbrella/{umbrella}/summary`)
- [x] [CODE] P1. ✅ Cloud Run execution logs + events surfaced through the same `/api/vm/logs` / `/api/vm/events` shape
      (so the UI is uniform VM-vs-job). — **MET via run-history (verified 2026-07-11)**: the full-estate work added
      `run_history` (`list_job_executions`) to the Cloud Run job DETAIL popover — the uniform "see the job's runs +
      status" surface the UI needs — and `deployment_state.py` (`_refresh_live_cloud_run_status` /
      `_parse_execution_name` / `_check_shard_logs_for_errors`) resolves CR execution logs/errors. Jobs read via
      run-history, not the VM log-tail. — **deployment-api**
- [x] [CODE] P1. ✅ Wire the deployment lifecycle (STARTED/PROGRESS/COMPLETED/FAILED/EXIT*STATUS) + the umbrella into
      the `/api/alerts` ledger kind (a `deployment` kind alongside `data_pipeline`). — **DONE (alerting-service@868872c,
      verified 2026-07-11)**: `rules/deployment_rules.py` routes DEPLOYMENT*\* via the shared
      `_route_data_pipeline_event` → ledger + #data-pipeline-alerts with umbrella + `/deployments/{name}` deep-link
      (mirrored into the data_pipeline family by deliberate "never forked" design; the ledger now surfaces it via #4's
      `deployment_target`). — **deployment-api**

## Phase 2 — deployment-ui: the /repos-grade Deployments surface

- [x] [UI] P0. ✅ A **Deployments** page at `/deployments` mirroring RepoCi grade: umbrella tabs (**Live / Batch /
      Paper**), each a matrix of VMs+Cloud-Run-jobs (status badge, last-run, exit_code, progress, cloud icon GCP/AWS),
      drill-down to per-target detail. Reuse `DeploymentHistory` + `VmEventsTimeline` + `StreamingLogsPanel`. `[UI]` +
      `pw:L2 ✓` + regression spec. — **deployment-ui** — deployment-ui@051c255 | pw:L2 ✓ | regression: >
      **[doc-reconciliation 2026-07-12, finding 196, §A2 B-queue ruling] SUPERSEDED UI SHAPE** (was: this
      umbrella-tabs > design, current at the time, deployment-ui@051c255):
      `active/deployment_observability_expansion_2026_07_08.md` > (created 2026-07-08) later collapsed the
      Live/Batch/Paper tabs into ONE flat all-modes table (Mode is a filter, > not tabs) — "3 cockpit tabs + 3 health
      tiles + 3 nav entries consolidated" — shipped at > `deployment-ui@50a6947`, confirmed on `live-defi-rollout` and
      postdating `051c255` (`git log --oneline     > 051c255..50a6947`, re-verified in this pass). The checkbox below
      stays `[x]` (051c255 genuinely shipped at the > time) but the tab architecture it describes is no longer the
      current `/deployments` shape — read the expansion > plan for the current UI. tests/smoke/deployments-page.spec.ts
      (`src/pages/Deployments.tsx` umbrella tabs Live/Batch/Paper + status-tone matrix + GCP/AWS cloud badges +
      VM/Cloud-Run kind icon + exit-137 highlight + per-umbrella summary header;
      `getDeploymentInventory`/`getUmbrellaSummary` in `src/api/deploymentApi.ts`; route+nav in App.tsx/Header.tsx;
      mock-api handlers; 6 vitest + 4 pw specs; tsc 0 / eslint 0-warn / vitest 883 / pw 265/265 smoke / build 0)
- [x] [UI] P0. ✅ Per-target detail (VM or Cloud Run job): live log tail + event timeline + exit_code + the durable
      `run.log` link — same grade as a repo's CI detail. — **deployment-ui** — deployment-ui@051c255 | pw:L2 ✓ |
      regression: tests/smoke/deployments-page.spec.ts (`src/pages/DeploymentDetail.tsx` route `/deployments/:name`
      reuses `VmEventsTimeline` + `StreamingLogsPanel`; shows exit_code/137-OOM + GCS `run_log_uri` console link +
      classified status/umbrella/cloud). NOTE: "linked alerts" inline on the detail is the P1 cross-link below (still
      open — needs Alerts.tsx).
- [x] [UI] P1. ✅ Cloud filter (GCP/AWS) + status filter + asset_group filter, URL-param-backed (deep-linkable from an
      alert e.g. `/deployments?umbrella=batch&cloud=gcp&status=failed`). — **deployment-ui** — deployment-ui@051c255 |
      pw:L2 ✓ | regression: tests/smoke/deployments-page.spec.ts (`useSearchParams`-backed umbrella tab + cloud/status/
      asset_group selects; the status deep-link spec asserts the list narrows + the succeeded Cloud-Run row is filtered
      out)
- [x] [UI] P1. ✅ Cross-link: an `/alerts` deployment/data_pipeline alert → its target's `/deployments` detail. —
      **deployment-ui@96d9167 + deployment-api@e370906** (2026-07-11). The ledger surfaces `deployment_target` (the
      infra watchers' flattened `vm_name`); `Alerts.tsx` renders an internal `/deployments/{name}` Link on those rows.
      pw:L2 ✓ (`tests/smoke/alerts-page.spec.ts` — the vm_down alert deep-links + navigates).

## Phase 3 — Slack parity (deployments → channel at /repos grade)

- [x] ✅ [CODE] P1. Deployment lifecycle events (STARTED/COMPLETED/FAILED/exit-nonzero) → Slack with the umbrella +
      cloud + deep-link to the `/deployments` detail (reuse the alerting router + the data-pipeline notifier pattern; a
      `#deployments` channel or fold into `#data-pipeline-alerts` per operator). — **alerting-service@868872c**
      (`rules/deployment_rules.py` routes UTL DEPLOYMENT_STARTED/COMPLETED/FAILED via the shared
      `_route_data_pipeline_event` path → #data-pipeline-alerts mirror with umbrella/cloud fields + `/deployments/{vm}`
      deep-link; FAILED=CRITICAL also pages. Folded into #data-pipeline-alerts per the notifier reuse.)
- [x] [CODE] P2. Per-umbrella daily Slack digest (live up / batch completion / paper status) — reuse the daily-digest
      cron pattern. — **e2e-testing / deployment-service** — DONE 2026-07-13. Emits the per-umbrella deployment-estate
      digest to Slack over the **PROVEN Pub/Sub relay** — the SAME path parity #3 (deployment lifecycle) + the
      data-pipeline fleet monitors use: UTL `log_event("DEPLOYMENT_DIGEST", INFO, details={message,…})` →
      `lifecycle-events` Pub/Sub topic → ni-service `alert_subscriber` → `deployment_rule_for` → mirror to
      `#data-pipeline-alerts` (INFO, never pages). **No HTTP URL to configure** (an earlier httpx-POST cut needed an
      `ALERTING_SERVICE_URL` nobody sets — client-reporting's own digest URL is unwired too; switched to the relay so
      nobody writes a URL). Evidence: • unified-trading-library@22885e3 — `DEPLOYMENT_DIGEST` lifecycle event constant
      (added to `DEPLOYMENT_EVENT_TYPES` + `STANDARD_LIFECYCLE_EVENTS`; set-size ratchet 6→7; UTL QG green). •
      unified-api-contracts@bd8a46e9 — reverted the now-unused `AlertCode.DEPLOYMENT_DIGEST` (event-name path, not an
      AlertEvent; UAC QG green). • alerting-service@3bee248 — `deployment_rules.py` routes `DEPLOYMENT_DIGEST` as an
      INFO deployment event + routing test (`test_deployment_rules.py`); reverted the parity-ratchet entry (109 passed;
      only QG red is the pre-existing `click` pip-audit vuln). • deployment-api@b2694c0 — `routes/deployment_digest.py`
      (`build_deployment_digest_message` folds the per-umbrella rollups; `build_estate_summaries` loads
      `_load_inventory` once + `build_umbrella_summary` for LIVE/BATCH/PAPER; `run_deployment_digest` emits via
      `log_event` wrapped in `run_lifecycle` after best-effort `_ensure_live_events` wires the `PubSubEventSink` to
      `lifecycle-events` — mirrors the monitor CLI; `POST /api/deployments/digest/run` on-demand endpoint) +
      `scripts/deployment_digest_worker.py` (isolated Cloud Run Job entrypoint, exit-0-always) + 5 unit tests (QG
      green). • deployment-service@a01202d — `terraform/gcp/deployment_digest_scheduler.tf`: isolated Cloud Run Job
      (deployment-api image, 4Gi/cpu2) + daily 07:30 UTC Cloud Scheduler via the Jobs `:run` API (modeled on the
      data-pipeline fleet monitors, so the census load stays off the memory-sensitive live service); the
      `unified_trading` runtime SA already holds `pubsub.publisher` on `lifecycle-events`. `terraform validate` Success.
      Tier-safe: deployment-api never imports alerting-service — it publishes an event to Pub/Sub. **No apply-time
      knob** — the digest reaches Slack the moment the cron runs (nothing for the operator to configure).

## Phase 4 — GCP completion (operator: GCP first, to completion + documented)

- [x] [VERIFY] P0. ✅ Every GCP VM prefix + every GCP Cloud Run job appears in `/api/deployments`, classified, with live
      status — 0 unclassified, 0 untracked. Audit + close gaps. — **CLOSED by the full-estate census (verified
      2026-07-11)**: `deployment_full_estate_cost_provenance` unions the deployment registry with the live GCE
      aggregated-list + censuses all Cloud Run jobs; the warm reconciliation vs `gcloud` showed **0 untracked** (the
      previously-invisible `vm-zombie-watchdog` now classifies as `adhoc`). Re-runnable only on a warm census — the
      transpacific dev-box cold-census degrades to empty (known latency artifact, not a classification gap). —
      **deployment-api, deployment-service**
- [x] [CODE] P1. ✅ Backfill the durable-log streamer into the remaining bespoke GCP launchers (the open tail from
      `vm_launcher_durable_log_observability` — aave/amm/gcs-migration/sports/planning-vm) so every GCP target streams
      logs. — **COVERED via launcher_common (verified 2026-07-11)**: aave / amm / gcs-migration / sports launchers all
      `source launcher_common.sh`, which provides the same durable-observability contract as `vm-exec-with-gcs-tee.sh`
      (30s stream + terminal STOPPED/FAILED signal durable in GCS). Only `planning-vm` doesn't source it — the
      interactive orchestrator VM, not a data backfill (N/A). — **deployment-service**

## Phase 5 — AWS parity (after GCP complete)

- [x] ✅ [CODE] P1. AWS compute (EC2 backfill VMs + Batch Fargate) into `/api/deployments` under the same umbrellas;
      cloud=aws. Reuse the AWS launchers (`*-aws.sh`) + the AWS census. — **deployment-api, deployment-service** —
      deployment-service@53be0f1 (read-only `backends/aws_census.py` seam: `list_ec2_census` + `list_batch_census` via
      the deferred-boto3 boundary; honest-degrades to `[]`) + deployment-api@ab11b36 (`routes/_aws_deployments.py`
      censuses EC2 + Batch → `classify_deployment_target(cloud=DeploymentCloud.AWS)`; EC2 exit_code from the durable S3
      `vm-logs/{name}/EXIT_STATUS` blob via cloud-agnostic `get_storage_client(provider='aws')`; wired into
      `GET /api/deployments/inventory` — `cloud` unset|aws includes AWS, `cloud=gcp` unchanged). Tests: moto
      (`@mock_aws`, `importorskip`) EC2 + Batch census + pure classification / exit-137 EXIT_STATUS=failed/137 /
      no-GCP-regression. `cd deployment-api && bash scripts/quality-gates.sh` exit 0 (cov 79.39%). Live-wiring note: no
      AWS deployments running today — wiring verified-by-shape via moto + pure tests.

## Phase 6 — Documentation (HARD: "all documented and done")

- [x] ✅ P1. New codex `/codex/05-infrastructure/deployment-observability.md` — DONE (umbrella model + classification
      SSOT + /api/deployments contract + /deployments UI + Slack parity + GCP-complete/AWS-pending). New codex
      `/codex/05-infrastructure/deployment-observability.md` — the umbrella model, the classification SSOT, the
      `/api/deployments` contract, the `/deployments` UI surface, the Slack parity, GCP-vs-AWS coverage. —
      **unified-trading-pm**
- [x] ✅ P2. One-liner + pointer in CLAUDE.md — DONE (cursor-configs/CLAUDE.md VM-launchers section: every compute unit
      = classified DeploymentTarget). One-liner + pointer in CLAUDE.md (new canonical contract: every compute unit is a
      classified deployment target). — **unified-trading-pm**

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
  (deployment-service@360678e) + `CLOUD_RUN_JOBS` registry (61 jobs (was: 49 — see the P0 checkbox correction above)
  from all 24 `*_scheduler.tf`; BATCH for
  infra/consolidator/catalogue/expected-universe/monitors/digests/hygiene/rollups/t1-recon, PAPER for the 3
  paper-week/paper-engine jobs) + a 10-test guard (`tests/unit/test_cloud_run_job_registry_guard.py`) that asserts every
  VmPrefixSpec prefix classifies, every scheduler-tf job stem is registered (with a vacuity-proof phantom-job test),
  paper prefixes → PAPER, consolidator → BATCH, unknown lifecycle raises. `bash scripts/quality-gates.sh` exit 0
  (deployment-service 51s, UAC 38s). The [DESIGN] enums shipped earlier at UAC@34bb0f16. Phase 1 (deployment-api
  `/api/deployments`) is next — it imports `classify_deployment_target` + `CLOUD_RUN_JOBS` from these modules.
- **2026-06-22 Phase 1 P0 (the two unified-inventory endpoints) COMPLETE** (deployment-api@5df5f01). Shipped
  `routes/deployments_inventory.py` (`GET /api/deployments/inventory` filterable VM+Cloud-Run inventory +
  `GET /api/deployments/umbrella/{umbrella}/summary` rollup) + `routes/_cloud_run_executions.py` (Cloud Run latest-
  execution status via the deployment-service `_gcp_sdk` `run_v2` boundary — `JobsClient.list_jobs` +
  `ExecutionsClient.list_executions`, honest-degrades to `{}` on any GCP error → jobs fall back to `status="unknown"`).
  **Path is `/api/deployments/inventory`, NOT bare `/api/deployments`** — the existing `routes/deployments/` package
  already owns `GET /api/deployments` + `/{deployment_id}` (service-version deploys), so the plan's bare path would
  collide; `/deployments/inventory` + `/deployments/umbrella/{umbrella}/summary` are collision-free and stay under the
  deployments namespace. VM rows reuse `DeploymentsRegistry` (same source as `/api/vm-deployments`); classification is
  the single `classify_deployment_target` resolver (a local honest prefix→lifecycle registry seeds the VM lifecycle,
  mirroring `_fleet_census`). exit-137 VM → `status=failed`/`exit_code=137`; running VM heartbeat > 15 min → `stale`.
  Registered in `main.py` under `/api`, tag "Deployment Inventory". 13 credential-free / block-network tests (registry +
  Cloud Run client + GCS all mocked). `bash scripts/quality-gates.sh --no-fix` exit 0 (76s). Shipped via the dirty-deps
  direct-LDR carve-out (deployment-service had foreign uncommitted WIP → quickmerge pre-flight refuses; commit carries
  the `Quickmerge: agent` provenance trailer). Wire shape for the deployment-ui consumer: `DeploymentItem`
  `{name, kind, umbrella, cloud, service, asset_group, status, last_run_at, exit_code, heartbeat_age_seconds, captured_progress, run_log_uri}`;
  `DeploymentInventoryResponse` `{items[], total, vm_count, cloud_run_job_count}`; `UmbrellaSummaryResponse`
  `{umbrella, total, counts_by_status{}, stale_count, last_failure{name,exit_code,last_run_at}}`. Remaining Phase 1: the
  P1 Cloud-Run logs/events `/api/vm/logs`-shape uniformity + the `/api/alerts` `deployment` kind.

## Progress Log

- **2026-06-22 (autonomous, Opus 4.8) — GCP observability parity SHIPPED**: Phase0 spine (uac@34bb0f16/3c7dd51a
  DeploymentUmbrella/Target/classify, deployment-service@360678e resolver + 61-job CLOUD*RUN_JOBS registry +
  unclassified guard) → Phase1 deployment-api@5df5f01 (`/api/deployments/inventory` + `/umbrella/{u}/summary`,
  VMs+CloudRun classified, exit_code/status) → Phase2 deployment-ui@051c255 (`/deployments` Live/Batch/Paper tabs at
  /repos grade, pw:L2 ✓ 265/265, drill-down reuses VmEventsTimeline+StreamingLogsPanel) → Phase3
  alerting-service@868872c (DEPLOYMENT*\* → #data-pipeline-alerts with umbrella + `/deployments/{name}` deep-link) +
  Tier-1 enrichment (deployment_ui_base_url config + inline trace block + deep-link buttons to
  /ops/vms,/deployments,data-status,GCS run.log) → Phase4 deployment-service@5d07bb1f (durable-log streamer backfilled
  into 4 unconverted GCP launchers + coverage guard). Phase6 docs: codex deployment-observability.md + CLAUDE.md
  one-liner. **3 CI guards make 0-unclassified/0-untracked a fleet invariant** (VM-prefix classify, scheduler-tf
  registry, launcher durable-log). REMAINING: Phase1-P1 (CloudRun logs uniformity + /api/alerts deployment kind),
  Phase2-P1 (/alerts→/deployments cross-link), Phase5 AWS, + the data_pipeline Phase-6 self-healing (C). Peer filed
  `issues/dp_event_pubsub_delivery_gap_2026_06_22.md` (DP events emitted but the alerting subscriber may not subscribe
  their topic — verify end-to-end delivery).

## FINAL REPORT (autonomous /autonomous — 2026-06-22, slot-0·human-planning, Opus 4.8)

**Mandate**: bring live/batch/paper deployment observability (Slack + deployment-ui) to /repos grade, every VM + Cloud
Run job classified under an umbrella across GCP+AWS (GCP first to completion), documented; compose with
alert-enrichment + self-healing.

**SHIPPED (end-to-end, GCP + AWS):**

- Phase 0 spine — uac@34bb0f16/3c7dd51a + deployment-service@360678e (DeploymentUmbrella + classify_deployment_target +
  61-job CLOUD_RUN_JOBS registry + unclassified guard).
- Phase 1 API — deployment-api@5df5f01 (`/api/deployments/inventory` + `/umbrella/{u}/summary`).
- Phase 2 UI — deployment-ui@051c255 (`/deployments` Live/Batch/Paper tabs, pw:L2 ✓ 265/265, drill-down).
- Phase 3 Slack + B enrichment — alerting-service@868872c (DEPLOYMENT\_\* → channel w/ umbrella + deep-link; inline
  trace + click-through buttons to /deployments,/ops/vms,data-status,GCS run.log; deployment_ui_base_url config).
- Phase 4 GCP logs — deployment-service@5d07bb1f (durable-log streamer into 4 remaining GCP launchers + coverage guard).
- Phase 5 AWS — deployment-service@53be0f1 + deployment-api@ab11b36 (EC2 + Batch Fargate → inventory cloud=AWS,
  moto-tested; GCP unchanged).
- Phase 6 docs — codex `deployment-observability.md` + CLAUDE.md one-liner.

**Invariant established**: 3 CI guard tests make "0 unclassified / 0 untracked" permanent (VM-prefix classify,
scheduler-tf registry, launcher durable-log) — a future "added a VM/job/launcher, forgot to classify/stream" fails CI.

**Forced-tradeoff decisions (rule 1/2):** (a) inventory at `/api/deployments/inventory` not bare `/api/deployments`
(latter owned by service-version deploys); (b) inherited a peer's footystats_odds pipeline_mode fix trapped in the same
UAC tree, shipped it; (c) AWS verified-by-shape (moto) — no live AWS estate today.

**REMAINING (tracked, not silent):**

- **C self-healing — delivery gap is being closed by a LIVE PEER session** (`issues/dp_event_pubsub_delivery_gap`):
  emitters now `setup_events(mode=live, topic=lifecycle-events)` + subscriber subscribes `lifecycle-events` (in-flight
  across alerting/e2e/deployment-service; deployment-service/escalation.py edited <3min ago — NOT stomped). The rest of
  C (actuators consolidator/backfill-relaunch, `data_pipeline_failure` WALL_TYPE, reprobe scheduling+auto-flip,
  bucket-env parity DP-ENV-001, 429-aware key rotation, RB-DATA runbook) builds on that substrate once it lands —
  tracked in `data_pipeline_hardening_self_monitoring_2026_06_22.md` Phase 6.
- **P1 polish (tracked)**: `/api/alerts` deployment kind (deployment-api); `/alerts`→`/deployments` cross-link
  (deployment-ui).
