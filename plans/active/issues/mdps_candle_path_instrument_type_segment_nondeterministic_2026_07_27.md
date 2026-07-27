---
doc_type: issue
title: MDPS candle object path's instrument_type segment presence varies run-to-run for the same shard
summary: >-
  Two consecutive --force candle writes for the identical (CEFI, BINANCE-FUTURES, trades, 2026-07-05, 1m, BTC-USDT@LIN)
  shard landed at two different object paths in the -test- bucket — one with an instrument_type= path segment, one
  without — despite byte-identical content (same md5Hash, same size). Not root-caused; tracked as a P3 follow-up
  alongside the existing candle canonical-path migration epic.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer, admin]
created: 2026-07-27
assigned_vm: NA
parent_epic: infrastructure_master
resolved_by:
locked_by:
source: [data_pipeline_check_mdps_features_2026_07_20.md todo 8]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
tags: [data, mdps, canonical-path, minor]
priority: P3
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# MDPS candle object path's instrument_type segment presence varies run-to-run for the same shard

## What I found

While re-running `/data-pipeline-check-mdps` force-leg checks against the SAME shard (CEFI:BINANCE-FUTURES:trades,
day=2026-07-05, instrument BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN) across several independent `--force` VM runs today,
two OBJECTS exist side by side in the `-test-` bucket for the identical timeframe=1m candle, byte-identical content
(same `md5Hash=aS3EOfBORmGK24TlkgEpOA==`, same `size=246354`), but at two different paths — one WITH an
`instrument_type=PERPETUAL` path segment, one WITHOUT it:

```
processed_candles/by_date/day=2026-07-05/pipeline_mode=batch_tardis/timeframe=1m/data_type=trades/instrument_type=PERPETUAL/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet
processed_candles/by_date/day=2026-07-05/pipeline_mode=batch_tardis/timeframe=1m/data_type=trades/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:BTC-USDT@LIN.parquet
```

Per `/data-pipeline-check-mdps`'s own skill doc: "`instrument_type=` is **required** on this declared/canonical template
but only **tolerated** (not required) by the force/skip legs' measured template — a not-yet-migrated legacy object still
on disk during the P7 migration window lacks it." That describes a KNOWN legacy-vs-canonical split, but does not explain
why a **fresh `--force` re-run today** would write to the segment-less path at all, given every attempt used the
identical CLI invocation shape.

## Why it matters

If the instrument_type segment's presence in the write path is non-deterministic for the identical input (same
venue/instrument/day/timeframe/pipeline_mode), that is either (a) a race/ordering dependency in how the writer resolves
`instrument_type` for this instrument (e.g., depends on which entry of the 424,624-key wire-map hash iteration order
lands first), or (b) two different code paths (e.g., the `pipeline_e2e_check.py` skill's own launcher invocation vs. a
plain direct `python -m market_data_processing_service --operation process` CLI invocation) resolve `instrument_type`
differently for the same shard. This was NOT root-caused this session (out of scope for todo 8's force/skip proof) but
is exactly the kind of "canonical shape gap" the check skill's own `content_check=non_canonical` worklist is meant to
catch — it should have caught this if the canonical leg had run against both write attempts.

## Recommended decision

File as tracked follow-up rather than block on it — todo 8's force/skip proof does not depend on which of the two paths
is "the" canonical one; both carry the same 7,615-candle-equivalent content. Root-cause during the canonical A/B/C
migration work already tracked (`candle_canonical_path_migration_execution_2026_07_24.md`) rather than as new scope
here.

## Todos

- [ ] [DATA] P3. Root-cause why two consecutive `--force` writes for the identical (CEFI, BINANCE-FUTURES, trades,
      2026-07-05, 1m, BTC-USDT@LIN) shard landed at two different object paths (with vs. without `instrument_type=`
      segment) — check whether this is invocation-path-dependent (skill driver vs. direct CLI) or a race in
      instrument_type resolution (repo: market-data-processing-service).
