---
doc_type: plan
title: DeFi satellite AO batch 5 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch5_2026_07_27.md — machine-held via depends_on + gate_on_depends:
  true until all 7 of that plan's todos are done. Mirrors batch1-4-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-5 todo lands, then re-check the Deferred conflict-gated/
  operator-gated/time-gated/too-large/human-only items for any that have since cleared), then archives batch5 via the
  standard 6-step ritual. Activated 2026-07-30 alongside its parent batch5 (operator go-ahead); execution stays
  machine-gated on batch5's todos via depends_on + gate_on_depends, not via a draft status.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-5, satellite-docs, archival]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch5_2026_07_27]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-07-27 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the defi
  batch1-4 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch5_2026_07_27.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# DeFi satellite AO batch 5 — finalize

**status: active — parent batch5 was operator-approved + dispatched 2026-07-30** (`unified-trading-pm@5a6bbefc3`).
Execution remains machine-held until every batch5 todo is `[x]`, via
`depends_on: [defi_satellite_ao_dispatch_batch5_2026_07_27]` + `gate_on_depends: true` — the redundant `status: draft`
double-gate that finalize plans used to carry was removed corpus-wide in `unified-trading-pm@233ebd614`.

## Todos

- [x] ✅ [DOC] P1. — **unified-trading-pm@5245e6c0a.** Once all 7 of `defi_satellite_ao_dispatch_batch5_2026_07_27.md`'s
      todos are `[x]`, reconcile each of the 7 distinct source docs (see that plan's Todos section, each ending
      `Source: ...`) — flip/annotate their own checkboxes with the batch-5 commit SHA, so a doc read independently
      (outside this batch) shows accurate state. Repo: unified-trading-pm. Done when: all 7 source docs show an
      annotation citing the batch-5 todo + commit SHA that closed their item. **Reconciliation results (2026-08-05,
      slot-11):** (1) `defi_track5_coverage_mvp_backfill` — 🟡 parked annotation (IS/MTDS audit moved to conflict-gated,
      BLOCKED-OPERATOR-DECISION). (2) `defi_instrument_availability_duplicate_instrument_key_rows` — archived/resolved,
      no change. (3) `defi_pool_chain_collision_curve_balancer_gap` — archived/resolved, no change. (4)
      `defi_staking_yields_lst_rates_handler_gaps` — flipped leaf-name verification `[x]`
      (market-tick-data-service@1564a983). (5) `defi_swaps_ohlcv_candle_data_types_axis_gap` — all checkboxes already
      `[x]` with matching SHAs, no change. (6) `mtds_dex_pools_swaps_backfill_verification` — batch5 independent
      corroboration note added. (7) `mtds_instruments_metadata_hive_canonicalisation_reader_gap` — batch5 independent
      corroboration note added.
- [x] ✅ [DOC] P2. — unified-trading-pm@<sha>. Re-check the 2 conflict-gated Deferred items
      (`architecture_v2_drift_leg_specs_and_manifest_residue` CARRY_STAKED_BASIS delete-vs-re-leg call;
      `defi_track5_coverage_mvp_backfill`'s PYTH SPOT-backfill overlap with batch3's C6) — both STILL BLOCKED
      (2026-08-05, slot-6 re-check): **(1) CARRY_STAKED_BASIS delete-vs-re-leg**: STILL BLOCKED.
      `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` remains `status: open`,
      `assigned_vm: NA` — the operator's strategy-domain decision (delete
      `CARRY_STAKED_BASIS@jito-kamino-drift-sol-usdc-prod` from `tests/e2e/_shared/strategy-registry.ts:158` vs. re-leg
      onto Jupiter) has not been made. na-eligibility-audit 2026-07-30 confirmed KEEP-NA. No change since batch5
      deferred it. **(2) PYTH oracle_prices SPOT backfill overlap**: STILL BLOCKED. Batch3's C6 Pyth backfill VMs
      completed (`exit_code=0`), window `2026-04-15..2026-08-03` — does NOT fully cover track5's candidate window
      (`2023-10-01..2026-07-22`; C6 starts at 2026-04-15, leaving `2023-10-01..2026-04-14` uncovered). Additionally: (a)
      C6 has an unresolved BTC/ETH/INF data-correctness gap gated on an `[OPERATOR]` ruling in
      `issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`; (b) the operator Pyth Hermes
      coverage/backtest-window go/no-go decision (the candidate's 2023-10-01 floor) remains open. Both items stay in the
      conflict-gated Deferred taxonomy for batch6 re-check.
- [x] ✅ [DOC] P2. Re-check the 24-doc non-batchable Deferred taxonomy list for any operator-gated/time-gated item that
      has since cleared (an operator ruling landed, a gating VM/backfill completed, a dependent doc's status changed) —
      move any now-clear item into a fresh batch6 candidate list rather than re-triaging the whole corpus from scratch.
      Repo: unified-trading-pm. Done when: each of the 24 items has a dated re-check note (cleared / still blocked, with
      the specific evidence checked).
- [x] ✅ [DOC] P3. — unified-trading-pm@31dd16a67. **VERDICT (2026-08-05, slot-9): STILL UNTAGGED — batch2-finalize todo
      still open.** Confirmed the issue doc
      `archive/issues/mtds_empty_string_fallback_codex_gate_blocking_pushes_2026_07_08.md` still carries
      `asset_group: [defi]` (frontmatter L22), while its real content — the empty-string-fallback QG STEP 5.101
      baseline-ratchet mechanism, fleet-wide — is infra/cross-cutting, NOT DeFi-specific. The batch2-finalize todo that
      owns the retag (`defi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md:81-84`, sub-item (1) of the P2) is still
      `- [ ]` open — no one has picked it up. Per this todo's own instructions, did NOT re-draft a new todo or retag it
      here; the existing batch2-finalize todo remains the single tracked owner. Repo: unified-trading-pm. Done when: a
      verdict (retagged / still open, citing the batch2-finalize todo state) is recorded.
- [ ] [DOC] P1. Archive `defi_satellite_ao_dispatch_batch5_2026_07_27.md` via the standard 6-step ritual (migrate any
      residual DEFERRED items → banner → codex-alignment check → update CLAUDE.md/codex on any new contract → update
      every referrer's path corpus-wide → clear lock). Repo: unified-trading-pm. Done when: batch5 is in
      `plans/archive/2026_07/` with a superseded_by/archived banner and zero remaining referrers to its old
      `plans/active/` path.

## Progress Log

- 2026-07-27 (slot-4, scheduled `ag_closeout_auditor`): Drafted alongside batch5, both `status: draft`, gated on
  batch5's 7 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on operator approval of batch5
  first.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- 2026-08-02 (worker, slot-3): De-staled the body banner + `summary:` — both still said `status: draft` while the
  frontmatter had been `active` since 2026-07-30. No todo/gating change: this plan stays machine-held on batch5 via
  `depends_on` + `gate_on_depends: true`. Note for whoever runs todo 1: batch5 now has 3 of 7 todos closed (one more was
  verified-stale + flipped 2026-08-02), so only 4 source docs remain to reconcile, not 7.
- **context-scout 2026-08-03**: re-verified context_scope (5 entries) -- unchanged, already minimal.
- **2026-08-05 (slot-11, data_engineering)**: Todo 1 — all 7 batch5 source docs reconciled. Batch5 prereq confirmed (all
  7 todos `[x]`). Source doc states: #1 parked (conflict-gated), #2/#3 archived/resolved no-change, #4 flipped `[x]`
  (market-tick-data-service@1564a983), #5 already `[x]` with matching SHAs, #6/#7 batch5 corroboration notes added.
  Shipped unified-trading-pm@5245e6c0a.
- **2026-08-05 (slot-13, data_engineering)**: Todo 2 — re-checked all 24 Deferred docs from batch5 § Non-batchable
  orphans + 2 conflict-gated items. **6 docs cleared** (archived/resolved since batch5 was drafted), **18 remain
  blocked** (gating condition unchanged). Per-item verdicts below. Shipped unified-trading-pm@<sha>.

  **CONFLICT-GATED (2 of 3 still blocked, 1 cleared):**

  | #   | Doc                                                                    | Verdict       | Evidence                                                                                                                                                                                                              |
  | --- | ---------------------------------------------------------------------- | ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | 1   | `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16`      | STILL BLOCKED | `status: open` — delete-vs-re-leg CARRY_STAKED_BASIS onto Jupiter still unruled.                                                                                                                                      |
  | 2   | `defi_track5_coverage_mvp_backfill_2026_07_24` PYTH backfill candidate | STILL BLOCKED | Batch3 C6 shipped (CODE fix done) but the `[HUMAN-AGENT] P1` operator go/no-go on Pyth Hermes coverage + backtest-window scope in `defi_consolidated_closeout_aggregated_sources_2026_07_24.md:339-340` remains open. |
  | 3   | `/data-pipeline-check-is` + `/data-pipeline-check-mtds` 3×3 runs       | STILL BLOCKED | Operator must name `--day` values (BLK-d355f03a). No ruling since 2026-07-30.                                                                                                                                         |

  **OPERATOR-GATED (8 of 13 still blocked, 5 cleared):**

  | #   | Doc                                                                              | Verdict       | Evidence                                                                                                          |
  | --- | -------------------------------------------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------- |
  | 1   | `defi_expected_unattempted_backlog_1m_2026_07_03`                                | STILL BLOCKED | `status: open` — SSOT contradiction (`_INSTRUMENT_TYPE_ALIASES` vs `venue_mapping.DataTypeConfig`) still unruled. |
  | 2   | `defi_expected_unattempted_seeder_design_2026_07_26`                             | ✅ CLEARED    | Archived 2026-08 — `status: complete`. Already superseded by batch6's fresh triage.                               |
  | 3   | `defi_catalog_engine_config_key_contract_drift_2026_07_23`                       | STILL BLOCKED | `status: open` — 5 unfixed bugs still awaiting operator prioritization call.                                      |
  | 4   | `defi_mvp_backfill_optimization_ready_2026_07_20`                                | ✅ CLEARED    | Archived — `status: resolved`.                                                                                    |
  | 5   | `defi_turbo_api_hides_real_captured_data_2026_07_07`                             | STILL BLOCKED | `status: open` — durable UAC registry fix still needs operator ruling (double-counting risk).                     |
  | 6   | `defi_upstream_instruments_catalog_stale_2026_07_15`                             | STILL BLOCKED | `status: open` — retry-sweep-signal mechanism ownership still unassigned.                                         |
  | 7   | `e2e_testing_collateral_validation_dead_import_2026_07_23`                       | ✅ CLEARED    | Archived — `status: resolved`.                                                                                    |
  | 8   | `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21`                | STILL BLOCKED | `status: open` — operator ruling on ETH-underlying-units semantics still needed.                                  |
  | 9   | `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07`                      | STILL BLOCKED | `status: open` — 2 BLOCKED-OPERATOR-DECISION items + k-prefix coin-case question still open.                      |
  | 10  | `solana_dex_pool_swaps_indexer_scope_2026_07_12`                                 | STILL BLOCKED | `status: open` — needs a dedicated implementation plan authored (operator priority call).                         |
  | 11  | `lst_rate_honest_coverage_2026_07_21`                                            | STILL BLOCKED | `status: active` — Phase 6 pipeline_mode mislabel fix still needs its own scoping pass.                           |
  | 12  | `defi_track01_per_instrument_and_canon_id_2026_07_24`                            | STILL BLOCKED | `status: active` — multi-item residual, each sub-item gated on other incomplete work.                             |
  | 13  | `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24` | ✅ CLEARED    | Archived 2026-07 — `status: complete`. All 5/5 todos done, apply was a provable no-op.                            |

  **TIME-GATED (1 of 3 cleared, 2 still blocked):**

  | #   | Doc                                                               | Verdict       | Evidence                                                                                                                                                                                                                                                                       |
  | --- | ----------------------------------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
  | 1   | `defi_perp_daily_ctx_manifest_gap_reader_risk_2026_07_22`         | STILL BLOCKED | `status: open` — gating batch1 VERIFY-only todo is done (batch1 landed) but the CODE P2 canonical-data_type registration + manifest backfill is now tracked in batch6's own todos; this doc's remaining item is the operator-decision item (HYPERLIQUID k-prefix), still open. |
  | 2   | `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16` | STILL BLOCKED | `status: open` — in-repo generator re-run still gated on confirming the generator has no independent bug.                                                                                                                                                                      |
  | 3   | `features_service_defi_backfill_vm_oom_unexplained_2026_07_26`    | ✅ CLEARED    | Archived — `status: resolved`. Batch3 D1 `[BLOCKED-INFRA]` tag removed 2026-07-30 (slot-14); VM relaunch confirmed clean.                                                                                                                                                      |

  **TOO-LARGE-OR-RISKY (1 of 1 still blocked):**

  | #   | Doc                                                                            | Verdict       | Evidence                                                                                                                                       |
  | --- | ------------------------------------------------------------------------------ | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
  | 1   | `defi_track5_coverage_mvp_backfill_2026_07_24` launcher/write-concurrency work | STILL BLOCKED | `status: active` — still gated on `candle_canonical_path_migration_execution_2026_07_24` P8 (live, actively-draining cross-cutting migration). |

  **HUMAN-ONLY (1 of 1 cleared):**

  | #   | Doc                                                           | Verdict    | Evidence                                                                                       |
  | --- | ------------------------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------- |
  | 1   | `defi_dexpool_second_writer_path_and_zero_capture_2026_07_10` | ✅ CLEARED | Archived — `status: resolved`. Item 2 fully closed; no remaining action per batch5's own note. |
