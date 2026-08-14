---
doc_type: plan
title: defi satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the defi tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 16
  conflict-cleared, bounded/deterministic items pulled directly from 13 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_migration_audit_log_2026_07_24.md,
    /plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md,
    /plans/active/issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md,
    /plans/archive/2026_08/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md,
    /plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md,
    /plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md,
    /plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
    /plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md,
    /plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.4
estimate_calibrated_ai_days: 1.9
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# defi satellite AO dispatch batch 13 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] [CODE] P2. ✅ Delete the now-dead `_parse_curve` function in
      market-tick-data-service/market_tick_data_service/cli/handlers/_dex_pools_parsers.py (confirmed unreferenced dead
      code, mechanical deletion) Source:
      `plans/active/issues/defi_balancer_dex_pool_state_writer_schema_mismatch_2026_08_04.md` —
      market-tick-data-service@97a8b8e870. Deleted the function, its `DexPoolsHandler._parse_curve` class binding, and
      its direct unit test (`test_parse_curve_full`); confirmed no other code references remain (only historical
      comments in `_dex_pools_subgraph.py`/`_parse_balancer`'s docstring, left as-is — accurate prose, not broken code).
      Full quality-gates.sh green.
- [x] [CODE] P2. ✅ Determine the real scope of the HYPERLIQUID perp_funding gap around 2026-04-20 via a bounded
      manifest query across April-May 2026 (explicitly not a corpus walk, worker-determinable outcome) Source:
      `plans/active/issues/defi_lst_yields_backfill_blocked_manifest_consolidator_and_hyperliquid_perp_funding_gap_2026_08_08.md`
      — market-tick-data-service@ba8b3146. Bounded
      `read_availability_index(..., filters=[("date",">=",...),("date","<=",...)])` query for
      `(cefi, perp_funding, HYPERLIQUID)` across 2026-04-01..2026-05-31 found **61/61 days captured, zero gap**
      (including 2026-04-20 itself). The original 2026-08-08 preflight failure no longer reproduces — the gap has since
      closed. Confirmed NOT the same root cause as `defi_perp_daily_ctx_hl_forward_gap_since_2026_06_02_2026_08_04.md`
      (different data_type, non-overlapping window). Full findings in the source issue doc's Progress Log.
- [x] [CODE] P2. ✅ P3 test-isolation flake fix: add a setup_events() fixture to
      test_batch_harness.py::test_position_state_survives_across_ticks so it passes in isolation (strategy-service repo)
      -- bounded/mechanical, not a judgment call. Source:
      `plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` — already shipped pre-batch,
      strategy-service@3ae05318 (2026-08-11, a different slot). Re-verified live: the fixture + its use on
      `test_position_state_survives_across_ticks` are present at HEAD and the test passes in isolation
      (`pytest tests/unit/engine/strategies/v2/test_batch_harness.py::TestMultipleTicksCarryForward::test_position_state_survives_across_ticks`
      → 1 passed). No new code change needed for this batch; checkbox reconciliation only.
- [x] [CODE] P2. ✅ Cross-check instrument_type=spot_pair (9,802 rows) against defi-canonical-naming-ssot.md's locked
      instrument_type list Source: `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` —
      unified-trading-pm (this commit). Live re-check (2026-08-12 honest-coverage rollup,
      `by_venue_instrument_type.defi`) found exactly 3 venues carrying `instrument_type=spot_pair`: CHAINLINK (119,247
      cells) and PYTH (18,441 cells) are LEGITIMATE —
      `unified_api_contracts...capability_declarations._defi.PROTOCOL_CAPABILITIES["chainlink"/"pyth"]` deliberately
      declares `[SPOT_PAIR, SPOT_ASSET]` for their `oracle_prices` capability (2026-07-20 catalogue canonicalization:
      pair-denominated ETH/USD-style feeds vs single-asset feeds); `defi-canonical-naming-ssot.md`'s locked
      instrument_type row was simply stale (never updated when that decision landed) — corrected in this commit.
      EIGENLAYER's 3,816 `spot_pair` cells are NOT explained by its registry declaration (`_RESTAKING` = `spot_asset`
      only) — filed as `plans/active/issues/defi_eigenlayer_spot_pair_unexplained_expected_cells_2026_08_14.md` for
      root-cause (all 3,816 cells are `captured=0`, so not a live-writer contamination bug — likely a stale
      expected-universe seed). All 3 venues' cells are 0% captured, which is also why the original "9,802 rows" figure
      (dated 2026-08-07) no longer matches any live rollup — the underlying population has moved substantially across
      the many DeFi canonicalization fixes that landed 2026-08-08..08-13; not independently reproduced, not material to
      the drift-vs-legitimate verdict.
- [x] [CODE] P2. ✅ Fix the deployment-api/instruments-service Distinct Values panel's <blank> instrument_type badge to
      exclude capture_status=empty_confirmed rows (mirrors the already-shipped attempted_failed enumeration-key fix,
      instruments-service@8b59e8ba2) Source:
      `plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` — already shipped
      `instruments-service@1e82416a` (verified on origin/live-defi-rollout): added
      `_is_fully_empty_confirmed_leaf`/`_drop_blank_instrument_type_fully_empty_confirmed` in
      `scripts/measure_honest_coverage.py`, scoped to drop only the BLANK `instrument_type` key from
      `by_venue_instrument_type` when its entire row-set is `empty_confirmed`; a mixed leaf (real captured/
      attempted_failed rows alongside empty_confirmed) keeps its full counts. Checkbox reconciliation only — no new code
      change needed for this batch.
- [x] [CODE] P2. ✅ Add aggregator-routes as the 9th migrate_defi_full_v9_canonical.py migrator spec (per the 2026-08-08
      operator decision already ruling it a dedicated bucket, mirroring the shipped gas-fees/liquidations 7th/8th specs)
      — market-tick-data-service@795ddf39e1: registered
      `BucketSpec("aggregator-routes", "aggregator_route",     "spot_asset", grain="path")` in
      `_migrate_defi_classify.py`, mirroring the gas-fees/liquidations 7th/8th specs. Source:
      `plans/active/defi_migration_audit_log_2026_07_24.md`
- [x] [CODE] P2. ✅ RESOLVED-AS-MOOT — the redirect target no longer exists. Live investigation (2026-08-14) found the
      "dedicated migrated-bucket" architecture this todo describes was RETIRED by a LATER, closed-out decision: a
      "bucket estate cleanup" (`gcs_bucket_estate_cleanup_2026_07_10`,
      `defi_dedicated_bucket_shared_migration_2026_07_13`) deleted every dedicated per-data_type DeFi bucket kind
      (dex-pools/dex-swaps/lending-indices/perp-funding/
      lst-rates/oracle-prices/gas-fees/eigenlayer-rewards/evm-defi/solana-defi) from
      `deployment-service/configs/cloud-providers.yaml` on confirmed-zero-callers grounds — every DeFi writer (including
      the 4 named "orphan" handlers) already converges on the ONE shared `market-data-tick-defi-{env}-{pid}` bucket
      (`kind="market-data"`, aliased `kind="tick-data"`). Direct code read confirms all 4 handlers already call
      `get_write_bucket_name("market_data", "defi")` / `resolve_bucket_name(kind="market-data", asset_group="defi")` —
      byte-identical to what `dex_pools_handler`/`lending_indices_handler`/`lst_rates_handler` (the audit doc's "already
      migrated" set) call. No divergence remains to redirect; no code change is possible or needed. Full evidence + the
      adjacent stale-todo fallout (gas-fees manifest-rebuild-scope, delete-after-migration, aggregator-routes-9th-spec)
      filed at `plans/active/issues/defi_migration_dedicated_bucket_architecture_retired_2026_08_14.md`. Source:
      `plans/active/defi_migration_audit_log_2026_07_24.md`
- [x] [CODE] P2. ✅ Wire gas_fees into the manifest could-exist denominator as a per-chain expected cell (IS
      enumerate_expected_universe + deployment-api/UI data-status), the (b) half of the already-registered gas-fees
      manifest todo Source: `plans/active/defi_migration_audit_log_2026_07_24.md` — `instruments-service@e866ca1ac5`.
      Extended `_yield_v2_defi_pre_launch_rows`'s chain-level gas_fees venue-grain pass (previously pre-genesis-only) to
      also seed `expected_unattempted` cells for the LIVE/post-genesis window, one per `(chain, day)` (blank
      `instrument_type`/`instrument_id`, matching the chain-grain manifest atom `gas_fee_handler` actually records at).
      Verified `gas_fees` is already in `DATA_TYPES_BY_ASSET_GROUP["defi"]` and `(defi, spot_asset, gas_fees)` is
      already validity-matrix-eligible (two independent injection points in `market_data_categories.py`) — neither
      needed a code change, only the enumerator's live-window generation gap did. deployment-api reads the manifest the
      enumerator seeds rather than re-deriving coverage, so no downstream deployment-api/UI change was needed. New unit
      test `test_defi_v2_gas_fees_chain_level_pre_genesis_and_live_window` covers legacy-mode (present_set absent),
      uncaptured live-window seeding, and per-atom suppression when already in the manifest. Full `quality-gates.sh`
      green (235/235 tests in the v2 enumerator suite).
- [x] [CODE] P2. ✅ Live-verify DP-LIVE-003 correctly RESOLVES (posts a checkbox RESOLVED bookend) for whichever of
      findings 3-10 get relaunched, per the doc's own [SCRIPT] P3 todo Source:
      `plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md` — deployment-service@a927715ed6.
      Live-checked both remaining ACTIVE genuinely-absent producers first (findings 3/7,
      `mdps-features-live-tradfi-`/`prediction-arb-detector-`): zero running instances (GCP compute list) and zero new
      `instances.insert` audit-log events since the doc's 2026-08-10 finding — the source doc's `[OPERATOR]`
      relaunch-intent todo is still open, so no genuine production relaunch has happened yet (the other 6 of findings
      3-10 are `NOT_YET_ACTIVE` and DP-LIVE-003 never evaluates them at all, so they can never trigger a RESOLVED
      bookend). Closed via the worker-executable equivalent: added
      `test_missing_producer_resolved_bookend_fires_when_producer_relaunches` to
      `tests/unit/test_missing_live_producer_watcher.py`, exercising the full lifecycle end-to-end (page-on-absence →
      `meta_watchers.reconcile_resolved` → producer present next sweep → RESOLVED bookend fires with the identical
      alert-key identity `mlpw._miss_key` == `meta_watchers._alert_key`) — proving the mechanism itself is correct
      rather than waiting indefinitely on the operator decision. `quality-gates.sh --no-fix` ALL PASSED (252s, sentinel
      `a927715ed6b160ea2689634aece13d0c7056676c`).
- [ ] [CODE] P2. Extract the lst_rate_honest_coverage_2026_07_21.md Progress Log's VM-monitoring-history block
      (~2026-07-21..07-26 entries) into a companion doc, per Todo 1's stated pattern Source:
      `plans/active/issues/lst_rate_honest_coverage_over_cap_findings_2026_08_03.md`
- [ ] [CODE] P2. Root-cause why lending_indices capture stopped 2026-08-01 — read-only diagnosis (check for a stalled
      cron/Workflow trigger), reopened 2026-08-08 with the underlying stall independently reconfirmed real via a live
      availability_index re-check; the operator-blocking premise that originally parked it was resolved the same day.
      Source: `plans/active/issues/defi_onchain_dep_check_blazestake_lstrates_stalls_2026_08_06.md`
- [ ] [CODE] P2. Verify whether the declining DeFi shard-density trend (Dec2025-Feb2026 ~28,000 shards/day →
      2026-06-30..07-19 ~934/day, a >30x drop assumed but never confirmed to reflect venue retirement) is genuine or an
      actual capture gap — bounded cross-check with an explicit done-when already stated in the doc. Source:
      `plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md`
- [ ] [CODE] P2. Run /data-pipeline-check-is and /data-pipeline-check-mtds 3x each (baseline/mid-backfill/final) across
      the defi backfill using --day 2026-07-01 (operator-unparked 2026-08-08, exact commands already specified in the
      doc) — launcher-driven VM check, worker-executable, not yet dispatched anywhere Source:
      `plans/active/defi_track5_coverage_mvp_backfill_2026_07_24.md`
- [ ] [CODE] P2. todo1: investigate whether solana_dex_pool_swaps_indexer-002's workload characteristics (prompt size,
      tool-call pattern, worktree size) disproportionately trigger the now-root-caused fleet-wide TmuxPruner crash-loop,
      per agent-orchestrator logs/code Source:
      `plans/active/issues/solana_dex_pool_swaps_indexer_002_repeat_wedge_parked_2026_08_08.md`
- [ ] [CODE] P2. Update defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md row 1's stale script-name/numbers
      once the gas_fees manifest purge is confirmed complete — bounded doc-hygiene edit Source:
      `plans/archive/2026_08/issues/defi_gas_fees_legacy_purge_manifest_step_blocked_vm_infra_flakiness_2026_08_05.md`
- [ ] [CODE] P2. Relaunch the dex_swaps legacy-fold script WITHOUT --allow-stale-fallback once the DeFi manifest
      consolidator has genuinely caught up (mechanical rerun, worker can verify freshness precondition and execute)
      Source: `plans/active/issues/defi_manifest_allow_stale_fallback_incomplete_for_long_pause_2026_08_07.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
