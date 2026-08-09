---
doc_type: issue
title: "plan_reconciler daily deep reconciliation run — sports tranche, 2026-08-09"
summary: >-
  Run-findings doc for plan_reconciler dispatch agt-196785 (slot 4, 2026-08-09), tranche=sports. Corpus: 87
  asset_group:sports-tagged docs in plans/active + plans/active/issues (~3.3MB); 18 (21%) are in the 12h grace window
  and read-only this run, leaving 69 non-grace docs as the actionable set, plus the normative refs (PLAN_FORMAT.md /
  task_template.md / INDEX.md / ACTIVE_INDEX.md) and codex which stay in scope for every shard per
  cursor-configs/skills/plan-reconcile/SKILL.md.
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, findings, scheduled, sports]
related: []
created: "2026-08-09"
parent_epic: plan_hygiene_master
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
assigned_role: review
assigned_vm: planning
execution_scope: orchestrator-agent
locked_by: plan_reconciler
locked_since: "2026-08-09"
supersedes:
superseded_by:
resolved_by:
source: "slot 4, plan_reconciler agt-196785, 2026-08-09"
context_scope:
  [
    unified-trading-pm/scripts/plan-hygiene/run_hygiene_sweep.sh,
    unified-trading-pm/agents/plan_reconciler.md,
    unified-trading-pm/cursor-configs/skills/plan-reconcile/SKILL.md,
    unified-trading-pm/plans/epics/sports_master.md,
  ]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler run — 2026-08-09 (agt-196785, tranche=sports)

## Scope + method

- `TRANCHE=sports` supplied → this run audits ONLY `asset_group: sports`-tagged docs (87 docs, ~3.3MB) + normative refs
  - codex, per `cursor-configs/skills/plan-reconcile/SKILL.md` § "Topic-scoped (sharded) runs". A sibling wave of
    workers on other slots covers the other 9 tranches today; cross-tranche contradictions are out of this shard's reach
    by design (caught only by the weekly `all` run).
- **Naming deviation (noted for the operator):** `agents/plan_reconciler.md` STEP 2b specifies the findings-doc path as
  `plan_reconciler_findings_<TODAY>.md` with no tranche component — but today is a sharded multi-tranche day (per
  SKILL.md's Sun-Fri per-tranche cadence), so multiple sibling slots running concurrently would collide on that exact
  filename. This doc uses `plan_reconciler_findings_sports_2026_08_09.md` (tranche-qualified) instead, consistent with
  how other tranche-scoped skills name their outputs (e.g. `sports_satellite_ao_dispatch_batchN_<date>.md`). Filed as a
  hygiene finding below (see `## Filed`) — the boot-prompt SSOT should adopt this convention explicitly.
- Grace set (newest commit <12h old at run start, `date +%s`=1786244451 / 2026-08-09 03:00:51 UTC): 18 of 87 sports docs
  (21%). Read-only context this run.
- Non-grace actionable set: 69 sports docs, spanning `parent_epic: sports_master` (55 docs, most numerous),
  `infrastructure_master` (17), `instruments_master` (7), `agent_operating_framework_master` (3), `manifest_master` (2),
  `predictions_master` (1), `observability_master` (1), `mtds_mdps_master` (1) — note some docs carry >1 asset_group tag
  so epic-membership counts overlap the 87 total.

## Flips verified

## Contradictions

## Doc-drift

## Hygiene fixes

## Filed

1. **Findings-doc naming collision risk on sharded multi-tranche days** — `agents/plan_reconciler.md` STEP 2b's
   `plan_reconciler_findings_<TODAY>.md` path has no tranche component; on a day where multiple tranche shards run
   concurrently (the Sun-Fri norm per SKILL.md), every sibling slot would target the identical filename. Recommend the
   SSOT (`agents/plan_reconciler.md` STEP 2b) adopt `plan_reconciler_findings_<tranche-or-all>_<TODAY>.md`. Not
   auto-fixed here (editing `agents/plan_reconciler.md` is outside `plans/**`, out of this skill's write scope) — routed
   as a filed finding for operator/follow-up action.

## Archive candidates (operator review)

## Refuted (dropped by verify)

## Coverage (hunters / batches / docs)

## Plans not reached
