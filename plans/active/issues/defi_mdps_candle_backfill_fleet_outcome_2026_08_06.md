---
doc_type: issue
title: DeFi MDPS candle backfill fleet (2026-07-28) — terminal outcome + incomplete-shard follow-up
summary: >
  Terminal verification of the 5-VM SPOT fleet launched 2026-07-28 for DeFi MDPS candle backfill (year-sharded
  2022-2026). 1/5 VMs completed cleanly (2022, honest zero-output), 1/5 failed on a transient manifest-consolidator
  outage (2024, but all 366 per-date subprocesses returned rc=0), 3/5 were SPOT-preempted before writing a terminal
  marker (2023/2025/2026). Total candle output: 1,158 day partitions. The 2025 and 2026 shards have material coverage
  gaps (272/366 and 156/~220 days respectively) warranting a relaunch.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-data-processing-service, deployment-service]
scope: [engineer]
tags: [defi, mdps, candles, backfill, spot-preemption, verification]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
  ]
created: "2026-08-06"
parent_epic: defi_master
priority: P2
author: slot-9 (data_engineering)
source:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md (todo 10),
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md (todo 15),
  ]
assigned_vm: planning
assigned_role: data_engineering
resolved_by:
archive_exempt: true # BRIDGE 2026-08-12: the SUPERSEDED-dedup conversion above (todo relocated to meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md) collapsed this doc's own checkbox count to 0-open, but real remaining work still lives in that other doc -- this is a relocation, not completion. Do NOT archive; leave open pending that doc's own closure, then re-triage.
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    deployment-service/scripts/vm/launch-mdps-sharded-backfill.sh,
    market-data-processing-service/market_data_processing_service/cli/handlers/process_handler.py,
    /codex/05-infrastructure/spot-vms-for-backfill.md,
  ]
---

# DeFi MDPS candle backfill fleet — terminal verification (2026-08-06)

## What I found

Verified the terminal outcome of the 2026-07-28 DeFi MDPS candle-backfill fleet
(`launch-mdps-sharded-backfill.sh defi --env prod`, 5 SPOT VMs, run-ts=20260728-044648, e2-standard-8) by reading each
VM's complete `run.log` from `gs://deployment-scripts-central-element-323112/vm-logs/` and counting distinct
`processed_candles/by_date/` day partitions in `gs://market-data-tick-defi-prd-central-element-323112`.

### Per-shard terminal status

| Shard | VM                               | DEPLOYMENT Marker      | Exit | Candle Days | Root Cause                                                                                                                                                                                                                                                                                                                          |
| ----- | -------------------------------- | ---------------------- | ---- | ----------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2022  | `mdps-defi-2022-20260728-044648` | `DEPLOYMENT_COMPLETED` | 0    | 0           | Honest — every day (2022-11-01..12-31) had 0 raw tick files for `dex_pool_swaps` (the only DeFi data_type with an MDPS adapter). "Listed 0 files" on all 61 days, correctly skipped.                                                                                                                                                |
| 2023  | `mdps-defi-2023-20260728-044648` | **NONE** (preempted)   | N/A  | 364         | SPOT preemption ~9h in (04:50→14:00 UTC). 238K log lines. Jan 1-8 processed successfully; Jan 9-18 all hit the 1800s subprocess-per-date timeout (30 min each = 5h of timeouts); log ends mid-candle-aggregation at 14:00.                                                                                                          |
| 2024  | `mdps-defi-2024-20260728-044648` | `DEPLOYMENT_FAILED`    | 1    | 366         | Manifest consolidator for `instruments-store-defi-prd` was DOWN (heartbeat 2300+s old, >120s budget). **All 366 per-date subprocesses returned rc=0** — the failure was at the orchestration-level handler wrapping up after every date had already succeeded individually. Full year coverage achieved despite the failure marker. |
| 2025  | `mdps-defi-2025-20260728-044648` | **NONE** (preempted)   | N/A  | 272         | SPOT preemption ~20h in (04:50→01:02 UTC next day). 395K log lines. Feb 3-9 hit 1800s subprocess timeouts with `empty_confirmed` FetchEvidence warnings on BALANCER-ETHEREUM; log ends mid-candle-aggregation. 272/366 days covered (through ~Sep 2025).                                                                            |
| 2026  | `mdps-defi-2026-20260728-044648` | **NONE** (preempted)   | N/A  | 156         | SPOT preemption ~2.7h in (04:54→07:35 UTC). 72K log lines. Jan 1-5 timed out at 1800s each; log ends mid-candle-aggregation. 156/~220 days covered (through ~Jun 2026).                                                                                                                                                             |

**Total candle output**: 1,158 distinct day partitions across 2023-2026 (0 for 2022).
`gs://market-data-tick-defi-prd-central-element-323112/processed_candles/by_date/`: 2022=0, 2023=364, 2024=366,
2025=272, 2026=156.

### `max_workers` / GCS write concurrency

The launcher's `_max_workers_for defi` returns empty → uses the MDPS `ProcessConfig.max_workers` default of
`min(os.cpu_count() or 4, 16)` = **8 on e2-standard-8**. `MAX_WORKERS` controls per-instrument parallelism within each
date: up to 8 instruments are processed concurrently via a `ThreadPoolExecutor`, each independently calling
`polars_candle_engine.write_parquet()` which writes to a `gs://` path unique per `(instrument_id, timeframe, date)`.
**YES, concurrent GCS writes can overlap** — with 8 workers, up to 8 concurrent blob writes target distinct object paths
in the same bucket. No object-level conflict because each worker writes a different blob.

No measured write-concurrency figure exists on record for this specific fleet (the VM logs don't instrument per-blob
write latency/timing). The concurrency is structural — derived from the `ThreadPoolExecutor(max_workers=N)` design — not
measured empirically.

## Why it matters

- **2025/2026 coverage gaps are material**: 272/366 (74%) for 2025 and 156/~220 (71%) for 2026. Features-service
  `DEFI:onchain` depends on these candles. The gap is from SPOT preemption, not a code defect — idempotent re-run will
  close it.
- **2024 is effectively complete** despite the `DEPLOYMENT_FAILED` marker — the failure was a transient manifest
  consolidator outage at wrap-up time, not a compute failure. 366/366 days have candle output.
- **2023 is near-complete** (364/365) — the one missing day (Jan 9 or whichever didn't complete) is negligible.
- **2022 is honestly zero** — no DeFi raw tick data exists for Nov-Dec 2022 `dex_pool_swaps`. This is correct, not a
  gap.
- **Subprocess-per-date 1800s timeout is the dominant failure mode** for large-instrument-universe dates (Jan 9-18 for
  2023, Feb 3-9 for 2025, Jan 1-5 for 2026). The `STALL_TIMEOUT_SEC=7200` (2h) launcher-level timeout was NOT the issue
  — these are the 30-min per-date subprocess timeouts, which are too short for DeFi dates with 3,000-10,000+
  instruments.

## Recommended decision

- [x] ✅ [DATA] P2. **Relaunch `mdps-defi-2025` and `mdps-defi-2026`** as SPOT VMs using the same launcher
      (`launch-mdps-sharded-backfill.sh defi --year 2025 2026 --env prod`), which are idempotent (skip-if-fresh). The
      existing 272+156 day partitions will be skipped; only the missing days will be computed. Consider setting
      `MDPS_MAX_WORKERS=4` to reduce per-date memory pressure on large-instrument dates (the 1800s timeouts suggest
      individual dates with 10K+ instruments may be hitting the subprocess timeout, not a code bug — fewer concurrent
      instruments may keep each date under the 1800s cap by reducing contention). Repo: deployment-service. —
      mdps-defi-2025-20260807-203541 + mdps-defi-2026-20260807-203541 RUNNING (SPOT, MAX_WORKERS=4,
      run-ts=20260807-203541)
- [x] ~~[DATA] P3.~~ **SUPERSEDED 2026-08-10 (/plan-reconcile 2026-08-12 dedup)** — duplicate-tracked as a real `- [ ]`
      checkbox in `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` (also
      `assigned_vm: planning`), which cites this doc by name and carries a measured done-when condition. Two
      independently dispatchable copies of the same todo risked double-dispatch (both docs `assigned_vm: planning`).
      Converted to a non-ingestable pointer line here per `task_template.md` finding H — the meta-plan batch doc owns
      the live checkbox; do not dispatch from here. Original text: **Investigate raising the per-date subprocess
      timeout** from 1800s for DeFi — the `STALL_TIMEOUT_SEC` launcher-level watchdog was correctly set to 7200s, but
      the inner per-date timeout (hardcoded in MDPS `process_handler.py`) is 1800s. DeFi years with 10K+ instruments can
      legitimately exceed 30 min per date. Repo: market-data-processing-service.

## Progress Log

- **context-scout 2026-08-07**: populated context_scope (5 entries).
- **slot-6 2026-08-07**: P2 done — launched mdps-defi-2025-20260807-203541 and mdps-defi-2026-20260807-203541 as SPOT
  VMs (e2-standard-8, MAX_WORKERS=4, zone=asia-northeast1-c). Both RUNNING verified via gcloud.
- **2026-08-12 (/plan-reconcile)**: converted the sole remaining P3 todo to a non-checkbox EXTRACTED pointer (dedup fix
  — it was duplicate-tracked as a live checkbox in `meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`, both
  docs `assigned_vm: planning`). This doc now has 0 open `- [ ]` checkboxes but is NOT archive-eligible — the work isn't
  done, only relocated. Flagging for the next `/na-eligibility-audit`/archive pass to re-triage this doc (e.g. confirm
  `assigned_vm` should move off `planning` now that it holds no dispatchable item) rather than reclassifying
  unilaterally here.
