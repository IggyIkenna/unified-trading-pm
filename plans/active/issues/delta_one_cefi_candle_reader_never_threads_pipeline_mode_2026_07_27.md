---
doc_type: issue
title:
  "delta_one's CEFI candle-loading path never threads pipeline_mode — cannot find ANY real CEFI candle data (all current
  MDPS writes are pipeline_mode-partitioned)"
summary: >-
  Discovered while trying to PROVE the by_date/day= writer fix (features_by_date_root_canonicalisation_2026_07_21.md
  todo 6) green on a real day for delta_one CEFI. Every real-VM + direct-CLI attempt failed candle lookback validation
  with "0/N candles" or "No pre-loaded candles" for EVERY instrument tried — including
  HYPERLIQUID:PERPETUAL:BTC-USD@LIN, independently confirmed to have real, non-empty candle parquet (24 real 1h rows,
  real OHLCV) at
  gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2026-07-19/pipeline_mode=batch_hyperliquid/timeframe=1h/data_type=trades/instrument_type=PERPETUAL/venue=HYPERLIQUID/HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet.
  Root-caused: `features_service/delta_one/engine/orchestrator.py::_load_and_validate_candles` calls
  `DataLoader.load_candles_with_buffer(...)` WITHOUT a `pipeline_mode` argument (always defaults to `None`). UTL's
  `candle_read_prefixes()` (unified_trading_library/config_interface/paths/registry.py:436) explicitly documents: "Only
  emitted when `pipeline_mode` is supplied; when it is `None` only the pipeline_mode-less variants are returned." Direct
  `gcloud storage ls` sampling across 6+ distinct days (2026-05-04, 2026-05-22/23, 2026-06-26..29, 2026-07-19..21) shows
  EVERY current CEFI candle write under `processed_candles/by_date/day=*/` is pipeline_mode-partitioned
  (`pipeline_mode=batch_hyperliquid/`, `pipeline_mode=batch_aster/`, etc.) — there is no pipeline_mode-less variant left
  to fall back to for recent data. So the delta_one reader's `pipeline_mode=None` default structurally guarantees zero
  candles found for any CEFI instrument, regardless of whether real data exists.
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [features-service, unified-trading-library]
scope: [engineer, admin]
tags: [data-correctness, candles, pipeline_mode, delta_one, cefi, canonical, gcs-paths]
related:
  [
    /plans/active/issues/features_by_date_root_canonicalisation_2026_07_21.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-27 while proving features_by_date_root_canonicalisation_2026_07_21.md todo 6 (real-VM
  pipeline_e2e_check.py delta_one CEFI force+skip run + direct scoped CLI invocations) — real GCP infra, real GCS
  objects, not inferred.
---

# delta_one's CEFI candle reader never threads pipeline_mode — structural zero-candles bug

## What was found

While attempting to PROVE the delta_one/volatility `by_date/day=` writer fix
(`features_by_date_root_canonicalisation_2026_07_21.md` todo 6) green on a real day:

1. Launched the sanctioned `/data-pipeline-check-features` real-VM harness
   (`features-service/scripts/pipeline_e2e_check.py --day 2026-07-26 --asset-group CEFI --family delta_one --legs force,skip --auto-day --require-captured`).
   `--auto-day` resolved to window `2026-07-19..2026-07-20` (its own coverage check judged this window "fully covered").
   The VM (`features-e2e-cefi-20260727-083854-025349`) ran for ~30+ minutes, processing 552 CEFI instruments across many
   venues (BINANCE-FUTURES, COINBASE-SPOT, COINBASE-FUTURES, BITFINEX-FUTURES, HYPERLIQUID, …) — **every single
   instrument logged "No pre-loaded candles for X — skipping" or an equivalent no-data warning. Zero successful feature
   computations across the entire run.**
2. Independently reproduced with a direct, minimal CLI invocation (bypassing the VM):
   `python -m features_service.delta_one --operation compute --mode batch --asset-group CEFI --feature-group technical_indicators --timeframe 1h --start-date 2026-07-19 --end-date 2026-07-19 --instruments "HYPERLIQUID:PERPETUAL:BTC-USD@LIN"`
   (against the `-test-` sink bucket, `IS_TEST_RUN=true`). Result:
   `Lookback validation FAILED ... HYPERLIQUID:PERPETUAL:BTC-USD@LIN: 0/68 candles`.
3. Independently verified the underlying candle data DOES genuinely exist: downloaded
   `gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2026-07-19/pipeline_mode=batch_hyperliquid/timeframe=1h/data_type=trades/instrument_type=PERPETUAL/venue=HYPERLIQUID/HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet`
   directly and read it with pandas: **24 real rows**, real `timestamp`/`open`/`high`/`low`/`close`/`volume`/… columns,
   timestamps spanning `2026-07-19 01:00:00+00:00` to `2026-07-20 00:00:00+00:00`. The object is real, non-empty,
   correctly-shaped candle data — not a phantom/empty shard.
4. Root-caused the mismatch by reading the actual call chain:
   - `features_service/delta_one/engine/orchestrator.py::_load_and_validate_candles` (line ~709) calls
     `self.data_loader.load_candles_with_buffer(instrument_id=..., data_type=..., start_date=..., end_date=..., buffer_days=..., timeframe=...)`
     — **no `pipeline_mode` kwarg at all**, so `DataLoader`'s default (`pipeline_mode: str | None = None`) always
     applies for this call site.
   - `DataLoader._resolve_blob_paths` / `_canonical_candle_blob_paths` thread `pipeline_mode` down to UTL's
     `candle_read_prefixes()` (`unified_trading_library/config_interface/paths/registry.py:436`), whose own docstring
     states plainly: _"pipeline_mode: WITH the `pipeline_mode=` segment ... then WITHOUT it ... Only emitted when
     `pipeline_mode` is supplied; when it is `None` only the pipeline_mode-less variants are returned."_
   - Sampled 6+ distinct real days directly via `gcloud storage ls` on
     `market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=*/` (2026-05-04, 2026-05-22,
     2026-05-23, 2026-06-26, 2026-06-27, 2026-06-28, 2026-06-29, 2026-07-19, 2026-07-20, 2026-07-21): **every single
     day's candle objects sit under a `pipeline_mode=*/` segment** (`batch_hyperliquid`, `batch_aster`, `batch_tardis`
     per the related canonical-path-divergence doc's earlier findings) — **no pipeline_mode-less variant exists for any
     recent CEFI day sampled.**
   - Conclusion: `_load_and_validate_candles`'s `pipeline_mode=None` default is **structurally guaranteed to find zero
     candles** for any CEFI instrument right now, because the only real-object shape has moved to
     pipeline_mode-partitioned and the reader never tries it.

## Why this matters (do not descope)

This is a **CEFI delta_one feature-computation-blocking bug** — independent of, and NOT introduced by, the
`features_by_date_root_canonicalisation_2026_07_21.md` `by_date/day=` writer-path fix (that fix is separately
unit-test-verified correct — 30/30 tests pass, explicitly asserting the `delta_one/by_date/` and `volatility/by_date/`
prefixes). This candle-reader gap means **delta_one CEFI feature computation cannot succeed against ANY
currently-written real CEFI candle data**, via either the VM launcher's bulk-preload path or the CLI's per-instrument
fallback path — a genuine, severe, silent data-pipeline correctness gap (features that should compute from real data
instead silently produce nothing, logged only as unremarkable per-instrument WARNINGs that are easy to miss at scale).

**Related but distinct** from `candle_feature_canonical_path_divergence_2026_07_20.md` (which documents the WRITER side
emitting both pipeline_mode-partitioned and pipeline_mode-less shapes on the same day, and that doc's todo 5 claims the
reader was already fixed to "dual-read via `candle_read_prefixes`" — but that fix evidently did not thread a real
`pipeline_mode` value into THIS specific call site, or the pipeline_mode-less shape it relied on falling back to has
since disappeared from recent days as writes fully migrated to pipeline_mode-partitioned).

**Not yet traced**: the exact bulk-preload mechanism the VM run's "No pre-loaded candles" path uses (distinct code path
from `_load_and_validate_candles`, invoked when a `preloaded_candles` dict is passed in) — it produces the same
zero-candles symptom for the same instruments/days, consistent with the same root cause, but its own source wasn't
located in `features_service/delta_one/` (likely lives in a shared bulk-loader, `unified_trading_library`, or the batch
handler's setup code not yet grepped). The fix-todo below should trace and fix BOTH paths.

## Todos

- [x] ✅ 1. [DATA] P0. Traced and fixed `_load_and_validate_candles`'s candle-loading call chain to pass a real
      `pipeline_mode` value. Added `OrchestrationService._resolve_read_pipeline_mode` (mirrors todo 2's
      `_tf_cluster_helper._resolve_read_pipeline_mode` pattern) using the sanctioned UTL
      `resolve_pipeline_mode(service, mode, venue, asset_group=, data_type=)` resolver — venue = the instrument_id's
      `VENUE:TYPE:SYMBOL` first segment. `_load_and_validate_candles` now resolves + threads `pipeline_mode` into
      `DataLoader.load_candles_with_buffer(...)`; returns `None` (skip, never raise) when unresolvable — shard-level
      failure isolation preserved. Added `tests/delta_one/unit/test_load_and_validate_candles_pipeline_mode.py` (real,
      unstubbed resolver proving `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` → `batch_hyperliquid`, plus a mocked-data_loader
      test asserting `load_candles_with_buffer` is called WITH `pipeline_mode=` — the exact regression scenario). Full
      `quality-gates.sh` green (17900 passed, 0 failed; sentinel-verified). features-service@e9430f0d. Filed a separate
      flaky-gate finding while shipping (2 of 4 full QG runs failed on an unrelated 60s-timeout in STEP 5.83's
      adapter-contract-call ratchet under shared-host contention, confirmed the check itself passes standalone —
      `/plans/active/issues/adapter_contract_regression_ratchet_60s_timeout_flaky_under_contention_2026_07_27.md`).
- [x] ✅ 2. [DATA] P0. Located and fixed the bulk-preload mechanism — CONFIRMED same root cause. Located in
      `features_service/delta_one/cli/handlers/_tf_cluster_helper.py`: `_load_base_candles` and
      `_load_one_instrument_range` both call `DataLoader.load_candles_with_buffer(...)` without `pipeline_mode`,
      identical bug to `_load_and_validate_candles` (todo 1). Fixed via a new `_resolve_read_pipeline_mode` helper using
      the sanctioned UTL `resolve_pipeline_mode(service, mode, venue, asset_group=, data_type=)` resolver (venue = the
      instrument_id's `VENUE:TYPE:SYMBOL` first segment, same convention `DataLoader._resolve_blob_paths` already uses);
      threaded `asset_group` through both functions (already in scope at both call sites). Added
      `tests/delta_one/unit/test_resolve_read_pipeline_mode.py` (real, unstubbed resolver — proves
      `HYPERLIQUID:PERPETUAL:BTC-USD@LIN` → `batch_hyperliquid`, the exact regression scenario) + updated
      `test_tf_cluster_helper.py`'s existing coverage for the new `asset_group` parameter. Full `quality-gates.sh` green
      (sentinel-verified). features-service@2c6062ab.
- [ ] 3. [DATA] P1. Once fixed, re-run the real-day proof for `features_by_date_root_canonicalisation_2026_07_21.md`
      todo 6 (delta_one + volatility force/skip legs) — this issue is what's currently blocking that proof.
- [ ] 4. [DATA] P2. Check whether the SAME `pipeline_mode=None` gap affects other CEFI-reading call sites in
      features-service (cross_instrument, multi_timeframe) or other asset groups where MDPS candle writes have also
      fully migrated to pipeline_mode-partitioned shapes.

## Progress Log

- **2026-07-27** — Filed while working `features_by_date_root_canonicalisation_2026_07_21.md` todo 6 (real-day proof).
  Root-caused via direct code read + real GCS verification (not inferred). Did not attempt the fix in this pass — out of
  scope for the by_date/day= writer-proof task this was discovered under, and the bulk-preload path's fix location needs
  its own investigation. Real-VM check (`features-e2e-cefi-20260727-083854-025349`) was left running in the background
  against the `-test-` bucket (no prod mutation) — expected to eventually report `PROVED NOTHING` per this root cause;
  its report can serve as further corroborating evidence once it completes.
- **2026-07-27** — Todo 1 shipped: `features-service@e9430f0d`. Full `quality-gates.sh` green (pytest 17900 passed/0
  failed, basedpyright clean, adapter-contract-call ratchet clean). Both delta_one CEFI candle-reader paths (the
  bulk-preload path from todo 2 and the per-instrument path from this todo) now thread a resolved `pipeline_mode`. Todo
  3 (re-run the real-day proof for `features_by_date_root_canonicalisation_2026_07_21.md` todo 6) is now unblocked.
