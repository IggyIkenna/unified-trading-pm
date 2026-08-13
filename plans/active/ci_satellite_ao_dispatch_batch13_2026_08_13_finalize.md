---
doc_type: plan
title: ci satellite AO batch 13 — finalize
summary: >-
  Gated closeout for ci_satellite_ao_dispatch_batch13_2026_08_13.md — machine-held via depends_on + gate_on_depends
  until every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source doc's
  checkbox (this was an extraction batch, so the source docs' own checkboxes are the ones that go stale), archives any
  source doc that reaches zero open todos as a result, and runs the standard 6-step archival ritual on the batch plan
  itself.
status: active
nature: process
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ci, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [/plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md, /plans/active/ci_consolidated_closeout_2026_07_25.md]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ci_satellite_ao_dispatch_batch13_2026_08_13]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-sweep session. Ships
  status: active (not draft) per the /ag-closeout-audit skill's 2026-07-30 finding: gate_on_depends already
  machine-holds every task until the batch's own todos are done, so a second draft-gate is redundant.
---

# ci satellite AO batch 13 — finalize

> **Machine-gated on `/plans/active/ci_satellite_ao_dispatch_batch13_2026_08_13.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [ ] [REVIEW] P2. For every completed todo in `ci_satellite_ao_dispatch_batch13_2026_08_13.md`, reconcile the evidence
      back into its cited `Source:` doc's own checkbox — find the matching item in the source doc and either flip it
      `[x]` with a citation to this batch's commit, or add a note pointing at the batch todo that superseded it. Do not
      trust the batch's own checkbox alone; re-verify each cited commit sha is real. Done when: every source doc touched
      by this batch has its corresponding item's checkbox state reconciled.
- [ ] [REVIEW] P2. For each source doc reconciled above, check whether it now has zero open todos. If so, run the
      standard 6-step archival ritual on it (dated archive folder, exact-successor banner if applicable, corpus-wide
      referrer-path fixup) — do not leave a now-fully-done source doc live and un-archived. Done when: every source doc
      left with zero open todos is archived, and `run_hygiene_sweep.sh` reports no orphan referrers to any of them.
- [ ] [REVIEW] P2. Once `ci_satellite_ao_dispatch_batch13_2026_08_13.md` itself has zero open todos, run the standard
      6-step archival ritual on it, then archive this finalize plan too. Done when: the batch plan and this finalize
      plan are both under `plans/archive/`, and `regenerate_active_plan_inventory.py` reports zero orphan referrers to
      either.
