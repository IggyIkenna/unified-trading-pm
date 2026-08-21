---
doc_type: issue
title: ag-closeout-audit tradfi 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit tradfi tranche Phase 1 audit (3 batches, 74 candidate docs). Compact orphan table —
  full escalation-worthy findings live in the cross-tranche big-findings doc.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, tradfi, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/tradfi_consolidated_closeout_2026_07_18.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit tradfi, 3 Phase-1 batches, 74 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit tradfi 2026-08-21

74 candidates, 3 batches. Counts: archivable_now 6 · archivable_after_planned_work ~9 · orphaned_partial_coverage 9
· orphaned_never_touched 18 · exclude_cross_cutting 26 (very high mistag rate). tradfi's own master closeout
`tradfi_consolidated_closeout_2026_07_18.md` is `assigned_vm: NA` — same methodology caveat as defi.

**Escalation-worthy tradfi finding already in the cross-tranche big-findings doc** (item 7): Databento CME billing
block, 8+ days stale, burning real SPOT compute daily, unanswered pause-vs-accept decision.

## Orphaned — compact table

| Doc | Taxonomy |
|---|---|
| `data_completion_tradfi_2026_07_15.md` | multiple P0/P1 items uncovered: Phase-0 layout audit, G1.run gate, R1 data-loss record, EIA credential ask, altdata home decision, phantom-manifest VM re-run |
| `data_completion_tradfi_line_cap_blocks_e7_stale_item_close_2026_08_16.md` | content-judgment split needed |
| `databento_ice_opra_subscription_ask_2026_08_09.md` | BLOCKED-CREDENTIALS |
| `dp_vm_001_mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16.md` | operator relaunch + tarball-cadence design |
| `dp_vm_001_mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14.md` | operator relaunch decision |
| `dp_vm_001_tradfi_bf_cme_ohlcv_1m_*` (4 near-duplicate docs, BTC/ES/g01_6a_6l 2020/2021) | see cross-tranche big-findings item 7; 4 separately-tracked `[OPERATOR]` relaunch/policy checkboxes, un-reconciled — consolidate |
| `features_service_corporate_actions_polygon_io_banned_vendor_2026_08_18.md` | vendor re-sourcing decision + contingent registry work |
| `retirement_completeness_pollutant_reverify_ice_still_live_2026_08_15.md` | ICE-databento + CBOE VIX-cash purge, surfaces-audit |
| `tradfi_bf_cme_ohlcv_1m_relaunch_dispatch_budget_hit_2026_08_16.md` | manual-relaunch-vs-wait |
| `tradfi_canonical_path_migration_design_2026_07_19.md` | combo_chain (~207K objects) + short-code migration, added 2026-08-18 |
| `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` | standing-health-check design question |
| `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` | CBOE/VX P1-OPERATOR-DECISION, GCS/manifest measure-and-migrate, dead-code-wiring |
| `tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md` | ~881K-row prod-manifest DELETE, un-tracked |
| `tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md` | gate-design question |
| `tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md` | root-cause + fix+re-purge (gated) |
| `tradfi_fred_forward_capture_and_backfill_gap_2026_08_13.md` | 2 investigation todos |
| `tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md` | 787-row blank-instrument_type writer ID + leftover stash cleanup |
| `tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md` | genuine parked ambiguity |
| `tradfi_reconciliation_2026_08_17_findings_2026_08_17.md` | multi-token-equity-symbol join-convention design (8/9 items already covered) |
| `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` | 7 engineering todos, correctly assessed NA on real risk merits |
| `tradfi_tbbo_unclassified_adapter_error_dp_fetch_009_2026_08_15.md` | classify_venue_error key-mismatch fix + Option A/B decision |
| `tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md` | dry-run then full-mode launch, real prod-bucket delete |
| `tradfi_volatility_options_groups_empty_confirmed_missing_fetch_evidence_2026_08_17.md` | locate call site + fix honest-absence wiring |
| `yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md` | re-run latency script + codex doc update |
| `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` | credential ask + launcher wiring + post-backfill check |

## Mechanical hygiene flags

- `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` and
  `tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` — both substantively resolved
  via `batch13`, but their own source-doc checkboxes were never flipped (citation drift, not real remaining work).
- `tradfi_volatility_options_groups_empty_confirmed_missing_fetch_evidence_2026_08_17.md` and
  `yahoo_ohlcv_1h_availability_semantic_undecided_2026_08_13.md` are single-AG tradfi content but carry
  `parent_epic: security_and_cross_cutting_master`/`uac_master` — should route to `tradfi_master` per the
  asset-group-specific epic-assignment rule.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit tradfi Phase-1 sweep (3 batches). No
  mechanical fixes applied yet.
