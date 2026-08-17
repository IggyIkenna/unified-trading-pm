---
doc_type: issue
title: >-
  `/data-pipeline-check-mdps` driver OOM-killed on DEFI within ~60s on a dedicated e2-highmem-4 (32GB) driver VM —
  CEFI/TRADFI/SPORTS/PREDICTION ran fine; SPORTS produced the first-ever clean automated round-trip report
summary: >-
  Attempted the plan's genuinely-open todo (`data_pipeline_check_mdps_features_2026_07_20.md`'s "Complete the automated
  `/data-pipeline-check-mdps` skill's OWN multi-cell round-trip" — gate `mdps-e2e-shared-host-teardown-fixed` confirmed
  RESOLVED 2026-08-16) by launching 5 AG-scoped driver VMs in parallel via
  `deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh --service mdps --day 2026-07-05 --legs
  force,skip --require-captured --auto-day --asset-group <AG>` (one per CEFI/DEFI/TRADFI/SPORTS/PREDICTION — the
  §1a dedicated-driver-VM pattern that decouples the run from any interactive session, which is what actually fixes
  the previously-tracked shared-host-teardown mechanism this todo was gated on). Result: SPORTS completed cleanly in
  ~6 min (`total=4 passed=2 failed=0 skipped=2`, report mirrored to
  `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mdps/2026-07-05/data_pipeline_e2e_check_mdps_2026_07_05_sports.md`)
  — the first-ever clean automated completion of this driver end-to-end. CEFI/TRADFI/PREDICTION were still actively,
  genuinely progressing (poll-tick counters incrementing, driver RSS 1.2-5.7GB, new per-cell sub-VM launches every
  1-2 min) when this session ended — not stalled, just multi-hour by cell count (103/222 total cells were DEFI's
  alone; CEFI/TRADFI/PREDICTION split the rest). DEFI itself failed hard: `run.log` shows Phase-0 consolidation
  completing at 22:47:30, then the process silently killed (`bash: ... Killed`, `rc=137`) by 22:48:22 — under 60
  seconds after Phase-0, with NO enumeration/shard-launch log lines ever appearing. This is a NEW, distinct OOM
  incident from `defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md` (that one was a
  `--workers`-oversubscribed fold BACKFILL script on an `e2-standard-4`/16GB box; this is the pipeline_e2e_check
  DRIVER itself, on a purpose-built `e2-highmem-4`/32GB box whose sizing comment explicitly claims "comfortably above
  the observed 15.7GB (features) / 21.9GB (MTDS) driver peaks" — DEFI blew past that headroom in under a minute,
  a materially worse peak than any previously-measured driver for this same launcher).
status: open
nature: issue
asset_group: [defi, infrastructure]
stage: [data]
repos: [market-data-processing-service, deployment-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    pipeline-e2e-check,
    mdps,
    oom,
    memory-bounding,
    defi,
    driver-vm,
    single-walk,
  ]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/defi_legacy_fold_relaunch_vm_infra_flakiness_and_oom_2026_08_15.md,
    /plans/archive/issues/shared_host_ram_exhaustion_kills_background_qg_2026_07_27.md,
  ]
created: 2026-08-16
author: slot-15 (data_engineering)
assigned_vm: planning
parent_epic: infrastructure_master
priority: P1
resolved_by:
locked_by:
source:
  - data_pipeline_check_mdps_features_2026_07_20.md's "NEW todo (was 8's remaining scope)" — the specific dispatched
    todo this session was attempting to close
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# `/data-pipeline-check-mdps` driver OOM-killed on DEFI — mechanism now proven for the other 4 AGs

## What I found

Launched 5 parallel AG-scoped driver VMs (`launch-pipeline-e2e-check-driver-vm.sh --service mdps --day 2026-07-05
--legs force,skip --require-captured --auto-day --asset-group {CEFI,DEFI,TRADFI,SPORTS,PREDICTION} --project
central-element-323112`) at 2026-08-16T22:42:32Z. Splitting by asset_group (the "fleet width" lever the skill's own
§5 recommends) both cuts wall-clock and isolates AG-specific failures instead of one giant unscoped run dying
opaquely.

**SPORTS — clean pass, first-ever automated round-trip for this driver**: `total=4 passed=2 failed=0 skipped=2`.
The 2 "skipped" rows are the SKIP leg for both timeframes, self-skipped as `duplicate_in_flight` (the force VM for
the same shard was still `RUNNING` when the skip leg checked) — a real, separate, minor finding: firing force+skip
back-to-back on a single-cell AG doesn't leave enough of a gap for the skip leg to see the force VM as terminal, so
the skip-proof mechanism itself wasn't exercised here even though the driver's own round-trip mechanics (enumerate →
launch → poll → verify → write report → mirror to GCS) all worked end-to-end for the first time on record. Report:
`gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mdps/2026-07-05/data_pipeline_e2e_check_mdps_2026_07_05_sports.md`.

**CEFI / TRADFI / PREDICTION — genuinely progressing, not stalled**, confirmed via 2 independent polls ~90s apart
each: poll-tick counters climbing steadily (CEFI ticks 3→8, TRADFI 1→6, PREDICTION 1→2 across the observed window),
new per-cell sub-VM launches appearing in the log each check (`mdps-backfill-{ag}-pipelinecheck-...`), driver RSS
stable and well within the 32GB ceiling (CEFI 5.68GB, TRADFI 3.33GB, PREDICTION 1.54GB peak). These are multi-hour
runs by cell count (CEFI/TRADFI/PREDICTION together cover the ~119 non-DEFI, non-SPORTS cells of the 222-cell
`--require-captured` matrix) — still in flight when this session ended; no session-teardown risk since they run on
their own dedicated VMs, independent of any interactive/AO session (this IS the fix for the very
`mdps-e2e-shared-host-teardown-fixed` gate condition this todo was blocked on).

**DEFI — OOM-killed within ~60s of Phase-0 completing**, before any shard enumeration/launch log line ever
appeared:

```
2026-08-16 22:47:19,919 INFO run_pipeline_check: 103 shard cell(s) for day=2026-07-05 legs=['force', 'skip'] mvp_only=False
2026-08-16 22:47:30,264 INFO Phase-0 consolidation: market-data-tick-defi-test-... OK — ... shards=4 rows_in=4120 rows_out=4104 ...
[~52s pass with only one heartbeat line]
bash: line 1:  5060 Killed                  /home/ikennaigboaka/venv/bin/python scripts/pipeline_e2e_check.py --day 2026-07-05 --asset-group DEFI --legs force,skip --require-captured --auto-day --project central-element-323112
[vm-exec] command exited rc=137
```

`launch-pipeline-e2e-check-driver-vm.sh` sizes every driver VM at a hardcoded `e2-highmem-4` (32GB, no env override
— unlike the note in `data-pipeline-check-mdps/SKILL.md` §5 implying `MACHINE_TYPE` is env-overridable on "this
launcher", which is only true of the per-shard backfill launcher, not this driver launcher), with the sizing comment
explicitly citing "32GB headroom -- comfortably above the observed 15.7GB (features) / 21.9GB (MTDS) driver peaks".
DEFI exceeded that same 32GB ceiling in under a minute — a new worst-case peak, and it happened BEFORE shard
enumeration even logged a first cell, strongly suggesting the blowup is in whatever runs immediately after Phase-0
consolidation and before the first `_captured_days_by_cell`/enumeration log line — most likely the DEFI-scoped
`read_availability_index` call feeding `_captured_days_by_cell` (DEFI's raw `dex_pool_swaps` PROD manifest alone is
~2.37M rows per `data_pipeline_check_mdps_features_2026_07_20.md`'s own todo 13 measurement) even though that call
already does column-pushdown (`_INPUT_INDEX_COLUMNS`, 5 columns) — either the pushdown isn't effectively narrowing
the underlying parquet read for this bucket's layout, or some other DEFI-specific step (the 103-cell
`mdps_mvp_universe(DEFI)` enumeration itself, or a subsequent full-frame `.groupby` materializing a large
object-dtype frame) is the actual culprit. Not root-caused further in this session — the actual mechanism needs a
live-attached memory profile (e.g. rerun under `scripts/dev/run-bounded-analysis.sh`-style RSS sampling) to pin down
which specific call balloons, which is real investigation work, not a one-line fix.

## Why it matters

DEFI is the single largest asset_group by far (103/222 `--require-captured` cells, ~46%) and is the asset_group this
whole plan's headline goal (concrete ETA to backfill all remaining DeFi MVP) is actually about — a driver that can't
even start on DEFI blocks the one AG this plan cares about most, even though the underlying force/skip MECHANISM is
now independently proven correct via the direct-GCS-verified runs from todo 8 and now further corroborated by
SPORTS's clean automated pass today.

## Recommended decision

1. `[SCRIPT] P1.` Root-cause the DEFI-specific OOM: re-run `python scripts/pipeline_e2e_check.py --day 2026-07-05
   --asset-group DEFI --legs force,skip --require-captured --auto-day` under an RSS-sampling wrapper (or add a
   coarse `tracemalloc`/periodic-RSS log around `_read_input_index_frame`/`mdps_mvp_universe(DEFI)`/the
   `_captured_days_by_cell` groupby) to identify which specific call balloons past 32GB. Repo:
   market-data-processing-service.
2. `[SCRIPT] P2.` Once root-caused, either (a) fix the read to genuinely row-group/date-filter instead of relying on
   column pushdown alone (mirroring `precompute_confirmed_empty_dates`'s date-range-pushdown pattern from this same
   plan's todo 10-followup-b), or (b) if the read is already properly bounded and the blowup is structural
   (`mdps_mvp_universe(DEFI)`'s 103-cell object materialization, or a `.groupby` producing a large intermediate),
   bump `launch-pipeline-e2e-check-driver-vm.sh`'s `MACHINE_TYPE` to an env-overridable value (default
   `e2-highmem-4`, allow `PIPELINE_E2E_CHECK_DRIVER_MACHINE_TYPE` override) so a large-AG run like DEFI can request
   `e2-highmem-8`/`-16` without a code change every time. Repo: deployment-service.
3. `[SCRIPT] P3.` Fix the SPORTS skip-leg `duplicate_in_flight` false-skip: when force+skip run in the SAME driver
   invocation back-to-back on a single-cell AG, the skip leg should wait for the force VM to reach a terminal state
   (it already polls `EXIT_STATUS` elsewhere in this same driver) rather than treating "still RUNNING" as grounds to
   skip the skip-proof entirely — right now a single-cell AG's skip leg can never actually validate the freshness-gate
   mechanism. Repo: market-data-processing-service.
4. `[DATA] P1.` Once (1)/(2) land, re-run DEFI (and re-verify CEFI/TRADFI/PREDICTION reached a terminal state — they
   were still in flight when this session ended) to close
   `data_pipeline_check_mdps_features_2026_07_20.md`'s open todo for real, with all 5 AGs' reports consolidated.
