---
doc_type: issue
title: Sports fixtures_schedule — some writes land under a raw af_league_id folder instead of the canonical league_id
summary:
  86 in-window, registry-member blank-round rows sit under non-canonical `league=<raw_af_league_id>` (numeric-string) or
  bare day-level `fixtures_schedule.parquet` shards instead of the canonical `league=<CANONICAL_ID>` folder — these are
  structurally invisible to the canonical-folder-scoped round-derivation backfill mechanism
  (`backfill_sports_fixture_round_2026_07_17.py`'s `_league_blob_index()` keys off the canonical folder name via the UAC
  registry `universe` dict), so they can never be closed by that mechanism regardless of how many times it runs.
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [sports, data-correctness, canonical-naming, fixtures-schedule, non-canonical-path]
related:
  [
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md,
  ]
created: 2026-07-24
assigned_vm: planning
parent_epic: sports_master
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
source: discovered live while running the round-derivation residual backfill (sports_closeout_batch1_ao_ready-008)
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Sports fixtures_schedule — non-canonical raw-af_league_id folders hold unreachable blank-round rows

## How this was found

Running the round-derivation residual backfill (`sports_closeout_batch1_ao_ready-008`), a corpus census reported 486
in-window (season>=2019), registry-member blank-`round` rows across 10 (af_league_id, season) pairs. Running
`backfill_sports_fixture_round_2026_07_17.py --apply` against all 10 pairs applied **zero** fills despite genuine API
fetches succeeding for most pairs (e.g. 309/557/558 fixtures fetched per pair). Direct inspection of the canonical
`league=CHINA_SUPER_LEAGUE` folder (af_league_id=169) showed all 9 of its rows for season=2026 already fully populated —
the reported blanks for that pair didn't live there at all.

A targeted concurrent scan for `af_league_id==169, season==2026` across **every** folder (not just the canonical one)
found the real blanks: 36 rows, **100% under `league=169`** — a folder named with the raw numeric `af_league_id` instead
of the canonical string (`CHINA_SUPER_LEAGUE`). Example paths:

```
sports_reference/by_date/day=2026-05-05/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=169/fixtures_schedule.parquet
sports_reference/by_date/day=2026-05-06/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=169/fixtures_schedule.parquet
```

Re-running the full corpus census with a canonical-vs-non-canonical split (folder name is purely numeric, or the
day-level bare/multi-league parquet) confirmed this is not isolated to one league: **86 of the 486 reachable blanks sit
under non-canonical folders**, leaving 400 in genuinely canonical folders (of which 393 are honest-absence — `J2_LEAGUE`
season 2026 not yet published — and 7 are ordinary fetch-miss residue, both matching the exact terminal- state
categories the 2026-07-19 sweep already established as acceptable).

## Why this is a bug, not a naming variant

`backfill_sports_fixture_round_2026_07_17.py`'s `_league_blob_index()` groups blobs by the `/league=<X>/` path segment
and only ever queries `X` values present in its `universe` dict, which is built from the UAC registry
(`get_leagues_by_classification` over `prediction`/`reference`/`features`) keyed by **canonical** league_id strings
(e.g. `CHINA_SUPER_LEAGUE`). A raw numeric folder name (`league=169`) is never a canonical id, so it is silently
excluded from every scoped run — not because the league is out of registry scope (169 IS a registered af_id, just under
the wrong path), but because the **path itself** was written wrong. The round-derivation day-pool script
(`derive_sports_fixture_round_2026_07_18.py`) is folder-agnostic (groups by the `af_league_id` **column**, not the
path), so it WOULD close these if a canonical-folder sibling existed for the same day — but for the dates observed, no
canonical sibling exists that day, so even the folder-agnostic mechanism can't help.

This is the same defect CLASS as the day=2026-04-14 wrong-schema finding
(`sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`) but a different manifestation: a writer occasionally
resolves the canonical league_id lookup to the raw af_id instead, and writes the shard there.

## Scope measured (2026-07-24, two independent corpus census runs agree exactly)

| population                                                                                                                                |    rows | reachable by existing mechanism?                          |
| ----------------------------------------------------------------------------------------------------------------------------------------- | ------: | --------------------------------------------------------- |
| in-window, registry-member, canonical folder, honest absence (`J2_LEAGUE` 99:2026, season not yet published)                              |     393 | yes — attempted, correctly 0-filled                       |
| in-window, registry-member, canonical folder, fetch-miss residue (`EREDIVISIE` 88:2025, 7 specific fixtures not in the bulk season fetch) |       7 | yes — attempted, correctly 0-filled                       |
| **in-window, registry-member, NON-canonical folder (raw af_league_id or bare)**                                                           |  **86** | **no — structurally invisible to `_league_blob_index()`** |
| **total reachable (registry-member, in-window)**                                                                                          | **486** | —                                                         |

Confirmed `league=169` (CHINA_SUPER_LEAGUE) alone accounts for 36 of the 86; the remaining ~50 are spread across the
other affected pairs (not yet individually enumerated — see todo below).

## Recommended decision

1. Enumerate every non-canonical `league=<numeric>` / bare-day folder in the fixtures_schedule corpus (single walk, not
   per-pair) to size the full non-canonical population beyond the 10 pairs this task happened to sample.
2. Root-cause why the writer sometimes resolves to the raw af_id instead of the canonical league_id string — likely a
   registry lookup miss/fallback in the write path that silently uses the raw id rather than failing loud.
3. Fold the non-canonical shards into their canonical counterparts (merge by `af_fixture_id`, keep whichever content is
   more complete, same snapshot-then-merge pattern already used for the `dex_pools`/`lending_indices` DeFi fold), then
   delete the non-canonical originals — same class of migration as the DeFi canonical folds already completed.
4. Fix the writer so it never falls back to a raw-id folder again; add a regression test.

## Todos

- [ ] [DIAG] P1. Root-cause why the sports fixtures_schedule writer sometimes resolves the canonical league_id lookup to
      the raw `af_league_id` instead of the registered string, and writes the shard under `league=<raw_id>` (repo:
      instruments-service). **Done when**: a written conclusion cites the specific writer code path and the
      lookup-miss/fallback condition that triggers it.
- [ ] [DIAG] P2. Enumerate the full non-canonical (`league=<numeric>` / bare) population across the whole
      fixtures_schedule corpus, not just the 10 pairs this task sampled (repo: instruments-service). **Done when**: a
      corpus-wide census reports the total row count and the set of affected (league, season) pairs.
- [ ] [CODE] P1. Fix the writer so it never falls back to writing under a raw-id folder — fail loud (or resolve via a
      documented, tested fallback) instead (repo: instruments-service). **Done when**: a regression test reproduces the
      old lookup-miss condition and asserts the fix.
- [ ] [DATA] P2. Fold every non-canonical shard's rows into its canonical counterpart (merge by `af_fixture_id`,
      snapshot first, delete the non-canonical original after verification), same pattern as the DeFi
      `dex_pools`/`lending_indices` fold (repo: instruments-service). **Done when**: a post-fold corpus census shows
      zero non-canonical `league=<numeric>`/bare fixtures_schedule shards remain, and every previously non-canonical row
      is present (verified by `af_fixture_id`) in its canonical folder.
