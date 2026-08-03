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
related: [/plans/active/issues/mdps_cefi_candle_backfill_recent_date_bugs_2026_07_26.md]
created: "2026-08-03"
last_updated: "2026-08-03"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
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
slots on this shared host (per `codex/12-agent-workflow/async-wait-and-poll-discipline.md` and the fleet-wide QG
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

- [ ] [DATA] P3. **Re-run the identical single-instrument HYPERLIQUID `derivative_ticker` backfill (see command above)
      on a QUIET host (a dedicated VM with no other concurrent agent load, or during a fleet-quiet window)** and capture
      `RESOURCE_SAMPLE` RSS across all 7 timeframes. **Done when**: either (a) RSS stays in the low hundreds-of-MB to
      low-GB range (matching bug 1's proof for `trades`, ~1.3GB peak for 2 instruments) — confirms this was
      host-contention noise, close as WORKS-AS-INTENDED; or (b) RSS genuinely climbs into the multi-GB range for ONE
      instrument — escalate to P1 and root-cause the specific aggregation step responsible (bisect by commenting out
      timeframes one at a time, or profile with `tracemalloc`/`memray`), following the same "unscoped listing/retention"
      investigation pattern as todo 1. Repo: market-data-processing-service.
