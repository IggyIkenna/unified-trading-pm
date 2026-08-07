---
doc_type: issue
title:
  "plan_reconciler run findings — 2026-08-07 cefi tranche shard (agt-8ce897): flips verified, contradictions/doc-drift
  routed, hygiene fixes applied"
summary: >-
  Daily deep plan-reconciliation, cefi tranche only (94 cefi-tagged docs in plans/active+issues + cefi_master epic +
  normative refs + codex). Fan-out DETECT via read-only hunter sub-agents, adversarial VERIFY (refuter + confirmer),
  then apply only confirmed fixes on review branch plan_reconciler/agt-8ce897. 4 hygiene-sweep hard failures
  (reference-path ratchet 83/81, AG-closeout linkage 77/69, terminal-status-archived 4/0, archive-candidates) are the
  Phase-0 mechanical feeds; 8 inventory orphans + INDEX drift 21 noted. Grace set (38 cefi docs, <12h) read-only. Final
  counts and the Phase-5.9 ledger live in the sections below.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, run-findings, cefi, sharded]
related: [plan_reconcile_autonomous_sweep_2026_07_30, zero_checkbox_sweep_all_tranches_2026_07_31]
created: 2026-08-07
author: plan_reconciler
parent_epic: plan_hygiene_master
priority: P2
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: NA
drift_direction: none
source: agt-8ce897
depends_on: []
resolved_by:
locked_by: plan_reconciler
---

# plan_reconciler findings — 2026-08-07 (cefi tranche, dispatch agt-8ce897)

Run journal + presentation doc. Sections appended as the run progresses.

## Run metadata

- Dispatch: `agt-8ce897`, slot 12, branch `plan_reconciler/agt-8ce897`
- Tranche: `cefi` (asset_group: cefi → 94 docs in plans/active + issues/; epic `plans/epics/cefi_master.md`; normative
  refs + codex stay in scope per SKILL.md)
- Grace set (read-only, newest change <12h): 38 cefi docs — listed in Coverage section
- Hygiene sweep: 4 hard failures (reference-path 83/81; existence 92/86; AG-closeout linkage 77/69;
  terminal-status-archived 4/0; archive-candidates 0), 8 inventory orphans, INDEX drift 21

## Phase-0 mechanical feed (itemized, adjudicated subset)

Adjudicated inline from the sweep report (2026-08-07 00:14 run) — cefi-tagged subset only:

- **Terminal-status-archived (4, baseline 0): ALL NON-cefi** — sit_stamp_skipped_on_detached_head_pinned_sha_2026_08_06
  (resolved), sports_mtds_backfill_vm_unscoped_fetch_oom_2026_08_06 (resolved),
  omniroute_multi_provider_routing_evaluation_2026_08_03 (superseded),
  tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25 (complete). Owned by sibling tranches; not touched here.
- **AG-closeout linkage (77 vs baseline 69): cefi orphans = 7** — 4 in grace set (cefi_book_snapshot5…,
  cefi_derivative_ticker_tardis_resolver…, cefi_liquidations_attempted_failed…, plan_reconciler_findings_2026_08_07
  [this doc, expected]) + **3 writable**:
  features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27,
  mtds_cefi_docker_image_stale_5mo_2026_07_30,
  mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02. Corpus-wide regression already tracked
  in ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06 (grace).
- **Reference-path ratchet (format 83/81, existence 92/86): ZERO violations in cefi-tagged plans/active docs** — the 39
  plans/active hits are scratch_scenarios_day1 (defi) + sports/infra/ao/cross-cutting docs. Standing issue:
  reference_path_convention_2026_07_23.
- **Inventory orphans (8): cefi-tagged count TBD** — H5 mechanical adjudicator verifying.
- **Archive candidates: 0** (0 locked / 0 archivable) — nothing to do this run.

## Flips verified

<!-- appended as STEP 4/5 confirms -->

## Zero-checkbox sweep (cefi, H6 result — pending STEP-4 verify)

Zero-checkbox docs in writable cefi set: **2** (both prose-work; register already lists both as NEW/unclassified in its
2026-08-06 measurement):

1. `plans/active/issues/mtds_pipeline_check_enumerate_shards_masks_cefi_sports_mvp_2026_08_06.md` (assigned_vm:
   planning, AO-eligible) — proposed conversion: 2× `[SCRIPT] P1` (CEFI/SPORTS override in `_venue_data_type_is_mvp()`
   mirroring `_TRADFI_MVP_SHARDS`; per-asset_group fallback in the last-resort enumerate) + 1× `[REVIEW] P2` re-run of
   the full-matrix invocation as done-when.
2. `plans/active/issues/mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` (assigned_vm: NA,
   local-only) — proposed conversion: `[DATA] P1` reproduce with strace/py-spy to capture the signal, `[REVIEW] P1`
   check systemd/loginctl idle-session-reaper policy (needs VM-level access), `[OPERATOR] P2` host-wide
   install-pkill-guard-shell-env.sh if cross-slot pkill confirmed.

Grace-set zero-checkbox docs: 0. finished-record / informational / ambiguous: 0 each. Verification + conversion
application in STEP 4/5; the standing register (`zero_checkbox_sweep_all_tranches_2026_07_31.md`) gets its two
NEW/unclassified rows classified at apply time.

## Mechanical adjudication (H5 result — pending STEP-4 verify)

- **AG-closeout linkage: 6 REAL cefi orphans (P2 each), not checker artifacts.** 3 writable:
  `issues/mtds_cefi_docker_image_stale_5mo_2026_07_30.md`,
  `issues/mtds_live_mode_never_touches_authenticated_tardis_datasets_endpoint_2026_08_02.md` (both
  `parent_epic: cefi_master`, related-edges all archived/codex), and
  `issues/features_universe_filter_settlement_suffix_and_vm_tarball_staleness_2026_07_27.md` —
  **`locked_by: live-defi-rollout` → lock-protocol, operator-routed, NOT auto-fixed**. 3 same-tranche but in GRACE set
  (deferred, filed): `issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28.md`,
  `issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28.md`,
  `issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30.md` (related-edges all archived/codex). The
  closeout family's own 2026-08-02 linkage-gap fix (aggregated_sources:776) added only 2 docs — these 6 are pre-existing
  gaps it missed. Fix shape for writable ones: add family `related:`/body mention resolving to
  cefi_consolidated_closeout_2026_07_18 / _aggregated_sources_2026_07_24.
- **Terminal-status-archived: ZERO cefi hits confirmed** (sit_stamp=cross-cutting, sports_mtds=sports, omniroute=ao,
  tradfi_batch2=tradfi — all read from frontmatter).
- **Reference-path: ZERO cefi hits confirmed** in plans/active + issues (12 unique active-dir docs with dangling refs,
  all sports/infra/cross-cutting/ao; scratch_scenarios_day1 format hits are asset_group-less scratch docs).
- **Inventory orphans (8): exactly 1 cefi-tagged** —
  `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02_finalize.md` (P3, real: mtds_mdps_master epic exists
  but 0 refs to it) — **in GRACE set → deferred, filed**; fix = reference in owning epic.
- Side-effect: H5's sanctioned inventory regen re-wrote
  `plans/archive/2026_07/active_plan_inventory_dashboard_2026_07_24.md` (dirty, regenerable; left uncommitted).

## Moved-doc referrer hits (H9 result — existence-VERIFIED inline)

48 cefi-tagged findings: **17 P1 live referrers** (13 writable — existence-verified: old path gone, archive path
present; applied in STEP 5) + **4 P1 grace-set referrers** (deferred+filed: cefi_track7_candle_namespace_residual:138,
cefi_book_snapshot5:239, mtds_qg_red_combined_coverage_shortfall:27/65) + **2 P2 display-text-only**
(aggregated_sources:171/204, grace) + **29 P2 archived referrers** (gate-excluded by the 2026-08-02 ruling; filed as one
class — full list parked in the hunter report; candidates for a corpus-wide sweep, not this shard). Zero dangling-ref
candidates from cefi referrers. Adjacent (codex, meta): `codex/02-data/defi-data-pipeline.md` cites
`/plans/archive/2026_08/hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` — the doc never moved (still
`plans/active/…`); wrong-path citation → ROUTED (codex edit, operator).

Writable P1 repoints to apply (old→new, all existence-verified):

- cefi_e4_e8_orphan_sweep_gapfill_rebuild_execution_2026_07_28.md:283 →
  plans/archive/issues/cefi_hardstop2_carveout_codex_vs_plan_contradiction_2026_07_29.md
- data_completion_cefi_2026_07_15.md:474/541/733 → archive/issues/cefi_e6_cf7_relabel…,
  archive/2026_08/mdps_candle_manifest_near_total_coverage_gap…,
  archive/issues/cefi_instruments_store_blank_data_type_residual…
- candle_feature_canonical_path_divergence_2026_07_20.md:497/505 →
  archive/2026_08/infra_satellite_ao_dispatch_batch2_2026_07_27.md
- instruments_docs_audit_outstanding_items_2026_07_08.md:51 →
  archive/issues/instrument_id_format_canonicalization_2026_07_08.md
- instruments_remaining_work_audit_2026_07_10.md:609 →
  archive/issues/defi_dead_storage_shape_b_cleanup_candidate_2026_07_10.md
- mdps_features_deadcode_consolidation_2026_07_20.md:90/96/104/110 →
  archive/2026_08/infra_satellite_ao_dispatch_batch2_2026_07_27.md
- plans/audit/results/data_pipeline_reconciliation_cefi_2026_08_06.md:170 →
  archive/issues/cefi_bare_okx_venue_removal_2026_08_04.md

## Codex-alignment (H7 result — pending STEP-4/6 routing)

- **P1 SSOT STALE**: `codex/02-data/cefi-capture-universe.md:208-220` carries the reversed 2026-07-17 "accept 50.79%"
  verdict as live; closeout RULING 2026-07-18 reversed it and track2 backfill resumed (VM launched 2026-07-27). Codex is
  the stale side → ROUTED (operator-ruled codex edit). Plan-side stale framing feeding it:
  `issues/cefi_residual_followups_after_honest_done_2026_07_17.md:5` (writable) opens "CLOSED at honest-done … 50.79%"
  with no reversal note → plan-side fix (reversal banner) in STEP 5.
- **P1 SSOT STALE**: `codex/02-data/data-lineage-MTDS-features-ml.md:123-131` "on-chain-perp candle gap still open /
  deliberately deferred" — plan documents DONE 2026-07-26 for 3/4 venues (aster_and_cefi_rolling_adv_feature:177-183;
  ASTER residual = manifest-registration gap). → ROUTED (codex edit, operator).
- **P2 codex↔codex**: cefi-capture-universe.md:139-142 (BINANCE-DELIVERY in MVP scope, 2026-06-24 status) vs
  cross-asset-canonical-target-ssot.md:468 (descoped from MVP, kept registered, 2026-07-18) — stale half is
  cefi-capture-universe → ROUTED.
- **P2 PLAN WRONG**: cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md:116-137 Phase-2 todo mandates retired
  EQUITY_PERP/TOKENIZED_EQUITY stamping vs SSOT (operator 2026-07-16: PERPETUAL only) AND the plan's own STATUS banner
  (:143-149, fix DONE). Todo checkbox still `[ ]` — align todo text to the ruling; cross-check H4 missed-flip before
  editing (same file).
- **P2 unresolvable ref**: `codex/CLAUDE.md` cited at instruments_satellite_ao_dispatch_batch1_2026_07_27.md:220 (also
  deployment_registry_firestore_p5_verify:88, pipeline_mode_source_batch_live_replay_standardisation:305) — no such doc;
  narrative pointer to a moved doc → filed, no safe target.

## Topic contradictions (H8 result — routing classified)

- **C1 P1 — instrument_id non-canonical share 16.67% vs ~44.3% on the same 11.19M manifest** (closeout:423-424 vs
  aggregated_sources:732, child worklist sums ~43.7%). Both presented as live measurements; unresolvable from the record
  without a re-measure → ROUTED (operator; aggregated_sources in grace).
- **C2 P2 — Track-2 ETA ~1-2 days (closeout:14/222) vs measured ~30 days (track2 checkpoints:198)** — correction
  documented in the fork; parent digest summary uncorrected → annotate closeout (writable).
- **C3 P3 — deribit options_chain af=10,114 (blocker doc title) vs 112,727/113,615 family reads** — blocker doc in
  GRACE; its own note (:104-108) flags the title as NOT durable → filed (post-grace).
- **C4 P2 — LIGHTER-ZKSYNC "does NOT fetch from datasets.tardis.dev" (skill §3 + CLAUDE.md) vs "use the Tardis archive
  (from 2026-04-17)" (onchain_venues:130-135)** — guard doc's own resolution (:108-110: removed from
  TARDIS_CAP_EXEMPT_VENUES 2026-07-30) corroborates onchain_venues; the STALE sides are CLAUDE.md + the skill → ROUTED
  (doc-drift, normative docs, operator).
- **C5 P1 DATA-CORRECTNESS — track-7 delete gate "delete ONLY after bundles verified complete" (residual:77-80) vs
  deletion confirmed while 96/112 cells MISSING (candle_bundle_regeneration_vm:62-64/136-138); the 2026-08-06 flip cited
  404s not bundle-completeness verification** → ALERTED (P0-class, /blocked) + filed; both docs in grace.
- **C6 P2 — UPBIT "VERDICT: FAIL … Tardis-only coverage" (closeout:533) vs "PIPELINE STOPPAGE (restorable), data IS
  available" (upbit_cefi_data_gap_may:145-152)** — newer issue establishes root cause → annotate closeout:533 with
  pointer (writable); verdict itself not reversed.
- **C7 P3 — E4 orphan-sweep population ~1.2M (data_completion:427, aggregated_sources:570) vs measured 287,074
  deleted-verified (e4_e8_execution:158-161)** — execution SSOT documents correction → annotate data_completion:427
  (writable); aggregated_sources in grace.
- Verified consistent (no action): DERIBIT misclassification census; track-2 preemption facts; 50.79% reversal chain; E6
  CF-7 11.61% measurement; hyperliquid/aster migration 7,599 objects.

## STEP-4 inline verification results

- H4 flip evidence chain: instruments-service@97801b5d + @766549c7 ANCESTOR-OK; unified-api-contracts@989e9d16
  ANCESTOR-OK; `_DRYRUN_COLS` includes "chain" (dedup script:219); quarantine.py has PACIFICA-SOLANA (10 hits) ✓.
- mdps@6ce1a25 NOT resolvable on current origin (pre-2026-08-05 history-rewrite sha) — relevant only to
  candle_feature:442 which stays open anyway (its own text: count deliverable not produced; "todo itself stays open
  pending that measurement").
- candle_feature:442 → NOT a flip (doc self-documents remaining deliverable). cefi_track2_finalize:69 → HARD (baselines
  verified in archived extract doc:121-135, both `[x]` with run evidence).

## Epic-cluster issues batch1 (H2 result — 19 candidates, none P0)

Writable → apply in STEP 5:

- **C2 P2** cefi_residual_followups_after_honest_done:171 — body "residual #3 (10,368-row eu-twin) still OPEN" STALE vs
  todo :516-529 DONE 2026-07-27 (apply ran, 8,778,675 rows, 28,755 dropped, 0 residual) → annotate :171.
- **C3 P2** instruments_remaining_work_audit:162-168 — §1 "12 open todos" vs headline 4 (:130-136) corrected "~2 of 13
  remain" → align §.
- **C7 P3** instruments_remaining_work_audit:50 — `related` cites missing active-path layer1 doc → repoint to
  /plans/archive/2026_07/layer1_remeasure_and_certify_2026_07_06.md (exists).
- **C15 P3** cefi_onchain_perp_batch_venue_allowlist_gap — last_updated 2026-07-12 vs log 2026-08-05 → refresh.
- **C16 P3** estate_orphan_assessment — last_updated 2026-07-21 vs log 2026-08-06 → refresh; **C6 P3** annotate
  na-eligibility "6+8 remain genuinely NA" with todo-8 DONE 2026-07-30.
- **C17 P3** honest_coverage_shard_dimension_model — vitest 21/21 vs 43-test claims (different runs; no re-run this
  shard) → REPORTED, no fix; last_updated refresh.
- **C19 P3** mtds_is_full_adapter_smoketest_findings:110-113 — §2 matrix rows unbannered vs resolved todos (huobi
  RESOLVED 2026-07-12, polymarket fixed uac@42ce2de3/mtds@f4a118be) → add resolution banners; last_updated refresh.
- **FALSE-UNCHECKED** estate_orphan_assessment todo 3 (:108, :545-548 — all 4 AG sweeps COMPLETED, apply converted
  637,523 vs dry-run 637,724) → inline-verify + flip.
- **C18 P3** mtds_backfill_vm_memory_hang_large_chunk — recurrence numbering gap + BLOCKED-CREDENTIALS restoration
  unrecorded → REPORTED, filed (operator confirmation needed), no edit.

Grace-set → filed (deferred): C1 phantom-SHA aaa0866c (instrument_availability_hive_migration, real sha eca688ac… — also
todo-8 DEFAULT-RULED checkbox never flipped), C4/C5/C9/C10 (deribit_combo_perpetual_partition_move: todo carries
ruling+awaiting-answer, resolved_by says open vs todos done, "all 7 done" vs unchecked, archived doc cited at active
path), C8 (cefi_book_snapshot5 body cites predecessor at active dir), C11/C12 (defi_cefi_venue_chain: title
not-root-caused vs ROOT-CAUSED; 35 vs 42 rows), C13/C14 (cefi_track2_backfill_vm_preempted: prose claims a non-existent
[OPERATOR] todo; last_updated), C1-doc last_updated.

## Contradictions

<!-- routed + filed -->

## Doc-drift

<!-- flagged, routed to operator -->

## Hygiene fixes

<!-- applied -->

## Filed

<!-- durable todos/issue refs -->

## Archive candidates (operator review)

<!-- none / listed -->

## Refuted (dropped by verify)

<!-- appended -->

## Coverage (hunters / batches / docs)

- Total cefi-tagged docs: 94 (+ epic cefi_master + normative refs + codex)
- Grace-set docs (read-only): 38 — cefi_satellite_ao_dispatch_batch4_2026_07_31,
  issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30,
  issues/cefi_live_event_cold_compactor_oom_and_legacy_path_check_2026_08_07,
  cefi_satellite_ao_dispatch_batch6_2026_08_02,
  issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27,
  issues/mtds_qg_red_combined_coverage_shortfall_2026_08_05,
  issues/cefi_content_migration_corpus_still_incomplete_relaunch_round3_needed_2026_07_31,
  data_pipeline_check_mdps_features_2026_07_20, issues/cefi_tardis_derivative_ticker_historical_gap_2026_08_04,
  issues/mtds_backfill_launcher_guard_overapplies_to_nontardis_venues_2026_07_28,
  cefi_consolidated_closeout_aggregated_sources_2026_07_24, cefi_satellite_ao_dispatch_batch8_2026_08_06,
  issues/cefi_book_snapshot5_schema_contract_ts_event_levels_mismatch_2026_07_28,
  issues/cefi_derivative_ticker_tardis_resolver_aiodns_hardfail_2026_07_28,
  issues/cefi_track7_candle_bundle_regeneration_vm_2026_08_04, issues/coverage_floor_new_backfill_gaps_found_2026_07_27,
  issues/coverage_floor_registries_no_cross_propagation_2026_07_17,
  issues/deribit_options_chain_af_g4_blocker_2026_07_03, issues/strategy_ml_orphan_coverage_design_gaps_2026_08_03,
  issues/tarball_stale_window_cefi_live_capture_correctness_risk_2026_08_01,
  issues/uac_data_type_validity_combinator_fragmentation_2026_07_07,
  issues/cefi_liquidations_attempted_failed_lifetime_count_stale_2026_07_30,
  cefi_track7_candle_namespace_residual_finalize_2026_07_25,
  issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31,
  cefi_track7_candle_namespace_residual_2026_07_25, issues/cefi_content_migration_fleet_half_incomplete_2026_07_26,
  issues/deribit_combo_perpetual_partition_move_2026_07_21,
  issues/instrument_availability_hive_migration_unrecognized_shapes_and_content_mismatch_2026_08_03,
  hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02_finalize,
  issues/bybit_futures_chain_write_shape_2026_07_13, issues/cefi_track2_backfill_vm_preempted_no_recovery_2026_07_30,
  hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02, issues/ag_closeout_audit_cefi_parked_2026_08_06,
  issues/okx_futures_instid_marker_convention_mismatch_2026_07_30, cefi_satellite_ao_dispatch_batch7_2026_08_03,
  issues/upbit_cefi_data_gap_may_2026_2026_08_04, issues/defi_cefi_venue_chain_axis_contamination_2026_07_28,
  ag_closeout_audit_rollout_2026_07_25
- Writable cefi docs: 56 (94 − 38)

## Plans not reached

<!-- appended if any -->

## Phase-5.9 ledger

- routed_to_operator == parked_in_issue_doc: TBD
- agent_skips == enumerated: TBD (no apply-agents expected — single-writer orchestrator)
