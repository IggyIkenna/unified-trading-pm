---
doc_type: plan
title: Deployment observability — full-estate kinds census + VM/service work-health (backend)
summary:
  Backend half of the deployment-observability expansion. Census the compute kinds the inventory route ignores today
  (Cloud Run services, ECS/Fargate services, off-registry Cloud Run jobs, Lambda, Cloud Functions), surface the rich
  GCP/AWS fields already fetched-and-discarded, and replace heartbeat-only VM health with a composite work-health model
  (edge /proc metrics + workload-PID liveness + manifest object-delta + control-plane hang detection) plus a service
  sub-taxonomy. No Cloud Monitoring / CloudWatch. Feeds the UI half (deployment_obs_ui_popover_health_2026_07_09), a
  LOCAL plan executed interactively once this plan lands the contract. Full design + open-question resolutions live in
  the LOCAL parent deployment_observability_expansion_2026_07_08.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-api-contracts]
scope: [engineer]
tags: [deployment-observability, cockpit, vm-health, cloud-run, ecs, lambda, heartbeat, deployment-api]
related: [deployment_observability_expansion_2026_07_08.md, deployment_obs_ui_popover_health_2026_07_09.md]
created: "2026-07-09"
last_updated: "2026-07-09"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7.2
assigned_role: backend-engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_observability_expansion_2026_07_08.md
---

# Deployment observability — full-estate kinds census + VM/service work-health (backend)

> **AO-DISPATCHED backend plan.** Full design context — the universal metric vector, the capture→store→API→UI data path,
> the composite health taxonomy, the scale/cost budget, and the 8 resolved open questions — lives in the LOCAL parent
> **`deployment_observability_expansion_2026_07_08.md`** (read WS-B, WS-C, and all of WS-D first, incl. D.0 principles
> and the D.3 taxonomy). The UI half is **`deployment_obs_ui_popover_health_2026_07_09.md`** — a LOCAL plan built
> interactively AFTER this one lands; this plan's LAST task hands off the frozen contract sha so the UI wires against
> real fields.

## Non-negotiable design principles (from parent WS-D.0 — inherit on every task)

1. A verdict is a JOINT function — resource in-band AND a work signal advancing (neither alone).
2. Self-logged counters are a HINT, not truth (log-scraped, MAX-over-tail); **manifest object-delta is authoritative**.
3. Push metrics from the EDGE (VM `/proc`), never a per-request central pull.
4. Existence from the control-plane list already called; OOM cause from exit-137. **No Cloud Monitoring / CloudWatch.**
5. **Add ZERO new bucket walks** (single-walk HARD RULE) — object-delta is a manifest LOOKUP.

## Codex SSOTs (READ before touching each area — plan↔codex drift is review-blocking)

- Inventory contract + classification: `deployment-api/.../routes/deployments_inventory.py`.
- Deployment observability / no-fire-and-forget: `codex/05-infrastructure/deployment-observability.md`.
- Heartbeat daemon + wrapper: `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`,
  `deployment-service/deployment_service/vm/heartbeat_cli.py`, `unified_trading_library.lifecycle`.
- Availability manifest (object-delta cross-check): `codex/02-data/availability-manifest-and-data-status.md`.
- Shard-level failure isolation (honest per-kind degradation): `codex/04-architecture/shard-level-failure-isolation.md`.

## Todos

### Kinds census (make the estate visible)

- [ ] [BACKEND] P1. Add `CLOUD_RUN_SERVICE` to the census — `run_v2.ServicesClient` list + ready-state + revision +
      region. New `DeploymentKind` value in UAC. **Mode = "—"** (a service has no live/batch/paper phase; the `Kind`
      badge/filter carries "this is a service"). No PLATFORM/INFRA mode.
- [ ] [BACKEND] P1. Add `ECS_SERVICE` census — ECS list-services/describe-services across the prod clusters
      (uts-defi-prod, unified-trading-prod) → **desiredCount + runningCount** + task-def revision; `cloud=AWS`. Always
      emit the row even at 0 running tasks (state derives from desired-vs-running — see the service sub-taxonomy task).
- [ ] [BACKEND] P1. Make the Cloud Run **jobs** census DYNAMIC — list live jobs instead of the hardcoded
      `CLOUD_RUN_JOBS` name-registry, so off-pattern jobs stop hiding (keep the registry only for classification hints,
      not as the allow-list). Run the exact registry-vs-live diff first to quantify the current hidden set.
- [ ] [BACKEND] P2. Add `LAMBDA` census — existence + config via `list_functions` (`cloud=AWS`). NOTE: invocation/error
      stats are CloudWatch-only (no host/cgroup on Lambda) — the ONE scoped exception to principle 4; default to
      existence-only and add a CloudWatch call ONLY if Lambda health proves worth it.
- [ ] [BACKEND] P2. Add `CLOUD_FUNCTION` (gen2) census — `functions list`; note gen2 = Cloud Run underneath.
- [ ] [BACKEND] P1. Extend `DeploymentKind` (UAC) + the inventory route's kind counts + filters to the 6 kinds; keep
      honest degradation (a census failure for one kind never blocks the others).

### Rich per-target fields + wire contract

- [ ] [BACKEND] P1. Surface the **Tier-0 free wins** already fetched-and-discarded: the GCE aggregated-list returns
      machine_type/zone/labels/boot-disk but the inventory uses only `.keys()`
      (`deployments_inventory.py:_load_gcp_vm_entries`) — keep the values. The registry entry already carries
      `rows_in/rows_error/events_emitted/uptime_hours/machine_type/zone/health_status` — surface them (today only
      `rows_out` → captured_progress is exposed).
- [ ] [BACKEND] P3. Recent error count / last log line — from the EXISTING teed GCS log / Cloud Logging (popover only);
      no new CloudWatch dependency.
- [ ] [REVIEW] P2. Extend `DeploymentItem` in UAC/backend to the mock's optional rich-field shape (already in the UI
      type) so the wire contract matches — one SSOT, no client-only fields.

### VM / service work-health (capture → store → API)

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
- [ ] [BACKEND] P1. **Composite health status** (parent D.3) replacing `_vm_status` — VM 7-state + the
      per-lifecycle-class `stalled` threshold table (progress-metric primary, cpu secondary, never a global CPU cut).
- [ ] [BACKEND] P1. **Service-health sub-taxonomy** (parent D.3) — `serving`/`scaled-to-zero`/`dead`/`degraded` from ECS
      desired-vs-running (and Cloud Run ready-state/revision); services always emit a row. Read-only in v1 (no
      controls).
- [ ] [BACKEND] P2. **`/deployments/{id}/detail`** endpoint serving the rolling window (popover); the thin list carries
      only the composite + headline numbers.
- [ ] [BACKEND] P2. **Alerts** on `oom-risk` (before the kill) + `stalled` (progress flatlines, heartbeat fresh) — wire
      into the existing alerts surface.
- [ ] [REVIEW] P2. Gate `/freshness` fetches to VM kinds only (services use error-rate health, not manifest freshness) —
      the mock currently fetches freshness for all LIVE rows.

### Hand off to the interactive UI session (LAST task)

- [ ] [REVIEW] P3. **Hand off the UI half** — the UI plan `deployment_obs_ui_popover_health_2026_07_09.md` is LOCAL
      (executed interactively, NOT AO-dispatched). Once the census + `DeploymentItem` contract + composite/service
      health land, record the frozen contract sha (`<repo>@<sha>` + the new `DeploymentItem` field list) in that plan's
      Progress Log and NOTIFY THE OPERATOR so the UI work can start here. Do NOT flip its status — a LOCAL plan is never
      ingested.

## Progress Log

- 2026-07-09 — Created from the LOCAL parent (`deployment_observability_expansion_2026_07_08.md`) after all 8 open
  questions were resolved. Backend v1 scope: kinds census + rich fields + composite/service work-health, all
  cheap/central/free (no Cloud Monitoring/CloudWatch, no per-workload instrumentation). Cost-per-target (WS-E) and typed
  structured-progress (WS-H) stay in the parent for later phases.
