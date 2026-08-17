---
doc_type: plan
title: DeFi satellite AO batch 6 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for defi_satellite_ao_dispatch_batch6_2026_07_30.md — machine-held via depends_on + gate_on_depends:
  true until all 20 of that plan's todos are done. Mirrors batch1-5-finalize's pattern (reconcile each distinct source
  doc's checkboxes independently once its batch-6 todo lands, then re-check the Deferred conflict-gated/
  operator-gated/time-gated/too-large/human-only items for any that have since cleared), then archives batch6 via the
  standard 6-step ritual. status: draft until the operator approves batch6 itself.
status: complete # 2026-08-17 archival sweep: all 4 todos [x], no locked_by
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, close-out, batch-6, satellite-docs, archival]
related:
  [
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.7
estimate_calibrated_ai_days: 0.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_satellite_ao_dispatch_batch6_2026_07_30]
gate_on_depends: true
source: >-
  `/ag-closeout-audit defi` run 2026-07-30 (autonomous, scheduled ag_closeout_auditor), per task_template.md §4's
  finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan, mirroring the defi
  batch1-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/defi_satellite_ao_dispatch_batch6_2026_07_30.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/defi_satellite_ao_dispatch_batch5_2026_07_27_finalize.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# DeFi satellite AO batch 6 — finalize

> **✅ ARCHIVED 2026-08-17 (slot-33, data_engineering).** All 4 todos `[x]`, no `locked_by`. Archived alongside
> `defi_satellite_ao_dispatch_batch6_2026_07_30.md` (also archived this session) — see that doc's own archived banner
> for the batch's closure summary.

> **CORRECTED 2026-08-12 (/plan-reconcile)**: this line previously read "status: draft — activated only after its parent
> batch6 is operator-approved and dispatched", contradicting the frontmatter (`status: active`). Per
> `unified-trading-pm@233ebd6148` ("remove redundant status:draft double-gate on finalize plans"), a finalize plan's
> `depends_on` + `gate_on_depends: true` already machine-holds its todos until the upstream is done — a separate
> body-level `status: draft` is a stale double-gate. Frontmatter `status: active` is correct; this plan is machine-gated
> on `defi_satellite_ao_dispatch_batch6_2026_07_30.md`. **STALE-COUNT-FIXED 2026-08-16 (plan_reconciler, defi tranche,
> dispatch agt-1a88e0)**: the "1 of 26 todos still open" claim above was from 2026-08-12 and never re-checked —
> `defi_satellite_ao_dispatch_batch6_2026_07_30.md` is now fully `[x]` (item 24 + its follow-up both closed
> 2026-08-15), so this finalize plan is gate-clear and ready for dispatch.

## Todos

- [x] ✅ [DOC] P1. Once all 20 of `defi_satellite_ao_dispatch_batch6_2026_07_30.md`'s todos are `[x]`, reconcile each of
      the ~21 distinct source docs (see that plan's Todos section, each ending `Source: ...`) — flip/annotate their own
      checkboxes with the batch-6 commit SHA, so a doc read independently (outside this batch) shows accurate state.
      Repo: unified-trading-pm. Done when: all source docs show an annotation citing the batch-6 todo + commit SHA that
      closed their item. **DONE 2026-08-05 (slot-8, review/data_engineering, unified-trading-pm@057dc55d7).** Reconciled
      all ~21 distinct source docs: 11 active docs edited with batch-6 annotations (11 files modified), 7 archived docs
      already [x] (no edits needed), 3 docs already pre-annotated or not requiring changes. Note: batch-6 todo 24
      (HYPERLIQUID/ASTER delete) is still `[ ]` in the parent plan — its source doc
      (`non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md`) is annotated as "dispatched to batch-6 (still
      open)" rather than closed. See Progress Log below for full reconciliation table.
- [x] ✅ [DOC] P2. **DONE 2026-08-17 (slot-16, data_engineering).** Re-checked both conflict-gated Deferred items — both
      resolved-no-action, neither produces new batch7 work. **(1) SUSHISWAP classic-vs-V3 alias
      (`defi_venue_lst_rates_residual_2026_07_24.md`)**: operator ruled 2026-08-08 (fold bare `SUSHISWAP`→`SUSHISWAP_V3`
      + migrate/purge); scoping the same day found the literal premise didn't hold (bare `SUSHISWAP` is 100%
      `chain=ARBITRUM`, already-canonical data — zero Ethereum legacy rows to migrate); a follow-up operator ruling
      2026-08-11 picked option (a) — close as verified no-op, redirect the real remaining scope (registering
      `SUSHISWAP_V3-ARBITRUM` as a new canonical venue) to the already-tracked sibling issue
      `issues/defi_sushiswap_uniswap_bare_version_factory_gap_2026_07_21.md`. All 4 todos in the source doc are now
      `[x]`, doc unlocked and marked `archive_exempt: true` (its own referrer-sweep archival pass is separately tracked
      hygiene work, not blocking this verdict). **(2) `defi_catalog_engine_config_key_contract_drift_2026_07_23.md`'s
      item-2 sweep vs whole-doc operator-gate**: batch6's 2026-07-30 characterization was already stale by the time it
      was written — the "item 2" 7-archetype sweep (`CARRY_FUNDING_DISPERSION`/`DEFI_LP_CONCENTRATED`/`DEFI_LP_POOL`/
      `DEFI_LP_VAULT`) had already shipped 2026-07-24 (`strategy-service@03310bdf`'s systemic guardrail test covers all
      4, confirmed clean); the checkbox itself was just stale-unflipped until `na-eligibility-audit 2026-08-01` flipped
      it `[x]`. The doc-level operator-gate (batch5: "awaiting an operator prioritization call") has since substantially
      cleared too: operator ruled 2026-08-08 on the P0 5-broken-archetype design decision (3 filed `[SCRIPT]` todos, all
      since shipped + `[x]`) and 2026-08-09 on the liquidation-candidate-feed transport shape. As of the doc's own
      2026-08-16 `na-eligibility-audit` re-confirmation, its sole remaining open checkbox is the `[DESIGN] P2`
      pollable-candidate-registry item — independently re-confirmed (2026-08-09 slot-17 self-correction +
      round9-reclassify-satellite-sweep) as genuinely NOT AO-dispatchable (a second design sub-decision on
      features-service's per-candidate feature-naming shape + a 3-repo scoping pass remain outstanding), correctly held
      `assigned_vm: NA`. No new bounded batch7 work to fold in for either item.
- [x] ✅ [DOC] P2. **DONE 2026-08-17 (slot-9, data_engineering).** Re-checked all 27 non-batchable Deferred taxonomy
      items against current doc state. Full per-item verdicts recorded in the Progress Log below. **Summary: 1 item's
      gating decision cleared but already spawned its own independently-tracked dispatchable plan (no new batch7 todo
      needed); 1 item is fully resolved with 0 open todos (nothing to fold in — archival-ready, not a batch7 candidate);
      the remaining 25 items are still genuinely blocked** (operator-gated design/judgment calls unruled, or time-gated
      on an in-flight process) — no fresh batch7 candidate work identified this pass.
- [x] ✅ [DOC] P3. **DONE 2026-08-17 (slot-9, data_engineering).** `mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`
      is now fully archived (`plans/archive/2026_08/issues/mtds_dex_pools_swaps_backfill_verification_2026_07_24.md`,
      **ARCHIVED 2026-08-16**) with all 17 top-level todos `[x]`, including the todo-3/todo-5 re-checks this item was
      waiting on (confirmed via `grep -n "^- \[x\]"` over the archived doc — the manifest cross-check and OOM-recurrence
      spot-checks both landed `[x]` DONE 2026-08-05/2026-08-16). Nothing to fold into batch7 — the source doc closed on
      its own before this re-check ran.
- [x] ✅ [DOC] P1. **DONE 2026-08-17 (slot-33, data_engineering).** Archived `defi_satellite_ao_dispatch_batch6_2026_07_30.md`
      via the 6-step ritual: (1) no residual DEFERRED items needed migrating — todos 2-3 above already re-checked every
      Deferred item this same day and found zero new batch7-dispatchable work; (2) archived banner + superseded_by
      (none — no successor batch) added; (3) codex-alignment check — batch6's 20 todos were routine fixes/audits
      (subgraph swap, catalogue expansion, KAMINO/KALSHI diagnostics, legacy-venue fold, perp_daily_ctx registration,
      AAVE/FLUID-PLASMA onboarding, chain-collision trace, manifest read-site audit, HL/ASTER migration + RULE 11
      relax) already covered by existing codex SSOTs (honest-absence-downstream-handling.md,
      defi-canonical-naming-ssot.md, gcs-and-manifest-delete-safety-protocol.md) — no new contract to stub; (4) no
      CLAUDE.md change needed for the same reason; (5) fixed the 2 active-corpus referrers with real path-shaped
      citations to the old `/plans/active/` path
      (`plans/active/issues/dp_vm_003_manifest_recon_cefi_silent_death_unsliced_manifest_read_2026_08_15.md`,
      `plans/active/issues/defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`) — `plans/archive/` is
      explicitly excluded from `check_reference_paths.py`'s scope, so historical archived-doc mentions were left as
      the frozen record they are; regenerated `plans/active/INDEX.md` + `plans/epics/defi_master.md` via their
      generator scripts to drop/repoint the now-archived entries; (6) cleared (no lock existed). Both batch6 and this
      finalize plan moved to `plans/archive/2026_07/` in the same session. Repo: unified-trading-pm.

## Progress Log

- 2026-07-30 (slot-2, scheduled `ag_closeout_auditor`): Drafted alongside batch6, both `status: draft`, gated on
  batch6's 20 todos via `depends_on` + `gate_on_depends: true`. No work started — waiting on operator approval of batch6
  first.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — fixed a duplicate `context_scope` frontmatter key.
- **2026-08-05 (slot-8, review/data_engineering)**: Completed todo 1 (source-doc reconciliation). Reconciled all ~21
  distinct source docs referenced by batch-6's 26 todos (25 done, 1 still open — todo 24 HYPERLIQUID/ASTER delete).
  **Active docs edited (11 files):** `defi_base_adapter_success_key_ignored_by_failure_accounting` (batch-6 todo 1,
  audit verdict recorded), `defi_broader_local_fallback_vs_uac_sweep` (batch-6 todo 2, inventory flipped [x]),
  `defi_kalshi_perp_perp_funding_source_not_registered` (batch-6 todo 10, both DIAG items flipped [x]),
  `defi_lst_yields_coverage_extension_gcs_verified` (batch-6 todo 12, backfill confirm flipped [x]),
  `features_onchain_featureless_shards_and_vocabulary_split` (batch-6 todo 18, partial-closure annotation),
  `mtds_instruments_metadata_hive_canonicalisation_reader_gap` (batch-6 todo 21, todos 6+7 flipped [x]),
  `non_tardis_dexperp_venue_data_status_smoketest` (batch-6 todo 24, still-open annotation — only unchecked batch-6
  todo), `read_availability_index_bare_defi_callers` (batch-6 todo 25, QG baseline sync annotation),
  `reconcile_phantom_manifest_rows_all_defi_memory_footprint` (batch-6 todo 26, both checkboxes annotated),
  `mvp_backfill_defi_onchain_v10` (batch-6 todos 22+23, 4 checkboxes annotated),
  `defi_gas_fees_historical_venue_path_ migration` (batch-6 todo 9, re-verification annotation). **Archived docs (7
  docs, already [x], no edits needed):** `defi_dex_pools_catalogue_undercoverage`, `defi_plasma_chain_onboarding_gap`,
  `defi_pool_chain_collision_curve_ balancer_gap`, `features_defi_onchain_mtds_ingestion_claim_needs_reverify`,
  `features_service_defi_backfill_vm_oom_ unexplained`,
  `market_tick_data_service_lending_instrument_type_historical_restamp`,
  `onchain_manifest_dishonest_and_ recompute_blocked`. **Pre-annotated/no-change (3 docs):**
  `defi_clean_path_fetch_evidence_fidelity_scope` (todo 3 already cites batch-6),
  `defi_legacy_precanonical_composite_venue_objects` (todo 11 already cites batch-6),
  `defi_perp_daily_ctx_manifest_gap_reader_risk` (todo 13 already cites batch-6). **Not annotated (not batch-6
  covered):** `defi_expected_unattempted_backlog_1m` (line 345 — explicitly deferred by batch-6 as operator-gated).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **context-scout 2026-08-15**: re-verified context_scope, no change needed (5 entries).
**context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-08-17 (slot-16, data_engineering)**: Completed todo 2 (re-check the 2 conflict-gated Deferred items). Both
  resolved-no-action — full verdicts recorded inline on the checkbox above. Neither item produces new batch7 work: (1)
  SUSHISWAP classic-vs-V3 was already fully resolved by two operator rulings (2026-08-08, 2026-08-11) — the source doc
  `defi_venue_lst_rates_residual_2026_07_24.md` is now 4/4 done and `archive_exempt: true`; (2) the
  `defi_catalog_engine_config_key_contract_drift_2026_07_23.md` "item 2" sweep was already shipped 2026-07-24 (its
  checkbox was just stale-unflipped, corrected by `na-eligibility-audit 2026-08-01`), and that doc's whole-doc
  operator-gate has since substantially cleared via 2026-08-08/09 rulings — its one remaining open item
  (pollable-candidate-registry design) is correctly still human-gated, not a batch7 candidate.
- **2026-08-17 (slot-9, data_engineering)**: Completed todo 3 (27-doc non-batchable taxonomy re-check) and todo 4
  (`mtds_dex_pools_swaps_backfill_verification` todos-3/5 re-check). Per-item verdicts:

  **Operator-gated (16 distinct docs):**
  - `data_completion_defi_2026_07_15.md` — STILL BLOCKED. `status: active`, `last_updated: 2026-08-15`, still 16 open
    todos; the G2/G3/G4 human-only promote chain and G6 Jupiter-historical-reconstruction items named by batch6 remain
    unruled. No batch7 fold-in.
  - `defi_dedicated_bucket_shared_migration_2026_07_13.md` — CLEARED (ownership question) but NOT the specific
    batch6-named item. Doc carries a "✅ OWNERSHIP RESOLVED 2026-07-31" banner, but that resolved doc-ownership, not the
    repoint/delete-8-dead-scripts ambiguous-condition item batch6 flagged — body still shows the perp-funding script
    "confirmed dead... cannot currently run" with no operator ruling on re-scoping. STILL BLOCKED, same item.
  - `defi_migration_audit_log_2026_07_24.md` — STILL BLOCKED (7 open todos remain; multiple 2026-08 operator rulings
    landed on OTHER items in this doc — e.g. the 2026-08-15 DELETE-orphan-buckets ruling, the 2026-08-08
    governance_events MVP-scope ruling — but none touch the specific Era-B/Solana-mapping/gas-fees-denominator items
    batch6 named as still-open design calls). No new batch7 fold-in from the named items; the orphan-bucket DELETE
    ruling is already covered separately below (Too-large-or-risky).
  - `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` — STILL BLOCKED. 1 open todo remains
    (the CARRY_STAKED_BASIS delete-vs-re-leg strategy-domain call); no operator ruling found post-2026-07-30.
  - `issues/defi_archetype_universe_no_curtailment_mechanism_2026_07_23.md` — **CLEARED, 0 open todos.** A
    2026-08-16 operator ruling (round7 Q&A, MVP_SCOPE catalog-identity item) closed the doc's last open item. No new
    batch7 work to fold in — the doc is fully resolved, archival-ready (separate hygiene sweep, not this batch's scope).
  - `issues/defi_adapter_dead_code_audit_2026_07_24.md` — PARTIALLY CLEARED. 2026-08-07/08 operator rulings resolved 2
    of 4 named items (governance-parameters-refresh scoping now bounded; `thegraph_ws_adapter.py` ruled DELETE), but 1
    open todo remains (jupiter.py register-vs-delete still needs the operator per doc content) — STILL BLOCKED overall,
    no clean batch7 fold-in without a fresh read of the 1 remaining item (out of this todo's re-check-only scope).
  - `issues/defi_code_codex_drift_2026_05_27.md` — CLEARED but not net-new: doc is fully **ARCHIVED 2026-08-13** (D1-D13
    closed); the specific batch6-named item (D15 HYPERLIQUID/ASTER migration) was independently resolved 2026-08-02 via
    `hyperliquid_aster_defi_to_cefi_asset_group_migration_2026_08_02.md` (already reconciled by batch6's own todo 24 /
    this finalize plan's todo 1 reconciliation pass). No new batch7 work — already fully accounted for.
  - `/plans/archive/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` — `status: resolved`, `last_updated:
    2026-08-08`; the operator/engineering ruling batch6 was waiting on has landed and the doc is resolved. The
    large-scale 63.9M-row seed-apply execution itself is separately tracked below (Too-large-or-risky) — that piece
    still needs its own dedicated VM-backed plan, not a batch7 todo.
  - `issues/defi_lst_empty_marker_hardcoded_venue_2026_07_27.md` — ARCHIVED 2026-07-31, but the ARCHIVED banner resolved
    only the stale `locked_by` blocker batch6 also mentioned — the physical-marker-write-vs-manifest-only architecture
    decision itself is confirmed still explicitly "left for a future decision" in the doc body. STILL BLOCKED.
  - `issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` — STILL BLOCKED. 1 open todo remains, no operator
    ruling found post-2026-07-30 on the double-counting-risk question named by batch6.
  - `issues/defi_upstream_instruments_catalog_stale_2026_07_15.md` — STILL BLOCKED. 1 open todo remains, no
    post-2026-07-30 dated activity in the doc.
  - `/plans/archive/2026_07/defi_venue_phase_live_definition_contradiction_2026_07_22.md` — already noted RESOLVED +
    archived by batch6 itself; re-confirmed still archived, no change, no action.
  - `issues/deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16.md` — STILL BLOCKED. 1 open todo remains;
    the generator-vs-committed-files authority ruling batch6 named is not present in the doc's operator-ruling mentions
    (both hits are the older 2026-07-16 DRIFT/PACIFICA-kill ruling, unrelated to this item).
  - `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — STILL BLOCKED. 2 open todos remain (D1
    deferred-by-design, D4 BLOCKED-CREDENTIALS); no clearing evidence found.
  - `issues/lst_yields_writegate_permanently_blocked_2026_07_28.md` — PARTIALLY CLEARED but ARCHIVED as resolved
    2026-08-06: the wBETH/sanctumSOL UAC-registry naming item batch6 named IS done (`[x]`, unified-api-contracts@8f1c11c8),
    and PARTIAL_OK adoption shipped too. Doc fully resolved/archived — no residual open item to fold into batch7.
  - `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md` — STILL BLOCKED. 1 open todo remains;
    doc's own "Needs an explicit operator ruling" section is still open (money-path review + ShareClass convergence),
    matching batch6's characterization exactly.
  - `issues/solana_dex_pool_swaps_indexer_scope_2026_07_12.md` (+ its Solana-DEX-handlers-gap counterpart in
    `lst_exchange_rate_data_availability_2026_07_21.md`) — **CLEARED at the authoring-decision level**: operator ruled
    2026-08-08 "prioritize it now"; a dedicated implementation plan (`/plans/active/solana_dex_pool_swaps_indexer_2026_08_08.md`,
    `assigned_vm: planning`, 5 todos, sequential) + gated finalize companion were authored and are already independently
    dispatchable. No new batch7 todo needed — the real build work is already tracked outside this batch, exactly as the
    authoring decision was supposed to unblock. `lst_exchange_rate_data_availability_2026_07_21.md` itself is separately
    ARCHIVED 2026-07-30 (its own item #4 Aave-oracle wire was already done pre-batch6) — its Solana-DEX-gap follow-up
    (#5 in its own doc) is the same gap now covered by the new indexer plan, not independently open.
  - `lst_rate_honest_coverage_2026_07_21.md` — STILL BLOCKED. Phase 6 E3 recursive-staking-borrow leg (money-path) and
    the ShareClass enum convergence remain flagged "needs an explicit operator ruling" per the doc's own Phase 6 E2 row;
    Phase 5 #4 stays explicitly operator-owned by design (runner script forbids agent execution). No clearing found.

  **Time-gated (3 items):**
  - `defi_expected_unattempted_seeder_design_2026_07_26.md` / `defi_dex_pool_symbol_fix_backfill_purge_*` — already
    verdicted archivable/covered by batch6 itself; re-confirmed no change, no action needed.
  - `issues/features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md` — ARCHIVED 2026-08-02, resolved; already
    independently closed by batch6's own 2026-07-30 slot-14 Progress Log entry (D1 unblocked same day). No new work.
  - `lst_rate_honest_coverage_2026_07_21.md`'s Phase 5 #1 (blocked on `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md`)
    — STILL BLOCKED. The gating doc is `status: open` with 2 open todos remaining (root-cause diagnostic work), not yet
    fully closed — the memory-hang bug itself is not confirmed fixed (a related but distinct VM-reaping bug was fixed
    2026-08-14). Phase 5 #2 dex_pool_swaps 3-VM fleet — not independently re-checked this pass (multi-week watch item,
    outside this todo's taxonomy scope).

  **Too-large-or-risky (3 items, unchanged by design):**
  - `defi_migration_audit_log_2026_07_24.md`'s DELETE-duplicate-orphan-buckets item — operator ruling landed 2026-08-15
    per the doc's own Progress Log, but a GCS delete still requires explicit operator sign-off per the delete-safety HARD
    RULE regardless of the ruling — correctly stays a human-execution item, not a batch7 todo.
  - `/plans/archive/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`'s 63.9M-row seed-apply — doc now
    `status: resolved`, but the large-scale execution itself still needs its own dedicated VM-backed plan per batch6's
    original characterization — unchanged, not a batch7-sized todo.
  - `plans/archive/issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md`'s §6.3 (11 of 14 UAC-declared staking
    protocols unimplemented) — doc now `status: resolved`, `last_updated: 2026-08-15`, but §6.3 was explicitly named as a
    substantial multi-protocol build, not a bounded single todo — unchanged in scope even though the doc itself closed.

  **Human-only, permanently (2 items):** `data_completion_defi_2026_07_15.md`'s Progress-Log P2 sub-bucket phantom-audit
  item and `defi_migration_audit_log_2026_07_24.md`'s remaining uncategorized items — both docs confirmed still
  active/open above; no change to this classification.

  **Net result: zero new batch7 candidates drafted this pass.** The one item whose gating decision genuinely cleared
  (Solana DEX indexer authoring) already spawned its own independently-tracked, already-dispatchable plan pair outside
  this batch — exactly the outcome the deferral was waiting for, requiring no batch7 todo of its own. The
  `defi_archetype_universe_no_curtailment_mechanism` doc fully resolved (0 open todos) but produced no residual scope to
  fold in. All other items remain genuinely operator-gated, time-gated, or scope-unchanged-despite-doc-closure exactly as
  batch6 characterized them. Todo 4 (mtds_dex_pools_swaps_backfill_verification): confirmed archived 2026-08-16 with all
  17 todos `[x]` including the todo-3/todo-5 re-checks — nothing to fold in, the source doc closed on its own.
