---
doc_type: issue
title: plan_reconciler findings — defi tranche — 2026-08-06
summary:
  Run-findings doc for the sharded daily plan-reconciler run (tranche=defi). Candidate register, verification results,
  applied fixes, routed items, coverage ledger.
status: open
created: "2026-08-06"
author: plan_reconciler
source: agt-24f4b0
nature: issue
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
parent_epic: defi_master
priority: P3
assigned_vm: NA
resolved_by: >-
asset_group: [defi]
tags: [plan-reconciler, run-findings, defi]
related: [defi_consolidated_closeout_2026_07_18]
locked_by: agt-24f4b0
---

# plan_reconciler run findings — defi tranche — 2026-08-06

Dispatch: `agt-24f4b0` · slot 7 · tranche `defi` · review branch `plan_reconciler/agt-24f4b0`

## Scope + inventory

- defi-tranche corpus (asset_group matching defi): **96 docs** = 28 active plans + 67 issue docs + 1 epic
  (`defi_master`)
- 12h GRACE SET (read-only this run): **45 docs** — heavily in-flight corpus (batch9/batch10 dispatches,
  hyperliquid→cefi migration, LST-rate work)
- WORKING SET (fixable): **51 docs** = 41 with open todos + 9 fully-done/zero-open candidates + 1 epic (41 open todos)
- Zero-checkbox docs in working set: `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `defi_kamino_lending_venue_drift_live_data_verification_gap_2026_08_04.md`,
  `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`

## Flips verified

(append as confirmed)

## Contradictions

(append as confirmed)

## Doc-drift

(append as confirmed)

## Hygiene fixes

(append as applied)

## Filed

(append as filed)

## Archive candidates (operator review)

(append as confirmed)

## Refuted (dropped by verify)

(append as refuted)

## Coverage (hunters / batches / docs)

(append per hunter batch)

## Plans not reached

(append if any)

## Phase-5.9 ledger

- routed_to_operator: TBD
- parked_in_issue_doc: TBD
- agent_skips: TBD (enumerated below if any)

## Run progress — pre-compact checkpoint 2026-08-06 20:31 UTC

**State**: STEP 3 in flight — 10 read-only hunters launched in parallel (all model=sonnet, full
SUB_AGENT_MANDATORY_RULES injected). Results arrive as notifications; each feeds STEP 4 (adversarial verify: refuter +
confirmer, tiebreaker on splits; HARD-evidence bar for flips = sha reachable on `origin/live-defi-rollout` via
`git merge-base --is-ancestor`, or artifact live via grep-then-READ). Then STEP 5 (apply on review branch only), STEP 6
(route via `/blocked` + file here), STEP 7 (PR plan_reconciler/agt-24f4b0 → live-defi-rollout), STEP 8 (/done when no
open questions).

**Hunter roster (10)**:

- H1/H2/H3 — epic-cluster: defi_master.md + lst_rate_honest_coverage, data_completion_defi,
  data_pipeline_check_mdps_features, defi_satellite_batch2, cryptovenue, defi_collateral_sizing, cefi_ml_directional,
  defi_track5, defi_pipeline_e2e, instruments_satellite_batch1
- H4/H5/H6 — issue-cluster: all 23 working-set issue docs (defi_catalog_engine_config_key_contract_drift,
  estate_orphan_assessment, defi_morpho, defi_archetype, autonomous_session_operator_decisions, pnl_interest_accrual,
  mtds_is_full_adapter_smoketest, honest_coverage_shard_dimension, candle_feature_canonical_path_divergence,
  non_tardis_dexperp, defi_upstream_instruments_catalog_stale, defi_perp_daily_ctx_manifest_gap, defi_turbo,
  defi_expected_unattempted_backlog, defi_lst_oracle, backfill_smoke, adapter_findings, defi_legacy_precanonical,
  mtds_gas_fees, features_service_clean_check, defi_pipeline_mode_yearn, mdps_features_deadcode, dex_pool_state_build)
- H7 — missed-flip sweep: all ~96 defi docs, open `- [ ]` with sha/PR/artifact evidence in own text
- H8 — codex-alignment: 9 working active plans vs cited codex SSOTs (defi-canonical-naming-ssot, honest-coverage-model,
  pipeline-mode-partition, availability-manifest, honest-absence, defi-execution-overview, live-data-persistence,
  feature-formula-versioning)
- H9 — mechanical adjudicator: non-canonical todos (candle_feature:485, defi_pipeline_mode_yearn:158/166,
  mdps_features_deadcode:112), AG-closeout orphans (defi), terminal-status, line-caps
  (defi_cefi_venue_chain_axis_contamination ~1001L over-cap — GRACE, flag only), 3 zero-checkbox docs, 6 fully-done docs
- H10 — AO-readiness (vm=planning plans) + grace-set status one-liners

**Phase-0 mechanical inputs (measured, re-derivable in seconds)**:

- defi corpus = `rg -l '^asset_group:.*defi' plans/active/*.md plans/active/issues/*.md plans/epics/*.md` → 96 docs
  (28+67+1)
- grace set (45 docs): newest `git log -1 --format=%ct` <12h — heavily in-flight (batch9/batch10 2026-08-06,
  hyperliquid→cefi migration, LST-rate work); read-only this run
- working set (51 docs): 41 with open todos + 9 fully-done/zero-open + epic (41 open)
- AG-closeout orphans in defi (real, per check_ag_closeout_linkage.py):
  defi_balancer_dex_pool_state_writer_schema_mismatch, defi_bridge_events_historical_backfill_gap,
  defi_dex_pool_swaps_733_row_indexer, defi_onchain_dep_check_blazestake, delta_one_get_available_instruments,
  dex_pool_state_build_instrument_id_colon, features_service_clean_check, lighter_tardis_writerless_route_hang,
  mtds_gas_fees_migration_script (+ my findings doc itself, now linked via
  `related: [defi_consolidated_closeout_2026_07_18]`)
- terminal-status-archived (3, ALL non-defi: sit_stamp_skipped, sports_mtds_backfill_vm_unscoped, omniroute) +
  archive-candidates (2, non-defi: archive_candidates_content_verification_backlog, cloudbuild_template_behind_repos) —
  sibling tranche shards' scope
- reference-path violations (83 format / 88 dangling): NONE in defi-tranche docs — all plans/ai, plans/audit,
  plans/prompts, scratch_scenarios_day1, codex/, sports/ci-owned
- fully-done working docs (archive candidates to verify): instruments_satellite_ao_dispatch_batch1,
  issues/defi_expected_unattempted_backlog_1m, issues/autonomous_session_operator_decisions,
  issues/dex_pool_state_build_instrument_id_colon_in_symbol, cefi_deribit_binance_futures_bundle_verification_finalize,
  issues/defi_lst_oracle_timestamp_glued_instrument_id (last two locked_by live-defi-rollout — LOCKED, operator-gated)
- zero-checkbox working docs: issues/candle_feature_canonical_path_divergence (0 open/0 done — read in full: finished
  record vs prose work), issues/defi_kamino_lending_venue_drift_live_data_verification_gap,
  issues/mtds_pipeline_check_process_killed_during_skip_leg_poll

**Scratch tools (deliberately NOT promoted — re-derivable in seconds)**:

- `/tmp/defi_inventory.py` (per-doc open/done/age/status inventory; the findings-doc sections above already carry the
  derived facts)
- `/tmp/defi_batches.py` (hunter batch file lists)
- `/tmp/defi_docs.txt` / `/tmp/defi_working.txt` (doc path lists)
- `/tmp/hygiene_sweep.txt` (sweep output; the numbers are recorded above)
- None are referenced by any committed doc; no secrets anywhere (checked).

## Deferred work after 2026-08-06

| Item                                                             | State / why deferred                | Blocked-on                                |
| ---------------------------------------------------------------- | ----------------------------------- | ----------------------------------------- |
| STEP 4 — adversarial verification of hunter candidates           | Not done — 10 hunters still running | hunter results (notifications)            |
| STEP 5 — apply confirmed fixes on review branch                  | Not done — verification first       | STEP 4                                    |
| STEP 6 — route contradictions/doc-drift via /blocked + file here | Not done                            | STEP 4                                    |
| STEP 7 — open PR plan_reconciler/agt-24f4b0 → live-defi-rollout  | Not done                            | STEP 5/6                                  |
| STEP 8 — POST /api/plan_health/result + /done                    | Not done                            | STEP 7 + operator answers to any /blocked |

**Next item**: collect hunter results → dedup → STEP 4 refuter/confirmer pass.
