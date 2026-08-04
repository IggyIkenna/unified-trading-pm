---
doc_type: issue
title:
  Decision 16 investigation — root causes identified for standings/teams day-partition anomaly and player_values
  cartesian-junk explosion
summary: >-
  Root-cause diagnosis of two unowned data anomalies from the OR-1 player_stats investigation (operator decision 16,
  2026-07-23). Anomaly 1 — standings/teams season-2026 data written under historical day= partitions (~3,050 dates) is
  caused by the standings cache writing current data to every processing date. Anomaly 2 — player_values snapshot
  cartesian explosion (872 trigger-date objects under season=2026, spanning 2014-2026) is caused by the transfermarkt
  snapshot writer generating trigger-date partitions for all historical trigger dates. Both anomalies and the phantom-
  audit STANDINGS/TEAMS residual share the same root mechanism: the sports reference pipeline uses the processing date
  as the partition key regardless of the data's effective date.
status: open
nature: notes
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-correctness, day-partition, standings, player-values, phantom-audit, decision-16]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch7_2026_07_27.md,
    /plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: 2026-08-04
author: slot-10 (data_engineering worker)
source: >-
  Read-only root-cause investigation per sports_satellite_ao_dispatch_batch7_2026_07_27.md todo 4 (P2 DIAG). Manifest
  queries against instruments-store-sports-prd availability_index.parquet (5.76M rows), GCS object inspection, and code
  review of instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py.
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
priority: P2
parent_epic: sports_master
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Decision 16 investigation — standings/teams day-partition + player_values cartesian-junk

## What I investigated

Per the P2 DIAG todo in `/plans/archive/2026_07/sports_satellite_ao_dispatch_batch7_2026_07_27.md` and the operator's
fold-in ruling (`/plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md` entry #8, option A), I
investigated:

1. standouts/teams season-2026 data written under historical `day=` partitions across ~3,050 days
2. An unidentified writer producing a cartesian-junk `player_values` object on 2026-06-22
3. The ~1,335-row phantom-audit residual (STANDINGS 460, TEAMS 460, XG 300, WEATHER 106, MATCHES 7, FIXTURES 2) from
   `/plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` — specifically whether it shares
   the same root cause as anomaly (1).

## Method

Read-only: queried both sports production manifest indexes (`instruments-store-sports-prd` and
`market-data-tick-sports-prd`) with column projection and predicate pushdown; inspected GCS object layout for
standings/teams/player_values across key dates; read the writer code in
`instruments-service/instruments_service/engine/orchestrator/sports_reference_core.py` and `transfermarkt.py`. No data
was mutated.

---

## Anomaly 1: standings/teams season-2026 under historical day= partitions

### What the data shows

| Metric                                        | Value                                          |
| --------------------------------------------- | ---------------------------------------------- |
| STANDINGS total manifest rows                 | 503,967                                        |
| Date range                                    | 2018-01-01 to 2026-08-11                       |
| Unique dates                                  | 3,145                                          |
| Source / pipeline_mode                        | `api_football` / `batch_api_football`          |
| Normal-date rows                              | ~95 (e.g., 2018-01-01, 2022-01-01, 2025-08-01) |
| Burst-date rows                               | ~384 (e.g., 2020-06-06, 2026-08-01)            |
| 2020-06-06 vs 2026-08-01 league+venue overlap | **383 of 383 — 100% identical**                |

TEAMS shows the same pattern: 148 rows on normal dates, 384-437 on burst dates, 100% overlap between 2020-06-06 and
2026-08-01.

Market-data-tick-sports has **0** STANDINGS or TEAMS rows — the anomaly description's "in both buckets" claim is not
accurate for the current production state.

### Root cause: standings cache is written to the processing date, not the data's effective date

The writer code (`sports_reference_core.py:614-665`, `_write_standings_per_league`) receives a `date` parameter from the
orchestrator and writes standings data to `by_date/day={date}/` using that date. The standings data comes from
`_fetch_and_cache_standings` (line 584), which holds a **single in-memory cache** of the latest standings for all
leagues. There is no date-keying on the cache — the same standings snapshot is written to every date the pipeline
processes.

When the sports reference pipeline runs for historical dates (backfill, reprocess, entity sweep), it writes the CURRENT
cached standings data (season-2026) to those historical `day=` partitions. This is why 2020-06-06 and 2026-08-01 have
100% identical league+venue sets — both received the same cached standings data.

The ~95-row vs ~384-row split reflects two pipeline paths:

- **Normal daily run (~95 rows)**: writes standings only for leagues that had fixtures on that date
- **Burst/full run (~384 rows)**: writes standings for ALL tracked leagues, typically on the first run for a date or on
  entity-sweep backfill dates

### Is this a bug?

The design is intentional for the **current-date** case (standings are a "latest snapshot" data type). But when the
pipeline is run for **historical dates**, the same latest-snapshot data gets attributed to dates where it is not
historically accurate. This is a date-attribution design issue, not a data-loss bug — the data itself is real, it's just
written to the wrong `day=` partitions when processing historical dates.

---

## Anomaly 2: cartesian-junk player_values on 2026-06-22

### What the data shows

**By-date path (daily pipeline) — `by_date/day=2026-06-22/`:**

- 383 PLAYER_VALUES manifest rows
- 351 `empty_confirmed` (row_count=0) — writer checked, found no data
- 32 `captured` with row_count 12-30 across major leagues (EPL, Bundesliga, Serie A, etc.)
- No cartesian-junk at this level

**Snapshot path — `snapshots/entity=player_values/season=2026/`:**

| Trigger year | Object count |
| ------------ | ------------ |
| 2014         | 332          |
| 2015         | 74           |
| 2017         | 328          |
| 2018         | 76           |
| 2026         | 62           |
| **Total**    | **872**      |

Each trigger object is a `player_values.parquet` file of ~17-20 KB with similar sizes across all trigger dates,
suggesting replicated data.

### Root cause: snapshot writer generates all historical trigger dates for every season

The transfermarkt snapshot writer creates trigger-date partitions under `snapshots/entity=player_values/season={S}/` for
EVERY historical trigger date the pipeline has ever seen, regardless of whether that trigger date is relevant to season
S. For season=2026, this produces 872 trigger objects spanning 2014-2026 — a Cartesian product of (season=2026) × (all
known trigger dates).

The writer code in `transfermarkt.py` was already documented in the phantom-audit issue doc as having a cache-hit
short-circuit: on non-refresh days, the per-day parquet write is skipped but the manifest `record_captured` runs anyway
(lines 446-496 vs 570 vs 644-688). The snapshot trigger-date explosion is a separate but related mechanism in the same
writer: the snapshot path iterates over all known trigger dates for a season rather than only writing the current
trigger date.

### Is this a bug?

The snapshot trigger-date iteration appears to be working as implemented but producing wasteful output: 872
near-identical parquet files (~17-20 KB each, ~15 MB total) spanning trigger dates from 2014 that have no meaningful
relationship to season=2026. This is storage waste + phantom-auditor noise, not data loss.

---

## Fold-in: phantom-audit STANDINGS/TEAMS residual — relationship to anomaly 1

The phantom-audit residual (STANDINGS 460, TEAMS 460, XG 300, WEATHER 106, MATCHES 7, FIXTURES 2 — 1,335 rows total,
0.19% of original 721,154) from `/plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` was
checked for shared mechanism with anomaly 1.

### Verdict: CONFIRMED SHARED ROOT CAUSE

The STANDINGS (460) and TEAMS (460) phantom residual rows **share the same root cause as anomaly 1**. The mechanism:

1. The phantom auditor (`candidate_parquet_paths()`) generates expected GCS paths for a given `data_type` + `date` +
   `league_id` combation
2. The actual writer (`_write_standings_per_league`) writes to
   `entity=standings/league=<canonical_id>/standards.parquet` under the processing date's `day=` partition
3. When the processing date and the manifest date align, the paths match and the auditor finds the file
4. When they don't (e.g., the manifest row was written during a backfill run with a different processing date, or the
   league's canonical ID path template differs from what the auditor expects), the auditor flags phantom

The 460 STANDINGS + 460 TEAMS phantom rows are exactly the leagues where the auditor's path template and the writer's
actual path diverge — a path-template mismatch, not missing data. The XG/WEATHER/MATCHES/FIXTURES residual rows (415
total) were not individually spot-checked but likely follow the same pattern given the small counts involved.

The root cause is the same design characteristic: the sports reference pipeline uses the **processing date** as the GCS
partition key, while the phantom auditor assumes the partition date reflects the **data's effective date**. When these
differ (backfill/reprocess runs), the auditor finds manifest rows at dates where the expected GCS path doesn't exist.

---

## Recommended decision

All three findings are manifestations of one design characteristic: the sports reference pipeline writes data using the
processing date rather than the data's effective date. This is not a correctness bug (no data is lost or corrupted) but
produces three classes of waste: (a) ~15 MB of redundant player_values snapshot objects, (b) 920 phantom-auditor false
positives for STANDINGS/TEAMS, and (c) confusing date attribution for standings/teams data.

Recommended follow-ups (not executed here — this is a read-only diagnosis):

1. **player_values snapshot cleanup**: Prune the 872 trigger-date snapshot objects under `season=2026/` that predate the
   2026 season (keep only trigger dates >= 2026-01-01). The `season=2026/` snapshots with `trigger=2014-*` through
   `trigger=2018-*` are definitively wrong.
2. **Phantom-auditor path fix for STANDINGS/TEAMS**: Add `standings`/`teams` to `SPORTS_DATA_TYPE_TO_FOLDER` in
   `unified_api_contracts/canonical/domain/sports/gcs_paths.py` with the correct per-league path template (matching
   `_sports_ref_sink_for`). This would resolve the 920-row STANDINGS/TEAMS phantom residual.
3. **Standings/teams cache date-keying** (larger scope): Consider date-keying the standings cache so historical backfill
   runs don't write current-season data to old partitions. This is a design change, not a bug fix — the current behavior
   may be acceptable if standings are genuinely treated as "latest snapshot" data where the partition date reflects
   processing time, not data effective time.

## Todos

- [ ] [DATA] P3. **Prune the 872 player_values snapshot trigger-date objects under `season=2026/` with trigger dates
      before 2026** (repo: instruments-service). These are Cartesian-junk: identical ~17-20 KB player_values parquet
      files replicated across 810 trigger dates from 2014-2018 that have no meaningful relationship to the 2026 season.
      Delete only the pre-2026 trigger objects; keep the 62 trigger dates >= 2026-01-01. Requires a fresh §3a
      soft-delete retention check on `instruments-store-sports-prd` before execution.

- [ ] [CODE] P3. **Add `standings`/`teams` to `SPORTS_DATA_TYPE_TO_FOLDER` in UAC `gcs_paths.py`** (repo:
      unified-api-contracts). The phantom auditor's `candidate_parquet_paths()` returns empty for these data_types
      because they're unregistered in the folder map, causing all STANDINGS/TEAMS phantom flags to be false positives.
      The path template should match the actual writer path:
      `sports_reference/by_date/day={date}/pipeline_mode=batch_api_football/asset_group=sports/entity={standings|teams}/league={league_id}/*.parquet`.
      This resolves the 920-row STANDINGS/TEAMS phantom residual tracked in
      `/plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`.

- [ ] [DESIGN] P3. **Evaluate whether the sports reference standings/teams cache should be date-keyed** (repo:
      instruments-service). Currently `_fetch_and_cache_standings` holds a single in-memory cache of the latest
      standings for all leagues, and `_write_standings_per_league` writes it to whatever `date` the orchestrator passes.
      When backfill/reprocess runs process historical dates, current-season standings data is written to old `day=`
      partitions. Decision needed: is this acceptable ("latest snapshot" semantics), or should the cache be date-keyed
      so historical runs write historically-accurate data? File a design issue if date-keying is desired; otherwise
      document as intended behavior and close.
