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
status: open
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
priority: P2
source:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch19_2026_08_13.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
resolved_by:
locked_by:
---

# CeFi equity-perp indexPrice/markPrice/fundingRate — existing `derivative_ticker` already covers it

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

- [ ] [OPERATOR] P2. Decide: close `cefi_satellite_ao_dispatch_batch19_2026_08_13.md`'s "capture Binance/OKX/Bybit
      indexPrice+markPrice+fundingRate" todo as already-satisfied by `derivative_ticker` (cite this doc), or direct that
      a standalone data_type be built anyway (and if so, why — the duplicate-storage tradeoff vs.
      `perp_funding_handler.py`'s ASTER/LIGHTER-ZKSYNC precedent above should be addressed explicitly). Repo:
      unified-trading-pm (plan-doc decision only).
- [ ] [CODE] P3. Verify (manifest-query, not blob-listing) that BINANCE-FUTURES/OKX-FUTURES/BYBIT-FUTURES
      `derivative_ticker` capture is actually dispatched + landing non-null `mark_price`/`index_price`/`funding_rate`
      for the CeFi equity-perp instrument set (COIN/MSTR/PLTR/... + SPXUSDT/NAS100/XAUUSDT index perps) specifically,
      not just the venues' native crypto pairs. If a real gap is found (universe/enumeration excludes these symbols from
      the `derivative_ticker` shard set), fix the enumeration — do not build a new data_type. Repo:
      market-tick-data-service.
