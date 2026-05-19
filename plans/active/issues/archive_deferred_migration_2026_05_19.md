---
title: Archive DEFERRED-item migration audit — 24 plans with open items
created: 2026-05-19
author: slot-1
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
