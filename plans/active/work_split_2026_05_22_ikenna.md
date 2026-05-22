---
name: work-split-2026-05-22-ikenna
title: Ikenna work-split 2026-05-22 — AWS toggle + backfill parity + unfreeze + backlog close
supersedes: work_split_2026_05_20_ikenna.md
related_plans:
  - aws_cloud_toggle_and_backfill_parity_2026_05_22.md
  - aws_migration_defi_first_2026_05_07.md
  - instruments_backfill_phase3_2026_05_22.md
  - mtds_backfill_phase3_2026_05_22.md
  - mdps_backfill_phase3_2026_05_22.md
  - features_backfill_phase3_2026_05_22.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
  - strategy_repo_consolidation_2026_05_19.md
  - ml_repo_consolidation_2026_05_19.md
parent_epic: orchestrator_master
priority: P0
status: active
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
created: 2026-05-22
last_updated: 2026-05-22
---

# Ikenna work-split 2026-05-22

**Context**: CODE FREEZE LIFTED 2026-05-22 (GCS write-freeze also lifted). Epic VM fleet commissioned (11 VMs running).
Priority P0 work today: AWS cloud toggle end-to-end + AWS backfill launcher scripts. Phase 3 backfill VMs are still
**GATED** — do NOT launch until `mtds_mdps_master` Phase 7 GREEN.

---

## Slot stack — local laptop (slots 1-8)

| Slot | Theme                                                       | Plan(s)                                                                                                   | Status                                      |
| ---- | ----------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| 1    | Main orchestrator + ping audit + planning                   | This file                                                                                                 | Continuous                                  |
| 2    | Writegate Wave 3.S + Phase A AvailabilityRule               | `writegate_honest_coverage_endtoend_2026_05_06.md`                                                        | 🟡 IN PROGRESS (4 items left)               |
| 3    | AWS migration Phases 1.B+1.C+3-6 + backfill scripts Phase 4 | `aws_migration_defi_first_2026_05_07.md` + `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` § Phase 4 | 🟡 IN PROGRESS                              |
| 4    | AWS cloud toggle Phases 1-3 (service+route+UI)              | `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` §§ 1-3                                               | 🟢 DISPATCH (re-sent — cleanup wiped prior) |
| 5    | 4 plan closes: bucket_ssot + 3 design plans                 | See § Slot 5 below                                                                                        | 🟡 IN PROGRESS                              |
| 6    | ⚪ Queue exhausted — available for next dispatch            | —                                                                                                         | AVAILABLE                                   |
| 7    | Phase 11a+11b: strategy/ml repo terraform cleanup           | `strategy_repo_consolidation_2026_05_19.md` + `ml_repo_consolidation_2026_05_19.md`                       | 🟡 PENDING                                  |
| 8    | Push tab-branch to LDR + Phase 2.E smoke test               | `code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.E                                         | 🟡 PENDING UNFREEZE PUSH                    |

---

## Slot 2 — Writegate Wave 3.S + Phase A AvailabilityRule

**Ping**: `ikenna_orchestrator/pings/slot_2.md`

Completed this session: UAC `instruments_catalog` contract + sports `BUNDLED_DATA_TYPES` seeding.

**Remaining** (from "Next dispatch items remaining" in slot_2 ping):

1. Wave 3.S UAC enum values — `EXPECTED_OUTSIDE_TRANSFER_WINDOW` + `EXPECTED_OUTSIDE_TRADING_HOURS`
2. Wave 3.S `sports_per_source_rules.py`
3. UTL `_classify_sports` + `_classify_tradfi` additions
4. Phase A AvailabilityRule Protocol (5 sub-items — per writegate plan Phase 1A)

**QG**: UAC + UTL after each code item.

---

## Slot 3 — AWS migration remaining + AWS backfill launchers

**Ping**: `ikenna_orchestrator/pings/slot_3.md`

**Dispatch 1 (2026-05-21, not yet DONE)**: `aws_migration_defi_first_2026_05_07.md` Phases 1.B, 1.C, 3-6.

**Dispatch 2 (2026-05-22, P0)**: `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phase 4 — create 7 AWS EC2
backfill launcher scripts in `deployment-service/scripts/vm/`:

1. `launch-mtds-backfill-vm-aws.sh`
2. `launch-mdps-backfill-vm-aws.sh`
3. `launch-defi-backfill-vm-aws.sh`
4. `launch-features-backfill-vm-aws.sh`
5. `launch-features-onchain-backfill-vm-aws.sh`
6. `launch-instruments-backfill-vm-aws.sh`
7. `launch-cefi-sharded-backfill-aws.sh`

Reference: `lib/aws_ec2_launch_lib.sh` + `launch-epic-vm-aws.sh` (m7i.xlarge, ap-northeast-1).

**QG**: `bash scripts/quality-gates.sh` in deployment-service after all scripts added.

---

## Slot 4 — AWS cloud toggle Phases 1-3 (P0)

**Ping**: `ikenna_orchestrator/pings/slot_4.md`

Prior dispatch (7 plan closes) is **DONE** as of 2026-05-22.

**New dispatch (2026-05-22, P0)**: `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` Phases 1-3:

- Phase 1: `data_status_service.py` — thread `cloud` param through 3 methods (6 hardcoded `cloud="gcp"` removed)
- Phase 2: `routes/data_status.py` — add `cloud: Literal["gcp", "aws"] = Query("gcp")` to 3 route handlers
- Phase 3: `data-status-context.tsx` + `data-status-provider.tsx` + `data-status-filters-header.tsx` + `_api-stub.ts`

Note: this dispatch was in commit `f1dc256ed` but slot_4's cleanup sweep wiped it. Re-sent 2026-05-22.

---

## Slot 5 — 4 plan closes

**Ping**: `ikenna_orchestrator/pings/slot_5.md`

**Dispatched 2026-05-21** (no DONE ack yet):

1. `bucket_name_ssot_canonicalisation_*` — 73% done, 2.7 cal — mechanical bucket-name refactor, QG each repo
2. `expected_universe_v2_design_2026_05_08.md` — 73% done, 1.6 cal
3. `manifest_cross_asset_rescan_design_2026_05_08.md` — 50% done, 1.2 cal
4. `available_at_lookahead_bias_completion_2026_05_08.md` — 66% done — HARD STOP on Track E features-sports wire-in
   (DEFERRED), close everything else

---

## Slot 6 — Available

Queue exhausted after Wave 1 plan closes + `plan_closeout_archive_2026_05_21.md` archived at `PM@c38098ec`.

**Candidate next dispatch** (operator to choose):

- Sports rename pipeline (`sports_master` Phase 3+4: 4-repo `data_available_at` → `available_at` rename) — unblocks
  MTDS-3.2.D / MDPS-3.3.Sports / FEAT-3.4.Sports
- AWS smoke test Phase 5 coordination (once Phases 1-3 shipped by slot 4)
- Feature writegate Phase A AvailabilityRule overflow (assist slot 2)

---

## Slot 7 — Phase 11a+11b terraform cleanup

**Ping**: `ikenna_orchestrator/pings/slot_7.md`

QG Cluster C (strategy + execution + ml) is **DONE** (`strategy@72beb56c`, `execution@8a3cbe48f`, `ml@29cc7b2`).

**Still pending** (from prior dispatch, consumed by Epic VM bootstrap):

- `strategy_repo_consolidation_2026_05_19.md` Phase 11a — terraform destroy 5 archived stacks + shared TF cleanup +
  grafana
- `ml_repo_consolidation_2026_05_19.md` Phase 11b — same pattern for ML repos

---

## Slot 8 — Push unfreeze work to LDR

**Ping**: `ikenna_orchestrator/pings/slot_8.md`

UNFREEZE notice sent 2026-05-22. Needs to push from `tab/ikennaigboaka/8`:

- MDPS OHLCV nullability fix
- Phase 2.E implementation
- `features-volatility` ServiceEmissionPolicy
- Cloud Run Slack `--update-secrets` (P0) + staging smoke (P3)

Then run Phase 2.E smoke test against GCS (now unblocked).

**Gate**: Phase 3 backfill VMs remain BLOCKED until `mtds_mdps_master` Phase 7 GREEN — do NOT launch.

---

## Critical gates for 2026-05-22

| Gate                     | Condition                                          | Blocks                                         |
| ------------------------ | -------------------------------------------------- | ---------------------------------------------- |
| AWS toggle live          | Slot 4 Phases 1-3 DONE                             | AWS data-status UI + Phase 5 smoke test        |
| AWS launcher scripts     | Slot 3 Phase 4 DONE                                | AWS backfill launches                          |
| AWS smoke test           | Phases 1-3 + 4 DONE + AWS buckets have ≥1 day data | Billing estimate + AWS backfill go/no-go       |
| mtds_mdps_master Phase 7 | Manifest v8 label-flip GREEN                       | Phase 3 backfill VMs (all 4 wrapper plans)     |
| Sports rename            | sports_master Phase 3+4                            | MTDS-3.2.D / MDPS-3.3.Sports / FEAT-3.4.Sports |
