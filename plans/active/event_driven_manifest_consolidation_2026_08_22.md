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
- **2026-08-22 (autonomous session, in progress — Phase-0 sequencing gate + manifest v10)**: Worked the sequencing-gate
  todo and the D19 root-cause-gate todo before touching anything cron/terraform-side, per this doc's own explicit
  ordering. **Root-cause gate**: confirmed already satisfied by prior sessions —
  `mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md` traces to the consolidator
  lock-wedge fully diagnosed on `dp_watcher_002_defi_market_data_consolidator_lock_wedge_2026_08_21.md` (missing
  `consolidator_content_write_at` marker → fail-closed full merge → 7200s Cloud Run timeout → SIGKILL → orphaned lock →
  re-arm loop; bit-for-bit the mechanism already root-caused + fixed for cefi). Code fix is shipped
  (`unified-trading-library@af783d92e4`/`53abdf72f3`); the live production recovery (clear the orphaned lock + GCS
  metadata restamp) is correctly NOT executed — the doc's own most recent entry shows a prior session declining an
  authorization claim that arrived through a non-verifiable channel (a doc entry, not the AO `/blocked` escalation
  queue), and that precedent is respected here too: this is a separately-owned, carefully-gated live-ops decision, not
  a D19 deliverable. Citing this as satisfying "root cause is fixed or explicitly shown orthogonal, cited here" — Phase
  2 is not gated on the live recovery landing, only on the root cause being understood, which it is.
  **Sequencing gate**: inventoried every wall-clock freshness consumer (`AG_STALENESS_BUDGET_SEC` / `_budget_for` /
  `_entry_budget`, the ~48 VM launchers' `MANIFEST_CONSOLIDATED_STALENESS_SEC=` env values, `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC`,
  deployment-api's cockpit dict + generated catalog). Found and fixed a real gap: `prediction` is a live, deployed
  asset_group (`launch-prediction-*.sh`, `launch-mtds-prediction-*.sh` launchers exist) with NO calibrated override in
  EITHER `AG_STALENESS_BUDGET_SEC` (UTL, the real read-path gate) or deployment-api's legacy fallback dict — both fell
  through to the generic 120s default, the exact "120s-class check" this gate exists to catch: at a 900s worst-case
  gap once Phase 1's `*/15` cron ships, prediction reads would false-trip into the degraded per-VM-shard fallback
  almost every cycle, the identical failure class sports/defi/tradfi each independently hit and fixed in July/August.
  Fixed: `unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py` adds
  `"prediction": 1800` (interim safe floor mirroring the sports precedent, pending a measured-cadence calibration
  follow-up — not yet a live-measured value like the cefi/defi/tradfi entries); `deployment-api/deployment_api/routes/health_consolidator/__init__.py`
  mirrors the same addition. **Investigated but did NOT fix** (kept for its own follow-up): deployment-api's
  `_entry_budget()` reads a GENERATED `_CATALOG` (`scripts/gen_consolidator_catalog.py`) FIRST, before falling back to
  the legacy dict — per `test_catalog_live_market_data_is_120_everything_else_86400`, the catalog currently assigns
  `tradfi` the generic 120s "live tick" budget with no slow-merge exception (unlike defi's documented 3600s one),
  which may itself be stale versus UTL's real measured ~hourly tradfi cadence (7200s) — a real, plausible, but
  UNVERIFIED gap (reading the generator was out of scope for this pass); adding `tradfi` to the legacy dict alone was
  reverted after breaking 2 pinned tests (`test_entry_budget_reads_catalog_then_falls_back`,
  `test_budget_for_cefi_overrides_default_others_pass_through`) that explicitly assert today's pass-through behaviour
  — flagging as a genuine open question rather than forcing an unverified fix through. **Follow-up todo**:
  - [ ] [DATA] P2. Verify whether `deployment-api/scripts/gen_consolidator_catalog.py`'s tradfi budget (currently
        120s "live tick", per `test_catalog_live_market_data_is_120_everything_else_86400`) should carry the same
        slow-merge exception defi has (3600s), given UTL's own `AG_STALENESS_BUDGET_SEC["tradfi"]=7200` reflects a
        real measured ~hourly cadence (`tradfi_third_es_mes_backfill_consolidator_staleness_gap_2026_07_31.md`) far
        exceeding a 120s live-tick assumption. If stale, tradfi's deployment-api cockpit health view has been
        showing false DOWN/degraded status independent of anything in D19 — a pre-existing bug, not caused by the
        */15 cron change. Repo: deployment-api.
  **Manifest v10 (this session's exclusive-ownership core deliverable)**: cross-referenced the sibling child plan
  `trading_pipeline_config_shard_identity_and_latency_profile_2026_08_22.md` (D13/D17, owned by `batch_live_symmetry_master`,
  not yet locked/started by anyone) for the precise field specs, since that plan — not this one — is where
  `config_shard_id`/`config_version`/`code_semver`/`latency_profile_hash` are actually designed; this plan only
  contributes `upstream_gap_class`/`upstream_gap_days`/`upstream_gap_ratio` (T5 "produced-with-gaps") directly.
  Also found `MANIFEST_SCHEMA_VERSION` was still the live `9` despite `_rows.py`'s `quarantined_legs` field
  (shipped 2026-08-15, `fail_hard_canonical_enforcement_design_2026_07_20.md` §5b Gap 1) already self-labelling its
  own comment "v10" — the version-constant bump was apparently never actually done. That doc's OWN separate Stage-2
  todo (`instrument_id_form`) also informally claimed "v10" but is DEPENDENCY_BLOCKED (reaffirmed 5+ times, most
  recently 2026-08-21) on unrelated prerequisites with no near-term unblock — corrected that doc to "v11" (shipped
  doc-only, `unified-trading-pm@cdc008a33f`) since only one batch can legitimately claim the constant. Landed the
  real v10 bump as ONE coherent batch folding together: `quarantined_legs` (retroactive), `config_shard_id` /
  `config_version` / `code_semver` / `run_attempt` / `latency_profile_hash` (D13/D17, this plan's sibling), and
  `upstream_gap_class` / `upstream_gap_days` / `upstream_gap_ratio` (this plan's own T5 scope) —
  `unified-trading-library/unified_trading_library/manifest_writer/_schema.py` (`MANIFEST_SCHEMA_VERSION = 10` +
  full version-history comment matching the v5-v9 convention) and `_rows.py` (the 8 new dataclass fields, all
  purely-additive with `""`/`0`/`0.0` defaults). Migration-plan verdict per
  `/codex/02-data/chunk-safe-manifest-migrations.md`'s own three-part test: NO chunk-safe worker/coordinator rewrite
  needed — none of the 8 new columns require backfilling a REAL value into any existing row (legacy rows correctly
  read back as empty/zero, identical to how v6-v9's own additive columns already work); this is a pure additive
  version bump, single-VM-shape by the doc's own criteria. **Still open**: the codex doc section itself
  (`/codex/02-data/availability-manifest-and-data-status.md` "## Schema v9" → "## Schema v10", drafted but not yet
  applied — holding until the code change actually ships so the doc can cite a real commit sha, not a placeholder).
  **Not yet shipped**: both `_schema.py`/`_rows.py` (unified-trading-library) and the `_staleness_budget.py` +
  deployment-api dict fix are complete locally and re-diagnosed clean (2 unified-trading-library test failures fixed
  in `test_manifest_writer_per_vm.py` to reflect the corrected prediction behaviour; a 3rd, unrelated
  `test_five_thousand_sequential_writers_do_not_leak_fds` timeout matches an independently-documented pre-existing
  host-contention flake from a prior session on this exact host) — but `quality-gates.sh` has not yet returned a
  clean run on this host: the QG governor itself reports `unified-trading-library` queued 1830s+ (30+min, still
  climbing) on "host-wide cap 7" tokens all busy, and deployment-api's full re-run showed WORSENING, non-deterministic
  subprocess/threading timeouts (auth-boot subprocess SIGKILLs with the correct stderr already captured before the
  kill; a 60s gRPC-client-init timeout with a 9-worker-thread dump) in code paths this session never touched — direct,
  governor-confirmed evidence of severe multi-agent host contention (≥4 concurrent Claude sessions in this one slot),
  not a defect in this change. Per the HARD RULE (commit only from a green tree), holding until a clean run lands
  rather than shipping on a red gate or hammering the shared host with repeated back-to-back full-suite retries.
  Next tick: retry QG after a longer gap, ship both repos + the codex doc together, THEN move to Phase 0's remaining
  follow-up todo above and D19 Phase 1 (terraform).
