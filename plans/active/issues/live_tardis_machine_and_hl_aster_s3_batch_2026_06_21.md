---
title:
  Live tardis-machine stream-normalized option + HL/ASTER batch via S3 archive (operator-directed, batch-live symmetry)
created: 2026-06-21
source:
  - operator messages 2026-06-21 (tardis normalised / live free / batch-live symmetry / avoid conversion)
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py
  - market-tick-data-service/market_tick_data_service/live/connectors/ (18 per-venue WS connectors)
locked_by: live-defi-rollout
parent_epic: mtds_mdps_master
priority: P2
status: active
---

# Live tardis-machine option + HL/ASTER S3 batch (batch-live symmetry)

Operator 2026-06-21 directed two architecture improvements while reviewing the cefi live + free-venue work. Both are
**live-pipeline / mtds** scope (the `live_pipeline_mtds_mdps_features` + `batch_live_symmetry_master` epics own them).

## 1 — LIVE: add a tardis-machine `stream-normalized` source option (P0, operator-requested)

**Ask:** "for live we should have an OPTION to use tardis-machine because it avoids us having to convert."

**Context (verified in code):** Tardis's value is **normalised** data (uniform `trade`/`book_snapshot_5`/
`derivative_ticker` across every exchange) via **tardis-machine** (Node sidecar; `tardis-dev` npm). Two endpoints:
`replay-normalized` (historical — **billed**, = the 775k cefi Tardis-gated cells) and **`stream-normalized` (real-time —
FREE**, just proxies the exchange WS + normalises). MTDS today does NOT use tardis-machine for live — live runs **18
bespoke per-venue direct-exchange-WS connectors** (`live/connectors/*.py`) that hand-normalise into `ReceivedTick`. The
operator's point: a tardis-machine source gives the SAME normalised schema for ALL venues from ONE sidecar — no
per-venue conversion code to write/maintain.

**Design (proposed):**

- New `TardisMachineWSFeedConnector(WSFeedConnector)` in `market_tick_data_service/live/connectors/` that connects to a
  local tardis-machine `/ws-stream-normalized` (sidecar on the live VM), subscribes
  `(exchange, dataTypes=[trade, book_snapshot_5, derivative_ticker], symbols)`, and yields normalised `ReceivedTick`s
  (tardis-machine already emits the canonical normalised shape → near-zero conversion).
- Register it as an ALTERNATIVE source for any Tardis-covered venue (selected via a
  `--live-source tardis-machine|native` flag or `VM_LIVE_SOURCE` metadata on `launch-mtds-live.sh`), so the per-venue
  connectors stay the default and tardis-machine is opt-in.
- Sidecar: run `tardis-machine` (Node) on the live VM (`setup-data-pipeline-vm.sh` installs+starts it for
  `VM_LIVE_SOURCE=tardis-machine`; free for `stream-normalized` — no API key needed for live, unlike replay).
- **Batch-live symmetry:** the normalised `stream-normalized` schema == the `replay-normalized` (batch) schema → live
  and batch produce identical data_types/fields by construction (the determinism-spine goal).

**Why opt-in, not default:** the per-venue connectors already deliver free normalised live (18 venues shipped); the
tardis-machine option reduces connector maintenance + guarantees batch-live schema identity. Operator wants it
available, not forced.

## 2 — BATCH: enable HL/ASTER via their S3 archive (non-Tardis), in prod canonical (P0)

**Ask:** "in e2e we got HYPERLIQUID/ASTER data right WITHOUT Tardis for at least some data_types — why can't prod do
that in canonical form?"

**Context (verified):** `HyperliquidAdapter` (`market_interface/adapters/onchain_perps/hyperliquid_adapter.py`) fetches
`trades` / `book_snapshot_5` / `derivative_ticker` / funding from the **public `hyperliquid-archive` S3** —
`book_snapshot_5` from 2023-04-15, trades 2025-03-22+ (free; Tardis only fills the small 2024-10-29→2025-03-21 trades
gap). `AsterAdapter` is REST (Binance-compatible). **e2e proved this non-Tardis path works.** So the 48.5k HL/ASTER
free-venue `attempted_failed` cells ARE re-fetchable in prod — the blockers are mechanical:

1. The cefi `--operation download` orchestrator (`engine/orchestrator::_filter_active_venues`) STRIPS HL/ASTER (they're
   `defi` in `VENUE_TO_ASSET_GROUP`) even with explicit `--venues` → the adapter is never reached via the cefi download.
2. No launcher invokes the onchain-perps adapter batch fetch directly.

**Fix (proposed):** a `launch-cefi-onchain-batch.sh` (or un-strip path) that drives
`HyperliquidAdapter.fetch_trades/funding/book/derivative_ticker` + `AsterAdapter` for the HL 2023→26 / ASTER 2024→26
ranges, writing canonical parquets + manifest (`source=hyperliquid/aster`, `pipeline_mode=batch_hyperliquid/aster`),
bypassing the orchestrator defi-strip; requester-pays S3 via `aws-hyperliquid-s3` (minor egress, admin perms). Resolve
the HL/ASTER `cefi`-vs-`defi` `VENUE_TO_ASSET_GROUP` classification so the manifest tag + download-strip agree. Expect
some cells to resolve `attempted_failed→empty_confirmed` (honest absence). Supersedes the mechanism-gap framing in
`cefi_free_venue_historical_refetch_mechanism_2026_06_21.md` (the mechanism EXISTS — the adapter — it just isn't wired
into a prod launcher).

## §2 UPDATE 2026-06-21 — DIAGNOSED + premise corrected (cefi-lane)

The §2 premise ("cefi download STRIPS HL/ASTER because they're defi in VENUE_TO_ASSET_GROUP") is **STALE**: verified
`VENUE_TO_ASSET_GROUP['HYPERLIQUID']=='cefi'` and `['ASTER']=='cefi'` (post UAC 0.30.0). The 48.5k `attempted_failed`
were diagnosed from the consolidated cefi `availability_index.parquet` (read-only, 2026-06-21):

- **pipeline_mode**: `batch_hyperliquid` 30,835 + `batch_aster` 17,675 → these are **BATCH** on-chain-perp cells (the
  HyperliquidAdapter S3 archive / AsterAdapter REST path), **NOT** the cefi-live path.
- **error_reason**: `UNCLASSIFIED_ADAPTER_ERROR` **45,109** + `VENUE_FETCH_FAILED` 3,220 + 181 phantom-no-parquet.
- **data_type**: trades 16,524 / book_snapshot_5 16,522 / derivative_ticker 13,804 / liquidations 1,479.
- (For context HL/ASTER cefi already has captured=15,002 / empty_confirmed=15,226 / expected_unattempted=24,390.)

**Conclusion:** the gap is a **batch on-chain-perp ADAPTER bug** — the HyperliquidAdapter/AsterAdapter batch fetch hits
an error it does NOT classify (violates the "every adapter classifies via UAC `classify_venue_error()`" rule → the
`UNCLASSIFIED_ADAPTER_ERROR` bucket), so the cells never resolve to captured/empty. This is **defi-lane / batch-adapter
owned** (they own `HyperliquidAdapter` + actively run HL S3 batch — a blind cefi re-fetch would COLLIDE). **Next step
(defi-lane, P0):** read a sample `batch_hyperliquid` cell's adapter run.log to root-cause the unclassified error, fix
the adapter's error classification + the underlying fetch, then re-run the batch backfill for the 48.5k range. NOT a
cefi-lane / cefi-live task; the cefi LIVE path is fully fixed (bugs #6/#7/#8, captured rows verified).

## Status

- **Bug #7 (live capture validation) — FIXED + VERIFIED 2026-06-21 (cefi-lane)**: UTL `ManifestWriter.record_captured`
  gained a `validate=False` gate; the live recorder passes it (bookkeeping df; real ticks validated+written by
  `LiveWebsocketTickSink`; `pipeline_mode`+`source` carry provenance). Durably shipped (UTL@`057264fd` +
  mtds@`e6b0f29`).
- **Bug #8 (MissingSourceError) — FIXED + VERIFIED 2026-06-21 (cefi-lane)**: registered `hyperliquid`/`aster` as cefi
  sources on the 5 cefi perp data_types (UAC@`061cfd01`). cefi LIVE HL trades now captured (row_count>0, verified).
- **#1 (tardis-machine live option) — ✅ SHIPPED + QG-GREEN 2026-06-21 (mtds-lane)**: `TardisMachineWSFeedConnector`
  (`market_tick_data_service/live/connectors/tardis_machine_ws.py`) connects to a local tardis-machine
  `stream-normalized` WS (default `ws://localhost:8001/ws-stream-normalized`,
  `MTDS_TARDIS_MACHINE_WS_URL`-configurable), subscribes `(exchange, dataTypes, symbols, withDisconnectMessages)`, and
  maps tardis `trade`/`book_snapshot_5`/ `derivative_ticker` → the EXACT canonical `tick` dict the native connectors
  emit (unit-test asserts key-parity vs `_parse_binance_trade` / `_parse_hyperliquid_l2book` /
  `_parse_hyperliquid_ticker` → batch-live schema identity by construction). Opt-in:
  `--live-source native|tardis-machine` (CLI) / `MTDS_LIVE_SOURCE`|`VM_LIVE_SOURCE` (config), native stays the default
  (zero behaviour change unset); NOT auto-registered in `WS_FEED_CONNECTOR_FACTORIES` (source-selected, not
  venue-keyed). VENUE→tardis-exchange map covers the 10 Tardis-covered cefi venues. Launcher:
  `launch-mtds-live.sh --live-source` → `VM_LIVE_SOURCE` metadata; `setup-data-pipeline-vm.sh` installs Node +
  `tardis-machine` + starts the FREE stream-normalized sidecar on :8001 when `VM_LIVE_SOURCE=tardis-machine`, passing
  `--live-source tardis-machine` to the CLI. Shipped: mtds@`0aa6163` (connector + handler dispatch + config +
  `--live-source` CLI arg + 24-test `test_tardis_machine_ws_connector.py`, QG-green) + deployment-service@`b5246a6`
  (launcher + VM setup, QG-green). Both on `origin/live-defi-rollout`.
- **#2 (HL/ASTER batch) — ✅ HANDLER + LAUNCHER SHIPPED + PROVEN + QG-GREEN 2026-06-21**: instead of patching the
  orchestrator-routed `HyperliquidAdapter`/`AsterAdapter` (whose `fetch_trades` S3-dated branch returns `[]`
  "delegated to MTDS" → the unclassified-error gap), built a **dedicated batch CLI handler** `OnchainPerpBatchHandler`
  (`market_tick_data_service/cli/handlers/onchain_perp_batch_handler.py`, op `collect-onchain-perp-batch`) that drives
  `HyperliquidS3Downloader` (requester-pays S3, `aws-hyperliquid-s3` secret) + `AsterAdapter` REST **directly**,
  bypassing the orchestrator DeFi-strip. Writes cefi canonical parquet via the orchestrator `PartitionedTickWriter`
  (byte-identical paths → Batch=Live) + manifest captured/empty/failed rows via `ManifestWriter` with
  `asset_group=cefi`, `source=hyperliquid/aster`, `pipeline_mode=batch_hyperliquid/batch_aster` — matching the failed
  cells' provenance so they resolve `attempted_failed → captured`. data_types: `trades` / `book_snapshot_5` /
  `derivative_ticker` (funding inline); ASTER `book_snapshot_5` = honest absence (no historical depth endpoint); HL
  liquidations out of scope. Shard-level isolation + UAC `classify_venue_error` + `ADAPTER_FETCH_FAILED`.
  **PROVEN on a real S3 fetch**: HL `derivative_ticker` BTC 2023-05-21 → **1440 rows captured**, canonical parquet at
  `gs://market-data-tick-cefi-prd-…/raw_tick_data/by_date/day=2023-05-21/pipeline_mode=batch_hyperliquid/asset_group=cefi/venue=HYPERLIQUID/instrument_type=perpetual/data_type=derivative_ticker/BTC-PERP.parquet`
  + a **captured manifest row** in `_index/availability_index.parquet`
  (`HYPERLIQUID | derivative_ticker | BTC-PERP | captured | source=hyperliquid | batch_hyperliquid | asset_group=cefi`).
  14 unit tests; ruff/basedpyright/pytest green on touched files. Shipped: mtds@`1e4dfb2` (handler + cli/main.py op-map
  + `--onchain-perp-symbols`/`--onchain-perp-data-types` args + tests) + deployment-service@`b04cfcc` (launcher
  `VM_OPERATION=download`→`collect-onchain-perp-batch` + `cefi-hl-aster-backfill` VM_TASK routing in
  `setup-data-pipeline-vm.sh`). Both on `origin/live-defi-rollout`. **REMAINING (operator/infra)**: run the launcher
  over the HL 2023→26 / ASTER 2024→26 ranges to backfill all 48.5k cells to completion (fire-and-verify VMs).

## §3 — funding_rate is a FIELD in derivative_ticker (data-model note, operator 2026-06-21)

Operator: "isn't funding rate inside derivative ticker?" — **Confirmed.** HL `derivative_ticker` (from `activeAssetCtx`,
`hyperliquid_ticker_ws.py`) carries `funding_rate` + `predicted_funding_rate` + `open_interest` + `mark_price` +
`index_price` in ONE snapshot. So funding arrives 3 ways: (1) `derivative_ticker.funding_rate` field, (2) standalone
`(cefi, funding_rate)` data_type, (3) standalone `(defi, perp_funding)` REST `candleSnapshot` leg. (2) is **largely
redundant** with (1); (3) is justified by the carry archetype's distinct cadence/semantics (realized-vs-predicted,
funding-interval granularity — `perp_funding_data_semantics_and_cadence_2026_06_16.md`).

**Consequence for #2 (HL/ASTER batch):** wiring the `derivative_ticker` batch fetch resolves the 13,804 failed
`derivative_ticker` cells AND delivers funding inline — no separate funding fetch needed for the ticker snapshot. The
batch onchain-perp data_types to wire are therefore: `trades`, `book_snapshot_5`, `derivative_ticker` (funding
included). **Possible cleanup (P2, operator-decision):** retire the standalone `(cefi, funding_rate)` data_type in
favour of `derivative_ticker.funding_rate` (has downstream consumers — needs an audit before removal; do NOT drop
unilaterally).

## §4 — bug#9: CEX live-source provenance gap (surfaced by the tardis-machine smoke, 2026-06-21)

Launching the tardis-machine smoke on `cefi:BINANCE-FUTURES:trades --live-source tardis-machine` FAILED at startup:
`ValueError: No PipelineMode for source 'tardis' in mode 'live'`. **Root cause (NOT tardis-specific — affects native CEX
live too):** the live writer resolves pipeline_mode via `live_pipeline_mode_for_venue` → `live_source_for_venue(asset_group,
venue, data_type)` (mode-agnostic) → for a CEX venue with no venue→vendor entry it defaults to `SOURCE_PRIORITY[(cefi,
trades)][0] = "tardis"` → `pipeline_mode_for_source("tardis", LIVE)` raises because **tardis is batch-only** (academic
licence blocks CeFi live/replay; `SOURCE_MODE_CAPABILITY[tardis]={batch}`). So **any CEX venue (binance/okx/bybit/kraken/
deribit) live capture — native connector OR tardis-machine — currently dies at preflight**; CEX native live was simply
never run before so it never surfaced. (HYPERLIQUID/ASTER work because `live_source_for_venue` returns their own vendor,
which has LIVE_<vendor> + is a registered cefi source.)

**The architecture tension:** a CEX venue's BATCH source is `tardis` (archive) but its LIVE source must be the EXCHANGE
itself (`binance` live WS → `live_binance`). `live_source_for_venue` returns ONE source per venue (mode-agnostic), so it
cannot today say "tardis for batch, binance for live." The fix (P1, careful — provenance layer; the code SSOT warns
SOURCE_PRIORITY[0] mis-stamping caused the VX/CFE incident):
1. Add `LIVE_<vendor>` PipelineMode members for the CEX vendors that lack them (`LIVE_BINANCE` exists; check OKX/BYBIT/
   KRAKEN/DERIBIT) + `SOURCE_MODE_CAPABILITY[<vendor>] ⊇ {live}`.
2. Register the CEX vendors as cefi LIVE sources for trades/book_snapshot_5/derivative_ticker (additive to SOURCE_PRIORITY;
   tardis stays index-0 BATCH primary).
3. Make `live_source_for_venue` mode-aware (or add a venue→live-vendor map) so a CEX venue resolves to its exchange vendor
   in LIVE mode while staying `tardis` in BATCH — so `batch_tardis` (archive) and `live_binance` (exchange) coexist on the
   same shard, source column distinguishing them (Live=batch schema, different provenance — which is correct: the live
   data genuinely comes from the exchange, the historical from the Tardis archive).

**Tardis-machine smoke PROVEN instead on `cefi:HYPERLIQUID:derivative_ticker --live-source tardis-machine`** (VM
`mtds-live-cefi-hyperliquid-derivative-ticker-20260621-225252`) — HL resolves cleanly (`hyperliquid` vendor, LIVE_HYPERLIQUID,
registered source), so it validates the tardis-machine connector + Node sidecar + dispatch + capture end-to-end. The CEX
flagship case is gated on the §4 fix above (not on the tardis-machine code, which is correct).
