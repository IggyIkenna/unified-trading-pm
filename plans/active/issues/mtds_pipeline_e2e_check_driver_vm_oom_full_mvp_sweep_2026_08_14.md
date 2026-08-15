---
doc_type: issue
title: >-
  /data-pipeline-check-mtds full unscoped --mvp-only sweep OOMs the isolated driver VM itself (exit 137), even on
  e2-highmem-4 (32GB) — the §1a driver-VM mitigation is insufficient post-enumeration-fix
summary: >-
  Confirmed live (2026-08-14, defi_satellite_ao_dispatch_batch13 baseline pipeline-check run, --day 2026-07-01): a
  driver-VM-launched (`launch-pipeline-e2e-check-driver-vm.sh --service mtds --legs force,skip --mvp-only
  --require-captured --auto-day`) full unscoped sweep enumerates 3126 shards (`run_pipeline_check: 3126 shard(s)
  enumerated for day=2026-07-01 legs=['force', 'skip'] mvp_only=True`) — this is the CORRECT post-fix count following
  mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md's resolution (cefi+sports now correctly
  included). The driver process itself was SIGKILLed (`bash: line 1: 4852 Killed ... pipeline_e2e_check.py`, exit
  rc=137) ~10 minutes into the run, having fired off force+skip launch-and-wait pairs for ~30 CEFI shards
  (log:launch_vm_and_wait tick pattern shows shard-pair launches ~2s apart, i.e. the driver does not wait for one
  shard's force+skip pair to fully resolve before starting the next — it fans out per-shard `launch_vm_and_wait()` calls
  without a concurrency bound). VM run.log's own `driver RSS peak=14231.3MB` telemetry (for a nested
  mtds-backfill-cefi-pipelinecheck-* poll, not the top-level checker) stayed flat across polls right up to the kill,
  suggesting the OOM signal isn't even the metric the run.log surfaces — the top-level `pipeline_e2e_check.py` process's
  own RSS was never logged, so the actual growth curve is unmeasured. This is on the DEDICATED, ISOLATED e2-highmem-4
  (32GB) driver VM the skill's own §1a section already added specifically to escape a prior 2026-08-06 OOM on the shared
  AO host (21.9GB RSS there) — so that mitigation is not sufficient for the post-enumeration-fix 3126-shard scale of a
  genuinely-unscoped sweep. Net effect: nobody has completed a real full-matrix `/data-pipeline-check-mtds` baseline run
  since the shard-enumeration fix landed — every attempt at the documented §1a "sweep the whole MVP matrix in one
  launcher call" invocation for MTDS will OOM before finishing. Workaround used this session: none applied yet (out of
  scope to root-cause + fix within a P2 satellite-batch todo); the IS-side companion check (`/data-pipeline-check-is`)
  succeeded on the SAME session once its own separate flag bug was fixed (see companion finding, same commit) — this OOM
  is MTDS-specific, not systemic to the shared launcher.
status: open
nature: issue
asset_group: [defi, cefi, tradfi, sports, prediction]
stage: [data]
repos: [market-tick-data-service, deployment-service, unified-trading-library]
scope: [engineer]
tags: [data-correctness, oom, pipeline-e2e-check, mtds, vm-launcher, driver-vm, smoke-test]
related:
  [
    /plans/archive/2026_08/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md,
    /plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md,
    /plans/active/defi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-14"
author: defi_satellite_ao_dispatch_batch13 worker (slot 12)
last_updated: "2026-08-14"
source: defi_satellite_ao_dispatch_batch13_2026_08_13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.4
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    unified_trading_library/pipeline_e2e_check/launcher.py,
    deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh,
    unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/SKILL.md,
    /plans/archive/2026_08/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md,
  ]
---

## What I found

Running the baseline (`--day 2026-07-01`) leg of `/data-pipeline-check-mtds` per
`defi_track5_coverage_mvp_backfill_2026_07_24.md`'s "3x each" cadence todo, via the skill's own §1a driver-VM launcher:

```bash
bash deployment-service/scripts/vm/launch-pipeline-e2e-check-driver-vm.sh \
  --service mtds --day 2026-07-01 --legs force,skip --mvp-only --require-captured --auto-day \
  --project central-element-323112
```

VM `pipeline-e2e-check-mtds-20260814-223014-388f81` (e2-highmem-4, 32GB) ran for ~10 minutes, enumerated 3126 shards,
launched force+skip `launch_vm_and_wait()` pairs for roughly 30 CEFI shards back-to-back (≈2s apart per pair, i.e. no
observed throttling/concurrency bound between shards), then the top-level `pipeline_e2e_check.py` process was SIGKILLed
(exit rc=137 — OOM-killer signature) at 22:43:44. Full `run.log`:
`gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260814-223014-388f81/run.log`.

Companion IS-side run (`/data-pipeline-check-is`, same session) succeeded once a separate flag-compatibility bug in the
skill doc was fixed (IS's `pipeline_e2e_check.py` doesn't accept `--require-captured`/`--auto-day`/`--mvp-only` at all —
fixed in `unified-trading-pm/cursor-configs/skills/data-pipeline-check-is/SKILL.md` same session, no code change needed
there). The MTDS OOM is a distinct, MTDS-specific failure — its driver genuinely fans out many concurrent per-shard
VM-launch-and-wait calls with no visible bound.

## Why it matters

`/data-pipeline-check-mtds`'s entire value proposition is proving the MTDS backfill path end-to-end on real
infrastructure. Since the enumeration fix (2026-08-06) correctly grew the full sweep from a masked ~2967-minus-cefi-
sports count to the real 3126-shard MVP surface, nobody has been able to actually finish a real unscoped run — the
skill's own documented "single launcher call sweeps everything" invocation (§1a) reliably OOMs partway through. This
blocks `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s pipeline-check gate todo (and the equivalent gate for every
other asset_group) from ever reaching a genuine baseline/mid-backfill/final verdict via the documented single-command
path. Every future invocation of the documented command wastes real VM spend (~10 min of e2-highmem-4 runtime before the
kill) without producing a report.

## Recommended decision

Two independent angles, not mutually exclusive:

1. **Root-cause the driver's memory growth** — `market-tick-data-service/scripts/pipeline_e2e_check.py`'s per-shard loop
   calls `launch_vm_and_wait()` for each of 3126 shards; confirm whether results/report state accumulates unbounded in
   memory across shards (most likely — the report has to hold every shard's verdict) or whether it's
   `launch_vm_and_wait()`'s own per-call state (subprocess handles, polling threads) that isn't released between calls.
   Either way, either bound concurrency + stream report rows to disk incrementally instead of building the whole report
   object in memory, or process shards in smaller committed batches (e.g. per `--asset-group`, matching the
   already-recommended workaround from the 2026-08-06 enumeration-fix issue) so a crash only loses one batch's progress,
   not the whole sweep.
2. **Interim mitigation** (no code change, ships immediately): update the MTDS skill's §1a canonical example to
   recommend explicit per-`--asset-group` invocations (5 separate driver-VM launches) instead of one unscoped sweep,
   mirroring the workaround `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` already used —
   this bounds each driver process's shard count to a fraction of 3126 and is far less likely to OOM even without a code
   fix.

## Todos

- [ ] [CODE] P1. Root-cause `market-tick-data-service/scripts/pipeline_e2e_check.py`'s per-shard memory growth on a full
      unscoped `--mvp-only` sweep (3126 shards) and bound it — either stream the report to disk per-shard instead of
      accumulating in memory, or cap concurrent in-flight `launch_vm_and_wait()` calls. Verify by running the same
      unscoped `--day 2026-07-01 --legs force,skip --mvp-only --require-captured --auto-day` sweep to a clean exit on
      the same e2-highmem-4 driver VM class. **STRENGTHENED 2026-08-15 (see Progress Log): the per-asset-group
      workaround (todo below) is NOT a sufficient interim mitigation — 3/5 asset_groups still failed to produce a clean
      report on a real re-run** (CEFI + DEFI drivers died silently with no EXIT_STATUS/report at all; SPORTS exited
      `rc=3` with no report and no logged traceback). This root-cause fix is now the ONLY path to a genuinely complete
      MTDS baseline — the interim doc-only workaround does not close this issue. (repos: market-tick-data-service)
- [x] [DOCS] P2. ✅ Update `unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/SKILL.md` §1a to recommend
      per-`--asset-group` driver-VM invocations (5 launches) as the default sweep pattern until the above OOM fix ships,
      instead of the current single unscoped-sweep example. (repos: unified-trading-pm) — unified-trading-pm (this
      commit). §1a now shows a `for AG in CEFI DEFI TRADFI SPORTS PREDICTION; do ...` loop as the default, with a note
      that even a per-asset_group run may still need `--venue`-level splitting (cefi alone was ~30+ shards deep and
      still climbing when the unscoped run OOM'd).
- [ ] [DATA] P2. Once either todo above lands, re-run the MTDS baseline (`--day 2026-07-01`) to completion and cite the
      resulting report path in `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s pipeline-check gate todo. **ATTEMPTED
      2026-08-15, NOT satisfied — see Progress Log.** Real per-`--asset-group` re-run only completed cleanly for
      PREDICTION + TRADFI (reports rescued to `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_{AG}.md`);
      CEFI, DEFI, SPORTS did not produce usable reports. Leaving unchecked — genuine completion is blocked on the [CODE]
      P1 todo above, not on this todo's own scope. Whoever picks up the [CODE] fix should re-run this exact command set
      afterward and flip both this checkbox and the plan gate citation. (repos: market-tick-data-service)
- [x] [CODE] P1. ✅ **NEW (found 2026-08-15).** The report writer's GCS mirror path has NO `asset_group` segment
      (`pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/<run_date>/data_pipeline_e2e_check_mtds_<run_date>.md`,
      no `{AG}` component) — confirmed live: running the §1a per-`--asset-group` loop sequentially, each completing
      asset_group's report SILENTLY OVERWRITES the previous one at that same GCS path. A human/agent following the
      documented per-AG loop and checking the report only at the end will see only the LAST asset_group's results and
      believe (incorrectly) that it covers the whole sweep. Fix: parameterize the GCS mirror path (and ideally the local
      path too) with `{asset_group}` — e.g.
      `.../data_pipeline_e2e_check_mtds/<run_date>/data_pipeline_e2e_check_mtds_<run_date>_<asset_group>.md` — so
      sequential/parallel per-AG runs never clobber each other. Until fixed, anyone running the per-AG loop MUST
      download/rescue each AG's report immediately after that AG's driver VM reaches a terminal `EXIT_STATUS`, before
      launching or waiting on the next AG. — **unified-trading-library@ff9cb5f811**: `write_report()` now suffixes the
      GCS blob name with the single asset_group whenever a report's results are scoped to exactly one (a genuine
      unscoped multi-asset_group sweep keeps the original unsuffixed name, unchanged) — derived from the real
      `ShardCheckResult.shard_label`s via the existing `_asset_groups_tested()` helper, never a new CLI flag. 2 new
      regression tests added (`tests/unit/test_pipeline_e2e_check_report_gcs_upload.py`); full `quality-gates.sh` green
      on this exact commit. This closes the silent-clobber risk for FUTURE per-AG runs; it does not itself produce the
      still-missing CEFI/DEFI/SPORTS reports from the [CODE] P1 root-cause todo above, which remains open. (repos:
      market-tick-data-service)

## Progress Log

- **2026-08-14 (defi_satellite_ao_dispatch_batch13 worker, slot 12)**: filed from a failed MTDS baseline attempt while
  executing the batch13 satellite todo "Run /data-pipeline-check-is and /data-pipeline-check-mtds 3x each". IS baseline
  succeeded (separate doc fix, no code bug); MTDS baseline blocked on this OOM. Not fixing inline — out of the satellite
  todo's bounded scope.
- **2026-08-15 (slot 6 worker)**: attempted the re-run per the now-landed §1a per-`--asset-group` workaround — launched
  5 separate driver VMs (CEFI/DEFI/TRADFI/SPORTS/PREDICTION,
  `--day 2026-07-01 --legs force,skip --mvp-only --require-captured --auto-day`, all e2-highmem-4). Real outcome, 40-70
  min later:
  - **PREDICTION** — completed cleanly, exit_code=1 (partial pass — total=8 passed=1 failed=3 skipped=4, failures are
    genuine data gaps, not a crash). Report rescued to
    `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_PREDICTION.md` (GCS source:
    `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-07-01/`,
    since overwritten by TRADFI's run — see the new report-collision todo above).
  - **TRADFI** — completed, exit_code=1, total=12 passed=0 failed=12 (all `no_parquet_under` on the `-test-` bucket —
    reads as a genuine pre-existing test-bucket data gap for these NASDAQ/NYSE cells, not evidence of the OOM/crash
    class this issue tracks; not investigated further here, out of this todo's scope). Report rescued to
    `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_TRADFI.md`.
  - **CEFI** — driver VM (`pipeline-e2e-check-mtds-20260814-233918-a4fbf5`) ran ~13 min (RSS holding at 13.5GB, well
    under the 32GB VM cap — so not a simple "hit the memory ceiling" OOM this time), then `run.log` stops mid-poll with
    NO further output, NO `EXIT_STATUS`, NO report — the VM shows a `delete` operation ~18 min after the last log line
    (`operation-…-5875e5b8`, no `preempted` op), consistent with the top-level process being killed abruptly (signal not
    captured because the trap never ran) and an outer wrapper eventually self-deleting on a stall/timeout path.
  - **DEFI** — same silent-death pattern, but far earlier: `run.log` (only 2.8KB) stops right after the Phase-0
    manifest-consolidation line, ~1 minute into the run, before any shard force/skip work is even logged. No
    `EXIT_STATUS`, no report, `delete` op fired ~18 min later.
  - **SPORTS** — driver exited `command exited rc=3` after successfully launching + confirming one shard VM
    (SMARKETS:odds) — no `EXIT_STATUS`-blocking crash signature (not 137), but no Traceback/ERROR/Exception string
    anywhere in its 49.9KB `run.log` either — the failure mode is currently undiagnosed. No report produced.
  - **Net**: even scoped to ONE asset_group per driver VM (the documented interim mitigation), only 2/5 completed
    cleanly. The per-asset-group split reduces but does NOT eliminate the underlying instability — root-causing [CODE]
    P1 above is now the only path to a genuinely complete baseline. Did not attempt a 3rd retry of CEFI/DEFI/SPORTS in
    this session (out of proportion to a single P2 data todo — the retry would very likely hit the same unfixed root
    cause). Plan gate todo (`defi_track5_coverage_mvp_backfill_2026_07_24.md`'s "Run /data-pipeline-check-is and
    /data-pipeline-check-mtds 3x each") updated to cite this partial result honestly rather than a false "done".
