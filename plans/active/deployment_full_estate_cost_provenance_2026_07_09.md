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
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, unified-api-contracts]
scope: [engineer]
tags:
  [deployment-observability, cockpit, cost, provenance, unmanaged-vms, leaked-resources, deployment-api, deployment-ui]
related:
  [
    deployment_obs_backend_kinds_health_2026_07_09.md,
    deployment_obs_ui_popover_health_2026_07_09.md,
    deployment_observability_expansion_2026_07_08.md,
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

## Codex SSOTs (READ before touching each area — plan↔codex drift is review-blocking)

- Inventory contract + classification + composite health: `deployment-api/.../routes/deployments_inventory.py`;
  `codex/05-infrastructure/deployment-observability.md`.
- VM launchers + labels/tags (provenance): `deployment-service/scripts/vm/launch-*.sh`;
  `codex/05-infrastructure/vm-launcher-runbook.md`, `…/vm-tarball-deployment.md`.
- GCE resource reads (disks/IPs already partly built): `deployment-api/deployment_api/vm_utils.py`
  (`get_vm_instance_details`, `get_disk_details`, `list_unattached_disk_names`).
- Shard-level failure isolation (per-kind/region honest degradation):
  `codex/04-architecture/shard-level-failure-isolation.md`.
- UI testing layers: `codex/06-coding-standards/ui-testing-layers.md`.

## Existing surfaces to REUSE — audited 2026-07-10 (do NOT rebuild these)

A live audit of the deployment-ui cockpit found **three already-built surfaces this plan overlaps**. Extend/reuse them;
building parallel duplicates is review-blocking.

1. **`FleetOrphans` (`GET /api/fleet/orphans`, `FleetOrphansContent`, Fleet tab)** — already renders stopped/terminated
   VMs with **boot-disk GB + $/mo**, a **reap verdict** (`reap`/`keep_within_grace`/`keep_not_ephemeral`/
   `keep_retained`/`keep_no_timestamp`), rollup cards (**Idle disk $/mo**, **Reclaimable $/mo**), and **bulk-reap
   (dry-run first) + per-instance delete** (`POST /api/fleet/reap`, `DELETE /api/fleet/instances/{name}`). This ALREADY
   covers most of the leaked-boot-disk cost catch. **Genuine gaps to target:** data disks / regional PDs (only the boot
   disk today), **static IPs** (none), **truly-orphaned disks/IPs with no owning VM** (it's VM-keyed), and surfacing the
   leak as a **red badge on the Deployments inventory row + the running→leaked→rest sort** (today it's a Fleet-tab-only
   panel).
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

- [ ] [BACKEND] P0. **Full GCE VM census** — union the deployment registry with the live GCE aggregated-list so EVERY
      live GCE instance gets a row, not just registry-tracked ones. Un-registered instances become `unmanaged` rows
      carrying their live GCE state via the EXISTING `health_status` field (`RUNNING`/`STOPPED`/`TERMINATED`). Reuses
      `get_vm_instance_details` (already fetched every census cycle — no new API call); the registry entry, when
      present, enriches the row (task/mode/heartbeat/D.1 metrics) exactly as today. **Reuse the reconciliation union**
      (`GET /api/fleet/reconciliation` already computes registry-vs-live "unknown"/"expected-missing") as the same
      source — don't build a second union. Surfaces the 3 unmanaged VMs found 2026-07-09.
- [ ] [BACKEND] P0. **`launched_by` provenance field** on the LOCAL `DeploymentItem` BaseModel (+ its TS mirror
      `deployment-ui/src/api/deploymentApi.ts` — NOT UAC) — `deployment-api` when the resource has a registry entry,
      else `adhoc`, sourced from the SAME registry-vs-live union reconciliation uses (a VM in reconciliation's `unknown`
      set → `adhoc`). Wire for GCE VMs + AWS EC2 (already full census — cross-ref the registry) + Cloud Run jobs
      (registry-hint match) + services/functions. `managed_by_label` is a trivial echo of the already-present `labels`
      field once launcher-label standardization (below) lands, so drift (label-present-but-no-registry, or vice-versa)
      is detectable.
- [ ] [REVIEW] P1. **Confirm consistency across clouds AND no-duplication of existing surfaces** — AWS EC2 is already a
      full `describe_instances` census, GCP VMs become one here; Cloud Run/services/functions/ECS/Lambda are already
      full censuses. Verify every kind resolves `launched_by` honestly (never a fabricated `deployment-api`), and a
      registry-only archived VM with no live cloud instance still classifies `dead` (not `adhoc`). **Also verify reuse,
      not rebuild:** the census union == the reconciliation union (`/api/fleet/reconciliation` `unknown` count ==
      Deployments `launched_by=adhoc` count), and leaked-boot-disk detection defers to `/api/fleet/orphans` rather than
      re-detecting it (a discrepancy is a review-blocking bug, not a display quirk).

### 🔴 Leaked / unreleased resources on non-running VMs (the direct cost catch)

- [ ] [BACKEND] P0. **Leaked-resource detection — the gaps FleetOrphans does NOT cover.** The boot-disk-on-stopped-VM
      leak + $/mo + reap is ALREADY done by `GET /api/fleet/orphans` (reuse it, don't re-detect boot disks). Add the
      missing dimensions: (a) **data disks / regional PDs** still attached to a non-`RUNNING` VM (orphans shows boot
      only — reuse `get_disk_details`/`list_unattached_disk_names`), (b) reserved **static IPs** (a new
      `addresses.aggregated_list` read). Surface `has_unreleased_resources: bool` +
      `unreleased_resources: list[{type, name, size_gb, disk_type, est_monthly_usd}]` on the local `DeploymentItem`.
      Honest absence when the read fails (never a false "clean").
- [ ] [UI] P0. **Red "Unreleased resources" badge ON the Deployments inventory row** (the net-new vs. the Fleet-tab
      orphans panel) — non-running VMs carrying leaked disks/IPs show a red badge (+ est. monthly cost) right where the
      operator scans the fleet; click → the detail popover lists each resource with the exact console link + release
      guidance (link the existing orphans reap/delete action where the VM overlaps). `pw:L2` regression: a stopped VM
      with a lingering disk shows the red badge; a cleanly-torn-down VM does not.

### Region + kind completeness (nothing running is invisible)

- [ ] [BACKEND] P1. **Multi-region census** — Cloud Run jobs/services + Cloud Functions census only `asia-northeast1`
      today, and AWS only one region; a resource in any other region is invisible. Fan the censuses out across every
      region we actually use (discover dynamically, or a config'd region set) with per-region honest degradation.
- [ ] [BACKEND] P1. **Orphaned disks + unattached static IPs as first-class rows** — a persistent disk or reserved IP
      with NO owning VM at all (truly orphaned) still costs money and is INVISIBLE in FleetOrphans (which is VM-keyed).
      Emit them as their own inventory rows (`kind=DISK`/`kind=STATIC_IP`, `launched_by=adhoc/unknown`) with size/type +
      est. cost. Reuses the `list_unattached_disk_names` code already in `vm_utils.py`. (New kinds → the UI-registration
      todo below must register them or they render un-iconed/un-filterable.)
- [ ] [BACKEND] P2. **Completeness audit** — enumerate every billable running resource per cloud, existence-based
      (credits-agnostic): GKE clusters/node-pools, Cloud SQL, Dataflow/Composer, AWS RDS / EBS volumes / NAT gateways /
      Elastic IPs. Diff against the tab; add the materially-costly missing kinds as census rows (or file the rest as a
      follow-up with the measured $/month each). Deliverable: a one-shot report of "running-but-invisible" per cloud.

### Scheduled-job liveness — "did it fire? on time?" (deployments = liveness lens; "did it produce data" is the consolidator's, see hand-off)

- [ ] [BACKEND] P1. **Cloud Scheduler census (new kind)** — the "fired at the right time?" signal has NO source today: a
      Cloud Run job row shows only its latest _execution_ time, never its _expected_ fire time, and we read Cloud
      Scheduler nowhere (grep-confirmed). Add a Cloud Scheduler census (schedule cron + `last_attempt_time` +
      `last_attempt_status`), join it to the Cloud Run job / target it triggers, and surface an **OVERDUE badge** when
      the last fire is later than `schedule + grace` (or the last attempt FAILED). Honest per-region degradation like
      the rest. This is the ONLY honest source of the on-time signal — execution timing alone cannot answer it.
- [ ] [BACKEND] P1. **Fix the Lambda `last_run_at` honesty gap** — `_lambda_item` currently sets
      `last_run_at = fn.last_modified` (the last _deploy_ time, silently mislabeled as run-time). Relabel to
      `last_modified_at` semantics; the real last-invocation needs CloudWatch (`GetMetricStatistics` Invocations) — wire
      it or mark last-run honestly-absent for Lambda. **Never** present deploy-time as run-time.
- [ ] [BACKEND] P2. **Job run-history in the detail popover** — extend the job detail vector to carry the last N
      executions (start/end time + status + duration), not just the latest, so "did it fire on its cadence" is
      answerable by eye. Reuses `list_executions` (already called in `latest_execution_by_job`; raise `page_size` from 1
      for the detail path only — the list path stays at 1, no new cost).
- [ ] [BACKEND/UI] P2. **Job → manifest bridge (link + hint only, NOT the verdict)** — on a job row's detail popover,
      cross-link to that job's asset_group manifest/consolidator partition and show a lightweight "rows since last run"
      delta reusing the batched `object_delta` lookup already built (no new walk). The **authoritative** "did the data
      land / is it correct" verdict lives on the consolidator page (see hand-off) — this is a link + a hint, so a red
      "fired-but-produced-nothing" is spotted from deployments but confirmed on the consolidator. **DEPENDS ON** the
      consolidator agent exposing a per-job/per-asset_group "last run → partitions+rows written" surface keyed by the
      same job identity.

### Provenance robustness (drift-proof the signal)

- [ ] [DEVOPS] P1. **Standardize a `managed-by=deployment-service` label/tag on every launcher** — GCP `--labels` + AWS
      tags across all `deployment-service/scripts/vm/launch-*.sh` (today labels are inconsistent: `purpose=`/`env=` but
      no uniform `managed-by`). Then any cloud resource WITHOUT the label is provably ad-hoc, catching even the
      registry-write race window. Edit via the launcher template if one exists, not per-copy.

### UI surfacing

- [ ] [UI] P1. **"Launched by" column + "unmanaged" filter** — add `launched_by` to `UNIFIED_COLUMNS` and a new filter
      mirroring the existing client-side `kind` filter, for a one-click view of every ad-hoc resource so stranded
      compute is immediately findable. `pw:L2` regression: the filter isolates `launched_by=adhoc` rows.
- [ ] [UI] P1. **Render the new signals + kinds the census now emits (nothing new renders un-styled).** Three UI wirings
      the backend todos above imply but that have no home today: (a) **register the new kinds** — add `DISK`,
      `STATIC_IP`, and the Cloud-Scheduler kind to `KIND_META` (icon/label/tone) + the `kind` filter dropdown, else they
      render un-iconed and can't be filtered; (b) **OVERDUE / fired-on-time indicator on job rows** — job rows show NO
      health chip today (the `Health` column is null for non-service/non-live-VM kinds), so slot the scheduled-job
      on-time verdict there (or a dedicated schedule chip); (c) **job run-history timeline** in the `DeploymentDetail`
      popover from the last-N executions the detail vector now carries. `pw:L2` on each: a DISK row renders its kind
      chip; an overdue job shows the red OVERDUE chip; the detail popover lists >1 execution.
- [ ] [UI] P1. **Default sort — running → leaked → the rest (net-new; the table has no client-side sort today).** The
      inventory renders items in server order currently; add a client-side comparator in `DeploymentsContent`/
      `DeploymentMatrix`: `RUNNING` → non-running-WITH-unreleased-resources (red rows spotted immediately, per operator
      ask) → everything else. `pw:L2` regression pins the three-band order.
- [ ] [UI] P2. **Leaked-cost surfacing (per-row cost already renders)** — the `Cost/day` column off `cost_per_day_usd`
      already exists, so the net-new is: the **leaked disk/IP monthly $** on the red unreleased-resources badge, and an
      **estate-total "stranded cost"** number (sum of leaked + orphaned rows) so the money at stake is visible at a
      glance. Reuse the orphans endpoint's `monthly_idle_usd`/`monthly_reapable_usd` rollup where the VM overlaps.
      `pw:L2` on the stranded-total + leaked-cost cell rendering.

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
- **The seam the deployments page needs from you:** expose a lightweight lookup keyed by the SAME job identity (short
  Cloud Run job name / asset_group) → `{last_run_at, partitions_written, rows_written, expected_vs_actual, verdict}`, so
  the deployments detail popover can cross-link "this run → its produced data" without re-walking. Agree the join key
  with this plan (Cloud Run job short-name ∪ asset_group) before building.
