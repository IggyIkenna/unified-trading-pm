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

- [x] ✅ [REVIEW] P1. **Re-verify batch13's done-claim against reality** — re-run
      `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py --only plans/active/*.md plans/active/issues/*.md`
      and confirm the reported `unsourced_ruling_baseline` matches the claimed value; spot-check a sample of the cited
      fixes against their sources. **Done when**: independently confirmed, any discrepancy re-opened as a new tracked
      todo here. **VERIFIED — no discrepancy.** `--only` is precommit-scoped (checks only staged files; nothing staged →
      trivial 0), so the meaningful re-run is the corpus-wide default invocation:
      `python3 scripts/quality_gates/check_plan_operator_ruling_evidence.py` →
      `Unsourced operator-ruling citations: 2     (baseline 2)` — matches batch13's claimed final baseline (52→4→2,
      Progress Log 2026-08-10 entry) exactly. Both remaining flagged lines are the 2 batch13 itself named as
      deliberately-unrecoverable: `ao_open_issues_consolidated_close_out_2026_07_17.md:407` (AO state-home ruling) and
      `data_completion_defi_2026_07_15.md:223` (DeFi-volatility removal) — confirmed present verbatim at those lines,
      neither has a traceable source doc in the corpus (grep-confirmed), consistent with batch13's own reasoning for
      leaving them unfixed. Spot-checked 4 of batch13's claimed fixes against their cited sources, all traceable and
      accurate: (1) `ao_open_issues...:399` — reworded "Operator ruling needed"→"Decision needed", confirmed present;
      (2) `pm_scripts_typecheck_debt_2026_06_11.md:101/112` cites
      `/plans/archive/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 row "87" — table row confirmed:
      "Narrow 'can never red' claim + bump off P3" → "pm_scripts_typecheck_debt edit incl. zero-warning-policy caveat",
      matches the citing text exactly; (3) `defi_pipeline_e2e_and_coverage_validation_2026_06_20.md:89` cites the same
      doc's §A2 row "46" — confirmed: "Phase-D gate checkbox REOPENED" → "revert to [ ] + dependent real-data re-run
      todo", matches; (4) `sports_consolidated_closeout_2026_07_19.md:724-726` cites
      `/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md` todo 17 — doc exists, citation traceable.
      No discrepancies found — no new todo needed. Repo: unified-trading-pm.
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
- **2026-08-10 (slot-18, review)** — Flipped todo 1: independently re-verified batch13's done-claim, no discrepancy. See
  the todo's own checkmark text for full evidence.
