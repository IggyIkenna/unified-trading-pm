---
doc_type: issue
title: "tradfi /ag-closeout-audit 2026-08-19 — parked findings (mistag survey, archive candidates, one cross-agent inconsistency)"
summary: >-
  Companion to `tradfi_satellite_ao_dispatch_batch19_2026_08_19.md`. A 71-agent Phase 1 Workflow classified every
  tradfi-primary candidate doc; this doc carries the findings that don't fit that batch's Deferred taxonomy
  (process/meta corpus-quality observations, not tradfi content work). Headline: 23 of 71 candidates (32%)
  verdicted `exclude_cross_cutting` — almost all are legitimately multi/cross-AG-tagged docs (many already
  self-tagged `cross-cutting` or all-5-AGs) whose tradfi-specific slice has since closed or was always trivial;
  this is the audit working as designed, not a corpus defect, and needs no fix. A genuine minority (4 docs) show
  real tag drift worth a dedicated retag. 3 docs verdicted `archivable_now` (0 genuine remaining work,
  cross-verified against independent sources). One live inconsistency was found between two Phase-1 agents'
  classification of sibling DP_CRON docs.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, ag-closeout-audit, parked-findings, orthogonality, mistag-survey, archive-candidates]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch19_2026_08_19.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch19_2026_08_19_finalize.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_tradfi_parked_2026_08_10.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_tradfi_parked_2026_08_10_r2.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
created: "2026-08-19"
author: "ag_closeout_auditor (dispatch agt-8b4230, slot 29, sharded $TRANCHE=tradfi)"
last_updated: "2026-08-19"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /plans/active/tradfi_satellite_ao_dispatch_batch19_2026_08_19.md,
  ]
source: >-
  `/ag-closeout-audit tradfi` Phase 0-2, dispatch agt-8b4230, slot 29, 2026-08-19. Prior parked docs
  (`ag_closeout_audit_tradfi_parked_2026_08_10.md`, `_r2`) checked first per the skill's "reconcile prior dated
  parked docs FIRST" rule — both fully resolved/archived, nothing carried forward.
---

# ag-closeout-audit tradfi — parked findings 2026-08-19

## Informational — Orthogonality survey (23 `exclude_cross_cutting` verdicts, no action needed for 19 of them)

Every candidate's asset_group tag was already checked by the pre-Phase-1 Orthogonality HARD CHECK (grep for
single-tranche+cross-cutting dual-tags) — that check found only one hit
(`databento_ice_opra_subscription_ask_2026_08_09.md`), which turned out to be a **false positive**: the doc is
already correctly tagged `[tradfi]` (fixed by a prior 2026-08-10 audit); my grep matched text inside the
explanatory comment documenting that prior fix, not a live second tag. No corpus defect there.

Phase 1's own per-doc content judgment then found a much larger population (23 docs) where the doc's REAL current
scope doesn't (or no longer does) belong in the tradfi tranche's orphan-risk count. Reading all 23 mistag_notes:
**19 of these are not corpus defects at all** — the doc already carries `cross-cutting` (or all 5 AG tags at once,
"the classic cross-cutting signature" per several agents' own words) and the audit is correctly excluding it from
tradfi's count because tradfi's specific slice is closed/trivial. This is the skill's designed behavior (a doc
"legitimately spans multiple/all 5 AGs + cross-cutting... fine as-is, if slightly redundant") — no retag needed:

- `ag_closeout_audit_rollout_2026_07_25.md`, `data_pipeline_check_mdps_features_2026_07_20.md`,
  `autonomous_session_operator_decisions_2026_07_25.md`, `b21_distinct_values_noncanonical_live_2026_08_18.md`,
  `coverage_floor_registries_no_cross_propagation_2026_07_17.md`,
  `defi_cefi_venue_chain_axis_contamination_2026_07_28.md`,
  `dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md`,
  `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`, `dp_cron_did_not_fire_false_positive_burst_2026_08_10.md`,
  `estate_orphan_assessment_2026_07_21.md`, `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`,
  `instruments_docs_audit_outstanding_items_2026_07_08.md`, `instruments_remaining_work_audit_2026_07_10.md`,
  `mdps_features_deadcode_consolidation_2026_07_20.md`, `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`,
  `mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`, `phantom_audit_estate_coverage_gap_2026_07_10.md`,
  `strategy_ml_orphan_coverage_design_gaps_2026_08_03.md`, `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`.

**4 docs show genuine tag drift** — the tag doesn't already include cross-cutting and the recommended fix isn't
just "already multi-tagged, ignore tradfi's slice." Not retagged in this run: each recommendation points to a
different, non-tradfi owning tranche/epic, and per the skill's concurrent-safety rule ("any write to a shared
doc... belongs to the OWNING tranche alone, so N workers never race the same file") — today is a sharded
multi-tranche dispatch, so writing these is left to whichever tranche/process actually owns each doc:

1. `plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` —
   `asset_group: [tradfi]` should become cross-cutting (or `[tradfi, cross-cutting]`). Its 2 tradfi-specific todos
   are done; the sole remaining item (a `check_line_caps.sh` net-zero-length-carve-out gate-design question) is
   generic and its `parent_epic` was reassigned to `plan_hygiene_master` TODAY (2026-08-19) by a separate
   epic-assignment-audit pass — the `asset_group` field was never correspondingly updated. Likely owner: `infra`
   tranche (plan_hygiene_master's usual home) or a direct operator/plan_hygiene fix.
2. `plans/active/issues/uac_data_type_validity_combinator_fragmentation_2026_07_07.md` —
   `asset_group: [cefi, defi, tradfi]` should become `[defi]`. TradFi's one substantive finding shipped and closed;
   both genuinely remaining checkboxes are 100% DeFi-scoped (SPARK/COMPOUND_V3/MORPHO/RADIANT/FLUID/KAMINO-SOLANA
   oracle_prices backfill). Likely owner: `defi` tranche.
3. `plans/active/issues/uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md` —
   `asset_group: [cefi, defi, tradfi, prediction]` should become `[cross-cutting]`. A single shared UAC-registry
   mechanism decision; the doc's own 2026-08-19 epic-reassignment comment already made this determination for
   epic routing (`cefi_master` → `uac_master`) but `asset_group` wasn't updated to match.
4. `plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` — should drop `tradfi`
   (recommended `[cefi, meta]`). Zero tradfi objects measured anywhere in the doc; its own §6 caller-audit table
   marks the tradfi row's impact explicitly "NONE."

Recommend a `[DOCS] P3` corpus-hygiene todo (below) rather than a same-run fix, given the ownership ambiguity and
today's concurrent sharded dispatch.

## Informational — one live cross-agent classification inconsistency (not urgent, worth a future reconciliation pass)

Two Phase-1 agents reached opposite scope verdicts on sibling DP_CRON-alert docs describing the SAME underlying
alerting-service mechanism (a `RecurringCooldownState`/`AlertDeduplicator` dedup bug and its aftermath):
`dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` and
`dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md` both verdicted `exclude_cross_cutting` (correctly
recognizing the fix is generic, fleet-wide infra, not tradfi-specific — both already carry `parent_epic:
security_and_cross_cutting_master`), while their direct successor,
`dp_cron_did_not_fire_storm_recurred_on_stable_revision_2026_08_17.md`, verdicted `orphaned_partial_coverage`
(kept as a tradfi candidate) and fed batch19's item list is untouched by it (its one clean uncovered item — a P3
"check whether the 10-deploys-in-18h churn has a cause beyond the deliberate fix-deploy cycle" — was deliberately
NOT drafted into batch19 pending this reconciliation). Recommend the `cross-cutting` or `ci` tranche's own audit
(or a `/plan-reconcile` pass) settle this doc's real classification the same way its 2 siblings were settled,
rather than tradfi silently keeping only the inconsistent one.

## Todos

- [ ] [DOCS] P3. **Retag the 4 genuine-drift docs** listed above to their recommended `asset_group` values (each
      recommendation is fully evidenced in this doc's Orthogonality section — no fresh investigation needed, just
      the write + a `check_ag_closeout_linkage.py` re-run). Given ownership is split across tranches/epics, either
      the operator assigns each to its owning tranche's next audit pass, or a single corpus-hygiene pass does all 4
      at once (mirroring `asset_group_ao_ci_infra_schema_expansion_2026_07_27.md`'s precedent). Done when: all 4
      docs' `asset_group` reflects the recommended value and `check_ag_closeout_linkage.py` runs clean for every
      tranche touched.
- [ ] [DOCS] P3. **Archive the 3 confirmed-`archivable_now` docs** (0 genuine remaining open work, each
      independently cross-verified against 2-3 corroborating sources this run):
      `dp_vm_001_tradfi_bf_cme_ohlcv_1m_g01_6a_6l_2020_exit137_stall_relaunch_bound_page_2026_08_15.md` (both
      checkboxes superseded by the confirmed billing root-cause, precedent already set by its `btc_2020` sibling),
      `tradfi_autonomous_session_operator_decisions_2026_07_25.md` (0 open todos, `archive_exempt` already
      standing), `tradfi_vix_full_history_backfill_2026_08_10.md` (0 open todos, successor doc already archived
      2026-08-16, this doc's own `archive_exempt` justification is now stale). Run the standard 6-step archival
      ritual (or dispatch via `/archive-candidates-audit`) on all 3. Done when: all 3 are archived with banners +
      referrer sweep clean.
- [ ] [DOCS] P3. **Reconcile the DP_CRON storm-doc classification inconsistency** described above —
      `dp_cron_did_not_fire_storm_recurred_on_stable_revision_2026_08_17.md` vs. its 2 already-cross-cutting-tagged
      siblings. Done when: the doc's `asset_group` is settled one way or the other and, if it moves to
      cross-cutting, its one clean remaining item (the 10-deploys/18h churn-cause check) is picked up by that
      tranche's own batch process instead of staying stranded.

## Progress Log

- **2026-08-19, ag_closeout_auditor (dispatch agt-8b4230, slot 29)**: Phase 0-2 audit complete. 71 tradfi-primary
  candidates classified via a 71-agent Workflow. 23 exclude_cross_cutting (19 no-action, 4 genuine drift — this
  doc), 3 archivable_now, 11 archivable_after_planned_work, 34 orphaned (12 conflict-clear extracted to
  `tradfi_satellite_ao_dispatch_batch19_2026_08_19.md`, 22 non-batchable-taxonomy-gated — tracked in that batch's
  own Deferred section). Parked-findings count reconciliation: 3 todos filed above = 3 findings that don't fit
  batch19's Deferred taxonomy (process/meta, not tradfi content work) — balanced.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
