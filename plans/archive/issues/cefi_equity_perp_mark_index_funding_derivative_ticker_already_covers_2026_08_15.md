---
doc_type: issue
title:
  CeFi equity-perp indexPrice/markPrice/fundingRate capture — existing derivative_ticker data_type already covers it
  (design collision, not a gap)
summary: >-
  A dispatched batch-19 todo asks to capture Binance/OKX/Bybit indexPrice+markPrice+fundingRate for the equity-perps as
  a NEW first-class MTDS data_type. Investigation found the existing `derivative_ticker` data_type (already first-class,
  already registered in EXPECTED_COVERAGE for all three venues) already fully populates mark_price, index_price, and
  funding_rate for all three venues via already-wired live WS connectors — building a standalone data_type would
  duplicate storage for an identical-source signal, the same anti-pattern this repo's own perp_funding_handler.py
  precedent (ASTER/LIGHTER-ZKSYNC) was written to avoid. One open question (whether capture is actually dispatched for
  the equity-perp symbol subset specifically) could not be settled via a bounded GCS probe this session and needs a
  manifest-level follow-up, not a new build.
assigned_vm: planning
created: "2026-08-15"
author: slot-7-backend_engineer
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, derivative_ticker, funding_rate, mark_price, index_price, equity-perp, dedup]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
parent_epic: cefi_master
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    unified-api-contracts/unified_api_contracts/registry/expected_coverage.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py,
  ]
priority: P2
source:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# CeFi equity-perp indexPrice/markPrice/fundingRate — existing `derivative_ticker` already covers it

> **ARCHIVED 2026-08-15 (slot-9)** — both todos done: the `[OPERATOR]` decision resolved via BLOCKED Q BLK-483148f6
> (decision A, already-satisfied), and the `[CODE]` manifest-level verification confirmed no enumeration gap (see the
> 2026-08-15 Progress Log entry below for full evidence). No open work remains. Original body preserved below.

## What I found

Dispatched todo (`cefi_satellite_ao_dispatch_batch19_2026_08_13.md`, sourced from
`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` Phase 1b): "market-tick-data-service — capture
Binance/OKX/Bybit `indexPrice` + `markPrice` + `fundingRate` for the equity-perps as a first-class data_type ... These
ride the existing CeFi premiumIndex/funding endpoints."

Investigation (market-tick-data-service + unified-api-contracts, this session) found this is **already implemented**,
not a gap — via the EXISTING `derivative_ticker` data_type (already a first-class MTDS data_type, already in
`EXPECTED_COVERAGE["BINANCE-FUTURES"]`,
`unified-api-contracts/unified_api_contracts/registry/expected_coverage.py:75-81`, and the OKX-FUTURES/SWAP + Bybit
entries nearby):

- **Binance**: `market-tick-data-service/market_tick_data_service/live/connectors/binance_futures_book_ticker_ws.py` —
  `BinanceFuturesTickerWSConnector` (line ~357) subscribes `<sym>@markPrice@1s` (Binance's own premiumIndex WS stream);
  `market_tick_data_service/market_interface/adapters/binance.py:180-191` `normalize_derivative_ticker()` parses
  `BinanceMarkPriceUpdate` into `CanonicalDerivativeTicker` with `mark_price`, `index_price`, `funding_rate`,
  `next_funding_timestamp` fully populated (not partial).
- **OKX**: `market_tick_data_service/live/connectors/okx_futures_book_ticker_ws.py` + `okx_futures_ws.py:551-655` —
  `derivative_ticker` via the `tickers` channel; UAC
  `unified_api_contracts/unified_api_contracts/external/okx/normalize.py:236-261` `normalize_okx_derivative_ticker()`
  extracts `mark_price`/`index_price` from `info.markPx`/`info.idxPx` + funding from `OKXFundingRate`.
- **Bybit**: `market_tick_data_service/live/connectors/bybit_futures_book_ticker_ws.py` (line ~358) —
  `derivative_ticker` via the `tickers.<SYMBOL>` channel; UAC
  `unified_api_contracts/unified_api_contracts/external/bybit/normalize.py:217-242`
  `normalize_bybit_derivative_ticker()` extracts `markPrice`/`indexPrice`/`fundingRate` straight from the ticker `info`
  dict.

All three venues' `derivative_ticker` capture is generic across the whole venue-shard's instrument universe (not
symbol-type-filtered) — there is no code path that would exclude the equity-perp symbols (COIN/MSTR/PLTR/SPXUSDT/etc)
from a capture that already runs for the venue's other perpetuals.

This directly parallels an existing precedent already coded in this repo: `perp_funding_handler.py`'s module docstring
explains ASTER/LIGHTER-ZKSYNC stay retired from standalone `perp_funding` capture because their funding rate is
"code-proven byte-identical to derivative_ticker's embedded funding_rate field (same underlying fetch)" — restoring a
standalone capture there "would duplicate storage, not add a second independent signal." The same reasoning applies
here: Binance/OKX/Bybit's `indexPrice`/`markPrice`/`fundingRate` are the SAME premiumIndex/tickers-channel fetch already
landing in `derivative_ticker`'s `mark_price`/`index_price`/`funding_rate` columns — a new standalone data_type would be
a second signal from the identical source, not new coverage.

## Why it matters

The plan todo's literal wording ("as a first-class data_type") reads as calling for NEW capture/write-path code. Per
`backend_engineer.md`'s craft north-star ("reach for the RIGHT existing primitive before writing your own... never
reinvent a wheel the workspace ships"), building a second parallel data_type here would be the anti-pattern the
codebase's own `perp_funding_handler.py` precedent was written to avoid — duplicate GCS storage + a second manifest
shard for a field-for-field identical signal, with no independent value.

**One genuine open question I could NOT settle this session** (bounded-scope GCS verification, not a code question):
whether the live `derivative_ticker` WS capture is actually SCHEDULED/DISPATCHED in production for the specific CeFi
equity-perp symbol set (COIN/MSTR/PLTR/... + index perps SPXUSDT/NAS100/XAUUSDT) on BINANCE-FUTURES specifically — vs.
only for the venue's native crypto pairs. A scoped `raw_tick_data/by_date/day=<D>/` listing on the prod bucket
(`market-data-tick-cefi-prd-central-element-323112`) for the last 5 days returned suspiciously few objects/day (513-540)
with zero `venue=BINANCE-FUTURES` matches at all (not just zero equity-perp matches) — this reads as an artifact of
`StorageClient.list_blobs()` not honouring `max_results` as an exhaustive-pagination cap (the returned set was
alphabetically truncated well before reaching venues later in sort order, e.g. `pipeline_mode=live_binance...` sorts
after `pipeline_mode=batch_hyperliquid...`), not genuine absence — I did not have a reliable bounded manifest-query tool
at hand to settle it cleanly within this task's scope, and did not want to risk a wider/unbounded GCS walk to force an
answer (single-walk-discipline / heavy-I/O-on-shared-host concerns).

## Recommended decision

(A) **Close the plan todo as already-satisfied** — cite this issue doc + the file:line evidence above, no new
data_type/code needed. (B) File a narrower follow-up todo to verify (not build) that `derivative_ticker` capture is
live-dispatched for the CeFi equity-perp instrument set specifically, using a manifest-level query (not a blob-listing
probe) — e.g. `market-tick-data-service`'s own manifest-freshness/capture_status tooling for a handful of known
equity-perp symbols on BINANCE-FUTURES/OKX-FUTURES/BYBIT-FUTURES. Recommend (A) + (B), not building duplicate capture
infrastructure.

## Todos

- [x] ✅ [OPERATOR] P2. Decide: close `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s "capture Binance/OKX/Bybit
      indexPrice+markPrice+fundingRate" todo as already-satisfied by `derivative_ticker` (cite this doc), or direct that
      a standalone data_type be built anyway (and if so, why — the duplicate-storage tradeoff vs.
      `perp_funding_handler.py`'s ASTER/LIGHTER-ZKSYNC precedent above should be addressed explicitly). Repo:
      unified-trading-pm (plan-doc decision only). **RESOLVED 2026-08-15 — operator approved decision (A) via BLOCKED Q
      BLK-483148f6**: closed as already-satisfied, no standalone data_type. Reflected in
      `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s own todo (checkbox already flipped there).
- [x] ✅ [CODE] P3. Verify (manifest-query, not blob-listing) that BINANCE-FUTURES/OKX-FUTURES/BYBIT-FUTURES
      `derivative_ticker` capture is actually dispatched + landing non-null `mark_price`/`index_price`/`funding_rate`
      for the CeFi equity-perp instrument set (COIN/MSTR/PLTR/... + SPXUSDT/NAS100/XAUUSDT index perps) specifically,
      not just the venues' native crypto pairs. If a real gap is found (universe/enumeration excludes these symbols from
      the `derivative_ticker` shard set), fix the enumeration — do not build a new data_type. Repo:
      market-tick-data-service. **DONE 2026-08-15 (slot-9) — VERIFIED, no code needed.** Full evidence + two venue
      naming corrections in the Progress Log entry below.

## Progress Log

- **context-scout 2026-08-15**: populated context_scope (4 entries).

- **2026-08-15 (slot-9) — manifest-level verification (not blob-listing) of derivative_ticker equity-perp capture.**
  Queried the prod cefi availability index directly (`read_availability_index_safe`, `filters=` row-group pushdown — no
  GCS blob-listing walk) for `data_type=derivative_ticker` over the trailing 10 days, then parsed each row's
  `instrument_id` (`<VENUE>:PERPETUAL:<BASE>-<QUOTE>@<MARGIN>`) to isolate rows whose base is in UAC
  `CEFI_EQUITY_PERP_BASE_UNIVERSE` — a manifest-only technique (no parquet content download needed) since this
  workspace's cefi manifest keys derivative_ticker at `(venue, data_type, instrument_type, instrument_id, day)`
  granularity, not an aggregate per-venue row.

  **Two venue-naming corrections vs. this todo's own literal wording** (both confirmed via code, not the connector
  registry's naming alone):
  - **"OKX-FUTURES" is the wrong OKX venue for this check.** `market_tick_data_service/live/connectors/okx_ws.py`'s own
    module docstring (2026-07-09 venue-key bug fix) states OKX-FUTURES is OKX's genuinely distinct DATED-futures product
    (real instIds like `BTC-USD-260710`) and is deliberately left UNREGISTERED for the live trades/derivative_ticker
    connector — every real instId this connector handles ends in `-SWAP` (perpetual). Binance/OKX/Bybit equity perps are
    typed `PERPETUAL` (2026-07-16 architecture ruling, this doc's own citation) and trade as `-SWAP` contracts on OKX,
    so the venue that actually carries them is **OKX-SWAP** — matching what
    `e2e-testing/scripts/cefi/equity_perp_funding_basis_scan.py` (this doc's own referenced precedent) already reads.
  - **Bare "BYBIT" (not "BYBIT-FUTURES") is Bybit's canonical, EXPECTED_COVERAGE-declared venue.** UAC
    `EXPECTED_COVERAGE_BY_ASSET_GROUP["cefi"]` and `VENUES_BY_ASSET_GROUP["cefi"]` both declare `BYBIT`, not
    `BYBIT-FUTURES`; `CanonicalParquetReader.read_shard(venue="BYBIT-FUTURES", ...)` raises
    `UnknownVenueAssetGroupError` (`to_canonical_venue()` only resolves `LEGACY_DEFI_VENUE_ALIASES`, not
    `CEFI_VENUE_FOLD`).

  **Manifest results (captured, non-`expected_unattempted`/`empty_confirmed`, equity-perp-base rows only, 10-day
  window):**

  | Venue             | Total derivative_ticker rows | Equity-perp-base rows | Distinct equity-perp bases CAPTURED                                       |
  | ----------------- | ---------------------------- | --------------------- | ------------------------------------------------------------------------- |
  | BINANCE-FUTURES   | 6,799                        | 1,592                 | **144** (AAPL/NVDA/TSLA/COIN/MSTR/PLTR/META/AMZN/SPY/SPX/XAU/XAG/QQQ/...) |
  | OKX-SWAP          | 4,387                        | 1,303                 | **180**                                                                   |
  | BYBIT (canonical) | 7,136                        | 1,386                 | **123**                                                                   |
  | BYBIT-FUTURES     | 1,284                        | 126                   | **0** — see below                                                         |

  **Verdict: no enumeration gap.** derivative_ticker capture on each exchange's real, canonical/working venue
  (BINANCE-FUTURES, OKX-SWAP, BYBIT) is confirmed generically dispatched across the full instrument universe including
  the equity-perp base set — COIN/MSTR/PLTR and the rest of `CEFI_EQUITY_PERP_BASE_UNIVERSE` are landing real `captured`
  derivative_ticker rows on all three exchanges today, exactly as this doc's original "What I found" section claimed. No
  new data_type, no enumeration fix needed.

  **BYBIT-FUTURES's 0 equity-perp captures is NOT a new/equity-perp-specific finding — it is the ALREADY-TRACKED,
  venue-wide (not equity-perp-specific) live-capture outage documented in
  `/plans/active/cross_ag_live_capture_parity_2026_08_14.md` Finding C** (100% `empty_confirmed` across ALL 4
  BYBIT-FUTURES data_types — trades/book_snapshot_5/depth_of_book_10/derivative_ticker alike — re-confirmed live by that
  doc as of 2026-08-15, root-caused to an IS same-day-catalog-at-boot timing issue, open `[CODE] P1` fix todo there). My
  independent manifest query corroborates that doc's numbers exactly (1,284 BYBIT-FUTURES derivative_ticker rows in the
  10-day window, 100% empty_confirmed) and confirms the outage is not selectively excluding equity perps — it is total.
  No duplicate issue doc filed; the fix stays owned by that plan's Finding C todo, not this one.
