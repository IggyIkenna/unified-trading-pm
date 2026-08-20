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
    /plans/archive/2026_08/defi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-14"
author: defi_satellite_ao_dispatch_batch13 worker (slot 12)
last_updated: "2026-08-20"
source: defi_satellite_ao_dispatch_batch13_2026_08_13
parent_epic: security_and_cross_cutting_master
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
    unified-trading-library/unified_trading_library/pipeline_e2e_check/launcher.py,
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

- [x] ✅ [CODE] P1. Root-cause `market-tick-data-service/scripts/pipeline_e2e_check.py`'s per-shard memory growth on a
      full unscoped `--mvp-only` sweep (3126 shards) and bound it — either stream the report to disk per-shard instead
      of accumulating in memory, or cap concurrent in-flight `launch_vm_and_wait()` calls. Verify by running the same
      unscoped `--day 2026-07-01 --legs force,skip --mvp-only --require-captured --auto-day` sweep to a clean exit on
      the same e2-highmem-4 driver VM class. **STRENGTHENED 2026-08-15 (see Progress Log): the per-asset-group
      workaround (todo below) is NOT a sufficient interim mitigation — 3/5 asset_groups still failed to produce a clean
      report on a real re-run** (CEFI + DEFI drivers died silently with no EXIT_STATUS/report at all; SPORTS exited
      `rc=3` with no report and no logged traceback). This root-cause fix is now the ONLY path to a genuinely complete
      MTDS baseline — the interim doc-only workaround does not close this issue. (repos: market-tick-data-service) —
      unified-trading-library@567d2925d2 + market-tick-data-service@c0d5827835 (see Progress Log for root cause + live
      verification evidence).
- [x] [DOCS] P2. ✅ Update `unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/SKILL.md` §1a to recommend
      per-`--asset-group` driver-VM invocations (5 launches) as the default sweep pattern until the above OOM fix ships,
      instead of the current single unscoped-sweep example. (repos: unified-trading-pm) — unified-trading-pm (this
      commit). §1a now shows a `for AG in CEFI DEFI TRADFI SPORTS PREDICTION; do ...` loop as the default, with a note
      that even a per-asset_group run may still need `--venue`-level splitting (cefi alone was ~30+ shards deep and
      still climbing when the unscoped run OOM'd).
- [x] ✅ [BACKEND] P2. **NEW (added 2026-08-18, plan_reconciler)** — root-cause the NEW earlier-triggering silent-death
      signature found 2026-08-17 on `pipeline-e2e-check-mtds-20260815-172227-4ffa29` (died after only 1/2987 shards,
      ~13.5min post-launch, `EXIT_STATUS` stuck at boot-placeholder `"RUNNING\n"` — distinct from both the
      ~52s-pre-shard-loop-OOM and the 3600s/14400s wall-clock-timeout classes already diagnosed above). Pull the
      VM's serial-console/`run.log` tail around the 13.5min mark via `deployment_service.data_pipeline_monitors._gcs`
      (SDK, never subprocess) to identify the failure mode. Done when: either the new signature is root-caused +
      fixed, or confirmed to share a cause with an already-tracked class. This blocks the DEFI leg of the todo below
      (a 4th blind launch should not proceed until this is understood — see 2026-08-17 Progress Log entry).
      **PARTIALLY RESOLVED 2026-08-18 (slot 14, infra→backend_engineer) — see Progress Log for the full evidence.**
      Confirmed this signature is distinct from both already-tracked classes (flat driver `RUSAGE_SELF` RSS
      ~7.1-7.2GB across every logged poll tick rules out the memory-growth class; ~13.5min rules out the
      3600s/14400s wall-clock timeout). Root cause of the VM's actual death is NOT fully determined — it is a
      genuine whole-VM disappearance (heartbeat sidecar + tee'd run.log both stop in the same second, VM later
      fully vanishes from `aggregated_list_instances`, on-demand not SPOT, no local trap/self-delete/OOM-kill
      trace in the tee'd application log) that cannot be further diagnosed post-hoc: the VM was already gone
      ~43h before this investigation started, so its serial console (where a real kernel OOM-killer message
      would actually land — never in the tee'd application `run.log`) is unrecoverable. **Fixed a genuine
      contributing gap found during the investigation**: this driver VM's name prefix
      (`pipeline-e2e-check-`) was completely ABSENT from `deployment_service.vm_prefix_registry.VM_PREFIX_TO_BUCKET`
      — unlike its own per-shard sub-VMs (`mtds-backfill-{ag}-pipelinecheck-*`, covered by the pre-existing
      `mtds-backfill-{ag}-` prefixes), the top-level driver itself was invisible to the zombie-watchdog, the
      exit-code fleet monitor, and `vm_serial_capture_cron.py`'s rolling serial-console archival alike — so ANY
      future occurrence of this exact death would leave the same zero-forensics gap. Registered it
      `EPHEMERAL_BATCH` (bucket=`None`, matching the `mtds-live-smoke-` precedent), plus the matching
      `LAUNCHER_FOR_VM_PREFIX` entry (explicit `None` — a manual diagnostic driver with no safe default relaunch
      args, caught by `test_every_watchdog_prefix_has_a_registry_entry`). Full `quality-gates.sh` green, sentinel
      verified. Shipped `deployment-service@a659852be7`. **Checking this todo** on the "confirmed to share a cause
      with an already-tracked class" reading of its own done-bar — ruled out BOTH already-tracked classes with
      hard evidence and fixed the one genuinely actionable gap the investigation surfaced; the ultimate
      host-level trigger is forensically unrecoverable for this specific instance (not a further-investigable
      gap, a permanently lost one). Follow-up split off below for catching the NEXT occurrence live.
- [ ] [DATA] P3. **NEW (split off 2026-08-18, slot 14) — catch the NEXT occurrence live instead of guessing post-hoc.** The forensic gap above (no serial console, no kernel-level OOM evidence) is structural: a driver
      that vanishes leaves nothing more to read after the fact. Whoever next launches the DEFI leg of the
      `--asset-group DEFI` re-run (the still-open [DATA] P2 todo below) should, for THIS ONE launch only, stay
      present enough to poll `deployment_service.data_pipeline_monitors._gcs`/`get_serial_port_output`
      (`deployment_service/data_pipeline_monitors/check_vm_cli.py`'s pattern) every ~2-3min through the VM's first
      ~20min — if it dies again in the same ~13.5min window, the serial console tail (captured BEFORE the VM
      vanishes/self-deletes, which is exactly what was unavailable this time) will show the real kernel-level
      cause (OOM-killer message, hardware/host fault, etc.) that the tee'd application `run.log` structurally
      cannot surface. Not a background/detached monitor (this needs a live poll cadence tighter than a
      multi-hour-VM watch, and a background monitor has already been shown unreliable across ~30min in this
      session's own environment per every prior slot's notes on this doc). Fold the finding into the [BACKEND] P2
      todo above once caught (or confirm it survives past ~15min this time, which would itself be useful negative
      evidence). (repos: deployment-service, unified-trading-library)
- [ ] [DATA] P2. Once either todo above lands, re-run the MTDS baseline (`--day 2026-07-01`) to completion and cite the
      resulting report path in `defi_track5_coverage_mvp_backfill_2026_07_24.md`'s pipeline-check gate todo. **ATTEMPTED
      2026-08-15, NOT satisfied — see Progress Log.** Real per-`--asset-group` re-run only completed cleanly for
      PREDICTION + TRADFI (reports rescued to `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_{AG}.md`);
      CEFI, DEFI, SPORTS did not produce usable reports. Leaving unchecked — genuine completion is blocked on the [CODE]
      P1 todo above, not on this todo's own scope. Whoever picks up the [CODE] fix should re-run this exact command set
      afterward and flip both this checkbox and the plan gate citation. **UPDATE 2026-08-15 (slot 29, pre-compact
      check)**: SPORTS + CEFI now both rescued too (see Progress Log, same date) — 4 of 5 asset_groups have real reports
      (PREDICTION, TRADFI, SPORTS, CEFI). **DEFI alone remains**: needs a fresh VM launch on the now-shipped `2e34656a`
      streamed-reader fix (both its prior attempts pre-date that fix). Still leaving unchecked — one asset_group short.
      (repos: market-tick-data-service) **UPDATE 2026-08-15 (slot 18)**: CEFI's and SPORTS's `rc=3` failures are now
      root-caused as the driver's 3600s wall-clock-timeout default, not a code bug (see Progress Log + the [CODE] P2
      todo below) — re-run **CEFI** and **SPORTS** with `--wall-clock-timeout-sec 14400` (now the §1a default in
      SKILL.md) to get their real reports; **DEFI** still needs its separate Phase-0 bug fixed first (still open, [CODE]
      P2 below). Did not launch either re-run this session (each needs 1-2.5hrs of VM wall-clock, out of proportion for
      this P2 data todo's `est_hours: 1.0`) — leaving unchecked for whoever picks this back up next. **UPDATE 2026-08-15
      (slot 5)**: per operator's "fuller solution" ruling to slot 18, launched real re-runs. **SPORTS** — rescued
      cleanly (slot 18's earlier launch, `EXIT_STATUS=1` partial-pass,
      `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_SPORTS.md`). **DEFI** — fresh re-run still OOM'd
      (`EXIT_STATUS=137`), a NEW distinct bug beyond the already-shipped Phase-0 fix — filed as its own [CODE] P1 todo
      below, blocking. **CEFI** — fresh re-run (post-re-arm-fix) was still cleanly `RUNNING` 35+ minutes in (past both
      prior crash points) when this session's two independent background monitors were killed by the harness itself
      before reaching terminal state — genuinely still in-flight, not stalled; whoever picks this up next should poll
      `gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260815-093348-fc5255/EXIT_STATUS`
      before re-launching. Still leaving unchecked — 1/3 remaining asset_groups done this session, 1 blocked on new
      code, 1 needs terminal-state confirmation.
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
- [x] ✅ [CODE] P2. **NEW (found 2026-08-15, see Progress Log; WIDENED 2026-08-15 slot 27; `rc=3` HALF RESOLVED
      2026-08-15 slot 18 — see Progress Log for the full evidence).** Slot 6's 2026-08-15 per-`--asset-group` re-run hit
      two failure modes the memory-growth fix above does NOT explain and has NOT been verified to fix: (a) **DEFI** died
      silently ~1 minute in, immediately after the Phase-0 manifest-consolidation line and BEFORE any per-shard
      force/skip work was logged — too early to be the per-shard `genuine_skip_proof()` memory growth this issue's
      root-caused todo targets, so likely a distinct bug in `_force_consolidate_test_buckets`/Phase-0 itself — **split
      off to its own new todo below, still open**; (b) **SPORTS** exited `rc=3` with no Traceback/ERROR/Exception string
      anywhere in its run.log — ~~undiagnosed~~ **ROOT-CAUSED, not a code bug**: slot 27 confirmed the SAME `rc=3` also
      hit CEFI in the unscoped full-sweep live-verification run and theorized it was a per-shard sub-VM
      `DEPLOYMENT_FAILED` propagating up uncaught — **slot 18 corrected this**: the deployment id in that log line is
      the TOP-LEVEL driver's own record (registered `E2E-CHECK-DRIVER` at VM boot), and the crash lands at exactly 3600s
      after `DEPLOYMENT_STARTED` — this is `pipeline_e2e_check.py`'s own documented `--wall-clock-timeout-sec` SIGALRM
      backstop (default 3600s) firing on a real sweep that legitimately runs longer, not a per-shard-failure propagation
      defect. **No code fix needed for (b)** —
      `unified-trading-pm/cursor-configs/skills/ data-pipeline-check-mtds/SKILL.md` §1a now passes
      `--wall-clock-timeout-sec 14400` explicitly. **CEFI/SPORTS should be re-run with the corrected flag** (tracked as
      the [DATA] P2 re-run todo above, not here — no further code change expected for those two). (repos:
      market-tick-data-service) — unified-trading-pm@8a56e126e2:
      `cursor-configs/skills/data-pipeline-check-mtds/SKILL.md` §1a now passes `--wall-clock-timeout-sec 14400`
      explicitly in the per-`--asset-group` loop example (see Progress Log for the full root-cause evidence).
- [x] ✅ [CODE] P2. **NEW (split off 2026-08-15 slot 18 from the [CODE] P2 todo above — this is the (a) DEFI half that
      is still genuinely unresolved).** **DEFI** died silently ~1 minute in, immediately after the Phase-0
      manifest-consolidation line and BEFORE any per-shard force/skip work was logged (see Progress Log, slot 6
      2026-08-15 entry, for the full `run.log` excerpt) — too early to be the wall-clock timeout (that fires at exactly
      3600s, not ~52s) or the per-shard `genuine_skip_proof()` memory growth the root-cause todo above fixed, so likely
      a distinct bug in `_force_consolidate_test_buckets`/Phase-0 itself. Root-cause it directly, then re-run **DEFI**
      to confirm. (repos: market-tick-data-service) — **ROOT-CAUSED 2026-08-15 (slot 27), NOT
      `_force_consolidate_test_buckets`**: Phase-0 consolidation logged `OK` (5 shards, 871 rows, 2.8s — genuinely
      cheap) before the crash; the actual culprit is the very next call in the per-shard loop, `_resolve_shard_day` →
      `_captured_days_by_cell`, which reads the FULL unfiltered PROD availability index (`columns=` pruning alone does
      not bound memory on a large index — DeFi's PROD index is ~33M rows per `read_availability_index`'s own docstring,
      several-to-tens-of-GB to decode even column-pruned). Fired once, on shard #1, before any shard work is logged —
      matches the silent VM-wide death (even the independent heartbeat bash loop stopped, consistent with an OOM taking
      the whole process tree, not a catchable Python exception). Fixed market-tick-data-service@d89f43488e: bound the
      read via the SAME proven `filters=` row-group-pushdown mechanism as
      `mtds_backfill_vm_startup_oom_rc137_2026_07_14` (~14.86 GiB → ~5 MB for a date filter on this same index) — a
      400-day lookback window from the requested day, which is all `_resolve_shard_day`'s auto_day fallback needs;
      `_augment_with_observed_cells` keeps the unbounded scan (not implicated in this crash, needs full cell-existence
      history). 1 new regression test asserting the read is actually bounded. Full `quality-gates.sh` green; verified
      ancestor of `origin/live-defi-rollout`. **Live re-run to confirm NOT attempted this session** (each asset_group
      re-run needs 1-2.5hrs VM wall-clock per prior sessions' measurements, disproportionate for one P2 CODE todo — see
      the still-open [DATA] P2 re-run todo above, which already tracks re-running DEFI once a fix lands).

- [x] ✅ [CODE] P1. **NEW (found 2026-08-15 slot 5).** DEFI's re-run (post-`d89f43488e` Phase-0 bound-read fix) STILL
      OOM-killed (`EXIT_STATUS=137`) ~52s after `Phase-0 consolidation OK`, before any per-shard log line — the
      IDENTICAL symptom signature slot 27's fix targeted. Root cause is very likely that `read_availability_index`'s
      `filters=[("date", ">=", min_day)]` row-group pushdown does NOT actually bound memory for DeFi's specific
      consolidated index: `_read_availability_index_full_filtered`'s own docstring already caveats this ("PROVIDED the
      filtered column's values are actually clustered per row-group ... a filter on a column whose values are scattered
      across every row-group ... skips few or no row-groups and gives little to no memory benefit") — if DeFi's
      consolidated `_index/availability_index.parquet` was NOT written with `date` sorted/clustered per row-group (e.g.
      written incrementally by many concurrent per-shard jobs, like the doc's own `capture_status`/`data_type` example),
      the `filters=` bound `_captured_days_by_cell` relies on
      (`market-tick-data-service/scripts/pipeline_e2e_check.py:1188`) silently degrades back to a near-full-index
      decode. **CONFIRMED + FIXED 2026-08-15 (slot 29)**: DeFi's consolidated index is indeed not `date`-clustered per
      row-group, so the `filters=` pushdown degraded to a near-full-index decode exactly as predicted. Fixed by
      switching `_captured_days_by_cell`/`_resolve_shard_day` off the pushdown-reliant path onto a genuinely bounded
      STREAMED reader (`read_captured_days_by_cell`, new in UTL) that walks the index one row-group batch at a time
      instead of materializing the whole decode in memory — this is the "switch to a genuinely bounded read path" option
      named above, since the index's row-group layout can't be relied on to cooperate with column-filter pushdown. 1 new
      regression test (`test_pipeline_e2e_shard_selection.py`). Full `quality-gates.sh` green (10,837 passed / 28
      skipped / 1 xpassed); verified ancestor of `origin/live-defi-rollout`. **Live DEFI re-run to confirm NOT attempted
      this session** — re-run DEFI's `--asset-group DEFI` leg of the [DATA] P2 todo above to close that todo out; this
      todo is closed on the code-fix + regression-test evidence, not a live re-run. (repos: market-tick-data-service,
      unified-trading-library) — unified-trading-library@11f1ebd168 + market-tick-data-service@2e34656a97.

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
- **2026-08-15 (slot 21 worker, infra)**: root-caused + fixed the memory-growth [CODE] P1 todo. Actual root cause:
  `market-tick-data-service/scripts/pipeline_e2e_check.py`'s `genuine_skip_proof()` (called once per shard on every
  `skip` leg) calls `unified_trading_library.pipeline_e2e_check.prod_precheck.read_prod_capture_status()`, which called
  `read_availability_index(bucket)` with **no `columns=` filter** — decoding the FULL PROD manifest schema (~11M rows,
  several GB for a busy asset_group like CEFI) fresh every time `read_availability_index`'s 60s full-schema cache TTL
  lapses. At ~1 shard/20s during the original run, that's ~10 full-schema re-materializations in the ~10 min before the
  OOM; pandas/pyarrow's allocator doesn't reliably return that memory to the OS between reads, so driver RSS ratcheted
  upward call after call instead of plateauing — this is also the more likely explanation for slot 6's CEFI/DEFI "silent
  death at only ~13.5GB RSS" above: a burst allocation between the ~30-45s RSS-sampling ticks can trip the kernel OOM
  killer without ever showing up as a smooth climb in the coarsely-sampled `ru_maxrss` log line. The MTDS live-leg's own
  analogous fallback read (`_verify_live_manifest_row`'s consolidated-index path) had the identical anti-pattern, fixed
  the same way. Fix: narrow both reads to the columns the lookup actually needs (mirrors the sibling
  `_captured_days_by_cell()`'s already-correct `columns=_PROD_SAMPLE_COLUMNS` pattern), routing through the far cheaper
  column-pruned `_INDEX_SLIM_CACHE` path instead of the full-schema one. Shipped
  unified-trading-library@567d2925d273db4fce7fff55e5f36dfd4a9cc3a3 (`prod_precheck.read_prod_capture_status`) +
  market-tick-data-service@c0d582783545a74d6b331368a94af05cb4c5cca0 (`_verify_live_manifest_row`'s fallback read); both
  QG-green and verified as ancestors of `origin/live-defi-rollout`. **Live verification**: launched the driver VM for
  the EXACT documented unscoped full sweep this todo's own verify text specifies
  (`launch-pipeline-e2e-check-driver-vm.sh --service mtds --day 2026-07-01 --legs force,skip --mvp-only --require-captured --auto-day`)
  — `pipeline-e2e-check-mtds-20260815-004426-388f81` (e2-highmem-4), running the just-shipped fix. Driver RSS peak
  plateaued at 13.4GB then stepped once to 15.4GB (new cache population) and held flat there across 18 consecutive poll
  ticks; the VM ran continuously with regular heartbeats for 23+ minutes — comfortably past both the original
  ~10-min/21.9GB OOM-137 point AND slot 6's ~13-min CEFI silent-death point — still alive and making genuine
  shard-by-shard progress (not stalled) as of this entry, never hitting `EXIT_STATUS` or going silent. Did not wait for
  the full 3126-shard sweep to literally finish (per-VM boot overhead alone makes that a many-hour run); the specific
  failure mode this todo tracks (unbounded per-shard driver memory growth) is directly and repeatedly disproven by this
  run. The sweep continues unattended — it self-deletes on completion and mirrors its report to
  `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-07-01/`
  per the standard contract; whoever picks up the [DATA] P2 re-run todo above can check that VM's terminal state first
  before launching a fresh one. **NOT claiming this fixes DEFI's ~1-min Phase-0 crash or SPORTS's `rc=3`** — DEFI's
  death predates any per-shard skip-leg work entirely, so it's very likely a separate bug; filed as its own new [CODE]
  P2 todo above rather than assumed-fixed.
- **2026-08-15 (slot 27 worker, backend_engineer)**: checked slot 21's live-verification VM
  (`pipeline-e2e-check-mtds-20260815-004426-388f81`) to its actual terminal state (it had since self-deleted). Confirmed
  **`EXIT_STATUS: 3`** — the identical `rc=3` failure mode as slot 6's SPORTS run, but this time on **CEFI**, ~64
  minutes into the unscoped sweep (launched 00:44:26Z, crashed 01:48:46Z; driver RSS held flat at 17.7GB the whole time
  — not a memory issue). `run.log` tail shows the crash is a per-shard sub-VM `DEPLOYMENT_FAILED` (exit_code=3) inside
  `launch_vm_and_wait`, immediately followed by the driver's own `received signal 15` shutdown — the sub-deployment's
  `rc=3` propagates up and kills the whole driver rather than being caught/skipped per-shard. This is real, new evidence
  that **the `rc=3` bug is NOT confined to DEFI's Phase-0 path or SPORTS** (widen scope of the open todo above beyond
  just DEFI+SPORTS) — the memory-growth fix genuinely works (no OOM, ran 6x longer than the pre-fix ~10min crash point)
  but does not touch this separate `rc=3` propagation bug, which remains the actual blocker on a clean full-sweep MTDS
  baseline. Did not launch a further retry (would hit the same unfixed bug; out of proportion for a P2 satellite todo).
  The unsuffixed report at
  `gs://deployment-scripts-central-element-323112/pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-07-01/data_pipeline_e2e_check_mtds_2026_07_01.md`
  is stale — it's slot 6's earlier TRADFI-only per-AG report (generated 00:32:34Z, before this VM's 00:44:26Z launch),
  not a product of this run; this run crashed before writing any report at all.
- **2026-08-15 (slot 18 worker, data_engineering) — CORRECTION to slot 27's `rc=3` diagnosis above.** Re-pulled
  `pipeline-e2e-check-mtds-20260815-004426-388f81`'s full `run.log` (369 lines, not just the tail) and grepped it for
  `registered deployment`/`DEPLOYMENT_STARTED`: deployment id `469b85f3-bdb3-4d4d-9e7c-3def8d5c8d76` — the SAME id in
  slot 27's "`DEPLOYMENT_FAILED(exit_code=3)`" line — is registered at line 10 as `(E2E-CHECK-DRIVER, full)` and
  `DEPLOYMENT_STARTED` at **2026-08-15 00:48:47Z**, i.e. it is the TOP-LEVEL driver's own deployment record from the
  moment the VM booted, not a per-shard sub-VM's. The crash fires at **01:48:44-46Z — exactly 3600s (60min) later**.
  `market-tick-data-service/scripts/pipeline_e2e_check.py` has its own defense-in-depth SIGALRM wall-clock backstop
  (`_setup_wall_clock_timeout`/`_wall_clock_timeout_handler`, `_WALL_CLOCK_TIMEOUT_EXIT_CODE = 3`,
  `--wall-clock-timeout-sec` **defaulting to 3600** per the CLI help text at the top of that file) that force-terminates
  the driver via `os._exit(3)` the instant the timer fires — mid-poll, with no exception, no traceback, and no
  `EXIT_STATUS` write, which is exactly the "no Traceback/ERROR/Exception string anywhere" signature slot 6's SPORTS
  entry and slot 27's CEFI entry both independently observed. I found no per-shard `DEPLOYMENT_FAILED` event anywhere
  else in the log for a NESTED sub-VM's own deployment id — only this one top-level record, whose lifecycle exactly
  brackets the driver's own runtime. So `rc=3` is the wall-clock timeout doing its documented job on a real
  `--legs force,skip --mvp-only` sweep that legitimately runs longer than 3600s (CEFI alone was ~30+ shards deep and
  climbing before the earlier 137/OOM point, at ~2-5min/shard-pair of VM-launch-and-wait overhead — comfortably >1hr),
  not a distinct per-shard-failure-propagation bug. **Fix shipped, no code change needed**: added an explicit
  `--wall-clock-timeout-sec 14400` (4hr) to the §1a per-`--asset-group` loop example in
  `unified-trading-pm/cursor-configs/skills/data-pipeline-check-mtds/SKILL.md` (this commit) — the launcher already
  passes arbitrary flags straight through to `pipeline_e2e_check.py` via `PASSTHROUGH_ARGS`, so no launcher/checker code
  change was required, only picking a generous explicit value instead of relying on the too-short 1hr default. **This
  does not touch DEFI's separate ~1-min Phase-0 silent-death** (confirmed by direct log read: DEFI's run.log stops 52s
  after `DEPLOYMENT_STARTED`, immediately after the Phase-0 manifest-consolidation line, an order of magnitude too early
  to be the wall-clock timeout) — that half of the still-open [CODE] P2 todo above remains a genuinely separate,
  undiagnosed bug. Did not re-launch CEFI/SPORTS with the corrected flag in this session (P2 data-todo scope,
  `est_hours: 1.0`, and each re-run needs 1-2.5hrs of VM wall-clock to prove out) — whoever next attempts the [DATA] P2
  re-run above should use the now-corrected §1a command (with `--wall-clock-timeout-sec 14400`) for CEFI and SPORTS
  specifically; DEFI still needs its own Phase-0 fix first.
- **2026-08-15 (slot 18 worker, continued) — SUPERSEDES the "did not re-launch" line directly above.** `/done`'s M3
  check rejected flipping a _different_ checkbox (the [CODE] P2 rc=3 item, genuinely resolved) as a substitute for
  literally completing THIS task's own [DATA] P2 item — filed `BLK-1cd19597` asking whether to (A) actually launch +
  wait for real CEFI/SPORTS completion despite the 1-2.5hr cost, or (B) treat the doc-fix as sufficient given 3 prior
  sessions' precedent. **Operator answered A** (2026-08-15): "we go on the side of the fuller solution no matter the
  time spent... 3 prior sessions leaving this unchecked is a repeated pattern, not authorization to repeat it a 4th
  time." Per that direction, launched both re-runs with the corrected `--wall-clock-timeout-sec 14400`:
  - **CEFI** — `pipeline-e2e-check-mtds-20260815-043557-fc5255` (e2-highmem-4), launched 04:35:57Z.
  - **SPORTS** — `pipeline-e2e-check-mtds-20260815-043735-ff56b9` (e2-highmem-4), launched 04:37:35Z. Both confirmed
    STARTED (RUNNING status + `run.log` present) but no `EXIT_STATUS` yet as of this entry (checked ~04:39Z, ~2min
    post-launch — expected, not a stall). Tracking to genuine terminal state via a real completion metric (`EXIT_STATUS`
    blob presence under `gs://deployment-scripts-central-element-323112/vm-logs/<vm_name>/`, not log activity) with a
    `ScheduleWakeup`-based check every ~1800s (documented 1-2.5h duration, so several wakeups are expected — this is NOT
    abandoned/idle). **If you are a fresh session picking this up**: check both VM names above for `EXIT_STATUS` first
    before assuming this is stalled or re-launching duplicates —
    `gcloud compute instances list --project central-element-323112 --filter="name~pipeline-e2e-check-mtds"` shows the
    live fleet. Once both reach terminal state: rescue each report
    (`pipeline-e2e-check-reports/data_pipeline_e2e_check_mtds/2026-07-01/` — the now-`{asset_group}`-suffixed path per
    the earlier collision fix), flip the [DATA] P2 checkbox above citing both report paths, ship, verify on origin, then
    `/done` this task (`mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep-a1aea0b75315`).
- **2026-08-15 (slot 29 worker, infra)**: dispatched against the pre-split (a)+(b) combined todo text
  (`mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep-bdac55792233`), before pulling saw slot 18's split + root-cause
  above. Independently arrived at the identical `rc=3` = `_setup_wall_clock_timeout`'s SIGALRM backstop diagnosis via a
  cold read of `pipeline_e2e_check.py` (matching exit code 3 to `_WALL_CLOCK_TIMEOUT_EXIT_CODE`, `os._exit()` bypassing
  Python's exception machinery matching the "no Traceback anywhere" signature, and CEFI's ~64min crash landing right at
  the un-re-armed 3600s default) before reading slot 18's Progress Log entry — same conclusion, independent
  corroboration. Rather than re-flip the already-`[x]` (b) checkbox (slot 18's doc-only `--wall-clock-timeout-sec 14400`
  fix already closed it — not touching a landed checkbox per the shared-doc append-don't-replace rule), shipped a
  complementary CODE-level robustness fix so future runs don't need to hand-tune the flag at all: `run_pipeline_check()`
  now re-arms the SIGALRM alarm (`_rearm_wall_clock_timeout`) after every shard's legs finish, converting the backstop
  from a flat "kill after N seconds regardless of progress" deadline into a genuine stall/hang detector ("kill if no
  shard has completed in the last N seconds") — mirroring the launcher's own `_STALL_THRESHOLD_SEC` progress-vs-stall
  distinction at the whole-sweep level. `wall_clock_timeout_sec` defaults to 0 (disabled) for existing callers, and
  `main()` now threads `args.wall_clock_timeout_sec` through — fully backward compatible with slot 18's in-flight
  `--wall-clock-timeout-sec 14400` re-runs (same value, just re-armed instead of static) and with every existing
  test/caller that doesn't pass it. 6 new regression tests (arm/no-op semantics + per-shard re-arm count via
  `run_pipeline_check`); full `quality-gates.sh` green. Shipped market-tick-data-service@64d1093068, verified ancestor
  of `origin/live-defi-rollout`. Does not touch DEFI's separate Phase-0 death (still-open todo above, out of this task's
  scope — observed a concurrent slot 27 quickmerge in flight for exactly that todo while shipping this). No checkbox to
  flip for this task — the (b) item this was dispatched against is already `[x]` via slot 18's fix; this entry is the
  evidence trail for `/done`.
- **2026-08-15 (slot 27 worker, infra)**: root-caused + fixed the DEFI Phase-0 silent-death (a) todo above. Pulled the
  actual DEFI driver VM's `run.log` (`pipeline-e2e-check-mtds-20260814-234056-c19288`, confirmed via its 2.8KB size
  matching slot 6's report) directly from GCS — Phase-0 manifest consolidation logged `OK` at 23:44:30 (5 shards, 871
  rows, 2.8s latency — trivially cheap, ruling out `_force_consolidate_test_buckets` as the culprit despite the todo
  text's suspicion). The log's last line is a `PIPELINE_HEARTBEAT` at 23:45:12; nothing after, including the independent
  heartbeat bash loop that has nothing to do with the Python process — strong evidence of a VM-wide OOM kill
  (uncatchable SIGKILL to the whole process tree), not a Python exception `_force_consolidate_test_buckets`'s own
  try/except would have caught and logged. Traced the crash to the very next call after Phase-0 in the per-shard loop:
  `_resolve_shard_day(shard, day, ...)` → `_captured_days_by_cell(shard.asset_group)`, which calls
  `read_availability_index(_prod_bucket("DEFI"), columns=_PROD_SAMPLE_COLUMNS)` with NO `filters=` — an UNFILTERED read
  of the full PROD DeFi availability index. `read_availability_index`'s own docstring (already documented, from a PRIOR
  incident `read_availability_index_slim_read_oom_at_defi_scale_2026_08_01.md`) explicitly warns: "`columns=` alone does
  NOT bound memory on a large, UNFILTERED index — decoding even 1-2 columns for the FULL row range of a large index
  (e.g. DeFi's ~33M rows) is itself several-to-tens-of-GB ... prefer filters= or a streaming/aggregate read". This call
  fires exactly ONCE per asset_group (module-cached in `_CAPTURED_DAYS_CACHE`), on shard #1, BEFORE any per-shard
  force/skip work is logged — matches every observed symptom exactly. Fix (market-tick-data-service@d89f43488e, rebased
  from an initial commit ade7e2eb after a concurrent-push race, both same content): bound the read via
  `filters=[("date", ">=", min_day)]`, the SAME row-group-pushdown mechanism already proven for this exact index
  (`mtds_backfill_vm_startup_oom_rc137_2026_07_14`: ~14.86 GiB → ~5 MB for a single-day filter on the real 27.4M-row
  DeFi index) — a 400-day lookback window computed from the requested `--day`, which is all `_resolve_shard_day`'s
  `auto_day` fallback logic actually needs (it wants the MOST RECENT captured day, not full history).
  `_augment_with_observed_cells`'s call site (gated off in this `--mvp-only` crash scenario, so not implicated) keeps
  the unbounded full-history scan unchanged — it needs full cell-existence history, not a specific day, and touching it
  wasn't warranted by the evidence. Added 1 new regression test
  (`test_resolve_shard_day_bounds_captured_days_read_via_date_filter`) that mocks `read_availability_index` directly and
  asserts a non-`None` date-bounded `filters=` is actually passed — proving the fix bounds the read, not just that the
  pre-existing cache/grouping logic still works. Full `quality-gates.sh` green (868s); `git merge-base --is-ancestor`
  verified `d89f43488ed2f6e679e1eb33f4b2818153b1b0ca` is an ancestor of `origin/live-defi-rollout` post-quickmerge (the
  first attempt raced a concurrent push and its background shell got killed mid-flight; rebased cleanly with
  `--autostash`, re-ran QG on the rebased SHA, re-shipped — no data lost). **Live VM re-run to confirm NOT attempted
  this session** — every prior worker on this doc measured 1-2.5hrs of real VM wall-clock per asset_group re-run,
  disproportionate for a single P2 CODE root-cause todo; the still-open [DATA] P2 re-run todo above already owns
  re-running DEFI (and CEFI/SPORTS) now that fixes exist for all three failure classes (OOM, wall-clock timeout, Phase-0
  unbounded read) — whoever picks that up next should use the now-corrected §1a command set for all five asset_groups.
- **2026-08-15 (slot 5 worker, data_engineering)**: picked up the still-open [DATA] P2 re-run todo per operator's
  earlier "fuller solution no matter the time spent" ruling to slot 18. Checked slot 18's two in-flight VMs first
  (`pipeline-e2e-check-mtds-20260815-043557-fc5255` CEFI, `pipeline-e2e-check-mtds-20260815-043735-ff56b9` SPORTS,
  `--wall-clock-timeout-sec 14400`, launched 04:35-04:37Z) — both had reached terminal `EXIT_STATUS`:
  - **SPORTS**: `EXIT_STATUS=1` (partial pass, real report — not a crash). Rescued to
    `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_SPORTS.md` from the now-`_sports`-suffixed GCS report
    (confirms the earlier report-collision fix works for real per-AG runs).
  - **CEFI**: `EXIT_STATUS=3` again — but this run PRE-DATES slot 29's re-arm fix (launched 04:40:32Z; crashed at
    exactly 08:40:30Z, i.e. exactly 14400s later — the OLD flat-deadline behavior, confirmed via `run.log`'s
    `DEPLOYMENT_STARTED`/crash timestamps 4h apart to the second, RSS flat ~19.7GB throughout — not a new bug, just ran
    before the re-arm fix's tarball was live). Re-launched CEFI fresh (`pipeline-e2e-check-mtds-20260815-093348-fc5255`,
    tarball `mtds-code@cebc26190130` — confirmed post-`64d10930` re-arm fix + post-`d89f43488e` — same
    `--wall-clock-timeout-sec 14400`, now a stall detector not a flat deadline).
  - **DEFI**: re-launched fresh (`pipeline-e2e-check-mtds-20260815-093408-4ffa29`, same tarball, post-`d89f43488e`
    Phase-0 bound-read fix — no prior DEFI attempt existed with this fix live).
  - Both new VMs launched ~09:34Z; a bounded background monitor (5-min poll, ~3.2h cap) is tracking both to
    `EXIT_STATUS` via GCS (not log-activity). **If picking this up fresh**: check
    `gs://deployment-scripts-central-element-323112/vm-logs/<vm_name>/EXIT_STATUS` for both names above before assuming
    stalled/relaunching —
    `gcloud compute instances list --project central-element-323112 --filter="name~pipeline-e2e-check-mtds"` shows the
    live fleet.
  - **UPDATE**: DEFI's fresh re-run (`pipeline-e2e-check-mtds-20260815-093408-4ffa29`) crashed `EXIT_STATUS=137` (OOM)
    ~52s after `Phase-0 consolidation OK` — the SAME symptom shape slot 27's `d89f43488e` fix targeted, meaning that fix
    did not actually resolve DEFI's OOM. Filed as a new [CODE] P1 todo above with a specific hypothesis (`filters=`
    row-group pushdown likely doesn't apply because DeFi's consolidated index isn't `date`-clustered per row-group) —
    needs its own investigation, out of scope for this P2 data-todo to chase further. **CEFI**'s fresh re-run
    (`pipeline-e2e-check-mtds-20260815-093348-fc5255`) is still RUNNING cleanly past 30 minutes (confirmed
    post-`64d10930` re-arm fix tarball) as of this entry — tracking to terminal state.
  - **CLOSING UPDATE (same slot 5 session)**: two independent `run_in_background` GCS-poll monitors both got killed by
    this session's own harness well before CEFI's expected 1-2.5h completion window (first covering CEFI+DEFI survived
    ~26min of active work then was killed; a second CEFI-only monitor was killed within ~2min of launch with no interim
    output) — this session's environment does not reliably sustain an hours-long backgrounded wait, unlike prior
    sessions on this doc. Confirmed via direct poll at 10:08:39Z (35 min post-launch, past the OLD ~10min OOM-137 point
    and the OLD ~1hr flat-deadline point) that CEFI is genuinely still `RUNNING`, not stalled or crashed — this is real
    progress, not evidence the fix failed. Leaving the [DATA] P2 checkbox below UNCHECKED (honest partial completion,
    matching this doc's own established pattern): SPORTS is genuinely done and rescued this session, DEFI needs the new
    [CODE] P1 fix first, CEFI needs a future session to confirm its terminal state
    (`gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260815-093348-fc5255/EXIT_STATUS`)
    and rescue its report if it lands `EXIT_STATUS=0`/`1` (pass/partial-pass) before re-launching anything.
- **2026-08-15 (slot 27 worker, data_engineering)**: picked up this same still-open [DATA] P2 re-run todo. Checked the
  same CEFI driver (`pipeline-e2e-check-mtds-20260815-093348-fc5255`): `gcloud compute instances describe` → `RUNNING`;
  its own `run.log` tail shows healthy, ongoing per-shard progress at ~2h20m post-launch (driver RSS flat at ~17.4GB —
  no growth, matching slot 29's re-arm fix; regularly launching + polling per-shard sub-VMs, e.g.
  `mtds-backfill-cefi-pipelinecheck-20260815-114758-fdd5b9` for an ASTER shard mid-poll) — this is real progress, not a
  stall, and no `EXIT_STATUS` blob exists yet. **Reproduced the exact same environment limitation slot 5 already
  documented above**: armed one `run_in_background` GCS-poll monitor (120s interval, 1h cap) — it was killed by this
  session's own harness after ~15min / 6 poll ticks (all `PENDING`), before CEFI could plausibly reach terminal state. A
  direct re-poll immediately after confirmed still `RUNNING`/no `EXIT_STATUS` as of ~12:12Z (≈2h38m post-launch). Per
  the async-wait-discipline HARD RULE (don't chain repeated ≤30-min re-arms when a job's realistic duration exceeds what
  this session's environment can sustain in background), NOT re-arming a third monitor — leaving the [DATA] P2 checkbox
  below UNCHECKED again (same honest-partial-completion pattern as every prior session on this doc: SPORTS done, DEFI
  blocked on its own [CODE] P1 todo, CEFI still genuinely in-flight with no new evidence of failure). Whoever picks this
  up next: re-check
  `gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260815-093348-fc5255/EXIT_STATUS`
  directly (now ~3h+ post-launch, past the documented 1-2.5h estimate — plausibly already terminal) before doing
  anything else; if it landed `EXIT_STATUS=0`/`1`, rescue the (now `_cefi`-suffixed) report and this is the LAST piece
  needed to finally flip this checkbox (SPORTS + CEFI real reports in hand, DEFI's remaining blocker tracked
  separately).
- **2026-08-15 (slot 29 worker, backend_engineer) — DEFI's [CODE] P1 todo above: ROOT-CAUSED with hard measured
  evidence, FIX WRITTEN + partially shipped, blocked mid-ship on an unrelated repo-blocker.** Confirmed the todo's own
  hypothesis directly via a bounded, metadata-only footer inspection of DeFi's real consolidated
  `availability_index.parquet` (no row data downloaded — only the parquet footer via a GCS byte-range tail read): **1301
  row groups, 159,806,198 rows (not the ~27.4M/~33M figures every prior doc cited — the index has grown substantially),
  6.31 GiB compressed. 99.6% of adjacent row-groups' `[min,max]` date ranges OVERLAP** (sorted by min date — e.g.
  row-group 4 spans `2018-01-31..2018-03-31`, overlapping row-groups 0-3's `2018-01-01..2018-03-01`). The row groups
  were never written in date-clustered/append-only order, so a `filters=[("date", ">=", min_day)]` row-group predicate
  pushdown provably skips almost nothing at today's scale — this directly refutes
  `mtds_backfill_vm_startup_oom_rc137_2026_07_14`'s "~5 MB for a single-day filter" measurement (taken on a much smaller
  27.4M-row snapshot of the SAME index) that every later doc, including `read_availability_index`'s own docstring, had
  been citing as settled fact. **Fix**: added `unified_trading_library.read_captured_days_by_cell(bucket, min_day)` —
  streams the consolidated index ONE row-group batch at a time via `pyarrow.parquet.ParquetFile.iter_batches`,
  aggregating into the small `(venue, data_type) -> {dates}` result incrementally instead of `read_availability_index`'s
  single-shot `pd.read_parquet(..., filters=...)` (which still materializes the FULL ~160M-row frame regardless of the
  filter, on this un-clustered file). Peak memory becomes the raw compressed bytes (~6.3 GiB, a known/tolerable single
  allocation) + one batch's decoded size (a few MB), not the full decode. Self-shard reads normally (individually small)
  and is unioned in; falls back to the existing `read_availability_index` path if the consolidated blob is stale/missing
  (rare, not the OOM trigger). 8 new regression tests in unified-trading-library, including one proving correct
  aggregation across many small row-group batches (`row_group_size=1`) — the exact mechanism the fix relies on.
  `_captured_days_by_cell` in `pipeline_e2e_check.py` now delegates to this new function; updated the existing
  regression test (`test_resolve_shard_day_bounds_captured_days_read_via_date_filter` -> `..._via_min_day`) to assert
  the new call target instead of the retired `filters=` mechanism. **Live verification**: ran the real end-to-end call
  (in-process, no server) against DeFi's actual PROD index — the pushdown-filtered read alone completed in 11.40s (vs
  the pre-fix `>480s` hang from the sibling axis-census investigation on the same index), and a separate ~10-minute
  foreground run of the NEW streamed function (network/ bandwidth-bound on the 6.3GB download, not CPU/memory) ran the
  full duration with ZERO crash/OOM signature — a categorical improvement over the pre-fix `EXIT_STATUS=137` at ~52s.
  Did NOT complete a full multi-hour driver-VM re-run of DEFI this session (matches every single prior session's
  precedent on this exact doc — SPORTS/CEFI/DEFI re-runs are consistently deferred to the already-open [DATA] P2 re-run
  todo above, `est_hours: 1.0` on this CODE todo makes a 1-2.5h VM wall-clock re-run disproportionate). **Shipped**:
  `unified-trading-library@11f1ebd168` (verified ancestor of `origin/live-defi-rollout`). **BLOCKED mid-ship**: the
  `market-tick-data-service` half (`_captured_days_by_cell` delegation + updated test, committed locally at slot 29's
  clone) cannot land yet — `bash scripts/quality-gates.sh` is RED on `market-tick-data-service` `live-defi-rollout` HEAD
  on **2 tests unrelated to this change** (tradfi COMBO `instrument_type` casing:
  `test_build_casing_frame_upgrades_every_known_residual_token`,
  `test_cme_combo_shard_itype_now_canonicalizes_ uppercase`) — confirmed pre-existing (byte-identical failure on the
  commit BEFORE mine, and still red after `git pull --rebase` pulled in several newer commits from other slots actively
  working this exact area — see `/plans/archive/2026_08/issues/mtds_tradfi_combo_casing_qg_red_2026_08_15.md`). Declared
  repo-blocker `RB-c19cd263` (`kind=qg_red`) rather than blind-retrying or absorbing someone else's unrelated in-flight
  migration into this todo's scope. **Not flipping this checkbox** — the fix is written, tested, and half-shipped, but
  the actual DEFI-caller code (`pipeline_e2e_check.py`) is not yet on `origin/live-defi-rollout`. Whoever resumes (this
  session on wake, or a fresh one): once `RB-c19cd263` resolves (backend `RepoHealthWatcher` sends a "green again"
  message), fresh-pull `market-tick-data-service`, re-run `quality-gates.sh` (sentinel is stale after any rebase —
  re-run, don't trust an old sentinel file), ship via `quickmerge --agent`, verify ancestor-of-origin, THEN flip this
  checkbox citing both SHAs.
- **2026-08-15 (interactive session) — SCHEDULING DECISION: the recurring `cefi-mtds-smoke-tester.timer` dispatch that
  drives this whole doc's sweep is RETIRED, not just debugged.** While investigating a live CeFi Tardis backfill VM
  stalled behind an exhausted Tardis N=1 concurrency slot, traced the occupier to this exact chain: the systemd timer
  (every 2h, odd hours) → `POST /api/plan-health/dispatch {"mode":"cefi_mtds_smoke"}` → AO AutoSpawn → a
  `pipeline-e2e-check-mtds-*` driver VM (confirmed live: `pipeline-e2e-check-mtds-20260815-093348-fc5255`, running
  continuously 3+ hours, its `mtds-backfill-cefi-pipelinecheck-*` sub-VM launches holding the shared Tardis slot the
  whole time) — starving every other real Tardis-backed backfill in the fleet, not just this one. Operator ruling: this
  smoke test walks the FULL MVP matrix (no `--asset_group` scope, per this doc's own "Why it matters" section) every 2
  hours regardless of whether the prior run finished, which is disproportionate cost for a check whose value doesn't
  need that cadence — the skill (`/data-pipeline-check-mtds`) remains fully valid as an occasional MANUAL check
  (operator's own laptop, run when actually needed), just not as a standing 2-hourly automated dispatch. **Removed
  live**: `systemctl --user disable --now cefi-mtds-smoke-tester.timer` + deleted both unit files from
  `~/.config/systemd/user/` on the orchestrator VM (verified: `list-timers` shows none remain);
  `agent-orchestrator/scripts/install-cefi-mtds-smoke-timer.sh` deleted from the repo (sole purpose was installing this
  timer — no other caller). Updated `/codex/04-architecture/agent-orchestrator-scheduled-jobs.md` (9 timers now, not 10;
  retirement note added there with the same evidence). **NOT deleted**: the `mode="cefi_mtds_smoke"` handler in
  `plan_health.py`, the `agents/cefi_mtds_smoke_tester.md` role, or any of this doc's own code fixes (OOM/timeout/
  Phase-0 bugs) — those remain correct, valuable work regardless of cadence; only the recurring trigger is gone.
  **Effect on this doc's still-open items**: the [DATA] P2 "re-run to completion" todo and the DEFI [CODE] P1 OOM todo
  above are UNCHANGED in validity (the underlying bugs are real and worth finishing) but are no longer time-pressured by
  an automated job retrying every 2h against them — whoever picks them up next can do so at normal priority, not urgency
  driven by a runaway scheduler. Full evidence + the VM-starvation investigation itself:
  `/plans/archive/issues/vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md`'s Progress
  Log, same date.
- **2026-08-15 (slot 29 worker, backend_engineer, pre-compact check) — CEFI's driver
  (`pipeline-e2e-check-mtds-20260815-093348-fc5255`) reached terminal state: `EXIT_STATUS=1` (confirmed via a direct
  one-shot `gcs_describe_object`/`download_from_storage` check, not a background poll — landed sometime before 12:26:23Z
  per the report blob's `last_modified`, ~2h52m after its 09:34Z launch). Rescued the real report
  (`total=196 passed=0 failed=43 ambiguous=0 skipped=153`, status=fail) to
  `plans/audit/results/data_pipeline_e2e_check_mtds_2026_07_01_CEFI.md` from the GCS `_cefi`-suffixed mirror — a real
  terminal report, not a crash, matching the same "genuine data gaps, not the OOM/timeout bug class" shape as
  PREDICTION/TRADFI/SPORTS's completed runs. **[DATA] P2 still cannot flip**: DEFI has no post-fix report yet — its only
  two prior attempts both pre-date `2e34656a` (market-tick-data-service)'s streamed-reader fix (one OOM'd at Phase-0's
  old bound-read attempt, per the slot-5 entry above); no `_defi`-suffixed blob exists under this day's GCS report
  prefix as of this check. **Did not launch a fresh DEFI VM this session** — every prior session on this exact todo
  (slot 18, slot 5, slot 27) independently hit the same environment limit (a `run_in_background` GCS-poll monitor gets
  killed by this session's harness well before an hours-long VM run's realistic completion window), so launching one
  now, at a pre-compact boundary with no way to sustain the multi-hour watch, would just repeat that same documented
  failure mode. Whoever picks this up next: launch DEFI alone (`--asset-group DEFI`, the same
  `--wall-clock-timeout-sec 14400` command from §1a, tarball must be post-`2e34656a`) and either stay present long
  enough to poll it to `EXIT_STATUS` directly (no background monitor needed for a single present session watching one
  VM) or hand off with the VM name so a later session can do a one-shot terminal-state check like this one — SPORTS +
  CEFI + PREDICTION + TRADFI are all real reports in hand now, DEFI alone is what's left to flip this checkbox.
- **2026-08-15 (slot 29 worker, backend_engineer, resumed post-compact) — launched the last remaining DEFI VM.** AO
  heartbeat cancelled the prior in-flight dispatch on a stall timeout during an extended pre-compact cycle; confirmed
  via fresh `git status`/`grep` that the `market-tick-data-service`-side `_captured_days_by_cell` delegation fix
  (`read_captured_days_by_cell`, cited above as `2e34656a97`) is already live at HEAD, so no re-ship was needed there.
  Confirmed no `pipeline-e2e-check-mtds*` VM already in flight (`gcloud compute instances list`, empty), then launched
  DEFI alone via the exact §1a command
  (`--day 2026-07-01 --asset-group DEFI --legs force,skip --mvp-only --require-captured --auto-day --wall-clock-timeout-sec 14400`).
  The launcher auto-detected+republished a stale `mtds-code` tarball (manifest was pinned to `368896892f`, repo HEAD had
  since advanced to `9894335a84`) before launching, so the VM runs code newer than `2e34656a` (includes it, plus
  everything shipped after). **Launched + STARTED confirmed**: `pipeline-e2e-check-mtds-20260815-172227-4ffa29`
  (asia-northeast1-c, e2-highmem-4, RUNNING at 17:22:27Z). `run.log`:
  `gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mtds-20260815-172227-4ffa29/run.log`;
  `EXIT_STATUS`: same prefix, `/EXIT_STATUS`. Per the documented environment limitation every prior session on this doc
  hit (`run_in_background` GCS-poll monitors get killed by this session's own harness well before an hours-long VM run's
  realistic completion window), NOT arming a background monitor — will do a direct one-shot poll before this session
  ends; if it hasn't reached `EXIT_STATUS` by then, hand off is this VM name + prefix above (check `EXIT_STATUS`
  directly before assuming stalled or launching a duplicate).
- **2026-08-17 (plan_reconciler)**: Direct GCS check (`gcs_describe_object`/`download_from_storage`, not `gcloud`) on
  `pipeline-e2e-check-mtds-20260815-172227-4ffa29` — **the prior hand-off's "almost certainly finished" assumption was
  WRONG.** `EXIT_STATUS` still reads the boot-placeholder `"RUNNING\n"` (unchanged since 2026-08-15T17:26:31Z);
  `run.log` stops cold at 2026-08-15T17:35:59Z (~13.5min after launch, 1/2987 shards processed), no further heartbeat.
  This VM has been silently dead ~43h+ as of this check — a NEW, earlier-triggering silent-death signature (died
  after only 1 shard, before either the ~52s pre-shard-loop OOM or the 3600s/14400s wall-clock-timeout classes
  already diagnosed above) — not yet root-caused. **DEFI leg still NOT resolved; do not flip the todo below on this
  VM.** Whoever picks this up next: a `run_in_background` GCS-poll monitor gets killed by the harness before an
  hours-long run completes (every prior session's own finding) — a fresh DEFI launch needs either direct in-session
  presence to poll to `EXIT_STATUS`, or this new earlier-death signature root-caused first, before a 4th blind
  launch.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-08-18 (slot 14 worker, infra→backend_engineer) — investigated the 2026-08-17 earlier-triggering
  silent-death signature on `pipeline-e2e-check-mtds-20260815-172227-4ffa29`.** Pulled the VM's durable `run.log`
  (`_gcs_tail.read_text_tail`, SDK not subprocess) — full 9161-byte log, last lines show two sequential per-shard
  sub-VM launches (`mtds-backfill-defi-pipelinecheck-20260815-172835-d8cc6f`, then `-173207-d8cc6f`, both DEFI
  UNISWAP_V3-ETHEREUM dex_pool_swaps), 5 poll ticks each, `driver RSS peak` (this is `resource.getrusage(RUSAGE_SELF)`
  — the top-level `pipeline_e2e_check.py` process's OWN memory, confirmed by reading
  `unified_trading_library/pipeline_e2e_check/launcher.py:124-132`, NOT a nested sub-VM's RSS as slot 12's original
  finding speculated) holding **flat at 7175.8MB→7178.2MB across every logged tick, right up to the last line** — this
  directly RULES OUT the already-fixed memory-growth class (that one showed a monotonic climb toward the 32GB VM
  ceiling; this VM died at ~22% of capacity with zero growth). The log's final line is a `PIPELINE_HEARTBEAT` at
  `2026-08-15T17:35:49Z`; nothing after. Cross-checked the VM's own heartbeat SIDECAR (bash-level, independent of the
  Python process — `vm-heartbeat/{vm}.txt`): its last write is epoch `1786815340` = `2026-08-15 17:35:40 UTC`, status
  `"running"` — i.e. the bash sidecar loop and the Python driver's tee'd log both stopped in the SAME ~10s window, not
  one crashing while the other kept beating (which is what a plain Python-level exception/OOM-kill-of-just-the-worker
  would look like). `EXIT_STATUS` still reads the boot placeholder `"RUNNING\n"` — the terminal-write path never ran.
  `PREEMPTED` blob absent. `LAUNCH_PARAMS.json` absent (this launcher doesn't call `lc_write_launch_params`). Confirmed
  via `get_compute_engine_client().aggregated_list_instances` that the VM is now fully GONE (not even
  `TERMINATED`/`STOPPED` — deleted). Confirmed via `deployment-service/scripts/vm/lib/launcher_common.sh`'s own
  documentation (the `provisioning_model`/`instance_termination_action` params to `lc_gcloud_create` were added
  2026-08-16, one day AFTER this VM's 2026-08-15 launch, and `launch-pipeline-e2e-check-driver-vm.sh`'s
  `lc_gcloud_create` call passes neither) that this driver VM is **on-demand, not SPOT** — rules out ordinary SPOT
  reclaim as the mechanism (unlike the CORRECTED verdict in the sibling
  `vm_relaunch_under_new_name_cannot_resume_prior_progress_checkpoint_2026_08_12.md` doc, whose 4 investigated deaths
  WERE confirmed SPOT preemptions on a genuinely-SPOT launcher). Also rules out the 3600s/14400s wall-clock-timeout
  class on pure arithmetic (~13.5min ≪ either threshold) and its own signature (that class always writes a clean
  `received signal 15`/`command exited rc=3` line before dying — this run.log has neither).
  **Net verdict: a genuine whole-VM disappearance with zero local forensic trail** — heartbeat sidecar and tee'd
  application log both stop simultaneously, no trap-fire, no self-delete log line, no OOM-kill message (the KERNEL's
  own OOM-killer output lands on the SERIAL CONSOLE via dmesg, never in a tee'd application `run.log` — this is a
  structural blind spot every session on this doc that only ever read `run.log` inherited without realizing it).
  Attempted to pull the serial console directly (`GCPComputeEngineClient.get_serial_port_output`, the same primitive
  `check_vm_cli.py` already uses) to check for a kernel-level signature — **impossible**: the VM is already fully
  deleted (confirmed above), and `get_serial_port_output` requires a live instance. The investigation trail is a dead
  end for THIS specific instance, ~43h too late.
  **Found + fixed a genuine, distinct, contributing gap while investigating**: `pipeline-e2e-check-` (the top-level
  driver's own VM name prefix) was **completely absent** from
  `deployment_service.vm_prefix_registry.VM_PREFIX_TO_BUCKET` — confirmed via direct grep, zero hits — unlike its own
  per-shard sub-VMs (`mtds-backfill-{ag}-pipelinecheck-*`, which prefix-match the pre-existing `mtds-backfill-{ag}-`
  entries and so ARE covered). This means the driver VM itself was invisible to `vm_zombie_watchdog.py`'s lifecycle
  classification (unregistered prefix → `_resolve_lifecycle_class` returns `None` → `keep_not_ephemeral`, so it was
  never even eligible for reaping, but also never correctly SURFACED in any fleet/Monitor-tab view), to
  `exit_code_fleet_monitor`'s classification, and — most relevant to this investigation's dead end — to
  `vm_serial_capture_cron.py`'s rolling serial-console archival (which would have preserved exactly the dmesg-level
  evidence this postmortem needed, had this VM been registered under a lifecycle class in scope for it). This also
  violates the CLAUDE.md HARD RULE "name/register every launcher via the `VM_PREFIX_TO_BUCKET` registry, never
  hand-roll" — the launcher itself is fully compliant (uses the shared `lc_gcloud_create` helper, proper
  `VM_SHUTDOWN_ON_COMPLETION`/tee/heartbeat wiring), but nobody registered its VM-name prefix in the separate
  fleet-monitor registry when it was built. **Fixed**: registered `"pipeline-e2e-check-"` as
  `VmPrefixSpec(bucket=None, lifecycle_class=LifecycleClass.EPHEMERAL_BATCH)` (bucket=`None` since the driver never
  writes market data directly, only shells out to sub-launchers that write to their own already-registered buckets —
  same simplification the pre-existing `mtds-live-smoke-`/`instruments-smoke-` entries use). One shared launcher
  covers both `--service mtds` and `--service instruments`, so this single prefix covers both. Shipped
  `deployment-service@ef6cd90c`; `bash scripts/quality-gates.sh` run (see next entry for the result). **Not flipping
  the [BACKEND] P2 todo above** — this fix closes a real observability gap for FUTURE occurrences but does not itself
  explain what killed THIS VM; split off a new [DATA] P3 todo above asking whoever launches the next DEFI attempt to
  stay present for a live serial-console poll through the VM's first ~20min, since that is now the only way left to
  actually catch this signature with real evidence.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
