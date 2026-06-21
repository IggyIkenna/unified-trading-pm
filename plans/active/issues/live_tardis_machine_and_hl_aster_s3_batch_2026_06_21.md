---
title: Live tardis-machine stream-normalized option + HL/ASTER batch via S3 archive (operator-directed, batch-live symmetry)
created: 2026-06-21
author: cefi-lane (/autonomous, Opus) — operator architecture direction
source:
  - operator messages 2026-06-21 (tardis normalised / live free / batch-live symmetry / avoid conversion)
  - market-tick-data-service/market_tick_data_service/market_interface/adapters/onchain_perps/hyperliquid_adapter.py
  - market-tick-data-service/market_tick_data_service/live/connectors/ (18 per-venue WS connectors)
locked_by: live-defi-rollout
parent_epic: mtds_mdps_master
---

# Live tardis-machine option + HL/ASTER S3 batch (batch-live symmetry)

Operator 2026-06-21 directed two architecture improvements while reviewing the cefi live + free-venue work. Both are
**live-pipeline / mtds** scope (the `live_pipeline_mtds_mdps_features` + `batch_live_symmetry_master` epics own them).

## 1 — LIVE: add a tardis-machine `stream-normalized` source option (P0, operator-requested)

**Ask:** "for live we should have an OPTION to use tardis-machine because it avoids us having to convert."

**Context (verified in code):** Tardis's value is **normalised** data (uniform `trade`/`book_snapshot_5`/
`derivative_ticker` across every exchange) via **tardis-machine** (Node sidecar; `tardis-dev` npm). Two endpoints:
`replay-normalized` (historical — **billed**, = the 775k cefi Tardis-gated cells) and **`stream-normalized` (real-time
— FREE**, just proxies the exchange WS + normalises). MTDS today does NOT use tardis-machine for live — live runs
**18 bespoke per-venue direct-exchange-WS connectors** (`live/connectors/*.py`) that hand-normalise into `ReceivedTick`.
The operator's point: a tardis-machine source gives the SAME normalised schema for ALL venues from ONE sidecar — no
per-venue conversion code to write/maintain.

**Design (proposed):**
- New `TardisMachineWSFeedConnector(WSFeedConnector)` in `market_tick_data_service/live/connectors/` that connects to a
  local tardis-machine `/ws-stream-normalized` (sidecar on the live VM), subscribes `(exchange, dataTypes=[trade,
  book_snapshot_5, derivative_ticker], symbols)`, and yields normalised `ReceivedTick`s (tardis-machine already emits
  the canonical normalised shape → near-zero conversion).
- Register it as an ALTERNATIVE source for any Tardis-covered venue (selected via a `--live-source tardis-machine|native`
  flag or `VM_LIVE_SOURCE` metadata on `launch-mtds-live.sh`), so the per-venue connectors stay the default and
  tardis-machine is opt-in.
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

## Status

- **Bug #7 (live capture validation) — FIXED 2026-06-21 (cefi-lane)**: `ManifestWriter.record_captured` gained a
  `validate=False` gate; the live recorder passes it (bookkeeping df; real ticks validated+written by
  `LiveWebsocketTickSink`; `pipeline_mode`+`source` carry provenance). This unblocks CAPTURE for BOTH live sources
  (per-venue connectors AND the future tardis-machine source) — foundational for #1.
- #1 + #2 are P0 follow-ups for the live-pipeline / mtds lane.
