# Verdict pack — SPORTS (G4 ⑬–⑲ pre-apply, R3/R7 + R8 on HEAD 2026-06-17)

**VERDICT: 🟢 GREEN — gate clean (removed=0, captured_regressions=0), ready for operator V6 eyeball + `G4 --apply`.**
The cleanest AG: cell coverage is byte-identical projected-vs-current; the only delta is the honest exclusion of
ODDS_API zero-count probe artifacts.

## Projected-v9 render (vs current/live `_index`)

| metric                 | PROJECTED                                                       | CURRENT (`_index`) | Δ                                     |
| ---------------------- | --------------------------------------------------------------- | ------------------ | ------------------------------------- |
| rows                   | 786,508                                                         | 803,796            | −17,288                               |
| captured               | **202,087**                                                     | 202,087            | **0 (identical)**                     |
| empty_confirmed        | 584,257                                                         | 584,257            | 0 (identical)                         |
| attempted_failed       | 164                                                             | 164                | 0 (identical)                         |
| `None`-status          | 0                                                               | 17,288             | **−17,288 (probe artifacts dropped)** |
| coverage% (cap/Σ)      | **25.7%**                                                       | 25.7%              | 0                                     |
| schema_version         | **9 = 100%**                                                    | 8≈98% / 4 / 9      | →v9 migrate                           |
| pipeline_mode + source | `batch_odds_api` 786,508 (`source=odds_api` where data present) | blank/None 100%    | **blank → source-aware**              |

- Projection: `gs://market-data-tick-sports-prd-…/_index/audit/projected_index_sports.parquet` (rebuild `mtds@77f1a61`,
  unchanged since 06-11; corpus frozen → HEAD-equivalent). Sports uses `candidate_parquet_paths()`, so the generic
  orphan sweep is N/A by design — the sports-specific sweep (R8) drove **E=0 on BOTH sports buckets**.

## manifest_diff (projected vs current) — `manifest_diff_sports.json`

- **GATE: removed_cells=0 · captured_regressions=0 · changed=0 · 55,412 cells unchanged → GREEN.** No status transitions
  of any kind.
- The −17,288 row delta is entirely the `None`-status (blank capture_status) ODDS_API zero-count probe rows present in
  the current index but legitimately excluded from the v9 projection — **cell coverage is unaffected** (every
  captured/empty/failed cell is identical on both sides).

## R8 — sports gates (DONE)

- **Sports-specific orphan sweep** (`migration_orphan_sweep_sports.py` + `backfill_orphan_class_e_sports.py`,
  is@94ea099 + @37793dd): odds E 20→0; reference E 87,659→0 (~81.8k league-grain cells recorded; index 2,681,044→
  2,681,628 no-loss). `unknown_prefixes=0` on both buckets.
- **v1_archive ROW-coverage** proven before any drop: 398/398 days, 72,522/72,522 rows covered via
  `source_fixture_id`↔`af_fixture_id`; the archive carried as `B2_v1_archive_superseded` G4.5 delete-candidate
  (operator-gated, never auto-deleted).

## Reason-level residual (does NOT block apply)

- **CF-5 oracle relabel = ZERO** (root-caused + fixed in code, preserved on `origin/wip-preserve/mtds-346-cf5-trades`,
  mtds@d0a15a3): `_PER_FIXTURE_DERIVED_DATA_TYPES` had lowercase `"trades"` vs the `.upper()` membership test → step-6.5
  truthset gate skipped every `trades` empty. Reason-level only; **status-diff is GREEN** so it does not gate G4. Land
  it
  (`quickmerge --files 'market_tick_data_service/scripts/rebuild_sports_manifest_v9.py tests/unit/scripts/test_rebuild_sports_manifest_v9.py'`)
  the moment MTDS deps are clean.

**G4 `--apply` for sports: AWAITING OPERATOR (dry-run GREEN).**
