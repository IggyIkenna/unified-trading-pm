---
doc_type: plan
title: All-shard smoke matrix MTDS → ML — one day per shard, warm workers per (service × AG × data_type × instrument_type), manifest-only skip leg, empty-cell force leg, 64 GB ceiling
summary: >-
  Child of trading_pipeline_smoke_and_shard_telemetry_2026_08_22 (forked per task_template finding R). Runs the
  data-pipeline-check engine over EVERY shard from MTDS through MDPS, features and ML for one operator-given day — the
  existing shard proves skip time + performance, an empty -test- cell proves the full e2e — on long-lived worker VMs,
  one per (service × asset_group × data_type × instrument_type), × model_family for ML / strategy / execution (ruling
  D15, 2026-08-22): ~120-200 warm VMs instead of the 1-2k one-VM-per-(shard, leg) launches the engine does today, so VM
  boot is paid per worker not per shard. Skip leg is a manifest-only decision (no download), force leg is the single
  download + compute; every leg emits the standardised ShardRunTelemetry row. PROD consolidator liveness is asserted
  pre-run and -test- buckets are consolidated by triggering the prod-identical job --once after the run (D16). Memory
  management is improved before any machine resize and 64 GB RAM is a hard stop. /data-pipeline-alerts-reconcile and
  /vm-preemption-billing-waste-audit run interleaved while shards process.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, features, meta]
repos:
  [
    unified-trading-library,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    instruments-service,
    deployment-service,
    deployment-api,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [smoke-test, all-shards, warm-workers, vm-boot, baked-image, memory, 64gb-ceiling, alerts-reconcile, telemetry, consolidator]
related:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /plans/active/shard_plan_and_resource_driven_shapes_2026_08_22.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
    /plans/epics/system_readiness_master.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 15
estimate_calibrated_ai_days: 12
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: [trading_pipeline_smoke_and_shard_telemetry_2026_08_22]
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator interactive session + Q&A 2026-08-22 (slot 6) — "shard smoke tests for all shards just one day ... abstract away startup ... 64gb ram you need to hard stop ... all the smoke tests should be vms ... one vm per service x AG x data_type x instrument type ... if we know we are testing we can just trigger after all the tests"]
context_scope:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/06-coding-standards/service-orchestration-patterns.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/launcher.py,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/prod_precheck.py,
    unified-trading-pm/cursor-configs/skills/honest-coverage-dump/scripts/shard_universe.py,
    unified-trading-pm/cursor-configs/skills/data-pipeline-alerts-reconcile/SKILL.md,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf,
  ]
---

# All-shard smoke matrix MTDS → ML

> **Human plan**, child of
> [`trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`](/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md)
> (needs its T1 telemetry contract and T2 engine changes; the worker launcher consumes the `ShardPlan` from
> [`shard_plan_and_resource_driven_shapes_2026_08_22.md`](/plans/active/shard_plan_and_resource_driven_shapes_2026_08_22.md)).
> Rulings D9, D11, D12, D15 and D16 of the parent govern this plan.

## The startup arithmetic (why the runner shape is the whole plan)

- Today the e2e engine launches **one VM per (shard, leg)** from a stock image with `apt-get` + `uv pip install` at
  boot. 600+ shards × 2 legs × 5-10 min ≈ **100-200 h of boot** — 4-8 days serial — before any data moves, and the
  force + skip pair downloads twice when skip is implemented as a re-read.
- Target (D15): **one warm worker VM per (service × asset_group × data_type × instrument_type)**, × model_family where
  ML / strategy / execution optimise across many configs — **~120-200 workers**. With a baked image each boots in
  ~1 min, so total boot is ~2-4 h of VM-time spread across a parallel fleet (minutes of wall), versus 1-2k boots.
  Per shard: skip ≈ seconds (a cell read of the manifest, no download) + force ≈ minutes (one download + compute into
  an empty `-test-` cell). Download happens once. Reads come from PROD (or the previous layer's `-test-` output);
  writes go to `-test-` only.
- Per-shard time, bytes, peak RSS and $ land as `ShardRunTelemetry` rows (parent T1), so the matrix IS the capacity
  and cost baseline — the input the `ShardPlan` uses to choose horizontal vs vertical scaling.

## Memory ladder (D12)

Order of remedies before any resize: per-shard cleanup contract (`service-orchestration-patterns.md` § 15) → single
engine end-to-end → cell-scoped manifest reads (parent T3) → streaming reads (`shard_plan…` child) → read-once caches
(MTF) → `POLARS_MAX_THREADS` pinned → then the next machine shape. Ceiling `*-highmem-8` (64 GB). A shard whose peak
RSS still exceeds 64 GB after the ladder is a defect (issue doc + parent T4/T3 todo), never a bigger machine.

## Consolidators (D16)

Smoke cadence is roughly one run per shard per month, so `-test-` buckets get **no scheduled consolidator**. The
controller (a) asserts every PROD consolidator is live before starting (a lagging cycle warns, it does not block —
skip decisions read PROD and tolerate staleness), and (b) after the run — optionally between layers — triggers the
**prod-identical** Cloud Run job with `--bucket <test-bucket> --once`, so test coverage updates exactly the way prod
will, with zero config drift and no standing job cost.

## Todos

- [ ] [DATA] P0. **Enumerate the shard matrix** — IS/MTDS cells from coverage.json via `shard_universe.py`
      (`iter_shard_cells`), MDPS processed-candle atoms (`MDPS_DERIVABLE_DATA_TYPES` × timeframes), features
      feature-group atoms (`EXPECTED_FEATURE_GROUPS_BY_SERVICE`), ML model atoms (`ModelRegistry`), strategy slots
      (`StrategySlot.slot_label` × client) and execution (client × venue × region); group into the D15 worker units and
      write `plans/audit/results/benchmarks/all_shard_matrix_<date>.md` with the real shard + worker counts per service
      × AG and the chosen operator `--day` per AG. Done-when: the artefact exists and replaces "600+" / "120-200" here.
- [ ] [INFRA] P0. **Warm-worker runner** — add `--shard-list <file>` to the UTL `pipeline_e2e_check` engine so the
      per-shard loop (`for shard in shards` in the service drivers) runs ON the worker VM against a list, emitting one
      telemetry row per (shard, leg), checkpointing progress to
      `gs://<sink-bucket>/_ops/checkpoints/all_shard_matrix_<service>_<ag>_<data_type>_<instrument_type>.jsonl`
      (resumable, task-id-keyed). Done-when: one worker completes ≥ 20 shards with no re-boot and the checkpoint
      resumes after a kill.
- [ ] [INFRA] P0. **Worker launcher from the ShardPlan** — `launch-smoke-worker-vm.sh` registered in
      `VM_PREFIX_TO_BUCKET`, one VM per D15 unit, SPOT, shape + workers-per-VM read from the `ShardPlan` (never
      hard-coded), resume-from-checkpoint on preemption. Done-when: `/vm-resource-rightsizing-check` passes on the
      first 30-min run and no `MACHINE_TYPE=` literal exists in the launcher.
- [ ] [INFRA] P0. **Monitors acknowledge multi-shard VMs** — dp-heartbeat-watcher, dp-exit-code-monitor, the Cloud Run
      monitors and the `data-pipeline-alerts` registry treat one VM processing N shards as healthy while its checkpoint
      grows (progress metric), and attribute alerts per (AG, data_type, instrument_type) from the telemetry row, not
      per VM name. Done-when: a worker mid-matrix raises zero false DP-\* alerts across one full run.
- [ ] [INFRA] P0. **Baked image** — build a GCE image (and AWS AMI) from `setup-data-pipeline-vm.sh` with apt + wheels
      preinstalled, versioned by code tarball; launchers take `--image-family uts-data-pipeline`. Done-when: measured
      boot-to-first-heartbeat ≤ 90 s (telemetry), documented in `vm-tarball-deployment.md`.
- [ ] [DATA] P0. **Consolidator gate + post-run trigger (D16)** — controller pre-flight asserts PROD consolidator
      liveness per bucket (`_index/latest.json` age, warn not block); after the run (and optionally per layer) executes
      the prod-identical consolidator job `--bucket <test> --once` for every `-test-` bucket written. Done-when: test
      coverage.json reflects the run within one trigger; no scheduled test consolidator exists.
- [ ] [INFRA] P0. **Central manifest-staleness sentinel per (service, AG)** — a lightweight standing job (extend an
      existing regular / long-lived Cloud Run job, NEVER the download VM): per bucket, read `_index/latest.json` +
      `gcs_describe_object` on the consolidated blob + LIST `_index/per_vm/` object mtimes (metadata-only, no data
      read/write), publish a per-(service, AG) verdict `consolidated_age vs newest_per_vm_shard` to the deployment
      registry + a small GCS verdict object + telemetry. Done-when: verdicts visible per AG/service and measured cost
      is a handful of Class A/B ops per bucket per tick.
- [ ] [INFRA] P0. **Deadman on the consolidator itself** — the existing deadman / Cloud Run monitors page when a
      consolidator job has not RUN within its per-bucket staleness budget (distinct from the sentinel's output-age
      verdict); registered in the data-pipeline alerts registry with state-transition dedup. Done-when: pausing a test
      consolidator fires exactly one page and a ✅ close on recovery.
- [ ] [DATA] P0. **Pre-flight consumes the sentinel, never recomputes** — worker pre-flight reads the central verdict
      for its (service, AG); if stale AT ALL → fail pre-flight loud with the verdict detail in logs + a registered
      DP-\* alert, never start the shard; data-pipeline escalation restores the consolidator/manifest unless an active
      plan/issue for that (AG, service) says not to (the alert cites it). Done-when: a forced-stale bucket blocks the
      worker with the right alert and the escalation runbook entry exists.
- [ ] [DATA] P0. **Skip leg = manifest-only** — the engine's skip leg decides from the cell index / `filters=` read
      (parent T3), never by re-downloading; its timing is recorded as `stage=list` only. Done-when: skip-leg bytes_in
      per shard ≈ the cell's manifest bytes, objects_read = 0.
- [ ] [DATA] P0. **Force leg = empty-cell full e2e** — for every shard, force into an empty `-test-` cell (Phase-0
      resolved-bucket assertion kept), verify objects created with `time_created` ≥ run start + manifest row
      `captured` (never `attempted_failed` silently) + content check. Done-when: 100 % of matrix shards have a force
      row; failures are root-caused rows, not gaps.
- [ ] [DATA] P0. **Run the matrix, MTDS → MDPS → features → ML → strategy → execution, per AG** in dependency order
      (each layer's force leg reads the previous layer's `-test-` output), 3 dated checkpoints per finding K.
      Done-when: 3 cited report paths per worker unit and the matrix artefact updated.
- [ ] [REVIEW] P0. **Alerts interleave** — the controller runs `/data-pipeline-alerts-reconcile` and
      `/vm-preemption-billing-waste-audit` every N shards (N from the measured per-shard time, ≤ 30 min), checks each
      worker's heartbeat + log mtime + checkpoint growth, and pauses the matrix on any DP-\* alert until root-caused.
      Done-when: the controller log shows every interleave tick with its verdict.
- [ ] [DATA] P1. **Memory ladder applied per failing shard** — any shard with peak RSS > 80 % of the worker's RAM goes
      through the ladder above before a resize; > 64 GB → issue doc + parent todo, no resize. Done-when: the matrix
      artefact lists every shard that needed a ladder step and which step fixed it.
- [ ] [DATA] P1. **Skip-time SLO** — from the matrix, set a per-service p95 skip-leg time budget and wire it into the
      check skills as an expected value (parent T1 expected-vs-actual). Done-when: SLO rows in the cost model.
- [ ] [DOC] P1. **Codex** — `vm-launcher-runbook.md` gains the warm-worker + baked-image pattern;
      `manifest-consolidator-ssot.md` gains the D16 test-bucket trigger rule; the check skills document `--shard-list`.
      Done-when: docs merged.
- [ ] [DOC] P2. **Archive** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once every todo is
      `[x]`.

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md` — launch/registry/SPOT/rightsizing rules every worker follows.
- `/codex/05-infrastructure/vm-tarball-deployment.md` — boot path today; baked image lands here.
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator runtime; D16 trigger rule lands here.
- `/codex/06-coding-standards/service-orchestration-patterns.md` — § 15 per-shard cleanup (memory ladder step 1).
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — progress-metric polling for the controller.
- `/codex/02-data/availability-manifest-and-data-status.md` — the manifest cell read the skip leg depends on.

## Progress Log

- **2026-08-22 (interactive session, slot 6, operator)**: Forked from the parent's T8 with the startup arithmetic,
  memory ladder and alert-interleave requirements as stated by the operator.
- **2026-08-22 (Q&A round 2)**: Worker unit refined to (service × AG × data_type × instrument_type) [× model_family]
  (D15); consolidator ruling D16 (prod liveness gate, prod-identical `--once` trigger for test buckets after the run);
  monitors-acknowledge-multi-shard-VM todo added; strategy + execution layers added to the run order.
- **2026-08-22 (operator, consolidator-monitoring ruling)**: sentinel / deadman / pre-flight-consumes-verdict todos added; all per (service, AG).
