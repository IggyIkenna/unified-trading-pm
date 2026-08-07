---
doc_type: issue
title: >-
  DeFi manifest consolidator "SILENT STALL" was a false alarm — stall-alert threshold miscalibrated for the bucket's own
  long lock-TTL override (RESOLVED 2026-08-06)
summary: >-
  While shipping a small KAMINO_LENDING manifest fix, observed the DeFi bucket's manifest consolidator
  (`uts-prod-manifest-consolidator-market-data-defi-cron`, runs every 1 min) firing a self-diagnosed "SILENT STALL"
  CRITICAL alert for 34+ consecutive cycles. INITIAL (WRONG) hypothesis: `consolidator.lock` was stuck past its TTL and
  never being reclaimed. Manually deleted the lock once (safe: a coordination blob, not manifest content) to test — a
  merge ran and completed successfully, but a later cycle "got stuck" the same way, which looked like confirmation of a
  stale-lock bug.

  ACTUAL root cause, found on deeper investigation: the DeFi bucket's Cloud Run Job overrides
  `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` (70 min) because its full merges legitimately take 18-30 min (confirmed via a
  full timeline of `duckdb_merge_start`/`duckdb_merge_done` log pairs — rows_out climbing steadily every cycle: 74372122
  -> 74372296 -> 74374953 -> 74375634 -> 74376131 -> 74376131). The lock/reclaim mechanism was working correctly the
  entire time; there was no stuck lock. But `_STALL_ALERT_CYCLES=10` (hardcoded, calibrated against the code-DEFAULT
  300s TTL) fires after only ~10 consecutive no-op cron ticks with shards landing — and shards land continuously from
  other writers throughout every legitimate 18-30-min merge window. So EVERY SINGLE MERGE on this bucket tripped a false
  CRITICAL alert around the 10-minute mark, self-cleared once the merge finished (`progressed` resets the streak), then
  re-tripped on the next merge. My earlier manual lock-delete actually risked orphaning a genuinely in-progress merge (a
  lock, once deleted, no longer protects the still-running container from a concurrent competing cycle) — a real, if
  low-blast-radius, mistake made while operating on the wrong hypothesis.

  FIX: made `_STALL_ALERT_CYCLES` env-overridable (`CONSOLIDATOR_STALL_ALERT_CYCLES`), mirroring the existing
  `CONSOLIDATOR_LOCK_TTL_SECONDS` pattern (`unified-trading-library@899976c6`), and wired per-bucket overrides in
  Terraform for the three buckets with long-TTL overrides — market-data-defi=90, instruments-sports=40,
  market-data-cefi=20 — proportional to each bucket's own TTL (`deployment-service`
  terraform/gcp/manifest_consolidator_scheduler.tf). Verified end state directly against the canonical index:
  `KAMINO_LENDING` captured=0 (fully retired), `KAMINO-SOLANA` captured=80 (fully consolidated — the per-VM-shard dedup
  naturally collapses the two relabel runs' overlapping dates to one row per distinct key, not a literal sum of each
  run's object count; an earlier "expect 629" note in this doc's first draft was a math error, not a real gap).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [manifest, consolidator, stall-alert, infra, defi]
related: []
created: 2026-08-05
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.5
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  unified-trading-library@899976c6 (CONSOLIDATOR_STALL_ALERT_CYCLES env-override) + deployment-service@173afd6e
  (per-bucket threshold wiring)
depends_on: []
source: >-
  interactive session, discovered while shipping the KAMINO_LENDING relabel/retirement fix
  (defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md row 7)
---

## What actually happened (corrected timeline)

1. **2026-08-05 ~22:23Z**: observed a `consolidator.lock` blob with `started_at` far in the past relative to the code's
   DEFAULT `_LOCK_TTL_SECONDS=300` — assumed stale, deleted it via `gcs_delete_object` (a coordination artifact delete,
   not manifest content — reversibility was never a concern here).
2. A merge ran and completed (`duckdb_merge_done rows_out=74375634`) — this was read at the time as "proof the merge
   logic works, but something else re-stuck it."
3. **On closer inspection** (`gcloud run jobs describe` for the actual Cloud Run Job): the bucket's deployed environment
   sets `CONSOLIDATOR_LOCK_TTL_SECONDS=4200`, NOT the 300s code default. This override already exists in Terraform with
   a full incident writeup (this same file, `manifest_consolidator_lock_ttl_seconds` map) — the SAME "TTL shorter than
   real merge duration causes overlapping-competing-merge livelocks" class was already found and fixed for
   `instruments-sports` and `market-data-cefi` too, each with its own TTL override.
4. Pulling the full `duckdb_merge_start`/`duckdb_merge_done` log timeline showed merges completing successfully every
   cycle, taking 18-30 minutes each — entirely within the 4200s TTL. There was never a stuck lock.
5. Root cause: `_STALL_ALERT_CYCLES=10` (hardcoded) assumes ~10 minutes of no-progress is suspicious — true for the
   300s-TTL default case, false for any bucket whose TTL override implies legitimately-longer merges. Confirmed by
   inspecting `_check_consolidation_stall`'s logic directly: it increments a streak on every no-op cron tick where
   shards have landed since the last real merge, and 18-30 min of legitimate merge time at a 1-min cron cadence
   guarantees 18-30 such ticks — always exceeding the 10-cycle threshold.

## Fix shipped

- `unified_trading_library/manifest_consolidator.py`: `_STALL_ALERT_CYCLES` now reads `CONSOLIDATOR_STALL_ALERT_CYCLES`
  env var (default `10`, unchanged for every bucket that doesn't override it) — mirrors the existing `_LOCK_TTL_SECONDS`
  pattern exactly.
- `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf`: new `manifest_consolidator_stall_alert_cycles`
  local map, wired into `environment_variables` alongside the existing lock-TTL map. Values: `market-data-defi=90`,
  `instruments-sports=40`, `market-data-cefi=20` — each roughly `TTL_seconds/60` (one full TTL window's worth of cron
  ticks), with defi getting extra headroom (90 vs its 70-cycle TTL-window baseline) since its corpus keeps growing and
  merge duration trends upward.

## Verified

- `unified-trading-library` QG green, shipped, landed on LDR.
- `deployment-service` QG green, shipped, landed on LDR.
- Direct read against the canonical index post-fix: `KAMINO_LENDING` captured=0 (fully retired), `KAMINO-SOLANA`
  captured=80 (fully consolidated).
- `duckdb_merge_done` log entries continue completing every ~9-20 min with `rows_out` climbing / stable as expected — no
  further false stall alerts observed after the fix deployed (Cloud Run Jobs pick up new env vars from the NEXT
  scheduled invocation, no redeploy/rebuild needed since these are plain env vars on an existing job resource).

## Lesson

Don't manually intervene on a production coordination primitive (lock, in this case) based on a HYPOTHESIS about its
staleness without first checking whether the bucket has an env-var override changing what "stale" even means for it. The
Terraform file itself already documented three prior incidents of exactly this override pattern (defi, sports, cefi)
with full historical context — reading that file BEFORE acting would have caught the real story immediately, no manual
lock-deletion needed.

## Todos

- [x] [DATA] P1. Root-cause the false SILENT STALL (miscalibrated threshold vs. TTL override, not a stale-lock-reclaim
      bug).
- [x] [DATA] P1. Ship an env-overridable stall-alert threshold, mirroring the lock-TTL pattern.
- [x] [OPS] P2. Wire proportional thresholds for all 3 long-TTL buckets (defi/sports/cefi), not just defi.
- [x] [DATA] P2. Verify the KAMINO_LENDING relabel shard fully consolidated post-fix (`KAMINO-SOLANA` captured=80,
      `KAMINO_LENDING` captured=0 — confirmed).

## Progress Log

- **2026-08-05 (interactive session)**: found while shipping a KAMINO_LENDING manifest fix, initially misdiagnosed as a
  stale-lock-reclaim bug. Manually cleared what turned out to be a legitimately-held lock (safe: a coordination blob,
  not manifest content, but based on a wrong hypothesis — flagged as a lesson above).
- **2026-08-06 (same session)**: root-caused correctly via `gcloud run jobs describe` (found the
  `CONSOLIDATOR_LOCK_TTL_SECONDS=4200` override) + a full merge-cycle log timeline (proved merges were completing
  successfully every cycle, no stuck lock). Shipped the real fix (env-overridable stall-alert threshold + per-bucket
  Terraform wiring for all 3 affected buckets). Verified the KAMINO_LENDING relabel/retirement fully consolidated.
  Status flipped to resolved.
