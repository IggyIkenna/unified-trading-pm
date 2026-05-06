---
name: sports-fixtures-legacy-schema-migration
slug: sports_fixtures_legacy_schema_migration_2026_04_28
date: 2026-04-28
owner: claude-code
status: active
priority: P2
phase: pending_approval
domain: data-pipeline
related_plans: []
locked_by: live-defi-rollout
locked_since: 2026-04-28
---

# Sports fixtures legacy → new schema migration (Option B)

## Background

`gs://instruments-store-sports-{pid}/sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet` exists in **two
schemas** that were written by different generations of the sports adapter:

- **NEW** (post ~2019/2020): 32 flat columns —
  `af_league_id, af_fixture_id, af_home_id, af_home_name, af_away_id, af_away_name, timestamp, status_short, …` plus
  score breakdowns; match stats split out into a separate `entity=fixture_stats/` parquet.
- **LEGACY** (pre ~2019, plus scattered partial backfills): 41 columns with nested struct cells —
  `league = {country, league_id, logo_url, name}`, `home_team = {name, logo_url, …}`, `away_team = {…}`, `venue = {…}`,
  `status = {…}`, plus all match stats inline (`home_xg, away_xg, home_corners, home_possession, home_passes_total, …`).

deployment-api commit `c6a4044` (2026-04-28) added view-time normalization so reads work against both schemas. This plan
executes the **side-by-side rewrite** that retires the legacy form on disk so every consumer (BigQuery external tables,
ML pipelines, ad-hoc analytics) sees one schema.

## Pre-audit manifest

| Surface                 | Read site                                                                          | Action                                                                                                                   |
| ----------------------- | ---------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| deployment-api          | `services/data_status_drilldown.py::_extract_af_league_id_series`                  | **keep** for backwards compat during rollout; delete after Phase 4                                                       |
| features-sports-service | `engine/orchestrator.py:175` (reads `entity=fixtures`)                             | already on new schema; will continue to work because Phase 3 ATOMIC RENAME drops in new-schema parquets at the same path |
| features-sports-service | `engine/orchestrator.py:413` (reads `entity=fixture_stats`)                        | will see the new split-out stats parquets after migration; today this read returns empty for legacy days                 |
| ml-training-service     | BigQuery external tables over `instruments-store-sports-{pid}/sports_reference/**` | will see one schema after migration; pre-migration the queries fail / skip rows on legacy days                           |

**Scope:**

- Bucket: `gs://instruments-store-sports-{pid}/sports_reference/by_date/`
- ~3,627 day partitions discovered today; legacy schema scattered (no clean date boundary — partial backfills mean both
  schemas coexist within 2018-2022).
- Legacy entities present on legacy days: `entity=fixtures`, `entity=injuries`, `entity=leagues`, `entity=standings`,
  `entity=teams`, `entity=understat_xg` (no `entity=fixture_stats`, `entity=fixture_lineups`, `entity=fixture_events`,
  `entity=footystats_*`, `entity=player_stats`, `entity=weather` — those are post-2024 entities).
- **Only `entity=fixtures` is in scope for this plan.** Other legacy entities (`teams`, `leagues`, `standings`,
  `injuries`, `understat_xg`) are smaller and untouched by deployment-api consumers; defer to a Phase 6 follow-up if
  they surface as a problem.

## Architectural design

### Schema mapping (LEGACY → NEW + entity=fixture_stats split)

The 41-col legacy fixtures parquet decomposes into TWO output parquets:

**`fixtures.parquet` (32 cols, NEW schema)** — fixture metadata only:

| New column                                     | Legacy source                                          |
| ---------------------------------------------- | ------------------------------------------------------ |
| `af_fixture_id`                                | parse `int(source_fixture_id)`                         |
| `af_league_id`                                 | regex `/leagues/(\d+)\.png` against `league.logo_url`  |
| `af_home_id`                                   | regex `/teams/(\d+)\.png` against `home_team.logo_url` |
| `af_home_name`                                 | `home_team.name`                                       |
| `af_away_id`                                   | regex against `away_team.logo_url`                     |
| `af_away_name`                                 | `away_team.name`                                       |
| `af_winner_id`                                 | derived: home/away score comparison; `null` on draw    |
| `home_score`, `away_score`                     | `home_goals`, `away_goals`                             |
| `home_score_halftime`, `away_score_halftime`   | `home_goals_halftime`, `away_goals_halftime`           |
| `home_score_fulltime`, `away_score_fulltime`   | same as `home_goals` (legacy doesn't separate)         |
| `home_score_extratime`, `away_score_extratime` | `null` (legacy doesn't capture)                        |
| `home_score_penalty`, `away_score_penalty`     | `null`                                                 |
| `timestamp`, `date`                            | `kickoff_utc`                                          |
| `day`                                          | partition key (already known per migration call)       |
| `season`                                       | `season` (passthrough)                                 |
| `round`                                        | `null` (legacy doesn't capture)                        |
| `status_short`, `status_long`                  | parse `status` struct                                  |
| `status_elapsed_time`                          | `null`                                                 |
| `periods_first`, `periods_second`              | `null`                                                 |
| `referee_name`                                 | `referee`                                              |
| `venue_id`, `venue_name`, `venue_city`         | parse `venue` struct                                   |
| `data_available_at`                            | `data_available_at` (passthrough)                      |

**`fixture_stats.parquet` (~18 cols, NEW schema)** — match stats split-out:

| New column                                     | Legacy source                            |
| ---------------------------------------------- | ---------------------------------------- |
| `af_fixture_id`                                | same `int(source_fixture_id)` (join key) |
| `home_xg`, `away_xg`                           | passthrough                              |
| `home_total_shots`, `away_total_shots`         | passthrough                              |
| `home_shots_on_target`, `away_shots_on_target` | passthrough                              |
| `home_shots_blocked`, `away_shots_blocked`     | passthrough                              |
| `home_corners`, `away_corners`                 | passthrough                              |
| `home_fouls`, `away_fouls`                     | passthrough                              |
| `home_offsides`, `away_offsides`               | passthrough                              |
| `home_possession`, `away_possession`           | passthrough                              |
| `home_passes_total`, `away_passes_total`       | passthrough                              |
| `home_passes_accuracy`, `away_passes_accuracy` | passthrough                              |
| `home_yellow_cards`, `away_yellow_cards`       | passthrough                              |
| `home_red_cards`, `away_red_cards`             | passthrough                              |
| `match_week`                                   | passthrough                              |
| `data_available_at`                            | passthrough                              |

### Phased execution DAG

```
Phase 0 (pre-audit) ──► Phase 1 (mapper) ──► Phase 2 (parity tests)
                                                        │
                                                        ▼
                                       Phase 3 (per-VM rewrite × N years)
                                                        │
                                              ┌─────────┴─────────┐
                                              ▼                   ▼
                                  Phase 4 (atomic cutover) ──► Phase 5 (cleanup)
```

- Phase 0–2 SEQUENTIAL on a workstation (~1 day).
- Phase 3 PARALLEL — N small VMs, one per year-shard (8 years × ~7 min/year ≈ wall-clock 10 min).
- Phase 4 SEQUENTIAL atomic rename (~5 min).
- Phase 5 SEQUENTIAL cleanup (~30 min).

## Todos

### Phase 0 — Pre-audit (DONE 2026-04-28)

- [x] [AGENT] P0. Scan every day partition under `sports_reference/by_date/` via entity-set signature (legacy = no
      `entity=fixture_stats/`). Output: `instruments-service/scripts/sports_legacy_schema_audit.json` keyed by
      `day=YYYY-MM-DD`. 124s wall-clock for 3,627 days. (Initial pyarrow `read_metadata` approach was too slow / hung at
      ~600 reads after 18 min — switched to delimiter-based listing.)
- [x] [AGENT] P0. Sanity-check confirmed 2018-04-01 LEGACY (`league` struct, 402 rows), 2024-08-17 NEW (14 entities),
      2026-04-15 LEGACY (276 rows, real legacy schema not just missing partition).
- [x] [AGENT] P0. Audit summary: NEW 2,459 / LEGACY 594 / MISSING 574.

### Phase 0.5 — Writer regression fix (NEW — discovered by audit)

**Audit finding**: 112 LEGACY days are in 2026, including current dates (e.g. 2026-04-15). The fixtures-writer is still
emitting legacy schema concurrently with newer per-entity writers (`progressive_stats`, `sfi_leagues`, `footystats_*`).
Without fixing the writer, any one-shot rewrite would be re-polluted by the next adapter run.

LEGACY-by-year breakdown from audit: 2018=364, 2019=27, 2020=58, 2021=2, 2022=7, 2023=4, 2024=8, 2025=12, **2026=112** ←
active regression.

- [x] [AGENT] P0. Locate the writer. **Found**: `instruments-service/instruments_service/engine/orchestrator.py` lines
      3126 + 3187 (post-fix; pre-fix lines ~3011 + ~3072). Two `pd.DataFrame([fx.model_dump() for fx in fixtures])`
      patterns where `CanonicalFixture` keeps nested `league` / `home_team` / `away_team` / `venue` Pydantic structs;
      `model_dump()` preserves them as parquet struct cells = the legacy schema. No separate "legacy writer" exists —
      this IS the live orchestrator and has always emitted nested structs; what changed in 2024 is sibling writers
      (`fixture_stats`, `progressive_stats`, `footystats_*`) showed up alongside it on more days.
- [x] [AGENT] P0. Fix shipped: instruments-service `90a0940` introduces `_flatten_canonical_fixture_for_disk(fx, day)`
      that maps CanonicalFixture → 32 flat columns matching `SPORTS_FIXTURES` SchemaContract. Both write call-sites
      flipped; per-league groupby uses `af_league_id`. PIT `data_available_at` derives from `timestamp` (new field)
      instead of `kickoff_utc` (legacy field).
- [x] [AGENT] P0. Unit tests: `tests/unit/test_orchestrator_fixture_flattener.py` (13 cases) — column-set guarantee,
      no-nested-cell, af_id resolution, winner_id derivation, default-null on ET / penalty / period, DataFrame assembly.
      All passing.
- [ ] [OPERATOR] P0. **Smoke (deferred)**: refresh tarballs, launch one sports VM for a recent date (e.g. today), re-run
      the audit script, confirm the new day's parquet has `af_league_id` column + no `league` struct. Tarball + VM steps
      from `unified-trading-pm/codex/05-infrastructure/vm-tarball-deployment.md`.

### Phase 0.6 — Verification (DONE 2026-04-28, after writer fix landed)

- [x] [AGENT] P0. Re-ran audit (smoke VM `af-backfill-20260428-143127` for 2026-04-29 wrote NEW flat schema, 329 rows,
      verified via direct parquet read). Audit upgraded to two-pass design (entity-set then parquet header probe via
      Blob.download_as_bytes; pyarrow gs:// URI hangs at scale).
- [x] [AGENT] P0. Refined classification: NEW 2,459 / **LEGACY 398** (was 594 — 197 promoted to ORPHAN_NEW) /
      MISSING 573. instruments-service `bcf630a`.

### Phase 1 — Mapper helper (DONE)

- [x] [AGENT] P0. Authored `instruments-service/instruments_service/sports/legacy_schema_mapper.py` with
      `is_legacy_schema(df)` + `map_legacy_to_new(df, day)` returning `(fixtures_df, fixture_stats_df)` tuple. Helpers
      `_parse_af_id_from_struct` (logo_url regex), `_derive_winner_id`. Imports: stdlib + pandas only (no UAC import to
      avoid cycles; column lists + dtype implied by the SPORTS_FIXTURES SchemaContract).
- [x] [AGENT] P0. Empty-DataFrame path preserves column order via explicit column list. Output column sets pinned via
      `_FIXTURES_COLUMNS` + `_FIXTURE_STATS_COLUMNS` constants.

### Phase 2 — Parity tests (DONE)

- [x] [AGENT] P0. `tests/unit/test_sports_legacy_schema_mapper.py` — 18 tests: is_legacy_schema true/false/empty, full
      SPORTS_FIXTURES + SPORTS_FIXTURE_STATS column-set guarantee, no-nested-cell, af_id from logo_url, winner_id
      (home/away/draw/unplayed), default-null on ET / penalty / period, stats routing, fixture_id join consistency,
      malformed cells, empty DF column order, kickoff_utc → date/timestamp. All 18 passing.
- [x] [AGENT] P0. instruments-service `d4ca6b5`.

### Phase 3 — Side-by-side rewrite (DONE — local Python, not VM)

- [x] [AGENT] P0. Authored `instruments-service/scripts/migrate_sports_fixtures_legacy_to_new.py`. Reads
      `sports_legacy_schema_audit.json` for the LEGACY day set; per day downloads fixtures.parquet, runs
      `map_legacy_to_new`, writes to `sports_reference_v2/by_date/day={D}/entity=fixtures/fixtures.parquet` +
      `entity=fixture_stats/fixture_stats.parquet`. 16-thread, dry-run + limit flags. Shard-level failure isolation.
- [x] [AGENT] P0. **Ran locally** (no VM needed for 20MB at 16 threads). 398 days migrated in 121s wall-clock, 72,522
      rows in / 72,522 fixtures + 72,522 fixture_stats out. Zero failures.

### Phase 4 — Per-day in-place cutover (DONE — replaces atomic-rename plan)

- [x] [AGENT] P0. Authored `instruments-service/scripts/validate_sports_fixtures_v2_parity.py` — per-day row-count
      match + af_league_id derivation parity (legacy logo_url regex == v2 column) + af_fixture_id consistency between
      fixtures and fixture_stats. **All 398/398 days passed parity in 75s.**
- [x] [AGENT] P0. Authored `instruments-service/scripts/cutover_sports_fixtures_v2_to_canonical.py` — strategy pivoted
      from bucket-wide atomic-rename to **per-day in-place overwrite** so sibling entities (teams, leagues, injuries,
      etc.) stay untouched. Idempotent: skips canonical→archive copy if archive blob already exists. Reversible via
      `--reverse` flag (pulls from `sports_reference_v1_archive/` back to canonical).
- [x] [OPERATOR] P0. Paused 4 forward-poll Cloud Schedulers in `asia-northeast1`
      (`uts-dev-sports-fixtures-{6am,     noon,6pm,midnight}-t1-schedule`) before cutover.
- [x] [AGENT] P0. **Cutover EXECUTED 2026-04-28 15:04**: 398 days in 127s, zero failures. Final audit: **0 LEGACY days
      remaining** (NEW jumped 2,459 → 2,857; ORPHAN_NEW + MISSING unchanged). instruments-service `507792a`.
- [x] [OPERATOR] P0. Re-enabled all 4 forward-poll schedulers. Spot-checks across 2018-04-01, 2020-06-15, 2024-12-15,
      2026-04-15 all confirm canonical now flat schema, archive holds legacy, fixture_stats partition added.

### Phase 5 — Cleanup (next session)

- [ ] [AGENT] P0. Delete view-time normalization: remove `_extract_af_league_id_series` from
      `deployment-api/deployment_api/services/data_status_drilldown.py`, revert to direct `df["af_league_id"]` access.
      CI green per repo.
- [ ] [AGENT] P0. Delete `instruments_service/sports/legacy_schema_mapper.py` (kept only for the migration; no runtime
      caller after rename).
- [ ] [AGENT] P0. Update codex doc `unified-trading-pm/codex/02-data/sports-fixtures-schema.md` — drop the dual-schema
      callout; legacy schema is retired.
- [ ] [OPERATOR] P0. After 7 days of green production: delete `gs://...sports_reference_v1_archive/`
      (`gsutil -m rm -r`).

### Phase 6 — Other legacy entities (deferred)

- [ ] [AGENT] P1. If `entity=teams`, `entity=leagues`, `entity=standings`, `entity=injuries`, `entity=understat_xg` need
      migration: separate mapper per entity, same VM-shard pattern. Triggered only if a consumer surfaces a
      schema-mismatch failure.

## Repo update classification

| Repo                | Files                                                                   | Change type                      |
| ------------------- | ----------------------------------------------------------------------- | -------------------------------- |
| instruments-service | `sports/legacy_schema_mapper.py` (new) + tests + `scripts/migrate_*.py` | feat — purely-additive Phase 1-3 |
| deployment-service  | `scripts/vm/launch-sports-fixtures-migration-vm.sh` (new)               | feat                             |
| deployment-api      | `services/data_status_drilldown.py::_extract_af_league_id_series`       | DELETE in Phase 5                |
| unified-trading-pm  | this plan + codex update                                                | docs                             |

## Effort estimate

- Phase 0 (audit): 0.5 day
- Phase 1 (mapper + types): 0.5 day
- Phase 2 (tests): 0.5 day
- Phase 3 (VM rewrite): 0.5 day code + ~10 min wall-clock
- Phase 4 (cutover): 0.5 day (parity validation + coordination)
- Phase 5 (cleanup): 0.25 day
- **Total: ~2.75 days** + ~$5-10 GCP compute

## Rollback plan

- **Phase 3 fails partway**: just delete `sports_reference_v2/`. Original `sports_reference/` untouched. No producer
  impact.
- **Phase 4 atomic rename fails**: `gsutil -m mv sports_reference_v1_archive/ sports_reference/` reverses it. The sports
  adapter resumes against the original prefix. Total downtime < 10 min worst case.
- **Phase 5 reveals a missed consumer**: keep `sports_reference_v1_archive/` for the 7-day window; restore via reverse
  rename if any consumer breaks.

## Success criteria

- **Phase 2 gate**: parity tests + UAC schema-contract validation green on hand-crafted + 3 real LEGACY parquet samples.
- **Phase 3 gate**: 8 year-VMs report `RUN_COMPLETE`; zero `MIGRATION_SHARD_FAILED` events; `sports_reference_v2/` total
  bytes ≈ `sports_reference/` total bytes (within 5% — accounts for the fixture_stats split-out adding new files but
  each smaller).
- **Phase 4 gate**: parity report shows 100% row count match across every day partition; smoke endpoint returns same
  rows as before.
- **Phase 5 gate**: deployment-api QG green after view-time normalizer removed; codex doc updated.
- **B1 (business)**: BigQuery external tables over `sports_reference.fixtures` query with native `af_league_id`
  predicates — no UDF / schema branching needed in downstream ML.

## References

- Schema diff established 2026-04-28 via probes: legacy 41 cols vs new 32 cols, only 2 in both (`data_available_at`,
  `season`).
- Today's view-time normalizer: deployment-api `c6a4044`.
- Per-VM tarball deployment SSOT: `unified-trading-pm/codex/05-infrastructure/vm-tarball-deployment.md`.
- Shard-level failure isolation: `unified-trading-pm/codex/04-architecture/shard-level-failure-isolation.md`.
