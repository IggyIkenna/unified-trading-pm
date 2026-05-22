---
name: audit03_deployment_cron_provisioning
title: "AUDIT-03 remediation — deployment cron + cutover-gate provisioning (May-23 P0)"
type: active
parent_epic: infrastructure_master
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
status: active
priority: P0
created: 2026-05-22
last_updated: 2026-05-22
locked_by: live-defi-rollout
source: audits/audit-files/audit_03_defi_archetypes_e2e.md (§2.10 CUT + §6.1 re-verification ledger)
gate: Cloud Run Jobs (Phase 1) must exist before their schedulers (Phase 2) are applied
---

# AUDIT-03 remediation — deployment cron + cutover-gate provisioning

Closes the cutover-readiness infrastructure gaps from AUDIT-03 §2.10, all Opus-re-verified 2026-05-22 (audit §6.1).
These are the missing/broken Cloud Scheduler crons + Cloud Run Job targets that mean the May-23 backtest-fidelity,
scenario-regression, reconciliation, and alerting gates have **no running infrastructure**. Phase-2 e2e cannot
meaningfully run until these land (this — not e2e-script staleness, see F-07 downgrade — is the real Phase-2 blocker).

**Closes:** F-39 (P0), F-40 (P0), F-41 (P0), F-42 (P0), F-43 (P1), F-44 (P1).

> ADC admin perms on GCP (`central-element-323112`) are available — terraform apply does NOT require an operator pause
> (only the hard-stops in CLAUDE.md do). Pre-migration VM drain rule applies if any apply touches buckets.

## Pre-audit

- [x] ✅ [AGENT] P0. Read `deployment-service/terraform/gcp/defi_collection_scheduler.tf` — it is the CORRECT pattern
      (co-located `google_cloud_run_v2_job` via the container-job module + `google_cloud_scheduler_job`). All new crons
      follow it. — deployment-service@7026f49
- [x] ✅ [AGENT] P0. Read the self-documenting NOTE in `t1_batch_scheduler.tf:6-14` — it names the absent targets
      (`fast-t1-recon`, `cefi-t1-recon`, `batch-live-reconciliation`). — deployment-service@7026f49

## Phase 1 — Cloud Run Job targets (F-41, P0) — must precede schedulers

- [x] ✅ [AGENT] P0. **F-41** — Create the missing `google_cloud_run_v2_job` resources (via the container-job module) for
      every `t1_batch_scheduler.tf` cron target: `batch-live-reconciliation-service` (L166-170), `fast-t1-recon`,
      `cefi-t1-recon`. NOTE: the old finding's "batch-vs-live-recon" name is NOT a real resource — do not create it
      (§6.1 correction). — deployment-service@7026f49 (audit03_cron_provisioning.tf Phase 1)
- [x] ✅ [AGENT] P0. Remove the `t1_batch_scheduler.tf:6-14` NOTE once the targets exist; the crons now point at real jobs. — deployment-service@7026f49

## Phase 2 — provision missing Cloud Scheduler crons (F-39/40/42, P0)

- [x] ✅ [AGENT] P0. **F-39** — Provision `cron:mtds-paper-smoke` (`google_cloud_scheduler_job` + its Cloud Run Job) — the
      backtest-fidelity / paper-smoke gate. Currently 0 terraform resources (verified absent vs the 13 existing
      schedulers). — deployment-service@7026f49 (audit03_cron_provisioning.tf Phase 2, 05:30 UTC daily)
- [x] ✅ [AGENT] P0. **F-40** — Provision `cron:mtds-scenario-matrix` — the scenario-regression-matrix gate. RUNS the
      `DEFI_LST_DEPEG_STETH_5PCT` scenario from `audit03_carry_execution_safety_remediation_2026_05_22.md`:Phase 1
      (cross-plan dep — that scenario must exist first). — deployment-service@7026f49 (audit03_cron_provisioning.tf Phase 2, 08:00 UTC daily; BLOCKED on carry-safety Phase 1 for meaningful results)
- [x] ✅ [AGENT] P0. **F-42** — Provision `cron:alerting-paging` — scheduled alerting for live-trading P&L /
      position-breach paging. The paging CODE + telegram secret already exist in alerting-service; only the scheduler is
      missing. — deployment-service@7026f49 (audit03_cron_provisioning.tf Phase 2, hourly, 55-min run)

## Phase 3 — cutover-gate test paths (F-43/44, P1)

- [ ] [AGENT] P1. **F-43** — Add a Solana devnet paper-execution path to `e2e-testing/scripts/defi/run-paper.sh` (today
      Tenderly-EVM-only; Solana devnet appears only as a balance health-check in `preflight-cutover.sh`, not a paper
      path). Gate requires "Tenderly fork + Solana devnet".
- [ ] [AGENT] P1. **F-44** — Add a Playwright e2e for the `ManualTradeGateDialog` approve / deny / timeout→unhold flow
      in `unified-trading-system-ui/tests/e2e/` (current spec exercises only the trade FORM, not the gate state
      transitions).

## Phase 4 — apply + verify on real GCP

- [ ] [SCRIPT] P0. `terraform plan` then `apply` for the new jobs + schedulers on `central-element-323112`.
      **BLOCKED-OPERATOR-DECISION**: `terraform` binary is not installed on the slot-11 host (confirmed 2026-05-22).
      Run from a host where terraform is available (operator workstation or CI runner):
      ```bash
      cd deployment-service/terraform/gcp
      terraform plan -var-file="environments/prod.tfvars"
      terraform apply -var-file="environments/prod.tfvars" -auto-approve
      ```
- [ ] [SCRIPT] P0. Verify each scheduler exists + is ENABLED + fires: `gcloud scheduler jobs describe <name>` + a manual
      `gcloud scheduler jobs run <name>` → Cloud Run Job execution SUCCEEDED.

## Success criteria

- D1: all 4 crons provisioned; their Cloud Run Job targets exist; `gcloud scheduler jobs list` shows them ENABLED.
- D2: a manual trigger of each cron produces a SUCCEEDED Cloud Run Job execution (no "job not found").
- e2e: run-paper.sh exercises both Tenderly + Solana devnet; the gate-flow Playwright e2e passes.

**Full-execution criterion** (per "Plans Run To Actual Completion"):

- ✅ Each of the 4 crons exists on real GCP and a manual run completes SUCCEEDED.
  - **What ran**:
    `gcloud scheduler jobs run {mtds-paper-smoke,mtds-scenario-matrix,alerting-paging,batch-live-reconciliation}`.
  - **Verification**: `gcloud run jobs executions list --job <target>` shows a SUCCEEDED execution per trigger;
    `gcloud scheduler jobs describe` state = ENABLED.

**Cross-plan dep**: F-40 (scenario-matrix cron) is inert until `DEFI_LST_DEPEG_STETH_5PCT` ships in the carry-safety
plan Phase 1.
