---
doc_type: plan
title: MDPS — precompute intra-bar book-microstructure summaries into candle columns
summary:
  "Shift CeFi/prediction book_snapshot_5 handling from LOCF-last to intra-bar distributional summaries baked as candle
  columns, so the bar is self-contained for the ~100 microstructure features (no book ticks needed downstream)."
status: active
nature: process
asset_group: [cefi, prediction, cross-cutting]
stage: [data, features]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer, admin]
tags: [mdps, book-microstructure, candle-schema, uac, reduced-data, spread, imbalance, microprice]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ./features_read_book_columns_not_snapshots_2026_06_28.md,
    ../epics/mtds_mdps_master.md,
  ]
created: 2026-06-28
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: design
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on:
source: [operator request 2026-06-28, ../epics/mtds_mdps_master.md]
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
- [ ] [SPEC] P1. (opus) Extend the processed-candle schema (`schemas/output_schemas.py` PROCESSED_CANDLE_SCHEMA + UAC
      schema provenance) with the new nullable columns; **bump the schema version** (currently v9) and record the bump
      in the manifest schema-version contract. — Gate: schema validates; `basedpyright` clean; the version bump is
      reflected in the manifest writer so new rows carry the new `schema_version`.
- [ ] [IMPLEMENT] P1. Implement intra-bar summary aggregation in `CefiBookSnapshotAdapter` (and the prediction book path
      that extends it): consume the ~15 intra-bar samples, emit the columns, time-weighted, right-edge-safe. Keep the
      existing mid/spread LOCF columns for back-compat ONLY if a downstream still reads them; otherwise delete per
      no-tech-debt. — Gate: running MDPS `process --CEFI --data-types book_snapshot_5` over one BINANCE-FUTURES day
      produces candles with the new columns populated and non-null.
- [ ] [TEST] P1. Unit + property tests: time-weighting correctness (a synthetic book stream with known spread profile
      yields the expected twmean/std), null-rule for AGs without book, and a right-edge test (a sample stamped exactly
      at `t_close` of bar N belongs to bar N, not N+1). — Gate: tests pass in MDPS `quality-gates.sh`; no DTZ/TID251
      regressions.
- [ ] [VERIFY] P1. Full-run on a real BINANCE-FUTURES book shard (one day) on real infra; read the output parquet back
      and assert the column distributions are sane (spread > 0, imbalance ∈ [-1,1]). — Gate: per CLAUDE.md "Plans Run To
      Actual Completion" — name the command + GCS path + observed column stats.
- [ ] [AGENT] P1. Workspace QG validation of MDPS + UAC; quickmerge with `--agent --files`. — Gate: `quality-gates.sh`
      green on both repos; CI `quality-gates-v2` green on the merge.

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
