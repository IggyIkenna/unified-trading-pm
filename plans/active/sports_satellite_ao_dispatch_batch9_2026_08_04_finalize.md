---
doc_type: plan
title: Sports satellite AO batch 9 — finalize (reconcile source docs)
summary: >-
  Gated closeout for sports_satellite_ao_dispatch_batch9_2026_08_04.md — machine-held via depends_on + gate_on_depends:
  true until all 30 of that plan's todos are done. Mirrors the batch2-8-finalize pattern: reconcile each of the 17
  distinct source docs' checkboxes once its batch-9 todo(s) land, then archive both docs.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, ao-dispatch, close-out, batch-9, satellite-docs]
related:
  [
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-04"
last_updated: "2026-08-06"
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [sports_satellite_ao_dispatch_batch9_2026_08_04]
gate_on_depends: true
source: >-
  /ag-closeout-audit sports tranche run, 2026-08-04, per task_template.md §4's finalize-plan-coverage rule — every
  assigned_vm: planning plan needs a companion gated finalize plan, mirroring the batch2-8 precedent. Authored status:
  active from the start (not draft) per the 2026-07-30 no-double-gate finding recorded in the ag-closeout-audit skill:
  gate_on_depends already machine-holds every todo below regardless of the parent batch's own draft/active status, so a
  second manual flip on this doc would be redundant.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/sports_satellite_ao_dispatch_batch9_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/sports_satellite_ao_dispatch_batch8_2026_07_30_finalize.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
---

# Sports satellite AO batch 9 — finalize

> **Machine-gated on `sports_satellite_ao_dispatch_batch9_2026_08_04.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 30 tasks in that plan are `done`. `sequential: true` because
> todo 1 needs the parent plan's evidence to reconcile source docs correctly.

## Todos

- [ ] [REVIEW] P1. **Reconcile source-doc checkboxes for all 30 batch-9 todos.** Each batch-9 todo ends with a `Source:`
      line naming one of 17 distinct source docs — flip (or add, for prose-only items) the corresponding remaining-work
      marker there, citing the batch-9 commit(s) that shipped it. Verify every cited commit/evidence actually exists
      before citing it (`git merge-base --is-ancestor <sha> origin/live-defi-rollout`, or for diagnosis-only todos,
      re-verify the stated finding yourself rather than trusting the batch-9 todo's own claim). For the 3 combined
      `mdps_sports_honest_absence_writes_fail_fetchevidence_gate_2026_08_01.md` todos specifically, confirm each of the
      6 original findings (3, 4, 5, plus the ruled-option-A implementation) is individually accounted for, not just the
      combined todo checked off. **Done when**: every Source-cited doc has its corresponding item flipped/updated with
      verified evidence, across all 17 source docs.
- [ ] [DOC] P2. **Archive `sports_satellite_ao_dispatch_batch9_2026_08_04.md` (and this finalize doc) once both are
      terminal**, per CLAUDE.md's plan-archival ritual: re-verify the Deferred section's 84 items are still accurately
      taxonomy-tagged (a conflict-gated item may have cleared, an operator-gated item may have been ruled since) before
      carrying any still-live ones forward into a tracked note for a future `batch10` → add the archive banner → confirm
      no new durable contract needs a codex update (this batch establishes none) → grep the corpus for every referrer of
      `sports_satellite_ao_dispatch_batch9_2026_08_04` and fix each path to the archived location → clear `locked_by`
      (already empty; confirm). **Done when**: both docs are in `plans/archive/2026_08/`, every corpus referrer resolves
      to the new path, and `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` is 0-hard-failures afterwards.

## Codex SSOTs

None new — see the parent batch's own Codex SSOTs section.

## Progress Log

- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
