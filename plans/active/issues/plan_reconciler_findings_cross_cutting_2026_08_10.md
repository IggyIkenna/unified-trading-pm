---
doc_type: issue
title: plan_reconciler findings — cross-cutting tranche — 2026-08-10
summary: >-
  Daily deep plan-reconciliation run-findings doc for the cross-cutting topic tranche, dispatch agt-33a6ec (slot 28).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, cross-cutting, sharded-run]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: "2026-08-10"
author: plan_reconciler
source: agt-33a6ec
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-33a6ec) since 2026-08-10T00:20:00Z
depends_on: []
---

# plan_reconciler findings — cross-cutting tranche — 2026-08-10

Dispatch `agt-33a6ec`, slot 28, tranche `cross-cutting`. PM head at run start: `f8f07e7459`.

## Scope

147 docs carry `asset_group: cross-cutting` in `plans/active/` (incl. `issues/`). **58 of 147 are inside the 12-hour
grace window** (heavy concurrent fleet activity on this tranche — several sibling batch/finalize plan pairs and issue
docs created within the last few hours) — read-only context this run, not written. **89 are workable.**

Note: yesterday's cross-cutting run (`plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_09.md`,
`agt-627fc7`) shows all sections still `(none yet)`/`(in progress)` — it appears to have died mid-flight before its
first STEP-5 checkpoint. That doc is itself inside today's grace window (locked since 2026-08-09T16:00:00Z, <12h old at
this run's start) so it is read-only context only; not touched, not diagnosed further here (a dead one-shot dispatch
with zero committed content is not, by itself, an actionable finding for this run).

## Flips verified

(none yet)

## Contradictions

(none yet)

## Doc-drift

(none yet)

## Codex corrections applied (mechanical, evidence-cited)

(none yet)

## Hygiene fixes

(none yet)

## Filed

1. **`plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md`** — live unauthenticated prod Cloud Run
   endpoint (`uts-shared-deployment-api`), open 4+ days with 2 prior re-flags (na-eligibility-audit 2026-08-07,
   ag-closeout-audit 2026-08-08 ×2), still unresolved. Escalated immediately rather than batching at end-of-pass given
   severity: `BLK-46b42d75` (options A/B/C, recommendation A, evidence-backed via a fresh consumer-count grep). Progress
   Log entry appended to the target doc itself (already carries the tracked `- [ ]` todos — no new todo needed, this is
   a re-verify + escalate, not a new finding). Not counted as a hunter candidate (found via direct read while
   cross-referencing grace-window `ag_closeout_audit_cross_cutting_parked_*` docs for the Phase-0 pileup check).

## Archive candidates (operator review)

(none yet)

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(in progress)

## Plans not reached

(none yet)
