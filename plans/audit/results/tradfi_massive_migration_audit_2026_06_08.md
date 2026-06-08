---
type: audit-result
epic: tradfi_master
instructions_ref:
  plans/audit/instructions/tradfi_master_audit_instructions.md (§ "Dual-source provenance" h–o + § "TradFi-specific
  standing checks" tradfi-erab/tradfi-dual/tradfi-vix/tradfi-listing); CF-1…CF-14
auditor: harsh (interactive, hk laptop)
date: 2026-06-08
status: complete
parent_plan: plans/active/tradfi_massive_dual_source_2026_05_28.md
related_plans:
  - plans/active/data_source_provenance_all_asset_groups_2026_06_01.md
  - plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md
method:
  code-state (4 parallel read-only repo audits) + write-path verification + manifest-bucket reachability probe; prod-row
  data-state reads deferred (laptop host)
---

# TradFi Databento → Massive migration — multi-axis audit (2026-06-08)

## Why this audit + what already existed

Operator (Harsh) requested a thorough migration audit across five axes (shape parity · source flagging · batch/live mode
· canonical zero-drift for consumers · pre-subscription readiness), and asked whether an Ikenna audit instruction
already exists.

**It does — no new instruction created.** `plans/audit/instructions/tradfi_master_audit_instructions.md` was aligned
**2026-06-08** with a dedicated _Dual-source provenance_ section (items h–o), CF-1…CF-14 canonical-form coverage, and
Massive-specific standing checks (`tradfi-erab`/`tradfi-dual`/`tradfi-vix`/`tradfi-listing`). The five operator axes map
cleanly onto it (see § Axis → instruction map). This document is the **result** of running that instruction against the
five axes, plus one instruction gap it exposed (§ Instruction augmentation).

**Method**: four parallel read-only code-state audits across `unified-api-contracts`, `unified-trading-library`,
`market-tick-data-service`, `market-data-processing-service`, `features-service`, `instruments-service`; plus first-hand
verification of the headline finding; plus a manifest-bucket reachability probe. Prod-row _data-state_ reads (actual
`source`-column histograms) are **deferred** — this ran on the hk laptop; both prod TradFi `_index` buckets are
reachable (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/...` and the no-env legacy variant) but the
column-distribution read belongs on a VM and is gated on the backfill anyway.

## Headline verdict

| #   | Axis (operator words)                                           | Verdict                             | One-line                                                                                                                                                                |
| --- | --------------------------------------------------------------- | ----------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Massive parquet has the SAME shape as Databento                 | 🔴 **RED**                          | The Massive connector emits a hand-rolled dict and is **not wired through the shared canonical writer** every other TradFi adapter uses → shapes diverge today.         |
| 2   | Every cell flagged with its source (tradfi first, then all AGs) | 🟢 GREEN (write-path) / 🟡 residual | TradFi write-path + registry + UTL gate complete; cefi empty/failed path + 4 cross-AG code items still open.                                                            |
| 3   | Mode recorded (batch backfill vs live websocket)                | 🟢 GREEN                            | `batch_massive` enum + resolver + 900 s delayed-latency + REST-only (no Massive WS, correct) + `pipeline_mode=` LEFT of `asset_group=` + `transport` as its own column. |
| 4   | Canonical, zero drift for downstream consumers                  | 🔴 **RED** (same root as #1) + 🟡   | No shared canonical TradFi _row_ schema exists to enforce parity; read-path source-collapse IS wired for tradfi.                                                        |
| 5   | All code/issues done BEFORE we subscribe & pay                  | 🟡 **NOT READY**                    | Connector/tests/symbology/read-path ready; **4 genuine code gaps** must land before a safe backfill (see § Axis 5).                                                     |

**Bottom line for the operator's central requirement** ("use old + new parquet without checking the source"): **not met
today.** Two independent, blocking reasons — (A) the Massive connector does not produce the canonical on-disk shape and
isn't integrated into the write path (Axis 1/4), and (B) the manifest consolidator's dedup key omits `source`, so once
both vendors co-mingle the second source row is silently dropped (Axis 5). Both are **code gaps fixable now, before we
pay** — which is exactly the window the operator wants them closed in.

---

## Axis 1 + 4 — Shape parity & canonical zero-drift 🔴 RED

**Finding (verified first-hand, not just sub-agent):** `MassiveTradfiRestConnector`
(`market-tick-data-service/.../market_interface/adapters/tradfi/massive_tradfi_rest_connector.py`) has **zero non-test
references** anywhere in the service — it is not registered in any orchestrator, factory, or dispatch path. And unlike
**every** other TradFi adapter (`databento_adapter`, `openbb`, `yahoo_finance`, `ecb`, `ibkr`, `fred`, `ofr` all
`from .tradfi_shared import write_tradfi_shard`), the Massive connector imports **only** `BaseTradfiAdapter` — it never
calls `tradfi_shared.write_tradfi_shard` / `finalise_tradfi_rows_and_path`, the shared function that produces the
canonical on-disk TradFi parquet shape + the `pipeline_mode=` path.

Consequence: the Massive connector returns dicts with its own column set; nothing canonicalises or persists them in the
service. The only Massive→parquet code is `scripts/massive_flat_files_smoke.py`, a `/tmp` smoke test using a _different_
normaliser.

**Shape comparison** (Databento on-disk shape = the real sample recorded in `tradfi_massive_dual_source` Phase-5 task
-030, 2026-05-30; Massive shape = the connector's `_normalize_*` output, `massive_tradfi_rest_connector.py:464-545`):

|                                                                       | Databento on-disk (ohlcv)                                                                                           | Massive connector emits                                                                                 | Drift                                                                                                                        |
| --------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| columns                                                               | `timestamp, timestamp_out, venue, symbol, instrument_id, open, high, low, close, volume, trade_count, market_state` | `timestamp, open, high, low, close, volume, vwap, transactions, available_at`                           | Massive **missing** `timestamp_out, venue, symbol, instrument_id, trade_count, market_state`; **extra** `vwap, transactions` |
| timestamp                                                             | written by `tradfi_shared`                                                                                          | ISO-8601 **string** via `_ns_to_iso` (`:456`)                                                           | dtype/format mismatch                                                                                                        |
| trades                                                                | canonical id cols present                                                                                           | `timestamp(str), price, size, exchange, conditions, available_at` — no `instrument_id`/`symbol`/`venue` | RED                                                                                                                          |
| tbbo                                                                  | `bid_px_00`/`ask_px_00`/…                                                                                           | `bid_price`/`ask_price`/`bid_size`/`ask_size`                                                           | name + scaling mismatch                                                                                                      |
| options/futures chain (Era-B `instrument_type=…`, `data_type=trades`) | bundled per underlying via `tradfi_shared`                                                                          | flat snapshot / reference-universe dicts; never reaches the Era-B partition                             | RED                                                                                                                          |

**Structural gap behind it:** there is **no canonical TradFi market-data _row_ schema** in UAC or UTL to enforce parity
against — `_ROW_KEY_COLUMNS` is the _manifest_ key, and the parquet writer is `strict=False`, so each adapter's columns
land verbatim. The only byte-identity test (`test_tradfi_shared_path_byte_identity.py`) covers the path _string_, not
row columns. So "identical shape" is asserted nowhere; there is no cross-source row-schema parity test.

**GREEN within this axis:** both connectors classify errors via `classify_venue_error()` + emit `ADAPTER_FETCH_FAILED`;
the canonical `tradfi_shared` partition path is itself source-aware and _would_ produce `batch_massive` correctly **if**
Massive output were routed through it; the downstream read-path collapse (Axis-4 consumer side) IS wired (see Axis 5
#5).

**Required fix (before backfill):** rebuild the Massive connector to emit the **same columns/dtypes `tradfi_shared`
writes for Databento** and route its output through `finalise_tradfi_rows_and_path` / `write_tradfi_shard` — OR define a
shared canonical `TRADFI_ROW_COLUMNS` contract in UAC and conform both adapters to it. Add a **cross-source row-schema
parity test** (same instrument+window from databento vs massive → identical column set/dtypes). Until then Axis 1 + 4
stay RED and the "consumers don't care about source" guarantee is false.

> ⚠️ This contradicts `tradfi_massive_dual_source_2026_05_28.md` Phase 4 being ticked `✅`. Phase 4 shipped the
> connector _as a standalone REST fetcher with unit tests_ — it did **not** integrate it into the canonical write path
> or prove shape parity. Phase 4 is **re-opened** with corrective todos (see § Plan todos filed).

---

## Axis 2 — Source flagging (TradFi first, then all asset groups) 🟢 write-path / 🟡 residual

**TradFi: GREEN end-to-end at code/registry/gate level.**

- `SOURCE_PRIORITY` (`unified-api-contracts/.../source_priority.py`): all 6 TradFi cells ordered `databento`→`massive`
  (ohlcv_15m also →`yahoo`,`barchart`). Helpers `source_required`/`default_source`/`external_sources_for`/
  `COMPUTED_SOURCES`/`select_primary_available_source`/`get_all_sources_with_priority`/`detect_dual_source_conflicts`
  all present + exported.
- UTL universal gate `_resolve_and_validate_source()` (`manifest_writer.py:2053`): blank multi-source → raises
  `MissingSourceError`; single-source → auto-stamps; invalid source → raises; computed/unregistered → exempt. Applied in
  `record_captured`, legacy `add`, and `record_captured_from_counts`. `MANIFEST_SCHEMA_VERSION = 9`; `source` in
  `_ROW_KEY_COLUMNS`. Bonus cross-check `_assert_source_matches_pipeline_mode` catches
  `batch_databento`+`source=massive` disagreement.
- MTDS Massive connector defines `MASSIVE_SOURCE="massive"` and stamps it on the fetch result.

**"Then all asset groups" — per-AG write-path status:**

| AG         | Captured path                                                                                                            | Empty/Failed path                                                                                    | Verdict                 |
| ---------- | ------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ----------------------- |
| tradfi     | databento+massive threaded; Massive stamps `massive`                                                                     | via row_key                                                                                          | 🟢 (backfill/read open) |
| prediction | both paths pass `asset_group="prediction"` → `polymarket_clob` auto-stamps; lifecycle→`polymarket_gamma_api`             | exempt                                                                                               | 🟢                      |
| defi       | multi-source threaded (`oracle_prices`=chainlink/pyth_hermes, `native_staking`=solana_rpc/helius_rpc); single auto-stamp | recorder present                                                                                     | 🟢                      |
| sports     | FIXTURES threaded `api_football` (in **instruments-service**); singles auto-stamp; source is a **column** not a path key | exempt                                                                                               | 🟢                      |
| cefi       | captured auto-derives `source="tardis"` (MDPS `canonical_writer.py`)                                                     | 🔴 **GAP**: `record_empty`/`record_failed` don't forward `source` → blank on empty/failed cefi cells | 🟡                      |

**Still-open code items for "all AGs flagged"** (all already tracked as `- [ ]` in
`data_source_provenance_all_asset_groups_2026_06_01.md`): (1) cefi empty/failed `source` threading; (2) downstream
resolver wired only for tradfi — dead code for cefi until its 2nd source; (3) **consolidator dedup key omits `source`**
(also Axis 5 #1); (4) QG checker not wired into MTDS/MDPS `quality-gates.sh`. The rest open there are operational
backfill/re-consolidation, not write-path code.

---

## Axis 3 — Batch vs Live mode recorded 🟢 GREEN

- `PipelineMode.BATCH_MASSIVE = "batch_massive"` (`pipeline_mode.py:95`); `pipeline_mode_for_source("massive", BATCH)`
  resolves it; `emission_latency_ms_for_source("massive") = 900_000` (15-min delayed Starter tier).
- `SOURCE_MODE_CAPABILITY` (M2) is **shipped in code** (not plan-only): `"massive": {BATCH, LIVE, REPLAY}`
  (`source_priority.py:444`) with `modes_for_source`/`source_supports`/`sources_supporting` accessors.
- **No Massive WS/live connector exists** — correct, Massive is batch/REST only per the plan; `databento_tradfi_ws.py`
  remains the sole TradFi live path. `LIVE_MASSIVE`/`REPLAY_MASSIVE` enum members exist but are gated on the paid
  real-time tier (deploy-time, not code).
- Write path puts `pipeline_mode={mode}_{source}/` immediately after `day=` and **LEFT of `asset_group=`** in both MTDS
  orchestrator and MDPS config. `transport` (rest/ws/flat_file) is a separate manifest **column**
  (`default_transport_for_source`), not glued into `source` (the `hyperliquid_rest` antipattern is retired).
- Open M-items (do NOT block Massive batch tagging): M1-BREAKING (`live_websocket`→`live_<source>` object migration), M4
  live read-path resolver `select_for_mode`, M3/M5(UI)/M6/M7.

---

## Axis 5 — All code done BEFORE we subscribe & pay 🟡 NOT READY

**READY:** connector's 6 fetch methods + endpoint maps + error classification + `ADAPTER_FETCH_FAILED`; API key via
Secret Manager (`MASSIVE_API_KEY`, not os.environ); 33 unit tests (per-data_type 200 + 401/429/500 + normalisation +
symbol helpers) with `@pytest.mark.requires_credentials` integration tests skipped in CI; `massive_futures_ticker()`
(ESH26 convention) + equity/index helpers; downstream read-path collapse `_resolve_multi_source_blobs`
(`orchestration_scanner.py:485`, 8 regression tests, `select_primary_available_source` exported from UAC top-level);
`available_at` parity column landed.

**🔴 CODE GAPS — must land BEFORE paying (these make the backfill _unsafe/incorrect_, not just un-runnable):**

| P      | Gap                                                                                                                     | Evidence                                                                                                                                                        | Why it blocks                                                                                                                                                                                                     |
| ------ | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **P0** | Massive connector not wired to canonical writer / shape drift                                                           | Axis 1 above                                                                                                                                                    | Backfilled Massive parquets would be unreadable by consumers expecting the Databento shape                                                                                                                        |
| **P0** | Manifest **consolidator dedup key omits `source`**                                                                      | `manifest_consolidator.py:179-193` `_BASE_DEDUP_COLS`+`_OPTIONAL_DEDUP_COLS` (no `source`)                                                                      | Two source rows for one cell collapse last-write-wins → the per-source manifest row the design requires is **silently dropped** the moment both vendors co-mingle. Tracked open `- [ ]` P1 in provenance plan:284 |
| **P1** | **No S3 flat-files bulk-backfill ingester**                                                                             | `massive_flat_files_smoke.py` is a `/tmp` smoke test (uses `os.environ`, `boto3`, hardcoded `/tmp`, inline `s3://`, no `record_captured`/`resolve_bucket_name`) | The plan prescribes `s3://flatfiles/us_stocks_sip/` for bulk history; that production ingester does not exist. Only slow paginated REST remains → the bulk mechanism is unbuilt when the sub arrives              |
| **P1** | Backfill walk prefix missing `pipeline_mode=` segment                                                                   | `backfill_tradfi_source_column.py:155` walks `…/day={D}/asset_group=tradfi/`                                                                                    | Won't match canonical Phase-3 paths (`pipeline_mode=` LEFT of `asset_group=`) → under-stamps legacy rows. Also uses `google.cloud.storage` directly (should be UTL `gcs_*`)                                       |
| **P1** | Connector has **no retry/backoff**                                                                                      | `_get`/`_get_paginated` raise on first non-200; 429 classified but never retried                                                                                | Paid-tier rate limits will fail-fast on every throttle during a multi-million-row backfill                                                                                                                        |
| **P2** | `MASSIVE_API_KEY` not in `UnifiedCloudConfig`/`AliasChoices`/`ApiKeyReloader`                                           | direct SM-name fetch only                                                                                                                                       | Bypasses the typed-config + hot-reload contract (STEP 5.34)                                                                                                                                                       |
| **P2** | Stale docstrings in connector (`tradfi_il_dual_source`, `"il"` source, nonexistent `PipelineMode.BATCH_MASSIVE` import) | `massive_tradfi_rest_connector.py:20`                                                                                                                           | Cosmetic, misleading                                                                                                                                                                                              |

**RUN-BLOCKED (no code — only the paid key + operator drain):** the legacy-row backfill _run_ (drain→consolidate→
snapshot→backfill→re-consolidate, task -029); live ticker-convention verification.

---

## Feasibility probe — can Massive actually fill the canonical shape? (LIVE, 2026-06-08)

Before any code work, probed the **real** endpoints with the live `MASSIVE_API_KEY` (REST) + `MASSIVE_S3_*` (flat-files)
creds from GCP SM — not vendor docs. Two questions: (1) is the shape mismatch _mechanically_ fixable, and (2) is the
data actually _present + accessible_ on the current (free/unpaid) entitlement?

### Key architectural finding — the canonical identity columns are COMPUTED, not vendor-sourced

The columns Massive "lacks" (`instrument_id`, `instrument_type`, `underlying`, `symbol`, `venue`, `session`, `phase`,
`data_type`, `timestamp_out`) are **not pulled from Databento either** — `tradfi_shared` / `_enrich_with_canonical_ids`
computes them deterministically from `(ticker, exchange, timestamp)`. Massive returns `ticker` + `exchange` +
`timestamp` in **every** dataset. **So routing Massive through the same enrichment yields byte-identical canonical
columns — the Axis-1 RED is an _integration_ gap, not a _data_ gap. The planned fix is sound.** The vendor-sourced
measures (OHLCV / price+size / bid+ask) are all that must come from the response, and they do.

### What was verified live (✅ present / ❌ gated)

| Cell                                | Canonical measure needed             | Massive REST (`api.polygon.io`)                                                                                                                    | Massive flat-files (`files.massive.com`)                                                             | Verdict                |
| ----------------------------------- | ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- | ---------------------- |
| `ohlcv_1m`/`ohlcv_15m` (stocks/ETF) | o/h/l/c/v + trade_count              | ✅ `/v2/aggs` → `o,h,l,c,v,vw,t,n` (n=trade_count)                                                                                                 | ✅ `us_stocks_sip/minute_aggs_v1` `ticker,volume,o,c,h,l,window_start(ns),transactions`              | **READY**              |
| `ohlcv_*` (futures)                 | same                                 | ✅ `/v2/aggs/ticker/ES/...` returns bars                                                                                                           | ✅ `us_futures_{cme,cbot,nymex,comex}/minute_aggs_v1` (+`exchange,session_end_date,dollar_volume`)   | **READY**              |
| `options_chain`                     | strike/expiry/type/underlying + OHLC | ✅ `/v3/snapshot/options/{u}` → `details{contract_type,expiration_date,strike_price,ticker,shares_per_contract}`, greeks, day OHLCV, open_interest | ✅ `us_options_opra/minute_aggs_v1` (OPRA ticker `O:A240119C00110000` decodes strike/expiry/type)    | **READY**              |
| `trades` (options)                  | price,size,ts,exchange,conditions    | (n/a)                                                                                                                                              | ✅ `us_options_opra/trades_v1` `ticker,conditions,correction,exchange,price,sip_timestamp,size`      | **READY**              |
| `trades` (futures)                  | price,size,ts,exchange               | (n/a)                                                                                                                                              | ✅ `us_futures_cme/trades_v1` `ticker,timestamp,seq,price,size,correction,exchange,session_end_date` | **READY**              |
| `tbbo` (futures)                    | bid/ask px+sz, ts                    | (n/a)                                                                                                                                              | ✅ `us_futures_cme/quotes_v1` `ticker,ts,ask_price,ask_size,bid_price,bid_size,exchange,...`         | **READY**              |
| **`trades` (stocks/ETF)**           | price,size,ts,exchange,conditions    | ❌ `/v3/trades` → `NOT_AUTHORIZED`                                                                                                                 | ❌ `us_stocks_sip/trades_v1` → **403 Forbidden** (LIST ok, GET denied)                               | **🔴 ENTITLEMENT GAP** |
| **`tbbo` (stocks/ETF)**             | bid/ask px+sz, ts                    | ❌ `/v3/quotes` → `NOT_AUTHORIZED`                                                                                                                 | ❌ `us_stocks_sip/quotes_v1` → **403 Forbidden**                                                     | **🔴 ENTITLEMENT GAP** |
| `trades`/`tbbo` (futures) via REST  | price,size,ts / bid,ask              | ✅ `/futures/v1/trades/{t}` + `/futures/v1/quotes/{t}` → **200 on current key**                                                                    | ✅ flat-files too                                                                                    | **READY**              |
| `futures_chain` reference + aggs    | contract/expiry/product + OHLCV      | ✅ `/futures/v1/{contracts,products,aggs,schedules}` → **200** (NOT the old `/v3/reference/futures/*` path)                                        | ✅ flat-file alternative                                                                             | **READY (path fix)**   |

### Two concrete gaps the probe surfaced (beyond the integration rebuild)

1. **Equity/ETF tick-level `trades` + `tbbo` gated — OPERATOR DECISION RESOLVED (Harsh 2026-06-08): not needed for the
   MVP.** REST returns `NOT_AUTHORIZED` and `us_stocks_sip/trades_v1`+`quotes_v1` flat-files return **403 Forbidden**
   (we can LIST them — 1.5 GB trades, 6.7 GB quotes/day — but GET is denied; entitlement is asset-class-specific —
   options + futures ticks GET fine, only equity ticks are gated). **Decision: 1-minute candles are sufficient for
   current TradFi needs — equity ticks are too much data with no current use case, so NO tier upgrade is required and
   the gating is acceptable.** Equity/ETF backfill scope = **OHLCV-only**. The connector MUST still implement the
   `trades`+`tbbo` fetch methods (code-ready, turn on when a use case appears — do not delete). Equity **minute aggs**
   are accessible now, so ETF OHLCV is unaffected; re-open the equity-tick entitlement only when a tick-consuming
   archetype lands.
2. **Futures 404 = WRONG PATH, not a key/entitlement problem** (deep-investigated 2026-06-08 per operator request;
   live + official docs `massive.com/docs/rest/futures/*`). The connector calls Polygon's equities-style reference path
   `/v3/reference/futures/{contracts,products}` which **does not exist** → plain-text `404 page not found`. The
   diagnostic tell: a real but unentitled endpoint returns a **JSON** `403 {"status":"NOT_AUTHORIZED"}` (as `/v3/trades`
   does), never a plain `404 page not found`. The **current `MASSIVE_API_KEY` HAS full futures entitlement** — the
   dedicated Futures REST API `/futures/v1/` (GA; `/futures/vX/` alias) returns **200** for contracts, products, aggs,
   trades, quotes, and schedules. **Fix = re-map to `/futures/v1/`** (not flat-files-only — REST futures is fully
   available, including futures trades+tbbo without any upgrade). aggs `resolution` = `{mult}{unit}` (`1min`/`15min`/
   `1session`; underscore-form `1_minute`/`15_minute` also accepted live). ⚠️ Docs-vs-live drift noted: the docs page
   states path `/futures/v1/` + `1min`/`1session`; live additionally accepts `/futures/vX/` + `_minute` forms — code to
   the documented `/futures/v1/` + `1min`/`15min`.

### Normalization deltas (decisions, not blockers)

Massive carries extras Databento lacks — REST `vw` (vwap), futures flat-file `dollar_volume`, options `greeks`/
`open_interest`. To hold strict shape parity these are dropped on normalize (or added to BOTH sources). Massive
`window_start` is the **left edge** of the bar (ns) → the smoke script already converts to canonical right-edge
(`+60s`); the rebuilt connector must do the same so bar timestamps align with Databento.

### Feasibility verdict

**Practically achievable — with one entitlement decision.** The shape can be made identical (enrichment computes the
identity columns from fields Massive always returns), and the data is present for **OHLCV (all classes), options chains,
options/futures trades, and futures tbbo — today, on the current creds**. The **only hard data gap is equity/ETF
tick-level trades+tbbo**, which needs a paid tier; resolve whether the MVP even needs equity ticks (vs minute bars)
before subscribing. Filed both gaps as Phase-4b todos.

## Cross-cutting bar-edge convention audit — ALL sources (2026-06-08, operator-requested)

Operator asked to extend the Massive `window_start` (bar-edge) check to **every** source, since the candle-timestamp
edge is cross-cutting. Canonical = RIGHT-edge `t_close`
(`unified-api-contracts/.../canonical/crosscutting/bar_boundary.py` `bar_window_for_close`; interval-aware HOW = UTL
`compute_bar_close_boundary(ts, timeframe)` using `BAR_TIMEFRAME_SECONDS`). **Central enforcement = MDPS write-gate**
`assert_bar_boundary_contract` (`market-data-processing-service/.../core/canonical_writer.py`) — every emitted candle's
`timestamp` is validated as a midnight-aligned `t_close`; `available_at = t_close + emission_latency` (the 2026-05-11
double-add overshoot is fixed). So any source feeding the candle pipeline with a wrong-edge timestamp **raises at write
time** — the system is sound at the MDPS layer; the only risks are at the raw-adapter ingestion boundary.

| Source                                                              | edge the vendor gives              | converted to canonical t_close?                                              | verdict                                                                                                                                |
| ------------------------------------------------------------------- | ---------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| databento, tardis (cefi), pyth/onchain, polymarket                  | trade/event-time ticks             | tick→candle via MDPS aggregator → `period_end`=t_close; write-gate validates | ✅ aligned (interval-aware)                                                                                                            |
| yahoo/openbb (VIX/equity bars)                                      | vendor bar ts                      | flows through MDPS aggregator + write-gate                                   | ✅ aligned (gate-enforced)                                                                                                             |
| **massive (flat-file aggs)**                                        | LEFT/open `window_start` (ns)      | smoke script `+60s` HARDCODED to 1m                                          | 🟡 latent — fine for 1m today, misaligns 15m/daily; the **production backfill ingester must convert interval-awarely** (Phase-4b todo) |
| **hyperliquid candleSnapshot (instruments-service reference-data)** | dict has both `t`=open & `T`=close | code reads `t` (LEFT/open)                                                   | 🔴 one-interval-early stamp — `instruments-service/.../reference_data/adapters/cefi/hyperliquid.py:255`                                |
| ecb/fred (macro rate series)                                        | publication/observation date       | n/a — not OHLCV bars                                                         | ⚪ n/a                                                                                                                                 |

**Two findings filed**: (1) the Massive interval-aware conversion requirement is folded into the backfill-ingester
Phase-4b todo (do NOT inherit the smoke script's `+60s`); (2) the hyperliquid left-edge read is a real bug **outside
this plan's scope** (instruments-service reference-data, DeFi/CeFi) → filed as
`plans/active/issues/hyperliquid_ohlcv_left_edge_timestamp_2026_06_08.md`. Note it does NOT pollute the canonical candle
store (that path is right-edge-enforced by the MDPS gate); it only affects consumers reading `OHLCVRef.timestamp`
directly. **Window-edge IS preferred right-edge and is centrally enforced — no systemic drift across sources.**

## Cross-cutting flags for the operator

1. **Plan-drift on credential state.** `data_source_provenance_all_asset_groups_2026_06_01.md:151,357` claims
   `MASSIVE_API_KEY` was provided 2026-06-01 ("backfill UNBLOCKED"), while `tradfi_massive_dual_source_2026_05_28.md`
   still shows Phase 5 `BLOCKED-CREDENTIALS` (BLK-b00254d7). Reconcile before any go/no-go — the audit's premise (still
   free tier) matches the tradfi plan.
2. **The "use old + new without checking source" goal has TWO independent blockers**, both code-fixable now: shape
   integration (Axis 1) and the consolidator dedup key (Axis 5 P0). Neither needs the paid subscription to fix.

## Axis → instruction map (coverage confirmation)

| Operator axis                      | Covered by instruction item                                                                                                           |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Shape parity                       | CF-1/2/3/7/9; tradfi-erab; **gap: no explicit "route through tradfi_shared + cross-source row-schema parity test"** → augmented below |
| Source flagging (tradfi + all AGs) | h, i, j, k, o + provenance plan                                                                                                       |
| Batch/live mode                    | CF (pipeline_mode partition); tradfi-dual; mode plan M1/M2                                                                            |
| Canonical zero-drift / consumers   | l, m, n (read-path reconciliation)                                                                                                    |
| Pre-subscription readiness         | a–g (scaffold) + o (BLOCKED-CREDENTIALS) — extended by Axis-5 gap list                                                                |

## Instruction augmentation (the one gap this audit exposed)

The instruction's shape checks are implicit in CF-1…CF-7 but never state the **integration + parity** requirement that
just failed. Recommend adding to `tradfi_master_audit_instructions.md` § "TradFi-specific standing checks":

- **(tradfi-shape) Massive routes through the canonical writer + cross-source row-schema parity.** Every TradFi adapter
  (incl. Massive) MUST emit output via `tradfi_shared.finalise_tradfi_rows_and_path`/`write_tradfi_shard` (the SSOT for
  the on-disk column set + `pipeline_mode=` path) — RED-flag any adapter that hand-rolls its parquet shape or is not
  referenced by an orchestrator/factory. A cross-source parity test asserts databento vs massive emit an identical
  column set + dtypes per data_type for the same instrument/window.

## Plan todos filed (per Capture-Discoveries HARD RULE)

Added to `plans/active/tradfi_massive_dual_source_2026_05_28.md` (Phase 4 re-opened + new Phase 4b). Cross-AG items
already exist as `- [ ]` in `data_source_provenance_all_asset_groups_2026_06_01.md` (cefi empty/failed, consolidator
dedup key, QG wiring) — not duplicated here.

## Reproduce

```
# Wiring (Massive not integrated):
rg -n "MassiveTradfiRestConnector|massive_tradfi_rest" -t py -g '!*test*' market-tick-data-service/
# Every other adapter routes through tradfi_shared; Massive does not:
rg -n "tradfi_shared" -t py market-tick-data-service/.../adapters/tradfi/
# Consolidator dedup key:
rg -n "_BASE_DEDUP_COLS|_OPTIONAL_DEDUP_COLS" unified-trading-library/.../manifest_consolidator.py
```
