---
doc_type: issue
title: >-
  cefi depth_of_book_10 live wiring shipped + verified for BINANCE-FUTURES; the other 4 capable venues
  (BYBIT-FUTURES/DERIBIT/COINBASE-SPOT/OKX-SWAP) produce only empty_confirmed/zero manifest rows
summary: >-
  The cefi live-capture dispatcher wiring gap for depth_of_book_10 (shard launcher + Pub/Sub topic/subscription) is now
  fully fixed and verified end-to-end with real captured data for BINANCE-FUTURES. This tracks the NEW, narrower
  data-correctness gap the fix surfaced: BYBIT-FUTURES/DERIBIT/COINBASE-SPOT/OKX-SWAP produce only empty_confirmed/zero
  depth_of_book_10 manifest rows on live WS traffic despite their other data_types capturing normally on the same
  venues/VM/window — the first live dispatch any of these 5 connectors has ever had.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, depth_of_book_10, live-capture, data-correctness, pubsub, websocket]
related:
  [
    /plans/archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/l2_book_microstructure_capture_2026_07_13.md,
  ]
created: "2026-08-09"
author: slot-23-infra
assigned_vm: planning
parent_epic: infrastructure_master
priority: P2
locked_by:
resolved_by: cefi_depth_of_book_10_live_capture_only_binance_producing_rows-f2e44d1a47db (slot 22, 2026-08-09)
source: >-
  Discovered while executing cefi_satellite_ao_dispatch_batch13_2026_08_09.md todo 2 ("wire depth_of_book_10 into the
  CeFi live event-log capture dispatcher"). The dispatcher-wiring gap itself is now fully fixed and verified end-to-end
  with real captured data for BINANCE-FUTURES; this doc tracks the NEW, separate data-correctness gap this fix surfaced
  for the other 4 venues.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# cefi depth_of_book_10 live wiring shipped; 4/5 venues not producing real rows

> **🟢 ARCHIVED 2026-08-09 — RESOLVED.** All 4 per-venue debug todos + the wiring gap + the P3 MDPS-enum question are
> shipped. Codex updated at `/codex/05-infrastructure/live-pipeline-architecture.md` § "Trigger cascade". Remaining work
> (VM cycle + fresh manifest read across all 5 venues to prove real captured rows) is tracked on
> `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2 (its `BLOCKED-ON:` tag on this doc
> was cleared in the same session — see that plan's Progress Log).

## What I found

**The dispatcher-wiring gap (this batch's actual scope) is CLOSED and verified end-to-end:**

1. `deployment-service/scripts/vm/setup-cefi-live-consolidated-vm.sh` never had a `depth_of_book_10` shard entry in its
   `MVP_SHARDS` array (the actual live-capture process launcher for the consolidated CeFi VM) — added 5 entries
   (`BINANCE-FUTURES`/`BYBIT-FUTURES`/`DERIBIT`: `+depth_of_book_10`; `COINBASE-SPOT`/`OKX-SWAP`: new venues,
   `depth_of_book_10` only) to both copies of the array (the outer export loop + the embedded supervisor heredoc, which
   must match). Shipped `deployment-service@28e64163`.
2. Adjacent bug found + fixed in the same file family: `launch-mtds-live-cefi-consolidated.sh`'s `FORCE=false` hardcoded
   default silently ignored the `FORCE=true` env-var override the script's own refusal message advertises. Shipped
   `deployment-service@778ee0e3`.
3. **A second, deeper wiring gap surfaced once the shards actually ran**: the `persist-cefi-depth-of-book-10` Pub/Sub
   topic + its GCS warm-sink subscription (`deployment-service/terraform/gcp/live_event_log/{main.tf,warm_sink.tf}`) had
   never been created — every one of the 4 existing cefi data_types (`book_snapshot_5`/`derivative_ticker`/
   `liquidations`/`trades`) has one, `depth_of_book_10` did not. Added both Terraform resources mirroring the existing
   `persist_cefi_*` pattern exactly, and **applied them to live prod** via the module's own standalone `tofu` state
   (`terraform/state/live-event-log` — a SEPARATE root from the `terraform/gcp` root the `tofu.sh` wrapper drives;
   documented in `main.tf`'s own header comment, not currently covered by `deployment-service-gcp-tofu-state.md`).
   **Caution for the applier**: the module's `create_bq_external_tables` variable defaults to `false` in `variables.tf`,
   but the deployed state has it `true` (52 BQ external tables exist) — a plan run without
   `-var="create_bq_external_tables=true"` proposes destroying all 52. Always recover the real values from
   `tofu state show` (or the compactor Cloud Run Job's env vars) before planning against this module; there is no
   committed `.tfvars` file. Confirmed apply:
   `2 to add, 1 to change (harmless client-metadata drift on the compactor job), 0 to destroy`.
4. Cycled the live `mtds-live-cefi-consolidated-*` VM (deleted `-20260806-163414`, healthy per a fresh heartbeat
   - active `trades` writes at delete time; launched `-20260809-121034`) to deploy the fix — 22 shard processes
     confirmed up (17 pre-existing + 5 new `depth_of_book_10`).
5. **Verified real data landing end-to-end for BINANCE-FUTURES**:
   `gs://central-element-323112-events/live-events/warm/cefi/depth_of_book_10/` now exists with 15+ warm files (all
   `pipeline_mode=live_binance`), and the per-VM availability-manifest shard
   (`_index/per_vm/mtds-live-cefi-consolidated-20260809-121034.parquet`) shows 709 `capture_status=captured` rows for
   `BINANCE-FUTURES`/`depth_of_book_10` (real per-instrument book data, not a placeholder).

**What's NOT working — the new finding this doc tracks:**

For the other 4 capable venues (confirmed via ~30 min of live observation post-deploy):

- `BYBIT-FUTURES`: 1 manifest row, `empty_confirmed`.
- `COINBASE-SPOT`: 424 manifest rows, ALL `empty_confirmed`.
- `OKX-SWAP`: 438 manifest rows, ALL `empty_confirmed`.
- `DERIBIT`: **ZERO** `depth_of_book_10` manifest rows at all (its `derivative_ticker` shard on the same venue has 2,997
  rows in the same window, proving the manifest-write path itself works for this venue).

No warm GCS file for `depth_of_book_10` carries any `pipeline_mode` other than `live_binance` — confirmed by parsing all
landed warm files as NDJSON envelopes (they are NDJSON with a `.parquet` filename suffix, matching the existing 4
data_types' own format — not a new problem).

This is NOT a venue-connectivity problem: `BYBIT-FUTURES` and `DERIBIT` both have thousands of `captured` rows for their
OTHER data_types (`book_snapshot_5`/`derivative_ticker`/`trades`) in the identical time window on this same VM — the
venue WS connections and IS-universe resolution work fine. It is also not a REST-reachability problem:
`market-tick-data-service/scripts/book_microstructure_connectivity_check.py` (todo 6 of the source plan) already proved
all 5 venues' public REST order-book endpoints return real depth via the SAME `compute_book_microstructure` derivation
path. This narrows the bug to the LIVE WEBSOCKET depth_of_book_10 path specifically, for these 4 venues' connector
classes — `BybitFuturesDepth10WSConnector`, `DeribitDepth10WSConnector` (exact class names not yet confirmed by
file/line read — only `_bybit_factory`/`_deribit_factory`'s dispatch branches were read), `CoinbaseDepth10WSConnector`,
and the OKX-SWAP depth10 factory branch in `okx_ws.py`. Per the source plan's own Progress Log
(`l2_book_microstructure_capture_2026_07_13.md`, todo 6, 2026-07-14): "todo 2's live WS connectors are shipped but have
never actually been dispatched in production" — this is the FIRST time any of these 5 connectors has ever run live, so
this is a newly-surfaced defect, not a regression I introduced.

**Separate, non-fatal noise also observed** (does not block persistence, logged every flush cycle for all 5 venues):
`websocket_runner.py::_publish_boundary_event` tries to publish a `CandleBoundaryCrossedEvent` with
`data_type="depth_of_book_10"`, but
`unified_api_contracts.internal.domain.market_data_processing.candle_schema.DataType` (the MDPS candle-schema enum
`CandleBoundaryCrossedEvent.data_type` is typed against) does not include `depth_of_book_10` (or its sibling
L2-microstructure types `queue_position`/`order_flow_imbalance`) — a pydantic `ValidationError`, caught and logged
(`"instrument-window flush failed for ...; continuing"`), never fatal. Whether the fix is "add `depth_of_book_10` to the
MDPS `DataType` enum" (if depth_of_book_10 SHOULD feed MDPS candle aggregation, matching how `book_snapshot_5` does per
that data_type's book-summary-column precompute) or "skip the boundary-event publish for data_types outside the MDPS
candle-eligible set" (if it shouldn't) is a real design question, not something I judged safe to guess at inline.

## Why it matters

`depth_of_book_10` is the direct dependency for `queue_position`/`order_flow_imbalance` derivation
(`compute_book_microstructure`, `BookMicrostructureHandler`) and ultimately the `MarketMakingQueueMicrostructureEngine`
backtest gate (`l2_book_microstructure_capture_2026_07_13.md` todo 7's own downstream Phase E1 dependency). Landing real
data for only 1 of 5 capable venues means the derived microstructure features + that engine's eventual gate stay
effectively single-venue, not the full 5-venue MVP scope the source plan targeted.

## Recommended decision

Investigate the 4 venue-specific `*Depth10WSConnector` implementations directly against live WS traffic (not just the
REST connectivity check) to find why they parse/buffer zero real depth updates — likely a subscription-channel or
symbol-format bug specific to the depth10 slicing path, given the SAME venues' other connectors work correctly on this
exact VM in this exact time window. Separately, resolve the `CandleBoundaryCrossedEvent.data_type` MDPS enum question
(add `depth_of_book_10`, or scope `_publish_boundary_event`'s callers to skip non-candle-eligible data_types) — an
operator/architecture call, not a mechanical fix.

- [x] ✅ [CODE] P2. Debug why `BybitFuturesDepth10WSConnector` (bybit_futures_book_ticker_ws.py) produces only
      `empty_confirmed` manifest rows on live WS traffic despite the venue's other connectors (trades/book_snapshot_5/
      derivative_ticker) capturing real data on the same VM in the same window — compare against the REST-verified book
      depth from `book_microstructure_connectivity_check.py` to isolate whether the WS subscription/parse path is
      silently dropping real depth updates. Repo: market-tick-data-service. — **DONE 2026-08-09, slot-19,
      `market-tick-data-service@e3bd10b9`.** Root cause: NOT the connector's WS subscribe/parse path at all —
      `BybitFuturesDepth10WSConnector` reuses the exact same `_BybitBookStateConnector` base class as the WORKING
      `book_snapshot_5` connector, only `depth`/`subscribe_depth` differ. The bug is upstream, in IS-universe
      resolution: `BYBIT-FUTURES` is a UAC-registered alias that maps to the SAME underlying Tardis exchange as `BYBIT`;
      instruments-service's batch IS writer persists `instrument_key`s under the PRIMARY venue token (`BYBIT`), never
      under the alias. A live shard launched with `venue=BYBIT-FUTURES` looked up an `instruments.parquet` blob that
      never existed, resolved zero instruments, and spun in the empty-universe retry loop. Since `websocket_runner`'s
      `_buffers`/`connect(instrument_ids=...)` are both keyed off that same resolved set, the connector subscribed to
      nothing and every flush cycle wrote `empty_confirmed` with zero real data. Fix: `_resolve_is_lookup_venue()` in
      `market_tick_data_service/live/_is_universe.py` mirrors IS's own
      `TardisReferenceDataAdapter._resolve_instrument_key_venue` resolution so the lookup targets the blob IS actually
      wrote; falls back to the venue unchanged when it has no Tardis alias (confirmed via live `VenueMapping` check:
      only `BYBIT-FUTURES` of the 5 depth10 venues is an alias — `DERIBIT`/`COINBASE-SPOT`/ `OKX-SWAP`/`BINANCE-FUTURES`
      all resolve to themselves, consistent with their differing symptoms/root causes). New regression test
      (`test_is_lookup_venue_resolves_tardis_alias_to_primary_venue`) + all 38 existing `test_websocket_runner.py` tests
      pass; full repo suite (10332 passed) + QG green.
- [x] ✅ [CODE] P2. Debug why `DeribitDepth10WSConnector` (deribit_book_ticker_ws.py) produces ZERO `depth_of_book_10`
      manifest rows at all (not even `empty_confirmed`) despite `derivative_ticker` capturing 2,997 rows on the same
      venue/VM/window — check whether the connector even registers a flush-triggering instrument window for this
      data_type. Repo: market-tick-data-service. — market-tick-data-service@90e2336c (see Progress Log for root cause +
      live-reproduction evidence).
- [x] ✅ [CODE] P2. Debug why `CoinbaseDepth10WSConnector` (coinbase_book_ws.py) produces only `empty_confirmed` rows
      (424 in ~30 min) — this is COINBASE-SPOT's first-ever live dispatch on this VM (no prior working baseline for
      comparison), so also verify the venue's `level2` subscription itself is actually receiving book-diff messages, not
      just that the depth-10 slicing logic runs. Repo: market-tick-data-service. — **DONE 2026-08-09, slot 6,
      `market-tick-data-service@cc736408`.** Root cause: Coinbase Exchange deprecated the public `level2` channel — it
      now requires authentication (live-verified: unauthenticated subscribe gets
      `{"type":"error","reason":"level2, level3, and full channels now require     authentication..."}` then an empty
      `{"type":"subscriptions","channels":[]}`). The connector's `_handle_frame` never recognized
      `error`/`subscriptions` frame types (silently returned `[]` for anything but `snapshot`/ `l2update`), so the WS
      connected fine (no connectivity error) and just received zero real data forever — exactly the
      `empty_confirmed`-only symptom. Fix: switched to `level2_batch` (still public, unauthenticated, Coinbase aliases
      it server-side to `level2_50`) — live-verified to emit the IDENTICAL `snapshot`/`l2update` message shape already
      parsed, so no parsing logic changed, only the subscribed channel name (3 call sites: `_open_and_subscribe`/
      `subscribe`/`unsubscribe`). Also added `error`-frame logging so a future rejected subscribe is never silent again
      (was the actual reason this bug went undetected). `level2_batch`/`level2_50` caps at top 50 levels/side (not
      uncapped like the old `level2`) — irrelevant here since `depth_of_book_10` only slices 10. New regression test
      (`test_error_frame_logged_not_silently_dropped`) + all 39 existing connector tests pass.
- [x] ✅ [CODE] P2. Debug the OKX-SWAP `depth_of_book_10` factory branch in `okx_ws.py` — same `empty_confirmed`-only
      pattern (438 rows in ~30 min), also OKX-SWAP's first-ever live dispatch on this VM. Repo:
      market-tick-data-service. — **DONE, `market-tick-data-service@52383e877`**: SSH'd into the live production VM
      (`mtds-live-cefi-consolidated-20260809-121034`), confirmed the shard process alive (not crash-looping), IS
      universe resolving all 438 instruments correctly, and a live wire probe subscribing all 438 real OKX instIds in
      one `books`-channel batch works fine (438 subscribe acks, real snapshot/update data flowing) — ruling out
      connectivity, universe-resolution, and batch-size-limit causes (the classes that broke BYBIT-FUTURES/DERIBIT
      respectively). Root cause found by grepping the live shard's OWN log for the actual canonical instrument_ids it
      was handling: production IS-universe hands `_instrument_to_okx_inst_id` ids like `OKX-SWAP:PERPETUAL:0G-USDT@LIN`
      / `OKX-SWAP:PERPETUAL:ADA-USD@INV` (confirmed across hundreds of distinct instruments) — contradicting
      `_build_okx_canonical_id`'s docstring claim that OKX is exempt from the `@LIN`/`@INV` margin marker. The
      `parts[-1]`-only reverse built the WRONG wire `instId` (`"0G-USDT@LIN-SWAP"` — not a real OKX instrument), so
      every subscribe silently matched nothing. Fixed by stripping the marker before building the wire instId (mirrors
      the established `bybit_ws._instrument_to_bybit_symbol` pattern). 2 new regression tests
      (`test_perpetual_strips_lin_margin_marker`/`test_perpetual_strips_inv_margin_marker`); all 113 OKX connector tests
      pass. **Not yet live-verified past deploy** — like the BINANCE-FUTURES/BYBIT-FUTURES/DERIBIT fixes above, this
      needs a VM cycle to pick up the code change before a fresh manifest read can confirm real rows landing. —
      **CORRECTION, 2026-08-09, slot 6, `market-tick-data-service@98fad5ad`**: the `52383e877` fix above only covers the
      OUTBOUND half (`_instrument_to_okx_inst_id` stripping the marker before subscribing) — that alone is INSUFFICIENT.
      `_build_okx_canonical_id` (the INBOUND parse direction, used to turn a real received wire instId back into a
      canonical instrument_id) was never updated to re-attach the `@LIN`/`@INV` marker, so a real received tick's
      canonical id (e.g. `OKX-SWAP:PERPETUAL:0G-USDT`, no marker) never matches the IS-universe-derived buffer key
      (`OKX-SWAP:PERPETUAL:0G-USDT@LIN`, with marker) that `websocket_runner._buffers` is keyed on — `record_tick`'s
      "unknown/dropped instrument silently skipped" path drops every real tick anyway, even though the subscribe itself
      now succeeds. Fixed `_build_okx_canonical_id` to derive the same `@LIN`/`@INV` marker from the quote asset
      (`USD`→`INV`, else `LIN`) on the inbound side too — independently corroborated by
      `tests/market_interface/adapters/cefi/test_tardis_canonical_output.py`'s pre-existing
      `OKX-SWAP:PERPETUAL:BTC-USDT@LIN`/`@INV` expectations (instruments-service side, unrelated to this bug, already
      assumed this exact marker convention). Also added `error`-frame logging to `okx_ws.py` +
      `okx_futures_book_ticker_ws.py`'s shared `_OKXBaseConnector` (covers book_snapshot_5/derivative_ticker/
      depth_of_book_10) so a future rejected subscribe is never silent again (same fix shape as the COINBASE-SPOT todo
      above). **Live-verified without waiting for a VM cycle**: instantiated the real `OKXFuturesDepth10WSConnector`
      class directly against the actual production IS universe (438 real instruments, read live from
      `instruments-store-cefi-prd-central-element-323112`) and drained `stream()` against real
      `wss://ws.okx.com:8443/ws/v5/public` for 15s — **438/438 instruments received real ticks with non-None book
      levels, with received instrument_ids matching the IS-universe buffer keys exactly** (0/438 would match on the
      outbound-only fix alone, since the inbound canonical id never carried the marker). 203 connector tests pass
      (merged/reconciled with the concurrent `52383e877` fix's own 2 regression tests, kept theirs + added coverage for
      the inbound direction). VM cycle to pick up this code in prod is still the one remaining step to confirm
      `capture_status=captured` manifest rows land — same caveat as BINANCE-FUTURES/BYBIT-FUTURES/DERIBIT above.
- [x] ✅ [CODE] P3. Resolve whether `depth_of_book_10` (and its L2-microstructure siblings `queue_position`/
      `order_flow_imbalance`) should be added to
      `unified_api_contracts.internal.domain.market_data_processing.candle_schema.DataType` (feeding MDPS candle
      aggregation the way `book_snapshot_5` does) or whether `websocket_runner.py`'s `_publish_boundary_event` should
      skip data_types outside the MDPS candle-eligible set — currently every flush cycle for all 5 depth_of_book_10
      venues logs a caught-but-noisy `pydantic.ValidationError` traceback. Repo: unified-api-contracts (enum) or
      market-tick-data-service (`live/websocket_runner.py`, caller-side skip). — **DONE 2026-08-09, slot-22,
      `market-tick-data-service@55fac6f5`.** Decision: skip on the caller side, do NOT add to the MDPS enum. Grepped
      MDPS's `CandleAdapterRegistry.register(...)` call sites across the whole repo — every currently-registered
      (asset_group, data_type) pair (trades/book_snapshot_5/derivative_ticker/liquidations/futures_chain/
      options_chain/... across cefi/defi/tradfi/prediction/sports) has a real adapter; `depth_of_book_10` has none and
      none is referenced anywhere in MDPS. It's consumed directly by
      `market_tick_data_service.derived.book_microstructure_compute`/`BookMicrostructureHandler`, not candle-aggregated
      — adding it to the enum would create a phantom candle-eligible type with no adapter ever built for it. Fix:
      `LiveWebsocketRunner._publish_boundary_event` now checks `is_candle_boundary_eligible(self._data_type)` before
      constructing `CandleBoundaryCrossedEvent` and no-ops for ineligible data_types (currently just `depth_of_book_10`
      in practice — `queue_position`/`order_flow_imbalance` are derived-only and never reach this live WS runner as a
      `data_type` param at all). Extracted the eligibility check + the event build/publish/log into
      `_ws_window_helpers.py` (mirrors the existing `record_flush_captured`/`record_flush_failed` extraction in that
      same file) to keep `websocket_runner.py` under the 900-line QG file-size cap — it was exactly at 900 lines
      pre-change, zero slack. New regression test
      `test_flush_window_skips_boundary_publish_for_non_candle_eligible_data_type` (asserts capture/empty manifest
      recording is unaffected, only the boundary-event publish is skipped) + all 39 existing `test_websocket_runner.py`
      tests pass; full repo `quality-gates.sh` green on the committed SHA.

## Progress Log

- **2026-08-09, slot-22**: closed the P3 MDPS-enum todo (the last open item on this doc). See the todo's own entry above
  for the root-cause/decision detail. `archive_exempt: true` is a TEMPORARY bridge for this commit only — this doc is
  genuinely archival-eligible (0 open todos, unlocked) and IS being archived in the immediately-following commit
  (status→resolved + banner + `git mv`); the flip and the archival move are split into two commits per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`'s "never combine the checkbox flip with the
  `git mv` in one commit" rule (this doc's own path is the orchestrator task's `plan_ref`, so `/done`'s M3 check needs
  the flip visible at this still-active path first). The remaining VM-redeploy + re-verify pass across all 5 venues is
  tracked on `/plans/archive/2026_08/cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2, not as a new todo here.

- **2026-08-09, slot 6**: Closed the COINBASE-SPOT `[CODE] P2` todo. Live-verified against the real Coinbase Exchange WS
  API (unauthenticated `level2` subscribe → rejected with an `error` frame the connector never logged) that the root
  cause was a Coinbase API deprecation, not a parsing bug — `level2` now requires auth, `level2_batch` is the
  still-public alternative with an identical message shape. Fixed the 3 subscribe/unsubscribe call sites in
  `coinbase_book_ws.py` + added `error`-frame logging (the actual detection gap) + a regression test. Did not touch the
  other 3 venue-specific todos (BYBIT-FUTURES/DERIBIT/OKX-SWAP) — distinct WS APIs, out of this task's scope; this doc
  stays open for those.
- **2026-08-09, slot-23**: filed after shipping + verifying the dispatcher-wiring fix (deployment-service@28e64163,
  @778ee0e3, Terraform `persist-cefi-depth-of-book-10` topic+subscription applied to prod) end-to-end for
  BINANCE-FUTURES, and discovering the other 4 venues do not yet produce real captured rows. See
  `cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2's Progress Log for the full session narrative.
- **2026-08-09, slot-27**: root cause found + fixed for the DERIBIT `depth_of_book_10` todo, confirmed live against the
  real Deribit WS API (not simulated). `DeribitBookWSConnector._open_and_subscribe`/`subscribe`/`unsubscribe` (the base
  class `DeribitDepth10WSConnector` inherits without override) build ONE combined `public/subscribe` JSON-RPC request
  listing a `book.*` channel for EVERY instrument in the venue's IS-resolved universe. `cefi/DERIBIT`'s real live
  universe resolves to **2,997 instruments** (verified via `read_is_universe_sync` against the live IS bucket) — exactly
  the row count the issue's own `derivative_ticker` evidence cites (one row per instrument, all almost certainly
  `empty_confirmed` for the same underlying reason, not real ticker data — the manifest-write path working is real,
  "capturing real data" was not verified). Live reproduction against `wss://www.deribit.com/ws/api/v2` (public,
  unauthenticated, read-only):
  - A `public/subscribe` request with the full 2,997 real `book.{instrument}.none.20.100ms` channels (131KB payload)
    gets the WHOLE WebSocket connection closed by Deribit's server with close code **1009 (MESSAGE_TOO_BIG)** before any
    response arrives — zero channels ever subscribed.
  - Binary-searching the channel count found Deribit's JSON-RPC layer itself rejects anything above ~700-800 channels in
    one request with a clean `{"error": {"code": -32600, "message": "request entity too large"}}` response (channels
    1-700 subscribed fine; 800+ → the whole batch, not just the excess, is rejected).
  - So `DeribitDepth10WSConnector`'s single-message subscribe-the-whole-universe approach NEVER succeeds against
    DERIBIT's real instrument count — every reconnect attempt resends the identical oversized request and fails
    identically, so the connector never receives a single depth-10 update. (The runner's window/buffer registration
    itself is unaffected — `self._buffers` populates from IS resolution independent of subscribe success — so the "not
    even empty_confirmed" symptom is consistent with `derivative_ticker`'s sibling `DeribitTickerWSConnector` having the
    SAME defect and its 2,997 rows actually being empty, not real data; not independently re-verified against live prod
    capture_status here.)
  - **Fix** (market-tick-data-service, `deribit_book_ticker_ws.py`): batch the channel list into chunks of
    `_MAX_CHANNELS_PER_SUBSCRIBE_MSG = 200` (well under the measured ~700-channel-OK boundary) and send one
    `public/subscribe`/`public/unsubscribe` RPC per chunk instead of one giant request. Applied to BOTH
    `DeribitBookWSConnector` (used by `book_snapshot_5` + inherited by `DeribitDepth10WSConnector`) and
    `DeribitTickerWSConnector` (`derivative_ticker`) — same file, same root-cause pattern, same fix shape
    (findings-triage "in your file → fix in same commit").
  - **Re-verified live post-fix**: instantiated the real `DeribitDepth10WSConnector` class with the actual
    2,997-instrument production IS universe, called `connect()` + drained `stream()` for 12s against live Deribit —
    received **7,344 real depth-10 ticks** (previously 0). `connect()` returns cleanly, WS stays open.
  - Added 2 unit tests (`tests/unit/test_deribit_book_ticker_ws_coverage.py`) asserting `subscribe()` splits a large
    instrument set into multiple `<= _MAX_CHANNELS_PER_SUBSCRIBE_MSG`-sized `public/subscribe` messages, for both
    connector classes. Full existing suite (69 tests) green.
  - **Not yet done**: redeploying the live `mtds-live-cefi-consolidated-*` VM to pick up this fix, and re-verifying real
    `capture_status=captured` manifest rows for DERIBIT `depth_of_book_10` in prod (this repo's fix is code-level; a VM
    cycle deploys it — out of this todo's DETERMINABLE-by-worker-alone scope, the remaining
    BYBIT-FUTURES/COINBASE-SPOT/OKX-SWAP todos on this issue doc still need debugging, and this issue doc should stay
    open until all 4 are resolved + prod-verified).
- **2026-08-09, slot-19**: closed the BYBIT-FUTURES `[CODE] P2` todo. Root cause is upstream of the connector entirely —
  `BybitFuturesDepth10WSConnector` shares its WS subscribe/parse implementation with the WORKING `book_snapshot_5`
  connector (`_BybitBookStateConnector`, differing only in `depth`/`subscribe_depth`), so the WS layer was never the
  bug. `BYBIT-FUTURES` is a UAC-registered Tardis-alias venue routing to the SAME underlying exchange as `BYBIT`;
  instruments-service's batch IS writer only ever persists `instrument_key`s under the PRIMARY venue token (`BYBIT`). A
  shard launched with `venue=BYBIT-FUTURES` looked up an `instruments.parquet` blob under the alias name, found nothing,
  resolved zero instruments, and spun in the empty-universe retry loop — since `_buffers`/`connect()` are both keyed off
  that same resolved set, the connector subscribed to nothing, hence `empty_confirmed` on every flush. Live-checked via
  `VenueMapping` that this alias-mapping bug is BYBIT-FUTURES-specific among the 5 depth10 venues
  (`DERIBIT`/`COINBASE-SPOT`/`OKX-SWAP`/`BINANCE-FUTURES` all resolve to themselves) — consistent with the other 3
  venues needing distinct, connector-specific fixes (subscribe-batching, deprecated-channel, TBD) rather than this same
  root cause. **Fix**: `_resolve_is_lookup_venue()` added to `market_tick_data_service/live/_is_universe.py`, mirroring
  IS's own `TardisReferenceDataAdapter._resolve_instrument_key_venue`; `read_is_universe_sync` resolves the lookup venue
  before building the IS blob path, falling back to the venue unchanged when it has no Tardis alias. Shipped
  `market-tick-data-service@e3bd10b9` (QG green: 10332 passed/28 skipped/1 xpassed repo-wide; new regression test
  `test_is_lookup_venue_resolves_tardis_alias_to_primary_venue` + all 38 `test_websocket_runner.py` tests pass). **Not
  yet done** (same caveat as slot-27's DERIBIT entry): redeploying the live `mtds-live-cefi-consolidated-*` VM to pick
  this fix up and re-verifying real `capture_status=captured` BYBIT-FUTURES `depth_of_book_10` rows in prod — code-level
  fix only; a VM cycle deploys it. This issue doc stays open pending OKX-SWAP (todo still open) + the MDPS-enum P3
  todo + prod re-verification for all 3 fixed venues.
- **2026-08-09, slot 11**: closed the OKX-SWAP `[CODE] P2` todo — the 4th and last of the per-venue debug items (found
  Coinbase + Deribit + Bybit already fixed by other slots concurrently on arrival; my own first attempt independently
  re-derived the identical Coinbase `level2`→`level2_batch` root cause but landed seconds after slot 6's more thorough
  fix — discarded my redundant local commit in favor of the already-landed one, per no-blind-overwrite discipline).
  SSH'd into the live production VM (`mtds-live-cefi-consolidated-20260809-121034`) to get REAL signal instead of
  further static/generic-probe guessing: confirmed the OKX-SWAP shard alive (not crash-looping), IS universe resolving
  all 438 instruments, and a live wire probe subscribing all 438 real OKX instIds in one `books`-channel batch (mirrors
  the exact production shape) works fine — 438 subscribe acks, real book data flowing — ruling out connectivity,
  universe-resolution, and batch-size-limit causes (the classes that broke DERIBIT/BYBIT-FUTURES respectively). Grepped
  the live shard's OWN log for the actual canonical instrument_ids it processes: every one carries an `@LIN`/`@INV`
  margin marker (`OKX-SWAP:PERPETUAL:0G-USDT@LIN`, `OKX-SWAP:PERPETUAL:ADA-USD@INV`, confirmed across hundreds of
  distinct instruments) — contradicting `_build_okx_canonical_id`'s own docstring claim that OKX is exempt from that
  marker. `_instrument_to_okx_inst_id`'s `parts[-1]`-only reverse built the WRONG wire `instId` (`"0G-USDT@LIN-SWAP"` —
  not a real OKX instrument), so every subscribe silently matched nothing, exactly the `empty_confirmed`-only symptom.
  Fixed by stripping the marker before building the wire instId, mirroring the established
  `bybit_ws._instrument_to_bybit_symbol` pattern. Shipped `market-tick-data-service@52383e877` (QG green; 2 new
  regression tests, all 113 OKX connector tests pass). **Not yet live-verified past deploy** — same caveat as every
  other fix in this doc: a VM cycle is needed to pick up the code change, then a fresh manifest read confirms real rows
  landing. **All 4 P2 per-venue debug todos are now code-fixed** (BINANCE-FUTURES already worked;
  BYBIT-FUTURES/DERIBIT/COINBASE-SPOT/OKX-SWAP fixed across `market-tick-data-service@{level2_batch sha}`, `e3bd10b9`,
  `52383e877` + slot-27's Deribit batching fix) — only the P3 MDPS-enum question and a live VM redeploy+re-verify pass
  across all 5 venues remain before this doc (and the parent plan's todo 2) can close.
- **2026-08-09, slot 6**: dispatched the OKX-SWAP `[CODE] P2` todo independently (arrived after slot-11's `52383e877`
  had already landed on origin). Found slot-11's outbound-only fix (`_instrument_to_okx_inst_id` stripping the
  `@LIN`/`@INV` marker before subscribing) was NECESSARY but NOT SUFFICIENT: `_build_okx_canonical_id` (the inbound
  parse direction) still built a marker-less canonical id from a real received wire instId, which never matches the
  `@LIN`/`@INV`-carrying IS-universe buffer key `websocket_runner._buffers` is keyed on — `record_tick` silently drops
  every real tick even after a successful subscribe. Confirmed this independently via a direct live probe (not just
  static analysis): instantiated `OKXFuturesDepth10WSConnector` against the real 438-instrument production IS universe
  and drained `stream()` against real OKX WS for 15s BEFORE applying any fix — 0/438 received instrument_ids matched the
  buffer keys (all real ticks would have been silently dropped by the outbound-only fix alone). Fixed
  `_build_okx_canonical_id` to derive the same marker from the quote asset (`USD`→`INV`, else `LIN`) on the inbound
  side, rebased onto `52383e877` (git rebase conflict on `okx_ws.py`/`test_okx_ws_coverage.py`, resolved by keeping
  slot-11's tests + simpler one-line outbound strip, adding the missing inbound half + my own tests) — same-turn
  re-verification: 438/438 received instrument_ids now match the IS-universe buffer keys exactly, all with real
  (non-None) book levels. Also added `error`-frame logging (`okx_ws.py` trades path + `okx_futures_book_ticker_ws.py`'s
  shared `_OKXBaseConnector`, covering book_snapshot_5/derivative_ticker/depth_of_book_10 uniformly) so a future
  rejected subscribe is never silent again — the same detection gap that let this bug (and the earlier COINBASE-SPOT
  bug) go undetected. Shipped `market-tick-data-service@98fad5ad` (QG green: 203 OKX-connector tests pass). **All 4
  per-venue fixes are now genuinely correct on both directions** (BYBIT-FUTURES/DERIBIT/COINBASE-SPOT already round-trip
  correctly; OKX-SWAP now does too) — the remaining step across all 5 venues is still the VM redeploy+re-verify pass +
  the P3 MDPS-enum question.
