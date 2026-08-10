---
doc_type: issue
title:
  "A blocked-question answer can be silently delivered into an unrelated task once its slot is force-reassigned —
  SlotMessageRow delivery is keyed by slot_id alone, with no task_id/dispatch-generation check"
summary: >-
  Operator-traced scenario (2026-08-06): a worker on slot N asks a blocked question (`BlockedRow`, slot.status set to
  "blocked"). The slot is then force-reassigned — `POST /api/slots/{slot_id}/reassign` with `kill_worker=true`
  (`routes/slots_ops.py:620-719`) is gated only on `slot.current_task is not None`, NOT on `slot.status`, so it can kill
  and free a blocked slot despite the watchdog's explicit "never kill a blocked slot" rule. A brand-new, unrelated task
  gets dispatched onto the same slot_id and runs for hours. Meanwhile the ORIGINAL BlockedRow is still open. When it is
  finally answered via `answer_blocked_endpoint` (`routes/backlog.py:945-1105`), the tmux nudge is accidentally safe
  (gated on `slot.status == "blocked"`, which is no longer true), but `ss.enqueue_message(session, row.slot_id, ...)`
  runs unconditionally, and the delivery table (`SlotMessageRow`, write + read in `state_store/activity.py:242-305`) is
  keyed ONLY by `slot_id` — no `task_id`, session id, or dispatch-generation check anywhere in that path. The stale
  "BLOCKED Q answered: …" message is folded straight into the new, unrelated agent's next `/boot`, `/heartbeat`, or
  `/progress` response (`routes/slots_worker.py:598,624` etc.) — injected into a task that has no idea what question is
  supposedly being answered. `POST /api/slots/{slot_id}/skip-current-task` (`routes/slots_ops.py:722-835`) has the same
  gap (checks `slot.current_task is not None`, not `slot.status`). The codebase fixed a structurally identical "stale
  per-slot state bleeds into the new occupant" bug once before for a different mechanism (`_prereq_blocked_since`, see
  `/plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md:626-641` and its fix
  `ao_dispatch_liveness_p0_2026_07_20.md`) — this is the same shape, unfixed, for blocked-question message delivery.
status: open
nature: issue
asset_group: [ao]
scope: [engineer]
stage: [meta]
repos: [agent-orchestrator]
tags: [agent-orchestrator, blocked-queue, worker-liveness, dispatch, slot-reassign, message-delivery, operator-reported]
related:
  [
    /plans/archive/issues/ao_blocked_question_not_retired_when_condition_resolves_2026_08_06.md,
    /plans/archive/issues/ao_blocked_slot_no_timeout_or_redispatch_policy_2026_08_06.md,
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-06
author: agent
last_updated: 2026-08-06
priority: P2
parent_epic: orchestrator_master
source:
  "operator-directed, interactive session — operator asked what happens when slot N is force-reassigned to a new task
  while an earlier blocked question on that slot is still open and later gets answered; traced end-to-end in code and
  confirmed a real cross-delivery gap rather than a no-op"
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/server/routes/slots_ops.py,
    agent-orchestrator/server/routes/backlog.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/state_store/activity.py,
    agent-orchestrator/server/blocked_reconcile.py,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
---

# Blocked-answer message delivery is not scoped to the dispatch it was raised for

## Why this matters

`reassign_slot` and `skip-current-task` are the only two code paths that can move a blocked slot onto new work (the
liveness watchdog refuses to touch `status == "blocked"` everywhere else — `worker_liveness_watchdog.py:764-766,1160`,
`/codex/04-architecture/agent-orchestrator-worker-liveness.md:378`). Neither of them clears or orphans the `BlockedRow`
still pointing at that slot_id, and neither the write nor the read side of `SlotMessageRow` knows that a message was
meant for a specific task, not a specific slot number. The result: answering an old blocked question after its slot has
moved on doesn't error, doesn't no-op, and doesn't silently vanish — it gets handed to whichever unrelated task is
currently running on that slot, injected directly into that task's next boot/heartbeat/progress payload. A worker
mid-task on something completely unrelated can suddenly see "[operator] BLOCKED Q <label>: <answer>" show up in its
context with no way to know what question it refers to.

## Todos

- [x] ✅ [INFRA] P2. **Scope `SlotMessageRow` delivery to the dispatch it was raised for.** Add a `task_id` (or a
      dispatch-generation id, e.g. `slot.claude_session_id` at enqueue time) to `SlotMessageRow`. On write
      (`answer_blocked_endpoint`, `blocked_reconcile.py`'s auto-answer paths), stamp the id of the task/session the
      `BlockedRow` was raised against. On read (`take_pending_messages`, `state_store/activity.py:246-305`), only
      deliver a message to a session that is still working the task_id (or session id) it was stamped with; otherwise
      leave it undelivered and log it (`blocked_message_orphaned_by_reassign` or similar) rather than silently handing
      it to whoever polls next. Add a regression test reproducing the exact scenario: slot N blocked → force-reassign
      with `kill_worker=true` → new unrelated task dispatched to slot N → old `BlockedRow` answered → assert the new
      task's next boot/heartbeat/progress response does NOT contain the stale message. — **SHIPPED, checkbox was stale**
      — `agent-orchestrator@365e18e` (same day, a different session working the companion doc) implements exactly this:
      optional `task_id` column on `SlotMessageRow`, stamped at both call sites named above, `take_pending_messages`
      orphans (never delivers, marks terminal, logs `blocked_message_orphaned_by_reassign`) a task-scoped message once
      `slot.current_task` no longer matches. Regression test present: `tests/test_slot_message_task_scoped_delivery.py`
      reproduces the exact scenario this todo specifies. Found via na-eligibility-audit 2026-08-07 cross-checking the
      companion doc's Progress Log, which cites this same commit.

- [ ] [INFRA] P3. **Resolve or flag orphaned `BlockedRow`s at reassign time.** When `reassign_slot`
      (`routes/slots_ops.py:620-719`) or `skip-current-task` (`routes/slots_ops.py:722-835`) moves a slot off a task
      that still has an unanswered `BlockedRow`, either (a) explicitly retire it with a distinct disposition
      (`auto_orphaned_slot_reassigned`), consistent with how `blocked_reconcile.py`'s `classify_retirement()` already
      handles task-terminal/doc-archived retirement, or (b) at minimum surface it on the dashboard as "orphaned — its
      slot moved on" so an operator answering it later isn't misled into thinking the answer reaches anyone. Prefer (a)
      if todo 1's task-id scoping already makes the answer a guaranteed no-op for the original asker — an orphaned row
      with a guaranteed-dead delivery path is exactly what the existing retirement sweep is for.

## Progress Log

### 2026-08-06 — filed (interactive session)

Traced end-to-end while answering the operator's question about slot-reuse-while-blocked. Confirmed via direct code read
(not just grep) that the tmux nudge is accidentally gated safe (`slot.status == "blocked"` check at answer time) but the
underlying `SlotMessageRow` enqueue/delivery path has no equivalent scoping — `slot_id`-only on both write and read. Not
yet reproduced against a live prod row; scenario is grounded in code reachability, not an observed incident.

- **na-eligibility-audit 2026-08-07** (tranche=ao, autonomous): KEEP-NA, stale items — todo 1 was already shipped same
  day by a parallel session (`agent-orchestrator@365e18e`, verified via direct commit/diff/test read, not just the
  citation) while working the companion doc `ao_blocked_slot_no_timeout_or_redispatch_policy_2026_08_06.md`; closed with
  evidence above. Todo 2 stays open and stays NA: it is a genuine `(a) or (b)` design choice (new `BlockedRow`
  disposition vs. dashboard-only surfacing), P3, no stated done-when/acceptance test — not re-litigated here even though
  todo 1 landing makes "(a)" the doc's own stated preference, since choosing and implementing a new retirement
  disposition is still a real judgment call, not a mechanical follow-on.

### context-scout 2026-08-07

Populated/refreshed context_scope (6 entries) — swapped `orm.py` (generic, never named in the doc's own body) for
`blocked_reconcile.py`, which both open todos explicitly name by function (`auto-answer paths`,
`classify_retirement()`).

### na-eligibility-audit 2026-08-09 (round11)

KEEP-NA, valid — re-checked the sole open todo (`[INFRA] P3`, resolve-or-flag orphaned `BlockedRow`s at reassign time)
against the round7-10 precedent set; none apply. The doc's own text states a preference for option (a) now that todo 1
landed, but choosing + implementing a NEW retirement disposition in `classify_retirement()` remains a real judgment call
(per the 2026-08-07 marker's own reasoning), not a fully-specified mechanical follow-on — no done-when is stated either.
Corroborated same-day: `/ag-closeout-audit ao` batch12 independently lists this doc under operator-gated (22), declined
zero-extraction.

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: KEEP-NA, valid — full re-read of the sole open
  item ((a)-or-(b) design choice for orphaned `BlockedRow` disposition at reassign time, P3, no stated done-when).
  round11 (2026-08-09) already confirmed this is a genuine judgment call, not a mechanical follow-on despite todo 1's
  landing. No new facts found this pass.
