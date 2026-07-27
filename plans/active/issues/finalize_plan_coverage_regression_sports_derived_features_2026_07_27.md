---
doc_type: issue
title:
  "check_finalize_plan_coverage.py regression (2 > baseline 1) —
  sports_derived_features_postfloor_residue_purge_2026_07_27.md ships assigned_vm:planning with no gated finalize plan"
summary: >-
  Discovered while shipping an unrelated fix (ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3,
  slot-git-status-report.sh loopback preference) — quickmerge.sh's corpus-wide pre-flight re-gate failed on
  check_finalize_plan_coverage.py, which scans ALL of plans/active/ (not just changed files) for assigned_vm:planning
  plans with more than 1 open todo and no companion finalize plan. Root-caused via git log —
  plans/active/sports_derived_features_postfloor_residue_purge_2026_07_27.md (unified-trading-pm@6af68d7b2, slot-12,
  "author the derived_features postfloor residue census+purge follow-up plan") shipped `assigned_vm: planning` but has
  no `<slug>_finalize_*.md` companion with `depends_on: [<slug>]` + `gate_on_depends: true` (task_template.md §4
  pattern). This corpus-wide gate blocks EVERY slot's quickmerge on unified-trading-pm, not just mine — confirmed by
  running the checker standalone (`check_finalize_plan_coverage.py --workspace-root ...`), which reports 2 violations
  against a baseline of 1 (the other, `deployment_registry_firestore_p0_unblock_2026_07_14.md`, is the pre-existing
  accepted baseline entry). Not caused by my session — my own new issue doc that initially also tripped this
  (pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md) has already been fixed in a separate commit (assigned_vm
  flipped to NA, since it's a standalone findings doc, not a real AO-dispatch batch plan).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [quality-gates, finalize-plan-coverage, plan-hygiene, repo-blocker, sports]
related: [/plans/active/sports_derived_features_postfloor_residue_purge_2026_07_27.md, /plans/PLAN_FORMAT.md]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: infrastructure_master
source:
  "slot-11 (infra), discovered while shipping ao_satellite_ao_dispatch_batch1_2026_07_26.md item 3; declared as
  repo-blocker RB-8cb21a60"
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
---

# finalize-plan-coverage regression — sports_derived_features_postfloor_residue_purge_2026_07_27.md

## What I found

`check_finalize_plan_coverage.py --workspace-root <ws>` reports:

```
Scanned plans/active/ for assigned_vm: planning plans lacking a gated finalize plan — 2 violation(s).

Plans missing a gated finalize plan (add depends_on: [<this-slug>] + gate_on_depends: true to a new/existing
companion plan — see task_template.md §4):
  - unified-trading-pm/plans/active/sports_derived_features_postfloor_residue_purge_2026_07_27.md
  - unified-trading-pm/plans/active/deployment_registry_firestore_p0_unblock_2026_07_14.md

❌ Regression: 2 > baseline 1. New AO plan(s) shipped without a gated finalize plan — author one before merging
(task_template.md §4).
```

`deployment_registry_firestore_p0_unblock_2026_07_14.md` is already listed in
`scripts/quality_gates/finalize_plan_coverage_baseline.yaml`'s `baseline_files` (the one accepted pre-existing
violation) — the NEW regression is `sports_derived_features_postfloor_residue_purge_2026_07_27.md`
(`unified-trading-pm@6af68d7b2`, authored 2026-07-27 01:48 UTC by slot-12). This is a corpus-wide scan (runs over ALL of
`plans/active/`, not scoped to a changeset), so it blocks every slot's `quickmerge.sh` on this repo until fixed, not
just the session that discovered it.

## Why it matters

Per `task_template.md` §4 (operator ruling 2026-07-24), a plan shipped with `assigned_vm: planning` but no gated
finalize companion leaves its own todos' evidence/archival stuck forever with nothing that reconciles it — the same
class of gap the `sports_closeout_batch1_ao_ready` / `sports_closeout_batch1_finalize` pattern exists to close. Beyond
the direct risk to that one plan, it is currently red-blocking the ENTIRE repo's ship pipeline.

## Recommended decision

Either: (a) Author `plans/active/sports_derived_features_postfloor_residue_purge_finalize_2026_07_27.md` with
`depends_on: [sports_derived_features_postfloor_residue_purge_2026_07_27]` + `gate_on_depends: true` (task_template.md
§4 pattern), or (b) If that plan was never actually meant for AO dispatch, flip its `assigned_vm` to `NA` instead.

This decision belongs to whoever owns the sports_derived_features plan's intent (slot-12 / the sports asset-group
track), not to an unrelated repo-blocker waiter — filed here + declared as repo-blocker `RB-8cb21a60` so the fix routes
to the right owner via the standard escalation rather than being fixed blind by someone with no context on the plan's
actual scope.

## Todos

- [ ] [SCRIPT] P1. Author the gated finalize plan for
      `plans/active/sports_derived_features_postfloor_residue_purge_2026_07_27.md` (task_template.md §4 pattern), OR
      flip its `assigned_vm` to `NA` if it was never meant for AO dispatch — whichever matches the plan owner's actual
      intent. **Done when**: `check_finalize_plan_coverage.py --workspace-root <ws>` reports violations at/below
      baseline (1) again. (repo: unified-trading-pm)
