---
doc_type: plan
title: Content-derived backlog task ids — gated finalize (verify the migration actually held, then archive)
summary: >-
  Gated closeout for /plans/active/content_derived_backlog_task_ids_2026_08_08.md — machine-held via `depends_on` +
  `gate_on_depends: true` until every todo there is done. Exists because this particular migration's two failure modes
  are both SILENT: a missed `completed_tasks` remap un-gates a task with no error (`dispatch._completed_task_satisfied`
  treats an absent id as satisfied), and a renamed `dispatched` row only surfaces when a live worker 404s on its next
  `/done`. Neither shows up as a red gate at apply time, so "the migration ran without raising" is NOT evidence it was
  correct — this plan is the after-the-fact proof pass that says so, plus the standard source-doc reconciliation and
  archival ritual.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, task-id, migration, finalize, verification]
related:
  [
    /plans/active/content_derived_backlog_task_ids_2026_08_08.md,
    /plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
last_updated: "2026-08-18"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
effort: medium
sequential: true
drift_direction: advance-process
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [content_derived_backlog_task_ids_2026_08_08]
gate_on_depends: true
source: >-
  Required companion for the AO-dispatched parent plan (task_template.md §4 finalize-plan coverage); authored in the
  same 2026-08-08 interactive session as the parent.
context_scope:
  [
    /plans/active/content_derived_backlog_task_ids_2026_08_08.md,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/routes/slots_worker.py,
    /plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Content-derived task ids — gated finalize

> Held by `depends_on` + `gate_on_depends: true`. Do not start until every todo in
> `/plans/active/content_derived_backlog_task_ids_2026_08_08.md` is `[x]`.

## Why a verification pass, not just an archival ritual

Both of the parent plan's hazards fail **silently**. A migration that "ran clean" proves nothing about either:

- A `completed_tasks` entry that was never remapped does not error — it releases a downstream task that should still be
  blocked, and stays invisible until that task dispatches and does work it should not have done.
- A `dispatched` row renamed mid-flight only surfaces as a 404 on that worker's next `/done`, potentially hours later,
  by which point the work is done but uncloseable.

So the questions below are asked against **live state after the fact**, not against the migration's own exit code.

## Todos

- [ ] [BACKEND] P1. **Prove no task was silently un-gated.** Re-run the parent's pre/post prereq-remap assertion against
      LIVE `state.db` + `backlog.yaml` and confirm zero unexplained `completed_tasks`/`prerequisites` entries. Then
      cross-check dispatch history since the apply: any task that went `queued -> dispatched` whose upstream was still
      open at dispatch time is a silent un-gate and must be reported, not quietly re-blocked. (repo: agent-orchestrator)
- [ ] [BACKEND] P1. **Prove no in-flight worker was stranded.** Search the orchestrator log since the apply for a 404 on
      `/done`, `/progress` or `/blocked` carrying a task_id, and confirm zero. A hit means a `dispatched` row was
      renamed despite the deferral gate — recover that worker's shipped work before anything else. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P1. **Confirm `done_sha` audit history survived intact.** Compare the pre-apply map artifact against
      live rows: every `done` row must still carry its original `done_sha`/`done_at`/`done_evidence`, byte-identical,
      under whatever id it now has. This is the operator ruling's actual requirement ("not a fresh-start-only rewrite
      that abandons existing history"). (repo: agent-orchestrator)
- [ ] [BACKEND] P2. **Confirm the collision class is genuinely gone, not just quiet.** `grep -c "REFUSING to reset"`
      over a full `PlanRegenLoop` cycle must be 0, AND a deliberate test-only attempt to mint a colliding id must fail
      at the new collision check rather than silently succeed. Quiet logs alone are consistent with "regen stopped
      running", so assert the positive too. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. **Reconcile the source doc.** Update
      `/plans/archive/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md`: flip its content-hash-rewrite
      todo and its 2026-07-27 `dispatched`-row-gap todo with evidence, and record in its Progress Log that BLK-29884333
      was satisfied (properly-phased execution plan) rather than overridden. **Leave its `assigned_vm: NA` untouched** —
      it stays the analysis SSOT. (repo: unified-trading-pm)
- [ ] [BACKEND] P3. **Archive the parent plan** via the standard 6-step ritual per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`, fixing every corpus referrer. Archive this
      finalize plan in the same pass. (repo: unified-trading-pm)

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step ritual + referrer rule

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **2026-08-08 (interactive session, slot 1)**: Authored alongside the parent as its required gated finalize companion.
- **context-scout 2026-08-15**: populated context_scope (5 entries) — dropped `bootstrap.py` (not cited anywhere in this
  doc's own body); added `routes/slots_worker.py` (todo 2's hazard-1 target — `/done`/`/progress`/`/blocked` 404
  checks), the root-cause issue doc (todo 5's explicit reconciliation target), and the archival-discipline codex SSOT
  (todo 6 + this doc's own "Codex SSOTs" section).
