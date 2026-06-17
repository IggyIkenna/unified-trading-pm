# Verdict pack — PREDICTION (G4 ⑬–⑲ pre-apply, R3/R7 + R8 regenerated on HEAD 2026-06-17)

**VERDICT: 🟢 GREEN — dry-run clean, ready for operator V6 eyeball + `G4 --apply`.** Projected canonical coverage is
**75.3%** (7,116 captured cqg bundles, 1 attempted_failed). The migration is a SAFE by-design grain change (legacy raw
per-cid `trades` cells → the canonical cqg-bundle atom); no data lost.

> **The cqg-classifier "block" was a STALE-PROJECTION artifact — operator was right.** My first pass (06-11 projection)
> showed 0.2% coverage / 542,170 `attempted_failed[ClassifierConfidenceLow]` and I provisionally flagged it
> BLOCKED-OPERATOR-DECISION. The operator correctly noted the cqg registry had already been expanded. Root cause: the
> cqg classifier lives in **UAC**, and the registry was expanded under **decision 338** in 3 UAC commits AFTER the 06-11
> projection (`uac@8e3108d` sports matrix +30 groups/17 leagues · `uac@e0035fd` crypto PRICE_RANGE + political + geo +
> box-office + MISC_NOVELTY residual · `uac@d52217f` 10 alt-coin UP_DOWN_DAILY + 7 macro + WEATHER_TEMP). The 06-11
> projection used the OLD registry. **Re-projecting on HEAD against the expanded registry: 0.2% → 75.3%, and the 542,170
> ClassifierConfidenceLow failures → 1.** No operator decision is needed — the registry already covers the live market
> set.

## Projected-v9 render (HEAD projection, expanded cqg registry)

| metric            | PROJECTED (HEAD)             | CURRENT (`_index`) | note                                                           |
| ----------------- | ---------------------------- | ------------------ | -------------------------------------------------------------- |
| rows              | 9,447                        | 19,299             | grain change (raw per-date cells → cqg-group bundle atom)      |
| captured          | **7,116**                    | 16,968             | **7,116 cqg-group bundles** (the canonical atom)               |
| empty_confirmed   | 2,330                        | 2,331              | CF-11 honest absence (dates with no classifiable bundle)       |
| attempted_failed  | **1**                        | 0                  | **was 542,170 under the OLD registry** — now ~fully classified |
| coverage% (cap/Σ) | **75.3%**                    | 87.9% (raw grain)  | the REAL cqg coverage (vs the stale 0.2%)                      |
| schema_version    | **9 = 100%**                 | 4≈74% / 8 / 9      | →v9 migrate                                                    |
| pipeline_mode     | `batch_polymarket_clob` 100% | blank/None 100%    | **blank → source-aware**                                       |

- Projection: `gs://market-data-tick-pred-prd-…/_index/audit/projected_index_prediction_head20260617.parquet` (rebuild
  `mtds@df69ada` against the **HEAD UAC** editable clone; 2025-01-01→2026-06-17; 573,536 objects scanned, elapsed
  2,483s). CF-11 counters: reemit_empty 2,330 · reemit_failed 1 · source_returned_zero_preserved 50.

## manifest_diff (HEAD projection vs current) — `manifest_diff_prediction.json`

- GATE: removed_cells=3,588 · captured_regressions=4 → RED (gate). status-transitions: only
  `captured→empty_confirmed` 4. Net by data_type: `prediction_canonical_question_group` **+7,116** (the NEW canonical
  cqg-bundle atom) · `trades` −12,014 · `prediction_trades` −4,937 (legacy RAW per-cid grain).

## Adjudication

- **removed_cells=3,588 + the 16,968 unmatched** = the legacy RAW-grain `trades`/`prediction_trades` POLYMARKET cells,
  **SUPERSEDED BY DESIGN** by the bundled `prediction_canonical_question_group` atom (E5 rewrite: the canonical shard
  atom replaces raw grain; the live writer emits ONLY bundles). The 7,116 cqg bundles aggregate the same underlying
  trade objects at the canonical grain — the captured 16,968→7,116 is a GRAIN re-expression, not loss. Objects are not
  deleted (orphan sweep E=0; G4.5 delete is separate + operator-gated).
- **captured→empty_confirmed = 4** = residual trail dates (2026-04-26..29 / 06-09) where Polymarket markets returned
  zero classifiable bundles → honest CF-11 downgrade at the canonical grain.
- **attempted_failed = 1** (was 542,170 on the OLD registry): the expanded cqg registry now classifies essentially the
  whole live market set — sports/politics/crypto-range/macro/weather all bucket into real groups.

## R8 — prediction migrator dry-plan on HEAD (`pred_migrator_dryplan.txt`)

`migrate_prediction_to_pred_prd_v9.py --dry-run` on HEAD: **TOTAL planned=1,897,691 copied=0 (DRY-RUN), 0 errors** —
751,723 raw + 582,730 processed objects in scope + 563,238 `category=` stale-source canonicalisations. Object migration
plan GREEN.

**G4 `--apply` for prediction: AWAITING OPERATOR (dry-run GREEN, 75.3% cqg coverage on the HEAD registry).**
