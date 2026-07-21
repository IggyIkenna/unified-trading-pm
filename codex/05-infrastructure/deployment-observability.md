---
doc_type: codex-ssot
title: Deployment Observability — live/batch/paper × GCP/AWS at /repos grade (SSOT)
summary:
  SSOT for classifying every compute unit (VM or Cloud Run job) into a DeploymentUmbrella (LIVE / BATCH / PAPER /
  EXPERIMENT) × cloud × kind and surfacing it at /repos grade in deployment-ui /deployments + /cockpit + Slack —
  classify_deployment_target resolver, the CLOUD_RUN_JOBS registry, CI guard tests, and the 3-layer out-of-band deadman
  monitoring.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [agent-orchestrator, alerting-service, deployment-api, deployment-service, deployment-ui, unified-trading-system-ui]
scope: [engineer, admin]
tags: [observability, monitoring, deployment, self-healing, ui, cost, billing]
related:
  [
    codex/05-infrastructure/data-pipeline-alerts.md,
    codex/05-infrastructure/deployment-ui-architecture.md,
    codex/05-infrastructure/deployment-clusters-live-vs-batch.md,
    codex/05-infrastructure/live-deployment-monitoring.md,
    plans/active/deployment_ui_cost_per_day_accuracy_2026_07_20.md,
  ]
created: 2026-06-22
authoritative_for:
  [
    DeploymentUmbrella classification (live/batch/paper/experiment) + deployment-target inventory API + health/cockpit
    rollup,
  ]
referenced_by:
  [
    codex/02-data/instruments-foundation-and-catalogue-completeness.md,
    codex/04-architecture/cross-venue-prediction-arb-detection.md,
    codex/05-infrastructure/data-pipeline-alerts.md,
    codex/05-infrastructure/spot-vms-for-backfill.md,
    plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md,
    plans/active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md,
    plans/active/issues/terminated_vm_disk_orphan_no_reaper_2026_06_30.md,
  ]
owner:
last_reviewed: 2026-07-21
code_refs:
  [
    deployment-api/deployment_api/services/cost_observability/service.py,
    deployment-api/deployment_api/services/cost_observability/models.py,
    deployment-api/deployment_api/routes/deployments_inventory.py,
    deployment-ui/src/pages/Deployments.tsx,
  ]
---

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

## Cost/day attribution contract (per-target cost cell)

The Deployments table's Cost/day column (`CostCell`, `deployment-ui/src/pages/Deployments.tsx`) reads real GCP BigQuery
resource-level billing export + AWS Athena CUR data via `deployment-api`'s
`CostObservabilityService.per_resource_daily()` (`deployment_api/services/cost_observability/service.py`) — **no rate
card, no fabrication**. It attaches three USD figures per deployment target by joining on billing
`resource_id == item.name`. Fixed 2026-07-21 (`plans/active/deployment_ui_cost_per_day_accuracy_2026_07_20.md`) after
all three figures were individually correct in source but wrong in aggregation.

**The three definitions** (`ResourceDailyCost`, `cost_observability/models.py`) — net = cost + credit, USD (GCP already
converted from GBP at query time):

| Field               | Definition                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `actual_usd`        | Net cost on the most recent **COMPLETE** billing day (a day strictly before UTC-today); falls back to the latest (still-accruing) day only if no complete day exists yet.                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `avg_7d_usd`        | Total net over the trailing window ÷ **the count of days the resource actually has billing rows** (`len(day_net)`) — NOT the fixed window length. A 1-day-old resource averages over its 1 day, so it reads `$4.4 · 7d ~$4.4`, not `$4.4 · 7d $0.63` (the reported symptom — divided by the fixed `days=7` even when the resource only had 1 billing day).                                                                                                                                                                                                                                                         |
| `projected_24h_usd` | The same most-recent COMPLETE day's net (so `actual_usd == projected_24h_usd` is expected + correct for any resource with a complete day); falls back to **partial-day normalisation** (`day_cost / hours_billed × 24`) only when no complete day exists — `hours_billed` = wall-clock hours elapsed since UTC midnight (floored at 1h to avoid a runaway multiplier in the first minutes of a new UTC day). Not a new hourly billing query — the billing snapshot stays daily-grained. Previously `max(daily)` (peak observed day), which silently overstated any resource whose peak day wasn't its most recent. |
| `cost_basis`        | `"complete"` when a complete billing day exists (both figures above derive from it); `"partial"` when no complete day exists yet and both fall back to the latest, still-accruing day. Carried onto `DeploymentItem.cost_basis: str \| None` (`None` = no billing row yet, honest absence) — never fabricated.                                                                                                                                                                                                                                                                                                     |

**Active-days average, not fixed-window** is the core fix: `per_resource_daily(days=N)` GROUP BYs `(resource_id, day)`
over the window, then divides each resource's sum by however many distinct days THAT resource has rows for, not `N`. A
resource billed on only 1 of the last 7 days no longer reads as if it cost 1/7th of what it actually cost.

**GCP-name / AWS-ARN join** (`_attach_costs`, `deployment_api/routes/deployments_inventory.py`): a GCP VM's billing
`resource.name` already equals its instance name (== `item.name`), so GCP rows join directly. AWS Athena CUR's
`line_item_resource_id` is an ARN or bare instance-id (`arn:aws:ec2:<region>:<acct>:instance/i-...`), which won't match
a friendly name — `_load_aws_items` builds `{instance_id: Name tag}` from the EC2 census
(`deployment-service/backends/aws_census.py` `AwsInstanceCensus` / `list_ec2_census()`) and threads it into
`_attach_costs` as `aws_instance_id_by_name`. `_aws_instance_id_from_resource_id` parses the trailing `instance/i-…`
segment off the ARN (or accepts a bare `i-…`), resolves it through the map, and re-keys the cost record under the
friendly name before the by-name join runs. No mapping found (unmapped instance, non-EC2 AWS resource) → the item's cost
fields stay `None` — **never a fabricated `$0`**.

**Cost enrichment is best-effort and never breaks the census**: `_attach_costs` wraps the `per_resource_daily()` call in
a try/except — a billing-source failure (Athena/BigQuery down) logs a warning and leaves every item's cost fields
`None`; the inventory itself still returns.

**UI colour convention (no text label)**: `CostCell` renders `cost_actual_usd` in `text-amber-400` when
`item.cost_basis === "partial"`, else the normal `text-[var(--color-text-primary)]` tone — colour is the ONLY signal
distinguishing a still-accruing partial-day figure from a settled complete-day one (operator decision 2026-07-20;
refines an earlier tooltip proposal). The same `text-amber-400` convention is reused elsewhere on the page for
"estimated, not billing-derived" figures (e.g. the unmanaged-VM cost fallback) — one consistent amber = "approximate /
provisional" signal across the table, not cost-specific. pw:L2 regression: `tests/smoke/deployments-cost-cell.spec.ts`
(complete-day renders the normal tone; partial-day renders amber with no added text).

## Slack parity + alert enrichment

- **Deployment lifecycle** (`DEPLOYMENT_STARTED/COMPLETED/FAILED`, UTL events) routes via
  `alerting-service/rules/deployment_rules.py` → `#data-pipeline-alerts` with the **umbrella + cloud + a
  `/deployments/{name}` deep-link** (FAILED=CRITICAL pages; STARTED/COMPLETED=INFO).
- **Daily estate digest** (`DEPLOYMENT_DIGEST`, UTL event, INFO): a once-a-day per-umbrella rollup (LIVE up / BATCH
  completions+failures / PAPER status + the last-failure per umbrella) so operators get one morning glance instead of
  watching the lifecycle stream. Built by deployment-api `routes/deployment_digest.py` off `_load_inventory` +
  `build_umbrella_summary` (loaded once), emitted via UTL `log_event("DEPLOYMENT_DIGEST", INFO, details={message,…})` →
  the `lifecycle-events` Pub/Sub topic → the ni-service subscriber → `deployment_rule_for` → `#data-pipeline-alerts`
  (channel-only, never pages; the digest text rides in `details["message"]`). Cron: an isolated daily Cloud Run Job
  (`scripts/deployment_digest_worker.py`) via `deployment-service/terraform/gcp/deployment_digest_scheduler.tf`, off the
  live service's request path. **Same relay as the lifecycle events above — no HTTP URL to configure.** On-demand /
  dry-run preview: `POST /api/deployments/digest/run`.
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

## AWS backend activation (deployment-registry DynamoDB)

The deployment-registry `DeploymentRegistryStore` (UTL `cloud_interface`) has a DynamoDB backend implementing the SAME
Protocol as the GCP Firestore backend — provisioned now (Phase 4 of
`plans/archive/2026_07/deployment_registry_firestore_p4_dynamodb_2026_07_14.md`) but **inactive**: the store factory
selects the backend from the active cloud (mirrors `resolve_bucket_name`'s GCS/S3 selection) and defaults to Firestore
on GCP.

- **Table**: `unified-trading-{environment}-deployments` (terraform
  `deployment-service/terraform/aws/deployment_registry_dynamodb.tf`) — partition key `deployment_id`, GSI
  `status-index` on `status` (the DynamoDB analogue of the Firestore `query_by_status` query). `PAY_PER_REQUEST` billing
  by default (`deployment_registry_dynamodb_billing_mode` var toggles to the 25-WCU/25-RCU free-tier `PROVISIONED`
  mode). Server-side encryption enabled.
- **Activation is one line**: flip the active-cloud selector to AWS — the store factory then instantiates
  `DynamoDbDeploymentRegistryStore` instead of `FirestoreDeploymentRegistryStore`; no caller changes. Until that flip,
  the table sits provisioned + empty (no writes, negligible cost).

## The cockpit + health rollup + per-deployment freshness (2026-06-24)

The unified **`/cockpit`** is the deployment-ui DEFAULT page (`src/pages/Cockpit.tsx`): one place to answer "is
everything OK right now?" across live/batch/paper deployments + fleet/consolidators/CI/alerts/billing, plus
deploy/launch and stream logs without leaving. 12 tabs (Health · Deploy · Live · Batch · Paper · Fleet · Consolidators ·
CI · Alerts&Logs · Launch · Chaos · Safety); top bar is pure-utility (env badge · LIVE/MOCK DATA · GCP/AWS · API status
· version). The **Health TAB is the landing** — a tile grid wired to the rollup endpoints (no placeholders); each
per-domain tab folds the existing page COMPONENT in-place (never a rebuild) + reads the real inventory.

**Health rollup endpoints (deployment-api `routes/health_overview.py` + `health_consolidator.py`):**

- **`GET /api/health/overview`** →
  `{generated_at, overall: ok|degraded|critical, tiles:[{id, label, status, value, detail_href}]}` — aggregates the
  EXISTING signals into one envelope (fleet vm-census, consolidator staleness, coverage, open alerts by class, GH
  rate-limit, today's cost). Pure reuse — no new data sources. The cockpit Health tiles overlay this rollup + the 3
  umbrella summaries (live/batch/paper) + repo-ci overview (ci) → all 10 landing tiles show real data.
- **`GET /api/health/consolidator`** →
  `{overall, asset_groups:[{asset_group, bucket, status, index_age_seconds, staleness_budget_seconds, per_vm_shard_fallback_active, last_successful_run_at, detail}]}`
  — per-AG manifest-index freshness (the consolidated `_index` heartbeat age + whether the per-VM shard recovery-merge
  fallback is active). Honest per-AG degrade to `unknown` on a read failure, never a 5xx. **Bucket kind is per-AG**:
  cefi/defi/tradfi/sports use `market-data`; prediction uses the dedicated `market-data-tick-prediction` key (a guard
  test keeps the map complete so an unmapped AG fails at test-time, never 5xx in prod).

**Per-deployment data freshness ≠ health (a liveness ping) — manifest-derived per OWNED shard (Phase 4.5):** the binding
_deployment → the shard-set it owns_ is the deployment-service resolver
`deployment_cluster_registry.responsibility_for_deployment(target) -> ShardResponsibility` (a PURE derivation off the
classified `service`+`asset_group`+`umbrella` — never a hand-dict; raises rather than silently `NONE` for a data
service). `ShardResponsibility` (UAC `canonical/crosscutting/lifecycle_class`) has
`kind ∈ {asset_group_capture, manifest_consolidation, strategy_shard, none}`. **`GET /api/deployments/{id}/freshness`**
(`routes/deployment_freshness.py`) classifies the deployment → resolves its responsibility → for a data obligation reads
the owned asset_group's **consolidated availability-index posture** (REUSES `consolidator_posture` — the index heartbeat
IS the manifest-derived freshness for the AG's owned shards; no new manifest walk) →
`{responsibility, asset_group, mode, freshness_status: fresh|stale|liveness_only|unknown, index_age_seconds, staleness_budget_seconds, per_vm_shard_fallback_active, oldest_available_at, detail}`.
**`NONE` (gateway/control-plane) → `liveness_only`** — never a false "fresh". The availability **manifest** stays the
per-shard freshness SSOT; this endpoint attributes it PER deployment instead of guessing from the in-memory health-ping
callback. (Known gap: the resolver keys off canonical SERVICE names, so VM rows whose `_derive_service` stem is a
launcher family — `strategy-live-*`, `cefi-binance-spot-*` — currently resolve `liveness_only` until the resolver maps
launcher families; tracked in the cockpit plan.)

**Inventory perf — the cockpit Live/Batch/Paper tabs are fast (2026-06-24):** `GET /api/deployments/inventory` read the
~hundreds of per-VM registry JSONs SEQUENTIALLY over a transpacific GCS hop (291-VM census + 7-day archive) → >100s,
timing out the tabs. Fixed (`routes/deployments_inventory.py`) with (1) **parallel per-object GCS reads**
(`_download_entries_parallel`, 32-worker ThreadPool — the GCS-object-ops pattern; GCS REST releases the GIL) + the 4
coarse calls run concurrently, and (2) a **stale-while-revalidate short-TTL cache** (45s): a fresh snapshot serves
instantly, a stale one serves instantly + kicks a single background refresh, a cold burst collapses to ONE census under
a lock. Measured: cold ~10s (one-time) → warm <0.2s.

**Cross-cloud reconciliation — "every RUNNING instance accounted for" (Phase 4):** `GET /api/fleet/reconciliation`
(`routes/fleet_reconciliation.py`) reconciles the live RUNNING set (the GCE aggregated-list) against the REGISTERED set
(the parallel active-registry read `active_registry_vm_names` plus `CLOUD_RUN_JOBS`) plus a control-plane prefix
allowlist — surfacing **UNKNOWN** (running but unregistered → classify-or-kill, its own alert class) and
**EXPECTED-MISSING** (registered/active but not running) as distinct `classify_vm_target`-classified rows. Rows are
capped at 200/cloud for a responsive payload while `unknown_count`/`expected_missing_count` carry the EXACT totals. AWS
rides the same shape and degrades to empty without creds (never blocks GCP). The cockpit **Fleet tab** wires it
(accounted / unknown / expected-missing cards). NOTE: a large `expected_missing` is dominated by un-reaped STALE active
entries (registry-hygiene debt — the zombie-watchdog's reap job), a real signal the reconciliation surfaces. The
reconciliation reads the full active registry (~2.4k entries) per call → ~13s cold; a stale-while-revalidate cache (the
inventory pattern) is a tracked perf follow-up.

**Monitoring-registration enforcement — declare-or-fail-QG (Phase 4):** every long-lived deployable service MUST
self-register in `MONITORED_SERVICES` (`deployment_service/monitored_services.py`) — each entry carries its resolved
`ShardResponsibility` (data-plane producers own their asset_group capture shards; gateways/control-plane are
`NONE`/liveness-only). The **guard test**
`tests/unit/test_monitored_services_registry_guard.py::test_every_long_lived_service_repo_is_registered` asserts every
`service`/`api-service`/`api` repo in `workspace-manifest.json` has a `MONITORED_SERVICES` entry — a NEW unregistered
deployable service **fails deployment-service's `quality-gates-v2`** ("fails QG"), the parallel-to-
`test_cloud_run_job_registry_guard.py` enforcement. (A per-repo `base-service.sh` STEP is deliberately NOT added — a
per-repo bash check cannot read a CENTRALISED Python registry, so the centralised guard is the SSOT; `batch-service`
repos register as Cloud Run JOBS, not here.)

## Out-of-band liveness + data-pipeline self-monitoring (2026-06-24)

Three layers, each independent of the one it watches (so a dead watcher is never invisible):

- **Layer 1 — the dp-\* fleet monitors** (`deployment_service.data_pipeline_monitors`, 3 Cloud Run jobs on
  `deployment-api:latest` via `data_pipeline_fleet_monitor_scheduler.tf`): `exit-code` (`*/5`) + `heartbeat` (`*/5`) +
  `meta` (`*/15`). Each reads durable GCS artifacts and emits `DP_*` → #data-pipeline-alerts. **8Gi/cpu2** (they read
  the whole RUNNING fleet's per-VM shards — OOM at 2/4Gi → stale sentinel → false deadman page). Each writes
  `vm-census/{mode}-last-run.json` at end-of-sweep.
  - **Heartbeat liveness is SIDECAR-authoritative** (REVISED 2026-06-24, supersedes the 2026-06-22 run.log-primary
    BUG2): `heartbeat_age_min` = the fresh infra **sidecar blob** (`vm-heartbeat/{vm}.txt`, 60s direct-GCS channel) — it
    goes stale ONLY when the VM **host/network** wedges. The GCS-tee'd run.log `PIPELINE_HEARTBEAT` marker lags 42-78m,
    so keying STALL/auto-kill on it false-flagged every healthy-slow VM. run.log-frozen (generous **90m** bound, above
    the max tee lag) is now the hung-WORKER-on-a-live-host **alert-only** corroborator. Per-VM shard mtime stays the
    best signal while capturing.
  - **Auto-kill is sidecar-gated** (`should_auto_kill`, default-on): a fresh sidecar ⇒ `is_vm_progressing` True ⇒ NEVER
    reaped; only a sidecar stale ≥ `kill_minutes` (45m, host wedged) + not-capturing + backfill + not-live is deleted to
    reclaim its wave-launcher slot (cap 5/sweep).
  - **LIVE-VM exemption from `DP_VM_GONE_NO_CAPTURE` (2026-06-27)**: for LIVE VMs (`umbrella == "live"`) the manifest
    `captured` count is the INSTRUMENT COUNT (~15, stable) — it never climbs like a batch instrument-days counter. Flat
    captured on a live VM is benign by design; `DP_VM_GONE_NO_CAPTURE` is **suppressed** (verdict →
    `EXPECTED_NO_CAPTURE`). A live crash (exit != 0) is still caught by `DP_VM_EXIT_NONZERO`. Live capture health (VM
    alive, stream dead) is owned by `live_stream_watcher.py` DP-LIVE-001/002, not the exit-code sweep. Gated on
    `umbrella_for_vm` resolver returning `"live"` — absent it the check falls back to batch behaviour (fail-safe
    conservative).
  - **Host-cron freshness**: the TradFi wave-launcher (a Cloud Run job, `0 */3`) writes
    `vm-census/wave-launcher-last-run.json` each tick (`wave_launcher._write_last_run_sentinel`); the meta sweep probes
    its freshness (budget 360m) with NO Cloud-Run cross-check.
  - **RESOLVED bookend** (`meta_watchers.reconcile_resolved`, all 3 sweeps): a `DP_*` that fired last sweep but not this
    one posts a `:white_check_mark: RESOLVED` INFO. Per-mode active-alert blobs
    (`vm-census/active-dp-alerts-{mode}.json`) so the disjoint-event sweeps don't clobber each other.
- **Layer 2 — the out-of-band deadman** (`uts-prod-monitoring-deadman`, `deadman_poster.py`): probes the Layer-1
  sentinels + the watchdog census DIRECTLY (read-only GCS) and posts to its OWN Slack webhook — **never** `log_event` /
  PubSub / the alerting-service (it must be independent of the path it watches); exits 0 always. **Freshness reads the
  blob CONTENT `ts`**, not the storage-client `last_modified` (which is bare on `deployment-scripts-*` — a JSON sentinel
  reads `age=None` → false "missing (never ran)" otherwise; the epoch-sidecar shape still parses its first-line epoch).
- **Layer 3 — critical-service uptime** (`critical_service_uptime.tf`): 5 GCP-native `uptime_check_config` + alert
  policies (deployment-api / agent-orchestrator / **alerting-service** / deployment-dashboard /
  unified-trading-system-ui) every 5 min → the deadman **email** channel — fully independent of the Slack relay + the
  alerting-service SPOF, so they page even when the alerting path itself is down. `/health` returns 2xx
  (alerting-service is auth-gated → accept 403 = alive-but-protected). **No `notification_rate_limit`** (API rejects it
  for metric-threshold policies).
- **deployment-api memory (2026-07-14, `deployment_api_memory_alert.tf`)** — `uts-shared-deployment-api`
  OOM-crash-looped twice this week (4GiB container, unbounded per-worker caches); uptime checks (Layer 3 above) only
  fire AFTER the service is already down, i.e. post-crash-loop. Closes that gap one step earlier:
  `google_monitoring_alert_policy.deployment_api_memory_high` fires on
  `run.googleapis.com/container/memory/utilizations` &gt;85% sustained 300s, reusing the SAME `monitoring_deadman_email`
  channel as the uptime alert above (deliberately not a new channel). Remediation SSOT:
  `plans/active/deployment_api_cache_oom_and_ui_latency_remediation_2026_07_13.md` (bounded-cache architecture, the
  manifest live-build OOM guard, `WORKERS=2`). Applied live via targeted `tofu apply` 2026-07-14 (policy
  `projects/central-element-323112/alertPolicies/10817162460883602732`) — remember **no auto-apply pipeline exists for
  `terraform/gcp/`** (see the box below), a shipped `.tf` here is not live until someone runs `tofu apply`.

> **No terraform-apply pipeline for `terraform/gcp/`** — there is NO auto-apply. New infra there (uptime checks,
> schedulers) needs a deliberate `tofu apply` (remote GCS state `uts-terraform-state-{pid}`, prefix
> `terraform/state/prod` — a `-target`ed apply is safe + lock-protected). A shipped `.tf` is NOT live until applied.

## Anti-patterns (banned)

- A surface re-deriving umbrella/service/asset_group instead of reading `classify_deployment_target` / `CLOUD_RUN_JOBS`.
- A new Cloud Run scheduler tf or GCP launcher without a registry entry / durable-log streamer (the guards catch it —
  don't whitelist to dodge).
- A silent default umbrella (`classify_deployment_target` raises `UnclassifiedDeploymentError` — fix the classification,
  don't swallow).
