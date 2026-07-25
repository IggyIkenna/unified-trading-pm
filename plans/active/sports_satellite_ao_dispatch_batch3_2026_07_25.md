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
status: draft
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
last_updated: "2026-07-25"
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

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. Every todo below is same-priority and touches distinct files (verified — see the per-todo
> `files_touched` provenance in the triage workflow journal, `subagents/workflows/wf_74a99101-69b/journal.jsonl`) so
> they are safe to dispatch concurrently once activated.

## Todos

- [ ] [DATA] P2. **Build the alias→canonical league_id mapping for the 85 contaminated
      `day=2026-04-14     entity=fixtures_schedule` league folders and check GCS for existing canonical-folder fixtures
      data (read-only, no PROD write/delete).** For each of the 85 raw folder names (e.g. `ARGENTINA_RESERVE_LEAGUE`,
      `ENGLAND_CHAMPIONSHIP`, `ITALY_SERIE_B`, `SAUDI_ARABIA_PRO_LEAGUE`, ... — full list re-derivable via a bounded
      listing of `sports_reference/by_date/day=2026-04-14/pipeline_mode=batch_api_football/entity=fixtures_schedule/`
      and identifying the instrument-catalogue-shaped shards, same method the issue doc used), compute the UAC
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
      `issues/sports_fixtures_schedule_wrong_schema_day_2026_04_14.md`.
- [ ] [CODE] P2. **Close the PRIMERA_DIVISION (Chile) Odds-API team-name alias gap** — re-run the shipped
      `FixtureIdResolver`/`validate_team_resolution()` match-rate measurement (mirroring this doc's own methodology)
      against every real captured `pipeline_mode=batch_odds_api` PRIMERA_DIVISION day currently in bucket
      `market-data-tick-sports-prd-central-element-323112` (not just the original 4-day sample) to enumerate the
      COMPLETE current roster of `UNRESOLVED_TEAM_NAME` team-name strings (known as of the doc's 2026-07-23 RE-TRIAGE:
      `Coquimbo Unido`, `Deportes Concepción`, `Deportes Limache`, `Universidad de     Concepción` — confirmed still
      absent from the alias dict via direct repo grep; re-verify the list is still current/complete since it may have
      grown or shrunk with newer captured days). For each unresolved name, look up its correct AF-verified canonical
      spelling + EXISTING canonical_team_id via the already-checked-in crosswalk
      `unified_api_contracts/canonical/domain/sports/data/team_mapping.csv` (already has rows
      `COQUIMBO_UNIDO`/`CONCEPCION`/`DEPORTES_LIMACHE`/`UNIVERSIDAD_DE_CONCEPCION` with verified AF team names/ids — no
      live API-Football pull or new canonical-id minting needed), cross-checked against the real
      `af_home_name`/`af_away_name` fields in the captured
      `sports_reference/.../entity=fixtures/league=PRIMERA_DIVISION/fixtures.parquet` for the same fixtures — the exact
      verification method the already-landed `OHIGGINS`/`UNIVERSIDAD_CATOLICA` Phase-E L2a fix used per its own code
      comments. Add the missing entries to `CHILE_PRIMERA_TEAM_ALIASES` / `API_FOOTBALL_TO_CANONICAL_CHILE_PRIMERA` /
      `_CROSS_PROVIDER_ALIASES` in `unified_api_contracts/external/api_football/team_mappings.py`, add regression tests
      in `unified-api-contracts/tests/unit/test_team_mappings.py` mirroring the existing accent/bare/suffix
      disambiguator cases, then re-run the match-rate measurement to confirm PRIMERA_DIVISION's rate improves from the
      57% baseline. (repo: unified-api-contracts). **Done when**: `validate_team_resolution()` resolves all 4
      currently-known unresolved names (plus any others the fuller-date-range re-measurement surfaces) without raising
      `TeamResolutionError`; new regression tests pass; PRIMERA_DIVISION's `UNRESOLVED_TEAM_NAME` count is zero or every
      residual is explicitly documented; `quality-gates.sh` green. Source:
      `issues/sports_odds_team_name_alias_gap_south_america_2026_07_09.md`.
- [ ] [DATA] P2. Re-pin unified-api-contracts's `source_data_latency.py` 5 p95-lag constants (SFI/API-Football/
      FootyStats/Understat/Open-Meteo) from empirical `latency_observations` data — the ~2-week accrual window has
      passed (recorder shipped + wired to the live sports-scheduler 2026-06-22/24). Run
      `instruments-service/scripts/aggregate_source_latency_observations.py --emit-constants` (add
      `--first-success-only` if the polling-retry enhancement has landed) against `instruments-store-sports-prd`'s
      `_index/latency_observations/day=*/*.parquet`, review the per-source p50/p95/max-vs-assumed verdict (the script
      floors at the current assumed value unless `--allow-lower`, and reports UNDER-SAMPLED below `--min-samples=20`
      rather than a spurious re-pin), then update the 5 `Final[int]` constants in
      `unified_api_contracts/unified_api_contracts/registry/source_data_latency.py` from the observed p95 and ship via
      quickmerge. Historical rows need no migration (write-time stamps only). Repo: unified-api-contracts. **Done
      when**: the aggregator's emitted constants (or an explicit UNDER-SAMPLED verdict per source, with sample count
      cited) are recorded; `source_data_latency.py`'s 5 constants are updated to the empirical p95 wherever samples are
      sufficient; and `sports_live_availability_and_source_latency_2026_07_24.md`'s Source-latency Step-2 verdict table
      is flipped from UNVALIDATABLE-FROM-BACKFILL to VALIDATED, citing sample sizes. Source:
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [DATA] P2. Determine the disposition of `market-data-tick-sports-prd`'s 20,785 `venue=KALSHI`/
      `empty_confirmed`/`row_count=0` rows (paired with `source=polymarket_clob`, dates 2020-06-06..2026-05-21) —
      classify as (a) an independent instance of the same writer/consolidator asset_group-mislabeling class the
      fleet-wide TOCTOU bug (ROUND 4-6) produces in the sibling `instruments-store-sports-prd` bucket, (b) a legacy
      artifact predating the sports/prediction venue split, or (c) something else — and state whether it warrants its
      own remediation (lower urgency: `row_count=0` throughout, no real data at risk). Investigation/ classification
      only — do NOT attempt any manifest write or remediation (the parent issue's ROUND 6/7 fix for the sibling bucket
      is explicitly BLOCKED-OPERATOR-DECISION; this is a read-only classification task on a DIFFERENT, lower-risk
      population in a different bucket). Repo: market-tick-data-service / unified-trading-library (read-only). **Done
      when**: Todo 15 in `cross_ag_prediction_rows_bleed_into_sports_instruments_index_2026_07_20.md` is answered with a
      cited classification (a/b/c) and an explicit remediation recommendation, recorded as a new dated section in that
      same doc; the doc's own `status: open` and ROUND 6/7 gating on the unrelated population are left untouched.
      Source: `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [DOC] P3. Write the sports features-bucket (`sports_features/`) path-layout SSOT in codex/02-data — document that
      `odds_features` is day-level (`sports_features/by_date/day=<D>/feature_group=odds_features/features.parquet`)
      while `derived_features`/`fixture_features` are per-league with RAW api-football numeric ids in the GCS path
      (`league=<raw_af_id>/feature_group={derived,fixture}_features/features.parquet`, historical/addressable,
      deliberately NOT to be renamed in place) but a CANONICAL league NAME in the manifest key (via
      `_canonical_league_id`), and that readers must handle both layouts. Cite
      `features-service/features_service/sports/data/writer.py:26-27` +
      `.../sports/cli/handlers/batch_handler.py:300-323` as ground truth. Repo: unified-trading-pm (codex/02-data/).
      **Done when**: a new codex/02-data doc exists documenting this exact layout with the cited writer file:line
      references, and its path is added to `sports_consolidated_closeout_2026_07_19.md`'s Codex SSOTs list. Source:
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [DATA] P3. Audit instruments-service's `odds_api_team_mapping.parquet` (`sports_reference/mappings/`) coverage
      against the distinct `od_team_name` values actually present in MDPS's bucketed-odds shards, and extend the mapping
      table with the missing `od_team_name -> af_team_id` rows found (confirmed gap as of 2026-07-14: `Burgos CF`,
      SEGUNDA_DIVISION, is unmapped — smaller-league spellings are likely under-covered generally). Repo:
      instruments-service. **Done when**: a coverage census (distinct MDPS `od_team_name` values vs mapping-table keys)
      is run and its gap count reported; every genuinely-resolvable gap found is added to
      `odds_api_team_mapping.parquet` with the team/league identity confirmed (not guessed); any residual
      honestly-unmappable names are left dropping at ml-service merge time as already documented, not fabricated.
      Source: `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [DATA] P2. Remove/relabel the 2 confirmed cross-asset_group mislabeled rows sitting in the SPORTS manifest: (1)
      `date=2026-06-26 venue=UNISWAP_V3-BASE asset_group=defi service_name=instruments-service     capture_status=attempted_failed source=api_football`,
      and (2) a second row `source=instruments_service asset_group=cefi capture_status=captured` found in the same
      2026-07-15 probe. Trace the writer path that emitted each into `instruments-store-sports-prd`'s manifest instead
      of its own asset_group's bucket; if reproducible, fix the mis-route at source; delete the phantom row(s) CAS-safe,
      snapshot-first. Repo: market-tick-data-service / instruments-service. **Done when**: both rows are confirmed
      removed from the sports manifest via a fresh re-read (0 rows matching either predicate); a snapshot was taken
      before the delete; and either the mis-routing writer is fixed with a regression test, or a documented reason it
      isn't reproducible is recorded as a new dated section in
      `issues/api_football_reverify_attempted_failed_and_asset_group_2026_07_14.md`. Source:
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [INFRA] P3. Grant `lifecycle-catalogue-regen@central-element-323112.iam.gserviceaccount.com`
      `storage.objects.create` on `central-element-323112-events` (or the correct events-sink bucket, confirm the exact
      name at execution time) so `CATALOGUE_SHRINK_BLOCKED`/similar structured events from the
      sports/prediction/cefi/defi `lifecycle-catalogue-regen-*` Cloud Run Jobs stop silently 403ing out of the event-log
      sink (Cloud Logging still carries the signal today, but the structured event-log sink does not). Repo:
      deployment-service (Terraform IAM). **Done when**: the IAM binding is applied via Terraform (+ live-apply matching
      it), and a fresh forced `CATALOGUE_SHRINK_BLOCKED`-class event (or a synthetic equivalent write) is confirmed
      reaching the events-sink bucket without a 403. Source:
      `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [DOC] P3. Re-verify and flip
      `plans/active/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md` to `status: resolved` with
      `resolved_by: instruments-service@ac22305c` populated — it documents the identical 3 oversized sports-domain
      functions (`_AfManifestHooks.emit_empty_gaps_for_entity()` / `_fetch_teams_and_standings()` /
      `_write_per_fixture_entities()`, same 89L/205L/253L measurements) already confirmed decomposed + resolved by the
      same commit via `sports_reference_function_size_qg_regression_2026_07_16.md`'s own 2026-07-23 RE-TRIAGE, but was
      never itself flipped. Repo: unified-trading-pm. **Done when**: the doc's frontmatter `status` reads `resolved`
      with `resolved_by` populated, citing either the same live-code re-measurement evidence already gathered in the
      sibling doc or a fresh independent re-measurement if this doc's own claims need independent reverification first.
      Source: `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`.
- [ ] [DIAG] P2. **Verify whether the sports manifest's 2026-vs-prior-year enumeration-grain inconsistency (~10x more
      cells seeded per data_type for 2026 than prior years) still persists** — measure current per-data_type
      cell-seeding counts for a matched 2025 vs 2026 sample window directly against the live
      `instruments-store-sports-prd/_index/availability_index.parquet` manifest. The diagnosed cause (over-seeding,
      "Cause A") was substantially addressed by the 2026-06-23 `enumerate_expected_universe.py` fix
      (instruments-service@0bcf727) and the subsequent write-gate/dereg/canonicalize program —
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s own "Post-backfill entity-coverage relabel" todo measured a
      ~30x reduction in the closely-related phantom-seed count (1,027,396 → 33,905 rows) as a side effect of that same
      program. If the 2025-vs-2026 ratio is now ~1x, annotate this line "resolved as side effect" citing the measurement
      (no code change). If a genuine ~10x-class grain inconsistency still persists, file a scoped
      `plans/active/issues/<slug>.md` documenting the root cause + measurement for follow-up — do NOT attempt a code fix
      in this todo (repo: instruments-service / unified-api-contracts, read-only measurement). **Done when**: a
      per-data_type 2025-vs-2026 cell-seeding ratio has been measured and reported against the live `-prd-` manifest,
      AND either (a) this item is annotated "resolved as side effect" with the measurement cited, or (b) a new scoped
      issue doc is filed under `plans/active/issues/` with the measurement + root-cause hypothesis (no fix implemented).
      Source: `data_completion_sports_2026_07_24.md`.
- [ ] [DIAG] P2. Determine whether the free-text `error_reason` pattern documented in this doc's §2.5
      ("record_empty(reason=SOURCE_RETURNED_ZERO) rejected: instruments-service catalog says ...") is still live-writing
      today by running a fresh distinct-`error_reason` census over the prod sports manifest
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
      `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`.
- [ ] [DOC] P3. Apply this doc's own already-specified §4.5 self-correction to itself: in
      `sports_shard_enumeration_cartesian_blowup_2026_07_20.md`'s original "Why it is wrong" section, bullet 5 (~lines
      117-119: "Coverage is not universal even where it IS meaningful ... There is no per-(venue, fixture/market)
      expectation gate") is FALSE per the doc's own later VERIFIED DIAGNOSIS section — a per-(bookmaker,league)
      applicability gate DOES exist and IS consulted
      (`unified-api-contracts/unified_api_contracts/registry/sports_bookmaker_league_coverage.py`, wired at
      `sentinels.py:321`, materialised on 606,772 prod rows). Add an inline correction note at that bullet (matching the
      doc's existing top-of-file "⚠️ CORRECTION" banner convention) striking/superseding the false claim and pointing to
      the verified finding. Also re-verify via `grep -n '538,098\|369,272'` in the doc that no OTHER live
      (non-audit-trail) citation of those stale reason-split figures remains uncorrected. Repo: unified-trading-pm.
      **Done when**: bullet 5 carries an inline correction/strike note pointing to the verified finding; a fresh grep
      for the stale figures shows only the already-corrected audit-trail citation; the doc's own Deferred-work table row
      for §4.5 is flipped from "Not done" to a dated done-state citing the commit SHA. Source:
      `issues/sports_shard_enumeration_cartesian_blowup_2026_07_20.md`.

## Deferred — conflict-gated (NOT dispatched; queued for operator review)

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
