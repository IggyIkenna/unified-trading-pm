---
doc_type: issue
title: Live-CeFi VM cold start hits an empty IS universe until the 13:30 UTC daily refresh — no prior-day fallback
summary:
  A live-CeFi VM redeploy timed before instruments-service's 13:30 UTC daily `is-daily-enum-cefi` job captures
  ZERO rows for every venue (not just the venue being fixed) until that job publishes "today"'s instrument
  partition — MTDS has no fallback to the prior day's still-valid partition on a cold start. Self-resolving,
  not data-corrupting (honest-absence), but an avoidable multi-hour capture gap on every early-UTC-day redeploy.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, deployment-service]
scope: [engineer]
tags: [cefi, live-capture, instruments-service, redeploy, cold-start]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16_finalize.md,
  ]
parent_epic: mtds_mdps_master # was: cefi_master (epic-assignment audit 2026-08-19) -- root cause + fix are in
  # generic MTDS live-plumbing (instrument_availability_paths.py, live/_is_universe.py) with no asset-group gating --
  # same day-partition-fallback gap hits any asset group's live VM redeployed early in the UTC day
created: "2026-08-17"
author: "slot-17 (infra, AO-dispatched)"
source: ["cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16_finalize.md P2.2/P2.3"]
assigned_vm: planning
priority: P2
locked_by:
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /codex/04-architecture/instruments-service-as-ssot-for-mtds.md,
    /plans/archive/2026_08/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16_finalize.md,
    market-tick-data-service/market_tick_data_service/instrument_availability_paths.py,
    market-tick-data-service/market_tick_data_service/live/_is_universe.py,
    deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh,
  ]
---

# Live-CeFi VM cold start hits an empty IS universe until the 13:30 UTC daily refresh

## What I found

While live-verifying the `mtds-live-cefi-consolidated-20260817-025031` redeploy (finalize plan for the
OKX-FUTURES xperp marker fix), all 24 MVP shard processes came up correctly, but zero warm-tier
(`live-events/warm/cefi/{trades,book_snapshot_5,derivative_ticker}/*.parquet`) objects have landed since the
redeploy (checked 2026-08-17T02:52Z through 03:14Z — 22+ minutes, no new writes for ANY venue, not just
OKX-FUTURES).

SSH into the VM (`sudo tail /home/ikennaigboaka/logs/live-<venue>-<data_type>.log`) showed the same message on
**every** venue checked (OKX-FUTURES, BINANCE-FUTURES, HYPERLIQUID):

```
read_is_universe_sync: no instruments.parquet for cefi/<VENUE> (lookup_venue=<VENUE>) day=2026-08-17 in either
by_date layout
MTDS live WS: IS universe empty for cefi/<VENUE>/trades — retrying in 300s
```

Root cause confirmed via GCS: `instruments-store-cefi-prd-central-element-323112` has
`instrument_availability/by_date/day=2026-08-15/...` (written 2026-08-16T13:35 UTC) and
`day=2026-08-16/...` (written 2026-08-16T13:37 UTC — i.e. the PRIOR day's data, written the NEXT day), but
**no `day=2026-08-17/` partition existed as of 03:15 UTC**. The producing job is Cloud Scheduler
`is-daily-enum-cefi`, schedule `30 13 * * *` (13:30 UTC daily) — so "today's" exact-date instrument partition
simply isn't published yet this early in the UTC day; this is normal, on-schedule behavior, not a broken job.

`market_tick_data_service.live._is_universe.read_is_universe_sync` /
`instrument_availability_paths.resolve_instruments_blob` resolve **only the exact `day=<today>` partition** —
there is no fallback to the most-recent prior day. `websocket_runner._resolve_or_keepalive` handles this
gracefully (retries every 300s, emits honest-absence, keeps the process alive with heartbeats — this is NOT a
crash and NOT fabricated data), but the net effect is: **a live-CeFi VM that cold-starts before ~13:30 UTC
captures ZERO rows for every venue until that daily job lands**, typically ~13:35-13:40 UTC — up to ~13 hours
of dead capture from a redeploy timed early in the UTC day.

The PREVIOUS VM (`mtds-live-cefi-consolidated-20260814-041422`, launched 2026-08-14) was NOT affected by this
same-day gap — it was still producing real warm-tier writes at 02:40-02:47 UTC on 2026-08-17, well before
today's `day=2026-08-17` partition existed. This confirms the universe is resolved ONCE at process startup and
then held for the life of the process (not re-resolved at each UTC day boundary) — so only a REDEPLOY (not the
mere passage of a day boundary on an already-running VM) can land in this gap.

## Why it matters

Every live-CeFi VM redeploy (routine maintenance, a code-fix rollout like this one, a preemption relaunch)
timed before ~13:30 UTC silently zeroes out live capture for **all** CeFi venues for however long remains
until the daily refresh — not just the venue being fixed. The connector's own honest-absence design means no
data is fabricated, but this is still a real, avoidable capture gap with no current guardrail warning the
operator/agent at redeploy time.

## Recommended decision

Add a preflight/fallback so a redeploy timed inside the blind window doesn't silently sit empty for hours —
either give `resolve_instruments_blob` a same-connector fallback to the most-recent prior-day partition when
`day=<today>` isn't published yet (bounded staleness, e.g. instrument universes rarely change day-to-day), or
have the launcher warn/gate on it. Both are legitimate; leaving the choice to whichever worker picks this up
since either closes the gap.

- [ ] [DATA] P2. Add a bounded fallback in
      `market-tick-data-service/market_tick_data_service/instrument_availability_paths.py` /
      `live/_is_universe.py`: when `day=<today>`'s `instruments.parquet` is absent for
      a venue, look back up to N prior days (e.g. 3) for the most recent available partition and use it (log
      clearly that it's a fallback, not silently treat it as today's fresh data) instead of returning an empty
      universe until the daily job lands. Add a unit test covering the fallback + the "no partition in the
      lookback window either" honest-absence case. Repo: market-tick-data-service.
- [ ] [INFRA] P3. Add a short comment/warning to
      `deployment-service/scripts/vm/launch-mtds-live-cefi-consolidated.sh` (and any sibling live-connector
      launchers reading the same `instrument_availability/by_date/day=<today>` path) noting the `is-daily-enum-*`
      13:30 UTC dependency, so a future redeploy done before that time is a documented, expected tradeoff rather
      than a surprise. Repo: deployment-service.

## Progress Log

- **context-scout 2026-08-17**: populated context_scope (5 entries).
