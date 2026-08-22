---
doc_type: plan
title: All-shard smoke matrix MTDS → ML — one day per shard, warm workers, manifest-only skip leg, empty-cell force leg, 64 GB ceiling
summary: >-
  Child of trading_pipeline_smoke_and_shard_telemetry_2026_08_22 (forked per task_template finding R). Runs the
  data-pipeline-check engine over EVERY shard from MTDS through MDPS, features and ML for one operator-given day — the
  existing shard proves skip time + performance, an empty -test- cell proves the full e2e — on long-lived worker VMs
  (one per service × asset_group) that iterate shard lists, so VM boot is paid per worker not per shard (600+ shards ×
  two legs × 5-10 min boot would otherwise be days of pure startup). Skip leg is a manifest-only decision (no
  download), force leg is the single download + compute; every leg emits the standardised ShardRunTelemetry row.
  Memory management is improved before any machine resize and 64 GB RAM is a hard stop. /data-pipeline-alerts-reconcile
  and /vm-preemption-billing-waste-audit run interleaved while shards process so dead VMs, missing dumps and
  attempted_failed storms are caught in-run.
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
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: [smoke-test, all-shards, warm-workers, vm-boot, baked-image, memory, 64gb-ceiling, alerts-reconcile, telemetry]
related:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
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
source: [operator interactive session 2026-08-22 (slot 6) — "shard smoke tests for all shards just one day ... abstract away startup ... 64gb ram you need to hard stop ... all the smoke tests should be vms ... run /data-pipeline-alerts-reconcile whilst agents are processing each shard"]
context_scope:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/05-infrastructure/vm-tarball-deployment.md,
    /codex/06-coding-standards/service-orchestration-patterns.md,
    /codex/12-agent-workflow/async-wait-and-poll-discipline.md,
    unified-trading-library/unified_trading_library/pipeline_e2e_check/launcher.py,
    unified-trading-pm/cursor-configs/skills/honest-coverage-dump/scripts/shard_universe.py,
    unified-trading-pm/cursor-configs/skills/data-pipeline-alerts-reconcile/SKILL.md,
    deployment-service/scripts/vm/setup-data-pipeline-vm.sh,
    deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh,
  ]
---

# All-shard smoke matrix MTDS → ML

> **Human plan**, child of
> [`trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`](/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md)
> (needs its T1 telemetry contract and T2 engine changes; forked so its own ordering + VM fleet + alert loop are
> machine-enforceable). Rulings D9, D11 and D12 of the parent govern this plan.

## The startup arithmetic (why the runner shape is the whole plan)

- Today the e2e engine launches **one VM per (shard, leg)** from a stock image with `apt-get` + `uv pip install` at
  boot. 600+ shards × 2 legs × 5-10 min ≈ **100-200 h of boot** — 4-8 days serial, still ~1 day at 8× fan-out — before
  any data moves, and the force + skip pair downloads twice when skip is implemented as a re-read.
- Target: **one warm worker VM per (service × asset_group)** iterating a shard list. Boots = number of workers (≈ 20 →
  ~2-3 h total, ~10 min wall in parallel; ~1 min each once the image is baked). Per shard: skip ≈ seconds (a cell read
  of the manifest, no download) + force ≈ minutes (one download + compute into an empty `-test-` cell) → 600 shards ×
  ~4 min ÷ 20 workers ≈ **~2 h wall**. Download happens once.
- Per-shard time, bytes, peak RSS and $ land as `ShardRunTelemetry` rows (parent T1), so the matrix IS the capacity
  and cost baseline, not a separate exercise.

## Memory ladder (D12)

Order of remedies before any resize: per-shard cleanup contract (`service-orchestration-patterns.md` § 15) → single
engine end-to-end → cell-scoped manifest reads (parent T3) → read-once caches (MTF) → `POLARS_MAX_THREADS` pinned →
then and only then the next machine shape. Ceiling `*-highmem-8` (64 GB). A shard whose peak RSS still exceeds 64 GB
after the ladder is a defect (issue doc + parent T4/T3 todo), never a bigger machine.

## Todos

- [ ] [DATA] P0. **Enumerate the shard matrix** — IS/MTDS cells from coverage.json via `shard_universe.py`
      (`iter_shard_cells`), MDPS processed-candle atoms (`MDPS_DERIVABLE_DATA_TYPES` × timeframes), features
      feature-group atoms (`EXPECTED_FEATURE_GROUPS_BY_SERVICE`), ML model atoms (`ModelRegistry`); write
      `plans/audit/results/benchmarks/all_shard_matrix_<date>.md` with the real count per service × AG and the chosen
      operator `--day` per AG. Done-when: the artefact exists and the count replaces "600+" here.
- [ ] [INFRA] P0. **Warm-worker runner** — add `--shard-list <file>` to the UTL `pipeline_e2e_check` engine so the
      per-shard loop (`for shard in shards` in the service drivers) runs ON the worker VM against a list, emitting one
      telemetry row per (shard, leg), checkpointing progress to
      `gs://<sink-bucket>/_ops/checkpoints/all_shard_matrix_<service>_<ag>.jsonl` (resumable, task-id-keyed). Done-when:
      one worker completes ≥ 20 shards with no re-boot and the checkpoint resumes after a kill.
- [ ] [INFRA] P0. **Worker launcher** — `launch-smoke-worker-vm.sh` registered in `VM_PREFIX_TO_BUCKET`, one VM per
      (service × asset_group), SPOT, shape from the memory ladder (start `e2-standard-8`), resume-from-checkpoint on
      preemption. Done-when: `/vm-resource-rightsizing-check` passes on the first 30-min run.
- [ ] [INFRA] P0. **Baked image** — build a GCE image (and AWS AMI) from `setup-data-pipeline-vm.sh` with apt + wheels
      preinstalled, versioned by code tarball; launchers take `--image-family uts-data-pipeline`. Done-when: measured
      boot-to-first-heartbeat ≤ 90 s (telemetry), documented in `vm-tarball-deployment.md`.
- [ ] [DATA] P0. **Skip leg = manifest-only** — the engine's skip leg decides from the cell index / `filters=` read
      (parent T3), never by re-downloading; its timing is recorded as `stage=list` only. Done-when: skip-leg bytes_in
      per shard ≈ the cell's manifest bytes, objects_read = 0.
- [ ] [DATA] P0. **Force leg = empty-cell full e2e** — for every shard, force into an empty `-test-` cell (Phase-0
      resolved-bucket assertion kept), verify objects created with `time_created` ≥ run start + manifest row
      `captured` (never `attempted_failed` silently) + content check. Done-when: 100 % of matrix shards have a force
      row; failures are root-caused rows, not gaps.
- [ ] [DATA] P0. **Run the matrix, MTDS → MDPS → features → ML, per AG** in dependency order (each layer's force leg
      reads the previous layer's `-test-` output), 3 dated checkpoints per finding K (baseline, mid, final). Done-when:
      3 cited report paths per (service × AG) and the matrix artefact updated.
- [ ] [REVIEW] P0. **Alerts interleave** — the controller runs `/data-pipeline-alerts-reconcile` and
      `/vm-preemption-billing-waste-audit` every N shards (N from the measured per-shard time, ≤ 30 min), checks each
      worker's heartbeat + log mtime + checkpoint growth (progress metric, never activity), and pauses the matrix on any
      DP-\* alert until root-caused. Done-when: the controller log shows every interleave tick with its verdict.
- [ ] [DATA] P1. **Memory ladder applied per failing shard** — any shard with peak RSS > 80 % of the worker's RAM goes
      through the ladder above before a resize; > 64 GB → issue doc + parent todo, no resize. Done-when: the matrix
      artefact lists every shard that needed a ladder step and which step fixed it.
- [ ] [DATA] P1. **Skip-time SLO** — from the matrix, set a per-service p95 skip-leg time budget and wire it into the
      check skills as an expected value (parent T1 expected-vs-actual). Done-when: SLO rows in the cost model.
- [ ] [DOC] P1. **Codex** — `vm-launcher-runbook.md` gains the warm-worker + baked-image pattern; the four check skills
      document `--shard-list`. Done-when: docs merged.
- [ ] [DOC] P2. **Archive** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once every todo is
      `[x]`.

## Codex SSOTs

- `/codex/05-infrastructure/vm-launcher-runbook.md` — launch/registry/SPOT/rightsizing rules every worker follows.
- `/codex/05-infrastructure/vm-tarball-deployment.md` — boot path today; baked image lands here.
- `/codex/06-coding-standards/service-orchestration-patterns.md` — § 15 per-shard cleanup (memory ladder step 1).
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — progress-metric polling for the controller.
- `/codex/02-data/availability-manifest-and-data-status.md` — the manifest cell read the skip leg depends on.

## Progress Log

- **2026-08-22 (interactive session, slot 6, operator)**: Forked from the parent's T8 with the startup arithmetic,
  memory ladder and alert-interleave requirements as stated by the operator.
