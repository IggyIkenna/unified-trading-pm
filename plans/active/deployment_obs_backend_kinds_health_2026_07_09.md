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
- [x] ✅ [BACKEND] P1. Add `ECS_SERVICE` census — ECS list-services/describe-services across the prod clusters
      (uts-defi-prod, unified-trading-prod) → **desiredCount + runningCount** + task-def revision; `cloud=AWS`. Always
      emit the row even at 0 running tasks (state derives from desired-vs-running — see the service sub-taxonomy task).
      — deployment-service@3262d7c (`list_ecs_census()` pages `list_services`/`describe_services` across both prod
      clusters → `AwsEcsServiceCensus` with desired_count/running_count/task_definition_revision) +
      deployment-api@c90eaf4 (`_ecs_service_item()` wires the census into
      `DeploymentItem(kind=ECS_SERVICE,     umbrella=NONE, cloud=AWS)`; `load_aws_inventory()` now census all three AWS
      kinds). A service is always emitted, including at 0 running/desired tasks (an intentional scale-to-zero stays
      visible — Open-Q7). Status is a conservative desired-vs-running placeholder (`running`/`stopped`/`unknown`); the
      full `serving`/`scaled-to-zero`/ `dead`/`degraded` sub-taxonomy is the separate service-health-sub-taxonomy todo
      (already shipped, not yet wired here since `ecs_service_health_status()` needs an error-rate signal this census
      doesn't carry yet). Tests: `test_build_aws_inventory_classifies_ecs_service_running` /
      `_scaled_to_zero_always_emitted` / `_desired_but_not_running_is_unknown` + a moto-backed
      `test_list_ecs_census_discovers_service_across_clusters` pinning both cluster names. QG green, sentinel=c90eaf4.
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
- [x] ✅ [BACKEND] P2. Add `LAMBDA` census — existence + config via `list_functions` (`cloud=AWS`). NOTE:
      invocation/error stats are CloudWatch-only (no host/cgroup on Lambda) — the ONE scoped exception to principle 4;
      default to existence-only and add a CloudWatch call ONLY if Lambda health proves worth it. —
      deployment-service@7c8b210 + deployment-api@050d9a4. `list_lambda_census()` (single paginated `list_functions`
      call, no per-function `describe`/`list_tags` N+1) + `_lambda_item()` (classifies by `FunctionName`, same
      name-based resolution as Cloud Run jobs) → `DeploymentItem(kind=LAMBDA)`, existence-only status from `State`
      (Active/Pending/Failed/Inactive → running/pending/failed/stopped), no CloudWatch call. Landed + merged alongside 2
      concurrently-shipped sibling census todos on this same plan (ECS_SERVICE @ deployment-service/deployment-api, the
      DeploymentKind 6-kind UAC extension) — 3-way conflict resolution kept all three kinds' code paths. QG green both
      repos (sentinels 7c8b210 / 050d9a4).
- [ ] [BACKEND] P2. Add `CLOUD_FUNCTION` (gen2) census — `functions list`; note gen2 = Cloud Run underneath.
- [x] ✅ [BACKEND] P1. Extend `DeploymentKind` (UAC) + the inventory route's kind counts + filters to the 6 kinds; keep
      honest degradation (a census failure for one kind never blocks the others). — deployment-api@9353d28. UAC
      `DeploymentKind` already carried all 6 values (VM/CLOUD_RUN_JOB/CLOUD_RUN_SERVICE/ECS_SERVICE/LAMBDA/
      CLOUD_FUNCTION) — no UAC change needed. Added a `kind=` query filter to `GET /deployments/inventory` (case-
      insensitive, same pattern as `umbrella`/`cloud`/`status`) and a `counts_by_kind: dict[str, int]` rollup on
      `DeploymentInventoryResponse`, additive alongside the legacy `vm_count`/`cloud_run_job_count` (kept for
      back-compat, no UI break). `counts_by_kind` only keys a kind actually present in the (post-filter) item set — a
      kind whose census hasn't shipped yet or failed this cycle is simply absent from the map, never a fabricated `0` —
      so this generic, kind-agnostic counting/filtering layer needs no further changes as the remaining census todos
      (CLOUD_RUN_SERVICE, LAMBDA, CLOUD_FUNCTION) land; ECS_SERVICE already flows through it today (landed concurrently
      by another slot, `deployment-api@c90eaf4`, verified by rebase). New tests:
      `test_counts_by_kind_omits_absent_kinds` (pure function) + `test_inventory_route_kind_filter` + `counts_by_kind`
      assertions in `test_inventory_route_mock_shape`. QG green (sentinel 9353d28, 142s).

### Rich per-target fields + wire contract

- [x] ✅ [BACKEND] P1. Surface the **Tier-0 free wins** already fetched-and-discarded: the GCE aggregated-list returns
      machine_type/zone/labels/boot-disk but the inventory uses only `.keys()`
      (`deployments_inventory.py:_load_gcp_vm_entries`) — keep the values. The registry entry already carries
      `rows_in/rows_error/events_emitted/uptime_hours/machine_type/zone/health_status` — surface them (today only
      `rows_out` → captured_progress is exposed). — deployment-api@517bbbe. `_load_gcp_vm_entries` now returns the GCE
      aggregated-list join (`name -> machine_type/zone/labels/boot_disk_name/status`) alongside the registry entries;
      threaded through `build_inventory` -> `_vm_item` -> `DeploymentItem` (new fields: `rows_in`, `rows_error`,
      `events_emitted`, `uptime_hours` (derived `started_at`->`completed_at`/now), `machine_type`, `zone`,
      `health_status` (raw GCE status), `boot_disk_name`, `labels`). All optional, default `None` for Cloud Run jobs /
      an unjoined VM (honest absence). New unit test `test_build_inventory_surfaces_tier0_free_wins` pins both the
      joined and unjoined paths. QG green (sentinel 517bbbe).
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
- [x] ✅ [INFRA] P0. **Workload-PID liveness** — shell passes `CMD_PID`; daemon includes
      `workload_alive = kill -0 CMD_PID`. Kills the OOM-false-alive without the exit-file race. —
      `unified-trading-library@0265663b` (`SignalProtocol.cmd_pid_file`/`read_cmd_pid()`/`workload_alive()` +
      `HeartbeatDaemon._sample_workload_liveness()`, sampled every heartbeat tick, independent of the terminal
      `exit_status_file` check) + `deployment-service@2794163` (`vm-exec-with-gcs-tee.sh` passes
      `--cmd-pid-file "$PID_FILE"` to the daemon at launch — the daemon starts BEFORE `CMD_PID` exists so it reads the
      file lazily each tick; `DeploymentRegistryEntry.workload_alive` (default `True`, honest-unknown) wired through
      `_entry_to_registry`/`_registry_to_entry`/`_vm_payload`). `None` (unconfigured/not-yet-written/unparseable) never
      overwrites the entry's prior value — only a resolved `kill -0` reading stamps `workload_alive`. QG green both
      repos (UTL sentinel 0265663b, deployment-service sentinel 2794163).
- [x] ✅ [INFRA] P1. **`parse_counters` tail-read fix** — seek-to-end / read last ~64 KB, not `read_text()` on a
      multi-GB log every tick (existing per-VM I/O waste at scale). — `unified-trading-library@b77c8592` (binary seek to
      the last `DEFAULT_TAIL_BYTES` (64 KiB) from EOF instead of `read_text()` loading the whole file).
- [x] ✅ [BACKEND] P1. **Object-delta = manifest lookup** (authoritative write-truth) — extend `/freshness` to an
      object-count-delta per shard off the manifest the consolidator maintains; NO new bucket walk. —
      `deployment-api@defdabe`: `_object_delta_for_bucket()` reads the SAME consolidated availability-index blob
      `consolidator_posture` already resolves (`read_availability_index`, zero new bucket walks), sums captured
      `row_count`/`instrument_count` per written date, diffs the two most recent dates; wired onto
      `DeploymentFreshness.object_delta` + `object_delta_detail`. QG green; 11 unit tests (4 new) passing.
- [x] ✅ [BACKEND] P1. **Hang detection = control-plane existence + stale heartbeat** (NOT Cloud Monitoring) — reuse the
      `aggregated_list` / EC2 / Run-execution lists already fetched. — deployment-api@f5f6ff4 (same commit as the
      composite status below — `_composite_health_status`'s `hung` branch IS this todo: `control_plane_running` derived
      from the GCE aggregated-list join's key set, combined with heartbeat staleness).
- [x] ✅ [BACKEND] P1. **Composite health status** (parent D.3) replacing `_vm_status` — VM 7-state + the
      per-lifecycle-class `stalled` threshold table (progress-metric primary, cpu secondary, never a global CPU cut). —
      deployment-api@f5f6ff4. Additive `DeploymentItem.composite_health_status` (no wire break — `status` untouched).
      `_composite_health_status()` computes the 5 states with a real signal today: `dead` (control-plane confirms the VM
      is gone) / `hung` (control-plane confirms running but heartbeat stale) / `disk-full` / `oom-risk` / `working` (D.1
      `/proc` metrics). `stalled` + `workload-dead` degrade honestly to `"unknown"` (WS-D.0 principle 2 — a hint is not
      truth) rather than being guessed from a proxy signal. Blocked-question BLK-7751ce11 (operator-answered Option B)
      scoped this to the signals available at the time; `object_delta` (Object-delta todo above) and `workload_alive`
      (Workload-PID liveness todo above) have SINCE landed from sibling slots mid-task — wiring them into
      `stalled`/`workload-dead` is captured as its own follow-on todo below rather than re-opening this diff.
- [x] ✅ [BACKEND] P1. **Service-health sub-taxonomy** (parent D.3) — `serving`/`scaled-to-zero`/`dead`/`degraded` from
      ECS desired-vs-running (and Cloud Run ready-state/revision); services always emit a row. Read-only in v1 (no
      controls). — deployment-api@eda5be5. `ecs_service_health_status()` + `cloud_run_service_health_status()`
      (`deployments_inventory.py`) are pure classifiers implementing the exact D.3 state set — `scaled-to-zero` wins on
      `desired_count<=0` (or Cloud Run `min_instance_count<=0` + no active instances) regardless of stray running/active
      counts (never flagged red for an intentional off switch); `dead` on `desired>0, running==0` (ECS) or
      `ready is False` (Cloud Run, and takes priority over scale-to-zero config); `degraded` on partial capacity
      (`0<running<desired`), unknown ready-state, or error-rate over a v1 0.05 threshold (undocumented SLO in the plan,
      tune later); `serving` otherwise. 15 unit tests (`test_service_health_taxonomy.py`) pin every state + boundary
      (threshold is `>` not `>=`, dead beats scaled-to-zero on priority). NOT yet wired to live inventory rows — the
      `ECS_SERVICE`/`CLOUD_RUN_SERVICE` census this consumes (this plan's kinds-census todos, still unchecked) hasn't
      landed, and `DeploymentKind` doesn't carry those kinds yet; these are the reusable status-derivation half, ready
      for that census to call once it ships. QG green (sentinel eda5be5).
- [x] ✅ [BACKEND] P2. **`/deployments/{id}/detail`** endpoint serving the rolling window (popover); the thin list
      carries only the composite + headline numbers. — deployment-api@7c4265a. `GET /deployments/{name}/detail` (path
      param is the wire `DeploymentItem.name` — VM/job/service name, not an orchestration `deployment_id`; distinct
      3-segment template from `routes/deployments/`'s `/deployments/{deployment_id}/verify`, no collision) returns
      `DeploymentDetailResponse` — the thin-list item plus the D.1 metrics vector
      (`cpu_pct`/`mem_pct`/`mem_slope`/`disk_pct`/`io_write_rate_bytes_sec`/
      `net_recv_rate_bytes_sec`/`workload_alive`). New `_vm_entry_by_name_cache` side-cache is populated as a side
      effect of the SAME GCP census `_compute_inventory` already runs each cache cycle (zero new bucket walks/API
      calls); 404 if the name isn't in the current cached inventory. **Honest scope note**: this serves the single
      most-recent D.1 sample (overwritten in place each heartbeat tick) — NOT a persisted rolling window. The original
      D.2 STORE design called for keeping the last ~10 samples on the registry entry so `mem_slope`/ "sustained idle"
      have a trend to plot; that persistence never shipped (the "Enrich the heartbeat" todo above only stamps
      single-point values). Filed as a new todo below rather than silently claiming more than this delivers. 3 new tests
      (`test_detail_route_mock_shape`, `test_detail_route_unknown_name_404`,
      `test_detail_route_live_path_includes_d1_metrics`). QG green (sentinel 7c4265a, 78s). Rebased twice onto
      concurrent same-file landings (D.3 composite health `f5f6ff4`, AWS Lambda census `050d9a4`) — one duplicate-field
      artifact from an auto-merge in the test file's `_FakeEntry` dataclass, caught + fixed before shipping.
- [ ] [INFRA] P2. **Persist a short D.1 rolling window** (last ~10 samples) on the registry entry — today only a single
      most-recent sample is stored (overwritten each heartbeat tick), so `mem_slope` / "sustained idle" have no real
      trend to plot and the new `/deployments/{id}/detail` endpoint (above) can only serve a point-in-time snapshot, not
      a sparkline. Per the original D.2 STORE design (parent `deployment_observability_expansion_2026_07_08.md` D.2):
      extend `DeploymentRegistryEntry` with a bounded ring-buffer field (`unified-trading-library`/`deployment-service`,
      mirrors the "Enrich the heartbeat" todo's scope) + surface it on `DeploymentDetailResponse` (`deployment-api`,
      additive — the current single-sample fields stay for back-compat).
- [ ] [BACKEND] P2. **Alerts** on `oom-risk` (before the kill) + `stalled` (progress flatlines, heartbeat fresh) — wire
      into the existing alerts surface.
- [ ] [REVIEW] P2. Gate `/freshness` fetches to VM kinds only (services use error-rate health, not manifest freshness) —
      the mock currently fetches freshness for all LIVE rows.
- [ ] [BACKEND] P1. **Wire `stalled` + `workload-dead` into `_composite_health_status`** (`deployment-api`,
      `deployments_inventory.py`) — both prerequisite signals now exist: `object_delta` via
      `deployment_freshness.compute_freshness()` / `_object_delta_for_bucket()` (per-asset_group manifest lookup,
      `deployment_freshness.py`), and `workload_alive` via the heartbeat daemon's `CMD_PID` liveness field
      (`unified-trading-library`/`deployment-service`, Workload-PID liveness todo above). `stalled`'s threshold table is
      per-`lifecycle_class` (backfill/batch → `object_delta==0` ≥15min AND cpu<10%; live-capture → no progress ≥5min in
      an expected-active window; paper → `work_delta==0` ≥15min) — `compute_freshness` needs a `deployment_id` +
      resolves per-asset_group, not per-VM-entry, so this needs its own call-shape design (batch the lookup once per
      asset_group per census cycle, not once per VM, to respect the zero-new-bucket-walk principle at scale), not a
      copy-paste into the per-entry loop. Filed here rather than expanding deployment_obs_backend_kinds_health-015
      (deployment-api@f5f6ff4) — that diff was already large from 3 concurrent cross-slot rebases on this same file.
- [ ] [REVIEW] P3. **`deployments_inventory.py` is now 1000+ lines** (cap is 900; QG's file-size check is non-blocking
      in this repo's config today but the file is a real hotspot — 4+ slots landed sibling D.3/kinds-census todos here
      concurrently in one session). Consider splitting Cloud-Run-job census / composite-health / service- taxonomy into
      sibling modules once this plan's todos stop actively converging on it (splitting mid-convergence risks more
      cross-slot conflicts than it saves).

### Hand off to the interactive UI session (LAST task)

- [ ] [REVIEW] P3. **Hand off the UI half** — the UI plan `deployment_obs_ui_popover_health_2026_07_09.md` is LOCAL
      (executed interactively, NOT AO-dispatched). Once the census + `DeploymentItem` contract + composite/service
      health land, record the frozen contract sha (`<repo>@<sha>` + the new `DeploymentItem` field list) in that plan's
      Progress Log and NOTIFY THE OPERATOR so the UI work can start here. Do NOT flip its status — a LOCAL plan is never
      ingested.

## Progress Log

- 2026-07-09 — **`/deployments/{name}/detail` drill-down endpoint shipped** (slot 15): `deployment-api@7c4265a`
  (`deployment_api/routes/deployments_inventory.py`) — `DeploymentDetailResponse` (thin-list item + the D.1 metrics
  vector) served via a new `_vm_entry_by_name_cache` side-cache populated as a side effect of the SAME GCP census
  `_compute_inventory` already runs each cache cycle (zero new bucket walks). Path param is the wire
  `DeploymentItem.name`, not an orchestration `deployment_id` — a distinct 3-segment route template from
  `routes/deployments/`'s existing `/deployments/{deployment_id}/verify`, no collision. **Finding surfaced + tracked,
  not absorbed**: the endpoint currently serves a single most-recent D.1 sample (each heartbeat tick overwrites the
  registry entry's fields in place) rather than a true persisted rolling window — the original D.2 STORE design called
  for keeping the last ~10 samples, but that was never actually shipped by the earlier "Enrich the heartbeat" todo.
  Added a new `[INFRA] P2` todo above (rolling-window persistence) instead of silently claiming the endpoint delivers a
  trend it can't yet plot. 3 new tests. QG green (sentinel 7c4265a, 78s). Rebased twice onto concurrent same-file
  landings (D.3 composite health `f5f6ff4`, AWS Lambda census `050d9a4`) — caught and fixed one duplicate-field artifact
  an auto-merge left in the test file's `_FakeEntry` dataclass before shipping.
- 2026-07-09 — **LAMBDA census shipped** (slot 4): `deployment-service@7c8b210`
  (`deployment_service/backends/aws_census.py`) adds `AwsLambdaFunctionCensus` + `list_lambda_census()` — one paginated
  `list_functions` call, deliberately no per-function `describe`/`list_tags` follow-up (avoids an N+1; classification is
  by `FunctionName`, the same name-based resolution Cloud Run jobs already use, not tags). `deployment-api@050d9a4`
  (`deployment_api/routes/_aws_deployments.py`) wires it: `_lambda_item()` classifies via
  `classify_deployment_target(kind=DeploymentKind.LAMBDA)`, status from `State` only (Active/Pending/Failed/Inactive →
  running/pending/failed/stopped) — no CloudWatch call, per the plan's existence-only default. Landed through TWO 3-way
  merge conflicts against concurrently-shipped sibling work on this same plan: the ECS_SERVICE census
  (deployment-service/deployment-api) and the DeploymentKind 6-kind UAC extension (`unified-api-contracts`) — my own UAC
  `DeploymentKind.LAMBDA` addition turned out fully redundant with the other slot's more complete 6-kind extension
  (`CLOUD_RUN_SERVICE`/`ECS_SERVICE`/`LAMBDA`/`CLOUD_FUNCTION` all at once), so it was dropped rather than duplicated.
  Also fixed a pre-existing STEP-5.101 empty-string-fallback baseline breach in `deployment-service` (94 > 91, unrelated
  3 script files) that was blocking `quality-gates.sh` for the whole repo — noqa-marked/rewrote to fail-fast, back to 89
  ≤ baseline 91. Filed `plans/active/issues/uac_ws_cassette_coexistence_dex_swap_uniswap_v3_2026_07_09.md` for an
  unrelated pre-existing `unified-api-contracts` QG blocker (STEP 5.7X WS cassette coexistence, broken by
  `mtds@d02cf88f`'s real `dex_swap_uniswap_v3_ws` connector landing with no matching cassette) discovered while shipping
  this — cross-repo, blocks quickmerge for all of UAC, tracked separately since it's out of DeFi-craft scope for this
  task. New/updated tests: `test_build_aws_inventory_classifies_lambda_functions`,
  `test_build_aws_inventory_lambda_defaults_to_empty_list`, `test_list_lambda_census_discovers_deployed_function`
  (moto). QG green both repos (sentinels 7c8b210 / 050d9a4).
- 2026-07-09 — **Composite health status + hang detection shipped** (slot 12): `deployment-api@f5f6ff4`
  (`deployments_inventory.py`) — additive `DeploymentItem.composite_health_status` (renamed from an initial
  `health_status` to avoid a real field-name collision with the concurrently-shipped Tier-0 free-wins commit's OWN
  `health_status` field, a different concept — raw GCE instance status). `_composite_health_status()` computes 5 of the
  D.3 7 states with a real signal today: `dead` (the GCE aggregated-list join's key set doesn't contain the VM — also
  completes the separate "Hang detection" todo's control-plane half), `hung` (control-plane confirms running but
  heartbeat stale), `disk-full`, `oom-risk`, `working` (D.1 `/proc` metrics, already sampled by the heartbeat daemon).
  `stalled`/`workload-dead` degrade honestly to `"unknown"` — filed as a follow-on todo above now that their
  prerequisite signals (`object_delta`, `workload_alive`) landed from sibling slots mid-task. Required 3 separate
  `git pull --rebase --autostash` cycles (this file had 4+ concurrent slots landing sibling D.3/kinds-census commits in
  the same session) and one real hand-resolved merge conflict on `_vm_item`/`build_inventory`'s signatures + the
  `health_status` field-name collision — consolidated onto the Tier-0 commit's `vm_details_by_name` join so no separate
  running-set parameter was needed. Blocked-question BLK-7751ce11: operator approved Option B (additive field, compute
  `hung` now since its inputs already exist, degrade `stalled`/`workload-dead` honestly). 61+ unit tests pin the 5
  states + the honest-unknown fallback; full suite (4381 tests) + QG green (sentinel f5f6ff4).
- 2026-07-09 — **Workload-PID liveness shipped** (slot 7): `unified-trading-library@0265663b`
  (`unified_trading_library/lifecycle/signal_protocol.py`, `daemon.py`) — `SignalProtocol` gains a `cmd_pid_file` field
  - `read_cmd_pid()`/`workload_alive()` (`kill -0` semantics: `ProcessLookupError`→dead, `PermissionError`→alive-under-
    another-UID, any other `OSError`→dead); `HeartbeatDaemon._sample_workload_liveness()` samples it every heartbeat
    tick (independent of the terminal `exit_status_file` check in `complete()`, so a mid-run OOM-kill is visible before
    the wrapper's final `wait` writes the exit status — "kills the OOM-false-alive without the exit-file race" per the
    todo). `deployment-service@2794163` (`scripts/vm/vm-exec-with-gcs-tee.sh`, `deployment_service/vm/heartbeat_cli.py`,
    `deployment_service/deployments_registry.py`) — the wrapper already captured `CMD_PID` into `$PID_FILE` (line 169);
    it now also passes `--cmd-pid-file "$PID_FILE"` to the daemon at launch, even though the daemon starts BEFORE
    `CMD_PID` exists (`read_cmd_pid()` tolerates the file not existing yet and returns `None`/"unknown", never "dead").
    `DeploymentRegistryEntry.workload_alive: bool = True` (honest-unknown default, non-alarming for pre-2026-07-09 rows
    and non-VM callers without a configured `cmd_pid_file`) wired through `_entry_to_registry`/`_registry_to_entry`/
    `_vm_payload`. New tests: UTL `test_signal_protocol.py` (cmd-pid read/unparseable/own-pid-alive/fork-and-reap-dead)
  - `test_daemon.py` (stamps on known PID, leaves untouched when unconfigured, stamps `False` once the wrapper PID
    dies) + deployment-service `test_deployments_registry.py` (round-trip `False`, legacy-row defaults `True`). QG green
    both repos (UTL sentinel 0265663b — a QG_HOST_CONCURRENCY=1 governor-token wait inflated the FIRST run's wall clock
    to ~3100s, which failed only the sanctioned wall-clock meta-gate with every substantive check green; re-ran with
    `IGNORE_TIMEOUT=true` per codex quality-gates.md's documented transient-contention escape, completing in 132-232s
    once it actually held the token; deployment-service sentinel 2794163, 107s). Not yet wired into the deployment-api
    inventory route / composite health status — that's this plan's separate "Composite health status" P1 todo, which
    consumes `workload_alive` alongside the D.1 host-metric vector already shipped.
- 2026-07-09 — **Kind counts + filter extended to all 6 DeploymentKind values** (slot 15): `deployment-api@9353d28`
  (`deployment_api/routes/deployments_inventory.py`) — UAC `DeploymentKind` already carried all 6 kinds, so this was
  purely the inventory-route half: a `kind=` query filter (same case-insensitive pattern as `umbrella`/`cloud`/`status`)
  - a `counts_by_kind: dict[str, int]` rollup on `DeploymentInventoryResponse`, additive alongside the legacy
    `vm_count`/`cloud_run_job_count` (kept for UI back-compat). `counts_by_kind` only keys a kind actually present
    post-filter — a kind whose census hasn't shipped or failed this cycle is simply absent, never a fabricated `0`; this
    generic layer needs no changes as the remaining census todos (CLOUD_RUN_SERVICE/LAMBDA/CLOUD_FUNCTION) land.
    ECS_SERVICE already flows through it today (landed concurrently, `deployment-api@c90eaf4` — rebased cleanly, one
    one-line docstring conflict). New tests: `test_counts_by_kind_omits_absent_kinds`,
    `test_inventory_route_kind_filter`, `counts_by_kind` assertions in `test_inventory_route_mock_shape`. QG green
    (sentinel 9353d28, 142s).
- 2026-07-09 — **Tier-0 free wins surfaced** (slot 15): `deployment-api@517bbbe`
  (`deployment_api/routes/deployments_inventory.py`) — the GCE aggregated-list join (`get_vm_instance_details`,
  previously discarded down to just the running-VM-name set) is now threaded through `_load_gcp_vm_entries` ->
  `build_inventory` -> `_vm_item` and surfaced on `DeploymentItem` alongside the registry entry's
  `rows_in`/`rows_error`/`events_emitted` (already captured, only `rows_out` was wired) and a new derived
  `uptime_hours`. New fields (`rows_in`, `rows_error`, `events_emitted`, `uptime_hours`, `machine_type`, `zone`,
  `health_status`, `boot_disk_name`, `labels`) are all optional, defaulting to `None` for kinds without the underlying
  source (Cloud Run jobs, a VM absent from the join) — honest absence, never fabricated. New unit test
  `test_build_inventory_surfaces_tier0_free_wins` covers both the joined and unjoined paths plus Cloud Run job
  None-defaults. Rebased cleanly onto two concurrent same-file landings from this session (`eda5be5` service-health
  sub-taxonomy, `9d50835` dynamic Cloud Run census) — only a docstring merge conflict, resolved by keeping both
  paragraphs. QG green (sentinel 517bbbe, 188s).
- 2026-07-09 — **Service-health sub-taxonomy shipped** (slot 4): `deployment-api@eda5be5`
  (`deployment_api/routes/deployments_inventory.py`) — `ecs_service_health_status()` +
  `cloud_run_service_health_status()` implement the D.3 4-state set (`serving`/`scaled-to-zero`/`dead`/`degraded`) as
  pure, testable classifiers (mirrors the existing local `_vm_status` pattern). `scaled-to-zero` is checked first so an
  intentional `desired_count==0` (or Cloud Run `min_instance_count==0` + no active instances) never reads red; `dead`
  fires on `desired>0, running==0` or Cloud Run `ready is False` (priority over scale-to-zero config — "should be up,
  isn't" beats "configured off"); `degraded` covers partial capacity, unknown ready-state, and an over-threshold
  error-rate (v1 default 0.05, undocumented SLO — no committed number in the plan, revisit with operator feedback). 15
  unit tests (`tests/unit/test_service_health_taxonomy.py`) pin every state + the two boundary cases (`>` not `>=` on
  the error-rate threshold; dead-beats-scaled-to-zero priority). **Not yet wired to live inventory rows** — this plan's
  `ECS_SERVICE`/`CLOUD_RUN_SERVICE` kinds-census todos (still unchecked, `DeploymentKind` doesn't carry those kinds yet)
  are the prerequisite census that will call these; scoped this way to avoid duplicating/colliding with those
  separately-tracked todos. QG green, sentinel=eda5be5.
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
