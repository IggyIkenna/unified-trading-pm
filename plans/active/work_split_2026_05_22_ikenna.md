---
name: work-split-2026-05-22-ikenna
title: Ikenna work-split 2026-05-22 — 8-hour autonomous run (200 AI-days queued)
supersedes: work_split_2026_05_20_ikenna.md
related_plans:
  - aws_cloud_toggle_and_backfill_parity_2026_05_22.md
  - aws_migration_defi_first_2026_05_07.md
  - instruments_backfill_phase3_2026_05_22.md
  - mtds_backfill_phase3_2026_05_22.md
  - mdps_backfill_phase3_2026_05_22.md
  - features_backfill_phase3_2026_05_22.md
  - strategy_execution_contract_remediation_2026_05_20.md
  - batch_live_symmetry_2026_05_10.md
  - promote_workflow_may23_cli_path_2026_05_10.md
  - cme_polymarket_arb_2026_05_08.md
  - config_grid_archetype_extend_2026_05_20.md
parent_epic: orchestrator_master
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
created: 2026-05-22
last_updated: 2026-05-22
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# Ikenna work-split 2026-05-22 (8-hour autonomous run)

**Context**: CODE FREEZE LIFTED 2026-05-22 (GCS write-freeze also lifted). Epic VM fleet commissioned (11 VMs running).
Operator 8-hour run: all 8 slots loaded. **Critical gate**: `mtds_mdps_master` Phase 7 (manifest v8 backfill +
label-flip) must be GREEN before any backfill VMs launch. Slot 5 owns Phase 7; all other backfill slots queue behind it.

**Backfill chain (sequential per AG)**: IS → MTDS → MDPS → features. Sports blocked on `sports_master` Phase 3+4 rename.

---

## Slot stack — local laptop (slots 1-8)

| Slot | Wave 1 (active)                                                                  | Wave 2 (after Wave 1 ack)                                                       | Queued days |
| ---- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | ----------- |
| 1    | `gap_2_4_d` bucket fix + `strategy_execution_contract_remediation` (Phases 1-4)  | Monitor backfill chain; `honest_coverage` final item; alerting ALERT_THRESHOLDS | ~4d         |
| 2    | `cme_polymarket_arb` Phases 2-5 (34% remaining)                                  | `config_grid_archetype_extend` (4 new families) + `d8_perf_upgrade`             | ~8d         |
| 3    | `aws_migration_defi_first` Phases 1.B+1.C+3-6 + AWS launcher scripts (7 scripts) | `instruments_backfill_phase3` (5 AGs, Phase 7 gate)                             | ~7d         |
| 4    | `aws_cloud_toggle_and_backfill_parity` Phases 1-3 (UI toggle)                    | `batch_live_symmetry` → **vm-cross-cutting** (dispatched 2026-05-22)            | ~16d        |
| 5    | ✅ 4 plan closes + Phase 6 Docker verify + Phase 7 v8 DONE (PM@ec208173d)        | `mtds_backfill_phase3` Phases 1+3+5 — gated on Phase 5 AWS + sports rename      | ~12d        |
| 6    | Codex audit Phases 1+2 P0 items                                                  | Codex audit Phase 3 bulk pass → `mdps_backfill_phase3`                          | ~10d        |
| 7    | Phase 11a+11b terraform cleanup (strategy + ml repos)                            | `features_backfill_phase3` (gated on MDPS) → `promote_workflow_may23_cli_path`  | ~9d         |
| 8    | Cloud Run Slack P0 + Phase 2.E smoke test                                        | `manifest_schema_final_gate` final verify → `alerting` PagerDuty policy         | ~5d         |

---

## Slot 2 — CME Polymarket arb + config grid + d8 perf (Wave 2 — Wave 3.S DONE)

**Ping**: `ikenna_orchestrator/pings/slot_2.md`

Wave 3.S DONE at PM@662c5ebc4. Slot 2 free.

**New dispatch (2026-05-22)**:

1. `cme_polymarket_arb_2026_05_08.md` Phases 2-5 (34% left): `linked_canonical_question_group` in IS → MTDS
   binary-outcome shard atom → IS per-cluster expiry for daily binaries → strategy cross-venue arb pairs archetype
2. `config_grid_archetype_extend_2026_05_20.md` — extend `run_2yr_config_grid_backtest.py` to ml-continuous / ml-settled
   / arbitrage-sportsbook / arbitrage-event-markets families
3. `d8_perf_upgrade_2026_05_20.md` — hot-path GCS round-trip reduction (P2, code now)

---

## Slot 3 — AWS migration + AWS backfill launchers → IS backfill (Wave 2)

**Ping**: `ikenna_orchestrator/pings/slot_3.md`

**Wave 1 (active)**: `aws_migration_defi_first_2026_05_07.md` Phases 1.B+1.C+3-6 +
`aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phase 4 (7 AWS backfill launcher scripts).

**Wave 2 (after Wave 1 ack)**: `instruments_backfill_phase3_2026_05_22.md` — launch IS VMs once Phase 7 GREEN (ack from
slot 5). Phases 1/2/3/5; Phase 4 (Sports) BLOCKED-UPSTREAM on sports rename.

---

## Slot 4 — AWS cloud toggle Phases 1-3 (Wave 1 only; Wave 2 → vm-cross-cutting)

**Ping**: `ikenna_orchestrator/pings/slot_4.md`

**Wave 1 (active)**: `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phases 1-3 (service + route + UI toggle).

**Wave 2 (dispatched 2026-05-22 → vm-cross-cutting)**: `batch_live_symmetry_2026_05_10.md` remaining 11 items — 3 BLOCK
banners + Phase 3 VM fleet migration (consolidator VM n1-standard-8) + Phase 4 consumer sweep + Phase 9 QG sweep +
batch-live reconciliation engine greenfield. See `## VM Dispatches` below for vm-cross-cutting boot details.

---

## Slot 5 — 4 plan closes → Phase 6+7 → MTDS backfill (Wave 3)

**Ping**: `ikenna_orchestrator/pings/slot_5.md`

**Wave 1 ✅ DONE (PM@ec208173d)**: 4 plan closes + Phase 6 Docker verify (all 9 prd buckets 100% v8) + Phase 7 manifest
v8 (7.4M rows migrated; blank ec flipped CEFI 3146 + SPORTS 326; DIVERGENT_EMPTY 765 → phase_11_rebackfill). Gate
CLEARED.

**Wave 2 (ACTIVE — gated)**: `mtds_backfill_phase3_2026_05_22.md` — Phase 1 (CeFi 15 venues) + Phase 3 (DeFi:
Pyth/Chainlink/DEX/LST) + Phase 5 (Pred: Polymarket/Kalshi). Remaining gates: Phase 5 AWS migration GREEN (slot 4) + P0
consolidator terraform prd-bucket fix. Phase 4 (Sports) BLOCKED-UPSTREAM on sports rename. Phase 2 (TradFi) already
DONE.

---

## Slot 6 — Codex audit P0 → Phase 3 bulk pass → MDPS backfill (Wave 2)

**Ping**: `ikenna_orchestrator/pings/slot_6.md`

**Wave 1 (✅ DONE PM@072ba9423)**: `codex_plan_audit_differential_2026_05_22.md` Phases 1+2+3 ALL complete. Group D
items flipped; plan-hygiene.md + infrastructure_master + plan_hygiene_master updated.

**Wave 2 (ACTIVE)**: `mdps_backfill_phase3_2026_05_22.md` — MDPS backfill launches. Phase 3 TradFi: launching (no gate —
MTDS-3.2.B done 2026-05-17). Phase 1 CeFi / Phase 2 DeFi / Phase 5 Pred: gated on MTDS-3.2.A-V / 3.2.C-V / 3.2.E-V GREEN
(monitoring).

---

## Slot 7 — Phase 11 terraform → features backfill → promote workflow (Wave 2)

**Ping**: `ikenna_orchestrator/pings/slot_7.md`

**Wave 1 (✅ DONE)**: Phase 11a (deployment-service@09c45f4 — terraform destroy, prior session) + Phase 11b already
completed. Sports Phase 3+4 DONE (instruments-service@fc7b306 + UTL@94e43e8c + features-service@9847b350,
2026-05-22/24).

**Wave 2 (ROLLOUT-AGENT HOLD)**: `features_backfill_phase3_2026_05_22.md` — operator hold, do not touch.
`promote_workflow_may23_cli_path_2026_05_10.md` — gated on features_backfill.

**vm-cross-cutting dispatch (2026-05-26, overnight autonomous run)**:

- ✅ [FIX] P0. basedpyright `|| true` exit-code swallow in base-service.sh — PM@fd4d1ef4c (CRITICAL infrastructure fix)
- ✅ [FIX] P1. deployment-service BASEDPYRIGHT_MAX_ERRORS=1297 ratchet baseline — deployment-service@25dd325
- ✅ [FIX] P1. deployment-service QG: resolve 149 ruff errors + STEP 5.21 + coverage ≥70% — deployment-service@e7fea4e
- ✅ [FIX] P1. deployment-api STEP 5.77: annotate L2-mode-seam exceptions — deployment-api@644b349
- ✅ [FIX] P1. deployment-api STEP 5.90: wire compute_honest_coverage into execution data-status —
  deployment-api@644b349
- ✅ [FIX] P1. deployment-api STEP 5.79: pin node:20-slim to @sha256:3d0f054... in Dockerfile + Dockerfile.dashboard;
  fix STEP 5.79 alias detection bug in base-service.sh (false-positive on `asia-northeast1-docker` hostname) —
  deployment-api@36987d2 | PM@de940512a
- ✅ [FIX] P1. deployment-api STEP 5.61/5.63: wire fastapi_uei_lifespan into lifespan.py; add run_lifecycle to
  data_status_rollup_worker.py main(); update base-service.sh STEP 5.61 to accept fastapi_uei_lifespan —
  deployment-api@0cd1c78 | PM@172440fa9

---

## Slot 8 — Slack P0 + Phase 2.E → manifest gate → alerting (Wave 2)

**Ping**: `ikenna_orchestrator/pings/slot_8.md`

**Wave 1 (✅ DONE)**: ✅ Cloud Run Slack `--update-secrets` (P0) — PM@c2579b8ee + deployment-service@c31e262. ✅ Staging
smoke (P3) — AGENT*ORCHESTRATOR_SLACK_WEBHOOK + AGENT_ORCHESTRATOR_SLACK_SIGNING_SECRET confirmed mounted on
agent-orchestrator-staging (europe-west4, rev 00014-hdn); smoke done at archived plan Phase 4
(agent-orchestrator@07e42e2). ✅ Phase 2.E smoke GCS — 4 buckets sampled: cefi/instruments-cefi/instruments-defi/tradfi
all 100% schema_version=8, 0 blank error_reason on empty_confirmed rows, EXPECTED*\* reasons populated correctly;
writegate status table updated (2.E.2→✅, 2.E.3→✅). ✅ agent_orchestrator_slack_notifications_2026_05_19.md already
archived 2026-05-21.

**Wave 2 (ACTIVE)**: `manifest_schema_final_gate_2026_05_09.md` final verify (re-pull manifest counts post-backfill) →
`alerting_service_live_rules_2026_05_07.md` 2 agentable items: PagerDuty `uts-prod-live-trading` escalation policy +
update `ALERT_THRESHOLDS` in UAC with quietness-VM baseline values (VM auto-shutdown ~2026-05-24 08:32 UTC).

---

## Critical gates for 2026-05-22 8-hour run

| Gate                      | Owner  | Condition                                       | Unblocks                                               |
| ------------------------- | ------ | ----------------------------------------------- | ------------------------------------------------------ |
| Phase 7 manifest v8 GREEN | Slot 5 | ✅ CLEARED PM@ec208173d (2026-05-22 ~04:22 UTC) | All 4 backfill wrapper plans gated on Phase 5 AWS next |
| IS preflight A-E GREEN    | Slot 3 | instruments_master Phase A-E passed             | MTDS backfill launch                                   |
| AWS toggle live           | Slot 4 | Phases 1-3 DONE + QG green                      | AWS data-status UI                                     |
| MTDS CeFi verify          | Slot 5 | MTDS-3.2.A-V passes                             | MDPS CeFi reprocessor (Slot 6)                         |
| MDPS CeFi verify          | Slot 6 | MDPS-3.3.CeFi-V passes                          | Features CeFi compute (Slot 7)                         |
| Sports rename             | Epics  | sports_master Phase 3+4                         | MTDS-3.2.D / MDPS-3.3.Sports / FEAT-3.4.Sports         |

---

## VM Dispatches (2026-05-22)

### vm-prediction — `predictions_master` epic

**Spawned**: slot 1 (main-orchestrator), 2026-05-22. **Epic**: `plans/epics/predictions_master.md` (tier L0, priority
P1, `assigned_vm: vm-prediction`) **Primary active plan**:
`plans/active/data_status_coverage_gaps_and_prediction_manifest_fix_2026_05_22.md` — Phases 1-4 largely complete (IS
CeFi ✅, IS Sports ✅, IS Prediction manifest fix ✅, Codex alignment ✅).

**Remaining work for vm-prediction**:

1. `predictions_master` P0 MTDS migration items (orchestrator.py:1990-1995 data_type replacement; lifecycle gating;
   manifest reflip; old parquet deletion; backfill canonical groups).
2. `kalshi_api_migration_to_elections_subdomain_2026_05_20.md` Phases 3-4 (BLOCKED-CREDENTIALS — Kalshi API key,
   awaiting operator ack).
3. Phase 3.4b: Prediction bucket naming mismatch (P1 DEFERRED to `bucket_name_ssot_canonicalisation_2026_05_10.md`).
4. Phase 3.5: Schema column in drilldown UI verify.

**VM instruction**: main-orchestrator spawns review agent (slot 2) + workers (slots 3-5); reads epic SSOT before coding;
runs `bash scripts/quality-gates.sh` before every push; follows Commit+Push+Flip HARD RULE.

---

### vm-cross-cutting — `infrastructure_master` + `batch_live_symmetry_master` epics

**Spawned**: slot 1 (main-orchestrator), 2026-05-22. **Epics**: `plans/epics/infrastructure_master.md` (tier L4, P0) +
`plans/epics/batch_live_symmetry_master.md` **Active plans**: `plans/active/batch_live_symmetry_2026_05_10.md` +
`plans/active/deployment_api_qg_remediation*`

**Deployment-api QG failures (6, must fix first — blocking CI)**:

1. STEP 5.61 / 5.63: `ServiceBootstrap` missing from `deployment_api/main.py` + wrap `main()` in
   `with run_lifecycle(service_name=...) as run:` at both `deployment_api/main.py` AND
   `deployment_api/scripts/data_status_rollup_worker.py`
2. STEP 5.77: `mode == "batch"/"live"` comparisons outside CLI seam — annotate with `# noqa: L2-mode-seam` at
   `routes/strategy_shard.py:96`, `routes/strategy_shard.py:98`, `routes/data_batch_processing.py:474`
3. STEP 5.79: Dockerfile base pin — `Dockerfile` + `Dockerfile.dashboard` both use `:tag`; pin to `@sha256:digest`
4. STEP 5.82: Staging branch workflow does not trigger Cloud Build — wire image-build trigger per Phase 5
5. STEP 5.90: `deployment_api/routes/service_status.py` missing canonical coverage helper import
   (`compute_coverage_for_bucket` from UTL or `compute_honest_coverage` from UAC)

**batch_live_symmetry remaining work**:

- Phase 3: VM fleet migration (consolidator VM n1-standard-8)
- Phase 4: Consumer sweep
- Phase 9: QG sweep
- Reconciliation engine greenfield (`engine/orchestrator.py` + `cli/handlers/reconcile_handler.py`)

**VM instruction**: fix deployment-api QG failures first (unblocks CI), then batch_live_symmetry phases;
main-orchestrator spawns review agent (slot 2) + workers (slots 3-5); reads epic SSOT before coding; Commit+Push+Flip
HARD RULE.
