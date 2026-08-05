---
doc_type: issue
title:
  MDPS derivative_ticker candle build showed 12-22GB RSS for a SINGLE HYPERLIQUID instrument/day during live
  verification of the deriv_ohlcv_1m SchemaContract fix — ambient host contention was severe, root cause unconfirmed
summary: >-
  While live-verifying that HYPERLIQUID derivative_ticker candle building now resolves instrument_type correctly
  (mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md todo 2), a single-instrument (HYPERLIQUID:PERPETUAL:
  ADA-USD@LIN), single-day (2026-07-19) derivative_ticker backfill showed RESOURCE_SAMPLE RSS oscillating 11-22GB per
  timeframe (15s through 1h), on a shared host already under severe contention (swap ~22GB in use, load average ~41,
  before this job started). The run eventually disappeared (exit 1, no traceback) partway through the 4h aggregation
  step. All candle writes that DID complete (15s/1m/5m/15m/1h from this run, 4h/1d surviving from an earlier
  same-session attempt) landed correctly with valid data — this is a resource-usage anomaly, not a correctness defect;
  filed per the findings-closure hard rule since it wasn't fixed inline (out of this todo's scope) and the ambient host
  noise makes root-causing it a separate, dedicated investigation.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [mdps, candle, derivative-ticker, memory, resource-usage, host-contention]
related: [/plans/archive/issues/mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md]
created: "2026-08-03"
author: unknown
last_updated: "2026-08-05"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
source: >-
  Discovered 2026-08-03 (slot 6) while live-verifying mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md todo 2
  against real prod data (market-data-tick-cefi-prd-central-element-323112, day=2026-07-19,
  HYPERLIQUID:PERPETUAL:ADA-USD@LIN, data_type=derivative_ticker).
locked_by:
locked_since:
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/adapters/cefi/derivative_adapter.py,
    market-data-processing-service/market_data_processing_service/app/calculators/fast_candle_aggregation.py,
    market-data-processing-service/market_data_processing_service/app/core/live_workers_chain.py,
  ]
resolved_by:
depends_on: []
---

# MDPS derivative_ticker candle build: high RSS for a single instrument, unconfirmed root cause

## What I found

Verifying todo 2 of `mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md` (HYPERLIQUID `derivative_ticker`
instrument_type resolution), I ran a real, narrowly-scoped backfill:

```
GCP_PROJECT_ID=central-element-323112 \
PROTOCOL_DATA_SOURCE_BUCKET_CEFI=market-data-tick-cefi-prd-central-element-323112 \
MDPS_ASSET_GROUP=CEFI MDPS_DATA_TYPES=derivative_ticker MDPS_VENUES=HYPERLIQUID \
MDPS_INSTRUMENT_IDS=HYPERLIQUID:PERPETUAL:ADA-USD@LIN \
market-data-processing-service process --operation process --mode batch \
  --start-date 2026-07-19 --end-date 2026-07-19 --force
```

A SECOND attempt (the first was killed by an external `timeout` after appearing to stall — see "Why it matters" below)
logged `RESOURCE_SAMPLE` lines showing RSS climbing to 11-22GB across the 15s/1m/5m/15m/1h aggregation steps, for ONE
instrument on ONE day (1440 base 15s rows). It then stopped abruptly (no Python traceback, no further log lines) partway
through the 4h aggregation step, with the harness reporting exit code 1.

**Important caveat — the host was already in severe distress before this job started**: `swap=22187MiB` in use and
`load average ~41` (measured via `free -h`/`uptime`) at job start, consistent with heavy concurrent activity from OTHER
slots on this shared host (per `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` and the fleet-wide QG
capacity-crisis precedent). The FIRST attempt at this same command was killed by a `timeout 180` wrapper, but `ps`
showed it alive and accumulating CPU for 10+ minutes before actually dying — i.e., even a 180s wall-clock timeout did
not fire promptly under this host's contention. It's therefore NOT certain whether the 11-22GB RSS figures reflect
genuine MDPS-side memory growth (a new bug distinct from the whole-day-listing OOM already fixed in
`mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md` todo 1) or an artifact of memory fragmentation / swap
thrashing induced by the ambient host pressure this job did not cause.

**The correctness outcome was NOT affected**: every timeframe that completed (either in this run or the earlier
same-session attempt) landed a valid, correctly-partitioned parquet
(`processed_candles/by_date/day=2026-07-19/pipeline_mode=batch_hyperliquid/timeframe={tf}/data_type=derivative_ticker/ instrument_type=PERPETUAL/venue=HYPERLIQUID/HYPERLIQUID:PERPETUAL:ADA-USD@LIN.parquet`
for tf in 15s/1m/5m/15m/1h/4h/1d) — confirmed via `gcloud storage ls -L` (per-file creation timestamps) and by
downloading + inspecting the 1m file (1440 rows, correct `instrument_id`, 24 non-null
`mark_price_mean`/`funding_rate_mean` observations matching the raw file's 24 hourly snapshots, rest honest-absence
NaN).

## Why it matters

If this RSS pattern is genuinely MDPS-side (not host noise), a SINGLE-instrument `derivative_ticker` candle build
scaling to 20GB+ would make even a narrowly `--instrument-ids`-scoped backfill risk OOM on the standard `e2-standard-8`
(32GB) launcher — the same failure class as todo 1's now-fixed whole-day-listing bug, but with a different, unconfirmed
root cause (possibly in `fast_candle_aggregation.aggregate_from_15s_efficient`, or in how each timeframe's polars
aggregation retains/copies the base 15s frame). This was NOT reproduced on a quiet host, so it is not yet confirmed as a
genuine defect — hence P3, not P1 like todo 1.

## Recommended decision

- [x] ✅ [DATA] P1. **Re-run the identical single-instrument HYPERLIQUID `derivative_ticker` backfill on a QUIET host**
      — CONFIRMED scenario (b): RSS climbed to 18,492 MiB (~18.5 GB) for ONE instrument on ONE day in ~33 seconds on a
      quiet host (load ~7, 32Gi available RAM, swap 8.2Gi — vs the original run's load ~41, swap ~22Gi). Two
      RESOURCE_SAMPLE data points captured before OOM kill: rss=1121MiB at init, rss=18492MiB during 1-file processing.
      This is a GENUINE MDPS memory defect, NOT host-contention noise. Repo: market-data-processing-service.

- [ ] [DATA] P1. **Root-cause the `derivative_ticker` single-instrument memory explosion (18.5GB RSS for 1 instrument ×
      1 day).** Bisect by timeframe (comment out timeframes one at a time in the aggregation loop to isolate which
      aggregation step is retaining/copying data), or profile with `tracemalloc`/`memray`. Likely culprit:
      `fast_candle_aggregation.aggregate_from_15s_efficient` or per-timeframe polars aggregation retaining/copying the
      base 15s frame. Follow the same "unscoped listing/retention" investigation pattern as the now-fixed todo 1
      (`mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md`). Repo: market-data-processing-service.

## Progress Log

- **context-scout 2026-08-03**: refreshed context_scope (3 entries, unchanged — still accurate).
- **slot-4 investigation 2026-08-05**: Re-ran the identical single-instrument backfill on a quiet host (load ~7, 32Gi
  available RAM, swap 8.2Gi — vastly better than the original run's load ~41, swap ~22Gi). Two RESOURCE_SAMPLE data
  points captured before the process was OOM-killed:
  - `ts=2026-08-05T13:12:31Z`: rss=1121MiB (~1.1GB) — initialization/loading phase
  - `ts=2026-08-05T13:13:04Z`: rss=18492MiB (~18.5GB) — processing 1 file, ~33s after init **Conclusion: CONFIRMED
    scenario (b)** — RSS genuinely climbs into multi-GB range for ONE instrument on ONE day. This is a GENUINE MDPS
    memory defect, NOT host-contention noise. The prior 11-22GB reading (2026-08-03, slot 6) is now corroborated.
    Escalated to P1 with a new root-cause todo (bisect by timeframe or profile with tracemalloc/memray). Priority bumped
    P3→P1 in frontmatter.
