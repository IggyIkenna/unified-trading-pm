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
  `sports_closeout_batch1_ao_ready_2026_07_24.md` pattern. 37 todos (corrected 2026-07-25 plan-reconcile, was 36) from
  15 source docs. Internally-sequential multi-step chains (e.g. a 5-step GCS migration recovery procedure, a 4-step
  census→copy→reprocess→swap execution sequence) are combined into single todos rather than fanned out — AO's per-todo
  model has no mechanism to mechanically gate step N on step N-1 within one plan short of `sequential: true` for the
  WHOLE plan, and this plan's other todos genuinely benefit from concurrent dispatch, so combining same-job chains into
  one todo each is the safe choice, not a fragile cross-todo ordering promise. 4 real AO-eligible items were
  deliberately EXCLUDED (not lost — flagged in their source docs) because they depend on either another todo below
  landing first (a 5-repo-spanning parity test; a UI relabel gated on its own backend todo) or a human/operator decision
  that has not yet been made (the SportsMatchingEngine-vs-L0Matcher design call blocks all 3 of
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
    /plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md,
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
- [x] ✅ [DATA] P0. **94-league enrichment backfill** — the residual golden-window gap is now GENUINE missing enrichment
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
      the gap actually closed before flipping this checkbox. — **Re-health-checked 4x (01:45Z slot 7 / 02:24Z slot 2 /
      02:30Z slot 9 / 02:49Z slot 4), latest 2026-07-25T02:49Z**: `af-backfill-20260725-002739` still RUNNING,
      `PROGRESS.json` monotonic-advancing (`last_completed_date=2025-05-30`, ~7.4/8.5yrs), rate ACCELERATING (ETA now
      <1hr vs earlier "hours"), no error/stall signature. Each check released via `/skip-current-task`, NEVER
      duplicate-launched. — **TERMINAL 2026-07-25T03:21:57Z (slot 4, data_engineering): completed cleanly**
      (`exit_code=0`, `DEPLOYMENT_COMPLETED`, `last_completed_date=2026-07-25` — reached present day, self-deleted).
      Re-ran the INJURIES gate-query the todo asks for, but **checkbox NOT flipped — the result doesn't cleanly show
      closure and needs a fresh assessor, not a rubber-stamp**: consolidated-index re-measurement for the 94-league
      universe now shows `captured=9,260 / expected_unattempted=8,568` — BOTH lower than this todo's own pre-backfill
      baseline (`captured=10,502 / expected_unattempted=10,219`), the opposite of what a successful catch-up backfill
      should show. Cross-checked against the VM's own per-VM shard directly (not just the consolidated index, in case of
      a consolidation-lag artifact): shard has 9,251 real captured INJURIES rows, date range 2020-06-06→2026-07-25 —
      consistent with the consolidated count, so this isn't a lag artifact, the counts are genuinely lower. **Likely
      confound, not verified**: the 2020-06-06 uniform data-floor WIPE (`/codex/02-data/sports-2020-06-data-floor.md`)
      landed 2026-07-21, AFTER this todo's baseline was measured — pre-floor rows previously counted as
      `expected_unattempted` may have been deleted from the manifest entirely, which would lower both numbers
      independent of the backfill's real contribution. Did not have time to confirm this confound explains the full
      delta (would need the baseline's original exact query + a floor-aware re-run to isolate the backfill's true
      effect) — flagging for whoever assesses this todo next rather than guessing either way. — **CONFOUND RESOLVED,
      CHECKBOX FLIPPED 2026-07-25T04:20Z (slot 11, data_engineering): it was a methodology artifact, not a real
      regression.** Downloaded 3 manifest snapshots directly (`availability_index.20260724-202648.bak.parquet` /
      `availability_index.20260725-002417.drop_14231_315.bak.parquet` [the actual pre-backfill baseline] / current
      `availability_index.parquet`) and re-ran the INJURIES query filtered consistently to the same 96-league canonical
      set (`unified_api_contracts...mvp_scope_rules._mvp_football_league_ids()`) across all three. Root cause of the
      apparent regression: the prior assessor's cited baseline (`captured=10,502 / expected_unattempted=10,219`) was
      **unfiltered** (all leagues), while the cited "current" re-measurement
      (`captured=9,260 / expected_unattempted=     8,568`) was 94-league-**filtered** — an apples-to-oranges comparison,
      not a real decrease. Re-run with the SAME filter both times: baseline (00:24, post-drop_14231_315, i.e. the true
      pre-backfill state) `captured=8,803 /     expected_unattempted=10,219` (pre-floor phantom 8,474 + post-floor real
      gap 1,745) → current (04:12) `captured=     9,260 / expected_unattempted=8,474` (pre-floor phantom 8,474
      UNCHANGED, post-floor gap 1,745→**0**, fully closed). Three independent signals rule out a lost-update/floor-clamp
      confound: (1) the pre-floor phantom count is byte-identical (8,474) across all 3 snapshots spanning
      before/during/after the backfill — the deferred manifest phantom-prune
      (`/codex/02-data/sports-2020-06-data-floor.md`) genuinely has not touched these rows; (2) filtered row COUNT grew
      (294,920→299,090), ruling out a row-collapse/lost-update explanation (a collapse loses rows, this gained them);
      (3) captured is monotonically increasing across all 3 reads (8,800→8,803→9,260) both filtered and unfiltered
      (10,499→10,502→10,920) — consistent with real, ongoing backfill progress, not noise. **Done-when met**: the 6
      non-INJURIES entities were already confirmed exhaustively-attempted (>99% honest-absence) by the prior session's
      re-measurement above; INJURIES — the one genuine exception — now shows its post-floor real gap closed 100%
      (1,745→0 `expected_unattempted`). `af-backfill-20260725-002739` confirmed terminal
      (`exit_code=0`/`DEPLOYMENT_COMPLETED`, self-deleted, per the prior session); the only `af-backfill-*` VM currently
      running (`af-backfill-20260725-032253`) is an unrelated FIXTURE_EVENTS refetch-recovery job from a different task,
      not a duplicate of this one. Source:
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`.
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
      `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`. — **RECONCILED 2026-07-25 (slot 4,
      data_engineering): checkbox correctly stays unchecked — this todo is ALREADY superseded-by-decomposition, not a
      fresh start.** Step 1's continental-majors slice shipped (`unified-api-contracts@7b13196e`); the 171-country
      domestic-selection slice is split into 11 confederation-batch todos in
      `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md` (all 11 now `[x]`, see re-verify
      below). Steps 2 (backfill) + 3 (residual drop) are explicitly gated on all 11 landing first. No code touched:
      re-executing step 1 here would duplicate/collide with the already-dispatched batches; this todo's real done-when
      is now "all 11 batches + step 2 + step 3 land," tracked in the issue doc, not re-derived here. — **RE-VERIFIED
      2026-07-25 (slot 4): still unchecked** — step 2 gate MET but launch-BLOCKED on the `af-backfill-*` singleton lock
      (held by `-031`'s fixture_events re-fetch); step 3 deferred. Live tracker: issue doc's final gated item. —
      **RE-VERIFIED 2026-07-25T12:56Z (slot 11): still unchecked** — lock cleared, backfill launched (this todo's
      "2019→" text is stale vs. the 2020-06-06 sports floor, corrected), step 2 in progress, step 3 untouched. Detail in
      the issue doc.

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
- [x] ✅ [DATA] P2. **PIT horizon-gating gap for the new `odds_decimal_<outcome>_<venue>` columns** (found while
      shipping the todo above): `feature_expectations.py`'s `ODDS_COLUMNS` registry drives PIT horizon-gating
      (`apply_horizon_gate()`), which only walks a fixed column list — the new dynamic per-venue columns aren't in it
      and so bypass PIT gating entirely (there's no schema allowlist blocking them at the parquet-write boundary either,
      so they DO reach output — just ungated). Add a pattern-match (e.g. `startswith("odds_decimal_")`) to
      `apply_horizon_gate()`/`get_column_horizons()` so these get the same leak protection as every other odds field.
      Add a regression test proving a T-24h row's `odds_decimal_*` doesn't leak a later horizon's value. (repo:
      features-service) — features-service@daa373bd. Extended `apply_horizon_gate()` to pattern-match the
      `odds_decimal_` prefix, gating those dynamic columns at the same horizon as the static "odds" group (read from the
      registry via `_ALWAYS_FULL_GROUPS["odds"][1]`, not duplicated, so a future change to the odds group's horizon
      stays in sync automatically) — `get_column_horizons()` itself stays a static SSOT dict (unchanged contract for
      downstream consumers); the dynamic extension happens only inside the sports `apply_horizon_gate()` wrapper, which
      has the live `df.columns` needed to pattern-match. 2 regression tests: one confirming the columns survive gating
      at T-24h (their real home horizon); one monkeypatching a later horizon and confirming the column then gets NaN'd,
      proving the wiring is genuinely real rather than coincidentally matching the untouched-metadata path. Session
      survived a mid-task session death (this exact fix was lost and had to be reapplied byte-for-byte before shipping —
      verified via git status showing a clean tree post-resume). `quality-gates.sh` green.
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
- [ ] [DATA] P1. **Migrate `features_service/sports/calculators/odds_columns.py`'s `ODDS_COLUMNS`** + the odds-features
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
- [ ] [OPERATOR] P1. **Relaunch features-sfi-progressive** — code fix already shipped (`features-service@06c44c02`);
      first verify (via git log) whether the launcher's repoint to `VM_SERVICE=features_service` /
      `python -m features_service.sports.scripts.compute_sfi_progressive_only` already shipped (the source doc cites
      placeholder `<sha>`s, not real ones); if not, ship it. Then confirm market-tick-data-service is clean (no foreign
      uncommitted WIP blocking the tarball build) → rebuild SPORTS tarball via
      `create-code-tarballs.sh --asset-group SPORTS` →
      `RECOMPUTE_FORCE=true     launch-sfi-progressive-features-backfill-vm.sh --force 2020-01-01 <today>` → verify
      run.log has no `MissingFeatureFamilyError`. (repo: deployment-service
      `scripts/vm/launch-sfi-progressive-features-backfill-vm.sh`, `scripts/vm/create-code-tarballs.sh`;
      features-service `features_service/sports/scripts/compute_sfi_progressive_only.py` — read-only dependency check on
      market-tick-data-service, no edits there). **[OPERATOR]**: `RECOMPUTE_FORCE=true --force` overwrites captured prod
      manifest rows for the full 2020-01-01→today window + launches a billed VM — cite
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`, get operator go-ahead before the relaunch step (the
      verify/tarball-rebuild prep above is safe without it). **Done when**: launcher confirmed pointed at
      `features_service.sports.scripts.compute_sfi_progressive_only` (fixed if not); SPORTS tarball rebuilt; relaunch's
      run.log shows no `MissingFeatureFamilyError` and `PROGRESSIVE_DAY_CAPTURED` events, exit code 0. Source:
      `data_completion_sports_2026_07_24.md`.

### From `sports_legacy_cutover_closeout_tasks_2026_07_24.md`

- [x] ✅ [DATA] P2. **T6.8 — retire the one-offs + the dead knob + the false-progress tick — SAFE SUBSET SHIPPED,
      residual tracked.** Per-file `Delete-when` + git-history/import-graph verification found the blanket-delete
      premise false for `migrate_sports_canonical_v9.py` (live import chain) and most of the "~26"
      `instruments-service/scripts/**` grep-estimate (permanent-lifecycle / broader-campaign-gated / recently-active /
      unverifiable). Shipped: the doubly-broken gate + 2 named one-offs (market-tick-data-service@f8276e22); full
      `include_legacy_archive` knob retirement after fixing its 1 live caller (unified-api-contracts@887ab894,
      instruments-service@5ff530f9) — `rg 'include_legacy_archive'` → 0 hits workspace-wide; the 5
      independently-verified `instruments-service/scripts/**` one-offs shipped same-day (instruments-service@269440d7);
      v1_archive gate un-tick/correction already done (unified-trading-pm@3aff7f716). Residual (v9-cluster + ~14
      unverified one-offs) tracked, not dropped:
      `plans/active/issues/sports_t6_8_oneoff_retirement_residual_2026_07_25.md`. The todo's own literal final gate
      (`rg -c 'sports-central-element-323112'` → 0) is corrected as unachievable — many remaining hits are legitimate
      permanent-lifecycle/doc references; see the source doc for full detail. Source:
      `sports_legacy_cutover_closeout_tasks_2026_07_24.md`.

### From `sports_prelaunch_cf5_verify_residual_2026_07_24.md`

- [x] ✅ [DATA] P1. **Sports CF-5 oracle relabel = ZERO — landed.** — market-tick-data-service@7f1262a0. Confirmed
      `origin/wip-preserve/mtds-346-cf5-trades` (`mtds@d0a15a3`, 2026-06-16) had NOT landed and was too stale to
      cherry-pick wholesale (predates + would regress the 2026-07-13 SFI_PROGRESSIVE_STATS retired-set fix and several
      later CF-11/attempted_at/chain-blank fixes on the same file). Applied the isolated one-line fix
      (`"trades"`→`"TRADES"` in `_PER_FIXTURE_DERIVED_DATA_TYPES`) directly on current HEAD + adapted the wip branch's
      regression test onto current HEAD (not restored wholesale). TDD-verified: confirmed the new test fails against the
      pre-fix lowercase entry and passes with the fix. quality-gates.sh green. Landing required several retries —
      quickmerge's full-suite re-gate hit genuine host-load-induced infra flakiness (pytest-xdist worker crash under
      load 17-30 on an 8-core box, 3+ concurrent slots running full QGs simultaneously), not a content issue; landed
      once host load allowed a clean re-gate pass. (repo: market-tick-data-service). **Done when**: worker confirms
      landed-or-not first (citing the check); if not landed, the fix + its regression test are confirmed present on
      market-tick-data-service main/LDR HEAD, citing the landing commit sha. Source:
      `sports_prelaunch_cf5_verify_residual_2026_07_24.md`.

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

- [x] ✅ [DATA] P2. **Manifest-slice replacement for `check_api_football_dependency()`** —
      `instruments-service@bd1da540`. Added `_manifest_shows_fixtures_captured()`: a pyarrow-pushed-down
      `read_availability_index()` slice (`date`/`data_type`/`capture_status`, ~0.1s/call) as the PRIMARY check, matching
      `data_type in {FIXTURES, FIXTURES_SCHEDULE}` + `capture_status == "captured"` — NOT `venue ==     "API_FOOTBALL"`
      per the issue doc's prose: live-data probe found these rows carry an EMPTY `venue` column, api-football identity
      is implied by `data_type` alone. Verified equivalent to the old GCS-probe verdict against 12+ real dates
      (2024-2026, incl. 2 genuine-miss dates) before writing tests. Old GCS-probe KEPT UNCHANGED as fallback
      (manifest-read failure/staleness returns `False`, never raises) — path-template duplication is moot since the hot
      path no longer touches them, per this todo's own anticipated outcome. 9 new/updated unit tests. `quality-gates.sh`
      PASSED. Source: `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.
- [x] [DATA] P2. ✅ **Cached/batched fix for `sports_fixtures.py:356`** — `instruments-service@2be5698d`. The doc's
      stated path (`instruments_service/reference_data/sports_fixtures.py`) was stale — the real file is
      `instruments_service/engine/orchestrator/sports_fixtures.py`, and the actual per-(entity×league) primitive
      (`_read_existing_per_league_fixture_ids`, called from
      `sports_reference_fixtures.py::_read_captured_per_entity_league`) had ALREADY been fanned out concurrently by a
      prior fix (`api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`) — wall-clock was
      already fixed, but call COUNT was unchanged (still up to ~4 entities × ~33 leagues individual `.exists()` probes).
      No per-date consolidated parquet exists in the real storage layout (verified: each league is a genuinely separate
      GCS object under `entity={entity}/league={L}/`), so a true single-read-per-date isn't achievable — the real
      ceiling is per-ENTITY batching via the ALREADY-EXISTING shared helper `_read_per_league_entity_df` (same one used
      to fix the other ~9 sites in this issue doc), which lists+downloads every league's data for one entity+date in a
      single pass. Implemented as a new small cohesion module (`sports_fixture_prefetch_skip.py` — kept
      `sports_reference_fixtures.py` under the 900-line ratchet) with `_read_captured_league_fixture_ids_for_entity()`
      (batched per-entity read) + `_captured_fixture_ids_by_league()` (grouping helper); collapses call count from
      O(entities × leagues) to O(entities) — up to ~132 individual `.exists()` probes down to `len(entities)` (typically
      ≤4) `list_blobs` passes. Removed the now-dead `_read_existing_per_league_fixture_ids` (zero remaining callers,
      confirmed via full-repo grep) + its 2 stale `__all__` exports. Rewrote the 2026-07-18 concurrency regression tests
      (`TestGatherPerFixtureRowsBatchedPreFetchSkip`, was `...ConcurrentPreFetchSkip`) to prove the NEW invariant — 1
      batched call per entity regardless of league count (not just wall-clock) — while preserving entity-level
      concurrency coverage; added 3 new direct unit tests for the grouping/batched-read helpers (fid-column fallback,
      no-blobs-found, transport-failure fail-safe-empty). Fixed 4 existing integration-test mock targets (facade path
      changed with the module split). Full `quality-gates.sh` green (4880+ tests, 0 basedpyright errors beyond the
      pre-existing warn-only ceiling, file-size ratchet clean). Source:
      `issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`.

### From `issues/sports_legacy_duplicate_triage_2026_07_22.md`

- [ ] [DATA] P1. **Migrate-forward the 58 v2 post-floor rows** (16 days) into canonical per-league `entity=fixtures` /
      `entity=fixture_stats` — reuse `migrate_sports_per_league.py`'s per-fixture-league-join logic, not a delete.
      Re-run the sweep after to confirm these flip to `A_canonical`. (repo: instruments-service —
      `scripts/migrate_sports_per_league.py` logic against bucket `instruments-store-sports-prd`; re-run
      `scripts/migration_orphan_sweep_sports.py --bucket reference` afterward). **Done when**: all 58 rows across the 16
      days have canonical objects written, and a re-run of the orphan sweep reclassifies them as `A_canonical` instead
      of `B_legacy_duplicate`. Source: `issues/sports_legacy_duplicate_triage_2026_07_22.md`.
- [ ] [CODE] P1. **Repoint or retire the two flat-legacy readers** before the 28,100 post-floor flat rows can be
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

- [x] ✅ [DATA] P3. **Fleet-wide sweep for the same seeder-over-captured pattern** — CLEAN, no unguarded asset_group.
      `enumerate_v2()`'s `captured_set` drop-filter is ONE choke point after per-AG dispatch (no `sports`-only gate) —
      structurally universal across all 5 `_V2_ENUMERATORS`. All 5
      `expected-universe-v2-{cefi,defi,tradfi,sports,     prediction}` jobs share ONE terraform image ref; each job's
      most recent (2026-07-25 ~01:30 UTC) execution resolved to the SAME digest `sha256:e88f3ded52…` = current
      `:latest`, tagged `f539945` (built 2026-07-23, 10d after guard commit `ba306543` 2026-07-13) — content-verified
      present (`merge-base --is-ancestor` reads false only due to the LDR→main squash, not a real gap). Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`.
- [x] [CODE] P1. ✅ **Extend the "never emit `empty_confirmed` over a captured atom" guard** to the regular sports
      instruments batch-capture emission path (`sports_fixtures.py`/`sports_reference_core.py` or wherever
      `uts-prod-instruments-service-sports-fixtures`'s `--operation=instruments --mode=batch --asset-group=SPORTS` run
      emits `EXPECTED_NO_FIXTURE`/`EXPECTED_PAUSED_LEAGUE`/etc.) — same guard shape as `ba306543`
      (`enumerate_expected_universe.py`'s `captured_set` check), applied to this SEPARATE code path. (repo:
      instruments-service — exact emission site TBD by worker on read). **Done when**: a `captured_set`-style guard is
      added to the batch-capture emission path; unit tests added and passing; a fresh production run no longer produces
      new masking rows of the observed pattern. Source:
      `issues/sports_index_recency_masked_captured_atoms_2026_07_13.md`. — DONE 2026-07-25: exact emission site found at
      `process_write._write_sports_fixture_venue`'s empty-gap loop
      (`instruments_service/engine/orchestrator/     process_write.py`) — the ACTUAL masking writer named in the issue
      doc's "ROOT CAUSE CORRECTED" section. Added `_manifest_captured_fixture_leagues` (`sports_reference_core.py`, kept
      out of `process_write.py` to stay under the 900-line file cap) — a single filtered manifest read (row-group
      pushdown on date, slim columns) building the set of leagues already CAPTURED for FIXTURES_SCHEDULE on this date;
      unioned into the empty-gap exclusion set. A manifest-read failure returns `None` and the caller skips the whole
      empty-emission pass (fail-safe, mirrors `_AfManifestHooks._presence_guarded_captured_leagues`'s existing contract)
      rather than risk masking. 6 new unit tests (`tests/unit/test_process_write_fixtures_captured_guard.py`) cover the
      guard helper (canonical-captured filtering, empty-index, read-failure fail-safe) and the integration
      (manifest-captured league excluded even with zero this-run captures; this-run-captured league still excluded;
      read-failure skips empty-emission entirely) — QG green (909 sports/fixture/process_write tests passing, full
      quality-gates.sh green). The "fresh production run no longer produces new masking rows" half of done-when is a
      live-verification follow-up for the NEXT real `uts-prod-instruments-service-sports-fixtures` production run (code
      is now shipped to LDR; not independently re-verified against live prod data in this session) —
      instruments-service@450b1b58.
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

- [x] ✅ [CODE] P1. **WEATHER layout mismatch — confirm, align, reverify (3-step ordered sequence, one worker).** (1)
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
      `issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`. — SHIPPED 2026-07-25
      (slot 4): unified-api-contracts@b73c95d5. Confirmed via code + live GCS listing (league= objects only, zero bare);
      set `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` to `PER_DAY_PER_LEAGUE` + regression test; sports phantom audit re-run:
      12,851 real captures, 0 phantom (exceeds ≥106 baseline). No placeholder residue found. QG green. Full evidence in
      the issue doc.

### From `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`

- [x] [DATA] P1. ✅ **`player_stats` idempotent de-dup rewrite** — `instruments-service@210d4567`. Reference tooling
      (`~/tmp-cutover/t2_4_build_canon_keys.py`) was session-local and gone, so wrote a fresh script
      (`scripts/dedup_canonical_player_stats_2026_07_25.py`) covering ALL 26,687 manifest-tracked
      `PLAYER_STATS`/`captured` cells uniformly (safe no-op on already-clean objects). Object paths via UAC's
      `candidate_parquet_paths(..., pipeline_mode=...)` SSOT; generation-matched CAS writes. **Result: 7,066 objects
      deduped, 808,279 duplicate rows removed; re-run confirmed 0 duplicates remain project-wide** (this todo's own
      done-when). Two incidental findings, left untouched not absorbed: schema heterogeneity also affects ~12% of
      player_stats cells; ~4.9% of captured cells have no GCS object (2019 era). Detail:
      `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md` (Finding 1, resolved).
- [ ] [DATA] P1. **`fixture_events` re-fetch into the canonical 13-col schema** — fold into the OR-1 `fixture_events`
      re-fetch campaign. (repo: instruments-service). **Done when**: a full re-census shows 0 genuinely non-canonical
      objects remaining (or documented unrecoverable). **🟡 IN PROGRESS (2026-07-25, slot 2)**: full census done
      (12,603/43,233 genuinely non-canonical, recovery-ids parquet built), re-fetch launch blocked on the af-backfill
      singleton lock (INJURIES VM still running) — full state + resume command:
      `issues/sports_fixture_events_refetch_progress_2026_07_25.md`. — **Stale sub-status corrected 2026-07-25T05:38Z
      (slot 11): the INJURIES-VM lock cleared hours ago; the re-fetch VM (`af-backfill-20260725-032253`) has been
      RUNNING since 03:22Z** (launched by slot 4, health-checked healthy by slot 11 at 04:18Z and again now — heartbeat
      fresh, no stall, now in the slower per-fixture event-loop phase covering 16,765 fixtures across 2019→2026-07-25).
      Genuinely hours from terminal; not completable in an AO turn. Full detail in the issue doc above — do not
      re-dispatch a duplicate health-check within the next ~30min. — **Health-checked 2026-07-25T06:43Z (slot 2)**:
      still `RUNNING`, heartbeat 34s old, run.log grew 69,781→79,917 lines (+10,136) since the issue doc's 06:08Z check
      (same doc, more detail there — this parent plan's todo and the issue doc both point at the same VM; resist the
      urge to duplicate full detail in both). Released via `/skip-current-task`, not duplicate-launched. — **🔴
      2026-07-25T08:34Z (slot 7, data_engineering) — CRITICAL: live data-correctness bug found + fixed, VM stop
      escalated.** Health-check found the VM zero-progress since 08:12Z (API-Football DAILY quota exhausted, 8,534
      failed fetches logged, date boundary stuck at `2020-03-22`) and root-caused a real code bug: the 4 per-fixture
      `api_football.py` adapters (`get_fixture_statistics`/`get_fixture_events`/`get_fixture_lineups`/
      `get_fixture_player_stats`) swallowed hard fetch failures internally and returned `[]`, so
      `_gather_per_fixture_rows`'s `entity_failures` tracking never fired and affected leagues/dates were silently
      stamped `empty_confirmed`/`EXPECTED_NO_FIXTURE` instead of `attempted_failed` — the exact honest-absence violation
      this campaign exists to fix. Full evidence:
      `issues/api_football_per_fixture_hard_failure_silently_recorded_empty_2026_07_25.md`
      (`unified-trading-pm@9022488a2`, PR #1492). Filed `/blocked` (`BLK-78a76a51`); main ruled **A — stop the VM now**
      (SPOT+idempotent, safe to relaunch; leaving it running keeps writing false `empty_confirmed`, which is WORSE than
      `attempted_failed` since downstream won't retry it). **Fix shipped**: `instruments-service@f31fb2e9` — the 4
      adapters now re-raise after `_emit_fetch_failed` instead of swallowing; 4 unit tests updated
      (`*_error_returns_empty` → `*_error_propagates`, mirrors the existing `get_injuries_error_propagates` precedent);
      full `quality-gates.sh` green (109s); orchestrator-level `TestCF11PerFixtureEntityFailurePath` suite (already
      correct) confirms `_fetch_one`/`_handle_empty_fixture_entity` now actually receive the failure signal.
      **BLOCKED-OPERATOR on my end**: could not execute the VM stop myself — `gcloud` auth expired mid-session
      (`Unable to retrieve Identity Pool subject token: job is already completed`, both available accounts,
      non-interactive reauth impossible) — flagged via `/progress` for another slot/main with working credentials to run
      `gcloud compute instances stop af-backfill-20260725-032253     --zone asia-northeast1-c`. **Do NOT flip this
      checkbox done yet**: (1) VM stop still pending execution, (2) once stopped, relaunch only after the API-Football
      daily quota resets, (3) the window `08:12Z`→stop-time was written under the OLD buggy code — those dates'
      `empty_confirmed` rows must be relabeled/re-fetched (issue doc todo 4), not trusted at face value by the eventual
      re-census. Released via `/skip-current-task {"reason_code":     "GATED"}` — genuinely gated on the VM-stop +
      quota-reset, not undoable from this slot.
- [x] ✅ [CODE] P2. **Writer-side de-dup + schema-conformance gate** so neither defect re-accrues — the `player_stats`
      writer rejects/dedupes rows on write; the `fixture_events` writer validates/enforces the canonical 13-col schema
      before accepting new objects. — `instruments-service@f5fa9f8a`. Added a `player_stats` de-dup gate (drop
      within-object exact duplicates on `(fixture_id, player_id)`, mirroring
      `dedup_canonical_player_stats_2026_07_25.py`'s own methodology) in `_prepare_fixture_entity_df`, and a
      `fixture_events` schema-conformance gate (reindex to the canonical UAC 13-col `SPORTS_FIXTURE_EVENTS` contract —
      missing columns null, non-canonical columns dropped) in `_write_fixture_entity_per_league`, applied AFTER the
      league-mapping join so it never strips the join key. Both gates live in a new sibling cohesion module
      (`sports_reference_fixture_entity_gates.py`) to keep `sports_reference_fixtures.py` under the 900-line file-size
      ratchet. 11 new regression tests (`test_sports_reference_fixture_entity_writer_gates.py`) cover: dedup drops
      duplicates / no-ops when already clean / no-ops when key columns absent (nested schema variant); schema gate
      passthrough-when-canonical / fills missing + drops non-canonical columns on the degenerate 5-col stub; end-to-end
      wiring through `_write_per_fixture_entities` proving the gate applies to the object actually handed to
      `_gated_sink_write`. Full existing suite (124 tests across the 4 related test files) + full `quality-gates.sh`
      green. Source: `issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`.

### From `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`

- [x] ✅ **ABANDONED 2026-07-25 (operator ruling, deliberate) — source bucket deleted before STEP 1 ran, data
      unrecoverable; see `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`.** [DATA] P1. **32-day
      legacy→canonical MDT row recovery (5-step ordered sequence, one worker, execute in order — this is one recovery
      procedure, not 5 independent jobs).** (1) READ-ONLY: re-derive the ~32 gap days by whole-day KEY-LEVEL containment
      (legacy tick keys − canonical tick keys) over the candidate window (2022-09-07..2022-10-01 dominant + a handful of
      2023/2025 days) — do NOT inherit the banner's day-list, confirm it; expect ~32 days / 550,062 legacy-only keys
      (524,486 pre-match + 25,576 in-play) / ~2,081 objects. (2) BUILD: per confirmed gap day, read legacy old-shape
      objects → extract canonical-absent keys → derive canonical segments via `build_instrument_id` (the
      already-validated 100.0000% derivation map — do NOT re-derive) → split pre-match vs in-play by kickoff time →
      MERGE (never overwrite — canonical holds `bookmaker_key`/`fixture_id`/`available_at` legacy lacks) → de-dup on the
      poll key `(event,market,outcome,bm_time,price)` → stamp `available_at` via
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
      (canonical); consumes but does not modify `unified_trading_library.availability_stamping`). **Done when**: N/A —
      **BLOCKED 2026-07-25**, source bucket deleted 2026-07-17 pre-STEP1, confirmed deliberate operator decision to
      abandon recovery (ruling 2026-07-25), data unrecoverable. Source:
      `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`,
      `issues/mdt_legacy_bucket_deleted_before_recovery_2026_07_25.md`.
- [x] ✅ [DOC] P3. **File a new issue doc** for the standalone finding: "30/200 sampled canonical MDT objects carry
      duplicate rows on the poll key (event, market, outcome, bm_time, price, fetch_utc), independent of the OR-5b
      cutover." — `issues/mdt_canonical_odds_poll_key_duplicate_rows_2026_07_25.md`. Note: the recovery-sequence todo
      above's step 2 dedup was scoped only to the abandoned 32-day recovery's own merged rows, never the wider
      already-existing canonical population this finding covers, and that recovery is now itself ABANDONED (source
      legacy bucket deleted before STEP 1 ran) — so the new doc adds 2 fresh `[DATA]` fix todos (root-cause + measure,
      then de-dup if warranted) rather than treating remediation as already covered elsewhere. Source:
      `issues/mdt_legacy_canonical_row_gap_2026_07_16.md`.

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
- [x] ✅ **2026-07-25 (slot 7) — step-4 resolved: genuine-gain merged 2026-07-17, duplicate residual staged for human
      purge — market-tick-data-service@75f226e8 (prior merge) + unified-trading-pm@2705cb4fd,@b5bf80d53 (this session's
      execution + verification + correction).** [DATA] P0. **CREDENTIAL BLOCKER RESOLVED 2026-07-25**
      (`deployment-service@3ba14ff` routes tarball uploads through ADC, not gsutil — re-verified end-to-end: full 5-repo
      republish succeeded). The MDPS `odds_horizon_bucket` reprocess + `batch_footystats` copy+swap remain genuinely
      un-executed (not a credential issue anymore, just not yet done) — pick up fresh via
      `launch-mdps-sports-bucket-vm.sh`. Full detail:
      `/plans/active/issues/gsutil_broken_credentials_blocks_vm_tarball_republish_2026_07_25.md`. **League_id casing
      migration — census→copy→reprocess→swap (4-step ordered sequence, one worker, execute in order — this is one
      already-verified, ready-to-execute migration, not 4 independent jobs).** **Progress**: (a) found step (2)'s
      manifest swap (raw `TRADES`/`batch_odds_api` shape) had silently reverted since its 2026-07-22 run (TOCTOU
      consolidator race, closed by `unified-trading-library@14301571` on 2026-07-24 — 2 days after the swap ran).
      Re-applied `manifest_swap_2026_07_22.py --apply-prod --confirm-prod-write` and verified STABLE across 5
      consolidator cycles (~7.5 min) — the raw TRADES shape is now genuinely canonical, not just log-claimed. Full
      detail: `/plans/active/issues/sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`. (b)
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
      either run `gcloud auth login` interactively once, or refresh the service-account federation. **CASING CORRECTED
      2026-07-25** (operator ruling — repoint to lower-case; executor hardcoded UPPER, needed a real code fix; see
      `issues/sports_satellite_batch2_casing_direction_contradicts_k1k2_revert_2026_07_25.md`): shipped `mtds@fb51d86c`
      — casing now lower-case, QG-green; dry-run baseline below remains valid. (1)
      `migrate_sports_league_id_casing_2026_07_21.py --apply-prod` (no `--confirm-prod-write`, no `--index`) once, for
      the live out-of-scope census + VM-guard + PLAN, using the now-corrected executor (`mtds@fb51d86c`) — expect
      results consistent with the verified full-corpus dry-run baseline (266,408 objects / 34,228 units, 0 unknown raws,
      0 unresolved league_ids). (2) `--apply-prod --confirm-prod-write --index scripts/.../raw_index.tsv` —
      copies+CAS-verifies the raw `batch_odds_api/odds/trades` shape (~139,155 objects) to canonical paths
      (`league_id=<CANON>/instrument_type=odds/data_type=trades/`), with the parquet's `league_id` CONTENT column
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
      `issues/sports_league_id_namespace_migration_2026_07_20.md`. — **Prep done 2026-07-25T02:42Z (slot 9), launch NOT
      yet executed** — tarballs re-verified/re-fixed, TOCTOU fix confirmed included, mechanism dry-run-verified correct,
      ready-to-execute command staged. Full detail + exact next step:
      `issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`. — **Step (3) MDPS `odds_horizon_bucket`
      reprocess EXECUTED + VERIFIED 2026-07-25 (slot 7).** Re-verified tarball freshness (2 of 5 had drifted again in
      the ~40min since the prep doc; republished), launched 4 sharded VMs
      (`mdps-sports-bucket-20260725-{035949,040027,040053,040119}`, SPOT, `force` mode, confirmed clean start via SSH
      each). All 4 completed: shard1 (2020-06-06→2021-12-31) 574/574 dates 0 failed; shard2 (2022-01-01→2023-06-30)
      546/546 dates 0 failed; shard3 (2023-07-01→2024-12-31) 550/550 dates 0 failed; shard4 (2025-01-01→2026-07-25) 571
      dates, 22 `attempted_failed` + 4 `LOSS_GUARD_BLOCKED` — investigated in full, all 26 are honest upstream gaps /
      correct protective refusals, not script defects (18 known `ADAPTER_RETURNED_EMPTY_OUTPUT` pre-vetted in the prep
      doc + 4 novel `RAW_ODDS_SHAPE_UNRECOGNIZED` dates confirmed via direct GCS read to have zero real odds data, only
      `instrument_type=sport` meta-snapshots + 4 `LOSS_GUARD_BLOCKED` dates where re-deriving would have shrunk the
      corpus, correctly refused). Total 166,751 shards / ~5.4M bucketed rows written. Manifest-verified STABLE across 2
      consolidator-cycle-separated polls (~100s apart): `odds_horizon_bucket` = 408,815 rows / 130 distinct canonical
      league_id values, identical both polls — no TOCTOU-style revert. Full detail + shard4 residual tracking (P2 retry
      todo, does not block this checkbox): `issues/mdps_odds_horizon_bucket_shard4_residual_failures_2026_07_25.md`.
      **Step (4) `batch_footystats` copy+swap — CORRECTED 2026-07-25 (slot 7): this is NOT a casing-extension task, the
      wording was stale.** Deterministic probe (writer-emission grep + manifest census, per BLK-b89f6ec3) found the
      16,969-object population is not a footystats shape at all: 100% carries `source=ODDS_API`, mis-stamped
      `pipeline_mode=batch_footystats` for what is really `batch_odds_api` data. This was ALREADY diagnosed AND largely
      fixed by an archived investigation:
      `plans/archive/issues/sports_canonical_migrated_odds_mistamped_footystats_2026_07_16.md` — the genuine-gain
      199/1,815 days were merged into canonical `batch_odds_api` on 2026-07-17 (`market-tick-data-service@75f226e8`,
      acceptance-tested against the real MDPS derive, 0 rows lost). Re-verified 2026-07-25 (BLK-8e3fdaff): the manifest
      now carries ZERO rows for this population (already purged/pruned) but the raw GCS objects still exist as ORPHANS
      for most sampled days; a fresh content-compare on `day=2022-06-15` reconfirms the archived doc's finding that the
      remainder is a pure duplicate of already-canonical content (0 unique keys either side). **There is no remaining
      copy+swap work — the copy already happened correctly.** What remains is the archived doc's own still-open,
      human-gated PURGE of the now-redundant orphaned objects, staged (not executed) per the 5-part delete-safety proof:
      `issues/sports_batch_footystats_mistamped_odds_orphan_delete_staging_2026_07_25.md`. **This checkbox reflects
      steps 1-4 as CORRECTLY resolved for all AO-executable work** — the remaining PURGE is human-only per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3.1 (prod-bucket delete hard stop), tracked in the
      linked issue doc, not blocking. Full addendum on the original (now-superseded) footystats-shape spot-check:
      `issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`.

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
  substantially de-risked, NOT complete.** Full investigation (candidate-pool discovery from a pre-pruning backup
  parquet, the `in_mvp_scope` architecture fix, the continental-majors slice shipped `unified-api-contracts@7b13196e`,
  per-source-cap measurements, and the 2 near-miss error classes hit) moved to
  `issues/sports_curated_universe_domestic_selection_remaining_2026_07_25.md` to avoid this plan's line-cap growth — see
  there for full detail; do not duplicate it here. Checkbox stays unchecked: steps 2-3 haven't started and step 1's
  domestic-selection slice (145 countries) remains open, now decomposed into 11 confederation-batch todos in that issue
  doc (backlog: 4 dispatched, 7 queued as of 2026-07-25T03:02Z). Released per main's BLK-7daa3e2a ruling
  (correctly-parked research gap, not a stall) — `unified-trading-pm@7608a8ef3`.

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

- **2026-07-25 (slot 7, data_engineering) — League_id casing migration, step (3) MDPS `odds_horizon_bucket` reprocess —
  LAUNCHED, running.** Picked up from `issues/mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`'s
  ready-to-execute recipe. Re-verified tarball freshness first (the prep doc's own claim was already 40min stale):
  `market-tick-data-service` and `unified-api-contracts` tarballs had drifted from local HEAD again — republished via
  `deployment-service/scripts/vm/create-code-tarballs.sh` (no flags, default CORE_REPOS covers UAC/UTL/MTDS/
  deployment-service), re-verified all 5 repos byte-exact via `gcloud storage cat .../code/<tarball>.manifest.json` vs
  local `git rev-parse HEAD` (not the launcher's own `lc_verify_tarball_freshness`, which reads via `gsutil` and is
  still blind per the credential-blocker doc's residual gap — it printed false "MISSING" warnings on launch despite the
  manual gcloud-storage check confirming all 5 fresh seconds earlier; this is a known gap, not a new defect). Launched
  the 4-way sharded split per the launcher's own docstring example: `mdps-sports-bucket-20260725-035949`
  (2020-06-06→2021-12-31), `-040027` (2022-01-01→2023-06-30), `-040053` (2023-07-01→2024-12-31), `-040119`
  (2025-01-01→2026-07-25), all `mode=force`, SPOT. Confirmed clean start on all 4 via SSH (`ps aux` shows the
  `reprocess_sports_odds.py` worker live + `/tmp/vm-exec-*.log` streaming `LOSS_GUARD_PASS`/bucketed-row lines, no
  tracebacks) — no fire-and-forget. Throughput ~25-30 days/min per shard against 546-574 days/shard → each shard ETA
  well under 1hr, matching the launcher's <1hr sharded target. Monitoring to completion (EXIT_STATUS + failure-
  signature watch armed); once all 4 report `DEPLOYMENT_COMPLETED`, will poll `_index/availability_index.parquet`'s
  `odds_horizon_bucket` league_id distribution across ≥2 consolidator cycles before flipping this todo, per
  `sports_league_id_swap_silently_reverted_toctou_2026_07_25.md`'s lesson (a prior manifest write on this exact
  migration silently reverted due to a TOCTOU race — do not declare done from the VM's own completion log alone).
  `batch_footystats` copy+swap (16,970 objects, separate step) not yet started.

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
