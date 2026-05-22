---
title: "AUDIT-03 — Phase 1 (static-readiness) results: §2.10 CUT (cutover gates)"
audit_id: AUDIT-03
run_phase: "Phase 1 — static readiness assessment of cutover-gate wiring (RUN gates assessed by artifact presence)"
section: "§2.10 cutover gates (CUT-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - e2e-testing — scripts/defi/{colocated_engine.py,run-batch.sh,run-paper.sh,run-live.sh,preflight-cutover.sh}
  - deployment-api@HEAD — deployment_api/routes/promote.py
  - deployment-service — terraform/gcp/t1_batch_scheduler.tf, scripts/audit/credential-probe.sh
  - unified-api-contracts@c3f7a45 — internal/domain/strategy_service/lifecycle.py (StrategyMaturityPhase)
  - strategy-service@b303a358 — scripts/run_2yr_config_grid_backtest.py
  - unified-trading-library — batch_live_reconciler.py
  - unified-trading-system-ui — components/dart/manual-trade-gate-dialog.tsx + tests
oracle: plans/active/{master_to_live_defi_2026_05_23.md, promote_workflow_may23_cli_path_2026_05_10.md}
---

# AUDIT-03 — Phase 1 — §2.10 CUT (cutover-gate static readiness)

Sub-agent first pass, Opus-reviewed. Phase-1 assesses whether the **artifact/wiring each gate depends on exists** (RUN
execution is operator/Phase-2). **6 findings (F-38…F-44)** — incl. **4 P0 readiness gaps** (3 unprovisioned crons +
terraform-scheduler-against-nonexistent-job). One sub-agent P0 (CUT-01 APD→CEFI) **downgraded to P1** on Opus review.

## Per-checkpoint verdicts

| ID     | Verdict                      | Evidence                                                                                                                                                                                                                                                                                                                                              |
| ------ | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| CUT-01 | PASS (path) + **P1 finding** | `run-live.sh`→`colocated_engine.py` wired; both archetypes in `STRATEGY_CATEGORIES`. **F-38**: single category→feature-bucket mapping (`carry_staked_basis`→DEFI, `arbitrage_price_dispersion`→CEFI, colocated_engine.py:134-135) → `_get_feature_bucket` resolves ONE asset-group bucket each; can't express DeFi+CeFi hybrid. ≥7-day RUN = operator |
| CUT-02 | PHASE2 + **GAP**             | `run-paper.sh` exists (Tenderly EVM fork default); Tenderly fixtures in execution-service tests. **F-43**: no Solana devnet path in run-paper.sh / colocated_engine paper mode (gate requires "Tenderly fork + Solana devnet")                                                                                                                        |
| CUT-03 | PASS + **GAP**               | `ManualTradeGateDialog` + unit test (approve/deny) + wired into DART terminal. **F-44**: Playwright `dart-manual-trade-flow.spec.ts` tests the trade form, NOT the gate's approve/deny/timeout flow (unit-test-only coverage of the critical path)                                                                                                    |
| CUT-04 | **GAP**                      | `cron:mtds-paper-smoke` "NOT YET RUNNING/DEPLOYED" per master plan (1337,1357); no terraform scheduler def → **F-39**                                                                                                                                                                                                                                 |
| CUT-05 | **GAP**                      | `cron:mtds-scenario-matrix` "NOT YET PROVISIONED" (master 1338) — confirmed: zero terraform defs → **F-40**. Composes RSK-05 (no LST-depeg scenario to run even if cron existed)                                                                                                                                                                      |
| CUT-06 | PASS                         | `strategy-service/scripts/run_2yr_config_grid_backtest.py`; `SUPPORTED_ARCHETYPES` (131-133) includes both; per-archetype dimension tables + unit tests. Operator RUN for full gate                                                                                                                                                                   |
| CUT-07 | PASS                         | `deployment-service/scripts/audit/credential-probe.sh` with `--mode live` (22-74); KMS signing checks. Operator RUN for 100%-pass                                                                                                                                                                                                                     |
| CUT-08 | PASS (partial)               | `e2e-testing/scripts/defi/preflight-cutover.sh` (10 probes; `--archetype carry_staked_basis`/`arbitrage_price_dispersion`). 5-perp-testnet smoke = operator RUN                                                                                                                                                                                       |
| CUT-09 | **CODE-DRIFT**               | `batch_live_reconciler` shipped (UTL); `batch-live-reconciliation` cron in `t1_batch_scheduler.tf:166` BUT the file's own NOTE (4-14) states the Cloud Run Job target "does not exist" → cron fires against nothing → **F-41**                                                                                                                        |
| CUT-10 | **GAP**                      | `circuit_breaker_config.yaml` + kill-switch code present, but `cron:alerting-paging` "scheduling pending" (master 1343,1361); no terraform def → **F-42** (live-trading safety gate)                                                                                                                                                                  |
| CUT-11 | PASS                         | `StrategyMaturityPhase` has only `PAPER_1D` + `LIVE_EARLY` promotable (no `LIVE_FULL` member); promote.py validates target ∈ {PAPER_1D, LIVE_EARLY}; CLI (run-paper/run-live) + UI promote present                                                                                                                                                    |
| CUT-12 | **CODE-DRIFT**               | Same root cause as CUT-09: `batch-vs-live-recon` cron in t1_batch_scheduler.tf points at non-existent Cloud Run Job. Batch=live is code-enforced (shared path) but scheduled recon not operationally wired → **F-41**                                                                                                                                 |
| CUT-13 | PASS                         | `POST /api/promote/...` rejects `live_full` with 422 (StrategyMaturityPhase(...) ValueError + explicit guard `target_phase ∉ {PAPER_1D, LIVE_EARLY}`); `tests/unit/api/test_promote.py` confirms                                                                                                                                                      |

## Findings

| ID   | Checkpoint      | Class      | Finding                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Sev                                       | Status        |
| ---- | --------------- | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- | ------------- |
| F-38 | CUT-01          | CODE-DRIFT | `colocated_engine.py` single category→feature-bucket mapping (carry→DEFI/features-onchain, APD→CEFI/features-delta-one) cannot express DeFi+CeFi hybrid archetypes — each reads only one asset-group's feature bucket. Latent feature-starvation: APD Variant-A DEX prices (features-onchain) absent under CEFI; carry's CeFi perp-funding hedge feature absent under DEFI. Likely OK for the May-23 MVP (APD=funding-dispersion CeFi, carry=Solana-LST+perp) — **verify downstream feature-merge** before clearing | **P1** (Opus downgrade from sub-agent P0) | NEEDS-CONFIRM |
| F-39 | CUT-04          | GAP        | `cron:mtds-paper-smoke` not provisioned (no terraform Cloud Scheduler entry) — backtest-fidelity gate has no running cron                                                                                                                                                                                                                                                                                                                                                                                           | P0                                        | CONFIRMED     |
| F-40 | CUT-05          | GAP        | `cron:mtds-scenario-matrix` not provisioned (zero terraform defs) — scenario-regression-matrix gate has no infra. Composes RSK-05 (F-33)                                                                                                                                                                                                                                                                                                                                                                            | P0                                        | CONFIRMED     |
| F-41 | CUT-09 + CUT-12 | CODE-DRIFT | `t1_batch_scheduler.tf` defines `batch-live-reconciliation` + `batch-vs-live-recon` Cloud Scheduler crons whose Cloud Run Job targets do NOT exist (self-documented in the tf NOTE, lines 4-14) → crons fail silently at runtime                                                                                                                                                                                                                                                                                    | P0                                        | CONFIRMED     |
| F-42 | CUT-10          | GAP        | `cron:alerting-paging` not provisioned — kill-switch/breaker code + telegram-bot-token secret exist, but no scheduled alerting cron to catch P&L deviations / position breaches during live trading (a live-trading safety gate)                                                                                                                                                                                                                                                                                    | P0                                        | CONFIRMED     |
| F-43 | CUT-02          | GAP        | `run-paper.sh` wires only Tenderly EVM fork; no Solana devnet paper path. Gate ("Tenderly fork + Solana devnet") cannot fully pass even on operator run                                                                                                                                                                                                                                                                                                                                                             | P1                                        | CONFIRMED     |
| F-44 | CUT-03          | GAP        | `ManualTradeGateDialog` Playwright e2e tests the manual-trade form, not the gate's approve/deny/timeout→execution-unhold flow (unit-test-only). CUT-03 cross-refs RPT-04 (which REFUTED F-02 — the dialog IS wired now)                                                                                                                                                                                                                                                                                             | P1                                        | CONFIRMED     |

## Reviewer notes

- **CUT-01 downgraded P0→P1**: the sub-agent flagged APD→"CEFI" as a P0 DEX-feature-starvation bug. But the May-23 APD
  MVP is the **funding-rate-dispersion** variant (CeFi 6-perp, the APD-13 live gate), for which a CEFI bucket is
  correct. The single-category mapping is a **latent hybrid-archetype** limitation (also affects carry→DEFI missing its
  CeFi perp- funding hedge feature). Diagnose-before-fix: confirm whether features merge downstream for the MVP path
  before treating as a blocker. Composes the DeFi+CeFi hybrid architecture rule.
- **4 P0 readiness gaps (F-39/40/41/42)** are all infra-provisioning: 3 unprovisioned crons + 2 terraform schedulers
  firing against non-existent Cloud Run Jobs. None are code-correctness in the archetypes; all are deployment-topology
  gaps that block the master-plan continuous-verification columns. F-40 (scenario-matrix cron) + F-33 (no LST-depeg
  scenario) compound: the carry depeg path has neither the scenario nor the cron to run it.
- The promote-path gates (CUT-11/13) are **solid** — `live_full` correctly unreachable (not even an enum member) and the
  endpoint 422s it.
- Genuinely Phase-2 operator-RUN: CUT-01 (≥7d), CUT-02 (≥3d paper), CUT-06 (2yr backtest), CUT-07 (cred-probe 100%),
  CUT-08 (5-perp testnet smoke).
