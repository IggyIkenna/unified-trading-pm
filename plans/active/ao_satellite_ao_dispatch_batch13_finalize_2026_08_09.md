---
doc_type: plan
title: AO satellite AO batch 13 — finalize
summary: >-
  Gated closeout for `ao_satellite_ao_dispatch_batch13_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends` until its sole todo is done. Reconciles the verified todo's evidence back into
  `operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`'s own checkbox, checks whether that source doc is
  now fully closed and archives it if so, then archives the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-13, finalize, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch13_2026_08_09.md,
    /plans/archive/issues/operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: review
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch13_2026_08_09]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch13_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch, 2026-08-09, per the satellite-batch-extraction pattern's mandatory finalize-twin rule.
---

# AO satellite AO batch 13 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch13_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until its sole todo is `done`. The batch itself stays `status: draft`
> until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P1. **Re-verify batch13's done-claim against reality** — re-run
      `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py --only plans/active/*.md plans/active/issues/*.md`
      and confirm the reported `unsourced_ruling_baseline` matches the claimed value; spot-check a sample of the cited
      fixes against their sources. **Done when**: independently confirmed, any discrepancy re-opened as a new tracked
      todo here.
- [ ] [REVIEW] P0. **Reconcile the verified todo's evidence into
      `operator_ruling_evidence_baseline_raised_58_to_76_2026_08_09.md`'s own `[SCRIPT] P2` checkbox** — replace the
      redirect-pointer text batch13 left behind with the real completion evidence. **Done when**: the source checkbox
      carries real evidence, not a bare redirect pointer.
- [ ] [REVIEW] P1. **Check whether the source doc is now fully closed** (both its todos done) — if so, run the standard
      6-step archival ritual on it. **Done when**: the doc's current open-todo count is confirmed, and it is archived
      with evidence cited here if fully closed.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch13_2026_08_09.md`, move to `plans/archive/2026_08/`, fix every
      corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then re-run the active-plan
      inventory generator. **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly,
      and `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`, `/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored in the same turn as batch13, per the mandatory finalize-twin rule (task_template.md §4).
  `sequential: true` since the 4 todos are a genuine chain. Ships `status: active` (not `draft`) — `gate_on_depends`
  already machine-holds every task until batch13's own todo is done, matching the batch7-12 finalize precedent.
