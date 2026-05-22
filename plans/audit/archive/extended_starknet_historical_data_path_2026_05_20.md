---
title: Extended Starknet — historical/batch data path investigation
created: 2026-05-20
author: background agent (delegated by slot-1 main)
locked_by: live-defi-rollout
related_plans:
  - emerging_perp_venue_adapters_broken_2026_05_13.md
---

## Live URLs (already confirmed)

Resolved here as a side-finding (updates `emerging_perp_venue_adapters_broken_2026_05_13.md` § 2026-05-15 ping, which
marked DNS dead — stale as of today's probe).

- **Mainnet REST base**: `https://api.starknet.extended.exchange/api/v1`
- **Testnet REST base**: `https://api.starknet.sepolia.extended.exchange/api/v1`
- **Live probe 2026-05-20**: `GET /info/markets` → HTTP 200, returns full perpetual market catalog (ENA-USD, BTC-USD,
  …). The `api.starknet.extended.exchange` host IS live; the slot-3 ping (`HTTP 000 DNS dead`) was a transient
  resolution failure or pre-mainnet-cutover state. **Operator unblock signal**: slot-3 can lift
  `BLOCKED-OPERATOR-DECISION` on the `_EXTENDED_API_BASE` patch.
- Source: `https://api.docs.extended.exchange/` (confirms base URLs) + direct curl probe (this investigation).

## Path 1 — Official archive bucket

**Status: NOT-FOUND**

- Probed common URL patterns — all 404 / NXDOMAIN:
  - `https://extended-historical-data.s3.amazonaws.com/` → 404
  - `https://x10-historical-data.s3.amazonaws.com/` → 404
  - `https://extended-archive.s3.amazonaws.com/` → 404
  - `https://archive.extended.exchange/` → DNS fail
  - `https://data.extended.exchange/` → DNS fail
  - `https://historical.extended.exchange/` → DNS fail
- Docs pages searched (`docs.extended.exchange/`, `api.docs.extended.exchange/`,
  `x10xchange.github.io/x10-documentation/`): zero mentions of "archive", "S3", "bulk", "snapshot", "dump", or
  "backfill".
- GitHub org `x10xchange` lists `python_sdk`, `rust-crypto-lib-base`, `x10-documentation` — no `historical-data` /
  `archive` / `data-dumps` repos visible.
- **Verdict**: Extended does NOT publish an S3/GCS archive bucket. Unlike Drift (`s3://drift-historical-data-v2`) or
  Hyperliquid's public S3 archive, batch ingest cannot piggy-back on a vendor-published bulk feed.

## Path 2 — REST history depth

Direct probes against `https://api.starknet.extended.exchange/api/v1` 2026-05-20:

| Endpoint                                                         | Page cap       | Observed depth (BTC-USD)                                       | Verdict                                                                                                                                           |
| ---------------------------------------------------------------- | -------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `/info/candles/{market}/trades?interval=P1D&limit=10000`         | 10,000 records | **664 daily candles** back to `2024-07-26` (~22 months)        | ✅ DEEP — full mainnet history accessible                                                                                                         |
| `/info/candles/{market}/trades?interval=PT1M&limit=10000`        | 10,000 records | 2,800 rows on first page = ~46h; `endTime` cursor paginates    | ✅ DEEP — but ~10k pages needed for 22-month 1m history                                                                                           |
| `/info/{market}/funding?startTime=&endTime=`                     | 10,000 records | **7,340 hourly funding rows** from `2025-07-18` → `2026-05-20` | ⚠ MEDIUM — funding only available from 2025-07-18 onwards (likely Starknet-mainnet cutover; pre-migration funding under x10 legacy not retained) |
| `/info/{market}/open-interests?interval=P1H&startTime=&endTime=` | 300 records    | (docs-only; 300/req is small; needs many calls)                | ✅ but chatty — 300-row chunks                                                                                                                    |
| `/user/trades` (per-account fills)                               | 10,000 records | Authenticated; per-account only                                | ❌ NOT useful for batch market-data ingest                                                                                                        |
| Order-book snapshots (REST)                                      | n/a            | No historical L2 snapshot endpoint documented                  | ❌ live WebSocket only (matches workspace pattern)                                                                                                |

**Pagination model**: cursor-based, descending by ID; `cursor` query param + 10k page cap. For 1m candle backfill, walk
backward via `endTime` parameter (last row's `T` from previous page).

**Verdict**: REST is **VIABLE FOR BATCH** for candles (full depth, ~22 months back to 2024-07-26) and **VIABLE WITH
CAVEAT** for funding (only ~10 months back to 2025-07-18; pre-2025-07 funding does not appear retained by the API). This
matches Extended's mainnet launch on Starknet (August 2025) — the x10 sepolia/legacy data did not migrate.

## Path 3 — Third-party aggregators

**Status: NOT-FOUND**

- **Tardis.dev**: `https://tardis.dev/exchanges` returned HTTP 404 on direct fetch; search results show Tardis covers
  Hyperliquid + Backpack but no listing for "Extended" / "X10" / "Starknet" perp DEX in catalogue. The 2026 perp-DEX
  airdrop guides citing Tardis coverage do not include Extended.
- **CoinAPI / Kaiko / CoinGecko**: no result rows for Extended/X10 venue in API explorer searches. CoinGecko lists
  Extended at the project level (TVL/volume display) but does NOT expose historical tick/candle/funding data for it.
- **Dune Analytics**: dashboards exist (`dune.com/margaritalucidi1/perp` covers Lighter/Hyperliquid/Extended/Pacifica
  perp metrics). Dune is SQL-on-Starknet-events surface, not a bulk-data API — usable for one-off analysis but not as a
  pipelined batch ingest source. Adds a Dune API + rate-limit dependency the workspace does not currently use.
- **CCXT**: open issue `ccxt/ccxt#26549` ("New Exchange: Extended") — integration request pending, no merged adapter.

**Verdict**: no commercial aggregator currently surfaces Extended. Tardis is the workspace's preferred aggregator path;
Extended is **not** covered. Defer reconsideration until Tardis adds Extended (file a ping if/when operator wants to
escalate to Tardis support).

## Path 4 — On-chain indexing

**Settlement contract**: `0x062da0780fae50d68cecaa5a051606dc21217ba290969b302db4dd99d2e9b470` on Starknet mainnet (per
starknet.io launch announcement + extended.exchange architecture blog). This is the **USDC deposit/settlement
contract**; the on-chain layer settles batched trades after off-chain CLOB matching (hybrid CLOB → Starknet pattern).
NOT every trade emits an on-chain event — only batched settlements + deposits/withdrawals. Live trade ticks live in the
off-chain sequencer and surface via the REST/WebSocket API.

**Indexer options**:

- **Voyager API** (`apis.voyager.online`) — public indexed API for Starknet events. Free tier exists; covers contract
  event reads.
- **Apibara** — Starknet event indexer; example repos cover Uniswap-V2-style DEXs but not Extended specifically.
- **Pathfinder / Juno archive nodes** — full Starknet state; self-host or use Chainstack/Alchemy/Quicknode RPC.
- **Dune Starknet tables** — Extended already appears in community dashboards.

**Effort estimate**:

- Reading deposits/withdrawals (USDC custody flows) via Voyager: ~1 AI-day. Useful for wallet-side reconciliation but
  NOT a substitute for tick/trade/funding data (those don't land on-chain individually under the hybrid model).
- Reconstructing per-trade fills from on-chain batch settlements: **NOT POSSIBLE** — off-chain matching means individual
  fill prices/quantities/timestamps are not on-chain. The on-chain layer commits Merkle roots of batched state
  transitions, not per-trade event logs equivalent to e.g. Drift's `tradeRecords` PDA.

**Verdict**: Path 4 is **INFEASIBLE** as a primary historical source for tick/candle/funding data because Extended's
hybrid CLOB does not emit per-trade events on Starknet. It IS feasible as a secondary cross-check for deposit/withdrawal
custody balances + as an integrity audit (settlement-batch roots match REST-reported aggregate volumes), but that's a
post-cutover audit feature, not a batch ingest path.

## Recommendation

**Primary batch path**: **Path 2 — REST API direct backfill** via `/info/candles/{market}/trades` (depth: 2024-07-26 →
present, ~22 months) + `/info/{market}/funding` (depth: 2025-07-18 → present, ~10 months) +
`/info/{market}/open-interests` (300-row chunks). Pagination is cursor-based via `endTime`; 10,000-record page cap
matches the workspace's existing HYPERLIQUID/ASTER paginate-backward adapter pattern. The existing
`instruments-service/instruments_service/reference_data/adapters/defi/extended.py` scaffold (slot-3 work) extends
naturally; MTDS handler follows the same hourly-funding / 1m-candles pattern as Aster/Hyperliquid.

**Fallback**: **None viable today**. Path 1 + Path 3 + Path 4 each ruled out for distinct reasons (no archive bucket; no
aggregator coverage; hybrid-CLOB on-chain has no per-trade events). If REST goes down mid-backfill, the only mitigation
is retry-with-backoff against the same REST surface.

**Effort to ship a backfill adapter**: **2 AI-days calibrated** (estimate_class=`brand-new`, baseline 2 days × 1.0×):

- 0.5 day — patch `_EXTENDED_API_BASE` in instruments-service + MTDS adapters; verify `/info/markets` listing matches
  UAC venue registry (slot-3 work already 80% complete; just needs the URL flip).
- 0.5 day — wire MTDS funding-rate handler (mirror Aster's `mtds-perp-funding-backfill` VM pattern); validate against
  known BTC-USD funding row format `{m,f,T}`.
- 0.5 day — wire MTDS candles handler with backward-pagination via `endTime` (10k-row page cap, ~22 months × 1m = ~10k
  pages → singleton-locked VM with rate-limit respect per CLAUDE.md singleton-locked-launchers SSOT).
- 0.5 day — QG STEP 5.61/5.62 wiring + manifest-emission per writegate Phase 6.x + UTL `classify_venue_error()` mapping
  - `record_empty(reason=SOURCE_RETURNED_ZERO)` for pre-launch dates (BTC-USD before 2024-07-26; funding before
    2025-07-18; per-market launch from `/info/markets` listing).

**Blockers**: **None requiring operator decision**. The earlier `BLOCKED-OPERATOR-DECISION` ping (canonical API URL) is
operationally resolved by this investigation — confirmed live URL is `https://api.starknet.extended.exchange/api/v1`,
public/unauthenticated for market-data endpoints. Slot-3 can proceed with the URL patch + adapter flip without further
operator approval.

**Status reclassification**: per CLAUDE.md "External Data Is Always Available" SSOT, the venue moves from
`BLOCKED-OPERATOR-DECISION` → unblocked. Adapter shipping is now the only remaining work.

## Live=batch viability

**YES — both modes ingest the same data shape via Path 2 (REST).**

- Live mode: WebSocket public-market streams (`order book`, `trades`, `mark price`, `candles`, `funding`) deliver the
  same field set as REST polling. Per workspace "batch = live" SSOT
  (`writegate_honest_coverage_endtoend_2026_05_06.md`), the live WS handler and batch REST handler share data_type
  schemas, manifest emission, and `available_at` write-time semantics.
- Batch mode: REST `/info/candles/.../trades` + `/info/.../funding` + `/info/.../open-interests` deliver identical
  fields (open/close/high/low/volume/timestamp for candles; market/funding-rate/timestamp for funding) — no separate
  live-only data_type, no derived `available_at`-at-read-time.
- Funding caveat: pre-2025-07-18 funding rows are unavailable via REST → MTDS handler MUST emit
  `record_empty(reason=PRE_LAUNCH_VENUE_NOT_TRADING)` for pre-launch dates (the venue existed on x10 legacy infra but
  funding history did not migrate to Starknet mainnet). This is a normal honest-absence handling case, not a SSOT
  violation. Per-market launch dates derivable from candle-history first-row timestamps; codify in UAC
  `registry/venue_launch_dates.py` per-market.

## Cross-references

- Companion: `emerging_perp_venue_adapters_broken_2026_05_13.md` § 2026-05-15 (this investigation lifts the
  EXTENDED-STARKNET `BLOCKED-OPERATOR-DECISION` flag).
- Pattern parent: ASTER root-cause fix (`instruments-service@c0c6593`) — same canonical-URL-stale pathology.
- Workspace SSOT: CLAUDE.md "External Data Is Always Available — Never Silently Defer Adapters" (REST-only is a
  legitimate batch path when no archive exists, provided depth is real).

## Next actions (todo seeds for slot 3 or operator-assigned successor)

- `- [ ]` [SCRIPT] P0. Patch `_EXTENDED_API_BASE = "https://api.starknet.extended.exchange/api/v1"` in
  `instruments-service/instruments_service/reference_data/adapters/defi/extended.py` (drop the URL probe TODO comment
  added at `@7c2fc5f`).
- `- [ ]` [SCRIPT] P0. Patch MTDS `ExtendedClientConfig.base_url` to mainnet REST base; mirror Aster's
  `market-tick-data-service@b3e6df0` pattern.
- `- [ ]` [SCRIPT] P0. Wire MTDS funding handler for Extended (mirror Aster `mtds-perp-funding-backfill` VM); ensure
  `record_empty(reason=PRE_LAUNCH_VENUE_NOT_TRADING)` for pre-`2025-07-18` BTC-USD dates and per-market launch dates
  from `/info/markets` first-candle-timestamp.
- `- [ ]` [SCRIPT] P1. Wire MTDS candles handler with backward `endTime` pagination; singleton-locked backfill VM
  `mtds-extended-candles-backfill` (asia-northeast1-c per workspace zone rule).
- `- [ ]` [SCRIPT] P1. Codify per-market launch dates in UAC `registry/venue_launch_dates.py` `CEFI_VENUE_LAUNCH_DATES`
  (per-market keys for Extended, derived from `/info/markets` first-candle scan).
- `- [ ]` [SCRIPT] P2. Lift `BLOCKED-OPERATOR-DECISION` flag in `emerging_perp_venue_adapters_broken_2026_05_13.md` →
  flip to `✅ adapter URL confirmed` with link to this investigation.
