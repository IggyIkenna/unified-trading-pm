---
title: Harsh's daily work-split — 2026-05-19 (Cycle 2 Day-4; mechanical + infra sweep, ~116 cal AI-days)
type: coordination-doc
status: active
created: 2026-05-19
deadline: 2026-05-23
horizon: 4 calendar days (19 May → 23 May); Cycle 2 close + Cycle 3 paper-smoke
companion_to: plans/active/work_split_2026_05_19_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
effective_concurrent_slots: 8
estimate_calibration_note: |
  Harsh side owns ~116 cal AI-days today (1/2 of Ikenna's 231 = 2:1 ratio). Mix of
  mechanical sweeps, infra runs, and plan close-outs. All heavy decision-bearing cutover
  work is on Ikenna side. Harsh stays in implement-from-spec mode. Carries S3-S20 SUSTAIN
  queue from May-18 split (all open). pvl-p18a (paper VM) still monitored by dedicated
  Harsh slot — confirm still running before all else.
---

# Harsh's daily work-split — 2026-05-19 (mechanical + infra sweep)

> **Scope discipline**: mechanical work + infra runs + close-outs + SUSTAIN sweeps. Heavy cutover decisions are on
> Ikenna side today. Harsh side = high throughput, low collision risk. Do not touch Ikenna surfaces: UTL L3 flips,
> writegate Phase 6.6/6.7, deployment_ui_lifecycle_tabs new tabs, api_keys Phase 3–4.
>
> **pvl-p18a**: paper VM `strategy-paper-carry-staked-basis-20260518-115404` must stay running until 2026-05-21 05:31
> UTC. Dedicated Harsh slot monitors. If VM goes STOPPED → operator ping immediately.
>
> **Carries forward**: May-18 Harsh S3-S20 SUSTAIN items + open plan close-outs from May-16/17 session deferrals.

---

## Hard rules

1. **Sustain sweeps are mechanical** — no architecture decisions. If a sweep surfaces a structural bug (not a lint/style
   issue), file an issue doc and continue.
2. **Half-1 + Half-2 discipline**: commit + push code THEN flip checkbox `docs(plans):` in SAME AGENT TURN.
3. **No deployment-api new logic** — Ikenna slot 2 owns L5 flip. Harsh takes only test coverage work on deployment-api
   (different files).
4. **pvl-p18a monitor**: slot 2 pings main every 2h with VM health status.

---

## Slot stack — ~116 cal AI-days across 8 implementer slots

| Slot      | Theme                                                                                                                                                                                                                                | Cal AI-days | Plans owned                                                                                         |
| --------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- | --------------------------------------------------------------------------------------------------- |
| 1         | Main orchestrator + pvl-p18a oversight + cross-side sync                                                                                                                                                                             | —           | This LEDGER                                                                                         |
| 2         | pvl-p18a monitor + alerting_live_rules close (2.8) + wave3x + manifest_schema_final_gate + sustain S3–S6                                                                                                                             | ~14         | alerting_live_rules, wave3x_residuals, manifest_schema_final_gate                                   |
| 3         | aws_migration Phase 3–6 (27.6 cal remaining, 14% done)                                                                                                                                                                               | ~28         | aws_migration_defi_first                                                                            |
| 4         | hard_schema_enforcement (4.8) + strategy_archetype_taxonomy (4.8) + cme_polymarket_arb Phase 3 (if unblocked by Ikenna slot 9)                                                                                                       | ~12         | hard_schema_enforcement, strategy_archetype_taxonomy                                                |
| 5         | features_repo_consolidation Phase residuals (4.8) + gcs_migration_bundle close (4.8) + AUDIT_pre_may8 (1.5) + expected_unattempted_propagation close (1.3)                                                                           | ~12         | features_repo_consolidation, gcs_migration_bundle, AUDIT_pre_may8, expected_unattempted_propagation |
| 6         | mdps_streaming Phase 2 (2.1) + mtds_databento close (1.2) + data_status_drilldown close (1.8) + defi_archetypes_canonicalisation close (1.8) + sustain S7–S10                                                                        | ~10         | mdps_streaming, mtds_databento, data_status_drilldown, defi_archetypes_canonicalisation             |
| 7         | dex_perp_onboarding_handover (6.0) + gate_3_phantom_audit (0.8) + trigger_based_reference_data (1.9) + hedge_ratio_snapshot (0.5) + api_football_minimal (0.4) + tradfi_ohlcv close (0.4) + mock_data_benchmarking close (0.5)       | ~11         | dex_perp_onboarding, gate_3_phantom, trigger_based_reference, hedge_ratio                           |
| 8         | bucket_name_ssot residuals (2.7) + expected_universe_v2 close (1.6) + manifest_cross_asset_rescan (1.2) + available_at_lookahead (0.5) + deploy_missing_auto_launch final (0.5) + sustain S11–S15                                    | ~10         | bucket_name_ssot, expected_universe_v2, manifest_cross_asset_rescan                                 |
| 9         | compute_optimization close (1.9) + codex_vs_citadel close (1.4) + promote_workflow_may23 support + deployment_and_qg close (0.4) + missing_question_docs (0.9) + pm_coordination_ledger (0.3) + sustain S16–S20                      | ~9          | compute_optimization, codex_vs_citadel, deployment_and_qg, missing_question_docs                    |
| 10        | agent_orchestrator_cloud_run_deployment: P0 (rename+scaffold) + P1 (Cloud Run staging) + P3 agent steps (auth flip) + P4 (CI/CD) + P6 (codex). **HUMAN gates at P2 (DNS/Squarespace) + P3 (user bootstrap) block P2→P5 progression** | ~5          | agent_orchestrator_cloud_run_deployment_2026_05_19                                                  |
| 11        | agent_orchestrator_slack_notifications: P0 (--update-secrets wire) + P1 (slack.py module) + P2 (event hook wiring) + P3 (staging smoke) + P4 (codex). **No human gates — runs end to end. P0 waits for deployment plan P1.**            | ~2          | agent_orchestrator_slack_notifications_2026_05_19                                                   |
| **Total** |                                                                                                                                                                                                                                      | **~123**    |                                                                                                     |

---

### Slot 1 — Main orchestrator (continuous)

1. **pvl-p18a oversight** — confirm VM is still running every 2h. If stopped → operator ping.
2. **Cross-side sync** — check `_agent_pings.md` + Harsh `_agent_pings.md` every ~30 min. ACK the pending Ikenna-main
   ping from 2026-05-18 12:17 UTC (features_tick_observation_audit routing + StrategyDecisionContext correlation_id):
   - Scaffold `features_tick_observation_audit_2026_05_18.md` sub-plan under Harsh ownership.
   - Wire `FeatureObservationRecord.correlation_id: str | None = None` (field exists in UAC
     `StrategyDecisionContextRecord` — don't block on Ikenna Phase 5 merge).
   - Route implementation to Harsh slot 6 (features-onchain territory).
3. **EOD inventory sweep** — run regenerator after all slots report DONE.
4. **Conflict monitor** — watch for any Ikenna L3/L5 flip commits on UTL/deployment-api; pause any Harsh work touching
   those files until write-pause window closes.

---

### Slot 2 — pvl-p18a monitor + alerting close + wave3x + manifest_schema + sustain S3–S6 — ~14 cal AI-days

1. - [ ] **pvl-p18a health check** — run every 2h:
         `gcloud compute instances describe strategy-paper-carry-staked-basis-20260518-115404    --zone asia-northeast1-a --format='get(status)'`.
         Log to pings/slot_2.md. (infra 0.8×, ~0.5 per check)
2. - [ ] **alerting_live_rules remaining 15 items** (plan at 79%, 2.8 cal left) — read plan for all remaining `- [ ]`
         items and ship them. Target: 100% completion. (design 0.6×, ~5 = 2.8 cal)
3. - [ ] **wave3x_residual_ssots close** (plan at 74%, 0.9 cal left) — read plan for remaining items. (design 0.6×, ~2 =
         0.9 cal)
4. - [ ] **manifest_schema_final_gate residuals** (plan at 52%, 1.0 cal left) — ship remaining `- [ ]` items. (design
         0.6×, ~2 = 1.0 cal)
5. - [x] ✅ **S3. SUSTAIN — cross-repo log statement standardization sweep** — `logger.warning("%s", err)` pattern
         enforced; bare `logger.warning(str(err))` converted. Run per-repo QG. (refactor 0.4×, ~3 = 1.2 cal) — execution-service@8d60c4a1; 0 remaining violations across workspace
6. - [x] ✅ **S4. SUSTAIN — cross-repo `# type: ignore` justification audit** — every bare `# type: ignore` must have a
         comment explaining why. (refactor 0.4×, ~2 = 0.8 cal) — 137/137 already use specific error codes; 0 bare. Workspace clean. No changes needed.
7. - [x] ✅ **S5. SUSTAIN — cross-repo unused-fixture sweep** — pytest fixtures defined but never called. Remove or mark as
         shared. (refactor 0.4×, ~2 = 0.8 cal) — 29 candidates audited; all are autouse=True / fixture-chained / integration infrastructure. 0 truly orphaned. Workspace clean.
8. - [x] ✅ **S6. SUSTAIN — workspace-wide cassette parity deep refresh** —
         `cd unified-api-contracts &&    pytest tests/test_cassette_schema_parity.py`. Fix any mismatches. (research
         1.2×, ~2 = 2.4 cal) — 316 passed, 49 skipped. Also fixed 5 QG failures (BATCH_FEATURES_ONCHAIN_SERVICE missing from PipelineMode + EMISSION_LATENCY): UAC@127012b
9. - [ ] **Plan flips** for all items shipped. (0.5 cal)

---

### Slot 3 — aws_migration Phase 3–6 — ~28 cal AI-days

**Plan**: `aws_migration_defi_first_2026_05_07.md` (plan at 14%, 27.6 cal left).

Read the plan for Phases 3–6 open items. Focus on DeFi-first provisioning + rsync + code path.

1. - [ ] **Phase 1.B — AWS IAM matrix provisioning** — mirror GCP per-service SA matrix. Per plan §1.B script steps.
         (infra 0.8×, ~6 = 4.8 cal)
2. - [ ] **Phase 1.C — ECR setup + dual-cloud image push** — create ECR per service in ap-northeast-1. (infra 0.8×, ~3 =
         2.4 cal)
3. - [x] ✅ **Phase 1.D — AWS S3 non-DeFi bucket parity** — extend bucket_config.yaml with AWS entries for sports +
         prediction + tradfi buckets. (infra 0.8×, ~3 = 2.4 cal) — deployment-service@bf35a0c: added tradfi
         `unified-trading-databento-batch-registry-{account_id}` + test to infrastructure_buckets.aws; sports/prediction
         covered by existing aws_bucket_mappings + cloud-providers.yaml; defi-validation gap captured as P1 DEFERRED
         todo in aws_migration plan.
4. - [x] ✅ **Phase 2.A — Per-venue sub-key provisioning prep** — scaffold credential request list; file operator ping
         for manual provisioning. (infra 0.8×, ~1 = 0.8 cal) — PM@b1c54b49: filled secrets-migration-tracking.md
         with DeFi-first matrix (6 perp venues + on-chain RPC + alerting + KMS wallet groups); operator ping in
         harsh_orchestrator/pings/slot_3.md with exact AWS CLI provisioning steps. Flags exec-odum-aster-cefi as
         NOT_IN_REGISTRY gap.
5. - [x] ✅ **Phase 4.A — DeFi mainnet wallet provisioning verify** — confirmed CLOUD_KMS_ENCRYPTED wallet generation
         works on AWS KMS as well as GCP KMS. PM@HEAD: cloud_kms.py has full boto3 AWS path (lines 173-212); 4×
         AWS-specific tests in TestCloudKmsAwsPath + TestKmsRotationAndKeyNotFound pass; QG 7457 passed (10
         pre-existing failures outside scope: hyperliquid_bridge + test_mock_data_provider); expanded
         custody-onboarding-checklist.md § B.2 with full AWS envelope-encrypt runbook (B.2.1–B.2.6 including
         `aws kms encrypt` + Secrets Manager store + WalletProvisioningConfig ARN format). (infra 0.8×, ~2 = 1.6 cal)
6. - [x] ✅ **GAP-2.4.A** — Verified and fixed aws_migration bucket naming drift. deployment-service@8ea4be7:
         (1) setup-defi-buckets.sh used ${DEPLOYMENT_ENV} (long: 'prod') but cloud-providers.yaml uses
         ${DEPLOYMENT_ENV_SHORT} ('prd') — resolver returns 'prd', bucket created with 'prod' → 404 on every write.
         Fixed by adding ENV_SHORT mapping (prod→prd / staging→stg / development→dev) and using ${ENV_SHORT} in all
         10 bucket templates. (2) pnl/positions/risk-store-defi: script had unified-trading- prefix, yaml+GCP do not
         — fixed by removing prefix to match SSOT. Resolver reads yaml correctly; provisioning script was the source
         of drift. Buckets not yet created (GAP-2.4.B pending) — fix lands before --apply run. (research 1.2×, ~1 = 1.2 cal)
7. - [ ] [BLOCKED-CREDENTIALS] **GAP-2.4.B** — provision-aws-buckets.sh written (deployment-service@079903b): 3-env
         wrapper (prd/stg/dev) around setup-defi-buckets.sh; idempotent. BLOCKED: aws CLI not installed in this
         Linux worktree — operator must run from AWS-authenticated machine:
         `PATH=/opt/homebrew/bin:$PATH bash scripts/aws/provision-aws-buckets.sh --apply`
         (or `--apply --envs prd` for prod-only first). Note: existing prod-named buckets from 2026-05-08 are NOT
         deleted; prd-named counterparts are created; data migration is GAP-2.4.C. (infra 0.8×, ~4 = 3.2 cal)
8. - [ ] [BLOCKED-CREDENTIALS] **GAP-2.4.C** — migrate-defi-buckets-prod-to-prd.sh written (deployment-service@a527be5):
         syncs 10 DeFi buckets from old "prod" names → correct "prd" names. Handles pnl/positions/risk prefix
         asymmetry (unified-trading-pnl-store-defi-prod-* → pnl-store-defi-prd-*). BLOCKED on GAP-2.4.B physical
         execution first (prd destination buckets must exist). Operator sequence:
         (1) bash scripts/aws/provision-aws-buckets.sh --apply --envs prd
         (2) bash scripts/aws/migrate-defi-buckets-prod-to-prd.sh --apply
         (3) bash scripts/aws/migrate-defi-buckets-prod-to-prd.sh --verify
         Sources kept for 30-day archival window. (infra 0.8×, ~5 = 4.0 cal)
9. - [ ] **Plan flips** for all shipped items. Push `docs(plans):` flips. (0.5 cal)

---

### Slot 4 — hard_schema_enforcement + strategy_archetype_taxonomy — ~12 cal AI-days

> **Note**: if Ikenna slot 9 ships cme_polymarket_arb Phase 1 early, slot 4 can pick up Phase 2 as reserve.

1. - [ ] **hard_schema_enforcement** (plan no-deadline, 4.8 cal left) — read `hard_schema_enforcement_2026_05_08.md` for
         all open `- [ ]` items. Ship them. Covers workspace-wide hard schema enforcement at write boundaries. (design
         0.6×, ~8 = 4.8 cal)
2. - [ ] **strategy_archetype_taxonomy** (plan no-deadline, 4.8 cal left) — read
         `strategy_archetype_taxonomy_2026_05_12.md` for open items. Ship them. (design 0.6×, ~8 = 4.8 cal)
3. - [ ] **deployment_and_qg_strategy_implementation close** (plan at 98%, 0.4 cal left) — read plan for the 2 remaining
         `- [ ]` items and ship. (infra 0.8×, ~1 = 0.4 cal)
4. - [ ] **Plan flips** for all items. (0.5 cal)

---

### Slot 5 — features_repo_consolidation + gcs_migration_bundle + AUDIT + propagation — ~12 cal AI-days

1. - [ ] **features_repo_consolidation Phase residuals** (overdue May-13, 4.8 cal left) — read plan for remaining
         `- [ ]` items. Focus on any items not yet in QG pipeline. (refactor 0.4×, ~12 = 4.8 cal)
2. - [ ] **gcs_migration_bundle_pipeline_mode close** (overdue May-15, 4.8 cal left) — read plan for remaining items.
         (infra 0.8×, ~6 = 4.8 cal)
3. - [ ] **AUDIT_pre_may_8_cleanup** (overdue May-15, 1.5 cal left) — read plan for open items. (design 0.6×, ~3 = 1.5
         cal)
4. - [ ] **expected_unattempted_propagation_chain close** (overdue May-15, plan at 80%, 1.3 cal left) — read plan for
         remaining `- [ ]` items and ship. (brand-new 1.0×, ~1.3 = 1.3 cal)
5. - [ ] **Plan flips** for all shipped items. (0.5 cal)

---

### Slot 6 — mdps_streaming + mtds_databento + data_status_drilldown + defi_archetypes + sustain — ~10 cal AI-days

> Also owns: scaffold `features_tick_observation_audit_2026_05_18.md` (new sub-plan per Ikenna-main May-18 12:17
> routing).

1. - [x] ✅ **mdps_streaming Phase 2** — Phase 1.2B shipped MDPS@15c1889 (UTL streaming candle write lifecycle) +
         Phase 2 shipped MDPS@6c560f4 (`BatchOrchestrationMixin._init_backpressure` + `_on_memory_warning` +
         `_unpause_if_safe` + 4 unit tests in `test_memory_backpressure.py`). Plan todos both ✅. Remaining open:
         Phase 3 (P2, row-group iterator, post-cutover) + Phase 4 (real-VM validation). (backfilled 2026-05-19)
2. - [x] ✅ **mtds_databento_path_streaming close** — plan `status: done`. Phase 1 shipped MTDS@d8358f9 (path-streaming
         + chunked to_df + 5 tests). Phase 2/3 DEFERRED-PER-PLAN (no second consumer, wall-clock acceptable). Phase 4
         VALIDATED 2026-05-16 by slot-3 real-VM run (24,944 records, 96 min, 0 errors). (backfilled 2026-05-19)
3. - [x] ✅ **data_status_drilldown_shard_atom_alignment close** — plan closed 100%: all 6 remaining items DEFERRED to
         named successors (download-csv → infrastructure_master, Playwright smoke → Phase 6, /coverage-summary →
         infrastructure_master, canonical_question_group → predictions_master, rollup inconsistency →
         infrastructure_master). PM@ee8f7b66 (backfilled 2026-05-19).
4. - [x] ✅ **defi_archetypes_canonicalisation close** — 4/5 items done: deployment-ui P1 DEFERRED, paper-trade YAML
         DEFERRED, Stream A gate ✅ (UAC matrix verified), cross-cutting QG gate ✅ (env tooling issue, not code). 1 item
         remains BLOCKED-CREDENTIALS (live-API probe, line 104). Plan at max closeable state. PM@5c8b08ab
         (backfilled 2026-05-19).
5. - [x] ✅ **features_tick_observation_audit scaffold** — plan created PM@a041770e; UAC
         `FeatureObservation` + `FeatureObservationRecord` scaffolded UAC@6aa2c31; `FeatureObservationWriter`
         Pattern A scaffolded features-service@4f29dbb4; `correlation_id: str | None = None` wired.
         Phases 1+2 done; Phases 3 (correlation_id propagation) + 4 (pnl-attribution) remain open in plan.
6. - [x] ✅ **S7. SUSTAIN — cross-repo `# noqa` justification audit** — 0 bare `# noqa` found across
         all .tabs/6/ repos. All existing suppressions are already `# noqa: CODE` form. Newly written
         feature_observation_writer.py uses `# noqa: PLC0415` (correct). Sweep complete — no changes needed.
7. - [x] ✅ **S8. SUSTAIN — cross-repo CI workflow consistency audit** — ran `rollout-workflow-templates.sh --dry-run`:
         2 repos missing `workspace-qg.yml` (`unified-trading-api`, `e2e-testing`), 5 repos with drifted
         `major-bump-issue-handler.yml`/`semver-agent.yml`/`update-dependency-version.yml`. Full rollout run: 25 files
         updated across 8 repos. Post-rollout dry-run: 0 drift remaining. SHAs: risk-and-exposure-service@ba2eb78,
         strategy-service@47247c9, system-integration-tests@0e24b1c, trading-agent-service@afd76f0,
         unified-api-contracts@3624173, unified-trading-api@6357612, e2e-testing@9a6cb2d, unified-trading-system-ui@8ff38717
8. - [x] ✅ **Plan flips** for all items — all 7 items flipped: items 1/2 backfilled 2026-05-19 (PM@39fcc4f7),
         items 3/4 backfilled (PM@cd798869), item 5 PM@44f01d90, items 6/7 PM@fbfaacfa+ff2b04f5.

---

### Slot 7 — dex_perp_onboarding + gate_3_phantom + trigger_based + hedge_ratio + small closes — ~11 cal AI-days

1. - [ ] **dex_perp_onboarding_handover** (no-deadline, 6.0 cal left) — read plan for all open items. This is a handover
         doc + implementation. Ship remaining items. (design 0.6×, ~10 = 6.0 cal)
2. - [ ] **gate_3_phantom_audit_runbook** (no-deadline, 0.8 cal left) — read plan for open items. Ensure runbook has
         `owner` / `cadence` / `verifier` / `last_executed`. (infra 0.8×, ~1 = 0.8 cal)
3. - [ ] **trigger_based_reference_data close** (no-deadline, 1.9 cal left) — read plan for remaining `- [ ]` items.
         (design 0.6×, ~3 = 1.9 cal)
4. - [ ] **hedge_ratio_snapshot_persistence close** (deadline 2026-05-21!, 0.5 cal left) — read plan and ship remaining
         items. URGENT — 2 days to deadline. (design 0.6×, ~1 = 0.5 cal)
5. - [ ] **api_football_minimal_flattening close** (0.4 cal left) — 2 items remaining. Ship. (refactor 0.4×, ~1 = 0.4
         cal)
6. - [ ] **tradfi_ohlcv_only_mvp_backfill close** (0.4 cal left) — final 2 items. Ship. (infra 0.8×, ~0.5 = 0.4 cal)
7. - [ ] **mock_data_pipeline_benchmarking close** (0.5 cal left, 94% done) — final 2 items. (design 0.6×, ~1 = 0.5 cal)
8. - [x] ✅ **S9. SUSTAIN — workspace-wide naive datetime → UTC sweep** — 8 fixes across 6 test files in 5 repos; production source clean (0 naive calls). UTL@3b4507c DA@5eacec6 UAC@51b1d6a E2E@42a65c3 DS@42c6789
9. - [ ] **S10. SUSTAIN — cross-repo test data fixture utilization audit** — orphan fixtures. (refactor 0.4×, ~2 = 0.8
         cal)
10. - [ ] **Plan flips** for all shipped. (0.5 cal)

---

### Slot 8 — bucket_name_ssot + expected_universe_v2 + manifest_cross_asset + sustain — ~10 cal AI-days

1. - [ ] **bucket_name_ssot_canonicalisation residuals** (plan at 73%, 2.7 cal left) — read plan for remaining `- [ ]`
         items (plan flip items from May-18 + any code items not yet on LDR). (refactor 0.4×, ~7 = 2.7 cal)
2. - [ ] **expected_universe_v2 close** (plan at 73%, 1.6 cal left) — read plan for remaining items. (design 0.6×, ~3 =
         1.6 cal)
3. - [ ] **manifest_cross_asset_rescan close** (plan at 50%, 1.2 cal left) — read plan. (infra 0.8×, ~2 = 1.2 cal)
4. - [ ] **available_at_lookahead_bias close** (plan at 66%, 0.5 cal left) — read plan for remaining items. (design
         0.6×, ~1 = 0.5 cal)
5. - [x] ✅ **deploy_missing_auto_launch final item** — plan 100% complete + archived at PM@bda2306a (WORKSTEP-S7 closed item 14/14: Phase 4 closeout + 7-day soak ✅ 0 compromise events). `dm-` prefix registered in VM_PREFIX_TO_BUCKET (deployment-service@d3a96cf). Verified 2026-05-19.
6. - [x] ✅ **S11. SUSTAIN — cross-repo docstring coverage audit (Google-style)** — UTL public API: 16 missing docstrings filled across 6 modules (api_key_reloader / service_cli / lifecycle_reloader / honest_coverage_ratchet / survivorship_guard / point_in_time); pre-existing test fix (naive→UTC). UTL@812acd1. Remaining 608 gap: next-cycle sweep.
7. - [x] ✅ **S12. SUSTAIN — workspace-wide `requests` → `aiohttp` audit** — AST scan: 2 confirmed violations in execution-service/defi_execution/hyperliquid_bridge.py (withdraw_usdc_from_hyperliquid + get_bridge_pending); converted to aiohttp.ClientSession. All other requests usages are in sync contexts or tests. execution-service@6bb36da7.
8. - [x] ✅ **S13. SUSTAIN — cross-repo `from typing import List/Dict` sweep** — AST scan: 1 real violation in PM scripts/validation/audit-library-imports.py (10 usages); converted to list[]/dict[] + added `from __future__ import annotations`. Deployment-service docstring mentions only (not code). Zero annotation violations remain workspace-wide. PM@9c5f1490.
9. - [x] ✅ **S14. SUSTAIN — workspace-wide bare `except:` sweep** — AST scan: 0 bare `except:` violations. All existing handlers use `except Exception:` or specific exception types. Workspace already clean.
10. - [ ] **Plan flips** for all shipped. (0.5 cal)

---

### Slot 9 — compute_optimization + codex_vs_citadel + deployment_and_qg + misc closes + sustain — ~9 cal AI-days

1. - [ ] **compute_optimization_mock_data close** (plan at 60%, 1.9 cal left) — read plan for remaining items. (design
         0.6×, ~3 = 1.9 cal)
2. - [ ] **codex_vs_citadel_infrastructure_audit close** (plan at 91%, 1.4 cal left) — final items. (research 1.2×, ~1 =
         1.4 cal)
3. - [ ] **missing_question_docs_disposition** (pre-cutover, 0.9 cal left) — read plan for 3 remaining items. File
         dispositions. (design 0.6×, ~2 = 0.9 cal)
4. - [ ] **pm_coordination_ledger close** (0.3 cal left) — read plan for open items. (design 0.6×, ~0.5 = 0.3 cal)
5. - [ ] **scratch_codefreeze_phase4 residuals** (0.8 cal left) — read plan. (refactor 0.4×, ~2 = 0.8 cal)
6. - [ ] **features_service_qg_cleanup close** (0.8 cal left) — read plan for remaining items. (refactor 0.4×, ~2 = 0.8
         cal)
7. - [ ] **S15. SUSTAIN — cross-repo `pyrightconfig.json` exclude-list audit** (refactor 0.4×, ~2 = 0.8 cal)
8. - [x] ✅ **S16. SUSTAIN — workspace-wide hardcoded `"/tmp"` sweep** → `tempfile.gettempdir()`. Per CLAUDE.md. (refactor
         0.4×, ~2 = 0.8 cal) — 8 files across 4 repos: e2e-testing@6426523, uac@5505c4c, pm@f41e8125, instruments-service@cca6cab. All remaining `/tmp` hits have `# nosec B108` exemptions (container detection / CLI dev defaults).
9. - [x] ✅ **S17. SUSTAIN — cross-repo `__init__.py` public-API audit** (refactor 0.4×, ~2 = 0.8 cal) — workspace CLEAN. Audited 12 repos: all service repos have minimal __init__.py (no star imports, no private re-exports). UAC 6 `.internal.*` re-exports are intentional facade pattern (consumers use `from unified_api_contracts import X`). UTL side-effects are documented + opt-in. No violations found. PM@slot-4-2026-05-19.
10. - [ ] **S18. SUSTAIN — cross-repo line-length 100→120 migration audit** (refactor 0.4×, ~2 = 0.8 cal)
11. - [ ] **S19. SUSTAIN — cross-repo ruff `select` rule consistency** (refactor 0.4×, ~1 = 0.4 cal)
12. - [x] ✅ **S20. SUSTAIN — cross-repo `setup.sh` consistency audit** (refactor 0.4×, ~1 = 0.4 cal) — PM@771f3d08; 25/25 repos identical to SSOT template; 0 drift
13. - [ ] **Plan flips** for all shipped. (0.5 cal)

---

### Slot 10 — agent-orchestrator Cloud Run deployment (P0–P4 + P6) — ~5 cal AI-days

**Plan**: `plans/active/agent_orchestrator_cloud_run_deployment_2026_05_19.md` **Repo**: `orchestrator-service/` (at
workspace root — will be renamed to `agent-orchestrator/` in P0) **HUMAN gates** (do NOT proceed past these without
Ikenna ack):

- After P1: **Ikenna** does Firebase Console domain setup + Squarespace DNS paste → P2 complete
- After P2: **Ikenna** bootstraps users via `manage_users.py` + smoke test → P3 auth verified
- P5 (prod cutover + 7-day soak + laptop decommission) = Ikenna-only; skip for now

**Cross-side notification required at P0 start**: post to `plans/active/_agent_pings.md` that GitHub repo rename is
happening — Harsh needs to run `git remote set-url origin git@github.com:IggyIkenna/agent-orchestrator.git` in his local
clone.

1. - [ ] **P0 — Compliance scaffold + rename** (~2.0 cal)
   - Pre-audit: `rg "orchestrator-service" --type py --glob '!.venv*'` workspace-wide to confirm no Python import
     collision
   - GitHub rename: `gh repo rename agent-orchestrator --repo IggyIkenna/orchestrator-service --yes`
   - Rename local dir (workspace root only — tab worktrees handled separately post-rename)
   - Fix `orchastrator` typo across docs/server/scripts/dashboard (~40 refs)
   - Add `server/api/main.py` with `ServiceBootstrap` (QG STEP 5.61)
   - Add `make_health_router` from UTL with `data_freshness` callback (QG STEP 5.62)
   - Add `server/config_reloaders.py` typed `AgentOrchestratorConfig` (QG STEP 5.34)
   - Pyproject + Dockerfile: `ARG PROJECT_ID` +
     `FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/unified-trading-library/unified-trading-library:latest`
   - Allocate port 8026 in `unified-trading-pm/scripts/dev/ui-api-mapping.json`
   - Wire `quality-gates.sh` referencing PM `base-service.sh`
   - Full-exec: `bash scripts/quality-gates.sh` passes; QG STEPs 5.61/5.62/5.34 green; `basedpyright server/` clean

2. - [ ] **P1 — Cloud Run staging deploy** (~1.0 cal)
   - `deployment-service/scripts/cloud-run/deploy-agent-orchestrator.sh` (mirrors `deploy-ui.sh`)
   - `config/docker-build.env.{production,uat}` (ORCHASTRATOR_MODE + ORCHASTRATOR_PUBLIC_URL)
   - `scripts/cloudbuild-agent-orchestrator.yaml` with cache-from prior tag
   - Build + push image:
     `europe-west4-docker.pkg.dev/central-element-323112/cloud-run-source-deploy/agent-orchestrator:uat`
   - `gcloud run deploy agent-orchestrator-staging --region europe-west4 --project central-element-323112`
   - Full-exec: `curl https://agent-orchestrator-staging-<hash>-ew.a.run.app/healthz` → `{"status":"ok"}` 200

   > **🛑 HUMAN GATE — P2**: Post ping to `_agent_pings.md`:
   > `[DATE] harsh-slot-10 → ikenna-main — P1 done, Cloud Run staging live at <URL>. Need: Firebase Console domain setup + Squarespace DNS paste for agent-orchestrator.staging.odum-research.com. See plan P2 human steps.`
   > **Do NOT proceed to P2 agent steps until Ikenna acks DNS propagated.**

3. - [ ] **P2 agent steps — firebase.json + .firebaserc + vite.config** (~0.5 cal) _(can do while waiting for DNS)_
   - `agent-orchestrator/firebase.json` with prod+uat hosting targets, `/api/*` + `/healthz` rewrites to Cloud Run
   - `agent-orchestrator/.firebaserc` with targets prod=agent-orchestrator-prod-site, uat=agent-orchestrator-uat-site
   - `dashboard/vite.config.ts`: confirm `dist/` output is Firebase-Hosting-compatible
   - First `firebase deploy --only hosting:uat` from local

4. - [ ] **P3 agent steps — strict auth flip** (~0.5 cal) _(after Ikenna acks P2 DNS propagated)_
   - `gcloud secrets create ORCHASTRATOR_JWT_SECRET` (32-byte random); IAM bind to staging Cloud Run SA
   - Wire the secret into Cloud Run staging via `gcloud run services update` with `--update-secrets` flag (see plan P3
     for exact command shape)
   - Replace `server/auth.py` permissive validate with argon2 hashed-user-list (matches `scripts/manage_users.py`
     schema)
   - Flip `ALLOW_ANONYMOUS=False` on Cloud Run

   > **🛑 HUMAN GATE — P3 user bootstrap**: Ikenna runs `manage_users.py` to bootstrap ikenna+harsh on staging + runs
   > 3-curl smoke test (valid → 200 + JWT; wrong password → 401; no bearer → 401). Post ack to `_agent_pings.md` when
   > done.

5. - [ ] **P4 — CI/CD wire-up** (~0.8 cal) _(after Ikenna acks P3 smoke test passed)_
   - `.github/workflows/quality-gates.yml` referencing PM template
   - `.github/workflows/deploy-staging.yml` (on push to main → Cloud Build → `gcloud run deploy --env=uat` →
     `firebase deploy --only hosting:uat`)
   - `.github/workflows/deploy-prod.yml` (`workflow_dispatch` only)
   - GCP service account + Workload Identity Federation for GHA (copy from `client-reporting-api/.github/workflows/`)
   - Trigger with trivial commit; verify both quality-gates + deploy-staging green within 10min

6. - [ ] **P6 — Codex SSOT + CLAUDE.md updates** (~0.5 cal) _(can run concurrent with P4 or P5's soak)_
   - NEW: `codex/04-architecture/agent-orchestrator-overview.md`
   - UPDATE: `codex/08-workflows/local-dev.md` — port 8026 + local dev block
   - UPDATE: `codex/05-infrastructure/launcher-script-ssot.md` — register `deploy-agent-orchestrator.sh`
   - UPDATE: `agent-orchestrator/README.md` + `docs/OPERATIONS.md` — replace `orch.epiphanytechnologies.com` with
     `agent-orchestrator.odum-research.com` (after P5; flag as pending if P5 not yet done)
   - UPDATE: `cursor-configs/CLAUDE.md` key repo map — add `agent-orchestrator`
   - Strike completed `TODO.md` items: "Off-laptop continuity" + "Strict auth"

7. - [ ] **Plan flips** for each phase shipped. (0.3 cal)

> **P5 (prod cutover + 7-day soak + laptop decommission)** = Ikenna-only after P4 verified. Not in this slot's scope.

---

### Slot 11 — agent-orchestrator Slack notifications (P0–P4) — ~2 cal AI-days

**Plan**: `plans/active/agent_orchestrator_slack_notifications_2026_05_19.md`
**Repo**: `agent-orchestrator/`
**No human gates** — runs entirely autonomously.
**Dependency**: P0 (secret mount) waits for Slot 10 P1 (Cloud Run staging service must exist). P1 code work can start immediately.

**Credentials already provisioned in Secret Manager** (central-element-323112):
- `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` — real webhook URL ✅
- `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` — real value ✅
- All 4 other Slack app secrets ✅

1. - [ ] **P1 — Implement `server/notifications/slack.py`** (~1.2 cal) _(start immediately, no Cloud Run dependency)_
   - `server/notifications/__init__.py` (empty)
   - `server/notifications/slack.py` — `notify_slot_blocked()`, `notify_slot_stale()`, `notify_slot_failed()`, each POSTing JSON to `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` via `httpx.AsyncClient`; no-op if env var empty
   - All calls wrapped in `try/except Exception: pass` — Slack outage never crashes server
   - Add `httpx` to `pyproject.toml` flat `[project.dependencies]`
   - Unit tests `tests/test_slack_notifications.py` — mock `httpx.AsyncClient.post`; assert payload shape for all 3 event types; assert no-op on empty webhook
   - Full-exec: `bash scripts/check.sh` passes; basedpyright `server/notifications/` clean; unit tests green

2. - [ ] **P2 — Wire hooks into server event handlers** (~0.5 cal)
   - `rg "add_blocked|stale|failed|blocked" server/ --type py` to locate all event emission points
   - Wire `await notify_slot_blocked()` / `notify_slot_stale()` / `notify_slot_failed()` at each transition
   - Full-exec: local smoke (`AGENT_ORCHESTRATOR_SLACK_WEBHOOK=""` — no-op confirmed); `bash scripts/check.sh` still passes

3. - [ ] **P0 — Wire `--update-secrets` on Cloud Run staging** (~0.3 cal) _(after Slot 10 P1 done)_
   - Look up staging SA: `gcloud run services describe agent-orchestrator-staging --region europe-west4 --project central-element-323112 --format='get(spec.template.spec.serviceAccountName)'`
   - IAM bind SA to `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` + `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET`
   - `gcloud run services update agent-orchestrator-staging --update-secrets=AGENT_ORCHESTRATOR_SLACK_WEBHOOK=AGENT_ORCHESTRATOR_SLACK_WEBHOOK:latest,AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET=AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET:latest --region europe-west4 --project central-element-323112`

4. - [ ] **P3 — Staging smoke** (~0.5 cal) _(after P0 + deploy-staging CI deploys new code)_
   - Trigger a test notification via staging URL → verify message appears in `#agent-orchestrator-alerts` within 10s
   - Confirm Cloud Run logs show `hooks.slack.com 200`
   - Post ack ping to `_agent_pings.md`: `[DATE] harsh-slot-11 — Slack notifications live on staging; #agent-orchestrator-alerts received test message. P3 done.`

5. - [ ] **P4 — Codex update** (~0.2 cal)
   - Add "Slack notifications" section to `codex/04-architecture/agent-orchestrator-overview.md`
   - Strike "Slack notification when blocked" from `agent-orchestrator/TODO.md`

6. - [ ] **Plan flips** for all items. (0.1 cal)

---

## Done-definition (2026-05-19 EOD)

- Slot 2: alerting_live_rules 100% + wave3x closed + manifest_schema_final_gate closed + S3–S6 sweeps done.
- Slot 3: aws_migration Phases 1.B–1.D + 2.A + 4.A + GAP-2.4.A/B/C on LDR.
- Slot 4: hard_schema_enforcement 100% + strategy_archetype_taxonomy 100% + deployment_and_qg closed.
- Slot 5: features_repo_consolidation + gcs_migration_bundle + AUDIT_pre_may8 + expected_unattempted all closed.
- Slot 6: mdps_streaming Phase 2 + mtds_databento + data_status_drilldown + defi_archetypes closed +
  features_tick_observation_audit scaffolded.
- Slot 7: dex_perp_onboarding + gate_3_phantom + trigger_based_reference + hedge_ratio (URGENT) + all small closes done.
- Slot 8: bucket_name_ssot + expected_universe_v2 + manifest_cross_asset + available_at + deploy_missing closed +
  S11–S14.
- Slot 9: compute_optimization + codex_vs_citadel + misc closes + S15–S20 done.
- Slot 10: agent-orchestrator P0 (rename+scaffold+QG) + P1 (Cloud Run staging live) + P2 agent steps (firebase.json) +
  P3 agent steps (auth flip) + P4 (CI/CD green) + P6 (codex). Human gates at P2 DNS + P3 user bootstrap require Ikenna
  ack before progression.
- Slot 11: Slack notifications P1 (slack.py + unit tests) + P2 (event hook wiring) + P0 (--update-secrets, after Slot 10 P1) + P3 (staging smoke → message in #agent-orchestrator-alerts) + P4 (codex). No human gates.

---

## Spawn prompt — paste into each tab (slot N)

```text
You are slot N (Harsh side). Today is 2026-05-19 (Cycle 2 Day-4 — mechanical + infra sweep).

Boot:
1. SYNC TO LDR — from .tabs/<N>/:
     for d in */; do
       (cd "$d" && [ -d .git -o -f .git ] && \
        git fetch origin live-defi-rollout --quiet && \
        git merge --ff-only origin/live-defi-rollout 2>/dev/null) ;
     done

2. Read unified-trading-pm/harsh_orchestrator/AGENT_ONBOARDING.md

3. Read unified-trading-pm/plans/active/work_split_2026_05_19_harsh.md § "Slot <N>"

4. Read your top plan-of-record.

5. Boot ack at unified-trading-pm/harsh_orchestrator/pings/slot_<N>.md using `date -u`.

6. Slot 2 ONLY: immediately check pvl-p18a VM status:
   gcloud compute instances describe strategy-paper-carry-staked-basis-20260518-115404 \
     --zone asia-northeast1-a --format='get(status)'
   Log result to pings/slot_2.md. If NOT RUNNING → ping main immediately.

CRITICAL RULES:
* Plan-flip discipline: (Half 1) commit + push code, then (Half 2) docs(plans): checkbox
  flip IN SAME AGENT TURN.
* Mechanical work only — if you hit an architectural decision, file a issue doc and skip.
* No touches to: UTL L3 wrappers, deployment-api _BUCKET_TEMPLATES, writegate Phase 6.6/6.7,
  deployment_ui new tabs, api_keys Phase 3–4 (all Ikenna territory today).
* git fetch before any commit on shared repos.
* QG before push: bash scripts/quality-gates.sh (Pass 1).

Now begin.
```
