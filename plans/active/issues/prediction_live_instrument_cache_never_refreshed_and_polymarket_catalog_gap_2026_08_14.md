---
doc_type: issue
title:
  Prediction live VMs resolve their instrument universe once at boot and never refresh it — plus a separate upstream gap
  where instruments-service stopped producing daily POLYMARKET catalogs after 2026-08-05
summary: >-
  Diagnosing why the three prediction live VMs (prediction-live-kalshi-trades / prediction-live-polymarket-trades /
  prediction-live-polymarket-book-snapshot-5, all RUNNING since 2026-08-03) stopped producing captured rows on
  2026-08-03/08-05 while continuing to run found two independent, non-overlapping root causes. (1) The live runner's
  hot-reload path (`InstrumentCacheRefreshConsumer` / `apply_instrument_delta`) exists in
  `market_tick_data_service/live/websocket_runner.py` but is never wired up — the real CLI entrypoint
  (`cli/handlers/websocket_streaming_handler.py::WebsocketStreamingHandler.run()`) constructs `LiveWebsocketRunner(...)`
  without ever passing `cache_refresh_consumer=`, so every live VM resolves its instrument universe exactly once at boot
  and never re-reads a later day's catalog as markets settle and new ones open. (2) Independently, instruments-service's
  POLYMARKET `instrument_availability/by_date/` catalog writer stopped producing entirely after 2026-08-05 (KALSHI's
  writer is unaffected and stayed fresh) — a genuine upstream gap that would starve capture even if (1) were fixed. Both
  are outside this session's ownership (VM launchers / shard configs / the live-capture alerting check) — (1) is inside
  `market_tick_data_service/live/**` and the websocket handler (owned by a different worker on
  `cross_ag_live_capture_parity_2026_08_14.md`), (2) is an instruments-service data-production gap with a separate
  owner. Filed here so both are tracked rather than left as session findings.
status: open
nature: issue
asset_group: [prediction]
stage: [data]
repos: [market-tick-data-service, instruments-service, deployment-service]
scope: [engineer]
tags: [prediction, live-trading, mtds, instruments-service, wsfeedconnector, manifest]
related:
  [
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /codex/05-infrastructure/live-pipeline-architecture.md,
  ]
created: 2026-08-14
author: claude-code (interactive session, cross_ag_live_capture_parity_2026_08_14.md Finding C non-sports legs)
parent_epic: batch_live_symmetry_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source: >-
  Live diagnosis, 2026-08-14: run.log grep across the full 11-day/31MB history for both prediction-live-kalshi-trades
  and prediction-live-polymarket-* VMs (`resolved N instruments prediction/<VENUE>` appears exactly once, at boot, never
  again) + a direct GCS listing of `instrument_availability/by_date/day=<date>/.../venue=POLYMARKET/` showing 62-63
  blobs on 08-03/08-05 and zero on 08-10/08-13/08-14 while KALSHI stayed populated every day.
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/websocket_runner.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py,
    market-tick-data-service/market_tick_data_service/live/_instrument_cache_consumer.py,
  ]
depends_on: []
locked_by:
locked_since:
resolved_by:
drift_direction: advance-code
---

# Prediction live VMs resolve their instrument universe once at boot and never refresh it

## Root cause A — the hot-reload path exists but is never wired into the live CLI entrypoint (both venues)

`LiveWebsocketRunner.run()` (`market_tick_data_service/live/websocket_runner.py:325-390`) only resolves the IS
instrument universe when its internal buffer starts empty, and only spawns the `InstrumentCacheRefreshConsumer`
background task when `self._cache_refresh_consumer is not None`. The real production entrypoint,
`WebsocketStreamingHandler.run()` (`market_tick_data_service/cli/handlers/websocket_streaming_handler.py:220-266`),
constructs `LiveWebsocketRunner(...)` without ever passing `cache_refresh_consumer=` — so it is always `None` for every
real live VM, and `apply_instrument_delta()` (the delta subscribe/unsubscribe method) never runs in production.

Evidence: grepping the full run.log for `prediction-live-kalshi-trades-20260803-181821` (11 days, 31MB) for `resolved` /
`instrument_cache_refresh` / `MTDS_LIVE_INSTRUMENT_CACHE_REFRESHED` finds exactly one match —
`resolved 13098 instruments prediction/KALSHI` at 2026-08-03 17:22:27, boot time. Same shape for both Polymarket VMs
(`resolved 319820 instruments prediction/POLYMARKET` at boot, never again). Meanwhile instruments-service is confirmed
still producing fresh daily KALSHI catalogs through 2026-08-14 that the KALSHI VM never re-reads — it is alive and still
subscribed to its 08-03 market list, which has simply settled/closed in the following days.

- [ ] [CODE] P1. Wire `cache_refresh_consumer=` into the `LiveWebsocketRunner(...)` construction in
      `websocket_streaming_handler.py::run()` (or add an equivalent periodic full-day re-resolution loop), so a running
      prediction shard re-reads `instrument_availability/by_date/day={today}` as the wall-clock date rolls and picks up
      newly-listed markets — DoD: a live shard running across a UTC day boundary shows a fresh `resolved N instruments`
      (or delta-apply) log line for the new day without a restart, and captured rows resume for markets that opened
      after boot. Owner: whoever holds `market_tick_data_service/live/**` +
      `cli/handlers/websocket_streaming_handler.py` on `cross_ag_live_capture_parity_2026_08_14.md` (not this session —
      VM launchers/shard configs/alerting only).

## Root cause B — instruments-service stopped writing POLYMARKET daily catalogs after 2026-08-05 (KALSHI unaffected)

Direct GCS check of `instrument_availability/by_date/day=<date>/…/venue=POLYMARKET/`: 62-63 blobs on 2026-08-03 and
2026-08-05, **zero** on 2026-08-10/08-13/08-14. The same check for KALSHI shows blobs present and fresh on all the same
days — this is POLYMARKET-specific, not a blanket IS outage. This is an independent gap from Root Cause A: even once the
hot-reload wiring above is fixed, a Polymarket live shard would have nothing new to re-read after 08-05. Compounding
this, both Polymarket per-VM manifest shards show 0 of 319,820 rows ever `captured` in 11 days (100% `empty_confirmed`)
— the connector may never have received a single tick even during the 08-03..08-05 window when the catalog was fresh;
that half is inside `market_tick_data_service/live/connectors/**` (a different worker's ownership on the parity plan)
and is flagged, not diagnosed further, here.

- [ ] [DATA] P1. Root-cause why instruments-service's Polymarket `instrument_availability` catalog writer stopped
      producing after 2026-08-05 while the KALSHI writer (same service, same day-range) kept working — DoD: a named
      cause (scheduler paused for this one venue, an upstream Polymarket API change, a silent per-venue exception) and
      either a fix or, if operator-gated, a retag. Owner: instruments-service (not this session's ownership scope).
- [ ] [CODE] P2. Diagnose why zero of 319,820 Polymarket rows were ever `captured` even during the 08-03..08-05 window
      when the catalog WAS fresh — is this the same fallthrough class as Finding A on the parity plan, or a distinct
      connector bug? Owner: `market_tick_data_service/live/connectors/**` (a different worker's ownership on
      `cross_ag_live_capture_parity_2026_08_14.md` — flagged, not investigated further here).

## Progress Log

- **2026-08-14**: filed from `cross_ag_live_capture_parity_2026_08_14.md` Finding C's prediction leg. This session's
  scope was VM launchers/shard configs/the live-capture alerting check only — both root causes above live in files
  explicitly out of that scope (the websocket handler / live connectors, owned by a different worker on the same plan;
  and instruments-service, a separate service). The in-scope half of this diagnosis (the monitoring gap that let this
  run silent — `live_stream_watcher.build_prediction_live_shards()` resolving the wrong GCS bucket kind and silently
  returning zero shards every sweep) was fixed directly in this session, not filed here — see
  `deployment-service@<pending commit>` and the parity plan's Progress Log.
