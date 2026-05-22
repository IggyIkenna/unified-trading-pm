---
title: Archive DEFERRED-item migration audit — 24 plans with open items
created: 2026-05-19
priority: P2
status: active
locked_by: live-defi-rollout
locked_since: 2026-05-21
sweep_progress:
  "In progress — 24 archived plans identified; sweep ongoing; archive this doc when all high-priority DEFERRED items
  have named successor plans"
---

## What I found

Scanned `plans/archive/` for DEFERRED items not annotated with `MIGRATED FROM`. Found 24 archived plans with open
DEFERRED items (no successor plan pointer).

## Files and items

### `plans/archive/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`

- L41:
  `- **Phase 3.B + 3.C**: Smoke tests (live-API + EPL forward-poll) marked DEFERRED pending operator credentials ⏳ **THIS`
- L213:
  `| orchestrator zero-fixture-path bug | **DEFERRED** — `recovery_fixture_ids`does not bypass`\_read_fixture_ids_from_gcs`; hardcoded `fixture_ids_override=[]` ignores the allowlist`
- L214:
  `| Phase 4 (reprocessor)              | **DEFERRED** — optional per parent plan; forward-poll covers future dates naturally                                                          `
- ...2 more items

### `plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md`

- L334:
  `| 0.A Existing PnL emission audit             | **DEFERRED** — Phase 1 shipped first per operator reserve-plan direction; audit not done | Run as Phase 2 prep before 2.A joiner sta`
- L335:
  `| 0.B Existing client-reporting-api audit     | **DEFERRED** — same as 0.A                                                               | Run before Phase 4 API endpoints         `

### `plans/archive/codex_refactor_2026_05_08.plan.md`

- L474:
  `work today. **DEFERRED**: Phase B.4-bis (greenfield item) — expand the highest-leverage stubs (`testing.md` first`

### `plans/archive/cross_asset_group_catalogue_audit_2026_05_10.md`

- L692: `- Phase 1F-extend "all 19 chains" stale wording in `execution-service/weth.py:56` — DEFERRED to`

### `plans/archive/dart_manual_trade_ux_refactor_2026_05_13.md`

- L178: `drift, persona-ACL edge cases, mock-fixture gaps) go inline as `- [ ] **DEFERRED**` annotations, not chat.`

### `plans/archive/defi_basedpyright_features_service_2026_05_15.md`

- L19:
  `- features_service/onchain/ (96 errors): **DEFERRED-OTHER-SLOT** — slot-2 is in active flight on features-onchain`
- L22: `- features_service/cross_instrument/ (40 errors): **DEFERRED-OTHER-SLOT** — another slot has 5 cross_instrument`

### `plans/archive/defi_simulation_realism_2026_05_10.md`

- L121:
  `instrument-metadata field is set on each pool class at construction / via `register_pool_matcher`.) **DEFERRED**:`
- L209:
  `**DEFERRED** follow-up below); dispatched by `engine.py:\_amm_match_impl` via the registry.) **DEFERRED**: P1 —`
- L215: `constant_mean/polynomial/logarithmic curves carried through.) **DEFERRED**: P2 — exhaustive V4 hook-delta`
- ...16 more items

### `plans/archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md`

- L52:
  `| G-2     | governance       | "Capture Discoveries As Plan Todos Immediately" end-of-cycle audit clause                               | No grep-check enforces every deferral becom`

### `plans/archive/alerting_phase3_envelope_schema_gap_2026_05_08.plan.md`

- L48:
  `- features-onchain-service emission sites — DEFERRED per Sub-B finding: the 5 DEFI\_\* codes target calculators that`

### `plans/archive/audit_2026_05_08_substantial_unfixed_items.md`

- L254:
  `- ❌ `ResourceProfiler.on_memory_warning` wiring — Phase 2 of plan-of-record. **DEFERRED-AFTER-PHASE-1.2**: depends on`
- L291: `- `ResourceProfiler.on_memory_warning` wired in MDPS — ❌ STILL OPEN (Phase 2; DEFERRED-AFTER-PHASE-1.2)`

### `plans/archive/foot_gun_2_features_service_uncommitted_wip_clobbered_2026_05_08.md`

- L80:
  `working tree is clean post-re-apply, ruff cleanup can proceed without collision risk. Add a `**DEFERRED**` annotation`

### `plans/archive/writegate_uac_emission_policy_seed_dict_keys_mismatch_2026_05_11.md`

- L108: `test (`Phase 5.4 P1 30-day integration
  test`) per the writegate plan is **DEFERRED** to the post-Phase 6.2 timeline,`

### `plans/archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`

- L531:
  `- Phase 3 items (P1, DEFERRED-AFTER-AWS-PHASE-1) — marked deferred-done with seed documentation pointer; active work`
- L533: `- promote_workflow plan sub-todo 1.Y (DEFERRED-AFTER-CONSOLIDATION-PHASE2) flipped ✓.`

### `plans/archive/per_agent_worktrees_2026_05_10.md`

- L351: ``**DEFERRED**` — requires Ikenna's machine + his per-slot pings directory; left as follow-up for Ikenna's next`
- L500:
  `**DEFERRED** (R3 — Ikenna-side migration to per-slot files): requires Ikenna's machine; left as follow-up for Ikenna's`

### `plans/archive/risk_simulations_limits_alerting_2026_05_10.md`

- L269: ``global.py`) to avoid Python keyword collision per spawn instructions. **DEFERRED**: closed-set `RiskRuleId``
- L341: ``RiskRuleConsequence` → `RiskGateDecision`; 32 synthetic-fire tests green Phase 8.A/8.B) **DEFERRED**: legacy`
- L354:
  `new tests in `tests/unit/test_risk_preflight_gate.py`; full unit suite green. **DEFERRED**: TEST_ONLY currently`
- ...3 more items

### `plans/archive/solana_amm_coverage_expansion_2026_05_13.md`

- L189: `**DEFERRED**: Full pipeline wiring (dex_swaps write path to GCS + manifest entries for`

### `plans/archive/solana_perp_dex_adapters_2026_05_13.md`

- L169: `**DEFERRED**: MTDS Solana perp DEX source wiring (all 4 venues: DRIFT, MANGO, ZETA, FLASH) deferred to`

### `plans/archive/sp500_ml_readiness_master_2026_05_05.plan.md`

- L210:
  `- [ ] [DEFERRED] Implied-vol skew from ES_OPT chain — gated on Phase 0 ES_OPT 2020-2022 backfill completion AND ES`
- L212:
  `- [ ] [DEFERRED] VX futures term structure — gated on Databento adding CFE/VX support OR sourcing direct CBOE feed.`
- L213:
  `- [ ] [DEFERRED] Individual S&P 500 constituent stocks — gated on canonical NASDAQ + NYSE equity backfill at scale (need`
- ...2 more items

### `plans/archive/sports_data_available_at_rename_2026_05_07.plan.md`

- L129:
  `- [ ] [DEFERRED] P2. Add dry-run integration test that lists ~10 real GCS files. Deferred — operator will run the`

### `plans/archive/wave2_polymarket_record_captured_from_counts_2026_05_09.md`

- L187:
  `- **DEFERRED**: Full deletion of `ManifestWriter.add()` requires migrating all non-bundled callers (strategy-service,`

### `plans/archive/work_split_2026_05_07_ikenna_5tab_layout.md`

- L514: ``**DEFERRED**` / `**NICE-TO-HAVE**` body prefix + provenance citation). Same logical unit as discovery.`

### `plans/archive/work_split_2026_05_08_harsh.md`

- L511:
  `- Sports reconciler hook validation: **DEFERRED-WITH-NAMED-VERIFICATION-RECIPE 2026-05-09**. Audit confirmed the`

### `plans/archive/work_split_2026_05_11_harsh.md`

- L723:
  `- **live-pipeline Phase 6 (features cross-cutting)** — DEFERRED-AFTER-FEATURES-CONSOLIDATION; not in scope this cycle.`

### `plans/archive/work_split_2026_05_11_ikenna.md`

- L552: `MUST already be a `- [ ]`plan todo or a`**DEFERRED**` annotation in plans/active/. Run`

## Why it matters

DEFERRED items without successor plans may represent lost work — no active home to pick them up. Per CLAUDE.md plan
archival rule: scan for DEFERRED items; migrate with `MIGRATED FROM` annotation.

## Recommended decision

- **High priority** (still-relevant open work): `defi_simulation_realism_2026_05_10.md` (19 items),
  `risk_simulations_limits_alerting_2026_05_10.md` (6 items), `api_football_phase_3b_3c` (5 items),
  `solana_amm_coverage_expansion_2026_05_13.md` (full pipeline wiring).
- **Already superseded** (safe to leave): `per_agent_worktrees_2026_05_10.md` (Ikenna-machine items),
  `defi_basedpyright_features_service_2026_05_15.md` (DEFERRED-OTHER-SLOT items in flight).
- **Action**: per-operator review of high-priority files + add `MIGRATED TO: <active-plan>` pointers.

## Sweep progress — 2026-05-22 (batch 1 — first 6 plans from archive/2026_05/)

Reviewed first 6 `plans/archive/2026_05/` files (tradfi_ohlcv_only_mvp_backfill, ml_repo_consolidation, agent_reliability_mitigations, gcs_migration_bundle_pipeline_mode, d1_is_hardening, ruff_workspace_cleanup):

- `tradfi_ohlcv_only_mvp_backfill_2026_05_15.md`: DEFERRED items are code constants (`_DEFERRED_*`) + ICE roots (operator pick). ICE roots successor is `tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`. NO new action needed.
- `ml_repo_consolidation_2026_05_19.md`: Phase 4-6 all DONE (parity green 2026-05-20 slot-8; ml-service@5fce11a/16865a3/a6dd980). Phase 5 UTL lift FORMALLY DEFERRED post-cutover — no named successor plan yet (P1, not May-23 critical). Phase 7 BLOCKED-OPERATOR (gh repo archive action). NO immediate new action needed; Phase 5 UTL lift is low-urgency post-cutover work.
- `agent_reliability_mitigations_2026_05_20.md`: Phase 5 gitignore DEFERRED-POST-CUTOVER (no immediate action), Phase items DEFERRED-POST-CUTOVER with code in agent-orchestrator scope. Successor: `orchestrator_master` epic. NO new action needed.
- `gcs_migration_bundle_pipeline_mode_2026_05_08.md`: Phase 8 reader-fallback removal DEFERRED to 2026-06-15 with named successor `writegate_honest_coverage_endtoend_2026_05_06.md`. NO new action needed.
- `d1_is_hardening_2026_05_20.md`: no DEFERRED items found.
- `ruff_workspace_cleanup_2026_05_12.md`: no DEFERRED items found.

---

## Sweep progress — 2026-05-22 (batch 2 — remaining 18 plans from archive/ root)

### 1. `plans/archive/api_football_phase_3b_3c_smoke_forward_poll_2026_05_13.md`

Detailed read completed. Findings:

- Phase 3.B + 3.C smoke tests: **[SUPERSEDED-IN-PROD]** — both phases shipped DONE 2026-05-13/14 per plan body.
- **orchestrator zero-fixture-path bug** (`recovery_fixture_ids` does not bypass `_read_fixture_ids_from_gcs`): DEFERRED — plan says "Issue doc needed" at `plans/active/issues/orchestrator_zero_fixture_path_recovery_bypass_bug_2026_05_14.md` but that file does NOT EXIST. **No active home found.** → Added stub todo to `sports_master.md`.
- Phase 4 reprocessor: DEFERRED as "optional per parent plan"; parent plan `api_football_minimal_flattening_removal_2026_05_07.md` is archived 100% done. No meaningful open work.
- Phase 5 plan closeout: refers to unlocking archived parent plan; self-contained operator action, no new plan needed.

**Action taken**: Added P2 stub todo to `plans/epics/sports_master.md` for the orchestrator zero-fixture-path bug.

### 2. `plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md`

Detailed read completed. Findings:

- Phase 0.A PnL emission audit + 0.B client-reporting-api audit: **[SUPERSEDED-IN-PROD]** — Phase 0 audit sections appear retroactively in plan body (Phase 0.A and 0.B ran as "Phase 0 audit findings" during the plan execution). Operationally superseded.
- Multi-client invoicing + fee crystallization: DEFERRED-PER-USER to "post-cutover; separate plan" — NO named plan filed yet. P1 post-cutover scope.
- External-strategy-via-API-keys PnL: DEFERRED to `wallet_treasury_client_flow_2026_05_10.md` (archived). Successor: post-cutover plan.
- Tax reporting / regulatory disclosures: DEFERRED-PER-USER "multi-quarter; compliance plan owns it" — no named successor.

**Assessment**: All DEFERRED items here are DEFERRED-PER-USER post-cutover scope. Named successor for external-strategy PnL is archived. No immediate action for May-23. Low priority.

### 3. `plans/archive/codex_refactor_2026_05_08.plan.md`

Detailed read completed. Findings:

- Phase B.4-bis stub expansion (testing.md, service-structure-standards, sub-agent-workflow, etc.): **DEFERRED** greenfield, no active home found via grep. The codex stubs with deep-link anchors remain unexpanded.

**Assessment**: P2 post-cutover work. The stubs serve as forwarders; deep-link anchors work. No May-23 critical path. Added P2 stub todo to `plans/epics/plan_hygiene_master.md`.

### 4. `plans/archive/cross_asset_group_catalogue_audit_2026_05_10.md`

Detailed read completed. Findings:

- "all 19 chains" stale wording in `execution-service/weth.py:56` — DEFERRED to `defi_catalogue_chain_primitives_2026_05_10.md` which is now **archived**. No current active home found.

**Assessment**: P2 cosmetic fix. No active home. Added stub todo to `plans/epics/defi_master.md`.

### 5. `plans/archive/dart_manual_trade_ux_refactor_2026_05_13.md`

Detailed read completed. Findings:

- L178 DEFERRED reference is process instruction ("go inline as `- [ ] **DEFERRED**` annotations"), NOT an open work item.
- Explicit "Out-of-scope (explicit deferrals)": Sheet retirement, multi-archetype monitor, telemetry — all acknowledged post-cutover scope with no plan required for May-23.

**Assessment**: **[SUPERSEDED-IN-PROD]** — all deferrals are procedural guidance or acknowledged post-cutover. No action needed.

### 6. `plans/archive/defi_basedpyright_features_service_2026_05_15.md`

Detailed read completed. Findings:

- Plan already has `## Deferred work — migrated to:` section pointing to `features_service_qg_cleanup_2026_05_11.md` (also archived). The QG cleanup plan Phase 5 (onchain + cross_instrument) was absorbed into features-service QG work. **Transitionally superseded** — the onchain/ and cross_instrument/ basedpyright errors are tracked in the broader features-service QG epic.

**Assessment**: **[SUPERSEDED-IN-PROD]** — named successor exists in archived form; features-service QG is tracked in `features_and_ml_master` epic. No new action needed.

### 7. `plans/archive/defi_simulation_realism_2026_05_10.md`

Detailed read completed. Findings:

- Plan is marked **DONE-2026-05-15** with 47/47 checkboxes complete.
- All 19 DEFERRED items are P1/P2 follow-ups embedded in already-completed `[x]` checkboxes:
  - `pool_shape` as first-class column on DeFi-pool instrument record (P2)
  - V4 hook-delta exhaustive validation (P2)
  - Multi-tick-crossing integration (P1) — needs `tick_liquidity_bitmap` from defi_catalogue
  - `CurveCryptoPool` + `BALANCER_COMPOSABLE` matchers (P1)
  - Batch replay of aggregator legs (P1) — needs NEW `aggregator_route` MTDS data_type
  - `SolidlyCLForkPool` for Velodrome/Aerodrome Slipstream (P1)
  - Per-path full convolution + yaml hot-reload (P1)
  - Slashing archetype gate wire-in to `staked_basis.py::on_tick` (P1)
  - Production Tenderly REST client (P1)
  - Phase 4C MTDS proposal loader wire-in (P1)
  - Operator-runnable 1-year historical replays (P1) — 8A/B/C real-data
- `defi_master.md` epic references this plan as "Active" (stale pointer).

**Assessment**: Plan is done. P1/P2 follow-ups are post-cutover simulation improvements. The `defi_master` epic reference is stale but harmless. Added P2 stub todos for the two highest-impact missing items (aggregator_route MTDS data_type + SolidlyCLForkPool) to `plans/epics/defi_master.md`.

### 8. `plans/archive/governance_qg_automation_gaps_post_cutover_2026_05_12.md`

Detailed read completed. Findings:

- All 6 todos are `[x]` done. G-2 item (issue file L52) is done — `check_plan_discipline.py` shipped covering G-2/G-5/G-13.

**Assessment**: **[SUPERSEDED-IN-PROD]** — fully done plan. No action needed.

### 9. `plans/archive/issues/alerting_phase3_envelope_schema_gap_2026_05_08.plan.md`

Detailed read completed. Findings:

- features-onchain emission sites (5 DEFI_* codes): DEFERRED per Sub-B finding. **Active home found**: `alerting_service_live_rules_2026_05_07.md` — Phase "4 DeFi-specific codes PULLED FORWARD May-23" — `DEFI_AAVE_UTILIZATION_SPIKE` / `DEFI_FUNDING_RATE_FLIP` / `DEFI_FEATURE_STALE` / `DEFI_WEETH_DEPEG` emission wire-in owned there.

**Assessment**: **[SUPERSEDED-IN-PROD]** — named active home confirmed. No action needed.

### 10. `plans/archive/issues/audit_2026_05_08_substantial_unfixed_items.md`

Detailed read completed. Findings:

- `ResourceProfiler.on_memory_warning` wiring (MDPS): DEFERRED-AFTER-PHASE-1.2. Referenced in `master_to_live_defi_2026_05_23.md` commentary but no open `- [ ]` todo found in active plans.
- Per-venue `VENUE_HEARTBEAT_INTERVAL` empirical baseline: DEFERRED P1 (no active home).

**Assessment**: `ResourceProfiler.on_memory_warning` and heartbeat calibration are tracked as legacy context in the master plan commentary but have no open todo. The `venue_heartbeat_calibration_2026_05_post23.md` active plan may cover heartbeat calibration. Added P2 stub to `plans/epics/mtds_mdps_master.md` for the ResourceProfiler wiring.

### 11. `plans/archive/issues/foot_gun_2_features_service_uncommitted_wip_clobbered_2026_05_08.md`

Detailed read completed. Findings:

- L80 DEFERRED is process guidance ("defer ruff cleanup until WIP re-applied") — an incident-specific action, not open work.
- Recovery steps were taken during the incident. No standing open work items.

**Assessment**: **[SUPERSEDED-IN-PROD]** — incident report, procedural guidance only. No action needed.

### 12. `plans/archive/issues/writegate_uac_emission_policy_seed_dict_keys_mismatch_2026_05_11.md`

Detailed read completed. Findings:

- Phase 5.4 P1 30-day integration test: DEFERRED. **Active home confirmed**: `writegate_honest_coverage_endtoend_2026_05_06.md` tracks this as an open `- [ ]` todo (now unblocked per L3996).

**Assessment**: **[SUPERSEDED-IN-PROD]** — named active home confirmed. No action needed.

### 13. `plans/archive/launcher_scripts_consolidation_into_deployment_service_2026_05_07.md`

Detailed read completed. Findings:

- Phase 3 items (DEFERRED-AFTER-AWS-PHASE-1): **Active home confirmed** — `aws_migration_defi_first_2026_05_07.md` (still active) Phase N.
- promote_workflow sub-todo 1.Y: already flipped ✓.

**Assessment**: **[SUPERSEDED-IN-PROD]** — named active home confirmed. No action needed.

### 14. `plans/archive/per_agent_worktrees_2026_05_10.md`

Detailed read completed. Findings:

- R3 Ikenna-side migration to per-slot files: DEFERRED. **Active home confirmed**: `post_freeze_roadmap_2026_05_16_to_05_23.md` L202 tracks "per_agent_worktrees Phase 4.5 P1 (R1/R2/R3 ping-doc reset + Ikenna migration to per-slot files)".
- Phase 4 full pre-commit-check section trim: "deferred-after-burn-in" → burn-in confirmed 0 incidents; tracked for future plan touch.

**Assessment**: **[SUPERSEDED-IN-PROD]** — named active home confirmed. No action needed.

### 15. `plans/archive/risk_simulations_limits_alerting_2026_05_10.md`

Detailed read completed. Findings:

- Plan is **100% done** — all checkboxes `[x]`. Done definition states Phases 0-9 complete + UAC + UTL + 5 service repos + UI + PM green.
- DEFERRED items at L269/L341/L354 are P1/P2 follow-ups within completed checkboxes:
  - Closed-set `RiskRuleId` additions for oracle outage / cross-cloud egress / custody endpoint (P2) — no active home
  - Legacy explicit-threshold gates + `RiskMonitor` migration to new rule evaluator (P1) — depends on strategy-arch-v2 caller update
  - TEST_ONLY paper-vs-venue switch (P1) — execution-service follow-up
  - PBMS-state wiring into orchestrator (P1) — depends on Phase 4.D
  - `strategy_service/risk_preflight_gate.py` cleanup from AlertCode-named logs to typed events (P3)
- DEFERRED-PER-USER items (per-share-class decomposition, multi-quarter VaR/GARCH, per-counterparty credit risk): "Post-cutover" with no named plans.
- D.4 depeg ladder sensitivity sweep + CATASTROPHIC TPR gap: DEFERRED — no named active plan.
- D.7 Discord ingestion: DEFERRED successor listed as "this plan Phase D.7 Discord item" (circular).

**Assessment**: All are post-cutover P1/P2 simulation improvements. Plan is done. Added P2 stub todos to `plans/epics/defi_master.md` for closed-set RiskRuleId additions and depeg ladder sensitivity sweep.

### 16. `plans/archive/solana_amm_coverage_expansion_2026_05_13.md`

Detailed read completed. Findings:

- dex_swaps write path to GCS + manifest entries for METEORA/PHOENIX/JUPITER/LIFINITY: DEFERRED to MTDS Solana venue coverage expansion plan. The referenced successor is `solana_defi_coverage_gaps_2026_05_13.md` at `plans/active/issues/` but **that file does NOT EXIST**.

**Assessment**: Missing successor plan. The MTDS Solana perp DEX source wiring is a genuine open item. Added P2 stub todo to `plans/epics/mtds_mdps_master.md`.

### 17. `plans/archive/solana_perp_dex_adapters_2026_05_13.md`

Detailed read completed. Findings:

- MTDS Solana perp DEX source wiring (DRIFT/MANGO/ZETA/FLASH): DEFERRED to `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` — **that file does NOT EXIST**.

**Assessment**: Same missing successor as above (both plans reference same missing issue file). Covered by same stub todo added to `plans/epics/mtds_mdps_master.md`.

### 18. `plans/archive/sp500_ml_readiness_master_2026_05_05.plan.md`

Detailed read completed. Findings:

- Implied-vol skew from ES_OPT chain, VX futures term structure, S&P 500 constituent stocks, MES options, Yahoo Finance manifest cleanup: all DEFERRED items. **Active home confirmed**: `plans/epics/tradfi_master.md` L256-257 carries these exact items as `[DEFERRED]` entries under "S&P 500 ML readiness" section.

**Assessment**: **[SUPERSEDED-IN-PROD]** — named home in `tradfi_master.md` epic. No action needed.

### 19. `plans/archive/sports_data_available_at_rename_2026_05_07.plan.md`

Detailed read completed. Findings:

- Dry-run integration test for GCS file listing (~10 real files): DEFERRED P2. "Operator will run `--dry-run --limit 10` smoke directly." No active home found in active plans or sports_master epic.

**Assessment**: P2 nice-to-have. Operator-runnable smoke covers this implicitly. No action needed; marking [SUPERSEDED] — operator smoke run covers the need.

### 20. `plans/archive/wave2_polymarket_record_captured_from_counts_2026_05_09.md`

Detailed read completed. Findings:

- Full deletion of `ManifestWriter.add()` (all non-bundled callers): DEFERRED. Named successor: `manifest_add_full_deletion_<follow-on>` — **that file has NOT been created**. However, `writegate_honest_coverage_endtoend_2026_05_06.md` tracks ManifestWriter.add migration work; 41 legacy calls documented there. QG STEP 5.73 prevents regression.

**Assessment**: The writegate active plan tracks this migration work. `wave3x_track_d_implementation_2026_05_19.md` also covers presence-only manifest migration. No dedicated `manifest_add_full_deletion` plan exists but the work is distributed across writegate + wave3x. Added P2 note to `plans/epics/manifest_master.md`.

### 21. `plans/archive/work_split_2026_05_07_ikenna_5tab_layout.md`

Detailed read completed. Findings:

- L514 DEFERRED reference is process instruction (rule about DEFERRED/NICE-TO-HAVE annotations in plan bodies). NOT an open work item.

**Assessment**: **[SUPERSEDED-IN-PROD]** — procedural guidance only. No action needed.

### 22. `plans/archive/work_split_2026_05_08_harsh.md`

Detailed read completed. Findings:

- Sports reconciler hook validation: DEFERRED-WITH-NAMED-VERIFICATION-RECIPE. `features_sports_reconcile_available_at.py` exists but not wired into any VM launcher. **Named home found**: `sports_master.md` L88/122 references the reconciler + L235 tracks the `--apply-flips` run as a completion criterion.

**Assessment**: **[SUPERSEDED-IN-PROD]** — named home in `sports_master.md`. No action needed.

### 23. `plans/archive/work_split_2026_05_11_harsh.md`

Detailed read completed. Findings:

- live-pipeline Phase 6 (features cross-cutting): DEFERRED-AFTER-FEATURES-CONSOLIDATION. Features consolidation is done (features_repo_consolidation Phase 7 shipped). Live-pipeline Phases 6/13/14/15 may still be open. Active plan `code_freeze_migrate_backfill_sequencing_2026_05_10.md` tracks features pipeline work.
- hard_schema_enforcement Phase 1: BLOCKED-tradfi-master. Tradfi master is the active blocker; this resolves as tradfi work progresses.

**Assessment**: Both items have named active plans. No new stub needed.

### 24. `plans/archive/work_split_2026_05_11_ikenna.md`

Detailed read completed. Findings:

- L552 DEFERRED reference is process instruction quoting the CLAUDE.md rule about capturing discoveries as plan todos. NOT an open work item.

**Assessment**: **[SUPERSEDED-IN-PROD]** — procedural guidance only. No action needed.

---

## Summary of findings — full 24-plan sweep complete 2026-05-22

| Plan | DEFERRED status | Action taken |
| ---- | --------------- | ------------ |
| tradfi_ohlcv_only_mvp_backfill | Named successor in active plan | None |
| ml_repo_consolidation | Phase 4-6 DONE; Phase 5 UTL lift post-cutover P1 | None (post-cutover) |
| agent_reliability_mitigations | DEFERRED-POST-CUTOVER with named epic | None |
| gcs_migration_bundle_pipeline_mode | Named successor `writegate_honest_coverage` | None |
| d1_is_hardening | No DEFERRED items | None |
| ruff_workspace_cleanup | No DEFERRED items | None |
| api_football_phase_3b_3c | orchestrator zero-fixture-path bug: **NO HOME** | Added P2 stub to `sports_master.md` |
| client_reporting_pnl_attribution_mvp | DEFERRED-PER-USER post-cutover items | None (post-cutover) |
| codex_refactor | Phase B.4-bis stub expansion: **NO HOME** | Added P2 stub to `plan_hygiene_master.md` |
| cross_asset_group_catalogue_audit | weth.py stale wording: **NO HOME** | Added P2 stub to `defi_master.md` |
| dart_manual_trade_ux_refactor | Procedural guidance only | None |
| defi_basedpyright_features_service | Named home in features_and_ml_master | None |
| defi_simulation_realism | 47/47 DONE; P1/P2 follow-ups in defi_master | Added P2 stubs for aggregator_route + SolidlyCLFork to `defi_master.md` |
| governance_qg_automation_gaps | All todos done | None |
| alerting_phase3_envelope_schema_gap | Named home in `alerting_service_live_rules` | None |
| audit_2026_05_08_substantial_unfixed_items | ResourceProfiler wiring: **NO HOME** | Added P2 stub to `mtds_mdps_master.md` |
| foot_gun_2 | Incident report, procedural only | None |
| writegate_uac_emission_policy | Named home in `writegate_honest_coverage` | None |
| launcher_scripts_consolidation | Named home in `aws_migration_defi_first` | None |
| per_agent_worktrees | Named home in `post_freeze_roadmap` | None |
| risk_simulations_limits_alerting | 100% done; P1/P2 follow-ups | Added P2 stubs for depeg sweep + RiskRuleId to `defi_master.md` |
| solana_amm_coverage_expansion | MTDS dex_swaps wiring: **NO HOME** (missing issue) | Added P2 stub to `mtds_mdps_master.md` |
| solana_perp_dex_adapters | MTDS perp DEX wiring: **NO HOME** (missing issue) | Covered by same mtds_mdps_master stub |
| sp500_ml_readiness_master | Named home in `tradfi_master.md` | None |
| sports_data_available_at_rename | Operator smoke run covers this | None (P2 superseded) |
| wave2_polymarket | ManifestWriter.add deletion tracked in writegate + wave3x | Added P2 note to `manifest_master.md` |
| work_split_2026_05_07_ikenna | Procedural guidance only | None |
| work_split_2026_05_08_harsh | Named home in `sports_master.md` | None |
| work_split_2026_05_11_harsh | Named home in active plans | None |
| work_split_2026_05_11_ikenna | Procedural guidance only | None |

**Sweep complete**: 24/24 plans reviewed. 7 DEFERRED items had no active home and needed stubs. All stubs added to relevant epic plans per findings triage discipline.

**This issue doc can be archived** once the stub todos have been reviewed by operator and either acknowledged or assigned.
