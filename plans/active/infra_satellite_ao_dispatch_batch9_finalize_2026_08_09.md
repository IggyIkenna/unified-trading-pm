---
doc_type: plan
title: Infra satellite AO dispatch batch 9 — finalize (reconcile source-doc checkboxes + archive)
summary: >-
  Gated closeout for `infra_satellite_ao_dispatch_batch9_2026_08_09.md`, per the finalize-plan-coverage gate
  (task_template.md §4, operator ruling 2026-07-24; machine-enforced by
  `scripts/quality_gates/check_finalize_plan_coverage.py`). Once all 4 batch todos are done, reconciles the
  corresponding item back into `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md` (flip its todos 1-4,
  leave its operator-gated todo 5 untouched) and checks whether that source doc is now an archival candidate (expected:
  NOT — todo 5 stays open, `assigned_vm: NA`). `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own Deferred item 3
  (G2) is prose-only documentation, not a live checkbox — no reconciliation needed there beyond a citation note. Then
  runs the standard ritual on the batch pair itself.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, finalize, batch-9, plan-hygiene]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: medium
sequential: true
drift_direction: advance-code
depends_on: [infra_satellite_ao_dispatch_batch9_2026_08_09]
gate_on_depends: true
locked_by:
locked_since:
context_scope:
  [
    /plans/active/infra_satellite_ao_dispatch_batch9_2026_08_09.md,
    /plans/active/issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
supersedes:
superseded_by:
source: >-
  Authored alongside its parent batch by `/ag-closeout-audit infra` (2026-08-09), per the standing
  finalize-plan-coverage rule (every ≥2-todo `assigned_vm: planning` plan needs a gated finalize twin).
---

# Infra satellite AO batch 9 — finalize

Machine-held via `depends_on` + `gate_on_depends: true` until all 4 of
`infra_satellite_ao_dispatch_batch9_2026_08_09.md`'s todos are done — this plan can never dispatch early, regardless of
whether the batch is `draft` or `active` at the time (the gate reads the batch's own checkboxes directly, per the
skill's no-double-gate mechanism).

## Todos

- [ ] [REVIEW] P2. **Reconcile `issues/codex_drift_followups_dual_cloud_image_builds_2026_08_08.md`'s todos 1-4.** Once
      batch9's todos 2-4 ship, flip that source doc's matching `- [ ]` checkboxes (its own todo 1↔2 map to batch9's
      combined `_AR_REPO` todo, its todo 3 maps to batch9's trigger-cleanup todo, its todo 4 maps to batch9's
      `deployed_versions` todo) to `[x]`, citing the batch9 commit SHA(s) for each. Do NOT touch its todo 5
      (`[OPERATOR] P3` AWS IAM read-access decision) — that stays open, `assigned_vm: NA`, not this batch's scope.
      Confirm the source doc is NOT an archival candidate afterward (todo 5 remains open by design). (repo:
      unified-trading-pm)
- [ ] [REVIEW] P3. **Note G2's resolution against `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s Deferred
      item 3.** That item is prose documentation (not a live checkbox) recording why the 0.10.8-constant move was
      originally parked. Once batch9's todo 1 ships, add a one-line dated note to that Deferred entry pointing at
      `infra_satellite_ao_dispatch_batch9_2026_08_09.md`'s commit as the resolution (batch1 itself stays active — it has
      its own unrelated open todo, the E2E login-helper chain — this is a citation-accuracy fix only, not a
      reconciliation of a checkbox). (repo: unified-trading-pm)
- [ ] [DOC] P3. **Archive `infra_satellite_ao_dispatch_batch9_2026_08_09.md`** once both todos above are done and both
      reconciliations are verified — run the standard 6-step archival ritual (`git mv` to `plans/archive/2026_08/`, fix
      every corpus referrer path, confirm `check_ag_closeout_linkage.py` and `regenerate_active_plan_inventory.py` both
      stay clean). Do this as a SEPARATE commit from the checkbox-flip commits above (never combine a flip + `git mv` in
      one commit — 2026-07-30 incident, `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`). (repo:
      unified-trading-pm)

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual + the
  never-combine-flip-with-git-mv rule
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule this plan satisfies

## Progress Log

- **2026-08-09** — Authored alongside `infra_satellite_ao_dispatch_batch9_2026_08_09.md` by `/ag-closeout-audit infra`
  (autonomous mode, scheduled daily run, slot 22, dispatch agt-3b6f6b).
