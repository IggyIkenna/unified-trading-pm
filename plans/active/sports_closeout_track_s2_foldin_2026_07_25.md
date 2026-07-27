---
doc_type: plan
title: Sports closeout Track S2 — fold-in absorption from 3 archived plans (split from the sports closeout)
summary: >-
  Extraction of sports_consolidated_closeout_2026_07_19.md's remaining Track S2 "FOLD-IN ABSORPTION" items (line-cap
  split, 2026-07-25) — real data/infra engineering work extracted 2026-07-23 from 3 now-archived plans
  (sports_manifest_canonicalisation_2026_06_01, sports_pipeline_to_100pct_golden_window_first_2026_06_27,
  sports_p2_history_apifootball_2015_to_present_2026_06_27). A sibling triage
  (sports_consolidated_native_ao_extract_2026_07_25.md) already extracted 7 Track S2 items (or sub-parts of them) as its
  own AO-eligible candidates before this split ran — those are excluded here (4 fully covered, 3 partially: only their
  remaining, still-human-flagged sub-part is carried here). Several remaining items are real judgment calls that stay
  non-dispatchable (tagged `[OPERATOR]`/`BLOCKED-PREREQUISITES`) or pure cross-plan pointers reformatted as non-checkbox
  digests per task_template.md finding H — this fold-in does not manufacture dispatchability that was never there.
  Verifying each item's cited detail doc against its CURRENT status (finding C) also surfaced 4 items the parent's Track
  S2 text described as live open work that are actually already resolved (the IS L6 index regression 3-step fix, the
  exit_code_fleet_monitor misclassification fix, the api_football gate-reader fix, and the WEATHER layout fix — the last
  resolved literally today, 2026-07-25) — those are carried forward as closed digests, not re-manufactured as open
  todos.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, track-s2, fold-in, satellite-docs]
related:
  [
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/active/sports_closeout_track_s2_foldin_2026_07_25_finalize.md,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/archive/2026_07/sports_manifest_canonicalisation_2026_06_01.md,
    /plans/archive/sports_pipeline_to_100pct_golden_window_first_2026_06_27.md,
    /plans/archive/2026_07/sports_p2_history_apifootball_2015_to_present_2026_06_27.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_odds_bookmaker_coverage_enumeration_2026_06_20.md,
    /plans/active/sports_legacy_fixtures_path_migration_2026_07_24.md,
    /plans/active/sports_satellite_ao_dispatch_batch2_2026_07_24.md,
    /plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3.5
estimate_calibrated_ai_days: 2.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Extracted 2026-07-25 from sports_consolidated_closeout_2026_07_19.md's Track S2 (line-cap split pass — the parent was
  over its 1000L hard cap), after removing the items/sub-items sports_consolidated_native_ao_extract_2026_07_25.md
  already drafted from the same Track.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# Sports closeout Track S2 — fold-in absorption

> **Status corrected 2026-07-26: this plan is `active`** (frontmatter has said so since creation; this banner was stale
> — the operator review it said to wait for is the 2026-07-26 rulings recorded in the two `[OPERATOR]` items below, both
> now closed). `sequential: false` — every item below touches a distinct file/doc/population; the several
> `BLOCKED-PREREQUISITES`/ `[OPERATOR]` tags below make real cross-item and cross-plan ordering non-dispatchable
> explicitly rather than relying on file position, so serializing the whole plan is unnecessary.
>
> **Overlap reconciliation (2026-07-25)**: `sports_consolidated_native_ao_extract_2026_07_25.md` already extracted, as
> its own AO-eligible candidates: (1) the mis-keyed-duplicate-bug mdps-surface check (excluding the sibling "88 orphan
> rows manual review" sub-item — carried here below); (2) Sports P2a sub-item (c) ONLY, the 40,041 FIXTURES
> `attempted_failed` re-run (excluding sub-items (a)/(b) — carried here below, rescoped); (3) the TEAMS full-history
> backfill (fully covered, not repeated here); (4) the legacy-CAS aggregate-manifest-gate question + 205-227 cell
> re-fetch (fully covered, not repeated here); (5) the post-07-13 rebuild-delta reconciliation (fully covered, not
> repeated here); (6) the staleness-budget mirror + hardcoded-workaround grep (fully covered, not repeated here); (7)
> the `check_high_attempted_failed` runbook note (excluding the sibling "re-check once K1/K2 DELETE executes" sub-part —
> carried here below). Nothing below duplicates any of the 7.
>
> **Staleness correction (2026-07-25, finding C)**: verifying each item's cited detail doc against its CURRENT status —
> not just carrying forward the parent's text — found 4 items the parent's Track S2 section described as live open work
> that are actually already resolved and archived. These are kept as closed digests below (not re-created as open todos)
> so the fact they were once tracked here stays visible.

## Todos

- [ ] [DATA] P0. BLOCKED-PREREQUISITES — **Sports E8 legacy-bucket delete gate stays RED, blocked on the PARENT doc's
      own Track H "schedule + run the CF-8 `available_at` maintenance window" todo** (that todo stays in the parent,
      un-dispatched — a dispatched child cannot `depends_on`+`gate_on_depends` against a LOCAL plan's todo, so this item
      is tagged non-dispatchable instead and must be re-checked by hand once CF-8's window runs).
      `cf_manifest_audit_2026_06_01.py` is RED on both the legacy `market-data-tick-sports` + `instruments-store-sports`
      bucket surfaces; the primary blocker is CF-8's `available_at` backfill (code fix shipped
      `market-tick-data-service@af627b5b`, unit-tested only, not yet run in production — same window as the parent's
      Track H todo, run together). Do not re-dispatch the audit itself until that window runs — 30+ prior re-audits
      reproduced identical RED with zero new information. **Correction (2026-07-25, finding C): the parent's own
      "separately, the L6-legacy-only == 0 gate criterion needs redefining" clause is STALE — that redefinition already
      shipped `unified-trading-pm@10ad5d69a` (2026-07-15, confirmed still live by a 2026-07-23 RE-TRIAGE)**, so CF-8's
      `available_at` fill rate is the ONLY remaining blocker on this item, not two blockers. Detail:
      `sports_cf8_available_at_backfill_regression_2026_07_13.md`. (repo: market-tick-data-service /
      deployment-service). **Done when**: the parent's Track H CF-8 todo is confirmed `[x]` AND a fresh
      `cf_manifest_audit_2026_06_01.py` run is GREEN on both surfaces.
- **[DATA] P0.** Sports IS L6 index regression — **ALREADY RESOLVED, not carried forward as an open todo (finding C,
  2026-07-25).** The parent's Track S2 text described this as a live 3-step fix (base-image rebuild / resume schedulers
  / re-consolidate); the cited detail doc (`sports_is_index_fixtures_job_direct_write_328k_row_cut_2026_07_15.md`, now
  archived, `status: resolved`) shows all 3 steps executed and verified 2026-07-15 (`unified-trading-library@45a43438`,
  `instruments-service@a25cf70d`, `unified-api-contracts@c280e1ff`, `unified-trading-pm@10ad5d69a`), with a 2026-07-23
  RE-TRIAGE confirming the live index has grown monotonically since with no recurrence. The doc's one
  genuinely-still-open residual (P1 forensics: what wrote the pre-launch rows that caused the original regression) is
  already tracked in `sports_consolidated_closeout_aggregated_sources_2026_07_24.md`'s digest — not re-created here.
- **[DATA] P0.** Legacy no-env instruments-store-sports bucket decommission - tracked in
  sports_legacy_bucket_cutover_2026_07_16.md, not here.
- **[OPERATOR] P2.** Manual review of the 88 mis-keyed-duplicate orphan rows' disposition — **ALREADY RESOLVED, not
  carried forward as an open todo (2026-07-26, same "finding C" staleness pattern this plan already flags for 4 other
  items above).** These 88 rows (0.01% of the 2026-07-13 683,592-row dedup cleanup that had no canonical twin to dedupe
  against, left untouched during `market-tick-data-service@55f9e961`'s fix) are genuinely-captured, unique API-Football
  `PLAYER_STATS` rows (100% `capture_status=captured`, spread across 21 leagues, 2020-2026) mis-stamped with
  `service_name=market-tick-data-service` and a blank `asset_group` by the same root-cause bug — real data, not
  corrupted/redundant, so deletion was never the right disposition. The disposition was decided and **executed** the
  same week this bug was found, before this 2026-07-25 plan was even written: `instruments-service@9ce3450e`'s
  `scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py` did a direct canonical rewrite (re-stamp
  `service_name→instruments-service`, `asset_group→sports`), matching this incident family's established rule (twin
  exists → drop the mis-keyed copy; no twin → relabel, never drop — same pattern used by
  `dedup_mtds_instruments_surface_duplicate_rows_2026_07_13.py` and `drop_stale_xg_shots_shot_rows_2026_07_09.py`).
  Independently re-verified live 2026-07-14
  (`plans/archive/2026_07/sports_data_sources_canonical_completion_2026_07_13.md:111-116`): a fresh manifest read
  confirmed 0 remaining `service_name=market-tick-data-service` + `source=api_football` rows. Detail:
  `instruments-service/scripts/restamp_orphan_mtds_player_stats_rows_2026_07_13.py`,
  `plans/archive/2026_07/sports_data_sources_canonical_completion_2026_07_13.md:56-77,111-129`. No further action
  needed.
- [ ] [DOC] P1. **Move the mis-filed DEFI tracking item out of the sports corpus entirely: add "features-service: ban
      `category=defi` in on-disk GCS path reads (`mtds_canonical_reader.py::_legacy_twin()`,
      `eigen_rewards_calculator.py`)" as a tracked `- [ ]` todo in `data_completion_to_100_all_ag_2026_06_21.md`'s own
      todo list** (its real gating plan — this item has nothing to do with sports and was mis-filed under the
      now-archived `sports_manifest_canonicalisation_2026_06_01.md`). Cite that doc's current defi C-GREEN status as of
      the move. (repo: unified-trading-pm, doc edit only — no code change, this todo relocates the tracking). **Done
      when**: the item appears as a real todo in `data_completion_to_100_all_ag_2026_06_21.md` and is removed from
      anywhere it duplicates in the sports corpus.
- [ ] [DATA] P1. **Sports P2a sub-item (a) — G1 non-canonical-league NOISE wipe, audit-then-conditionally-purge.** First
      check whether the ~1,437-league/~106k-row NOISE population is the SAME population as the already-approved
      489-pair/10,869-row §U purge (Track V's non-registry-league decision) — the scale differs by ~10x, so this must
      not be assumed. If the census confirms it is the same population (or a strict superset), execute the
      already-approved purge on the residual (snapshot-first, same pattern as every other purge in this doc family). If
      the census shows a genuinely different population, STOP and report the discrepancy — do not purge an unapproved
      population. (repo: instruments-service). **Done when**: the population-match census is recorded, AND either the
      approved purge has executed on the confirmed-matching residual, or a discrepancy report exists (not both silently
      skipped).
- [ ] [DIAG] P1. **Sports P2a sub-item (b) — G2 2015-2017 zero-captured diagnosis ONLY, do NOT implement a fix.**
      Determine whether the 2015-2017 zero-captured seasons are a subscription-tier limit or a backfill bug. The source
      todo bundled an undecided "then fix" after diagnosis (subscription-tier-limit-vs-backfill-bug fix paths differ) —
      that fork stays human; this todo is diagnosis-only, mirroring the same diagnosis-only pattern already used
      elsewhere in this doc family (e.g. Track O's `[DIAG]` items). (repo: instruments-service, read-only). **Done
      when**: a written finding states which of the two causes applies, citing evidence — does NOT implement either fix
      path.
- [ ] [DATA] P1. **Sports P2b — reference sources + odds history 2015→present, never started.** Extend the
      golden-window-proven honest-coverage recipe (weather, soccerfootball_info, transfermarkt, understat, footystats,
      odds-api) to full 2015→present within each source's own `coverage_start`; season-aware smart-skip only (typed
      `EXPECTED_*` reasons, never blanket re-fetch). (repo: instruments-service). **Done when**: a fresh coverage census
      shows each of the 6 named sources extended to its own `coverage_start`, with 0 un-typed skip reasons.
- [ ] [DATA] P2. BLOCKED-PREREQUISITES — **Sports P2c — features history backfill to ML-ready, blocked on the P2a and
      P2b todos above landing first.** Extend the features-service sports feature matrix from the golden window
      (2025-09-01..11-30) to 2015→present once P2a/P2b land. (repo: features-service). **Done when**: P2a/P2b are both
      confirmed done AND the features matrix extension completes with a fresh coverage census cited.
- [ ] [REVIEW] P2. BLOCKED-PREREQUISITES — **Sports P2d — final e2e gate stamp, deliberately deferred, blocked on the
      P2a/P2b/P2c items above.** R3-daily/R4/R5 sub-items already shipped/verified; R1/R2/R3-history remain blocked
      pending P2a+P2b+P2c — re-run this gate once those land, don't mark it DONE early. (repo: unified-trading-pm).
      **Done when**: P2a/P2b/P2c are all confirmed done AND the gate re-run passes.
- [x] ✅ [OPERATOR] P2. **Unresolved cefi-before-sports gate TENSION, never ruled** (flagged 2026-07-14, still open).
      `instruments_foundation_completeness_2026_06_24.md` states sports does NOT start its G1→G5 until cefi is DONE, but
      cefi's own G4/G5 were still open when this coordinator's G1 noise-wipe work executed (2026-06-28). Unclear whether
      the 2026-06-27 re-homing was an implicit operator override. (repo: unified-trading-pm, decision record). **Done
      when**: the operator has ruled on whether the re-homing was an intended override. ✅ **RULING (2026-07-26):
      retroactively BLESSED as an intended exception, not remediated.** The 2026-06-27 re-homing was a workspace-wide
      infra migration (epic VMs → role-based dispatch), not a sports-specific override, but a direct 2-days-earlier
      TRADFI precedent (`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md:169-171`, operator-dispatched ahead of
      cefi-first ordering 2026-06-25) already establishes the standing rule: reversible/audit-class work proceeds
      regardless of cefi's gate state; irreversible/expensive operations stay gated on cefi DONE. The sports G1 wipe
      matched that pattern exactly (snapshot-first, reversible). cefi/sports share no storage/manifest surface, so no
      contamination was possible by construction, and no harm traceable to the sequencing has surfaced since. Full
      ruling + standing rule recorded at the source SSOT: `instruments_foundation_completeness_2026_06_24.md`'s
      TENSION-flag section (now marked RESOLVED). No remediation needed — the already-executed G1 work stands.
- **[REVIEW] P0.** Fixtures-entity-split live-freeze contradiction (`instruments-service@e1524d21`'s
  `_read_fixtures_entity_with_schedule_fallback`) — tracked to completion in
  `sports_legacy_fixtures_path_migration_2026_07_24.md`, not here; that plan's Phase 1 measures the exact load-bearing
  subset before any data moves.
- [ ] [VERIFY] P0. BLOCKED-PREREQUISITES — **FINAL full-history zero-missing (R1/R2/R3), bounced 6× as of last check.**
      Gate: 0 `expected_unattempted_pending_fetch`, 0 blank-reason, 0 un-evidenced `attempted_failed` for every (source,
      data_type) within coverage windows, plus features ML-ready. Do NOT fetch the `api_football ×     ODDS eu=89,073`
      slice if it resurfaces — impossible-not-fetchable denominator pollution pending a purge/retype pass, not real
      work. (repo: instruments-service). **Done when**: the full gate above passes corpus-wide.
- [ ] [DATA] P2. BLOCKED-PREREQUISITES — **Features recompute for enriched dates, gated on
      `sports_satellite_ao_dispatch_batch2_2026_07_24.md`'s INJURIES 94-league enrichment backfill landing first** (that
      plan is itself AO-dispatched and still in flight — re-check its status before dispatching this todo). After
      full-history AF enrichment lands, re-run sports features with force/no-skip for the enriched dates
      (`derived_features` + `fixture_features` only; `odds_features` unaffected). (repo: features-service). **Done
      when**: the INJURIES enrichment is confirmed done AND the forced re-run completes for the enriched dates.
- [ ] [VERIFY] P2. BLOCKED-PREREQUISITES — **ML-readiness re-verify, transitively gated behind the features-recompute
      todo above.** (repo: unified-trading-pm). **Done when**: the features-recompute todo above is confirmed done AND
      the ML-readiness re-verify passes.
- **[INFRA] P2.** `exit_code_fleet_monitor` CLEAN-misclassification — **ALREADY RESOLVED, not carried forward as an open
  todo (finding C, 2026-07-25).** The parent's Track S2 text described this as live open work; the cited detail doc
  (`exit_code_fleet_monitor_clean_misclassifies_premature_kill_2026_07_21.md`, now archived, `status: resolved`) shows
  both fixes shipped: `deployment-service@2e22c54` (defensive CLEAN-classification check) and
  `deployment-service@6671f02` (preemption-marker write hardening).
- **[DATA] P3.** Season-cache-0-fixtures gap investigation — **ALREADY RESOLVED, not carried forward as an open todo
  (finding C, 2026-07-25).** The cited detail doc
  (`api_football_enrichment_stale_ns_fixture_status_and_gate_reader_inconsistency_2026_07_19.md`, now archived,
  `status: resolved`, 10/10 todos done) shows the gate-reader root causes fixed,
  `resolved_by: instruments-service@4ef4cfeb`.
- **[DATA] P3.** WEATHER layout mismatch — **ALREADY RESOLVED, not carried forward as an open todo (finding C,
  2026-07-25 — resolved literally today).** The cited detail doc
  (`sports_weather_uac_layout_per_day_bare_vs_writer_per_day_per_league_2026_07_20.md`, now archived,
  `status: resolved`) shows `SPORTS_DATA_TYPE_LAYOUT["WEATHER"]` aligned to `PER_DAY_PER_LEAGUE`,
  `resolved_by: unified-api-contracts@b73c95d5` (2026-07-25).
- [ ] [DATA] P3. BLOCKED-PREREQUISITES — **sports/trades `DP_RUN_MOSTLY_EMPTY` post-DELETE re-check, gated on the
      parent's Track V K1/K2 legacy-object DELETE (`[OPERATOR]`-gated) executing first.** Not a live defect (the 87.2%
      ratio spike is a K1/K2 denominator-shrink artifact on already-dead residue, not a new outage) — this is just the
      re-check once that DELETE lands. Filed: `sports_trades_attempted_failed_2026_07_23.md`. (repo: deployment-service,
      read-only once unblocked). **Done when**: the parent's K1/K2 DELETE todo is confirmed `[x]` AND a fresh ratio
      check confirms the spike resolves as predicted.
- **[DOC] P2.** `sports_features_layer_findings_sweep_2026_07_18.md` is NOT closed by this plan or by the parent
  closeout — 73 open todos there are the features-layer correctness backlog, deliberately not duplicated here (too large
  to fold in). Do not treat sports feature-layer correctness as done when this closeout or this child archives; that doc
  tracks its own, separate completion.

## Codex SSOTs

`/codex/02-data/availability-manifest-and-data-status.md`, `/codex/02-data/honest-absence-downstream-handling.md`,
`/codex/05-infrastructure/vm-preemption-and-billing-waste-monitoring.md`. Plan↔codex drift is review-blocking.
