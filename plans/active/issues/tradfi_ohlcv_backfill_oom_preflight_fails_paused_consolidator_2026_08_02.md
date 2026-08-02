---
doc_type: issue
title:
  Every tradfi download-VM launch is self-deleting at boot (exit_code=78, OOM preflight) because the tradfi market-data
  manifest-consolidator cron has been PAUSED since 2026-07-29, pending mtds_available_at_cross_asset_backfill's own open
  apply-then-resume todos
summary: >-
  DP-VM-001 escalation agt-7b8e54 (RB-INFRA-RELAUNCH) for `tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-030450`
  (exit_code=78) found the failure is NOT a one-off VM glitch. `vm-setup.log` shows `setup-data-pipeline-vm.sh`'s
  shell-level OOM preflight (§5b, 2026-05-28 defense-in-depth) refusing to start the Python download workload because
  `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` is stale beyond its 86400s
  (24h) budget — confirmed live at ~42h stale (last update 2026-07-31T18:29:54Z). Root cause: the Cloud Scheduler job
  `uts-prod-manifest-consolidator-market-data-tradfi-cron` is confirmed `PAUSED` (verified live via `gcloud scheduler
  jobs describe`). This is a SANCTIONED pause from `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`
  (paused 2026-07-29, `data_engineering slot-10`) as part of that plan's snapshot→pause→apply→resume protocol for an
  `available_at` manifest backfill — whose "Apply `rebuild_tradfi_manifest.py`..." and "Resume the tradfi consolidator
  cron" todos are both still `- [ ]` open. A relaunch of the SAME shard
  (`tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-114655`) failed identically within ~3 minutes (only `LAUNCH_PARAMS.json`
  written — no `vm-setup.log` reached GCS before self-delete, consistent with the same guard firing even faster). Per
  RB-INFRA-RELAUNCH's "if it re-fails the SAME way twice, STOP relaunching, file an issue" rule, no further relaunch was
  attempted. This is fleet-wide, not shard-specific: EVERY `VM_SERVICE=market_tick_data_service VM_OPERATION=download
  VM_ASSET_GROUP=tradfi` VM launched anywhere in the fleet while the index stays this stale hits the identical guard and
  self-deletes before doing any work — the tradfi backfill fleet has effectively been down since the index crossed the
  24h budget. The sanctioned resume script
  (`market-tick-data-service/scripts/mtds_available_at_backfill_resume_tradfi_2026_07_30.py`) explicitly refuses to be
  run before that plan's apply step: "Do NOT run this before that apply step — resuming early defeats the
  pause/apply/resume sequence this plan's HARD constraint section requires." Filed rather than overridden per `/blocked`
  `BLK-058d5928` (main auto-continued with the filed-issue option).
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    tradfi,
    manifest-consolidator,
    oom-preflight,
    exit-code-78,
    data-correctness,
    cron-paused,
    dp-vm-001,
    backfill-outage,
  ]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/issues/tradfi_pred_manifest_consolidator_cron_stuck_paused_2026_07_29.md,
    /plans/active/issues/tradfi_manifest_consolidator_staleness_budget_missing_2026_07_31.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
  ]
created: 2026-08-02
parent_epic: infrastructure_master
priority: P1
source:
  [
    "DP-VM-001 escalation agt-7b8e54 (data_pipeline_failure worker, slot 3), RB-INFRA-RELAUNCH runbook",
    "vm-setup.log for tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-030450 (EXIT_STATUS=78, SETUP_EXIT_STATUS=78)",
    "gsutil stat gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet (Update time
    2026-07-31T18:29:55Z)",
    "gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-tradfi-cron --location=asia-northeast1
    (state: PAUSED)",
    "Relaunch tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-114655 (identical failure, ~3min lifecycle)",
    "/blocked BLK-058d5928",
  ]
assigned_vm: NA
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days:
estimate_calibrated_ai_days:
locked_since:
execution_scope: local-only
drift_direction: advance-code
depends_on: [mtds_available_at_cross_asset_backfill_2026_07_13]
last_updated: 2026-08-02
context_scope:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
---

# Tradfi OHLCV backfill VMs self-deleting at boot (exit_code=78) — consolidator cron paused since 2026-07-29

## What I found

Dispatched as the `data_pipeline_failure` escalation for DP-VM-001 (`repository_dispatch`, `action=relaunch_vm`) to
relaunch `tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-030450` (reported `exit_code=78`) per RB-INFRA-RELAUNCH.

1. **Registry lookup**: `DeploymentsRegistry` had NO row for this VM (neither `active/` nor `archive/` over 3 days) — it
   crashed before ever calling `register()`. Cross-checked the vm-name family (`tradfi-bf-nasdaq-ohlcv-1m-2024-d0*`) and
   confirmed this is a recurring ~3-hourly batch launch (all 5 date-range shards `d01..d05` launched together, e.g. 6
   successful waves on 2026-08-01 at 05:13/07:50/09:05/12:05/15:05/18:05) — today's ~03:04 wave's `d01` shard is the one
   flagged.
2. **Launcher resolution**:
   `launcher_registry.LAUNCHER_FOR_VM_PREFIX["tradfi-bf-nasdaq-ohlcv-1m-"] = "launch-tradfi-bf-nasdaq-ohlcv-1m.sh"`.
   Reconstructed the exact `d01`/2024 date-range slice (`2024-01-01..2024-03-14`, deterministic via
   `ohlcv_split_date_slices`) + the UAC ticker universe (622 tickers) and called `ohlcv_create_vm` directly for JUST
   that one shard (not the sibling `d02-d05`, not flagged by this alert).
3. **Original VM's root cause**
   (`gs://deployment-scripts-central-element-323112/vm-logs/tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-030450/vm-setup.log`):
   ```
   OOM preflight FAIL: gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet is
   117438s stale (budget 86400s) — exiting 78 to skip Python startup; EXIT trap will self-delete VM.
     Diagnosis: manifest-consolidator for asset_group=tradfi is degraded. Reader would fall back to merging per-VM
     shards → OOM at startup. Fix consolidator + relaunch.
   ```
   `EXIT_STATUS`/`SETUP_EXIT_STATUS` both `78`. This is `setup-data-pipeline-vm.sh` §5b's shell-level OOM preflight
   (2026-05-28 defense-in-depth against a stale-index → per-VM-shard-merge OOM at startup), NOT the Python-level
   `assert_consolidator_healthy()`/`ManifestConsolidatorStaleError` guard the two `related:` docs above already fixed
   (that one reads via `AG_STALENESS_BUDGET_SEC`, a separate mechanism now correctly overridden to 7200s for tradfi;
   THIS guard is a fixed 86400s default checked directly via `gsutil ls -L` against the market-data bucket, before
   Python even starts).
4. **Relaunched the `d01` shard fresh** (`tradfi-bf-nasdaq-ohlcv-1m-2024-d01-20260802-114655`, dry-run verified first,
   `--provisioning-model=SPOT`). It launched RUNNING, then vanished (404 on `gcloud compute instances describe`) within
   ~3 minutes — the SAME failure class (only `LAUNCH_PARAMS.json` reached GCS, no `vm-setup.log`/`EXIT_STATUS`,
   consistent with hitting the identical preflight guard even before the log-tee wrapper was wired up).
5. **Confirmed the systemic cause**: `gsutil stat` on the market-data index shows `Update time: 2026-07-31T18:29:55 GMT`
   (`consolidator_run_at: 2026-07-31T18:29:54`) — ~42h stale as of this writing, vs the 24h budget.
   `gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-tradfi-cron --location=asia-northeast1`
   returns `state: PAUSED` (schedule `*/1 * * * *` — should run every minute). Cross-referencing
   `/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`: this exact cron was deliberately paused
   2026-07-29 (`data_engineering slot-10`) as the "pause" half of that plan's snapshot→pause→apply→resume protocol for
   an `available_at` manifest backfill. **Both of that plan's remaining todos in the sequence are still open**: "Apply
   `rebuild_tradfi_manifest.py` (full date range)... force-consolidate..." and "Resume the tradfi consolidator cron"
   (retrofit note: resume via `scripts/mtds_available_at_backfill_resume_tradfi_2026_07_30.py`, which itself refuses
   early use: _"Do NOT run this before that apply step — resuming early defeats the pause/apply/resume sequence this
   plan's HARD constraint section requires."_).

## Why it matters

- **Fleet-wide, not shard-specific.** The OOM preflight (`setup-data-pipeline-vm.sh` §5b) fires for EVERY
  `VM_SERVICE=market_tick_data_service VM_OPERATION=download VM_ASSET_GROUP=tradfi` VM (any venue: CME/ICE/NASDAQ/
  NYSE/CBOE/CFE/FX/KRX/FRED), not just the one flagged shard — every such VM launched since the index crossed the 24h
  staleness threshold self-deletes at boot before attempting any capture. This has been true since sometime after
  2026-07-31T18:29:54Z (the index's last update) — the tradfi OHLCV backfill fleet has effectively had zero throughput
  for a growing window, silently (each VM exits fast and cleanly at rc=78, which does NOT look like an OOM/crash-loop to
  a casual glance — it takes reading `vm-setup.log` to see the real cause).
- **This is a genuine cross-plan sequencing conflict, not something I can unilaterally fix.** The consolidator pause is
  deliberate and its own governing plan's resume script explicitly refuses early use. Resuming the cron out of sequence
  could interfere with that plan's still-in-flight `available_at` backfill apply step (the exact scenario its HARD
  constraint section is written to prevent). Per RB-INFRA-RELAUNCH's own termination rule (2 same-shape failures → STOP
  relaunching, file an issue) and CLAUDE.md's "big finding... NOTIFY OPERATOR + issue doc", filing this rather than
  guessing. Filed a `/blocked` question (`BLK-058d5928`) with three options (leave-paused-and-file,
  expedite-the-apply-step, or override-and-resume-now); main auto-continued with the filed-issue path (option A).
- **No data was lost or corrupted** — every affected VM self-deleted cleanly at rc=78 before any capture attempt
  (shard-level, idempotent; nothing to roll back). The cost is throughput/latency (a growing backlog of un-attempted
  tradfi OHLCV dates), not correctness.

## Recommended decision

Option A (filed, not overridden): leave the cron paused, do not relaunch further tradfi download VMs until resolved
(they will keep failing identically and burn SPOT VM-minutes for zero capture), and treat
`/plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s two open todos ("Apply
`rebuild_tradfi_manifest.py`..." and "Resume the tradfi consolidator cron") as the fix — whoever picks that plan up next
should be aware the resume is now overdue-urgent (fleet-wide tradfi backfill outage), not just a routine cleanup step,
and should prioritize accordingly. If that plan's apply step is stalled/deprioritized for longer than is tolerable,
re-open the question of an early, deliberate resume (option C from the `/blocked` question) as an explicit operator/main
call — not a default.

## Todos

- [ ] [OPERATOR] P1. Decide whether to expedite `mtds_available_at_cross_asset_backfill_2026_07_13`'s open
      apply-then-resume todos, or authorize an early cron resume (breaking that plan's stated sequencing) to stop the
      fleet-wide tradfi OHLCV backfill outage sooner. Until resolved, do not relaunch tradfi download VMs — they will
      fail identically at rc=78.

## Progress Log

- 2026-08-02 (slot 3, `data_pipeline_failure` escalation agt-7b8e54, DP-VM-001): filed per the findings above; posted
  `/blocked` `BLK-058d5928` (auto-continued with option A); no further relaunch attempted (RB-INFRA-RELAUNCH's
  same-failure-twice stop rule).
- 2026-08-02 (slot 4, `data_pipeline_failure` escalation agt-fad570, DP-VM-001): independent corroborating hit on a
  DIFFERENT tradfi launcher family — `tradfi-bf-cme-ohlcv-1m-g01-cl-cl-2026-20260802-120343` (exit_code=78, CME OHLCV-1m
  current-year incremental shard, vs this doc's NASDAQ 2024 historical shard) — confirms the outage is genuinely
  fleet-wide across venues, not NASDAQ-specific. Live-reconfirmed both signals independently:
  `availability_index.parquet` still `Update time: 2026-07-31T18:29:55 GMT`;
  `uts-prod-manifest-consolidator-market-data-tradfi-cron` still `state: PAUSED`. This shard's own relaunch history
  (`vm-logs/tradfi-bf-cme-ohlcv-1m-g01-cl-cl-2026-*/EXIT_STATUS`) pins the outage onset precisely: 11 consecutive
  successful ~3-hourly runs 2026-07-30T21:12Z..2026-08-01T18:12Z (all `EXIT_STATUS=0`), then 5 consecutive identical
  `EXIT_STATUS=78` failures 2026-08-02T00:10Z..2026-08-02T12:03Z — the outage began between those two runs, consistent
  with the 24h staleness budget elapsing ~2026-08-01T18:29Z (24h after the consolidator's last successful run). No
  relaunch attempted (would fail identically — 5/5 confirmed since onset — and contradicts this doc's own Recommended
  decision); no cron override (consistent with the existing `BLK-058d5928` ruling). Pinged authoring slot
  `dp-fleet-monitor` with the outcome; deferring to this doc's existing `[OPERATOR]` todo for the actual fix.
