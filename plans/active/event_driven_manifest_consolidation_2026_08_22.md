---
doc_type: plan
title: Event-driven manifest consolidation — fire on per-VM shard writes, 15-min UTC floor, trigger-aware staleness, benchmark-gated long-lived merge service
summary: >-
  Child of trading_pipeline_smoke_and_shard_telemetry_2026_08_22 under manifest_master (operator ruling D19,
  2026-08-22). Today every consolidator fires on a Cloud Scheduler default of every minute across 10+ buckets — ~1,440
  executions/day/bucket of mostly-idle runs. Ruled replacement — consolidators fire off actual per-VM shard writes
  (GCS OBJECT_FINALIZE on _index/per_vm/ → Pub/Sub → debounce dispatcher) with a fleet-wide 15-minute UTC-aligned
  floor: next_run = max(previous run's next 15-min boundary, first write-trigger after the previous run); no writes →
  no trigger → no run; a trigger landing mid-run queues exactly one follow-up. Wall-clock staleness budgets (120 s
  generic / 2400 s sports / 3600 s defi / ~9000 s heavy) retire in favour of trigger-aware staleness ("newest per-VM
  write older than consolidated AND no run within debounce+grace"). Every AG's WORST-CASE full merge must fit the
  15-min window; whether that runs as the existing Cloud Run Job or a long-lived min-instances Cloud Run service (warm
  DuckDB + spill volume — Cloud Run tmpfs is RAM-backed, 32 GiB / 8 vCPU cap) is decided by a per-AG worst-case
  benchmark with DEFI/CEFI row counts modelled at roughly 2× today's (unless already ≥90 % tagged — measure first),
  including in-region GCS read/write throughput, since slow I/O negates the job shape's value. Supersedes the
  manifest-consolidator SSOT's minutely-cadence and NOT-a-VM/always-job framing once the benchmark rules.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-trading-library, deployment-service, deployment-api, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [manifest, consolidator, event-driven, pubsub, debounce, cloud-run, duckdb, staleness, cost, benchmark]
related:
  [
    /plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md,
    /plans/active/trading_pipeline_all_shard_smoke_matrix_2026_08_22.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /plans/epics/manifest_master.md,
  ]
created: 2026-08-22
last_updated: 2026-08-22
parent_epic: manifest_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
assigned_role: infra
effort: max
drift_direction: advance-code
depends_on: [trading_pipeline_smoke_and_shard_telemetry_2026_08_22]
locked_by:
locked_since:
supersedes:
superseded_by:
source: [operator Q&A 2026-08-22 (slot 6) — "no point running consolidator constantly ... trigger = max(15 min even utc intervals, vm per shard update trigger) ... every AG able to do a full consolidation within 15 mins ... cloud run long lived service ... test this on the most complex merge possible per AG ... assume DEFI and CEFI rows roughly double unless already 90%+ tagged"]
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    unified-trading-library/unified_trading_library/manifest_consolidator.py,
    unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py,
    deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf,
    /plans/active/trading_pipeline_all_shard_smoke_matrix_2026_08_22.md,
  ]
---

# Event-driven manifest consolidation (D19)

> **Human plan**, child of
> [`trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md`](/plans/active/trading_pipeline_smoke_and_shard_telemetry_2026_08_22.md).
> Trigger rule, floor and the fit-in-15-min bound are operator-ruled (D19); the merge HOME is benchmark-gated, not
> assumed. The matrix child's sentinel / deadman / pre-flight todos consume the trigger-aware staleness defined here.

## Todos

- [ ] [INFRA] P0. **Phase 1 — `*/15` aligned cron now** — change `local.manifest_consolidator_schedule`'s default from
      `*/1 * * * *` to a 15-min UTC-aligned cron for every bucket (drop faster per-bucket overrides unless a cited
      consumer needs them); the existing content-write-marker incremental cutoff makes skips cheap. Done-when:
      executions/day per bucket drop ~15× in the Cloud Run metrics, terraform applied with the apply log cited.
- [ ] [BACKEND] P0. **Phase 2 — write-triggered debounce** — per bucket, GCS `OBJECT_FINALIZE` notification with
      `--object-prefix=_index/per_vm/` → Pub/Sub `manifest-per-vm-writes`; a scale-to-zero dispatcher implements
      `next_run = max(previous run's next 15-min UTC boundary, first trigger after previous run)`, queues at most one
      follow-up for triggers landing mid-run, and runs nothing on idle buckets. Done-when: an idle bucket shows zero
      runs over 24 h while a written bucket consolidates within its window (both cited from metrics).
- [ ] [DATA] P0. **Measure current tagged share first** — per AG, what fraction of DEFI/CEFI manifest rows is already
      canonical/tagged (the ~2× growth model applies only to the untagged remainder). Done-when: one table in this
      plan, cited row counts per bucket.
- [ ] [DATA] P0. **Worst-case merge benchmark per AG** — largest realistic per-VM backlog + full canonical at
      today's rows AND at the modelled ~2× DEFI/CEFI rows; measure in-region GCS read MB/s, write MB/s, merge wall,
      peak RSS and $ per run for (a) the existing Cloud Run Job cold, (b) a warm min-instances Cloud Run service with
      a spill volume; every run emits `ShardRunTelemetry`. Done-when: per-AG table + the explicit job-vs-service
      ruling recorded here with numbers, incl. whether every AG fits the 15-min bound at 2× rows.
- [ ] [BACKEND] P1. **Phase 3 — the winner ships** (gated on the benchmark) — if service: min-instances-1 Cloud Run
      service, billing mode chosen by measured idle cost (request-based billing + idle-instance rate vs
      instance-based), warm DuckDB + volume-mounted spill (tmpfs is RAM-backed — never spill to /tmp), direct Pub/Sub
      pull, in-process debounce; if job: keep jobs + dispatcher + NFS spill only where an AG misses the 15-min bound.
      Done-when: shipped for every bucket, one week of metrics cited.
- [ ] [BACKEND] P1. **Trigger-aware staleness replaces wall budgets** — retire the 120 s / 2400 s / 3600 s / ~9000 s
      wall-clock budgets in `manifest_writer/_staleness_budget.py` + the deployment-api consolidator health route:
      stale ⇔ newest `_index/per_vm/` mtime is newer than the consolidated blob AND no run within debounce + grace;
      the matrix child's sentinel / deadman / pre-flight consume this definition. Done-when: budgets removed, health
      route + sentinel verdicts trigger-aware, no false staleness pages across one quiet weekend.
- [ ] [DATA] P1. **Cost accounting** — before/after executions/day and $ per bucket from telemetry + billing export.
      Done-when: the reduction is a cited number in this plan and the cost model.
- [ ] [INFRA] P2. **Test-bucket runs reuse the dispatcher** — the matrix controller's post-run `-test-` consolidation
      (D16) fires through the same dispatcher (manual trigger), keeping one code path and zero drift. Done-when: one
      matrix run consolidates its test buckets via the dispatcher.
- [ ] [BACKEND] P0. **Sequencing gate — freshness consumers go trigger-aware BEFORE any cron slows.** Inventory every
      consumer of wall-clock index freshness (backfill-VM launcher stale-index loud-fails, `ManifestReader`'s 7200 s
      consolidated-blob fallback, `_staleness_budget` readers, the DP monitors/alerts keyed on blob age) and flip each
      to the trigger-aware definition (or a raised interim budget) FIRST — otherwise Phase 1's `*/15` cron immediately
      false-trips the 120 s-class checks and can block or kill RUNNING backfill VMs that gate on index freshness.
      Done-when: the inventory table is in this plan and every consumer is trigger-aware before the Phase-1 terraform
      applies; a running backfill VM survives a full 15-min quiet window without a monitor kill.
- [ ] [BACKEND] P0. **Root-cause gate — the open DEFI stale-consolidated issue first** — `plans/active/issues/`
      `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md` shows the
      consolidated blob hours stale while minutely runs report success: evidence the incremental content-write-marker
      cutoff can skip real merges. D19 leans harder on that exact logic, so the issue is a dependency, not a neighbour.
      Done-when: that issue's root cause is fixed or explicitly shown orthogonal, cited here, before Phase 2 ships.
- [ ] [BACKEND] P1. **Dual-shape transition for per-VM shards** — while old-code VMs still write single-file
      `per_vm/{instance}.parquet` and new code writes append-only parts (parent T3), the consolidator and the
      self-shard read merge BOTH shapes; no flag-day. Done-when: a mixed-shape bucket consolidates correctly in a test.
- [ ] [INFRA] P1. **Retire the old cadence when done** — once Phase 2/3 is proven: delete the `*/15` primary crons
      (keep ONE slow fallback trigger, e.g. hourly, as the missed-notification safety net the deadman watches), remove
      the retired wall-clock budgets and their config, and mark the superseded sections of
      `/codex/05-infrastructure/manifest-consolidator-ssot.md` — never leave the scheduled and event-driven paths both
      primary. Done-when: scheduler list shows only the fallback; a killed notification path is caught by deadman +
      fallback within one hour in a test.
- [ ] [DOC] P1. **Codex** — rewrite `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s cadence + runtime
      sections for D19 (trigger rule, floor, trigger-aware staleness, benchmark-ruled home; SUPERSEDED banners on the
      minutely/always-job framing). Done-when: doc merged, `check_codex_refs.sh` clean.
- [ ] [DOC] P2. **Archive** per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` once every todo
      is `[x]`.

## Codex SSOTs

- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — the doc this plan rewrites for D19.
- `/codex/02-data/availability-manifest-and-data-status.md` — per-VM shard + consolidated-index contract.

## Progress Log

- **2026-08-22 (operator Q&A, slot 6)**: Created from ruling D19 (trigger = max(15-min UTC boundary, per-VM write),
  fleet-wide floor, trigger-aware staleness, benchmark-gated long-lived Cloud Run service vs job, DEFI/CEFI ~2× row
  model unless ≥90 % tagged).
- **2026-08-22 (operator Q&A — billing + read-path detail for the benchmark todo)**: the worst-case benchmark compares
  read paths DuckDB native `gs://` httpfs vs a Cloud Storage FUSE mount (FUSE is NEVER a spill target — spill is
  tmpfs/RAM or a Filestore NFS volume only; FUSE writes are whole-object replacement, fine for the consolidated
  parquet), and three Cloud Run billing modes — scale-to-zero request-based ($0 idle, cold start + cold caches),
  min-instances-1 request-based (idle-rate memory + discounted CPU, warm process), instance-based always-on (only if
  merges were near-continuous, which D19 prevents). Autoscaling: per-bucket Pub/Sub push with concurrency=1 gives one
  instance per in-flight bucket merge, `max-instances` capped; in-region GCS↔Cloud Run egress is free, only op counts
  bill.
- **2026-08-22 (operator follow-up)**: retirement + sequencing-gate + dual-shape + DEFI-issue-gate todos added after the backfill-gating question.
