---
doc_type: issue
title:
  "MDPS backfill VM mdps-backfill-cefi-20260802-140125 exited exit_code=1 (non-OOM) — final date 2026-08-01 (venue
  ASTER, trades) timed out in the per-date 1800s subprocess; 943/944 dates completed. Relaunched per RB-INFRA-RELAUNCH
  (mdps-backfill-cefi-20260811-001021)."
summary:
  "DP-VM-001 escalation agt-c06379: mdps-backfill-cefi-20260802-140125 (deployment fcc19739-ded4-4d44-9738-
  6b2237a408b9, launch scope 2024-01-01..2026-08-01, venue ASTER, data_type trades, mode full, DEPLOYMENT_ENV=prod)
  terminated exit_code=1. run.log root cause: `subprocess-per-date: date=2026-08-01 TIMED OUT after 1800s (FAILED, child
  killed)` — the final date's per-date subprocess exceeded the 1800s cap; handler returned 1. The 943 prior dates
  (2024-01-01..2026-07-31) completed, and 2026-08-01 was PARTIALLY written (2,318 processed_candles objects present
  under processed_candles/by_date/day=2026-08-01/pipeline_mode=batch_aster/...). Not OOM (host mem ~26%, mem_slope flat;
  no OOM signature). Relaunched the launcher per codex/15-runbooks/incidents/rb_infra_relaunch.md → VM
  mdps-backfill-cefi-20260811-001021 (SPOT, e2-standard-8, asia-northeast1-c, same scope). Outcome pending."
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer]
tags: [data-pipeline, vm, mdps, cefi, aster, backfill, per-date-timeout, dp-vm-001, escalation]
related:
  [
    /codex/15-runbooks/incidents/rb_infra_relaunch.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    /plans/active/issues/mdps_1h_candle_backfill_blocked_upstream_mtds_raw_tick_gap_bitget_2026_08_09.md,
    /plans/active/issues/mdps_force_flag_dropped_subprocess_per_date_2026_08_08.md,
  ]
created: 2026-08-11
last_updated: 2026-08-11
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.25
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: DP-VM-001 escalation agt-c06379 (dp-fleet-monitor → orchestrator → slot 11)
---

# MDPS backfill cefi ASTER — exit_code=1 from per-date 1800s timeout on final date 2026-08-01

## What I found

- **VM**: `mdps-backfill-cefi-20260802-140125` (launched 2026-08-02 14:01:25 UTC; ran 8 days to 2026-08-10).
- **Deployment row** (`deployments/archive/2026-08-10/fcc19739-...json`): `exit_code: 1`,
  `completed_at 2026-08-10T08:49:07Z`, `asset_group CEFI`, `end_date 2026-08-01`, host mem ~26% (no OOM signature).
- **LAUNCH_PARAMS.json**: `RESUME_ASSET_GROUP=cefi`, `RESUME_START_DATE=2024-01-01`, `RESUME_END_DATE=2026-08-01`,
  `RESUME_MODE=full`, `MDPS_DATA_TYPES=trades`, `MDPS_VENUES=ASTER`, `DEPLOYMENT_ENV=prod`, `FORCE=false`.
- **run.log tail**: the run iterated all 944 dates.
  `ERROR subprocess-per-date: date=2026-08-01 TIMED OUT after 1800s (FAILED, child killed)` →
  `Handler returned non-zero exit code: 1`. Last successful work was `2026-08-01` candles being aggregated; 943 prior
  dates completed.
- **Partial write**: `processed_candles/by_date/day=2026-08-01/` holds **2,318 objects** (under
  `pipeline_mode=batch_aster/timeframe=.../data_type=trades/instrument_type=PERPETUAL/venue=ASTER/...`) — the killed
  date subprocess wrote most of the date before the 1800s kill. The incomplete portion (remaining timeframes /
  manifest-finalisation) is what a relaunch resumes.

## Why it matters

- DP-VM-001: a VM exit `exit_code != 0` means the shard did **not** complete cleanly. The cefi ASTER trades candle
  backfill for 2026-08-01 is not yet fully captured; downstream feature/service layers expect contiguous candles.
- This is a **known, recent failure class**: the per-date 1800s subprocess cap is flagged in the launcher docstring
  (`launch-mdps-backfill-vm.sh` cites `mdps_1h_candle_backfill_blocked_upstream_mtds_raw_tick_gap_bitget_2026_08_09.md`)
  as a cap a wide venue/timeframe scope can legitimately blow.

## Classification note (dispatch vs monitor tier)

- The orchestrator dispatch text said `RELAUNCH` because `DP_VM_EXIT_NONZERO` is unconditionally in
  `deployment_service.data_pipeline_monitors.escalation._VM_LIFECYCLE_EVENTS` — the fast-spawn context is generic.
- The exit-code fleet monitor itself classified this finding **PAGE_OPERATOR** (non-OOM: `exit_code=1` is neither 137
  nor 124), and did **not** bind `relaunch_launcher` (only OOM/worker-stalled findings bind it). The DP-VM-001 registry
  row says non-OOM → page; the OOM actuator (`RelaunchBackfillVm`) would return `SKIPPED/not_oom`.
- This dispatch is therefore a runbook hand-off to a planning-VM worker, not the in-image actuator path. Action taken
  per `rb_infra_relaunch.md`: resolve launcher via registry → re-run deterministically → verify STARTED + PROGRESS →
  stop + file issue if it re-fails the same way.

## Action taken

- Resolved launcher: `launch-mdps-backfill-vm.sh` (`mdps-backfill-cefi-` → longest-prefix match in
  `launcher_registry.py`).
- Relaunch budget for `mdps-backfill-cefi-` on 2026-08-11: **0** (within the ≤2/(vm-prefix,day) bound).
- Re-ran the launcher with the captured scope:
  `bash scripts/vm/launch-mdps-backfill-vm.sh --data-types trades --venues ASTER cefi 2024-01-01 2026-08-01 full`
- **New VM**: `mdps-backfill-cefi-20260811-001021` (SPOT, e2-standard-8, asia-northeast1-c) — **STARTED / RUNNING**,
  LAUNCH_PARAMS.json + TARBALL_PINS.json persisted; all 5 code tarballs fresh at launch.
- Presence-skip makes the 943 completed dates a fast no-op; the relaunch re-attempts only 2026-08-01's residual.

## Outcome

- [x] ✅ [OPS] Relaunch `mdps-backfill-cefi-20260811-001021` verified **STARTED** (GCE RUNNING at 2026-08-11T00:11Z;
      deployment `cc8e2596-520e-4783-8be8-88d96fdc5ac3` registered with `log_uri` set, `exit_code: null`) and
      **PROGRESS** (run.log advancing within minutes: `POLARS AGGREGATED: 1 24h candles` at 2026-08-11T00:13:37Z). Per
      RB-INFRA-RELAUNCH the launch is not fire-and-forget: STARTED@T+60s + PROGRESS@T+10min both confirmed.
- [ ] [OPS] Terminal-state confirmation of `mdps-backfill-cefi-20260811-001021` (EXIT_STATUS 0 + `day=2026-08-01` ASTER
      trades candles complete) is covered by the exit-code fleet monitor's own DP-VM-001 sweep — if the relaunch
      re-exits non-zero (esp. the same per-date 1800s timeout on 2026-08-01), it re-alerts and the shard is wedged: STOP
      relaunching and fix the root cause (raise/split the per-date timeout for recent large ASTER dates or narrow the
      timeframe scope). Repo: market-data-processing-service.
