---
doc_type: issue
title:
  Phase 8 (utl_reuse_phase8_codex_ssot_archive) dispatched despite gate_on_depends:true with dependency phases
  incomplete — ml model-registry codex doc update deferred as a result
summary: |
  Two findings from working `utl_reuse_phase8_codex_ssot_archive-001` (the codex-SSOT-update closing phase of the
  UTL/UAC reuse-consolidation split family). (1) **Dispatcher gate gap**: Phase 8's own frontmatter
  (`depends_on: [phase0..phase7, phase9]`, `gate_on_depends: true`) and its body note ("machine-held until every
  other split plan reaches done... do not start it early even if individually unblocked") both say this phase should
  not dispatch until all 9 dependency phases are done — but it was dispatched to slot 6 while those phases were
  mostly incomplete (Phase 3 ml_model_registry 0/9 todos checked; Phase 4 features_builder_registry 0/6 checked;
  Phase 1 strategy_risk_hwm 1/7 checked). (2) **Consequence**: of the 4 codex-doc updates bundled into todo #1, 3 were
  verified independently true and shipped now (UTL retry helper, agent-orchestrator UTL cloud-IO routing, the
  strategy-risk-HWM vs UTL-fee-HWM NON-finding); the 4th — "ml model-registry doc: UTL is SSOT; writegate/manifest/
  allowlist now in UTL" — is FALSE today (`ml_service/training/ml/model_registry.py` still exists un-migrated, every
  Phase 3 todo unchecked) and was deferred rather than written, to avoid misdocumenting an unshipped migration.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm, ml-service]
scope: [engineer, admin]
tags: [utl, uac, consolidation, dispatcher, gate_on_depends, codex, ml-registry, findings]
related:
  [
    plans/active/utl_reuse_phase8_codex_ssot_archive_2026_07_13.md,
    plans/active/utl_reuse_phase3_ml_model_registry_2026_07_13.md,
    ../../codex/06-coding-standards/README.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend-engineer
drift_direction: correct-codex
source:
  [
    plans/active/utl_reuse_phase8_codex_ssot_archive_2026_07_13.md#L46-L51,
    plans/active/utl_reuse_phase3_ml_model_registry_2026_07_13.md,
    ml-service/ml_service/training/ml/model_registry.py,
  ]
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# Phase 8 dispatched early + ml-registry codex doc deferred

> Filed by slot 6 while working `utl_reuse_phase8_codex_ssot_archive-001` ("Update codex for every contract this plan
> changes"). Escalated live via `/blocked` (BLK-4d25a1f8); main agent answered **A** — ship the 3 verified doc updates
> now, defer the 4th, file this doc. This issue is the tracked-todo closure for that deferral (RULES.md §4.5).

## What I found

**Finding 1 — dispatcher didn't honor `gate_on_depends: true`.** `utl_reuse_phase8_codex_ssot_archive_2026_07_13.md`
frontmatter lists `depends_on: [phase0, phase1, phase2, phase3, phase4, phase5, phase6, phase7, phase9]` +
`gate_on_depends: true`, and its body says explicitly: "Machine-held until every other split plan (0, 1, 2, 3, 4, 5, 6,
7, 9) reaches `done`" and "This is the LAST phase — do not start it early even if individually unblocked." At dispatch
time (2026-07-13), checkbox counts across those dependency plans were:

| Plan                               | checked / total |
| ---------------------------------- | --------------- |
| phase0_guardrails                  | 1 / 3           |
| phase1_strategy_risk_hwm           | 1 / 7           |
| phase2_api_auth_dedup              | 2 / 5           |
| phase3_ml_model_registry           | 0 / 6           |
| phase4_features_builder_registry   | 0 / 6           |
| phase5_deployment_api_cloud_sdk    | 4 / 6           |
| phase6_venue_health_retry          | 2 / 5           |
| phase7_low_lint_tail               | 4 / 8           |
| phase9_deployment_registry_extract | 5 / 7           |

None of these are fully done. Yet `POST /api/slots/6/boot` returned `utl_reuse_phase8_codex_ssot_archive-001` with
`dispatch_reason: "tier=1 priority=20 plan_order=0 — highest-rank queued task with prereqs met and no collision"` — i.e.
the backend's prereq check reported satisfied when the plan's own explicit gate says it should not be.

**Finding 2 — one of the 4 bundled doc-update items is not yet true.** Todo #1 bundles updates to 4 codex docs into a
single checkbox. Verified status of each, 2026-07-13:

- `codex/06-coding-standards/README.md` (retry helper) — **TRUE.** UTL `unified_trading_library/utils/retry.py` ships
  `with_retry`/`retry` (commit `20c8ae8d`). Shipped.
- `codex/04-architecture/agent-orchestrator-overview.md` (cloud I/O via UTL) — **TRUE.** `server/gcs_sync.py` +
  `server/auth.py` migrated to `get_storage_client()` at `agent-orchestrator@62894565` (2026-06-22); zero raw
  `google.cloud`/`boto3` imports remain in `server/`.
- `codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md` (HWM NON-finding) — **TRUE, independent fact.**
  The strategy-risk equity-drawdown HWM and UTL's fee-crystallization HWM are genuinely different domains regardless of
  Phase 1's completion status (verified against `utl_reuse_phase1_strategy_risk_hwm_2026_07_13.md`'s own "Verified
  reality" note).
- **ml model-registry doc** ("UTL is SSOT; writegate/manifest/allowlist now in UTL") — **FALSE.**
  `ml_service/training/ml/model_registry.py` still exists as the live local implementation (27440 bytes, last modified
  2026-06-10); every todo in `utl_reuse_phase3_ml_model_registry_2026_07_13.md` is unchecked (`[ ]`). UTL does have a
  `ModelRegistry` class ready (`unified_trading_library/ml/model_registry.py:35`), but ml-service has not cut over.
  Writing "now in UTL" into codex today would misdocument an unshipped migration.

## Why it matters

Codex is the durable SSOT other agents read as ground truth. Writing "UTL is SSOT for writegate/manifest/allowlist"
while the actual code still routes through the local `ml_service` registry would cause a future agent to (a) skip
migrating `ml-service` because codex says it's already done, or (b) build new ml-service code against the wrong
registry, assuming UTL is already wired in. Separately, the dispatcher's `gate_on_depends` not blocking Phase 8 means
the "machine-held until every split plan is done" contract that this whole split family was designed around is not
actually enforced — other gated phases in this or future split families may be dispatching early too.

## Recommended decision

1. Fix or confirm the `gate_on_depends` / `depends_on` prereq check semantics in the orchestrator backlog dispatcher so
   a plan-level `depends_on` entry (naming a whole plan file, not a single task id) is only satisfied once every task
   derived from that plan is `done` — or, if the intended semantics are coarser (e.g. only checks specific listed task
   ids), update `plans/PLAN_FORMAT.md` / `task_template.md` to document that distinction so plan authors don't write a
   body note promising whole-plan gating that the backend doesn't provide.
2. Once `utl_reuse_phase3_ml_model_registry_2026_07_13.md` reaches `done` (all its todos checked, local
   `model_registry.py` deleted/repointed to UTL), a follow-up task should add the 4th doc update to
   `codex/04-architecture/` (the ml model-registry doc) and flip `utl_reuse_phase8_codex_ssot_archive-001`'s checkbox in
   `utl_reuse_phase8_codex_ssot_archive_2026_07_13.md`.

## Todos

- [ ] [INFRA] P2. Audit `server/regen_backlog_from_plan.py` / the prereq-check code path (agent-orchestrator repo) for
      how `depends_on` + `gate_on_depends: true` is evaluated — confirm whether it checks whole-plan-done vs a narrower
      signal, and either fix it to whole-plan-done semantics or document the narrower contract in
      `plans/PLAN_FORMAT.md`. (repo: agent-orchestrator)
- [ ] [AUDIT] P2. Once Phase 3 (`utl_reuse_phase3_ml_model_registry_2026_07_13.md`) is fully done, add the ml
      model-registry codex doc update ("UTL is SSOT; writegate/manifest/allowlist now in UTL") to the appropriate
      `codex/04-architecture/` doc and flip the corresponding checkbox in
      `utl_reuse_phase8_codex_ssot_archive_2026_07_13.md` todo #1. (repo: unified-trading-pm)
