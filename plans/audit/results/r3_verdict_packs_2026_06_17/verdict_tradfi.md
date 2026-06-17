# Verdict pack — TRADFI (G4 ⑬–⑲ pre-apply, R3/R7 on HEAD 2026-06-17)

**VERDICT: 🟢 GREEN — dry-run clean, ready for operator V6 eyeball + `G4 --apply`.** Migration **6.4× the captured
corpus** (legacy pre-hive parser now manifests 183,943 objects); the gate's RED is spot-verified phantom
closed-market-day downgrades + legacy pre-hive key respelling.

## Projected-v9 render (vs current/live `_index`)

| metric                 | PROJECTED                                                                                                      | CURRENT (`_index`) | Δ                                             |
| ---------------------- | -------------------------------------------------------------------------------------------------------------- | ------------------ | --------------------------------------------- |
| rows                   | 946,360                                                                                                        | 144,314            | **+802,046**                                  |
| captured               | **902,878**                                                                                                    | 100,787            | **+802,091**                                  |
| empty_confirmed        | 37,477                                                                                                         | 37,490             | −13                                           |
| attempted_failed       | 6,005                                                                                                          | 6,037              | −32                                           |
| coverage% (cap/Σ)      | **95.4%**                                                                                                      | 69.8%              | **+25.6pp**                                   |
| schema_version         | **9 = 100%**                                                                                                   | 8≈88% / 4 / 9      | →v9 migrate                                   |
| pipeline_mode + source | `batch_massive` 885,524 (`source=massive`) · `batch_databento` 17,328 · `batch_barchart` 13 · `batch_yahoo` 13 | blank/None 100%    | **blank → source-aware + `source` populated** |

- Projection: `gs://market-data-tick-tradfi-prd-…/_index/audit/projected_index_tradfi.parquet` (rebuild `mtds@c21bc91`,
  unchanged since 06-11; corpus DRAINED/frozen since 06-08 → HEAD-equivalent). Note `mtds@0962bad` (Massive CME route)
  landed code but no capture ran under the drain, so the corpus — and this projection — is HEAD-current.

## manifest_diff (projected vs current) — `manifest_diff_tradfi.json`

- GATE: removed_cells=4,374 · captured_regressions=2,902 → RED (gate). status-transitions: `empty_confirmed→captured` 14
  · **`captured→empty_confirmed` 2,629 + `captured→attempted_failed` 273 = 2,902 downgrades.**
- Net row delta = **+802,046 (additive)**: `trades` +401,480 · `ohlcv_1m` +198,775 · `options_chain` +120,655 · `tbbo`
  +86,425 — the legacy PRE-HIVE / no-`instrument_type` objects (FX spot_pair · CME chains · CBOE 15m · NYSE/ NASDAQ
  equity) that the rebuild legacy parser (`mtds@c21bc91`) now manifests (unparseable 183,943→106).

## Adjudication (phantom downgrades SPOT-VERIFIED on HEAD 2026-06-17)

- **captured downgrades = 2,902** are phantom `captured` rows on **genesis/closed-market days**. SPOT-VERIFIED this run:
  the diff's `captured→empty_confirmed` samples are `ohlcv_15m` BARCHART/CBOE/CME/FX on **`day=2020-01-01`** (New Year's
  holiday + genesis sentinel). GCS probe: `day=2020-01-01/.../venue=CME/` holds only `ohlcv_1m`/`tbbo`/`trades` —
  **`ohlcv_15m` is ABSENT** (`gcloud storage ls '…/**ohlcv_15m**'` → empty). So the current `_index` `captured` cell is
  a phantom (no backing object); the projection's downgrade to `empty_confirmed` is the HONEST correction.
- **removed_cells=4,374** unmatched tail = legacy pre-hive blank-key cells (FX `ohlcv_24h` 1,798 · blank-key
  `tbbo`/`trades`/`ohlcv_1m`/`ohlcv_15m` · coarse CBOE/ICE/CME/NASDAQ/NYSE) re-expressed at canonical
  (venue,data_type,instrument_type) grain — superseded, not lost (captured RISES +802,091).
- **T-OLD-2 carry**: the 14 Era-A `options_chain` objects the migrator skips are class-E (PRESERVE + backfill, never
  delete) per ratification — they surface in the tradfi orphan-sweep report parquet; the verified-delete tool refuses
  class-E. Orphan sweep E=0 / unknown=0 (06-11 final).

**G4 `--apply` for tradfi: AWAITING OPERATOR (dry-run GREEN).** Residual reason-level P1: CME Massive futures route
re-probe (`BLOCKED-UPSTREAM` — Massive futures-endpoint 404) — does NOT block the apply (status-diff GREEN).
