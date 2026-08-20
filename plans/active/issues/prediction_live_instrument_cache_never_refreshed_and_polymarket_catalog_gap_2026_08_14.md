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
    /plans/active/cross_ag_live_capture_parity_2026_08_14.md,
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
      **2026-08-15 re-verification (empty_confirmed_and_coverage_correctness_audit_2026_08_15.md todo "Verify prediction
      Polymarket catalog-gap vs SOURCE_RETURNED_ZERO absorption")**: re-measured live via
      `get_storage_client().list_blobs()` against `instruments-store-pred-prd-central-element-323112` —
      08-03/08-05/08-08 all have 62-63 POLYMARKET blobs, **08-10/08-13/08-14/08-15 all have exactly 0** (KALSHI stayed
      healthy every date, 43→50 growing). So the actual break point is between 08-08 and 08-10, not immediately after
      08-05 as this doc's title states — retitle/update once root-caused. Separately confirmed Polymarket's Gamma API
      itself is NOT the cause: a live unauthenticated `GET gamma-api.polymarket.com/markets?closed=false&active=true`
      today returned HTTP 200 with normal market payloads (full field set present, no schema drift) — so this is NOT an
      upstream API outage or a Gamma schema-drift silently emptying `PolymarketGammaMarket.model_validate()` (which
      would be a genuine SOURCE_RETURNED_ZERO-absorption bug, the same class just fixed for cefi Deribit/Hyperliquid and
      the 5 defi oracle collectors — see this audit plan's completed todos). Checked for a Cloud Scheduler job or GH
      Actions workflow driving this catalogue build (`gcloud scheduler jobs list`, grep of `.github/workflows/*.yml` for
      `schedule:` + prediction/catalog) — found neither, so the trigger mechanism lives outside this repo's visible
      config (Cloud Run job / VM cron / agent-orchestrator dispatch) and needs whoever owns that trigger to check
      whether the POLYMARKET leg of the job is still being invoked at all. Zero blobs (not a thin/partial catalogue) is
      more consistent with the job never running for this venue since 08-10 than with an in-code SOURCE_RETURNED_ZERO
      absorption bug — but this is not fully proven without reading the job's own run logs, which this session did not
      have access to.
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
  `deployment-service@ebeef843c9` (verified reachable ancestor of `origin/live-defi-rollout` — plan_reconciler 2026-08-17) and the parity plan's Progress Log.
- **na-eligibility-audit 2026-08-17** [body-hash:d4ac8fe6162f4ea9]: KEEP-NA, valid — 3 open todos, all real, unblocked
  root-cause/design investigations (P1 CODE: wire `cache_refresh_consumer=` into the live runner or add a periodic
  re-resolution loop; P1 DATA: root-cause why the IS Polymarket catalog writer stopped after 2026-08-05; P2 CODE:
  diagnose the zero-ever-captured Polymarket connector gap), each explicitly self-labeled "not this session's
  ownership" and pointing at `cross_ag_live_capture_parity_2026_08_14.md` or instruments-service as the likely
  executing owner. **Not independently cross-checked against `cross_ag_live_capture_parity_2026_08_14.md` for a
  duplicate claim this run** (out of this pass's budget) — flagging for a future pass to verify before treating these
  as this doc's own dispatch surface. None are mechanically bounded (root-cause + design-decision work). Doc stays
  NA.

- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries).

- **na-eligibility-audit 2026-08-17 (prediction tranche, re-verify)** [body-hash:53901990cf58bd20]: KEEP-NA, valid —
  3 open items re-confirmed as genuine, unblocked root-cause/design investigations on live-dispatch-critical capture
  code. Cross-checked `cross_ag_live_capture_parity_2026_08_14.md` and confirmed a mutual redirect (that plan's own
  item at line 224 stays open specifically pending this doc's fix), not a duplicate extraction —
  `KEEP_NA_STALE_DUPLICATE` does not apply. Doc stays NA.
- **na-eligibility-audit 2026-08-18** [body-hash:eb19afefaee42f7d]: KEEP-NA, valid -- all 3 open items explicitly redirect to cross_ag_live_capture_parity_2026_08_14.md (mutual redirect re-confirmed -- that plan's own item at line 224 stays open pending this doc) or to an instruments-service investigation blocked on trigger-log access this session does not have. Doc stays NA -- flipping assigned_vm here would misroute the dispatch mechanism.
- **plan_reconciler 2026-08-18 (prediction tranche)**: label fix only — the 2 entries above both said "todo 224",
  but `cross_ag_live_capture_parity_2026_08_14.md` has only 17 top-level todos total; 224 is that doc's LINE number
  for the redirect item (`- [ ] [DATA] P1. Diagnose the prediction live-capture stall...`), not a todo ordinal. The
  substance both entries describe (a real, deliberate mutual redirect) is verified accurate — only the "todo 224"
  label was imprecise. Corrected in place above rather than left to keep misleading a future reader.
- **na-eligibility-audit 2026-08-18** [body-hash:6421e3c290c99166]: KEEP-NA, valid — 3 open items re-confirmed: all
  explicitly redirect to `cross_ag_live_capture_parity_2026_08_14.md` (confirmed mutual redirect, not a duplicate —
  `KEEP_NA_STALE_DUPLICATE` does not apply) or to an instruments-service investigation blocked on trigger-log access
  this session lacks. A redirect banner means the dispatch mechanism would be wrong even though the todo text itself
  reads boundable — flipping `assigned_vm` here would misroute the work. Consistent with 3 prior passes. Doc stays
  NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-21 (prediction tranche)**: KEEP-NA, valid — 3 open items re-confirmed: 2 explicitly
  redirect to `cross_ag_live_capture_parity_2026_08_14.md` (mutual redirect re-verified — that plan's own item at
  line 224 stays open specifically pending this doc's fix, so `KEEP_NA_STALE_DUPLICATE` does not apply) and 1
  redirects to an instruments-service investigation blocked on trigger-log access this session doesn't have. A
  redirect banner means the dispatch mechanism would be wrong even though the todo text reads boundable — flipping
  `assigned_vm` here would misroute the work, per the never-re-litigate-a-redirect rule. Doc stays NA.
