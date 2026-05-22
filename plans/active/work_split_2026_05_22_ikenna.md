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
---

# Ikenna work-split 2026-05-22 (8-hour autonomous run)

**Context**: CODE FREEZE LIFTED 2026-05-22 (GCS write-freeze also lifted). Epic VM fleet commissioned (11 VMs running).
Operator 8-hour run: all 8 slots loaded. **Critical gate**: `mtds_mdps_master` Phase 7 (manifest v8 backfill +
label-flip) must be GREEN before any backfill VMs launch. Slot 5 owns Phase 7; all other backfill slots queue behind it.

**Backfill chain (sequential per AG)**: IS → MTDS → MDPS → features. Sports blocked on `sports_master` Phase 3+4 rename.

---

## Slot stack — local laptop (slots 1-8)

| Slot | Wave 1 (active)                                                                  | Wave 2 (after Wave 1 ack)                                                               | Queued days |
| ---- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | ----------- |
| 1    | `gap_2_4_d` bucket fix + `strategy_execution_contract_remediation` (Phases 1-4)  | Monitor backfill chain; `honest_coverage` final item; alerting ALERT_THRESHOLDS         | ~4d         |
| 2    | `cme_polymarket_arb` Phases 2-5 (34% remaining)                                  | `config_grid_archetype_extend` (4 new families) + `d8_perf_upgrade`                     | ~8d         |
| 3    | `aws_migration_defi_first` Phases 1.B+1.C+3-6 + AWS launcher scripts (7 scripts) | `instruments_backfill_phase3` (5 AGs, Phase 7 gate)                                     | ~7d         |
| 4    | `aws_cloud_toggle_and_backfill_parity` Phases 1-3 (UI toggle)                    | `batch_live_symmetry` Phase 3 VM fleet + Phase 4 consumer sweep + reconciliation engine | ~16d        |
| 5    | ✅ 4 plan closes + Phase 6 Docker verify + Phase 7 v8 DONE (PM@ec208173d)        | `mtds_backfill_phase3` Phases 1+3+5 — gated on Phase 5 AWS + sports rename              | ~12d        |
| 6    | Codex audit Phases 1+2 P0 items                                                  | Codex audit Phase 3 bulk pass → `mdps_backfill_phase3`                                  | ~10d        |
| 7    | Phase 11a+11b terraform cleanup (strategy + ml repos)                            | `features_backfill_phase3` (gated on MDPS) → `promote_workflow_may23_cli_path`          | ~9d         |
| 8    | Cloud Run Slack P0 + Phase 2.E smoke test                                        | `manifest_schema_final_gate` final verify → `alerting` PagerDuty policy                 | ~5d         |

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

## Slot 4 — AWS cloud toggle Phases 1-3 → batch_live_symmetry (Wave 2)

**Ping**: `ikenna_orchestrator/pings/slot_4.md`

**Wave 1 (active)**: `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phases 1-3 (service + route + UI toggle).

**Wave 2 (after toggle ack)**: `batch_live_symmetry_2026_05_10.md` remaining 11 items — 3 BLOCK banners + Phase 3 VM
fleet migration (consolidator VM n1-standard-8) + Phase 4 consumer sweep + Phase 9 QG sweep + batch-live reconciliation
engine greenfield (`engine/orchestrator.py` + `cli/handlers/reconcile_handler.py`).

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

**Wave 1 (pending)**: `strategy_repo_consolidation_2026_05_19.md` Phase 11a + `ml_repo_consolidation_2026_05_19.md`
Phase 11b — terraform destroy 5 archived stacks + shared TF cleanup + grafana.

**Wave 2**: `features_backfill_phase3_2026_05_22.md` (gated on MDPS per-AG verify GREEN) — CeFi/DeFi/TradFi feature
compute. Then `promote_workflow_may23_cli_path_2026_05_10.md` — `preflight-cutover.sh` + `run-paper.sh`/`run-live.sh`
updates + testnet venue constructors (Bybit/Binance/OKX/Hyperliquid/Aster missing testnet mode) + Solana devnet for LST
archetypes.

---

## Slot 8 — Slack P0 + Phase 2.E → manifest gate → alerting (Wave 2)

**Ping**: `ikenna_orchestrator/pings/slot_8.md`

**Wave 1 (active)**: Cloud Run Slack `--update-secrets` (P0) + staging smoke (P3) + Phase 2.E smoke test.

**Wave 2**: `manifest_schema_final_gate_2026_05_09.md` final verify (re-pull manifest counts post-backfill) →
`alerting_service_live_rules_2026_05_07.md` 2 agentable items: PagerDuty `uts-prod-live-trading` escalation policy +
update `ALERT_THRESHOLDS` in UAC with quietness-VM baseline values (VM auto-shutdown ~2026-05-22 11:12 UTC).

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
