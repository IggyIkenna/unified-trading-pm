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
- [x] ✅ [BACKEND] P1. Make the Cloud Run **jobs** census DYNAMIC — list live jobs instead of the hardcoded
      `CLOUD_RUN_JOBS` name-registry, so off-pattern jobs stop hiding (keep the registry only for classification hints,
      not as the allow-list). Run the exact registry-vs-live diff first to quantify the current hidden set. —
      deployment-api@9d50835. `build_inventory` now iterates the LIVE job set (`cloud_run_status` keys, already fetched
      by `latest_execution_by_job`'s `list_jobs` — no new API call) and treats `CLOUD_RUN_JOBS` as a classification hint
      (stem match), falling back to the honest `EPHEMERAL_BATCH` default for off-pattern jobs; degrades to the static
      registry (status=unknown) only when the live list itself is empty. Registry-vs-live diff was already quantified by
      this plan's own parent doc's 2026-07-08 live census (WS-B gap table: "~10-15 of ~48" GCP Cloud Run jobs off the
      static registry) — this sandboxed worker slot has no working `gcloud` (snap confinement blocks it here), so no
      fresh live diff was re-run; the fix + a new regression test (`test_off_pattern_live_cloud_run_job_is_not_hidden`)
      prove an off-pattern job now surfaces instead of hiding.
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

- [x] [INFRA] P0. ✅ **Enrich the heartbeat** — the daemon loop samples the D.1 vector from `/proc` (psutil or raw, no
      new dep) + `mem_slope` from a rolling window; stamp onto the registry entry each tick. —
      `unified-trading-library@6da762b3` (new `HostMetricsSampler`, wired into `HeartbeatDaemon.heartbeat_once`) +
      `deployment-service@a6881d1` (D.1 fields on `DeploymentRegistryEntry` + `heartbeat_cli.py` wiring). Sampled
      fields: cpu_pct/mem_pct/mem_slope/disk_pct/io_write_rate_bytes_sec/net_recv_rate_bytes_sec. `object_delta` +
      `workload_alive` are separate todos below (manifest lookup / `kill -0 CMD_PID`), not part of this one.
- [ ] [INFRA] P0. **Workload-PID liveness** — shell passes `CMD_PID`; daemon includes
      `workload_alive = kill -0 CMD_PID`. Kills the OOM-false-alive without the exit-file race.
- [ ] [INFRA] P1. **`parse_counters` tail-read fix** — seek-to-end / read last ~64 KB, not `read_text()` on a multi-GB
      log every tick (existing per-VM I/O waste at scale).
- [x] ✅ [BACKEND] P1. **Object-delta = manifest lookup** (authoritative write-truth) — extend `/freshness` to an
      object-count-delta per shard off the manifest the consolidator maintains; NO new bucket walk. —
      `deployment-api@defdabe`: `_object_delta_for_bucket()` reads the SAME consolidated availability-index blob
      `consolidator_posture` already resolves (`read_availability_index`, zero new bucket walks), sums captured
      `row_count`/`instrument_count` per written date, diffs the two most recent dates; wired onto
      `DeploymentFreshness.object_delta` + `object_delta_detail`. QG green; 11 unit tests (4 new) passing.
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

- 2026-07-09 — **Cloud Run jobs census made DYNAMIC** (slot 12): `deployment-api@9d50835`
  (`deployment_api/routes/deployments_inventory.py`) — `build_inventory` now iterates the LIVE job set
  (`cloud_run_status` keys, already fetched by `latest_execution_by_job`'s `run_v2.JobsClient.list_jobs`, no new API
  call) and treats `CLOUD_RUN_JOBS` as a classification hint (stem match via `_match_registered_job`) rather than an
  allow-list; an off-pattern job falls back to `classify_deployment_target(..., lifecycle_class=EPHEMERAL_BATCH)` (the
  honest default) instead of being hidden. Degrades to the static registry with status="unknown" only when the live list
  itself is empty (GCP call failed) — never an empty census. New regression test
  `test_off_pattern_live_cloud_run_job_is_not_hidden` pins the fix; `test_build_inventory_classifies_vms_and_jobs`
  updated for the dynamic (live-count, not registry-count) row count. Registry-vs-live diff: already quantified by this
  plan's parent doc's 2026-07-08 live census ("~10-15 of ~48" off-pattern) — this worker slot's `gcloud` is
  snap-confined/non-functional, so no fresh live diff was re-run here.
- 2026-07-09 — **D.5 "Enrich the heartbeat" shipped** (slot 6): new `HostMetricsSampler`
  (`unified_trading_library.lifecycle.host_metrics`, `unified-trading-library@6da762b3`) samples
  cpu_pct/mem_pct/disk_pct/io_write_rate_bytes_sec/net_recv_rate_bytes_sec via psutil (no new dep) + a rolling-window
  `mem_slope`; wired into `HeartbeatDaemon.heartbeat_once()` so it samples + stamps onto `entry.metadata` every
  heartbeat tick (shard-level failure isolation — a sampler exception logs + skips the tick, never breaks it).
  `deployment-service@a6881d1` adds the 6 fields to `DeploymentRegistryEntry` (0.0 defaults so pre-2026-07-09 registry
  rows keep loading) + wires `heartbeat_cli.py`'s `_entry_to_registry` / `_registry_to_entry` / `_vm_payload` to carry
  them. Out of scope for this todo (separate D.5 todos): `object_delta` (manifest lookup) and `workload_alive`
  (`kill -0 CMD_PID`).
- 2026-07-09 — Created from the LOCAL parent (`deployment_observability_expansion_2026_07_08.md`) after all 8 open
  questions were resolved. Backend v1 scope: kinds census + rich fields + composite/service work-health, all
  cheap/central/free (no Cloud Monitoring/CloudWatch, no per-workload instrumentation). Cost-per-target (WS-E) and typed
  structured-progress (WS-H) stay in the parent for later phases.
