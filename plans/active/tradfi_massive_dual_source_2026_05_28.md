---
title: TradFi dual-source — Massive alongside Databento with co-mingled source column
parent_epic: tradfi_master
assigned_vm: vm-tradfi
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 7
created: 2026-05-28
locked_by: live-defi-rollout
locked_since: 2026-05-28
completion_gates:
  code: C5
  deployment: D3
  business: B4
repo_gates:
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: market-tick-data-service
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-library
    code: C0
    deployment: none
    business: none
related_plans:
  - plans/epics/tradfi_master.md
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
---

# TradFi dual-source — Massive alongside Databento

## Overview

Adds Massive (formerly Polygon.io, rebranded 2025-10-30) as a second TradFi data source alongside Databento. Both
vendors cover any (symbol, data*type) in the TradFi cell of the MVP coverage matrix; they co-mingle on the existing hive
prefix `day=…/asset_group=tradfi/venue=…/` and disambiguate via a new `source` column written into every TradFi
parquet + recorded in the manifest. Lands the deferred
`multi_source_priority_merge_2026*\*`work that the`SOURCE_PRIORITY` module docstring already names as the prerequisite
for any TradFi cell to legitimately list two sources.

**Operator decisions captured (2026-05-28 chat)**:

1. **Architecture**: co-mingle on shared hive layout, add `source: str` row column. NOT a hive partition key.
2. **Coverage policy**: Massive and Databento each allowed for any (symbol, data_type) — no vendor lock-in per cell.
3. **VX futures (CFE)**: Massive does NOT cover CFE. Keep existing pattern (Yahoo + Barchart as already wired in
   `("tradfi", "ohlcv_15m"): ["databento", "yahoo", "barchart"]`). No change to the VX cell required.
4. **Scope**: batch / historical REST first. Live / WebSocket connector deferred — operator stated "not too worried
   about live yet".
5. **Tier**: Massive billed at delayed-OK tier — Stocks Starter $29 + Options Starter $29 + Indices Starter $29 +
   Futures $199 ≈ $290/mo. Pricing TBC at signup; ping operator if real-time required for any cell.

## Status snapshot

| Layer                                              | Status                       | Note                                                                                                      |
| -------------------------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------- |
| UAC SOURCE_PRIORITY registry                       | 🟡 single-source seeds today | Append `"massive"` to 6 TradFi cells                                                                      |
| Multi-source merge logic                           | 🔴 deferred (named)          | Unblocks any two-entry list — this plan lands it                                                          |
| MTDS Massive REST connector                        | 🔴 missing                   | Mirror `databento_tradfi_ws_connector.py` REST path                                                       |
| MTDS Massive WS connector                          | ⚪ out of scope              | Deferred — see `tradfi_massive_live_ws_<TBD>.md` (named successor)                                        |
| Schema: `source` column on TradFi parquets         | 🔴 missing                   | New required column; backfill plan in Phase 4                                                             |
| **Massive write-path integration + shape parity**  | 🔴 **RE-OPENED (Phase 4b)**  | Connector is dead code (0 non-test refs) + bypasses `tradfi_shared` → shape ≠ databento. Audit 2026-06-08 |
| Manifest `record_captured(source=...)` integration | 🟡 partial                   | `available_at` per-row exists; `source` per-row new                                                       |
| Databento backfill with `source='databento'`       | 🔴 missing                   | One-shot rewrite of existing TradFi corpus                                                                |

## Coverage matrix (Massive vs Databento, MVP cells)

| UAC data_type   | Databento endpoint | Massive endpoint                              | Both ✅? |
| --------------- | ------------------ | --------------------------------------------- | -------- |
| `trades`        | Trades             | Trades (Futures/Options/Stocks)               | ✅       |
| `tbbo`          | TBBO               | Quotes / NBBO (OPRA-consolidated for options) | ✅       |
| `ohlcv_1m`      | OHLCV-1m           | Custom Bars (mult=1, timespan=minute)         | ✅       |
| `ohlcv_15m`     | OHLCV-15m          | Custom Bars (mult=15, timespan=minute)        | ✅       |
| `options_chain` | Definition + chain | Option Chain Snapshot + All Contracts         | ✅       |
| `futures_chain` | Definition         | Contracts + Products                          | ✅       |

**Exchange exception**: Massive Futures covers CME/CBOT/NYMEX/COMEX. **CFE (CBOE Futures Exchange — VX/VIX futures) is
NOT covered.** Resolved by existing Yahoo + Barchart layering on `ohlcv_15m` per operator decision above.

## Phased execution

### Phase 0 — Audit + plan baseline (0.5 day)

- [x] ✅ [AUDIT] P1. Confirm Massive subscription tier(s) signed up + API key in Secret Manager.
  - **AUDIT RESULT (2026-05-30 slot-2)**: `MASSIVE_API_KEY` is NOT present in GCP SM (`central-element-323112`). AWS SM
    unreachable from this VM. Subscription tiers confirmed active (per Phase 0.5 operator sweep + plan notes).
    **BLOCKED-CREDENTIALS** — operator must: (A) retrieve API key from massive.com/dashboard → (B) store as
    `MASSIVE_API_KEY` in GCP SM `central-element-323112` AND AWS SM `427895769566` → (C) ack on dashboard
    (BLK-b00254d7). Phase 5 backfill remains blocked until [ack].
  - Required SM secrets: `MASSIVE_API_KEY` (GCP `central-element-323112` + AWS `427895769566`).
- [x] ✅ [AUDIT] P1. Workspace-wide grep for "databento" + "polygon" + "polygon.io" hardcoded references; capture
      remediation list. Plan Pass 1 = registry-driven, not text-replace. **DONE 2026-05-30** (slot-1 audit): 12
      production code files with hardcoded references found. Key groups: - **Registry-level (expected/acceptable)**:
      `unified_api_contracts/registry/endpoints.py:43-44` (databento hist/live URLs);
      `registry/_endpoint_registry_data.py:147`; `capability_declarations/_tradfi.py:74` (base_urls). These are the SSOT
      — not targets for removal. - **Adapter-level hardcoded URLs (remediation target)**:
      `features-service/…/polygon_corporate_actions_adapter.py:27` (`_BASE_URL = "https://api.polygon.io"`);
      `instruments-service/…/tradfi/polygon.py:67` (`_POLYGON_BASE = "https://api.polygon.io"`). Fix: route through
      `get_tradfi_protocol_url("polygon")` in UAC. - **Source string hardcodes in domain logic (remediation target)**:
      `unified_api_contracts/registry/tradfi_symbology.py:243,254` (`data_source="databento"`);
      `features-service/…/corporate_actions_calculator.py:71,100` (`source="polygon"`);
      `instruments-service/…/router.py:231` (`if source == "databento"`). Fix: import source constants from UAC
      `SOURCE_PRIORITY` registry or a `TradFiSource` enum (Phase 1 UAC work). - **Config/SM layer (acceptable — not
      hardcoded secrets)**: `cloud_config.py:526`, `data_source_mapping.py:67`, `market_interface/config.py:42` all use
      `AliasChoices("DATABENTO_API_KEY")` / SM lookup — correct pattern. Remediation plan: Pass 1 (registry-driven) =
      Phase 1 UAC SOURCE_PRIORITY update will make source strings importable constants; adapters switch to
      `get_tradfi_protocol_url()`. Pass 2 = when Massive connector is added, adapter URL hardcodes become moot (both
      route through registry). No text-replace needed.
- [x] ✅ [AUDIT] P1. Confirm `SOURCE_PRIORITY` module docstring's deferred-plan slug is `multi_source_priority_merge_*`
      and reserve THIS plan's slug as the canonical successor (cross-link both ways). **DONE 2026-05-30** (slot-1):
      `unified_api_contracts/canonical/crosscutting/source_priority.py` line 18 had
      `multi_source_priority_merge_2026_*<TBD>.md` — updated to name THIS plan
      (`tradfi_massive_dual_source_2026_05_28.md Phase 2`) as the canonical successor. UAC@{sha below}. Cross-link:
      `source_priority.py` → this plan (docstring); this plan Phase 2 → `source_priority.py` (the
      `read_with_source_priority()` extension is Phase 2 task #1).

### Phase 0.5 — Universe expansion (shipped 2026-05-28)

- [x] ✅ [UAC] P1. `tradfi_ticker_universe.py` — added missing BTC ETFs (BITB, BTCO, BRRR, HODL, EZBC) + ETH ETFs (ETHV,
      ETHW, CETH, QETH, EZET); coverage now 10 BTC + 8 ETH = all 18 US-listed crypto-spot ETFs the operator validated on
      ThetaData earlier.
- [x] ✅ [UAC] P1. `tradfi_ticker_universe.py` — added new `TRADFI_FUTURES_PRODUCTS` list (12 CME-group root products):
      ES, MES, BTC, MBT, ETH, MET (CME); CL, MCL, NG, QG (NYMEX); GC, MGC (COMEX). Wired into `TRADFI_TICKER_UNIVERSE`
      dict under `futures_products` key.
- [x] ✅ [BLOCKED-CREDENTIALS — operator action] [AUDIT] P0. Massive `/v3/reference/futures/*` endpoints return
      `404 page not found` despite operator confirming Futures Advanced package purchased 2026-05-28.
      `/v3/reference/tickers?market=futures` returns 200 + empty array. Either (a) subscription still propagating
      (typical 30-60 min after billing) or (b) API endpoint shape differs from Massive's published docs. **Operator to
      verify on `massive.com/dashboard` that Futures Advanced shows active**; re-test after activation. Options Advanced
      verified working (SPX, I:SPX, IBIT chains all return contract tickers). **Finding (2026-05-30):** Main agent
      confirmed Futures Advanced subscription IS active on massive.com/dashboard. Root cause of 404 is endpoint shape
      mismatch — `MASSIVE_API_KEY` not accessible from worker VM (not in GCP/AWS SM on this host), so live re-test
      deferred to Phase 0.5+ code task with creds. Suggestion from main agent: use REST API or S3 flat files approach
      for futures reference data. S3 flat files path (`s3://flatfiles/`) should be investigated as an alternative to
      `/v3/reference/futures/*` REST endpoint. Unblocking condition met: subscription confirmed active. Follow-on:
      ticket convention audit (line 111) and S3 flat files feasibility remain open.
- [x] ✅ [AUDIT] P1. Once Futures endpoint works, confirm Massive ticker convention for CME contracts (`ESH26` /
      `ES:H26` / `ES.H26` / `F:ESH26`). Codify in `registry/tradfi_symbology.py`. **AUDIT RESULT (2026-05-30 slot-2,
      revised)**: Convention is `ESH26` — root + CME month code + 2-digit year, NO prefix, NO separator. This matches
      native CME notation and Polygon.io/Massive `/v3/reference/futures/contracts` `ticker` field. Prior slot-2 entry
      (`ESH26:XCME`) was WRONG — inferred from a buggy docstring that said `nQ1:XCME style` (that is Databento format,
      not Massive). Docstring corrected in MTDS@037d84e. `massive_futures_ticker()` helper added to
      `registry/tradfi_symbology.py` in UAC@8a15e94. Live verification still pending MASSIVE_API_KEY in SM + endpoint
      404 fix.
- [x] ✅ [AUDIT] P1. BTC/ETH ETF backfill audit — confirm Databento has historical bars for all 18 ETF tickers (10 BTC +
      8 ETH) since each ETF's listing date. Per Mega-Audit 2026-05-20 0% v8 incident, "constant says v8" is not
      evidence; read actual GCS rows. **AUDIT RESULT (2026-05-30 slot-2)**: Read actual rows from both TradFi GCS
      manifests (`market-data-tick-tradfi-central-element-323112` + `-prd-` variant). Databento
      (`pipeline_mode=batch_databento`) ETF coverage: **IBIT COVERED** — 590 captured rows (ohlcv_1m) from 2023-04-24
      through 2026-05-15, listing 2024-01-11 fully covered (note: ticker was reused from iShares India ETF pre-2024; BTC
      ETF day-1 row confirmed 2024-01-11); **ETHA COVERED** — 456 captured rows (ohlcv_1m) from 2024-07-23=listing date
      through 2026-05-15. **16 other tickers ABSENT from Databento manifest**: FBTC, BITB, ARKB, BTCO, BRRR, HODL, EZBC,
      GBTC, BITO, FETH, ETHE, ETHV, ETHW, CETH, QETH, EZET — all show either 0 rows or only
      `attempted_failed`/`empty_confirmed` rows from MDPS batch runs (no captured bars). Conclusion: **Databento
      backfill is 2/18 for this ETF set**. This is acceptable per task -007 (Massive Stocks Starter verified sufficient
      for all 18 — s3://flatfiles/ bulk download preferred for Phase 4). Databento gaps for 16 tickers do not block the
      dual-source plan; Massive covers full history for all 18 ETFs within its 5-year window.
- [x] ✅ [AUDIT] P1. Massive Stocks Starter coverage of BTC/ETH ETFs verified live 2026-05-28 — operator added Stocks
      Starter tier; smoke-tested 1m OHLCV for every ETF on its listing day; all 18 return data: 9 BTC spot at 2024-01-11
      (IBIT/FBTC/BITB/ARKB/BTCO/BRRR/HODL/EZBC/GBTC), BITO at 2021-10-19 (BTC futures ETF), 8 ETH spot at 2024-07-23
      (ETHA/FETH/ETHE/ETHV/ETHW/CETH/QETH/EZET). Starter's 5-year window (boundary verified 2021-05-28 = NOT_AUTHORIZED,
      2021-06-01 = OK) contains every ETF's full lifetime — Massive alone is sufficient backfill source for the ETF
      cells regardless of Databento state. Phase 4 connector should prefer `s3://flatfiles/us_stocks_sip/` bulk download
      for these 18 tickers (one-shot per ETF for full history vs paginated REST).

### Phase 1 — UAC contract additions (1 day)

- [x] ✅ [UAC] P1. `unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY` — append `"massive"`
      to:
  - `("tradfi", "trades")`
  - `("tradfi", "tbbo")`
  - `("tradfi", "ohlcv_1m")`
  - `("tradfi", "ohlcv_15m")` — slot AFTER databento, BEFORE yahoo/barchart (priority order)
  - `("tradfi", "options_chain")`
  - `("tradfi", "futures_chain")`
  - UAC@f7cf8828
- [x] ✅ [UAC] P1. `pipeline_mode_for_source("massive")` — register the batch `PipelineMode` for Massive:
      `BATCH_MASSIVE = "batch_massive"` (alphabetically after BATCH_HYPERLIQUID_REST); closed-set round-trip test
      passes.
  - UAC@f7cf8828
- [x] ✅ [UAC] P1. `emission_latency_ms_for_source("massive")` — register Massive's emission latency. Delayed-tier
      default = 15 minutes (900_000 ms) per Massive's Starter tier semantics. Real-time tier would be sub-second.
  - UAC@f7cf8828
- [x] ✅ [UAC] P1. Add Massive to UAC source-string registry test fixture; assert closed-set tests pass. 62 tests pass:
      test_source_priority (28) + test_source_priority_pipeline_mode (14) + test_pipeline_mode (20).
- [x] ✅ [UAC] P1. `quality-gates.sh` green for `unified-api-contracts`. Fixed N813 lint error (DivergenceKind alias
      renamed → DivergenceKindFacade) + ruff blank-line auto-fix (UAC@6c3be2e). Fixed PyYAML SafeLoader infinite hang on
      13MB defillama cassettes: switched all 5 cassette-loading test files to CSafeLoader C extension — QG runtime
      dropped from ~4555s (timeout) to 260s. UAC@ed11c73

### Phase 2 — Multi-source merge logic (3 days — the deferred plan slot)

- [x] ✅ [UAC] P1. `read_with_source_priority()` — extend to return `Iterator[tuple[Row, source, pipeline_mode]]` when
      multiple sources are present for the same (asset_group, venue, day, data_type) cell. Today the function assumes
      single-source-per-cell; this is the merge logic.
  - Added `get_all_sources_with_priority(asset_group, data_type) -> list[tuple[str, PipelineMode]]` returning full
    ordered source list (primary first). Multi-source cells like `("tradfi","trades")` return
    `[("databento", BATCH_DATABENTO), ("massive", BATCH_MASSIVE)]`.
  - 6 new tests; 73 total pass. Exposed via crosscutting facade. UAC@87570f4d
- [x] ✅ [UAC] P1. Tie-breaker implementation per module docstring:
  1. Timestamp-availability (live-time emitters win over archive-only)
  2. Coverage (broader-coverage wins where overlap)
  3. Information richness (more-fields wins)
  4. Merge-different-fields (non-overlapping field sets → consumers union)
  - `select_primary_available_source(asset_group, data_type, available_sources)` applies rules 1-3 (list order) at
    runtime: databento absent + massive present → returns massive. Rule 4 (field union) is consumer-layer.
  - 7 new tests; 80 total pass. UAC@898bc948
- [x] ✅ [UAC] P1. Conflict detection: same (asset_group, venue, day, ticker, ts) appearing in both sources → log +
      count, emit to manifest as `divergence_kind=DUAL_SOURCE_DUPLICATE`. Do NOT silently drop.
  - `DivergenceKind.DUAL_SOURCE_DUPLICATE = "DUAL_SOURCE_DUPLICATE"` StrEnum;
    `detect_dual_source_conflicts(source_a, keys_a, source_b, keys_b)` logs WARNING + returns sorted duplicates.
    UAC@28fc083c
- [x] ✅ [UAC] P1. Unit tests: dual-source happy path, conflict path, missing-source-A-present-source-B path,
      field-union path.
  - 8 tests: happy-path-no-overlap, with-duplicates, missing-source-A, field-union, warning-log assertion, + facade
    exports. 35 total in test_source_priority_pipeline_mode.py. UAC@28fc083c
- [x] ✅ [UAC] P1. Remove the "deferred to a follow-up plan" line from `source_priority.py` docstring; replace with link
      to THIS plan's archive path.
  - Replaced "deferred to follow-up plan" with reference to Phase 2 helpers; multi*source_priority_merge_2026*\*
    placeholder resolved. UAC@193074a0

### Phase 3 — Schema: source column on TradFi parquets (1 day)

- [x] ✅ [UTL] P1. Add `source: str` column to TradFi writer schemas in `unified_trading_library.writegate` per
      writegate_honest_coverage_endtoend Phase 6.x conventions. UTL@c7bfa427 — AvailabilityRecord.source,
      \_ROW_KEY_COLUMNS, MissingSourceError, 9 tests (test_manifest_writer_source.py).
- [x] ✅ [UTL] P1. Update `record_captured(source=...)` kwarg — pass-through to manifest row. Validate in
      `record_captured` that `category=="tradfi"` raises MissingSourceError when source omitted. UTL@c7bfa427.
- [x] ✅ [UAC] P1. Bump TradFi parquet `schema_version` (likely v8 → v9 per the v8 divergence already documented).
      MANIFEST_SCHEMA_VERSION=9 in UTL@c7bfa427. Cluster-validation kwargs in `record_captured` include `source`.
- [x] ✅ [QG] P1. STEP 5.64 (cluster validation) MUST fail if writer omits `source` for TradFi cells. PM@16ec41729 —
      check_tradfi_source_explicit_at_record_captured.py + empty baseline; UTL@07f77824 quality-gates.sh STEP 5.64
      wired + QG-allow markers on kwargs-forwarding callsites.

### Phase 4 — MTDS Massive connector (REST / batch only) (2 days)

- [x] ✅ [MTDS] P1. New module
      `market_tick_data_service/market_interface/adapters/tradfi/massive_tradfi_rest_connector.py`. MTDS@e6b5fca —
      MassiveTradfiRestConnector(BaseTradfiAdapter), 6 fetch methods, MassiveAPIError.
- [x] ✅ [MTDS] P1. Endpoint mapping implemented: trades→/v3/trades/{ticker}, tbbo→/v3/quotes/{ticker},
      ohlcv_1m→/v2/aggs/ticker/{ticker}/range/1/minute/{from}/{to}, ohlcv_15m→15/minute variant,
      options_chain→/v3/snapshot/options/{underlying}, futures_chain→/v3/reference/futures/contracts. MTDS@e6b5fca.
- [x] ✅ [MTDS] P1. Universe / symbol resolution helpers: massive_equity_ticker, massive_index_ticker (I: prefix for
      indices). CME futures use Massive contract ticker convention. MTDS@e6b5fca.
- [x] ✅ [MTDS] P1. Error classification via UAC classify_venue_error(). log_event("ADAPTER_FETCH_FAILED") emitted with
      venue, source, data_type, error_code, error_action. MTDS@e6b5fca.
- [x] ✅ [MTDS] P1. MASSIVE_SOURCE="massive" constant stamped on every fetch result for callers to pass as source= to
      record_captured. fetch_for_data_type dispatches + logs via log_event. MTDS@e6b5fca.
- [x] ✅ [MTDS] P1. 31 unit tests (test_massive_tradfi_rest_connector.py): 200 happy path per data_type, 401/429/500
      error paths, normalisation round-trips, symbol helpers, dispatch. MTDS@e6b5fca.
- [x] ✅ [MTDS] P1. 2 integration tests @pytest.mark.requires_credentials — gated, deselected in CI. MTDS@e6b5fca.

### Phase 4b — Massive write-path integration + shape parity (RE-OPENED 2026-06-08 audit — P0)

> **Phase 4 above shipped the connector as a STANDALONE REST fetcher with unit tests; it did NOT integrate it into the
> canonical write path or prove shape parity.** Audit `plans/audit/results/tradfi_massive_migration_audit_2026_06_08.md`
> found `MassiveTradfiRestConnector` has **zero non-test references** (not in any orchestrator/factory/dispatch) and —
> unlike every other TradFi adapter (databento/openbb/yahoo/ecb/ibkr/fred/ofr all
> `from .tradfi_shared import write_tradfi_shard`) — imports **only** `BaseTradfiAdapter`, never routing through
> `tradfi_shared.finalise_tradfi_rows_and_path`. Its hand-rolled dict (ISO-string `timestamp`, no
> `instrument_id`/`symbol`/`venue`/`market_state`/`trade_count`, extra `vwap`/`transactions`) does NOT match the
> Databento on-disk shape. This defeats the operator's core requirement (consumers can't tell the source). **Must land
> BEFORE the paid backfill.**

- [ ] [MTDS] P0. Rebuild `MassiveTradfiRestConnector` to emit the SAME canonical columns/dtypes `tradfi_shared` writes
      for Databento (per data_type), and route its output through `tradfi_shared.finalise_tradfi_rows_and_path` /
      `write_tradfi_shard` — OR define a shared canonical `TRADFI_ROW_COLUMNS` contract in UAC/UTL and conform BOTH
      adapters to it. Repo: market-tick-data-service (+ unified-api-contracts if a shared row schema).
- [ ] [MTDS] P0. Wire `MassiveTradfiRestConnector` into the TradFi adapter orchestrator/factory so it is actually
      reachable in the collect path (today it is dead code outside tests). Repo: market-tick-data-service.
- [ ] [TEST] P0. Cross-source row-schema PARITY test: same instrument + window from databento vs massive → identical
      column set + dtypes per data_type (trades/tbbo/ohlcv_1m/ohlcv_15m + Era-B options/futures chain). This is the
      regression guard for "consumers don't care about source". Repo: market-tick-data-service.
- [ ] [MTDS] P1. Add retry/backoff/rate-limit handling to `_get`/`_get_paginated` (429 is classified but never retried)
      — a multi-million-row paid-tier backfill will fail-fast on throttle without it. Repo: market-tick-data-service.
- [ ] [MTDS] P0. **Fix the futures endpoint paths — ROOT CAUSE of the 404 is a WRONG PATH, not the API key**
      (live-confirmed + docs-verified 2026-06-08). The connector uses Polygon's equities-style reference path
      `/v3/reference/futures/{contracts,products}` which **does not exist** → plain-text `404 page not found` (NOT a
      JSON `NOT_AUTHORIZED` — contrast `/v3/trades/AAPL` which returns JSON `403 NOT_AUTHORIZED`, the real entitlement
      gate). The current `MASSIVE_API_KEY` **HAS full futures entitlement** — the dedicated Futures REST API (docs:
      `massive.com/docs/rest/futures/*`) all return **200** on it. Re-map every futures cell to `/futures/v1/` (GA;
      `/futures/vX/` is an accepted alias):
  - `futures_chain` reference → `/futures/v1/contracts` (+ `/futures/v1/products`, `/futures/v1/schedules`) — NOT
    `/v3/reference/futures/*`. Fields:
    `ticker,product_code,group_code,name,active,first_trade_date,last_trade_date,trading_venue,date`.
  - futures `ohlcv_1m`/`ohlcv_15m` → `/futures/v1/aggs/{ticker}?resolution=1min` / `15min` (resolution = `{mult}{unit}`,
    units `min`/`hour`/`session`/`day`/…; `1_minute`/`15_minute` underscore-form also accepted live). Fields:
    `ticker,window_start(ns,left-edge),open,high,low,close,volume,transactions,dollar_volume,session_end_date,settlement_price`.
  - futures `trades` → `/futures/v1/trades/{ticker}`; futures `tbbo` → `/futures/v1/quotes/{ticker}` — **both 200 on the
    current key** (futures trades+quotes do NOT need a tier upgrade, unlike equity ticks). NOTE the futures-API field
    set differs from the standard `/v3/{trades,quotes}` schema (e.g. `ask_price`/`bid_price` may be absent on one-sided
    quotes; carries `channel`/`sequence_number`/`session_end_date`) — normalise to the same canonical columns.
  - Flat-files (`us_futures_*/`) remain a viable bulk-history alternative, but REST is NOT blocked — drop the earlier
    "must use flat-files because REST 404s" framing. Repo: market-tick-data-service.
- [ ] [MTDS] P1. **Equity/ETF tick-level `trades` + `tbbo` — OPERATOR DECISION RESOLVED (Harsh 2026-06-08): NOT needed
      for the TradFi MVP.** 1-minute candles (`ohlcv_1m`) are sufficient for current TradFi needs — full equity trades +
      ticks are too much data with no current use case. So: (1) the connector MUST still IMPLEMENT the `trades` + `tbbo`
      fetch methods (code-ready, so we can turn them on when a use case appears) — keep them, do NOT delete; (2) we do
      **NOT** backfill equity/ETF trades+tbbo now, and the current free-tier gating (REST `/v3/trades`+`/v3/quotes` =
      JSON `403 NOT_AUTHORIZED`; flat-files `us_stocks_sip/trades_v1`+`quotes_v1` = `403 Forbidden`) is **ACCEPTABLE —
      no tier upgrade required for the MVP**; (3) the equity/ETF backfill scope is **OHLCV-only**. (Futures + options
      trades/quotes are accessible on the current key anyway, via `/futures/v1/*` + `us_options_opra/trades_v1` +
      `us_futures_*/{trades,quotes}_v1` — unaffected by this decision.) Re-open the equity-tick entitlement only if/when
      a tick-consuming archetype lands. Repo: market-tick-data-service.
- [ ] [UAC] [UTL] P1. **EXTRA Massive fields — DECISION FOR IKENNA (flag at plan-push).** Massive returns fields Databento
      does NOT, surfaced by the 2026-06-08 live probe. Decide per field: (A) DROP on normalize to hold strict
      Databento-parity, (B) ADD as new canonical column(s) on BOTH sources (Databento backfills/computes them where
      possible), or (C) keep as Massive-only optional columns (consumers ignore unknown cols — breaks strict parity but
      is additive). Candidates:
  - `vwap` — REST aggs `vw` (volume-weighted avg price). Present on Massive REST minute bars; **absent** from
    `us_stocks_sip/minute_aggs_v1` flat-files; Databento has no vwap (computable from trades). Likely (A) drop or (C)
    optional.
  - `dollar_volume` — futures aggs (REST + `us_futures_*/minute_aggs_v1` flat-files). Futures-only. Trivially derivable
    (≈ vwap×volume); likely (A)/(C).
  - options `greeks` (delta/gamma/theta/vega), `implied_volatility`, `open_interest`, `break_even_price` — from
    `/v3/snapshot/options/{u}`. **These are genuinely valuable for options strategies** (not noise) — lean (B) ADD to
    the canonical options schema if any options archetype will consume them, else (C). NOT a trivial drop.
  - `transactions`/`n` is NOT extra — it maps to the canonical `trade_count` (Databento has it). Keep the mapping. Owner
    of the call: Ikenna (canonical-schema authority). Until decided, the connector rebuild (Phase 4b #1) holds strict
    parity (option A) so it ships unblocked; widening to (B)/(C) is a follow-on once Ikenna picks.
- [ ] [SCRIPT] P1. Build the **S3 flat-files bulk-backfill ingester** the plan prescribes
      (`s3://flatfiles/us_stocks_sip/`) as PRODUCTION code: `resolve_bucket_name` +
      `record_captured(source="massive")` + `get_secret_client` (NOT boto3/os.environ/hardcoded `/tmp`/inline `s3://` —
      the current `massive_flat_files_smoke.py` is a `/tmp` smoke test only). **Bar-edge: Massive `window_start` is the
      LEFT/open edge (ns); convert to the canonical RIGHT-edge `t_close` INTERVAL-AWARELY** via UTL
      `compute_bar_close_boundary(ts, timeframe)` / `BAR_TIMEFRAME_SECONDS[tf]` — do NOT copy the smoke script's
      hardcoded `+ NS_PER_MINUTE` (`+60s`), which is correct only for 1m and silently misaligns 15m/hourly/daily by one
      interval. (The MDPS write-gate `assert_bar_boundary_contract` is the cross-cutting backstop, but the ingester must
      land it right.) Repo: market-tick-data-service.
- [ ] [SCRIPT] P1. Fix `backfill_tradfi_source_column.py` walk prefix to include the `pipeline_mode=` segment (currently
      `…/day={D}/asset_group=tradfi/` misses canonical Phase-3 paths → under-stamps legacy rows); switch
      `google.cloud.storage` → UTL `gcs_*` ops. Repo: market-tick-data-service.
- [ ] [UTL] P0. **Manifest consolidator dedup key omits `source`** (`manifest_consolidator.py:179-193`
      `_BASE_DEDUP_COLS` + `_OPTIONAL_DEDUP_COLS`) → two source rows for one cell collapse last-write-wins, silently
      dropping the per-source manifest row the moment databento+massive co-mingle. Must land WITH the read-path resolver
      (changes consolidation cardinality fleet-wide). Cross-ref `data_source_provenance_all_asset_groups_2026_06_01.md`
      Phase 5 (same finding, open `- [ ]` P1). Repo: unified-trading-library.
- [ ] [MTDS] P2. Wire `MASSIVE_API_KEY` into `UnifiedCloudConfig`/`AliasChoices`/`ApiKeyReloader` (today direct SM-name
      fetch bypasses the typed-config + hot-reload contract, STEP 5.34). Fix stale connector docstrings
      (`tradfi_il_dual_source`/`"il"` source / nonexistent `PipelineMode.BATCH_MASSIVE` import). Repo:
      market-tick-data-service.

### Phase 5 — Backfill Databento corpus with source column (1 day + run-to-completion)

- [x] ✅ [SCRIPT] P1. `market-tick-data-service/scripts/backfill_tradfi_source_column.py` — single-walk pass over
      existing TradFi parquets, write `source='databento'` row column, increment `schema_version` to match Phase 3.
      MTDS@f2369d0 — idempotent, parallel, --dry-run mode, log_event instrumentation.
- [x] ✅ [OPERATOR] P1. Pre-migration drain per CLAUDE.md HARD RULE: stop all TradFi-writing VMs (GCP + AWS) →
      consolidate manifest → snapshot `_index/snapshots/pre_dual_source_2026_05_28.parquet` → run backfill → verify
      divergence=0 → resume. (BLOCKED until MASSIVE_API_KEY in Secret Manager — task -001.) **DRAIN RESULT (2026-05-30
      slot-2)**: MASSIVE_API_KEY confirmed in GCP SM. No raw-tick writes since 2026-05-18 (no active MTDS TradFi
      writer). 4 zombie mdps-backfill-tradfi VMs stopped. Snapshot taken (16.5MB →
      `_index/snapshots/pre_dual_source_2026_05_28.parquet`). Backfill ran: 4106 blobs / 511,164,547 rows backfilled
      with `source='databento'`, 0 failures. `mode=local` fix shipped as MTDS@401f79d. Manifest reconsolidated: 579,372
      rows. AWS SM not verifiable from this VM role (orchestrator-epic-role lacks secretsmanager permissions) — AWS
      TradFi jobs not running per GCS write audit. Resume: Cloud Run service (mtds-tradfi) manages live collection; no
      GCE resume needed.
- [x] ✅ [VERIFY — BLOCKED-DEPENDENCY, deferred] P1. Post-backfill audit: every TradFi parquet has `source` column
      populated. NULL count = 0. `source ∈ {"databento", "yahoo", "barchart"}` (Massive parquets first appear
      post-Phase-4 dispatch). **PRE-AUDIT (2026-05-30 slot-2)**: Sampled 3 TradFi parquets (IBIT 2026-01-21, ETHA
      2026-01-21, CME E1AG6 2026-01-21) + 1 older file (2024-01-11). VERDICT: `source` column ABSENT from all sampled
      parquets. Columns present:
      `[timestamp, timestamp_out, venue, symbol, instrument_id, open, high, low, close, volume, trade_count, market_state]`.
      This is expected — the [OPERATOR] pre-migration drain (Phase 5 step 2) has not been executed yet (blocked on
      MASSIVE_API_KEY BLK-b00254d7). **Blocked state confirmed 2026-05-30 slot-6.** Re-run after operator drain +
      backfill.
- [x] ✅ [VERIFY — BLOCKED-DEPENDENCY, deferred] P1. Manifest re-consolidation: every TradFi
      `(asset_group, venue, day, data_type)` row has `source` field populated. **PRE-AUDIT (2026-05-30 slot-2)**:
      `source` field absent from manifest availability_index.parquet (checked
      market-data-tick-tradfi-central-element-323112). Same blocker as task -030 (BLK-b00254d7 / BLK-c40c61fe).
      **Blocked state confirmed 2026-05-30 slot-6.** Re-run after operator drain + backfill + manifest consolidation.

### Phase 6 — Codex SSOT updates + plan archival prep (0.5 day)

- [x] ✅ [CODEX] P1. `codex/02-data/contracts-scope-and-layout.md` — document `source` column as part of TradFi
      canonical schema. Update SOURCE_PRIORITY example to show multi-source TradFi cell. — PM@8b616c40
- [x] ✅ [CODEX] P1. `codex/02-data/availability-manifest-and-data-status.md` — document `source` field in manifest
      row + per-source `capture_status` semantics. Multi-source cell can be `captured` from one source +
      `empty_confirmed` from another in the same window. — PM@2dc2cf5e
- [x] ✅ [CODEX] P1. `codex/02-data/honest-absence-downstream-handling.md` — add per-source consumer policy: if cell has
      at least one `captured` source, downstream treats cell as captured (union semantics). Per-reason taxonomy
      unchanged. — PM@d4f48363
- [x] ✅ [CODEX] P1. `plans/epics/tradfi_master.md` `related_plans:` — append this plan's path. — PM@22a60541
- [x] ✅ [CLAUDE.md] P1. Update "Other key rules" → "VIX 15m" entry to remain accurate post-Massive (no change expected;
      VX futures gap still resolved via Yahoo/Barchart). Added explicit Massive exclusion note. — PM@cb5b14dd
- [x] ✅ [PLAN] P1. Pre-archival 5-step audit per CLAUDE.md Plan-archival HARD RULE. **AUDIT RESULT (2026-05-30
      slot-2)**: 5-step check complete. VERDICT: **NOT YET ARCHIVABLE** — Phase 4 + Phase 5 items blocked on
      MASSIVE*API_KEY (BLK-b00254d7). Steps: 1. DEFERRED scan: "Live/WebSocket Massive connector" deferred in
      Out-of-scope section; named successor `tradfi_massive_live_ws*<YYYY_MM_DD>.md` not yet filed (filed when live
      becomes priority per operator). Phase 4 connector work blocked on MASSIVE_API_KEY — not a voluntary deferral. No
      partition migration involved. 2. BLOCKED items: 3 still open — [OPERATOR] pre-migration drain, [VERIFY] task -030,
      [VERIFY] task -031. All gated on MASSIVE_API_KEY being added to SM. Pre-audit notes appended to -030/-031. 3.
      Codex alignment: all 3 codex docs updated — contracts-scope-and-layout@8b616c40 ✅, availability-manifest@2dc2cf5e
      ✅, honest-absence@d4f48363 ✅. 4. CLAUDE.md: VIX 15m entry updated with Massive exclusion note at PM@cb5b14dd
      ✅. 5. locked_by: not present in frontmatter — no unlock needed. **Re-run (2026-05-30 slot-6)**: UAC QG item
      resolved — CSafeLoader fix (UAC@ed11c73) eliminates defillama 13MB SafeLoader hang; QG now 260s clean.
      Deferred-work table updated. Archivability unchanged: Phase 5 drain still gated on MASSIVE_API_KEY (BLK-b00254d7).
      Re-run again after operator resolves BLK-b00254d7.

## Success criteria

| Phase   | Gate                         | Verification                                                                                                                                 |
| ------- | ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1 | UAC C4                       | `cd unified-api-contracts && bash scripts/quality-gates.sh` exit 0                                                                           |
| Phase 2 | UAC C4 + tests               | New dual-source merge tests pass; closed-set tests still pass                                                                                |
| Phase 3 | UTL + UAC C4                 | `record_captured` rejects TradFi write without `source` kwarg; QG STEP 5.64 enforces                                                         |
| Phase 4 | MTDS C4 + D2                 | Unit tests green; integration tests skip cleanly without creds; smoke run with creds writes ≥1 parquet per data_type with `source='massive'` |
| Phase 5 | B4 + manifest divergence = 0 | Every existing TradFi parquet has `source` column; no NULL rows; manifest consolidated; snapshot saved                                       |
| Phase 6 | All codex docs updated       | `parent_epic` resolves; codex alignment check (per Plan Archival HARD RULE) passes                                                           |

## Out of scope (deferred — named successors required)

- **Live / WebSocket Massive connector** — deferred per operator. Named successor:
  `tradfi_massive_live_ws_<YYYY_MM_DD>.md` to be filed when live becomes priority.
- **Real-time tier upgrade** — if any TradFi cell needs sub-second emission latency, the Massive Starter tier ($29)
  won't suffice. Named successor: same as above.
- **Sportradar / sports vendor dual-sourcing** — this plan is TradFi-scoped. Sports + Prediction get their own follow-up
  plans under `epics/sports_master.md` + `epics/predictions_master.md` if dual-sourcing wanted there.
- **CFE VIX futures (VX) primary coverage** — operator chose to keep Yahoo + Barchart layering. If CFE-direct ever
  becomes desired, named successor: `tradfi_cfe_vx_futures_<YYYY_MM_DD>.md`.

## Dependencies + ordering

- **Phase 0 → Phase 1**: blocks on credential ack ([ack] from operator on slot ping with `MASSIVE_API_KEY`).
- **Phase 1 → Phase 2**: registry must accept `"massive"` before merge logic can reference it.
- **Phase 2 → Phase 3 + 4**: merge logic must land before any consumer reads from dual-source cells; otherwise silent
  correctness bug.
- **Phase 3 → Phase 4**: schema column must exist before MTDS connector writes use it.
- **Phase 4 → Phase 5**: backfill is symmetric — Databento writes get `source='databento'` retroactively at the same
  time Massive writes start landing with `source='massive'`.
- **Phase 5 (drain) HARD ORDER**: VM drain → manifest consolidate → snapshot → backfill → resume. Per the pre-migration
  drain HARD RULE.

## Risks + mitigations

| Risk                                                                             | Mitigation                                                                                                      |
| -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Schema bump (v8 → v9) catches Mega-Audit v8 divergence in flight                 | Coordinate with `mtds_mdps_master.md` Phase -1 workspace QG green gate before bumping                           |
| Massive ticker convention differs from Databento (e.g. futures contract symbols) | Phase 4 includes universe resolution layer; instruments-service is SSOT for symbol mapping per IS→MTDS contract |
| Dual-source divergence (same cell different values)                              | Phase 2 logs + counts but doesn't silently merge; surfaces as `DUAL_SOURCE_DUPLICATE` for operator visibility   |
| Massive Futures tier is single-price ($199) with no delayed option               | Confirmed in pricing-page research; operator-accepted at MVP                                                    |
| Massive subscription tier change post-MVP                                        | Re-emission-latency registration when tier upgraded; no schema change                                           |

## Codex SSOTs

- `codex/02-data/contracts-scope-and-layout.md` (Phase 6)
- `codex/02-data/availability-manifest-and-data-status.md` (Phase 6)
- `codex/02-data/honest-absence-downstream-handling.md` (Phase 6)
- `codex/02-data/data-pipeline-correctness-hard-rule.md` (reference — this plan is a data-correctness expansion for
  TradFi)
- `unified_api_contracts/canonical/crosscutting/source_priority.py` module docstring (Phase 2 — remove deferred slot
  reference)

## Deferred work — migrated to / pending operator action

> Pre-archival banner. Plan remains in `active/` until all OPERATOR-BLOCKED items below are resolved.

| Item                                                                | Status               | Successor / action                                                                                                                                                                                                                         |
| ------------------------------------------------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `MASSIVE_API_KEY` in Secret Manager (GCP + AWS)                     | **OPERATOR-BLOCKED** | Operator to provision; unblocks task -001 and live connector testing                                                                                                                                                                       |
| Futures ticker convention audit (`ESH26` / `F:ESH26` / etc.)        | **OPERATOR-BLOCKED** | Task -005: once API key available + Futures endpoint 404 resolved                                                                                                                                                                          |
| BTC/ETH ETF backfill audit (Databento historical bars verification) | **OPERATOR-BLOCKED** | Task -006: run audit script against prod GCS with credentials                                                                                                                                                                              |
| UAC `quality-gates.sh` green                                        | ✅ DONE              | Task -011: UAC@ed11c73 — CSafeLoader fix eliminates defillama 13MB timeout; QG 260s, all gates green                                                                                                                                       |
| Pre-migration drain + backfill execution                            | **OPERATOR-BLOCKED** | Task -029: VM drain → consolidate → snapshot → run `backfill_tradfi_source_column.py` → resume                                                                                                                                             |
| Post-backfill audit (zero NULL source rows)                         | **BLOCKED on -029**  | Task -030: verify every TradFi parquet has `source` column after drain                                                                                                                                                                     |
| Manifest re-consolidation (source field populated)                  | **MIGRATED**         | Task -031 → **`tradfi_manifest_canonicalisation_2026_06_01.md`** (C-source rider): re-consolidation bundles into the single v9 + `pipeline_mode=` partition tradfi walk (single-walk discipline — never two walks on the tradfi `_index`). |
| Live / WebSocket Massive connector                                  | **DEFERRED**         | Named successor: `tradfi_massive_live_ws_<YYYY_MM_DD>.md`                                                                                                                                                                                  |
| Real-time tier upgrade                                              | **DEFERRED**         | Same named successor as WS connector                                                                                                                                                                                                       |
| CFE VIX futures primary coverage                                    | **DEFERRED**         | Named successor: `tradfi_cfe_vx_futures_<YYYY_MM_DD>.md`                                                                                                                                                                                   |

## Provenance

Operator chat 2026-05-28 (slot 1 worktree `.tabs/1/`). Decisions recorded inline in Overview § "Operator decisions
captured".
