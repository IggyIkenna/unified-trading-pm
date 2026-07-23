---
doc_type: issue
title: Plan-reconciler findings 2026-07-23 — daily deep reconciliation (agt-59c374)
summary:
  Daily deep plan/codex/cross-plan reconciliation run (dispatch agt-59c374, slot 2). Fan-out read-only hunters DETECT
  candidates across plans <-> epics <-> codex <-> issue docs <-> real code state; every candidate is adversarially
  VERIFIED (refuter + confirmer + tiebreaker) before any write. Auto-fixes the verified-easy (sha/PR-evidenced flips +
  mechanical hygiene), auto-archives verified-done unlocked non-grace plans, and routes the hard ones (contradictions /
  doc-drift) to the operator. Phase-0 inventory this run — 126 top-level active plans (529 incl. subdirs), grace set 52
  (<12h, read-only), hygiene 0 hard / 1 soft, 3 archivable + 1 locked candidate, INDEX.md drift 127.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer, admin]
tags: [plan-reconciler, reconciliation, plan-hygiene, findings, adversarial-verify, scheduled]
related:
  [
    plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md,
    ../../../codex/11-project-management/doc-frontmatter-schema.md,
  ]
created: 2026-07-23
last_updated: 2026-07-23
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
locked_by: plan_reconciler
locked_since: 2026-07-23
supersedes:
superseded_by:
resolved_by:
source: plan_reconciler daily run agt-59c374 (2026-07-23, slot 2)
depends_on: []
---

# Plan-reconciler findings — 2026-07-23 (dispatch agt-59c374)

Daily deep reconciliation over `unified-trading-pm`. DETECT (read-only hunter fan-out) → VERIFY (adversarial) → APPLY
only the confirmed → ROUTE the rest. This doc is the run journal + human-readable presentation; the machine mirror is
the `/api/plan_health/result` POST.

## Run context (Phase 0 — deterministic inputs, trusted not recomputed)

- **Repos**: all 25 slot clones FF-clean to `origin/live-defi-rollout` (STEP-4 code checks read current trees).
- **Active plans**: 126 top-level (529 incl. subdirs; 359 in `issues/`). 509 plan headers in skeleton, 298 with open
  todos.
- **Grace set (<12h since last commit, READ-ONLY this run)**: 52 plans.
- **Hygiene sweep**: 0 hard failures / 1 soft warning (line caps — 23 plans over 1000L hard cap, check is soft).
- **Archive candidates (0 open todos)**: 4 — 3 archivable (unlocked, non-grace), 1 locked
  (`sports_odds_bookmaker_coverage_enumeration_2026_06_20.md`, `locked_by: live-defi-rollout`).
- **INDEX.md ↔ active drift**: 127 (126 active plans absent from INDEX.md + 5 stale INDEX entries).
- **Parent-epic keyword WARNs (soft, informational)**: ~20 plans whose declared `parent_epic` mismatches the
  keyword-derived top match.

## Flips verified

_(HARD-evidence missed flips confirmed by STEP-4 refuter/confirmer — appended as applied.)_

## Contradictions

_(Confirmed plan↔plan / plan↔epic contradictions — fixed inline where reader-verifiable, else routed.)_

## Doc-drift

_(Confirmed plan↔codex drift — FLAGGED only; never auto-edited. Routed to operator.)_

## Hygiene fixes

_(Mechanical frontmatter / todo-format / superseded-banner fixes on non-grace files.)_

## Filed

_(Durable `- [ ]` todos filed for routed items.)_

## Archive candidates (operator review)

_(Verified-done plans archived on the review branch, + locked/unverifiable ones suggested for operator action.)_

## Refuted (dropped by verify)

_(Candidates a hunter surfaced but the adversarial pass did NOT confirm — recorded for auditability.)_

## Coverage (hunters / batches / docs)

_(Hunter families spawned, batches, docs read in full vs skimmed, confirmed/refuted tally.)_

## Plans not reached

_(Any working-set plans not reached before context exhaustion — filed as a finding.)_
