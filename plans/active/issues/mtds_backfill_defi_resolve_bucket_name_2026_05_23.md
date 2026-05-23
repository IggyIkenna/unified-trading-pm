---
title: mtds-backfill-defi-20260523 VM broken — resolve_bucket_name() unexpected 'env' kwarg on every chunk
created: 2026-05-23
author: slot-2-ikenna
source:
  - vm-logs/mtds-backfill-defi-20260523/run.log
  - market-tick-data-service/market_tick_data_service/cli/handlers/tick_data_handler.py
locked_by: live-defi-rollout
---

## What I found

`mtds-backfill-defi-20260523` (RUNNING, asia-northeast1-c, 2024-01-01→2026-05-23, tarball sha 498148da) is looping on
every chunk with a preflight error at startup. Observed at 20:18:54 UTC (chunk 1/125) and again at 20:30:51 UTC (chunk
2/125 attempt).

```
ERROR Handler TickDataHandler failed during setup/preflight:
  resolve_bucket_name() got an unexpected keyword argument 'env'
Traceback:
  File ".../tick_data_handler.py", line 94, in preflight
      self._bucket = resolve_bucket_name(cloud="gcp", kind="tick-data",
                                         asset_group=primary_ag, env="live")
TypeError: resolve_bucket_name() got an unexpected keyword argument 'env'
```

**Root cause**: The VM's `tick_data_handler.py` still calls `resolve_bucket_name(env="live")` but the UTL version in the
tarball has removed the `env` kwarg. The current worktree's `tick_data_handler.py` line 94 calls
`get_tick_data_bucket()` instead. The tarball was built before the API-drift fix was included.

**Impact**: The VM processes 125 chunks spanning 2024-01-01→2026-05-23 but FAILS on every chunk in preflight. Zero
candles are produced. No manifest rows written. The VM loops for the full planned duration burning GCP resources.

**Unrelated to UAC@8e1e7e58** (POOL/pool case fix) — different layer of the stack.

## Recommended decision

1. **Operator: kill the VM immediately** — it's wasting e2-standard-4 resources:
   ```
   gcloud compute instances delete mtds-backfill-defi-20260523 \
     --zone=asia-northeast1-c --quiet
   ```
2. Investigate API mismatch: check when `tick_data_handler.py:preflight` was changed from
   `resolve_bucket_name(env="live")` → `get_tick_data_bucket()`. Confirm the tarball build script picks up the correct
   MTDS + UTL versions.
3. Rebuild tarball AFTER including:
   - UAC@8e1e7e58 (POOL/pool case fix)
   - Correct `tick_data_handler.py` using `get_tick_data_bucket()`
   - All prior MTDS fixes (mtds@69d694b1 + @e86a6ad8)
4. Relaunch `mtds-backfill-defi-YYYYMMDD` with fresh tarball.

## Status

- 2026-05-23 ~20:45 UTC — Found by slot-2 during VM monitoring. VM is RUNNING but producing zero candles. Operator
  action required.
- 2026-05-23 (slot-4 audit) — **Fix landed**: `MTDS@22dcada6` (remote commit
  `fix(mtds): add remaining missing imports for get_prediction_leagues and get_league_fixture_calendar`) removed
  `env="live"` from `resolve_bucket_name` call in `tick_data_handler.py:94`. Branch is now fast-forwarded. **Action
  still required**: kill `mtds-backfill-defi-20260523` VM (was using tarball `498148da` which predates the fix), rebuild
  MTDS DEFI tarball (MTDS@22dcada6 + UAC fix included), relaunch.

## Plan refs

`plans/epics/mtds_mdps_master.md` — MDPS-3.3.DeFi-V verify gate
`plans/active/issues/mdps_defi_swaps_ohlcv_schema_lookup_2026_05_23.md` — related: 195633 batch POOL/pool case issue
(different tarball problem, same verify-gate impact)
