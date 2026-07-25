---
doc_type: issue
title: check_finalize_plan_coverage.py regression — 2 AO plans lack a gated finalize plan (baseline 1, actual 2)
summary: >-
  `scripts/quality_gates/check_finalize_plan_coverage.py` (a PM QG post-gate check) fails workspace-wide: 2
  `assigned_vm: planning` plans have no companion plan gating their archival via `depends_on` + `gate_on_depends: true`,
  against a tolerated baseline of 1. Confirmed pre-existing (identical failure reproduces on a clean tree with my own
  unrelated commit stashed out) — not introduced by my session. Blocks any plan-doc-touching quickmerge in
  unified-trading-pm right now, since this is a post-gate check that runs regardless of which files are staged.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, finalize-plan-coverage, quality-gate, regression, repo-blocker]
related: []
created: 2026-07-25
assigned_vm: NA
parent_epic: agent_operating_framework_master
execution_scope: local-only
priority: P1
estimate_class: refactor
source: >-
  Hit while shipping sports_curated_universe_domestic_selection_remaining_2026_07_25.md's Middle East batch checkbox
  flip — unrelated file, confirmed the regression pre-exists independent of my change.
resolved_by:
  infra_capture_and_devops_leftovers_finalize_2026_07_25.md (another slot, landed the missing gated finalize plan)
locked_by:
drift_direction: advance-code
depends_on: []
---

# check_finalize_plan_coverage.py regression — 2 plans missing a gated finalize plan

## What's failing

```
Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — 2 violation(s).

Plans missing a gated finalize plan (add depends_on: [<this-slug>] + gate_on_depends: true to a new/existing
companion plan — see task_template.md §4):
  - unified-trading-pm/plans/active/infra_capture_and_devops_leftovers_2026_07_06.md
  - unified-trading-pm/plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md

❌ Regression: 2 > baseline 1. New AO plan(s) shipped without a gated finalize plan — author one before merging
(task_template.md §4).
```

Confirmed pre-existing via `git stash` (my own unrelated file change stashed out, checker still fails identically) — not
caused by this session's work. Both plans are `assigned_vm: planning`, `status: active`, with no `depends_on` pointing
at a gated finalize companion.

## Why I didn't fix it directly

Both plans belong to domains outside this session's scope (infra/devops capture wiring; deployment-registry Firestore
migration) — authoring a correct finalize plan requires understanding what "done" looks like for each initiative
(task_template.md §4's own standard), which I don't have context for. Per the plan-authoring HARD RULE, guessing a
finalize-plan shape for someone else's in-flight AO work risks a wrong done-when baked into a gate that then silently
mis-gates archival. Bumping the checker's baseline (`--baseline-write`) would unblock shipping but mask a real
regression rather than fix it — the ratchet is supposed to go down via genuine fixes, not casual bumps by an unrelated
worker.

## Recommended remedy

Whoever owns `infra_capture_and_devops_leftovers_2026_07_06.md` and
`deployment_registry_firestore_p0_unblock_2026_07_14.md` authors (or points `depends_on` at an existing) gated finalize
plan for each, per `task_template.md §4`. Until then, this blocks every unrelated plan-doc quickmerge in
unified-trading-pm.

## RESOLVED 2026-07-25

`plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md` landed (another slot), gating
`infra_capture_and_devops_leftovers_2026_07_06.md`. `check_finalize_plan_coverage.py` now reports 1 violation
(`deployment_registry_firestore_p0_unblock_2026_07_14.md`, still missing) — back at the pre-existing baseline of 1, so
the REGRESSION this doc tracked (2 > baseline 1) is closed. The remaining single violation is not a regression; it
predates this session and stays open at its own priority.
