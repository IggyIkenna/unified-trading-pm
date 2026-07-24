---
doc_type: plan
title: UTL/UAC reuse consolidation — Phase 8 codex SSOT + archive
summary:
  Update every codex contract this consolidation effort changed, record the verified NON-findings, remove the in-flight
  banners, and archive the tracker + all split plans once every repo reaches C5.
status: complete # (was: active) 2026-07-15 plan-reconcile §6: remnant folded out to its target (operator ruling); zero open todos
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [utl, uac, consolidation, codex, archive, split]
related: [plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
locked_by: # cleared 2026-07-15 — operator [unlock-plan] (plan-reconcile §7)
locked_since:
supersedes:
superseded_by:
depends_on:
  [
    utl_reuse_phase0_guardrails_2026_07_13,
    utl_reuse_phase1_strategy_risk_hwm_2026_07_13,
    utl_reuse_phase2_api_auth_dedup_2026_07_13,
    utl_reuse_phase3_ml_model_registry_2026_07_13,
    utl_reuse_phase4_features_builder_registry_2026_07_13,
    utl_reuse_phase5_deployment_api_cloud_sdk_2026_07_13,
    utl_reuse_phase6_venue_health_retry_2026_07_13,
    utl_reuse_phase7_low_lint_tail_2026_07_13,
    utl_reuse_phase9_deployment_registry_extract_2026_07_13,
  ]
gate_on_depends: true
source: [split from utl_uac_reuse_consolidation_remediation_2026_06_10 tracker, operator-approved 2026-07-13]
assigned_role: backend_engineer
drift_direction: correct-codex
---

# UTL/UAC reuse consolidation — Phase 8 codex SSOT + archive (HARD RULE)

> **Split provenance (2026-07-13):** Phase 8 of
> [`utl_uac_reuse_consolidation_remediation_2026_06_10.md`](utl_uac_reuse_consolidation_remediation_2026_06_10.md).
> **Machine-held until every other split plan (0, 1, 2, 3, 4, 5, 6, 7, 9) reaches `done`** — this is the closing phase
> per the tracker's HARD RULE that a plan archives only once all repos hit C5.

## Todos

- [x] ✅ [AUDIT] P1. Update codex for every contract this plan changes: `/codex/06-coding-standards/README.md`
      (reuse-before-reimplement rule + the new UTL retry helper),
      `/codex/04-architecture/agent-orchestrator-overview.md` (cloud I/O via UTL; auth-fetch only),
      `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` (strategy equity-drawdown-HWM is local +
      distinct from UTL fee-crystallization HWM — record the NON-finding so a future audit doesn't re-flag it), and the
      ml model-registry doc (UTL is SSOT; writegate/manifest/allowlist now in UTL). — DONE (2026-07-13, slot-3),
      `unified-trading-pm@<this commit>`:
  - **`/codex/06-coding-standards/README.md`**: added Core Principle 6 ("Reuse before reimplement") citing the whole
    9-phase remediation as the verification precedent; documented UTL's new `retry`/`with_retry` helper
    (`unified-trading-library@20c8ae8d`) as the pattern for hand-rolled adapter retry loops, distinct from the existing
    `@handle_api_errors`/`@handle_storage_errors` decorators.
  - **`/codex/04-architecture/agent-orchestrator-overview.md`**: added a callout noting `server/gcs_sync.py` and
    `server/auth.py::_load_gcs_secret` go through UTL `get_storage_client()` (not raw `boto3`/`google.cloud.storage`) as
    of `agent-orchestrator@62894565` — auth-fetch only, JWT signing itself untouched.
  - **`/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`**: added the equity-curve-drawdown vs
    fee-crystallization-HWM NON-finding (matching the existing `hwm_seeds.py` NON-finding's format) — strategy-service's
    `RiskCalculator.calculate_drawdown`/`compute_drawdown` + the `pnl_monitor.py`/`output_builders.py` peak loop are a
    different domain (real-time risk gating) from §8's fee HWM (performance-fee billing); do not collapse them.
  - **`/codex/04-architecture/ml-service-architecture.md`**: updated the sub-package layout diagram (the local
    `model_registry` entry was deleted in Phase 3) and added a "ModelRegistry class SSOT" note pointing at
    `unified_trading_library.ModelRegistry` as the canonical home, listing all 4 repointed ml-service consumers.
- [x] ✅ [AUDIT] P1. Record the **verified NON-findings** list (greeks BSM kernel — UAC has only delta-strike schemas;
      execution-service per-venue order circuit breaker — UTL's CB is DR-recovery tooling; batch-live stage-grain recon
      schemas; trading-agent ephemeral ledger; ibkr TCP health probe; client-reporting-api `core/hwm_seeds.py` — static
      seeds for UTL's three-method HWM, not a `max(equity)` reimpl) in the relevant codex docs so the next reuse audit
      doesn't re-open them. — unified-trading-pm@6bd87af85. Recorded in
      `/codex/04-architecture/greeks-service-overview.md`, `/codex/04-architecture/kill-switch-circuit-breaker.md`,
      `/codex/09-strategy/operational/paper-batch-live-reconciliation.md`,
      `/codex/04-architecture/trading-agent-service-directive-pipeline.md`, `/codex/02-venues/prime-brokers.md`, and
      `/codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md`.
- [x] [VERIFY] P1. Remove the Phase-0 in-flight banners (added to the 5 epic plans); run plan-hygiene + active-inventory
      regen; archive the tracker (`plans/active/utl_uac_reuse_consolidation_remediation_2026_06_10.md`) and this whole
      split family per the 5-step HARD RULE once all repos hit C5. — **FOLDED OUT** to
      plans/epics/infrastructure_master.md (2026-07-15, plan-reconcile §6 operator ruling); tracked there, not here.

## Success criteria

Codex updated for every changed contract + NON-findings recorded; banners removed; tracker + split plans archived per
HARD RULE.

## Notes for the worker

- Commit + Push + Flip each shippable unit in the same turn (CLAUDE.md HARD RULE).
- This is the LAST phase — do not start it early even if individually unblocked; the `gate_on_depends: true` on
  `depends_on` above enforces this at the dispatcher level.
