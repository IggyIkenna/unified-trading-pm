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

- [ ] [DATA] P0. **Eliminate the bare/legacy dual-layout** (operator: "legacy needs canonicalising or deleting — that's
      the whole point") — per-league entities that have BOTH a per-league split AND bare files for older days
      (`gcs_paths.py:96`) carry a stale parallel layout. For each: canonicalise the bare→per-league (in-retention) OR
      DELETE (pre-retention). Distinguish from the by-design bare entities (XG/WEATHER/player_values-bulk) which stay
      bare. (repo: instruments-service; read-only reference: unified-api-contracts `gcs_paths.py` `SportsLayout`).
      **Done when**: every per-league entity with a dual bare+per-league layout is canonicalised (in-retention) or
      deleted (pre-retention), snapshot-first; by-design bare entities left untouched. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [ ] [DATA] P0. BLOCKED-OPERATOR-DECISION **Retention floor = the EXISTING per-source genesis registry — NOT a blanket
      2015 delete.** 2026-07-25 investigation (`sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`):
      this todo's premise does not survive contact with the real GCS objects — **(a) day=all fold is genuinely
      blocked**: UAC's SSOT only maps VENUES to a FLAT layout (TEAMS is PER_DAY_PER_LEAGUE-only, so "fold into FLAT" is
      inapplicable to TEAMS as stated); the legacy `day=all/entity=venues/venues.parquet` (3,445 rows, raw numeric
      api_football `venue_id` keys, e.g. `1456`) and the live FLAT `sports_reference/venues/venues.parquet` (2,860 rows,
      slugified string keys, e.g. `OLD_TRAFFORD`) have **zero key overlap** — verified directly, not assumed — so there
      is no join key to "dedup" against; no live reader of `day=all` was found in any of the 6 core sports repos (looks
      like dead legacy data from an earlier writer generation), but `instruments-store-sports-prd` has soft-delete=0
      (irreversible) and the original plan author explicitly flagged "would break team/venue resolution" as a delete
      risk — needs explicit operator sign-off (see issue doc's Options A/B/C), not a unilateral fold-that-can't-work or
      an irreversible delete. **(b) pre-genesis anomaly check is NOT new work**: the 131,306 TEAMS + 1,457 VENUES
      pre-floor rows found are a subset of the ALREADY-TRACKED, already-deferred 944,776-row
      phantom-pre-floor-manifest-row issue in `/codex/02-data/sports-2020-06-data-floor.md` (blocked on a GCS-walk
      manifest rebuild, explicitly NOT a hand-edit target) — satisfied by reference, no separate script needed. Also:
      this todo's quoted per-source genesis dates (understat 2014/api_football 2015/footystats etc. 2019) are **stale**,
      superseded 2026-07-21 by a uniform 2020-06-06 WIPE floor for all sports sources (see the floor doc). Full
      evidence, GCS byte/row counts, and recommended option in the issue doc. Source:
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
- [ ] [DATA] P0. **Drop 2 out-of-universe numeric `league=` dirs** (`14231`/`315`), snapshot-first, twin/scope-verified.
      (repo: instruments-service). **Done when**: both dirs are dropped (snapshot-first) or explicitly folded into the
      curated-set residual-drop todo below's tracked scope. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [ ] [DATA] P0. **94-league enrichment backfill** — the residual golden-window gap is now GENUINE missing enrichment
      (XG_SHOTS 0% / XG 13% / PLAYER_STATS 21% / MATCHES 35% / INJURIES 37%), NOT a schema artifact. API-Football
      fixtures (fast, already 100%) → enrichment for the 94, fix broken, be thorough → re-measure toward 100%. (Its
      stated prerequisite — the tarball rebuild with the write-gate — is already DONE.) (repo: instruments-service).
      **Done when**: enrichment coverage for the 94-league universe re-measured and materially improved toward 100% for
      XG_SHOTS/XG/PLAYER_STATS/MATCHES/INJURIES, with any broken enrichment paths fixed. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
- [ ] [CODE] P1. **UAC canonical registry build/refine** — league/cup canonical + ids + is-cup + country + season
      start/end + transfer window; per-source eligibility maps + annual-id-change handling; team/player/fixture
      canonical + mappings. Wire honest-coverage to consume them. (Spec fully established by the source doc's
      Architecture section + the operator's Directive A.) (repo: unified-api-contracts canonical/domain/sports
      registries; instruments-service honest-coverage consumers). **Done when**: UAC holds the canonical league/cup
      registry (name/ids/is-cup/country/season start-end/transfer window), per-source eligibility maps with
      annual-id-change handling, and team/player/fixture canonical mappings; honest-coverage code consumes them instead
      of ad hoc logic. Source: `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
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

- [ ] [SCRIPT] P0. **Fix `fixture_id=NULL` propagation in the odds_api backfill path** — golden window `trades` data has
      all fixture_ids as NULL, which blocks per-fixture cluster validation entirely. Likely market-tick-data-service
      (`market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py` + `fixture_id_resolver.py`, which
      already has partial `af_fixture_id` join scaffolding) — NOT instruments-service despite the source doc's
      frontmatter; confirm exact ownership at execution time (grep both repos for the golden-window trades write path)
      before scoping. (repo: market-tick-data-service). **Done when**: golden-window (2025-09-01..2025-11-30) odds_api
      `trades` rows carry a non-NULL `fixture_id` (or the existing `af_fixture_id` join is confirmed to already satisfy
      this — either outcome is determinable); a regression test proves `fixture_id` is stamped on newly-captured trades
      rows; `quality-gates.sh` green. Source: `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`.

### From `sports_odds_feature_naming_canonicalization_2026_07_21.md`

> Sequencing note for AO: the 5 todos below (spanning features-service, unified-api-contracts, ml-service, and
> strategy-service ×2) are each in a DIFFERENT file, safe to dispatch concurrently. A 6th todo from this source doc (the
> cross-repo FSS↔ml-service↔strategy-service parity test) is DELIBERATELY EXCLUDED here because it depends on ALL 5 of
> these landing first and this plan has no mechanical way to gate one todo on 5 siblings without serializing the whole
> plan — add it as a new todo (in this plan or a successor) once these 5 are confirmed shipped.

- [ ] [DATA] P1. **New compute, not a rename**: add per-bookmaker raw decimal-odds retention to
      `features_service/sports/calculators/` (whatever calculator currently collapses per-venue quotes into
      `best_odds_*`/`odds_variance_*` — trace it first) so a `decimal_odds_<outcome>_<venue>` shape can actually be
      populated for `SportsArbDutchingEngine`. (repo: features-service). **Done when**: a decimal odds field keyed per
      outcome+venue (final name per the decided scheme, e.g. `odds_decimal_home_pinnacle`) is computed and populated in
      FSS output for real bookmaker/venue combinations. Source:
      `sports_odds_feature_naming_canonicalization_2026_07_21.md`.
- [ ] [DATA] P1. **Rename UAC's `OddsFeaturesMixin`/`SportsFeatureVector` fields** to the 2026-07-23 DECIDED naming
      scheme (rename in place). Add/update UAC unit tests covering the schema's field set. (repo: unified-api-contracts
      `unified_api_contracts/internal/domain/features_sports/_features_venue_referee_player_odds.py`). **Done when**:
      field names match the decided scheme table in the source doc's 2026-07-23 Progress Log (`prob_implied_*`,
      `prob_fair_*`, `odds_market_*`, `odds_decimal_*`, etc.); UAC unit tests updated and passing. Source:
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

- [ ] [DATA] P1. **Post-backfill entity-coverage relabel** (after confirming the 6 previously-running backfill VMs are
      terminal and the consolidator is drained — relabel races a live manifest): extend the entity-coverage relabel
      (`refresh_sports_league_entity_coverage` / migration C logic) over the 120 recent dates (2026-02-20→06-19) × 789
      leagues — no-coverage (league,data_type) pairs → `expected_empty` (`EXPECTED_NO_PROVIDER_COVERAGE`), and reconcile
      cells whose data already exists in GCS → `captured`. Then re-measure honest-cov (expect a large jump). (repo:
      instruments-service + market-tick-data-service manifest migration touch point). **Done when**: VMs confirmed
      terminal → relabel applied over the 120-date × 789-league window → cells reclassified correctly → honest-cov
      re-measured and the delta recorded in the source plan. Source: `data_completion_sports_2026_07_24.md`.
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

- [ ] [BACKEND] P2. **Switch `deployment-api/services/fixtures_browser.py` to the single catalogue** (currently still
      the day-walk, `@5815582`). Read `prod/catalog.parquet` ONCE (schema-aware projection), filter
      `instrument_type=="fixture"`, TTL-cache the PARSED frame. Map → `FixtureRow`: `fixture_id`=`instrument_id`;
      `home_team_id`/`away_team_id` parsed from the id's `HOME_v_AWAY` (or UAC `build_team_id`); `venue_id`="" (honest,
      not carried). Filter/group on `available_from` (verified 17,064/17,064 = 100% identical to the id's `:YYYYMMDD`
      suffix, zero drift). Delete `_MAX_WINDOW_SPAN_DAYS` (120d cap). Start CLEAN from `@5815582` — a prior half-written
      attempt broke the module and was reverted; do not resume from that state. (repo: deployment-api
      `services/fixtures_browser.py`). **Done when**: `fixtures_browser.py` reads `prod/catalog.parquet` once (cached
      parsed frame), filters+maps per the spec above, `_MAX_WINDOW_SPAN_DAYS` is deleted, `quality-gates.sh` is green.
      Source: `sports_fixtures_browser_single_catalogue_source_2026_07_24.md`.

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
      `sports_master_closeout_progress_log_2026_07_24.md` (tracking table row) — unified-trading-pm@PENDING_SHA.

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

- [ ] [CODE] P1. **Stop stale/zombie ticks at bucket assignment** (fix locus: MDPS, not MTDS raw ingestion). Primary fix
      in `market-data-processing-service/.../adapters/sports/bucket_assignment_adapter.py`: drop rows whose
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
      `issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`.

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

- [ ] [DATA] P0. **Fix the independent per-fixture league_id defect** — `sports_reference_fixtures.py:224-229` has its
      own instance of the same class of bug the shipped `mtds@ad4f1872` write-path fix addressed: the
      `fx.league.league_id` branch always wins over the numeric-id `elif` (making id-based resolution dead code), and
      `build_league_id()` falls back to a bare slug when `country` is empty. Live leakage evidence already on disk:
      `.../entity=injuries/league=235/`. (repo: instruments-service `sports_reference_fixtures.py` lines ~224-229 —
      DIFFERENT file from the migration-sequence todo below, safe to dispatch concurrently). **Done when**: numeric
      `api_football_id` resolution takes precedence over the raw `fx.league.league_id` branch; `build_league_id()` no
      longer falls back to a bare numeric id when country is empty; a regression test mirrors the 3 tests shipped in
      `mtds@ad4f1872` (incl. one asserting the six known collisions resolve to distinct slugs); no more bare-numeric-id
      partitions produced going forward. Source: `issues/sports_league_id_namespace_migration_2026_07_20.md`.
- [ ] [DATA] P0. **League_id casing migration — census→copy→reprocess→swap (4-step ordered sequence, one worker, execute
      in order — this is one already-verified, ready-to-execute migration, not 4 independent jobs).** (1)
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

- **2026-07-25 (slot 2, data_engineering) — "Eliminate the bare/legacy dual-layout" todo — SCOPED, execution DEFERRED
  (not started, checkbox correctly left unchecked).** Operator explicitly confirmed sign-off for the irreversible GCS
  apply this todo implies (asked directly given the discovery below) before any investigation proceeded further.
  Findings:
  - **Clarified a scope boundary that wasn't obvious from this plan's todo text alone**: this exact "bare/legacy
    dual-layout" work is the same underlying action as the archived `sports_manifest_canonicalisation_2026_06_01.md`'s
    E3→E8 apply steps (superseded into `sports_consolidated_closeout_2026_07_19.md`), which that doc explicitly flags as
    never having fired (gated on operator sign-off + fleet drain + foundation gates). Separately, the closeout doc ALSO
    carries an explicit **"DO NOT EXECUTE, cross-reference only"** warning for the _legacy no-env bucket decommission_
    (`instruments-store-sports` vs `-prd-`, owned by `sports_legacy_bucket_cutover_2026_07_16.md`,
    `assigned_vm: NA`/`execution_scope: local-only` — never AO-dispatchable). Confirmed these are DIFFERENT scopes: this
    todo is an intra-bucket path-LAYOUT cleanup (bare-path objects vs. `league=`-partitioned objects, both already
    living inside the single canonical `instruments-store-sports-prd-*` bucket, per
    `unified_api_contracts/canonical/domain/sports/gcs_paths.py`'s `SportsPathLayout` enum) — NOT the whole-bucket
    decommission. The DO-NOT-EXECUTE boundary does not cover this todo; the operator-sign-off gate does, and was
    obtained.
  - **Identified existing tooling to reuse rather than rewrite**:
    `instruments-service/scripts/migrate_sports_per_league.py` (436 lines, `--dry-run`/`--no-dry-run`,
    `--entity {name|all}`) already implements exactly the bare→per-league canonicalize half of this todo, covering
    `fixture_stats`/`fixture_events`/`fixture_lineups`/`player_stats` (fixture-id join),
    `footystats_predictions`/`footystats_matches` (canonical-fixture-id prefix), `injuries` (direct `league_id` column),
    `understat_xg` (league column). It does NOT cover every entity in `SPORTS_DATA_TYPE_LAYOUT` with
    `PER_DAY_PER_LEAGUE` (e.g. `FIXTURES` itself, `TEAMS`, `STANDINGS`, `ODDS`, `PREDICTIONS`, `XG_SHOTS`,
    `SFI_PROGRESSIVE_STATS`) — either those never had a bare-layout era, or their migration needs separate handling; NOT
    yet determined which.
  - **DID NOT get to a real census**: attempted `bash scripts/setup.sh` to get a working `.venv` for a `--dry-run` scan
    (needed before any real numbers on scope: which entities actually have residual bare files, how many dates/objects,
    in-retention vs pre-retention split against the `SOURCE_COVERAGE_START` genesis registry) — the setup timed out at 2
    minutes (dependency install for a large repo) before completing.
  - **Deliberately stopped here rather than rush the irreversible half.** This todo's own "Done when" bar requires FULL
    completion (every dual-layout entity canonicalised-or-deleted, snapshot-first) — not a partial pass. Given (a) the
    real census hasn't run yet, so the true scope (object count, date range, retention split) is unknown, (b) this is a
    genuinely multi-entity, multi-year GCS operation with an IRREVERSIBLE delete half, and (c) this session was already
    at a compaction-flagged context level when the task was dispatched — starting the snapshot/canonicalize/delete
    sequence without first completing the census, and without headroom to see it through to full verification, risks
    leaving prod sports data in a partially-migrated, unverified state. That is a worse outcome than a clean, documented
    handoff. Per this codebase's own heavy-I/O rule (`/codex/05-infrastructure/vm-launcher-runbook.md` § heavy-I/O), a
    full multi-year census + migration at this scale is also a candidate for a dedicated VM run rather than an
    interactive session, which the next pickup should evaluate.
  - **Recommended next step for whoever picks this up**: (1) get a working venv (or run on a fresh VM per the heavy-I/O
    precedent), (2) run `migrate_sports_per_league.py --entity all --dry-run` against
    `instruments-store-sports-prd-central-element-323112` to get the real per-entity bare-file census, (3) for entities
    the script doesn't cover, determine (via manifest query, not a new whole-corpus walk) whether they ever had a bare
    layout at all, (4) THEN snapshot + canonicalize/delete with the retention floor from UAC `SOURCE_COVERAGE_START`.
    Operator sign-off for the irreversible apply is already on record in this session (chat, not yet written elsewhere —
    worth a durable note if/when execution actually starts).

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
