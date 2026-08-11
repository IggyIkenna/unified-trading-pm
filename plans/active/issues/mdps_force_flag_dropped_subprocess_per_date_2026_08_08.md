---
doc_type: issue
title: MDPS --force silently dropped when spawning per-date subprocesses — fixed
summary: >-
  market-data-processing-service's default subprocess-per-date execution model built each child date-subprocess's argv
  from only --operation/--mode/--start-date/--end-date, never forwarding the parent's --force flag. Every multi-day
  `process --force` backfill therefore ran every child date with force=False, silently skipping already-materialized
  (stale) bundles instead of regenerating them, while still exiting 0 and logging as if it had force-reprocessed
  everything. Fixed in market-data-processing-service@e9f9819.
status: open
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [mdps, force-flag, subprocess-per-date, backfill, data-correctness, cross-cutting]
related:
  [
    /plans/active/issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md,
    /plans/active/cefi_satellite_ao_dispatch_batch10_2026_08_08.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
author: slot-26 (data_engineering)
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  cefi_satellite_ao_dispatch_batch10_2026_08_08.md todo 3 (Track-7 VM terminal-state check + re-audit)
context_scope:
  [
    market-data-processing-service/market_data_processing_service/cli/handlers/process_handler.py,
    market-data-processing-service/market_data_processing_service/cli/main.py,
    /plans/active/issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04.md,
  ]
---

# MDPS --force silently dropped when spawning per-date subprocesses

## What I found

While checking the terminal state of `mdps-backfill-cefi-20260807-130321` (relaunched for CeFi Track-7 candle bundle
regeneration), its `run.log` showed the parent MDPS invocation carried `--force` (`legacy argv: [..., '--force', ...]`),
but the per-date CHILD subprocess it spawned for `2023-06-01` did NOT:

```
Parent: ['process', '--start-date', '2023-06-01', '--end-date', '2026-01-01', '--CEFI', '--force', ...]
Child:  ['process', '--start-date', '2023-06-01', '--end-date', '2023-06-01', '--CEFI', ..., '--no-subprocess-per-date']
Log:    Date: 2023-06-01, Timeframes: [...], Force: False
```

Root cause: `market_data_processing_service/cli/handlers/process_handler.py::_run_date_as_subprocess` (the function
actually used by the default `subprocess-per-date` execution model — NOT the similarly-named but unused
`_build_single_date_argv`, which correctly forwards `--force` but is only ever called from tests) built the child `cmd`
list from `--operation`/`--mode`/`--start-date`/ `--end-date` only. `args.force` was never appended, and there is no
`MDPS_FORCE` env-bridge either, so the parent's force intent never reached the child at all.

**Impact confirmed live**: two consecutive CeFi Track-7 `--force` relaunches (`mdps-backfill-cefi-20260804-190444`,
`mdps-backfill-cefi-20260807-130321`) reached `2023-06-01`'s BYBIT `futures_chain` bundle and did NOT rewrite it — GCS
object `Update time` still reads `2026-08-03T01:59:07Z`, predating both relaunches, despite the run.log showing the day
was actively processed. The bundle remains in its pre-fix PARTIAL state (1 symbol, `BTC-29DEC23` only — the original
race-collision defect this whole Track-7 effort exists to fix). This means every multi-day `--force` backfill on this
service silently no-ops on already-captured cells, not just this one.

A THIRD VM, `mdps-backfill-cefi-20260808-095136` (started 2026-08-08T08:57:08Z, same
2023-06-01→2026-01-01/BYBIT+DERIBIT/--force scope, confirmed alive and progressing — currently on `2023-07-14` as of
this writing, `Force: False` confirmed in its own run.log), is running right now — almost certainly the launcher's
SPOT-preemption auto-relaunch (`RelaunchPreemptedVm`) re-invoking with the SAME persisted `LAUNCH_PARAMS.json`, which
predates this fix and inherits the same oversized full-date-range scope. It has not yet reached any of the 6 remaining
Track-7 target days (`2023-08-02`, `2023-11-02`, `2024-02-01`, `2024-02-02`, `2024-07-01` — plus the already-passed
`2023-06-01`), and at the observed ~12 min/day processing rate would need ~950 processed days / ~8 months of continuous
uptime to reach `2026-01-01`, virtually guaranteeing further preemptions before completion. It was NOT terminated by
this todo (STEP 0.55 VM-delete guardrail: it is actively progressing, not stale, so unilateral deletion is out of scope
for this agent) — flagging for operator visibility given the compute waste.

## Why it matters

This is not scoped to Track-7. ANY service consumer relying on
`market_data_processing_service process --force --start-date X --end-date Y` (Y > X, the default subprocess-per-date
path) to densify/regenerate already-captured candle cells has been silently getting a no-op since subprocess-per-date
became the default (`mdps_polars_engine_cost_sharpening_2026_06_28`). The run still exits 0 and logs normally, so
nothing downstream would flag it — a genuine "looks like it worked, definitely didn't" data-correctness trap.

## Recommended decision

Already fixed: `market-data-processing-service@e9f9819`
(`fix(process_handler): forward --force to per-date subprocess spawns`) appends `--force` to the child `cmd` list when
`args.force` is set; unit tests added asserting the child `cmd` does/doesn't carry `--force` per the parent flag. Green
QG, landed + verified ancestor of `origin/live-defi-rollout`.

Remaining: any NEW VM launch (this fix lands via a fresh tarball pull) will now correctly force- reprocess. The
already-running `mdps-backfill-cefi-20260808-095136` does not have this fix baked in (started before it landed) — its
BYBIT cells will remain unfixed even if it reaches them. Operator/next-agent should let it run to its natural terminal
state (preemption or completion, `--force` backfills are idempotent so no data-loss risk either way) and relaunch fresh,
correctly scoped per-day (see the Track-7 doc's Relaunch todo), once fully done.

## Todos

- [x] ✅ [DATA] P1. **Fix `_run_date_as_subprocess` to forward `--force` into the per-date child subprocess argv** in
      `market-data-processing-service/market_data_processing_service/cli/handlers/process_handler.py`. Add unit test
      coverage asserting the child `cmd` list carries `--force` iff the parent `args.force` is set. **Done**:
      `market-data-processing-service@e9f9819`, quality-gates.sh green, quickmerge-landed + verified ancestor of
      `origin/live-defi-rollout`.
- [ ] [DATA] P2. Once `mdps-backfill-cefi-20260808-095136` reaches a terminal state (completed or preempted), relaunch
      the CeFi Track-7 candle regen SCOPED PER-DAY (single-day `--start-date`==`--end-date` launches for each of the 6
      target days, NOT the full 2023-06-01→2026-01-01 range — the launcher has no day-list flag, and the full-range
      scope is what caused 2 prior preemptions plus ~8 months of unnecessary compute at the observed ~12 min/day rate)
      now that the force-forwarding fix is live. (repo: deployment-service, market-data-processing-service)

## Progress Log

- **slot-26 data_engineering 2026-08-08**: Root-caused + fixed while checking terminal state of
  `mdps-backfill-cefi-20260807-130321` for `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` todo 3. Filed as a
  separate doc since the defect is cross-cutting (any multi-day `--force` MDPS backfill), not Track-7-specific.
- **data_engineering (slot 11) 2026-08-08T22:14Z**: Checked terminal-state gate for todo 2 (P2 relaunch). VM
  `mdps-backfill-cefi-20260808-095136` (`asia-northeast1-c`) is still `RUNNING` — confirmed via
  `gcloud compute instances describe` (status=RUNNING) +
  `gs://deployment-scripts-central-element-323112/vm-logs/mdps-backfill-cefi-20260808-095136/run.log` showing active
  POLARS aggregation output at `2026-08-08T22:12:28Z` (~2 min before this check — not stalled, genuinely progressing, no
  zombie-watchdog intervention needed per STEP 0.55). Todo 2 remains gated: not actionable until this VM reaches a
  terminal state (completed or preempted), which per this doc's own estimate (~12 min/day, ~950 remaining days) is far
  more likely to be a SPOT preemption than natural completion, on an unpredictable timeline. Not busy-waiting on this in
  a live session — releasing the task back to the queue rather than holding a session open for an indeterminate
  (possibly month-scale) external condition; a future dispatch cycle should re-check terminal state the same way.
- **data_engineering (slot 15) 2026-08-08T22:26Z**: Re-checked terminal-state gate for todo 2. VM
  `mdps-backfill-cefi-20260808-095136` is still `RUNNING` (`gcloud compute instances describe` status=RUNNING) — run.log
  shows active POLARS aggregation at `2026-08-08T22:26:32Z` (this check's own timestamp), now on `Date: 2023-08-09` (up
  from `2023-07-14` at the prior check ~12 min earlier — consistent with the doc's ~12 min/day rate, so genuinely
  progressing, not stalled). Still ~880 days from `2026-01-01`. Todo 2 remains gated, same as the prior check —
  releasing back to the queue rather than busy-waiting on an external condition with a month-scale timeline.
- **cicd/data_engineering (slot 24) 2026-08-08T22:40Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING), run.log
  progressing (`Date: 2023-08-11` at `2026-08-08T22:39:40Z`, up from `2023-08-09` at the prior check — consistent rate,
  not stalled). Todo 2 remains gated. While checking, found a SEPARATE, unrelated live data-correctness bug in this same
  run.log: DERIBIT `options_chain` candle derivation raises `SchemaContractNotFoundError` for the `15s` tier
  (`instrument_type='OPTION' data_type='options_chain_15s'`), causing that date's per-date subprocess to exit `rc=1`
  (masked at the top level by shard-level isolation). Filed separately as
  `/plans/archive/issues/mdps_cefi_deribit_options_chain_15s_missing_schema_contract_2026_08_08.md` (P1, UAC
  CONTRACT_REGISTRY gap, resolved + archived 2026-08-09) since it's cross-cutting and unrelated to the
  `--force`-forwarding fix this doc tracks. Releasing todo 2 back to the queue per the same precedent — not busy-waiting
  on a month-scale external condition.
- **data_engineering (slot 9) 2026-08-10T13:26Z**: Re-checked terminal-state gate for todo 2. VM
  `mdps-backfill-cefi-20260808-095136` is still `RUNNING` (`gcloud compute instances describe` status=RUNNING) — run.log
  shows active POLARS aggregation at `2026-08-10T13:25:06Z` (this check's own timestamp, ~2 days after the last check at
  2026-08-08T22:40Z — it has NOT preempted in that window, still progressing through the full 2023-06-01→2026-01-01
  range). Todo 2 remains gated: not actionable until the VM reaches a terminal state (completed or preempted), which per
  this doc's own estimate is still month-scale (or an unpredictable SPOT preemption). Releasing back to the queue with
  `reason_code: GATED` per worker.md § 4c — not busy-waiting on an indeterminate external condition.
- **data_engineering (slot 18) 2026-08-10T17:20Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING), run.log
  actively progressing at `2026-08-10T17:19:09Z` (this check's own timestamp, ~4h after slot 9's check). Now at
  `Date: 2024-01-28` (up from `2023-08-11` at slot 24's check ~42h ago — ~170 days processed, ~15 min/day, consistent
  with the documented ~12 min/day rate). ~704 days remaining to `2026-01-01` ≈ ~141 hours of continuous uptime. Todo 2
  remains gated — releasing back to the queue with `reason_code: GATED` per worker.md § 4c; not busy-waiting on a
  month-scale external condition.
- **data_engineering (slot 23) 2026-08-10T20:40Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING), run.log
  actively progressing at `2026-08-10T20:38:38Z` (this check's own timestamp, ~3.3h after slot 18's check). Now at
  `Date: 2024-02-10` (up from `2024-01-28` at slot 18's check — ~13 days processed in ~3.3h ≈ ~15 min/day, consistent
  with the documented ~12-15 min/day rate; `Force: False` confirmed in run.log, as expected for this pre-fix VM). ~690
  days remaining to `2026-01-01` ≈ ~140 hours of continuous uptime. Todo 2 remains gated — releasing back to the queue
  with `reason_code: GATED` per worker.md § 4c; not busy-waiting on a month-scale external condition.
- **data_engineering (slot 24) 2026-08-11T00:27Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING, zone
  `asia-northeast1-c`). All 3 liveness signals confirm alive, not stalled: run.log (`SIZE=235380054`) actively written
  through `2026-08-11T00:24:40Z` (this check's own timestamp — POLARS AGGREGATED lines through 00:24:37Z), heartbeat
  blob last_modified `2026-08-11T00:25:50Z`, and now on `Date: 2024-02-24` (up from `2024-02-10` at slot 23's check
  ~3.8h earlier — ~14 days processed in ~3.8h ≈ ~16 min/day, consistent with the documented ~12-15 min/day rate;
  `Force: False` confirmed, as expected for this pre-fix VM). ~676 days remaining to `2026-01-01` ≈ ~170 hours of
  continuous uptime. Todo 2 remains gated — releasing back to the queue with `reason_code: GATED` per worker.md § 4c;
  not busy-waiting on a week-scale external condition.
- **data_engineering (slot 7) 2026-08-11T04:04Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING, zone
  `asia-northeast1-c`). Liveness signals confirm alive, not stalled: run.log (`SIZE=245559611`) last_modified
  `2026-08-11T03:59:30Z`, POLARS AGGREGATED lines through `2026-08-11T04:01:29Z` (this check's own timestamp), and now
  on `Date: 2024-03-08` (up from `2024-02-24` at slot 24's check ~3.5h earlier — ~13 days processed in ~3.5h ≈ ~16
  min/day, consistent with the documented ~12-15 min/day rate; `Force: False` confirmed, as expected for this pre-fix
  VM). ~663 days remaining to `2026-01-01` ≈ ~175 hours of continuous uptime. Todo 2 remains gated — releasing back to
  the queue with `reason_code: GATED` per worker.md § 4c; not busy-waiting on a week-scale external condition.
- **data_engineering (slot 20) 2026-08-11T05:22Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING, zone
  `asia-northeast1-c`, created 2026-08-08T08:57Z). Liveness signals confirm alive, not stalled: run.log
  (`SIZE=249935400`, ~250MB) last_modified `2026-08-11T05:21:24Z` (this check's own timestamp), POLARS AGGREGATED lines
  through `2026-08-11T05:21:21Z` — seconds before this check, so actively progressing, not stale. Terminal state NOT
  reached — todo 2 remains gated on it. Releasing back to the queue with `reason_code: GATED` per worker.md § 4c; not
  busy-waiting on a week-scale external condition.
- **data_engineering (slot 20) 2026-08-11T05:42Z**: Re-checked terminal-state gate for todo 2, same result — VM
  `mdps-backfill-cefi-20260808-095136` still `RUNNING` (`gcloud compute instances describe` status=RUNNING, zone
  `asia-northeast1-c`, created 2026-08-08T08:57Z). Liveness signals confirm alive, not stalled: run.log
  (`SIZE=250890352`, ~250MB) actively written with POLARS AGGREGATED lines through `2026-08-11T05:41:50Z` (this check at
  05:42:38Z — ~1 min earlier, so actively progressing, not stale); heartbeat blob content timestamp `1786426942`
  (~2026-08-11T05:42:22Z) confirms the sidecar is alive. Terminal state NOT reached — todo 2 remains gated on it.
  Releasing back to the queue with `reason_code: GATED` per worker.md § 4c; not busy-waiting on a week-scale external
  condition.
