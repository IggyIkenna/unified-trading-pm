---
doc_type: issue
title: "Sports ODDS rebuild delta — LA_LIGA_2 data loss (846 cells in GCS, absent from manifest)"
summary: >-
  The post-07-13 manifest rebuild correctly pruned PLAYER_VALUES (−10,934, phantom-correction) and most ODDS (−2,334,
  phantom-correction), but 846 LA_LIGA_2 captured cells exist in GCS with no corresponding manifest row — genuine data
  loss because LA_LIGA_2 is absent from the instruments-service league catalogue used by the rebuild.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, rebuild-delta, data-loss, la-liga-2, manifest, track-s2]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md,
  ]
created: "2026-08-05"
author: slot-5 (data_engineering)
assigned_vm: planning
source: ["post-07-13 rebuild delta reconciliation (sports_consolidated_native_ao_extract-024)"]
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
parent_epic: sports_master
locked_by:
locked_since:
resolved_by:
---

# Sports ODDS rebuild delta — LA_LIGA_2 data loss

## What I found

The post-07-13 manifest rebuild delta reconciliation (Track S2, `sports_consolidated_native_ao_extract_2026_07_25.md`)
ran a comprehensive per-key manifest-vs-GCS cross-reference for PLAYER_VALUES and ODDS in
`instruments-store-sports-prd-central-element-323112`:

**PLAYER_VALUES (−10,934 delta)**: **PHANTOM CORRECTION.** All 1,474 GCS dates have corresponding manifest entries. Zero
GCS-only dates. The rebuild correctly dropped cells that had no real GCS data. No data loss.

**ODDS (−3,180 delta)**: **MIXED — ~2,334 phantom-correction + ~846 data loss.**

### Data loss: LA_LIGA_2 (846 cells)

- **846 GCS objects** exist at paths like
  `sports_reference/by_date/day=2020-06-10/.../entity=footystats_odds/.../league=LA_LIGA_2/footystats_odds.parquet`
- These span **2020-06-10 through 2026-05-18** across all 7 years — sustained, real data, not a transient artifact
- **Zero manifest rows** carry `league_id=LA_LIGA_2` for ODDS — not as captured, not as empty_confirmed, not at all
- Root cause: `LA_LIGA_2` is absent from the instruments-service league catalogue (the catalogue has `LA_LIGA`,
  `BUNDESLIGA_2`, etc., but not `LA_LIGA_2`)
- +1 BRASILEIRAO cell also in GCS but absent from manifest (same root cause likely)

### Additional finding: `league=NULL` phantom entries (2,149 current manifest rows)

- 2,149 manifest ODDS rows have `league_id=NULL` and `capture_status=captured` with no GCS object at a
  `league=`-prefixed path
- 2,145 of these DO correspond to non-league-prefixed GCS objects (e.g.
  `entity=footystats_odds/fetched_at_hour={H}/footystats_odds.parquet` without any `league=` subdirectory) — these are
  real data, just stored without a league key
- 783 dates have `league=NULL` manifest entries but NO corresponding GCS objects at all — these are pre-floor 2018-2019
  dates, already covered by the sports data floor ruling

## Evidence

Manifest: `gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet` (downloaded
2026-08-05 ~06:10 UTC, 112MB). Cross-reference via DuckDB + `gcloud storage ls --recursive` delimiter descent against
the live bucket, same session.

### Key counts

| Surface                    | ODDS (date, league)                     | PLAYER_VALUES (date, season) |
| -------------------------- | --------------------------------------- | ---------------------------- |
| GCS distinct               | 21,041                                  | 1,481                        |
| Manifest captured          | 30,260                                  | 48,823 (date, league)        |
| GCS-only (not in manifest) | **847** (846 LA_LIGA_2 + 1 BRASILEIRAO) | **0**                        |
| Manifest-only (not in GCS) | 2,149 (all league=NULL)                 | 1,299 dates                  |

## Why it matters

- LA_LIGA_2 has real, sustained GCS data (846 captured date-league cells across 7 years) that the availability manifest
  does not acknowledge. Any downstream consumer keyed on the manifest (coverage gates, honest-coverage denominators,
  backfill launchers) cannot see this data.
- This was likely introduced by the 2026-07-13 manifest rebuild — the pre-rebuild manifest may have covered LA_LIGA_2
  (contributing to the 30,928 cited pre-rebuild count), but the rebuild dropped it because the league isn't in the
  catalogue the rebuild uses to enumerate expected cells.

## Recommended decision

1. Add `LA_LIGA_2` to the instruments-service sports league catalogue (and verify BRASILEIRAO is already registered —
   the single GCS-only BRASILEIRAO cell may be a different edge case)
2. Re-run the manifest rebuild (or targeted re-emission) for `LA_LIGA_2` ODDS cells to restore the 846 missing rows
3. After the fix, re-verify the manifest-vs-GCS cross-reference confirms 0 GCS-only cells

## Progress Log

### 2026-08-05 ~07:30Z — slot-2: Verification (todo #3)

Re-ran manifest-vs-GCS cross-reference for ODDS. Downloaded the live availability manifest
(`gs://instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet`, 113MB, 9,246,416 rows)
and queried via DuckDB.

**Key counts (current state):**

| Metric                                 | Count                              |
| -------------------------------------- | ---------------------------------- |
| Manifest total rows                    | 9,246,416                          |
| ODDS total rows                        | 372,910                            |
| ODDS distinct leagues                  | 383                                |
| ODDS leagues with captured>0           | 30                                 |
| ODDS leagues with empty_confirmed only | 353                                |
| LA_LIGA_2 manifest rows                | **0** (still absent)               |
| BRASILEIRAO manifest rows              | 2,847 (962 captured + 1,885 empty) |

**Verdict: 0 GCS-only cells NOT YET achieved.** The 846 LA_LIGA_2 cells (+1 BRASILEIRAO edge case) are still GCS-only
because todo #2 (re-emit LA_LIGA_2 ODDS manifest rows) has not been executed.

**Potential blocker for todo #2**: `_LEAGUE_ALIASES` in
`unified_api_contracts/canonical/domain/sports/provider_league_ids.py` still maps `LA_LIGA_2 → SEGUNDA_DIVISION`.
`canonicalize_league_id()` applies the alias BEFORE checking the registry, so it always returns `SEGUNDA_DIVISION` for
`LA_LIGA_2` input. The manifest rebuild for todo #2 must construct GCS paths directly from the catalogue's `league_id`
(bypassing `canonicalize_league_id()`) or the alias must be removed now that LA_LIGA_2 is a real league again (not just
an alias for SEGUNDA_DIVISION). The alias comment in the file says "LA_LIGA_2 → SEGUNDA_DIVISION: prod manifest has
3,465 rows under the alias; SEGUNDA_DIVISION has LeagueDefinition" — that was written before the re-registration at
b4bac708, so it may now be stale and in need of removal.

**Recommendation**: Execute todo #2 with awareness of the alias issue, then re-verify.

- [x] ✅ [DATA] P1. Add `LA_LIGA_2` to the instruments-service sports league catalogue. — unified-api-contracts@b4bac708
      (note: SSOT is in UAC, not instruments-service)
- [x] ✅ [DATA] P1. Re-emit LA_LIGA_2 ODDS manifest rows for the 846 (date, league) cells with real GCS objects. —
      instruments-service@80077c74 (repo: instruments-service, script: reemit_la_liga2_odds_manifest_rows.py; dry-run
      confirmed 846 cells, 2020-06-10→2026-05-18; apply wrote 846 manifest rows to per-VM shard with canonical
      league_id=SEGUNDA_DIVISION)
- [x] ✅ [VERIFY] P2. Re-run manifest-vs-GCS cross-reference for ODDS — **846 LA_LIGA_2 cells still GCS-only** (todo #2
      not yet executed). Manifest downloaded 2026-08-05 ~07:30 UTC, 113MB, 9,246,416 rows. ODDS: 372,910 rows, 30
      leagues with captured>0, 383 distinct leagues total. LA_LIGA_2: 0 manifest rows (confirmed). BRASILEIRAO: 962
      captured + 1,885 empty in manifest (the reported +1 GCS-only edge case was not independently verified — full GCS
      walk was too heavy for in-session). Re-verify after per-VM shard consolidation into canonical index. — slot-2
      @2026-08-05 ~07:30Z

      > **RE-VERIFIED 2026-08-06 ~13:20Z (plan_reconciler agt-4fdce1, operator ruling BLK-136e69bf).** Confirmed the
              > manifest consolidator (`uts-prod-manifest-consolidator-instruments-sports`, Cloud Run Job) has run
              > continuously every ~1 minute since 2026-08-05 (per `gcloud run jobs executions list`, all `succeeded=1`) —
              > the per-VM shard consolidation blocker cited above has long since cleared. Downloaded the current canonical
              > manifest (164MB, 10,032,719 rows) and re-ran the cross-reference via DuckDB, this time checking BOTH
              > `league_id='LA_LIGA_2'` and `league_id='SEGUNDA_DIVISION'` for `data_type='ODDS'` (the exact uppercase value
              > this corpus's writer emits — confirmed via `SELECT DISTINCT data_type`; a first attempt using lowercase
              > `'odds'` silently matched 0 rows, the exact vocabulary trap this workspace's reconciliation rules warn
              > about). **Result: `LA_LIGA_2` still shows 0 ODDS rows (the `_LEAGUE_ALIASES` mapping is still live at write
              > time, as the original todo-2 evidence already flagged), but `SEGUNDA_DIVISION` now shows 1,164 captured ODDS
              > rows, of which exactly 846 fall within the target date range 2020-06-10..2026-05-18 — a precise match to the
              > 846-cell gap.** The data loss IS resolved: all 846 target cells are captured in the canonical index today,
              > just filed under the aliased `SEGUNDA_DIVISION` key rather than `LA_LIGA_2`. This is a real, different residual
              > (mislabeling, not absence) — filed as todo #4 below, not silently closed. **BRASILEIRAO** captured count is
              > unchanged at 962 (identical to the 2026-08-05 baseline) — the +1 GCS-only cell claim was NOT independently
              > verified this pass either: a targeted `gcloud storage ls` scoped to just the `league=BRASILEIRAO` path
              > (wildcarding only the `day=`/`fetched_at_hour=` segments, not a full corpus walk) still timed out after 90s,
              > confirming the original "too heavy for in-session" finding rather than refuting it. Carried forward, still
              > genuinely unverified — see todo #5.

- [ ] [DECISION] P2. **Resolve the `LA_LIGA_2` → `SEGUNDA_DIVISION` alias now that LA_LIGA_2 is a registered league
      again.** `_LEAGUE_ALIASES` in `unified_api_contracts/canonical/domain/sports/provider_league_ids.py` still maps
      `LA_LIGA_2 → SEGUNDA_DIVISION`; `canonicalize_league_id()` applies it before any registry check, so every write
      (past and future) for this league lands under `SEGUNDA_DIVISION`, not `LA_LIGA_2` — the 846 target cells are
      captured (todo #3), but permanently mislabeled as long as the alias stays live, and any future LA_LIGA_2 fetch
      will keep silently merging into SEGUNDA_DIVISION's count too. Decide: (a) remove the alias entry now that
      LA_LIGA_2 has its own `LeagueDefinition` (`unified-api-contracts@b4bac708`) and re-stamp the 846+ rows'
      `league_id` from SEGUNDA_DIVISION back to LA_LIGA_2 via a targeted manifest re-stamp (mirrors the pattern already
      used for the FX/ICE/KRX and MTDS lending restamps elsewhere in this corpus), or (b) if the two are considered the
      same real-world league going forward, keep the alias and correct this doc's framing instead (no data-loss
      occurred, only a naming decision). This is a genuine judgment call, not mechanical — needs an operator/domain
      decision, not a plan_reconciler auto-fix.
- [ ] [DATA] P3. **Independently verify the +1 BRASILEIRAO GCS-only cell claim.** Still unverified as of 2026-08-06 —
      two separate attempts (2026-08-05 full-GCS-walk, 2026-08-06 league-scoped wildcard listing) both found the check
      too heavy to run in-session. A future pass should either (a) dispatch this as a bounded, single-league,
      single-shard listing on a dedicated VM rather than the shared planning host, or (b) narrow the date range first
      (the manifest's BRASILEIRAO captured span is 2018-04-14..2026-07-31 — an 8-year range; probing a recent 1-2-year
      slice first would be far cheaper and might be sufficient to confirm or refute the 1-cell claim without a full
      historical walk).
