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

## WS-B — Census the compute kinds the backend ignores (make the mock real)

- [ ] [BACKEND] P1. Add `CLOUD_RUN_SERVICE` to the census — `run_v2.ServicesClient` list + ready-state + revision +
      region. New `DeploymentKind` value in UAC. **Mode = "—"** (a service has no live/batch/paper phase; the `Kind`
      badge/filter carries "this is a service" — see Open-Q1). No PLATFORM/INFRA mode.
- [ ] [BACKEND] P1. Add `ECS_SERVICE` census — ECS list-services/describe-services across the prod clusters
      (uts-defi-prod, unified-trading-prod) → **desiredCount + runningCount** + task-def revision; `cloud=AWS`. Always
      emit the row even at 0 running tasks (state derives from desired-vs-running — see Open-Q7 + WS-D service-health
      sub-taxonomy).
- [ ] [BACKEND] P1. Make the Cloud Run **jobs** census DYNAMIC — list live jobs instead of the hardcoded
      `CLOUD_RUN_JOBS` name-registry, so off-pattern jobs stop hiding (keep the registry only for classification hints,
      not as the allow-list). Run the exact registry-vs-live diff first to quantify the current hidden set.
- [ ] [BACKEND] P2. Add `LAMBDA` census — existence + config via `list_functions` (`cloud=AWS`). NOTE: invocation/error
      stats are CloudWatch-only (no host/cgroup on Lambda) — the ONE scoped exception to WS-D.0-#4; default to
      existence-only and add a CloudWatch call ONLY if Lambda health proves worth it. Lower priority (portal/auth
      infra).
- [ ] [BACKEND] P2. Add `CLOUD_FUNCTION` (gen2) census — `functions list`; note gen2 = Cloud Run underneath.
- [ ] [BACKEND] P1. Extend `DeploymentKind` (UAC) + the inventory route's kind counts + filters to the 6 kinds; keep
      honest degradation (a census failure for one kind never blocks the others).

## WS-C — Richer per-target data + drill-down

- [ ] [BACKEND] P1. Surface the **Tier-0 free wins** already fetched-and-discarded: the GCE aggregated-list returns
      machine_type/zone/labels/boot-disk but the inventory uses only `.keys()`
      (`deployments_inventory.py:_load_gcp_vm_entries`) — keep the values. The registry entry already carries
      `rows_in/rows_error/events_emitted/uptime_hours/machine_type/zone/health_status` — surface them (today only
      `rows_out` → captured_progress is exposed).
- [ ] [DATA] P2. Cost-per-target join (see WS-E) → `cost_per_day_usd` on each item.
- [ ] [BACKEND] P2. Utilisation (cpu/mem/disk per target) — sourced from WS-D **edge-push** (VM `/proc`, Cloud Run
      cgroup), NOT a Cloud Monitoring / CloudWatch pull (see WS-D.0 principle 4). Owned by WS-D; listed here for the
      WS-C column/drill-down wiring.
- [ ] [BACKEND] P3. Recent error count / last log line — from the EXISTING teed GCS log / Cloud Logging (drill-down
      only); no new CloudWatch dependency.
- [ ] [UI] P1. **Name-click detail popover** (right-side panel) — table row shows current/last stats; clicking the
      target NAME opens a popover with the deep fields (cpu/mem/disk sparklines + timeline, req/min, p99, invocations,
      revision, running_tasks, rows in/out/error, object-delta breakdown, owning consolidator, absolute used/total GB).
      Flat table stays scannable; deep detail lives here. (Mock stores these fields already; wire the panel.)
- [ ] [UI] P1. **Console deep-link** in the popover — "Open in GCP/AWS console →" built from the target's identity: GCE
      `compute/instancesDetail/zones/{zone}/instances/{name}?project=…`, EC2 `ec2/home?region={r}#InstanceDetails:{id}`,
      plus Cloud Run service/job, ECS cluster/service, Lambda function URLs. Pure URL construction from fields already
      fetched (zone/region/id) — no new API call.
- [ ] [UI] P2. **Kind filter** dropdown next to Mode/Cloud/Status (isolate services vs jobs vs VMs). This is how a user
      finds always-on services (they have Mode="—") — see Open-Q1.
- [ ] [REVIEW] P2. Extend `DeploymentItem` in UAC/backend to the mock's optional rich-field shape (already in the UI
      type) so the wire contract matches — one SSOT, no client-only fields.

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

- [ ] [INFRA] P0. **Enrich the heartbeat** — the daemon loop samples the D.1 vector from `/proc` (psutil or raw, no new
      dep) + `mem_slope` from a rolling window; stamp onto the registry entry each tick.
- [ ] [INFRA] P0. **Workload-PID liveness** — shell passes `CMD_PID`; daemon includes
      `workload_alive = kill -0 CMD_PID`. Kills the OOM-false-alive without the exit-file race.
- [ ] [INFRA] P1. **`parse_counters` tail-read fix** — seek-to-end / read last ~64 KB, not `read_text()` on a multi-GB
      log every tick (existing per-VM I/O waste at scale).
- [ ] [BACKEND] P1. **Object-delta = manifest lookup** (authoritative write-truth) — extend `/freshness` to an
      object-count-delta per shard off the manifest the consolidator maintains; NO new bucket walk.
- [ ] [BACKEND] P1. **Hang detection = control-plane existence + stale heartbeat** (NOT Cloud Monitoring) — reuse the
      `aggregated_list` / EC2 / Run-execution lists already fetched.
- [ ] [BACKEND] P1. **Composite health status** (D.3) replacing `_vm_status` — VM 7-state + the per-lifecycle-class
      `stalled` threshold table (Open-Q3).
- [ ] [BACKEND] P1. **Service-health sub-taxonomy** (D.3) — `serving`/`scaled-to-zero`/`dead`/`degraded` from ECS
      desired-vs-running (and Cloud Run ready-state/revision); services always emit a row (Open-Q7). Read-only in v1 (no
      controls — Open-Q8).
- [ ] [BACKEND] P2. **`/deployments/{id}/detail`** endpoint serving the rolling window (drill-down); the thin list
      carries the composite + headline numbers.
- [ ] [UI] P1. **Health column = composite** — chip text = exact state, colour = 3-tier severity (Open-Q2); deep metrics
      move to the name-click popover (WS-C), not an inline drill-down. Controls column stays VM-only; services render
      read-only (Open-Q8).
- [ ] [BACKEND] P2. **Alerts** on `oom-risk` (before the kill) + `stalled` (progress flatlines, heartbeat fresh) — wire
      into the existing alerts surface.
- [ ] [OPERATOR] P2. Decide Cloud-Run-job live cpu/mem — **(b)** bucket-truth + exit-137 now (rec), or **(a)** a cgroup
      self-sampler in the job base image later (still no Monitoring).

## WS-E — Cost-per-target (reuse the billing work)

- [ ] [DATA] P2. Join BigQuery billing-export (GCP) + AWS CUR by resource-id/labels → `$/day` per VM / Cloud Run / ECS /
      Lambda. Coordinate with `cost_observability_ui_2026_07_08.md` (the /ops/costs page) so the per-target cost + the
      aggregate cost page share ONE query path.

## WS-F — Mock→real cutover + polish

- [ ] [UI] P2. Commit the richer-estate mock (currently uncommitted) once the shape is agreed, so the mock is the
      committed contract the backend targets.
- [ ] [UI] P3. Decide the standalone `/deployments` route — keep (deep-linkable) vs fold entirely into the cockpit tab.
      (Rec: keep.)
- [ ] [UI] P3. EXPERIMENT badge label — keep `batch·exp` vs plain `batch`. (Rec: keep.)
- [ ] [REVIEW] P1. When the real census lands, gate `/freshness` fetches to VM kinds only (services use error-rate
      health, not manifest freshness) — the mock currently fetches freshness for all LIVE rows.
- [ ] [DESIGN] P3. **Service controls (deferred, Open-Q8)** — scale-to-zero / restart affordances for Cloud Run / ECS
      services behind a safety design: confirmation modal + audit log + role check. NOT v1 (v1 services are read-only).
      Its own phase; high blast radius on prod.

## WS-H — Structured progress reporting (retire the log-scrape) — LAST PHASE, nice-to-have

> Deferred deliberately (high blast radius). v1 relies on the manifest (write-truth) + log-scrape (hint) + `/proc`; this
> phase makes progress TYPED + trustworthy, rolled out per service. **Graceful fallback:** the daemon reads
> structured-progress-when-present, else the log-scrape — so nothing breaks mid-migration.

- [ ] [INFRA] P3. **Central plumbing** — a `report_progress({...})` helper in UTL (rides the existing event facade) → a
      dedicated progress record (JSON-lines), SEPARATE from the stdout log; daemon reads the LAST record (O(1), exact,
      no regex); registry entry carries the typed payload; wrapper wires the second file. ~5 files, one-time.
- [ ] [DATA] P3. **Typed progress contract per workload**, extending the `SHARD_AXIS_MATRIX[(service, asset_group)]`
      registry: backfill `{shards_expected/downloaded/saved, bytes}`; features
      `{mdps_days_read, features_computed, parquet_written, force_replaced, formula_version}`; strategy/recon/execution
      each their own. Roll out per-service, priority order (backfills + features first).
- [ ] [BACKEND] P3. **Manifest cross-check per typed metric** — `shards_saved` vs manifest object count;
      `force_replaced` vs GCS object-GENERATION bumps → "is the VM telling the truth?" as an automated verdict.
- [ ] [INFRA] P3. **Cloud-Run-job cgroup self-sampler** (`memory.current ÷ .max`) pushed via the event facade — only if
      OOM-prediction on jobs proves worth it (still no Cloud Monitoring).

**Open (WS-H):** typed-contract schema — a per-service typed model in UAC (like `SHARD_AXIS_MATRIX`) vs one flexible
`{metric: value}` envelope validated per service. Leaning per-service typed (verifiable + self-documenting).

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
