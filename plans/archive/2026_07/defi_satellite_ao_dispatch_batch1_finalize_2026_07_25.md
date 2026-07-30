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
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
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

> **🟢 ARCHIVED 2026-07-30.** All 4 todos done: source-doc reconciliation (todo 1), the too-large-doc batch2 re-check
> (todo 2), the operator-ruling re-check (todo 3), and this archival (todo 4) — parent moved to
> `/plans/archive/2026_07/defi_satellite_ao_dispatch_batch1_2026_07_25.md`, corpus referrers updated (23 files with a
> literal `plans/active/...` path to the parent + 4 files pointing at this finalize doc's own path). No new durable
> contract from this batch — codex-alignment check: nothing to update (every todo executed an already-decided spec, per
> the parent's own banner).
>
> **Machine-gated on `defi_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 54 tasks in that plan are `done`. `sequential: true` because todo 2
> needs todo 1's reconciliation done first, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-7, review).** Reconciled all 29 source docs against batch1's 54 done
      todos: 11 docs edited with verified `repo@sha` citations (data_completion_defi, defi_consolidated_closeout Track
      2, defi_dedicated_bucket_shared_migration, defi_track01_per_instrument_and_canon_id, defi_adapter_dead_code_audit,
      defi_expected_unattempted_backlog_1m, features_onchain_featureless_shards_and_vocabulary_split,
      non_tardis_dexperp_venue_data_status_smoketest, phantom_captures_defi (special case — confirmed the 2026-07-28
      slot-15 root-cause completion, corrected stale banner text only, left `status`/`locked_by` untouched per its own
      unlock-gate), lst_rate_honest_coverage, defi_five_never_captured_venues_fix); 18 docs required no edit (already
      correctly reconciled by prior passes, or pure index docs). Every cited SHA independently verified to exist in its
      repo before flipping (17 distinct SHAs checked). 0 docs reached genuinely 0 open items overall, so 0
      `status:     resolved` flips — every touched doc still carries at least one unrelated open item. 1 pre-existing
      gap flagged (not created by this pass): `defi_curve_optimism_subgraph_no_allocations_2026_07_15.md`'s `--apply`
      execution citation for the CURVE/OPTIMISM reclassification could not be independently verified against batch1's
      own text — worth an operator/worker double-check, not blocking this reconciliation. **Reconcile all 29 distinct
      source docs' checkboxes** (corrected 2026-07-25 plan-reconcile: the original list below was missing the 29th doc,
      `/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` — the source of
      todo 54, appended after operator-decision entry #3 resolved; batch1's own frontmatter summary already
      independently states the correct "29 of those docs" figure, confirming 28 was the stale count). For each of
      `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s 54 now-done todos: flip the corresponding checkbox/section in
      its named source doc (each todo's text ends with "Source: `<doc>.md`" — 3 of the 53 original todos cite 2-3 source
      docs at once since they combine same-file candidates from multiple docs; flip the checkbox/section in EVERY cited
      doc for those), citing the batch-1 commit(s) that shipped it — verify the actual shipped commit exists before
      citing it. **Also flip `defi_consolidated_closeout_2026_07_18.md` Track 2's matching P0 checkbox** (the
      `write_defi_rows()` bare-symbol-filename-leaf defect) once todo 36 ships — that consolidated-plan checkbox tracks
      the identical defect via the same source issue doc and is NOT itself one of the 29 source docs below, so it would
      otherwise stay stale after this reconciliation. The 29 source docs:
      `/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` (1 todo — todo 54),
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
      `archive/issues/defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md` (2 todos, now archived — fully closed
      2026-07-30), `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md` (2 todos),
      `issues/defi_swaps_ohlcv_candle_data_types_axis_gap_2026_07_22.md` (2 todos),
      `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`,
      `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (2 todos),
      `issues/defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24.md` (4 todos),
      `issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md` (2 todos, 1 shared with the dex_swaps_handler.py
      combine), `issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` (3 todos),
      `issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` (6 todos),
      `archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md` (2 todos),
      `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`,
      `issues/phantom_captures_defi_2026_06_28.md` (**partially reconciled 2026-07-27** by the separate
      `june_2026_vintage_audit_findings_2026_07_27.md` §2 pass — its todo 2 "apply reconciliation" is genuinely done,
      flipped citing `mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md:754-762`'s APPLY COMPLETE evidence;
      that same pass ALSO found + corrected a false `[x]` on todo 1 (root-cause diagnosis) — it was never actually done,
      reverted to open. **NOT archived**: todo 1 is genuinely open and already tracked at
      `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s own identical unchecked todo — when THIS finalize plan's pass
      reaches it, confirm whether batch1 has since executed that root-cause diagnosis before re-flipping/archiving),
      `issues/defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22.md`. For each: after flipping, re-check whether it
      now has 0 open todos remaining (checkbox AND prose-form). Only flip a doc's `status` to `resolved` if it genuinely
      reaches 0 open todos. **Done when**: all 29 source docs' corresponding checkboxes/sections are flipped with
      verified evidence (including the consolidated-plan Track 2 cross-flip above), and any doc that genuinely reaches 0
      open todos is flipped to `status: resolved`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot-7, review) — no batch2 candidate needed, both items already fully
      closed.** Re-read `plans/archive/issues/defi_dexpool_second_writer_path_and_zero_capture_2026_07_10.md`
      (`status: resolved`, archived 2026-07-29, 0 open todos). Both items are settled, not merely "settled enough to
      extract a candidate" — they're DONE: **Item 2** (4 zero-capture protocols) closed 2026-07-14/24 (wired + verified;
      residual TRADER_JOE_V2/VELODROME_V2 gaps already dispatched via batch1's own `dex_swaps_handler.py` todo). **Item
      1** (the `batch_onchain_subgraph` bare-`0x<address>.parquet` second writer path) — per the doc's own "Update
      2026-07-28" section — was SUPERSEDED: root-caused + fixed at the query/parser source (not via a resolver) and
      historically re-backfilled + purged under `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`. **Independently
      re-verified today** (not just trusting the doc's prior claim) that this superseding plan is genuinely complete:
      all 5 of its own todos are `[x]` in the live plan file (`market-tick-data-service@63199601` query/parser fix,
      `@0f40a69f` feasibility test, the `dex_pool_state` re-backfill, and the old address-keyed-leaf purge) — this is
      notable because a live, currently-tracked dispatcher bug (`gate_on_depends` failing to wire a partially-done
      upstream — see `issues/gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`) previously showed this
      exact plan at 0/5 and 3/5 across several recurrence notes; confirmed it has since genuinely reached 5/5, so the
      superseding claim holds and is not itself a stale artifact of that bug. **Net verdict**: no
      `defi_satellite_ao_dispatch_batch2` item drafted — nothing remains to extract from this doc.
- [x] ✅ [DIAG] P1. **DONE 2026-07-30 (slot-7) — ANSWERED, and already fully extracted + executed + verified + archived;
      no batch2 item needed.** Entry 3 of `plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md`
      (Kamino/Solend `lending_indices` `instrument_type` shape conflict): **Operator answer (2026-07-25) = A — widen
      scope to probe both `solana_lending` and the Track-2-claimed `solana_amm_pool` before concluding**, entry status
      recorded as `resolved`. Verified the entry's own resolution note against the live plan state rather than trusting
      it blind: the widened probe was dispatched as `defi_satellite_ao_dispatch_batch1_2026_07_25.md`'s todo "Resolve
      the Kamino/Solend `lending_indices` `instrument_type` shape conflict" (line 806) — confirmed `[x]` done there,
      **✅ 2026-07-28 (slot-2)**. Result went beyond the ruling's literal scope: `solana_amm_pool` never existed for
      KAMINO `lending_indices` (Track-2's prose was a mislabeling); the real legacy shape is `instrument_type=lending`,
      clean on Track 2's own probe day (2026-04-14, 6/6 samples). Probing OTHER days per the widened-scope mandate
      surfaced a NEW confirmed fabrication (a frozen 2026-05-04/05 migration-script snapshot duplicated across a 16-17
      day window, `2025-01-01`..`2025-01-16/17` — not the ~21 months the coarse probe implied), filed + fully resolved
      separately at
      `/plans/archive/issues/defi_kamino_solend_lending_indices_legacy_shape_fabricated_history_2026_07_28.md`: full
      day-by-day scan (1,305 days × 2 venues), other-data_type check (fabrication confined to `lending_indices` only, by
      construction), fix executed via `launch-canonical-migration-vm.sh` (10,472 objects relabeled, 0 errors,
      `market-tick-data-service@b5dbb379`/`@906824c5`/`@f9222f78`), clean re-scan confirmed 1,331/1,331 distinct
      relabeled dest objects GENUINE (0 mismatch, 0 missing). That issue doc is `status: resolved`, 0 open todos,
      unlocked, **archived 2026-07-30**. Source doc
      `defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md` is also archived. **Verdict**: entry 3 IS
      answered (not still-queued); the deferred candidate was already fully extracted, dispatched, executed, and
      verified through batch1 + its own follow-up issue doc — there is nothing left to spin into a fresh
      `defi_satellite_ao_dispatch_batch2` item for this conflict.
- [x] ✅ [DOC] P1. **DONE 2026-07-30 (slot-7).** **Archived `defi_satellite_ao_dispatch_batch1_2026_07_25.md`** via the
      standard 6-step ritual (per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): (1) verified
      no untracked Deferred items remain — todos 2/3 above already confirmed the too-large-doc exclusion and the
      operator-ruling item are both genuinely closed with nothing left to migrate; (2) added the 🟢 ARCHIVED banner to
      both this doc and the parent, flipped both `status: complete`; (3) ran the codex-alignment check — this batch
      executed already-decided specs only, nothing new to reflect in codex; (4) no new CLAUDE.md/codex contract shipped
      by this finalize task itself (individual todos' own contracts, if any, were codex-aligned at their own ship time);
      (5) grepped the whole `unified-trading-pm` corpus for every literal
      `plans/active/defi_satellite_ao_dispatch_batch1_2026_07_25.md` /
      `plans/active/defi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md` path and repointed each to
      `plans/archive/2026_07/...` — 23 files fixed for the parent's path, 4 files fixed for this finalize doc's own path
      (bare-filename prose mentions with no path prefix were left as-is, consistent with the prediction/cefi/tradfi
      sibling archivals); regenerated `plans/active/INDEX.md` via `scripts/plans/regenerate_active_plan_index.py`
      (auto-generated file, never hand-edited) so both entries drop out of the active index; (6) `locked_by` confirmed
      empty on both docs, both moved via `git mv` to `plans/archive/2026_07/` in the same commit as this finalize doc's
      own archival. **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer resolves to the
      new path, and this finalize doc itself gets archived alongside it in the same commit. — unified-trading-pm (SHA
      recorded at ship time below).
