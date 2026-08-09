---
doc_type: issue
title:
  mtds-dex-swaps-backfill's 2026-08-07 relaunch replays from 2023-01-01 default instead of resuming past the
  already-captured range
summary: >-
  The checkpoint-fix relaunch of the dex_pool_swaps backfill (covering `defi_satellite_ao_dispatch_batch9_2026_08_06.md`
  todo 8) landed correctly on the correctness axis (CURVE/OPTIMISM's old pre-fix `attempted_failed` signature has frozen
  since 2026-08-07T07:00Z, confirmed via a fresh bounded manifest read 2026-08-09), but the relaunch used the launcher's
  hardcoded `START_DATE=2023-01-01` default instead of an explicit `--start` computed from the already-captured range
  (the original `mtds-dex-swaps-backfill-1`/`-2` VMs, before being consolidated into this one VM, had already completed
  2024-10-07 through 2025-12-14). As of this filing the VM's `PROGRESS.json` shows `last_completed_date=2023-07-10` —
  still ~15 months of redundant (idempotent, non-corrupting, but wasted) re-crawl before it reaches new ground.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [deployment-service, market-tick-data-service]
scope: [engineer]
tags: [defi, dex_pool_swaps, vm-launcher, efficiency, checkpoint, backfill]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    /plans/archive/2026_08/issues/defi_dex_pool_swaps_733_row_indexer_health_findings_2026_07_27.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
author: slot-32 (data_engineering)
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source: >-
  Investigated while closing `defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 8 (relaunch mtds-dex-swaps-backfill
  onto the shipped checkpoint fix). The correctness goal was already met by an independent 2026-08-07 relaunch (not this
  task); this finding documents the launch-parameter gap that relaunch left behind.
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch9_2026_08_06.md,
    deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh,
    market-tick-data-service/market_tick_data_service/cli/handlers/dex_swaps_handler.py,
  ]
---

# mtds-dex-swaps-backfill's 2026-08-07 relaunch is redundantly re-crawling already-captured dates

## What I found

`defi_satellite_ao_dispatch_batch9_2026_08_06.md` todo 8 asked to relaunch `mtds-dex-swaps-backfill-1`/`-2` onto the
shipped checkpoint fix (`market-tick-data-service@8046e25b`), using each VM's per-VM manifest shard's max `date` as an
explicit `--start` so the relaunch doesn't replay from `2023-01-01`.

Investigating this todo found the underlying correctness bug is **already fixed and live**, via an unrelated relaunch
that happened 2026-08-07T15:58:05Z (deployment `acaddf78-8696-4300-b9a3-8557f464461c`) — well before this task was
dispatched. Evidence (fresh bounded manifest read, 2026-08-09):

- CURVE/OPTIMISM `dex_pool_swaps` `attempted_failed` rows carrying the OLD pre-fix error string ("All 5 cascade schemas
  returned GraphQL errors for curve/OPTIMISM") are frozen at 22 rows, max `attempted_at` = `2026-08-07T07:00:44Z`
  (before the relaunch) — no new old-signature rows since.
- 194 rows now correctly classify as `empty_confirmed(EXPECTED_SUBGRAPH_DEINDEXED)`, max `attempted_at` =
  `2026-08-09T19:55:21Z` (~2 days of confirmed correct live classification).
- The original `-1`/`-2` VMs no longer exist (`-1` completed cleanly 2026-08-01T19:34Z covering
  `2024-10-07..2025-05-11`; `-2` ran the stale pre-fix binary until ~2026-08-07T15:22Z covering
  `2025-05-12..2025-12-14`) — both per-VM manifest shards (`_index/per_vm/mtds-dex-swaps-backfill-{1,2}.parquet`) have
  since been merged away by the consolidator, so the todo's literal "read the per-VM shard" step is moot.
- The current architecture launches ONE consolidated VM (`mtds-dex-swaps-backfill`, no `-1`/`-2` suffix) —
  `deployment-service/scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh` — which DOES support an explicit
  `--start`/`--end` flag, but the 2026-08-07 relaunch used the script's hardcoded default
  (`START_DATE="${START_DATE:-2023-01-01}"`), not a value derived from the already-captured range.
- Current `PROGRESS.json`: `{"last_completed_date":"2023-07-10","monotonic":true,"updated":"2026-08-09T20:53:35Z"}` — at
  this pace it will take roughly two more weeks of VM time to reach `2024-10-07`, the date `-1` had already reached by
  2026-08-01. Every day in `2024-10-07..2025-12-14` it re-crawls is a fully redundant (idempotent, non-corrupting)
  Tardis API call and write — wasted compute/API budget, not a correctness problem.

## Why it matters

Not a correctness issue (SPOT + idempotent shards mean no data is lost or corrupted) — but it is a real efficiency waste
(the craft's co-equal north-star per `unified-trading-pm/agents/data_engineering.md`) and directly the gap the original
todo asked to close. Left unaddressed, the VM will spend ~2 more weeks re-confirming ground it already covered before it
even starts making net-new progress.

## Recommended decision

Fix at the root next time this VM needs a relaunch (SPOT preemption, code deploy, etc.) rather than interrupting a
currently-healthy, actively-progressing run for a marginal efficiency gain today.

## Action items

- [ ] [INFRA] P3. Next time `mtds-dex-swaps-backfill` needs a relaunch (preemption, redeploy, or a deliberate efficiency
      pass), compute `--start` from the current manifest's max already-captured `date` for `dex_pool_swaps` (bounded
      read of `_index/availability_index.parquet`, filtered `data_type=dex_pool_swaps`) instead of accepting the
      launcher's `2023-01-01` default, so the run doesn't redundantly re-walk already-covered ground. Repo:
      deployment-service. Done when: the next relaunch of this VM passes an explicit `--start` derived from the manifest
      rather than the script default.

## Progress Log

- **2026-08-09 (slot-32, data_engineering)** — filed while closing `defi_satellite_ao_dispatch_batch9_2026_08_06.md`
  todo 8. Correctness goal already met by an independent 2026-08-07 relaunch; this doc tracks only the leftover
  launch-parameter inefficiency.
