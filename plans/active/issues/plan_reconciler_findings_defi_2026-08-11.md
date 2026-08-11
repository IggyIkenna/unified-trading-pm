---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — defi tranche, 2026-08-11"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-cf0be1 (slot 26, 2026-08-11), sharded to the `defi` topic tranche
  per the 2026-08-06 sharded-cadence ruling. Corpus: 195 docs matched by `asset_group:.*defi` (includes multi-AG docs);
  20 grace docs (12h window), 175 non-grace. Fans out read-only hunter sub-agents, adversarially verifies every
  candidate before acting, auto-fixes the verified-easy, and routes the hard ones.
status: open
nature: issue
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, defi]
related: [/plans/active/defi_consolidated_closeout_2026_07_18.md]
created: "2026-08-11"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-11"
source: "slot 26, plan_reconciler agt-cf0be1, 2026-08-11"
drift_direction: advance-code
supersedes:
superseded_by:
resolved_by:
depends_on: []
---

# plan_reconciler run — 2026-08-11 (agt-cf0be1, defi tranche)

## Scope + method

- `$TRANCHE=defi` supplied → sharded per-tranche run (Sun-Fri cadence, 2026-08-06 ruling).
- Corpus: `rg -l '^asset_group:.*defi' plans/active/{,issues/}` returns 195 docs (includes multi-AG docs, broader than
  the 120-doc scope of the 2026-08-09 run which used a more targeted pattern). The 2026-08-09 run identified that
  single-line `^asset_group:` patterns miss docs with wrapped frontmatter values.
- Grace set (newest commit <12h old): 20 docs — read-only context this run.
- Non-grace actionable set: 175 docs.
- Previous run: `plan_reconciler_findings_defi_2026_08_09.md` (slot 27, agt-1e903d) completed a full 8-batch hunter
  sweep. This run focuses on incremental changes since that run — new/modified docs, newly surfaced hygiene flags, and
  any missed-flip candidates.

## Flips verified

## Contradictions

## Doc-drift

## Hygiene fixes

## Filed

## Archive candidates (operator review)

## Refuted (dropped by verify)

## Codex corrections applied (mechanical, evidence-cited)

## Coverage (hunters / batches / docs)

## Plans not reached
