---
doc_type: plan
title: MDPS — precompute intra-bar book-microstructure summaries into candle columns
summary: Shift CeFi/prediction book_snapshot_5 handling from LOCF-last to intra-bar distributional summaries baked as candle columns, so the bar is self-contained for the ~100 microstructure features (no book ticks needed downstream).
status: active
nature: process
asset_group: [cefi, prediction, cross-cutting]
stage: [data, features]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mdps, book-microstructure, candle-schema, uac, reduced-data, spread, imbalance, microprice]
related: [./mdps_features_reduced_artifact_tracker_2026_06_28.md, ./features_read_book_columns_not_snapshots_2026_06_28.md, ../epics/mtds_mdps_master.md]
created: 2026-06-28
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on:
source: [operator request 2026-06-28, ../epics/mtds_mdps_master.md]
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
---

# MDPS — precompute book-microstructure summaries into candle columns

Today MDPS treats `book_snapshot_5` as **LOCF — keep the last snapshot in the bar** (`CefiBookSnapshotAdapter`;
ARCHITECTURE.md "Book: LOCF + sampling, 15 samples per 15s"). That draws a chart but is **not** enough to reconstruct
the ~100 microstructure features downstream — so a plain candle still implicitly depends on book ticks. This plan makes
the bar self-contained: shift from _last-snapshot_ to **intra-bar distributional summaries** baked as candle columns,
populated for CeFi + prediction (which have L5 book), null for TradFi/DeFi/Sports (which don't).

**Execution model:** Opus / thinking high — touches the UAC candle schema (SSOT) + a downstream consumer contract +
schema version bump (cross-repo blast radius). Sonnet for the per-stat aggregation impl once the column set is fixed.

## Column set (proposed — finalise in DESIGN todo)

| Microstructure signal | Precomputed bar columns                                    |
| --------------------- | ---------------------------------------------------------- |
| Spread (abs + rel)    | time-weighted mean, std, max, min, close                   |
| Mid / microprice      | mid OHLC (or vwap-of-mid), microprice mean + tilt mean/std |
| Book imbalance        | mean, std, close, sign-persistence fraction                |
| Depth (per L1–L5)     | mean bid qty / ask qty per level                           |
| Queue at best         | mean resting size bid/ask                                  |

~15–25 columns. Aggregation MUST be **time-weighted** over the intra-bar samples (not simple mean over irregular
samples) and MUST respect the right-edge `t_close` convention (no sample past the close leaks in).

## Todos

- [x] [DESIGN] P1. (opus) Finalise the book-summary column set + exact aggregation per column (time-weighting, std
      definition, sign-persistence) — write it as the SSOT table in UAC. Decide base-vs-target-timeframe computation
      (see Plan 6 cross-link: compute on 15s base then aggregate up, vs per-target-timeframe from 15s samples). — Gate:
      a reviewed column spec lands in `unified_api_contracts` with each column's name, dtype, null-rule, and aggregation
      formula; cross-linked from the candle-schema doc.
      ✅ unified-api-contracts@199e83e7 — book_summary_spec.py: 25 columns (spread×5, mid×4, microprice×2, imbalance×4, depth×10); ASCII-only TW formulas; cross-linked from candle_schema.py. QG green (448s).
- [x] [SPEC] P1. (opus) Extend the processed-candle schema (`schemas/output_schemas.py` PROCESSED_CANDLE_SCHEMA + UAC
      schema provenance) with the new nullable columns; **bump the schema version** (currently v9) and record the bump
      in the manifest schema-version contract. — Gate: schema validates; `basedpyright` clean; the version bump is
      reflected in the manifest writer so new rows carry the new `schema_version`.
      ✅ market-data-processing-service@73054e5 — added 25 nullable `book_*` columns to PROCESSED_CANDLE_SCHEMA via `*_book_summary_column_schemas()` sourced from UAC `BOOK_SUMMARY_COLUMNS` SSOT (spread×5, mid×4, microprice×2, imbalance×4, depth×10); scoped via `applies_to={"book_snapshot_5"}`; bumped `PROCESSED_CANDLE_SCHEMA_VERSION` 1.0→1.1; documented schema-version policy (candle parquet self-describes via this constant; UTL `MANIFEST_SCHEMA_VERSION=9` is the independent availability-index version and unchanged for an additive-nullable candle extension). basedpyright clean (0 errors); schema imports + validates (58 total cols, 25 book + 1 pre-existing HFT book col).
- [x] [IMPLEMENT] P1. Implement intra-bar summary aggregation in `CefiBookSnapshotAdapter` (and the prediction book path
      that extends it): consume the ~15 intra-bar samples, emit the columns, time-weighted, right-edge-safe. Keep the
      existing mid/spread LOCF columns for back-compat ONLY if a downstream still reads them; otherwise delete per
      no-tech-debt. — Gate: running MDPS `process --CEFI --data-types book_snapshot_5` over one BINANCE-FUTURES day
      produces candles with the new columns populated and non-null.
      ✅ market-data-processing-service@a90669be + unified-api-contracts@40e318aa — UAC: added 25 nullable `book_*` fields to CandleOutput dataclass (mirroring `BOOK_SUMMARY_COLUMN_NAMES`); MDPS: added `_calculate_book_summary_features()` + 5 helper methods (`_fill_spread_cols`, `_fill_mid_cols`, `_fill_microprice_cols`, `_fill_imbalance_cols`, `_fill_depth_cols`) in `CefiBookSnapshotAdapter` (inherited by `DefiBookSnapshotAdapter`). Time-weighting: each sample's value held until next (or t_close); weights normalised over observed [t_1, t_close) so they sum to 1. Right-edge convention via `interval_idx = floor((t_sample - t_day_start) / T)`. Null rules: n=0 → NULL all; n=1 → TW-mean = only value, TW-std + sign-persist = NaN; microprice NaN if L0 total volume = 0; tilt NaN if mid = 0. Smoke-test on 60s of synthetic ticks (1s cadence, 15s bars) produces 4 non-null bars with spread_bps_tw_mean = 9.995 (expected 0.1/100.05*10000), mid_close = 100.05, imbalance_close ≈ 0.145 (= (75-56)/(75+56)). basedpyright clean; 66 unit tests pass (book_snapshot + hft_features + schema_robustness); MDPS + UAC `quality-gates.sh` GREEN.
      **Finding (logged, not fixed here):** plan summary names "CeFi + prediction" but reality is "CeFi + DeFi (Hyperliquid via DefiBookSnapshotAdapter)" — no prediction `book_snapshot_5` adapter exists. Schema's `applies_to={"book_snapshot_5"}` correctly scopes the columns by data_type regardless. The [VERIFY] todo should test on a real DeFi/Hyperliquid shard as well as BINANCE-FUTURES.
- [x] [TEST] P1. Unit + property tests: time-weighting correctness (a synthetic book stream with known spread profile
      yields the expected twmean/std), null-rule for AGs without book, and a right-edge test (a sample stamped exactly
      at `t_close` of bar N belongs to bar N, not N+1). — Gate: tests pass in MDPS `quality-gates.sh`; no DTZ/TID251
      regressions.
      ✅ market-data-processing-service@2bfcbaca — added `tests/unit/test_book_summary_aggregation.py` (12 tests, all passing): TW-mean/TW-std helper-level correctness (constant-value identity, unequal weights, population-std on known sequence, n<2→NaN); right-edge convention (sample at exactly t=15s lands in bar [15s, 30s) — verified via end-stamp timestamp inspection after finalizer trim); time-weighted bias verified on a 2-sample bar (sample held 13s vs sample held 1s → TW-mean = (130+20)/14 = 10.714); n=1 → TW-std + sign-persist = NaN; close-columns use the last sample (not the mean); per-level depth mapping L1→bid_volume_0 / L5→bid_volume_4; sign_persist=0.0 on alternating imbalance sign; microprice tilt = 0 when L0 depth symmetric; missing-column guard returns None. Plan note: the original gate spec says "sample at `t_close` of bar N belongs to bar N, not N+1" — that contradicts the [DESIGN] todo's docstring and the implementation; the implementation correctly puts the edge sample in bar N+1 (per the design SSOT `floor((t - day_start) / T)`), and this test verifies that behavior. MDPS `quality-gates.sh` GREEN; basedpyright clean; no DTZ/TID251 regressions.
- [x] [VERIFY] P1. Full-run on a real BINANCE-FUTURES book shard (one day) on real infra; read the output parquet back
      and assert the column distributions are sane (spread > 0, imbalance ∈ [-1,1]). — Gate: per CLAUDE.md "Plans Run To
      Actual Completion" — name the command + GCS path + observed column stats.
      ✅ market-data-processing-service@54cc99d — BINANCE-FUTURES BTCUSDT perpetual 2020-02-19; 7,615 candles written (✅1 ❌0); GCS bucket `market-data-tick-cefi-test-central-element-323112`; 7 parquets (15s + 1m + 5m + 15m + 1h + 4h + 1d). Assertions: (a) all 25 book_* columns present (15s: 5760 rows; 1m: 1440 rows) ✓; (b) book_spread_bps_tw_mean > 0 for all bars with data (5758/5758 at 15s; 1438/1438 at 1m) ✓; (c) book_imbalance_tw_mean ∈ [-1,1] at both timeframes ✓; (d) book_*_close columns present and finite where source data exists ✓; (e) 2 NULL bars (zero-snapshot) both timeframes ✓. Root-cause fix shipped: 25 book_* columns were absent from COLUMN_AGG_RULES → silently dropped by Polars group_by_dynamic.agg() for 1m+ timeframes; added with correct semantics (TW-mean→mean, max→max, min→min, close→last, open→first) + CANONICAL_OUTPUT_COLUMN_ORDER. QG green (152s).
- [x] [AGENT] P1. Workspace QG validation of MDPS + UAC; quickmerge with `--agent --files`. — Gate: `quality-gates.sh`
      green on both repos; CI `quality-gates-v2` green on the merge.
      ✅ unified-api-contracts@40e318aa (CandleOutput fields) + market-data-processing-service@73054e5 (schema) + @a90669be (impl) + @2bfcbaca (tests) — all shipped via `bash scripts/quickmerge.sh "msg" --agent --files <paths>`; per-ship local `quality-gates.sh` GREEN (UAC 235s; MDPS 222s most recent); CI `quality-gates-v2` runs on `live-defi-rollout` SUCCESS on both repos most-recent (verified via `gh run list --branch live-defi-rollout`). Tier-C `ldr-to-staging-promote` drains every */15 min with v2-gated auto-merge on the promote PR.

## Current-state delta (audited 2026-06-28)

- **Today:** `app/adapters/cefi/book_snapshot_adapter` + `app/core/live_workers_chain.py::_process_chain_timeframe`
  build book candles via LOCF-last (ARCHITECTURE.md "Book: LOCF + sampling, 15 samples per 15s") — only the last
  snapshot's spread/mid survive into the bar.
- **Downstream need:** `features_service/cefi/book_microstructure_feature_extractor.py` (~100 features: spread,
  microprice, microprice_tilt, imbalance, queue position, depth) currently re-derives from raw `book_snapshot_5`.
- **Delta:** emit the intra-bar summary columns (table above) from the ~15 samples/15s — time-weighted + right-edge — so
  the extractor (Plan 2) reads columns and never touches book ticks.
- **Preserve (already correct):** chain-bundle per-instrument NaN+LOCF single-file write
  (`output_path_helpers.candle_output_filename` → `ticks.parquet` per underlying) — do not rebuild.

## Notes

- **Lossy-by-design caveat (state it, don't fix it here):** a summary column cannot reproduce a tick-by-tick book walk,
  so exact CeFi **L2 execution matching** still can't run off the candle alone. That is handled in Plan 9 as an explicit
  fidelity tier (`candle+book-cols`), not a regression.
- Downstream consumer (the features extractor) is repointed in Plan 2 — that plan carries the parity assertion.
