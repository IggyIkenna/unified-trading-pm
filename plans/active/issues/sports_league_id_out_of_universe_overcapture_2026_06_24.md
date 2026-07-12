---
doc_type: issue
title:
  Sports manifest is not a numeric-vs-canonical schema split — it is a cross-provider OUT-OF-UNIVERSE over-capture
  (1.68M of 4.6M rows are for leagues outside our 94/101-league canonical set)
summary:
  The operator framed the sports `_index` problem as "every data_type has 12–48% rows keyed by **numeric** API-Football
  league_id; the rest canonical; the numeric rows are legacy duplicates of canoni...
status: resolved
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [sports, manifest, data-correctness, honest-coverage, instruments, uac, canonicalisation, data-quality]
related:
  [
    plans/active/issues/sports_manifest_null_vs_empty_dedup_double_count_2026_06_21.md,
    plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md,
  ]
created: 2026-06-24
parent_epic: sports_master
priority: P1
source:
  [
    "instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet (live read 2026-06-24 06:44
    UTC)",
    unified_api_contracts.sports.LEAGUE_REGISTRY (101 leagues) / get_expected_leagues_for_source("api_football") (94),
    "instruments_service/engine/orchestrator/sports_reference_core.py::_fetch_injuries (per-league capture groupby)",
    "instruments_service/engine/orchestrator/sports.py::_canonical_league_id (passes unknown numerics/slugs through)",
  ]
assigned_vm:
resolved_by:
  "2026-07-12 doc-reconciliation fixer, finding 252 & §A2 B-queue ruling — operator-gated DROP decision (item 4) was
  made (DROP) + executed: instruments-service@acfd5ac (write-path universe gate, item 1) + G1 wipe (item 4), post-wipe
  IS index 2,898,902 rows canonical-only. See body annotation +
  sports_p2_history_apifootball_2015_to_present_2026_06_27.md Todo 1 for full evidence. NOTE: recommendation item 2
  (in-universe numeric/suffixed re-key+dedup) completion is NOT separately confirmed by this evidence — re-verify before
  treating as fully closed."
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-12
---

## What I found

The operator framed the sports `_index` problem as "every data_type has 12–48% rows keyed by **numeric** API-Football
league_id; the rest canonical; the numeric rows are legacy duplicates of canonical twins — dedupe them." Measuring the
**live `-prd-` index** (4,599,072 rows, mtime 2026-06-24 06:44 UTC) shows that framing captures only a small slice. The
full `league_id` taxonomy + canonicalization landscape (canonicalized via numeric→`get_league_by_api_football_id` then
`canonicalize_league_id` suffix-strip, then membership-tested against the **101-league `LEAGUE_REGISTRY`**):

| class                | rows      | canon → registry (in-universe) | out-of-universe                     |
| -------------------- | --------- | ------------------------------ | ----------------------------------- |
| `name` (slug)        | 3,089,696 | 2,403,789                      | **685,907**                         |
| `numeric`            | 1,052,700 | 215,881                        | **836,819**                         |
| `suffixed` (`X_<n>`) | 398,089   | 302,790                        | **95,299**                          |
| `hashlike` (16 hex)  | 288       | 0                              | 288                                 |
| `blank`              | 58,299    | 0                              | 58,299                              |
| **total**            | 4,599,072 | **2,922,460 in-universe**      | **1,676,612 out-of-universe (36%)** |

Key conclusions:

1. **The numeric rows are NOT mostly canonical-twin duplicates.** Only **215,881 of 1,052,700** numeric rows resolve to
   a registry league via `get_league_by_api_football_id`; the other **836,819** are api-football leagues OUTSIDE our
   94/101-league universe (ids `1,4,5,6,…,288,261,235…` — verified `get_league_by_api_football_id(288)=None`). Of the
   215,881 resolvable, **100% already have a canonical twin row** at the same `(date, data_type, canonical_league)` →
   clean dedup target, 0 orphan.
2. **The same over-capture exists in `name`/`suffixed` rows** — 685,907 slug-keyed + 95,299 suffixed rows are also
   out-of-universe (provider slugs like `BRAZIL_BAIANO_1`, `ALGERIA_LIGUE_1` — `get_league()` returns None). So this is
   a **cross-provider over-capture**, not an api-football-numeric schema split.
3. **Numeric rows are STILL being written right now** — 1,261 numeric rows in the last 24h, `written_at` max 06:04 UTC
   2026-06-24. The write-path canonicalizer (`_canonical_league_id`) DOES correctly map the 59 in-universe numerics, but
   **passes unknown numerics/slugs through unchanged** by design, so out-of-universe leagues are still born
   numeric-keyed (and slug-keyed) every run. Root cause: the date-wide adapter calls (`get_injuries(date)`, the fixtures
   roll-up, standings) return data for the **entire api-football/provider universe (~2,400 leagues)**, and the
   per-league capture groupby loops (`_fetch_injuries`, `_run_per_fixture_enrichment`, `_fetch_teams_and_standings`)
   write a captured row for every returned league — they do NOT gate captures to the expected/canonical universe (only
   the `emit_empty_gaps_for_entity` HONEST-ABSENCE path uses `get_expected_leagues_for_source`).

## Why it matters

- The operator-requested dedupe (numeric→canonical) only addresses **215,881 of 1,676,612** non-canonical rows. Shipping
  just that leaves 1.46M out-of-universe rows + an actively-polluting writer.
- The out-of-universe rows are **36% of the manifest** and inflate/distort the honest-coverage denominator
  (`captured/(captured+empty+failed+expected_unattempted)`), which the deployment-UI + features/strategy pre-flight
  read.
- Deciding to **drop** the 1.68M out-of-universe rows changes coverage numbers + deletes data the pipeline genuinely
  fetched (even if for leagues we don't trade); deciding to **keep** them means the canonical-one-schema goal is "every
  in-universe key canonical + out-of-universe kept honest-numeric/slug." This is a **data-model decision that reshapes
  coverage**, beyond a mechanical dedup — destructive-risk, so it needs operator sign-off (per Findings-Triage
  big-finding rule).

## Recommended decision

Split into a SAFE deterministic part (ship now, no operator decision) + an operator-gated part:

**SAFE — ship now (this task does it):**

1. **Write-path gate** — in the per-league CAPTURE loops (`_fetch_injuries`, `_run_per_fixture_enrichment` /
   `_write_per_fixture_entities`, `_fetch_teams_and_standings`) only `record_captured`/write for a league whose
   canonicalized id is in `get_expected_leagues_for_source(...)` / `LEAGUE_REGISTRY`; this is the SAME universe gate the
   honest-absence emit already uses, so it stops new out-of-universe + numeric pollution at the boundary without
   changing the in-universe data.
2. **In-universe re-key + dedup migration** — for the 215,881 numeric + 302,790 suffixed in-universe rows, rewrite key →
   canonical, dedup against the existing canonical twin (keep best status: captured > empty_confirmed >
   attempted_failed, prefer real-parquet), whole-`_index` rewrite (snapshot first, dry-run first).
3. **Date-level pre-flight** — already correct (`_freshness_preflight` defers per-league sports to per-entity
   `_should_skip_date_for_per_league`); the INJURIES failures are NOT a date-skip bug (see below).

**OPERATOR-GATED — needs a decision (this issue):** 4. The **1,676,612 out-of-universe rows** (836,819 numeric + 685,907
slug + 95,299 suffixed + 288 hash + 58,299 blank): **DROP from the manifest** (recommended — they are leagues outside
our 94-league trading universe; keeping them distorts coverage) **vs KEEP** (mark honestly, exclude from the coverage
denominator). Recommend DROP after a snapshot, contingent on confirming no downstream consumer (features-sports /
strategy) reads out-of-universe leagues.

## RESOLVED 2026-07-12 — finding 252, §A2 B-queue ruling

(Was: `status: open`, `resolved_by:` blank, unedited since 2026-06-27 — this issue read as an open, undecided
operator-gated question.)

The operator-gated decision above (item 4) was **DECIDED: DROP** + **EXECUTED**, and item 1 (write-path gate) shipped
alongside it, both in `sports_p2_history_apifootball_2015_to_present_2026_06_27.md` Todo 1 (session 2026-06-27→28):

- **Write-path gate (item 1)** — `instruments-service@acfd5ac` ("fix(sports): add canonical write-universe gate to all
  per-league write paths (G1)") — gates `footystats.py` / `process_write.py` / `sfi.py` / `sports_fixtures.py` /
  `understat.py` per-league write loops to the canonical universe, matching this issue's exact recommendation.
- **DROP execution (item 4, G1 wipe)** — `delete_noncanonical_sports_leagues_2026_06_25.py --apply` removed 1,515
  non-canonical `league_id`s (~3.05M rows) after a snapshot
  (`_index/snapshots/pre_noncanonical_leagues_delete_index_20260628_19343*/`
  - `pre_noncanonical_delete_seed_*`); post-wipe IS index = 2,898,902 rows, canonical-only (19:42 UTC 2026-06-28).

**Not separately confirmed by this evidence**: item 2 (in-universe numeric/suffixed re-key + dedup migration for the
215,881 numeric + 302,790 suffixed in-universe rows) — re-verify its status before treating the full recommendation set
as shipped; only items 1 and 4 (the operator-gated crux of this issue) are confirmed here.
