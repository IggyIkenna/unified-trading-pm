---
title: Harsh's daily work-split — 2026-05-08 (15 days to live-DeFi)
type: coordination-doc
status: active
created: 2026-05-08
deadline: 2026-05-23 (live DeFi)
horizon: 1-day cycle (rolls forward EOD)
companion_to: plans/active/work_split_2026_05_08_ikenna.md
locked_by: live-defi-rollout
locked_since: 2026-05-08
---

# Harsh's daily work-split — 2026-05-08

> **Companion**: [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md). Cross-side handshakes appear in
> both plans (mirror-image entries). The other side's plan is read-only for you.
>
> **Methodology**: see [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process" for the
> full spec — split principle, working models, universal mechanics. This doc is today's specific load-balancing; the
> spec is the durable rules.

## Why this split exists today

- **15 days to live-DeFi cutover** (2026-05-23). Master plan
  [`master_to_live_defi_2026_05_23`](master_to_live_defi_2026_05_23.plan.md) Group F + G are the gating ladder.
  Harsh-side absorbs the implement-from-spec / mechanical / parallel-safe / single-repo-edits / test-execution /
  launch-verify work that doesn't require cross-cutting design judgment.
- **Yesterday's Harsh orchestration ledger finished** with 12 spawned tabs ✅ DONE (Tabs 3-14): deployment-api Phase 2
  endpoints, deploy-missing Phase 1 tarball-refresh, lending-indices Bug 1+2+3 fixes (Tab 5), defi-988 audit,
  mtds-databento path-streaming Phase 1, audit_followups, lending-indices VM relaunch validation, predictions Phase 1
  ingestion, launcher consolidation 10 of 30, ml-features-phase2a (deferred per Tab 12 Q1), deploy-missing IAM proposal
  draft, defi-fork1-prep audit (13 of 17 UAC drift pairs flagged). Only Tab 2 (cefi-babysit) still IN FLIGHT — sweeps
  continuing, drain ETA tomorrow.
- **Carryover into today**: cefi VM drain monitor, cross-asset manifest rescan post-drain, TradFi MDPS post-drain
  cluster validation, sports per-source reconciler hook + features_sports_reconcile_available_at hook, defi_988 13,632
  actionable rows targeted backfill, predictions Phase 2+3 (after Tab 12 Q1 deferred), deployment-ui lifecycle tabs,
  ml/features parquet column-pruning + 8-service LookaheadBiasError wires (per resolved Tab 12 Q1 decision: absorbed
  into features_repo_consolidation), launcher consolidation remaining 20 of 30, hard_schema enforcement Phase 1-5,
  mtds_databento path-streaming Phases 2-4, mtds_per_instrument_download_api Phase 1.5,
  api_football_minimal_flattening_removal, cme_polymarket_arb, data_status_comprehensive_test_coverage.
- **Ping ledger (overnight)**: empty after rebase. `ml-features-phase2a-tab` Q1 ESCALATED-TO-OPERATOR was resolved this
  morning (operator picked option (b) — defer to features_repo_consolidation absorption). Beef-up sub-agent BLOCKED ping
  resolved via fast-forward rebase.

## Working model

**Model A — fixed thematic 5-tab clustering**, but with a pre-baked option to switch to Model B (1 main + dynamic
spawned tabs) mid-cycle if more items emerge from incoming pings or audit findings. Yesterday Harsh ran Model B (12
spawned tabs by EOD); today Model A is the starting shape because the carryover items cluster cleanly into 5 themes. If
Harsh prefers Model B's flexibility, treat the 5 tabs below as the day's initial scope and spawn additional tabs as work
clarifies — same universal mechanics either way.

## Coverage guarantee — 5 tabs absorb today's Harsh-side scope

| Source                                                                      | Item                                                                                                                                | Tab |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- | --- |
| `instruments_live_master_2026_05_08`                                        | Phase A-E live activation across all 5 asset_groups (Cloud Scheduler + audit jobs + UI tab integration)                             | 1   |
| `predictions_master_2026_05_07`                                             | Phase 2 lifecycle gating MTDS Polymarket/Kalshi adapter + UMI tick provider data_type rename                                        | 1   |
| `predictions_master_2026_05_07`                                             | Phase 3 reader / feature / strategy consumer migration to canonical_question_group                                                  | 1   |
| `instruments_and_market_tick_data_completion_2026_05_01`                    | Per-asset_group instrument lifecycle floor handling + catalog-aware writer-guard                                                    | 1   |
| `features_repo_consolidation_2026_05_08`                                    | Phase 0-3 (deadline 2026-05-13): pre-audit + scaffold consolidated repo + sub-package extraction + import-rewrite                   | 2   |
| `features_repo_consolidation_2026_05_08`                                    | Phase 4-7: per-source consumer migration + feature_family UAC column + deprecation banners + delete-source-repos commit             | 2   |
| `ml_and_features_master_2026_05_07`                                         | Phase 2A + 2B 8-service `assert_no_lookahead_for_feature_group` wires (resolved Tab 12 Q1: absorb into features_repo_consolidation) | 2   |
| `ml_and_features_master_2026_05_07`                                         | Phase 3 parquet column-pruning quick-win (1-3 day pure-win, self-contained)                                                         | 2   |
| `deployment_ui_lifecycle_tabs_2026_05_08`                                   | Phase A UAC SSOT for lifecycle column + Phase B UI re-shape (4 tab refactors)                                                       | 3   |
| `deployment_ui_lifecycle_tabs_2026_05_08`                                   | Phase C cloud-toggle + Phase D auth flow + Phase E env-resolution                                                                   | 3   |
| `deploy_missing_auto_launch_2026_05_07`                                     | Phase 1 tarball-refresh follow-on + Phase 2 auto-launch endpoint (after Ikenna Tab 5 ships IAM decision)                            | 3   |
| `cefi_master_2026_05_07`                                                    | Day-3 OPS babysit of remaining cefi VMs + drain reporting; TradFi MDPS post-drain ES.OPT 11-cluster validation                      | 4   |
| `manifest_migration_master_2026_05_07`                                      | Stage 4 cross-asset manifest rescan post-CeFi drain (mechanical operation; Ikenna Tab 3 designs the schema flip)                    | 4   |
| `sports_master_2026_05_07`                                                  | Per-source reconciler hook + features_sports_reconcile_available_at hook into per-source backfill VM exit-step                      | 4   |
| `defi_master_2026_05_07` + `issues/defi_988_missing_dates_audit_2026_05_08` | Targeted backfill of 13,632 actionable rows from Tab 6 audit (top-5 priority list)                                                  | 4   |
| `launcher_scripts_consolidation_into_deployment_service_2026_05_07`         | Migrate remaining 20 of 30 ad-hoc launchers into deployment-service/scripts/vm/                                                     | 5   |
| `data_status_comprehensive_test_coverage_2026_05_07`                        | All 30 todos: 5 test categories × 6 repos                                                                                           | 5   |
| `mtds_databento_path_streaming_2026_05_07`                                  | Phases 2-4 (chunked streaming + memory profiler + smoke fixtures)                                                                   | 5   |
| `mtds_per_instrument_download_api_2026_04_24`                               | Phase 1.5 chain axis (audit named CRITICAL-PATH)                                                                                    | 5   |
| `hard_schema_enforcement_2026_05_08`                                        | Phases 1-5 mechanical migration scripts per asset_group                                                                             | 5   |
| `api_football_minimal_flattening_removal_2026_05_07`                        | All 16 todos (UAC normalize.py:377-381 fix + re-fetch VM + manifest flip)                                                           | 5   |
| `cme_polymarket_arb_2026_05_08`                                             | All 6 phases (config + CLOB / CME tick wiring + execution route + DART)                                                             | 5   |

**22 items / 5 tabs / 0 dropped.**

## AI-day estimate (per tab, summed across the cycle)

| Tab                        | Theme                                                    | Items                                                                                                                          | AI-days |
| -------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ------- |
| 1                          | Instruments-live + lifecycle ingestion                   | 5 asset_group activations + Predictions Phase 2+3 + instrument-completion catalog work                                         | ~10     |
| 2                          | Features-repo consolidation + ml/features wiring         | 8 phases features-repo + Phase 2A/B + Phase 3 column-pruning                                                                   | ~10     |
| 3                          | Deployment-UI lifecycle tabs + deploy_missing            | 5 phases UI + deploy_missing Phase 1 + Phase 2                                                                                 | ~10     |
| 4                          | Per-asset_group VM ops + reconcilers + targeted backfill | cefi drain + TradFi cluster validation + cross-asset rescan + sports reconciler + defi_988                                     | ~8      |
| 5                          | Mechanical refactors + audit cluster (the dragon)        | 6 plans: launcher consolidation + data-status tests + databento + per-instrument + hard_schema + api_football + cme_polymarket | ~12     |
| **Total Harsh-side cycle** |                                                          | **~50**                                                                                                                        |

5 parallel agents × ~10 days solo = ~50 ai-days. Tab 5 is the heaviest (6 plans) but each plan is independently
shippable + has well-defined inputs/outputs — perfect for Harsh-side mechanical execution.

---

## TAB 1 — Instruments-live + lifecycle ingestion

**Identity**: you own the May-23 instruments-live activation thread. 5 asset_groups need lifecycle ingestion +
catalog-aware capture. Per CLAUDE.md "Prediction market lifecycle timing" rule, predictions specifically requires
per-market_id lifecycle timestamps (`market_created_at`, `resolution_time`, `settlement_time`). High-leverage tab
because Phase 1 ingestion shipped 2026-05-07 (instruments-service@98bb167, MTDS@b904785) but Phase 2+3 (adapter
migration + reader/feature/strategy consumers) was deferred.

**Plan-of-record**: [`instruments_live_master_2026_05_08.plan.md`](instruments_live_master_2026_05_08.plan.md)

- [`predictions_master_2026_05_07.plan.md`](predictions_master_2026_05_07.plan.md) Phase 2+3 +
  [`instruments_and_market_tick_data_completion_2026_05_01.plan.md`](instruments_and_market_tick_data_completion_2026_05_01.plan.md)
  (catalog-aware writer-guard).

**Scope (4 items, P0-P1)**:

- [ ] [SCRIPT] P0. **`instruments_live_master` Phase A-E** — 5 asset_group live activations: Phase A (cefi Cloud
      Scheduler + audit job + UI tab); Phase B (defi); Phase C (tradfi); Phase D (sports); Phase E (predictions). Each
      phase: Cloud Scheduler cron config + audit job that reconciles per-asset_group catalog vs manifest at midnight +
      deployment-UI tab integration to surface live status. ~5 AI-days (1 per phase).
- [ ] [SCRIPT] P0. **Predictions Phase 2 — MTDS Polymarket/Kalshi lifecycle gating + UMI tick provider data_type
      rename** — per [`predictions_master_2026_05_07.plan.md`](predictions_master_2026_05_07.plan.md) Phase 2 deferred
      from Tab 10 yesterday. Per CLAUDE.md "Prediction market lifecycle timing": MTDS CLOB capture must respect
      lifecycle bounds (NO ticks before `market_created_at`, NO new ticks after `settlement_time`). Rename
      `umi_tick_provider.py:225` + `orchestrator.py:1990-1995` `data_type` → `prediction_canonical_question_group`.
      Per-market_id manifest rows + cluster-coverage gate. ~2 AI-days.
- [ ] [SCRIPT] P0. **Predictions Phase 3 — reader/feature/strategy consumer migration** — every reader of Polymarket /
      Kalshi data migrates to the new shard atom keyed on
      `(asset_group=prediction, venue, data_type,     canonical_question_group, day)`. Features-prediction +
      strategy-service archetype consumers wired. ~2 AI-days.
- [ ] [SCRIPT] P1. **`instruments_and_market_tick_data_completion` per-asset_group catalog-aware writer-guard** —
      writegate Phase 3.D.5 Wave 3 deferred from 2026-05-07. Adds `instrument_catalog` reference at MTDS adapter
      construction so blank-zero-source-response gets routed to (D) zero-activity bars when the catalog says alive AND
      market hours. ~1 AI-day.

**Repos owned (collision boundary)**: instruments-service (full ownership for catalog + lifecycle ingestion; no
overlap), MTDS (Polymarket + Kalshi adapters + UMI tick provider; collides with Ikenna Tab 1 only on different files —
Ikenna touches DeFi adapters), deployment-ui (instruments-live tab integration; collides with Tab 3 here on UI re-shape
— see cross-tab handshake), Cloud Scheduler config files in deployment-service.

**Read-first**:

- CLAUDE.md sections: "Prediction market lifecycle timing", "Per-asset-group shard-key matrix", "Honest absence vs fake
  placeholders", "Four-category empty-output decision", "Cluster validation MANDATORY at record_captured"
- [`plans/active/instruments_live_master_2026_05_08.plan.md`](instruments_live_master_2026_05_08.plan.md)
- [`plans/active/predictions_master_2026_05_07.plan.md`](predictions_master_2026_05_07.plan.md) Phase 2+3
- [`plans/active/instruments_and_market_tick_data_completion_2026_05_01.plan.md`](instruments_and_market_tick_data_completion_2026_05_01.plan.md)
- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
- [`codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md`](../../codex/04-architecture/instrument-lifecycle-cache-delta-hot-reload.md)

**Sub-agent fan-out**:

- Phase A-E: 5 parallel sub-agents (one per asset_group). Each independent. Send all 5 in ONE message.
- Predictions Phase 2: 3 parallel sub-agents — (a) Polymarket adapter lifecycle gating; (b) Kalshi adapter lifecycle
  gating; (c) UMI tick provider rename + manifest writer change.
- Predictions Phase 3: 3 parallel sub-agents per consumer (features-prediction calculator + strategy-service archetype +
  reader fallback).

**Collision risk**:

- MTDS adapters: Ikenna Tab 1 owns DeFi adapters (lending-indices, vault-share-price, lst-rates). You own Polymarket +
  Kalshi. Different files. Pre-commit `git diff --cached --name-only` verifies.
- deployment-ui: Tab 3 here owns the UI re-shape (lifecycle-tabs); you own the instruments-live tab content. **Hard sync
  gate**: Tab 3 lands the lifecycle-tabs UAC SSOT first; you wire instruments-live content on top.

**Done definition**:

1. ✅ Phase A-E shipped: 5 asset_groups have Cloud Scheduler audit jobs running + UI tab surfaces alive.
2. ✅ Predictions Phase 2 + Phase 3 shipped: lifecycle gating active in MTDS, every reader/feature/strategy consumer
   migrated to canonical_question_group axis.
3. ✅ Catalog-aware writer-guard active in MTDS adapter base class; blank-zero-source response correctly routed to (D)
   zero-activity bars when catalog says alive.

---

## TAB 2 — Features-repo consolidation + ml/features wiring

**Identity**: you own the 8 repos → 1 features-service consolidation. Deadline 2026-05-13 (5 days). Pre-req for Ikenna
Tab 2's live-pipeline Phase 4-7 wiring. Tab 12 yesterday's deferred Phase 2A wires absorb into Phase 4-7 of THIS plan
per resolved Tab 12 Q1.

**Plan-of-record**: [`features_repo_consolidation_2026_05_08.plan.md`](features_repo_consolidation_2026_05_08.plan.md)

- [`ml_and_features_master_2026_05_07.plan.md`](ml_and_features_master_2026_05_07.plan.md) Phase 2A/2B + Phase 3.

**Scope (4 items, P0)**:

- [ ] [SCRIPT] P0. **Features-repo consolidation Phases 0-3** — Phase 0 pre-audit (every consumer of every features-\*
      repo enumerated); Phase 1 scaffold consolidated repo `features-service` with sub-package layout; Phase 2
      sub-package extraction (features-onchain → features_service.onchain etc.); Phase 3 import-rewrite sweep across 8
      source repos + every downstream consumer. ~3 AI-days.
- [ ] [SCRIPT] P0. **Features-repo consolidation Phases 4-7** — Phase 4 per-source consumer migration; Phase 5
      `feature_family` UAC column add (replaces N feature_groups with 1 column + value); Phase 6 deprecation banners +
      delete-source-repos commit (8 repos archived); Phase 7 codex SSOT updates per Post-Plan-Phase Codex Audit HARD
      RULE. ~3 AI-days.
- [ ] [SCRIPT] P0. **ml_and_features_master Phase 2A + 2B 8-service `assert_no_lookahead_for_feature_group` wires** —
      absorbs Tab 12 yesterday's deferred work. Wire UTL helper into 8 services at compute entry; strict-mode raise;
      per-service unit test asserting raise on stale input. Lands as sub-step of Phase 4 per resolved Tab 12 Q1
      (operator picked option (b) — defer-into-consolidation). ~2 AI-days.
- [ ] [SCRIPT] P0. **ml_and_features_master Phase 3 parquet column-pruning quick-win** — self-contained 1-3 day pure-win
      for ml-training-service. Memory + speed win on training reads. ~2 AI-days.

**Repos owned (collision boundary)**: features-onchain-service + features-sports-service + 6 other features-\* repos
(all source repos for the consolidation; Tab 5 owns mechanical sweeps elsewhere — different repos), new
`features-service` repo (target of consolidation), MDPS `base_adapter.py` if features-cefi/tradfi compute lives there
(collides with Ikenna Tab 2 live-pipeline wiring — different layers; pre-commit name-only verifies), ml-training-service
(Phase 3 column-pruning).

**Read-first**:

- CLAUDE.md sections: "ARCHITECTURE 2026-05-08 — Live pipeline" (features consolidation is the 3-5 day pre-req per the
  architecture decision), "Plans must capture full codebase impact upfront", "Post-Plan-Phase Codex Audit HARD RULE",
  "Shard-granularity SSOT" ([UAC] vs [UTL] vs [per-service] layer discipline)
- [`plans/active/features_repo_consolidation_2026_05_08.plan.md`](features_repo_consolidation_2026_05_08.plan.md)
- [`plans/active/ml_and_features_master_2026_05_07.plan.md`](ml_and_features_master_2026_05_07.plan.md) Phase 2A
  - 2B + 3
- [`plans/active/live_pipeline_mtds_mdps_features_2026_05_08.plan.md`](live_pipeline_mtds_mdps_features_2026_05_08.plan.md)
  (Ikenna Tab 2's plan — read for Phase 4-7 dependency surface)

**Sub-agent fan-out**:

- Phases 0-3: 4 parallel sub-agents — (a) Phase 0 pre-audit (every import enumeration); (b) Phase 1 scaffold; (c) Phase
  2 sub-package extraction; (d) Phase 3 import-rewrite. Master integrates between phases.
- Phases 4-7: 5 parallel sub-agents per source repo migration + 1 codex SSOT updater + 1 deprecation-banner sweeper.
- Phase 2A/2B 8-service wires: 8 parallel sub-agents (one per service). Send all 8 in ONE message.
- Phase 3 column-pruning: 1 sub-agent profiles current parquet read, identifies droppable columns, applies pruning.

**Collision risk**:

- MDPS `base_adapter.py`: Ikenna Tab 2 wires live-pipeline; you wire ml-features-phase2a-style lookahead-bias check.
  Different layers, methods. Per-commit pre-commit check + `git add -p` for any shared file.
- 8 features-\* source repos: yours; no other tab touches.
- New `features-service` repo: yours; new repo, no collision.

**Done definition**:

1. ✅ `features-service` repo scaffolded + 8 source repos' content migrated as sub-packages + import-rewrite swept
   across every consumer.
2. ✅ All 8 services compute calls wired with `assert_no_lookahead_for_feature_group` strict-mode + unit tests.
3. ✅ Column-pruning quick-win shipped + ml-training memory profile shows expected reduction.
4. ✅ 8 source repos archived with deprecation banner + final commit citing the migration sha.

---

## TAB 3 — Deployment-UI lifecycle tabs + deploy_missing

**Identity**: you own the deployment-UI re-shape thread. Auth + cloud-toggle + env-resolution + 4 lifecycle tab
refactors. Pre-req for Ikenna Tab 5 audit-log integration (auth re-shape ships first; audit-log wraps it).

**Plan-of-record**: [`deployment_ui_lifecycle_tabs_2026_05_08.plan.md`](deployment_ui_lifecycle_tabs_2026_05_08.plan.md)

- [`deploy_missing_auto_launch_2026_05_07.plan.md`](deploy_missing_auto_launch_2026_05_07.plan.md) Phase 1+2.

**Scope (3 items, P0)**:

- [ ] [SCRIPT] P0. **Deployment-UI lifecycle tabs Phases A+B** — Phase A UAC SSOT for lifecycle column (per the plan
      body's UAC schema design); Phase B UI re-shape (4 tab refactors: data-status, deployment-flow, operator-actions,
      alerts). ~3 AI-days.
- [ ] [SCRIPT] P0. **Deployment-UI lifecycle tabs Phases C+D+E** — Phase C cloud-toggle (UI reads `CLOUD_PROVIDER` env +
      per-cloud bucket lookups); Phase D auth flow (Firebase emulator → Cloud Run production parity); Phase E
      env-resolution (UI dev tier 0/1/2 startup script alignment per CLAUDE.md "Local Development"). ~3 AI-days.
- [ ] [SCRIPT] P0. **Deploy_missing Phase 1 + Phase 2** — Phase 1 = tarball-refresh follow-on (Tab 4 yesterday shipped
      the foundation at deployment-service@a620e1f + deployment-api@faac20a). Phase 2 = auto-launch endpoint that wraps
      `_TASK_TO_LAUNCHER` + `subprocess.run` flow, **gated on Ikenna Tab 5's IAM operator decision shipping first**.
      Phase 3+ = post-cutover. ~4 AI-days.

**Repos owned (collision boundary)**: deployment-ui (full ownership), deployment-api `auth_middleware.py` + new launch
endpoint (collides with Ikenna Tab 5 audit-log integration — sequence: auth re-shape ships first),
unified-config-interface (env-resolution), Firebase config files. **Hands off** instruments-live tab content to Tab 1.

**Read-first**:

- CLAUDE.md sections: "Local Development" (full body for tier 0/1/2 + Firebase emulator + dev-start / dev-tiers
  scripts), "Workflow Templates", "Deploy_missing UI" (in DeFi Execution Architecture context)
- [`plans/active/deployment_ui_lifecycle_tabs_2026_05_08.plan.md`](deployment_ui_lifecycle_tabs_2026_05_08.plan.md)
- [`plans/active/deploy_missing_auto_launch_2026_05_07.plan.md`](deploy_missing_auto_launch_2026_05_07.plan.md)
- [`codex/14-playbooks/authentication/firebase-local.md`](../../codex/14-playbooks/authentication/firebase-local.md)
- [`codex/05-infrastructure/runtime-tiers-and-deployment.md`](../../codex/05-infrastructure/runtime-tiers-and-deployment.md)

**Sub-agent fan-out**:

- Phase A+B: 5 parallel sub-agents — (a) UAC SSOT lifecycle column; (b) data-status tab refactor; (c) deployment-flow
  tab refactor; (d) operator-actions tab refactor; (e) alerts tab refactor.
- Phase C+D+E: 3 parallel sub-agents (one per phase). Cloud-toggle + auth + env-resolution are independent.
- Deploy_missing Phase 2: blocked until Ikenna Tab 5 ships IAM. While blocked, prep test scaffold + integration test
  fixtures + auto-launch endpoint draft (no IAM-decision-dependent code yet).

**Collision risk**:

- deployment-ui: yours alone. Tab 1 only adds an instruments-live tab content fragment AFTER your Phase A+B.
- deployment-api `auth_middleware.py`: Tab 5 here owns deploy_missing route definitions. Ikenna Tab 5 owns audit-log
  integration. Sequence enforced by cross-side handshake: you ship auth re-shape, Ikenna wraps with audit-log.
- Firebase config: yours.

**Done definition**:

1. ✅ Phases A-E shipped + every UI tab refactored + cloud-toggle works + auth flow Firebase-emulator-to-prod parity
   verified.
2. ✅ Deploy_missing Phase 1 follow-on shipped + Phase 2 auto-launch endpoint shipped (post-IAM decision).
3. ✅ Plan flips per shippable unit + codex updates per Post-Plan-Phase Codex Audit HARD RULE.

---

## TAB 4 — Per-asset_group VM ops + reconcilers + targeted backfill

**Identity**: you own the day-2/3 OPS thread. Cefi VM drain monitoring + post-drain reconcilers across all 5
asset_groups + targeted defi_988 backfill. Mechanical run-script-and-verify work.

**Plan-of-record**: [`cefi_master_2026_05_07.plan.md`](cefi_master_2026_05_07.plan.md) (cefi drain) +
[`tradfi_master_2026_05_07.plan.md`](tradfi_master_2026_05_07.plan.md) (TradFi MDPS post-drain) +
[`manifest_migration_master_2026_05_07.plan.md`](manifest_migration_master_2026_05_07.plan.md) Stage 4 (rescan)

- [`sports_master_2026_05_07.plan.md`](sports_master_2026_05_07.plan.md) (per-source reconciler hook) +
  [`issues/defi_988_missing_dates_audit_2026_05_08.md`](issues/defi_988_missing_dates_audit_2026_05_08.md).

**Scope (4 items, P0-P1)**:

- [ ] [OPS] P0. **CeFi VM drain final monitoring + sweep** — Tab 2 (cefi-babysit) yesterday continued, ETA today EOD.
      Per CLAUDE.md "No fire-and-forget VM launches": event-progression checks (`STARTED` → `PROCESSING` → `STOPPED`),
      sample-checked spot-shard via per-VM manifest at T+30min after each VM hits STOPPED. Drain report to operator +
      Ikenna Tab 5 (master plan refresh) before EOD. ~1 AI-day.
- [ ] [SCRIPT] P0. **TradFi MDPS post-drain ES.OPT 11-cluster validation rerun** — 5 mdps-tradfi-2021/22/23/24/25 VMs
      running per [`tradfi_master`](tradfi_master_2026_05_07.plan.md). After drain, rerun cluster-coverage gate on
      TradFi MDPS shards; flag any partial bundles via the existing `MissingClusterValidationError` guard; fix in place
      if any flag. ~1 AI-day.
- [ ] [SCRIPT] P0. **Cross-asset manifest rescan post-CeFi drain (Stage 4 of manifest_migration_master)** — Ikenna Tab 3
      designs the schema flip + ships rescan launcher. You operate the launcher
      (`reconcile_phantom_manifest_rows_all.py     --asset-group {cefi|defi|tradfi|prediction|sports} --dry-run` per
      CLAUDE.md "Manifest phantom audit") on a same-region GCE VM. Run dry-run first, operator review CSV, then
      `--apply-write`. Banner-add to 5+ active plans on launch + banner-remove on completion. ~1.5 AI-days.
- [ ] [SCRIPT] P1. **Sports per-source reconciler hook + features_sports_reconcile_available_at hook into per-source
      backfill VM exit-step** — sports_master Tab 3B Phase per
      [`sports_master_2026_05_07.plan.md`](sports_master_2026_05_07.plan.md). Hook fires after each per-source backfill
      VM completes; flips manifest captured → attempted_failed[error="MISSING_AVAILABLE_AT"] on parquets with absent or
      100% null available_at column. ~1 AI-day.
- [ ] [SCRIPT] P0. **defi_988 13,632 actionable rows targeted backfill** — Tab 6 yesterday's audit (PM@fc52188 →
      [`issues/defi_988_missing_dates_audit_2026_05_08.md`](issues/defi_988_missing_dates_audit_2026_05_08.md))
      identified the top-5 priority list. Launch targeted backfill VMs per (chain, protocol, data_type) tuple. Per
      CLAUDE.md "Singleton-locked launchers" + "VM Naming Convention" + "No fire-and-forget VM launches". Use
      rescan-aware skip per CLAUDE.md "Manifest concurrency principle" so concurrent VMs don't re-do work. ~2 AI-days.

**Repos owned (collision boundary)**: deployment-service `scripts/vm/` (you LAUNCH; Tab 5 here MIGRATES launchers —
different files, different ops); instruments-service `scripts/reconcile_phantom_manifest_rows_all.py` (you run; Ikenna
Tab 3 designs the rescan flip schema), per-VM manifest shards on GCS (you read), features-sports-service
`scripts/features_sports_reconcile_available_at.py` (you wire-into-VM-exit-step). **Hands off** lending-indices adapter
code edits to Ikenna Tab 1.

**Read-first**:

- CLAUDE.md sections: "VM tarball deployment", "VM Naming Convention", "Singleton-locked launchers", "No fire-and-forget
  VM launches", "Manifest concurrency principle", "Manifest phantom audit", "Per-VM shard isolation"
- [`plans/active/cefi_master_2026_05_07.plan.md`](cefi_master_2026_05_07.plan.md)
- [`plans/active/tradfi_master_2026_05_07.plan.md`](tradfi_master_2026_05_07.plan.md)
- [`plans/active/manifest_migration_master_2026_05_07.plan.md`](manifest_migration_master_2026_05_07.plan.md) Stage 4
- [`plans/active/sports_master_2026_05_07.plan.md`](sports_master_2026_05_07.plan.md) Tab 3B
- [`plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md`](issues/defi_988_missing_dates_audit_2026_05_08.md)

**Sub-agent fan-out**:

- CeFi drain monitoring: 1 monitoring sub-agent tails events bucket + flags stalls every 10-15 min. Master reports to
  operator at EOD + Tab 5.
- Cross-asset rescan: 5 parallel sub-agents (one per asset_group). Each runs scan-only + reports CSV; master decides
  apply-write per asset_group based on operator review.
- defi_988 backfill: per top-5 priority list, 5 parallel sub-agents launching VMs (each launches its own VM with proper
  VM_NAME prefix + watchdog-registered prefix + per-VM-shard isolation).

**Collision risk**:

- deployment-service `scripts/vm/`: Tab 5 here MIGRATES launcher files (creates new files in `scripts/vm/`, adds
  prefixes to `VM_PREFIX_TO_BUCKET`). You only RUN existing launchers. Coordinate via cross-tab handshake: Tab 5 ships
  any new prefix BEFORE you launch a VM with that prefix.
- per-VM manifest shards: yours alone for the rescan; Ikenna Tab 3's expected_universe v2 also writes shards but to
  different row_keys.

**Done definition**:

1. ✅ All cefi VMs drained + report to operator with per-VM manifest spot-check sample.
2. ✅ TradFi MDPS post-drain cluster-coverage validation green or partial-bundle fixes shipped.
3. ✅ Cross-asset rescan: per-VM shards from all 5 asset_groups merged into canonical manifest; triage file populated
   for any disagreements (Ikenna Tab 3 handles).
4. ✅ Sports reconciler hook wired into VM exit-step + first per-source VM cycle through validates the wire.
5. ✅ defi_988 top-5 priority backfill VMs launched + STARTED + per-VM progress events flowing.

---

## TAB 5 — Mechanical refactors + audit cluster (the dragon)

**Identity**: you own 6 plans of mechanical / parallel-safe / scoped refactor work. Tab 5 is the heaviest tab by plan
count but the cleanest by collision risk (each plan touches a different surface). Ideal for fan-out across 6
sub-agents + master integration.

**Plans-of-record**:
[`launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md`](launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md)

- [`data_status_comprehensive_test_coverage_2026_05_07.plan.md`](data_status_comprehensive_test_coverage_2026_05_07.plan.md)
- [`mtds_databento_path_streaming_2026_05_07.plan.md`](mtds_databento_path_streaming_2026_05_07.plan.md)
- [`mtds_per_instrument_download_api_2026_04_24.plan.md`](mtds_per_instrument_download_api_2026_04_24.plan.md)
- [`hard_schema_enforcement_2026_05_08.plan.md`](hard_schema_enforcement_2026_05_08.plan.md)
- [`api_football_minimal_flattening_removal_2026_05_07.plan.md`](api_football_minimal_flattening_removal_2026_05_07.plan.md)
- [`cme_polymarket_arb_2026_05_08.plan.md`](cme_polymarket_arb_2026_05_08.plan.md).

**Scope (7 items, P0-P1)**:

- [ ] [SCRIPT] P0. **Launcher consolidation: remaining 20 of 30 ad-hoc launchers** — Tab 11 yesterday migrated 10;
      finish the rest. Per CLAUDE.md "VM launcher script SSOT": every launcher under
      `deployment-service/scripts/vm/launch-{asset_group}-{flavor}-vm.sh` + `VM_PREFIX_TO_BUCKET` registry +
      `_SERVICE_LAUNCHER_SCRIPTS` registration if Deploy-Missing UI reachable + relaunch watchdog after each prefix add.
      ~2 AI-days.
- [ ] [TEST] P0. **data_status_comprehensive_test_coverage all 30 todos** — 5 test categories × 6 repos. Per
      [`data_status_comprehensive_test_coverage_2026_05_07.plan.md`](data_status_comprehensive_test_coverage_2026_05_07.plan.md).
      Each test category has explicit assertion shape per the plan body. ~3 AI-days.
- [ ] [SCRIPT] P1. **mtds_databento path-streaming Phases 2-4** — Phase 2 memory profiler verification on heavy day;
      Phase 3 chunked streaming for `get_async_range`; Phase 4 deployment-VM smoke + memory-bound assertion. Per
      [`mtds_databento_path_streaming_2026_05_07.plan.md`](mtds_databento_path_streaming_2026_05_07.plan.md). ~1.5
      AI-days.
- [ ] [SCRIPT] P0. **mtds_per_instrument_download_api Phase 1.5 chain axis** — audit named CRITICAL-PATH per
      [`mtds_per_instrument_download_api_2026_04_24.plan.md`](mtds_per_instrument_download_api_2026_04_24.plan.md). Adds
      chain axis to the per-instrument download API; needed for DeFi instrument download support. ~1 AI-day.
- [ ] [SCRIPT] P0. **hard_schema_enforcement Phases 1-5 mechanical migration scripts per asset_group** — per
      [`hard_schema_enforcement_2026_05_08.plan.md`](hard_schema_enforcement_2026_05_08.plan.md). Each asset*group gets
      a one-time migration script in instruments-service
      `scripts/migrate*<asset_group>\_to_hard_schema.py`    (precedent:`migrate_local_sfi_to_canonical.py`). Per
      CLAUDE.md "Manifest migration, NOT fallback". ~2.5 AI-days.
- [ ] [SCRIPT] P0. **api_football_minimal_flattening_removal all 16 todos** — UAC normalize.py:377-381 fix + re-fetch
      VM + manifest flip per
      [`api_football_minimal_flattening_removal_2026_05_07.plan.md`](api_football_minimal_flattening_removal_2026_05_07.plan.md).
      Per CLAUDE.md "Manifest migration, NOT fallback" — write a migration script + remove the flattening fallback. ~1
      AI-day.
- [ ] [SCRIPT] P1. **cme_polymarket_arb 6 phases** — config + CLOB / CME tick wiring + execution route + DART per
      [`cme_polymarket_arb_2026_05_08.plan.md`](cme_polymarket_arb_2026_05_08.plan.md). New archetype RFC-based;
      reference plan for similar arch wiring. ~2 AI-days.

**Repos owned (collision boundary)**: deployment-service `scripts/vm/` + `vm_zombie_watchdog.py` (you create files; Tab
4 launches existing files — coordinate via handshake), all 7 plan-target repos (each plan touches distinct surface).
**Hands off** anything cross-cutting (UAC schema design, UTL helper design) to Ikenna side.

**Read-first**:

- CLAUDE.md sections: "VM launcher script SSOT", "VM Naming Convention", "Singleton-locked launchers", "Manifest
  migration, NOT fallback", "Per-asset-group shard-key matrix"
- All 7 plan-of-records (above; substantial reading — fan out to sub-agents per plan)

**Sub-agent fan-out**:

- 7 parallel sub-agents (one per plan). Each gets a self-contained task with full done-definition. Send all 7 in ONE
  message at boot.
- Within each sub-agent's task, further sub-fan-out as plan dictates (e.g. data_status_test 5 test categories × 6 repos
  = 30 sub-sub-agents in one message; launcher consolidation 20 launchers = 20 sub-sub-agents).

**Collision risk**:

- deployment-service `scripts/vm/`: Tab 4 LAUNCHES existing scripts; you CREATE new ones + register prefixes.
  Coordinate: ship any new prefix in `VM_PREFIX_TO_BUCKET` BEFORE Tab 4 launches a VM with that prefix.
- UAC: Ikenna Tab 1 (`PROTOCOL_LAUNCH_DATES` flips); you (`api_football_minimal_flattening_removal` UAC change +
  `cme_polymarket_arb` UAC enums + `hard_schema_enforcement` UAC schema columns). Different lines + different files;
  pre-commit `git diff --cached --name-only` MUST match exactly your subset.
- MTDS: Ikenna Tab 1 (DeFi adapters); you (mtds_databento path-streaming + mtds_per_instrument_download_api). Different
  files.

**Done definition**:

1. ✅ 20 launchers migrated; watchdog relaunched; each new prefix Deploy-Missing-UI-reachable.
2. ✅ All 30 data_status tests shipped + green across 6 repos.
3. ✅ mtds_databento Phases 2-4 + memory profiler shows bounded peak.
4. ✅ mtds_per_instrument_download_api Phase 1.5 chain axis shipped + DeFi download integration test green.
5. ✅ hard_schema_enforcement migration scripts per asset_group + reader fallback removed.
6. ✅ api_football_minimal_flattening_removal: 16 todos shipped + sports backfill VM cycles correctly through the new
   shape.
7. ✅ cme_polymarket_arb 6 phases shipped + DART persona test green.

---

## Cross-tab handshakes (within Harsh side)

Hard sync gates between tabs.

- [ ] **Tab 3 (deployment-UI Phase A UAC SSOT) → Tab 1 (instruments-live UI tab content)**: lifecycle column SSOT lands
      first; Tab 1 wires content on top.
- [ ] **Tab 5 (launcher consolidation new prefix) → Tab 4 (VM launches)**: any new prefix in `VM_PREFIX_TO_BUCKET` ships
      first; Tab 4 launches with that prefix afterwards.
- [ ] **Tab 2 (features-repo consolidation Phase 4) → Tab 4 (sports reconciler hook)**:
      features_sports_reconcile_available_at lives in features-sports-service today; will move to features-service after
      consolidation. **Mitigation**: Tab 4 wires hook against current path; Tab 2 updates the import path during Phase 4
      sweep.
- [ ] **Tab 4 (cefi drain done) → Tab 5 (data_status tests rerun)**: data_status integration tests assume drain
      complete. Sequence: drain → rerun.
- [ ] **Tab 1 (instruments-live Phase E predictions) → Tab 1 (Predictions Phase 2+3)**: same tab, sequential.

## Cross-side handshakes (Harsh ↔ Ikenna)

Mirror-image entries appear in [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md).

- [ ] **Harsh Tab 1 (instruments-live + lifecycle ingestion) → Ikenna Tab 1 (lending-indices Bug 3 fix)**: Bug 3 =
      instruments-store-defi 2022 metadata floor. Harsh's instruments-live Phase D (defi instrument lifecycle
      activation) + catalog-aware writer-guard land the catalog-aware floor. Ikenna's Bug 3 fix reads the new catalog.
      Hard sync: Harsh Phase D + writer-guard ship first.
- [ ] **Harsh Tab 2 (features_repo_consolidation Phase 1-4) → Ikenna Tab 2 (live-pipeline Phase 4-7)**: Live-pipeline
      Phase 4-7 wires the consolidated features repo. **Hard ordering**: features_repo_consolidation Phase 1-4 must land
      before live-pipeline Phase 4-7. Harsh announces feat repo consolidation Phase 4 ship in plan-of-record
      `## Open questions`; Ikenna pulls + starts Phase 4-7 wiring.
- [ ] **Harsh Tab 2 (ml-features-phase2a wires) → Ikenna Tab 2 (live-pipeline Phase 11 ServiceEmissionPolicy slice b)**:
      Slice b couples to assert_no_lookahead_for_feature_group; ml-features-phase2a wires it into 8 services.
      Coordinate: Harsh ships per-service wires; Ikenna reads the wires + extends ServiceEmissionPolicy state to reflect
      lookahead-bias-checked status.
- [ ] **Harsh Tab 3 (deployment-ui-lifecycle-tabs auth re-shape) → Ikenna Tab 5 (deploy_missing audit-log
      integration)**: audit-log integration wraps the auth re-shape. Hard ordering: Harsh ships auth re-shape Phase D;
      Ikenna ships audit-log on top.
- [ ] **Harsh Tab 4 (per-asset_group VM ops + reconcilers) → Ikenna Tab 3 (cross-asset rescan design)**: Harsh runs the
      rescan; Ikenna designs the schema flip. Coordinate: Ikenna ships design + ships rescan launcher script; Harsh runs
      the launcher + reports findings; Ikenna handles edge cases.
- [ ] **Harsh Tab 5 (UAC additions) → Ikenna Tab 1 (UAC drift fixes)**: Harsh's `api_football` / `cme_polymarket_arb` /
      `hard_schema_enforcement` add UAC columns/enums; Ikenna flips `PROTOCOL_LAUNCH_DATES`. Different files, different
      lines; surgical `git add -p` mandatory if both edit UAC in the same window.

## Collision-risk callouts (file-level)

- **deployment-service `scripts/vm/` directory**: Tab 4 (launches existing) + Tab 5 (creates new) share the dir.
  Different files. Pre-commit `git diff --cached --name-only` verifies.
- **MDPS `base_adapter.py`**: Ikenna Tab 2 (live-pipeline) + Harsh Tab 2 (ml-features-phase2a-wires). Different layers.
  Pre-commit name-only + `git add -p` mandatory.
- **UAC**: Tab 5 (api_football + cme_polymarket + hard_schema) + Ikenna Tab 1 (PROTOCOL_LAUNCH_DATES) + Tab 3
  (deployment-UI lifecycle UAC SSOT). 3 distinct subsystems; no overlap.
- **deployment-api `auth_middleware.py` + new launch endpoint**: Tab 3 (auth re-shape + new launch endpoint) + Ikenna
  Tab 5 (audit-log on top). Sequence enforced.
- **8 features-\* source repos**: Tab 2 (consolidation source repos). Tab 4 wires hook into features-sports exit-step
  (one of the 8). Coordinate during Phase 4 import-path migration.
- **`live-defi-rollout` push race**: per CLAUDE.md conditional push rule. Pre-commit `git status` +
  `git diff --cached --stat` (no path arg) MANDATORY before EVERY commit. Use `git add -p` / `git add <specific-file>`
  only.

## Daily sync points

- **EOD T+0** (today, midnight UTC): Tabs 1-5 each report done-definition status to operator via plan-of-record
  `## Open questions` resolved + DONE block. CeFi drain reports done.
- **Tomorrow's daily reset**: 1 main-orchestrator-or-operator runs the daily reset per CLAUDE.md (fetch summary + Q&A
  sweep + draft tomorrow's split). Carryover items roll forward.
- **2026-05-13 features-repo consolidation deadline**: Tab 2 must land Phase 0-7 by then (5 days from today). Pre-req
  for Ikenna Tab 2's live-pipeline Phase 4-7.
- **2026-05-15 GCS migration deadline**: Ikenna Tab 3 deadline; Harsh Tab 4 supports the rescan.
- **2026-05-23 live-DeFi cutover**: master plan Group F+G must all be ✅. Tab 4 reports per-asset_group readiness;
  Ikenna Tab 5 aggregates.

## Defer post-cutover (BOTH must NOT touch)

(Same list as Ikenna's split — see [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) §"Defer
post-cutover".)

## Spawn prompts (paste-ready per tab)

> Use these when opening a fresh Claude Code tab + telling it _"work on Tab N"_.

### Tab 1 spawn prompt

```text
You are Tab 1 — a sub-agent spawned by Harsh's main orchestrator agent (a separate Claude
Code session on the SAME PC, sharing the SAME .git/ + working tree as you).

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — workspace rules + § "Daily Work-Split Process".
  2. unified-trading-pm/cursor-configs/SUB_AGENT_MANDATORY_RULES.md — sub-agent inheritance.
  3. plans/active/work_split_2026_05_08_harsh.md § "TAB 1 — Instruments-live + lifecycle ingestion".
  4. plans/active/instruments_live_master_2026_05_08.plan.md (primary plan-of-record).
  5. plans/active/predictions_master_2026_05_07.plan.md Phase 2+3.

Your agent-tag: instruments-live-tab. Your tab number: 1.

ORCHESTRATION RULES per CLAUDE.md § "Daily Work-Split Process" universal mechanics —
shared working tree, conditional push, plan-doc Q&A flow, plan-flip in same logical unit
as code, Findings Triage Discipline.

YOUR TASK: ship Phase A-E + Predictions Phase 2+3 + catalog-aware writer-guard. See
work_split_2026_05_08_harsh.md § "TAB 1" for full done-definition.

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE-2026-05-08 block at bottom of each
plan-of-record.
```

### Tab 2 spawn prompt

```text
You are Tab 2 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "ARCHITECTURE 2026-05-08 — Live pipeline"
     (in the "Plans must capture full codebase impact upfront" rule context),
     § "Shard-granularity SSOT" ([UAC] vs [UTL] vs [per-service] discipline),
     § "Post-Plan-Phase Codex Audit HARD RULE".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 2 — Features-repo consolidation".
  3. plans/active/features_repo_consolidation_2026_05_08.plan.md (primary).
  4. plans/active/ml_and_features_master_2026_05_07.plan.md Phase 2A/2B + Phase 3.

Your agent-tag: features-consolidation-tab. Your tab number: 2.

YOUR TASK: ship features-repo consolidation Phase 0-7 + 8-service lookahead-bias wires
+ parquet column-pruning. See work_split_2026_05_08_harsh.md § "TAB 2".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 3 spawn prompt

```text
You are Tab 3 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "Local Development",
     § "Workflow Templates", § "Plan Locking".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 3 — Deployment-UI lifecycle tabs".
  3. plans/active/deployment_ui_lifecycle_tabs_2026_05_08.plan.md (primary).
  4. plans/active/deploy_missing_auto_launch_2026_05_07.plan.md Phase 1+2.

Your agent-tag: deployment-ui-tab. Your tab number: 3.

YOUR TASK: ship Deployment-UI lifecycle tabs Phase A-E + deploy_missing Phase 1+2 (Phase
2 gated on Ikenna Tab 5 IAM decision shipping first). See work_split_2026_05_08_harsh.md
§ "TAB 3".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 4 spawn prompt

```text
You are Tab 4 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "VM tarball deployment",
     § "VM Naming Convention", § "Singleton-locked launchers", § "No fire-and-forget VM
     launches", § "Manifest concurrency principle", § "Manifest phantom audit".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 4 — Per-asset_group VM ops".
  3. plans/active/cefi_master_2026_05_07.plan.md (cefi drain).
  4. plans/active/tradfi_master_2026_05_07.plan.md (TradFi MDPS post-drain).
  5. plans/active/manifest_migration_master_2026_05_07.plan.md Stage 4 (rescan).
  6. plans/active/sports_master_2026_05_07.plan.md (per-source reconciler hook).
  7. plans/active/issues/defi_988_missing_dates_audit_2026_05_08.md (top-5 priority list).

Your agent-tag: vm-ops-tab. Your tab number: 4.

YOUR TASK: ship cefi drain monitoring + TradFi cluster validation + cross-asset rescan
operation + sports reconciler hook + defi_988 targeted backfill. See
work_split_2026_05_08_harsh.md § "TAB 4".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

### Tab 5 spawn prompt

```text
You are Tab 5 — a sub-agent spawned by Harsh's main orchestrator agent.

BEFORE doing anything else, read in order:
  1. unified-trading-pm/cursor-configs/CLAUDE.md — esp. § "VM launcher script SSOT",
     § "Manifest migration, NOT fallback", § "Per-asset-group shard-key matrix".
  2. plans/active/work_split_2026_05_08_harsh.md § "TAB 5 — Mechanical refactors + audit cluster".
  3. All 7 plan-of-records in TAB 5 scope (launcher consolidation + data-status tests +
     databento + per-instrument + hard_schema + api_football + cme_polymarket).

Your agent-tag: mechanical-refactor-tab. Your tab number: 5.

YOUR TASK: ship 7 plans of mechanical / parallel-safe / scoped refactor work. Fan out
7 parallel sub-agents (one per plan) at boot via a SINGLE message with 7 Task blocks.
See work_split_2026_05_08_harsh.md § "TAB 5".

REPORT-BACK: per CLAUDE.md HARD RULE cadence. DONE block at bottom of each plan-of-record.
```

## Discipline reminders (every tab, every commit)

(Same as [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) §"Discipline reminders" — see there for
the full list. Per CLAUDE.md § "Daily Work-Split Process" universal mechanics.)

## Done definition (whole layout)

When all 5 tabs hit their per-tab done-definition, today's Harsh split is complete. EOD: archive this plan to
`plans/archive/work_split_2026_05_08_harsh.md` + draft tomorrow's `work_split_2026_05_09_harsh.md` per the daily reset
protocol.

## Cross-references

- Companion: [`work_split_2026_05_08_ikenna.md`](work_split_2026_05_08_ikenna.md) — Ikenna's mirror plan.
- Methodology spec: [`cursor-configs/CLAUDE.md`](../../cursor-configs/CLAUDE.md) §"Daily Work-Split Process".
- Yesterday's archived split:
  [`plans/archive/work_split_2026_05_07_harsh_5tab_layout.md`](../archive/work_split_2026_05_07_harsh_5tab_layout.md).
- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](master_to_live_defi_2026_05_23.plan.md) — the durable
  readiness model.
