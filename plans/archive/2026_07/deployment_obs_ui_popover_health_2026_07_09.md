---
doc_type: plan
title: Deployment observability — kind badges, composite health, resource columns + detail popover (UI)
summary:
  UI half of the deployment-observability expansion — render the full-estate kinds (6 kind badges), the composite VM
  health chip (7-state, 3-tier severity colour) and the service health states, the cpu/mem/disk Resources columns, a
  Kind filter, and a name-click detail popover (sparklines + timeline + absolute used/total + owning consolidator + an
  "Open in GCP/AWS console" deep-link). LOCAL plan — executed interactively in this slot once the backend AO plan
  deployment_obs_backend_kinds_health_2026_07_09 lands the DeploymentItem contract (depends_on documents the ordering).
  Every UI task carries a Playwright L2 regression. Full design + the mock that is the visual contract live in the LOCAL
  parent deployment_observability_expansion_2026_07_08.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui]
scope: [engineer]
tags: [deployment-observability, cockpit, vm-health, ui, deployment-ui, playwright]
related:
  [
    /plans/archive/2026_07/deployment_observability_expansion_2026_07_08.md,
    /plans/archive/2026_07/deployment_obs_backend_kinds_health_2026_07_09.md,
  ]
created: "2026-07-09"
last_updated: "2026-07-09"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: ui-developer
drift_direction: advance-code
depends_on: [deployment_obs_backend_kinds_health_2026_07_09]
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_observability_expansion_2026_07_08.md
---

# Deployment observability — kind badges, composite health, resource columns + detail popover (UI)

> **✅ ARCHIVED 2026-07-13 — COMPLETE.** Every todo shipped (UI `[UI]` + `pw:L2` gated). No deferred items; no new codex
> contract (reuses `/codex/06-coding-standards/ui-testing-layers.md`). Frozen record.

> **LOCAL / human plan** (`assigned_vm: NA`, `execution_scope: local-only` — NOT AO-dispatched, never ingested).
> Executed **interactively in this slot** once the backend AO plan
> **`deployment_obs_backend_kinds_health_2026_07_09.md`** completes (`depends_on` documents the ordering) — the UI is
> visual-iteration-heavy (popover layout, chip colours, sparklines), so it's built here against the mock and wired to
> the real `DeploymentItem` fields the backend ships. Full design context + the mock visual contract live in the LOCAL
> parent **`deployment_observability_expansion_2026_07_08.md`** (read "Where we are" + WS-C + WS-D first). **UI gate:**
> no tick without `[UI]` + `pw:L2 ✓` + a cited regression spec (`/codex/06-coding-standards/ui-testing-layers.md`);
> Python tools are banned in this repo (tsc/ESLint/Vitest/Playwright only).

## Todos

- [x] 1. ✅ [UI] P1. **Kind badges + rich fields** — 6 kinds render (VM · CLOUD_RUN_JOB · CLOUD_RUN_SERVICE ·
      ECS_SERVICE · LAMBDA · CLOUD_FUNCTION); services show Mode="—" (umbrella NONE). — deployment-ui@608d221
      (`ModeBadge` NONE→"—", 8 service fixtures NONE) + @4895925. `pw:L2 ✓` cockpit.spec.ts "all 6 compute kinds render
      kind badges; services show Mode='—'".
- [x] 2. ✅ [UI] P1. **Composite Health column** — chip text = exact state (VM 7-state; service serving/scaled-to-zero/
      dead/degraded), colour = 3-tier severity. — deployment-ui@608d221 (`HEALTH_META`, `serviceHealthLabel`
      desired-vs-running sub-taxonomy). `pw:L2 ✓` cockpit.spec.ts "composite Health column names each VM state + the
      service sub-taxonomy".
- [x] 3. ✅ [UI] P1. **Resources columns** — cpu/mem/disk % colour-coded (amber ≥70, red ≥90, `↑` climbing mem);
      services cpu/mem only, no-sample rows "—". — deployment-ui@608d221 (`ResourceCell`). `pw:L2 ✓` cockpit.spec.ts
      "Resources column shows cpu/mem/disk for VMs; honest '—' for a no-sample row". NOTE: inline scalars need the
      backend to surface `cpu_pct`/`mem_pct`/`disk_pct` on the LIST (currently `/detail`-only) — small backend
      follow-up, flagged in Progress Log.
- [x] 4. ✅ [UI] P1. **Name-click detail panel** — enhances the existing cockpit slide-over: a `WorkHealthCard` served
      by `GET /deployments/{name}/detail` (cpu/mem/disk/io-write/net-recv/workload_alive + composite verdict, honest
      point-in-time note; "VM-only" for kinds without /proc), plus structural service fields (tasks running/desired,
      revision, runtime, memory) in the Target card. — deployment-ui@4895925 (`getDeploymentDetail`, mock `/detail`
      handler). `pw:L2 ✓` cockpit.spec.ts "name-click detail panel shows the /detail work-health vector" + "a service
      shows structural task counts + no /proc vector".
- [x] 5. ✅ [UI] P1. **Console deep-link** — `consoleUrl()` builds the GCP/AWS console URL per kind (GCE
      instancesDetail, EC2 instances search, Cloud Run job+service, ECS cluster/service, Lambda function, Cloud
      Function); rendered in the detail header. — deployment-ui@4895925. `pw:L2 ✓` cockpit.spec.ts "console deep-link is
      built per kind (GCE VM vs ECS service)". (EC2 uses a name-search URL — instance-id not on the contract; a backend
      `instance_id` field would make it exact.)
- [x] 6. ✅ [UI] P2. **Kind filter** dropdown next to Mode/Cloud/Status/asset-group (client-side) — finds services
      despite Mode="—". — deployment-ui@4895925 (`kindFilter` + `filter-kind` select). `pw:L2 ✓` cockpit.spec.ts "Kind
      filter isolates a single kind".

## Progress Log

- 2026-07-09 — **UI PLAN COMPLETE** — all 6 todos shipped (deployment-ui@608d221 contract alignment + @4895925
  detail/console/filter), QG green, full cockpit playwright spec 36 passed (incl. 7 new pw:L2). Two backend follow-ups
  surfaced for when the estate is wired to the live API (NOT blocking the UI): (1) surface
  `cpu_pct`/`mem_pct`/`disk_pct` summary scalars on the LIST `DeploymentItem` so the inline Resources column has data
  (currently `/detail`-only — the UI reads them optionally, shows "—" until then); (2) add an EC2 `instance_id` field so
  the VM console deep-link is exact (uses a name-search URL today). Both belong in the backend plan
  `deployment_obs_backend_kinds_health_2026_07_09.md`.
- 2026-07-09 — Created as a LOCAL plan (operator decision: do the UI here interactively, not on AO). Held until the
  backend AO plan completes and posts the frozen `DeploymentItem` contract sha here, so the UI wires against a real
  contract. The mock in `deployment_observability_expansion_2026_07_08.md` § "Where we are" is the visual target and
  already lives in this slot's `deployment-ui` working tree.
- 2026-07-09 — **STARTED (operator go-ahead despite AO not firing the handoff task).** Backend AO plan is 18/23; the
  three UI-critical items ALL landed: `DeploymentItem` contract + `composite_health_status` (deployment-api@9353d28
  area)
  - `/deployments/{id}/detail` (`DeploymentDetailResponse`, deployment-api@7c4265a). **Frozen contract** =
    `deployment-api/deployment_api/routes/deployments_inventory.py:176` (`DeploymentItem`) + `:237`
    (`DeploymentDetailResponse`). **Two reconciliations to honour when wiring:** (1) the D.1 metrics vector
    (cpu/mem/disk/slope/io/net/workload_alive) lives on `/detail`, NOT the thin list — inline Resources column needs 3
    summary scalars (`cpu_pct`/`mem_pct`/`disk_pct`) added to `DeploymentItem` (small backend follow-up; recommended
    over moving the glance into the popover); (2) service metrics are STRUCTURAL
    (`desired_count`/`running_count`/`task_definition_revision`, `revision`/`region`,
    `runtime`/`memory_size_mb`/`package_type`) not latency (req/min/p99/error_rate mock fields are dropped). Building
    against the mock with field names aligned to this contract so wiring is a no-op.
