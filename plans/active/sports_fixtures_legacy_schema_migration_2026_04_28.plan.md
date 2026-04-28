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

### Phase 0 — Pre-audit (this session)

- [ ] [AGENT] P0. Scan every `entity=fixtures/fixtures.parquet` under `sports_reference/by_date/` and record schema
      (`af_league_id` present? row count? legacy struct columns present?). Output:
      `instruments-service/scripts/sports_legacy_schema_audit.json` keyed by `day=YYYY-MM-DD`. ~3,627 reads (parallelize
      via gsutil cp + multiprocessing).
- [ ] [AGENT] P0. Spot-check 10 LEGACY days: row count + verify all expected columns present (corners, xG, possession,
      etc.).
- [ ] [AGENT] P0. Identify any LEGACY day with `af_league_id` PARTIAL population (some rows have it, others don't) —
      document as edge case for the mapper.

### Phase 1 — Mapper helper (this session)

- [ ] [AGENT] P0. Author `instruments-service/instruments_service/sports/legacy_schema_mapper.py`: -
      `is_legacy_schema(df) -> bool` — returns True if `af_league_id` column missing AND `league` struct column
      present. - `map_legacy_to_new(df_legacy) -> tuple[pd.DataFrame, pd.DataFrame]` — returns
      `(fixtures_new_df, fixture_stats_df)` per the schema mapping table above. - Helpers: `_parse_af_id_from_logo(url)`
      (regex `/leagues|teams/(\d+)\.png`), `_parse_status_struct(cell)` returns `(short, long, elapsed)`,
      `_derive_winner_id(home_score, away_score, home_id, away_id)`.
- [ ] [AGENT] P0. Strict-mode types: every helper uses `pd.Series[X]` / `pd.DataFrame` types; no `Any` returns.
- [ ] [AGENT] P0. Schema provenance: import `SPORTS_FIXTURES` and `SPORTS_FIXTURE_STATS` `SchemaContract`s from UAC;
      build output DataFrames with column order matching `contract.required_columns`.

### Phase 2 — Parity tests (this session)

- [ ] [AGENT] P0. `tests/unit/test_sports_legacy_schema_mapper.py`: - Fixture: hand-crafted LEGACY DataFrame with 3 rows
      (1 home win, 1 away win, 1 draw) covering all column types. - `test_is_legacy_schema_*` — true for legacy fixture,
      false for new schema fixture, false for empty DF. - `test_map_legacy_to_new_fixtures_columns` — output fixtures DF
      has all 32 new-schema columns in the right order. - `test_map_legacy_to_new_fixture_stats_columns` — output
      fixture_stats DF has all ~18 new-schema columns. - `test_winner_id_derivation` — covers home win / away win /
      draw. - `test_logo_url_parser_handles_missing_url` — graceful null on malformed cells. -
      `test_round_trip_against_uac_contracts` — `validate_row_df(fixtures_out, SPORTS_FIXTURES)` and
      `validate_row_df(fixture_stats_out, SPORTS_FIXTURE_STATS)` both pass strict-mode validation.
- [ ] [AGENT] P0. `tests/integration/test_sports_legacy_real_parquet.py`: - Reads 3 real LEGACY parquets from a fixture
      bucket (`tests/fixtures/sports_legacy_*.parquet`, copied once via `gsutil cp` and committed at < 100KB each). -
      Asserts row counts + at-least-one row per known league (af_league_id 39 = EPL, 140 = LaLiga, 78 = Bundesliga).
- [ ] [AGENT] P0. Run `cd instruments-service && bash scripts/quality-gates.sh` — must be green.

### Phase 3 — Per-VM rewrite (next session, post-approval)

- [ ] [AGENT] P0. Author `instruments-service/scripts/migrate_sports_fixtures_legacy_to_new.py`: - `--year YYYY` flag —
      scans `day=YYYY-*` partitions only. - `--output-prefix sports_reference_v2/` — write all output to a side-by-side
      prefix; never touches legacy in-place. - Per day: read legacy fixtures.parquet, call
      `legacy_schema_mapper.map_legacy_to_new`, write
      `sports_reference_v2/by_date/day={D}/entity=fixtures/fixtures.parquet` +
      `entity=fixture_stats/fixture_stats.parquet`. - For NEW-schema days: pass-through copy to `sports_reference_v2/`
      (so the v2 prefix is complete after Phase 3, ready for atomic rename in Phase 4). - Shard-level isolation: per-day
      failures emit `MIGRATION_SHARD_FAILED` + `classify_venue_error` and continue.
- [ ] [AGENT] P0. VM launch script
      `deployment-service/scripts/vm/launch-sports-fixtures-migration-vm.sh     --year YYYY` mirroring
      `launch-instruments-smoke-vm.sh`. e2-standard-4, `IS_TEST_RUN=true` initially for the first year, then full.
- [ ] [OPERATOR] P0. Refresh tarballs first:
      `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group SPORTS`.
- [ ] [OPERATOR] P0. Launch 8 VMs in parallel (one per year 2018-2025). Each writes to `sports_reference_v2/`. Watch for
      `MIGRATION_SHARD_FAILED` events. Per-year wall-clock ~7 min.
- [ ] [OPERATOR] P0. Reap VMs once `RUN_COMPLETE` event fires.

### Phase 4 — Atomic cutover (operator-gated)

- [ ] [OPERATOR] P0. Parity validation script: `scripts/validate_sports_fixtures_v2_parity.py` reads both
      `sports_reference/by_date/day={D}/entity=fixtures/fixtures.parquet` and
      `sports_reference_v2/.../fixtures.parquet`, asserts: - row count match (LEGACY: legacy_rows == fixtures_v2_rows;
      NEW: new_rows == fixtures_v2_rows). - For LEGACY days: spot-check 5 random rows that
      `af_league_id == derived_from_legacy_logo`, `af_home_id == derived_from_legacy_home_logo`, etc. - Output
      `parity_report.json` per day; fail if any mismatch.
- [ ] [OPERATOR] P0. Atomic rename:
      `     gsutil -m mv gs://...sports_reference/ gs://...sports_reference_v1_archive/     gsutil -m mv gs://...sports_reference_v2/ gs://...sports_reference/     `
      < 5 min wall-clock. Producers (sports adapter) MUST be paused for this window — operator coordinates via
      `pause-sports-adapter.sh` (deployment-service script that toggles a Cloud Scheduler job).
- [ ] [OPERATOR] P0. Smoke: `curl /api/data-status/download-fixtures-csv?day=2018-04-01&league_id=EPL` returns 2 rows
      (same as today via the view-time normalizer).

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
