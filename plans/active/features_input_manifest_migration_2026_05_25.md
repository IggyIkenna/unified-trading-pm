---
title: "Features-service input-read migration to v8 manifest (fix stale-path / stale-discovery read failures)"
created: 2026-05-25
last_updated: 2026-05-25
parent_epic: features_and_ml_master
assigned_vm: vm-ml
name: features-input-manifest-migration-2026-05-25
estimate_class: refactor
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 3.6
estimate_calibration_note: |
  Refactor class (0.4×): propagates the EXISTING onchain manifest-read pattern
  (`_read_manifest_rows` → `read_availability_index` → capture_status) to 3 more
  families + deletes drifted hardcoded path templates. Net-new surface is small
  (one shared UTL helper); the bulk is delete-and-rewire across known callsites.
---

## Problem statement (audited 2026-05-25)

features-service computes features by reading MDPS `processed_candles` from GCS. The input-discovery + pre-flight code
in several families **path-probes literal GCS paths and does NOT read the v8 availability manifest**, so it fails to
read data that demonstrably exists and is readable. Confirmed end-to-end: `delta_one` computes **zero features** on
current production data (2026-05-02/03 CEFI), despite 5,760 clean OHLCV rows per instrument-day being present and
readable in one line of polars.

Two bug classes, both layout/discovery drift:

- **BUG-1 — stale instrument discovery.** `get_available_instruments()` lists `processed_candles/by_date/` with
  `list_blobs(..., max_results=100)`. GCS lists lexicographically → the first 100 objects are the **oldest date (2019)**
  → the CLI "discovers" 2019-era DERIBIT instruments (`DERIBIT:PERPETUAL:BTC-PERPETUAL`, `BTC-PERPETUAL`) and requests
  them for 2026 dates → 404 on everything. The real 2026 universe is `BITGET-FUTURES`/`BITGET-SPOT` `…USDT`.
- **BUG-2 — legacy path template drift.** The lookback/dependency gate builds the pre-2026-04 layout
  `…/data_type={dt}/instrument_type={subdir}/venue={venue}/{id}@LIN.parquet`. MDPS dropped the `instrument_type=`
  segment and `@LIN` suffix in 2026-04; canonical is now `…/data_type={dt}/venue={venue}/{id}.parquet`. The gate never
  matches a real file → counts 0 candles → aborts before any feature computes.

**Why the manifest is the fix, not just a nicety:** the v8 manifest is layout-agnostic — it records exactly which
`(venue, data_type, instrument)` shards are `captured` for a given date. Both bugs are layout/scan drift; a
manifest-driven discovery + gate is immune to them and to future MDPS layout changes (MDPS is actively committing
schema/venue changes on `live-defi-rollout` right now). `onchain` already did this migration (its DeFi deps read
`capture_status`); this plan propagates that model.

**Manifest version: v8.** `MANIFEST_SCHEMA_VERSION = 8`
(`unified-trading-library/unified_trading_library/manifest_writer.py:145`). The real CEFI tick manifest is 34,933,247
rows, **100% at schema_version 8.0**. Migration target is the v8 availability index via `read_availability_index()`.

## Blast radius (8 families)

| Family               | BUG-1 | BUG-2 | Reads manifest?             | Status                                 | Evidence                                                                                                                                    |
| -------------------- | ----- | ----- | --------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **delta_one**        | ✅    | ✅    | ❌                          | **BROKEN (confirmed e2e: 0 features)** | `app/core/data_loader.py:165` (max_results=100); `app/core/dependency_checker.py` `_sum_candles_over_days` legacy `instrument_type=`/`@LIN` |
| **volatility**       | ✅    | ✅    | ❌                          | **BROKEN-LIKELY (worst)**              | `core/data_loader.py:100,168,231,290` legacy paths + hardcoded `venue=BINANCE-FUTURES` (actual data is BITGET) + `@LIN`                     |
| **cross_instrument** | ✅    | —     | ❌                          | **DEGRADED-LIKELY**                    | `app/calculators/realized_implied_vol.py:157` `max_results=100` on IV fetch                                                                 |
| **multi_timeframe**  | —     | —     | (consumes delta_one output) | **TRANSITIVELY BLOCKED**               | unblocks once delta_one writes features                                                                                                     |
| **onchain**          | ❌    | ❌    | ✅                          | **OK (reference model)**               | `app/core/dependency_checker.py:50-67` `_read_manifest_rows`                                                                                |
| **sports**           | ❌    | ❌    | ✅ (canonical)              | **OK**                                 | `data/gcs_reader.py` unbounded list + UAC SSOT paths                                                                                        |
| **calendar**         | n/a   | n/a   | n/a                         | **N/A (FRED API)**                     | no GCS input                                                                                                                                |
| **commodity**        | n/a   | n/a   | n/a                         | **N/A (vendor APIs)**                  | no GCS input                                                                                                                                |

Net: **3 directly broken + 1 transitive** of the core CeFi/TradFi feature path. 2 OK, 2 N/A.

## Reference pattern (copy from onchain)

`features_service/onchain/app/core/dependency_checker.py:50-67`: `read_availability_index(bucket)` → filter
`(date, data_type)` → check `capture_status` ∈ {`captured`, `empty_confirmed`, `attempted_failed`}. Instrument universe
for the target date comes from the manifest rows, not a lexicographic blob scan.

## Related work + dedup check (2026-05-25)

Verified against the plans corpus + UAC + recent repo commits before scoping, to avoid duplication:

- **Feature-DAG / required-inputs SSOT already EXISTS — do NOT rebuild.**
  `unified_api_contracts.canonical.domain.features.FEATURE_REQUIRED_INPUTS` (`required_inputs.py:80`; founding commit
  `UAC@4a25b07` + onchain/tradfi/36-sports expansions) maps each `feature_group → [InputReq(asset_group, data_type)]`.
  This plan **consumes** it (resolve which `(asset_group, data_type)` a group needs) — it does not define a new
  registry. Owned by epic `features_and_ml_master` Phase 1A.
  - **Gap, NOT this plan:** `InputReq` carries no `lookback_candles`; lookback lives only in per-family
    `feature_definitions.yaml` `_group.lookback_candles` and is absent for onchain/volatility/sports. Unifying lookback
    into the SSOT is a `features_and_ml_master` Phase 1A follow-up.
- **`features_and_ml_master` Phase 3** wires honest-absence RECORDING (`record_expected_unattempted` for out-of-scope
  instruments) in features batch handlers — it does NOT fix the GCS read bugs. **This read-path fix is a PREREQUISITE
  for Phase 3:** in-scope instruments must be readable before honest-absence on the rest is meaningful.
- **`archive/institutional_smoke_matrix_2026_04_20`** built the per-cell `scripts/*/smoke_matrix.py` (existence-only,
  single group per cell). A comprehensive per-feature coverage harness (all valid feature_group × asset_group cells,
  driven off `FEATURE_REQUIRED_INPUTS` + v8 manifest + per-group lookback) is a SIBLING extension of that + epic Phase
  5A (deferred phantom-audit-for-features) — **not in this plan** unless the operator folds it in.
- **deployment-api recent 11 commits (live-defi-rollout):** all data-status DISPLAY / DeFi ghost-venue-name
  canonicalization / type-error fixes — **no overlap** (display-side, not compute-side). They confirm the canonical
  `asset_group=` hive key, which the v8 manifest already uses, so this plan's reads are aligned.

**Net:** NET-NEW (input-read bug fix). Feature-DAG SSOT dropped as duplicate; coverage harness deferred to a sibling.

## Phases (DAG; QG gate between each)

### Phase 0 — Pre-audit + golden baseline `[P0]`

- [x] ✅ [AUDIT] P0. Confirm actual canonical layout per asset_group from real GCS (CEFI done: `venue=BITGET-*`,
      `data_type=trades`, no `instrument_type=`/`@LIN`). Repeat for TRADFI/DEFI/PREDICTION input buckets. Record
      verified recent test dates with populated buffer day per asset_group. — features-service@97fcbc3e
- [ ] [AUDIT] P0. Snapshot expected instrument universe + captured shards from the v8 manifest for the chosen test dates
      (the golden set each family's discovery must reproduce).
- [ ] [SCRIPT] P1. Fix smoke_matrix stale default date — `DEFAULT_SMOKE_DATE = "2024-06-15"` has **no data**, so all 8
      `scripts/*/smoke_matrix.py` silently fail. Replace with a dynamic recent-date resolver (latest date with manifest
      `captured` rows). Provenance: this masked the bugs.

### Phase 1 — delta_one (reference fix; confirmed-broken) `[P0]`

- [x] ✅ [IMPLEMENT] P0. **ROOT CAUSE (discovered during impl): features read the DEPRECATED legacy bucket.**
      `_get_source_bucket` + `LookbackValidator` bucket f-string → `resolve_bucket_name(kind="market-data")` (canonical
      `-prd`, bucket SSOT). The legacy bucket is un-consolidated (stale manifest, full 2019 history → phantom
      instruments); canonical is consolidated every minute. — features-service@2965bbda
- [x] ✅ [IMPLEMENT] P0. `get_available_instruments()` (BUG-1) → **manifest-driven** via
      `read_availability_index`/`capture_status` (supersedes worker's date-scoped path-probe `97fcbc3e` per operator
      decision 2026-05-25). — features-service@2965bbda
- [x] ✅ [IMPLEMENT] P0. `dependency_checker` lookback gate (BUG-2) → **manifest `capture_status`** (deleted legacy
      `instrument_type=`/`@LIN` blob probe + `_sum_candles_over_days`). — features-service@2965bbda
- [x] ✅ [VALIDATE] P0. `data_loader._build_blob_path` canonical confirmed: BITGET perps load **11520 candles** each on
      2026-05-03 CEFI from canonical bucket. QG green (279s). — features-service@2965bbda
- [x] ✅ [IMPLEMENT] P0. **Honest-absence reads (pipeline-readiness):** `blob_exists()`-check before download in
      `_try_load_one_day` (mirrors onchain/sports) + None-guard in `load_candles_with_buffer`. Missing/not-yet-backfilled
      shards now skip cleanly instead of 404→retry→None→`len()` crash. Validated 2026-05-03 CEFI: 48 real BITGET load,
      ~35 not-yet-backfilled venues skip, **0 NoneType crashes, 0 unhandled 404s**. — features-service@c35e5e72
- [x] ✅ [VALIDATE] P0. **READ + CALCULATE pipeline READY:** reads all available data + auto-picks-up venues as backfill
      lands; calculate validated (technical_indicators → 84 features, rsi_14 in [0,100]). Reads canonical **v8** manifest
      via `read_availability_index` (no pinned/legacy version; -prd manifest = 100% schema_version 8). Remaining for full
      end-to-end: WRITE P0 (deferred) + venue-ID encoding (below; only bites once those venues' data lands).

### Downstream findings exposed by the read fix (2026-05-25) — outside input-read scope

- [ ] 🔴 [BUG] P0. **`write_daily_partition: string index out of range`** fails for EVERY successfully-loaded instrument
      (all BITGET perps), blocking all feature writes → "0/83 completed" despite candles loading. Not in
      `feature_writer.py` (UTL/engine write path). Was masked until now because nothing loaded. Owner/plan TBD — likely
      `features_and_ml_master`. Provenance: features_input_manifest_migration e2e run 2026-05-25.
- [x] ✅ [BUG] P1. **Instrument-ID compose fixed** (the 404s were mostly "no data yet"; the real bug was id compose).
      `_compose_instrument_ids` now always builds canonical `{venue}:{instrument_type}:{symbol}` from the separate
      manifest columns — matching the MDPS writer (`build_processed_candle_path`, which is MDPS-local so features must
      mirror it). Kraken `/` and Bitfinex `:`-in-symbol now flow through correctly; malformed rows (empty venue/id, or
      **empty `instrument_type` — Bitfinex's manifest rows lack it**) are skipped honestly. Validated: discovery returns
      0 bare/malformed ids. — features-service@cedd31f5
  - [ ] 🟠 [UPSTREAM] P2. **Bitfinex manifest rows have empty `instrument_type`** → features can't form their canonical
        id, so they're skipped. Needs the manifest writer to populate `instrument_type` for Bitfinex. Added to issue
        `cefi_processed_candles_manifest_file_disconnect_2026_05_25.md`.
- [ ] 🟠 [INFRA] P1. **MTDS dual-writes legacy + canonical buckets** — legacy `market-data-tick-cefi-{pid}` still
      receives writes (2,099 per-VM shards, full history) alongside canonical `-prd`. Per bucket-SSOT migration the
      legacy bucket should be drained/cutover. Cross-side → flag Ikenna (MTDS/infra). Provenance: same investigation.

### Phase 2 — volatility `[P0]`

- [x] ✅ [IMPLEMENT] P0. Deleted hardcoded `venue=BINANCE-FUTURES` + legacy `instrument_type=`/`@LIN` templates in
      `core/data_loader.py`. Bucket → canonical via `resolve_bucket_name` (data_loader + `dependency_checker` +
      `io/loader.py`, all were on the deprecated legacy bucket). Discovery → manifest-driven (`read_availability_index`
      `get_available_instruments` + `_check_single_dependency` `capture_status`). Spot/perp venue+symbol resolved
      date-scoped from v8 manifest (`_resolve_spot_perp` — avoids 2019 DERIBIT phantom + `{underlying}USDT`
      mis-encoding). `blob_exists`-guarded reads (honest absence). — features-service@4b7e57b1
- [x] ✅ [VALIDATE] P0. Real GCS (central-element-323112, prd): bucket resolves to `market-data-tick-cefi-prd-…`
      (canonical), manifest read (2.6M rows), spot perp → `BITGET-FUTURES:BTCUSDT`, **5,760 BTC spot rows loaded,
      0 NoneType/404 crashes**. `futures_chain` has no captured CEFI data on 2026-05-03 (honest absence, confirmed via
      manifest — captured data_types: trades/ohlcv_1m/derivative_ticker/book_snapshot_5/liquidations). basedpyright
      0 errors; 683 volatility unit tests pass. (WRITE P0 `write_daily_partition` deferred per Phase 1 finding —
      reaching write means read+calc worked.) — features-service@4b7e57b1
- [ ] 🟠 [IMPLEMENT] P1. **DEFERRED** — volatility `engine/orchestrator.py:263` + `core/orchestration_service.py:166`
      still scan raw chain files via `raw_tick_data/.../instrument_type={chain_type}/` + `list_blobs` (the
      `VolatilityFeaturesOrchestrator` engine path — a SEPARATE raw-chain-discovery surface from `VolatilityDataLoader`
      which reads `processed_candles`). Same legacy `instrument_type=` + raw-list bug class; migrate to manifest-driven
      raw-chain discovery. Out of Phase-2 scope (processed-candle read path); named here as the successor. Provenance:
      Phase 2 grep-clean sweep 2026-05-25.

### Phase 3 — cross_instrument `[P1]`

- [x] ✅ [IMPLEMENT] P1. `realized_implied_vol._fetch_iv_blobs_from_gcs` → **unbounded venue-scoped** discovery
      (deleted `list_blobs(max_results=100)` cap AND the `blobs[:10]` slice — a double silent truncation to the oldest
      lexicographic shards that could drop every in-range blob). Reads ALL venue shards + filters `[start_ts, end_ts]`.
      Regression test added (15 shards all read, no `max_results` passed). — features-service@1d30b8c5
- [x] ✅ [VALIDATE] P1. Real GCS (central-element-323112, prd): volatility IV output bucket resolves to
      `features-volatility-cefi-…`; unbounded discovery runs clean (0 IV blobs present → honest None, **0 crashes**).
      Full e2e is transitively blocked by the deferred delta_one WRITE P0 — cross_instrument batch handler ingests
      delta_one output as INPUT (`No delta-one features found under …` is the honest dependency error, not a read-path
      bug); this is the Phase 4 transitive unblock. basedpyright 0 errors; 514 cross_instrument unit tests pass; QG
      exit 0 (289s). — features-service@1d30b8c5

### Phase 4 — multi_timeframe (transitive unblock) `[P1]`

- [ ] [VALIDATE] P1. After Phase 1 writes delta_one features, confirm multi_timeframe reads them and computes. No code
      change expected; verify only.

### Phase 5 — shared lift (dedupe; aligns with epic goal) `[P2]`

- [ ] [REFACTOR] P2. Extract the manifest-driven discovery + dependency-gate into a shared UTL `FeatureBatchHandler` /
      `DataLoader` base (epic `features_and_ml_master` item 2 calls out this duplicated glue). Single code path; delete
      per-family copies.

### Phase 6 — Codex SSOT + governance `[P1]`

- [ ] [DOC] P1. Update `codex/02-data/availability-manifest-and-data-status.md` §"Expected-universe pre-flight chain":
      add the **features→MDPS** manifest-read contract row (currently only MTDS+MDPS are operationalized; features
      pre-flight is only a scope gate). Document features reading MDPS `capture_status`.
- [ ] [DOC] P1. Update `codex/02-data/data-lineage-MTDS-features-ml.md` to state features input discovery is
      manifest-driven (v8), not path-probe.

## Success criteria

- Each of delta_one / volatility / cross_instrument computes features **end-to-end on real recent GCS data** (parquet
  written + manifest `captured` + non-null feature columns read back). Data-pipeline completeness target ≥ 99.9% of
  captured instruments compute.
- No hardcoded `instrument_type=`/`@LIN`/`venue=BINANCE-FUTURES` input paths remain (grep-clean). No `max_results` cap
  on input discovery.
- Input discovery + pre-flight read the v8 manifest (`read_availability_index` / `capture_status`).
- `bash scripts/quality-gates.sh` exit 0 (features-service). All 8 `smoke_matrix.py` use a live date and pass for
  supported cells.

## Continuous verification

- smoke_matrix per family (post date-fix) wired into features-service QG smoke; run on a rolling recent date.
- Grep guard: no `instrument_type=`/`@LIN` literal in `features_service/*/` input paths; no `max_results=` on
  `processed_candles` discovery.

## Notes / cross-refs

- MTDS + MDPS are active on `live-defi-rollout` (clean trees as of 2026-05-25); MDPS recent commits change OHLCV
  schema/venue matching — reinforces manifest-driven (layout-agnostic) reading.
- Composes with HARD RULE _Data Pipeline Correctness Is The Heartbeat_ (features can't compute on real data today = RED
  for CeFi/TradFi feature path).
- `onchain` is the reference implementation; do not regress it.

### Feature-count + calc-verification findings (2026-05-25)

- [x] ✅ [VERIFY] Single-config feature count measured (delta_one, CEFI/15s/1-instrument, `--feature-group ALL`
      = the 17 CLI `FEATURE_GROUPS`): **9,895 output columns / 1,671 base features** (base = collapse `_lag_N`/period/
      `_in_last_N_bars`). All 17 groups compute cleanly on real BITGET data (trades/book_snapshot_5/derivative_ticker/
      liquidations). NOTE: the broader `CALCULATOR_REGISTRY` (~30 calcs) is NOT what `--feature-group ALL` runs
      (batch_handler.py:684 expands FEATURE_GROUPS only); an earlier 11,580 count over-counted by iterating the registry.
- [ ] 🟠 [BUG] P2. **2 latent polars-on-pandas bugs in ML-enhancement calculators** (NOT in the CLI `FEATURE_GROUPS`
      ALL-run; only in `CALCULATOR_REGISTRY`, the post-feature ML-enhancement path): `polynomial_trendline.py`
      (`df["high"].cast(pl.Float64)` — polars `.cast` on a pandas Series) and `wedge_quality.py`
      (`df.with_columns(...)` — polars on a pandas DataFrame). The orchestrator passes pandas, so these error when run.
      `risk_reward` is NOT a bug (declares an explicit ATR-dependency; needs VolatilityCalculator first); `vwap` is NOT
      a bug (works once the orchestrator sets the DatetimeIndex). Provenance: feature-count verification run 2026-05-25.
