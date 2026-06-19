---
title: TradFi Databento subscription-universe lockdown + billing-safety guards
created: 2026-06-18
parent_epic: tradfi_master
assigned_vm: vm-tradfi
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
locked_by: live-defi-rollout
locked_since: 2026-06-18
---

# TradFi Databento subscription-universe lockdown + billing-safety guards

## Context

Operator (2026-06-18) committed to **exactly three** Databento datasets — `GLBX.MDP3`, `DBEQ.BASIC` (US Equities), `CFE`
(VIX/VX futures) — and to ingesting **only the free included-history schemas**. Querying anything outside the
subscription is billed pay-as-you-go (metered). We must (a) lock the universe, (b) fetch `ohlcv-1s` + `ohlcv-1m` for
OHLCV (both L0/free) and aggregate coarser bars (15m/1h/24h) downstream, (c) enforce per-level rolling-history floors
(L0 16y / L1 1y / L2+L3 1mo), and (d) hard-block `batch.submit_job` (streaming/live only) so we are never billed
silently.

**Scope note — the guards gate DATABENTO requests ONLY.** They do NOT touch stored data, the manifest/data-status, the
candle aggregator, or any non-Databento source. Barchart/Yahoo VIX `ohlcv_15m` is a DIFFERENT source — the Databento
guards never run on it, `ohlcv_15m`/`ohlcv_24h` remain registered TradFi data_types, and nothing deletes stored rows
(see "Out of scope" below + the codex SSOT "VIX" section).

**Codex SSOT:** `codex/02-data/tradfi-databento-sourcing-ssot.md`. **Contract module:**
`unified-api-contracts/unified_api_contracts/registry/databento_subscription_allowlist.py`.

## Shipped 2026-06-18 (this session)

- [x] [UAC] P0. Contract module `databento_subscription_allowlist.py` — dataset allowlist, schema→level map, per-level
      lookback floors, `batch.submit_job` ban, `assert_*` guards (fail-closed). Exported from
      `unified_api_contracts.registry`. Smoke-tested (all allowed/blocked paths + enum-repr normalization).
- [x] [UAC] P0. `market_data_categories.py` — added `ohlcv_1s` as a TradFi `data_type` (base granularity `1s`,
      `needs_candle_processing=True`, `TIMEFRAME_SECONDS["1s"]=1`).
- [x] [MTDS] P0. Wired guards in market-tick-data-service: `_resolve_databento_schema` (schema allowlist),
      `_fetch_timeseries_range` (`assert_databento_request_allowed` at the get_range chokepoint), `submit_batch_job`
      (hard block).
- [x] [DOCS] P0. Codex SSOT `tradfi-databento-sourcing-ssot.md` + CLAUDE.md one-liner.
- [x] [UAC] P0. Event contracts (operator 2026-06-18): `("tradfi","event_contract")` validity matrix admits
      `{trades, ohlcv_1s, ohlcv_1m, tbbo}` (CME `EC*` series on GLBX.MDP3 — covered by the existing subscription, no new
      dataset).
- [x] [UAC/MTDS] P0. OHLCV scope = `ohlcv-1s` **AND** `ohlcv-1m` (operator 2026-06-18; revises the earlier 1s-only).
      Both are L0/free 16y. 1m kept to complete the large existing 1m corpus (exercises migration/manifest/data-status);
      1s is the finer add. `_BANNED_OHLCV_SCHEMAS` now = `{ohlcv-1h, ohlcv-1d}` only; schema_map fetches both 1s+1m.
- [x] [MTDS] P0. SHIPPED the MTDS cutover (single-key config: `num_api_keys=1`, `use_multi_key_rotation=False` defaults;
      `DEFAULT_NUM_API_KEYS=1`; schema-guard + `assert_databento_request_allowed` at the get_range chokepoint;
      `batch.submit_job` ban via `assert_batch_api_allowed`; `ohlcv_1s`/`ohlcv_1m`/`mbp_10` in schema_map; tests updated
      to assert num_keys-driven + `trades` not the banned bar). — market-tick-data-service@88d1c65e | QG green.
- [x] [IS] P0. SHIPPED the IS Databento `definition`-schema entitlement guard with **DATASET-level shard isolation** —
      an off-allowlist dataset (XNAS.ITCH / IFEU.IMPACT / IFUS.IMPACT) raises `DatabentoSubscriptionError`, caught
      per-dataset in `get_instruments` so sibling allowed datasets (GLBX.MDP3 / DBEQ.BASIC / CFE) still return
      (transient BentoError/parse still propagates → `_fetch_one_venue` failed[] → attempted_failed, CF-11 preserved). +
      regression test `test_get_instruments_isolates_banned_dataset`. — instruments-service@86ecc67b | QG green.
- [x] [SECRET] P0. Deleted transitional secret `databento-api-key-1` (post single-key cutover) —
      `gcloud secrets list ~databento` now = only `databento-api-key`.

## Phase 1 — add the ohlcv-1s fetch + 1s aggregation (NON-breaking: 1m stays)

> NOT a breaking cutover — `ohlcv_1m` remains an allowed fetch schema, so the existing 1m pipeline keeps running. 1s is
> purely additive (a new, slower backfill alongside the 1m completion).

- [x] ✅ [MTDS] P0. Add an `ohlcv_1s` fetch request alongside the existing `ohlcv_1m` — DONE. The orchestrator requests
      data_types from `get_expected_data_types_for_venue` (UAC), so the real wiring gaps were: (1) **uac@d731396** — CME
      `VENUE_DATA_TYPE_CAPABILITIES` + `EXPECTED_COVERAGE` + `_PER_INSTRUMENT_SHARD_DATA_TYPES` gain `ohlcv_1s`; (2)
      **uac@1b6df4c** — `1s` added to the `BarTimeframe` closed-set (`BAR_TIMEFRAMES` + seconds map) so edge-conversion
      doesn't raise; (3) **mtds@e814a5b** — `ohlcv_1s→1s` in `_OHLCV_DATA_TYPE_TIMEFRAME` (open→close edge); (4)
      **mtds@521361a** — `ohlcv_1s` added to `_DATABENTO_SUPPORTED_DATA_TYPES` (the gate that actually routes the fetch —
      was the silent 0-rows cause). Smoke (CME, 2026-06-16): 1.01M `ohlcv_1s` rows, `pipeline_mode=batch_databento`,
      manifest `complete=True`. Repo: market-tick-data-service + unified-api-contracts.
- [x] ✅ [MDPS] P1. 1s candle path accepted (non-breaking; 1m base stays) — **mdps@2cfba0b**: `TradfiOhlcv1sAdapter`
      (`base_granularity="1s"`) registered for `ohlcv_1s` (same pre-aggregated passthrough + session-grid finalization as
      1m); `base_adapter.get_interval_seconds["1s"]=1` + `granularity_detector` (`GRANULARITIES["1s"]`,
      `_NATIVE_GRANULARITY["ohlcv_1s"]="1s"`). 15m/24h continue to aggregate from the 1m/1s base via the candle engine;
      QG-green (NaN/session-grid covered by existing passthrough tests). Repo: market-data-processing-service.
- [~] [DATA] P1. Backfill CME ohlcv_1m + ohlcv_1s 2019-01-01→2026-06-19 — **WIRING PROVEN, FULL-HORIZON BLOCKED ON IS
      CATALOG**. The MTDS download CLI works end-to-end on every catalog-covered date: smoke wrote **CME ohlcv_1m 216K
      rows** (2026-06-17), **CME ohlcv_1s 1.01M rows** (2026-06-16, `pipeline_mode=batch_databento`, v9 manifest
      `complete=True`), all verified in the `_index` (`schema_version=9`, `capture_status=captured`). A detached nohup
      backfill (`/tmp/cme_ohlcv_backfill.sh` → `/tmp/cme_ohlcv_backfill.log`, 1m then 1s) is running the full range.
      **BLOCKER (P1, see new todo below):** the per-date instrument enumeration returns 0 instruments for most historical
      dates (probed 2019-2025 + several 2026 weekdays = "0 skipped (no instruments)" / "No active venues") — only a sparse
      recent window (e.g. 06-10/15/16/17 ok; 06-12/18 empty) has IS-catalog coverage. CME futures expire daily and the
      instruments-service catalog has not been historically backfilled, so the OHLCV download has no universe to fetch for
      uncovered dates. This is an **instruments-service catalog-coverage gap, NOT an MTDS/OHLCV wiring gap** (the download
      path is correct on every covered date). The detached backfill writes every covered date + honestly skips the rest.
      Repo: market-tick-data-service.
- [ ] [IS] P1. **Backfill the instruments-service CME (GLBX.MDP3) catalog for the full 2019-01-01→present horizon** so the
      tradfi OHLCV download has a per-date instrument universe to fetch. Today the catalog only covers a sparse recent
      window → the ohlcv_1m/1s backfill writes 0 rows / "no active venues" for ~all historical dates and several recent
      weekdays. Re-run the IS Databento `definition`-schema enumeration per missing trading day (definition is L0/free 16y
      — within subscription), then re-run the MTDS `download` backfill over the now-covered range. Provenance: discovered
      2026-06-19 while running the Phase-1 DATA backfill — the OHLCV wiring is proven (smoke wrote 1m 216K + 1s 1.01M rows
      on covered dates) but blocked on catalog coverage. Composes with "Never copy instrument definitions between dates"
      (CME futures expire daily) + Data-Pipeline-Correctness. Repo: instruments-service.
- [x] ✅ [UAC] P1. SOURCE_PRIORITY: `("tradfi","ohlcv_1s")` entry in `canonical/crosscutting/_source_priority_data.py` +
      matching `("tradfi","ohlcv_1s")` in `availability_semantics.py` (`tick_timestamp`). — unified-api-contracts@3b76c0bc.
      **CORRECTED uac@2cfc756:** flipped from the `["massive","databento"]` mirror to **`["databento"]` (databento-only)**
      — Massive's flat-file connector does NOT serve a 1s schema (`massive_tradfi_rest_connector.SUPPORTED_DATA_TYPES`
      omits `ohlcv_1s`), so massive-first mis-stamped 1s rows `pipeline_mode=batch_massive` despite the data physically
      coming from Databento. databento-primary → `derive_pipeline_mode_for_row` now stamps `batch_databento`
      (provenance-correct; verified by smoke). The open massive-vs-databento ordering question is therefore MOOT for 1s
      (1s is Databento-exclusive); it remains open only for `ohlcv_1m`/`trades`/`tbbo` (still massive-first — Massive DOES
      serve those). Repo: unified-api-contracts.

## Phase 2 — prune the instrument universe to the 3 datasets

- [x] ✅ [UAC] P0. Drop ICE-only instruments from `registry/tradfi_instrument_universe.py`: Brent (`BRN`), Gasoil (`G`),
      ICE Dollar Index (`DX`), softs (`CT`/`CC`/`KC`/`SB`/`OJ`) — and remove `IFEU.IMPACT` / `IFUS.IMPACT` datasets.
      Repo: unified-api-contracts. — **uac@6790981**: `_ICE_FUTURES`/`_ICE_US_FUTURES` lists deleted + dropped codes
      removed from `EXCHANGE_CODE_TO_NAME`; `get_required_datasets()` now returns exactly `{GLBX.MDP3, DBEQ.BASIC, CFE}`.
- [x] ✅ [UAC] P0. Consolidate equity ETFs/stocks onto `DBEQ.BASIC` (currently ETFs on `XNAS.ITCH`); drop the per-venue
      equity datasets. Repo: unified-api-contracts. — **uac@6790981**: `_BTC_SPOT_ETFS`/`_ETH_SPOT_ETFS` (IBIT/ETHA)
      moved `XNAS.ITCH` → `DBEQ.BASIC`; **mtds@d3590c2**: live-ws `_VENUE_TO_DATASET` NYSE+NASDAQ → `DBEQ.BASIC`
      (per-venue XNYS/XNAS/XCBO/ARCX/BATS feeds dropped).
- [x] ✅ [UAC] P0. Wire `CFE` dataset + VX (VIX) futures instruments into `tradfi_instrument_universe.py` and the live-ws
      venue→dataset map (`live/connectors/databento_tradfi_ws.py`, currently `IFEU.IMPACT`/per-venue equities). Repo:
      market-tick-data-service + unified-api-contracts. — **uac@6790981** (`_CFE_FUTURES` VX.FUT on CFE/CBOE) +
      **uac@9fb2c33** (corrected `tradfi_symbology` `DATABENTO_VALID_PARENT_SYMBOLS` + `tradfi_roots.DATASET_CBOE_CFE`
      VX dataset `XCBF.*` → `CFE`, since XCBF is out of the allowlist) + **mtds@d3590c2** (live-ws `CBOE` → `CFE`).
- [x] ✅ [UAC] P1. Remove `ICE` from `VENUES_BY_ASSET_GROUP["tradfi"]`; add a `CFE`/Cboe venue if VX futures need a
      distinct venue token. Repo: unified-api-contracts. — **DIAGNOSED: ICE KEPT (uac@6790981)**. The ICE Databento
      *datasets* (IFEU/IFUS) are dropped, but `ICE` STAYS a tradfi venue because the ICE/NYBOT US Dollar Index (`DXY`)
      is still Yahoo-sourced under venue `ICE` (non-Databento) and the market-session / data-status / source-resolution
      registries + tests key off it (removing it breaks `data_source_continuity` + DXY source-resolution, which the
      dispatch explicitly forbade touching). VX uses the existing `CBOE` venue token (no new venue needed; CFE is the
      Databento *dataset*, CBOE the canonical venue). Plan-intent (remove ICE *Databento* exposure) is fully met.
- [x] ✅ [UAC] P1. Verify the CME event contracts (`EC*` series: ECES/ECNQ/ECRTY/ECYM/ECGC/ECCL/ECNG/EC6E/ECBTC) in
      `tradfi_instrument_universe.py` survive the prune, stay on `GLBX.MDP3`, and are tagged `event_contract` (not bare
      `option`) so the validity matrix admits `{trades, ohlcv_1s, tbbo}`. Repo: unified-api-contracts. — **VERIFIED
      (uac@6790981)**: all 9 EC* contracts in `_CME_EVENT_CONTRACTS` survive untouched on `GLBX.MDP3`; `event_contract`
      classification is by-symbol at normalize time (`external/databento/normalize._is_cme_event_contract_symbol`), so
      the static `instrument_type="OPTION"` def is correct — the runtime classifier tags them event_contract.

## Phase 3 — enforcement + tests + codex alignment

- [ ] [UAC] P1. Unit tests for `databento_subscription_allowlist` (allowed/blocked dataset, banned OHLCV schema,
      per-level lookback floor boundaries, batch ban, break-glass, enum-repr normalization). Repo:
      unified-api-contracts.
- [ ] [PM] P1. QG grep-ratchet: no raw `batch.submit_job` call outside the guarded `submit_batch_job`; no off-allowlist
      dataset string literal in tradfi fetch paths. Wire into market-tick-data-service `quality-gates.sh`. Repo: PM +
      market-tick-data-service.
- [x] [DOCS] P2. Update `codex/02-data/tradfi-data-types-catalog.md` to reflect **1m+1s** OHLCV (added `ohlcv_1s` row +
      the "OHLCV fetch = 1m AND 1s" note; CFE/VX-futures venue). — unified-trading-pm (this commit). **Still open:**
      `codex/04-architecture/tradfi-batch-live.md` (3-dataset universe + CFE) — pairs with the Phase-2 universe prune.
      Repo: unified-trading-pm.

## Out of scope / explicit non-goals

- **VIX 15m cash index gap** stays Barchart+Yahoo — `CFE` provides VX **futures**, not the cash index at 15m
  (`registry/data_source_continuity.py` unchanged).
- ICE / OPRA / EEX / Eurex subscriptions — re-add only on an explicit operator subscription decision.

## Codex SSOT updates

- `codex/02-data/tradfi-databento-sourcing-ssot.md` (NEW — authoritative).
- `codex/02-data/tradfi-data-types-catalog.md` (Phase 3 — reflect **1m+1s** OHLCV — DONE: `ohlcv_1s` row + OHLCV note).
- `codex/04-architecture/tradfi-batch-live.md` (Phase 3 — reflect 3-dataset + CFE).
