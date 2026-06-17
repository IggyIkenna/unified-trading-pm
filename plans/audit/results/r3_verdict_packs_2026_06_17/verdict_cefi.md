# Verdict pack — CEFI (G4 ⑬–⑲ pre-apply, R3/R7 on HEAD 2026-06-17)

**VERDICT: 🟢 GREEN — dry-run clean, ready for operator V6 eyeball + `G4 --apply`.** Migration nearly **doubles captured
coverage** (CF-11 honest-absence re-emit + processed pass-through); the gate's RED is the dispatch-named garbage class +
spot-verified phantom downgrades + CF-11 by-design reclassifies.

## Projected-v9 render (vs current/live `_index`)

| metric            | PROJECTED                                                                         | CURRENT (`_index`)    | Δ                        |
| ----------------- | --------------------------------------------------------------------------------- | --------------------- | ------------------------ |
| rows              | 3,886,859                                                                         | 2,728,435             | **+1,158,424**           |
| captured          | **2,491,437**                                                                     | 1,332,922             | **+1,158,515**           |
| empty_confirmed   | 150                                                                               | 109,259               | −109,109                 |
| attempted_failed  | 1,395,272                                                                         | 1,286,254             | +109,018                 |
| coverage% (cap/Σ) | **64.1%**                                                                         | 48.9%                 | **+15.2pp**              |
| schema_version    | **9 = 100%**                                                                      | 8≈95% / 6 / 5 / 4 / 9 | →v9 migrate              |
| pipeline_mode     | `batch_tardis` 3.82M · `batch_hyperliquid` 49.5K · `batch_hyperliquid_rest` 19.4K | blank/None 100%       | **blank → source-aware** |

- Projection: `gs://market-data-tick-cefi-prd-…/_index/audit/projected_index_cefi.parquet` (rebuild `mtds@03fbc9b`,
  unchanged since 06-11; market-data corpus DRAINED/frozen since 06-08 → HEAD-equivalent).

## manifest_diff (projected vs current) — `manifest_diff_cefi.json`

- GATE: removed_cells=733 · captured_regressions=375 → RED (gate). status-transitions: `attempted_failed→captured` 140 ·
  `empty_confirmed→captured` 70 · `empty_confirmed→attempted_failed` 3,981 (CF-11 GUARANTEED_WHEN_LISTED by design) ·
  **`captured→attempted_failed` 375 downgrades.**
- Net row delta = **+1,158,424 (additive)**: `trades` +668,960 · `book_snapshot_5` +331,453 · `derivative_ticker`
  +112,326 · `liquidations` +50,346 — the CF-11 honest-absence corpus that the pre-CF-11 pure object-scan dropped.

## Adjudication

- **removed_cells=733 = the dispatch-named GARBAGE class** (06-11 verified): `venue=UNKNOWN` + Bitfinex `F0`
  symbols-as-venue (`BTCF0`/`ETHF0`/`DOTF0`/…) — **0 GCS objects under any such venue path** → expected removals.
- **captured downgrades = 375** (was 943 on 06-11 — fewer now, the 06-14 consolidation already corrected some): genuine
  phantom `captured` rows with **no backing object** (06-11 spot-verified: BINANCE-SPOT 2021-01-04 BTCUSDC has `trades`
  objects but NO `book_snapshot_5` object). The projection's downgrade to `attempted_failed` is the HONEST correction,
  presented (not suppressed). The unmatched-removed tail (OKX/BINANCE/BYBIT/UPBIT with **blank data_type**) are coarse
  legacy keys re-expressed at canonical (venue,data_type) grain.
- `empty_confirmed→attempted_failed` 3,981 = the CF-11 within-bounds `GUARANTEED_WHEN_LISTED` reclassification (BY
  DESIGN — a listed-but-no-data cell is `attempted_failed`, not `empty_confirmed`).
- Orphan sweep E=0 / unknown_prefixes=0 (06-11 final). captured count RISES +1.16M — no net loss.

**G4 `--apply` for cefi: AWAITING OPERATOR (dry-run GREEN).**
