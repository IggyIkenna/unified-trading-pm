---
doc_type: issue
title:
  4 of 9 depth_of_book_10 target venues lack live book_snapshot_5 entirely (BINANCE-SPOT, OKX-FUTURES, OKX-SPOT, UPBIT)
summary: >
  l2_book_microstructure_capture_2026_07_13.md todo 2 ("extend the live capture") assumed all 9 target venues already
  had live book_snapshot_5 to extend. 4 of them do not (batch-only or trades-only today) — depth_of_book_10 for these
  needs the L5-equivalent live capture built first, which is new construction, not an extension.
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [live-capture, orderbook, microstructure, premise-correction]
related: [l2_book_microstructure_capture_2026_07_13.md]
created: 2026-07-13
parent_epic: strategy_master
priority: P2
source:
  [
    "Discovered while implementing l2_book_microstructure_capture_2026_07_13.md todo 2 (slot 8, 2026-07-13) — tracing
    each of the 9 target venues' factory registration in market_tick_data_service/live/connectors/ found 4 with no
    book_snapshot_5 branch at all.",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# 4 of 9 depth_of_book_10 target venues lack live book_snapshot_5 entirely

## What I found

`l2_book_microstructure_capture_2026_07_13.md` todo 2 says "extend the live capture ... to pull the deeper book" for
each of the 9 CeFi venues confirmed capable in todo 1's research doc. Implementing it required tracing each venue's
`_<venue>_factory()` in `market_tick_data_service/live/connectors/` to find its `book_snapshot_5` branch to extend. 5 of
9 have one and were successfully extended (see `market-tick-data-service@15f5657b`, this session): **BINANCE-FUTURES,
OKX-SWAP, BYBIT, DERIBIT, COINBASE-SPOT.**

**4 of 9 have NO live `book_snapshot_5` branch at all** — their factory functions ignore `data_type` entirely and always
return a trades-only connector:

1. **BINANCE-SPOT** (`binance_spot_ws.py::_binance_spot_factory`) — always returns `BinanceSpotWSFeedConnector` (trades
   only). `book_snapshot_5` for this venue exists only via Tardis batch replay (`tardis_machine_ws.py` maps
   `"BINANCE-SPOT": "binance"`), not live WS.
2. **OKX-FUTURES** — has NO registered connector at all in `WS_FEED_CONNECTOR_FACTORIES`. A 2026-07-09 fix
   (`okx_ws.py::register()` comment) deliberately left it unregistered: the existing `_okx_factory` only ever produces
   `OKX-SWAP`-prefixed canonical instruments, so registering it under `"OKX-FUTURES"` would have been wrong-venue
   tagging, not a genuine OKX-FUTURES (dated futures contract) feed.
3. **OKX-SPOT** (`okx_spot_ws.py::_okx_spot_factory`) — always returns `OKXSpotWSFeedConnector` (trades only, via
   re-tagged OKX-SWAP-shape frames). No `book_snapshot_5`/`depth_of_book_10` branch.
4. **UPBIT** (`upbit_spot_ws.py::_upbit_factory`) — always returns `UpbitSpotWSFeedConnector` (trades only).
   `book_snapshot_5` for UPBIT exists only via Tardis batch (confirmed via
   `shard_memory_profile.py: ("UPBIT", "book_snapshot_5", "spot_pair"): 11.0` and `tardis_csv_transport.py`'s v7 comment
   referencing `book_snapshot_5 on UPBIT`), never live WS.

## Why it matters

The parent plan's `## Todos` list treats all 9 venues as symmetric ("extend the live capture... for each venue confirmed
capable"). For these 4, there is nothing to extend — building `depth_of_book_10` live capture for them means building
the L5-equivalent-or-deeper live WS capture from scratch (new subscription, new parser, new connector class, new factory
registration), which is a materially bigger scope than the other 5 venues' extension work and should be
estimated/dispatched as its own unit rather than silently rolled into "todo 2 done".

OKX-FUTURES specifically also needs a real design decision before any code: OKX-FUTURES (dated futures contracts) is a
genuinely different instrument_type from OKX-SWAP (perpetual swap) in OKX's own API — building live capture for it is
not just "copy the SWAP connector", it needs its own dated-contract instrument resolution, which `okx_ws.py`'s
2026-07-09 fix explicitly punted on.

## Recommended fix

For each of the 4 venues, in the same style as the 5 already-extended venues:

1. **BINANCE-SPOT**: mirror `BinanceFuturesBookWSConnector`'s combined-stream `@depth5@100ms`/`@depth20@100ms` pattern
   against `wss://stream.binance.com:9443/stream` (Binance Spot's combined-stream endpoint — confirm the exact URL/path,
   it differs from the futures `fstream` host), wire into `binance_spot_ws.py`'s factory (currently has none).
2. **OKX-SPOT**: mirror `OKXFuturesBookWSConnector`/`OKXFuturesDepth10WSConnector`'s `books5`/`books` channel pattern
   with `instType: SPOT` instId format, wire into `okx_spot_ws.py`'s factory (currently has none).
3. **OKX-FUTURES**: **DECIDED (2026-07-13, slot 8) — real venue, in scope.** `OKX-FUTURES` is a fully-registered UAC
   canonical venue (`registry/venue_constants.py::OKX_FUTURES`), NOT a leftover/mistaken key: it has its own adapter-key
   (`venue_adapter_keys.py`: `"OKX-FUTURES": "tardis"`), coverage start `2020-01-01`
   (`venue_mapping.py::VENUE_COVERAGE_START`), full capability declarations
   (`PERP_TRADE`/`FUTURES_TRADE`/`OPTIONS_TRADE` in `venue_constants.py`), collateral-acceptance rows
   (`venue_collateral.py`), and an explicit expected-`data_types` list (`expected_coverage.py`:
   `"OKX-FUTURES": ["trades", "book_snapshot_5", "derivative_ticker"]`). A code comment at
   `market_data_categories.py:2089-2092` spells out the exact relationship to OKX-SWAP: _"OKX-FUTURES is dated futures
   but the MVP universe seeds with perps (the linear ones live under OKX-SWAP, the dated ones under OKX-FUTURES; both
   write trades for the MVP perp basket)"_ — i.e. OKX-FUTURES = OKX's genuinely distinct DATED (expiry) futures
   contracts, a real, separately-expected instrument universe, not a duplicate/wrong-tag of OKX-SWAP's perpetuals. The
   2026-07-09 live-connector fix (`okx_ws.py::register()`) only decided the SHARED perp-shaped `_okx_factory` must not
   be reused for it (that would mistag dated-futures frames as perpetual/SWAP) — it did NOT decide OKX-FUTURES is out of
   scope for live capture. **Conclusion: build a real OKX-FUTURES connector** (own `instId` resolution for OKX's
   dated-contract naming, e.g. `BTC-USD-250328`-style expiry symbols — check `venue_mapping.py`'s OKX helpers + the
   Tardis `okex-futures` exchange-name mapping for the exact format before writing the parser), following the same
   `books5`/`books` channel pattern as OKX-SWAP/OKX-SPOT once built.
4. **UPBIT**: mirror `UpbitSpotWSFeedConnector`'s subscribe pattern with a new `orderbook.{count}` message type
   (`{market_code}.30` per docs/L2_BOOK_DEPTH_RESEARCH_2026_07_13.md — 30 is UPBIT's hard cap, so build
   `book_snapshot_5` AND `depth_of_book_10` in one pass off the same 30-level channel, slicing 5 vs up-to-10 levels),
   wire into `upbit_spot_ws.py`'s factory (currently has none).

## Todos

- [x] ✅ [DATA] P2. Decide OKX-FUTURES's scope (real dated-futures venue vs. never-meant-to-carry-live-data) before any
      connector work — read the instrument-universe registry docs first. (repo: unified-trading-pm, decision only) —
      **DONE, slot 8**: real venue, in scope. See the "Recommended fix" section item 3 above for the full evidence trail
      (UAC adapter-key + coverage-start + capability + expected-data_types all present; the 2026-07-09 fix only barred
      reusing OKX-SWAP's factory, not a scope exclusion).
- [x] ✅ [DATA] P2. Build live `book_snapshot_5` + `depth_of_book_10` capture for BINANCE-SPOT (combined-stream
      depth5/depth20, mirrors BinanceFuturesBookWSConnector). (repo: market-tick-data-service) — **DONE, slot 8,
      `market-tick-data-service@e4029282`**. New `binance_spot_book_ws.py` (combined-stream
      `wss://stream.binance.com:9443/stream`, mirrors the futures connector exactly — depth5 for book_snapshot_5,
      depth20-sliced-to-10 for depth_of_book_10; simpler than futures since spot has no @LIN/@INV margin marker or
      derivative_ticker), wired into `binance_spot_ws.py`'s factory (previously always returned the trades-only
      connector regardless of `data_type`). 29 new tests + 34 existing spot-connector tests green, 0 new basedpyright
      violations (3 baseline errors, same shape as the futures original), full quality-gates.sh green.
- [ ] [DATA] P2. Build live `book_snapshot_5` + `depth_of_book_10` capture for OKX-SPOT (books5/books channels, mirrors
      OKXFuturesBookWSConnector/OKXFuturesDepth10WSConnector). (repo: market-tick-data-service)
- [ ] [DATA] P2. Build live `book_snapshot_5` + `depth_of_book_10` capture for UPBIT (single `{market_code}.30` channel
      backs both data_types since 30 is the venue's hard depth cap). (repo: market-tick-data-service)
- [ ] [DATA] P2. Build live `book_snapshot_5` + `depth_of_book_10` capture for OKX-FUTURES (own dated-contract `instId`
      resolution — check `venue_mapping.py`'s OKX helpers + the Tardis `okex-futures` exchange-name mapping for the
      exact expiry-symbol format first; then the same `books5`/`books` channel pattern as OKX-SWAP/OKX-SPOT). Scope
      decision above already resolved this to in-scope, real work — no longer P3/gated. (repo: market-tick-data-service)
