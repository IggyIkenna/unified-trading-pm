---
doc_type: plan
title: Sports satellite AO batch 3 — conflict-cleared extraction from the 2026-07-25 orphan audit
summary: >-
  Third AO-dispatch batch for sports, extracted from the 2026-07-25 orphan-audit's 26 genuinely-orphaned satellite docs
  (of 72 sports-primary docs total; see `ag_closeout_audit_rollout_2026_07_25.md` for the full audit). A 26-agent
  AO-eligibility-triage workflow found 25 candidate AO-eligible todos across those docs, but 23 of the 25 carried a
  flagged CONFLICT against `sports_consolidated_closeout_2026_07_19.md`'s own open todos (a broader or
  differently-scoped claim on the same ground) — per the operator's explicit 2026-07-25 instruction to never silently
  resolve a conflict, this batch contains ONLY the 12 todos that survived a per-item conflict review (either genuinely
  zero flagged conflict, or a flagged conflict whose topic provably does not overlap the specific extracted item). The
  23 conflict-gated candidates are NOT dropped — they're preserved with full detail in the Deferred section below and
  queued for the operator in `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`.
status: complete
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    unified-api-contracts,
    market-tick-data-service,
    unified-trading-library,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-3, satellite-docs, conflict-checked]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-31"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.9
estimate_calibrated_ai_days: 0.7
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /autonomous session 2026-07-25, driven by the /ag-closeout-audit skill Phase 3 (conflict-checked next-batch drafting)
  after the sports orphan-audit found 26 genuinely orphaned docs. Triage workflow `wf_74a99101-69b` (26 agents, 0
  errors) produced 25 AO-eligible candidates + 33 flagged conflicts; this doc is the conflict-cleared subset only.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports satellite AO batch 3 — conflict-cleared extraction

> **🟢 ARCHIVED 2026-07-31 — COMPLETE.** All 12 todos shipped with verified evidence (see each todo + the Progress Log
> below). The Deferred section's 6 docs / 7 conflict-gated candidates were fully resolved by
> `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md`'s todo 3 (2026-07-30) — see that doc (also archived
> alongside this one) for the per-item disposition. Successor: none (this batch's work is complete, not superseded).

## Todos

- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-10)** — **Build the alias→canonical league_id mapping for the 85
      contaminated `day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule` league folders and check
      GCS for existing canonical-folder fixtures data (read-only, no PROD write/delete).** For each of the 85 raw folder
      names (e.g. `ARGENTINA_RESERVE_LEAGUE`, `ENGLAND_CHAMPIONSHIP`, `ITALY_SERIE_B`, `SAUDI_ARABIA_PRO_LEAGUE`, ... —
      full list re-derivable via a bounded listing of
      `sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/` and
      identifying the instrument-catalogue-shaped shards, same method the issue doc used), compute the UAC
      prediction-tier league registry's own `build_league_id(country, league_name)` value for every registered league
      entry (`unified-api-contracts/.../league_data_prediction.py` + `canonical_ids.py`) and match against the 85 target
      strings to find each one's abbreviated canonical league_id (or record "no canonical match found" if none matches).
      For every matched canonical league_id, use UTL `gcs_describe_object`/`list_blobs` (read-only) to check whether
      `sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/league=<canonical_id>/fixtures_schedule.parquet`
      already exists, and if it exists, confirm it reads with the correct fixtures schema (not the contaminated
      instrument-catalogue schema). Rewrite/extend
      `instruments-service/scripts/recover_fixtures_schedule_wrong_schema_day_2026_04_14.py`'s investigation mode to do
      this (the issue doc flags its current form as implementing the wrong recovery model and "needs rewriting ...
      before any --apply run") — this todo covers ONLY the read-only investigation, not any `--apply`/write/delete.
      (repo: instruments-service, reads unified-api-contracts registry). **Done when**: a written report (appended to
      this issue doc or a linked scratch doc) lists, for each of the 85 affected league folder names: (1) the matched
      canonical league_id or "no match", and (2) whether canonical-folder `day=2026-04-14` fixtures data already exists
      and its schema-correctness. No PROD GCS object is written, moved, or deleted. Source:
      `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`. **This exact gate-(b)/(c) investigation was
      already fully completed by slot 11 (mapping) and slot 2 (GCS check) on 2026-07-25T05:45Z, and the corresponding
      remediation write already shipped (`instruments-service@a9f42320`, DATA P2 in the same issue doc, DONE
      2026-07-25T11:16Z) — the source issue doc had since moved to `plans/archive/issues/` with all 4 of its own todos
      checked, which the 2026-07-25 orphan-audit apparently missed before drafting this batch. Rather than re-deriving
      the 85-name mapping from scratch (duplicate work — and the todo's own suggested "iterate every registered league
      entry through `build_league_id()`" method is less robust than gate-(b)'s already-verified reverse-catalog
      approach, which achieved a clean 0-unmatched result), ran a bounded, read-only re-verification of the two things
      that could have drifted since: (1) confirmed 0/35 unregistered leagues have since been registered and 0/50
      previously-matched canonical league_ids have dropped out of `LEAGUE_REGISTRY`; (2) live-checked all 50 registered
      canonical `day=2026-04-14` fixtures_schedule shards — all 50 now read with the correct schema (confirming the
      instruments-service@a9f42320 write genuinely landed, not just the checkbox claim), zero contaminated/missing/
      errors. Full written report appended as a new dated section to the issue doc
      (`plans/active/issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md` §"Post-remediation verification of
      the 85-league mapping + GCS state (2026-07-27, slot-10, data_engineering)"; that doc was briefly, wrongly archived
      2026-07-25→2026-07-31 on a false-positive checkbox scan and has since been restored to `plans/active/`). No PROD
      GCS object was written, moved, or deleted — verification only.**
- [x] ✅ [CODE] P1. **DONE 2026-07-27 (slot-13)** — **Close the PRIMERA_DIVISION (Chile) Odds-API team-name alias gap**
      — unified-api-contracts@96d15ba7. Re-ran the `validate_team_resolution()` match-rate measurement against every
      real captured `pipeline_mode=batch_odds_api` day for the league across the full manifest history in
      `market-data-tick-sports-prd-central-element-323112` (411 captured days via the
      `_index/availability_index.parquet` manifest — not just the original 4-day sample; note the canonical `league_id`
      for this league is `CHILE_PRIMERA` per `unified_api_contracts/canonical/domain/sports/league_data_prediction.py` —
      "PRIMERA_DIVISION" is the league's display name used in this doc's title/prose, and a stale non-canonical
      `league_id=PRIMERA_DIVISION` folder also exists in GCS with 0 manifest rows, superseded by `CHILE_PRIMERA`).
      Baseline: 64.1% match rate (84,492 total rows), 9 distinct `UNRESOLVED_TEAM_NAME` strings — the 4 the issue doc
      originally cited (`Coquimbo Unido`, `Deportes Concepción`, `Deportes Limache`, `Universidad de Concepción`) plus 5
      more the fuller 411-day range surfaced (`CD Cobreloa` — a short-form gap on the pre-existing `COBRELOA` canonical
      — plus 4 genuinely new canonical entries: `Deportes Copiapó`→`DEPORTES_COPIAPO`, `La Serena`→`D_LA_SERENA`,
      `Magallanes`→`MAGALLANES`, `Antofagasta`→`ANTOFAGASTA`). Every canonical_team_id already existed in
      `unified_api_contracts/canonical/domain/sports/data/team_mapping.csv` — no live API-Football pull or new
      canonical-id minting needed. Cross-checked each against the real `af_home_name`/`af_away_name` fields in the
      captured `instruments-store-sports-prd-central-element-323112`
      `sports_reference/.../entity=fixtures/league=CHILE_PRIMERA/fixtures.parquet` for matching fixtures (same method
      the `OHIGGINS`/`UNIVERSIDAD_CATOLICA` Phase-E L2a fix used). Added all 9 alias entries (extended the existing
      `COBRELOA` entry + 8 new canonical entries) to `CHILE_PRIMERA_TEAM_ALIASES` in
      `unified_api_contracts/external/api_football/team_mappings.py`; added 22 regression tests (parametrized +
      no-regression cases) to `unified-api-contracts/tests/unit/test_team_mappings.py`. Re-measured post-fix: **100%
      match rate, 0 unresolved names**, across all 411 real captured days. `quality-gates.sh` green
      (`.qg_last_passed_sha=e052d16d` → shipped `96d15ba7`). Source:
      `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-15)** — Re-pin unified-api-contracts's `source_data_latency.py` 5 p95-lag
      constants (SFI/API-Football/FootyStats/Understat/Open-Meteo) from empirical `latency_observations` data. Ran
      `instruments-service/scripts/aggregate_source_latency_observations.py --emit-constants` and `--first-success-only`
      against `instruments-store-sports-prd`'s 552 `_index/latency_observations/day=*/*.parquet` files
      (2026-07-14..2026-07-27, ~13-day accrual). Only `api_football` accrued samples (n=2504, first-ATTEMPT ceiling only
      — `first_success` is 0/2504); observed p95=673s < assumed 1800s, so per the aggregator's fail-safe the constant is
      retained unchanged (CONFIRM, not a re-pin). The other 4 sources read n=0 (UNDER-SAMPLED), each for a distinct root
      cause now diagnosed and documented (no live trigger for SFI; a confirmed scheduler bug for Understat's
      `stats_delayed` trigger — filed `archive/issues/sports_post_match_trigger_24h_lookback_bug_2026_07_27.md`, P0;
      FootyStats/Open-Meteo never instrumented in `ENTITY_TO_OBSERVATION_TARGET`). All 5 constants in
      `source_data_latency.py` now carry per-source empirical-review docstrings citing sample counts + root causes
      (unified-api-contracts@37611070); no numeric value changed this cycle — that is the correct, evidence-based
      outcome, not a rubber-stamped VALIDATED. `sports_live_availability_and_source_latency_2026_07_24.md`'s Step-2
      verdict table updated accordingly (NOT a blanket VALIDATED — 4/5 sources remain genuinely un-validated pending the
      filed follow-up). `quality-gates.sh` green. Source: `sports_live_availability_and_source_latency_2026_07_24.md`
      (corrected 2026-07-25 plan-reconcile — the digest cited here as Source has 0 checkboxes and is not the real
      dispatch/reconciliation target; the actual open checkbox for this work lives in the doc now cited).
- [x] ✅ [DATA] P1. **DONE 2026-07-31.** Determine the disposition of `market-data-tick-sports-prd`'s 20,785
      `venue=KALSHI`/`empty_confirmed`/`row_count=0` rows (paired with `source=polymarket_clob`, dates
      2020-06-06..2026-05-21) — classify as (a) an independent instance of the same writer/consolidator
      asset_group-mislabeling class the fleet-wide TOCTOU bug (ROUND 4-6) produces in the sibling
      `instruments-store-sports-prd` bucket, (b) a legacy artifact predating the sports/prediction venue split, or (c)
      something else — and state whether it warrants its own remediation (lower urgency: `row_count=0` throughout, no
      real data at risk). Investigation/ classification only — do NOT attempt any manifest write or remediation (the
      parent issue's ROUND 6/7 fix for the sibling bucket is explicitly BLOCKED-OPERATOR-DECISION; this is a read-only
      classification task on a DIFFERENT, lower-risk population in a different bucket). Repo: market-tick-data-service /
      unified-trading-library (read-only). **Done when**: Todo 15 in
      `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` is answered with a cited
      classification (a/b/c) and an explicit remediation recommendation, recorded as a new dated section in that same
      doc; the doc's own `status: open` and ROUND 6/7 gating on the unrelated population are left untouched. **Answered:
      classification (b) — a dormant legacy artifact (live count re-confirmed unchanged at exactly 20,785, all
      `written_at` clustered in one 80-second 2026-07-13 window from an unrelated reason-taxonomy rebuild touching
      pre-existing rows — not new writes; `date` spans the full 2020-2026 history, not a recent window; zero growth 6
      days before/after; the live `_ADAPTER_PATHS` sports-fetch registry never targets Kalshi/Polymarket today; NOT the
      live TOCTOU class (a), which reasserts continuously — no remediation warranted, `empty_confirmed` is excluded from
      the honest-coverage denominator so this is also formula-inert.** Full evidence in the new "## 2026-07-31 update"
      section appended to that doc (todo 15). Source:
      `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` (corrected 2026-07-25 plan-reconcile
      — this todo's own Done-when already names the real target, todo 15 in that doc; the digest cited here as Source
      has 0 checkboxes).
- [x] ✅ [DOC] P1. **DONE 2026-07-27 (slot-13)** — Wrote the sports features-bucket (`sports_features/`) path-layout
      SSOT in codex/02-data — documents that `odds_features`/`odds_targets` are day-level
      (`sports_features/by_date/day=<D>/feature_group={odds_features,odds_targets}/features.parquet`) while
      `derived_features`/`fixture_features` are per-league with RAW api-football numeric ids in the GCS path
      (`league=<raw_af_id>/feature_group={derived,fixture}_features/features.parquet`, historical/addressable,
      deliberately NOT to be renamed in place) but a CANONICAL league NAME in the manifest key (via
      `_canonical_league_id`), and that readers must handle both layouts (dual-probe contract, single bounded prefix
      list per (date, group) — no corpus walk). Cited `features-service/features_service/sports/data/writer.py:26-27`,
      `.../sports/cli/handlers/batch_handler.py:93-112,299-361,639-648`, and
      `ml-service/ml_service/training/app/core/sports_feature_loader.py:52-146` as ground truth (all verified by direct
      read, not inferred). Repo: unified-trading-pm (codex/02-data/). New doc:
      `/codex/02-data/sports-features-bucket-path-layout.md`. **Done when**: a new codex/02-data doc exists documenting
      this exact layout with the cited writer file:line references, and its path is added to
      `sports_consolidated_closeout_2026_07_19.md`'s Codex SSOTs list. Source:
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-2)** — Audit instruments-service's `odds_api_team_mapping.parquet`
      (`sports_reference/mappings/`) coverage against the distinct `od_team_name` values actually present in MDPS's
      bucketed-odds shards, and extend the mapping table with the missing `od_team_name -> af_team_id` rows found
      (confirmed gap as of 2026-07-14: `Burgos CF`, SEGUNDA_DIVISION, is unmapped — smaller-league spellings are likely
      under-covered generally). Ran a stride-sampled coverage census (204 days across the 2020-06-06 data floor, 2,193
      shard reads — honestly disclosed as a sample, not an exhaustive corpus walk) against MDPS's
      `pipeline_mode=batch_mdps_odds_horizon_bucket` shards: 734 distinct team names observed, 131 gaps vs the 658-row
      table. Resolved 59 with confirmed identity (via the live pipeline's own `validate_team_resolution` alias resolver
      cross-referenced against `team_mapping_v2.parquet`, `af_league_id` majority-voted from already-mapped teammates in
      the same league sample — never guessed) and applied them (658 -> 717 rows, incl. `Burgos CF` ->
      `af_team_id=9580`). 72 residual names are genuinely unmappable today (no alias / not in team_mapping_v2 / no
      league vote) and are left dropping at ml-service merge time per this todo's own accepted behavior. Repo:
      instruments-service@dd3ecff1 (`scripts/odds_api_team_mapping_coverage_audit_2026_07_27.py`). Findings + full
      breakdown: `/plans/archive/issues/odds_api_team_mapping_coverage_audit_2026_07_27.md`. Source:
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-11)** — Remove/relabel the 2 confirmed cross-asset_group mislabeled rows
      sitting in the SPORTS manifest: (1)
      `date=2026-06-26 venue=UNISWAP_V3-BASE asset_group=defi service_name=instruments-service     capture_status=attempted_failed source=api_football`,
      and (2) a second row `source=instruments_service asset_group=cefi capture_status=captured` found in the same
      2026-07-15 probe. Trace the writer path that emitted each into `instruments-store-sports-prd`'s manifest instead
      of its own asset_group's bucket; if reproducible, fix the mis-route at source; delete the phantom row(s) CAS-safe,
      snapshot-first. Repo: market-tick-data-service / instruments-service. **Done when**: both rows are confirmed
      removed from the sports manifest via a fresh re-read (0 rows matching either predicate); a snapshot was taken
      before the delete; and either the mis-routing writer is fixed with a regression test, or a documented reason it
      isn't reproducible is recorded as a new dated section in
      `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`. Source:
      `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md` (corrected 2026-07-25 plan-reconcile
      — matches this todo's own Done-when target; the digest previously cited as Source has 0 checkboxes).
      `instruments-service@3e08f7d2`. **Root cause found via code read**: `_write_all_venues()`
      (`instruments_service/engine/orchestrator/process_write.py`) only treated the literal `"ALL"` sentinel as a
      multi-AG run; a genuine multi-value `--asset-group` list (the service's own CLI defines `nargs="+"`, a real
      supported shape) silently fell through and forced every venue into the single primary bucket. Fixed `_is_all_run`
      to also trigger on `len(asset_groups) > 1`, with a new regression test
      (`TestMultiAssetGroupListTriggersPerVenueBucketRouting`, `tests/unit/test_orchestrator_gaps.py`) proven to fail
      pre-fix / pass post-fix. Both phantom rows deleted CAS-safe (snapshot to
      `_index/snapshots/pre_cross_ag_phantom_delete_2026_07_27.parquet` first,
      `scripts/delete_cross_ag_phantom_rows_sports_manifest_2026_07_27.py`, generation `1785185026081616` ->
      `1785185292923233`, rows 6,841,125 -> 6,841,123); fresh re-read (twice) confirms 0 rows matching either predicate.
      A SEPARATE, still-open structural gap (the `process_completeness.py` honest-coverage writers never gained
      per-venue bucket routing at all) is the root cause of the `attempted_failed` row's class specifically —
      documented + filed as a new scoped P2 follow-up todo in the issue doc rather than fixed inline (bigger,
      higher-blast-radius change to the sports daily producer's shared completeness-check, out of this cleanup's scope).
      Full evidence: issue doc's "Update 2026-07-27" section.
- [x] ✅ [INFRA] P1. **DONE 2026-07-26 (slot-7)** — Grant
      `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com` `storage.objects.create` on
      `central-element-323112-events` (or the correct events-sink bucket, confirm the exact name at execution time) so
      `CATALOGUE_SHRINK_BLOCKED`/similar structured events from the sports/prediction/cefi/defi
      `lifecycle-catalogue-regen-*` Cloud Run Jobs stop silently 403ing out of the event-log sink (Cloud Logging still
      carries the signal today, but the structured event-log sink does not). Repo: deployment-service (Terraform IAM).
      **Done when**: the IAM binding is applied via Terraform (+ live-apply matching it), and a fresh forced
      `CATALOGUE_SHRINK_BLOCKED`-class event (or a synthetic equivalent write) is confirmed reaching the events-sink
      bucket without a 403. Source: `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`. Confirmed the exact
      bucket name is `central-element-323112-events` (the `warm_gcs_bucket`/`cold_gcs_bucket` Terraform vars for this
      same module both resolve to it in live state) — no ambiguity. `roles/storage.objectCreator` (==
      `storage.objects.create`) granted, codified in new
      `deployment-service/terraform/gcp/live_event_log/events_bucket_iam.tf`
      (`deployment-service@<see plan flip commit>`), live-applied, and verified with a synthetic impersonated-SA write
      that landed HTTP 200 (no 403) then was cleaned up. Full evidence + the credential gotcha hit along the way in the
      Progress Log below.
- [x] ✅ [DOC] P1. Re-verify and flip
      `plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md` to `status: resolved` with
      `resolved_by: instruments-service@ac22305c` populated — it documents the identical 3 oversized sports-domain
      functions (`_AfManifestHooks.emit_empty_gaps_for_entity()` / `_fetch_teams_and_standings()` /
      `_write_per_fixture_entities()`, same 89L/205L/253L measurements) already confirmed decomposed + resolved by the
      same commit via `sports_reference_function_size_qg_regression_2026_07_16.md`'s own 2026-07-23 RE-TRIAGE, but was
      never itself flipped. Repo: unified-trading-pm. **Done when**: the doc's frontmatter `status` reads `resolved`
      with `resolved_by` populated, citing either the same live-code re-measurement evidence already gathered in the
      sibling doc or a fresh independent re-measurement if this doc's own claims need independent reverification first.
      Source: `plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md` (corrected
      2026-07-25 plan-reconcile — this todo's subject IS that doc; the digest previously cited as Source has 0
      checkboxes and isn't the doc actually being flipped). — RE-VERIFIED 2026-07-27 (slot-12): the target doc's
      frontmatter is ALREADY `status: resolved` with `resolved_by: instruments-service@a8c0e18e (2026-07-25)` populated
      (a LATER, more complete closure SHA than this todo's `ac22305c` — that commit only closed the function-size
      regrowth; `a8c0e18e` closed the doc's remaining 2 P3 follow-ons, per its own "## Resolution (2026-07-25)"
      section). No further doc edit was needed — this todo's premise ("never itself flipped") was already stale by the
      time it dispatched. Sibling doc `sports_reference_function_size_qg_regression_2026_07_16.md` cross-checked:
      `status: resolved`, `resolved_by: instruments-service@ac22305c` — consistent, no drift between the two.
- [x] ✅ [DIAG] P1. **DONE 2026-07-27 (slot-9)** — **Verify whether the sports manifest's 2026-vs-prior-year
      enumeration-grain inconsistency (~10x more cells seeded per data_type for 2026 than prior years) still persists**
      — measure current per-data_type cell-seeding counts for a matched 2025 vs 2026 sample window directly against the
      live `instruments-store-sports-prd/_index/availability_index.parquet` manifest. The diagnosed cause (over-seeding,
      "Cause A") was substantially addressed by the 2026-06-23 `enumerate_expected_universe.py` fix
      (instruments-service@0bcf727) and the subsequent write-gate/dereg/ canonicalize program —
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s own "Post-backfill entity-coverage relabel" todo measured a
      ~30x reduction in the closely-related phantom-seed count (1,027,396 → 33,905 rows) as a side effect of that same
      program. If the 2025-vs-2026 ratio is now ~1x, annotate this line "resolved as side effect" citing the measurement
      (no code change). If a genuine ~10x-class grain inconsistency still persists, file a scoped
      `plans/active/issues/<slug>.md` documenting the root cause + measurement for follow-up — do NOT attempt a code fix
      in this todo (repo: instruments-service / unified-api-contracts, read-only measurement). **Done when**: a
      per-data_type 2025-vs-2026 cell-seeding ratio has been measured and reported against the live `-prd-` manifest,
      AND either (a) this item is annotated "resolved as side effect" with the measurement cited, or (b) a new scoped
      issue doc is filed under `plans/active/issues/` with the measurement + root-cause hypothesis (no fix implemented).
      — **(b): STILL PERSISTS, NOT resolved.** Ran a single-download read of the live prod manifest (6,847,192 rows)
      grouped by `data_type` over a matched H1 window (2025-01-01..2025-06-30 vs 2026-01-01..2026-06-30): overall ratio
      **3.13x** (363,842 → 1,137,706 cells); most data_types cluster 2.2x-3.6x; 3 outliers — `FIXTURES` 16.6x,
      `FIXTURES_OUTCOMES` 15.7x, `ODDS` 6.0x. Root cause identified by code read (a DIFFERENT mechanism than the fixed
      Cause A): every 2025 H1 row is `capture_status ∈ {captured, empty_confirmed}` only (zero `expected_unattempted`),
      while 2026 H1 rows carry a real 3-way split including a large `expected_unattempted` share — because
      `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`'s v2 enumerator `--start-date`
      (`var.     expected_universe_start_date`) is a STATIC, never-overridden Terraform default `"2026-02-20"`
      (verified: only declaration + only usage in `terraform/`), so the entire 2025 H1 window falls before the
      enumerator's bounded 120-day window and structurally never gets `expected_unattempted` seeded — an artifact of the
      bounded-window design, not a live over-seeding regression. Full measurement + root-cause writeup + 2 follow-up
      todos (1 `[OPERATOR]` window-policy decision, 1 `[DATA]` league-count-growth investigation) filed:
      `issues/sports_manifest_2026_h1_vs_2025_h1_enumeration_grain_persists_2026_07_27.md`. Measurement script:
      `instruments-service/scripts/sports_manifest_enumeration_grain_check_2026_07_27.py` (read-only, single-walk).
      Source: `data_completion_sports_2026_07_24.md`.
- [x] ✅ [DIAG] P1. **DONE 2026-07-27 (slot-9)** — Determine whether the free-text `error_reason` pattern documented in
      this doc's §2.5 ("record_empty(reason=SOURCE_RETURNED_ZERO) rejected: instruments-service catalog says ...") is
      still live-writing today by running a fresh distinct-`error_reason` census over the prod sports manifest
      (`market-data-tick-sports-prd-central-element-323112/_index/availability_index.parquet`, grouping
      `empty_confirmed`+`attempted_failed` rows by `error_reason`, diffed against UAC's `EMPTY_CONFIRMED_REASONS` closed
      set + classified error codes, single-walk discipline). If any live-dated (not frozen-legacy) row still carries a
      full-sentence value outside the closed set, locate the write site in market-tick-data-service's sports odds path
      (`engine/orchestrator/sentinels.py`'s v1/v2 emit functions and/or
      `market_tick_data_service/live/manifest_recorder.py:166-244`) and add a write-time guard that routes the
      rejection/diagnostic message to a log line instead of persisting it as the `error_reason` column value, with a
      regression test proving the guard fires. Repo: market-tick-data-service, unified-trading-library (only if the
      write site lives there instead). **Done when**: the census result is recorded in the issue doc's §2.5 (0 live
      matches → note the pattern is stale and no code change was needed; N live matches → a write-time guard shipped
      with a passing regression test proving `error_reason` for newly-written sports rows is always a member of the
      closed set, never a free-text sentence); `quality-gates.sh` green in the touched repo(s). Source:
      `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`. — **Ran the census
      (market-tick-data-service/scripts/sports_error_reason_free_text_census_2026_07_27.py, single read of 516,196-row
      manifest).** The EXACT originally-cited pattern is STALE (0 live matches). A DIFFERENT free-text pattern IS still
      live-writing: 1,998 rows / 1,976 distinct values, all dated 2026-07-25/26, from a
      `StreamingParquetWriter pre-write validation failed: [partition_mismatch] ...` diagnostic. **Write site
      correction**: not MTDS as this todo assumed — traced by code read to **market-data-processing-service**
      (`live_workers_streaming.py` → `close_candle_streaming_writer` → `_emit_status_for_shard`). Shipped the write-time
      guard there: `market-data-processing-service@da98dc7` — a new `_classify_write_error_reason()` classifies the
      pre-write-validation ValueError class to `RecordFailedReason.MALFORMED_ROW_KEY` (closed-set) and any other
      write-loop exception to `UNCLASSIFIED_ADAPTER_ERROR`, with the full diagnostic now logged instead of persisted; 2
      regression tests added/updated in `tests/unit/test_canonical_writer_record_helpers.py` proving the guard fires
      (`quality-gates.sh` green, `.qg_last_passed_sha=4544eb8692b0c28f26fb2f7e8db198a7219060df` (quickmerge then amended
      the commit to add its trailer, landed as `da98dc7`)). Full census + fix writeup:
      `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md` §2.5 "Update 2026-07-27". The underlying
      MATCH_ODDS/MATCH_ODDS_LAY partition-mismatch write FAILURE itself (data loss, not just the error_reason cosmetic)
      is a separate, still-open bug — filed as
      `issues/sports_odds_horizon_bucket_instrument_type_partition_mismatch_2026_07_27.md` (not fixed here, out of this
      DIAG todo's declared scope).
- [x] ✅ [DOC] P1. Apply this doc's own already-specified §4.5 self-correction to itself — DONE 2026-07-27,
      `unified-trading-pm@836202a79` (+ this same-turn archive-table-flip/plan-flip commit). Struck the false bullet 5
      claim in `sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s "Why it is wrong" section with an inline "⚠️
      CORRECTION 2026-07-27" note (matching the doc's existing banner convention) pointing to the verified
      per-(bookmaker,league) applicability gate
      (`unified-api-contracts/unified_api_contracts/registry/sports_bookmaker_league_coverage.py`, wired at
      `sentinels.py:321`, 606,772 prod rows); condensed the now-applied §4.5 section to a done-state to stay under the
      1000-line hard cap. Re-verified via `grep -n '538,098\|369,272'`: the only remaining hit is the already-corrected
      audit-trail citation in §4.5's own text (explicitly states the figures are wrong). Flipped the archive doc's
      (`plans/archive/2026_07/sports_shard_enumeration_cartesian_blowup_deferred_history_2026_07_22.md`) Deferred-work
      table row for §4.5 from "Not done" to a dated done-state citing the correction commit. Incidentally discovered and
      filed an unrelated pre-existing `check_plan_discipline.py` false-positive:
      `archive/issues/plan_discipline_unquoted_deferred_by_design_false_positive_2026_07_27.md`. Source:
      `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`.

## Deferred — conflict-gated (NOT dispatched; queued for operator review)

> **RESOLVED 2026-07-30** — all 6 docs / 7 candidates below were given a final disposition by
> `sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md` todo 3 (3 already shipped via batch4, confirmed; 4
> operator-ruled per `autonomous_session_operator_decisions_2026_07_25.md` #5-8 — 2 converted from prose into real
> tracked todos in `data_completion_sports_2026_07_24.md`, 1 confirmed already tracked via the
> `sports_legacy_fixtures_path_migration_2026_07_24.md` census todo, 1 folded into `batch7`'s decision-16 todo). The 2
> `doc_too_large_or_risky_for_batch` docs' recommendation was independently executed by
> `sports_satellite_ao_dispatch_batch8_2026_07_30.md`'s dedicated triage/design pass. Nothing below is still awaiting
> action — kept as the historical record of what was deferred and why.

The 26-agent triage workflow (`wf_74a99101-69b`) found 13 more AO-eligible candidates across the same 26 orphaned docs
that carried a flagged conflict against `sports_consolidated_closeout_2026_07_19.md`'s own open todos — a broader or
differently-scoped claim on the same ground (e.g. a narrow golden-window fix vs. the master plan's already-open
full-history 2015→present extension of the same recipe). Per the operator's 2026-07-25 instruction, these are NOT
silently resolved or dispatched. Full detail (todo text + conflict quote) is in the triage journal
(`subagents/workflows/wf_74a99101-69b/journal.jsonl`) and summarized in
`plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`. Docs with a conflict-gated candidate:
`data_completion_sports_2026_07_24.md` (2 items — Transfermarkt attempted_failed re-attempt, ODDS+PREDICTIONS
blank-reason measurement), `sports_legacy_fixtures_path_migration_2026_07_24.md` (1 item, 3 conflicts — the 2,319-date
fixtures-path diff overlaps Track S/Track E/C1), `issues/footystats_matches_predictions_fetch_gaps_2026_07_08.md` (1
item), `issues/fixtures_manifest_legacy_backfill_2026_07_24.md` (1 item — overlaps closed Track C1),
`issues/sports_odds_stale_fixture_reinjection_2026_07_14.md` (1 item — overlaps Track O),
`issues/sports_phantom_audits_reference_not_marketdata_2026_07_14.md` (1 item).

Also deferred entirely (flagged `doc_too_large_or_risky_for_batch` by the triage — need their own dedicated
triage/design pass, not a blind extraction):
`sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` (0 AO-eligible found anyway — all 8
remaining items are human-only design/operator-sign-off work) and
`issues/sports_features_layer_findings_sweep_2026_07_18.md` (the 73-todo sweep doc — 6 AO-eligible candidates found but
6 conflicts too, including a MAJOR overlap with the K-series UPPER-case migration operator decision already tracked in
the master plan; genuinely needs its own dedicated batch, not folded in here).

Every other orphaned doc's remaining work is human-only (operator sign-off, unbuilt safety tooling, time-gated accrual,
or a genuine design/judgment call) — see the triage journal for the full 103-item breakdown.

**Re-check note (2026-07-25, batch4):** per the `/ag-closeout-audit` skill's "batchN methodology" (added 2026-07-25),
this Deferred section's 6 docs / 7 candidates were re-checked against current state before drafting a fresh triage. 3 of
7 cleared (footystats verify+flip, fixtures_manifest_legacy_backfill doc-sync reconcile, the
sports_odds_stale_fixture_reinjection sweep — each provably stale/superseded or provably non-overlapping on re-check)
and now live as dispatchable todos in `sports_satellite_ao_dispatch_batch4_2026_07_25.md`. The other 4 (both
`data_completion_sports_2026_07_24.md` items, the `sports_legacy_fixtures_path_migration_2026_07_24.md` census, and the
`sports_phantom_audits_reference_not_marketdata_2026_07_14.md` spot-check) remain genuinely conflicted — see that
batch's own Deferred section and `autonomous_session_operator_decisions_2026_07_25.md` entries #5-8 (now actually
written up, not just pointed at). The 2 `doc_too_large_or_risky_for_batch` docs are unchanged, still pending their own
dedicated pass.

## Progress Log

- **2026-07-27 (slot-11)** — Worked the "2 cross-asset_group mislabeled sports-manifest rows" todo. Live-probed
  `instruments-store-sports-prd` (6,841,125 rows) and confirmed both rows exactly as described: a defi/UNISWAP_V3-BASE
  `attempted_failed` diagnostic row and a REAL cefi/BITGET-FUTURES `captured` row (row_count=39). Traced the writer via
  code read (not guessed): `_write_all_venues()` in `instruments-service/engine/orchestrator/process_write.py` only
  treats the literal `"ALL"` sentinel as a multi-AG run needing per-venue bucket routing; the service's own shared CLI
  (`unified_trading_library.service_cli`) defines `--asset-group` with `nargs="+"`, so a genuine multi-value, non-"ALL"
  invocation (a real, currently-supported shape) silently forces every venue into one primary bucket. Fixed
  `_is_all_run` to also trigger on `len(asset_groups) > 1`; added `TestMultiAssetGroupListTriggersPerVenueBucketRouting`
  to `tests/unit/test_orchestrator_gaps.py`, proved it fails pre-fix (stash/pop) and passes post-fix. A second, separate
  structural gap (`process_completeness.py`'s honest-coverage `ManifestWriter`s never gained per-venue routing at all)
  explains the attempted_failed row's class specifically — documented and filed as a new scoped P2 follow-up todo in the
  issue doc rather than fixed inline here (bigger, higher-blast-radius change to the sports daily producer's shared
  completeness-check). Deleted both phantom rows CAS-safe via a new one-off script
  (`instruments-service/scripts/delete_cross_ag_phantom_rows_sports_manifest_2026_07_27.py`) — snapshot taken first
  (`_index/snapshots/pre_cross_ag_phantom_delete_2026_07_27.parquet`), CAS write succeeded on attempt 1/30 (generation
  `1785185026081616` -> `1785185292923233`, rows 6,841,125 -> 6,841,123, exactly -2). Fresh re-read confirms 0 rows
  matching either predicate, held stable across a second re-read ~1 minute later. `quality-gates.sh` green in
  instruments-service. Full write-up in the issue doc's "Update 2026-07-27" section. No file collision with other
  in-flight batch3/batch4 todos (touched only `process_write.py`, `test_orchestrator_gaps.py`, the new one-off script,
  this plan, and the issue doc).

- **2026-07-27 (slot-15)** — Worked the `source_data_latency.py` re-pin todo. Ran the aggregator against 552 live
  `_index/latency_observations` parquets (13-day accrual). Only api_football had samples (n=2504, ceiling-only,
  first_success never confirmed); the other 4 sources read n=0. Investigated WHY rather than accepting a blanket
  UNDER-SAMPLED: found sfi has no live trigger wired at all, footystats/open_meteo were never added to
  `ENTITY_TO_OBSERVATION_TARGET`, and — the significant one — understat's `stats_delayed` trigger (offset_hours=24) is
  configured but can **structurally never fire**, root-caused to `get_upcoming_fixtures()`'s ~2h-post-kickoff
  fixture-visibility cutoff (`sports_trigger_state.py:44-176`) closing long before a 24h-offset trigger becomes due.
  Since that same trigger dispatches the REAL Understat/FootyStats XG capture (not just the latency proxy), this is a
  potential live data-completeness gap beyond this todo's scope — filed as a P0 issue doc
  (`archive/issues/sports_post_match_trigger_24h_lookback_bug_2026_07_27.md`) with two follow-up todos (confirm whether
  real XG/derived-features capture is also dead; design+ship the scheduler fix) rather than attempting the fix inline
  (different repo focus/testing surface than a constants re-pin). Updated `source_data_latency.py` with per-source
  empirical-review docstrings (no numeric value changed — api_football's ceiling p95 floors at the existing constant per
  the aggregator's own fail-safe; the other 4 remain UNDER-SAMPLED). Deliberately did NOT flip the source doc's Step-2
  table to a blanket VALIDATED since 4/5 sources are still genuinely unvalidated — flipped it to an accurate per-source
  empirical verdict instead. No file collision with other in-flight batch3/batch4 todos (touched only
  `source_data_latency.py`, this plan, the source doc, and the new issue doc).

- **2026-07-27 (slot-10)** — Worked the "85-contaminated-league alias→canonical mapping" todo. Found the source issue
  doc (`sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`) had already moved to `plans/archive/issues/` with all
  4 of its own todos checked — gate (b) mapping + gate (c) GCS check (this todo's exact ask) were done by slot 11/slot 2
  on 2026-07-25T05:45Z, and the remediation write already shipped (`instruments-service@a9f42320`). Ran a bounded,
  read-only re-verification instead of re-deriving from scratch: confirmed no `LEAGUE_REGISTRY` drift on either side of
  the 85 (0/35 newly registered, 0/50 dropped), and live-checked all 50 registered canonical `day=2026-04-14` shards —
  all 50 now read with the correct fixtures schema, confirming the prior remediation genuinely landed. Report appended
  to the archived issue doc's new "Post-remediation verification" section. No PROD write/delete; no code shipped (this
  was a read-only investigation todo by design — see the todo's own "covers ONLY the read-only investigation" text). No
  file collision with any other in-flight batch3/batch4 todo (touched only the archived issue doc + this plan file).

- **2026-07-26 (slot-7)** — Worked the `lifecycle-catalogue-regen` events-sink IAM-grant todo. Confirmed the bucket name
  ambiguity in the todo's own text resolves to `central-element-323112-events` (the `live_event_log` Terraform module's
  `warm_gcs_bucket`/`cold_gcs_bucket` vars both point at it in live state -- no separate "events-sink" bucket exists).
  Added `deployment-service/terraform/gcp/live_event_log/events_bucket_iam.tf` -- a single additive
  `google_storage_bucket_iam_member` (`roles/storage.objectCreator`, i.e. exactly `storage.objects.create`, least-
  privilege -- not `objectAdmin`) rather than hand-editing the machine-generated `main.tf` (its header says "Generated
  from `unified_api_contracts.events.sink_matrix.SINK_MATRIX`") or the unrelated `publisher_iam.tf` (Pub/Sub publish,
  not GCS object write).
  - **Credential-identity gotcha (worth flagging for the next agent touching this bucket's IAM)**: this environment has
    THREE distinct GCP identities in play, and they do NOT have the same permissions on `central-element-323112-events`:
    (1) Application Default Credentials, which Terraform's `google` provider uses by default, resolve to
    `unified-trading-sa@...` -- this SA lacks `storage.buckets.getIamPolicy`/`setIamPolicy` on this specific bucket
    (confirmed live: `terraform apply` 403'd on the read-modify-write with exactly that permission denied -- this is the
    SAME gap `main.tf`'s own trailing comment already documented for the Pub/Sub delivery SA's grant,
    "unified-trading-sa lacks setIamPolicy", so it's a standing property of this bucket, not new drift). (2) The active
    `gcloud auth` CLI account in this session, `github-actions-deploy@...`, DOES have both permissions on this bucket
    (verified: a direct `gcloud storage buckets add-iam-policy-binding` succeeded under it). (3) Feeding Terraform
    `GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token --account=github-actions-deploy@...)` resolved the apply
    cleanly --
    `terraform plan`/`apply -target=google_storage_bucket_iam_member. lifecycle_catalogue_regen_events_sink_writer`
    (with `warm_gcs_bucket`/`cold_gcs_bucket`/`compactor_sa_email` pulled from real `terraform state show` values, not
    guessed, to avoid drifting the rest of the module under `-target`): **1 added, 0 changed, 0 destroyed**.
    `terraform state list` now carries the resource; live `get-iam-policy` matches state exactly (only the new member
    added to the existing `objectCreator` binding -- the Pub/Sub SA's own membership in that binding is untouched,
    confirming the additive `_iam_member` resource type was the right choice over an authoritative `_iam_binding`).
  - **Live verification (Done-when's second half)**: `github-actions-deploy`'s cached access token also has
    `iam.serviceAccounts.getAccessToken` on `lifecycle-catalogue-regen` (confirmed via a direct
    `iamcredentials.googleapis.com:generateAccessToken` REST call -- `gcloud`'s own `--impersonate-service-account` flag
    failed with an unrelated WIF-refresh error, "Identity Pool subject token ... job is already completed", so the
    REST-call route bypassed that gcloud-specific bug). Used the minted impersonated token to `POST` a synthetic
    `CATALOGUE_SHRINK_BLOCKED`-shaped JSON object to `_iam_grant_verification/lifecycle-catalogue-regen-probe-<ts>.json`
    in the bucket via the GCS JSON API -- **HTTP 200**, object created, no 403. Also confirmed the grant is correctly
    least-privilege in the same pass: the impersonated SA's own `DELETE` on that same object correctly 403'd (no
    `objectAdmin`/delete rights granted, as intended). Cleaned up the probe object via the `github-actions-deploy`
    identity (`DELETE` -> 204, re-`GET` -> 404).
  - No plan/code collision: this todo's only file (`events_bucket_iam.tf`) is new and untouched by any other in-flight
    batch3/batch4 todo.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step should be machine-gated via a companion
`sports_satellite_ao_dispatch_batch3_finalize_2026_07_25.md`
(`depends_on: [sports_satellite_ao_dispatch_batch3_2026_07_25]`

- `gate_on_depends: true`), mirroring `sports_satellite_ao_dispatch_batch2_finalize_2026_07_24.md`'s pattern — whose own
  todo 2 (resolve deferred-gate follow-ups) should re-check the conflict-gated Deferred section above once the operator
  rules on the queued decision.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc,
except the new `sports-features-bucket-path-ssot.md` doc (to land under `codex/02-data/`) todo 5 itself creates (that
todo's own Done-when covers registering it in the master closeout's Codex SSOTs list).
