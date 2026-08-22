---
doc_type: plan
title: DeFi satellite AO batch 19 — extraction from the 2026-08-21 /ag-closeout-audit defi Phase 2/3 sweep
summary: >-
  Satellite-batch extraction from `ag_closeout_audit_defi_parked_2026_08_21.md`'s "Orphaned — compact table" (54
  rows). Re-classified each row against the bounded-vs-gated taxonomy (re-reading the target doc, not trusting the
  parked doc's one-line summary); of the rows read in full this pass, 3 conflict-cleared bounded items from 3 source
  docs are extracted here. The remaining rows stay untouched: most are genuinely operator/design/human/time-gated
  (many already reconfirmed correctly-NA by 3-8+ prior na-eligibility-audit rounds each, per the parked doc), several
  are already claimed by the still-draft `batch14`/`batch18` (false-orphans, not re-extracted here), and a residual
  set was not read in full this pass for budget reasons — see the parked doc's own Progress Log for the explicit
  not-yet-covered list. This batch also carries no [OPERATOR]-tagged items — every extracted todo is a read-only
  verification, a re-run-and-report VM check, or a reversible manifest reclassification already dry-run tested and
  cited against the GCS delete-safety protocol.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [deployment-api, unified-api-contracts, market-tick-data-service, market-data-processing-service]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-extraction, batch-19, ag-closeout-audit]
related:
  [
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_21.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_satellite_ao_dispatch_batch14_2026_08_16.md,
    /plans/active/defi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md,
    /plans/active/issues/dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-21"
last_updated: "2026-08-21"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
milestone: M3
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: medium
thinking_tier: high
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/issues/ag_closeout_audit_defi_parked_2026_08_21.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
source: >-
  `/ag-closeout-audit defi` Phase 2/3 sweep, 2026-08-21 (sub-agent pass over `ag_closeout_audit_defi_parked_2026_08_21.md`'s
  105-candidate Phase-1 output). Each extracted item's source doc was re-read in full (not just the parked one-liner)
  before extraction, per the shared conflict-check protocol §3.
sequential: false
drift_direction: advance-code
---

# DeFi satellite AO batch 19 — 2026-08-21

> **2026-08-22 — promoted per D8 ruling.** Was `draft` / `assigned_vm: NA` deliberately (per the same skill safety
> rail `batch14`/`batch18` used) pending explicit sign-off. D8 (ADOPTED-REC 2026-08-21, autonomous-dispatch
> authority, AUTONOMOUS_AGENT_RULES rule 2) supplies that sign-off ("Promote all — already conflict-checked,
> vetted work idle only for lack of sign-off; the defi batch also stops recurring false DP-FETCH-009 pages").
> Flipped `status: draft` → `active` above (per this dispatch's literal instruction). **`assigned_vm` stays `NA`**
> — flipping it to `planning` requires a gated finalize-companion plan per `task_template.md` §4 (the plan-hygiene
> pre-commit gate confirmed this: `check_ag_closeout_linkage`/finalize-coverage failed on the attempt), which is
> its own follow-on authoring task, not part of this dispatch; left as a `- [ ]` follow-up in this doc's own todos
> if/when AO dispatch of this batch is wanted. The batch is now a normal active, human-executed (`NA`) plan.

## Todos

- [ ] [SCRIPT] P1. **Register `(HYPERLIQUID, HYPERLIQUID)` and `(ASTER, BSC)` in UAC's `ALL_DEFI_VENUES` +
      `DEFI_VENUE_DATA_TYPE_CAPABILITIES`.** The underlying design question (does declaring these two CEFI/DEFI
      hybrid venues into DEFI's registries risk double-counting against CEFI's own coverage numbers) is already
      operator-ruled NOT a risk — `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` records
      the ruling directly ("Separately confirmed as NOT a bug... The `0/0` under DEFI isn't evidence of a bug on its
      own"), and the source doc's own reclassification (2026-08-08) already downgraded this todo `[CODE]` -> `[SCRIPT]`
      ("no further design decision needed first"). Re-verified 2026-08-21: both venues are STILL absent from
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py` (`ALL_DEFI_VENUES`) and
      `unified-api-contracts/unified_api_contracts/registry/defi_venue_capabilities.py`
      (`DEFI_VENUE_DATA_TYPE_CAPABILITIES`) — 0 grep hits each, unchanged since the 2026-08-08 check. Real data
      types to declare per the source doc's own live GCS sweep: HYPERLIQUID (own-chain-label venue, 3,768,971 real
      rows 2023-11-01→2026-05-31) and ASTER-BSC (1,066,091 real rows 2024-04-03→2026-05-31) — confirm current
      `capture_status`/`data_type` breakdown live before declaring exact data_type keys (the cited counts are from
      the 2026-07-07 sweep, re-verify freshness). Repo: unified-api-contracts. Source:
      `plans/active/issues/defi_turbo_api_hides_real_captured_data_2026_07_07.md` (its sole remaining open todo).
      Done when: both venue+chain pairs resolve in `ALL_DEFI_VENUES`, matching `DEFI_VENUE_DATA_TYPE_CAPABILITIES`
      entries exist for their real captured data_types, and the turbo API (`GET /api/data-status/turbo`) reports
      non-zero coverage for both instead of `0/0`/absent.

- [ ] [SCRIPT] P2. **Run the DEX-pool-swaps stale-row reclass script's `--apply` pass on a dedicated VM.**
      **Safe-idempotent, not a delete**: the script (`market-tick-data-service/scripts/reclass_defi_uniswap_v3_schema_validation_failed_stale_2026_08_17.py`,
      already shipped + dry-run tested, `market-tick-data-service@1b620c5485`) reclassifies 13,673
      `SCHEMA_VALIDATION_FAILED` rows (13 stale UNISWAP_V3/ETHEREUM `dex_pool_swaps` dates, 2025-01-09..21, already
      re-captured cleanly with current code per the source doc's live re-verification) to
      `error_reason=superseded_by_verified_recapture_success_2026_08_16` — a reversible manifest-classification
      change (`attempted_failed` -> a superseded-tagged variant already excluded from DP-FETCH-009's count via
      `SUPERSEDED_BY_REASON_PREFIX`), no row or GCS object deleted, no data lost. VM launch needed only because the
      defi `_index/availability_index.parquet` is ~159M rows / ~6.8GiB — too large for a full read/write on a
      shared host per the heavy-I/O HARD RULE (`/codex/05-infrastructure/vm-launcher-runbook.md`), not because the
      operation itself is risky. Gate `--apply` on a fresh reversibility check
      (`softDeletePolicy.retentionDurationSeconds` on the target bucket) per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a before running, per the script's own existing
      design. This is the step that actually stops DP-FETCH-009 from re-paging on these 13 dates (4 confirmed
      re-fires as of 2026-08-17, short of the natural ~2026-08-24 window-aging). Repo: market-tick-data-service.
      Source: `plans/active/issues/dp_fetch_009_defi_dex_pool_swaps_uniswap_v3_ethereum_stale_schema_validation_failed_2026_08_16.md`
      (its sole remaining open todo). Done when: the reclass `--apply` run completes on a dedicated VM, the
      reversibility check is filed, and a post-apply manifest query confirms the 13 dates no longer count toward
      DP-FETCH-009's `attempted_failed` total.

- [ ] [DATA] P1. **Re-run the DEFI `/data-pipeline-check-mdps` `--legs force,skip --require-captured --auto-day`
      matrix and consolidate the report with the other 4 asset groups.** Both blocking fixes this todo depends on
      are shipped and re-verified: the chain-axis key-composition fix
      (`market-data-processing-service@fae666bef2`) and the streamed-read replacement removing the ~160M-row
      full-manifest OOM (`market-data-processing-service@6ee153a0`, `unified-trading-library@11f1ebd1`), plus the
      cross-leg-retention `gc.collect()` fix (`market-data-processing-service@4990d2361`, independently re-verified
      2026-08-21 via direct code read + git blame per the source doc's own Progress Log). The prior 3 re-run attempts
      hit OOM/silent-death (root-caused + fixed each time) — this run should be the first clean terminal verdict.
      Standard `/data-pipeline-check-mdps` VM launch (a check driver, not a data-mutating backfill) — no delete-safety
      gate applies. Repo: market-data-processing-service (verification only; no code change expected unless the
      re-run surfaces a NEW gap). Source:
      `plans/active/issues/mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md` (its sole
      remaining open [DATA] P1 todo). Done when: the DEFI leg reports a real (non-"PROVED NOTHING") verdict with a
      nonzero verified-cell count, and the result is folded into `data_pipeline_check_mdps_features_2026_07_20.md`'s
      5-AG consolidated report.
      **2026-08-21 update (slot-24)**: attempted 4x this session — still "PROVED NOTHING", but the OOM/chain-axis/
      streamed-read bugs this todo's premise depended on are now confirmed fixed and NOT the cause. New, deeper
      blocker (consolidated index blob stale despite a healthy consolidator) filed at
      `plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`
      — read that doc before the next attempt.

## Conflict-check (per item, §3 protocol)

- **Turbo API HYPERLIQUID/ASTER registration**: grepped `plans/active/*.md` for `HYPERLIQUID.*ASTER`,
  `ALL_DEFI_VENUES.*HYPERLIQUID`, and the source doc's own filename — only hit is the source doc itself and
  `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md` (the sibling doc holding the operator
  ruling this todo cites, not a competing claim on the registration work itself). No active plan/batch already
  claims this registration. Clear.
- **DP-FETCH-009 reclass `--apply`**: grepped `plans/active/*.md` for `dp_fetch_009_defi_dex_pool_swaps_uniswap_v3`
  and `reclass_defi_uniswap_v3_schema_validation_failed` — only hit is the source doc itself. No active
  plan/batch already claims this VM run. Clear.
- **MDPS DEFI e2e re-run**: grepped `plans/active/*.md` for `mdps_defi_pipeline_e2e_check_zero_captured_days`,
  `PROVED NOTHING.*DEFI`, and `pipeline-e2e-check-mdps` — only hit is the source doc itself
  (`data_pipeline_check_mdps_features_2026_07_20.md`, the consolidating parent doc, is a citation target, not a
  competing claim on the DEFI-leg re-run specifically). Clear.
- **2026-08-22 re-check (D8 promotion)**: re-ran all 3 basename greps fresh — same zero-conflict result as
  2026-08-21 authoring time; `defi_turbo_api_hides_real_captured_data_2026_07_07.md`'s own remaining open todo
  still reads "➡️ EXTRACTED → plans/active/defi_satellite_ao_dispatch_batch19_2026_08_21.md" (its other citing
  docs — batch2/batch3_finalize/lst_rates_residual/instruments_completion_tracker — reference already-closed,
  different historical sub-items, not this one). No drift since drafting.

## Not extracted this batch — non-batchable taxonomy (rows read in full this pass)

**Operator-gated**:

- `issues/three_chain_registries_disagree_none_authoritative_2026_08_19.md` — sole open item is
  `BLOCKED-OPERATOR-DECISION` (the ONCHAIN pseudo-chain keep/remove ruling `chain_env.py:655-656` names). Genuinely
  a one-line ask, but still requires the operator's call — not batchable. Worth surfacing as a cheap operator ask.
- `issues/defi_oracle_prices_onchain_branch_retry_starvation_2026_08_16.md` — 2 open P2 todos are both gated on the
  pre-existing `mtds-oracle-prices-backfill` VM reaching a terminal state, the SAME open question tracked as its own
  todo in `uac_data_type_validity_combinator_fragmentation_2026_07_07.md`. Re-check once that VM's terminal state is
  determined (see this session's Progress Log note on that doc).

**Time/condition-gated**:

- `issues/dp_vm_002_mdps_defi_2022_dex_pool_swaps_pregenesis_no_manifest_trace_2026_08_15.md` — sole open todo is
  conditional ("if DP-VM-002 pages again for another `mdps-<ag>-<year>-*` VM, confirm..."), nothing to act on
  unless/until it re-fires.

**Genuinely design/build work, not bounded** (re-confirmed unchanged this pass):

- `issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md` — 4 remaining open items each
  self-declare an unresolved design question (own 2026-08-21 na-eligibility-audit wave-2 verdict: KEEP-NA valid,
  same day as this sweep).
- `strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` — beta-hedge/vol-target need a new
  book-level aggregation layer designed first (see this session's Progress Log note added to that doc).

**Already correctly resolved, no action needed**:

- `issues/glassnode_kaiko_credential_ask_2026_08_09.md` — Kaiko half already fully decommissioned (banned vendor,
  2026-08-10); Glassnode half is genuinely `BLOCKED-CREDENTIALS`, correctly `assigned_vm: NA`.
- `issues/defi_gas_net_cost_partial_wiring_gap_2026_08_17.md` — already self-dispatching
  (`assigned_vm: planning`, `execution_scope: orchestrator-agent`); sole remaining P3 todo will feed the AO backlog
  on its own, no extraction needed.

**Not read in full this pass** (budget — see the parked doc's Progress Log for the complete list of rows not yet
individually re-verified): `data_completion_defi_2026_07_15.md`, `defi_cf2_cf3_legacy_canonical_backfill_2026_08_08.md`,
`defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`, `defi_live_poller_phased_build_2026_08_15.md`,
`defi_migration_audit_log_2026_07_24.md` (residual items beyond what batch18 already extracted),
`defi_track5_coverage_mvp_backfill_2026_07_24.md`, `elysium_*` (2 docs, both repeatedly reconfirmed human-only),
`issues/defi_aavev3_bare_alias_enumerator_bug_2026_08_08.md`, `issues/defi_adapter_dead_code_audit_2026_07_24.md`,
`issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md`,
`issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md`,
`issues/defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md`,
`issues/defi_consolidator_paused_by_inflight_rebuild_vm_2026_08_07.md`,
`issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md` (already partly covered by batch18),
`issues/defi_lst_adapter_factory_family_unused_by_production_path_2026_08_09.md`,
`issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md`,
`issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`,
`issues/defi_morpho_lending_indices_never_wired_2026_07_12.md`,
`issues/defi_orphan_bucket_delete_list_includes_canonical_bucket_2026_08_15.md`,
`issues/defi_pyth_oracle_prices_seeded_feeds_unfetchable_2026_08_03.md`,
`issues/defi_strategy_ids_carry_banned_sce_suffix_identity_migration_2026_08_19.md`,
`issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`,
`issues/defi_venue_e2e_batch1_deferred_followups_2026_08_17.md`,
`issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`, `issues/exec_tenderly_2026_08_15.md`,
`issues/health_factor_monitor_no_production_entrypoint_liquidation_unprotected_2026_08_19.md` (already escalated
via the cross-tranche big-findings doc), `issues/mev_engines_no_tenderly_simulate_bundle_call_site_2026_08_19.md`,
`issues/onchain_staking_apy_bps_single_day_annualization_noise_2026_08_09.md`,
`issues/pendle_venue_onboarding_2026_08_16.md`, `issues/pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21.md`
+ `pnl_true_native_staking_return_spec_2026_08_20.md` (already extracted via batch18), `lst_rate_honest_coverage_2026_07_21.md`.
Docs already confirmed as false-orphans (claimed by draft `batch14`/`batch18`) are excluded from this list per the
parked doc's own table annotations.

## Progress Log

- **2026-08-21 (ag-closeout-audit defi tranche, Phase 3 sweep)**: drafted from `ag_closeout_audit_defi_parked_2026_08_21.md`'s
  "Orphaned — compact table". 3 items extracted from 3 fully-re-read source docs (all conflict-clear); a further
  ~10 rows read in full and correctly declined (operator/time/design-gated, or already resolved); the remainder of
  the 54-row table not read in full this pass for budget reasons (see the list above). `status: draft` per the
  skill's safety rail — flipping to `active` is an operator decision, not made here.
- **2026-08-21 (slot-24, data_engineering)**: item 3 (DEFI pipeline_e2e_check re-run) attempted 4x — still
  "PROVED NOTHING". The OOM/chain-axis/streamed-read fixes item 3 assumed were the last blockers are all confirmed
  working; found a new, deeper root cause instead (consolidated index blob stale despite a healthy consolidator),
  filed at
  `plans/active/issues/mdps_defi_captured_days_stale_consolidated_index_despite_healthy_consolidator_2026_08_21.md`.
  Also fixed an unrelated pre-existing pip-audit CVE (`PYSEC-2026-3721`) blocking shipment in
  unified-trading-library along the way. Item 3 stays not-done.
