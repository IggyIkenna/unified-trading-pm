---
doc_type: plan
title: Finalize — DeFi 6-venue pipeline→live build (reconcile + archive)
summary: >-
  Gated finalize companion for defi_venue_pipeline_to_live_ao_build_2026_07_30.md — reconciles the completed build's
  evidence back into its source issue doc, then archives both docs per plan-completion-and-archival-discipline once
  every todo is done.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, finalize, archival, ao-build]
related:
  [
    /plans/active/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
  ]
created: "2026-07-30"
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: [defi_venue_pipeline_to_live_ao_build_2026_07_30]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-07-24 — every AO-dispatched plan needs a gated finalize companion (see
  /plans/active/task_template.md §4).
---

# Finalize — DeFi 6-venue pipeline→live build

Machine-held (`gate_on_depends: true`) until every todo in
`/plans/active/defi_venue_pipeline_to_live_ao_build_2026_07_30.md` is done. Do not start manually before then.

## Todos

- [ ] [DATA] P2. Reconcile the completed build's evidence back into
      `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` — re-verify each of the build
      plan's 5 todos' cited commits/evidence actually exist (`git log`/`git show`, don't trust the build plan's own
      evidence lines uncritically), then flip the issue doc's digest pointer line to a resolved state citing the build
      plan + the before/after `completeness_pct` delta from the build plan's last todo. Done-when: the issue doc
      reflects the true, verified final state.
- [ ] [DATA] P2. Run the standard 6-step plan-completion-and-archival-discipline ritual (per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) on
      `plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` — archive to
      `plans/archive/2026_07/`, add an exact-successor banner pointing at
      `defi_venue_pipeline_to_live_ao_build_2026_07_30.md`, and fix every corpus referrer path (grep the repo for the
      old path and update each hit). Done-when: `regenerate_active_plan_inventory.py` shows zero orphan referrers to the
      archived path.
- [ ] [DATA] P2. Run the same 6-step archival ritual on `defi_venue_pipeline_to_live_ao_build_2026_07_30.md` itself (now
      fully done) and on this finalize plan. Done-when: both are archived, `run_hygiene_sweep.sh` is clean, and no
      active-corpus doc references either by its old `plans/active/` path.

## Progress Log

- **2026-07-30** — plan authored alongside its parent build plan (operator-ruled finalize-companion requirement).
