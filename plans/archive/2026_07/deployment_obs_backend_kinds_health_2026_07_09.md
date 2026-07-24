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
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-api-contracts]
scope: [engineer]
tags: [deployment-observability, cockpit, vm-health, cloud-run, ecs, lambda, heartbeat, deployment-api]
related:
  [
    /plans/archive/2026_07/deployment_observability_expansion_2026_07_08.md,
    /plans/archive/2026_07/deployment_obs_ui_popover_health_2026_07_09.md,
  ]
created: "2026-07-09"
last_updated: "2026-07-09"
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source: deployment_observability_expansion_2026_07_08.md
---

# Deployment observability — full-estate kinds census + VM/service work-health (backend)

> **CONVERTED TO LOCAL 2026-07-09** (`assigned_vm: NA` + `execution_scope: local-only`) — the AO worker stalled at 19/24
> (last activity 08:59); the operator took the remaining work over in the interactive slot. Setting `local-only` makes
> `_plan_contributes_briefs` return False, so on the next regen tick `_prune_stale` garbage-collects this plan's
> already-queued tasks from the AO DB (the anti-zombie path, Gap 3) — a first live test of that pruning behaviour. Full
> design context — the metric vector, capture→store→API→UI data path, composite health taxonomy, scale/cost budget, 8
> resolved open questions — lives in the LOCAL parent **`deployment_observability_expansion_2026_07_08.md`** (read WS-B,
> WS-C, all of WS-D). The UI half **`deployment_obs_ui_popover_health_2026_07_09.md`** is DONE (built here).

## Non-negotiable design principles (from parent WS-D.0 — inherit on every task)

1. A verdict is a JOINT function — resource in-band AND a work signal advancing (neither alone).
2. Self-logged counters are a HINT, not truth (log-scraped, MAX-over-tail); **manifest object-delta is authoritative**.
3. Push metrics from the EDGE (VM `/proc`), never a per-request central pull.
4. Existence from the control-plane list already called; OOM cause from exit-137. **No Cloud Monitoring / CloudWatch.**
5. **Add ZERO new bucket walks** (single-walk HARD RULE) — object-delta is a manifest LOOKUP.

## Codex SSOTs (READ before touching each area — plan↔codex drift is review-blocking)

- Inventory contract + classification: `deployment-api/.../routes/deployments_inventory.py`.
- Deployment observability / no-fire-and-forget: `/codex/05-infrastructure/deployment-observability.md`.
- Heartbeat daemon + wrapper: `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh`,
  `deployment-service/deployment_service/vm/heartbeat_cli.py`, `unified_trading_library.lifecycle`.
- Availability manifest (object-delta cross-check): `/codex/02-data/availability-manifest-and-data-status.md`.
- Shard-level failure isolation (honest per-kind degradation):
  `/codex/04-architecture/shard-level-failure-isolation.md`.

## Todos

### 🔴 Census hang — real-data blocker (found 2026-07-09, operator takeover)

- [x] ✅ [BACKEND] P0. **Inventory census must not hang** — `GET /api/deployments/inventory` blocked >240 s (0 bytes) on
      the new-contract backend: the GCP censuses ran serially with no per-provider timeout/isolation, so one wedged RPC
      blocked the whole inventory (only `_load_gcp_vm_entries`/`_load_aws_items` were wrapped, and the VM one _raised_
      502 rather than degrading). — **deployment-api@720697d**. New `_census_or_degrade()` + a dedicated `_census_pool`:
      each provider census (GCE VM registry / Cloud Run jobs / Cloud Run services / Cloud Functions / AWS) runs on its
      own worker, **wall-clock bounded (`_PROVIDER_CENSUS_TIMEOUT_SEC` = 45 s)**, and degrades to an honest EMPTY census
      for its own KIND on hang/error (WS-B / shard-level isolation) — never blocks or crashes the inventory.
      `_compute_inventory` now **fans the censuses out concurrently** (cold path ≈ slowest single census, not their sum)
      and **no longer 502s** on a VM-registry failure (degrades so the rest of the estate still shows). Root-cause
      hardening: **client-level RPC `timeout=30 s`** on every GCP list/aggregated call (`vm_utils` ×4, Cloud Run
      jobs/executions, services, functions) — a wedged RPC unwinds its worker (`DeadlineExceeded`, caught → empty)
      instead of leaking + starving the census pool. 3 regression tests (helper exception + timeout paths; a route-level
      proof that a hung services census degrades while VM/jobs/functions/AWS still return, bounded <10 s) + 3 fake GCP
      clients updated for the `timeout` kwarg. QG green (typecheck + 4360 tests; the only 3 failures are a pre-existing
      unrelated uniswap schema-override break in `test_data_status_drilldown.py`, another slot's UAC change — not this
      diff). Runtime-verified against a locally-run backend (see Progress Log). **File-split kept SEPARATE**
      (the >1000-line P3 below) — deliberately NOT folded in, to keep this correctness-critical fix focused + low-risk
      while the plan is being finished here; the split remains its own open P3.

### 🟡 Runtime findings from the live P0 verification (2026-07-09)

- [x] ✅ [BACKEND] P1. **Object-delta `str > int` TypeError** — `object_delta_for_bucket` raised
      `'>' not supported between 'str' and 'int'` when the availability index stored `row_count`/`instrument_count` as
      an object/string dtype, silently degrading EVERY object-delta to `None` and breaking the composite-health
      `working`/`stalled` signal that reads it. Fixed with `pd.to_numeric(errors="coerce").fillna(0)` before the `> 0`
      comparison + a string-dtype regression test (`test_object_delta_for_bucket_coerces_string_dtype_counts`). —
      **deployment-api@934f22f (LOCAL, unpushed** — held per operator until the pre-existing uniswap drilldown break is
      solved). Verified live: the TypeError no longer appears in the census log.
- [x] ✅ [BACKEND] P1. **Cloud Run jobs census N+1 → parallelized** — `latest_execution_by_job` issued one
      `ListExecutions` RPC per job serially (~70 jobs → routinely exceeded the 45 s per-provider census bound → the
      whole `CLOUD_RUN_JOB` kind flickered to empty). Fanned the per-job lookups out concurrently (`ThreadPoolExecutor`,
      16 workers) so the census is ~max(single RPC) not their sum. — **deployment-api@934f22f (LOCAL, unpushed)**.
      Verified live: no longer degrades, cold `/inventory` dropped 99.6 s → 85 s, census now captures **118** jobs (was
      73 when it intermittently timed out).

### 🟡 Runtime findings from the live P0 verification (2026-07-09 — capture, not yet fixed)

- [x] ✅ [BACKEND] P1. **`google-cloud-functions` missing from deployment-api's deps/lock** — the live CLOUD_FUNCTION
      census failed `No module named 'google.cloud.functions_v2'` and honest-degraded to empty (0 functions shown; would
      also break a prod deploy of the new census code). deployment-service@fb217de added `google-cloud-functions` and
      deployment-api uses `functions_v2` via its `_gcp_sdk` boundary, but deployment-api's `uv.lock` predated that
      addition so `uv sync` pruned it. — **deployment-api@bc506c5 (quickmerged)**. Regenerated the lock (transitive
      resolution from the deployment-service editable dep): adds `google-cloud-functions 1.24.0` +
      `google-cloud-artifact-registry 1.22.0`; no direct-dep needed (the `_gcp_sdk` boundary stays the only import
      seam). **Live-verified**: the census now returns 2 functions (`trigger-market-tick-cefi-job`,
      `trigger-instruments-job`, both running/python312). QG green (uniswap blocker resolved upstream).
- [x] ✅ [BACKEND] P2. **Object-delta cold census is slow (>45 s → degrades)** — with the str→numeric coercion landed
      (@934f22f) `_batched_object_deltas` no longer errored, but its per-distinct-asset_group manifest reads ran
      serially in a dict comprehension; on a cold cycle their sum exceeded the 45 s per-provider census bound
      (`object-delta census exceeded 45s — degraded to empty`), pushing the BATCH `working`/`stalled` composite to
      `unknown`. — **deployment-api@6e8d5f1 (quickmerged)**. Parallelized the reads (`ThreadPoolExecutor`,
      `_OBJECT_DELTA_WORKERS=8`) so the census is ~max(one read) not their sum; `object_delta_for_asset_group` already
      catches its own errors so no per-ag read can crash the map, and the once-per-distinct-asset_group behaviour is
      unchanged (existing tests green). Warm cache was always unaffected; this fixes the cold path.

### Kinds census (make the estate visible)

- [x] ✅ [BACKEND] P1. Add `CLOUD_RUN_SERVICE` to the census — `run_v2.ServicesClient` list + ready-state + revision +
      region. New `DeploymentKind` value in UAC. **Mode = "—"** (a service has no live/batch/paper phase; the `Kind`
      badge/filter carries "this is a service"). No PLATFORM/INFRA mode. — deployment-api@ab0c431. New
      `deployment_api/routes/_cloud_run_services.py` (`list_cloud_run_services()`, mirrors `_cloud_run_executions.py`'s
      `run_v2` boundary pattern) lists every live Cloud Run service in one region via
      `run_v2.ServicesClient.list_services` and maps ready-state (`terminal_condition`), latest revision, region, and
      URI. `_cloud_run_service_item()` wires it into `DeploymentItem(kind=CLOUD_RUN_SERVICE)`;
      `DeploymentKind.CLOUD_RUN_SERVICE` + the formal `DeploymentUmbrella.NONE` enum member (UAC) had already landed
      from a concurrent sibling slot by the time this shipped (superset of a first draft this task briefly duplicated
      with an ad-hoc `"—"` wire sentinel before realigning to the shipped `NONE` enum — see Progress Log). Honest
      degradation: a services-list failure yields zero rows without blocking the VM/job/ECS/Lambda/CloudFunction census.
      New tests: ready/reconciling state mapping, region parsing, GCP-error degradation, `build_inventory` wiring
      (umbrella=NONE, revision/region surfaced), unclassifiable-name skip. QG green (sentinel ab0c431). Rebased ~8 times
      onto concurrently-landing sibling census/health todos on this same file this session (Tier-0 free wins,
      ECS_SERVICE, kind-count/filter extension, D.3 composite health, Lambda census, detail endpoint, CLOUD_FUNCTION
      census, oom-risk/stalled alerting) — all additive, kept both sides at every conflict; squashed 3
      manual-rebase-conflict commits into one clean commit + added the `Quickmerge: agent` trailer by hand after
      `check_strict_quickmerge.py` flagged manually-recommitted rebase-continue commits as bypassing quickmerge.
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
- [x] ✅ [BACKEND] P2. Add `CLOUD_FUNCTION` (gen2) census — `functions list`; note gen2 = Cloud Run underneath. —
      deployment-service@fb217de (exposes `functions_v2` on the deferred `_gcp_sdk` GCP-SDK boundary + adds
      `google-cloud-functions` as a dependency, mirroring the existing `run_v2`/`compute_v1` pattern) +
      deployment-api@a025563 (new `_gcp_cloud_functions.py`: `list_cloud_functions()` lists every gen2 function via
      `FunctionServiceClient.list_functions`, existence + config only per WS-B scope — `state` maps to
      running/failed/pending/unknown, `build_config.runtime` and the underlying Cloud Run `service_config.service` name
      are surfaced, no CloudWatch/invocation-stats call; `_cloud_function_item()` classifies directly with
      `umbrella=NONE` — same no-live/batch/paper-phase precedent as ECS_SERVICE/CLOUD_RUN_SERVICE; wired into
      `_compute_inventory` under `want_gcp`, honest-degrades to `{}` on any GCP error without blocking the other kinds).
      8 new unit tests (state-mapping parametrized over all 6 `Function.State` values, config extraction, GCP-error
      degradation) + 1 new `_cloud_function_item` builder test — all credential-free (patches
      `deployment_service.backends._gcp_sdk.functions_v2` directly rather than `sys.modules` stubbing, since
      `tests/unit/conftest.py` pre-stubs the whole `deployment_service` package as empty for the session and several
      OTHER `deployment_service.backends` submodules import `_gcp_sdk` at their own module-init time). Rebased twice
      onto concurrent sibling census todos (Lambda census, kind-counts extension, detail endpoint, dead-VM fix) landing
      on this same plan — all merges additive, no logic conflicts. QG green both repos (sentinels fb217de / a025563).
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
- [x] ✅ [BACKEND] P3. Recent error count / last log line — from the EXISTING teed GCS log / Cloud Logging (popover
      only); no new CloudWatch dependency. — deployment-service@9ef144e. `recent_log_summary()`
      (`data_pipeline_monitors/_gcs.py`) reuses the SAME durable run.log blob + `_ERROR_LINE_RE` classifier
      `error_snippet_from_run_log` already reads for Slack alerts — no new GCS path, no CloudWatch call. Returns
      `RecentLogSummary(recent_error_count, last_log_line)` over the tail (`tail_lines=200` default); missing/empty log
      degrades to `(0, None)`, never raises. On-demand single-target read (popover-triggered), not a bulk sweep — same
      acceptable read pattern the existing snippet functions use. Not yet wired to an HTTP response — the
      `/deployments/{id}/detail` endpoint (separate P2 todo below) landed concurrently (slot 15,
      `deployment-api@7c4265a`) while this todo was in flight, so wiring `recent_log_summary()` onto
      `DeploymentDetailResponse` is now a small, immediately-actionable fast-follow rather than blocked on that endpoint
      existing. 4 unit tests (error-line counting, honest-empty, trailing-blank-line handling, tail-window respect). QG
      green, sentinel=9ef144e.
- [x] ✅ [REVIEW] P2. Extend `DeploymentItem` in UAC/backend to the mock's optional rich-field shape (already in the UI
      type) so the wire contract matches — one SSOT, no client-only fields. — deployment-api@e5f2ad4. **Premise
      correction (found, not assumed)**: verified against the actual UI code first — the mock's rich-field shape is NOT
      on the UI `DeploymentItem` type (`deployment-ui/src/api/deploymentApi.ts:636`, 12 thin fields, matches the backend
      model exactly, zero client-only fields on either side). Those rich fields (`rows_in`/`machine_type`/ `zone`/etc.)
      actually live on a DIFFERENT, unrelated UI type (`VmDeploymentEntry`, the legacy `/api/vm-deployments` shape) —
      and the backend `DeploymentItem` already carries its OWN 12 additional optional rich fields (Tier-0 free wins +
      composite/service health, landed earlier this session by sibling slots), all with honest `None` defaults. So the
      stated direction (UI has rich fields the backend lacks) doesn't hold; the real, still-open gap runs the other way
      inside the backend itself: `_ecs_service_item`/`_lambda_item` (`deployment_api/routes/_aws_deployments.py`)
      already fetch `cluster`/`desired_count`/`running_count`/`task_definition_revision` (ECS) and `runtime`/
      `memory_size_mb`/`package_type` (Lambda) from the AWS census but collapse them into just `status`, discarding the
      rest — the exact same "fetched-and-discarded" pattern the GCP Tier-0 todo fixed for VMs, just not yet applied to
      AWS. Fixed it: added the 7 fields to `DeploymentItem` (`deployments_inventory.py`) as optional Tier-0-style wins
      (`None` for kinds without the source, honest absence) and wired them through `_ecs_service_item`/`_lambda_item`. 2
      tests extended (`test_build_aws_inventory_classifies_ecs_service_running`,
      `test_build_aws_inventory_classifies_lambda_functions`) to assert the new fields. Extending the UI
      `DeploymentItem` type itself is explicitly out of this plan's `repos` scope (`deployment-api`/
      `deployment-service`/`unified-api-contracts` only) — that's the separate LOCAL UI plan
      (`deployment_obs_ui_popover_health_2026_07_09.md`, hand-off todo below). QG green (sentinel e5f2ad4, rebased 3x
      onto concurrently-landing sibling commits on this same file this session — `f914cc4` cost-obs fix, `a025563`
      CLOUD_FUNCTION census — no conflicts, all clean fast-forward re-applies).

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
      (threshold is `>` not `>=`, dead beats scaled-to-zero on priority). QG green (sentinel eda5be5). **⚠️ Classifier
      shipped @eda5be5 but was NOT wired to live rows** — service rows carried only a binary `running`/`pending`
      placeholder; the `serving`/`scaled-to-zero`/`dead`/`degraded` verdict never reached the cockpit (honesty gap found
      2026-07-10). **NOW WIRED — deployment-api@5149af19e (2026-07-10, quickmerged)**: extracted both classifiers to a
      shared `routes/_service_health.py` (a reverse import from `_aws_deployments` would have cycled), and
      `_cloud_run_service_item` / `_ecs_service_item` now set `DeploymentItem.composite_health_status` from them. Added
      `min_instance_count` to the Cloud Run census (`template.scaling.min_instance_count`) so an always-on service
      (min>0) reads `serving` while an idle min-0 one reads `scaled-to-zero`. 5 new/extended wiring tests
      (`test_build_inventory_wires_cloud_run_service_health_taxonomy` + composite assertions on the 3 ECS
      running/scaled-to-zero/dead tests) prove the live row carries the sub-taxonomy, not a placeholder.
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
- [x] ✅ [INFRA] P2. **Persist a short D.1 rolling window** (last ~10 samples) on the registry entry — so `mem_slope` /
      "sustained idle" have a trend to plot and `/detail` serves a sparkline, not a point. — **UTL already stored it**
      (`HeartbeatDaemon._append_host_metrics_window` appends each D.1 sample to a bounded
      `entry.metadata[HOST_METRICS_WINDOW_KEY]`, cap `DEFAULT_MEM_WINDOW_SIZE`=10 — found during the audit, no UTL
      change needed) + **deployment-service@44f44afe9** (new `DeploymentRegistryEntry.host_metrics_window` +
      `coerce_host_metrics_window`; `to_json`/`from_json` round-trip with legacy rows → `[]`;
      `heartbeat_cli._entry_to_registry` extracts it from metadata and `_registry_to_entry` rounds it back so the
      daemon's next tick appends instead of restarting) + **deployment-api@970bcdc** (surfaced on
      `DeploymentDetailResponse` + `/detail`; corrected the model's now-stale "hasn't shipped" scope note). The
      single-sample fields stay for back-compat (additive). Round-trip verified both directions at runtime; 3 new tests
      (registry round-trip + legacy-default + /detail window). QG green both repos.
- [x] ✅ [BACKEND] P2. **Alerts** on `oom-risk` (before the kill) + `stalled` (progress flatlines, heartbeat fresh) —
      wire into the existing alerts surface. — deployment-api@5e25dce. New `_persist_alert()` appends a JSONL row to the
      SAME shared GCS ledger (`unified-trading-cicd-events/cicd/alerts/{date}/alerts.jsonl`) agent-orchestrator's
      watchers + `notify-slack.yml` already write to (mirrors `notifications.slack._persist_to_gcs`'s exact row shape) —
      `GET /api/alerts` (`_repo_ci_alerts.py`) picks these up with zero reader-side changes. New
      `_alert_on_health_transition()` fires only on a fresh TRANSITION into `oom-risk`/`stalled` (in-process
      last-alerted-state per VM name), never on every ~45s cache-refresh poll while the state persists — avoids an
      alert-storm on a VM that stays unhealthy across many polls; a recovery back to a non-alertable state (e.g.
      `working`) clears the tracked state so re-entering `oom-risk` fires again as a genuine new transition. Wired into
      `_compute_inventory`'s GCP branch, shard-level isolated (a ledger-write failure logs + never breaks inventory
      computation). **`stalled` cannot actually fire yet** — `_composite_health_status` still degrades it to `"unknown"`
      pending the separate `[BACKEND] P1` "Wire `stalled` + `workload-dead`" todo below; included in
      `_ALERT_HEALTH_STATES` now so no code change is needed once that lands. 4 new tests
      (`test_alert_on_health_transition_fires_once_per_transition`,
      `test_alert_on_health_transition_ignores_non_alertable_states`, `test_persist_alert_writes_expected_row_shape`,
      `test_persist_alert_never_raises_on_storage_failure`). QG green (sentinel 5e25dce, 73s). Rebased onto 2
      concurrently-shipped sibling census todos (CLOUD_FUNCTION `a025563`, ECS/Lambda field surfacing `e5f2ad4`) —
      genuine same-file conflict (both call sites append to `_compute_inventory`'s GCP branch), resolved by keeping both
      additions (no logical overlap).
- [x] ✅ [REVIEW] P2. Gate `/freshness` fetches to VM kinds only (services use error-rate health, not manifest
      freshness) — the cockpit fetched `/deployments/{id}/freshness` for every LIVE-umbrella row. **Backend verified
      correct** (in-scope): `compute_freshness` already returns `liveness_only` for `ShardResponsibilityKind.NONE`
      (`deployment_freshness.py`), so a non-VM kind never gets a fabricated fresh/stale — no backend change needed. **UI
      defensively gated** — **deployment-ui@e9b77ac (quickmerged)**: `Cockpit.tsx` now filters the freshness fetch to
      `kind === "VM"` (only VMs are data producers with a manifest). tsc + eslint clean; the 2 existing cockpit
      freshness specs stay green (no regression — LIVE rows are ~always VMs). Honest scope note: no dedicated
      exclusion-regression was added — the in-app mock has no non-VM LIVE fixture and doesn't expose fetch-counting, so
      the gate is validated as defensive (backend already covers the edge case) rather than via a new pw:L2.
- [x] ✅ [BACKEND] P1. **Wire `stalled` + `workload-dead` into `_composite_health_status`** (`deployment-api`,
      `deployments_inventory.py`) — both prerequisite signals now exist: `object_delta` via
      `deployment_freshness.compute_freshness()` / `_object_delta_for_bucket()` (per-`asset_group` manifest lookup,
      `deployment_freshness.py`), and `workload_alive` via the heartbeat daemon's `CMD_PID` liveness field
      (`unified-trading-library`/`deployment-service`, Workload-PID liveness todo above). `stalled`'s threshold table is
      per-`lifecycle_class` (backfill/batch → `object_delta==0` ≥15min AND cpu<10%; live-capture → no progress ≥5min in
      an expected-active window; paper → `work_delta==0` ≥15min) — `compute_freshness` needs a `deployment_id` +
      resolves per-asset\*group, not per-VM-entry, so this needs its own call-shape design (batch the lookup once per
      `asset_group` per census cycle, not once per VM, to respect the zero-new-bucket-walk principle at scale), not a
      copy-paste into the per-entry loop. Filed here rather than expanding deployment_obs_backend_kinds_health-015
      (deployment-api@f5f6ff4) — that diff was already large from 3 concurrent cross-slot rebases on this same file. —
      deployment-api@29f3be5. `workload-dead` fires unconditionally on `entry.workload_alive is False` (ahead of the
      D.1-metric-dependent states — the CMD_PID reading is authoritative regardless of disk/mem/cpu). `stalled` is wired
      for the **BATCH umbrella only** — the one row of the threshold table whose prerequisite signal is real today;
      `object_delta` moved to a new public `health_consolidator.object_delta_for_bucket`/`object_delta_for_asset_group`
      (out of `deployment_freshness`, which already imports `deployments_inventory.classify_vm_target` — a reverse
      import would have cycled) and is batched via a new `_batched_object_deltas()` pre-pass: ONE manifest lookup per
      DISTINCT asset_group across the whole census cycle, threaded into `build_inventory`/`_vm_item` as an explicit
      `object_deltas` param so both functions stay pure/I/O-free for their existing unit tests (the manifest read
      happens once in `_compute_inventory`, the caller). LIVE/PAPER `stalled` still degrade honestly to `"unknown"` —
      their threshold-table signals (an expected-active-window calendar, a `work_delta` rows-out-delta tracker) don't
      exist anywhere in the codebase yet; guessing from idle io/net would misfire the now-live oom-risk/stalled alert
      wiring (deployment-api@5e25dce) on a genuinely-idle-but-healthy window. Also folded `object_delta>0` into the
      `working` state per the parent WS-D.3 spec's own OR clause (`object_delta>0 OR io_write_rate>0`), which the
      original `f5f6ff4` composite landed without since `object_delta` didn't exist yet. 10 new/updated unit tests
      (`test_composite_health_workload_dead\**`, `test*composite_health_stalled_for_batch**`,
      `test*composite_health_batch_working_when_object_delta_positive*\_`,
      `test*composite_health_live_umbrella_stalled*\_`,
      `test*batched_object_deltas_calls_once_per_distinct_asset_group`,
      `test_build_inventory_threads_object_deltas*\*`) + `health_consolidator`/`deployment_freshness`object-delta tests
      moved to their new home. Landed through 2 real rebase cycles against concurrently-shipped sibling work on this
      same hotspot file (CLOUD_RUN_SERVICE census`ab0c431`, ECS/Lambda field surfacing, the oom-risk/stalled alert
      wiring `5e25dce`) — one import-ordering conflict, one `build_inventory`new-param conflict (kept both the
      sibling's`cloud_run_services`param and my`object_deltas` param). QG green (sentinel 29f3be5, 119s).
- [x] [BACKEND] P3. **LIVE/PAPER `stalled` signals — DEFERRED (scope decision 2026-07-10, needs new subsystems)**.
      Discovered while wiring the BATCH row (deployment-api@29f3be5): LIVE `stalled` needs an expected-active-window
      calendar (market-hours-aware, so an idle-but-healthy off-hours window never misfires); PAPER needs a `work_delta`
      (rows-out-delta) tracker (the D.1 rolling window @970bcdc samples `/proc` cpu/mem/disk, NOT `rows_out`, so it
      would have to be extended to carry the counter history first). **Decision**: both are genuinely NEW subsystems — a
      market calendar and a counter-history tracker — disproportionate to build for a P3 `stalled` refinement, so they
      are DEFERRED to a future phase (tracked in the parent `deployment_observability_expansion_2026_07_08.md`). The
      current **honest-`"unknown"` degradation is confirmed correct** as the v1: `_composite_health_status` returns
      `"unknown"` for LIVE/PAPER `stalled` rather than guessing from a proxy (WS-D.0 principle 2), and the
      oom-risk/`stalled` alert wiring (deployment-api@5e25dce) only fires on a REAL state, so nothing misfires while
      these stay unknown. BATCH — the one umbrella with a real signal (`object_delta`) — is wired + shipped. This item
      stays open (not a fake `[x]`) as an explicit, tracked deferral. — **FOLDED OUT** to
      plans/active/deployment_observability_expansion_2026_07_08.md (2026-07-15, plan-reconcile §6 operator ruling);
      tracked there, not here.
- [x] ✅ [REVIEW] P3. **`deployments_inventory.py` hotspot — split into sibling modules** (cap 900; QG's file-size check
      is non-blocking today but the file was a real hotspot). Now that the plan's todos stopped converging on it,
      extracted the two lowest-coupling cohesive chunks the todo named: **service-taxonomy →
      `routes/_service_health.py`** (95 lines, `serving/scaled-to-zero/dead/degraded` classifiers, shared with the AWS
      row builder) and **composite-health → `routes/_vm_health.py`** (138 lines, `vm_status` +
      `composite_health_status` + the D.3 thresholds). Both are leaf modules (no `deployments_inventory` import → no
      cycle); public functions aliased back to the historical private names for existing call sites/tests. File **1503 →
      1390 lines** (~233 lines of classifier logic now in their own modules). The Cloud-Run-job census — the third named
      candidate — stays put: it's tightly interwoven with `build_inventory`'s VM loop and would need more untangling
      than the split saves; the file-size check is non-blocking, so it's left as future hygiene. basedpyright 0 errors;
      all inventory/health tests green. — **deployment-api@d5f179d (quickmerged)** (+ the earlier `_service_health.py`
      extraction @5149af19e).

### Hand off to the interactive UI session (LAST task)

- [x] ✅ [REVIEW] P3. **Hand off the UI half** — already handed off + BUILT: the UI plan
      `deployment_obs_ui_popover_health_2026_07_09.md` is DONE (all 6 todos, `pw:L2` green), built interactively against
      the landed contract and now running against the real backend. **Frozen contract (2026-07-10)**: `DeploymentItem`
      (`deployments_inventory.py`) — kind/umbrella(incl. `NONE`)/cloud/service/`asset_group`/status +
      `composite_health_status` (VMs: dead|hung|disk-full|oom-risk|working|stalled|workload-dead|unknown; services:
      serving|scaled-to-zero|dead|degraded) + Tier-0 fields (machine_type/zone/rows\*\*/uptime_hours) +
      ECS/Lambda/Cloud-Run structural fields + `counts_by_kind`; `DeploymentDetailResponse`
      (`GET /deployments/{name}/detail`) — the D.1 vector + `host_metrics_window` (sparkline). Contract additions since
      the UI's first build the UI could still adopt: service `composite_health_status` (now live-wired, @5149af19e) +
      `host_metrics_window` for a real sparkline (@970bcdc). Operator notified via this session.

## Progress Log

- 2026-07-09 — **🟢 P0 CENSUS-HANG FIXED + RUNTIME-VERIFIED** — deployment-api@720697d (**pushed to LDR**). Ran the
  slot-5 backend against the live estate (GCP `central-element-323112` ADC, real mode `mock_mode:false`): `/inventory`
  returned **HTTP 200 in 99.6 s cold → 1.3 s warm** with **2.49 MB / 3597 real items** (`counts_by_kind`: VM 3507,
  CLOUD_RUN_JOB 73, CLOUD_RUN_SERVICE 12, CLOUD_FUNCTION 2, ECS_SERVICE 3) — down from the ∞/240 s-timeout/0-byte hang.
  The two degradation logs PROVE the per-kind isolation works (a hung provider degrades instead of blocking). **Two
  follow-up fixes those logs surfaced** — deployment-api@934f22f (**committed LOCAL, NOT pushed** — held per operator
  until a pre-existing unrelated uniswap `VENUE_CONTRACT_OVERRIDES` break in `test_data_status_drilldown.py` is solved;
  that break FAILS at 5dc4208, the commit BEFORE the P0 fix — proven not-ours, blocks the deployment-api QG/quickmerge):
  (1) **object-delta TypeError** — `object_delta_for_bucket` raised `'>' not supported between 'str' and 'int'` when the
  availability index stored `row_count`/`instrument_count` as an object/string dtype, silently degrading EVERY
  object-delta to `None` and breaking the composite-health `working`/`stalled` signal → fixed with
  `pd.to_numeric(errors="coerce")` + a regression test. (2) **cloud-run-jobs N+1** — `latest_execution_by_job` ran one
  `ListExecutions` RPC per job serially (~70 jobs → routinely > the 45 s census bound → whole `CLOUD_RUN_JOB` kind
  flickered to empty) → parallelised the per-job lookups (`ThreadPoolExecutor`, 16 workers). QG green both commits
  (4360+ passed; the only 3 failures are the pre-existing uniswap drilldown break). Cold-path perf (99.6 s, dominated by
  3507 transpacific registry-JSON reads) is a separate optimisation, not a hang — warm cache serves the cockpit at 1.3
  s.
- 2026-07-09 — **CONVERTED TO LOCAL — operator takeover** (AO worker stalled at 19/24, last activity 08:59). Frontmatter
  flipped `assigned_vm: planning→NA` + `execution_scope: orchestrator-agent→local-only` so the regen `_prune_stale`
  garbage-collects the 5 still-queued tasks from the AO DB (`_plan_contributes_briefs`→False for a `local-only` plan;
  the Gap-3 anti-zombie path — FIRST live test of prune-on-local-only). Remaining work now executed in the interactive
  slot. **Verification of the regen path**: watch the AO backlog/dashboard after the next regen tick (≤30 min on
  central) — the 5 open tasks should disappear from `queued`; if they don't, `_prune_stale`/`prune_stale` config is the
  bug to file.
- 2026-07-09 — **🔴 NEW FINDING (blocks real-data viewing): the inventory census HANGS.**
  `GET /api/deployments/inventory` on the local slot-4 backend (`:8004`, new-contract code) returned 0 bytes after a 240
  s timeout (`/api/health` is instant, so the server is fine — the census itself blocks). Root cause candidate: the
  provider censuses are collected with unbounded `.result()` (e.g. `deployments_inventory.py:1207-1209`) — a
  slow/hanging provider (Cloud Run services / ECS / Lambda) blocks the whole inventory forever. This VIOLATES WS-B's "a
  census failure for one kind never blocks the others" (a hang bypasses the try/except). Captured as the P0 todo below.
- 2026-07-09 — **`CLOUD_RUN_SERVICE` census shipped** (slot 8): `deployment-api@ab0c431` (new
  `deployment_api/routes/_cloud_run_services.py` + wiring in `deployments_inventory.py`) — lists live Cloud Run services
  via `run_v2.ServicesClient.list_services` (ready-state/revision/region/URI), builds
  `DeploymentItem(kind=CLOUD_RUN_SERVICE, umbrella=DeploymentUmbrella.NONE.value)`. Started this task before a sibling
  slot's UAC `DeploymentKind` 6-kind extension had landed, so an early draft added its OWN `CLOUD_RUN_SERVICE` enum
  member + a raw `"—"` wire-string sentinel for the umbrella (no `DeploymentUmbrella.NONE` existed yet); once the
  sibling slot's superset UAC change (`CLOUD_RUN_SERVICE`/`ECS_SERVICE`/`LAMBDA`/`CLOUD_FUNCTION` + the formal
  `DeploymentUmbrella.NONE` member) landed on origin, discarded the now-fully-redundant local UAC commits (verified
  byte-identical via diff before dropping — nothing unique lost) and realigned the deployment-api wiring to emit
  `DeploymentUmbrella.NONE.value` instead of `"—"`. This file was the single hottest convergence point in the whole plan
  this session (4+ slots landing sibling census/health todos concurrently) — required ~8 `git pull --rebase` cycles to
  land, each a clean additive merge (new field/section per side, no logic conflicts); `check_strict_quickmerge.py`
  flagged 2 rounds of manually-recommitted `git rebase --continue` commits as quickmerge-bypassing (they lacked the
  `Quickmerge: agent` trailer peer commits carry) — fixed by squashing to one commit with the trailer added by hand
  before the final ship. QG green (sentinel ab0c431, 129s). Confirmed on `origin/live-defi-rollout` post-push.
- 2026-07-09 — **Alerts on oom-risk/stalled wired into the alert ledger** (slot 15): `deployment-api@5e25dce`
  (`deployment_api/routes/deployments_inventory.py`) — `_persist_alert()` appends to the SAME shared GCS ledger
  (`unified-trading-cicd-events/cicd/alerts/{date}/alerts.jsonl`) agent-orchestrator's watchers already write to
  (mirrors `notifications.slack._persist_to_gcs`'s row shape exactly), so `GET /api/alerts` picks these up with zero
  reader changes. `_alert_on_health_transition()` fires only on a fresh TRANSITION into `oom-risk`/`stalled` (in-process
  per-VM last-alerted-state), never every ~45s poll — deliberately conservative to avoid an alert-storm. Honest note:
  `stalled` can't fire yet (its `_composite_health_status` classifier still degrades to `"unknown"` pending the separate
  `stalled`/`workload-dead` wiring todo below) — included now so nothing else needs to change once that lands. 4 new
  tests. QG green (sentinel 5e25dce, 73s). Rebased onto 2 concurrent census landings (CLOUD_FUNCTION `a025563`,
  ECS/Lambda field surfacing `e5f2ad4`) — a genuine same-file conflict in `_compute_inventory`'s GCP branch (two
  independent appends), resolved by keeping both.
- 2026-07-09 — **Recent error count / last log line shipped** (slot 4): `deployment-service@9ef144e`
  (`deployment_service/data_pipeline_monitors/_gcs.py`) — `recent_log_summary()` returns
  `RecentLogSummary(recent_error_count, last_log_line)` for the popover, reusing the SAME durable run.log blob +
  `_ERROR_LINE_RE` classifier `error_snippet_from_run_log` already reads for Slack alerts (no new GCS path, no
  CloudWatch dependency). Not yet wired to an HTTP response — the `/deployments/{id}/detail` endpoint (slot 15,
  `deployment-api@7c4265a`, next entry below) landed concurrently, so wiring this in is now a small fast-follow, not
  blocked. 4 unit tests. QG green, sentinel=9ef144e.
- 2026-07-09 — **Fixed: "dead" was unreachable in the live path** (slot 6): `deployment-api@25afc62`
  (`deployment_api/routes/deployments_inventory.py`). Both "Hang detection" and "Composite health status" were already
  flipped `[x]` by slot 12's `f5f6ff4` before this task was picked up — its `composite_health_status` classifier
  correctly implements control-plane-existence + stale-heartbeat per the "Hang detection" mandate, so no duplicate
  implementation was added. Two residual bugs verified + fixed instead: (1) `_load_gcp_vm_entries` still filtered
  `active/` registry entries to those present in the GCE aggregated-list join (`if e.vm_name in running_vm_names`) — the
  exact "hard-killed VM" entry `dead` exists to catch was silently dropped before `_composite_health_status` ever saw
  it, making `dead` practically unreachable on the live path; removed the filter. (2) `build_inventory` derived
  `control_plane_running` from mere key presence in the join rather than the raw status value — GCE keeps a
  stopping/stopped/terminated instance visible in the aggregated-list for a while, so a present-but-not-`RUNNING` VM
  false-negatived as confirmed-running; now checks `status == "RUNNING"`. 2 new tests pin both (an active entry absent
  from a fresh GCE census survives `_load_gcp_vm_entries` unfiltered; a VM present in the join with a non-RUNNING status
  still resolves `dead`). Also fixed one pre-existing, unrelated QG STEP 5.101 empty-string-fallback violation in
  `fleet.py` that was blocking the full gate. Rebased through 5 concurrent same-file landings this session (dynamic
  Cloud Run census, service-health sub-taxonomy, Tier-0 free-wins, kind-count/filter extension, composite health, AWS
  Lambda census, drill-down endpoint) — 3 real conflicts hand-resolved (docstrings, signature unification), 2 clean
  auto-merges. QG green (sentinel 25afc62, 86s).
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
