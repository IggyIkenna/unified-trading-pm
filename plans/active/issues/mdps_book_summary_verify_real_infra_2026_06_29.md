---
doc_type: issue
title: MDPS book-summary precompute — [VERIFY] real-infra run deferred (BINANCE-FUTURES one-day shard)
summary:
  The [SPEC]/[IMPLEMENT]/[TEST]/[AGENT] todos of `mdps_book_microstructure_precompute_columns_2026_06_28.md` are ✅
  shipped (UAC@40e318aa + MDPS@73054e5+@a90669be+@2bfcbaca). The [VERIFY] gate ("Full-run on a real BINANCE-FUTURES book
  shard one day on real infra; read parquet back; assert column distributions sane") was deferred — needs a dedicated VM
  run.
status: resolved
nature: notes
stage: [data]
repos: [market-data-processing-service]
scope: [engineer]
tags: [mdps, book-microstructure, verify, real-infra]
related:
  [
    ../mdps_book_microstructure_precompute_columns_2026_06_28.md,
    ../features_read_book_columns_not_snapshots_2026_06_28.md,
  ]
created: 2026-06-29
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    "operator decision on block BLK-4e9d1df9 (2026-06-29) — chose Option A: defer + file issue doc + actionable todo",
    "plans/active/mdps_book_microstructure_precompute_columns_2026_06_28.md § [VERIFY] P1",
  ]
assigned_vm: planning
resolved_by: market-data-processing-service@54cc99d
locked_by: live-defi-rollout
asset_group: [cefi]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# [VERIFY] real-infra run deferred — MDPS book-summary precompute

## What I found

The implementation work for `mdps_book_microstructure_precompute_columns_2026_06_28.md` is fully shipped + QG-green:

- **UAC**: `CandleOutput` extended with 25 nullable `book_*` fields mirroring `BOOK_SUMMARY_COLUMN_NAMES`.
  (`unified-api-contracts@40e318aa`)
- **MDPS**: 25-col schema added to `PROCESSED_CANDLE_SCHEMA` via `*_book_summary_column_schemas()`;
  `PROCESSED_CANDLE_SCHEMA_VERSION` 1.0 → 1.1. (`market-data-processing-service@73054e5`)
- **MDPS**: intra-bar time-weighted aggregation implemented in
  `CefiBookSnapshotAdapter._calculate_book_summary_features()` + five `_fill_*_cols` helpers (inherited by
  `DefiBookSnapshotAdapter`). (`market-data-processing-service@a90669be`)
- **MDPS**: 12 unit/property tests in `tests/unit/test_book_summary_aggregation.py` cover TW-mean/std, right-edge
  convention, n=0/1 null rules, close-columns, per-level depth mapping, sign-persist, microprice tilt edges.
  (`market-data-processing-service@2bfcbaca`)
- Both repos' `quality-gates.sh` GREEN; CI `quality-gates-v2` SUCCESS on `live-defi-rollout` for both.

The remaining [VERIFY] gate explicitly requires a real-infra full-day run:

> Full-run on a real BINANCE-FUTURES book shard (one day) on real infra; read the output parquet back and assert the
> column distributions are sane (spread > 0, imbalance ∈ [-1,1]). — Gate: per CLAUDE.md "Plans Run To Actual Completion"
> — name the command + GCS path + observed column stats.

That is a multi-hour VM-lifecycle task (provision MDPS process VM, point at a specific BINANCE-FUTURES day, invoke
`process --operation candles --mode batch --asset-group cefi --data-types book_snapshot_5`, drain to GCS, read back) —
not deliverable inside a single in-session worker turn with the context budget I have remaining. Operator chose **option
A** on block `BLK-4e9d1df9`: defer the gate to a dedicated worker.

## Why it matters

- The four upstream todos depend on this column set behaving correctly on real L5 book data, not just synthetic ticks.
  The unit tests prove math correctness but cannot prove production data has the columns populated with sane stats
  (spread > 0, imbalance ∈ [-1, 1], depth columns finite, etc.).
- Plan 2 (`features_read_book_columns_not_snapshots_2026_06_28.md`) is the downstream consumer that re-points the ~100
  microstructure features at candle columns instead of book ticks. That parity assertion is the GATE for Plan 2 — but
  Plan 2 cannot ship before this [VERIFY] passes on real infra.

## Recommended decision

Run [VERIFY] on a named one-day BINANCE-FUTURES book_snapshot_5 shard (operator or worker to pick the day). Operator
inputs needed before the worker can run:

- **Target GCS bucket** (which mdps-input-_ / mtds-raw-_ bucket holds the upstream book_snapshot_5 ticks for
  BINANCE-FUTURES?)
- **Target day** (one day with known-dense book traffic — e.g. a recent BTCUSDT day, ≥10k snapshots)
- **Output bucket** for the processed candles (mdps-processed-candles-\*)

Once the worker has those, the verification script is straightforward.

## Actionable todos

- [x] [VERIFY] P1. Run MDPS `process --operation candles --mode batch --asset-group cefi --data-types book_snapshot_5`
      for ONE named BINANCE-FUTURES day on a fresh MDPS VM. Read the output parquet back; assert: (a) all 25 new
      `book_*` columns present, (b) `book_spread_bps_tw_mean` > 0 for bars with data, (c) `book_imbalance_tw_mean` ∈
      [-1, 1], (d) `book_*_close` columns present and finite where source data exists, (e) NULL rows for bars with zero
      in-bar snapshots. Cite command + GCS input/output paths + observed column stats (mean/min/max per column). Update
      the parent plan's [VERIFY] checkbox on completion. (repo: market-data-processing-service)
      ✅ market-data-processing-service@54cc99d — BTCUSDT perpetual 2020-02-19; 7,615 candles (✅1 ❌0); bucket
      `market-data-tick-cefi-test-central-element-323112`; all 5 assertions passed at 15s (5760 rows) + 1m (1440 rows).
      Parent plan [VERIFY] checkbox flipped. Root-cause fix also shipped: COLUMN_AGG_RULES was missing all 25 book_*
      columns → Polars group_by_dynamic silently dropped them for 1m+ timeframes.
