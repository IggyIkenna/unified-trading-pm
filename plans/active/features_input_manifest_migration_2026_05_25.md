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

## Phases (DAG; QG gate between each)

### Phase 0 — Pre-audit + golden baseline `[P0]`

- [ ] [AUDIT] P0. Confirm actual canonical layout per asset_group from real GCS (CEFI done: `venue=BITGET-*`,
      `data_type=trades`, no `instrument_type=`/`@LIN`). Repeat for TRADFI/DEFI/PREDICTION input buckets. Record
      verified recent test dates with populated buffer day per asset_group.
- [ ] [AUDIT] P0. Snapshot expected instrument universe + captured shards from the v8 manifest for the chosen test dates
      (the golden set each family's discovery must reproduce).
- [ ] [SCRIPT] P1. Fix smoke_matrix stale default date — `DEFAULT_SMOKE_DATE = "2024-06-15"` has **no data**, so all 8
      `scripts/*/smoke_matrix.py` silently fail. Replace with a dynamic recent-date resolver (latest date with manifest
      `captured` rows). Provenance: this masked the bugs.

### Phase 1 — delta_one (reference fix; confirmed-broken) `[P0]`

- [ ] [IMPLEMENT] P0. Replace `get_available_instruments()` blob scan (BUG-1) with manifest-driven discovery scoped to
      the target date (`read_availability_index` → captured instruments for `(date, data_type)`). Delete
      `max_results=100`.
- [ ] [IMPLEMENT] P0. Rewire `dependency_checker._sum_candles_over_days` (BUG-2) to gate on manifest `capture_status` +
      recorded row counts instead of probing the legacy `instrument_type=`/`@LIN` path. Delete the legacy path template.
- [ ] [VALIDATE] P0. Verify `data_loader._build_blob_path` canonical path matches real layout; confirm legacy-fallback
      still covered or deleted (no parallel paths).
- [ ] [VALIDATE] P0. **Full-execution criterion:** run CLI `--operation compute --feature-group ALL --asset-group CEFI`
      on a verified date end-to-end → ≥1 feature_group parquet written to test bucket + manifest row `captured`; read
      back parquet, assert non-null feature columns. Repeat TRADFI/DEFI/PREDICTION where input exists.

### Phase 2 — volatility `[P0]`

- [ ] [IMPLEMENT] P0. Delete hardcoded `venue=BINANCE-FUTURES` + legacy `instrument_type=`/`@LIN` templates in
      `core/data_loader.py` (lines ~100/168/231/290). Replace input discovery + path resolution with manifest-driven
      `(venue, data_type, instrument)` lookup.
- [ ] [VALIDATE] P0. End-to-end compute on verified date (CEFI/TRADFI) → parquet + `captured` manifest + non-null
      columns read-back.

### Phase 3 — cross_instrument `[P1]`

- [ ] [IMPLEMENT] P1. Replace `realized_implied_vol.py:157` `max_results=100` IV-blob scan with manifest-driven (or
      unbounded date-scoped) discovery.
- [ ] [VALIDATE] P1. End-to-end compute on verified date → parquet + manifest + read-back.

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
