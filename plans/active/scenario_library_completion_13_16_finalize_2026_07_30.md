---
doc_type: plan
title: Finalize — scenario library completion (execution_slippage_spike + lst_unstake_queue_blowup)
summary:
  Gated close-out twin for scenario_library_completion_13_16_2026_07_27, reclassified NA -> planning by
  /na-eligibility-audit defi on 2026-07-30. Reconciles the source plan's checkboxes, confirms both ScenarioOverlay
  entries are genuinely consumed downstream, and checks archival eligibility once the source plan's todos are done.
status: draft
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-api-contracts, unified-trading-library, unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch, close-out, reclassification, na-audit, scenario-injection]
related:
  [
    /plans/active/scenario_library_completion_13_16_2026_07_27.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-30"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: backend_engineer
drift_direction: none
locked_by:
locked_since:
supersedes: []
superseded_by:
depends_on: [scenario_library_completion_13_16_2026_07_27]
gate_on_depends: true
source:
  [
    "/na-eligibility-audit defi, 2026-07-30 — paired finalize twin authored per
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md § 1(b) (retroactive reclassification:
    assigned_vm flipped in place, name unchanged, bolt-on finalize sibling dated the day of the pass).",
  ]
---

# Finalize — scenario library completion (13 + 16)

> **Gated twin.** `depends_on` + `gate_on_depends: true` hold every todo here until every todo in
> `/plans/active/scenario_library_completion_13_16_2026_07_27.md` is done. Do not start these before that.

## Todos

- [ ] [VALIDATE] P3. **Confirm both new `ScenarioOverlay` entries are genuinely consumed, not just registered.** Grep
      the `unified-trading-library` scenario applier + any smoke test / game-day runbook for `execution_slippage_spike`
      and `lst_unstake_queue_blowup` by their real registered `scenario_id`, and cite the consuming call site for each.
      **Done when**: a named consumer is cited per scenario, or the source plan's VALIDATE todo is re-opened with the
      concrete gap.
- [ ] [DOC] P3. **Reconcile the source-plan checkboxes + the two Day-1 design docs.** Confirm every todo in
      `scenario_library_completion_13_16_2026_07_27.md` is `- [x]` with a `<repo>@<sha>` citation, and update
      `plans/active/scratch_scenarios_day1/13_execution_slippage_spike.md` and `16_lst_unstake_queue_blowup.md` to name
      the registry entry that now backs each (they stay as design provenance, per the pattern set by scenarios 01-10).
- [ ] [PM] P3. **Check archival eligibility for the source plan.** If every todo is done and `locked_by:` is empty, run
      the standard 6-step archival ritual (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) for
      `scenario_library_completion_13_16_2026_07_27.md` and archive this finalize doc alongside it. If `locked_by:` is
      set, STOP and escalate for `[unlock-plan]` — never autonomous.

## Progress Log

- **2026-07-30** — Authored by `/na-eligibility-audit defi` as the paired finalize twin for a `NA -> planning`
  reclassification. The source plan cleared the shared conflict-check (§ 3 of the naming/conflict-check SSOT) against
  all 231 currently-active `assigned_vm: planning` docs: zero open todo anywhere in the corpus duplicates its claim.
