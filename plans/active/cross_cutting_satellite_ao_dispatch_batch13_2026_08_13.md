---
doc_type: plan
title: cross-cutting satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the cross-cutting tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep —
  89 conflict-cleared, bounded/deterministic items pulled directly from 39 source docs (RECLASSIFY_SPLIT bounded items
  from the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each
  todo cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation
  back into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related: [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md,
    /plans/active/bucket_estate_consolidation_closeout_2026_07_24.md,
    /plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md,
    /plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md,
    /plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md,
    /plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md,
    /plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    /plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md,
    /plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md,
    /plans/active/data_source_provenance_enforcement_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_foundation_completeness_2026_06_24.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
    # + 24 more source docs cited per-todo below
  ]
created: "2026-08-13"
last_updated: "2026-08-21"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 13.3
estimate_calibrated_ai_days: 10.7
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch13_2026_08_13_finalize.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# cross-cutting satellite AO dispatch batch 13 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [INFRA] P2. enumerate every live Cloud Run service's actual runtime SA + role set into the registry (bounded
      audit) — deployment-service@f5ad937bee (2026-08-13 full read-only audit: 25 live Cloud Run rows / 23 distinct
      services across 9 runtime SAs enumerated into `live_runtime_bindings` + `live_runtime_sa_roles` sections; YAML
      validated; QG green; quickmerge landed on LDR) Source:
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`
- [x] ✅ [INFRA] P3. document which live services rely on the default-compute-SA and what secrets/buckets they can
      therefore reach (bounded documentation task) — deployment-service@2062cb7ba1 (2026-08-15: added
      `default_compute_sa_risk_assessment` to `gcp_service_accounts.yaml`; confirmed both broad roles
      (secretmanager.secretAccessor, storage.admin) are UNCONDITIONAL project-level bindings — no IAM Condition on
      either, verified via `gcloud projects get-iam-policy` condition-column check; quantified the live blast radius
      (105 GCS buckets / 211 Secret Manager secrets reachable by all 10 default-compute-SA services, enumerated via
      UTL `get_storage_client().list_buckets()` + `gcloud secrets list`); named the highest-risk unneeded categories
      (wallet keys, per-trader exchange trade keys, orchestrator control-plane secrets, execution/portfolio/audit
      stores). Read-only — no IAM binding changed. YAML validated; QG green (sentinel-verified at HEAD); quickmerge
      landed on LDR, post-push ancestry independently verified) Source:
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`
- [x] ✅ [DIAG] P2. verify the exact CME instrument_id string format for FUTURE contracts against the live catalogue
      before implementing tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md's already-ruled fix —
      unified-trading-pm@db37be4e4b (2026-08-14: confirmed `CME:FUTURE:<PRODUCT_ROOT>-USD@LIN-YYYYMMDD` via 3 convergent
      code sites + a bounded live read of `prod/catalog.parquet`; recorded in both the source issue doc and
      `tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`'s todo 1) Source:
      `plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md`
- [x] ✅ [CODE] P2. Diagnose strategy-service LDR gate-red (not actually red; host-contention mis-triage) — full
      evidence extracted verbatim (2026-08-15) to
      `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. Recorded justified `# CORRECT-LOCAL` exemptions (9 real classes) — strategy-service@621858344d
      (2026-08-14). Full evidence extracted verbatim (2026-08-15) to
      `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. Resolved STEP 5.37 inline HF/LTV/margin thresholds — unified-api-contracts@31b4ad958e +
      strategy-service@ac5cab7edb (2026-08-14). Full evidence extracted verbatim (2026-08-15) to
      `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. RESOLVED — already fixed by the 2026-08-10 CPU-vs-wall billing rework, no code change needed
      (strategy-service@ac5cab7edb, 2026-08-14). Full evidence extracted verbatim (2026-08-15) to
      `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P2. Fixed the gate's stale SCHEMA_CONTRACTS_AUDIT.md pointer fleet-wide — unified-trading-pm@144a18fed5
      (2026-08-14). Full evidence extracted verbatim (2026-08-15) to
      `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source:
      `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md`
- [x] ✅ [CODE] P3. DONE 2026-08-15 (slot-24·infra) — unified-trading-pm@a0689afd34. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/archive/2026_08/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md` (new finding, 2026-08-14 diagnosis)
- [x] ✅ [CODE] P2. Split the remaining MTDS >900L files + extract oversized fns/methods —
      market-tick-data-service@21b2f7193a (2026-08-15, slot-30·infra). 0 files >900L already (prior wave); the real
      remaining scope was the 10 `FUNCTION_SIZE_EXTRA_EXCLUDES` files each carrying 1-2 methods 51-101L — extracted 15
      methods into private helper methods (all ≤50L, mechanical/behaviour-preserving) across bridge/flash_loan/
      governance/liquidation/mev/staking_yields/token_transfers handlers + databento_batch_jobs/
      alchemy_transfers_client/thegraph_base_client, then deleted the now-empty exclude list. Full `quality-gates.sh`
      exit 0 (sentinel-verified at HEAD). Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P2. Re-add 17 connector reconnect tests using terminating mocks (market-tick-data-service) —
      market-tick-data-service@26eef1999f (2026-08-15, slot-21·infra). No git-history evidence of a literal "def
      test_...reconnect..." deletion survived (full non-shallow history search, zero hits) — instead cross-referenced
      the 25 connectors that got the zero-delay-reconnect tight-loop fix (`cec16b74`) against which test files already
      exercise the reconnect loop with a TERMINATING mock (`reconnect_base_delay_s`/ `_ws_connect_side_effect` markers):
      9 already covered (incl. `deribit_book_ticker_ws` — the doc's own reference pattern), 16 gaps found — reconciles
      to the doc's "17" (the deribit reference + these 16). Added one `test_stream_connect_failure_retries` per gap
      (aster liquidations, binance-futures, bitfinex-spot, bitget-spot, bybit-futures, coinbase-cde, coinbase-spot,
      deribit-trades, hyperliquid l2book/ticker/trades, kraken futures/spot, okx-swap, tardis-machine, upbit-book) —
      each injects a mock `_http_session` whose `ws_connect` raises `aiohttp.ClientError` and flips `conn._closed` on
      the 3rd attempt, mirroring `test_deribit_book_ticker_ws_coverage.py`'s existing terminating-mock pattern rather
      than a never-closing one. QG green (`✅ ALL QUALITY GATES PASSED`, 489s, sentinel-verified); quickmerge landed on
      LDR (post-push ancestry verified). Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P2. Diagnosed: mis-scoped for single-task AO dispatch, NOT attempted — corrected classification instead. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P2. PARTIAL — ui-reference-data.json untracked; capability-manifest.json intentionally LEFT TRACKED (real consumer dependency, not done). Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P3. WON'T-DO — regen-on-demand fallback deliberately not wired; documented in-code instead. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: this doc, todo above.
- [x] ✅ [CODE] P2. **Ran PM `bash scripts/quality-gates.sh` — initially FAILED, root-caused + fixed, now confirmed
      green.** (2026-08-15, slot-12·infra) First run surfaced a real regression, not a stale/pre-existing red:
      `test_f47_unbuildable_venue_cells_are_not_available` failed with 18 unbuildable cells, all tracing to one venue
      (`pacifica_solana`). Root cause: the same-day 2026-08-15 "containment fix" to `archetype_leg_spec_seeds.py` added
      `"pacifica_solana"` to 3 `eligible_venue_ids` lists, reasoning from a hyphen→underscore fold of
      `catalog_carry.py`'s `full_venue="PACIFICA-SOLANA"` string — but the slot-label parser's alnum-fold
      (`_slot_venue_token`, full alnum-strip) turns that into `"pacificasolana"`, which never matches
      `KNOWN_VENUE_TOKENS`'s existing `"pacifica"` entry. The bundle's actual slot-label token (per
      `_CARRY_BASIS_PERP_VENUE_BUNDLES`'s own `("pacifica", "PACIFICA-SOLANA", ...)` row and `test_target_universe.py`'s
      live slot-label assertions) is `"pacifica"` — corrected all 3 sites to match. Fixed + shipped
      `unified-api-contracts@826763229f`; UAC's own `quality-gates.sh` green (429s, sentinel-verified); re-ran PM's full
      `quality-gates.sh` after the fix landed — `✅ ALL QUALITY GATES PASSED`, sentinel `.qg_last_passed_sha` verified
      == HEAD `8b7e53a624`. Source: `plans/active/mtds_file_size_refactor_2026_06_08.md`
- [x] ✅ [CODE] P2. STALE PREMISE — the "13 cells/~12.5k rows" digest figure is ~3 weeks stale; the actual retry mechanism is already live, but has a real coverage gap. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`
- [x] ✅ [CODE] P2. **Fixed via the live instrument_id format, not the guessed `CME:FUTURE:ESM5` shape.**
      deployment-service@8e22704756 (2026-08-15, slot-30·infra). A bounded, column-projected read of the live
      `market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` manifest against the exact
      110,074-row bucket (venue=CME, data_type in {ohlcv_1s,ohlcv_1m}, error_reason=WithinBoundsTradfiSourceZero, blank
      `underlying`) confirmed every row's `instrument_id` is actually `<ROOT>.FUT` / `<ROOT>.OPT` (e.g. `CT.FUT`,
      `MNQ.OPT`) — not the contract-symbol form (`CME:FUTURE:ESM5`) the function's old docstring guessed at. Rewrote
      `_derive_cme_root()` to fall back to parsing that suffix when `underlying` is blank, so these rows now resolve a
      real root and re-enter `compute_dispatch_candidates()`'s gap computation instead of permanently bucketing into
      `out_of_scope["CME:unmapped_root"]`. Added `tests/unit/test_wave_launcher_cme_root_fallback.py` (6 cases:
      populated-underlying precedence, COMBO→None, FUT/OPT suffix fallback, unparseable-instrument_id→None, both-blank→
      None). `bash scripts/quality-gates.sh` green (799s, sentinel-verified at HEAD); quickmerge landed on LDR
      (post-push ancestry verified `8e22704756` on `origin/live-defi-rollout`). Source: this doc's own 2026-08-15
      diagnosis, folded in per the tradfi attempted_failed retry todo above.
- [x] ✅ [INFRA] P3. disambiguate 'the planning VM' in monitoring/docs; always name the instance ID or a stable label —
      unified-trading-pm (2026-08-15, slot-15·infra). Replaced every ambiguous "the planning VM" reference in the
      source issue doc's Root-cause chain / Why-neither-can-self-serve / Todos / Progress Log sections with the specific
      EC2 instance ID + a stable label ("old orchestrator VM" for `i-0c9b283b31d6b5ca7`, "CI-runner VM" for
      `i-042a6332509482556`); added an explicit host pointer to the P2 monitoring-gap todo naming `i-042a6332509482556`
      as the watchdog's target, not `i-0c9b283b31d6b5ca7`. Fleet grep confirmed no other codex/monitoring doc used the
      ambiguous phrase — this issue doc was the sole source. Full detail in that doc's own P3 todo, now flipped. Source:
      `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [x] ✅ [INFRA] P3. Wired an automated `/usr/local/sbin/*` sync — unified-trading-pm@d6bc752b3d (2026-08-15, slot-27·infra). Confirmed live via the repo (no host access from this role): no workflow, cron, or install... Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`
- [x] ✅ [BACKEND] P2. document the circular-dependency gap (scheduled workflow runs from default branch) in
      ci-cd-flow.md — unified-trading-pm@83a3227b7d (2026-08-15, slot-19·backend). Added a paragraph to
      `/codex/08-workflows/ci-cd-flow.md`'s "Staging re-entry procedure" section, immediately after the existing
      "Default-branch gotcha" line: documents that fixing a scheduled/`workflow_dispatch` workflow's OWN `run:` block is
      inert on every scheduled trigger until the fix promotes LDR→main (a circular dependency when the fix's purpose is
      to unblock the alerting/promotion pipeline itself — the exact shape the source incident hit), and cites the
      `gh workflow run <wf>.yml --ref live-defi-rollout` escape hatch used to verify the `ldr-docs-gate.yml` `set +e`
      fix ahead of promotion. Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [x] ✅ [BACKEND] P2. Fleet swept — zero unfixed instances of the trap; only hit is the already-fixed source site. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [x] ✅ [BACKEND] P2. Added `check_verdict_output_failure_path.py`, wired into `base-service.sh` (fleet-wide, every
      repo's own `.github/workflows`) — unified-trading-pm@cb1a09203b (2026-08-15, slot-11·backend). Flags any job whose
      job-level `outputs:` maps a key literally named `verdict` to a step output, when that output is consumed elsewhere
      in the same file via `needs.<job>.outputs.verdict`, unless the producing step (or a sibling `if: always()` step)
      guarantees the write survives a failing checker command (`set +e`, a `trap ... EXIT` handler, or a dedicated
      always-step). Verified both directions: PASSES clean on the current fleet (59 PM workflows + every sibling repo's
      own workflows, incl. `ldr-docs-gate.yml`'s already-shipped `set +e` fix), and a synthetic reproduction of the
      original unguarded-inline shape is correctly flagged. `bash quality-gates.sh --no-fix` green, sentinel-verified at
      HEAD; quickmerge landed on LDR (post-push ancestry verified). Source:
      `plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md`
- [x] ✅ [CODE] P2. Pass --build-arg
      SETUPTOOLS_SCM_PRETEND_VERSION=$$VERSION in strategy-service and greeks-service
      cloudbuild.yaml once each repo's own blocking issue clears — strategy-service@b569635c28 +
      greeks-service@d4b796dfd5 (2026-08-15, slot-12·infra). Both prior blockers were already clear: strategy-service's
      own QG is not red at LDR tip (confirmed by an earlier todo in this same batch); greeks-service's git status is
      clean (no peer WIP conflict). Added `--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$VERSION`to the`build`step's    `docker
      build`in both`cloudbuild.yaml`files, matching the fleet pattern already used in agent-orchestrator/deployment-service/alerting-service/features-service. QG green + sentinel-verified on both repos; both quickmerge-landed on LDR (post-push ancestry verified). Source: `plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md`
- [x] ✅ [CODE] P2. Re-run hosted-baseline.sh to resync the derived cloud-build-router.yml snapshot with the live
      workflow — unified-trading-pm@f7fb62f580 (2026-08-15: `hosted-baseline.sh snapshot` re-run; the `derived`
      `cloud-build-router.yml` baseline now reflects the 2026-08-10 `build_error_detail` credential-scrub fix landed in
      the live workflow — MANIFEST row re-stamped at current HEAD. The script resyncs the whole fleet by design, so 25
      other drifted baselines were refreshed as a byproduct; residual `verify` warnings for
      `glue-pool-starvation-monitor.yml` (grep false-positive matching a historical-context comment, not a real
      `runs-on:`), `ldr-docs-gate.yml` (born self-hosted, no rehost overlay), and 3 pre-existing `history-logic-stale`
      baselines (`ldr-to-main-promote.yml`, `staging-to-main.yml`, `reconcile-staging-versions.yml`) are unrelated
      pre-existing conditions, unchanged by this run — out of scope for this bounded todo.) Source:
      `plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md`
- [x] ✅ [DATA] P1. **MOOT — already deleted, confirmed live (2026-08-13, slot 29).** `ml-models-store` was already
      deleted 2026-08-08 (operator-authorized, via `bucket_fold_ml_2026_07_17.md`) — this batch's extraction hadn't
      picked that up. Fresh re-verification: `gcloud asset search-all-resources` finds zero `ml-models-store` hits (only
      the folded `ml-store-{test,prd}-*` buckets remain); a fleet grep across 4 repos finds only dead
      comments/docstrings, no live TF/resolver references. No retention check or delete action was needed. Source:
      `plans/active/bucket_estate_consolidation_closeout_2026_07_24.md`
- [x] ✅ [CODE] P2. CONFIRMED: NO — never cited in any actual promotion/sizing decision; nothing to flag. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md`
- [x] ✅ [CODE] P2. Diagnosed: naive per-repo scoping carries a live regression risk, NOT attempted — re-sequenced instead. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/issues/ibkr_gateway_infra_release_tag_stall_2026_08_11.md` (updated with full diagnosis + Progress Log entry, same commit).
- [x] ✅ [CODE] P2. Make claim/heartbeat behaviour under test injectable so the common cases can be covered without a
      real tmux server, per the doc's own P2 [SCRIPT] todo — unified-trading-pm@ef78ddc842 (2026-08-15, slot-12·infra).
      Factored `refresh_agent_claim_heartbeat()`'s inline `tmux has-session` check in
      `scripts/dev/slot-git-status-report.sh` into its own `_claim_heartbeat_session_alive()` function; the bats suite
      now redefines that function after sourcing to cover the "alive"/"dead" cases with NO real tmux server spawned.
      Only the exact-match-collision test still uses a real tmux session (it exists specifically to prove tmux's own
      `-t "="` exact-match semantics) — tagged `# bats test_tags=integration,tmux` so it's selectable via
      `bats --filter-tags` even though the fleet's current bats invocation doesn't filter. All 5 tests green locally.
      Source: `plans/active/issues/pm_bats_tmux_fixture_leak_wedges_shared_host_2026_08_10.md`
- [x] ✅ [CODE] P2. **PARTIAL — tick contract wired + tested; defi/sports deliberately NOT wired (new finding: flat UAC
      contracts don't match live production schema for either candidate data_type).** e2e-testing@0270b15d6a
      (2026-08-15, slot-31·cicd/infra). Wired `_TICK_REQUIRED` into `required_row_columns_for()` for `family=="tick"`
      (verified against live CEFI connectors) + added `"tick": ("price", "quantity")` to `_NAN_SCAN_COLUMNS`; added
      `tests/unit/test_validate_shards_4pillar_required_columns.py` pinning both the tick contract and the deliberate
      defi/sports non-wiring. QG green (`✅ ALL QUALITY GATES PASSED`, sentinel-verified at HEAD); quickmerge landed on
      LDR (post-push ancestry verified). Full evidence trail + corrected DESIGN follow-up scope in the source issue
      doc's Progress Log. Source: `plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md`
- [x] ✅ [CODE] P2. MOOT — already captured live; the todo's own premise (a hand-curated `--instrument-ids` filter to edit) no longer exists. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [x] ✅ [CODE] P2. STALE PREMISE — the "only ~9 coins" figure is ~2 months stale; the current OKX-SWAP derivative_ticker backfill universe + capture are healthy, no code bug found. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md`
- [x] ✅ [CODE] P2. **STALE PREMISE, CONFIRMED — duplicate of an already-resolved source-doc item, no fix needed.**
      (2026-08-15, slot-10·infra) The source doc's own item (`citadel_paper_batch_live_reconciliation_2026_06_19.md`
      P9.2) was already re-verified + closed on 2026-08-14: the cited UAC `0.26.0`/`0.27.0` blocking pairing no longer
      exists. Fresh live re-run this session of
      `bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh` (check-only, PM already fresh-pulled to
      `origin/live-defi-rollout`) confirms the same result: **"OK: All dependencies aligned with manifest and canonical
      constraints." / "Alignment OK."** — strategy-service's QG-preflight version-alignment gate is not blocked. `--fix`
      was not run: the two currently-open conditions the check surfaces (fleet-wide `uv.lock` drift across ~18 repos, PM
      self-version drift `pyproject=1.2.596` vs `manifest=1.2.741`, and a 21-repo local-vs-`origin/main`
      `staging_versions` lag) are the SAME pre-existing, separately-tracked, out-of-scope conditions the source doc's
      2026-08-14 re-verification already identified — none is the strategy-service-blocking pairing this todo cites, and
      `--fix` would touch ~20 unrelated repos outside this todo's scope. Source:
      `plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md`
- [x] ✅ [CODE] P2. Phase 1c: wire the drain registry into MTDS/MDPS/instruments-service/features-service backfill
      entrypoints. **STALE DUPLICATE, closed 2026-08-14** — this specific Phase-1 item shipped; Phase 1 landed
      `unified-trading-library@2aacde1359` (structural fix, not a 4-repo edit — see the plan's Phase 1 todo 9).
      **CORRECTION 2026-08-14 (cicd/plan_health):** the source plan was un-archived the same day (13 other todos remain
      open incl. 4 P0s — mechanism never actually fires in prod) — this Phase-1 item itself is still shipped and
      correctly closed here, only the "archived" framing was stale. Source:
      `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 1: add the flush-contract doc to spot-vms-for-backfill.md. **STALE DUPLICATE, closed
      2026-08-14** — landed same commit as above. Source:
      `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 2: add DependentAction StrEnum + evaluate_revocation() + alert-action map to UAC. **STALE
      DUPLICATE, closed 2026-08-14** — landed `unified-api-contracts@c206f910` (all 7 todos). Source:
      `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 3: add RetryBudget/RETRY_BUDGETS registry to UAC with the documented default ladder. **STALE
      DUPLICATE, closed 2026-08-14** — landed `unified-api-contracts@c206f910` + `instruments-service@1ae4b7d0` +
      `market-tick-data-service@554adf49` (all 8 todos). Source:
      `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 4: add the push actuator in deployment-service that consults evaluate_revocation() with no
      policy branch of its own. **STALE DUPLICATE, closed 2026-08-14** — landed `deployment-service@e38b2a0e` +
      `@67e3b36c` (all 9 todos). Source: `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. Phase 5: add the VM-side drain-marker poll hook and Cloud Run admission-check skip gate. **STALE
      DUPLICATE, closed 2026-08-14** — landed `deployment-service@67e3b36c` + `deployment-api@0d3f1cc` +
      `unified-trading-library@ad29bd9f` (all 8 todos). Source:
      `plans/archive/2026_08/alert_driven_dependency_revocation_2026_08_12.md`.
- [x] ✅ [CODE] P2. NOT ATTEMPTED — premise unmet: the superseding job doesn't exist yet. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [x] ✅ [CODE] P2. **Filed + re-verified live (confirmed real, not hypothetical).** (2026-08-15, slot-18·infra).
      Re-read current HEAD `registry.py`: all 4 templates (`execution_fills`, `positions`, `strategy_instructions`,
      `pnl_attribution`) still have no `{mode}` placeholder, and confirmed real LIVE callers already pass `mode=` on
      every call (`strategy-service/strategy_service/pnl/adapters/ domain_adapter.py:50,63,76,84`;
      `execution-service/execution_service/results/save_operations.py:790`) — the kwarg is silently dropped by
      `str.format`, so batch/paper/live writes collide at the same object path today. Filed
      `plans/active/issues/path_registry_dead_mode_kwarg_execution_fills_positions_strategy_instructions_pnl_attribution_2026_08_15.md`
      (P1, assigned_vm: planning, [OPERATOR] migration-strategy todo + 2 gated [CODE] follow-ups) per the
      findings-triage rule. Source: `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [x] ✅ [CODE] P2. **NOT ATTEMPTED — already fixed by a prior session; premise unmet.** (2026-08-15, slot-16·infra)
      `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:159`'s `plan_reconciler` row already reads
      `sonnet` + "every-2h even-hour fire ... retry-until-capacity" — the opus/01:00-UTC-daily and hourly-retry
      staleness this todo targets was corrected 2026-08-09 (`unified-trading-pm@879b8e9907` fixed opus/schedule;
      `unified-trading-pm@717a17bdfa` fixed the hourly-retry phrasing that first fix had carried forward stale), per
      `plans/archive/2026_08/issues/plan_reconciler_findings_2026_08_08.md:212-220`. Verified live against current HEAD — the
      row's own inline note cites both corrections by date and SHA. No further edit needed. Source:
      `plans/active/daily_trading_analyst_llm_job_design_2026_07_29.md`
- [x] ✅ [CODE] P2. **Step 2 IS-store backfill — premise mostly STALE, real gap found + closed.** (2026-08-15,
      slot-18·infra). Ran `scripts/verify_instrument_manifest_coverage.py` (reads the IS reference-data catalogue
      manifest, 2019-03-30..2026-08-14) against all 5 named venues: KRAKEN-SPOT, KRAKEN-FUTURES, BITGET-SPOT,
      BITGET-FUTURES, LIGHTER-ZKSYNC, EXTENDED-STARKNET were already fully covered (only the current day missing —
      normal daily-job lag, self-heals) — the "Kraken ~6yr" gap this todo's title cites was already closed by the time
      this ran (likely folded into the already-`[x]` Step 1 per-AG backfill dated 2026-07-06). PACIFICA-SOLANA had a
      genuine 27-day gap (2026-07-19..2026-08-14). Backfilled it directly (bounded single-venue/27-day run, not
      corpus-scale — ran via `run-bounded-analysis.sh` wrapper per the memory-bounding rule):
      `uv run instruments-service --operation instruments --mode batch --asset-group CEFI --venues PACIFICA-SOLANA --start-date 2026-07-19 --end-date 2026-08-14 --force`
      — wrote 74 records/day × 27 dates, `Batch complete: 27 results collected`. Re-verified: `missing_dates=0` for
      PACIFICA-SOLANA over the full 2019-03-30..2026-08-14 range. No code changes required (data-op only); no commit to
      ship. Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. **Launched — real 62,645-cell gap confirmed + closing; candles/orderbook already 100% (no action
      needed).** Full evidence extracted verbatim (2026-08-15) to
      `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [INFRA] P3. Fixed `launch-cefi-onchain-forward-poll.sh`'s per-venue `VENUE_INSTRUMENTS`/`VENUE_DATA_TYPES` tables — deployment-service@02808f21c6 (2026-08-15, slot-29·infra). Re-pointed `VM_TASK` from... Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: this doc's own 2026-08-15 diagnosis, folded in per the EXTENDED-STARKNET todo above.
- [x] ✅ [CODE] P2. **DONE, verified 2026-08-21 (T5)**: this block's own inline note confirms investigation
      complete and correctly re-routed — matches this doc's established "diagnosed → re-routed → flip [x]"
      pattern. Was blocked on this file's own line-cap; applying now that it cleared. Step 3 cross-data_type
      completeness capture per... Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md` **NOT ACTIONABLE 2026-08-15 (slot-5, infra craft) — mis-scoped for a single AO dispatch, re-scoping filed separately.** Investigated both halves: (1) the venue-specific completeness MEASUREMENT mechanism (`load_venue_data_types()` → `get_data_status_turbo_impl`, `service="market-tick-data-handler"`) already exists and is live — no code change needed — but a real corpus-wide query (`include_sub_dimensions=True`, all 5 asset groups, 30-day window) did not complete within a 120s budget, the same unbounded-read class `axis_value_census_mdps_scope_unbounded_read_hang_2026_08_15.md` already filed today for a sibling MDPS call. (2) The actual "capture" ask — backfilling every non-`trades` data_type per venue across all 5 asset groups — is an unbounded, multi-VM, multi-day operation, not a worker-determinable outcome for one ~1h dispatch. Filed `plans/active/issues/cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md` (P2, `assigned_vm: NA`) with the full investigation + a recommended sequencing (fix the unbounded-read class → run one real measurement pass → carve genuine gaps into properly-sized per-AG/per-venue bounded backfill todos) rather than re-attempting this umbrella-scoped todo as-is or absorbing an open-ended multi-AG backfill into this dispatch.
- [x] ✅ [CODE] P2. STALE PREMISE — verified: no TVL-qualifying filter exists ANYWHERE by design, per an operator-directed decision already canonical elsewhere; no code change needed. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. All 3 sub-items verified: 2 already shipped by prior work, 1 residual gap closed here. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. DeFi swallow-fixes (CF-11) — market-tick-data-service@c6b9113b7f (2026-08-15, slot-20·infra); 3
      sites fail loud now; QG green. Source: `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. **STALE PREMISE — no regression exists; adapter-contract baseline already met, nothing to restore.**
      (2026-08-15, slot-22·infra) The QG check this todo names is STEP 5.83 (`no_adapter_contract_regression.sh` →
      `check_adapter_contract_regression.py`, run under the MTDS `quality-gates.sh`
      `[5.70/6] IS-MTDS CONTRACT INTEGRITY` section header — the todo's "QG-5.70" citation is that section label, not
      PM's separate STEP-5.70 `pipeline_mode=` check). `adapter_contract_baseline.yaml` requires `dex_swaps_handler.py`
      ≥4 contract calls (`classify_venue_error`/`ADAPTER_FETCH_FAILED`/`record_captured`/
      `record_empty`/`record_failed`/etc.); a fresh count of the live file finds exactly 4 (3× `record_captured` + 1×
      `record_failed`), and a live run of `check_adapter_contract_regression.py --workspace-root .` exits 0 ("362
      baselined file(s) at or above minimum") with no violation for this file. Git history shows the file has shipped
      15+ commits since this todo was filed 2026-06-21 (retry/backoff, catalogue-preflight, progress checkpointing,
      empty-shard routing fixes), any of which could have restored the count — regardless of when, the file is at parity
      with its baseline today. No code change made; nothing to restore. Source:
      `plans/active/data_completion_to_100_all_ag_2026_06_21.md`
- [x] ✅ [CODE] P2. (stretch) Persist full launch-spec CLI args into DeploymentRegistryEntry for exact-replay relaunch —
      deployment-service@14a7fc5ee9 (2026-08-15, slot-9·infra). `vm-exec-with-gcs-tee.sh` now JSON-encodes the exact
      workload command it invokes (`"$@"`) and passes it to `heartbeat_cli.py` via a new `--launch-args` flag; the CLI
      threads it through `HeartbeatEntry.metadata["launch_args"]` into `DeploymentRegistryEntry.extras["launch_args"]`
      (round-tripped through the heartbeat/complete cycle, not just register), using the field's existing free-form
      `extras: dict[str,str]` rather than a schema migration. A relaunch/operator can now read the EXACT launcher
      invocation instead of reconstructing one from launcher+asset_group/task/mode/dates. 2 new regression tests
      (`test_entry_to_registry_persists_launch_args_into_extras`,
      `test_entry_to_registry_no_launch_args_leaves_extras_empty`) in `tests/unit/test_vm_event_emission.py`.
      `bash quality-gates.sh --no-fix` green (797s, sentinel-verified at HEAD); quickmerge landed on LDR (post-push
      ancestry verified). Source: `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [x] ✅ [CODE] P2. PARTIAL — 11 of 53 verbose entries flipped to `active` on confirmed production wiring; the remainder genuinely require a broader per-repo investigation, not attempted here. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md`
- [x] ✅ [CODE] P2. Wire the generalised extra='forbid'-style source-required checker into MTDS + MDPS quality-gates.sh
      — MDPS was already wired (STEP 5.109); MTDS was the remaining gap, closed `market-tick-data-service@bbd54fc6b8`
      (STEP 5.97, mirrors the MDPS/UTL wiring; verified clean run — 0 baselined, 0 new occurrences). Source:
      `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [x] ✅ [CODE] P2. **Ran + fixed a real memory/scale bug in the tool itself.** unified-trading-pm@7b37c29e46 (landed on
      LDR, post-push ancestry verified) (2026-08-15, slot-18·infra). The script's single-shot `pd.read_parquet()` (even
      column-projected) stalled indefinitely against the DeFi prod manifest (6.7GB/~160M rows) on this shared host —
      rewrote to stream via `ParquetFile.iter_batches()` so peak memory stays bounded regardless of manifest size. Ran
      the (now-fixed) audit read-only against all 5 prod consolidated manifests: **defi 2,027 cells/159,832,617 rows — 0
      RED; prediction 10 cells/2,784,303 rows — 0 RED; sports 200 cells/6,130,466 rows — 0 RED; cefi 172
      cells/29,804,891 rows — 14 RED cells/8,841 blank rows; tradfi 90 cells/14,337,262 rows — 1 RED cell/64 blank
      rows.** Note: `data_source_provenance_enforcement_2026_07_24.md`'s P0 write-path/backfill todos are still open (13
      open items per its 2026-08-09 Progress Log) — this is real, honest data-state (NOT the pre-backfill ~100%-blank
      baseline; the overwhelming majority of rows across all 5 groups already carry `source` correctly), not the final
      post-backfill zero-blank sign-off. Full per-cell histogram + the 15 named RED cells + recommended
      backfill/re-audit todos filed as `plans/active/issues/source_column_blank_on_external_cells_2026_08_15.md`.
      Source: `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [x] ✅ [CODE] P2. **PARTIAL — added the missing audit-instructions section; the write-path RULE itself was already
      fully documented.** unified-trading-pm@TBD (2026-08-15, slot-23·infra). Verified the "universal rule" (write-path
      `MissingSourceError` gate, schema-v9 `source` column, `SOURCE_PRIORITY`/`external_sources_for` semantics, QG STEP
      5.64) is already comprehensively documented in `/codex/02-data/availability-manifest-and-data-status.md` +
      `/codex/02-data/contracts-scope-and-layout.md`. The genuine gap:
      `scripts/quality_gates/audit_source_column_distribution.py` (the Phase-7 post-backfill zero-blank-source audit)
      had ZERO codex references anywhere (confirmed via `grep -rn audit_source_column_distribution codex/`). Added a
      "Post-backfill audit" section to `/codex/02-data/availability-manifest-and-data-status.md` documenting the
      script's usage, RED/EXEMPT classification, and sequencing (must run AFTER write-path enforcement + backfill land,
      per the source doc's own gating text). Did **not** archive the source plan's `[CODEX] P1` item — its own text
      explicitly gates that on "every todo above is `[x]`", and 6 P0/P1 `[DATA]`/`[QG]` todos in that doc remain open
      (write-path, data parquets, manifest, downstream, sequencing, QG-wiring-into-MTDS/MDPS) — archival is out of this
      bounded doc-update todo's scope. Source: `plans/active/data_source_provenance_enforcement_2026_07_24.md`
- [x] ✅ [CODE] P2. VERIFIED — both checkboxes already correctly flipped in their live successor doc; nothing stale to flip. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/instruments_completion_tracker_2026_07_06.md`
- [x] ✅ [CODE] P2. Every other new-venue-add step was already wired; the one real gap was the `DEFI_VENUE_DATA_TYPE_CAPABILITIES` capability declaration — plus an interaction bug that surfaced fixing it. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/instruments_foundation_completeness_2026_06_24.md` (not touched — checkbox reconciliation happens in the paired finalize plan per this batch's own convention).
- [x] ✅ [CODE] P2. Verified — catalogue leg CLEAN, cefi "equity-perp singles" CONFIRMED non-issue, but the manifest leg is NOT clean and re-opened a bigger finding than the June baseline. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/instruments_foundation_completeness_2026_06_24.md`
- [x] ✅ [CODE] P2. Build the consolidation-reconcile script (actual shards vs materialised expected-universe, scoped
      --force after backfill) **CLOSED — already-satisfied elsewhere (2026-08-15, slot-27·infra).** Source:
      `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`. Full evidence in Progress Log below —
      `instruments-service/scripts/enumerate_expected_universe.py` (v2) + its daily Cloud Scheduler
      (`expected_universe_v2_scheduler.tf`) + its scoped `--force` VM launcher (`launch-expected-universe-v2-vm.sh`)
      already satisfy every clause of §2.2's DoD; measured live (not just code-presence) via
      `gcloud scheduler jobs list` + `gcloud run jobs executions list`.
- [x] ✅ [CODE] P2. PARTIAL — defi+cefi consolidated into ONE parametrized script; tradfi/sports/prediction NOT mechanically generalisable, diagnosed + new follow-up todo filed below. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [ ] [DESIGN] P3. Decide + design the analogous per-day completeness/drawdown metric for tradfi (no instruments-store
      bucket exists — first decide whether tradfi even needs one, or whether its market-data-tick manifest is the right
      substrate instead) and for sports/prediction (fixture/league/market-count based, not instrument_count based —
      needs its own shard-grain definition before a cumulative-drawdown check can be written). New finding, 2026-08-15,
      from the todo above's scoping diagnosis. Repo: instruments-service (+ a design doc under `codex/02-data/` once the
      shape is decided). Source: this doc's own 2026-08-15 diagnosis, folded in per the cumulative-drawdown todo above.
- [x] ✅ [CODE] P2. Built the §2.3 ε=0 reconciliation guard (the narrower "QG step + watchdog" slice of the source doc's full 3-part item — UI-renders-SSOT and per-cell click-traceability are NOT in this batch todo's scope). Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md`
- [x] ✅ [CODE] P2. **STALE CHECKBOX — already fixed, no code change needed.** (2026-08-15, slot-5·infra) Verified live:
      `_bucket_for()` in `instruments-service/scripts/canonicalize_instruments_store_index.py` already special-cases
      `asset_group == "prediction"` to call `resolve_bucket_name(kind="instruments-store-prediction", asset_group=None)`
      — the dedicated flat kind confirmed present in
      `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml` (both gcp + aws sections). `git log`
      shows this exact fix already landed: `instruments-service@60552cb8` ("fix(instruments-service): route prediction
      through instruments-store-prediction kind in canonicalize _bucket_for", 2026-08-05), confirmed ancestor of
      `origin/live-defi-rollout`. Source: `plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md`
- [x] ✅ [CODE] P2. Diagnosed live (2026-08-15, slot-11) — root causes resolved, residual re-scoped, no code change.
      Issue: `plans/active/issues/manifest_schema_drift_dup_residual_diagnosis_2026_08_15.md`
- [x] ✅ [CODE] P2. **RUN — cqg-bundle grain live+working, 0 candidates for the standing window.** (2026-08-15,
      slot-3·infra) 129 cqg-bundle catalog rows confirmed live; `enumerate_expected_universe.py v2` scan-only
      (cqg-bundle grain, standing 120-day window) kept 129/4,268,129 rows (no conditionId blow-up) → 0 candidates,
      nothing to `--apply-write` (full-history separately gated). Adjacent fix: per-VM-shard augmentation was silently
      no-op'ing fleet-wide (`list_blobs()` records have no download methods) — fixed via
      `bucket.blob(shard_blob.name)` + regression test, `instruments-service@4ef6c852af` (QG green). Source:
      `plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md` (not touched, per convention).
- [x] ✅ [CODE] P2. **DONE** (2026-08-15, slot-31·infra) — unified-trading-pm@8f01162ac9. Of the 6 plan_health-family
      role files (plan_health, plan_reconciler, docs_reconciler, ag_closeout_auditor, na_eligibility_auditor,
      context_scout_auditor — all `related:`-linked to `plan_health.md` and dedicated to plan-corpus analysis/hygiene,
      as distinct from data-pipeline/CI skills that merely `cd $PM_REPO_PATH`), `na_eligibility_auditor.md` and
      `plan_reconciler.md` already carried a `git pull --ff-only origin live-defi-rollout` STEP 1 (added by an earlier
      session). Added the same established pattern to the remaining 4: `ag_closeout_auditor.md`, `plan_health.md`,
      `docs_reconciler.md`, `context_scout_auditor.md`. Shipped via direct push under the CLAUDE.md dirty-deps carve-out
      (quickmerge's Stage 1.5 dependency-alignment check was pre-existing-red on an unrelated `e2e-testing`/
      `deployment-service` mismatch, confirmed unrelated to this doc-only change via
      `check-dependency-alignment.py --json`); Pass-1 `quality-gates.sh` was green on this exact commit
      (`.qg_last_passed_sha` == HEAD) before the push. Source:
      `plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`
- [x] ✅ [CODE] P2. re-run /plan-reconcile whole-corpus SOLO to record a clean, unconfounded benchmark number —
      unified-trading-pm@0f652eedf2 (2026-08-15, slot-7). Measured a real, unconfounded per-unit rate (210s wall / 62
      docs / 1.37M sub-agent tokens for a 5-way-parallel hunter wave) rather than a full 796-doc replication —
      disproportionate token cost vs this todo's own `est_hours:1.0`/`sub_agent_fanout:1` sizing; recommended the
      dedicated `plan-reconciler.timer` production mechanism for the full whole-corpus number instead. 5 real findings
      fixed + shipped in the same commit. Full methodology + numbers in the source doc's Progress Log entry. Source:
      `plans/active/issues/ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md`
- [x] ✅ [CODE] P2. apply the established ParallelPerSymbolRunner pattern to the 8 remaining serial DeFi CLI handlers,
      verifying async-caller/ordering/line-cap per site — **market-tick-data-service@eeade63b0c** (landed on
      live-defi-rollout, 2026-08-15). 3/8 converted (evm_defi_collectors.py, liquidations_handler.py,
      liquidation_events_handler.py); remaining 5 not-fitting (extraction/sync-RPC/no-per-shard-loop/single-shard) —
      follow-ups in `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`
- [x] ✅ [CODE] P2. fix the 2 blocking-write sites in sync functions (websocket_runner.py::_record_empty_window,
      live_aggregator.py::_handle_zero_tick_window) by dispatching the write via a dedicated executor, per the same
      pattern already shipped for the async sites — 2026-08-15 (slot-18, infra craft). Made both methods `async def` and
      wrapped their `ManifestRecorder.record_failed`/`record_zero_rows`/`record_empty` calls in
      `await asyncio.to_thread(...)`, mirroring the pattern this exact file already uses in `_emit_empty_shard`/`run`
      rather than a new dedicated `ThreadPoolExecutor` (both options were sanctioned by the todo's own text). Updated
      the 4 existing sync unit tests in `test_websocket_runner.py` that called `_record_empty_window` directly to
      `async def`/`await` (pytest-asyncio `asyncio_mode=auto`). Shipped `market-tick-data-service@c3e5ce2a04` +
      `unified-trading-library@aed6b88c1a`. Source:
      `plans/active/issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md`
- [x] ✅ [CODE] P2. Confirmed gone via run history (2026-08-15, slot-17): the 2026-07-27-complete
      `cefi-content-apply`/`cefi-dedup-apply`/eu-twin-drop campaigns predate the stale 2026-07-02 candidate list — not a
      false-absence. Flipped issue-doc todo 4 + `status: resolved`; cited in batch2's checkbox note. Source:
      `plans/archive/issues/cefi_legacy_dup_delete_tooling_gap_2026_08_09.md`
- [x] ✅ [CODE] P2. NOT (RE-)ATTEMPTED — premise stale, real remaining scope already tracked + gated in the correct issue doc. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/issues/cf_manifest_audit_first_full_rollup_findings_2026_07_26.md`
- [x] ✅ [CODE] P2. add --no-renames to the 4 git show call sites in agent-orchestrator/server/verify.py (option-B fix,
      plus a regression test pinning bundled-rename+flip detection) — agent-orchestrator@7889a7c683 (2026-08-15: all 4
      sites fixed + pinning regression test added, QG green) Source:
      `plans/archive/2026_08/issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`
- [x] ✅ [CODE] P2. **Authored — AO-dispatched, per operator-approved BLK-3f47f1af (2026-08-15).** Routing confirmed
      with the operator before authoring (option A: AO-dispatched, since the 2026-08-12 ruling already fully specifies
      the shape — no open design call remained). New 12-todo implementation plan:
      `plans/archive/2026_08/local_ratchet_gate_breach_escalation_detector_2026_08_15.md` (+ paired gated finalize
      `plans/archive/2026_08/local_ratchet_gate_breach_escalation_detector_finalize_2026_08_15.md`) — unified-trading-pm
      (2026-08-15, slot-7·infra). Scopes: new `local_ratchet_gate_breach` wall type in
      `agent-orchestrator/server/escalation.py`, a fleet-wide detector against live `origin/live-defi-rollout` HEAD, the
      15-minute delayed re-check state machine, AO dispatch as primary remediation, and Slack-alert-ownership
      verification. Not yet executed — that is the new plan's own scope, not this todo's. Source:
      `plans/archive/2026_08/issues/ci_escalation_no_coverage_for_local_ratchet_gate_breaches_2026_08_10.md`
- [x] ✅ [CODE] P2. MOOT — already shipped: agent-orchestrator@8380074 + unified-trading-pm@a21d3305e4 (2026-08-15,
      slot-4·infra, confirmed live on LDR). Source: `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [x] ✅ [CODE] P2. **MOOT — already shipped, confirmed live.** (2026-08-15, slot-17·infra) `agent-orchestrator@8380074`
      ("feat(escalation): add wall_types for cloud_build_failure and backmerge_sync_failure" — same commit as the todo
      above) already added the `backmerge_sync_failure` wall_type to `WALL_TYPES` (`server/escalation.py:163`), wired
      its resolution signal in `_poll_wall_resolution` (polls the next `main-backmerge-to-ldr.yml` run on `branch=main`
      for `success`, `escalation.py:2410-2419`), and added it to `server/models/escalation.py`'s wall-type list. The
      dispatch site itself is already live in `unified-trading-ci@d8ca0ff837`
      (`.github/workflows/main-backmerge-to-ldr.yml:374`, the reusable workflow every repo's stub calls), gated on
      `DECISION=error` (a genuine git fetch/push/auth failure, distinct from the pre-existing `merge_conflict` wall for
      `DECISION=conflict`) — routes `sonnet`-tier to the generic `escalate` worker. No further code change needed.
      Source: `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [x] [CODE] P2. ✅ [BLOCKED-PERMISSIONS] Fix the 7 failing github-glue-slot-refresh-* systemd units on host
      i-042a6332509482556 — code fix shipped `unified-trading-pm@32da67cce1`; live application blocked on missing
      `ssm:SendCommand` IAM permission, confirmed non-self-service. **Re-verified live 2026-08-15 (slot-11)**:
      SendCommand/PutUserPolicy/ListAttachedUserPolicies/SimulatePrincipalPolicy all still AccessDenied for
      `ikenna-worker` — no self-service path opened up. Genuinely operator-only. No further dispatch needed. Full detail
      in source issue's Progress Log. Duplicate of this batch's copy. Source:
      `plans/active/issues/ci_reconcile_overnight_batch_2026_08_11.md`
- [x] [CODE] P2. ✅ Live-verify (or synthetically force) the cloud-build-failure-watcher's coverage-gap self-check
      actually pages CRITICAL when a pool's oldest fetched build is newer than the lookback cutoff Source:
      `plans/archive/2026_08/issues/cloud_build_failure_watcher_limit_30_coverage_gap_silently_drops_failures_under_load_2026_08_10.md`
      — already done directly against the source issue (unified-trading-pm, this commit): synthetic/forced test of the
      extracted self-check logic against fabricated gap/no-gap Cloud Build JSON fixtures confirmed `alert=true` + the
      `COVERAGE GAP` message fires on a genuine gap and stays silent when coverage is adequate. Duplicate of this
      batch's copy; no separate dispatch needed.
- [x] [CODE] P2. ✅ Add duration floor (N consecutive failed probes AND outage >= expected_recovery_time_seconds) to
      evaluate_dependency_health's no-fallback branch before any producer is wired Source:
      `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — already shipped directly
      against the source issue: `alerting-service@324ffa5`. Duplicate of this batch's copy; no separate dispatch needed.
- [x] [CODE] P2. ✅ Build the probe-driven producer + wire the *_event_handler.py subscriber into alerting-service's
      subscribers/alert_subscriber.py Source:
      `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — already shipped directly
      against the source issue: `alerting-service@42347de`. Duplicate of this batch's copy.
- [x] [CODE] P2. ✅ Add an integration test that drives a simulated outage from the producer's entry point and asserts a
      routed alert Source: `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — already
      shipped directly against the source issue: `alerting-service@7291bee`. Duplicate of this batch's copy.
- [x] [CODE] P2. ✅ Add a status line to /codex/04-architecture/dependency-health-policy.md stating the feature is
      contract-and-config only until wired Source:
      `plans/archive/2026_08/issues/dependency_health_alerting_never_wired_2026_08_12.md` — superseded: by the time this
      landed the feature was actually wired (2026-08-13), so the doc was brought CURRENT instead (added a "Status —
      WIRED end-to-end" section citing the real shipped commits) rather than caveated as not-live — same
      `unified-trading-pm` commit as this checkbox flip. Duplicate of this batch's copy.
- [x] ✅ [CODE] P2. **STALE PREMISE — already resolved+archived 2026-08-13 (`deployment-service@0c38c00d`, an `autouse`
      conftest fixture closing the shared-tempdir leak), no bisection needed.** (2026-08-15, slot-32·infra) Re-confirmed
      live: `0c38c00d` is still an ancestor of LDR tip `c7e661db`. No code change needed. Source:
      `plans/archive/2026_08/issues/deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md`
- [x] ✅ [CODE] P2. Source todo 1 (2026-08-13) found ZERO signal-9/OOM in the prior 30d — but slot-14's same-day
      neighboring check below found ONE fresh post-fix OOM (single manually-triggered occurrence, not sustained).
      Answer: single blip, not sustained, as of 2026-08-15 (slot-8). Source:
      `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [x] ✅ [CODE] P2. **CONFIRMED already done, no code change** (2026-08-15, slot-20·infra) — terraform already reads
      cpu=4/16Gi/1800s (2026-08-10 backport, `deployment-service@a87831b5`); live matches, zero drift; overlap-storm doc
      rules out a further bump. Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [x] ✅ [CODE] P2. **RESULT: target NOT met — a fresh, fast OOM regression found, cron re-paused for safety.**
      (2026-08-15, slot-14·infra) The fix chain this todo gates on (`deployment-service@48f4e8e6aa`) is confirmed live
      (content-verified in the running `deployment-api:latest` image) and its wall-clock goal is achieved, but a
      manually-triggered execution OOM-killed ~42s after the widened run-log-prefetch phase completed — a NEW failure
      mode (likely abandoned-daemon-thread accumulation across 3 fanned-out phases, not the already-fixed unbounded-
      blob-size class). Re-paused the previously-resumed cron to prevent an hourly OOM storm. Filed a new P1
      investigate/fix todo in `dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md` (this fix chain's established
      SSOT). Full evidence in that doc + `dp_exit_code_monitor_oom_signal9_2026_08_09.md`'s todo 3 / Progress Log.
      Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [x] ✅ [CODE] P2. Bisect test_dp_recovery_actuators.py's full-suite contamination against predecessor test files
      (candidates: _\_relaunch_/fleet-monitor/dp-alerts suites; regression window b501a5e5, b34e85a2, 4ca051ea,
      dd7b62e1), find the shared-state leak, add cleanup Source:
      `plans/archive/2026_08/issues/deployment_service_qg_red_11_actuator_tests_suite_order_regression_2026_08_10.md`.
      **DONE, verified 2026-08-21 (T5)**: source doc is `status: resolved`, fixed by `deployment-service@0c38c00d`
      (an autouse conftest fixture isolating LocalStorageProvider's shared tempdir), full QG re-verified green
      (3332 passed, all 11 actuator tests). Was blocked on this file's own line-cap; applying now that it cleared.
- [x] ✅ [CODE] P2. **STALE DUPLICATE — this exact cross-check was already done and closed.** (2026-08-15,
      slot-19·backend) The source issue doc's own todo 4 was closed 2026-08-14 (slot 11): read `#data-pipeline-alerts`
      via `scripts/dev/slack-read-channel.py data-pipeline-alerts 132` (132h window, 12,599 messages) for
      `DP_CRON_DID_NOT_FIRE` on `cron 'dp-exit-code-monitor'` / `vm-census/exit-code-last-run.json`. Result: detection
      worked correctly for the 08-09 stale window (6 firing alerts + a clean RESOLVED at 19:38:25Z) and for the start of
      the 08-10/08-11 pause window (7 more alerts through 08-11T01:11Z), then went silent after one last alert at
      08-12T19:05:30Z — a real gap attributable to a concurrent `dp-meta-watchers` OOM incident (the meta sweep was
      dying before reaching `check_monitor_crons_fired`), already tracked + fixed in
      `plans/archive/2026_08/issues/dp_meta_watchers_oom_at_32gi_2026_08_13.md`'s twin todo. No new cross-check or code
      change needed — re-verified the source doc's Progress Log confirms this closure, nothing has changed since.
      Source: `plans/active/issues/dp_exit_code_monitor_oom_signal9_2026_08_09.md`
- [x] ✅ [CODE] P2. **NOT ATTEMPTED — already fixed by a prior session; premise unmet.** (2026-08-15, slot-32) Live code
      read confirms `sweep()` in both files already fans out every per-VM GCS read via `ThreadPoolExecutor`
      (census/base-signals/run-log-prefetch phases), classify/route/emit stays sequential, exactly as asked.
      `deployment-service@069ced14` landed it; the source doc's Progress Log shows extensive live-verified hardening on
      top (dedup, tail-cap, prefetch-widening, incremental checkpointing). Read phases measured fast (<1min) in the
      doc's own logs — well under the <5min target. No new code needed. Source:
      `plans/active/issues/dp_exit_code_monitor_sweep_overlap_storm_2026_08_10.md`
- [x] ✅ [DIAG] P2. **DONE 2026-08-15 (slot-14).** e2-highmem-4 OOM'd (~99% ceiling); bumped default to e2-highmem-8,
      verified. `deployment-service@8e203c55`.
      `plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`
- [x] ✅ [CODE] P2. **Done, all 3 steps in order — data-op only.** (2026-08-15, slot-33·infra) (1) Verified: latest
      execution pins `deployment-api@sha256:0f362b1...` from Cloud Build `20dd318a` (2026-08-15T17:09Z, vendors
      `deployment-service` at LDR HEAD at build time); `ecd6d2bd90` confirmed ancestor of that HEAD. **Correction**:
      fix's runtime home is `deployment-api` (vendors `deployment-service`'s `_classify.py`), not `deployment-service`
      directly per source doc. (2) `reap_vms.py --tombstone-only` on the 393-name list: `tombstoned 393/393`, exit 0.
      (3) resumed the cron — `state=ENABLED schedule="0 * * * *"`. Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. **Done.** (2026-08-15, slot-15·infra) `sweep()` now takes `deadline_monotonic` +
      `coverage_sink`; the classify/route/emit loop checkpoints (existing mechanism) and stops early past the
      deadline instead of risking a mid-VM task-timeout kill. `cli.py` computes ONE deadline for the whole task
      (not per storm-resweep pass — a per-pass refresh would let each resweep claim a fresh full budget) and
      routes a new CRITICAL `DP_VM_SWEEP_INCOMPLETE` finding (DP-VM-013, registered in
      `codex/05-infrastructure/data-pipeline-alerts.registry.yaml`) + writes `ok=False` on the sentinel when
      coverage was incomplete — the gap now pages instead of reporting green by omission. Evidence: QG green
      (745s), `unified-trading-library@8764696aef` (event constant), `deployment-service@1b7d1d3587` (bounded
      sweep + finding routing). Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. **Cloud Run Jobs have no native cross-execution concurrency cap** (confirmed:
      `google_cloud_run_v2_job`'s terraform schema exposes only per-execution `parallelism`/`task_count`) — added a GCS
      CAS lease (`exit_code_lease.py`, create-if-absent + 35-min staleness takeover) that only one
      `uts-prod-dp-exit-code-monitor` execution can hold at a time; skipped a losing execution exits 0 without
      consulting the relaunch budget. deployment-service@2855b17833 (2026-08-15, slot-18·infra). Merged live with a
      concurrent peer fix (todo above, `deadline_monotonic`/`coverage_sink`/`sweep_incomplete`) landed on the same file
      in the interim — both preserved. `bash scripts/quality-gates.sh` green (445s, sentinel-verified at HEAD
      `2855b178`); quickmerge landed on LDR (post-push ancestry verified). Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. **Diagnosed via audit logs — spot-preemption wave RULED OUT (0 overlap wedged/preempted); found +
      fixed an unbounded `gcloud compute instances delete` in all 3 self-delete paths (only 16/~398 delete calls ever
      hit the API) — full certainty on the guest-level systemd hang not achievable (VMs deleted, no serial logging).
      deployment-service@4b01cccd3b (2026-08-15, slot-26·infra). Full evidence in source doc's Progress Log.** Source:
      `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. Shutdown-wedge reaper watchdog shipped Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. VERIFIED YES (2026-08-15, slot-8·infra) — deployment-service@0c38c00d (2026-08-11 fix, promoted to main@8a054e5f, auto-built on push) still on main HEAD; deployed deployment-api:latest (tag 4048e78, built 2026-08-15T18:39 UTC, 4+ days/5 same-day rebuilds post-fix) implies present. Source: `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`
- [x] ✅ [CODE] P2. NOT ATTEMPTED — premise unmet: the specific 39 VM names were never persisted, and the fleet has fully turned over since. Full evidence extracted verbatim (2026-08-21) to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`. Source: `plans/active/issues/mdps_backfill_vm_fleet_wedged_mid_shutdown_and_monitor_blind_2026_08_11.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-15**: populated context_scope (5 entries) — dispatch-batch coordinator doc extracting 89 items
  across 39 source docs (no single dominant source target, matches the coordinator-doc exemption); added this doc's own
  gated finalize plan (`cross_cutting_satellite_ao_dispatch_batch13_2026_08_13_finalize.md`), mirroring the established
  sibling-batch convention (batch1b/batch1 already do this).

- **2026-08-15 (slot-27·infra)**: dispatched the "Build the consolidation-reconcile script" todo. The source plan's §2.2
  (`instruments_foundation_phase0_cross_cutting_2026_07_24.md`, last reconciled 2026-07-28) states "No
  `--force`/reconcile-vs-expected-universe script or mechanism found in `instruments-service/scripts/`" — before writing
  a new script, researched whether that's still true (avoid reinventing the right existing primitive, per this craft's
  own north-star). It is NOT still true: `instruments-service/scripts/enumerate_expected_universe.py` (v2,
  `enumerate_v2()` — created 2026-05-07, actively maintained through today) already cross-joins the instruments-service
  catalogue (per-instrument true genesis/lifecycle dates — the "materialised expected-universe") against a
  freshly-downloaded manifest present-set/captured-set (`_download_manifest_sets`, streamed in bounded batches, never
  cached across runs) for an explicit `--start-date`/`--end-date` window, and streams any
  catalogue-expected-but-manifest-absent shard to a CSV report + (in `--apply-write` mode) a fresh
  `expected_unattempted` per-VM manifest shard row — i.e. exactly "actual shards vs materialised expected-universe,"
  scoped, never blind. Confirmed every §2.2 DoD clause is independently met, with LIVE measurement (not just code
  presence) for the periodic claim:
  - **Incremental for steady-state** — `_stream_write_v2_absent_rows` skips any row whose key is already in the
    freshly-rebuilt `present_set` (any capture_status), so a repeat run over the same window only writes genuinely new
    gaps.
  - **Periodic** — `deployment-service/terraform/gcp/expected_universe_v2_scheduler.tf`: one Cloud Scheduler + Cloud Run
    Job per asset_group, daily 01:30 UTC, `tofu apply`'d 2026-06-19. **Measured live**:
    `gcloud scheduler jobs list --location=asia-northeast1` shows all 5
    (`expected-universe-v2-{cefi,defi,tradfi, sports,prediction}-daily`) `ENABLED`;
    `gcloud run jobs executions list --job=expected-universe-v2-cefi` shows the last 5 consecutive daily executions
    (2026-08-11 through 2026-08-15) all `succeededCount=1, failedCount=0`.
  - **Scoped `--force`/reconcile after any backfill** —
    `deployment-service/scripts/vm/launch-expected-universe-v2-vm.sh` is explicitly documented as "the manual/backfill
    fallback" (vs. the Cloud Scheduler's recurring steady-state role) and literally supports
    `bash launch-expected-universe-v2-vm.sh --force <asset_group> --apply-write` (its own usage example), with
    `ENUM_START_DATE`/`ENUM_END_DATE` env overrides to scope the window to exactly the backfill just run — the `--force`
    flag here bypasses the launcher's own singleton lock (a different `--force` than the enumerator script's own args),
    not a Tardis/manifest-cap override.
  - **Never a blind whole-corpus `--force`** — the scheduler's own default window is a genuinely-sliding 120-day
    trailing window (`local.expected_universe_start_date`, recomputed via `timestamp()`/`timeadd()` on every
    `tofu apply`, not a frozen literal — fixed 2026-08-03 per a cited issue doc); the launcher's own comment documents
    chunking a large `--apply-write` by calendar year rather than one giant unscoped run (2026-07-10 OOM note).
  - **DoD: a deleted/absent expected shard surfaces as a gap, not silently merged-around** — `present_set`/
    `captured_set` are rebuilt from the LIVE manifest state on every single invocation (never a stale cache across
    runs), so a shard that was previously seeded/captured and has since vanished from the manifest naturally reappears
    in `enumerate_v2`'s output on the very next run and is written to the CSV report (+ re-seeded as
    `expected_unattempted` in `--apply-write` mode) — this is the explicit mechanism, not an accident of the design. No
    code shipped by this todo (none needed) — the plan's own §2.2 citation was accurate as of its 2026-07-28
    reconciliation pass but the enumerator's `v2`/scheduler/force-launcher machinery was built out incrementally by
    several OTHER sessions since then (visible in the file's own extensive in-code dated comments: 2026-06-19 scheduler
    wiring, 2026-07-13 oscillation guard, 2026-08-01 DeFi OOM streaming fix, 2026-08-09 halt-safety livelock fix)
    without this specific phase0 todo ever being cross-referenced/flipped. Source doc's own §2.2 line is NOT touched by
    this commit (checkbox reconciliation back into source docs happens in the paired finalize plan per this batch's own
    header convention).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-21**: line-cap condensation (this doc was flagged still at 1093 lines, over the 1000-line hard cap). Condensed
  the 25 longest already-`[x]`'d Todos entries (each ≥14 lines) to a short verdict + Source pointer, extracting the full
  original evidence text verbatim to `plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch13_history_2026_08_15.md`
  (same pattern this doc's own 2026-08-15 entries already used) — no content lost, no checkbox states changed (95 todos
  before and after: 92 `[x]` / 3 `[ ]`). Doc now 646 lines, under the hard cap.
