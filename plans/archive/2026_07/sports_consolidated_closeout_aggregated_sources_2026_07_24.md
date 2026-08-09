---
doc_type: plan
title: Sports consolidated close-out — aggregated source docs (discoverability index)
summary: >-
  The "Aggregated source docs" discoverability index extracted verbatim from
  sports_consolidated_closeout_2026_07_19.md's 2026-07-24 line-cap trim (2nd pass). Lists every other sports-relevant
  plan/issue with a repo-root-relative path and a condensed digest of its currently-open todos (bold, non-checkbox
  markers -- see task_template.md finding H -- so this stays structurally un-ingestable by AO's regen_backlog parser
  even though this doc itself is LOCAL/not dispatched). Read this alongside the parent for full context on what's open
  across the sports asset group; the parent's own native Tracks (F/C/S/E/O/H/V/K/D/X/S2) are NOT duplicated here.
status:
  complete # (was: active) 2026-07-28 archival sweep: this doc's own single [DOC] P3 todo (verify the digest is
  # accurate) is done; verified zero open todos of its own
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, discoverability, index, aggregated-source-docs, plan-hygiene]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
last_updated: "2026-07-24"
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Plan line-cap hygiene remediation, 2nd pass, /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md -- operator
  ruling 2026-07-24 removed the umbrella:true exemption entirely (flat 1000L hard cap, no exceptions).
assigned_role: data_engineering
drift_direction: advance-code
---

> **🗄️ ARCHIVED 2026-07-28 (plan-hygiene sweep)** — this doc's own scope (a verified-accurate discoverability digest) is
> complete; it does not represent the sports asset group being done. Per
> `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

# Sports consolidated close-out — aggregated source docs (discoverability index)

> Extracted verbatim from `/plans/active/sports_consolidated_closeout_2026_07_19.md`'s 2026-07-24 line-cap trim. Nothing
> summarized or dropped.

## Aggregated source docs (referenced, not duplicated — every other active sports + sports-touching plan/issue)

> Completeness check: `grep -l '^asset_group:.*sports' plans/active/*.md plans/active/issues/*.md` (run 2026-07-24),
> cross-referenced against this doc's own `related:` list and `ls plans/active/ | grep -i sports`. **5 fold-in plans are
> intentionally OMITTED** — `sports_manifest_canonicalisation_2026_06_01.md`,
> `sports_p2_history_apifootball_2015_to_present_2026_06_27.md`, `sports_p2_features_history_to_ml_ready_2026_06_27.md`
> (all 3 archived to `plans/archive/2026_07/`), plus `sports_pipeline_to_100pct_golden_window_first_2026_06_27.md` and
> `sports_odds_exchange_fixed_fork_2026_07_18.md` (still in `plans/active/` but `status: superseded`) — all 5 carry
> `superseded_by: sports_consolidated_closeout_2026_07_19.md`; their live content is already absorbed into Track C/S2
> above, so re-listing them here would be pure duplication. Only unchecked `- [ ]` top-level todos are counted below;
> `status: resolved` issue docs with residual unchecked boxes are listed as-is (resolved ≠ the file has zero open
> checkboxes — flagged per-doc).

- **Entry-point / progress-log companions (ARCHIVED 2026-07-24)**:
  - [`plans/archive/2026_07/sports_master_closeout_2026_07_21.md`](/plans/archive/2026_07/sports_master_closeout_2026_07_21.md)
    — was the companion entry-point doc (`entry_point_for: [sports_consolidated_closeout_2026_07_19]`); archived
    2026-07-24 (`status: complete` / `nature: record`, `superseded_by: sports_consolidated_closeout_2026_07_19`) once
    its 6 open todos moved here. Disposition: league_id-relocation manifest-swap+DELETE → folded into the "Operator
    decisions — ANSWERED" section above (new DELETE todo, 5-part-proof checklist preserved); cross-AG bleed cleanup →
    already represented by the "RE-TRIAGE ROUND 3" todo above (no new content needed, that item is more current);
    twin-delete phantom manifest rows → Track S; peripheral-bucket vocabulary contamination, ship-the-2-parked-changes,
    and the QG-structural-finding issue-doc todo → new Track X fold-in bullets. Everything else in the archived doc (the
    2020-06 floor narrative, the landmine resolution, the issue-doc catalogue, the enforcement-surface checklist) is
    preserved there as historical record.
  - [`plans/archive/2026_07/sports_master_closeout_progress_log_2026_07_24.md`](/plans/archive/2026_07/sports_master_closeout_progress_log_2026_07_24.md)
    — archived alongside its parent (0 open todos, pure history).

- **Audit / doc-health reconciliation**:
  - [`plans/archive/2026_07/sports_consolidated_audit_2026_07_19.md`](/plans/archive/2026_07/sports_consolidated_audit_2026_07_19.md)
    — 0 open todos (the 6-agent audit that fed this closeout; fully absorbed).
  - [`plans/active/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md`](/plans/archive/issues/sports_plan_and_docs_reconcile_findings_2026_07_24.md)
    (13 open — doc-corpus self-consistency findings):
    - **[DOC] P0.** `authoritative_for` collision, code-verified (`sports-batch-live.md` in-play claim)
    - **[DOC] P1.** `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` is not a clean auto-archive
    - **[DOC] P1.** `sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`'s re-triage undercounts open work
    - **[DOC] P1.** `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` falsely claimed
    - **[DOC] P1.** `sports-gcs-path-ssot.md`'s SPORTS-CANON ALIGNMENT note frames legacy no-env stale
    - **[DOC] P1.** `kelly.md`/`staking-methods.md` (archived pre-v2 strategy docs) missing 2 of 9 sibling refs
    - **[DOC] P1.** `unified-sports-reference-interface.yaml` (archived audit yaml) still says `status: "active"`
    - +6 more P2 (data-status catalog claims, `runtime-deployment-topology.md` USEI self-contradiction,
      `sports-2020-06-data-floor.md`/`sports-data-types-catalog.md` enum-value drift) — see file for the rest.

- **Fixtures / catalogue / reference universe**:
  - [`plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md`](/plans/active/sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md)
    (11 open):
    - **[DATA] P0.** Eliminate the bare/legacy dual-layout
    - **[DATA] P0.** Retention floor = the existing per-source genesis registry, not a blanket 2015 delete
    - **[DATA] P0.** Odds-granularity nice-to-have watch-item
    - **[DATA] P0.** 2 out-of-universe numeric `league=` dirs (`14231`/`315`) — fold into hybrid residual-drop
    - **[DATA] P0.** 94-league enrichment backfill (genuine missing enrichment)
    - **[CODE] P1.** UAC canonical registry build/refine (league/cup canonical + ids + is-cup + country + season)
    - **[DATA] P1.** Define the curated ~300-league reference set
    - **[DATA] P1.** Legacy-delete (E8) — `--drop-stale` is an unimplemented stub
    - **[DATA] P1.** Enrichment backfill 2015→present for the 94 leagues
    - +2 more P2 (curated-universe backfill, drop residual out-of-curated rows) — see file for the rest.
  - [`plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md`](/plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md)
    (4 open):
    - **[DATA] P2.** Design the manifest schema for fixture-grain (operator-confirmed 2026-07-14)
    - **[DATA] P2.** Write the fixture-grain catalog build implementation
    - **[DATA] P3.** Extend the catalog build to fixture-grain
    - **[REVIEW] P3.** Post-decision codex alignment check if the manifest/catalog grain changes
  - [`plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md`](/plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md)
    (3 open):
    - **[BACKEND] P2.** Switch `deployment-api/services/fixtures_browser.py` to the single catalogue
    - **[DATA] P2.** Freshness caveat — catalogue regenerated by rollup job (decide before/with P10-B)
    - **[UI] P3.** `FixturesBrowser.tsx` window note + span-cap warning update (once P10-B backend lands)
  - [`plans/active/data_completion_sports_2026_07_24.md`](/plans/active/data_completion_sports_2026_07_24.md) (4 open):
    - **[SCRIPT] P1.** Run the ramp-to-429 calibration probe on an ephemeral VM (operator-gated)
    - **[DATA] P1.** Post-backfill relabel (after the 6 running backfill VMs finish)
    - **[SCRIPT] P2.** Relaunch features-sfi-progressive (code fix shipped, SPORTS re-run pending)
    - **[DATA] P2.** Enrichment completed clean at ~30-34% honest, ~70k unattempted/entity = API-Football daily-cap
  - [`plans/archive/2026_07/data_completion_sports_history_2026_07_24.md`](/plans/archive/2026_07/data_completion_sports_history_2026_07_24.md)
    — 0 open todos (shipped-history fork from `data_completion_sports_2026_07_24.md`; record-only, status: complete).
  - [`plans/active/sports_live_availability_and_source_latency_2026_07_24.md`](/plans/archive/2026_08/sports_live_availability_and_source_latency_2026_07_24.md)
    (2 open, added to this index 2026-07-24 — was missing): Live-ODDS quota/book-set decision
    (BLOCKED-OPERATOR-DECISION)
    - re-pin the 5 `source_data_latency.py` p95-lag constants from empirical `latency_observations` data (the ~2-week
      accrual gate has now passed, actionable).

- **Odds / feature-naming / coverage**:
  - [`plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`](/plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md)
    — **corrected 2026-07-24, was wrongly "0 open"** (4 open): UAC `LEAGUE_ID_TO_TIER` mapping, extend
    `EXPECTED_BOOKMAKER_MARKET_SETS` to 28 unmapped league_ids, fix `fixture_id=NULL` propagation in the odds_api
    backfill, plus a 4th P1 item — see the doc's own P1 section (lines 205-223) for full detail.
  - [`plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md`](/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md)
    (8 open):
    - **[DATA] P1.** New compute (not a rename) — per-bookmaker raw decimal-odds retention
    - **[DATA] P1.** Update UAC `OddsFeaturesMixin`/`SportsFeatureVector` fields to the chosen names
    - **[DATA] P2.** Migrate `odds_columns.py`'s `ODDS_COLUMNS` + odds-features
    - **[BACKEND] P2.** Close the silent-agnostic gap in `SportsFeatureLoaderMixin`
    - **[BACKEND] P2.** Migrate `SportsValueBettingEngine` + `SportsArbDutchingEngine`
    - **[BACKEND] P2.** Migrate the legacy `sports_feature_subscriber.py`
    - **[REVIEW] P3.** FSS-output ↔ ml-service-input ↔ strategy-service-input parity test (after todos 2-6)
    - **[REVIEW] P3.** Cross-reference against the "wire sports end-to-end" plan
  - [`plans/active/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md`](/plans/archive/issues/sports_odds_ownership_registry_split_brain_and_bogus_api_football_denominator_2026_07_15.md)
    (2 open):
    - **[DOCS] P3.** Codex: state odds=MTDS-domain (footystats exception in IS is PREDICTIONS, not ODDS)
    - **[VERIFY] P2.** Reconcile the post-07-13 rebuild delta (`PLAYER_VALUES` −10,934, `ODDS` −3,180 cells)
  - [`plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md`](/plans/active/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md)
    (3 open):
    - **[CODE] P1.** Stop stale/zombie ticks at bucket assignment (fix locus: MDPS, not MTDS raw ingestion)
    - **[DATA] P2.** MTDS: sweep for the extent of the contamination
    - **[DATA] P3.** Re-run `verify_ml_readiness.py` after the P1/P2 fix
  - [`plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md`](/plans/active/issues/sports_halftime_odds_sfi_vs_inplay_2026_07_16.md)
    — `status: resolved` but 5 residual unchecked todos:
    - **[CODE] P1.** `_apply_ht_odds_pit_gate`'s default-cutoff branch unreachable in production
    - **[DATA] P1.** The blank-`fixture_id` raw generation is still being written — fix upstream writer
    - **[DATA] P1.** Re-calibrate `verify_ml_readiness.py`'s 95% non-NULL threshold against the honest matrix
    - **[DATA] P1.** Reconcile the market-data-sports manifest for the 2,436 deleted T-0 shards
    - **[ML] P2.** Retrain the CLV models after the ODDS_FEATURES recompute
  - [`plans/active/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md`](/plans/archive/sports_mtds_odds_trades_index_correctness_followup_2026_07_24.md)
    (2 open, both P0):
    - **[DATA] P0.** T2.9 — MDT `(sports, odds, trades)` schema contract drifted from reality (BIG FINDING)
    - **[DATA] P0.** T2.10 — 47,253 phantom `api_football × trades` `captured` rows in the MDT canonical index
  - [`plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md`](/plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md)
    — 0 open todos. **DECIDED 2026-07-23**: naming scheme canonicalized per
    [`sports_odds_feature_naming_canonicalization_2026_07_21.md`](/plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md)
    (Option A, UAC-as-SSOT); scoped 3-repo migration in flight — do not re-litigate.
  - [`plans/active/issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`](/plans/archive/issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md)
    — 0 open todos.
  - [`plans/active/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md`](/plans/archive/issues/sports_odds_capture_pipeline_scheduling_status_unknown_2026_07_23.md)
    — 0 open todos.

- **Live-mode / execution / arb readiness**:
  - [`plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md`](/plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md)
    (6 open, all P3):
    - **[OPERATOR] P3.** Decide whether to pursue a live sports-odds ingestion path at all
    - **[INFRA] P3.** Once P3-1 is a yes: scope the MTDS live-odds connector
    - **[INFRA] P3.** Once the MTDS connector lands: build `launch-mtds-live-sports.sh`
    - **[DATA] P3.** Build the FSS live handler for the sports feature family (currently batch-only)
    - **[REVIEW] P3.** Run a sports archetype through the CLI-primary promote workflow
    - **[OPERATOR] P3.** Final explicit go-ahead to flip sports (and prediction) live
  - [`plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md`](/plans/archive/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md`](/plans/archive/2026_08/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md)
    (8 open, all P3 — design-spec questions, not yet implementable):
    - **[DESIGN] P3.** Define the decay-window STATISTIC precisely
    - **[DESIGN] P3.** Define the WINDOW boundaries (signal-time to first-leg/last-leg fill)
    - **[DESIGN] P3.** Define the DATA SOURCE (signal-time odds snapshot)
    - **[DESIGN] P3.** Define the OUTPUT shape (decay curve, edge_bps_remaining vs elapsed_ms)
    - **[DESIGN] P3.** Define the GATE STATISTIC
    - **[DESIGN] P3.** Define the MINIMUM SAMPLE SIZE + soak duration
    - **[DESIGN] P3.** Define the PASS/FAIL threshold VALUE and where it lives
    - **[DESIGN] P3.** Define the ACCEPTANCE TEST for this design
  - [`plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md`](/plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md)
    (5 open, all P3):
    - **[BACKEND] P3.** Add `run_sports_backtest(args, config, config_path) -> int`
    - **[BACKEND] P3.** Wire a data source (reuse the Group-B fixture dataset)
    - **[DESIGN] P3.** Resolve `SportsMatchingEngine` vs `L0Matcher` duplication
    - **[SCRIPT] P3.** Add a hermetic test asserting a non-trivial `execution_alpha_bps`
    - **[DESIGN] P3.** Once the harness runs, decide its place in routine backtest-groups verification

- **Legacy cutover / manifest / league_id / data correctness**:
  - [`plans/active/sports_legacy_bucket_cutover_2026_07_16.md`](/plans/archive/2026_07/sports_legacy_bucket_cutover_2026_07_16.md)
    — 0 open todos.
  - [`plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md`](/plans/archive/sports_legacy_cutover_closeout_tasks_2026_07_24.md)
    (2 open):
    - **[REVIEW] P1.** T6.7 — post-phase codex audit (HARD RULE)
    - **[INFRA] P2.** T6.8 — retire the one-offs + the dead knob + the false-progress tick
  - [`plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md`](/plans/active/issues/sports_league_id_namespace_migration_2026_07_20.md)
    — 0 open todos.
  - [`plans/active/issues/sports_legacy_canonical_row_gap_2026_07_16.md`](/plans/archive/issues/sports_legacy_canonical_row_gap_2026_07_16.md)
    — `status: resolved`, 0 open todos.
  - [`plans/active/issues/mdt_legacy_canonical_row_gap_2026_07_16.md`](/plans/archive/issues/mdt_legacy_canonical_row_gap_2026_07_16.md)
    — 0 open todos. ⚠️ near-duplicate name of `sports_legacy_canonical_row_gap_2026_07_16.md` above — not verified
    whether these are the same finding filed twice or genuinely distinct; flagging, not resolving.
  - [`plans/archive/issues/mdt_t2_6_league_case_duplicate_population_2026_07_16.md`](/plans/archive/issues/mdt_t2_6_league_case_duplicate_population_2026_07_16.md)
    — 0 open todos.
  - [`plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md`](/plans/archive/issues/sports_legacy_duplicate_triage_2026_07_22.md)
    (5 open):
    - **1. [OPERATOR] P1.** Rule on the 1,492 v2 pre-floor rows
    - **2. [DATA] P2.** Migrate-forward the 58 v2 post-floor rows (16 days) into canonical `entity=fixtures`
    - **3. [CODE] P2.** Repoint or retire the two flat-legacy readers
    - **4. [REVIEW] P3.** Rescan `migration_orphan_sweep_sports.py --bucket reference`
    - **5. [REVIEW] P3.** Cross-file the pending "MANIFEST prune" deferred task against `sports_master_closeout`
  - [`plans/archive/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md`](/plans/archive/issues/sports_is_manifest_eu_regression_overwrite_2026_06_29.md)
    — `status: resolved`, 1 residual:
    - **[VERIFY] P2.** BLOCKED-PREREQUISITES (2026-07-06, slot-6 planning) — re-run task 007
  - [`plans/active/issues/sports_manifest_read_staleness_budget_missing_2026_07_15.md`](/plans/archive/2026_08/sports_manifest_read_staleness_budget_missing_2026_07_15.md)
    (3 open):
    - **[DATA] P1.** Add `"sports": 1800` to `AG_STALENESS_BUDGET_SEC`
    - **[DATA] P1.** Mirror the same into `_AG_STALENESS_BUDGET_SEC`
    - **[DATA] P2.** Grep the fleet for scripts hardcoding `MANIFEST_CONSOLIDATED_STALENESS_SEC` for sports
  - [`plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md`](/plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md)
    (6 open):
    - **[DATA] P2.** Design a manifest-slice-based replacement for `check_api_football_dependency()`
    - **[DATA] P2.** New follow-up finding — `_build_fixture_league_map_from_gcs` gap (flagged not fixed)
    - **[DATA] P2.** Design a separate cached/batched fix for `sports_fixtures.py:356`
    - **[DATA] P2.** Share path-template constants between the real fixtures writer and this checker
    - **[VERIFY] P2.** Confirm real backfill speedup against a real multi-month/full-year run
    - **[DATA] P2.** (duplicate-worded) manifest-slice-based replacement todo — verify not a literal dupe in-file
  - [`plans/active/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md`](/plans/archive/issues/sports_t0_t1_dependency_gate_never_wired_2026_07_15.md)
    (1 open):
    - **[SCRIPT] P2.** Thread `date` through every T1 call site of `create_sports_reference_adapter()`
  - [`plans/active/sports_prelaunch_cf5_verify_residual_2026_07_24.md`](/plans/archive/2026_08/sports_prelaunch_cf5_verify_residual_2026_07_24.md)
    (2 open, both P1):
    - **[DATA] P1.** Sports CF-5 oracle relabel = zero — root-caused + fixed (code), preserved to a wip branch
    - **[DATA] P1.** Sports pre-launch-window corpus decision (C3, 10,345 objects — operator-gated)
  - [`plans/archive/issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md`](/plans/archive/issues/sports_pre_floor_fixtures_orphan_misclassification_2026_07_22.md)
    — **RESOLVED 2026-07-27** (archived; the 3-open listing below is a stale historical snapshot, kept for context):
    - **2. [OPERATOR] P1.** Disposition ruling needed on the 83,541 pre-floor `FIXTURES_SCHEDULE` rows — DONE
    - **3. [DATA] P2.** Once ruled, run the delete-safety protocol's 5-part proof + execute the wipe — DONE
    - **4. [REVIEW] P2.** Re-run `migration_orphan_sweep_sports.py --bucket reference --dry-run` after the wipe — DONE
  - [`plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md`](/plans/archive/2026_08/sports_index_recency_masked_captured_atoms_2026_07_13.md)
    (4 open):
    - **[INFRA] P1.** Redeploy the `expected-universe-v2-sports` Cloud Run job image
    - **[CODE] P1.** Extend the "never emit empty_confirmed over a captured atom" guard to regular sports instruments
    - **[DATA] P3.** Sweep other asset groups for the same seeder-over-captured pattern
    - **[INFRA] P3.** Downgrade, don't drop, the original "redeploy" todo
  - [`plans/active/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`](/plans/archive/issues/sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md)
    — `status: resolved`, 2 residual:
    - **[DATA] P0.** Re-run the targeted L6 manifest re-emission for the regressed cells
    - **[DATA] P1.** Forensics (open question) — what wrote pre-launch captured rows into the IS canonical
  - [`plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md`](/plans/archive/issues/cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md)
    (8 open, cross-AG with prediction):
    - **1. [DATA] P1.** Pin the true full count and composition of the bleed
    - **2. [BACKEND] P1.** Locate the writer that puts `asset_group=prediction` rows into the sports index
    - **3. [BACKEND] P1.** Fix the misattribution at the writer
    - **4. [DATA] P2.** Remediate the already-written bleed rows
    - **5. [DATA] P0.** Read the UTL manifest consolidator to confirm the actual mechanism
    - **6. [DATA] P0.** Check whether the round-2 remediation script ran
    - **7. [DATA] P0.** Confirm whether a consolidation cycle has run since the 2026-07-23 remediation
    - **8. [DATA] P0.** Once todos 5-7 pin the mechanism, re-run the remediation

- **Features layer / ML readiness / derived data**:
  - [`plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md`](/plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md)
    (73 open — 18 P0 / 40 P1 / 14 P2 / 1 P3, capped hard here given the scale; see file for the full list):
    - **[DIAG] P0.** Verify whether the round writer fix (instruments-service@19ae5890) is even reachable
    - **[OPS] P0.** Let the FIXTURES backfill run to completion (watchdog v4 keyed on `entity=fixtures_schedule`)
    - **[ASK] P0.** Operator decision on K1/K2 normalisation direction — K2 is BLOCKED on this
    - **[DATA] P0.** Rebuild the sports catalogue
    - **[CODE] P0.** Implement derive-then-fetch for round population (score date→round per league/season)
    - **[CODE] P0.** Repoint `SPORTS_FIXTURE_ENTITY` to `fixtures_schedule`
    - **[DATA] P0.** Sports features must be RE-RUN — every pre-cutover row was computed from the stale legacy frame
    - **[DATA] P0.** Corpus-wide `derived_features` re-run required (clean, replaces the stopped fleet)
    - +10 more P0 (staleness audits across ~9 stale-entity consumers, backfill pilot follow-through, full-corpus dry-run
      gating), +40 P1, +14 P2, +1 P3 — see file for the complete 73-item breakdown.
  - [`plans/archive/issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md`](/plans/archive/issues/sports_derived_features_fabricated_corpus_scope_2026_07_20.md)
    — 0 open todos, archived 2026-07-30 (`status: resolved`).
  - [`plans/active/issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md`](/plans/archive/issues/sports_derived_features_per_league_layout_unread_by_ml_loader_2026_07_14.md)
    — `status: resolved`, 2 residual:
    - **[DOC] P3.** Write the features-bucket path SSOT (codex/02-data)
    - **[DATA] P3.** instruments-service: `odds_api_team_mapping` coverage gap (found during the P2 fix)
  - [`plans/active/issues/sports_features_rerun_stopped_writing_2026_07_21.md`](/plans/archive/issues/sports_features_rerun_stopped_writing_2026_07_21.md)
    — `status: superseded`, excluded (0 open todos, folded forward into the findings-sweep doc above).
  - [`plans/active/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md`](/plans/archive/issues/sports_mdps_derived_odds_products_zero_prod_objects_2026_07_23.md)
    — `status: resolved`, 0 open todos.
  - [`plans/archive/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`](/plans/archive/issues/sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md)
    (3 open):
    - **1. [DATA] P1.** Confirm the writer's intended WEATHER layout is `PER_DAY_PER_LEAGUE`
    - **2. [CODE] P1.** Align `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` to match
    - **3. [DATA] P1.** After the fix, re-run the sports phantom audit and confirm WEATHER false positives drop
  - [`plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md`](/plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md)
    (1 open):
    - **[DATA] P2.** Precompute `mvp: bool` for sports/prediction (traced + designed, not yet implemented)
  - [`plans/active/issues/sports_reference_function_size_qg_regression_2026_07_16.md`](/plans/archive/issues/sports_reference_function_size_qg_regression_2026_07_16.md)
    — `status: resolved`, 3 residual:
    - **[BACKEND] P3.** Decompose `_AfManifestHooks.emit_empty_gaps_for_entity()` (89L → ≤50L)
    - **[SCRIPT] P3.** Root-cause why the size gate didn't block the introducing commit
    - **[SCRIPT] P3.** Re-run a full (non-sliced) `quality-gates.sh` and confirm phase 5

- **API-Football / source-adapter correctness**:
  - [`understat_bulk_download_backfill_2026_06_29.md`](/plans/archive/issues/understat_bulk_download_backfill_2026_06_29.md)
    — ✅ ARCHIVED 2026-07-27, `status: resolved`, all 11/11 §8 items done (605,368-row corpus re-verified 0
    attempted_failed / 0 expected_unattempted / 0 duplicate; final gap `deployment-api@b04c082`).
    - **[VERIFY] P1.** After backfill: re-evaluate the `understat-vm-xg-complete` gate against real captured shots.
  - [`plans/archive/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md`](/plans/archive/issues/api_football_backfill_chronological_scan_never_reaches_pending_tail_2026_07_18.md)
    — **resolved 2026-07-24** (all 5 todos were already `[x]`; frontmatter `status` was stale, now corrected).
  - [`plans/active/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`](/plans/archive/issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md)
    (1 open, corrected 2026-07-24 — the P1 re-fetch-backfill item was a stale checkbox, already done per the doc's own
    "Update 2026-07-15" section, now flipped):
    - **[DATA] P2.** Remove/relabel 1 defi/UNISWAP_V3-BASE row mis-filed in the sports manifest
  - [`plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md`](/plans/active/issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md)
    (1 open):
    - **[DATA] P2.** BLOCKED-PREREQUISITES — re-verify + re-dispatch footystats backfill VM
  - [`plans/archive/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md`](/plans/archive/issues/mtds_sports_api_football_wrong_source_reaccumulated_post_wipe_2026_07_22.md)
    — `status: resolved`, 0 open todos.
  - [`plans/archive/issues/sports_trades_attempted_failed_2026_07_23.md`](/plans/archive/issues/sports_trades_attempted_failed_2026_07_23.md)
    (2 open):
    - **[DESIGN] P3.** Flag `check_high_attempted_failed` owner (deployment-service) re: same-day manifest
    - **[VERIFY] P3.** Once `sports_master_closeout`'s K1/K2 fully flip + the DELETE lands, re-verify
  - [`plans/active/issues/sports_trades_venue_fetch_failed_2026_07_15.md`](/plans/archive/issues/sports_trades_venue_fetch_failed_2026_07_15.md)
    — `status: resolved`, 0 open todos.
  - [`sports_golden_window_attempted_failed_remediation_2026_06_24.md`](/plans/archive/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md)
    — ✅ ARCHIVED 2026-07-27, `status: resolved`. The 3 listed items below were all stale-unflipped (already done):
    understat 404 scoping, odds-api backfill gaps (odds-api actually carries all 3 leagues post-gap-fill), and the
    `candidate_parquet_paths` gap. Sole remainder (3-way understat split, P3, dormant) footnoted at
    `/codex/02-data/sports-data-source-coverage-matrix.md` §2.3.
  - [`plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md`](/plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md)
    (1 open):
    - **[DATA] P1.** Once the TEAMS/STANDINGS deployment question is resolved, proceed with the fix
  - [`plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md`](/plans/active/issues/canonical_player_stats_fixture_events_quality_2026_07_16.md)
    — 0 open todos.
  - [`plans/active/issues/sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md`](/plans/archive/issues/sports_canonical_raw_truncated_rederive_destroys_corpus_2026_07_16.md)
    — `status: resolved`, 1 residual:
    - **[DOCS] P1.** Correct the cutover runbook's canonical-is-a-superset premise for raw odds on early dates
  - [`plans/archive/issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md`](/plans/archive/issues/sports_is_odds_capture_code_incomplete_reversal_2026_06_27.md)
    — `status: resolved`, 0 open todos.
  - [`plans/archive/issues/sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md`](/plans/archive/issues/sports_live_writer_instrument_type_casing_never_fixed_2026_07_22.md)
    — `status: resolved`, 4 residual:
    - **1. [SCRIPT] P1.** Grep-then-READ every `"odds"`/`"trades"` lowercase literal in `sentinels.py`
    - **2. [SCRIPT] P1.** Make the 3 confirmed call-site changes (venue_fetch.py x2, manifest_finalize.py x1)
    - **3. [REVIEW] P2.** Once shipped + deployed, re-verify empirically against a live day
    - **4. [DATA] P2.** Only after todos 1-3 land AND verify live: re-scope the gated delete of old non-canonical
  - [`plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md`](/plans/active/issues/sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20.md)
    — 0 open todos.
  - [`plans/active/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md`](/plans/archive/issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md)
    — 0 open todos.
  - [`plans/active/issues/sports_source_mdps_instruments_service_not_leakage_2026_07_16.md`](/plans/archive/issues/sports_source_mdps_instruments_service_not_leakage_2026_07_16.md)
    — `status: resolved`, 0 open todos.
  - [`plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`](/plans/archive/issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md)
    — 0 open todos.
  - [`plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md`](/plans/archive/issues/dp_catalog_not_running_sports_prediction_2026_07_15.md)
    — `status: resolved`, 2 residual (cross-AG with prediction, also referenced in
    `prediction_consolidated_closeout_2026_07_18.md`):
    - **[OPS] P2.** Verify the next scheduled `lifecycle-catalogue-regen-sports` run
    - **[INFRA] P3.** Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`

- **Cross-cutting infra (shared across asset groups, sports-tagged too — primary tracking in the owning domain/sibling
  closeout, listed here only for discoverability)**:
  `/plans/active/issues/adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `/plans/active/issues/backfill_smoke_write_path_canonical_audit_2026_07_20.md`,
  `/plans/archive/issues/candle_feature_canonical_path_divergence_2026_07_20.md`,
  `/plans/active/issues/coverage_floor_registries_no_cross_propagation_2026_07_17.md`,
  `/plans/active/issues/estate_orphan_assessment_2026_07_21.md`,
  `/plans/archive/issues/features_by_date_root_canonicalisation_2026_07_21.md`,
  `/plans/archive/issues/group_c_cloud_run_job_failures_triage_2026_07_16.md`,
  `/plans/active/issues/instruments_docs_audit_outstanding_items_2026_07_08.md`,
  `/plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`,
  `/plans/archive/issues/manifest_completeness_full_corpus_map_build_2026_07_20.md`,
  `/plans/active/issues/mdps_features_deadcode_consolidation_2026_07_20.md`,
  `/plans/archive/issues/mdps_prior_seed_context_thread_unsafe_2026_07_20.md`,
  `/plans/archive/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`,
  `/plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `/plans/active/issues/phantom_audit_estate_coverage_gap_2026_07_10.md`,
  `/plans/archive/issues/pipeline_e2e_check_vm_name_collision_2026_07_12.md`,
  `/plans/archive/issues/ui_coverage_ts_venue_category_v2_rename_gap_2026_07_10.md`,
  `/plans/archive/issues/vm_backfill_data_correctness_findings_2026_06_29.md`,
  `/plans/archive/2026_07/candle_canonical_path_migration_execution_2026_07_24.md`,
  `/plans/archive/2026_08/canonical_id_builder_retrofit_checklist_2026_07_08.md`,
  `/plans/active/data_pipeline_check_mdps_features_2026_07_20.md`,
  `/plans/archive/2026_07/mdps_features_reduced_artifact_tracker_2026_06_28.md` (ARCHIVED 2026-07-27),
  `/plans/archive/issues/understat_bulk_download_backfill_2026_06_29.md` (retagged `[sports]` 2026-07-25, was a
  cross-cutting mistag — see `cursor-configs/skills/ag-closeout-audit/SKILL.md`'s Orthogonality HARD CHECK; ARCHIVED
  2026-07-27).

- **Sibling closeouts / cross-AG (own primary tracking elsewhere, linked here for awareness only)**:
  `/plans/active/defi_consolidated_closeout_2026_07_18.md` (in this doc's own `related:` — cross-AG link, not sports
  scope), `/plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md` (downstream ML, gated, prediction-primary
  with a sports feeder dependency).

- **Folded-in, excluded from the digest above (all `superseded_by: sports_consolidated_closeout_2026_07_19.md`, live
  content absorbed into Track C/S2 — see the callout at the top of this section for the full list of 5)**.

## Todos

- [x] ✅ [DOC] P3. **This index is not "0 open work" — it aggregates dozens of sibling docs carrying real open todos**
      (by design, non-checkbox digest bullets — e.g. 73 open, 18 P0 / 40 P1 / 14 P2 / 1 P3, in
      `issues/sports_features_layer_findings_sweep_2026_07_18.md`); do not treat this doc's own checkbox-free format as
      evidence the sports asset group is done. **Verified accurate 2026-07-28** — re-read the doc in full: the caveat
      correctly describes the doc's own non-checkbox digest bullets, and the cited 73-open figure for
      `issues/sports_features_layer_findings_sweep_2026_07_18.md` matches that section's own text. No correction needed;
      checkbox flipped to record the verification.

## Deferred work — migrated to:

**The `DEFERRED — register XG_SHOTS in SPORTS_DATA_TYPE_META` line** (formerly § API-Football / source-adapter
correctness) is now RESOLVED — shipped `deployment-api@b04c082` once deployment-api LDR went QG-green
(`understat_bulk_download_backfill_2026_06_29.md` archived 2026-07-27, all 11/11 §8 items done). No longer a live
deferral; kept here as a historical pointer to
[`/plans/archive/issues/understat_bulk_download_backfill_2026_06_29.md`](/plans/archive/issues/understat_bulk_download_backfill_2026_06_29.md).
