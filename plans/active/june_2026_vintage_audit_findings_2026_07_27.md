---
doc_type: plan
title: June-2026 vintage audit findings — bugs, archives, migrations, rehomes, operator-gate queue
summary:
  Durable capture of the 2026-07-27 /plan-vintage-audit run over all 81 June-2026-created plans/issues (12-group
  Workflow classification). 2 cross-plan false-citation bugs, 11 archivable-now docs, 15
  migrate-to-July-plan-then-archive docs, 10 partially-done-rehome-remainder docs, 2 unclear docs, and a reference queue
  of the 42 operator-gated items for an interactive operator session. Nothing here has been executed yet except where
  noted.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, archival, migration, vintage-audit, operator-gated]
related: []
created: 2026-07-27
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2
last_updated: 2026-07-27
supersedes: []
superseded_by:
locked_by:
locked_since:
depends_on:
source:
  [
    cursor-configs/skills/plan-vintage-audit/SKILL.md,
    the 2026-07-27 /plan-vintage-audit workflow run over the June-2026 corpus,
  ]
assigned_role: project_management
drift_direction: none
---

# June-2026 vintage audit findings

Operator directive (2026-07-27): fix the 2 bugs below, execute the 11 archives + 15 migrations + 10 rehomes, THEN hold
an interactive session to work through the 42 operator-gated items (§5) one by one — operator asked "what do you need
from me" for each. The 2 unclear docs (§4) need a decision on whether to investigate further or archive as-is.

Execute with sub-agents (to conserve main-session context) — **operator said do not launch execution yet**; this doc is
the durable handoff so a fresh session can pick this up cold. Follow `/plan-vintage-audit`'s Phase 2 archival mechanics
exactly (dated archive folder, exact-successor banner citing commit SHAs, fix every corpus referrer including
codex/00-SSOT-INDEX.md, `[unlock-plan]` only on explicit per-doc operator authorization, `git rm` is blocked for
autonomous workers — relocate via `git mv`, ask the operator for true deletions).

---

## §1 — Fix first (2 cross-plan false-citation bugs, P1)

- [ ] [DATA] P1. **Fix false "0 open todos/closed" citation for
      `plans/active/issues/vm_backfill_data_correctness_findings_2026_06_29.md`** across FOUR AG closeout plans
      simultaneously (`tradfi_consolidated_closeout_2026_07_18.md`, `defi_consolidated_closeout_2026_07_18.md`,
      `cefi_consolidated_closeout_2026_07_18.md`, `sports_consolidated_closeout_2026_07_19.md` — verify exact filenames
      before editing). The doc has 4 genuinely open findings with NO checkboxes (that's why checkbox-counting indexes
      miscounted it closed): F4 (Curve subgraph dead, BLOCKED-CREDENTIALS), F5 (bybit dated-futures timeouts), F6 (DeFi
      lending-indices ~39% zero-row), F7 (TradFi capture un-gated by `is_mvp`, inventory-only). F1-F3 are done (commits
      a4dfa6b, 7da5f6ad, 75c8f148). Action: rehome F4+F6 as real `- [ ]` todos in the defi closeout, F5 into the cefi
      closeout, F7 into the tradfi closeout; correct all 4 false "closed" citations to point at the real open items;
      archive the F1-F3 portion of the source doc once F4-F7 have a home.
- [ ] [DATA] P1. **Fix stale "Plan 3 never authored" claim from
      `plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md`** that propagated unverified into
      `plans/active/cross_cutting_consolidated_closeout_2026_07_25.md` Track 10 and
      `plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` — Plan 3 actually shipped 2026-06-30
      (`unified-api-contracts@6bcff215`). Action: correct both citations; re-check whether Plans 2/6/9 (referenced by
      the same tracker) are actually unblocked as a result of Plan 3 having shipped — that dependency chain was never
      re-verified.

---

## §2 — Archive now (11 docs, fully-done or superseded, strict evidence bar already met)

- [ ] [PLAN] P2. `plans/active/defi_onchain_derivable_values_and_date_drift_2026_06_20.md` — 14/14 done, final Pyth
      Hermes/jitoSOL residual shipped (unified-api-contracts@4a29261e). A gated finalize plan already exists
      (`…_finalize_2026_07_27.md`, draft) — flip it active, execute reconciliation, then the 6-step archival ritual.
- [ ] [PLAN] P2. `plans/active/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md` — all 6 BUGs [x] with
      shipped SHAs (UTL@b587b91b/ed622af8, UAC@fd5bcfa/7fade10, execution-service@38c7e06f, strategy-service@b91d3e1f,
      features-service@16be6c0f). Sole remaining line already migrated 2026-06-21 into
      `perp_funding_data_semantics_and_cadence_2026_06_16.md` (tracked separately in §3). Archive via standard ritual.
- [ ] [PLAN] P2. `plans/active/issues/phantom_captures_defi_2026_06_28.md` — "Apply reconciliation" checkbox unflipped
      despite `plans/archive/mvp_backfill_defi_onchain_v10_operational_log_2026_07_24.md:754-762` recording APPLY
      COMPLETE (exit_code=0, 219,632 phantoms flipped, 2026-06-28T21:35:53Z), independently confirmed by
      `mvp_backfill_defi_onchain_v10_2026_06_27.md`'s banner. Flip citing evidence, archive.
- [ ] [PLAN] P2. `plans/active/issues/sports_golden_window_attempted_failed_remediation_2026_06_24.md` — 3 stale
      unchecked items all confirmed done (understat 404 scoping, `candidate_parquet_paths` gap, odds-api backfill via
      archived `sports_p1_golden_window_mtds_odds_2026_06_27.md` Todo 2). Sole remainder (3-way understat split) is a
      dormant contingency — carry forward as a footnote in `/codex/02-data/sports-data-source-coverage-matrix.md` or the
      sports closeout doc, then archive.
- [ ] [PLAN] P2. `plans/active/issues/understat_bulk_download_backfill_2026_06_29.md` — all 11/11 §8 done; 2026-07-26
      closure note + independent re-verification (605,368-row corpus, 0
      attempted_failed/expected_unattempted/duplicate); final gap shipped same session (deployment-api@b04c082).
      Archive, flip status open→resolved citing the closure note + SHA + archived
      `understat_local_backfill_completion_2026_07_06.md`.
- [ ] [PLAN] P2. `plans/active/issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md` — all 4 Gap items
      live-verified via gcloud/GCS (heartbeat sentinel writing, Cloud Logging showing app logs, alerting-service@ceed827
      confirmed ancestor of main + redeployed), independently confirmed by
      `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`. Flip all 4, archive; note Gap2's literal
      JSON-severity-formatter ask as an optional minor residual.
- [ ] [PLAN] P2. `plans/active/issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md` — 4/5 [x] (2 dated
      2026-07-27, build 2ea305e9 SUCCESS); 5th already done too — alerting-service@e111843 ancestor of main, live job
      shows durable command (updated 2026-07-12), matches terraform. Flip last checkbox citing evidence, flip status
      resolved, archive.
- [ ] [PLAN] P2. `plans/active/mdps_features_reduced_artifact_tracker_2026_06_28.md` — pure tracker (0 own todos), all 9
      linked mini-plans confirmed archived. Archive — no orphaned scope (do this AFTER §1's citation fix, since this doc
      IS the source of that bug).
- [ ] [PLAN] P2 (superseded). `plans/active/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` — both
      architecture asks SHIPPED+PROVEN+QG-GREEN (mtds@0aa6163+deployment-service@b5246a6;
      mtds@1e4dfb2+deployment-service@b04cfcc); "run launcher over full ranges" ask executed via archived
      `mvp_backfill_cefi_tick_v10_2026_06_27.md` → `cefi_completion_program_2026_07_15.md`; ongoing work continues in
      still-active `cefi_hl_aster_batch_data_gaps_2026_06_22.md`. Archive with a banner naming the absorption chain —
      first quick-check `cefi_hl_aster_batch_data_gaps_2026_06_22.md` to confirm the noted "2-day live-health check in
      progress" didn't fall through the cracks.
- [ ] [PLAN] P2 (superseded). `plans/active/issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` — RESOLVED
      2026-06-23 banner: 17/18 repos bumped (`workspace-constraints.toml` confirms aiohttp>=3.14.1). Sole remaining P2
      fully owned by `issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md` (confirmed open,
      operator-gated — see §5). Archive with a pointer to that doc as sole successor.
- [ ] [PLAN] P3 (superseded, unclear-adjacent). `plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` — single
      dated snapshot (4 defi cells, ORACLE_EXPECTS_DATA), no recurring instance found; reprobe mechanism has since
      industrialized into a scheduled auto-flip system, but that system never auto-flips ORACLE_EXPECTS_DATA verdicts —
      so the 4 cells were never mechanically re-resolved. Default: archive as stale. If certainty wanted first: run one
      fresh `reprobe_new_empty_confirmed.py` pass on the 4 named cells (ALCHEMY gas_fees, CHAINLINK oracle_prices, CURVE
      dex_pool_state, PANCAKESWAP_V3 dex_pool_state) before archiving.

---

## §3 — Migrate to a named July plan, then archive (15 docs)

- [ ] [PLAN] P2. `plans/active/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (P1, legs a-e) +
      `instruments_completion_tracker_2026_07_06.md` (Stage 2a/2b GAP-4). Already migrated verbatim 2026-07-26; both
      successors still open — dual-track until they ship, then flip+archive. 2 items correctly left gated/latent, not
      migrated.
- [ ] [PLAN] P2. `plans/active/issues/phantom_captures_prediction_2026_06_28.md` →
      `cross_cutting_consolidated_closeout_2026_07_25.md` Track 22. Track 22 only cites the 1 remaining CODE P2 todo
      (MTDS writer → `empty_confirmed` for 0-activity contracts) — copy the full todo text + gate verbatim, then
      archive.
- [ ] [PLAN] P2. `plans/active/issues/tradfi_backfill_oom_remediation_2026_06_24.md` →
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` ([TRADFI] P1 memray-footprint todo) + gated
      `…batch2_finalize_2026_07_25.md`. Successor todo still open/unexecuted — not yet archivable, just confirm the
      migration held.
- [ ] [PLAN] P2. `plans/active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` →
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` (~L270-286), covers items (2) DP_VM_GONE_NO_CAPTURE
      debounce + (3) InstrumentsHandler str/int bug. Item (1) (operator-gated prod-manifest `--apply`) has no other home
      — see §5, needs an operator-decision-ledger home first.
- [ ] [PLAN] P2. `plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (L69-81), verbatim, cites Source + "Done when." Not
      yet executed either place.
- [ ] [PLAN] P2. `plans/active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md` →
      `cross_cutting_satellite_ao_dispatch_batch2_2026_07_26.md` (L248-269). Sole remaining item (Cloud Logging
      ingestion gap) merged with a duplicate finding in `data_pipeline_ag_residual_backfill_decisions_2026_07_24.md`. 2
      other items already done in code (`alerting-service/alerting_service/api/main.py:77-88`;
      `deployment-service/terraform/gcp/alerting_relay_pubsub.tf`) — flip those first, then migrate the rest.
- [ ] [PLAN] P2. `plans/active/issues/uv_pin_fleet_drift_2026_06_22.md` →
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`. setup.sh fleet rollout + boot-script hardening already "DONE
      2026-07-26" there (instruments-service@40240042, unified-trading-pm@703b1e912); residue (0.10.8 constant
      centralization, uv-version drift-guard, Harsh's-laptop/epic-VM realignment) parked as batch1's own items 2-3. Flip
      several done-but-unchecked boxes in the source doc first.
- [ ] [PLAN] P2. `plans/active/l0_doc_index_generator_2026_06_24.md` →
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md` (~L476-498). 2 remaining Deferred items (AO-dashboard L0-graph
      route; on-demand stale-check wrapper) cited Source verbatim, still open there. Archive now with a banner (no
      lock).
- [ ] [PLAN] P2. `plans/active/issues/plan_issue_epic_consolidation_2026_06_30.md` → 5 forks:
      `instruments_completion_tracker_2026_07_06.md`+`mvp_scope_catalogue_tagging_2026_06_08.md` (D1);
      `infra_ops_residual_migration_verification_2026_07_24.md`+`master_data_canonicalisation_migration_catalogue_2026_06_07.md`+`issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md`
      (TradFi-G4-OOM); `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md` (D3);
      `cross_cutting_consolidated_closeout_2026_07_25.md`+`cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`
      (M-C7); `tradfi_consolidated_closeout_2026_07_18.md`+`data_completion_tradfi_2026_07_15.md` (altdata). Confirm a
      home for the one unverified item (Tardis-historical-billing, 775.9k cells) before archiving.
- [ ] [PLAN] P2. `plans/active/issues/instruments_service_plan_reconciliation_2026_06_29.md` →
      `cefi_layer1_denominator_gaps_2026_07_03.md` (C2/C4), `issues/deribit_options_chain_af_g4_blocker_2026_07_03.md`
      (C5). C6 likely covered by `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md` (name-match
      only — verify). C9 (EXTENDED-candle honest-absence, ~10-line fix) is a true orphan — fold into
      `instruments_completion_tracker_2026_07_06.md` or `cefi_consolidated_closeout_2026_07_18.md` first.
- [ ] [PLAN] P2. `plans/active/issues/issue_docs_remediation_sweep_2026_06_02.md` →
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, which cites this doc for 3 open todos (execution-service
      `service_name` drift; SIT's 2 QG failures; UAC `infura_*` rename). 2 true orphans (deployment-scripts bucket
      lifecycle rules; G-TRACE E2E trace API) need a home before archiving.
- [ ] [PLAN] P2. `plans/active/mvp_scope_catalogue_tagging_2026_06_08.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (draft), dispatches both AO-eligible residuals
      (FeaturesMvpRule/StrategiesMvpRule+consumer; real-data MVP-toggle verify) verbatim. Not yet archivable (batch1b
      hasn't run). Models-MVP-taxonomy item should be re-parked as its own `BLOCKED-OPERATOR-DECISION` issue doc.
- [ ] [PLAN] P2. `plans/active/ui_build_warm_cache_2026_06_17.md` → `ci_satellite_ao_dispatch_batch1_2026_07_26.md`
      (item 4). Item 1 (tsc incremental) is ALREADY implemented in both UI repos' tsconfig.json — flag batch1's D28
      entry as needing correction, not fresh dispatch. Item 2 confirmed genuinely not done; item 3 deferred as D20 (see
      §5, operator-gated pnpm decision).
- [ ] [PLAN] P2. `plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md` →
      `plans/epics/infrastructure_master.md` ("Folded-in scope 2026-07-15"). Sole remaining todo (remove 5 Phase-0
      banners, archive tracker) already folded there. **Requires operator `[unlock-plan]`**
      (`locked_by: live-defi-rollout`) before archival — confirm with operator this specific doc before flipping.
- [ ] [PLAN] P2. `plans/active/issues/features_service_coverage_and_script_canon_2026_06_10.md` →
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md` (draft), covers 3 bounded items (relocate 8
      `smoke_matrix.py` files; retire `compute_sfi_progressive_only.py`+launcher; script-homes sweep). 2
      owner-design-call items (velocity-accel fallback; `make_session` loop-safety) have no successor — see §5.

---

## §4 — Partially done, rehome the remainder (10 docs)

- [ ] [PLAN] P2. `plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — Phases 1(1b,1c)/2/5 (11
      todos) already migrated verbatim as Track 0 into `cefi_consolidated_closeout_2026_07_18.md` per operator ruling
      2026-07-25 — flip those checkboxes here once Track 0 closes. Phase 3 (live CLOB depth), Phase 4 (arb wiring),
      Codex SSOT-update, Phase 1d/1e/1f (IBKR equities, oil-perp research, dynamic-universe design, dividend re-run,
      regime research) are self-flagged "SCOPE UNCLEAR" — see §5, need explicit operator naming before any further
      migration. Do NOT archive the whole doc.
- [ ] [PLAN] P2. `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — lines 133/136/176, D3,
      D4 all done/superseded but unflipped (per_venue_margin_buffer_pct deleted; spot-venue axis shipped
      `catalog_staked_basis.py:44-84`; param audit done; D3's motivating Orca/DRIFT scenario deleted 2026-07-16; D4
      exhaustively scoped-not-built) — flip these. D2 (food-chain parameterization) already tracked in
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:110` — not lost, just note the pointer. D1
      (e2e tests bypass canonical config path) is the operator's own "DEFERRED-BY-DESIGN" — see §5. Do not archive given
      D1/D2 remain open.
- [ ] [PLAN] P2. `plans/active/issues/fleet_audit_triad_deferred_followups_2026_06_01.md` — item 1
      (rolling-archive/serial-capture tofu apply) done → `infra_capture_and_devops_leftovers_2026_07_06.md:161` (DONE
      2026-07-07); item 7 (DeFi swaps_ohlcv chain-column reprocess) → `data_completion_defi_2026_07_15.md:217` (D2),
      also cited in `defi_satellite_ao_dispatch_batch3_2026_07_26.md`. Flip both. Items 2-6,8 genuinely unresolved but
      under the operator's explicit 2026-06-01 "let it be" banner — no new plan warranted, keep dormant (see §5 for the
      Tardis-key/GCS-gap items specifically).
- [ ] [PLAN] P2. `plans/active/pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` — GATE-0 narrow
      tracker fully shipped (9/9, confirmed by `cross_cutting_consolidated_closeout_2026_07_25.md` Track 1). 2
      stale-unflipped traps: features delta_one reader (done, features-service@795e4f4), UI reference-data regen (done,
      0 `hyperliquid_rest` hits across all 4 files) — flip both. M6, M7, T+1 reconciliation+live-TTL, M8's
      cadence-column-wiring, and a confirmed-still-in-code `_merge_dataframes` dedup-key fix
      (`unified-trading-library/unified_trading_library/manifest_writer/_writer_io.py:1250-1261`) stay open here,
      coordinated (not duplicated) via `cross_cutting_consolidated_closeout_2026_07_25.md` Track 1. 2 CICD todos
      (L875/L900) are superseded/moot (staging dormant, destination plan archived) — close as superseded. 1 sports
      test-hermeticity followup (L769) is an orphan — needs a home (`sports_consolidated_closeout_2026_07_19.md`
      test-hygiene scope, or a standalone issue).
- [ ] [PLAN] P2. `plans/active/colocated_feature_pipeline_in_memory_handoff_2026_06_21.md` — items 1.4/1.3b/1.7e
      extracted verbatim into `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` (L113-125, own done-when
      criteria), still open there too — mark superseded-by-batch1 here to avoid duplicate dispatch. Item 1.5b (column
      pruning) confirmed un-migrated anywhere, still blocked on `features_service_e2e_pipeline_test_2026_05_26.md`
      reaching green — keep open here or fold into that plan's eventual owner.
- [ ] [PLAN] P2. `plans/active/codex_violations_ratchet_to_five_2026_06_10.md` — vast majority done (all fleet repos ≤5
      violations, verified 2026-07-27); MTDS >900-line-tail confirmed done in code — flip it, rewrite the
      "remaining >900 tail" catch-all to just instruments-service `_solana_utils.py` (1068L). 2 items (UAC
      `defi_position.py` threshold; deployment-api codex 5→0) already migrated into
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`, still open there — remove/cross-reference the duplicates.
      Rehome pip-audit bumps, domain-client base-gate retarget, `delta_proxy_repricer.py` confirm, and the Phase-3
      schema-provenance catch-all into batch2 once drafted. **Locked (`locked_by: live-defi-rollout`) — needs
      `[unlock-plan]`** before any archival (not yet archivable anyway — real remainder exists).
- [ ] [PLAN] P2. `plans/active/issues/service_dockerfile_pattern_normalization_2026_06_17.md` — 6/9 Pattern-B repos
      already normalized to Pattern A (alerting-service, batch-live-reconciliation-service, fund-administration-service,
      market-data-processing-service@bffb9df, ml-service, trading-agent-service) — 0 checkboxes flipped, flip them.
      execution-service, greeks-service, strategy-service (also vendoring MTDS) still confirmed Pattern-B, gated on
      "Owner: Ikenna" design call — see §5. Track remainder via `infra_consolidated_closeout_2026_07_25.md` Track 1.
- [ ] [PLAN] P2. `plans/active/issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md` — 9/11 done. Item (a)
      RULE-11 (drop `schedule:`/Haiku, delete Cloud Run hygiene-sweep job) confirmed still needed and already migrated
      verbatim into `infra_satellite_ao_dispatch_batch1_2026_07_26.md` ([OPERATOR]-tagged, open) — flip here. Item (b)
      "fold `--precommit` sweep into quality-gates-v2 + retire standalone plan-health-gate GHA job" is a true orphan —
      rehome into a July infra plan (batch2 once drafted, or `infra_consolidated_closeout_2026_07_25.md` Track 1) before
      archiving.
- [ ] [PLAN] P3. `plans/active/issues/orphan_rootm_branch_unmerged_work_2026_06_05.md` — core premise ("7 branches left
      in place") now factually false: `git ls-remote` (2026-07-27) confirms 0 matching `tab/rootm/*` branches remain in
      any of the 6 repos — add a correction banner. Disposition rehomed into
      `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s open REVIEW P2 todo (per-commit-set check, unexecuted) +
      `issues/autonomous_session_operator_decisions_2026_07_25.md` #23 (unresolved A/B/C — see §5). Don't archive until
      `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` writes a dated verdict onto this doc, or the operator
      rules on #23.

---

## §5 — Operator-gated queue, interactive session (42 items)

Operator asked to go through these one at a time: "what do you need from me?" Format: doc — the actual gate/decision
needed.

1. `cefi_ml_directional_continuous_live_2026_06_20.md` — ≥7-day live run needs wallet keys + kill-switch arming
   (BLK-e64b661a); 2-yr backtest grid needs an operator-scheduled VM run.
2. `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` — Phase 3/4/Codex/1d-1f scope self-flagged "SCOPE
   UNCLEAR" — needs explicit operator naming before migration.
3. `v2_engine_venue_buildout_2026_06_15.md` — Tier-2 Tardis-credentialed VOL_* backtests + 2 ML model-variant trainings,
   correctly parked on credentials/operator.
4. `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` — dual-deposit cross-exchange cost bps is a
   placeholder (`Decimal("150")`, `strategy-service/.../archetypes_rank.py:335`) needing a real calibrated number.
5. `issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` — D1 (e2e tests bypass canonical config path),
   operator's own "DEFERRED-BY-DESIGN," no timeline given.
6. `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24.md` — retention-floor day=all fold + part
   of the enrichment backfill are BLOCKED-OPERATOR-DECISION.
7. `sports_odds_bookmaker_coverage_enumeration_2026_06_20.md` — regression-test-deletion discrepancy (Todo 2/3) +
   canonical-namespace conflict vs closeout Track C/V both need explicit rulings.
8. `tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` — keep-vs-purge 4,655 stale barchart manifest rows, a human
   data-correctness call, unowned across all July batches.
9. `data_completion_to_100_all_ag_2026_06_21.md` — BYBIT futures_chain legacy-object delete is [OPERATOR]-gated
   (hard-stop #2).
10. `monitoring_control_plane_master_2026_06_10.md` — G4/G5 panels "BLOCKED-ON: verdict-store OR operator OK on a
    faithful port."
11. `issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md` — prod-manifest mutation via
    `populate_v9_index_columns_inplace.py --apply` explicitly surfaced to operator, not auto-applied.
12. `issues/fleet_audit_triad_deferred_followups_2026_06_01.md` — Tardis paid key + GCS manifest 22-day gap under the
    operator's 2026-06-01 "let it be" banner.
13. `issues/vm_backfill_data_correctness_findings_2026_06_29.md` — F4 (Curve subgraph dead) BLOCKED-CREDENTIALS; F7
    (TradFi `is_mvp` gating) inventory-only pending a scope call (see also §1).
14. `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — G5 (backfill-to-100%) has no per-AG owner
    anywhere, needs an ownership ruling; G1-ENUM P1 finding needs an owner picked from 3 given fix options.
15. `citadel_paper_batch_live_reconciliation_2026_06_19.md` — P2.7.3/P7.3 live-wallet reconciliation is
    BLOCKED-OPERATOR-DECISION (human-only custody gate).
16. `issues/live_mode_event_sink_topic_missing_2026_06_21.md` — needs an explicit pick between Option A (repoint to
    shared topic) vs Option B (per-service topic) — a batch doc explicitly declined to choose.
17. `issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md` — warm-GCS-parts durable sink (M-C7) explicitly
    awaiting operator greenlight to build real code.
18. `issues/execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md` — blocked on the operator's standing
    "do not refactor execution-service tests mid-active-development" (never lifted).
19. `issues/aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md` — same gate as #18 (its only remaining scope is that
    migration).
20. `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` — 3 operator-only decisions: cron cadence, quickmerge-provenance
    re-arm-leak accept/fix, WS-I service-to-service-auth re-homing.
21. `issues/aws_codebuild_pr_approval_status_noise_2026_06_25.md` — BLOCKED-OPERATOR-DECISION (needs AWS-side IAM
    change); a queued empirical check hasn't run yet.
22. `codex_violations_ratchet_to_five_2026_06_10.md` — locked (`live-defi-rollout`), needs `[unlock-plan]`;
    `delta_proxy_repricer.py` dead-code needs operator/architect confirm.
23. `repo_scripts_governance_audit_2026_06_18.md` — delete-execution is campaign-gated; D16 carve-scope decision open.
24. `issues/plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md` — RULE-11 (drop `schedule:`/Haiku, delete Cloud
    Run job) is [OPERATOR]-tagged.
25. `issues/plan_issue_epic_consolidation_2026_06_30.md` — residual operator-decision queue (5 of 7 already forked;
    Tardis-historical-billing item needs confirming).
26. `issues/plan_reconciler_doc_hygiene_findings_2026_06_17.md` — finding 2 (`plans/active/INDEX.md` abandoned,
    226-entry drift) is an explicit A/B/C operator call, parked in `infra_plan_reconcile_parked_decisions_2026_07_26.md`
    §3.
27. `issues/instruments_service_plan_reconciliation_2026_06_29.md` — C9 (EXTENDED-candle honest-absence fix) needs
    folding into a live successor before archival.
28. `issues/issue_docs_remediation_sweep_2026_06_02.md` — 2 true orphans (bucket lifecycle rules; G-TRACE API) need a
    home before archiving.
29. `bigquery_feature_ml_compute_engine_option_2026_06_08.md` — all 5 remaining todos gated behind 3 named "Open
    questions (operator)," re-confirmed correct as of 2026-07-26.
30. `bucket_iam_write_protection_per_tier_2026_06_09.md` — P1.2b BLOCKED-CREDENTIALS (current credential lacks
    `setIamPolicy`), pinged to operator.
31. `mtds_file_size_refactor_2026_06_08.md` — `status: paused` pending operator reprioritization; no external successor
    claims the scope.
32. `mvp_scope_catalogue_tagging_2026_06_08.md` — Models-MVP-taxonomy sub-item BLOCKED-OPERATOR-DECISION (no stable
    `model_id` taxonomy).
33. `ui_build_warm_cache_2026_06_17.md` — pnpm content-addressable store (D20) is an explicit decision item (changes
    lockfile format + CI install steps).
34. `utl_uac_reuse_consolidation_remediation_2026_06_10.md` — locked (`live-defi-rollout`), needs explicit
    `[unlock-plan]` grant (see also §3).
35. `instruments_foundation_completeness_2026_06_24.md` — multiple pending operator sign-off gates (GATE 0, G1 not
    recorded signed off; G4 contested 2026-07-13).
36. `issues/capability_wizard_analysis_findings_2026_06_11.md` — F46 BLOCKED-CREDENTIALS (3 CeFi perp adapters need live
    API keys); several LOGIC-FREEZE items recently unfrozen per operator ruling.
37. `issues/capability_wizard_gap_discovery_2026_06_11.md` — F45 exposure-normalization pipeline owner + margin_health
    CeFi LOGIC-FREEZE items are BLOCKED-OPERATOR-DECISION.
38. `issues/features_service_coverage_and_script_canon_2026_06_10.md` — 2 owner-design-call items (velocity-accel
    fallback semantics; `make_session` loop-safety) with no owner/successor.
39. `org_migration_to_odumresearch_2026_06_07.md` — `status: paused`, explicitly conditional on operator ruling
    org-vs-stay-on-Pro (still undecided — remotes/READMEs still default to IggyIkenna).
40. `issues/orphan_rootm_branch_unmerged_work_2026_06_05.md` — disposition of 7 (now-confirmed-deleted) branches is an
    unresolved operator decision (`autonomous_session_operator_decisions_2026_07_25.md` #23, A/B/C).
41. `issues/macro_micro_econ_data_capture_audit_2026_06_05.md` — 4 numbered "Open questions for operator" unresolved
    (Glassnode-Pro/CoinGlass build-vs-buy; single FRED source-of-truth); altdata home + EIA credential ask
    BLOCKED-CREDENTIALS/OPERATOR-DECISION downstream.
42. `issues/service_dockerfile_pattern_normalization_2026_06_17.md` — "Owner: Ikenna" design call on the 3 remaining
    Pattern-B repos (execution-service, greeks-service, strategy-service) — also in §4.

---

## §5-RESOLVED — Interactive operator-gate session (2026-07-27, all 42 items dispositioned)

Ran item-by-item; several turned out to be stale/already-resolved on fresh investigation (flagged below), not fresh
operator decisions. Recorded here so §2-§4 execution + fresh todos can proceed without re-litigating. **General
correction**: Tardis API-key/billing block is CLEARED — every item below tagged BLOCKED-CREDENTIALS(Tardis) is now
UNBLOCKED (#3, #12, #25). **General correction**: "Owner: Ikenna/Harsh" human-split tags are STALE — no more human-owner
splits, this is agent work (operator ruling, applies beyond #38/#42 — any other `Owner: <name>` design-call tag found
during §2-§4 execution should be treated the same way, not re-parked on a human).

1. cefi_ml — stands: wallet keys/kill-switch + operator-scheduled VM run, no chat decision.
2. cryptovenue_equity_perps — **CORRECTED**: no literal "SCOPE UNCLEAR" flag exists in the doc; Phase 1d-1f are
   well-scoped live DESIGN/RESEARCH/SCRIPT todos with clear repos already in the active plan, Phase 3/4/Codex-SSOT are
   plain 1-line P2 todos. No operator naming needed — leave the plan active, todos are normal open work, not blocked.
3. v2_engine_venue_buildout — Tardis creds UNBLOCKED (see general correction); VOL_* backtests can proceed. ML
   model-variant trainings still need an operator-scheduled VM run.
4. defi_collateral_sizing bps=150 — KEEP as documented reasonable estimate; close the placeholder flag, no calibration
   work needed.
5. e2e_defi_config_taxonomy D1 — confirmed stays DEFERRED-BY-DESIGN, no timeline.
6. sports_canonical day=all fold — **CORRECTED (was stale)**: already operator-authorized 2026-07-25 (Option A,
   `sports_day_all_teams_venues_fold_key_scheme_mismatch_2026_07_25.md`), reversibility re-verified 2026-07-27 (7-day
   soft-delete). Not about "teams over time" — confirmed dead legacy season-keyed snapshot, zero live readers.
   **Execute**: backup-copy-first, then delete the 2 named objects per the delete-safety protocol.
7. sports_odds_bookmaker_coverage — canonical-namespace conflict **ALREADY resolved** (merged 2026-07-27, UAC registry
   form wins, no fresh decision). Regression-test-deletion: **RESTORE** equivalent tests for `TestFootystatsOddsNanFill`
   (4 tests) + the SP-10-ODDS regression guard (functionality survived, only the tests were dropped in
   instruments-service@6404abd6 and never restored).
8. tradfi_eu_not_draining — 4,655 stale Barchart manifest rows: **PURGE** (source retired 2026-07-19).
9. data_completion_to_100_all_ag — BYBIT futures_chain legacy delete: **APPROVED**.
10. monitoring_control_plane G4/G5 panels — **UNBLOCK**: no CI/CD billing wall anymore: proceed with the real Firestore
    verdict-store generalisation (not the faithful-port workaround) for both panels.
11. dp_alerts_dp_not_v9 — `populate_v9_index_columns_inplace.py --apply`: **APPROVED** to run.
12. fleet_audit_triad Tardis paid key — UNBLOCKED (see general correction), proceed. GCS 22-day gap item unchanged
    (still under the 2026-06-01 "let it be" banner).
13. vm_backfill_data_correctness F4 (Curve subgraph) — stands, BLOCKED-CREDENTIALS, external. F7 (TradFi `is_mvp`
    gating) — **DECIDED**: yes, gate TradFi capture by `is_mvp`; file as a real P2/P3 todo in
    `tradfi_consolidated_closeout_2026_07_18.md` (this also unblocks the §1 bug-1 fix's F7 rehome).
14. master_data_canonicalisation — G1-ENUM fix: **Option (a) chosen** — symmetric `_rollup_bundle_grain` on the
    present-set before the set-difference. G5 ownership: **unblock the 5 named per-AG plans** (manifest migrations done
    everywhere, G4 green all 5 AGs) but **wrap the actual todos into a newer backfill plan covering AWS parity in code**
    (switch-toggle to use AWS via config, as already designed — smoke-testable; GCP stays home for MTDS full backfills)
    — check staleness of the 5 named plans' todos given their age since G4 unlocked.
15. citadel_paper_batch_live P2.7.3/P7.3 — stands, human-only custody gate, external.
16. live_mode_event_sink_topic — **Option A chosen**: repoint UTL `_sink_factory.py` to canonical
    `service-lifecycle-events`; delete the interim unmanaged `market-tick-data-service-events` topic after.
17. live_pipeline_persistence M-C7 warm-GCS-parts durable sink — **APPROVED** to build real code (not just design).
    18/19. execution_service_aioresponses migration (+ CVE-2026-34993 vcrpy) — **gate LIFTED** for this specific
    test-infra-only migration (mock library swap, no production-logic touch). 20a. cicd_mvp cron cadence — **Option A
    chosen**: self-hosted VM heartbeat, dispatch the promoter every 15min via `gh workflow run`. 20b. cicd_mvp
    quickmerge-provenance re-arm leak — **CLOSE the leak**: re-run the provenance check before re-arming an existing PR.
    20c. cicd_mvp WS-I service-to-service-auth — **still wanted**, re-home into a fresh active plan (not the other ~51
    deferred hygiene todos from the archived source).
18. aws_codebuild_pr_approval_status_noise — **CONFIRMED ALREADY RESOLVED**: verified live via `gh pr view` — the "AWS
    CodeBuild" status check shows `SKIPPED` (not the red `FAILURE` the finding described) on unified-api-contracts#776
    and deployment-service#571. Archive with this evidence, no fresh action.
19. codex_violations — unlock **GRANTED**. `delta_proxy_repricer.py`: NOT dead code as assumed — its dependency
    `UnderlyingTracker` is tested/used elsewhere but the repricer class itself has zero tests/callers (built, never
    wired in). **File as real work to wire in**: keep the module, open a new todo to integrate it into the live
    execution handler + add tests (MM delta-proxy repricing IS wanted).
20. repo_scripts_governance D16 — **PM-only carve scope chosen** (matches current CLAUDE.md carve #3). The
    campaign-gated delete-execution cohort is a sequencing gate, not a fresh decision (already correctly scoped: wait
    for each AG's manifest-canonicalisation plan to archive).
21. plan_hygiene RULE-11 — **APPROVED** (drop `schedule:`/Haiku, delete the Cloud Run hygiene-sweep job).
22. plan_issue_epic_consolidation Tardis-historical-billing (775.9k cells) — confirmed still unowned (separate rehome
    task, tracked in §4), now also UNBLOCKED (see general correction).
23. plan_reconciler INDEX.md — **KEEP + auto-generate**: extend `regenerate_active_plan_inventory.py` (or a sibling
    script) to render a domain-grouped index from each plan's own `summary:`/`asset_group:` frontmatter (every plan
    already carries `summary:`) — fixes the drift at the root while keeping the narrative-context value the pure
    checkbox dashboard doesn't have. Add a CLAUDE.md doc-retrieval rule to read it before scanning `plans/active/` for a
    domain.
24. instruments_service_plan_reconciliation C9 — fold into `cefi_consolidated_closeout_2026_07_18.md`.
25. issue_docs_remediation_sweep 2 orphans (deployment-scripts bucket lifecycle rules; G-TRACE E2E trace API) — **file
    both** into `infra_satellite_ao_dispatch_batch1_2026_07_26.md` as new todos.
26. bigquery_feature_ml — scale-bound subset first + BQML-vs-feature-store-per-model both **confirmed**. Sequencing: v9
    `--apply` **HAS landed** (G4 green all 5 AGs) — this plan is unblocked; **also check the corpus for other plans
    similarly stale-blocked on "wait for v9 apply"** (new todo, not yet done).
27. bucket_iam_write_protection P1.2b — stands, BLOCKED-CREDENTIALS (current credential lacks `setIamPolicy`), external
    grant needed from operator.
28. mtds_file_size_refactor — **RESUME** (un-pause).
29. mvp_scope_catalogue Models-MVP-taxonomy P2b — **CORRECTED**: a stable, already-versioned `model_id` scheme ALREADY
    EXISTS — `generate_model_id`/`parse_model_id` in `ml-service/ml_service/training/ml/config_schema.py`:
    `{ASSET_GROUP}_{ASSET}_{TARGET_TYPE}_{MODEL_TYPE}_{TIMEFRAME}_V{N}`, genuinely unique/stable over time by
    construction. The "BLOCKED-OPERATOR-DECISION" framing is stale — the real remaining work is wiring a `ModelsMvpRule`
    consumer against this existing scheme (an implementation task, not an open design decision).
30. ui_build_warm_cache pnpm — **MIGRATE** to pnpm's global content-addressable store.
31. utl_uac_reuse_consolidation — unlock **GRANTED**.
32. instruments_foundation_completeness GATE 0/G1/G4 sign-off tensions — **CORRECTED**: already accepted-as-is per the
    operator's 2026-07-23 unlock ruling, not re-litigated. No fresh decision needed.
33. capability_wizard_analysis F46 — stands, BLOCKED-CREDENTIALS (3 CeFi perp adapters need live API keys), external.
34. capability_wizard_gap F45 — **owner: strategy-service pre-trade layer** (not a net-new risk-service). The
    margin_health CeFi LOGIC-FREEZE items are mostly already implemented (`emit_live_cefi_margin_events` shipped); the
    one remaining stub is explicitly LOGIC-FREEZE-deferred to PBM dispatch, not a fresh operator ask.
35. features_service_coverage 2 owner-design items (velocity-accel fallback semantics; `make_session` loop-safety) —
    **operator directive: the plan (agent) owns investigating + scoping these into canonical tasks in the right plans**
    — todo for whoever executes §3/§4: do that scoping work, don't re-park on a human owner.
36. org_migration_to_odumresearch — **STAY on IggyIkenna Pro**. Close out: remove `status: paused`, drop the migration
    scope.
37. orphan_rootm_branch — **CORRECTED**: already resolved via `autonomous_session_operator_decisions_2026_07_25.md` #23
    (Option A, resolved) — batch1's read-only presence-check todo already covers it. Add a correction banner; archive
    once `ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` writes its dated verdict.
38. macro_micro_econ_data_capture — heads up: the doc's "Massive re-adopted as Databento's secondary source" premise is
    now STALE (Massive/Polygon.io fully REMOVED 2026-07-19) — **confirmed redundant, operator agrees**, correction
    banner needed. Answered anyway: (a) altdata home = **shared cross-asset axis**, no new asset_group; (b) paid sources
    = **DECLINE all** (no Glassnode/CoinGlass/CryptoQuant spend); (c) FRED dedup — checked both adapters: MTDS's (358L,
    canonical tradfi shard writer) vs features-service's (158L, independently re-fetches from live FRED API instead of
    reading MTDS's captured output) — **consolidate into MTDS, taking the best of both adapters** (not a pure delete —
    fold in whatever features-service's version does better, e.g. its Secret-Manager config pattern, before removing the
    duplicate fetch path); (d) first-tranche scope = **crypto (CeFi+DeFi) + ETF flows first**.
39. service_dockerfile_pattern_normalization — **agent owns it** (no more Ikenna/Harsh human-owner split, per the
    general correction above) — proceed with Pattern-A fan-out to the 8 remaining Pattern-B repos + the
    strategy-service/MTDS-vendoring tier-violation investigation.

---

## §6 — Unclear, needs a closer look before deciding (2 docs)

- [ ] [VALIDATE] P3. `plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md` — 23 done/8 open: 3 UI todos
      are code-shipped but un-ticked pending a playwright pw:L2 run — no evidence found that pw:L2 has actually run
      since. Plus a fresh 2026-07-18 finding (IS/sports + IS/tradfi CSV downloads return HTTP 500) with no successor
      tracking it anywhere. Check for a newer regression-spec commit on deployment-ui to see if pw:L2 quietly ran; if
      genuinely still blocked on a UI-capable slot, it's real open work, not stale. File the HTTP-500 finding into a
      tracked successor if none exists.
- [ ] [VALIDATE] P3. `plans/active/issues/empty_reprobe_disagreement_2026_06_22.md` — (also in §2) the specific 4 defi
      cells' current-day disposition was not independently re-probed this session. Run one fresh
      `reprobe_new_empty_confirmed.py` pass on the 4 named cells before deciding archive-as-is vs re-probe-first.

---

## Progress Log

- 2026-07-27: Plan created as the durable capture of the /plan-vintage-audit June-2026 workflow run (81 docs, 12
  classify groups), per operator directive to fix §1's 2 bugs, execute §2 (11 archives) + §3 (15 migrations) + §4 (10
  rehomes), then hold an interactive session over §5 (42 operator-gated items) and decide §6 (2 unclear items). Nothing
  in §1-§4 executed yet — operator explicitly said hold execution until after the operator-gate interactive session.
  Full per-doc evidence for every finding lives in this session's Workflow run (`wf_b21a8ddd-030` / task `wydy53w83`) if
  a deeper citation is ever needed beyond what's captured above.
