---
doc_type: plan
title: Deployment observability — full-estate kinds + rich per-target data + VM work-health
summary:
  Expand the merged Deployments cockpit tab from liveness-only VM/job observability into a full-estate, work-aware
  monitoring surface. Census the compute kinds the backend ignores today (Cloud Run services, ECS/Fargate services,
  Lambda, Cloud Functions, off-registry Cloud Run jobs), enrich every target with rich GCP/AWS data
  (machine/zone/cost/utilisation), and replace heartbeat-only VM health with a composite work-health model (cpu/mem/disk
  + workload-PID liveness + progress delta + bucket cross-check) so "alive but idle / OOM-dead" stops slipping through.
  Mock-first is done; this plan wires the real API + UI to match the mock.
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, deployment-api, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [deployment-observability, cockpit, vm-health, cloud-run, ecs, lambda, cost, mock-first, heartbeat]
related:
  [
    cost_observability_ui_2026_07_08.md,
    deployment_observability_parity_live_batch_paper_2026_06_22.md,
    deployment_obs_backend_kinds_health_2026_07_09.md,
    deployment_obs_ui_popover_health_2026_07_09.md,
  ]
created: "2026-07-08"
last_updated: "2026-07-08"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 14
estimate_calibrated_ai_days: 11
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: infra
drift_direction: advance-code
---

# Deployment observability — full-estate kinds + rich per-target data + VM work-health

> **LOCAL / human plan** (`assigned_vm: NA`, executed in an interactive session — NOT auto-dispatched). Mock-first: we
> iterate the look in `deployment-ui` mock mode, then wire the real API + UI to match. This doc is the capture point for
> the whole workstream + the open design questions — keep it current.

## Where we are (2026-07-08)

- **Merged Deployments tab — SHIPPED.** live/batch/paper collapsed into ONE flat all-modes table (Mode is a filter, not
  tabs); 3 cockpit tabs + 3 health tiles + 3 nav entries consolidated; bad columns killed (phantom Uptime, dup
  Heartbeat, Progress/Coverage dupe, paper Recon-drift/Determinism-ε placeholders). Evidence: `deployment-ui@50a6947` on
  `live-defi-rollout` (tsc + eslint + 915 vitest + coverage 75.98% + playwright smoke green).
- **Richer-estate mock — DONE (uncommitted).** In `deployment-ui` mock mode the Deployments table now shows all 6
  compute kinds + rich per-target data (Kind column, machine·zone subtitle, Cost/day, kind-aware Health, uptime for
  services). This is the visual TARGET the real API+UI must match. Files touched (not yet committed):
  `src/api/deploymentApi.ts` (kind union + optional rich fields), `src/lib/mock-api.ts` (18-row estate w/ real census
  names), `src/pages/Deployments.tsx` (Kind/Cost columns, kind-aware Health), `src/index.css` (table cell gutters — the
  unlayered `* { padding: 0 }` reset kills Tailwind `pr-*` on cells).

## The gap this plan closes (live census 2026-07-08, via gcloud/aws)

deployment-service can DEPLOY to GCP VM · Cloud Run (jobs+services) · AWS EC2 · Batch/Fargate · ECS · local, but the
classification contract is only `DeploymentKind = {VM, CLOUD_RUN_JOB}` and the inventory route censuses only 4 things.
What is RUNNING but INVISIBLE in the tab:

| Kind                                           | Live now              | In tab? | Note                                                                                                      |
| ---------------------------------------------- | --------------------- | ------- | --------------------------------------------------------------------------------------------------------- |
| GCP Cloud Run **services**                     | ~25 ready             | ❌      | Always-on prod: deployment-api, market-data-query, dashboards, alerting, quota-broker, data-status-rollup |
| AWS **ECS/Fargate services**                   | 3 defined (DeFi exec) | ❌      | uts-{strategy,features,execution}-service-prod (0 tasks now, invisible when they scale)                   |
| GCP Cloud Run **jobs** off the static registry | ~10-15 of ~48         | ⚠️      | market-tick-cefi-…, paper-trading-engine, oddspapi-…, tardis-data-loader                                  |
| AWS **Lambda**                                 | 6                     | ❌      | Portal/auth + ses-email-forwarder                                                                         |
| GCP **Cloud Functions** gen2                   | 4                     | ❌      | trigger-… (Cloud Run underneath)                                                                          |

Supported + running (no gap): GCP GCE VMs (10) · AWS EC2 incl. orchestrators (12) · AWS Batch queue (idle) · registered
Cloud Run jobs.

## Codex SSOTs (READ before touching each area — plan↔codex drift is review-blocking)

- Deployment inventory contract + classification: `deployment-api/.../routes/deployments_inventory.py`
  (`DeploymentItem`, `classify_deployment_target`, `CLOUD_RUN_JOBS`, AWS census seam).
- Deployment observability / VM tarball / no-fire-and-forget: `codex/05-infrastructure/deployment-observability.md`,
  `…/vm-tarball-deployment.md`.
- Heartbeat daemon + wrapper: `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`,
  `deployment-service/deployment_service/vm/heartbeat_cli.py`, `unified_trading_library.lifecycle`.
- Availability manifest / honest-absence (bucket ground-truth cross-check):
  `codex/02-data/availability-manifest-and-data-status.md`.
- Cost/billing (cost-per-target reuse): `codex/05-infrastructure/billing-cost-observability.md`,
  `cost_observability_ui_2026_07_08.md`.
- UI testing gate (playwright L2): `codex/06-coding-standards/ui-testing-layers.md`.

---

## Phasing — v1 NOW (cheap + already-available), high-blast-radius work LAST

**v1 = wire only what's cheap, free, and CENTRAL (no per-workload changes)** — and it already yields a real work-health
signal, because the two hardest pieces exist as free data:

- **Resource stats** — `/proc` sampling in the ONE heartbeat daemon (cpu/mem/disk/net) + `kill -0 CMD_PID`. 1-2 files,
  no per-workload change, $0.
- **Write-truth** — the manifest (`record_captured`, ALREADY written by every data workload), read per-target via the
  existing `/freshness` endpoint extended to an object-count-delta. No new bucket walk, no per-workload change.
- **Existence / hang** — the control-plane list APIs already called; **OOM cause** from exit-137.
- **Progress hint** — keep the existing log-scraped `rows_out` as a soft corroborator (free, already there).
- **Tier-0 fields** (WS-C) already fetched-and-discarded (machine/zone/rows/uptime) — just surface them.
- **Kinds census** (WS-B) — control-plane list APIs (central, no per-workload change).

**So v1 = WS-B + WS-C (free tier) + WS-D (minus the Cloud-Run cgroup), all central. Do this now.**

**LAST phase (nice-to-have, high blast radius) = WS-H** — typed structured progress reporting per service (retire the
log-scrape). Deferred deliberately: the v1 signal is good enough, and it touches ~8-10 services. Graceful fallback (the
daemon reads structured-progress-when-present, else the log-scrape) means it rolls out per-service with nothing breaking
— do it only as teams touch each service.

## WS-A — Merge live/batch/paper into one Deployments tab ✅ DONE

- [x] 1. ✅ [UI] P0. Collapse the 3 mode tabs + tiles + nav into one unified all-modes Deployments table (Mode =
      filter); kill the bad columns — `deployment-ui@50a6947` + QG green (915 vitest, pw smoke).

## WS-B — Census the compute kinds the backend ignores (make the mock real) ✅ COMPLETE

> **✅ WS-B EXTRACTED + COMPLETE** in `deployment_obs_backend_kinds_health_2026_07_09` (Plan 1, backend). Boxes mirrored
> here 2026-07-10 (cross-plan audit) — Plan 1 carries the per-item shas/evidence.

- [x] ✅ [BACKEND] P1. Add `CLOUD_RUN_SERVICE` to the census (list + ready-state + revision + region; Mode "—"). — done
      in Plan 1.
- [x] ✅ [BACKEND] P1. Add `ECS_SERVICE` census (desiredCount + runningCount + task-def revision, always-emit). — done
      in Plan 1.
- [x] ✅ [BACKEND] P1. Make the Cloud Run **jobs** census DYNAMIC (list live jobs, registry = hints only). — done in
      Plan 1.
- [x] ✅ [BACKEND] P2. Add `LAMBDA` census (existence + config; CloudWatch deferred). — done in Plan 1.
- [x] ✅ [BACKEND] P2. Add `CLOUD_FUNCTION` (gen2) census. — done in Plan 1.
- [x] ✅ [BACKEND] P1. Extend `DeploymentKind` + inventory kind counts/filters to the 6 kinds (honest degradation). —
      done in Plan 1.

## WS-C — Richer per-target data + drill-down (mostly ✅ COMPLETE)

> Backend rich-fields done in Plan 1; UI popover/console/kind-filter done in
> `deployment_obs_ui_popover_health_2026_07_09` (UI-popover). Two items remain OPEN (below): cost-per-target
> (WS-E/cost-plan-owned) and the P3 error-count drill-down.

- [x] ✅ [BACKEND] P1. Surface the **Tier-0 free wins** (machine_type/zone/labels/boot-disk/rows_in/error/uptime already
      fetched). — done in Plan 1.
- [x] ✅ [DATA] P2. Cost-per-target join (see WS-E) → three USD figures on each item. — DONE 2026-07-13, built HERE in
      the deployments tab (operator: USD-only, no currency toggle — GCP is GBP→USD-converted server-side).
      deployment-api@7489d57 (`per_resource_daily` reuses the CACHED billing window; `_attach_costs` joins by
      name==resource_id, honest None, never breaks the census) + deployment-ui@599a644 (`CostCell`: actual / 7d-avg /
      24h-projected; pw:L2 `deployments-cost-cell.spec.ts`).
- [x] ✅ [BACKEND] P2. Utilisation (cpu/mem/disk per target) from WS-D edge-push. — done in Plan 1 (UI Resources columns
      in UI-popover).
  - ~~[BACKEND] P3. Recent error count / last log line (drill-down).~~ **REMOVED 2026-07-13 (operator)** — redundant:
    the full teed GCS log is already shown in the detail popover on name-click. No action.
- [x] ✅ [UI] P1. **Name-click detail popover** (deep fields: sparklines + timeline + rows/object-delta + owning
      consolidator). — done in UI-popover (`WorkHealthCard`).
- [x] ✅ [UI] P1. **Console deep-link** in the popover (GCE/EC2/Cloud Run/ECS/Lambda URLs from fetched fields). — done
      in UI-popover (`consoleUrl()`).
- [x] ✅ [UI] P2. **Kind filter** dropdown (isolate services vs jobs vs VMs). — done in UI-popover.
- [x] ✅ [REVIEW] P2. Rich-field shape on the wire contract — landed on the LOCAL `DeploymentItem` BaseModel (NOT UAC;
      it's `# CORRECT-LOCAL`), so the UI type + wire match. — done in Plan 1.

## WS-D — VM / job WORK-health (not just liveness): capture → store → API → UI

> **Problem.** The heartbeat carries liveness + work-counters (rows_in/out/error, events) but **ZERO resource metrics**,
> and the heartbeat **daemon is decoupled from the workload** (`vm-exec-with-gcs-tee.sh`) — so a workload that OOM-dies
> keeps "running" while the daemon heartbeats. We've had to send agents to eyeball VMs to see if data is actually
> landing. This WS makes "is it actually doing its job?" a first-class, automated signal.

### D.0 Design principles (every task below inherits these)

1. **A verdict is a JOINT function** — resource-in-band **AND** a work signal advancing. Neither alone: CPU 100% can be
   healthy crunching or a GC death-spiral; CPU 5% can be idle-stuck or legitimate I/O-wait; rows_out "advancing" means
   nothing if no objects actually land in the bucket.
2. **The self-logged counters are a HINT, not truth.** They are log-scraped — `parse_counters`
   (`unified_trading_library/lifecycle/counters.py`) greps the last 2000 log lines for `rows_out=N` / `counters={…}` and
   takes MAX. So: a silent workload → 0 (looks stuck), format drift → breaks, a chatty log → the value scrolls out of
   the tail and REGRESSES. Treat rows_out-delta as corroboration; make **object-write delta the authoritative progress
   signal**.
3. **Push from the EDGE, don't pull per-request.** Each VM samples its OWN `/proc` locally (µs, <0.1% CPU) and rides the
   heartbeat it already writes → scales for free (N producers in parallel, zero central query).
4. **Existence from the control-plane list we ALREADY call**, metrics from edge-push, write-truth from the manifest,
   post-mortem from the exit code. **No Cloud Monitoring / CloudWatch** — not used today (only in Terraform for infra
   alarms), GCE has no Ops Agent anyway, and the list APIs + exit-137 already give existence + OOM cause.
5. **Add ZERO new bucket walks** (single-walk HARD RULE) — object-delta is a LOOKUP into the manifest the consolidator
   already maintains. This is the macro/micro split: Consolidators tab = "is the index fresh per asset_group?";
   Deployments health = "is THIS shard advancing?" — two altitudes of one write-path truth.

### D.1 The universal metric vector (normalise across kinds so the verdict + UI don't branch)

Sampled at the edge each heartbeat, stamped onto the registry entry:

| field            | VM source (`/proc`, free)    | Cloud Run source               | meaning                                     |
| ---------------- | ---------------------------- | ------------------------------ | ------------------------------------------- |
| `cpu_pct`        | `/proc/stat` delta           | cgroup `cpu.stat` (opt)        | are calculations happening                  |
| `mem_pct`        | `/proc/meminfo` MemAvailable | cgroup `memory.current ÷ .max` | OOM headroom (host RAM vs container limit)  |
| `mem_slope`      | trend over last N samples    | same                           | OOM PREDICTION (sustained climb)            |
| `disk_pct`       | `statvfs`                    | n/a                            | writes fail silently when full              |
| `io_write_rate`  | `/proc/diskstats` delta      | (bucket-delta proxy)           | "writing output?"                           |
| `net_recv_rate`  | `/proc/net/dev` delta        | n/a                            | "stream flowing?" (dead websocket = 0)      |
| `work_delta`     | rows_out delta (hint)        | —                              | counter moving (soft, log-scraped)          |
| `object_delta`   | manifest lookup              | manifest lookup                | **objects actually landed (authoritative)** |
| `workload_alive` | `kill -0 CMD_PID`            | execution running              | process not dead under a live daemon        |

### D.2 Capture → Store → API → UI (the data path)

- **CAPTURE.** VM: the existing heartbeat daemon loop (`heartbeat_cli`) adds a `/proc` sampler + `kill -0 CMD_PID` (the
  shell passes `CMD_PID` in) each tick. Cloud Run: existence + exit from the control-plane list; live cpu/mem deferred
  (open Q — cgroup self-push later). Fix `parse_counters` to seek-to-tail (read the last ~64 KB, not `read_text()` on a
  multi-GB log every tick).
- **STORE.** Enrich the GCS registry entry (`DeploymentRegistryEntry`) with the D.1 vector + a **short rolling window**
  (last ~10 samples) so `mem_slope` / "sustained idle" have a trend, not a point. No new store — it's the registry JSON
  the inventory route already reads.
- **API.** `object_delta` + `hung` are derived SERVER-side in the inventory route by joining the registry entry with (a)
  the manifest freshness (`/freshness`, extended to an object-count-delta per shard) and (b) the control-plane existence
  list already fetched. `_vm_status` → the composite (D.3). The thin list carries the composite + headline numbers; a
  `/deployments/{id}/detail` endpoint serves the rolling window for the drill-down.
- **UI.** Deployments **Health** column = the composite (not fresh/stale), colour-coded so `stalled` / `oom-risk` /
  `workload-dead` jump out. Drill-down: cpu/mem/disk sparklines + rows_out-delta + object-delta + which consolidator
  owns the shard. Alerts fire on `oom-risk` BEFORE the kill and `stalled` when progress flatlines.

### D.3 Composite health taxonomy (replaces heartbeat-only `_vm_status`)

**VM / job (7-state), keep all 7 — colour by 3-tier severity** (green=working · amber=stalled/oom-risk/disk-full ·
red=workload-dead/hung/dead); the chip TEXT carries the exact state, the COLOUR carries urgency (Open-Q2): `working`
(resource in-band AND (`object_delta`>0 OR `io_write_rate`>0)) · `stalled` (fresh heartbeat, flat `object_delta` + idle
cpu/net — thresholded PER lifecycle_class, Open-Q3) · `oom-risk` (`mem_slope`>0 toward >90%) · `workload-dead` (daemon
alive, PID gone) · `disk-full` (`disk_pct`>90) · `hung` (heartbeat stale + control-plane says RUNNING) · `dead`
(control-plane not running).

**`stalled` threshold table (v1 defaults, Open-Q3)** — progress-metric primary, cpu secondary, NEVER a global CPU cut:
backfill/batch/feature-compute → `object_delta==0` for ≥15 min AND cpu<10% · live-capture/live-trading → no
events/heartbeat-progress ≥5 min during an expected-active window · paper → `work_delta==0` ≥15 min · service → N/A (use
request/error-rate, below).

**Service (Cloud Run service / ECS) sub-taxonomy** — services have no manifest/object-delta, so a SEPARATE state set
(Open-Q7): `serving` (running==desired>0, green) · `scaled-to-zero` (desired==0, neutral — off on purpose) · `dead`
(desired>0 but running==0, RED — should be up, isn't) · `degraded` (error-rate over threshold, amber). Cloud Run service
uses ready-state + revision health in place of desired/running.

### D.4 Scale & cost budget (constrain the impl to the cheap architecture from day one)

- Edge `/proc` sampling: **~$0, <0.1% CPU/VM**, fully distributed — metrics NEVER cost a central query.
- Registry census: the EXISTING 32-worker parallel read + 45 s stale-while-revalidate cache (the >100 s 291-VM timeout
  they already fixed) — one background census, all readers hit the cache.
- Object-delta: manifest LOOKUP, **0 new bucket walks**.
- Control-plane existence: the `aggregated_list` / EC2 / Run-execution calls **already made**.
- **No Cloud Monitoring / CloudWatch** → the only paid line from the earlier estimate is removed.
- Net at ~200 targets: pennies/day, and NONE on the UI request path (UI reads a ~50 ms cache regardless of fleet size).

### D.5 Todos

- [x] ✅ [INFRA] P0. **Enrich the heartbeat** — D.1 `/proc` vector + `mem_slope` stamped per tick. — done in Plan 1.
- [x] ✅ [INFRA] P0. **Workload-PID liveness** — `workload_alive = kill -0 CMD_PID`. — done in Plan 1.
- [x] ✅ [INFRA] P1. **`parse_counters` tail-read fix** — seek-to-tail (last ~64 KB). — done in Plan 1.
- [x] ✅ [BACKEND] P1. **Object-delta = manifest lookup** (authoritative write-truth, no new walk). — done in Plan 1.
- [x] ✅ [BACKEND] P1. **Hang detection = control-plane existence + stale heartbeat**. — done in Plan 1.
- [x] ✅ [BACKEND] P1. **Composite health status** (D.3, VM 7-state + `stalled` threshold table). — done in Plan 1.
- [x] ✅ [BACKEND] P1. **Service-health sub-taxonomy** (D.3, `serving`/`scaled-to-zero`/`dead`/`degraded`). — done in
      Plan 1.
- [x] ✅ [BACKEND] P2. **`/deployments/{id}/detail`** endpoint serving the rolling window. — done in Plan 1.
- [x] ✅ [UI] P1. **Health column = composite** (chip text = state, colour = 3-tier severity). — done in UI-popover.
- [x] ✅ [BACKEND] P2. **Alerts** on `oom-risk` + `stalled` wired into the alert ledger. — done in Plan 1
      (deployment-api@5e25dce, slot 15).
- [x] [OPERATOR] P2. Decide Cloud-Run-job live cpu/mem — **(b)** bucket-truth + exit-137 now (rec), or **(a)** a cgroup
      self-sampler later. **✅ (b) ADOPTED — operator sign-off 2026-07-11.** Verified in `deployments_inventory.py`:
      `object_delta_for_asset_group` / `_batched_object_deltas` supply the BATCH bucket-truth signal + exit-code
      capture; **no cgroup self-sampler on Cloud Run jobs** (option (a) stays deferred). LIVE/PAPER `stalled` remains
      the tracked P3 deferral in `deployment_obs_backend_kinds_health_2026_07_09`.

## WS-E — Cost-per-target (reuse the billing work)

- [x] ✅ [DATA] P2. Join the billing exports (GCP BigQuery + AWS CUR) by resource-id → three USD figures per target. —
      DONE 2026-07-13. Reuses the SAME query path as the /ops/costs page: `CostObservabilityService.per_resource_daily`
      aggregates the cached `CostRecord` window (net = cost+credit, USD; GCP already GBP→USD-converted) per
      `resource_id` into
      `{actual_usd (last complete day), avg_7d_usd (trailing-7d average), projected_24h_usd (peak     observed daily ≈ a full 24h day)}`.
      Attached to each inventory row by name==resource_id (GCP VM/job names match; AWS ARNs keep None — honest absence).
      deployment-api@7489d57 + deployment-ui@599a644.

## WS-F — Mock→real cutover + polish

- [x] [UI] P2. Commit the richer-estate mock once the shape is agreed. **✅ SUPERSEDED (2026-07-11)** — the real
      census + UI landed (Plan 1 full-estate + UI-popover); `deployment-ui/src/lib/mock-api.ts` now carries the
      full-estate shape (VM + CLOUD_RUN_JOB / CLOUD_RUN_SERVICE + ECS_SERVICE + LAMBDA + CLOUD_FUNCTION + SCHEDULER +
      DISK + STATIC_IP fixtures), so the mock tracks the live contract rather than a placeholder. No separate "richer
      mock" deliverable.
- [x] [UI] P3. Decide the standalone `/deployments` route — keep vs fold. **✅ KEEP (operator-confirmed 2026-07-11)** —
      the standalone route ships (`deployment-ui/src/App.tsx:155` —
      `<Route path="/deployments" element={<Deployments />}` \+ the `/deployments/:name` detail route) alongside the
      cockpit tab. Decision: KEEP. > **⚠️ SUPERSEDED 2026-07-21** — the "alongside the cockpit tab" framing above is now
      stale. > `deployment_ui_plain_routes_retire_cockpit_tabs_2026_07_17.md` retired the `?tab=` cockpit-tab scheme >
      entirely (`deployment-ui@079b29e`): there is no separate "cockpit tab" left for `/deployments` to run > alongside
      — every screen, including the former tab, is now the SAME plain, URL-param-backed route. The > underlying decision
      (KEEP a URL-param-backed, filter-deep-linkable standalone `/deployments`) still holds > — it's exactly what the
      plain-routes refactor made universal; only the "two schemes coexist" premise is gone.
- [x] ✅ [UI] P3. EXPERIMENT badge label — kept as `batch·exp` (`ModeBadge` renders it). — done in UI-popover.
- [x] ✅ [REVIEW] P1. Gate `/freshness` fetches to VM kinds only (services use error-rate health). — done
      (deployment-ui@e9b77ac; `Cockpit.tsx` + `Deployments.tsx` filter `kind === "VM"`).
  - ~~[DESIGN] P3. Service controls (scale-to-zero / restart).~~ **REMOVED 2026-07-13 (operator)** — VM
    pause/resume/stop already ship and work (`deployment-ui/src/components/VmControls.tsx` →
    `/api/vm/admin/{vm}/(pause|resume|cancel)`); Cloud-Run/ECS service scale-to-zero is not needed here and is high
    blast radius. No action.

## WS-H — Structured progress reporting (retire the log-scrape)

> **🟢 EXTRACTED 2026-07-13 (operator) — moved OUT of this plan; needs its own dedicated plan (operator will create when
> it's staffed).** This is a fleet-wide, cross-service infra change (UTL helper + a typed progress contract per
> service), not deployments-UI work, and was always the deliberately-deferred "LAST PHASE, nice-to-have" (high blast
> radius). Removed from this plan's active scope so it can archive. The spec is preserved below (prose, no open
> checkboxes) so the future plan can lift it verbatim.
>
> **(was: `consolidator_throughput_backlog_monitor_2026_07_09.md`'s WS-2 pointed to this doc as "tracked here if/when
> WS-H ships" — that pointer is now stale/dangling since this same-day extraction; no plan currently owns WS-H until the
> operator creates one. [finding 183, synced 2026-07-14])

Spec to lift into the future plan:

- **Central plumbing** — a `report_progress({...})` helper in UTL (rides the existing event facade) → a dedicated
  progress record (JSON-lines), SEPARATE from the stdout log; daemon reads the LAST record (O(1), exact, no regex);
  registry entry carries the typed payload; wrapper wires the second file. ~5 files, one-time.
- **Typed progress contract per workload**, extending the `SHARD_AXIS_MATRIX[(service, asset_group)]` registry: backfill
  `{shards_expected/downloaded/saved, bytes}`; features
  `{mdps_days_read, features_computed, parquet_written, force_replaced, formula_version}`; strategy/recon/execution each
  their own. Roll out per-service, priority order (backfills + features first).
- **Manifest cross-check per typed metric** — `shards_saved` vs manifest object count; `force_replaced` vs GCS
  object-GENERATION bumps → "is the VM telling the truth?" as an automated verdict.
- **Cloud-Run-job cgroup self-sampler** (`memory.current ÷ .max`) pushed via the event facade — only if OOM-prediction
  on jobs proves worth it (still no Cloud Monitoring).
- **Open design question**: typed-contract schema — a per-service typed model in UAC (like `SHARD_AXIS_MATRIX`) vs one
  flexible `{metric: value}` envelope validated per service. Leaning per-service typed (verifiable + self-documenting).

---

## Open questions — ALL RESOLVED 2026-07-09 (operator; unambiguous for AO dispatch)

1. **Umbrella for always-on services.** ✅ RESOLVED — **no PLATFORM/INFRA mode; the `Kind` column carries it.** Services
   (deployment-api, market-data-query, execution/strategy-service-prod) ARE our deployments and belong in the tab, but
   have no live/batch/paper phase → **Mode = "—"**. Users find them via the **Kind filter** (WS-C). Topology note: our
   always-on services run on Cloud Run/ECS (one managed service = one deployment unit); VMs are single-purpose — the
   "many services on one VM" case does not occur today.
2. **Health taxonomy granularity.** ✅ RESOLVED — **keep all 7 states, colour by 3-tier severity** (green=working ·
   amber=stalled/oom-risk/disk-full · red=workload-dead/hung/dead). Chip text = exact state (actionable), colour =
   urgency. Metric values live in the popover. See D.3.
3. **`stalled` thresholds.** ✅ RESOLVED — **per-lifecycle-class table, progress-metric primary, cpu secondary, never a
   global CPU cut.** v1 defaults in D.3 (backfill/batch/feature ≥15 min flat object_delta + cpu<10%; live ≥5 min no
   events during active window; paper ≥15 min flat work_delta). Numbers tunable once real data lands.
4. **Push vs pull cost.** ✅ RESOLVED (2026-07-08) — **no Cloud Monitoring / CloudWatch.** Metrics = edge-push (60 s
   heartbeat, free); existence = control-plane list already called; write-truth = manifest lookup; OOM cause = exit-137.
   See WS-D.0 + WS-D.4.
5. **Rich-field contract ownership.** ✅ RESOLVED — **thin list + `/deployments/{id}/detail`.** List carries only the
   rendered columns + cpu/mem/disk summary scalars; the detail endpoint serves the full metric vector + rolling window +
   object-delta breakdown + owning consolidator for the name-click popover. See D.2 + WS-C.
6. **Inline columns vs drill-down.** ✅ RESOLVED — **the current mock IS the inline contract** (Mode·Kind·Target·Cloud·
   Service·Asset group·Status·Last run/up·Progress·Cost/day·Exit·Resources[cpu/mem/disk]·Health·Controls). Everything
   else → the name-click popover. Cost stays inline but nullable (`—` until WS-E).
7. **ECS 0-task services.** ✅ RESOLVED — **always show; desired-vs-running drives state** (`serving`/`scaled-to-zero`/
   `dead`/`degraded`, D.3 service sub-taxonomy). Hiding a 0-task service would make an intentional scale-to-zero
   indistinguishable from a crashed prod execution service — the exact blind spot to kill.
8. **Kill-switch / controls for non-VM kinds.** ✅ RESOLVED — **v1 = read-only for services** (Controls stay VM-only).
   Restarting/scaling a prod service is a high-blast-radius write; deferred to a later phase behind a real safety design
   (confirmation modal + audit log + role check). Tracked as WS-F below.

---

## Progress Log

- 2026-07-09 — **Split into 2 AO-dispatched child plans** (this doc stays the LOCAL parent tracker): backend =
  `deployment_obs_backend_kinds_health_2026_07_09.md` (`status: active`, 20 todos — kinds census + rich fields +
  composite/service work-health), UI = `deployment_obs_ui_popover_health_2026_07_09.md` (`status: draft` — badges,
  composite health, resource columns, name-click popover + console deep-link). **UI is LOCAL** (`assigned_vm: NA`,
  operator decision) — executed interactively in this slot once the backend AO plan lands + hands off the frozen
  `DeploymentItem` contract (`depends_on` documents the ordering); it's visual-iteration-heavy so best built here
  against the mock. Cost-per-target (WS-E), typed structured-progress (WS-H), and deferred service-controls (WS-F)
  remain here for later phases.
- 2026-07-09 — **All 8 open questions RESOLVED with the operator** (see the Open-questions section for each decision).
  Net: Q1 no PLATFORM/INFRA mode (Kind carries services, Mode="—"); Q2 keep 7 states + 3-tier severity colour; Q3
  per-lifecycle-class `stalled` table; Q5 thin list + `/deployments/{id}/detail`; Q6 mock = inline contract, rest in
- 2026-07-10 — **Reconciled the parent's boxes with the shipped children (cross-plan audit).** This tracker had 35
  "open" todos while the extracted work was already `- [x]` DONE in the children — a false-progress hazard. Verified
  each against the children and mirrored: **WS-B (all 6), WS-C rich-fields/popover/console/kind-filter/rich-contract,
  WS-D.5 heartbeat/PID/parse_counters/object-delta/hang/composite/service-health/`/detail`/Health-column/alerts, and
  WS-F EXPERIMENT-badge + `/freshness`-gating are DONE** (in `deployment_obs_backend_kinds_health_2026_07_09` (Plan 1)
  - `deployment_obs_ui_popover_health_2026_07_09` (UI-popover) — those carry the shas). **Open count 35 → 11**, and the
    remaining 11 are honestly future/deferred: cost-per-target join (WS-E, cost-plan-owned), P3 error-count drill-down,
    the operator cpu/mem decision (b-adopted), mock-commit (moot), standalone-route (keep), service-controls (Open-Q8),
    and the 4 WS-H structured-progress items (LAST PHASE, deferred). No work was lost — only the tracker made honest.
- 2026-07-09 — **All 8 open questions RESOLVED with the operator** (see the Open-questions section for each decision).
  Net: Q1 no PLATFORM/INFRA mode (Kind carries services, Mode="—"); Q2 keep 7 states + 3-tier severity colour; Q3
  per-lifecycle-class `stalled` table; Q5 thin list + `/deployments/{id}/detail`; Q6 mock = inline contract, rest in
  popover; Q7 always show services, desired-vs-running state; Q8 v1 read-only. New todos folded in: service-health
  sub-taxonomy (WS-D), console deep-link + name-click popover (WS-C), deferred service-controls safety design (WS-F).
  Plan is now unambiguous for AO split/dispatch.
- 2026-07-08 — Merged Deployments tab shipped (`deployment-ui@50a6947`). Richer-estate mock built + verified (18 rows, 6
  kinds, rich fields, 0 console errors) — uncommitted. Live GCP/AWS census run to quantify the gap. VM heartbeat traced:
  liveness + work-counters only, no resource metrics, daemon decoupled from workload. Plan authored (local).
- 2026-07-08 — WS-D fully designed (capture → store → API → UI): the universal metric vector (D.1), the data path (D.2),
  the composite health taxonomy (D.3), and the scale/cost budget (D.4). Confirmed the work-counters are LOG-SCRAPED
  (`counters.py`, MAX-over-last-2000-lines) → a hint, not truth; object-delta (manifest lookup) is the authoritative
  progress signal. **Decision: NO Cloud Monitoring / CloudWatch** (grep-confirmed unused for metrics; existence from the
  control-plane list APIs already called, OOM cause from exit-137). Push-from-edge keeps it ~$0 at 100s of targets.

- 2026-07-08 — Re-prioritised into PHASES: v1 = the cheap/central/already-free signals (WS-B kinds census, WS-C Tier-0
  fields, WS-D `/proc` + manifest write-truth + control-plane hang + composite health) with NO per-workload changes; the
  high-blast-radius typed structured-progress reporting deferred to WS-H (last, nice-to-have) with a graceful log-scrape
  fallback. Confirmed the write-truth (`record_captured` → manifest) already exists, so v1 needs zero workload
  instrumentation.

## Deferred / parking lot

- GitHub Actions minutes / runner cost as a "kind" (out of scope — different axis).
- Per-client isolation view of deployments (funds-isolation is a separate surface).

## Folded-in scope 2026-07-15 (plan-reconcile §6)

- [x] ✅ [BACKEND] P3. **LIVE/PAPER `stalled` signals — DEFERRED (scope decision 2026-07-10, needs new subsystems)**.
      Discovered while wiring the BATCH row (deployment-api@29f3be5): LIVE `stalled` needs an expected-active-window
      calendar (market-hours-aware, so an idle-but-healthy off-hours window never misfires); PAPER needs a `work_delta`
      (rows-out-delta) tracker (the D.1 rolling window @970bcdc samples `/proc` cpu/mem/disk, NOT `rows_out`, so it
      would have to be extended to carry the counter history first). **Decision**: both are genuinely NEW subsystems — a
      market calendar and a counter-history tracker — disproportionate to build for a P3 `stalled` refinement, so they
      are DEFERRED to a future phase. The current **honest-`"unknown"` degradation is confirmed correct** as the v1:
      `_composite_health_status` returns `"unknown"` for LIVE/PAPER `stalled` rather than guessing from a proxy (WS-D.0
      principle 2), and the oom-risk/`stalled` alert wiring (deployment-api@5e25dce) only fires on a REAL state, so
      nothing misfires while these stay unknown. BATCH — the one umbrella with a real signal (`object_delta`) — is
      wired + shipped. (FOLDED IN from deployment_obs_backend_kinds_health_2026_07_09, 2026-07-15, plan-reconcile §6
      operator ruling.) **MOVED ON 2026-07-21 (plan-reconcile consolidation pass, this plan archiving)**: this plan
      itself is now archiving, so the still-open deferral moves one hop further to
      `plans/epics/observability_master.md`'s "Folded-in scope 2026-07-21" section — see there for the live copy; this
      bullet stays here checked as a closed provenance record only.
