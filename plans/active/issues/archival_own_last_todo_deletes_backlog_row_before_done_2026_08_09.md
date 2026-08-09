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
resolved_by:
archive_exempt: true
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

- [x] ✅ [BACKEND] P2. Root-cause in `regen_backlog_from_plan.py` (or wherever the row-deletion actually happens):
      confirm whether a row for a task whose source doc just left `plans/active/` is deleted immediately on next regen
      tick, or only after some grace window — and whether `/done` could instead special-case "row missing but a
      `slot_done`-shaped call just arrived within N seconds of a matching archival commit" to still record completion
      before deleting. Done when: the deletion path is identified precisely (file + line), and either a fix ships or a
      documented decision states the current 404-then-skip-current-task recovery is an acceptable, cheap-enough steady
      state (bounded blast radius, no lost work). Repo: agent-orchestrator. — documented decision, no new code needed
      here (a fix already shipped same-day under a sibling issue that fully subsumes this scenario); see Progress Log.
- [x] ✅ [DOCS] P3. If the decision above is "no fix, current behavior is acceptable", add a one-line callout to
      `plans/active/task_template.md`'s finalize-plan-coverage section (or
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) telling a worker landing an
      archive-is-the-last-todo task to expect this exact `/done` 404 and go straight to `skip-current-task` with
      `reason_code: "OTHER"` instead of retrying blindly. Repo: unified-trading-pm. — MOOT: the shipped fix means a
      worker landing this exact shape no longer sees a 404/500 at all, so no such callout is needed; see Progress Log.

## Progress Log

- **2026-08-09 (slot 25, infra)**: Filed while completing
  `autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize-002`. Recovery used in the moment:
  `skip-current-task` with `reason_code: "OTHER"` and a full explanation in the reason field — server confirmed
  `orphaned_stale_marker: true`, row will not re-dispatch. All actual plan/doc work independently verified on origin
  before filing this doc; nothing here blocks or reopens that work.
- **2026-08-09 (slot 26, backend_engineer)**: Root-caused todo 1 by direct source read of
  `agent-orchestrator/server/regen_backlog_from_plan.py`. **Deletion path (file + line, no grace window)**:
  `_prune_stale()`'s orphan detection (lines 2992-2997) treats ANY yaml task whose `brief` is no longer among the
  currently-open todos (`_parse_open_todos` over the live `plans/active/` scan) as an orphan and unconditionally strips
  it from `backlog.tasks` (line 3005) — this fires on the very FIRST `PlanRegenLoop` tick after the checkbox flips
  and/or the doc leaves `plans/active/`, with no explicit grace-window delay coded; the only bound is the tick cadence
  itself (`config.plan_regen_interval_seconds`, default 600s). The SQLite `TaskRow` is NOT deleted by this same pass —
  the literal `DELETE FROM tasks` (line 3040) is scoped to `status IN ('queued','blocked') AND dispatched_to IS NULL`,
  which an actively-dispatched row never matches; a dedicated "done-not-removed race" check (lines 3055-3096) instead
  either leaves a still-live dispatched row alone (if the plan file is still readable with the todo checked) or flips it
  to terminal `status='cancelled'` (never deleted) once the source file is gone. Then found this is a **duplicate root
  cause of a sibling issue already filed, fixed, and archived TODAY**:
  `plans/archive/2026_08/issues/ao_done_and_skip_500_on_backlog_yaml_removed_orphan_task_2026_08_09.md` (slot 33 → 3 →
  6, `status: resolved`). That doc traced the exact same mechanism from the `/done`-caller side: `backlog.get(task_id)`
  (the in-memory YAML lookup `done_slot`/`skip_current_task` both use) returns `None` once `_prune_stale` has stripped
  the yaml entry, even though the SQLite `TaskRow` can still be `status=dispatched` — and BOTH `/done` and
  `/skip-current-task` previously mishandled that split state (500s), not merely 404s. Fix shipped same-day:
  `agent-orchestrator@3147392` (`done_slot` now calls the new `_maybe_close_orphaned_done_task` — releases the slot,
  deletes the dead `TaskRow`, returns a clean 200 instead of crashing) + `agent-orchestrator@4f78629`
  (`skip_current_task`'s `task_orphaned` predicate fixed to also treat `backlog_task is None` as orphaned, guarded
  against clobbering an already-terminal `done`/`cancelled` row) + `agent-orchestrator@8db0b29` (end-to-end regen-driven
  reproduction test, confirms both routes close the orphan cleanly with no exception). Verified this fix is live on
  `origin/live-defi-rollout` in this slot's already-fresh-pulled `agent-orchestrator` clone. **Answering todo 1's own
  question directly**: no time-window special-case was built (nor is one needed) — the shipped fix instead checks orphan
  status AT CALL TIME (`backlog.get(req.task_id) is None`) rather than correlating timestamps against an archival
  commit, which is strictly more robust (works regardless of how long the gap was, or whether the archival was the SAME
  worker's own last todo — this doc's exact scenario — or a prior session's). This makes todo 1's documented-decision
  branch the applicable one: **no new code needed from this todo** — the fix already covers this doc's precise "archival
  is my own last todo" shape (confirmed by re-reading `_maybe_close_orphaned_done_task`'s logic: it keys only on
  `task_def is None`, with no dependency on who performed the archival). Todo 2 is consequently MOOT — since `/done` no
  longer 404s/500s on this shape at all, no "expect this and go straight to skip-current-task" doc callout is needed;
  flipping it closed rather than writing a now-inaccurate callout. Recovery guidance for the tiny remaining edge (SQLite
  row itself somehow already gone, e.g. a genuinely stale/cleared dispatch pointer) still exists via
  `skip-current-task`'s `orphaned_stale_marker` path, now correctly handled per the sibling fix.
