---
doc_type: issue
title:
  "A todo whose own work IS archiving its plan deletes its own backlog row before /done can be called — every
  finalize-plan archival todo hits this"
summary: >-
  Worked `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize-002` ("archive the parent doc") to
  completion: flipped the checkbox with evidence (`unified-trading-pm@ce659757d`), then — since both the finalize plan's
  own todos were now done and unlocked — archived the finalize plan itself in the immediately-following commit per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` (`unified-trading-pm@dc6715618` + `c78ae0fcb`).
  Calling `POST /api/slots/25/done` for that same task_id then 404'd: `"task ... not found in backlog"`. `POST
  /api/slots/25/skip-current-task` confirmed the mechanism: `"orphaned_stale_marker":true`, `"next_step":"task's
  plan-todo is no longer dispatchable (BLOCKED-*/removed) — row deleted, will not be re-dispatched"`. Root cause
  (inferred from behavior, not yet code-confirmed): `regen_backlog_from_plan.py` derives backlog rows only from
  `plans/active/*.md` todos; once the source doc leaves `plans/active/` (archived), the next regen tick has nothing to
  derive that row from and deletes it — even though the row's own task_id is the one that JUST did the archiving, inside
  the same worker session, moments before it tried to call `/done`. This is not a rare race: ANY todo whose own "done
  when" is "archive this now-fully-done plan" (the standard shape of every finalize plan's last todo, per
  `plans/active/task_template.md`'s finalize-plan-coverage rule) will hit this every single time it's the archival step
  itself, because the archival necessarily removes the doc from the glob the regen scans before the worker's own `/done`
  call can land. The underlying WORK is not lost (checkbox flip + archival both verified on `origin/live-defi-rollout`),
  only the orchestrator's own SQLite done-bookkeeping/dashboard-visibility for that specific task_id.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, backlog, regen, archival, done-gate, dispatch, finalize-plan]
related:
  [
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
    /plans/active/issues/regen_positional_task_ids_not_content_stable_2026_07_17.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-08-09
author: slot-25-infra
priority: P2
parent_epic: orchestrator_master
source:
  "slot-25, infra, 2026-08-09 — hit live while archiving
  autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize_2026_08_08.md's own todo 2; confirmed via
  skip-current-task's orphaned_stale_marker response, not speculation"
execution_scope: orchestrator-agent
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [
    agent-orchestrator/server/regen_backlog_from_plan.py,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md,
  ]
---

# Archival-as-own-last-todo deletes its own backlog row before `/done` — structural, not a rare race

## What I found

A worker (this session) completed a finalize plan's last todo, whose own "done when" was to archive that same plan.
Following the ritual correctly (flip first as a plain edit, `archive_exempt: true` bridge, THEN `git mv` in a follow-up
commit) meant the plan doc left `plans/active/` inside the same worker session, before the worker's own `POST /done`
call for that todo's task_id. `/done` 404'd (`"not found in backlog"`); `/skip-current-task` confirmed the row was
already deleted (`orphaned_stale_marker: true`), not merely stale.

This is structural: `task_template.md`'s finalize-plan-coverage rule means every AO-dispatched plan gets a companion
finalize plan whose LAST todo is almost always "archive the (now fully-done) parent/self". Whichever worker lands that
exact todo will hit this every time, not occasionally — the archival step's own success condition is "leave
`plans/active/`", which is also the backlog-derivation glob's scan root.

**Blast radius, honestly bounded**: the real work (checkbox flip, archival, referrer fixes) is fully verified on
`origin/live-defi-rollout` regardless of this gap — nothing is lost or silently dropped. What's missing is the
orchestrator's own SQLite `done`-row bookkeeping and dashboard visibility for that one task_id, plus whatever
`slot_done_verified`/M-series audit signal downstream tooling (e.g. `audit_false_done.py`,
`ao_false_done_backlog_rows_and_unresolved_plan_refs_2026_08_08.md`) expects to see. A worker who doesn't recognize this
exact shape could easily read the 404 as "did I break something" and either retry blindly or leave the slot wedged —
this doc exists so the next worker (or `check-agent-orchestrator`) recognizes the pattern immediately.

## Todos

- [ ] [BACKEND] P2. Root-cause in `regen_backlog_from_plan.py` (or wherever the row-deletion actually happens): confirm
      whether a row for a task whose source doc just left `plans/active/` is deleted immediately on next regen tick, or
      only after some grace window — and whether `/done` could instead special-case "row missing but a
      `slot_done`-shaped call just arrived within N seconds of a matching archival commit" to still record completion
      before deleting. Done when: the deletion path is identified precisely (file + line), and either a fix ships or a
      documented decision states the current 404-then-skip-current-task recovery is an acceptable, cheap-enough steady
      state (bounded blast radius, no lost work). Repo: agent-orchestrator.
- [ ] [DOCS] P3. If the decision above is "no fix, current behavior is acceptable", add a one-line callout to
      `plans/active/task_template.md`'s finalize-plan-coverage section (or
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) telling a worker landing an
      archive-is-the-last-todo task to expect this exact `/done` 404 and go straight to `skip-current-task` with
      `reason_code: "OTHER"` instead of retrying blindly. Repo: unified-trading-pm.

## Progress Log

- **2026-08-09 (slot 25, infra)**: Filed while completing
  `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize-002`. Recovery used in the moment:
  `skip-current-task` with `reason_code: "OTHER"` and a full explanation in the reason field — server confirmed
  `orphaned_stale_marker: true`, row will not re-dispatch. All actual plan/doc work independently verified on origin
  before filing this doc; nothing here blocks or reopens that work.
