---
doc_type: issue
title:
  instruments-service cut the sports FIXTURES writer over to the fixtures_schedule/fixtures_outcomes entity-folder split
  with NO legacy dual-write — every downstream fixtures reader that still targets the legacy entity=fixtures path
  (features-service direct GCS reader + UTL's designated read_fixtures_joined() flip point) hard-fails for every date
  on/after the cutover
summary:
  "While running sports_p2_features_history_to_ml_ready-001 (Compute features 2015→present), gap-fill VM
  features-sports-sports-20260715-005012 (range 2025-08-11→2026-07-14) completed 306/307 dates cleanly then exited rc=1
  on the LAST date (2026-07-14) with `DependencyError: Required upstream blob missing within coverage: entity=fixtures
  date=2026-07-14`. GCS inspection confirmed day=2026-07-14 has ONLY
  pipeline_mode=batch_api_football/entity=fixtures_schedule/league=*/ and entity=fixtures_outcomes/league=*/ — no
  entity=fixtures at all (present, per-league, through 2026-07-13). Read
  instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py's fixtures writer: it unconditionally
  writes ONLY fixtures_schedule + fixtures_outcomes (via _gated_sink_write), no legacy dual-write, no feature-flag gate
  found in the codebase — the split write path is now the ONLY fixtures writer. This matches the open plan
  sports_fixtures_schema_split_completion_2026_06_20.md, whose 'Already shipped' section says the UTL reader-side join
  helper (read_fixtures_joined, utl@b2f60f31) already exists to 'hide the split from consumers' — but that helper's own
  docstring + code (unified-trading-library/unified_trading_library/fixtures/joined_reader.py) says the two-entity read
  is GATED ('has NOT run ... until after the sports canonicalisation migration') and still only reads the legacy single
  entity=fixtures parquet. The writer shipped its half of this coordinated migration (per the plan's own
  cross-plan-banner rule: 'the entity-folder split + migration + writegate same-day flip MUST ship in a single
  coordinated unit') without the reader-side flip landing alongside it. Net effect: ANY fixtures read for ANY date
  on/after the writer cutover (first observed 2026-07-14, so this is presumably affecting the LIVE daily sports pipeline
  too, not just this one backfill) returns nothing from every current reader — features-service raises DependencyError
  (blocks batch honest-absence recording / would halt live's circuit-breaker), and UTL's read_fixtures_joined() (zero
  current production callers, confirmed via workspace-wide grep) silently returns an empty frame. A second, independent
  drift also confirmed: even where entity=fixtures legacy rows still exist (through 2026-07-13), the raw
  score-distinction columns already use the NEW Q6 naming
  (home_score_regulation/home_score_after_extra_time/home_score_after_penalty_shootout, per
  instruments-service/instruments_service/engine/orchestrator/__init__.py:_Q6_OUTCOME_COLUMNS) — NOT the OLD naming
  (home_score_fulltime/home_score_extratime/home_score_penalty) that joined_reader.py's own docstring and column logic
  (_derive_outcomes_available_at, OUTCOME_COLUMNS tuple) still assume. So joined_reader.py is stale on BOTH the
  entity-split axis and the column-naming axis. FIXED (this session, scoped to features-service only — the plan's own
  repos list for sports_p2_features_history_to_ml_ready_2026_06_27.md does not include unified-trading-library): added
  _read_split_fixtures_fallback() to features-service's gcs_reader.py — when the legacy singleton AND per-league
  entity=fixtures reads both miss, it reads+left-joins the fixtures_schedule/fixtures_outcomes per-league shards on
  af_fixture_id (both split entities keep the writer's original raw column names unchanged — the split only partitions
  COLUMNS across two files, it does not rename them — so no column-mapping was needed) and returns the same shape
  normalize_fixtures already handles. 3 new regression tests added (TestReadReferenceEntitySplitFixturesFallback in
  tests/sports/unit/test_gcs_paths_and_reader_deps.py) covering: both split entities present (joined, unplayed fixtures
  get NaN outcome columns), only fixtures_schedule present (upcoming/unplayed fixtures, no outcomes shard yet), and
  neither split entity present (genuine gap — still raises DependencyError unchanged). NOT fixed here (cross-repo, out
  of this task's repo scope, flagged for operator routing): UTL's joined_reader.py — its own docstring names it 'the
  single place to flip' for this exact migration but nothing currently calls it in production, so fixing it is
  safe/isolated but is a unified-trading-library change outside this plan's repos:[]. Recommend implementing the same
  two-entity join there (reusing/porting this fix's approach) plus updating
  OUTCOME_COLUMNS/_derive_outcomes_available_at to the current Q6 raw names, THEN pointing features-service's gcs_reader
  at it instead of the duplicated local fallback, so there is truly one place that owns the joined view per the module's
  own design intent. Also flagging for operator: because the writer cutover has NO dual-write and appears date-triggered
  (not env/flag-gated), this likely already broke the LIVE daily sports pipeline's fixtures ingestion (not just this
  backfill) for every day since the cutover — worth an urgent check of live/forward sports compute logs for the same
  DependencyError signature."
status: resolved
nature: issue
asset_group: [sports]
stage: [features, data]
repos:
  [
    features-service,
    instruments-service,
    unified-trading-library,
    deployment-api,
    deployment-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags:
  [
    sports,
    fixtures,
    schema-migration,
    fixtures-schedule,
    fixtures-outcomes,
    honest-absence,
    data-correctness,
    cross-repo,
    reader-writer-drift,
  ]
related:
  [
    /plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    /plans/archive/2026_07/sports_fixtures_schema_split_completion_2026_06_20.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-15
parent_epic: sports_master
priority: P0
source:
  [
    "data_engineering slot-6, discovered while re-verifying sports_p2_features_history_to_ml_ready-001's gap-fill VM
    fleet, 2026-07-15",
    "data_engineering slot-4, P3 workspace grep for other direct entity=fixtures readers, 2026-07-15",
  ]
assigned_vm: planning
resolved_by:
  ["features-service (this session, reader-side split fallback + 3 regression tests, in-flight — see commit below)"]
locked_by:
locked_since:
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

> **🔴 NOTIFY-OPERATOR — cross-repo data-correctness gap; live sports feature-compute impact RULED OUT, but a wider and
> more urgent blast radius CONFIRMED inside instruments-service itself.** instruments-service shipped the FIXTURES →
> fixtures_schedule/fixtures_outcomes writer cutover (sports_fixtures_schema_split_completion_2026_06_20.md) with no
> legacy dual-write and no reader-side coordination. Every current direct `entity=fixtures` reader hard-fails or
> silently degrades for any date on/after the cutover (first observed 2026-07-14). Confirmed status as of 2026-07-15:
> (1) live sports feature-compute was never at risk — no live launcher has ever run for sports (finding #7); (2) the
> features-service backfill blocker is fixed this session; (3) a **workspace-wide grep (finding #8) found
> instruments-service's OWN `sports_dependency.py` pre-flight gate is blocking 6 downstream venue adapters
> (footystats/understat/transfermarkt/soccer_football_info/open_meteo/betfair) for every date on/after the cutover** —
> this is the single most urgent open item now (new P0 todo below), plus 4 more affected readers across
> deployment-api/deployment-service/MTDS and a UAC SSOT gap (new P1 todos below).

# instruments-service FIXTURES writer/reader entity-split desync

## What I found

1. **Trigger**: `sports_p2_features_history_to_ml_ready-001` gap-fill VM `features-sports-sports-20260715-005012` (range
   2025-08-11→2026-07-14) processed 306/307 dates cleanly, then exited `rc=1` on the LAST date (2026-07-14):
   `DependencyError: Required upstream blob missing within coverage: entity=fixtures date=2026-07-14 — gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day=2026-07-14/entity=fixtures/fixtures.parquet`.

2. **GCS confirms the writer cutover**: `day=2026-07-14/` has ONLY
   `pipeline_mode=batch_api_football/entity=fixtures_schedule/league=*/` and `entity=fixtures_outcomes/league=*/` — zero
   `entity=fixtures` objects. `day=2026-07-13/` and earlier still have `entity=fixtures/league=*/` (per-league legacy
   shape). `day=2026-07-10/day=2026-07-12` had neither `entity=fixtures` nor fixtures for those specific days but the
   per-league FALLBACK correctly found 1-2 rows via the legacy per-league probe — this is unrelated normal thin-day
   behavior, not the bug.

3. **Writer code confirms no dual-write**:
   `instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py`'s fixtures write function calls
   `_orch._gated_sink_write(...)` TWICE — once for `entity=fixtures_schedule` (all fixtures) and once for
   `entity=fixtures_outcomes` (completed fixtures only, gated on `home_score_regulation.notna()`). No third write to
   `entity=fixtures`. Grepped the whole orchestrator module for a feature-flag / env-var gate controlling old-vs-new
   write path — none found. This appears to be an unconditional, permanent cutover, not a staged rollout.

4. **The reader-side flip point exists but is stale-and-unwired**:
   `sports_fixtures_schema_split_completion_2026_06_20.md`'s "Already shipped" section names
   `unified_trading_library.fixtures.joined_reader.read_fixtures_joined(day, league_id)` (utl@b2f60f31) as the helper
   that "hides the split from consumers." Reading that module directly: its own docstring says "The GCS entity-folder
   split ... has NOT run and is gated until after the sports canonicalisation migration. Once the split lands, this
   reader switches to a two-entity read" — i.e. it was SHIPPED AS A STUB/GATED NO-OP, deliberately deferred, and the
   flip was never done. `_load_fixtures_for_day` still reads only
   `gs://{bucket}/sports_reference/by_date/day={day}/entity=fixtures/fixtures.parquet`. Workspace-wide grep for
   `read_fixtures_joined|joined_reader|read_fixtures_outcomes_pit_safe` found **zero production call sites** — only its
   own test file, its own `fixtures/__init__.py` export, and a doc-comment mention in
   `instruments-service/scripts/migrate_fixtures_split.py` (not a call). So nothing in production currently depends on
   this helper's current (broken) behavior — safe to fix in isolation.

5. **features-service's OWN direct GCS reader is separately broken** (not routed through the UTL helper at all):
   `features-service/features_service/sports/data/gcs_reader.py`'s `read_reference_entity(date, "fixtures")` probes the
   legacy singleton path, then the legacy per-league path, then raises `DependencyError` (since `"fixtures"` is in
   `_REQUIRED_ENTITIES` and the date is within `_FIXTURES_SOURCE_COVERAGE_START`). Neither probe knows about the split
   entities.

6. **A second, independent naming drift**: even for historical dates where `entity=fixtures` legacy rows still exist,
   the raw score columns already use the NEW Q6 naming (`home_score_regulation` / `home_score_after_extra_time` /
   `home_score_after_penalty_shootout` / `home_penalty_shootout_score`, per
   `instruments-service/instruments_service/engine/orchestrator/__init__.py:_Q6_OUTCOME_COLUMNS`), NOT the OLD naming
   (`home_score_fulltime` / `home_score_extratime` / `home_score_penalty`) that `joined_reader.py`'s own
   `OUTCOME_COLUMNS` tuple and docstring still assume. This means `joined_reader.py` was already stale on the
   column-naming axis independent of the entity-split axis — likely from an earlier, unrelated Q6 column-rename that
   also didn't reach this module.

7. **Live-incident check (this session, slot-7, 2026-07-15) — RULED OUT, no live production incident.**
   - Code path: `features-service/features_service/sports/cli/handlers/live_handler.py`'s `LiveHandler` (PubSub
     `persist-sports-odds-features-reader` subscriber) calls the shared engine
     `features_service/sports/engine/orchestrator.py::process_sports_record` / `_process_sports_record_impl`. That
     module has **zero import or call of `read_reference_entity`** — it computes features directly from the PubSub odds
     payload and never reads the `entity=fixtures` GCS blob. The `DependencyError` signature is raised only from
     `gcs_reader.py::read_reference_entity`, which is called exclusively by `batch_handler.py` and
     `pipeline/fixture_features.py` — both BATCH-mode-only code. So even if sports live mode were running, this exact
     error cannot fire on that path today.
   - Deployment check: no `mdps-features-live-sports-*` VM (the asset-scoped live launcher,
     `deployment-service/scripts/vm/launch-mdps-features-live.sh --asset-group sports`) has EVER been created — verified
     via `gcloud logging read` GCE-insert audit trail over the last 30 days (zero hits, project
     `central-element-323112`), consistent with that launcher's own header comment: "operational launch awaits Harsh
     slot 5 per-service consumer wiring + Phase 12 reconciliation gate green" (i.e. Phase 15 of
     `live_pipeline_mtds_mdps_features_2026_05_08.md` has not shipped for any asset_group, sports included). No
     equivalent instance found on AWS EC2 either (only the two `agent-orchestrator*` VMs are running there).
   - The only running/recent `*sports*` GCE instances (checked via `gcloud compute instances list` +
     `gcloud logging read` insert/delete audit trail, project `central-element-323112`) are a churn of short-lived
     `features-sports-sports-<date>-<time>` VMs — these are the BATCH gap-fill/backfill fleet from
     `sports_p2_features_history_to_ml_ready-001` (the same family as this issue's trigger VM), not live mode.
   - **Conclusion: no live/forward sports feature-compute incident, past or present.** The writer/reader desync is
     currently a backfill-only blocker (Todo 1 in "Recommended decision" is answered: rule out confirmed). Still worth
     fixing Todos 2-4 before ANY future live launch of sports (Phase 15), since the live gap only stays closed by
     accident (no reader call path today) — once #2 lands and something starts calling the fixed
     `read_fixtures_joined()`, or if the live engine is ever extended to read fixtures reference data directly, the same
     entity-split desync would resurface unless UTL's `joined_reader.py` is fixed first.

8. **[P3 todo, slot-4, 2026-07-15] Workspace-wide grep for other direct `entity=fixtures` readers found FIVE more
   affected production sites** — the widest is a SEVERE finding inside instruments-service itself:

   - **🔴 MOST SEVERE — `instruments-service/instruments_service/reference_data/sports_dependency.py`'s
     `check_api_football_dependency()`** is the hard pre-flight `DependencyError` gate called from
     `reference_data/adapters/sports/factory.py:90` for EVERY api-football-dependent venue adapter: `footystats`,
     `understat`, `transfermarkt`, `soccer_football_info`, `open_meteo` (weather), `betfair`
     (`_API_FOOTBALL_DEPENDENT_VENUES`). It probes ONLY `_CANONICAL_FIXTURES_PREFIX_TEMPLATE`
     (`.../pipeline_mode=batch_api_football/entity=fixtures/`), `_LEGACY_FIXTURES_PREFIX_TEMPLATE`
     (`.../entity=fixtures/`), and two bare-blob fallbacks — none of the four probes know about
     `entity=fixtures_schedule`. Net effect: for ANY date on/after the writer cutover (2026-07-14+), this gate raises
     `DependencyError` and **blocks all 6 dependent venue adapters from running at all** — a materially wider blast
     radius than the features-service backfill blocker this issue was originally filed for, and it's inside the SAME
     repo as the writer that caused the cutover.
   - `deployment-api/deployment_api/services/upcoming_fixtures.py::_read_one_day_frame` — reads the bare
     `entity=fixtures/fixtures.parquet` singleton directly (no split/per-league awareness at all); `object_exists`
     returns False for post-cutover days → silently returns `None` → the UI's "Upcoming Fixtures" panel silently shows
     fewer/no fixtures for those days, no error surfaced.
   - `deployment-api/deployment_api/services/data_status_drilldown/_csv_export.py::build_fixtures_csv_export` and
     `deployment-api/deployment_api/services/data_status_drilldown/_fixtures_pools.py` — both hardcode
     `entity=fixtures/fixtures.parquet` for the Data Status drilldown UI's fixtures CSV export / breakdown pool;
     post-cutover days hit the `FileNotFoundError` branch → empty CSV / empty pool, read as "adapter never ran" when it
     actually did (under the split entities).
   - `deployment-service/deployment_service/cli/utils/data_status_sports.py::_load_fixture_counts_for_date` — CLI
     data-status display; tries `entity=fixtures/` then a much older `sports_reference/fixtures/day=` legacy path,
     neither split-aware → silently reports 0 fixtures for post-cutover dates (reads as genuine expected-absence, not
     "adapter cutover", to whoever runs the CLI).
   - `market-tick-data-service/market_tick_data_service/engine/sports_catalog_reader.py::_FIXTURES_BLOB_TEMPLATE` —
     hardcoded `entity=fixtures/league={league_id}/fixtures.parquet`, used by the MTDS manifest sentinel fan-out (Phase
     3.D.5 v2 sports enumerator) to derive the expected `(bookmaker, league_id, fixture_id)` universe; post-cutover this
     silently yields an empty per-day fixture universe for the sentinel.

   **Root SSOT gap underneath the last two**:
   `unified-api-contracts/unified_api_contracts/canonical/domain/sports/ gcs_paths.py`'s `SPORTS_DATA_TYPE_TO_FOLDER`
   maps `"FIXTURES" → "fixtures"` only — there is no `"FIXTURES_SCHEDULE"`/`"FIXTURES_OUTCOMES"` data_type registered,
   so **every** caller of `candidate_parquet_paths("FIXTURES", ...)` is affected post-cutover, not just the two
   enumerated above. Confirmed production callers of `candidate_parquet_paths("FIXTURES"` (excluding tests/scripts):
   `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/fixture_id_resolver.py` (odds↔
   fixture join-key resolver) and `instruments-service/instruments_service/triggers/sports_fixtures_daily_repoll.py`
   (production repoll trigger) — both silently get an empty candidate-path list for post-cutover dates.

   **Confirmed NOT affected (already fixed)**: `deployment-service/deployment_service/sports_trigger_state.py` already
   carries a 3rd fallback pattern for `.../pipeline_mode=batch_api_football/entity=fixtures_schedule/` (added 2026-07-14
   per its own inline comment) — no action needed there.

   **Minor, non-blocking, noted for completeness**: instruments-service's OWN writer-side idempotency-check reads
   (`sports_fixtures.py:231,618`, `sports_reference_fixtures.py:114`, all via
   `_read_per_league_entity_df(..., "fixtures")`) also target the legacy entity, so post-cutover they will never find
   "already written" data and may trigger redundant re-fetches — wasteful but not a correctness bug (writes still land
   at the correct split location). No standalone todo filed for this; fold into the P0 fix below if convenient.

## Why it matters

- **Blocks `sports_p2_features_history_to_ml_ready-001`'s Todo 1** ("Compute features 2015→present") at its leading edge
  — every day on/after the cutover will hard-fail identically, forever, until fixed. (Does NOT block the bulk of the
  historical range — the other 2 in-flight gap-fill VMs cover 2018-07-09→2019-08-11 and 2020-03-07→2020-10-05, both well
  before the cutover.)
- **Likely breaks the LIVE/forward sports feature pipeline too** — `read_reference_entity` is the same code path
  `--mode live` would call for today's fixtures. If live compute has run since the cutover, it would either be silently
  missing fixtures features (if the live circuit-breaker doesn't halt cleanly) or halted outright. This session did not
  check live pipeline logs — flagging as the most urgent open item.
- **Cross-repo coordination gap**: the sports_fixtures_schema_split_completion_2026_06_20.md plan's own text warns "the
  entity-folder split + migration + writegate same-day flip MUST ship in a single coordinated unit" — the writer half
  shipped without the reader half, which is exactly the failure mode that warning exists to prevent.

## Recommended decision

1. **[P0, urgent, operator/infra]** Check whether live/forward sports feature compute has been failing or silently
   dropping fixtures since the writer cutover (first observed 2026-07-14) — grep recent live-mode `features-service`
   logs for the same `DependencyError: ... entity=fixtures` signature. If confirmed, this is an active production
   data-correctness incident, not just a backfill blocker.
2. **[P1, unified-trading-library]** Port this session's split-entity join fix into
   `unified_trading_library/fixtures/joined_reader.py._load_fixtures_for_day` (implement the TODO already left in that
   file), and update `OUTCOME_COLUMNS` / `_derive_outcomes_available_at` to the current Q6 raw column names. Zero
   current production callers confirmed — low blast radius.
3. **[P2, features-service]** Once (2) lands, consider switching `gcs_reader.py`'s fixtures read to call the UTL helper
   instead of the local `_read_split_fixtures_fallback` added this session, per the module's own "single place to flip"
   design intent — avoids two independent implementations of the same join drifting apart again.
4. **[P3]** Audit for any OTHER consumer reading `entity=fixtures` directly (outside features-service and UTL) that
   might also be silently affected. **DONE (this session, finding #8)** — see the new P0/P1 todos below.
5. **[P0, urgent, instruments-service]** Fix `sports_dependency.py::check_api_football_dependency()` to also probe
   `entity=fixtures_schedule` — this is currently blocking footystats/understat/transfermarkt/soccer_football_info/
   open_meteo/betfair adapter fetches for every date on/after the cutover, inside the SAME repo as the writer.
6. **[P1, unified-api-contracts]** Register `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` (or teach `"FIXTURES"` to probe
   both) in `SPORTS_DATA_TYPE_TO_FOLDER` / `candidate_parquet_paths()` — the SSOT gap silently breaks every
   `candidate_parquet_paths("FIXTURES", ...)` caller post-cutover (confirmed: MTDS `fixture_id_resolver.py`,
   instruments-service `sports_fixtures_daily_repoll.py`).
7. **[P1, deployment-api + deployment-service + market-tick-data-service]** Fix the 4 remaining hardcoded
   `entity=fixtures` readers found in finding #8 (deployment-api's `upcoming_fixtures.py` + 2 data-status-drilldown
   readers, deployment-service's `data_status_sports.py`, MTDS's `sports_catalog_reader.py`) to also probe the split
   entities.

## Todos

- [x] ✅ [CODE] P0. Check live/forward sports feature-compute logs (features-service `--mode live`) since 2026-07-14 for
      the `DependencyError: ... entity=fixtures` signature — confirm/rule out a live production incident. (repo:
      features-service) — unified-trading-pm (this doc, "What I found" #7): RULED OUT. No `mdps-features-live-sports-*`
      VM has ever been launched (0 hits in 30-day GCE-insert audit log); the sports live engine
      (`process_sports_record`) never calls `read_reference_entity` at all, so the signature cannot fire on that path
      even once live mode is launched. No live production incident, past or present.
- [x] ✅ [CODE] P1. Implement the two-entity `fixtures_schedule`/`fixtures_outcomes` join in
      `unified_trading_library/fixtures/joined_reader.py._load_fixtures_for_day` (the TODO already left in that file) +
      update `OUTCOME_COLUMNS`/`_derive_outcomes_available_at` to the current Q6 raw column names
      (`home_score_regulation` etc., not the stale `home_score_fulltime` etc.). Add regression tests. (repo:
      unified-trading-library) — unified-trading-library@46fc3395: `_load_fixtures_for_day` now falls back to
      `_read_split_fixtures_for_day` (lists + left-joins the per-league `fixtures_schedule`/`fixtures_outcomes` shards
      on `af_fixture_id` via `_read_split_entity_shards`) when the legacy singleton `entity=fixtures` parquet is
      missing; `OUTCOME_COLUMNS` updated to the current Q6 raw names (`home_score_regulation` etc.), retired
      `home_score_fulltime`/`_extratime`/`_penalty`/`af_winner_id`/bare `home_score`/`away_score` names dropped. 7
      regression tests added in `tests/unit/test_joined_reader_split_entities.py` covering: both split entities present
      (joined, unplayed fixtures get NaN outcome columns + NaT `outcomes_available_at`), only `fixtures_schedule`
      present (schedule-only), neither split entity present (still returns the standard empty frame), the GCS list/probe
      logic itself (canonical-prefix hit, canonical+legacy-both-empty), and the Q6 naming assertions on
      `OUTCOME_COLUMNS`. Full `quality-gates.sh` green (148s).
- [x] ✅ [CODE] P2. Once the UTL helper is fixed, switch `features-service/features_service/sports/data/gcs_reader.py`'s
      `_read_split_fixtures_fallback` to delegate to `read_fixtures_joined()` instead of duplicating the join locally.
      (repo: features-service) — unified-trading-library@428ef1b5 + features-service@c084023d: extended
      `read_fixtures_joined(day, league_id=None)` with an all-leagues mode (needed since
      `read_reference_entity(date, "fixtures")` has no per-league scoping), then rewrote `_read_split_fixtures_fallback`
      to call it directly instead of duplicating the per-league shard read + left-join locally. 2 new UTL regression
      tests (`TestReadFixturesJoinedAllLeagues` in `test_joined_reader_split_entities.py`); the 3 existing
      features-service fallback tests updated to mock `read_fixtures_joined` instead of the retired local
      per-league-read plumbing. Note: this todo collided with P1 above — unified-trading-library@46fc3395 (slot-12)
      landed the P1 fix concurrently with an equivalent implementation; reconciled by taking their (more robust,
      legacy-singleton-first) version as base and layering the `league_id=None` extension on top, discarding my
      duplicate P1 rewrite. Full `quality-gates.sh` green both repos.
- [x] ✅ [SCRIPT] P3. Grep the workspace for any other direct `entity=fixtures` GCS reader outside features-service/UTL
      that could be silently affected by the same writer cutover. (repo: cross-repo) — unified-trading-pm (this doc,
      "What I found" #8): found 5 more affected readers, the most severe being instruments-service's own
      `sports_dependency.py` pre-flight gate blocking 6 T1 adapters post-cutover. Filed as new P0/P1 todos below.
- [x] ✅ [CODE] P0. Fix `instruments-service/instruments_service/reference_data/sports_dependency.py`'s
      `check_api_football_dependency()` to also probe `entity=fixtures_schedule` (canonical + legacy `pipeline_mode=`
      prefix variants) — currently the pre-flight gate blocks footystats/understat/transfermarkt/
      soccer_football_info/open_meteo/betfair adapter fetches for every date on/after the writer cutover. (repo:
      instruments-service) — instruments-service@1415b735: added canonical
      (`pipeline_mode=batch_api_football/entity=fixtures_schedule/`) + legacy (`entity=fixtures_schedule/`) prefix
      probes, mirroring the existing fixtures probe pattern; 2 new regression tests in
      `tests/unit/test_sports_dependency_bucket.py`. `fixtures_schedule` alone (not `fixtures_outcomes`) is used as the
      equivalent "api-football ran" marker since it covers every fixture (played or not). QG green, shipped via
      quickmerge.
- [x] ✅ [CODE] P1. Register `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` in
      `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py`'s `SPORTS_DATA_TYPE_TO_FOLDER`
      (or teach `candidate_parquet_paths("FIXTURES", ...)` to probe both split entities) — the SSOT gap silently breaks
      every caller post-cutover, confirmed affecting
      `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/fixture_id_resolver.py` and
      `instruments-service/instruments_service/triggers/sports_fixtures_daily_repoll.py`. (repo: unified-api-contracts)
      — unified-api-contracts@c11e2899: did BOTH — registered `FIXTURES_SCHEDULE`/`FIXTURES_OUTCOMES` in
      `SPORTS_DATA_TYPE_TO_FOLDER`/`SPORTS_DATA_TYPE_LAYOUT` (reusing the existing `fixture_lifecycle.py` constants) AND
      taught `candidate_parquet_paths("FIXTURES", ...)` to auto-append `FIXTURES_SCHEDULE` candidates (not
      `FIXTURES_OUTCOMES` — that's a completed-fixtures-only subset and would under-report thin days as missing), so
      existing "FIXTURES" callers like MTDS `fixture_id_resolver.py` stay correct across the cutover with no call-site
      change. Also corrected `fixture_lifecycle.py`'s stale "gated, not shipped" docstring to reflect the 2026-07-14+
      cutover. New regression tests in `tests/unit/sports/test_gcs_paths_player_values.py` +
      `tests/unit/test_partition_paths.py` (dispatcher test updated for the new 4-candidate FIXTURES list). QG green,
      shipped via quickmerge. Note: re-checked `sports_fixtures_daily_repoll.py` — it does NOT actually call
      `candidate_parquet_paths` in code (only docstring mentions); the confirmed real caller is
      `fixture_id_resolver.py`.
- [x] ✅ [CODE] P1. Fix `deployment-api`'s 3 hardcoded `entity=fixtures` readers
      (`deployment_api/services/upcoming_fixtures.py::_read_one_day_frame`,
      `deployment_api/services/data_status_drilldown/_csv_export.py::build_fixtures_csv_export`,
      `deployment_api/services/data_status_drilldown/_fixtures_pools.py`) to also probe the split entities — currently
      silently degrade (empty/None) for the Upcoming Fixtures panel + Data Status drilldown CSV export/pool on any date
      on/after the cutover. (repo: deployment-api) — deployment-api@4642bcf: added a shared
      `deployment_api/services/_sports_fixtures_split.py::split_entity_league_blob_paths()` helper (probes the canonical
      `pipeline_mode=batch_api_football/entity={E}/league=` prefix, then the legacy bare-prefix shape, mirroring the
      pattern already shipped in instruments-service's `sports_dependency.py` + unified-trading-library's
      `joined_reader.py`) and wired it into all 3 readers: `upcoming_fixtures.py` falls back to reading + concatenating
      the per-league `fixtures_schedule` shards (raw af_-prefixed columns normalized to the friendly names
      `_row_to_fixture` expects) when the legacy singleton is absent; `_csv_export.py`'s `build_fixtures_csv_export`
      falls back to reading + left-joining `fixtures_schedule`/`fixtures_outcomes` shards on `af_fixture_id`;
      `_fixtures_pools.py`'s `_load_fixture_meta` falls back to the split `fixtures_schedule` shards via the existing
      `_FIXTURE_META_ALIASES` schema-adaptive resolution. `split_entity_league_blob_paths` is wired through the
      `data_status_drilldown` package's `_dd` facade (per that package's existing test-patch-surface convention) for the
      two drilldown readers; `upcoming_fixtures.py` imports it directly (standalone module). 7 new regression tests
      (`tests/unit/test_upcoming_fixtures.py::TestSplitEntityFallback`,
      `tests/unit/test_fixtures_split_entity_fallback.py`) covering: split-shard fallback success + column
      normalization, genuine-gap (neither legacy nor split present) still returns honest-absence (empty/None/
      "no_schedule"), and the schedule+outcomes left-join. Full `quality-gates.sh` green (137s), shipped via quickmerge.
- [x] ✅ [CODE] P1. Fix
      `deployment-service/deployment_service/cli/utils/data_status_sports.py::     _load_fixture_counts_for_date` to
      also probe `entity=fixtures_schedule` — currently silently reports 0 fixtures (read as genuine expected-absence)
      for post-cutover dates. (repo: deployment-service) — deployment-service@2c9d743: added `_FIXTURES_SCHEDULE_PREFIX`
      probe (canonical `pipeline_mode=batch_api_football/entity=fixtures_schedule/` shape) as a fallback tier in
      `_load_fixture_counts_for_date` (the calendar denominator) AND in `_check_league_status`'s per-league existence
      check (same legacy-only drift, same file) — without both, the calendar would show fixtures exist but the
      completeness check would still report them missing. 6 regression tests added in
      `tests/unit/test_data_status_sports.py` covering: legacy singleton still counted, post-cutover split-entity now
      counted (previously silently empty), oldest legacy fallback preserved, no-data case, per-league split-entity
      detection, and genuine gaps still reported missing. Full `quality-gates.sh` green (94s).
- [x] ✅ [CODE] P1. Fix `market-tick-data-service/market_tick_data_service/engine/sports_catalog_reader.py`'s
      `_FIXTURES_BLOB_TEMPLATE` (MTDS manifest sentinel fan-out / Phase 3.D.5 v2 sports enumerator) to also probe
      `entity=fixtures_schedule/league={league_id}/` — currently silently yields an empty per-day fixture universe for
      post-cutover dates. (repo: market-tick-data-service) — market-tick-data-service@7c3e5160: added
      `_FIXTURES_SCHEDULE_BLOB_TEMPLATE` (canonical `pipeline_mode=batch_api_football/entity=fixtures_schedule/` prefix
      — the split entity has no legacy/no-pipeline_mode variant, unlike `entity=fixtures`) and `list_instruments()` now
      falls back to it whenever the legacy `entity=fixtures` blob is absent. 3 regression tests in
      `tests/unit/engine/test_sports_catalog_reader_split_entity_fallback.py` covering: legacy-absent falls back to
      schedule and yields the fixture, legacy-present short-circuits without probing schedule (no behavior change
      pre-cutover), and neither entity present is a silent skip (not an error). Full `quality-gates.sh` green (6106
      tests), shipped via quickmerge.

## References

- `plans/archive/2026_07/sports_fixtures_schema_split_completion_2026_06_20.md` — the migration plan; "Already shipped"
  section names the UTL helper as already covering consumers (it does not, per finding #4 above).
- `plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md` — the task this was discovered under
  (Todo 1).
- `instruments-service/instruments_service/engine/orchestrator/sports_fixtures.py` — the writer (no dual-write).
- `unified-trading-library/unified_trading_library/fixtures/joined_reader.py` — the stale, unwired reader-side flip
  point.
- `features-service/features_service/sports/data/gcs_reader.py` — this session's fix (`_read_split_fixtures_fallback`).
- `instruments-service/instruments_service/reference_data/sports_dependency.py` — the pre-flight gate blocking 6
  downstream venue adapters post-cutover (finding #8, new P0 todo).
- `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py` — the `candidate_parquet_paths()`
  SSOT gap (finding #8, new P1 todo).
- `deployment-service/deployment_service/sports_trigger_state.py` — confirmed already fixed (3rd fallback pattern for
  `entity=fixtures_schedule`, 2026-07-14), no action needed.
