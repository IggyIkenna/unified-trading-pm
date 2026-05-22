---
title: "AUDIT-03 — Phase 1 READ results: §2.6 ALC + §2.7 CUS + §2.11 ONB"
audit_id: AUDIT-03
run_phase: "Phase 1 — static drift, READ checkpoints"
section: "§2.6 allocation/isolation (ALC-*) + §2.7 custody (CUS-*) + §2.11 onboarding (ONB-*)"
date: 2026-05-22
method: "sonnet sub-agent first-pass (evidence-required) → Opus reviewer consolidation"
auditor: Harsh + Claude Opus 4.7 (reviewer)
checklist: audits/audit-files/audit_03_defi_archetypes_e2e.md
code_audited:
  - strategy-service@b303a358 — client_admission_controller.py, client_worker.py, colocated_engine.py, portfolio_allocator/archetypes.py
  - execution-service — custody/{base,cloud_kms,factory,mock,copper,ceffu}.py, transfer_coordinator.py
  - unified-api-contracts — internal/domain/strategy_service/client_config.py, transfer_events.py, registry/venue_collateral.py
oracle: codex/04-architecture/{per-client-isolation-architecture.md, client-funds-isolation.md, custody-providers.md, client-config-and-risk-dimensions.md}
---

# AUDIT-03 — Phase 1 READ — §2.6 ALC + §2.7 CUS + §2.11 ONB

Sub-agent first pass, Opus-reviewed. **4 findings (F-23…F-26)**, incl. one **P0 client-funds-isolation** gap.

## Per-checkpoint verdicts

| ID | Verdict | Evidence |
| -- | ------- | -------- |
| ALC-01 | PASS | `portfolio_allocator/archetypes.py:566` delegates hedge-leg venue eligibility to `accepted_perp_collateral` (UAC matrix); no hardcoded allowlist ✓ |
| ALC-03 | PASS | `client_admission_controller.py` quarantines on crash (`_quarantine_client`/`ClientQuarantinedEvent`), bounded backoff → no bare `raise` in per-client loop ✓ |
| ALC-04 | PASS | `client_admission_controller.py:108` `multiprocessing.get_context("spawn")` (NOT fork); `TransferIntent.client_id` (transfer_events.py:83) binds source+dest ✓ |
| ALC-05 | **CODE-DRIFT** | `CrossClientTransferForbiddenError` enforced at **1 real layer** — execution-service `transfer_coordinator.py:241`. UAC `transfer_events.py` = docstring reference only (no schema raise); **strategy-service emit layer has NO raise** (0 hits). Codex HARD RULE = 3 layers → F-23 |
| ALC-06 | PASS | `rg "random|datetime.now()"` in portfolio_allocator/ = 0; allocators pure over Decimal ✓ |
| CUS-01 | PASS | `CloudKmsCustodyProvider` (custody/cloud_kms.py:51); `custody_config_from_wallet_provisioning()` calls `wallet.validate()` at bridge (factory.py:54-55) — config-parse-time error ✓ |
| CUS-02 | PASS | provider branching only inside `custody/factory.py`; 0 `if provider==` outside custody/ ✓ |
| CUS-03 | **GAP** | `health_check() -> CustodyHealth` ABSENT from `CustodyProvider` protocol (base.py) + all impls (cloud_kms/mock/copper/ceffu). 0 hits. Codex requires it (ping 60s / balance 5min) → F-24 |
| ONB-01 | **CODE-DRIFT/VERIFY** | UAC `internal/domain/strategy_service/client_config.py` defines `ClientStrategyOverride` (client_id, max_leverage, max_position_usd, allowed_perp_venues) — **missing** codex's `share_class`, `categories_enabled`, `max_drawdown_pct`. A second `internal/reporting/client_config.py` may carry them → F-25 |
| ONB-04 | PASS | `factory.py:35` `_SURFACE_TO_PROVIDER[CLOUD_KMS_ENCRYPTED]="cloud_kms"`; config-only routing ✓ |
| ONB-05 | PASS | `ClientAdmissionController._spawn()` → `Process(name=f"worker-{client_id}")`, one per client_id ✓ |
| ONB-02/06, CUS-04, ONB-07/08 | PHASE2/VERIFY | clients.yaml schema, ClientWorker preflight sequence, SigningSurface hot-reload — deferred |

## Findings

| ID | Checkpoint | Class | Finding | Sev | Status |
| -- | --------- | ----- | ------- | --- | ------ |
| F-23 | ALC-05 | CODE-DRIFT | `CrossClientTransferForbiddenError` at only 1 of 3 required layers (execution-consume). UAC schema = docstring-only; **strategy-service emit raise absent**. Client-funds-isolation HARD RULE defence-in-depth incomplete — a strategy bug emitting a cross-client transfer is caught only at the final layer. `transfer_coordinator.py:241` (present); strategy_service (absent); uac transfer_events.py (docstring) | P0 | **NEEDS-CONFIRM** (Opus re-verify the 3 layers) |
| F-24 | CUS-03 | GAP | `health_check() -> CustodyHealth` absent from `CustodyProvider` protocol + every impl; custody liveness unobservable (composes RSK-08 custody-disconnect breaker, which depends on it). `custody/base.py` | P1 | AGENT-FOUND |
| F-25 | ONB-01 | CODE-DRIFT | strategy-service `ClientConfig` is `ClientStrategyOverride`, missing `share_class`/`categories_enabled`/`max_drawdown_pct`; possible second canonical model in `internal/reporting/`. Reconcile with the e2e-flow doc + F-06 (entity model). | P1 | **NEEDS-CONFIRM** (Opus check reporting/client_config.py) |
| F-26 | CUS-02 | CODE-DRIFT | `get_custody_provider()` factory.py:120 silently returns `MockCustodyProvider` (only `logger.warning`) on unknown provider — silent mock-signing in a production path; should `raise ValueError`. | P2 | AGENT-FOUND |

## Reviewer note

F-23 (P0, client-funds-isolation HARD RULE) is the priority re-verification — I (Opus) confirm the 3-layer enforcement
map before it drives a fix. F-25 needs the `internal/reporting/client_config.py` check (may resolve to PASS). F-24/F-26
accepted on cited evidence.
