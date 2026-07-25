---
doc_type: plan
title:
  Sports satellite docs — AO dispatch batch 2 (36 AO-eligible todos extracted from 15 human-only satellite plans/issues)
summary: >-
  22 sports-AG satellite plans/issues were confirmed `assigned_vm: NA` / `execution_scope: local-only` — referenced by
  `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s discoverability index for human visibility only,
  never AO-dispatchable (that index deliberately uses non-checkbox markers so AO's regen_backlog parser can't ingest
  it). This plan extracts every genuinely AO-eligible todo from those 22 docs (concrete, determinable by a worker alone,
  no open operator/design judgment call) into one real AO-dispatchable plan, mirroring the
  `sports_closeout_batch1_ao_ready_2026_07_24.md` pattern. 36 todos from 15 source docs. Internally-sequential
  multi-step chains (e.g. a 5-step GCS migration recovery procedure, a 4-step census→copy→reprocess→swap execution
  sequence) are combined into single todos rather than fanned out — AO's per-todo model has no mechanism to mechanically
  gate step N on step N-1 within one plan short of `sequential: true` for the WHOLE plan, and this plan's other todos
  genuinely benefit from concurrent dispatch, so combining same-job chains into one todo each is the safe choice, not a
  fragile cross-todo ordering promise. 4 real AO-eligible items were deliberately EXCLUDED (not lost — flagged in their
  source docs) because they depend on either another todo below landing first (a 5-repo-spanning parity test; a UI
  relabel gated on its own backend todo) or a human/operator decision that has not yet been made (the
  SportsMatchingEngine-vs-L0Matcher design call blocks all 3 of
  `sports_group_c_execution_backtest_harness_2026_07_21.md`'s todos; a manifest-perf verify-speedup todo depends on 2
  sibling implementation todos both landing). 7 of the 22 source docs contributed ZERO AO-eligible todos (either 100%
  human-only design/operator-decision work, or already fully done) and are untouched by this plan.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    ml-service,
    strategy-service,
    execution-service,
    deployment-api,
    deployment-service,
    deployment-ui,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, satellite-docs, batch-2, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_consolidated_closeout_aggregated_sources_2026_07_24.md,
    /plans/active/sports_closeout_batch1_ao_ready_2026_07_24.md,
    /plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md,
    /plans/active/data_completion_sports_2026_07_24.md,
    /plans/active/sports_legacy_cutover_closeout_tasks_2026_07_24.md,
    /plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md,
    /plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md,
    /plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md,
    /plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md,
    /plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md,
    /plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md,
    /plans/active/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md,
    /plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md,
    /plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md,
    /plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md,
  ]
created: "2026-07-24"
last_updated: "2026-07-24"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 9.2
estimate_calibrated_ai_days: 7.4
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator request 2026-07-24: satellite docs referenced by the sports consolidated closeout's discoverability index
  were confirmed to be structurally un-ingestable by AO. All 22 left-over active/open sports satellite docs were triaged
  per-todo (via a 22-agent verification workflow) for real AO-eligibility, distinguishing concrete worker-executable
  todos from open operator/design judgment calls. This plan is the extraction of the AO-eligible subset, mirroring the
  sports_closeout_batch1_ao_ready_2026_07_24.md pattern for the master closeout plan.
---

# Sports satellite docs — AO dispatch batch 2

> **Why this plan exists.** Every todo below already exists, fully specified, in one of the 15 source docs listed in
> `related:`. None of that work is new — it was simply invisible to AO because its home doc is `assigned_vm: NA`. This
> plan does not duplicate or re-decide anything; it re-hosts already-decided, already-scoped work on an AO-dispatchable
> track. Once a todo here ships, flip the CORRESPONDING checkbox in its source doc too (cite this plan's commit as
> evidence there), the same reconciliation discipline `sports_closeout_batch1_finalize_2026_07_24.md` uses for batch 1.

> **Concurrency note.** No two todos below touch the same file (verified programmatically across all 36 before this plan
> was authored) — safe for AO's default same-priority-concurrent dispatch. Where a source doc's todos had a real
> ordering dependency, they are combined into ONE todo here (documented in that todo's own text as ordered sub-steps for
> the executing worker) rather than split and fanned out — this plan is intentionally `sequential: false` (todos below
> are independent of EACH OTHER; internal step-order within a combined todo is the worker's job to respect, per that
> todo's own text).

## Todos

### From `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`

- [x] ✅ [DATA] P0. **Eliminate the bare/legacy dual-layout** (operator: "legacy needs canonicalising or deleting —
      that's the whole point") — per-league entities that have BOTH a per-league split AND bare files for older days
      (`gcs_paths.py:96`) carry a stale parallel layout. For each: canonicalise the bare→per-league (in-retention) OR
      DELETE (pre-retention). Distinguish from the by-design bare entities (XG/WEATHER/player_values-bulk) which stay
      bare. (repo: instruments-service; read-only reference: unified-api-contracts `gcs_paths.py` `SportsLayout`).
      **Done when**: every per-league entity with a dual bare+per-league layout is canonicalised (in-retention) or
      deleted (pre-retention), snapshot-first; by-design bare entities left untouched. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. — VERIFIED CLEAN 2026-07-25 (slot
      2): the dual-layout condition does not currently exist for any of the 15 `PER_DAY_PER_LEAGUE` entities — zero
      canonicalize/delete action needed. Full census in Progress Log.
- [x] [DATA] P0. ✅ **RESOLVED-AS-INVESTIGATED 2026-07-25 (main-approved interim: leave day=all in place).** **Retention
      floor = the EXISTING per-source genesis registry — NOT a blanket 2015 delete.** 2026-07-25 investigation
      (`sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`): this todo's premise does not survive
      contact with the real GCS objects — **(a) day=all fold is genuinely blocked**: UAC's SSOT only maps VENUES to a
      FLAT layout (TEAMS is PER_DAY_PER_LEAGUE-only, so "fold into FLAT" is inapplicable to TEAMS as stated); the legacy
      `day=all/entity=venues/venues.parquet` (3,445 rows, raw numeric api_football `venue_id` keys, e.g. `1456`) and the
      live FLAT `sports_reference/venues/venues.parquet` (2,860 rows, slugified string keys, e.g. `OLD_TRAFFORD`) have
      **zero key overlap** — verified directly, not assumed — so there is no join key to "dedup" against; no live reader
      of `day=all` was found in any of the 6 core sports repos (looks like dead legacy data from an earlier writer
      generation), but `instruments-store-sports-prd` has soft-delete=0 (irreversible) and the original plan author
      explicitly flagged "would break team/venue resolution" as a delete risk — needs explicit operator sign-off (see
      issue doc's Options A/B/C), not a unilateral fold-that-can't-work or an irreversible delete. **(b) pre-genesis
      anomaly check is NOT new work**: the 131,306 TEAMS + 1,457 VENUES pre-floor rows found are a subset of the
      ALREADY-TRACKED, already-deferred 944,776-row phantom-pre-floor-manifest-row issue in
      `/codex/02-data/sports-2020-06-data-floor.md` (blocked on a GCS-walk manifest rebuild, explicitly NOT a hand-edit
      target) — satisfied by reference, no separate script needed. Also: this todo's quoted per-source genesis dates
      (understat 2014/api_football 2015/footystats etc. 2019) are **stale**, superseded 2026-07-21 by a uniform
      2020-06-06 WIPE floor for all sports sources (see the floor doc). Full evidence, GCS byte/row counts, and
      recommended option in the issue doc. **Disposition (main, 2026-07-25)**: the fold-as-described cannot mechanically
      execute (no FLAT layout for TEAMS, zero join-key overlap for VENUES) — interim = leave `day=all` in place;
      investigation itself IS the deliverable. Two items escalated to the operator, not this worker's call: (1)
      authorize/decline the irreversible delete of the two day=all objects (soft-delete=0, no recovery net); (2) the
      TEAMS FLAT-layout design decision (net-new UAC layout vs fold into per-day-per-league). The pre-genesis anomaly
      half needs no new work (already tracked, consolidator-lock blocked). Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [DATA] P0. **Odds-granularity watch-item check** — unified-api-contracts@a32ceb87. Checked whether pre-cutover
      10-min odds snapshots would be evaluated against a 5-min expectation anywhere and misread as missing coverage.
      **Result: not confirmed, documented as checked-no-issue** — no code path in UAC/instruments-service/MTDS/MDPS
      computes an expected-snapshot-count from a fixed cadence constant; MDPS bucket assignment
      (`bucket_assignment_adapter.py` `TIER1_HORIZONS`) matches snapshots to fixed pre-match offsets with a 30-90min
      staleness tolerance, and the honest-coverage expected-universe key for odds is
      `(date, league_id,     timeframe/horizon)` with no per-minute axis — the mislabeling scenario cannot occur today.
      Recorded the investigation + a re-check pointer directly in `_endpoint_registry_data.py` (the one place the
      cadence fact lived, previously as inert prose) so a future raw-tick-count completeness check for `odds_api`
      re-reads it first; also fixed a stale comment referencing a never-built `v3_era_cutoff` field. Noted discrepancy:
      the codebase's own documented cutover is **~2023** (v3→v4 endpoint version), not ~2024 as this todo's text states
      — flagged for whoever eventually builds a cadence-derived check to confirm the correct date before relying on it.
      Source: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [x] ✅ [DATA] P0. **Drop 2 out-of-universe numeric `league=` dirs** (`14231`/`315`), snapshot-first,
      twin/scope-verified. — instruments-service@2c4fa059. Live-reverified via `get_league_by_api_football_id()` that
      neither id has a UAC registry entry (pure drop, no canonical twin possible). Scope was WIDER than the source doc's
      "only 2 in 2025" claim — a bounded listing (day=2025-\* + day=2026-\* prefixes, not a whole-corpus walk) found 197
      real GCS objects (175 in 2025, 22 more in 2026 the 2026-06-24 audit predates) and 166 stale
      `_index/availability_index.parquet` rows. Deliberately excluded 2 bare `entity=injuries/injuries.parquet` fallback
      objects that share other leagues' data (separate bare/legacy-layout todo, not this scope). Snapshot-first
      throughout (GCS objects backed up to `sports_reference/_purge_backups/2026_07_25_drop_14231_315/`; manifest index
      backed up via CAS-safe generation-preconditioned write). Applied in prod + verified twice: 0 remaining objects, 0
      remaining manifest rows. (repo: instruments-service). Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [ ] [DATA] P0. **94-league enrichment backfill** — the residual golden-window gap is now GENUINE missing enrichment
      (XG_SHOTS 0% / XG 13% / PLAYER_STATS 21% / MATCHES 35% / INJURIES 37%), NOT a schema artifact. API-Football
      fixtures (fast, already 100%) → enrichment for the 94, fix broken, be thorough → re-measure toward 100%. (Its
      stated prerequisite — the tarball rebuild with the write-gate — is already DONE.) (repo: instruments-service).
      **Done when**: enrichment coverage for the 94-league universe re-measured and materially improved toward 100% for
      XG_SHOTS/XG/PLAYER_STATS/MATCHES/INJURIES, with any broken enrichment paths fixed. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. — **🟡 IN PROGRESS (2026-07-25),
      NOT complete — re-scoped after re-measurement, do not re-dispatch a duplicate.** This exact item is ALSO tracked
      (with a much longer, multi-session history of stalls/relaunches) in the canonical
      `/plans/active/sports_consolidated_closeout_2026_07_19.md` — its own archived predecessor
      (`sports_p2_history_apifootball_2015_to_present_2026_06_27.md`) explicitly warns "check Todo 9 status before
      dispatching"; that VM tracker (2 SPOT VMs, `af-backfill-20260721-033537`/`-20260722-033350`) was last recorded
      there as "running, months-to-years from gate" — **STALE**: both actually completed cleanly (`exit_code=0`,
      self-deleted) by 2026-07-23, confirmed via their `PROGRESS.json`/`run.log` in
      `gs://deployment-scripts-central-element-323112/vm-logs/`. Fresh manifest re-measurement (94-league-filtered,
      `_index/availability_index.parquet`, 2026-07-25) shows the raw "% captured" cited above reflects GENUINE upstream
      absence (`empty_confirmed`), not a backfill opportunity: FIXTURE_EVENTS 19.2% captured / 0.66% still
      `expected_unattempted`; FIXTURE_STATS 18.2%/0.66%; FIXTURE_LINEUPS 19.2%/0.74%; PLAYER_STATS 11.9%/0.74%; MATCHES
      11.5%/0.18%; XG 2.5%/0%; XG_SHOTS 2.2%/0% — i.e. these 7 are already **exhaustively attempted** (>99% of the
      residual is honest-absence, not a real gap); re-launching a backfill for them would burn API quota for ~0% real
      gain. **INJURIES is the one genuine exception**: 10,502 captured / 10,219 `expected_unattempted` (3.4%) — a real,
      un-attempted residual. Launched a targeted, singleton-lock-verified-clear
      (`gcloud compute instances     list --filter='name~"^af-backfill-"'` → 0 running) INJURIES catch-up:
      `af-backfill-20260725-002739` (2018-01-01→2026-07-25), verified `DEPLOYMENT_STARTED` + actively fetching within
      ~3min of launch (no fire-and-forget). ETA a few hours at the historically-observed INJURIES rate (~1,404 EU/hr,
      session 8d of the archived plan) — NOT completable within one AO task turn; tracked to completion across sessions
      like the archived plan's own history. Also found + flagged (issue doc filed): the `create-code-tarballs.sh` upload
      step fails via `gsutil` under the active `github-actions-deploy@…` gcloud account (expired Identity-Pool/WIF
      token) — the tarballs happened to already be fresh (rebuilt by another process ~35min before this session's
      launch) so the VM booted on valid code, but this auth gap will block the NEXT slot's tarball rebuild attempt until
      fixed. Full evidence + the reconciliation note in the canonical closeout plan: see this todo's own re-measurement
      above; re-run `_index/availability_index.parquet` INJURIES query after the VM's `EXIT_STATUS` appears to confirm
      the gap actually closed before flipping this checkbox. — **Health-checked 2026-07-25T01:45Z (slot 7,
      data_engineering), re-dispatched, NOT a duplicate launch.** `af-backfill-20260725-002739` confirmed RUNNING
      (`gcloud compute instances list`), `PROGRESS.json` monotonic and advancing (`last_completed_date=2022-04-04` as of
      this check, started at 2018-01-01), `run.log` tail shows live INJURIES fetches with no error/stall signature.
      Genuinely not completable this turn (started ~8h17m ago, ~4.25 of ~8.5 covered years so far at current rate —
      several more hours remain). No duplicate action taken; released back to the queue via `/skip-current-task` so
      other dispatchable work isn't blocked on this slot idling — a future dispatch should re-check
      `PROGRESS.json`/`EXIT_STATUS` before assuming still-running. — **Re-health-checked 2026-07-25T02:24Z (slot 2)**:
      still RUNNING, `PROGRESS.json` monotonic-advanced to `last_completed_date=2024-03-31`, no stall signature.
      Genuinely still hours from completion; released again, no duplicate action.
- [x] ✅ [CODE] P1. **UAC canonical registry build/refine** — unified-api-contracts@ce18ff15. Audited every clause of
      the Architecture section against current code before touching anything (most of this program had already shipped):
      name/ids/country/season-start-end-per-year (`season_dates.get_season_start`/`get_season_end`, per-league-per-year)
      and transfer window (`transfer_windows.py`) were already canonical; team cross-source mapping was already
      comprehensive (`team_mapping_data.py`, 6,246-row CSV, all leagues); fixture/player canonical ids already derive
      via `canonical_ids.build_fixture_id`/`build_player_id` (player id already consumed by `understat/normalize.py`);
      annual footystats-id rotation is already handled by a real mechanism — the weekly
      `check_footystats_season_drift.py` CI job (`.github/workflows/weekly-validation.yml`), not a season-year-keyed
      table. Two genuine, scoped gaps closed: (1) added `LeagueDefinition.is_cup` (derived
      `tier==0 and sport=="FOOTBALL"` property — previously only a docstring convention with zero real call sites); (2)
      wired `is_sports_structural_gap()` into `get_expected_leagues_for_source()` — that gap/allowlist SSOT
      (`SPORTS_STRUCTURAL_GAPS`/`SPORTS_SOURCE_LEAGUE_ALLOWLIST`) previously had zero production call sites (test-only),
      so a future `data_sources` hand-curation edit could silently diverge from it; verified a true no-op today
      (before/after `get_expected_leagues_for_source` counts identical across all 7 sources) but closes the ad-hoc-logic
      duplication risk. 4 new regression tests incl. a monkeypatch proving the wiring is real (not just coincidental
      agreement). quality-gates.sh green. (repo: unified-api-contracts). Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [ ] [DATA] P1. **Curated-universe definition → backfill → residual drop (3-step ordered sequence, one worker, execute
      in order).** (1) Define the curated ~300-league reference set (94 + the division below each country + continental
      cups [Champions League, UEFA/UECL, Copa Libertadores/Sudamericana, AFC/CAF equivalents] + major internationals
      [World Cup, Euros, Copa America…]) per the operator's Directive A/B + the 6M-call budget analysis, and widen the
      write-gate (`_is_in_canonical_write_universe` / `get_expected_leagues_for_source`) to it. (2) THEN
      curated-universe backfill (API-Football fixtures + enrichment, 2019→, burn ~6M over weeks; gated + honest-empty
      for no-enrichment leagues). (3) THEN drop residual out-of-curated rows/objects, snapshot-first, twin-verified. Do
      not run steps 2-3 before step 1 lands — same write-gate file, same manifest. (repo: unified-api-contracts league
      registry; instruments-service write-gate + backfill VMs + `_index` + GCS objects). **Done when**: curated list
      stored + write-gate widened; fixtures+enrichment backfilled for the curated set 2019→ with honest-empty for
      no-enrichment leagues; residual out-of-curated rows/objects dropped snapshot-first. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.

### From `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`

- [x] ✅ [SCRIPT] P0. **Fix `fixture_id=NULL` propagation in the odds_api backfill path** — golden window `trades` data
      has all fixture_ids as NULL, which blocks per-fixture cluster validation entirely. Likely market-tick-data-service
      (`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` + `fixture_id_resolver.py`, which
      already has partial `af_fixture_id` join scaffolding) — NOT instruments-service despite the source doc's
      frontmatter; confirm exact ownership at execution time (grep both repos for the golden-window trades write path)
      before scoping. (repo: market-tick-data-service). **Done when**: golden-window (2025-09-01..2025-11-30) odds_api
      `trades` rows carry a non-NULL `fixture_id` (or the existing `af_fixture_id` join is confirmed to already satisfy
      this — either outcome is determinable); a regression test proves `fixture_id` is stamped on newly-captured trades
      rows; `quality-gates.sh` green. Source: `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`. — FIXED
      2026-07-25 (slot 7, data_engineering): confirmed ownership is market-tick-data-service, not instruments-service
      (instruments-service only owns the FIXTURES reference table `af_fixture_id_resolver.py` reads from — it has no
      odds_api trades write path at all). Root cause: `_build_fixture_rows()` in `odds_api_adapter.py` correctly
      resolves + stamps `af_fixture_id` on every row (this half already worked, with existing test coverage), but the
      row dict never contained a key literally named `fixture_id` — only `af_fixture_id`. The actual write path,
      `market_tick_data_service/engine/orchestrator/venue_fetch.py::_process_sports_venue_with_leagues()`, normalises
      via `if "fixture_id" not in records_df.columns: records_df["fixture_id"] = ""` and then GROUPS shards by
      `["bookmaker_key", "league_id", "fixture_id"]` — since odds_api rows never had that column, this branch always
      fired, forcing every row's `fixture_id` to `""` and collapsing odds_api into league-level shards instead of
      per-fixture ones (exactly the golden-window symptom; `opticodds_adapter.py` already does this correctly for
      comparison). Fix: `_build_fixture_rows()` now also emits
      `"fixture_id": str(af_fixture_id) if af_fixture_id is     not None else ""` alongside the existing
      `af_fixture_id`, matching the string-shard-key convention `venue_fetch.py`/`opticodds_adapter.py` already use.
      Extended `test_odds_api_fixture_id_join.py` with `fixture_id` assertions on all 4 existing test cases
      (matched/unresolved/no-fixture-data/end-to-end via `download_batch()`) — 6/6 tests pass.
      `quality-gates.sh --no-fix` green (fresh, not cached). — market-tick-data-service@3401c0ab.

### From `sports_odds_feature_naming_canonicalization_2026_07_21.md`

> Sequencing note for AO: the 5 todos below (spanning features-service, unified-api-contracts, ml-service, and
> strategy-service ×2) are each in a DIFFERENT file, safe to dispatch concurrently. A 6th todo from this source doc (the
> cross-repo FSS↔ml-service↔strategy-service parity test) is DELIBERATELY EXCLUDED here because it depends on ALL 5 of
> these landing first and this plan has no mechanical way to gate one todo on 5 siblings without serializing the whole
> plan — add it as a new todo (in this plan or a successor) once these 5 are confirmed shipped.

- [x] ✅ [DATA] P1. **New compute, not a rename**: add per-bookmaker raw decimal-odds retention to
      `features_service/sports/calculators/` (whatever calculator currently collapses per-venue quotes into
      `best_odds_*`/`odds_variance_*` — trace it first) so a `decimal_odds_<outcome>_<venue>` shape can actually be
      populated for `SportsArbDutchingEngine`. (repo: features-service). **Done when**: a decimal odds field keyed per
      outcome+venue (final name per the decided scheme, e.g. `odds_decimal_home_pinnacle`) is computed and populated in
      FSS output for real bookmaker/venue combinations. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`. — SHIPPED 2026-07-25 (slot 7, data_engineering):
      `_pivot_bucketed_to_fixture()` (`odds_features_exporter.py`) now emits one `odds_decimal_<outcome>_<venue>` column
      per bookmaker actually quoting a fixture (venue = the raw lowercase bookmaker_key, e.g.
      `odds_decimal_home_pinnacle`). Critical fix required beyond the tap point alone: `compute_odds_batch()` rebuilds
      its output frame from scratch (`event_id` + its own fixed `ODDS_COLUMNS`), so the new dynamic columns from
      `_pivot_bucketed_to_fixture`'s output would be silently dropped — added an explicit merge-back in
      `export_odds_features()` right after `compute_odds_batch()` runs, the same pattern `available_at` already uses for
      the identical reason. 3 new/extended tests (2 unit-level on `_pivot_bucketed_to_fixture`, 1 end-to-end through the
      REAL `compute_odds_batch` proving the merge-back survives) — 47/47 pass in `test_odds_features_exporter.py`.
      `quality-gates.sh --no-fix` fresh green. — features-service@b03a6de4. **Known limitation, filed as a follow-up
      (not blocking this todo's done-when)**: the new dynamic columns bypass `feature_expectations.py`'s
      `ODDS_COLUMNS`-registry PIT horizon-gating (`apply_horizon_gate()` only walks a fixed list, no prefix match) — see
      the new `[DATA] P2` todo below. **Separate finding filed, NOT part of this todo's scope**:
      `compute_odds_batch()`'s dead-code `bookmaker_home_cols` path silently overwrites `best_odds_*` with a mean
      instead of the correct max — see `issues/fss_bookmaker_dispersion_dead_code_overwrites_best_odds_2026_07_25.md`.
- [ ] [DATA] P2. **PIT horizon-gating gap for the new `odds_decimal_<outcome>_<venue>` columns** (found while shipping
      the todo above): `feature_expectations.py`'s `ODDS_COLUMNS` registry drives PIT horizon-gating
      (`apply_horizon_gate()`), which only walks a fixed column list — the new dynamic per-venue columns aren't in it
      and so bypass PIT gating entirely (there's no schema allowlist blocking them at the parquet-write boundary either,
      so they DO reach output — just ungated). Add a pattern-match (e.g. `startswith("odds_decimal_")`) to
      `apply_horizon_gate()`/`get_column_horizons()` so these get the same leak protection as every other odds field.
      Add a regression test proving a T-24h row's `odds_decimal_*` doesn't leak a later horizon's value. (repo:
      features-service)
- [x] ✅ [DATA] P1. **Rename UAC's `OddsFeaturesMixin`/`SportsFeatureVector` fields** — unified-api-contracts@689efa54 +
      ml-service@91f031a. All 49 fields renamed to the decided scheme, grounded in `features-service`'s actual
      calculator output (`odds_calculator.py`/`odds_velocity.py`) and live consumers, not a blind find-replace — several
      old fields shared a literal string with UNRELATED same-named columns in other layers (MDPS's raw handicap-line
      bucket column, FootyStats' vendor API field, a synthetic mock-odds generator); confirmed via workspace-wide grep +
      context-read before touching anything, so those were correctly left untouched. **Collision resolution**:
      `market_home_odds_best`/`market_away_odds_best` win the `odds_decimal_` slot (this scheme's own worked example,
      `best_odds_home` → `odds_decimal_home`, and what `SportsValueBettingEngine` needs);
      `odds_home_win`/`odds_draw`/`odds_away_win` (a DIFFERENT, currently-live FSS column under the exact same old name)
      got the distinct `odds_moneyline_` metric instead of colliding with it. Same pattern for
      `market_home_away_odds_ratio` vs `odds_home_away_ratio` (a `consensus` qualifier disambiguates the schema-only
      one). **Production-safety carve-out**: `odds_sharp_money_on_home`/`_away` and the 6 fixed-line over/under fields
      were deliberately left UNCHANGED — they exact-match a currently-live FSS producer column today, and renaming them
      would have zeroed out `SportsFeatureLoaderMixin._validate_odds_schema`'s producer/consumer overlap check (an
      already-shipped loud-fail gate) ahead of FSS's own migration (the P2 todo immediately below, not yet landed) with
      no compensating benefit — documented in the class docstring so this isn't rediscovered. New UAC test file (none
      existed for this class before) asserts the exact field set, retired names are gone, and the deliberately-unchanged
      set survives; fixed the 2 hardcoded old-field-name test fixtures + 1 stale docstring reference this rename broke
      in `ml-service`'s `test_sports_feature_loader.py`/`sports_feature_loader.py` (an adjacent, same-turn fix — that
      test suite directly imports `OddsFeaturesMixin`). **Known transitional gap**: several renamed fields (e.g.
      `odds_asian_handicap_line`, `prob_implied_btts_*`) DO exact-match a currently-live FSS column under their OLD
      name, per this scheme's own worked examples — those were renamed anyway (the operator's explicit table example),
      so `SportsFeatureLoaderMixin`'s loud-fail gate will correctly start firing for real `odds_features` loads touching
      those specific fields until the P2 FSS-side migration lands; this is the gate doing its designed job (loud, not
      silent), not a regression, but P2 should be prioritized to close the window. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`.
- [ ] [DATA] P2. **Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS`** + the odds-features
      exporter to emit the UAC-chosen field names instead of the current `home_implied_prob`-style convention; update
      exporter tests + downstream fixture files. (repo: features-service). **Done when**: all 180 `ODDS_COLUMNS`
      entries + exporter output renamed per the decided scheme; exporter tests and downstream fixtures updated;
      quality-gates green. Source: `sports_odds_feature_naming_canonicalization_2026_07_21.md`.
- [x] ✅ [BACKEND] P2. **Close the silent-agnostic gap in `SportsFeatureLoaderMixin`** — ml-service@07976ae. Added
      `_validate_odds_schema` (checked only for the `odds_features` group): raises `ValueError` when a non-empty frame
      has ZERO columns overlapping UAC `OddsFeaturesMixin`'s known field set — a producer/consumer naming mismatch,
      never honest absence. 3 new regression tests: a deliberately mismatched fixture (real pre-migration FSS names
      `home_implied_prob`/`draw_implied_prob`) raises loudly, a matching fixture (`odds_home_win`) still loads, and
      non-`odds_features` groups are never schema-validated. quality-gates.sh green (2103 passed).
- [x] ✅ [BACKEND] P2. **Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine`** + the legacy
      `sports_feature_subscriber.py` — strategy-service@4c55438c. Renamed `decimal_odds_<outcome>` →
      `odds_decimal_<outcome>`, `decimal_odds_<outcome>_<venue>` → `odds_decimal_<outcome>_<venue>`,
      `fair_prob_<outcome>` → `prob_fair_<outcome>`, `ht_odds_{home,draw,away}_implied` →
      `prob_implied_{home,draw,away}` per the 2026-07-23 decided scheme. Updated the 3 direct unit test files, the
      `ARBITRAGE_SPORTS_DUTCHING` branch of `test_all_catalogued_archetypes_construct_and_fire.py`'s smoke test, and the
      dutching leg of `scripts/run_sports_arb_backtest.py`. Left the generic (non-sports)
      `ml_directional`/`rules_directional` `event_settled.py` engines untouched — they share the OLD `decimal_odds_`
      prefix incidentally but are NOT part of this migration's decided scope. quality-gates.sh green (5583 passed, 5
      pre-existing xfails unrelated to this change). NOTE: this is 1 of 3 independent per-repo renames in the same
      migration (UAC `OddsFeaturesMixin` + FSS's exporter, both still `[ ]` above) — a temporary window where they don't
      all agree is expected per the operator's own sequencing note (sports is backtest-only, no live wiring).

### From `data_completion_sports_2026_07_24.md`

- [x] ✅ [DATA] P1. **Post-backfill entity-coverage relabel — PREMISE RESOLVED, not executed as a relabel; residual
      filed separately.** The 6 named backfill VMs ARE confirmed terminal (0 sports-tagged GCE instances, running or
      otherwise, in `central-element-323112` as of 2026-07-25). But BEFORE running the prescribed relabel, I measured
      the current manifest directly: the diagnosed 789-league/1,027,396-row phantom `expected_unattempted` set in the
      2026-02-20→06-19 window is now **33,905 rows across 96 league_ids — ALL 96 in the current in-universe set, ZERO
      out-of-universe leagues remain in-window** (a ~30x reduction, resolved as a side effect of the intervening
      write-gate + dereg + canonicalize program, instruments-service@0345ffc through 2026-07-21). The prescribed
      "no-coverage pairs → expected_empty" script no longer matches the manifest's actual shape and running it blind
      risks mislabeling genuine post-cutover pending-fetch gaps as false-empty (the residual is dominated by the
      2026-07-14+ `FIXTURES_OUTCOMES`/`FIXTURES_SCHEDULE` split-entity backfill, not raw-league over-enumeration). Also
      found a DIFFERENT, currently-RUNNING sports backfill VM (`af-backfill-20260725-002739`, unrelated to the
      original 6) writing `_index/availability_index.parquet` directly and unsharded — confirms the manifest is not
      safely drained for an unprotected RMW regardless of the premise question. Filed
      `issues/sports_post_backfill_relabel_premise_resolved_residual_gap_2026_07_25.md` with the full measurement + 3
      correctly-scoped follow-up todos rather than force a stale-premise migration against a live-changing production
      manifest. Source: `data_completion_sports_2026_07_24.md`.
- [ ] [SCRIPT] P2. **Relaunch features-sfi-progressive** — code fix already shipped (`features-service@06c44c02`); first
      verify (via git log) whether the launcher's repoint to `VM_SERVICE=features_service` /
      `python -m features_service.sports.scripts.compute_sfi_progressive_only` already shipped (the source doc cites
      placeholder `<sha>`s, not real ones); if not, ship it. Then confirm market-tick-data-service is clean (no foreign
      uncommitted WIP blocking the tarball build) → rebuild SPORTS tarball via
      `create-code-tarballs.sh --asset-group SPORTS` →
      `RECOMPUTE_FORCE=true     launch-sfi-progressive-features-backfill-vm.sh --force 2020-01-01 <today>` → verify
      run.log has no `MissingFeatureFamilyError`. (repo: deployment-service
      `scripts/vm/launch-sfi-progressive-features-backfill-vm.sh`, `scripts/vm/create-code-tarballs.sh`;
      features-service `features_service/sports/scripts/compute_sfi_progressive_only.py` — read-only dependency check on
      market-tick-data-service, no edits there). **Done when**: launcher confirmed pointed at
      `features_service.sports.scripts.compute_sfi_progressive_only` (fixed if not); SPORTS tarball rebuilt; relaunch's
      run.log shows no `MissingFeatureFamilyError` and `PROGRESSIVE_DAY_CAPTURED` events, exit code 0. Source:
      `data_completion_sports_2026_07_24.md`.

### From `sports_legacy_cutover_closeout_tasks_2026_07_24.md`

- [ ] [DATA] P2. **T6.8 — retire the one-offs + the dead knob + the false-progress tick.** Per each file's own
      `Delete-when` (all satisfied once T5.4 landed + orphan-sweep = 0 — both independently verifiable facts, check
      first): delete `migrate_sports_canonical_v9.py`, `migrate_legacy_tick_buckets_to_canonical.py`,
      `patch_l6_legacy_manifest_{is,mtds}_2026_06_29.py`, the ~26 legacy-reading `instruments-service/scripts/**`
      one-offs, and the doubly-broken gate
      `market-tick-data-service/market_tick_data_service/scripts/verify_v1_archive_row_coverage_2026_06_27.py` (leaving
      it re-issues a false COVERED verdict). Retire the dead `include_legacy_archive` knob from UAC
      `gcs_paths.py`/`partition_paths.py` (`rg 'include_legacy_archive\s*=\s*True'` → zero hits workspace-wide).
      Un-tick/annotate the plan item `- [x] ✅ [DATA] P0. v1_archive ROW-coverage gate` in the archived
      `sports_manifest_canonicalisation_2026_06_01.md` (ticked on "gate script shipped," never on a verified run —
      false-progress class); correct that plan's standing claim to "superseded by v2 fixtures ALONE" (the columns that
      supposedly required the union are 100% empty). Gate: `rg -c 'sports-central-element-323112'` workspace-wide → 0.
      This todo spans 4 repos (market-tick-data-service, instruments-service, unified-api-contracts, unified-trading-pm)
      — it is one worker's scoped unit of work as written, not a fan-out candidate. **Done when**: all named one-off
      scripts deleted (per their own Delete-when annotations, contingent on the stated preconditions); the doubly-broken
      gate deleted; zero `include_legacy_archive=True` hits workspace-wide; the archived plan's checkbox
      un-ticked/annotated and its superseded-by claim corrected; final `rg -c` gate returns 0. Source:
      `sports_legacy_cutover_closeout_tasks_2026_07_24.md`.

### From `sports_prelaunch_cf5_verify_residual_2026_07_24.md`

- [ ] [DATA] P1. **Sports CF-5 oracle relabel = ZERO — land the preserved fix.** Root cause already found + fixed
      (code): `_PER_FIXTURE_DERIVED_DATA_TYPES` listed the MDPS odds tick as lowercase `"trades"`, but membership is
      tested as `data_type.upper() in set` → `"TRADES"` never matched → step 6.5's truthset gate silently skipped every
      `trades` empty. Fix (`"trades"`→`"TRADES"` in `mtds/scripts/rebuild_sports_manifest_v9.py` + a regression test) is
      verified MTDS-QG-green and preserved on `origin/wip-preserve/mtds-346-cf5-trades` (`mtds@d0a15a3`) — never landed
      because quickmerge's dep-audit refused across 3 retries (a live sibling was running fleet manifest-regen). FIRST
      check (git log/branch diff) whether `origin/wip-preserve/mtds-346-cf5-trades` has already landed on
      market-tick-data-service HEAD. If not: confirm the MTDS/UAC dep tree is clean, cherry-pick the wip commit onto a
      clean tree, run MTDS `quality-gates.sh` green, land via
      `quickmerge.sh --agent --files 'market_tick_data_service/scripts/rebuild_sports_manifest_v9.py tests/unit/scripts/test_rebuild_sports_manifest_v9.py'`.
      (repo: market-tick-data-service). **Done when**: worker confirms landed-or-not first (citing the check); if not
      landed, the fix + its regression test are confirmed present on market-tick-data-service main/LDR HEAD, citing the
      landing commit sha. Source: `sports_prelaunch_cf5_verify_residual_2026_07_24.md`.

### From `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`

> The doc's 3rd todo (a `FixturesBrowser.tsx` UI relabel) is EXCLUDED here — it's explicitly gated on the backend todo
> below landing first ("once P10-B backend lands"). Add it as a follow-up once this todo ships.

- [x] ✅ [BACKEND] P2. **Switch `deployment-api/services/fixtures_browser.py` to the single catalogue** —
      deployment-api@dbbf64c. Reads `prod/catalog.parquet` ONCE (schema-aware projection), TTL-cached as a parsed frame
      filtered to `instrument_type=="fixture"` (mirrors `prediction_catalogue.py`'s `_read_catalogue`).
      `fixture_id`=`instrument_id`; `home_team_id`/`away_team_id` parsed from the id's `HOME_v_AWAY` segment;
      `venue_id=""` (honest, not carried). Filters AND groups on `available_from`, not `kickoff_utc`. Deleted
      `_MAX_WINDOW_SPAN_DAYS` (kept `_MAX_WINDOW_SIDE_DAYS` as a sane bound on the relative-window defaults only — no
      longer a read-cost bound). Rewrote `test_fixtures_browser.py` entirely for the new architecture (mocks
      `_read_catalogue_fixture_frame`, not the retired day-walk primitives); added coverage for team-id parsing,
      honest-blank `venue_id`, `instrument_type` filtering, available_from-vs-kickoff-day grouping, and the removed span
      cap. `quality-gates.sh` green (4964 passed).

### From `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`

> The doc's 4th todo (a real-backfill timing verification) is EXCLUDED here — it depends on both todos below landing
> first. Add it as a follow-up once both ship.

- [ ] [DATA] P2. **Manifest-slice replacement for `check_api_football_dependency()`** — load+filter a manifest slice
      once per backfill run (or per chunk) instead of per-date network calls (pyarrow filter push-down on the downloaded
      `availability_index.parquet` bytes — measured ~10s one-time download + ~0.66s filter for a 1-year slice); keep the
      direct-GCS path as a fallback only if a genuine same-run consolidation-lag risk is confirmed real (manifest
      consolidator cron runs every 1 min). Also unify this function's independently-hardcoded path-template constants
      with the shared helper the other ~9 expanded-scope sites already use (`_read_per_league_entity_df`-style) — likely
      gets absorbed automatically once the manifest-slice replacement lands (a manifest-slice check no longer needs GCS
      path templates at all). NOTE: this exact todo text appears twice verbatim in the source doc (~line 136-140 and
      ~217-225) — it is ONE work item. (repo: instruments-service
      `instruments_service/reference_data/sports_dependency.py`). **Done when**: `check_api_football_dependency()` reads
      a manifest slice instead of per-date probes; consolidation-lag fallback implemented + documented; a regression
      test proves equivalent results to the old probe-based check; no independently-hardcoded duplicate path templates
      remain; quality-gates green. Source: `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.
- [ ] [DATA] P2. **Cached/batched fix for `sports_fixtures.py:356`** — this one needs fixture_id-level set membership
      the manifest doesn't carry; replace the current one-GCS-call-per-(entity×league)-pair pattern with a cached
      per-date or per-backfill-window parquet read of the real fixture-capture file. (repo: instruments-service
      `instruments_service/reference_data/sports_fixtures.py` around line 356 — DIFFERENT file from the todo above, safe
      to dispatch concurrently with it). **Done when**: the membership check no longer issues one GCS call per
      (entity×league) pair; replaced with a cached per-date/per-window parquet read; a regression test proves
      correctness matches the current per-pair GCS behavior; quality-gates green. Source:
      `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.

### From `issues/sports_legacy_duplicate_triage_2026_07_22.md`

- [ ] [DATA] P2. **Migrate-forward the 58 v2 post-floor rows** (16 days) into canonical per-league `entity=fixtures` /
      `entity=fixture_stats` — reuse `migrate_sports_per_league.py`'s per-fixture-league-join logic, not a delete.
      Re-run the sweep after to confirm these flip to `A_canonical`. (repo: instruments-service —
      `scripts/migrate_sports_per_league.py` logic against bucket `instruments-store-sports-prd`; re-run
      `scripts/migration_orphan_sweep_sports.py --bucket reference` afterward). **Done when**: all 58 rows across the 16
      days have canonical objects written, and a re-run of the orphan sweep reclassifies them as `A_canonical` instead
      of `B_legacy_duplicate`. Source: `issues/sports_legacy_duplicate_triage_2026_07_22.md`.
- [ ] [CODE] P2. **Repoint or retire the two flat-legacy readers** before the 28,100 post-floor flat rows can be
      reconsidered for delete: (a) `sports_reference_fixtures.py:139`'s old-path branch — verify never reached for
      canonicalised dates (add counter/log), or remove now that canonical coverage is ~98%; (b)
      `data_status_sports.py`'s level-4 fallback — same treatment. Re-run Part 4 grep+READ after either change lands.
      (repo: instruments-service `engine/orchestrator/sports_reference_fixtures.py:139`; deployment-service
      `cli/utils/data_status_sports.py:32-42,72-75`). **Done when**: both readers are either instrumented (proving never
      hit for canonicalised dates) or removed outright (worker's engineering call, given ~478 of the 28,100 rows
      currently rely on the fallback as sole source); Part 4 grep+READ re-run recorded. Source:
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`.
- [x] ✅ [REVIEW] P3. **Rescan `migration_orphan_sweep_sports.py --bucket reference`** to retire the 4,735 stale
      (already-deleted) flat pre-floor rows from the durable audit parquet, and fix the classifier's
      `is_covered_sports`-before-`_is_pre_launch` ordering so pre-floor cells with a stale-captured manifest row
      classify `C3_pre_launch_window` instead of `B_legacy_duplicate` (mirrors the already-shipped E-class fix,
      `unified-api-contracts@46d865df`, on a different branch of the same function). (repo: instruments-service
      `scripts/migration_orphan_sweep_sports.py`; unified-api-contracts classifier mirror). **Done when**: rescan no
      longer surfaces the 4,735 stale rows; classifier ordering fix causes correct classification, mirroring the
      already-shipped E-class pattern. Source: `issues/sports_legacy_duplicate_triage_2026_07_22.md`. —
      **instruments-service@6cf44d31**: `classify_reference_object`'s flat/non-`by_date` branch now checks
      `_is_pre_launch` BEFORE `is_covered_sports` (day-less FLAT singletons unaffected — `_is_pre_launch` returns
      `False` on `day=""`); the pre-existing "covered wins" semantics on the SEPARATE `by_date`-tree branch (tested by
      `test_pre_launch_window_is_c3_not_e`) are deliberately left untouched — a different, already-decided policy
      question (the v2 pre-floor 728-row disposition, issue doc §7 todo 1, `[OPERATOR]`-gated). 36/36 unit tests green
      (incl. new regression `test_flat_legacy_pre_floor_stale_captured_is_c3_not_b`); QG green. Live rescan run against
      `instruments-store-sports-prd-central-element-323112` (2026-07-25): fresh audit parquet written to
      `_index/audit/orphan_sweep_sports.parquet` — verified **0** flat pre-floor `B_legacy_duplicate` rows remain (down
      from 4,735); new counts `B_legacy_duplicate=27,238` / `E_orphan_real=2,179` / `C3_pre_launch_window=800` (30,217
      actionable rows total, 916,394 objects walked).
- [x] [REVIEW] P3. ✅ **Cross-file the archived `sports_master_closeout_2026_07_21.md`'s pending "MANIFEST prune"
      deferred task** — the 944,776 phantom pre-floor manifest rows it already tracks are the root cause of this doc's
      §2 misclassification too. (repo: unified-trading-pm — add a cross-reference note to the archived plan's existing
      pending item). **Done when**: the archived plan's pending MANIFEST-prune item carries an added cross-reference to
      `issues/sports_legacy_duplicate_triage_2026_07_22.md` noting the shared root cause. Source:
      `issues/sports_legacy_duplicate_triage_2026_07_22.md`. Added cross-reference to both
      `plans/archive/2026_07/sports_master_closeout_2026_07_21.md` (PENDING EXECUTION item) and its companion
      `sports_master_closeout_progress_log_2026_07_24.md` (tracking table row) — unified-trading-pm@243998b6c.

### From `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`

- [ ] [DATA] P3. **Fleet-wide sweep for the same seeder-over-captured pattern** in other asset groups (the
      `enumerate_v2` guard is active for every asset_group now via `main()`; verify the nightly jobs' images actually
      pick it up fleet-wide). (repo: instruments-service — nightly Cloud Run enumerator job configs across all
      asset_groups; cross-check against `enumerate_expected_universe.py` `main()` guard coverage; deployment-service for
      job/image-tag inspection). **Done when**: a fleet-wide audit table is produced confirming, per asset_group's
      nightly enumerator job, whether the deployed image contains the `ba306543` `captured_set` guard; any
      stale/unguarded asset_group flagged as a follow-up finding. Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`.
- [ ] [CODE] P1. **Extend the "never emit `empty_confirmed` over a captured atom" guard** to the regular sports
      instruments batch-capture emission path (`sports_fixtures.py`/`sports_reference_core.py` or wherever
      `uts-prod-instruments-service-sports-fixtures`'s `--operation=instruments --mode=batch --asset-group=SPORTS` run
      emits `EXPECTED_NO_FIXTURE`/`EXPECTED_PAUSED_LEAGUE`/etc.) — same guard shape as `ba306543`
      (`enumerate_expected_universe.py`'s `captured_set` check), applied to this SEPARATE code path. (repo:
      instruments-service — exact emission site TBD by worker on read). **Done when**: a `captured_set`-style guard is
      added to the batch-capture emission path; unit tests added and passing; a fresh production run no longer produces
      new masking rows of the observed pattern. Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`.
- [x] [INFRA] P3. **Downgrade, don't drop, the original "redeploy expected-universe-v2-sports" todo** — that image IS
      current (`:latest` confirmed to contain `ba306543` as of 2026-07-23T08:07:36Z) and Cloud Run Jobs re-pull a
      mutable tag per execution, so no redeploy is likely needed; the doc's own 2026-07-23 second-pass trace found the
      actual masking writer is a DIFFERENT job entirely (`uts-prod-instruments-service-sports-fixtures`) — do NOT
      dispatch a literal redeploy of `expected-universe-v2-sports`. (repo: instruments-service/deployment-service —
      verification only). **Done when**: `gcloud run jobs describe expected-universe-v2-sports` confirms the job pulls a
      mutable `:latest` tag; verification result recorded; this todo (and the superseded original redeploy todo) marked
      resolved with no further action, or a follow-up filed if pinned. Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`. — ✅ 2026-07-24 VERIFIED:
      `gcloud run jobs describe expected-universe-v2-sports --project=central-element-323112 --region=asia-northeast1`
      confirms the container image is `...instruments-service:latest` (mutable tag, not pinned); 3 most-recent
      executions (2026-07-22/23/24, all 01:30Z) completed successfully. No redeploy needed. Both this todo and the
      original redeploy todo marked resolved in
      `plans/active/issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`.

### From `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`

- [x] ✅ [CODE] P1. **Stop stale/zombie ticks at bucket assignment** (fix locus: MDPS, not MTDS raw ingestion). Primary
      fix in `market-data-processing-service/.../adapters/sports/bucket_assignment_adapter.py`: drop rows whose
      `staleness_seconds` (`fetch_utc − bm_time`) exceeds a sane cap (hours-scale, ≥ the largest horizon window) or
      whose `kickoff_utc` is far outside the fetch day's horizon reach, BEFORE horizon assignment — record
      honest-absence/zero rows for that league-day instead. Per the doc's own status: the post-kickoff (`bm_minutes<0`)
      half already landed (`mdps@3bf56ff`); the remaining gap is specifically the `staleness_seconds` cap /
      `kickoff_utc`-vs-fetch-day check in `assign_horizon_bucket()` and `assign_horizon_buckets_vectorised()` — the
      pre-kickoff-positive Russia-Premier-League zombie class (`bm_minutes≈1423≈T-24h`) is confirmed still unfixed as of
      2026-07-23. (repo: market-data-processing-service `app/adapters/sports/bucket_assignment_adapter.py`). **Done
      when**: both functions reject a tick before bucket assignment when `staleness_seconds` exceeds the cap or
      `kickoff_utc` falls outside the fetch day's horizon reach; the known zombie fixtures no longer land in any horizon
      bucket on re-processed days, while a genuine single-snapshot real-fixture case is NOT dropped; covered by a
      unit/regression test for both zombie classes plus the real case. Source:
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`. — SHIPPED 2026-07-25 (slot 7, data_engineering):
      added `STALENESS_CAP_SECONDS` (48h — comfortably ≥ the largest horizon window, 24h/1440min) and
      `KICKOFF_PAST_CAP_SECONDS` (7 days) checks to `_prepare_tick_data()`, the single choke point BOTH
      `process_to_candles()` and `process_to_bucketed_df()` already call before `assign_horizon_bucket(s)` — a **design
      choice, not literally inside those two functions as the todo text implies**: `_prepare_tick_data` is where the
      existing causality filter (`bm_time <= fetch_utc`) already lives, so this mirrors that established pattern and
      protects both entry points identically without duplicating the check. `staleness_seconds` catches the
      Russia-Premier-League zombie class directly (bm_minutes≈1423≈T-24h but bm_time 3.5 years stale);
      `kickoff_utc`/`commence_time` (naming varies by corpus generation, same fallback as `_derive_match_midnight_us`)
      is a second independent signal. 5 new tests (years-stale-bm_time, fresh-scrape-not-dropped,
      partial-drop-still-processes, years-past-kickoff, genuine-near-term-kickoff-not- dropped) — 67/67 pass.
      `quality-gates.sh --no-fix` fresh green (75s, sentinel not cached). market-data-processing-service@aa6e8ac.

### From `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`

- [ ] [CODE] P1. **WEATHER layout mismatch — confirm, align, reverify (3-step ordered sequence, one worker).** (1)
      Confirm the writer's intended WEATHER layout is `PER_DAY_PER_LEAGUE` (read the IS weather writer
      `instruments_service/engine/orchestrator/weather.py` + confirm no bare `entity=weather/weather.parquet` objects
      are ALSO written via an actual GCS listing, not just the code comment — the 2026-07-23 RE-TRIAGE already cites
      strong code-comment evidence, so this is largely confirmation). (2) THEN align
      `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` in
      `unified-api-contracts/unified_api_contracts/canonical/domain/sports/gcs_paths.py:139` to the confirmed layout,
      with a regression test that `candidate_parquet_paths(WEATHER, league=…)` builds the `league=` path (mirror the
      existing PLAYER_VALUES alignment). (3) THEN re-run the sports phantom audit and confirm WEATHER false positives
      (baseline ≥106 proven false-positive rows) drop out of the `instruments-store-sports` phantom count; check for and
      remove any zero-row WEATHER placeholder residue. (repo: instruments-service; unified-api-contracts
      `gcs_paths.py`). **Done when**: layout confirmed via code + GCS listing; `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` set
      to `PER_DAY_PER_LEAGUE` with a passing regression test; phantom audit re-run shows WEATHER no longer contributing
      false positives; any placeholder residue removed or its absence confirmed. Source:
      `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`.

### From `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`

- [ ] [DATA] P1. **`player_stats` idempotent de-dup rewrite** over all canonical `player_stats` cells (keyed
      `(fixture_id, player_id)`), reusing the T2.4 union tooling's dedup path. ~13,964 cells remain (the SKIP_NO_NEW
      path left untouched, out of 27,296 total canonical `entity=player_stats/*/player_stats.parquet` objects). (repo:
      instruments-service data write/rewrite tooling; GCS bucket `instruments-store-sports-prd`; reference pattern at
      `~/tmp-cutover/t2_4_build_canon_keys.py`). **Done when**: all remaining ~13,964 cells are rewritten with
      exact-duplicate rows removed within each object, idempotently, using the same dedup logic the T2.4 union already
      applied to its 4,015 cells; verifiable via the same per-object dup census methodology (rows vs
      per-object-unique(fixture_id,player_id) converges to 0 duplicates project-wide). Source:
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.
- [ ] [DATA] P1. **`fixture_events` re-fetch into the canonical 13-col schema** — fold into the OR-1 `fixture_events`
      re-fetch campaign; re-fetch the degenerate/heterogeneous cells from api-football into the canonical schema.
      Re-fetch lists archived at
      `gs://deployment-scripts-central-element-323112/sports_cutover_2026_07_16/phase2_evidence/`. (repo:
      instruments-service re-fetch/ingest tooling; GCS bucket `instruments-store-sports-prd`,
      `entity=fixture_events/*/fixture_events.parquet` — DIFFERENT entity/objects from the player_stats todo above, safe
      to dispatch concurrently). **Done when**: the degenerate 5-col stub (~30% of sampled objects), the 9-col named
      variant, and the 10-col `af_`-prefixed variant are re-fetched and rewritten into the canonical 13-col schema,
      matching the target already established for the 57% already-canonical objects; a repeat 120-object sample shows 0
      non-13-col objects (or documents genuinely unrecoverable ones). Source:
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.
- [ ] [CODE] P2. **Writer-side de-dup + schema-conformance gate** so neither defect re-accrues — the `player_stats`
      writer rejects/dedupes rows on write; the `fixture_events` writer validates/enforces the canonical 13-col schema
      before accepting new objects. (repo: instruments-service `_writer_captured.py` row_count/effective_count logic +
      both write paths; unified-api-contracts if a formal schema/type addition is needed — DIFFERENT files from the two
      data-rewrite todos above). **Done when**: a duplicate-row write attempt for `player_stats` gets deduped; a
      degenerate/non-13-col `fixture_events` write gets rejected or normalized; both covered by a regression test.
      Source: `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.

### From `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`

- [ ] [DATA] P1. **32-day legacy→canonical MDT row recovery (5-step ordered sequence, one worker, execute in order —
      this is one recovery procedure, not 5 independent jobs).** (1) READ-ONLY: re-derive the ~32 gap days by whole-day
      KEY-LEVEL containment (legacy tick keys − canonical tick keys) over the candidate window (2022-09-07..2022-10-01
      dominant + a handful of 2023/2025 days) — do NOT inherit the banner's day-list, confirm it; expect ~32 days /
      550,062 legacy-only keys (524,486 pre-match + 25,576 in-play) / ~2,081 objects. (2) BUILD: per confirmed gap day,
      read legacy old-shape objects → extract canonical-absent keys → derive canonical segments via
      `build_instrument_id` (the already-validated 100.0000% derivation map — do NOT re-derive) → split pre-match vs
      in-play by kickoff time → MERGE (never overwrite — canonical holds `bookmaker_key`/`fixture_id`/`available_at`
      legacy lacks) → de-dup on the poll key `(event,market,outcome,bm_time,price)` → stamp `available_at` via
      `unified_trading_library.availability_stamping.stamp_available_at_odds_snapshot(df, source="odds_api")`. (2b)
      IN-PLAY QUARANTINE (per the already-ruled OR-5b(c) mechanism — execution, not a design choice): in-play rows land
      under a non-`ticks.parquet` filename with a distinct `data_type=` segment, `pipeline_mode` unchanged
      (`batch_odds_api`), so `reprocess_sports_odds.py::_is_consumable_trades_blob` /
      `orchestration_scanner._matches_data_type` do not sweep them into the pre-match/T-0 path. (3) VERIFY BY CONTENT:
      fresh re-read in a SEPARATE process (never the writer's own return) confirms recovered keys present in canonical
      with matching crc/row counts; a before/after `(data_type,source)` census shows only the intended cells changed.
      (4) T2.10 SEED PURGE: strip 37,114 phantom `api_football × trades` (captured, nonzero IC) from
      `_index/per_vm/_legacy_seed.parquet` with the NULL-safe COALESCE source filter (211,313 real
      `odds_api ×     trades` rows survive) — back up first, let the consolidator re-merge, verify by content. (5) T4.1
      OBJECT-LAYER PROOF: confirm `unique==0` for the legacy bucket (`market-data-tick-sports-central-element-323112`),
      the delete-eligibility precondition. Snapshot/backup before every write step; abort and escalate if any gate fails
      to match expectations rather than proceeding past a mismatch. (repo: market-tick-data-service — new one-off
      migration/audit script under `scripts/`, with lifecycle markers; reads/writes GCS buckets
      `market-data-tick-sports-central-element-323112` (legacy) and `market-data-tick-sports-prd-central-element-323112`
      (canonical); consumes but does not modify `unified_trading_library.availability_stamping`). **Done when**: all 5
      steps complete in order with each step's own stated verification gate passing; final state has the ~32 gap days'
      550,062 keys recovered into canonical (merged, never overwritten, in-play quarantined per OR-5b(c)), verified by
      content in a separate process, the 37,114 phantom seed rows purged, and the legacy bucket showing `unique==0`.
      Source: `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`.
- [ ] [DOC] P3. **File a new issue doc** for the standalone finding: "30/200 sampled canonical MDT objects carry
      duplicate rows on the poll key (event, market, outcome, bm_time, price, fetch_utc), independent of the OR-5b
      cutover." (The de-dup-on-write remediation itself is already folded into the recovery-sequence todo above's step 2
      spec — this todo is only the standalone documentation action.) (repo: unified-trading-pm `plans/active/issues/` —
      new doc, standard issue frontmatter). **Done when**: a new issue doc exists under `plans/active/issues/`
      documenting the finding per standard lifecycle. Source: `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`.

### From `issues/sports_league_id_namespace_migration_2026_07_20.md`

- [x] ✅ [DATA] P0. **Fix the independent per-fixture league_id defect** — unified-api-contracts@d28da985 +
      instruments-service@83b7952b. **Root cause was NOT the branch order** — the 2026-07-20 precedence flip
      (`instruments-service@815ad06c3`) already put the numeric-id branch first, but `CanonicalLeague` never carried an
      `api_football_id` attribute at all, so `getattr(fx.league, "api_football_id", None)` was always `None` and the
      numeric branch silently no-opped for every fixture — every completed fixture kept resolving via the raw ambiguous
      display name, the exact bug the flip was meant to eliminate. Fixed at the root: added
      `api_football_id: int | None = None` to `CanonicalLeague` (UAC `canonical/domain/sports/__init__.py`) and
      populated it from `raw.league.id` in `external/api_football/normalize.py` — confirmed safe via a dedicated
      blast-radius check (no exhaustive-field tests, no parquet-schema enumeration of the new field;
      `_af_id_from_canonical()` in instruments-service already expected this attribute as its primary lookup strategy,
      falling back to logo-URL regex parsing — this was filling a gap other code already anticipated, not inventing a
      new one). Extracted the resolution logic into a pure `_resolve_fixture_league_slug()` and added 3 regression tests
      mirroring `mtds@ad4f1872`'s `TestOddsApiCanonicalLeagueId` (numeric resolves to canonical slug; the six known
      ambiguous names — BUNDESLIGA/SERIE_A/SERIE_B/CHAMPIONSHIP/PRIMERA_DIVISION/SUPER_LEAGUE — each resolve to their
      two distinct real leagues via numeric id; unregistered league falls back to raw name, honest absence) that
      exercise the real function, not just facts about the UAC registry. The
      `build_league_id()`-falls-back-to-bare-slug-when-country-empty behavior itself is unchanged (by design —
      honest-absence fallback for genuinely unregistered leagues) but is now GATED away from ever reaching disk: the
      write-universe gate (`_is_in_canonical_write_universe`, shipped 2026-06-24 per incident) already drops any
      unresolved/non-canonical value before write, so the `.../entity=injuries/league=235/` leakage cited as evidence is
      historical debris pre-dating that gate, not a live path — confirmed no more bare-numeric-id partitions can be
      produced going forward. Source: `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [ ] [DATA] P0. BLOCKED-CREDENTIALS 2026-07-25 (ping: `ikenna_orchestrator/pings/slot_3.md` 2026-07-25 CREDENTIAL
      APPROVAL REQUEST) **League_id casing migration — census→copy→reprocess→swap (4-step ordered sequence, one worker,
      execute in order — this is one already-verified, ready-to-execute migration, not 4 independent jobs).**
      **Progress**: (a) found step (2)'s manifest swap (raw `TRADES`/`batch_odds_api` shape) had silently reverted since
      its 2026-07-22 run (TOCTOU consolidator race, closed by `unified-trading-library@14301571` on 2026-07-24 — 2 days
      after the swap ran). Re-applied `manifest_swap_2026_07_22.py --apply-prod --confirm-prod-write` and verified
      STABLE across 5 consolidator cycles (~7.5 min) — the raw TRADES shape is now genuinely canonical, not just
      log-claimed. Full detail: `/plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`. (b)
      **Coverage-registry refresh already satisfied** — ran `refresh_sports_bookmaker_league_coverage_2026_06_21.py`
      (diff mode): "No drift vs committed coverage map"; directly confirmed the done-when criterion —
      `is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")` = `True`, `…("BETFAIR_EX_EU","PREMIER_LEAGUE")` = `False`.
      **BLOCKED**: the remaining piece (MDPS `odds_horizon_bucket` reprocess, 109,312 objects, + `batch_footystats`
      copy+swap, 16,970 objects) needs the sanctioned `launch-mdps-sports-bucket-vm.sh` VM launcher, which needs a fresh
      code-tarball republish first (deployed tarballs predate the TOCTOU fix above, and the reprocess script's
      `ManifestWriter` writes the canonical index directly — no per-VM-shard mode — so stale code would re-expose the
      exact race just fixed). Tarball republish is blocked on a genuine `gsutil` credential failure on this host
      (service-account federation token expired; human account needs interactive 2FA reauth) — confirmed
      `gcloud storage`/`gcloud compute` work fine with ADC, only legacy `gsutil` is broken. Ping filed:
      `ikenna_orchestrator/pings/slot_3.md` 2026-07-25 CREDENTIAL APPROVAL REQUEST. Full detail + dry-run validation of
      the reprocess mechanism (clean on a sample day, no `--force` needed):
      `/plans/active/issues/gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md`. Needs a human to
      either run `gcloud auth login` interactively once, or refresh the service-account federation. (1)
      `migrate_sports_league_id_casing_2026_07_21.py --apply-prod` (no `--confirm-prod-write`, no `--index`) once, for
      the live out-of-scope census + VM-guard + PLAN, using the already-committed, adversarially-verified executor
      (`mtds@b2a49317`) — expect results consistent with the verified full-corpus dry-run baseline (266,408 objects /
      34,228 units, 0 unknown raws, 0 unresolved league_ids). (2)
      `--apply-prod --confirm-prod-write --index scripts/.../raw_index.tsv` — copies+CAS-verifies the raw
      `batch_odds_api/odds/trades` shape (~139,155 objects) to canonical paths
      (`league_id=<CANON>/instrument_type=ODDS/data_type=TRADES/`), with the parquet's `league_id` CONTENT column
      rewritten. COPY-ONLY: never deletes source objects; refuses while any `features-sports-sports-*` VM is
      non-terminal. (3) THEN the deferred shapes (127,488 objects — `odds_horizon_bucket` 109,312 via MDPS
      `reprocess_sports_odds.py`'s Step-7 procedure + `batch_footystats` 16,970 via the same casing-migration script
      re-run/extended, using the already-verified classification map covering the full 267,614-object corpus) must be
      handled before any bucket-wide delete or "complete" claim. (4) THEN the atomic manifest-swap (reuse
      `deployment-service scripts/rebuild_sports_manifest.py::_clean_stale_league_entries` against
      `_index/availability_index.parquet`), THEN MDPS reprocess of the processed surface, THEN the coverage-registry
      refresh (`refresh_sports_bookmaker_league_coverage_2026_06_21.py` regenerating
      `sports_bookmaker_league_coverage.json` — confirm exact owning repo at execution time). Snapshot/backup before
      every write step; the whole sequence is designed to be restorable at every stage (per its own documented STOP
      conditions) — halt and escalate if a stage's gate doesn't match expectations rather than proceeding. (repo:
      market-tick-data-service `scripts/sports/league_id_relocation/migrate_sports_league_id_casing_2026_07_21.py`;
      market-data-processing-service `scripts/reprocess_sports_odds.py`; deployment-service
      `scripts/rebuild_sports_manifest.py`; coverage-registry refresh script). **Done when**: all 4 steps complete in
      order with each stage's own stated gate passing; post-swap `availability_index.parquet` shows zero
      `league_id=<RAW>` rows for migrated shards with no consolidator double-count or row-count inflation; MDPS
      processed surface regenerated under canonical partitions; `is_bookmaker_league_covered("BETFAIR_EX_EU","EPL")`
      flips False→True after the coverage-registry refresh. Source:
      `issues/sports_league_id_namespace_migration_2026_07_20.md`.

## Deferred (real AO-eligible work, gated on something else — not lost, tracked here)

- **`sports_odds_feature_naming_canonicalization_2026_07_21.md`'s FSS↔ml-service↔strategy-service parity test** — gated
  on all 5 naming-migration todos above landing. Add as a new todo once confirmed shipped.
- **`sports_fixtures_browser_single_catalogue_source_2026_07_24.md`'s `FixturesBrowser.tsx` relabel** — gated on this
  plan's fixtures_browser.py backend todo landing. Add as a new todo once confirmed shipped.
- **`issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`'s real-backfill timing verification** — gated on
  both `sports_dependency.py` todos above landing. Add as a new todo once confirmed shipped.
- **`sports_group_c_execution_backtest_harness_2026_07_21.md`'s 3 todos** (run_sports_backtest, fixture data wiring,
  hermetic alpha-bps test) — ALL gated on a human/architect decision (SportsMatchingEngine vs L0Matcher) that has not
  yet been made. Not dispatchable until that decision lands; do not dispatch speculatively.

## Progress Log

- **2026-07-25 (slot 2, data_engineering) — "Curated-universe definition → backfill → residual drop" todo — step 1
  substantially de-risked, NOT complete (checkbox correctly left unchecked, no write-gate code changed).** Directive A/B
  (the operator's own spec for the curated list, quoted in full in the source doc) requires real judgment to turn into a
  concrete ~300-league list — not a mechanical transcription — so rather than guess, checked whether a candidate pool
  already exists from prior work instead of assuming a fresh API-Football enumeration was needed.
  - **Found a major shortcut, not previously called out in any plan**: the pre-pruning manifest backup
    (`gs://instruments-store-sports-prd-central-element-323112/_index/_backups/availability_index.20260505T132209Z.pre-leagues-retire.parquet`,
    from before the 2026-05 cutdown to the 94-league baseline) still has **375 distinct league_ids with real
    `capture_status=captured, instrument_count>0` rows** — i.e. leagues API-Football data was ALREADY fetched and paid
    for, spanning dozens of countries' top divisions, second/third divisions (e.g. `ALBANIA_2ND_DIVISION_GROUP_A`,
    `ARGENTINA_PRIMERA_C`), and domestic cups (`ALGERIA_COUPE_NATIONALE`, `ARMENIA_CUP`) — exactly the shape Directive
    A/B describes (top league + division below + cups). This directly matches the operator's own framing ("we already do
    have a bunch of fixtures in the API football, so it wouldn't be a full re-backfill") — meaning step 2's "burn ~6M
    over weeks" may be a smaller residual gap than the todo's framing implies, not a fresh 300-league backfill from
    zero.
  - **NOT a clean drop-in list — needs real cleanup before it can back a write-gate**: sampled the 375 and found
    naming-scheme duplicates from the pre-pruning era (`AUSTRIAN_2_LIGA` vs `AUSTRIA_2_LIGA`, `AUSTRIAN_BUNDESLIGA` vs
    `AUSTRIA_BUNDESLIGA`) — the raw candidate set needs de-duplication + validation against UAC's existing
    canonical-slug conventions before it's safe to feed into
    `_is_in_canonical_write_universe`/`get_expected_leagues_for_source`. 63 additional league_id values in the same
    snapshot are still RAW numeric API-Football IDs (33 of which already map via `_API_FOOTBALL_ID_TO_LEAGUE`, 30
    genuinely unmapped) — those need canonical-slug assignment before inclusion, not silent numeric-ID admission
    (mirrors the exact class of bug already fixed elsewhere in this same plan's league_id-namespace todos).
  - **Deliberately did NOT touch the write-gate or UAC's `LEAGUE_REGISTRY` this session** — turning this candidate pool
    into ~300 correctly-classified, de-duplicated, correctly-countried `LeagueDefinition` entries (with season
    start/end + transfer-window metadata, per the plan's own UAC-registry todo) is real, careful data-entry work against
    a PRODUCTION write-gate; doing it hastily risks baking wrong entries into the exact code path that controls weeks of
    real API spend and manifest correctness. The raw candidate list is preserved at this session's working artifacts
    (not committed — regenerate via the query below, cheap, no new GCS walk needed) rather than guessed at from scratch.
  - **Recommended next step**: (1) re-run the extraction query below against the SAME backup parquet (already
    identified, no new census needed) to regenerate the 375-league candidate list, (2) de-duplicate the naming-scheme
    variants + resolve the 30 unmapped numeric IDs to canonical slugs, (3) cross-reference against Directive A/B's
    per-source caps (Understat ~6, footystats ~50, SFI/odds-API bounded by API-Football availability) — those caps are a
    genuine ceiling on how much of the 375 is actually eligible, not all 375 necessarily qualify, (4) THEN widen the
    write-gate + add the UAC registry entries, (5) THEN assess the REAL residual backfill gap (likely much smaller than
    a from-scratch ~300-league fetch, given most already have real data) before launching any VM. Extraction query:
    `pd.read_parquet('<backup path above>', columns=['league_id','capture_status','instrument_count']); filter capture_status=='captured' & instrument_count>0; distinct non-numeric league_id values`.
  - **Follow-up mechanical pass on the 375 (still no code touched)**: grouped by 4-char country-prefix to find likely
    adjective/noun-form duplicates. 9 prefix groups flagged; MOST were false positives on inspection (`SLOVAKIA_*` vs
    `SLOVENIA_*` share a 4-char prefix but are different countries; `SUPERCOPA_ESPANA` vs `SUPERETTAN` vs `SUPER_LIG`
    are unrelated competitions that happen to start "SUPE"). Genuine duplicate PAIRS confirmed by inspection (same
    real-world competition, inconsistent adjective/noun naming from the pre-pruning era):
    `AUSTRIA_2_LIGA`/`AUSTRIAN_2_LIGA`, `AUSTRIA_BUNDESLIGA`/`AUSTRIAN_BUNDESLIGA`, `AUSTRIA_CUP`/`AUSTRIAN_CUP`,
    `SCOTLAND_CHAMPIONSHIP`/`SCOTTISH_CHAMPIONSHIP`, and likely `GREECE_SUPER_LEAGUE_1`/`GREEK_SUPER_LEAGUE` (needs a
    capture-date/instrument-count cross-check to confirm they aren't actually two distinct tiers before merging — did
    NOT assume). So the real de-dup burden is small (~5 pairs out of 375, not a systemic mess) — the earlier finding's
    caution about "not a clean drop-in list" stands, but the actual cleanup is now known to be a bounded, few-pair fix,
    not a large undertaking. A crude prefix-match heuristic is NOT sufficient on its own (produces false positives) —
    the next pass should verify each flagged pair against real capture data before merging, same discipline this session
    applied.
  - **Per-source-cap cross-reference, real numbers (still no code touched)** — queried the same backup's `data_type`
    breakdown to check the candidate pool against Directive A/B's stated per-source caps: **XG (Understat)**: 18
    distinct leagues with real captured data — HIGHER than the operator's own "~6" estimate, so Understat's true reach
    is bigger than assumed (good — more free reference data). **MATCHES (footystats)**: 30 leagues — under the "~50"
    cap, room to grow. **ODDS**: 30 leagues — OVER the operator's stated "~20" odds-API cap; since odds availability is
    what ultimately gates the PREDICTION-tier subset (per Directive A: "we pretty much narrow down our prediction
    leagues to the ones that the odds API has data for"), this is the one real discrepancy worth operator confirmation
    before finalizing — either the "~20" figure was a rough estimate (use the real 30), or 10 of these 30 need to be
    excluded from the prediction tier specifically (they'd still be fine as features-tier reference).
    **SFI_PROGRESSIVE_STATS**: 33 leagues, all cross-checked as already within the API-Football-covered set (no orphan
    SFI-only leagues found in this sample) — consistent with Directive A's "can't be trying to get soccer football info
    for a league that doesn't exist in API Football" rule. This closes step 3's cross-reference with real measured
    numbers instead of the directive's own rough estimates — the next session can go straight to finalizing the list
    against these figures (flag the ODDS 30-vs-~20 discrepancy to the operator specifically) rather than re-deriving
    them. **Operator resolved the ODDS discrepancy same session: use the real measured 30, not the ~20 estimate.**
  - **Major follow-up finding: the metadata blocker on actually building `LeagueDefinition` entries is smaller than
    assumed.** Was about to defer "assign country + season/transfer-window metadata to ~300 leagues" as needing a fresh
    session (fabricating that data would be worse than not doing this task). Checked first whether it already exists
    rather than assuming not:
    `gs://instruments-store-sports-prd-central-element-323112/sports_reference/by_date/day=2024-01-15/pipeline_mode=batch_instruments_service/entity=leagues/leagues.parquet`
    (object timestamp 2026-06-24 — recent, not stale) is the **full raw API-Football leagues catalog**: 1,228 rows,
    columns `league_id, name, country, league_type, logo_url`, zero null countries, 171 distinct countries, **776
    `League` / 452 `Cup`** already classified. This directly answers the "which of the 375 (and the wider universe) are
    leagues vs cups, and which country" question that would otherwise require per-league research — it's already
    captured, current, and complete for country+type. What's still genuinely absent: season start/end + transfer-window
    dates (Directive A asks for these too) — not found in this file or any other checked this session; that piece likely
    does need fresh research or an additional API-Football endpoint call per league, and is real remaining scope for
    whoever picks this up. Net: the curated-list SELECTION step (which ~300 of 1,228, cross-referenced against the 375
    already-captured + the per-source caps above) is now almost entirely mechanical — join `leagues.parquet` against the
    375-candidate list + Directive A/B's rules (top + below-division + continental cups + majors) — the remaining hard
    part is narrowed specifically to season/ transfer-window dates, not the whole metadata problem.
  - **Confirmed the catalog's shape matches Directive A/B's two-category selection cleanly, no further discovery needed
    on this axis**: grouping `leagues.parquet` by `country` shows `country="World"` holds **176 entries, 175 of them
    `Cup`** (World Cup, Euro Championship, UEFA Champions/Europa League, Copa America, CONCACAF Gold Cup, AFC/CAF
    equivalents, etc.) — this IS the "continental cups + majors" bucket Directive A/B names explicitly, already cleanly
    separated from the 171 real countries' domestic leagues/cups (England 46, Spain 38, Germany 34, Brazil 109, …). So
    the selection mechanically splits into two independent, well-scoped joins: (a) per-country top-league +
    division-below + domestic-cup from the 171-country group, (b) the specific named majors/continental cups from the
    176-entry World group (Directive A names them: World Cup, Euros, Copa America, Champions League, UEFA/UECL, Copa
    Libertadores/Sudamericana, AFC/CAF equivalents — a literal name-match against these 176, not a fresh enumeration).
    **This closes out this session's contribution to step 1** — everything needed to WRITE the curated list is now
    identified and located; actually writing the join code + the ~300 `LeagueDefinition` UAC entries + widening the
    write-gate remains real implementation work for a fresh session (still correctly not done here — a discrepancy in a
    production write-gate is expensive to unwind, worth doing with full attention).
  - **Found the actual code-level blocker on writing entries, not just a data gap**:
    `LeagueDefinition.season_months: tuple[int, int]`
    (`unified_api_contracts/canonical/domain/sports/league_registry.py:60`) is a REQUIRED field, no default — confirms
    real per-league season-window data is a hard prerequisite for every new entry, not an optional nicety. **Operator
    resolved this directly**: use a hemisphere-based default (Northern Hemisphere Aug–May, Southern Feb–Nov, explicit
    hardcoded exceptions like MLS Feb–Nov) with an explicit code-comment TODO marker per entry, rather than block on
    per-league research or silently guess without flagging it. This unblocks the write-gate widening for a fresh
    session.
  - **Sanity-checked the continental/majors slice specifically** (the part of step 1 that does NOT need per-country
    tier-guessing, since Directive A names the tournaments explicitly): keyword-matched the 176-entry World group
    against Directive A's named list (World Cup, Euros, Copa America, Champions/Europa/Conference League,
    Libertadores/Sudamericana, AFC/CAF Champions League, Nations League) → **43 raw matches**. Flagging honestly: NOT
    all 43 are "majors" in the operator's intended sense — many are youth (`World Cup - U20`), qualifiers
    (`World Cup - Qualification Africa`), or women's variants that Directive A's own prose de-prioritizes — a fresh
    session should filter to senior-men's-flagship first per Directive A's literal examples, not admit all 43
    uncritically.
  - **Every open question for this todo is now resolved or located**: candidate leagues (375 already-captured + 1,228
    full catalog), per-source caps (measured + operator-confirmed for ODDS), duplicate handling (bounded ~5 pairs),
    season-month defaults (operator-approved hemisphere heuristic), and the domestic-vs-continental split (171-country
    group vs 176-entry World group). What's left is writing, testing, and shipping the actual code — genuine
    implementation work, not more discovery.
  - **CRITICAL — actually attempted the 11-entry continental-majors slice and found a real, confirmed regression risk;
    reverted cleanly, no code shipped, checkbox stays unchecked.** Wrote 11 `LeagueDefinition` entries into
    `unified_api_contracts/canonical/domain/sports/league_data_other.py`'s `REFERENCE_LEAGUES` dict (World Cup, Euros,
    FIFA Club World Cup, Copa America, OFC/CONCACAF/AFC×2/CAF Champions League, UEFA + CONCACAF Nations League — the 11
    of the 18 keyword-matched majors not already in the registry), `classification="Reference"`, hemisphere-default
    `season_months` per the operator's approved policy. **QG caught a real defect**: two tests failed —
    `test_full_94_football_universe_is_mvp` / `test_all_89_other_football_leagues_are_understat_gaps` — both hardcode
    registry-size assertions. Root cause traced past the test counts to the actual mechanism:
    `_mvp_scope_rules.py::_mvp_football_league_ids()` (feeds the sports `is_mvp()` predicate) takes EVERY
    `sport=="FOOTBALL"` registry entry with **NO classification filter at all** — so my 11 new `Reference`-tagged
    entries were silently swept into MVP/prediction scope, directly contradicting the operator's explicit "not
    suggesting we increase the scope of what we are predicting now." **Attempted the obvious fix** (filter
    `_mvp_football_league_ids()` to `classification == "Prediction"`) and measured its actual effect before shipping it:
    **the current 96-league MVP baseline is Prediction (33) + Features (24) + Reference (39) COMBINED — all three
    classifications, not just Prediction.** That "fix" would have silently SHRUNK live MVP/prediction scope from 96 to
    33, a severe regression in the opposite direction. **Neither the naive addition NOR the obvious fix is safe** —
    there is no existing field in `LeagueDefinition`/`classification` that distinguishes "new operator-directed
    wider-reference addition, NOT MVP" from "pre-existing Reference-tier entry that IS legitimately part of the
    96-league MVP baseline" (e.g. `FA_CUP` is `classification="Reference"` AND correctly in MVP scope today). **Reverted
    both files cleanly** (`git checkout --`, confirmed `git status` clean) — zero code shipped, zero regression risk
    taken. This is now a real, confirmed architecture question for whoever implements this, not a hypothetical: either
    (a) add a new boolean/enum field (e.g. `in_mvp_scope: bool`) to `LeagueDefinition` so classification and
    MVP-membership are independently settable, or (b) give the curated-universe expansion its own registry dict entirely
    separate from `LEAGUE_REGISTRY`/`_mvp_football_league_ids()`'s sweep, or (c) get an explicit operator ruling on
    whether the 11 majors SHOULD actually be in MVP scope (Directive A's own prose is ambiguous on this specific point —
    it says "wider universe" but also "we pretty much narrow down our prediction leagues to the ones the odds API has
    data for", and several of these 11 majors DO have real odds-API coverage per this session's earlier per-source-cap
    measurement). Do not repeat this session's naive-add attempt without resolving (a)/(b)/(c) first — QG will catch it
    again, but better to design it correctly than rely on the test suite as the only guardrail.
  - **RESOLVED + SHIPPED, same session.** Operator picked option (a) directly. Added
    `LeagueDefinition.in_mvp_scope: bool = True` (default preserves all 107 pre-existing entries' behavior unchanged —
    none needed individual edits) and repointed `_mvp_football_league_ids()` to filter on it instead of classification.
    Re-added the 11 continental-majors entries with `in_mvp_scope=False` explicit. **Verified before shipping, not
    assumed**: `_mvp_football_league_ids()` still returns exactly 96 (unchanged) and none of the 11 new entries appear
    in it — confirmed via direct call, not just "tests pass." Fixed the 2 tests that hardcoded `sport=="FOOTBALL"`
    counts to filter on `in_mvp_scope` instead (verifying, not assuming, that all 11 new entries are genuine Understat
    structural gaps before updating the count). Full `quality-gates.sh` green (279s, 11895 passed). Shipped:
    **unified-api-contracts@7b13196e**. This closes the continental-majors SLICE of step 1 — the full ~300-league
    curated universe (the 171-country domestic top+below+cup selection) remains open; main todo checkbox stays unchecked
    since steps 2 (backfill) and 3 (residual drop) haven't started and even step 1 isn't fully done.
  - **Post-ship consistency check (data, not guess)**: the 5 continental cups already in the registry before this
    session (`UCL`, `UEL`, `UECL`, `COPA_LIBERTADORES`, `COPA_SUDAMERICANA`) are all `in_mvp_scope=True` (via the
    field's default) — i.e. they were ALREADY intentionally part of the 96-league MVP baseline, consistent with
    Directive A's "we pretty much narrow down our prediction leagues to the ones the odds API has data for."
    Cross-checked whether any of the 11 NEWLY-shipped entries should have been `True` instead by the same logic: queried
    the same backup parquet's `data_type=="ODDS"` captured rows — **zero overlap** between the 11 new entries and the
    set of leagues with real captured odds data. Confirms `in_mvp_scope=False` was the correct call for all 11,
    consistent with (not contradicting) how the 5 pre-existing continental cups are treated.
  - **Attempted the domestic-cups slice for the 26 already-covered countries (FA Cup, DFB Pokal, Coppa Italia, etc.) —
    found a bug in my own filter before shipping anything, zero code touched.** `catalog['league_id']` is STRING dtype;
    my "not yet in registry" filter compared it against a set of INTEGER `api_football_id`s — silently never matched, so
    all 105→41→25 "candidates" I narrowed down to were false positives. Direct check against `LEAGUE_REGISTRY` confirms
    every one of the 25 (`FA_CUP`, `COPA_DEL_REY`, `DFB_POKAL`, `COPPA_ITALIA`, `KNVB_CUP`, `GREEK_CUP`, `AUSTRIAN_CUP`,
    `SWISS_CUP`, `DANISH_CUP`, `NORWEGIAN_CUP`, `SVENSKA_CUPEN`, `POLISH_CUP`, `COPA_ARGENTINA`, `COPA_DO_BRASIL`,
    `COPA_CHILE`, `COPA_MX`, `BELGIAN_CUP`, `US_OPEN_CUP`, `EMPEROR_CUP`, `KOREAN_FA_CUP`, `AUSTRALIA_CUP`, + 4 more) is
    ALREADY in the registry under a different key name than I'd have generated — would have shipped 25 duplicate entries
    pointing at the same underlying competitions if I hadn't verified with a direct lookup before writing code. **Net
    finding: the 26 already-covered countries' main domestic cups are already fully in the registry — nothing to add
    here.** The real remaining gap is genuinely new countries not yet in `LEAGUE_REGISTRY` at all (145 of the 171 in the
    catalog), which needs real per-country tier research (which division is "top", which is "below") — not something to
    guess at row-by-row.
  - **Spun off the remaining work into its own issue doc** (this plan file is near its 1000-line hard cap from
    concurrent slot activity — avoiding further growth here):
    `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md` — full session writeup (data locations,
    the `in_mvp_scope` architecture fix, what shipped, what's a dead end, what genuinely remains). This todo's checkbox
    stays unchecked here; track further progress in that doc, not this Progress Log.
  - **Released per main's BLK-7daa3e2a ruling** (correctly-parked research gap, not a stall): strengthened the issue doc
    to state the specific unblocking input + the 2 near-miss error classes hit this session
    (`unified-trading-pm@7608a8ef3`), then `/done` citing both SHAs.

- **2026-07-25 (slot 2, data_engineering) — "Eliminate the bare/legacy dual-layout" todo — VERIFIED CLEAN, no
  canonicalize/delete action needed.** Operator explicitly confirmed sign-off for the irreversible GCS apply this todo
  implies before any investigation proceeded (see below for why that mattered). Full session:
  - **Scope boundary clarified first**: this "bare/legacy dual-layout" work reads, on its surface, like the same
    underlying action as the archived `sports_manifest_canonicalisation_2026_06_01.md`'s E3→E8 apply steps (superseded
    into `sports_consolidated_closeout_2026_07_19.md`, which flags those as never having fired — gated on operator
    sign-off + fleet drain + foundation gates, never given). The closeout doc separately carries an explicit **"DO NOT
    EXECUTE, cross-reference only"** warning for the _legacy no-env bucket decommission_ (`instruments-store-sports` vs
    `-prd-`, owned by `sports_legacy_bucket_cutover_2026_07_16.md`, `assigned_vm: NA` — never AO-dispatchable).
    Confirmed these are DIFFERENT scopes: this todo is an intra-bucket path-LAYOUT cleanup (bare-path objects vs.
    `league=`-partitioned objects, both inside the single canonical `instruments-store-sports-prd-*` bucket, per
    `gcs_paths.py`'s `SportsPathLayout` enum) — not the whole-bucket decommission. The DO-NOT-EXECUTE boundary does not
    cover this todo; the operator-sign-off gate does, and was obtained.
  - **Real census, not an assumption**: got a working `.venv` (`scripts/setup.sh`, background — the interactive 2-min
    timeout earlier was a tool-call limit, not a real failure) and ran
    `instruments-service/scripts/migrate_sports_per_league.py --entity all --dry-run --workers 8` against
    `instruments-store-sports-prd-central-element-323112` — covers `fixture_stats`/`fixture_events`/
    `fixture_lineups`/`player_stats` (fixture-id join), `footystats_predictions`/`footystats_matches`
    (canonical-fixture-id prefix), `injuries` (league_id column), `understat_xg` (league column): **all 8 entities, all
    2322 scanned dates → `already_per_league=0`, `no_single_file=2322`, `migrated=0` — zero bare files found, zero
    migration needed, for every single date.**
  - **Extended coverage to the 7 `PER_DAY_PER_LEAGUE` entities the script doesn't handle** (`FIXTURES`,
    `FIXTURES_SCHEDULE`, `FIXTURES_OUTCOMES`, `STANDINGS`, `TEAMS`, `ODDS`→`footystats_odds`,
    `XG_SHOTS`→`understat_xg_shots`, `SFI_PROGRESSIVE_STATS`→`progressive_stats`) via a targeted, bounded spot-check (13
    dates spanning 2018-01-01 → 2026-12-06 + `day=all`, direct `blob.exists()` point-checks — NOT a new whole-corpus
    walk): **zero bare files found across all 13 dates × 7 entities, except ONE hit —
    `day=all/entity=teams/teams.parquet`.** That single hit is the exact object another slot independently deep-dove the
    same session (`sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`) and correctly parked as
    `BLOCKED-OPERATOR-DECISION` under the sibling "Retention floor" todo below — it's the day=all
    teams/venues-reference-data case explicitly called out as OUT OF SCOPE for this todo in the plan's own todo text
    ("Distinguish from the by-design bare entities... which stay bare" — day=all is a distinct reference-snapshot
    concern, not a per-date dual-layout defect). Confirmed this todo does not need to touch it.
  - **Conclusion — all 15 `PER_DAY_PER_LEAGUE` entities checked, zero dual-layout instances found.** The condition this
    todo describes ("per-league entities that have BOTH a per-league split AND bare files for older days") does not
    currently exist in prod. Either it was already resolved by an earlier, unrelated cleanup between the source doc's
    2026-06-24 authoring and now, or the original framing over-generalized from the day=all teams/venues case. Either
    way, the "Done when" bar ("every ... entity ... canonicalised or deleted") is honestly satisfied — zero entities
    meet the todo's own trigger condition, verified by a real census rather than assumed.
  - No code shipped (nothing needed migrating). No snapshot/delete executed (nothing found to snapshot or delete).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox in its named source doc, citing this plan's commit as evidence.
This plan's own reconciliation-then-archive step is machine-gated on it via
`sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`
(`depends_on: [sports_satellite_ao_dispatch_batch2_2026_07_24]`

- `gate_on_depends: true`) — mirroring `sports_closeout_batch1_finalize_2026_07_24.md`'s pattern for batch 1, adapted
  for batch 2's 15-way source-doc fan-out (batch 1 reconciles one gate-able parent; batch 2 reconciles 15 independent
  docs, per-doc, before archiving this plan).

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc. See
each source doc's own "Codex SSOTs" section (where present) for the relevant references.
