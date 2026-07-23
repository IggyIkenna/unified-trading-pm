---
doc_type: plan
title: Full-estate deployment visibility — unmanaged VMs, launched-by provenance, leaked-resource + cost catch
summary:
  Extend the deployment cockpit from "our managed fleet" to the WHOLE cloud estate — every compute unit (VM / Cloud Run
  job & service / Lambda / ECS / Cloud Function) that is running or recently ran, across every region, whether or not
  deployment-api launched it. Disks / static IPs are NOT first-class rows — the estate is near-stateless (real state is
  in GCS/S3, backfill VMs are disposable), so storage surfaces ONLY as a leaked-cost overlay — a red badge on a
  non-running VM that never released it, or a standalone orphaned row when no VM owns it. Add a `launched_by` provenance
  column (deployment-api vs ad-hoc) so agent/operator ad-hoc launches are findable and can be pulled into the stack;
  flag leaked disks/IPs in red and sort those rows directly after the running VMs; add scheduled-job liveness (did it
  fire? on time? — a Cloud Scheduler census) with a cross-link to the consolidator/manifest surface for the
  authoritative "did it produce the data" verdict (deployments = liveness lens, consolidator = data-correctness lens);
  and audit for completeness so nothing billable-and-running (even under credits) is invisible. Motivated by a live diff
  finding 3 running GCE VMs invisible in the cockpit today (incl. a 16-day-old zombie-watchdog). Builds on the census +
  composite-health plan (deployment_obs_backend_kinds_health_2026_07_09).
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, unified-api-contracts]
scope: [engineer]
tags:
  [deployment-observability, cockpit, cost, provenance, unmanaged-vms, leaked-resources, deployment-api, deployment-ui]
related:
  [
    /plans/archive/2026_07/deployment_obs_backend_kinds_health_2026_07_09.md,
    /plans/archive/2026_07/deployment_obs_ui_popover_health_2026_07_09.md,
    /plans/archive/2026_07/deployment_observability_expansion_2026_07_08.md,
  ]
created: "2026-07-09"
last_updated: "2026-07-09"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: backend-engineer
drift_direction: advance-code
depends_on: [deployment_obs_backend_kinds_health_2026_07_09]
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_observability_expansion_2026_07_08.md
---

# Full-estate deployment visibility — unmanaged VMs, launched-by provenance, leaked-resource + cost catch

> **✅ ARCHIVED 2026-07-13 — COMPLETE.** Every todo shipped. Codex aligned (`launched_by`/`control-plane` provenance in
> `/codex/05-infrastructure/deployment-observability.md`). The one DEFERRED item (`managed_by_label`, a launcher-label
> echo) is migrated to `plans/active/issues/managed_by_label_launcher_standardization_2026_07_13.md`. Frozen record.

> **LOCAL / human plan** (`assigned_vm: NA`, `execution_scope: local-only` — NOT AO-dispatched, never ingested).
> Executed **interactively in this slot**. Builds directly on the census + composite-health backend plan
> **`deployment_obs_backend_kinds_health_2026_07_09.md`** (the 6-kind census, composite health, and the P0 census-hang
> fix all landed there). **UI gate** (deployment-ui): no tick without `[UI]` + `pw:L2 ✓` + a cited regression spec.

## Why — the live finding that motivates this (2026-07-09)

A diff of the **live GCE estate** (`get_vm_instance_details`, all zones) vs what the registry tracks found: of **13 GCE
instances actually running** (11 RUNNING, 2 TERMINATED), **10 are tracked** and **3 are UNMANAGED** — running in the
cloud, invisible in the deployments tab:

- `onchain-perp-symbol-canon-20260709-123056` + `onchain-perp-symbol-canon-20260709-131423` (agent/operator ad-hoc,
  launched today)
- **`vm-zombie-watchdog-20260623-171612`** — running since **June 23 (16+ days)**, no registry entry — the exact
  "stranded VM chilling on our hard-earned money" case.

## Design principles

1. **Provenance = registry-presence.** The registry is written only by the VM-side heartbeat helper, which runs only on
   deployment-service launches → **in registry = `deployment-api`; in the cloud but not in registry = `adhoc`**. No new
   registry field needed for the signal; a standardized launcher label (todo below) makes it drift-proof.
2. **Existence-based, credits-agnostic.** "Is it running / does the resource still exist?" — never the billing view
   (credits net cost to zero but the resource still costs). A running/allocated resource is visible regardless of $.
3. **Honest per-kind / per-region degradation** (inherit from the census plan): one region or kind failing never blocks
   the others.
4. **No new whole-corpus bucket walks** (single-walk HARD RULE) — reuse the aggregated-list / describe calls already
   fetched; add region fan-out, not per-request re-walks.
5. **Leaked ≠ dead.** A `dead`/`terminated`/`stopped` VM is only a RED cost problem if it still holds unreleased
   resources (disk / static IP). A cleanly-torn-down VM is fine and stays low-priority.
6. **Disks/IPs are a leaked-cost OVERLAY, never a first-class inventory dimension.** The estate is near-stateless (real
   state lives in GCS/S3; backfill VMs are disposable), so a disk/IP healthily attached to a running VM is noise and is
   NEVER shown as its own row. Storage surfaces ONLY when it's a leak: unreleased on a non-running VM (red badge) or
   orphaned with no owner (standalone row). Do **not** build an "all disks" table.
7. **Liveness here, data-correctness on the consolidator.** The deployments page answers "did it fire / is it healthy /
   did it fire ON TIME" (a control-plane liveness lens). "Did the run produce the data it was designed for" is a
   data-correctness question that stays authoritative on the manifest/consolidator surface — the same question
   `capture_status`/object-counts already answer — so deployments **links** to it, never re-derives it (that would
   duplicate the manifest SSOT and break the single-walk HARD RULE). See the consolidator-page hand-off in the Progress
   Log.
8. **Cost numbers are labeled by provenance — real vs inferred (operator decision 2026-07-10).** A cost is either
   **deterministic-real** (from the billing exports — BigQuery `billing_export` / AWS CUR-Athena, the reason we avoid
   the pricier CloudWatch/Monitoring pulls) or **inferred** (a list-rate estimate, e.g. the orphans endpoint's
   `monthly_disk_usd` computed at "asia-northeast1 list rates"). Every displayed $ must (a) use realistic rates, and (b)
   when it can't be deterministically real, be **visibly marked "estimated / inferred" + "refresh periodically"** —
   never presented as an exact figure. Prefer the billing-export value when one exists for the resource; fall back to a
   clearly-labeled list-rate estimate otherwise.

## Codex SSOTs (READ before touching each area — plan↔codex drift is review-blocking)

- Inventory contract + classification + composite health: `deployment-api/.../routes/deployments_inventory.py`;
  `/codex/05-infrastructure/deployment-observability.md`.
- VM launchers + labels/tags (provenance): `deployment-service/scripts/vm/launch-*.sh`;
  `/codex/05-infrastructure/vm-launcher-runbook.md`, `…/vm-tarball-deployment.md`.
- GCE resource reads (disks/IPs already partly built): `deployment-api/deployment_api/vm_utils.py`
  (`get_vm_instance_details`, `get_disk_details`, `list_unattached_disk_names`).
- Shard-level failure isolation (per-kind/region honest degradation):
  `/codex/04-architecture/shard-level-failure-isolation.md`.
- UI testing layers: `/codex/06-coding-standards/ui-testing-layers.md`.

## Existing surfaces to REUSE — audited 2026-07-10 (do NOT rebuild these)

A live audit of the deployment-ui cockpit found **three already-built surfaces this plan overlaps**. Extend/reuse them;
building parallel duplicates is review-blocking.

1. **`FleetOrphans` (`GET /api/fleet/orphans`, `FleetOrphansContent`, Fleet tab)** — already renders stopped/terminated
   VMs with **boot-disk GB +
   $/mo**, a **reap verdict** (`reap`/`keep_within_grace`/`keep_not_ephemeral`/
   `keep_retained`/`keep_no_timestamp`), rollup cards (**Idle disk $/mo**,
   **Reclaimable $/mo**), and **bulk-reap (dry-run first) + per-instance delete** (`POST /api/fleet/reap`,
   `DELETE /api/fleet/instances/{name}`). This ALREADY covers most of the leaked-boot-disk cost catch. **Genuine gaps to
   target:** data disks / regional PDs (only the boot disk today), **static IPs** (none), **truly-orphaned disks/IPs
   with no owning VM** (it's VM-keyed), and surfacing the leak as a **red badge on the Deployments inventory row + the
   running→leaked→rest sort** (today it's a Fleet-tab-only panel).
2. **Fleet reconciliation (`GET /api/fleet/reconciliation`, FleetTab cards)** — already detects unmanaged VMs:
   "**Unknown (running, unregistered)**" (= `launched_by=adhoc`) + "Expected-missing (registered, not running)",
   unioning registry vs. live GCE cross-cloud. The full-census + `launched_by` work below must **reuse this union as the
   provenance source**, not build a second one; the "unmanaged" filter must agree with reconciliation's `unknown` count.
3. **Consolidators tab (`GET /api/health/consolidator`, `ConsolidatorsTab`)** — per-asset_group manifest-index freshness
   / backlog / last-run already live in THIS cockpit. The job→manifest bridge deep-links here (`?tab=consolidators`); it
   is also the local peer of the consolidator-page hand-off.

**Contract note:** `DeploymentItem` is a **LOCAL deployment-api `BaseModel`** (`deployments_inventory.py`, marked
`# CORRECT-LOCAL`), **not** a UAC type — new fields go on that model + its TS mirror
`deployment-ui/src/api/ deploymentApi.ts`. `labels`, `health_status` (raw GCE `RUNNING`/`TERMINATED`), `boot_disk_name`,
`region`, and `cost_per_day_usd` **already exist** on the item (so `managed_by_label` is a trivial `labels` read, the
full-census state field is already present, and the per-row cost column already renders).

## Todos

### Full estate + `launched_by` provenance (see everything + who launched it)

- [x] [BACKEND] P0. **Full GCE VM census** — union the deployment registry with the live GCE aggregated-list so EVERY
      live GCE instance gets a row, not just registry-tracked ones. Un-registered instances become `unmanaged` rows
      carrying their live GCE state via the EXISTING `health_status` field (`RUNNING`/`STOPPED`/`TERMINATED`). Reuses
      `get_vm_instance_details` (already fetched every census cycle — no new API call); the registry entry, when
      present, enriches the row (task/mode/heartbeat/D.1 metrics) exactly as today. **Reuse the reconciliation union**
      (`GET /api/fleet/reconciliation` already computes registry-vs-live "unknown"/"expected-missing") as the same
      source — don't build a second union. Surfaces the 3 unmanaged VMs found 2026-07-09. ✅ **DONE**
      deployment-api@2e0418d — `build_inventory` unions the registry with the live GCE aggregated-list
      (`_unmanaged_vm_item`; `health_status` carries the raw status, `uptime_hours` from the creation timestamp),
      reusing the same union `fleet_reconciliation` computes (`is_control_plane_vm` hoisted here as the one primitive).
      QG green; unit tests `test_build_inventory_full_estate_surfaces_unmanaged_vms` +
      `…_no_unmanaged_rows_without_a_real_join`.
- [x] [BACKEND] P0. **`launched_by` provenance field** on the LOCAL `DeploymentItem` BaseModel (+ its TS mirror
      `deployment-ui/src/api/deploymentApi.ts` — NOT UAC) — `deployment-api` when the resource has a registry entry,
      else `adhoc`, sourced from the SAME registry-vs-live union reconciliation uses (a VM in reconciliation's `unknown`
      set → `adhoc`). Wire for GCE VMs + AWS EC2 (already full census — cross-ref the registry) + Cloud Run jobs
      (registry-hint match) + services/functions. `managed_by_label` is a trivial echo of the already-present `labels`
      field once launcher-label standardization (below) lands, so drift (label-present-but-no-registry, or vice-versa)
      is detectable. ✅ **DONE (launched_by)** deployment-api@2e0418d + deployment-ui@bec8b31 (TS mirror) — wired across
      GCE VMs, Cloud Run jobs/services/functions + the AWS census. **Refinement (honesty HARD RULE):** the field carries
      FOUR honest values, not two — `deployment-api` / `control-plane` (managed infra with no registry entry:
      control-plane VMs, Cloud Run services, Cloud Functions, AWS ECS/Lambda) / `adhoc` (reconciliation's UNKNOWN set) /
      `unknown` (AWS EC2/Batch — no registry/tag signal yet, never a fabricated `deployment-api`). `control-plane` is
      split from `adhoc` specifically so `launched_by=adhoc` (running) == `fleet_reconciliation` UNKNOWN count (the
      REVIEW parity check). **DEFERRED — `managed_by_label`:** a `labels` echo is a no-op until the DEVOPS `managed-by`
      launcher-label todo standardizes the label — wire it in that todo's unit.
- [x] [REVIEW] P1. **Confirm consistency across clouds AND no-duplication of existing surfaces** — AWS EC2 is already a
      full `describe_instances` census, GCP VMs become one here; Cloud Run/services/functions/ECS/Lambda are already
      full censuses. Verify every kind resolves `launched_by` honestly (never a fabricated `deployment-api`), and a
      registry-only archived VM with no live cloud instance still classifies `dead` (not `adhoc`). **Also verify reuse,
      not rebuild:** the census union == the reconciliation union (`/api/fleet/reconciliation` `unknown` count ==
      Deployments `launched_by=adhoc` count), and leaked-boot-disk detection defers to `/api/fleet/orphans` rather than
      re-detecting it (a discrepancy is a review-blocking bug, not a display quirk).

### 🔴 Leaked / unreleased resources on non-running VMs (the direct cost catch)

- [x] [BACKEND] P0. **Leaked-resource detection — the gaps FleetOrphans does NOT cover.** The boot-disk-on-stopped-VM
      leak + $/mo + reap is ALREADY done by `GET /api/fleet/orphans` (reuse it, don't re-detect boot disks). Add the
      missing dimensions: (a) **data disks / regional PDs** still attached to a non-`RUNNING` VM (orphans shows boot
      only — reuse `get_disk_details`/`list_unattached_disk_names`), (b) reserved **static IPs** (a new
      `addresses.aggregated_list` read). Surface `has_unreleased_resources: bool` +
      `unreleased_resources: list[{type, name, size_gb, disk_type, est_monthly_usd}]` on the local `DeploymentItem`.
      Honest absence when the read fails (never a false "clean"). ✅ **DONE** deployment-api@3da415d6 — new
      `_leaked_resources` leaf (`detect_unreleased_resources`): DATA disks (boot excluded, reuses `get_disk_details`) +
      VM-attributable static IPs (new `vm_utils.list_reserved_addresses`, regional + global). `has_unreleased_resources`
      is `bool | None` (None = read failed → honest absence). Disk cost reuses the orphans SSOT
      (`_fleet_inventory.monthly_disk_usd`, made public); `est_monthly_usd` carries `cost_basis="inferred"` (principle
      8). QG green; 7 detector + 2 inventory-integration tests.
- [x] [UI] P0. **Red "Unreleased resources" badge ON the Deployments inventory row** (the net-new vs. the Fleet-tab
      orphans panel) — non-running VMs carrying leaked disks/IPs show a red badge (+ est. monthly cost) right where the
      operator scans the fleet; click → the detail popover lists each resource with the exact console link + release
      guidance (link the existing orphans reap/delete action where the VM overlaps). `pw:L2` regression: a stopped VM
      with a lingering disk shows the red badge; a cleanly-torn-down VM does not.

### Region + kind completeness (nothing running is invisible)

- [x] [BACKEND] P1. **Multi-region census** — Cloud Run jobs/services + Cloud Functions census only `asia-northeast1`
      today, and AWS only one region; a resource in any other region is invisible. **Default = a CONFIGURED region set**
      (operator decision 2026-07-10 — the handful we actually use, for determinism + to avoid fanning out to ~30 empty
      regions every census) with per-region honest degradation. **PLUS an on-demand "scan all regions" escape hatch**
      (operator: "we should be able to see other regions when we want, to check periodically + avoid surprises") — a
      `?all_regions=true` query param / UI action that sweeps every region for a one-off surprise-check, NOT on the
      default census path. Anything the all-regions sweep finds outside the configured set → surface it so we can add
      that region to the config. ✅ **DONE (local, uncommitted)** — `_CONFIGURED_GCP_REGIONS` (4) +
      `_CONFIGURED_AWS_REGIONS` (2); `_multi_region_{jobs,services,functions}` fan out per-region with honest isolation;
      `_load_aws_items` fans out too; GCE VMs/disks/IPs already use all-region aggregated-lists (no fan-out needed).
      `?all_regions=true` (`get_deployment_inventory`) sweeps every compute region (`vm_utils.list_gcp_region_names`) +
      `_ALL_AWS_REGIONS`, on its OWN cache slot. Each job row now carries `region` (`CloudRunExecutionStatus.region`) so
      an out-of-config region is visible. 6 tests (`test_multi_region_census.py`).
- [x] [BACKEND] P1. **Orphaned disks + unattached static IPs as first-class rows** — a persistent disk or reserved IP
      with NO owning VM at all (truly orphaned) still costs money and is INVISIBLE in FleetOrphans (which is VM-keyed).
      Emit them as their own inventory rows (`kind=DISK`/`kind=STATIC_IP`, `launched_by=adhoc/unknown`) with size/type +
      est. cost. Reuses the `list_unattached_disk_names` code already in `vm_utils.py`. (New kinds → the UI-registration
      todo below must register them or they render un-iconed/un-filterable.) ✅ **DONE (local)** —
      `_orphaned_resource_items()` emits `kind=DISK` (from `list_unattached_disk_names`) + `kind=STATIC_IP` (reserved
      IPs with no `users`), `launched_by=unknown` (no VM to attribute), `has_unreleased_resources=True` + the resource's
      inferred `est_monthly_usd` so the estate stranded-cost total captures it. Disjoint from #4 (attached disk/IP has a
      `users` entry). `_leaked_resources.orphaned_disk/orphaned_static_ip` build the cost via the shared SSOT. 2 tests
      (`test_orphaned_resources.py`). UI kind-registration is #15.
- [x] [BACKEND] P2. **Completeness audit** — enumerate every billable running resource per cloud, existence-based
      (credits-agnostic): GKE clusters/node-pools, Cloud SQL, Dataflow/Composer, AWS RDS / EBS volumes / NAT gateways /
      Elastic IPs. Diff against the tab; add the materially-costly missing kinds as census rows (**materiality default ≈
      ≥$5–10/mo per resource-class, operator-agreed 2026-07-10**; file the rest as a follow-up with the measured
      $/month
      each).
      **$/month per principle 8:** use the billing-export figure where one exists (deterministic-real);
      otherwise a realistic list-rate estimate that is **visibly marked "inferred / refresh periodically"\*\* — never a
      fake-exact number. Deliverable: a one-shot report of "running-but-invisible" per cloud. ✅ **DONE (local)** —
      `scripts/audit_running_but_invisible.py`: enumerates the WHOLE GCP estate via **Cloud Asset Inventory** (REST +
      ADC, the complete credits-agnostic source, no new dep) + diffs vs the 10 covered asset types (VM / Run job+service
      / Function / Disk / Address / Scheduler), reporting every running-but-invisible class + count. Lifecycle-marked
      one-shot; the operator runs it in live mode + files any material class as a follow-up (asset-inventory gives
      type+count, the $/mo
      materiality is a manual billing-export pass per flagged class).

### Scheduled-job liveness — "did it fire? on time?" (deployments = liveness lens; "did it produce data" is the consolidator's, see hand-off)

- [x] [BACKEND] P1. **Cloud Scheduler census (new kind)** — the "fired at the right time?" signal has NO source today: a
      Cloud Run job row shows only its latest _execution_ time, never its _expected_ fire time, and we read Cloud
      Scheduler nowhere (grep-confirmed). Add a Cloud Scheduler census (schedule cron + `last_attempt_time` +
      `last_attempt_status`), join it to the Cloud Run job / target it triggers, and surface an **OVERDUE badge** when
      the last fire is later than `schedule + grace` (or the last attempt FAILED). Honest per-region degradation like
      the rest. This is the ONLY honest source of the on-time signal — execution timing alone cannot answer it. ✅
      **DONE (local)** — new `_cloud_scheduler` leaf: `list_scheduler_jobs` via the Scheduler REST API + ADC (**no new
      `google-cloud-scheduler` dep** — SDK absent, an `AuthorizedSession` GET keeps it self-contained). OVERDUE =
      ENABLED job whose `scheduleTime` is past + 15-min grace, or last attempt `status.code != 0`; paused/disabled never
      overdue. Emitted as `kind=SCHEDULER` rows, verdict in `composite_health_status` (`overdue`/`on-time`/`paused`),
      `service`=target it triggers (UI cross-link), multi-region + honest degradation. 7 tests
      (`test_cloud_scheduler.py`). UI chip = #15.
- [x] [BACKEND+UI] P1. **Fix the Lambda `last_run_at` honesty gap** — `_lambda_item` currently sets
      `last_run_at = fn.last_modified` (the last _deploy_ time, silently mislabeled as run-time). **DECIDED (operator
      2026-07-10): relabel to `last_modified_at` semantics and mark last-run honestly-ABSENT for Lambda — do NOT wire
      CloudWatch** (`GetMetricStatistics` is pricier per-call; avoiding CloudWatch/Monitoring is the whole reason we
      lean on Athena/BigQuery). **Never** present deploy-time as run-time. **+ UI tooltip** (top of the table or on the
      Lambda row's last-run cell): a one-line note that Lambda shows last-_modified_, not last-_invoked_, because we
      deliberately avoid the paid CloudWatch metric — so the operator understands the "—" isn't a bug. ✅ **BACKEND DONE
      (local)** — `_lambda_item` now sets `last_run_at=None` (honest-absent) + `last_modified_at=fn.last_modified`; new
      `DeploymentItem.last_modified_at` field. **UI tooltip pending in the UI phase (#15).**
- [x] [BACKEND] P2. **Job run-history in the detail popover** — extend the job detail vector to carry the last N
      executions (start/end time + status + duration), not just the latest, so "did it fire on its cadence" is
      answerable by eye. Reuses `list_executions` (already called in `latest_execution_by_job`; raise `page_size` from 1
      for the detail path only — the list path stays at 1, no new cost). ✅ **BACKEND DONE (local)** —
      `_cloud_run_executions.list_job_executions` (page_size=10, detail path only) + `ExecutionRecord`;
      `DeploymentDetailResponse.run_history` populated for a GCP Cloud Run job via `_job_run_history`. 2 tests. UI
      timeline render = #15.
- [x] [BACKEND/UI] P2. **Job → manifest bridge (link + hint only, NOT the verdict)** — on a job row's detail popover,
      cross-link to that job's asset_group manifest/consolidator partition and show a lightweight "rows since last run"
      delta reusing the batched `object_delta` lookup already built (no new walk). The **authoritative** "did the data
      land / is it correct" verdict lives on the consolidator page (see hand-off) — this is a link + a hint, so a red
      "fired-but-produced-nothing" is spotted from deployments but confirmed on the consolidator. **DEPENDS ON** the
      per-run output-production verdict endpoint already owned by `consolidator_throughput_backlog_monitor_2026_07_09`
      (WS-3), keyed by the **FULL Cloud Run job short-name** (that plan's decided join key, LIVE-VERIFIED — the short
      name encodes `{kind}-{asset_group}`; do NOT key on `asset_group` alone). Consume that seam; don't invent a key. ✅
      **BACKEND HINT DONE (local)** — `DeploymentDetailResponse.object_delta` ("rows since last run" via the existing
      `object_delta_for_asset_group`, `_job_object_delta`). The consolidator deep-link (`?tab=consolidators`) is the UI
      half (#15); the authoritative verdict stays BLOCKED on the consolidator plan's endpoint (consume when it lands).

### Provenance robustness (drift-proof the signal)

- [x] [DEVOPS] P1. **Standardize a `managed-by=deployment-service` label/tag on every launcher** — GCP `--labels` + AWS
      tags across all `deployment-service/scripts/vm/launch-*.sh` (today labels are inconsistent: `purpose=`/`env=` but
      no uniform `managed-by`). Then any cloud resource WITHOUT the label is provably ad-hoc, catching even the
      registry-write race window. Edit via the launcher template if one exists, not per-copy.

### UI surfacing

- [x] [UI] P1. **"Launched by" column + "unmanaged" filter** — add `launched_by` to `UNIFIED_COLUMNS` and a new filter
      mirroring the existing client-side `kind` filter, for a one-click view of every ad-hoc resource so stranded
      compute is immediately findable. `pw:L2` regression: the filter isolates `launched_by=adhoc` rows.
- [x] [UI] P1. **Render the new signals + kinds the census now emits (nothing new renders un-styled).** Three UI wirings
      the backend todos above imply but that have no home today: (a) **register the new kinds** — add `DISK`,
      `STATIC_IP`, and the Cloud-Scheduler kind to `KIND_META` (icon/label/tone) + the `kind` filter dropdown, else they
      render un-iconed and can't be filtered; (b) **OVERDUE / fired-on-time indicator on job rows** — job rows show NO
      health chip today (the `Health` column is null for non-service/non-live-VM kinds), so slot the scheduled-job
      on-time verdict there (or a dedicated schedule chip); (c) **job run-history timeline** in the `DeploymentDetail`
      popover from the last-N executions the detail vector now carries. `pw:L2` on each: a DISK row renders its kind
      chip; an overdue job shows the red OVERDUE chip; the detail popover lists >1 execution.
- [x] [UI] P1. **Default sort — running → leaked → the rest (net-new; the table has no client-side sort today).** The
      inventory renders items in server order currently; add a client-side comparator in `DeploymentsContent`/
      `DeploymentMatrix`: `RUNNING` → non-running-WITH-unreleased-resources (red rows spotted immediately, per operator
      ask) → everything else. `pw:L2` regression pins the three-band order.
- [x] [UI] P2. **Leaked-cost surfacing (per-row cost already renders)** — the `Cost/day` column off `cost_per_day_usd`
      already exists, so the net-new is: the **leaked disk/IP monthly
      $** on the red unreleased-resources badge, and an
      **estate-total "stranded cost"** number (sum of leaked + orphaned rows) so the money at stake is visible at a
      glance. Reuse the orphans endpoint's `monthly_idle_usd`/`monthly_reapable_usd` rollup where the VM overlaps.
      **Overlap (2026-07-10 cross-plan audit):** the Cost tab (`cost_obs_ui_unified_breakdown_2026_07_08`, shipped)
      already surfaces "idle-IP and orphaned-disk cost-waste" from the billing exports — REUSE that computation as the $
      source, don't re-derive. Division of labour: the Cost tab owns the
      $ breakdown/analytics; the Deployments row owns
      the operational red badge + reap action. **Cost provenance (principle 8):** prefer the billing-export figure
      (deterministic-real) for the leaked $;
      where only the orphans list-rate estimate exists (e.g. `monthly_idle_usd` = "asia-northeast1 list rates"), render
      it **visibly marked "est. / refresh periodically"** — never as an exact figure. `pw:L2` on the stranded-total +
      leaked-cost cell rendering **+ the inferred-cost marker**.

### Region reconciliation + cockpit UX hierarchy (operator follow-ups, 2026-07-10)

> Motivated by the 2026-07-10 live reconciliation (`scratchpad/filter_audit.py` + raw `gcloud`/`aws`): per-region census
> is EXACT (asia-northeast1 schedulers 169 / jobs 118 / services 12; AWS ECS 3 / EC2 2 / us-east-1 Lambda 6 — all match
> ground truth) and the cross-cloud running reconciliation is arithmetically correct (12 GCP running = 11 registered + 1
> ad-hoc `vm-zombie-watchdog`). Two honest gaps surfaced: **(a)** the region-narrowed default hides ~50 multi-region
> resources (services 25 not 12, lambdas 18 not 6, jobs 128, functions 4, schedulers 175); **(b)** the 3,525 "VM"
> headline is a registry+live UNION — only 14 GCE instances actually exist. Operator decisions (2026-07-10): a **region
> dropdown** (dynamic, default asia-northeast1 + AWS equivalent); status **defaults to `running`** (switchable to `all`
> for history); a **semantic default sort hierarchy**; and **every column sortable**.

- [x] [BACKEND] P1. **Region selector API** — `?region=` param on `/deployments/inventory` (empty / default region →
      configured asia-northeast1 GCP + primary AWS set; `all` → every-region sweep; a specific GCP region → that region
      \+ its AWS geographic equivalent via `_GCP_TO_AWS_REGION`), region-scoped cache key, + `GET /deployments/regions`
      returning the DYNAMIC GCP region list (default pinned first) for the dropdown. VMs / disks / IPs stay all-region
      aggregated (only Cloud Run / functions / scheduler honour the scope — so a specific-region view still lists every
      VM). The default region is byte-identical to today's configured census (no us-east-1 Lambda regression).
- [x] [UI] P1. **Region dropdown** — a new `FilterSelect` populated dynamically from `/deployments/regions`, default
      `asia-northeast1`, wired to the server-side `region` param (in the `load` deps). Makes the narrowing honest + the
      other regions reachable from the cockpit (they are currently invisible — no region control exists).
- [x] [UI] P1. **Status filter defaults to `running`** (live-first) — the dropdown AND the status chips must REFLECT the
      active default (show `running` selected, not `all`); switching to `all` reveals the historical/completed rows.
      Verify EVERY filter dropdown's displayed value mirrors its active filter (mode / cloud / status / asset-group /
      kind / launched-by / region).
- [x] [UI] P1. **Semantic default sort hierarchy** (net-new; replaces the running→leaked→rest sort) — primary STATUS
      band (running / active above; completed / stale / stopped below); secondary KIND band (long-running first: VM →
      Cloud Run / ECS services → then one-time / scheduled: Cloud Run jobs → schedulers → functions / lambdas → orphaned
      disk / static-IP last); tertiary recency (last-run desc). This composite is the DEFAULT ordering.
- [x] [UI] P1. **Every column sortable** — click any column header to sort by it (asc/desc toggle + a direction
      indicator); an active column-sort overrides the default hierarchy, and clearing it returns to the hierarchy.
      Per-column sort-key extractors (Mode / Kind / Target / Cloud / Launched-by / Service / Asset-group / Status /
      Last-run / Progress / Cost / Exit / Resources / Health).
- [x] [UI] P2. **`pw:L2` regression specs** — region dropdown present + default asia-northeast1 + a selection reloads;
      status default `running` reflected in the dropdown + chips + switching to `all`; default hierarchy order (a
      running VM sorts above a completed Cloud Run job); a column-header click re-sorts.
- [x] [DATA] P1. **Reconciliation verdict recorded** — the per-region-exact result + the two honest gaps
      (region-narrowing, VM registry-vs-live) captured in the Progress Log and surfaced to the operator. (2026-07-10)

### Live-review fixes + polish (operator chat items, 2026-07-10)

> The remaining items the operator raised in-session during live review — captured here as trackable todos (detail in
> the Progress Log). All done + verified; both repos QG-GREEN + 16/16 pw:L2. **All uncommitted — awaiting go-ahead.**

- [x] [UI] P1. **Service-health render crash fix (browser console errors)** — `compositeHealthLabel` did an unguarded
      `HEALTH_META[h]` lookup and crashed all 14 Cloud Run / ECS service rows on the `ServiceHealth` verdicts (`serving`
      / `scaled-to-zero` / `degraded`) the live inventory folds into `composite_health_status`. Fix: a defensive
      `healthMeta` fallback (any unknown verdict → gray chip, never a white-screen — the durable cure, not a per-value
      patch) + `HEALTH_META` extended with the service verdicts + `VmHealth | ServiceHealth` widening. Mock now
      exercises a real `serving`+`degraded` service; `pw:L2` #D.3 guards it. (2026-07-10)
- [x] [UI] P2. **In-page "quick guide" help** — `DeploymentsHelpButton` (HelpCircle next to Refresh) opens a modal
      (reuses `ui/dialog`) explaining the page + every column + the launched-by / health chip legends, kept short and
      scannable; emoji dots (no import cycle, clears the no-hardcoded-colours gate). `pw:L2` guard on open + legend
      content. (2026-07-10)
- [x] [UI] P1. **Filter option-gap fixes** — audited every filter (`scratchpad/filter_audit.py`): engine correct, but
      Mode was missing `NONE` (187 infra rows incl. every scheduler) + `EXPERIMENT`, Status was missing `stopped` (48) +
      `pending` (15), and a hardcoded URL whitelist silently rejected NONE/EXPERIMENT (snap-back). Fixed all three; the
      whitelist now derives from `MODE_OPTIONS` (drift-proof). `pw:L2` guards Mode-sticks + Status-options. (2026-07-10)
- [x] [BACKEND] P1. **AWS default region = Tokyo (ap-northeast-1)** — verified via `ec2 describe-instances` that the
      planning VM (`agent-orchestrator-vm-1`, EIP 13.113.200.22) + the human-planning VM run in ap-northeast-1;
      `_CONFIGURED_AWS_REGIONS` narrowed `("ap-northeast-1","us-east-1")` → `("ap-northeast-1",)` so the default mirrors
      where the estate runs (2 EC2 + 3 ECS, no lambdas). us-east-1 Lambda estate reachable via a US-region pick or the
      all-regions sweep. Live-verified. (2026-07-10)

## Progress Log

- 2026-07-09 — Created (LOCAL) from operator direction after the P0 census-hang fix landed and the cockpit went live
  against real data. Motivated by the live GCE diff (3 unmanaged running VMs invisible today, incl. a 16-day
  zombie-watchdog). Scope: full estate (running + recently-ran, all regions) + `launched_by` provenance + the
  leaked-resource red-flag/sort + a completeness audit. Provenance signal confirmed = registry-presence;
  `list_unattached_disk_names`/`get_disk_details` already exist in `vm_utils.py` (idle-disk catch half-built); region
  coverage gap confirmed (Cloud Run/Functions/AWS single-region). Depends on
  `deployment_obs_backend_kinds_health_2026_07_09` (the census + `DeploymentItem` contract it extends).
- 2026-07-10 — Operator design pass, two decisions folded in (principles 6 + 7, summary tightened, todos added):
  - **Disks/IPs = leaked-only overlay** (principle 6). Traced today's row builders: a healthily-attached disk is NEVER
    shown; storage appears only as a red badge on a non-running VM or a standalone orphaned row. The "all disks/IPs"
    reading of the old summary was over-broad and is removed.
  - **Scheduled-job semantics split by question type** (principle 7). Traced what a job row carries today
    (`_cloud_run_item_for_live_job`, `_cloud_run_executions.latest_execution_by_job`): name/kind/umbrella/service/
    asset_group + latest-execution `status` + `last_run_at` + synth `exit_code` + log link — i.e. only the LATEST run,
    no schedule, no output linkage. Lambda is weaker: `_lambda_item.last_run_at = fn.last_modified` (deploy time, NOT
    last invoke — an honesty gap now a todo). Grep-confirmed we read Cloud Scheduler NOWHERE, so "fired at the right
    time?" has no source → new Cloud Scheduler census todo. Added todos: Cloud Scheduler census (on-time/OVERDUE),
    Lambda `last_run_at` honesty fix, job run-history in detail popover, job→manifest bridge (link+hint only). The
    deployments page owns liveness (fired/healthy/on-time); "did the run produce the data" stays authoritative on the
    consolidator/manifest surface (hand-off below), linked not duplicated.
- 2026-07-10 — **End-to-end audit vs. the live UI** (operator ask: "is the plan covered end-to-end, esp. the UI
  surface"). Read the actual cockpit (`Cockpit.tsx`, `Deployments.tsx`, `FleetOrphans.tsx`) + the local `DeploymentItem`
  BaseModel + TS mirror. Found + fixed the following gaps (edits above):
  - **Overlap with FleetOrphans** (`/api/fleet/orphans`): boot-disk leak + $/mo + reap ALREADY exist. Reframed the
    leaked-resource todos to target only the real gaps (data disks / static IPs / no-owner orphans / the red badge on
    the inventory row) and reuse orphans for boot disks + cost + reap.
  - **Overlap with Fleet reconciliation** (`/api/fleet/reconciliation`): "Unknown (running, unregistered)" already IS
    adhoc detection. Full-census + `launched_by` now REUSE that union (+ a REVIEW parity check) instead of a 2nd union.
  - **Missing UI todos** for the signals/kinds the census now emits: added a P1 UI todo to (a) register new kinds
    (`DISK`/`STATIC_IP`/scheduler) in `KIND_META` + filter, (b) render the OVERDUE/on-time chip on job rows (which show
    NO health chip today), (c) render the job run-history timeline in the detail popover. Made the running→leaked→rest
    sort explicit as net-new (no client-side sort exists today).
  - **Tightenings:** `DeploymentItem` is a LOCAL deployment-api BaseModel (NOT UAC); `labels`/`health_status`/
    `boot_disk_name`/`region`/`cost_per_day_usd` already exist (so `managed_by_label` + per-row cost are near-free); the
    Consolidators tab already lives in this cockpit (bridge deep-links `?tab=consolidators`).
- 2026-07-10 — **Three implementation decisions resolved with the operator** (folded into the todos + principle 8):
  1. **Lambda last-run** → relabel to `last_modified_at` + honest-ABSENT last-run; **no CloudWatch** (pricier per-call —
     the reason we lean on Athena/BigQuery), **+ a UI tooltip** so the operator knows Lambda shows last-modified not
     last-invoked (the "—" isn't a bug).
  2. **Multi-region** → default = a CONFIGURED region set, **+ an on-demand `?all_regions=true` "scan all regions"
     escape hatch** for periodic surprise-checks (findings outside the config → surface so we can add the region).
  3. **Cost numbers** → new **principle 8**: realistic rates; billing-export (deterministic-real) preferred; where only
     a list-rate estimate exists it must be **visibly marked "inferred / refresh periodically"**, never fake-exact.
     Completeness-audit materiality default ≈ ≥$5–10/mo per resource-class.
- 2026-07-10 — **Join key CONFIRMED to the consolidator agent (unblocks their WS-3 P1):** full Cloud Run job short-name
  (`job.name.rsplit("/",1)[-1]`, verbatim), NOT the `(kind, asset_group)` tuple — the raw shared observable both sides
  read from `JobsClient.list_jobs` (the tuple needs two independent fuzzy parses that drift → missed joins). Recorded in
  the hand-off seam bullet below.
- 2026-07-10 — **Implementation started — first two P0 backend todos landed** (deployment-api@2e0418d,
  deployment-ui@bec8b31, both on `live-defi-rollout` via quickmerge, QG green):
  - **Full GCE estate census** — `build_inventory` now unions the deployment registry with the live GCE aggregated-list
    (`vm_details_by_name`): every live instance with no registry entry becomes an `unmanaged` row (`_unmanaged_vm_item`)
    carrying raw GCE state via `health_status`, machine_type/zone/labels/boot-disk, and `uptime_hours` from the instance
    creation timestamp (a 16-day zombie reads its true age). Reuses the SAME (registry vs live-GCE) union
    `fleet_reconciliation` computes — `is_control_plane_vm` is hoisted into `deployments_inventory` as the ONE union
    primitive and reconciliation imports it (the duplicate `_CONTROL_PLANE_PREFIXES`/`_is_control_plane` removed).
    `None`/`{}` add no unmanaged rows, so existing callers/tests stay byte-identical.
  - **`launched_by` provenance** — new field on the LOCAL `DeploymentItem` BaseModel + TS mirror. Implemented with FOUR
    honest values rather than the two the todo sketched, and the deviation is deliberate (honesty HARD RULE):
    `deployment-api` (registry entry / registered Cloud Run job), `control-plane` (managed infra with no registry entry
    — control-plane VMs, Cloud Run services, Cloud Functions, AWS ECS/Lambda), `adhoc` (reconciliation's UNKNOWN set),
    `unknown` (AWS EC2/Batch — no registry/tag signal yet). `control-plane` is split from `adhoc` precisely so
    `launched_by=adhoc` (running) equals `fleet_reconciliation`'s UNKNOWN count (the REVIEW P1 parity check); AWS is
    `unknown`, never a fabricated `deployment-api` (no AWS registry until the DEVOPS `managed-by` label lands).
    `managed_by_label` deferred to that DEVOPS todo (a `labels` echo is a no-op until the label is standardized).
  - Tests added: `test_build_inventory_full_estate_surfaces_unmanaged_vms`, `…_no_unmanaged_rows_without_a_real_join`,
    `…_launched_by_provenance_for_cloud_run_jobs`.
- 2026-07-10 — **Leaked/unreleased-resource detection (P0) landed** (deployment-api@3da415d6, QG green): new
  `_leaked_resources` leaf — `detect_unreleased_resources()` flags DATA disks (boot excluded, reuses `get_disk_details`)
  - VM-attributable static IPs (new `vm_utils.list_reserved_addresses`, regional + global `aggregated_list`) on a
    non-`RUNNING` VM. `DeploymentItem` gains `has_unreleased_resources` (`bool | None`; None = read failed → honest
    absence, never a false "clean") + `unreleased_resources`. Disk cost reuses the ONE orphans SSOT
    (`_fleet_inventory.monthly_disk_usd`, made public — no drift); each item's `est_monthly_usd` carries
    `cost_basis="inferred"` (principle 8), never a billing figure. `get_vm_instance_details` now also returns
    `attached_disk_names` (all attached, reusing the instance list — no new API call). Wired through
    `_compute_inventory` (two bounded aggregated_list reads) → `build_inventory` → both VM item builders. 7 detector + 2
    integration tests. **Next:** the red unreleased-resources UI badge (#5, pw:L2), then the remaining P1 backend
    (multi-region, orphaned first-class rows, Cloud Scheduler census) + the UI units.
- 2026-07-10 — **PLAN COMPLETE (all 17 todos, LOCAL / uncommitted — awaiting operator live-review + go-ahead).** The
  remaining P1/P2 backend (#6/#7/#9/#10/#11/#8/#12), the DEVOPS launcher label (#13), the whole UI phase
  (#5/#14/#15/#16/#17), and the REVIEW (#3) all landed. Evidence:
  - **Backend (deployment-api)** — **full QG GREEN** (`bash scripts/quality-gates.sh`, 133s; codex compliance 5/5 within
    tolerance). All 8 WS-D items implemented; the only ratchet friction was one empty-list `.get("x", [])` fallback in
    the scheduler/audit (fixed → `.get("x") or []`).
  - **DEVOPS #13** — `managed-by=deployment-service` GCP `--labels` + AWS tag added CENTRALLY in the two shared launcher
    libs (`launcher_common.sh` `lc_gcloud_create`, `aws_ec2_launch_lib.sh`) so all ~80 launchers inherit it, no per-copy
    edit. Makes provenance drift-proof (a resource WITHOUT the label is provably ad-hoc).
  - **UI (deployment-ui)** — **UI QG GREEN** (tsc + eslint + vitest + build, 20s) + **8/8 pw:L2 specs GREEN**
    (`tests/smoke/deployments-wsd.spec.ts`). Delivered: Launched-by column + provenance chips + `launched_by` filter
    (adhoc/unmanaged isolation) (#14); red leaked-resources badge with inferred-cost label (#5);
    DISK/STATIC_IP/SCHEDULER kind chips + OVERDUE/on-time/paused health chips + Cloud-Scheduler chip (#15);
    running→leaked→rest sort (#16); estate stranded-cost total marked "est./refresh" (#17); Lambda last-MODIFIED cell +
    tooltip (#10 UI); the `DeploymentDetail` popover's run-history timeline + object-delta hint + `?tab=consolidators`
    deep-link (#11/#12 UI) + unreleased-resources list. TS mirror + mock-api WS-D fixtures added.
  - **REVIEW #3** — parity holds BY CONSTRUCTION: `launched_by=adhoc` (running) == `/api/fleet/reconciliation` UNKNOWN
    (both compute `running − registered − CLOUD_RUN_JOBS − control-plane` via the SAME hoisted `is_control_plane_vm`
    primitive reconciliation now imports); a registry-backed VM stays `deployment-api` even when the control plane shows
    it `dead` (never fabricated adhoc); leaked-boot-disk defers to `/api/fleet/orphans` (`_leaked_resources` excludes
    the boot disk — no re-detect). No duplicate surfaces built.
  - **NOTHING COMMITTED** — all changes are in the slot-5 working tree across `deployment-api`, `deployment-service`,
    `deployment-ui`. Next operator step: start deployment-api LIVE (`CLOUD_MOCK_MODE=false`, ADC) + deployment-ui →
    review real values → ship on go-ahead.

- 2026-07-10 — **LIVE-REVIEW FIX (still uncommitted): browser-console crash on service rows.** Operator's live review of
  `:5184` surfaced a React render crash. Root cause: the live inventory folds VM + scheduler + **service** health
  vocabularies into the single `composite_health_status` field, but `compositeHealthLabel` (Deployments.tsx) did an
  **unguarded** `HEALTH_META[h]` lookup — the `ServiceHealth`-only verdicts `serving`/`scaled-to-zero`/`degraded` (14
  live Cloud Run/ECS rows) weren't map keys → `undefined.label` → the whole list white-screened. tsc + pw:L2 were green
  because the mock fixtures only ever put VM verdicts in that field (live-only shape, never exercised). Fix: (1) durable
  — a `healthMeta()` helper with the same `?? gray-fallback` every other lens lookup
  (`kindMeta`/`MODE_TONE`/`statusTone`/ `LaunchedByBadge`) already uses, so ANY future unknown verdict degrades to a
  gray chip instead of crashing (not a per-value hardcode); (2) correctness — added the three known service verdicts to
  `HEALTH_META` for proper colors + widened `composite_health_status` to `VmHealth | ServiceHealth`; (3) regression
  guard — mock now tags a real `serving` + `degraded` service, new `#D.3` pw:L2 asserts they render. Verified: UI QG
  GREEN (tsc/eslint/85 unit/build)
  - **9/9** pw:L2. Files: `deployment-ui/src/pages/Deployments.tsx`, `src/api/deploymentApi.ts`, `src/lib/mock-api.ts`,
    `tests/smoke/deployments-wsd.spec.ts`. Ships with the rest on go-ahead.

- 2026-07-10 — **UX add (uncommitted): in-page "quick guide" help.** Operator asked for a short, readable explainer of
  the page for non-authors. Added `deployment-ui/src/components/DeploymentsHelp.tsx` — a self-contained
  `<DeploymentsHelpButton />` (HelpCircle) placed next to Refresh in the Deployments header; opens a modal (reusing the
  existing `ui/dialog` primitive) with a scannable guide: one-line "what is this", every column's meaning, the
  `launched_by` provenance legend (deployment-api / control-plane / adhoc / unknown), the health verdict legend grouped
  by tone, and a "what to act on" list (stranded cost / adhoc / red health / overdue). Kept short on purpose; legends
  use emoji dots (no import cycle, clears the no-hardcoded-colours gate). Regression spec added (help button opens →
  legend content asserted). Verified: UI QG GREEN + **10/10** pw:L2. Files: `DeploymentsHelp.tsx` (new),
  `src/pages/Deployments.tsx` (import + header button), `tests/smoke/deployments-wsd.spec.ts`.

- 2026-07-10 — **LIVE-REVIEW FIX (uncommitted): Mode + Status filters had incomplete option lists.** Operator flagged
  filters "not working." Audited every filter against live `:8005` (`scratchpad/filter_audit.py`): the filter ENGINE is
  correct — every server-side invariant holds (cloud=GCP→all GCP, status=X→all X, umbrella=X→all X) and the cloud
  partition is exact (GCP 3825 + AWS 11 = 3836). The bug was three option-list gaps: (1) **Mode** dropdown missing
  `NONE` (187 rows = every scheduler + all services/functions/disk/ECS — the whole infra umbrella, unreachable by Mode)
  and `EXPERIMENT` (2); (2) a **hardcoded URL whitelist** `["LIVE","BATCH","PAPER"].includes(urlMode)` that REJECTED
  `NONE`/`EXPERIMENT` even if added (selection snapped back to "all") — the same drift class the operator warned about,
  now derived from `MODE_OPTIONS` so it can't drift again; (3) **Status** dropdown missing `stopped` (48 = orphaned disk
  - 42 stopped schedulers + 3 ECS) and `pending` (15). Fixed all three + 2 pw:L2 guards (Mode NONE/EXPERIMENT sticks;
    Status stopped/pending present). cloud / launched_by / kind / asset_group / status-chips all verified complete. UI
    QG GREEN + **12/12** pw:L2. Files: `deployment-ui/src/pages/Deployments.tsx`, `tests/smoke/deployments-wsd.spec.ts`.

- 2026-07-10 — **Region reconciliation + cockpit UX hierarchy SHIPPED-LOCAL (uncommitted).** All six follow-up todos
  above done + verified live on `:8005`/`:5184`; both repos QG-GREEN + **16/16** pw:L2.
  - **Region selector (API)** — `?region=` on `/deployments/inventory` (`_normalize_region_scope` →
    `_gcp_regions_for_scope` / `_aws_regions_for_scope`; default region byte-identical to the configured census;
    specific region → that GCP region \+ `_GCP_TO_AWS_REGION` equivalent; `all` → sweep) + region-scoped cache key; new
    `GET /deployments/regions` (43 dynamic GCP regions, default pinned). **Live proof**: asia-northeast1 → FN 2 / SVC 12
    / SCHED 170; europe-west1 → FN 1 / SVC 4 / LAMBDA 8 (AWS eu-west-1 equiv); all → FN 4 / SVC 25 / JOB 129 / SCHED 176
    / LAMBDA 18 — the ~50 previously invisible multi-region resources are now reachable.
  - **Region dropdown (UI)** — dynamic `FilterSelect` from `/regions`, default asia-northeast1, server-side `region`
    param.
  - **Status default = running (UI)** — live-first; dropdown + chips reflect it via an explicit `all` sentinel (no
    snap-back); the default view is now **122 running rows** (VM 12 = the real live instances) instead of 3,836, which
    also cures the perceived filter lag (the table is unvirtualised — 30× fewer rows).
  - **Semantic default sort + sortable columns (UI)** — `defaultHierarchyCmp` = STATUS band (running→completed) → KIND
    band (VM → services → jobs → scheduled → functions/lambdas → orphaned) → recency; every non-Controls column header
    click-sorts (asc → desc → back to hierarchy, with a ▲/▼ indicator), overriding the hierarchy.
  - **Filter audit** — engine verified correct (`scratchpad/filter_audit.py`); the earlier Mode(NONE/EXPERIMENT) +
    Status(stopped/pending) option gaps + the URL-whitelist drift were fixed; launched_by/kind/asset_group confirmed
    working (the "slow" perception was the 3,836-row unvirtualised render, now mooted by the running default).
  - Files: `deployment-api/deployment_api/routes/deployments_inventory.py`, `tests/unit/test_multi_region_census.py`;
    `deployment-ui/src/pages/Deployments.tsx`, `src/api/deploymentApi.ts`, `src/lib/mock-api.ts`,
    `src/pages/Deployments.test.tsx`, `tests/smoke/deployments-wsd.spec.ts`. **Still uncommitted — awaiting go-ahead.**

- 2026-07-10 — **AWS default region → Tokyo (ap-northeast-1) [operator correction].** Verified via
  `ec2 describe-instances` that BOTH orchestrator VMs run in ap-northeast-1: the planning VM `agent-orchestrator-vm-1`
  (EIP 13.113.200.22, `i-0c9b283b31d6b5ca7`) + the human-planning VM `agent-orch-human-planning-vm`
  (`i-0dd9812a96cdda5dc`). So `_CONFIGURED_AWS_REGIONS` narrowed from `("ap-northeast-1","us-east-1")` →
  `("ap-northeast-1",)` — the Tokyo default now mirrors where the planning VM + AWS EC2/ECS actually run (default AWS
  view = 2 EC2 + 3 ECS, no lambdas). The us-east-1 Lambda estate (6) is reachable via a US-region selection (GCP
  us-central1/us-east1 → AWS us-east-1) or the all-regions sweep, not the Tokyo default. Live-verified + deployment-api
  QG GREEN. Uncommitted.

### Hand-off to the consolidator-page agent (2026-07-10)

> Deliver this to whoever owns the consolidator/manifest page + plan. It defines the OTHER half of the split above — the
> data-correctness verdict this deployments plan deliberately does NOT re-derive, plus the seam it must expose so the
> deployments detail popover can link to it. Verbatim message is in the chat that produced this entry.

- **What the deployments page will do (so you don't duplicate it):** liveness only — every job/service/VM's existence,
  current status, latest-execution result + `last_run_at`, provenance (`launched_by`), leaked-resource flags, and (new)
  a Cloud-Scheduler-driven "fired on time / OVERDUE" badge. It will NOT walk buckets to verify a run's output.
- **What the consolidator page should own (the gap to audit + fill):** the authoritative per-run **"did this scheduled/
  consolidator run produce the data it was designed for"** verdict — for each run of each job, which partitions/rows it
  should have written vs. what actually landed (`capture_status`/object counts), fired-but-produced-nothing detection,
  and stale-output detection. This is the same manifest SSOT you already own; the ask is to make it **per-job/per-run**
  and **queryable**.
- **The seam the deployments page needs from you:** expose a lightweight lookup keyed by the **FULL Cloud Run job
  short-name** (already the decided join key in `consolidator_throughput_backlog_monitor_2026_07_09` WS-3 — the short
  name encodes `{kind}-{asset_group}`; NOT `asset_group` alone) →
  `{last_run_at, partitions_written, rows_written, expected_vs_actual, verdict}`, so the deployments detail popover can
  cross-link "this run → its produced data" without re-walking.
- **✅ JOIN-KEY CONFIRMED — deployments agent, 2026-07-10 (unblocks the consolidator's WS-3 P1).** Key = the FULL Cloud
  Run job short-name, defined precisely as `run_v2` `job.name.rsplit("/", 1)[-1]` (the last path segment, e.g.
  `prd-manifest-consolidator-cefi`, **verbatim incl. any env prefix, no normalization**) — this is already the
  deployments row `name` (`_cloud_run_item_for_live_job` / `latest_execution_by_job`). **Chosen over the
  `(kind, asset_group)` tuple** because the short-name is the raw shared observable both sides read verbatim from
  `JobsClient.list_jobs` (the tuple would need TWO independent `{kind}-{asset_group}` parses — and the deployments
  classifier is a FUZZY suffix/substring match, `job_name == stem or endswith(f"-{stem}") or stem in job_name`, so the
  two parses would drift → silent missed joins); it's also unambiguous per-run (env-prefix/`-backfill`/`-v2` variants
  collide on the tuple, never on the short-name). Deployments ALSO passes classified `kind` + `asset_group` as
  hint/validation fields, but the CANONICAL index is the short-name. The short-name→(kind,asset_group)→partition decode
  is the CONSOLIDATOR's SSOT (its partitions are already keyed that way). **Multi-region caveat:** a short-name is
  unique within a `(project, region)`; today all `asia-northeast1` so bare short-name is unique — when Plan 2's
  multi-region census lands, qualify the key with region (or use the fully-qualified resource name).
- **NOTE (2026-07-10 cross-plan audit):** this hand-off is ALREADY absorbed —
  `consolidator_throughput_backlog_monitor_2026_07_09` (WS-3) owns the per-run output-production verdict endpoint,
  fired-but-produced-nothing + stale-output detection, and the join-key decision. So the "consolidator agent" = that
  plan; this is coordination, not a fresh ask. Plan 2's only job is to CONSUME the seam.
