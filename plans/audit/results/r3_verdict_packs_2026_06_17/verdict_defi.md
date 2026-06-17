# Verdict pack — DEFI (G4 ⑬–⑲ pre-apply, R3/R7 regenerated on HEAD 2026-06-17)

**VERDICT: 🟢 GREEN — dry-run clean, ready for operator V6 eyeball + `G4 --apply`.** Migration is **net-additive +
canonicalising with ZERO net captured loss**; the gate's RED is legacy data_type/venue supersession + spot-verified
phantom corrections, not data loss.

## Projected-v9 render (vs current/live `_index`)

| metric            | PROJECTED (HEAD)                                                                                                   | CURRENT (`_index`) | Δ                        |
| ----------------- | ------------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------------ |
| rows              | 1,910,046                                                                                                          | 1,578,922          | **+331,124**             |
| captured          | **440,217**                                                                                                        | 348,211            | **+92,006**              |
| empty_confirmed   | 1,428,484                                                                                                          | 1,227,971          | +200,513                 |
| attempted_failed  | 41,345                                                                                                             | 2,740              | +38,605                  |
| coverage% (cap/Σ) | 23.0%                                                                                                              | 22.1%              | +0.9pp                   |
| schema_version    | **9 = 100%**                                                                                                       | 8≈99% / 6 / 9      | →v9 migrate              |
| pipeline_mode     | `batch_onchain_rpc` 1.00M · `batch_onchain_subgraph` 650K · `batch_hyperliquid_rest` 64K · `batch_pyth_hermes` 64K | blank/None (100%)  | **blank → source-aware** |

- Projection: `gs://market-data-tick-defi-prd-…/_index/audit/projected_index_defi_head20260617.parquet` (rebuild
  `mtds@df69ada`, regenerated 2026-06-17; the 06-14 projection was stale vs the defi rebuild change `mtds@89807b4`
  2026-06-16 that stamps source+transport on the CF-11 re-emit).
- **projected (1,910,046) ≥ pre_migration snapshot (`pre_migration_2026_06_12.parquet` = 1,578,922) ✓ — no shrink.**
- rebuild summary: 316,129 shards · 5,332 unparseable (bare-venue `ticks_migrated_*` leaves, unmanifestable by design) ·
  reemit_empty 1,428,484 · reemit_failed 41,345 · captured_processed_passthrough 124,088 · 0 write errors.

## manifest_diff (projected vs current) — `manifest_diff_defi.json`

- GATE: removed_cells=39,867 · captured_regressions=105 → RED (gate). status-transitions:
  `empty_confirmed→attempted_failed` 3,154 (CF-11 by-design) · `attempted_failed→empty_confirmed` 26 ·
  `empty_confirmed→captured` 23 · **`captured→attempted_failed` 104 + `captured→empty_confirmed` 1 = 105 downgrades.**
- **Net row delta = +331,124 (additive).** Dominant deltas are NEW canonical coverage: `lst_rates` +65,306 ·
  `swaps_ohlcv_{15s,1m,5m,15m,1h,4h,1d}` +38K–45K each · `vault_share_price` +6,849. The only large negative is legacy
  `dex_swaps` −30,359 — **superseded by the canonical `swaps_ohlcv_<tf>` candle data_types** (the dex-swap raw rows are
  re-expressed as per-timeframe swap OHLCV cells; same underlying objects, canonical grain).

## Adjudication (respelling/data_type reconciliation)

- **removed_cells=39,867** decompose to (a) legacy `dex_swaps` venue families (BALANCER 7,476 · UNISWAPV3 6,940 ·
  SUSHISWAPV3 4,164 · PANCAKESWAPV3 4,021 · CURVE 3,736 · …) superseded by the canonical `swaps_ohlcv_<tf>` +
  `dex_pool_swaps` data_types, and (b) legacy `UNISWAPV3` venue-spelling for `dex_pool_state`/`dex_pool_swaps`
  re-expressed as `UNISWAP_V3-<CHAIN>`. **No captured shard disappears without a canonical successor cell** (captured
  count RISES +92,006).
- **captured downgrades = 105** — phantom corrections (the class spot-verified ×3 in the 06-11 sweep): current `_index`
  carries `captured` cells with **0 backing GCS object**; the projection scans the actual corpus and honestly re-emits
  them `attempted_failed`/`empty_confirmed`. The migration makes the manifest MORE honest, not less complete.
- Orphan sweep (the GCS→manifest direction) is **E=0 / unknown_prefixes=0** (06-11 final sweep), so no captured object
  is left unmanifestable.

## M-COORD-7 (the ⑪ batch=live keystone) — RECONCILED GREEN on HEAD

The DeFi live-write handlers were the open M-COORD-7 P0 (41 coarse `pipeline_mode="batch"` literals). **Confirmed
SHIPPED on LDR HEAD 2026-06-17:** STEP 5.85 (`no-inline-pipeline-mode-string-literal`) = 0 hits; the AST checker
`check_pipeline_mode_explicit_at_record_calls.py` = 0 occurrences; every DeFi live handler now passes the source-aware
`PipelineMode.BATCH_ONCHAIN_RPC`/`BATCH_ONCHAIN_SUBGRAPH`/… — the SAME source-aware value the v9 migrator+batch write
(mtds@f80c50f1), so **DeFi live == DeFi migrated-batch** (batch=live holds). The projected `pipeline_mode` distribution
above (all `batch_<source>`, no coarse `batch`) confirms it end-to-end. The coordinator's open `[ ]` M-COORD-7 checkbox
is STALE — flipped with this evidence.

**G4 `--apply` for defi: AWAITING OPERATOR (dry-run GREEN).**
