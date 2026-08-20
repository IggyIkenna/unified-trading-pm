---
doc_type: issue
title: check_finalize_plan_coverage.py's draft+gate_on_depends "redundant" heuristic false-positives on a gated
  BATCH (not just a finalize plan)
summary: >-
  `scripts/quality_gates/check_finalize_plan_coverage.py`'s "finalize plans redundantly stuck at status: draft"
  check flags ANY `status: draft` + `gate_on_depends: true` doc, on the theory (correct for a FINALIZE plan per the
  2026-07-30 no-double-gate ruling in `cursor-configs/skills/ag-closeout-audit/SKILL.md`) that the gate alone makes
  `status: draft` redundant. That reasoning does not hold for a genuinely-judgment-requiring satellite BATCH plan
  (not its finalize) that ALSO happens to be gated on an unrelated upstream content-readiness dependency (e.g. an
  extraction batch whose todos can't run until a sibling residual doc reaches 0 open todos) — there,
  `status: draft` is the operator-approval safety rail (a real, independent judgment gate) and `gate_on_depends` is
  a content-readiness gate; conflating them and telling the author to "just flip to active" would ship
  un-reviewed content. Found live 2026-08-19 drafting
  `prediction_satellite_ao_dispatch_batch15_2026_08_19.md` (gated on
  `prediction_phase_ab_residuals_2026_07_24`+`prediction_phase_d_formal_smoke_and_backfill_2026_07_24`) — worked
  around by leaving `gate_on_depends: false` while draft (inert either way, since `status: draft` alone already
  blocks 100% of dispatch) with an explicit same-edit-flip instruction for whoever approves it, rather than fixing
  the checker mid-audit.
status: open
nature: issue
resolved_by:
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [plan-hygiene, quality-gates, check_finalize_plan_coverage, false-positive, gate_on_depends]
related:
  [
    /plans/active/prediction_satellite_ao_dispatch_batch15_2026_08_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-20"
parent_epic: plan_hygiene_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.08
assigned_role: backend_engineer
effort: low
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
gate_on_depends: false
source: >-
  ag_closeout_auditor (slot 21, dispatch agt-6a0a6b), 2026-08-19, prediction-tranche /ag-closeout-audit run —
  found while validating `prediction_satellite_ao_dispatch_batch15_2026_08_19.md` against
  `check_finalize_plan_coverage.py` before drafting; worked around in that doc rather than fixed here (out of
  scope for a prediction-tranche satellite batch — this is shared plan-hygiene tooling).
context_scope:
  [/scripts/quality_gates/check_finalize_plan_coverage.py, /plans/active/task_template.md]
---

# check_finalize_plan_coverage.py draft+gate heuristic false-positive on gated (non-finalize) batches

## Todos

- [ ] [SCRIPT] P3. **Narrow the "finalize plans redundantly stuck at status: draft" check to actual finalize plans.**
      Current heuristic (as of 2026-08-19) flags any `status: draft` doc carrying `gate_on_depends: true`,
      regardless of whether it IS a finalize plan (whose only content is reconcile+archive, genuinely no
      independent judgment, correctly covered by the 2026-07-30 ruling) or a genuinely-judgment-requiring satellite
      batch that separately happens to be gated on an unrelated upstream dependency. Fix: only flag a doc if it is
      ALSO the `depends_on` target of some OTHER doc whose own filename matches `_finalize` (i.e. it IS being used
      as a batch-with-a-paired-finalize, the shape the 2026-07-30 ruling addressed) AND that other doc's
      `depends_on` names it as its sole/primary dependency — or, simpler and more robust: only apply the
      "redundant, flip to active" recommendation when the FLAGGED doc's own filename itself matches `_finalize`
      (a finalize plan is never itself gated on a content-readiness dependency the way a regular batch can be —
      it is always gated on its own paired batch). Repo: unified-trading-pm
      (`scripts/quality_gates/check_finalize_plan_coverage.py`). Source: this run's live encounter drafting
      `prediction_satellite_ao_dispatch_batch15_2026_08_19.md` (worked around there via `gate_on_depends: false`
      while draft, not fixed here). **Done when**: the check no longer flags a genuinely-gated, genuinely-draft
      BATCH plan (add a regression-guard fixture/test case mirroring batch15's shape: `status: draft` +
      `gate_on_depends: true` + a filename NOT matching `_finalize`), still correctly flags an actual finalize
      plan left stuck at `draft`, and `quality-gates.sh` is green.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, prediction tranche, dispatch agt-6a0a6b)**: filed while drafting
  `prediction_satellite_ao_dispatch_batch15_2026_08_19.md` and hitting this false positive
  (`❌ Regression: 1 > baseline 0`) on first validation pass. Worked around in that doc (see its summary +
  warning banner) rather than fixing the checker mid-audit — out of scope for a prediction-tranche satellite
  batch, this is shared `plan_hygiene_master` tooling.
- **context-scout 2026-08-20**: refreshed context_scope (2 entries) — the checker script (fix target) and
  task_template.md (source of the heuristic) still cover the doc's subject.
