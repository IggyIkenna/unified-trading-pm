---
doc_type: issue
title:
  "Sports WEATHER — UAC SPORTS_DATA_TYPE_LAYOUT declares PER_DAY_BARE but the writer emits PER_DAY_PER_LEAGUE, so
  candidate_parquet_paths false-absents every captured WEATHER object and manufactures phantoms"
summary: >-
  Found by the /data-pipeline-reconciliation sports run (2026-07-20, F2). UAC
  unified_api_contracts/canonical/domain/sports/gcs_paths.py:139 sets SPORTS_DATA_TYPE_LAYOUT[WEATHER]=PER_DAY_BARE
  (entity=weather/weather.parquet), but the writer emits PER_DAY_PER_LEAGUE (entity=weather/league={L}/weather.parquet)
  — proven on disk for K_LEAGUE_2 across three days (2026-07-10 / 2026-07-05 / 2026-06-20). Because
  candidate_parquet_paths() derives its probe path from that layout table, it looks under the bare path, never finds the
  per-league object, and the captured WEATHER data reads as absent — feeding false rows into the 721,154-row phantom
  ceiling (the reconciliation report measured WEATHER contributing at least 106 proven false positives). This is the
  SAME UAC-layout-vs-writer drift class the code itself documents for PLAYER_VALUES (gcs_paths.py:70-78, resolved
  2026-05-05 by aligning the table to the writer) — WEATHER is an un-fixed instance of it. Cross-repo — UAC layout table
  + IS weather writer.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags: [data-correctness, sports, weather, path-layout, phantom, false-absence, candidate-parquet-paths, uac-drift]
related:
  [
    data_pipeline_reconciliation_sports_2026_07_20,
    sports_phantom_audits_reference_not_marketdata_2026_07_14,
    phantom_audit_estate_coverage_gap_2026_07_10,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "/data-pipeline-reconciliation sports run 2026-07-20 (finding F2); UAC layout side code-verified at gcs_paths.py:139,
  writer side proven on disk by the report across three days"
resolved_by:
---

# Sports WEATHER — UAC layout `PER_DAY_BARE` vs writer `PER_DAY_PER_LEAGUE` manufactures phantoms

> **⚠️ BIG FINDING (data-correctness — cross-repo).** A UAC layout table that disagrees with the writer makes the
> path-dispatcher blind to captured data, so honest coverage under-counts and the phantom audit over-counts. Surfaced by
> the /data-pipeline-reconciliation sports run (F2, `data_pipeline_reconciliation_sports_2026_07_20.md`).

## The drift (UAC side verified in code)

- UAC declares WEATHER as bare: `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py:139` →
  `"WEATHER": SportsPathLayout.PER_DAY_BARE` (the bare tail
  `sports_reference/by_date/day={D}/entity=weather/weather.parquet`, no `league=` segment).
- The writer emits per-league: the reconciliation report probed disk on three days (2026-07-10 / 2026-07-05 /
  2026-06-20) and found the object at `…/entity=weather/league=K_LEAGUE_2/weather.parquet` (`PER_DAY_PER_LEAGUE`).
- `candidate_parquet_paths()` derives its probe path from `SPORTS_DATA_TYPE_LAYOUT` (`gcs_paths.py:225` —
  `layout = SPORTS_DATA_TYPE_LAYOUT.get(data_type, SportsPathLayout.PER_DAY_BARE)`, then the per-league `league=`
  segment is only appended when `layout == PER_DAY_PER_LEAGUE`, `:294-319`). With WEATHER pinned to `PER_DAY_BARE`, the
  dispatcher never builds the `league=` path that actually holds the data.

## Why it matters

The dispatcher looking under the wrong path reports the captured WEATHER object as absent. That false absence flows
straight into the phantom audit as a false positive (the reconciliation report identified WEATHER as a proven false
positive inside the stale 721,154-row `instruments-store-sports` phantom ceiling — at least 106 rows). Same failure mode
the code already documents for PLAYER_VALUES at `gcs_paths.py:70-78`: a pre-2026-05-05 SSOT pointed at the wrong layout,
"which never matched the writer; the audit script then false-flagged every captured row as phantom + a band-aid script
wrote zero-row placeholders to mask the drift." That was resolved by aligning the table to the writer's truth. WEATHER
is the same bug, still open.

## Fix direction (align the SSOT to the writer — the PLAYER_VALUES precedent)

The PLAYER_VALUES resolution aligned the layout table to the writer's actual output rather than changing the writer. The
same is the likely correct direction here — flip `SPORTS_DATA_TYPE_LAYOUT[WEATHER]` to `PER_DAY_PER_LEAGUE` so the
dispatcher probes the path the writer actually uses — but confirm which side is the intended truth before flipping (the
writer's per-league emission must be the deliberate layout, not itself a drift), and check whether any placeholder /
band-aid rows were written for WEATHER the way `write_player_values_placeholders.py` did for PLAYER_VALUES.

## Todos

- [ ] 1. [DATA] P1. Confirm the writer's intended WEATHER layout is `PER_DAY_PER_LEAGUE` (read the IS weather writer +
      confirm no bare `entity=weather/weather.parquet` objects are ALSO written) so the table is aligned to the true
      layout, not to a second drift (repo: instruments-service).
- [ ] 2. [CODE] P1. Align `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` in
      `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py` to the confirmed writer layout,
      with a regression test that `candidate_parquet_paths(WEATHER, league=…)` builds the `league=` path (mirror the
      existing PLAYER_VALUES alignment) (repo: unified-api-contracts).
- [ ] 3. [DATA] P1. After the fix, re-run the sports phantom audit and confirm the WEATHER false positives drop out of
      the `instruments-store-sports` phantom count; check for and remove any zero-row WEATHER placeholder residue (repo:
      instruments-service).
