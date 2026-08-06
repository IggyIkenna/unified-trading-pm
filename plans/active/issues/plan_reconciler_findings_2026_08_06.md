---
doc_type: issue
title: Plan reconciler findings — sports tranche (agt-132fc8)
summary:
  Run-findings doc for the sports-tranche sharded daily reconciliation (dispatch agt-132fc8, 2026-08-06). Hunter fan-out
  DETECT → adversarial VERIFY → apply confirmed → route hard items. Live journal for the run.
status: open
resolved_by:
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, findings, sports, reconciliation]
related: [/plans/epics/sports_master.md]
parent_epic: sports_master
priority: P2
assigned_vm: NA
created: 2026-08-06
author: plan_reconciler
source: agt-132fc8
locked_by: plan_reconciler
---

# Plan reconciler run-findings — sports tranche (agt-132fc8)

> Live journal for the 2026-08-06 sports-tranche reconciliation shard. Sections are appended as the run progresses.
> Normative refs (PLAN_FORMAT.md / task_template.md / INDEX.md / ACTIVE_INDEX.md) + codex stay in scope per the
> sharded-run contract; audit corpus = `asset_group: sports` docs in `plans/active/` + `plans/active/issues/` +
> `plans/epics/sports_master.md`.

## Coverage (hunters / batches / docs)

**Corpus** (2026-08-06, from `rg -l '^asset_group:.*sports'` over `plans/active/` + `plans/active/issues/` +
`plans/epics/`): 82 docs = 1 epic (`sports_master.md`, 168.5 KB) + 28 active plans + 53 issues. **Non-grace working set
= 53 docs (1.96 MB)**, grace set (newest git change <12h, context-only) = 29 docs + this findings doc.

**Hunter fan-out plan (10 hunters, all read-only, sonnet, SUB_AGENT_MANDATORY_RULES injected):**

| Hunter            | Batch                         | Docs                                                                                                                                                                                                                                                                                                                                                                                                           | Size       |
| ----------------- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------- |
| A (epic-cluster)  | closeout core                 | sports_consolidated_native_ao_extract (main GRACE + finalize), sports_closeout_track_s2_foldin (+finalize), sports_closeout_track_x_hygiene (+finalize), sports_closeout_exchange_fixed_odds_fork (+finalize), sports_track_h_denominator_gated, sports_track_h_denominator_prereqs                                                                                                                            | 10         |
| B (epic-cluster)  | data completion               | data_completion_sports, predictions_ml_walk_forward_and_arb, sports_arb_decay_window_and_alpha_gate_design, sports_odds_feature_naming_canonicalization, sports_canonical_universe_and_apifootball_reference_expansion, sports_catalog_league_grain_only_scope, sports_group_c_execution_backtest_harness                                                                                                      | 7          |
| C (epic-cluster)  | satellite AO + features sweep | sports_satellite_ao_dispatch_batch5, batch9_finalize, data_pipeline_check_mdps_features_finalize, sports_features_layer_findings_sweep (+part2, part3)                                                                                                                                                                                                                                                         | 6          |
| D (epic-cluster)  | odds API cluster              | sports_odds_api_scattered_multiyear_gaps, sports_batch_odds_api_capture_outage_recurrence_check, sports_odds_venue_enumeration_undercount_predrain, sports_odds_stale_fixture_reinjection, mtds_sports_odds_api_force_fetch_no_parquet, sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured, sports_odds_feature_naming_four_way_mismatch, sports_halftime_odds_sfi_vs_inplay | 8          |
| E (epic-cluster)  | estate/instruments            | estate_orphan_assessment, instruments_remaining_work_audit, mtds_is_full_adapter_smoketest_findings, instruments_service_sports_footystats_uac_overlap_qg_red                                                                                                                                                                                                                                                  | 4          |
| F (epic-cluster)  | recon/stats/fixtures          | sports_cf8_available_at_backfill_regression, sports_stats_delayed_live_capture_still_dead_post_fix, sports_fixtures_schedule_wrong_schema_day, candle_feature_canonical_path_divergence, sports_peripheral_bucket_league_vocabulary_contamination                                                                                                                                                              | 5          |
| G1 (epic-cluster) | ops/mdps                      | autonomous_session_operator_decisions, mdps_sports_honest_absence_writes_fail_fetchevidence_gate, mtds_pipeline_check_process_killed_during_skip_leg_poll, mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp, ml_training_and_prediction_pipeline_launchers_stale_post_consolidation, mdps_features_deadcode_consolidation, sports_catalog_dp_catalog_001_junk_name_crash                             | 7          |
| G2 (epic-cluster) | fetch/manifest/coverage       | footystats_matches_predictions_fetch_gaps, sports_dependency_check_manifest_vs_gcs_path, backfill_smoke_write_path_canonical_audit, adapter_findings_gcs_manifest_deployment_api_reconciliation_gap, sports_index_recency_masked_captured_atoms, phantom_audit_estate_coverage_gap                                                                                                                             | 6          |
| EPIC              | epic hub                      | sports_master.md in full + closeout cross-check                                                                                                                                                                                                                                                                                                                                                                | 1 (168 KB) |
| CODEX             | codex-alignment               | Codex SSOTs sections of 12 sports plans + 2 known-broken refs (sports-canonical-league-cup-registry, plan-completion-and-archival-discipline)                                                                                                                                                                                                                                                                  | 12 plans   |

**STEP-1 hygiene inputs** (sweep 2026-08-06 21:51 UTC): 4 hard failures — reference-path format 83 (baseline 81),
existence 88 (86), AG-closeout linkage 75 orphans (69), terminal-status-archived 3 (0); archive-candidates ratchet RED.
All corpus-wide ratchets — flagged, not sports-fixable in this shard. Sports-relevant flags: 2 BROKEN codex refs (see
CODEX hunter), 2 estimate DRIFTs (`sports_satellite_ao_dispatch_batch9/10_finalize`, 50% infra), 1 priority-tier WARN
(sports_odds_stale_fixture_reinjection P1), INDEX.md drift 19 (corpus-wide, not sports-owned).

**Cross-slot observation (noted, not touched)**: the ROOT PM clone (`unified-trading-pm`, not this slot) is checked out
on the ci-tranche reconciler's review branch `plan_reconciler/agt-a304c9` (PR #2400 open, committed work pushed) with
leftover staged WIP (`plan_reconciler_ci_late_findings_2026_08_06.md` staged-mod + untracked
`ag_closeout_audit_ci_parked_2026_08_06.md`). Not this run's work — left untouched, reported for awareness only.

## Flips verified

## Contradictions

## Doc-drift

## Hygiene fixes

## Filed

## Archive candidates (operator review)

## Refuted (dropped by verify)

## Plans not reached

---

## Hunter results — 10/10 complete (2026-08-06)

All 10 hunters returned (A,B,C,D,E,F,G1,G2,EPIC,CODEX — sonnet, read-only, full-doc reads, no writes). Every non-grace
sports doc was read in full by exactly one hunter; the epic was read by the EPIC hunter + cross-checked by 6 batch
hunters (zero doc↔epic track/status contradictions on batch docs; the epic's OWN listing drift is flagged below).

## Candidate registry (deduped; verify status as of 2026-08-06 22:30 UTC)

**V-wave 1 in flight (adversarial pairs, 6 agents):**

- **V1 [P0]** odds-api launch-readiness cross-doc contradiction —
  `sports_batch_odds_api_capture_outage_recurrence_check_2026_07_26.md:279-280,294` ("NOT YET LAUNCHED (corrected
  2026-08-02 … both gates are clear)") vs `sports_odds_api_scattered_multiyear_gaps_2026_07_27.md:163-170,173,181-183`
  ("BLOCKED-CREDENTIALS 2026-08-02: OUT OF USAGE CREDITS, `x-requests-remaining: -772`, /v4/historical 401 since 08-01
  12:40:24Z" + an embedded "UNBLOCKED 2026-07-31 … launch the backfill" directive inside the same P1) vs
  `mtds_sports_odds_api_force_fetch_no_parquet_2026_08_01.md:183-189` (same 401 evidence). Acting on doc A launches a
  backfill whose every call 401s. → cross-doc banner fix + operator notify.
- **V2 [P1]** false-progress flip — `sports_closeout_track_s2_foldin_2026_07_25.md:391` features-recompute `[x]` flipped
  at launch (slot-4, 08-06) while Progress Log :521-528 records VM `fts-backfill-20260806-012831` still RUNNING (~1h in
  at 02:34Z, no exit signal); done-when ("VM exit 0, manifest rows written") unmet; slot-13 reverted the identical
  pattern earlier the same day (:460-461); also `--force` (:398) vs `--redo-all` (:517) discrepancy on the same
  relaunch. → revert + note.
- **V3 [P1]** false-progress flip — `candle_feature_canonical_path_divergence_2026_07_20.md:317` todo 3 `[x]` "✅
  VERIFIED 2026-08-04" while its own continuation (:329-330) + Progress-Log audits (:533-535, :589-593) say the ~7.1M
  TradFi leaf-id repair is unresolved pending an operator ruling. → revert or adjudicate.
- **MECH-1a/1b/2 (3 confirmer agents, in flight)** — ~35 mechanical edits: frontmatter last_updated (~19 docs), statuses
  (sports_index_recency → resolved; sports_catalog resolved_by clear), counts (process_killed 2/2→3/3; fixtures_schedule
  85→≥86; halftime banner 5→3; batch5 12→11), stale summaries/titles (cf8, force_fetch, scattered_multiyear_gaps),
  banners (track_x draft; finalize draft), path repoints (~15: mdps_features×4, catalog_league_grain×3,
  group_c+odds_feature_naming, dependency_check×2, backfill_smoke×2, convention `../`×7, canonical_universe
  p2_history×2, footystats×2), codex-ref plan-side fixes (batch10_finalize — GRACE-deferred; canonical_universe:424 —
  wave 2), epic 8-item drift (E1-E8).

**Wave-2 verify (after wave 1):** V4 stats_delayed recommended-decision banner · V5 sweep-part2 K0-DECISION banner · V6
canonical_universe floor banner · V7 audit §1.3 count fix · V8 canonical_universe:424 codex-ref repoint.

**Refuted (dropped by verify, no flip):** all 15 missed-flip candidates across hunters carry their own counter-evidence
— operator-gated (canonical_universe:319 E8 `--drop-stale` BLOCKED-OPERATOR; cf8:357 BLK-d9137d48 STOP; halftime:197
cutover-gated), prereq-sha-only (arb_decay:144, group_c:77, batch5:116, sweep:604, footystats:173, data_completion:414,
backfill_smoke:284), or genuinely open per the doc's own notes (smoketest:358 FLUID, audit:825 umbrella, estate:344,
part2:211/:758, stale_fixture:246, batch_odds:279). **prereqs:118 (batch_footystats copy+swap) =
reported-done-unflipped** — fresh census 0 non-registry rows, 15,980/15,980 verify PASS, only ship-mechanics pending
(RB-166e706f) — SOFT self-report only, no HARD evidence chain in-session → FILED, not flipped.

**P1 route (owner decision):** `mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` —
`assigned_vm: planning` + `execution_scope: orchestrator-agent` with ZERO checkboxes (verified by grep: 0
`- [ ]`/`- [x]`); remediation exists only as prose (:130-141) so the AO can never ingest a data-correctness masking
defect. Fix direction (convert prose→todos vs flip NA) is a content call → route to owner.

**Archive candidates (operator review):** (1) `instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` —
superseded duplicate physically in active/issues, zero-checkbox by design, `locked_since: 2026-05-21` predates
`created: 2026-07-30` (impossible lock metadata — copy-paste; lock blocks auto-archive → ASK); refs from
`zero_checkbox_sweep_all_tranches_2026_07_31.md`, `ag_closeout_audit_sports_tooling_followups_2026_08_06.md`,
`docs_reconcile_operator_decisions_2026_08_02.md` (sports/cross-tranche referrers noted). (2)
`sports_index_recency_masked_captured_atoms_2026_07_13.md` — all 7 todos done; status→resolved + archive after fix.

**Epic drift (EPIC hunter, 8 items, non-grace 52h):** E1 golden-window coordinator banner → dead superseded coordinator
(:67-75; :20/:71 wrong `../active/` paths) · E2 Assigned-listing: 6 archived-complete plans shown "active"
(:1387-1430) + "16 active plans" vs measured 25 (:1382) + 17 actual plans missing — section is SCRIPT-GENERATED
(`scripts/plans/populate_epic_bodies_2026_05_21.py`), no epic filter → hand-edit sports_master only + flag fleet re-run
· E3 SFI backfill BLOCKED-ON-FREEZE stale (:1351-1353; freeze lifted 2026-07-17) · E4 P0 "DO NOT resume FWD/BACKFILL
VMs" self-contradictory (:448-449; Phase 2 complete 05-23, Phase 4 resumed) · E5 master-plan cross-refs wrong path +
"KEPT ACTIVE" false claim (:1546-1549) · E6 last_updated (:62) → 2026-08-02 · E7 critical-path "Phase 1 partial" (:367;
all phases complete) · E8 dangling `plans/ai/` ref (:1550, dir gone).

**Grace-deferred:** `sports_satellite_ao_dispatch_batch10_2026_08_06_finalize.md` codex-ref path swap (3h — GRACE;
`codex/11-project-management/plan-completion-and-archival-discipline.md` → `12-agent-workflow/…`, verified moved) ·
native_ao_extract draft banner + last_updated (GRACE, context-only).
