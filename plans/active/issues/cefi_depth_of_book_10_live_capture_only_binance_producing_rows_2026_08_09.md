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
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [deployment-service, market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, depth_of_book_10, live-capture, data-correctness, pubsub, websocket]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/active/l2_book_microstructure_capture_2026_07_13.md,
  ]
created: "2026-08-09"
author: slot-23-infra
assigned_vm: planning
parent_epic: infrastructure_master
priority: P2
locked_by:
resolved_by:
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

- [ ] [CODE] P2. Debug why `BybitFuturesDepth10WSConnector` (bybit_futures_book_ticker_ws.py) produces only
      `empty_confirmed` manifest rows on live WS traffic despite the venue's other connectors (trades/book_snapshot_5/
      derivative_ticker) capturing real data on the same VM in the same window — compare against the REST-verified book
      depth from `book_microstructure_connectivity_check.py` to isolate whether the WS subscription/parse path is
      silently dropping real depth updates. Repo: market-tick-data-service.
- [ ] [CODE] P2. Debug why `DeribitDepth10WSConnector` (deribit_book_ticker_ws.py) produces ZERO `depth_of_book_10`
      manifest rows at all (not even `empty_confirmed`) despite `derivative_ticker` capturing 2,997 rows on the same
      venue/VM/window — check whether the connector even registers a flush-triggering instrument window for this
      data_type. Repo: market-tick-data-service.
- [ ] [CODE] P2. Debug why `CoinbaseDepth10WSConnector` (coinbase_book_ws.py) produces only `empty_confirmed` rows (424
      in ~30 min) — this is COINBASE-SPOT's first-ever live dispatch on this VM (no prior working baseline for
      comparison), so also verify the venue's `level2` subscription itself is actually receiving book-diff messages, not
      just that the depth-10 slicing logic runs. Repo: market-tick-data-service.
- [ ] [CODE] P2. Debug the OKX-SWAP `depth_of_book_10` factory branch in `okx_ws.py` — same `empty_confirmed`-only
      pattern (438 rows in ~30 min), also OKX-SWAP's first-ever live dispatch on this VM. Repo:
      market-tick-data-service.
- [ ] [CODE] P3. Resolve whether `depth_of_book_10` (and its L2-microstructure siblings `queue_position`/
      `order_flow_imbalance`) should be added to
      `unified_api_contracts.internal.domain.market_data_processing.candle_schema.DataType` (feeding MDPS candle
      aggregation the way `book_snapshot_5` does) or whether `websocket_runner.py`'s `_publish_boundary_event` should
      skip data_types outside the MDPS candle-eligible set — currently every flush cycle for all 5 depth_of_book_10
      venues logs a caught-but-noisy `pydantic.ValidationError` traceback. Repo: unified-api-contracts (enum) or
      market-tick-data-service (`live/websocket_runner.py`, caller-side skip).

## Progress Log

- **2026-08-09, slot-23**: filed after shipping + verifying the dispatcher-wiring fix (deployment-service@28e64163,
  @778ee0e3, Terraform `persist-cefi-depth-of-book-10` topic+subscription applied to prod) end-to-end for
  BINANCE-FUTURES, and discovering the other 4 venues do not yet produce real captured rows. See
  `cefi_satellite_ao_dispatch_batch13_2026_08_09.md` todo 2's Progress Log for the full session narrative.
