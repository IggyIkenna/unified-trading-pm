---
doc_type: plan
title: Full-estate deployment visibility — unmanaged VMs, launched-by provenance, leaked-resource + cost catch
summary:
  Extend the deployment cockpit from "our managed fleet" to the WHOLE cloud estate — every VM / Cloud Run / Lambda / ECS
  / disk / IP that is running or recently ran, across every region, whether or not deployment-api launched it. Add a
  `launched_by` provenance column (deployment-api vs ad-hoc) so agent/operator ad-hoc launches are findable and can be
  pulled into the stack; flag any non-running VM that still holds unreleased disks / static IPs (leaked cost) in red and
  sort those directly after the running VMs; and audit for completeness so nothing billable-and-running (even under
  credits) is invisible. Motivated by a live diff finding 3 running GCE VMs invisible in the cockpit today (incl. a
  16-day-old zombie-watchdog). Builds on the census + composite-health plan
  (deployment_obs_backend_kinds_health_2026_07_09).
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

## Todos

### Full estate + `launched_by` provenance (see everything + who launched it)

- [ ] [BACKEND] P0. **Full GCE VM census** — union the deployment registry with the live GCE aggregated-list so EVERY
      live GCE instance gets a row, not just registry-tracked ones. Un-registered instances become `unmanaged` rows
      carrying their live GCE state (`RUNNING`/`STOPPED`/`TERMINATED`). Reuses `get_vm_instance_details` (already
      fetched every census cycle — no new API call); the registry entry, when present, enriches the row
      (task/mode/heartbeat/ D.1 metrics) exactly as today. Surfaces the 3 unmanaged VMs found 2026-07-09.
- [ ] [BACKEND] P0. **`launched_by` provenance field** on `DeploymentItem` (UAC) — `deployment-api` when the resource
      has a registry entry, else `adhoc`. Wire for GCE VMs + AWS EC2 (already full census — cross-ref the registry) +
      Cloud Run jobs (registry-hint match) + services/functions. Optional `managed_by_label` echo once the launcher
      label standardization (below) lands, so drift (label-present-but-no-registry, or vice-versa) is detectable.
- [ ] [REVIEW] P1. **Confirm the full-census + provenance is consistent across clouds** — AWS EC2 is already a full
      `describe_instances` census, GCP VMs become one here; Cloud Run/services/functions/ECS/Lambda are already full
      censuses. Verify every kind resolves `launched_by` honestly (never a fabricated `deployment-api`), and a
      registry-only archived VM with no live cloud instance still classifies `dead` (not `adhoc`).

### 🔴 Leaked / unreleased resources on non-running VMs (the direct cost catch)

- [ ] [BACKEND] P0. **Leaked-resource detection** — for any VM NOT in `RUNNING` state (terminated/stopped/dead), detect
      attached-but-not-released resources: (a) persistent disks that still exist (boot + data disks — reuse
      `get_disk_details`/`list_unattached_disk_names`), (b) reserved **static IPs** (a new `addresses.aggregated_list`
      read). Surface `has_unreleased_resources: bool` +
      `unreleased_resources: list[{type, name, size_gb, disk_type,     est_monthly_usd}]` on `DeploymentItem`. Honest
      absence when the read fails (never a false "clean").
- [ ] [UI] P0. **Red "Unreleased resources" column/badge** on non-running VMs listing the leaked disks/IPs (+ est.
      monthly cost); click → the detail popover shows each resource with the exact console link + release guidance.
      `pw:L2` regression: a stopped VM with a lingering disk shows the red badge; a cleanly-torn-down VM does not.
- [ ] [UI] P0. **Sort order — running first, then leaked, then the rest.** Default cockpit ordering: `RUNNING` VMs →
      non-running-WITH-unreleased-resources (the red rows, so they're spotted immediately) → everything else (clean
      terminated/archived). `pw:L2` regression pins the three-band order.

### Region + kind completeness (nothing running is invisible)

- [ ] [BACKEND] P1. **Multi-region census** — Cloud Run jobs/services + Cloud Functions census only `asia-northeast1`
      today, and AWS only one region; a resource in any other region is invisible. Fan the censuses out across every
      region we actually use (discover dynamically, or a config'd region set) with per-region honest degradation.
- [ ] [BACKEND] P1. **Orphaned disks + unattached static IPs as first-class rows** — a persistent disk or reserved IP
      with NO owning VM at all (truly orphaned) still costs money and has no VM row to hang off. Emit them as their own
      inventory rows (`kind=DISK`/`kind=STATIC_IP`, `launched_by=adhoc/unknown`) with size/type + est. cost. Reuses the
      `list_unattached_disk_names` code already in `vm_utils.py`.
- [ ] [BACKEND] P2. **Completeness audit** — enumerate every billable running resource per cloud, existence-based
      (credits-agnostic): GKE clusters/node-pools, Cloud SQL, Dataflow/Composer, AWS RDS / EBS volumes / NAT gateways /
      Elastic IPs. Diff against the tab; add the materially-costly missing kinds as census rows (or file the rest as a
      follow-up with the measured $/month each). Deliverable: a one-shot report of "running-but-invisible" per cloud.

### Provenance robustness (drift-proof the signal)

- [ ] [DEVOPS] P1. **Standardize a `managed-by=deployment-service` label/tag on every launcher** — GCP `--labels` + AWS
      tags across all `deployment-service/scripts/vm/launch-*.sh` (today labels are inconsistent: `purpose=`/`env=` but
      no uniform `managed-by`). Then any cloud resource WITHOUT the label is provably ad-hoc, catching even the
      registry-write race window. Edit via the launcher template if one exists, not per-copy.

### UI surfacing

- [ ] [UI] P1. **"Launched by" column + "unmanaged" filter** — a one-click view of every ad-hoc resource so stranded
      compute is immediately findable. `pw:L2` regression: the filter isolates `launched_by=adhoc` rows.
- [ ] [UI] P2. **Per-row cost surfacing** — est. monthly $ for the resource + its leaked disks/IPs, and an estate-total
      "stranded cost" number, so the money at stake is visible at a glance. `pw:L2` on the cost cell rendering.

## Progress Log

- 2026-07-09 — Created (LOCAL) from operator direction after the P0 census-hang fix landed and the cockpit went live
  against real data. Motivated by the live GCE diff (3 unmanaged running VMs invisible today, incl. a 16-day
  zombie-watchdog). Scope: full estate (running + recently-ran, all regions) + `launched_by` provenance + the
  leaked-resource red-flag/sort + a completeness audit. Provenance signal confirmed = registry-presence;
  `list_unattached_disk_names`/`get_disk_details` already exist in `vm_utils.py` (idle-disk catch half-built); region
  coverage gap confirmed (Cloud Run/Functions/AWS single-region). Depends on
  `deployment_obs_backend_kinds_health_2026_07_09` (the census + `DeploymentItem` contract it extends).
