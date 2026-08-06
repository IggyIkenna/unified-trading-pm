---
doc_type: issue
title:
  "canonical_id_builder_retrofit_checklist (AO plan) ships with no gated finalize plan — finalize-plan-coverage QG red
  on PM"
summary: >-
  The `finalize-plan-coverage` QG check (baseline 0, ratchet) flags
  `plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md` — an `assigned_vm: planning`, `execution_scope:
  orchestrator-agent` AO plan with no gated finalize companion (no `<slug>_finalize_*.md` with `depends_on: [<slug>]` +
  `gate_on_depends: true`). The red is PRE-EXISTING (verified on a clean tree with an unrelated diff stashed) and blocks
  the PM repo's green-tree shipping gate for all slots.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, finalize, plan-coverage, qg-red, mvi]
related:
  [
    /plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md,
    /plans/active/issues/context_scope_marker_claims_exceed_frontmatter_count_2026_08_06.md,
  ]
created: "2026-08-06"
author: worker slot-4 (context_scope_marker_claims_exceed_frontmatter_count-003)
last_updated: "2026-08-06"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  "2026-08-06 — resolved by archival of the completed plan (slot-6, task -002); finalize-plan-coverage re-verified GREEN
  fleet-wide"
source: >-
  Surfaced 2026-08-06 while shipping the COUNT_MISMATCH detection fix
  (context_scope_marker_claims_exceed_frontmatter_count-003): the full `quality-gates.sh` run exits 1 on
  `finalize-plan-coverage` (`scripts/quality_gates/check_finalize_plan_coverage.py`, baseline
  `finalize_plan_coverage_baseline.yaml` = 0). Clean-tree check (stash of the unrelated diff) reproduces the identical
  failure at LDR HEAD — not introduced by the context-scope work.
depends_on: []
---

# canonical_id_builder_retrofit_checklist is missing its gated finalize plan

## What I found

`scripts/quality_gates/check_finalize_plan_coverage.py` reports 1 violation vs a baseline of 0:

```
Plans missing a gated finalize plan (add depends_on: [<this-slug>] + gate_on_depends: true to a
new/existing companion plan — see task_template.md §4):
  - unified-trading-pm/plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md
❌ Regression: 1 > baseline 0.
```

The flagged plan is genuinely AO-dispatched work: `doc_type: plan`, `status: active`, `nature: notes`,
`assigned_vm: planning`, `execution_scope: orchestrator-agent`, `assigned_role: data_engineering`,
`model_tier: sonnet-doable`, P2 / ~5-day retrofit checklist (route ~48 DeFi + 5 on-chain-perp + other adapters through
the shared `build_canonical_instrument_id` / `build_leg` builders). It has NO
`canonical_id_builder_retrofit_checklist_2026_07_08_finalize_*.md` companion. The check's exemption list (nature-based)
does not cover it.

**Pre-existing, not task-caused**: with the COUNT_MISMATCH diff (`generate_context_scope_inventory.py` + test +
context-scout SKILL.md) stashed, the check fails byte-identically at LDR HEAD. It blocks the PM repo's green-tree gate
(QG exit 1 → no `.qg_last_passed_sha` sentinel → quickmerge Pass-1/Pass-2 refuse), so every PM slot currently cannot
ship.

## Why it matters

A blocked PM shipping gate stalls every slot's PM work (docs, plans, plan-hygiene scripts, CI changes) until resolved.
Independently, the plan genuinely should have a gated finalize per task_template.md §4 (operator ruling 2026-07-24): it
is a real AO plan whose completion needs a closeout gate before archival.

## Recommended decision

- [x] ✅ [DOC] P2. **RESOLVED 2026-08-06 — superseded by archival, no finalize authored.** The flagged plan
      `canonical_id_builder_retrofit_checklist_2026_07_08.md` was a COMPLETED plan (0 open / 14 closed todos); slot-6
      (task -002) archived it to `plans/archive/2026_08/` and deleted the stale `status: active` twin
      (unified-trading-pm@dda85c8cc, operator-authorized), which cleared `finalize-plan-coverage` to GREEN for the
      fleet. Authoring a finalize plan for a done+archived plan is no longer applicable.
      `check_finalize_plan_coverage.py` re-verified at 0 violations. No baseline bump needed.

## Progress Log

- **2026-08-06 (worker slot-4, context_scope_marker_claims_exceed_frontmatter_count-003)**: filed while blocked from
  shipping the COUNT_MISMATCH fix by this pre-existing red; clean-tree evidence above. RESOLVED same day — the red was
  transient (slot-6's parallel archival of the done plan, `dda85c8cc`, landed within the hour and flipped the gate
  green); the repo-blocker RB-fbeef249 is moot. This doc is closed.
