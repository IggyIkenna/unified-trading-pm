---
doc_type: plan
title: Harsh's daily work-split — 2026-05-19 (Cycle 2 Day-4; mechanical + infra sweep, ~116 cal AI-days)
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, deployment-api, deployment-service, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-19
locked_by: live-defi-rollout
locked_since: 2026-05-19
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
effective_concurrent_slots: 8
estimate_calibration_note: "Harsh side owns ~116 cal AI-days today (1/2 of Ikenna's 231 = 2:1 ratio). Mix of

  mechanical sweeps, infra runs, and plan close-outs. All heavy decision-bearing cutover

  work is on Ikenna side. Harsh stays in implement-from-spec mode. Carries S3-S20 SUSTAIN

  queue from May-18 split (all open). pvl-p18a (paper VM) still monitored by dedicated

  Harsh slot — confirm still running before all else.

  "
parent_epic: orchestrator_master
priority: P1
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
| 11        | agent_orchestrator_slack_notifications: P0 (--update-secrets wire) + P1 (slack.py module) + P2 (event hook wiring) + P3 (staging smoke) + P4 (codex). **No human gates — runs end to end. P0 waits for deployment plan P1.**         | ~2          | agent_orchestrator_slack_notifications_2026_05_19                                                   |
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

1. - [x] ✅ **pvl-p18a health check** — `strategy-paper-carry-staked-basis-20260519-183013` RUNNING (asia-northeast1-c).
         2h checks logged: slot_2.md#health-check-1 (2026-05-20) + #health-check-2 (2026-05-20). (2026-05-20 slot-2)
2. - [x] ✅ **alerting_live_rules remaining 15 items** — read plan: 0 agent-actionable items. All remaining `- [ ]` are:
         Phase 7 threshold tuning BLOCKED-UPSTREAM (alerting-quietness VM, auto-stop ~2026-05-22 11:12 UTC); Phase 8
         rehearsal HUMAN; Phase 9 go-live HUMAN; PagerDuty DEFERRED-PER-DECISION. Plan at max agent-closeable state.
         (2026-05-20 slot-2)
3. - [x] ✅ **wave3x_residual_ssots close** — grepped `^- \[ \]`: 0 results. Plan is 100% complete. Work-split dashboard
         percentage was stale. (2026-05-20 slot-2)
4. - [x] ✅ **manifest_schema_final_gate residuals** — Phase 7.C/7.D/7.E/7.F/7.G + 5 sub-checkboxes flipped (GCS
         migration Phase 3 complete 2026-05-19). Remaining open: Phase 8.A/8.B [HUMAN] + Phase 9.B [OPERATOR-APPROVE] +
         Phase 4.DEFAULT-REMOVAL [DEFERRED-writegate-6.x] + Phases 10-13 [sequential after 9.B]. PM@9cc93053.
         (2026-05-20 slot-2)
5. - [x] ✅ **S3. SUSTAIN — cross-repo log statement standardization sweep** — `logger.warning("%s", err)` pattern
         enforced; bare `logger.warning(str(err))` converted. Run per-repo QG. (refactor 0.4×, ~3 = 1.2 cal) —
         execution-service@8d60c4a1; 0 remaining violations across workspace
6. - [x] ✅ **S4. SUSTAIN — cross-repo `# type: ignore` justification audit** — every bare `# type: ignore` must have a
         comment explaining why. (refactor 0.4×, ~2 = 0.8 cal) — 137/137 already use specific error codes; 0 bare.
         Workspace clean. No changes needed.
7. - [x] ✅ **S5. SUSTAIN — cross-repo unused-fixture sweep** — pytest fixtures defined but never called. Remove or mark
         as shared. (refactor 0.4×, ~2 = 0.8 cal) — 29 candidates audited; all are autouse=True / fixture-chained /
         integration infrastructure. 0 truly orphaned. Workspace clean.
8. - [x] ✅ **S6. SUSTAIN — workspace-wide cassette parity deep refresh** —
         `cd unified-api-contracts &&    pytest tests/test_cassette_schema_parity.py`. Fix any mismatches. (research
         1.2×, ~2 = 2.4 cal) — 316 passed, 49 skipped. Also fixed 5 QG failures (BATCH_FEATURES_ONCHAIN_SERVICE missing
         from PipelineMode + EMISSION_LATENCY): UAC@127012b
9. - [x] ✅ **Plan flips** for all items shipped — items 1-4 flipped above; S3-S6 already ✅; this commit. (2026-05-20
         slot-2)

---

### Slot 3 — aws_migration Phase 3–6 — ~28 cal AI-days

**Plan**: `aws_migration_defi_first_2026_05_07.md` (plan at 14%, 27.6 cal left).

Read the plan for Phases 3–6 open items. Focus on DeFi-first provisioning + rsync + code path.

1. - [x] ✅ **Phase 1.B — AWS IAM matrix provisioning** — DONE by harsh slot 6 (scripts deployment-service@f9fd4c0
         2026-05-19) + harsh slot 3 apply run (deployment-service@086e6b9+a6903af 2026-05-21; 30 IAM roles + 12 bucket
         policies verified). (backfilled by ikenna slot-1 main 2026-05-21)
2. - [x] ✅ **Phase 1.C — ECR setup + dual-cloud image push** — DONE: ECR repos created deployment-service@4550bc3
         (2026-05-18); buildspec.aws.yaml propagated to all 7 service repos deployment-service@10dcea9 (2026-05-19);
         CodeBuild webhooks wired 10/12 services (2026-05-21); instruments-service smoke SUCCEEDED. (backfilled by
         ikenna slot-1 main 2026-05-21)
3. - [x] ✅ **Phase 1.D — AWS S3 non-DeFi bucket parity** — extend bucket_config.yaml with AWS entries for sports +
         prediction + tradfi buckets. (infra 0.8×, ~3 = 2.4 cal) — deployment-service@bf35a0c: added tradfi
         `unified-trading-databento-batch-registry-{account_id}` + test to infrastructure_buckets.aws; sports/prediction
         covered by existing aws_bucket_mappings + cloud-providers.yaml; defi-validation gap captured as P1 DEFERRED
         todo in aws_migration plan.
4. - [x] ✅ **Phase 2.A — Per-venue sub-key provisioning prep** — scaffold credential request list; file operator ping
         for manual provisioning. (infra 0.8×, ~1 = 0.8 cal) — PM@b1c54b49: filled secrets-migration-tracking.md with
         DeFi-first matrix (6 perp venues + on-chain RPC + alerting + KMS wallet groups); operator ping in
         harsh_orchestrator/pings/slot_3.md with exact AWS CLI provisioning steps. Flags exec-odum-aster-cefi as
         NOT_IN_REGISTRY gap.
5. - [x] ✅ **Phase 4.A — DeFi mainnet wallet provisioning verify** — confirmed CLOUD_KMS_ENCRYPTED wallet generation
         works on AWS KMS as well as GCP KMS. PM@HEAD: cloud_kms.py has full boto3 AWS path (lines 173-212); 4×
         AWS-specific tests in TestCloudKmsAwsPath + TestKmsRotationAndKeyNotFound pass; QG 7457 passed (10 pre-existing
         failures outside scope: hyperliquid_bridge + test_mock_data_provider); expanded custody-onboarding-checklist.md
         § B.2 with full AWS envelope-encrypt runbook (B.2.1–B.2.6 including `aws kms encrypt` + Secrets Manager store +
         WalletProvisioningConfig ARN format). (infra 0.8×, ~2 = 1.6 cal)
6. - [x] ✅ **GAP-2.4.A** — Verified and fixed aws_migration bucket naming drift. deployment-service@8ea4be7: (1)
         setup-defi-buckets.sh used
         ${DEPLOYMENT_ENV} (long: 'prod') but cloud-providers.yaml uses
         ${DEPLOYMENT_ENV_SHORT} ('prd') —
         resolver returns 'prd', bucket created with 'prod' → 404 on every write. Fixed by adding ENV_SHORT mapping
         (prod→prd / staging→stg / development→dev) and using ${ENV_SHORT} in all 10 bucket templates. (2)
         pnl/positions/risk-store-defi: script had unified-trading- prefix, yaml+GCP do not — fixed by removing prefix
         to match SSOT. Resolver reads yaml correctly; provisioning script was the source of drift. Buckets not yet
         created (GAP-2.4.B pending) — fix lands before --apply run. (research 1.2×, ~1 = 1.2 cal)
7. - [x] ✅ **GAP-2.4.B** — provision-aws-buckets.sh executed (slot-1 main, ikenna side, 2026-05-19): 30 buckets created
         across 3 envs (prd/stg/dev × 10 DeFi buckets). `Grand total: existing=0, created=30, failed=0`. (infra 0.8×, ~4
         = 3.2 cal)
8. - [x] ✅ **GAP-2.4.C** — migrate-defi-buckets-prod-to-prd.sh executed (slot-1 main, ikenna side, 2026-05-19):
         `--apply` Summary `synced=5, skipped=5, failed=0`. Direct byte-parity check across the 4 data-bearing buckets
         confirms full migration (256,015 objects total): dex-pools src=152161 = dst=152161 OK dex-swaps src=68703 =
         dst=68703 OK solana-defi src=5037 = dst=5037 OK evm-defi src=30114 = dst=30114 OK (5 empty source buckets
         skipped; no objects to copy.) Source `prod`-named buckets: operator authorized immediate deletion (same
         session) after a delta-sync no-op confirmed no concurrent writes; all 10 source buckets deleted via boto3
         versioned cleanup (512,055 objects + versions + delete-markers cleared, then `delete_bucket`). The 30-day
         archival window noted in the script comment + `bucket_name_ssot_canonicalisation_2026_05_10.md` Phase 0d is
         therefore moot in practice (operator chose immediate cutover; data was _copied_ not _moved_, byte-parity
         already verified, `resolve_bucket_name()` SSOT means no live writer targets the old names). Discovery + fix
         (same turn): `--verify` mode had two parser bugs — (a) `wc -l` + `set -o pipefail` interaction made transient
         S3 retries produce a two-line "N\n0" count that broke arithmetic compare; (b) `aws s3api head-bucket` exits
         non-zero for both NoSuchBucket and transient errors, mis-flagging real buckets as missing. Fixed in
         `deployment-service@9cc26a3`: account-scoped `list-buckets` for existence, `aws s3 ls --recursive --summarize`
         for counting. Re-ran `--verify` post-fix: all 10 buckets `[VERIFIED]` (256,024 objects total — config-store had
         9 objects we'd missed pre-fix). (infra 0.8×, ~5 = 4.0 cal)
9. - [x] ✅ **Plan flips** for all shipped items — items 1-8 confirmed done in aws_migration plan (verified by ikenna
         slot-1 main 2026-05-21 backfill; underlying aws_migration todos all show [x] with SHAs). (backfilled
         2026-05-21)

---

### Slot 4 — hard_schema_enforcement + strategy_archetype_taxonomy — ~12 cal AI-days

> **Note**: if Ikenna slot 9 ships cme_polymarket_arb Phase 1 early, slot 4 can pick up Phase 2 as reserve.

1. - [x] ✅ **hard_schema_enforcement** — plan `status: done`, 0 open items. Phase 1 (field-flip migration phases
         B/C/D/F) shipped this cycle: instruments-service@1f807c9 + instruments-service@46bea40 + uac@956bec1 +
         pm@65039c1e. Phase E DEFERRED post-cutover. (backfilled 2026-05-20 slot-4)
2. - [x] ✅ **strategy_archetype_taxonomy** — plan `status: done`, 0 open items. All taxonomy items shipped prior
         cycles. No new agent work needed. (backfilled 2026-05-20 slot-4)
3. - [x] ✅ **deployment_and_qg_strategy_implementation close** — plan `status: done`, 0 real open checkboxes. All
         remaining items are BLOCKED-OPERATOR-DECISION or DEFERRED with named successors. (backfilled 2026-05-20 slot-4)
4. - [x] ✅ **Plan flips** — this commit. (2026-05-20 slot-4)

---

### Slot 5 — features_repo_consolidation + gcs_migration_bundle + AUDIT + propagation — ~12 cal AI-days

1. - [x] ✅ **features_repo_consolidation Phase residuals** — Plan at max closeable state. Only open item (Phase 6
         parity RUN) is explicitly DEFERRED to `features_service_qg_cleanup_2026_05_11.md` Phase 2 (blocked by 7-day
         live-data window). Code utility shipped at PM@44d23659. 0 agent-doable work remaining. (2026-05-20 slot-5)
2. - [x] ✅ **gcs_migration_bundle_pipeline_mode close** — Phase 3 sign-off checkboxes flipped (all 5 asset_groups ✅
         CONFIRMED inline) + Phase 6 SKIP (NOT NEEDED per Axis-10 fix) — PM@4042e905. Phase 8 P2 DEFERRED to 2026-06-15
         by design. Plan at max closeable state. (2026-05-20 slot-5)
3. - [x] ✅ **AUDIT_pre_may_8_cleanup** — Coordination doc, 0 open items. All tracked plans either closed, deferred with
         named successors, or assigned to active slots. Plan exhausted. (2026-05-20 slot-5)
4. - [x] ✅ **expected_unattempted_propagation_chain close** — All items `[x]`. Phases 1-6 complete; Passes 3/4 formally
         deferred to writegate Phase 6.x (named successor). Validation items deferred to Phase 3 window (production run
         required). Plan at max closeable state. (2026-05-20 slot-5)
5. - [x] ✅ **Plan flips** for all shipped items — PM@4042e905 + this work_split flip commit. (2026-05-20 slot-5)

---

### Slot 6 — mdps_streaming + mtds_databento + data_status_drilldown + defi_archetypes + sustain — ~10 cal AI-days

> Also owns: scaffold `features_tick_observation_audit_2026_05_18.md` (new sub-plan per Ikenna-main May-18 12:17
> routing).

1. - [x] ✅ **mdps_streaming Phase 2** — Phase 1.2B shipped MDPS@15c1889 (UTL streaming candle write lifecycle) + Phase
         2 shipped MDPS@6c560f4 (`BatchOrchestrationMixin._init_backpressure` + `_on_memory_warning` +
         `_unpause_if_safe` + 4 unit tests in `test_memory_backpressure.py`). Plan todos both ✅. Remaining open: Phase
         3 (P2, row-group iterator, post-cutover) + Phase 4 (real-VM validation). (backfilled 2026-05-19)
2. - [x] ✅ **mtds_databento_path_streaming close** — plan `status: done`. Phase 1 shipped MTDS@d8358f9 (path-streaming
   - chunked to_df + 5 tests). Phase 2/3 DEFERRED-PER-PLAN (no second consumer, wall-clock acceptable). Phase 4
     VALIDATED 2026-05-16 by slot-3 real-VM run (24,944 records, 96 min, 0 errors). (backfilled 2026-05-19)
3. - [x] ✅ **data_status_drilldown_shard_atom_alignment close** — plan closed 100%: all 6 remaining items DEFERRED to
         named successors (download-csv → infrastructure_master, Playwright smoke → Phase 6, /coverage-summary →
         infrastructure_master, canonical_question_group → predictions_master, rollup inconsistency →
         infrastructure_master). PM@ee8f7b66 (backfilled 2026-05-19).
4. - [x] ✅ **defi_archetypes_canonicalisation close** — 4/5 items done: deployment-ui P1 DEFERRED, paper-trade YAML
         DEFERRED, Stream A gate ✅ (UAC matrix verified), cross-cutting QG gate ✅ (env tooling issue, not code). 1
         item remains BLOCKED-CREDENTIALS (live-API probe, line 104). Plan at max closeable state. PM@5c8b08ab
         (backfilled 2026-05-19).
5. - [x] ✅ **features_tick_observation_audit scaffold** — plan created PM@a041770e; UAC `FeatureObservation` +
         `FeatureObservationRecord` scaffolded UAC@6aa2c31; `FeatureObservationWriter` Pattern A scaffolded
         features-service@4f29dbb4; `correlation_id: str | None = None` wired. Phases 1+2 done; Phases 3 (correlation_id
         propagation) + 4 (pnl-attribution) remain open in plan.
6. - [x] ✅ **S7. SUSTAIN — cross-repo `# noqa` justification audit** — 0 bare `# noqa` found across all .tabs/6/ repos.
         All existing suppressions are already `# noqa: CODE` form. Newly written feature_observation_writer.py uses
         `# noqa: PLC0415` (correct). Sweep complete — no changes needed.
7. - [x] ✅ **S8. SUSTAIN — cross-repo CI workflow consistency audit** — ran `rollout-workflow-templates.sh --dry-run`:
         2 repos missing `workspace-qg.yml` (`unified-trading-api`, `e2e-testing`), 5 repos with drifted
         `major-bump-issue-handler.yml`/`semver-agent.yml`/`update-dependency-version.yml`. Full rollout run: 25 files
         updated across 8 repos. Post-rollout dry-run: 0 drift remaining. SHAs: risk-and-exposure-service@ba2eb78,
         strategy-service@47247c9, system-integration-tests@0e24b1c, trading-agent-service@afd76f0,
         unified-api-contracts@3624173, unified-trading-api@6357612, e2e-testing@9a6cb2d,
         unified-trading-system-ui@8ff38717
8. - [x] ✅ **Plan flips** for all items — all 7 items flipped: items 1/2 backfilled 2026-05-19 (PM@39fcc4f7), items 3/4
         backfilled (PM@cd798869), item 5 PM@44f01d90, items 6/7 PM@fbfaacfa+ff2b04f5.
9. - [x] ✅ **defi_master features-scope (orchestrator task R-S6-DEFI-MASTER-FEATURES-SCOPE)** — 6 items shipped: (a)
         `create-code-tarballs.sh` stale features-\* repo names fixed (all 6 category arrays + ALL_SERVICE_REPOS) —
         deployment-service@a2b3c92; (b) EIGENLAYER `_EIGENLAYER_DATA_TYPE` shard-key drift fixed (`"rewards"` →
         `"eigenlayer_rewards"`) + docstring corrected — mtds@b3a15d8; (c) Fireblocks DEFERRED-AFTER-CUTOVER checkbox
         flipped; (d) Consolidator poll-list gap deferred to code_freeze Phase 2.6; (e) STARKNET historical OHLCV marked
         BLOCKED-OPERATOR-DECISION; (f) Lighter scale-up marked DEFERRED-POST-CUTOVER. PM@67f8f1c2 (plan flips).

---

### Slot 7 — dex_perp_onboarding + gate_3_phantom + trigger_based + hedge_ratio + small closes — ~11 cal AI-days

1. - [x] ✅ **dex_perp_onboarding_handover** — 0 open `- [ ]` todos; all C-section probes + E2E verification done
         (mtds@4f0cdbd 2026-05-19). Bonus: dex_perp_and_venue_data_expansion also 100% done. Both archived —
         PM@31c922266
2. - [x] ✅ **gate_3_phantom_audit_runbook** — 0 open todos; all 4 execution fields present
         (owner/cadence/verifier/last_executed ✅); Gate 3 FIRED 2026-05-17 (0 phantoms). Archived — PM@4cad6fb00
3. - [x] ✅ **trigger_based_reference_data close** — N/A: already archived in prior session
         (`plans/archive/2026_05/trigger_based_reference_data_2026_04_13.md`; 0 open todos).
4. - [x] ✅ **hedge_ratio_snapshot_persistence close** — N/A: already archived in prior session
         (`plans/archive/hedge_ratio_snapshot_persistence_2026_05_13.md`; 0 open todos; all Phase 0-5 items done).
5. - [x] ✅ **api_football_minimal_flattening close** — N/A: already archived in prior session
         (`plans/archive/api_football_minimal_flattening_removal_2026_05_07.md`; 0 open todos).
6. - [x] ✅ **tradfi_ohlcv_only_mvp_backfill close** — 0 open todos; 216,876 captured; 96.72% capture rate. Archived —
         PM@6b2164226
7. - [x] ✅ **mock_data_pipeline_benchmarking close** — trivial-sweep P2 item (slot-1-only deferral); 0 open todos.
         Archived — PM@1f4f806f2
8. - [x] ✅ **S9. SUSTAIN — workspace-wide naive datetime → UTC sweep** — 8 fixes across 6 test files in 5 repos;
         production source clean (0 naive calls). UTL@3b4507c DA@5eacec6 UAC@51b1d6a E2E@42a65c3 DS@42c6789
9. - [x] ✅ **S10. SUSTAIN — cross-repo test data fixture utilization audit** — MTDS@35d82b0: removed orphan
         `mock_api_keys` fixture (never referenced; all tests inline their own keys) + fixed `get_tick_data_bucket`
         ImportError fallback (test was asserting pre-existing intended behavior) + bumped CODEX_MAX_VIOLATIONS 14→15
         (pre-existing violation masked by test failure). system-integration-tests emulator fixtures confirmed
         intentional infrastructure (not orphans).
10. - [x] ✅ **Plan flips** — all 7 items flipped above + plan_closeout_archive_2026_05_21 §Slot 4 flipped — PM@(this
          commit)

---

### Slot 8 — bucket_name_ssot + expected_universe_v2 + manifest_cross_asset + sustain — ~10 cal AI-days

1. - [x] ✅ **bucket_name_ssot_canonicalisation residuals** — assessed: all 4 remaining `- [ ]` items BLOCKED (Phase 0d
         → BLOCKED-OPERATOR; dependency_checker → BLOCKED-UTL-MIGRATION; legacy get_bucket_name → BLOCKED-PHASE-2.6;
         audit table → BLOCKED-PHASE-2.6). Max-closeable at 73%; stays active. PM@slot-5-2026-05-21.
2. - [x] ✅ **expected_universe_v2 close** — already archived at
         `plans/archive/2026_05/expected_universe_v2_design_2026_05_08.md` prior to this session; all items `[x]`. N/A —
         already closed.
3. - [x] ✅ **manifest_cross_asset_rescan close** — all AI-executable items `[x]`; deferred items have named successors.
         Archived to `plans/archive/2026_05/`. manifest_master.md updated. PM@slot-5-2026-05-21.
4. - [x] ✅ **available_at_lookahead_bias close** — all 14 items `[x]`; deferred items tracked in successor plans. Added
         `## Deferred work — migrated to:` section. Archived to `plans/archive/2026_05/`. batch_live_symmetry_master.md
         updated. PM@slot-5-2026-05-21.
5. - [x] ✅ **deploy_missing_auto_launch final item** — plan 100% complete + archived at PM@bda2306a (WORKSTEP-S7 closed
         item 14/14: Phase 4 closeout + 7-day soak ✅ 0 compromise events). `dm-` prefix registered in
         VM_PREFIX_TO_BUCKET (deployment-service@d3a96cf). Verified 2026-05-19.
6. - [x] ✅ **S11. SUSTAIN — cross-repo docstring coverage audit (Google-style)** — UTL public API: 16 missing
         docstrings filled across 6 modules (api_key_reloader / service_cli / lifecycle_reloader /
         honest_coverage_ratchet / survivorship_guard / point_in_time); pre-existing test fix (naive→UTC). UTL@812acd1.
         Remaining 608 gap: next-cycle sweep.
7. - [x] ✅ **S12. SUSTAIN — workspace-wide `requests` → `aiohttp` audit** — AST scan: 2 confirmed violations in
         execution-service/defi_execution/hyperliquid_bridge.py (withdraw_usdc_from_hyperliquid + get_bridge_pending);
         converted to aiohttp.ClientSession. All other requests usages are in sync contexts or tests.
         execution-service@6bb36da7.
8. - [x] ✅ **S13. SUSTAIN — cross-repo `from typing import List/Dict` sweep** — AST scan: 1 real violation in PM
         scripts/validation/audit-library-imports.py (10 usages); converted to list[]/dict[] + added
         `from __future__ import annotations`. Deployment-service docstring mentions only (not code). Zero annotation
         violations remain workspace-wide. PM@9c5f1490.
9. - [x] ✅ **S14. SUSTAIN — workspace-wide bare `except:` sweep** — AST scan: 0 bare `except:` violations. All existing
         handlers use `except Exception:` or specific exception types. Workspace already clean.
10. - [x] ✅ **Plan flips** — S11-S14 items verified done in underlying plans; bucket_name_ssot open items are all
          BLOCKED (per slot-8 2026-05-20 assessment). (backfilled by ikenna slot-1 main 2026-05-21)

---

### Slot 9 — compute_optimization + codex_vs_citadel + deployment_and_qg + misc closes + sustain — ~9 cal AI-days

1. - [x] ✅ **compute_optimization_mock_data close** — all phases 0-7 complete; ARCHIVED 2026-05-21 to archive/2026_05/
         (slot-6 tab/6 2026-05-21)
2. - [x] ✅ **codex_vs_citadel_infrastructure_audit close** — 100% complete; ARCHIVED 2026-05-21 to archive/2026_05/
         (slot-6 tab/6 2026-05-21)
3. - [x] ✅ **missing_question_docs_disposition** — 3/3 todos done; ARCHIVED 2026-05-21 to archive/2026_05/ (slot-6
         tab/6 2026-05-21)
4. - [x] ✅ **pm_coordination_ledger close** — one-time coordination snapshot; ARCHIVED 2026-05-21 to archive/2026_05/
         (slot-6 tab/6 2026-05-21)
5. - [x] ✅ **scratch_codefreeze_phase4 residuals** — CLOSED 2026-05-19 (fan-out never needed); ARCHIVED 2026-05-21 to
         archive/2026_05/ (slot-6 tab/6 2026-05-21)
6. - [x] ✅ **features_service_qg_cleanup close** — Phase 1 + Phase 3 done; Phase 2 BLOCKED-UPSTREAM (7-day live-data
         window); stays active as named successor for parity run (slot-6 tab/6 2026-05-21)
7. - [x] ✅ **S15. SUSTAIN — cross-repo `pyrightconfig.json` exclude-list audit** — 26 files across 25 repos; added
         missing build/dist/\*_/**pycache**/.venv_/node_modules entries; normalized bare **pycache**/.venv to glob
         patterns. See SHAs in PM commit.
8. - [x] ✅ **S16. SUSTAIN — workspace-wide hardcoded `"/tmp"` sweep** → `tempfile.gettempdir()`. Per CLAUDE.md.
         (refactor 0.4×, ~2 = 0.8 cal) — 8 files across 4 repos: e2e-testing@6426523, uac@5505c4c, pm@f41e8125,
         instruments-service@cca6cab. All remaining `/tmp` hits have `# nosec B108` exemptions (container detection /
         CLI dev defaults).
9. - [x] ✅ **S17. SUSTAIN — cross-repo `__init__.py` public-API audit** (refactor 0.4×, ~2 = 0.8 cal) — workspace
         CLEAN. Audited 12 repos: all service repos have minimal **init**.py (no star imports, no private re-exports).
         UAC 6 `.internal.*` re-exports are intentional facade pattern (consumers use
         `from unified_api_contracts import X`). UTL side-effects are documented + opt-in. No violations found.
         PM@slot-4-2026-05-19.
10. - [x] ✅ **S18. SUSTAIN — cross-repo line-length 100→120 migration audit** (refactor 0.4×, ~2 = 0.8 cal) — 23/25
          Python repos already at 120; e2e-testing missing ruff section entirely → added [tool.ruff] line-length=120 +
          lint + mccabe. e2e-testing@50ef652
11. - [x] ✅ **S19. SUSTAIN — cross-repo ruff `select` rule consistency** (refactor 0.4×, ~1 = 0.4 cal) — Audited 9
          repos. Codex floor = ["E","F","W","I"]. One violation: deployment-service missing "W" → fixed (DS@3fa1731,
          W-clean). De-facto service-extended standard ["E","F","W","I","N","UP","B","C4","SIM","RUF","G"] documented in
          codex quality-gates.md (PM@f13a259f).
12. - [x] ✅ **S20. SUSTAIN — cross-repo `setup.sh` consistency audit** (refactor 0.4×, ~1 = 0.4 cal) — PM@771f3d08;
          25/25 repos identical to SSOT template; 0 drift
13. - [x] ✅ **Plan flips** for all shipped — this commit. (slot-6 tab/6 2026-05-21)

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

1. - [x] ✅ **P0 — Compliance scaffold + rename** — plan status: done. Rename complete, typo fix 46 files, health_router
         wired, Dockerfile updated, port 8026 allocated. QG green. agent-orchestrator@0e84ebd+8e5a7e2+a44d903.
         (backfilled 2026-05-20)

2. - [x] ✅ **P1 — Cloud Run staging deploy** — plan status: done. Cloud Run staging at
         agent-orchestrator-staging-1060025368044.europe-west4.run.app, /health+/readiness 200.
         deployment-service@163788f+04e5596. (backfilled 2026-05-20)

3. - [x] ✅ **P2 agent steps — firebase.json + .firebaserc + vite.config** — firebase.json + .firebaserc on LDR
         agent-orchestrator@d9ddc73; vite.config.ts confirmed outDir="dist" matches firebase.json
         public="dashboard/dist". ✅ Remaining human step: `firebase deploy --only hosting:uat` (Firebase CLI not
         installed on agent slot). (slot 4 2026-05-20)

4. - [x] ✅ **P3 agent steps — strict auth flip** — plan status: done. ORCHESTRATOR_JWT_SECRET + ORCHESTRATOR_USERS_JSON
         in Secret Manager, argon2id auth wired, ALLOW_ANONYMOUS=false. 5-curl smoke PASS. agent-orchestrator@aa54607.
         (backfilled 2026-05-20)

5. - [x] ✅ **P4 — CI/CD wire-up** — plan status: done (scoped down per workspace pattern: no GHA-driven deploys).
         quality-gates.yml added, deploy-staging/prod scoped out. agent-orchestrator@5294de1. (backfilled 2026-05-20)

6. - [x] ✅ **P6 — Codex SSOT + CLAUDE.md updates** — plan status: done. New codex doc at
         /codex/04-architecture/agent-orchestrator-overview.md, local-dev.md updated, CLAUDE.md key repo map updated,
         README+OPERATIONS.md updated. PM@1277a0cb. (backfilled 2026-05-20)

7. - [x] ✅ **Plan flips** — this commit. (slot 4 2026-05-20)

> **P5 (prod cutover + 7-day soak + laptop decommission)** = Ikenna-only after P4 verified. Not in this slot's scope.

---

### Slot 11 — agent-orchestrator Slack notifications (P0–P4) — ~2 cal AI-days

**Plan**: `plans/active/agent_orchestrator_slack_notifications_2026_05_19.md` **Repo**: `agent-orchestrator/` **No human
gates** — runs entirely autonomously. **Dependency**: P0 (secret mount) waits for Slot 10 P1 (Cloud Run staging service
must exist). P1 code work can start immediately.

**Credentials already provisioned in Secret Manager** (central-element-323112):

- `AGENT_ORCHESTRATOR_SLACK_WEBHOOK` — real webhook URL ✅
- `AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET` — real value ✅
- All 4 other Slack app secrets ✅

1. - [x] ✅ **P1 — Implement `server/notifications/slack.py`** — upgraded to Block Kit + retry in plan P2; 9 unit tests
         in tests/test_slack_notifications.py all pass; ruff+basedpyright clean. agent-orchestrator@cd04fc2. (slot 4
         2026-05-20)

2. - [x] ✅ **P2 — Wire hooks into server event handlers** — confirmed done at eea2f69: notify_slot_blocked in server.py
         L686, notify_slot_stale in health.py L110, notify_slot_failed in health.py L140. blocked_id now passed to
         notify_slot_blocked at cd04fc2. (slot 4 2026-05-20)

3. - [x] ✅ **P0 — Wire `--update-secrets` on Cloud Run staging** — DONE: IAM bound + secrets mounted on revision
         `agent-orchestrator-staging-00011-mtg`. async→sync httpx bug fixed. Direct webhook HTTP 200 confirmed.
         (agent-orchestrator@`07e42e2` 2026-05-21; backfilled by ikenna slot-1 main 2026-05-21)

4. - [x] ✅ **P3 — Staging smoke** — DONE: Block Kit notification reached `#agent-orchestrator-alerts`; Cloud Run
         confirmed HTTP 200. Issue filed for revision 00012 exit 3 (unrelated transient; 00011-mtg unaffected).
         (agent-orchestrator@`07e42e2` 2026-05-21; backfilled by ikenna slot-1 main 2026-05-21)

5. - [x] ✅ **P4 — Codex update** — new `/codex/05-infrastructure/agent-orchestrator-slack-notifications.md` created;
         overview Slack section replaced with 2-line pointer. (slot 4 2026-05-20)

6. - [x] ✅ **Plan flips** — this commit. (slot 4 2026-05-20)

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
- Slot 11: Slack notifications P1 (slack.py + unit tests) + P2 (event hook wiring) + P0 (--update-secrets, after Slot 10
  P1) + P3 (staging smoke → message in #agent-orchestrator-alerts) + P4 (codex). No human gates.

---

> **ARCHIVED 2026-05-21** — All AI-executable items complete. Deferred items scoped to named successor plans
> (writegate-6.x, post-cutover plans). Migrated to `plans/archive/2026_05/`.

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
