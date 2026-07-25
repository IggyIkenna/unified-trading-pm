---
doc_type: plan
title: DeFi satellite AO batch 1 — finalize (reconcile source docs + resolve deferred items + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 54 of that plan's todos are done (53 original + todo 54, appended 2026-07-25 once operator-decision
  entry #3 resolved). Mirrors the cefi/tradfi/prediction batch1_finalize pattern (reconcile each of the 29 distinct
  source docs' checkboxes independently — 28 from the original 53 + 1 more for todo 54's source), plus 2 batch1-specific
  additions: re-check the 1 too-large-doc exclusion for whether it's now scoped enough for a batch2 pass, and re-verify
  the 1 operator-ruling item (Solana lending_indices path shape) has been answered before spinning it into a fresh todo.
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# DeFi satellite AO batch 1 — finalize

> **Machine-gated on `defi_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 54 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 29 distinct source docs' checkboxes** (corrected 2026-07-25 plan-reconcile: the
      original list below was missing the 29th doc,
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` — the source of todo 54, appended
      after operator-decision entry #3 resolved; batch1's own frontmatter summary already independently states the
      correct "29 of those docs" figure, confirming 28 was the stale count). For each of
      `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 54 now-done todos: flip the corresponding checkbox/section in
      its named source doc (each todo's text ends with "Source: `<doc>.md`" — 3 of the 53 original todos cite 2-3 source
      docs at once since they combine same-file candidates from multiple docs; flip the checkbox/section in EVERY cited
      doc for those), citing the batch-1 commit(s) that shipped it — verify the actual shipped commit exists before
      citing it. **Also flip `defi_consolidated_closeout_2026_07_18.md` Track 2's matching P0 checkbox** (the
      `write_defi_rows()` bare-symbol-filename-leaf defect) once todo 36 ships — that consolidated-plan checkbox tracks
      the identical defect via the same source issue doc and is NOT itself one of the 29 source docs below, so it would
      otherwise stay stale after this reconciliation. The 29 source docs:
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` (1 todo — todo 54),
      `defi_dedicated_bucket_shared_migration_2026_07_13.md` (5 todos), `data_completion_defi_2026_07_15.md` (3 todos, 1
      shared with the enumerate_expected_universe.py combine), `defi_strategy_pnl_axis_index_2026_07_24.md` (shared,
      lst_rates_handler.py combine), `lst_rate_honest_coverage_2026_07_21.md` (shared, lst_rates_handler.py combine),
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`,
      `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`,
      `issues/defi_adapter_dead_code_audit_2026_07_24.md` (2 todos),
      `issues/defi_curve_optimism_subgraph_no_allocations_2026_07_15.md` (2 todos, 1 shared with the
      dex_swaps_handler.py combine), `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` (shared,
      enumerate_expected_universe.py combine), `issues/defi_five_never_captured_venues_fix_2026_07_22.md` (4 todos),
      `issues/defi_legacy_precanonical_composite_venue_objects_2026_07_24.md` (2 todos),
      `issues/defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23.md`,
      `issues/defi_nonpool_per_instrument_eu_has_no_reconciliation_path_2026_07_20.md` (2 todos, 1 shared with the
      lst_rates_handler.py combine), `issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` (all 3 folded into
      1 combined todo), `issues/defi_perp_funding_canonicalisation_derivative_ticker_all_perps_2026_07_15.md`,
      `issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md` (2 todos),
      `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md` (2 todos),
      `issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md` (2 todos),
      `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`,
      `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (2 todos),
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md` (4 todos),
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` (2 todos, 1 shared with the dex_swaps_handler.py
      combine), `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` (3 todos),
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` (6 todos),
      `issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md` (2 todos),
      `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`,
      `issues/phantom_captures_defi_2026_06_28.md`, `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`.
      For each: after flipping, re-check whether it now has 0 open todos remaining (checkbox AND prose-form). Only flip
      a doc's `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 29 source docs'
      corresponding checkboxes/sections are flipped with verified evidence (including the consolidated-plan Track 2
      cross-flip above), and any doc that genuinely reaches 0 open todos is flipped to `status: resolved`.
- [ ] [REVIEW] P1. **Re-check the 1 too-large-doc exclusion for a batch2 pass.** Re-read
      `issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`'s current state — has whatever made it
      too-large/risky at batch-1 triage time settled enough that a fresh, precisely-scoped triage pass could now safely
      extract its AO-eligible candidate? If yes, recommend and scope a `defi_satellite_ao_dispatch_batch2` candidate
      item with a concrete done-when; if no, record why it's still too volatile and re-check again at the next batch
      cycle. **Done when**: the doc has an explicit settled-vs-still-volatile verdict recorded, with a scoped batch2
      candidate item if found settled.
- [ ] [DIAG] P1. **Re-verify the Solana lending_indices path-shape operator ruling has been answered.** Check entry 3
      (Kamino/Solend `instrument_type` shape: `solana_lending` vs `solana_amm_pool`) in
      `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`. If the operator has ruled: extract
      `issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`'s deferred candidate into a new
      tracked `defi_satellite_ao_dispatch_batch2` item scoped per the ruling (probe the operator-confirmed
      `instrument_type` shape, or both if the ruling says both are live). If still unanswered, leave it queued and do
      NOT spin a fresh todo — re-check at the next batch cycle. **Done when**: a definitive answered-vs-still-queued
      verdict is recorded here with the entry-3 status cited, and either a scoped batch2 candidate is created (if
      answered) or the item is confirmed still queued (if not).
- [ ] [DOC] P1. **Archive `defi_satellite_ao_dispatch_batch1_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todos 2 and 3
      above should have already resolved the too-large-doc and operator-ruling exclusions — verify none remain
      untracked) → add the archive banner → run the codex-alignment check → grep the corpus for every referrer of
      `defi_satellite_ao_dispatch_batch1_2026_07_25` and fix each path to point at the archived location → clear
      `locked_by` (already empty here, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
