---
doc_type: issue
title: >-
  DeFi manifest consolidator stuck in a SILENT STALL — `consolidator.lock` outlives its own 300s TTL and is never
  reclaimed by subsequent cron ticks (2026-08-05)
summary: >-
  While shipping a small KAMINO_LENDING manifest fix, discovered the DeFi bucket's manifest consolidator
  (`uts-prod-manifest-consolidator-market-data-defi-cron`, runs every 1 min) had been in a self-diagnosed "SILENT STALL"
  for 34+ consecutive cycles: every tick correctly detects `_index/consolidator.lock` as present and skips, but the
  lock's own `started_at` was 2168s old against a 300s `_LOCK_TTL_SECONDS` — it should have been auto-reclaimed as stale
  by `_is_lock_fresh()` (`unified_trading_library/manifest_consolidator.py`) many cycles earlier. Manually deleting the
  stale lock blob (via `gcs_delete_object`, not a destructive data action — this is a coordination artifact, not
  manifest content) let ONE cycle through, which ran a real merge (`duckdb_merge_start` → `duckdb_merge_done`,
  `rows_out=74375634`, confirming the merge logic itself works) — but a LATER cycle (`duckdb_merge_start` at 22:26:35Z)
  got stuck the same way, leaving another stranded lock past its own TTL, observed still un-reclaimed as of 22:37Z (11+
  min old). Every individual Cloud Run Job execution in this window completed cleanly in ~7-11s (`gcloud run jobs
  executions list` shows no long-running/hung executions) — meaning the STUCK STATE lives entirely in the GCS lock blob,
  not in a hung process, so the deployed `unified_trading_library` build likely predates the stale-lock-reclaim logic
  present in the current source tree (the SAME undeployed-fix class already found this session for
  `market-tick-data-service@bd153821`, stuck behind the LDR→main CI capacity backlog).
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-trading-library, deployment-service]
scope: [engineer, admin]
tags: [manifest, consolidator, stale-lock, infra, defi]
related: []
created: 2026-08-05
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source:
  interactive session, discovered while shipping the KAMINO_LENDING relabel/retirement fix
  (defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md row 7)
---

## Impact

Per-VM shards for the DeFi bucket are landing (317 shards, 91.7M rows seen in one merge attempt) but not reliably
reaching the canonical `_index/availability_index.parquet` — any tool that writes via the per-VM-shard path (relabels,
backfills, one-off migrations) can be silently stuck waiting on a consolidator that never runs. Concretely this session:
a KAMINO_LENDING→KAMINO-SOLANA relabel (80 objects/565 rows, `relabel_kamino_lending_venue_2026_08_05.py --apply`)
landed in `_index/per_vm/local-kamino-lending-relabel-extended.parquet` at 21:11Z and, as of this doc's writing, still
has not been merged into the canonical index — the axis-value-census / honest-coverage rollup both still show only 64
captured `KAMINO-SOLANA` rows (the earlier, already-consolidated 2026-08-05-session backfill), not 629.

This is NOT specific to my change — any shard-based writer for this bucket is affected while the consolidator is
stalled.

## What's confirmed

- Lock path: `gs://market-data-tick-defi-prd-central-element-323112/_index/consolidator.lock`
- TTL: `_LOCK_TTL_SECONDS=300` (default, unified-trading-library)
- Reclaim logic exists in the CURRENT source (`_is_lock_fresh()` in `unified_trading_library/manifest_consolidator.py`)
  and is correct by inspection.
- Observed in production: a lock with `started_at` 2168s in the past was still treated as fresh by every cron tick for
  34+ consecutive cycles — contradicts the source logic.
- A manual `gcs_delete_object()` of the stale lock let one cycle through; it ran a full merge and completed
  (`duckdb_merge_done rows_out=74375634`). A SUBSEQUENT cycle then got stuck the same way (new stale lock,
  `instance=1-9ea523be`, started_at=22:25:46Z, still un-reclaimed 11+ min later as of 22:37Z).
- Separately (self-healing, not this issue's blocker): the consolidator warns "canonical... has NO
  `consolidator_content_write_at` marker (out-of-band rewrite?)" whenever a direct full-index rewrite (POOL casing fold,
  dex_pools retire, KAMINO_LENDING retire — all from this session) doesn't carry that custom metadata forward, forcing a
  full (not incremental) merge for one cycle. The consolidator re-stamps it itself; no action needed, just expensive.

## Hypothesis (not yet confirmed)

Deployed `unified_trading_library` build predates the stale-lock-reclaim fix visible in the current source tree — same
class as the already-known undeployed `bd153821` writer fix, stuck behind the LDR→main CI capacity backlog
(`fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md` and successor docs). Needs verification: check the
deployed consolidator Cloud Run Job's actual `unified_trading_library` pin/build SHA against `origin/main`'s current
`manifest_consolidator.py`.

## Todos

- [ ] [DATA] P1. Confirm whether the deployed consolidator image's `unified_trading_library` predates the
      stale-lock-reclaim fix (compare build SHA vs `origin/main`); if so, this is blocked on the SAME CI capacity
      backlog as `bd153821` — no separate fix needed, just needs the backlog to clear.
- [ ] [DATA] P1. If the deployed code is current and the bug reproduces anyway, root-cause why `_is_lock_fresh()`'s
      reclaim branch isn't firing (add a probe/test reproducing a 2168s-old lock blob against the exact deployed code
      path).
- [ ] [OPS] P2. Once root-caused, decide: does the consolidator need a self-check that runs
      `_check_stall_on_lock_skip`'s own logged remedy (`consolidate(bucket, force=True)`) automatically after N stalled
      cycles, rather than only logging CRITICAL and waiting for a human to notice?
- [ ] [DATA] P2. After the fix (or CI backlog clears), verify the KAMINO_LENDING relabel shard
      (`_index/per_vm/local-kamino-lending-relabel-extended.parquet`, 80 rows) has been merged into canonical — confirm
      `KAMINO-SOLANA` shows 629 captured rows (64 + 565), not 64.

## Progress Log

- **2026-08-05 (interactive session)**: found while shipping a KAMINO_LENDING manifest fix. Manually cleared one stale
  lock (safe: a coordination blob, not manifest content) to confirm the merge logic itself works (it does — one cycle
  completed cleanly). Did not chase further live-intervention on the SAME cron given it re-stuck immediately after;
  filing this doc instead of continuing to manually babysit a production cron loop.
