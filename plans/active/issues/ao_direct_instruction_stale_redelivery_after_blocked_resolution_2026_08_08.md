---
doc_type: issue
title:
  "AO direct-instruction dispatch redelivers a stale message citing an already-resolved blocked-question/escalation —
  confirmed 4x same-day (2026-08-08) across both review and worker roles"
summary: >-
  A "Direct instruction from main" message citing escalation `BLK-091671d7` / DP-VM-001 (`agt-fe0635`) — asking the
  recipient to investigate/relaunch for the `expected-universe-v2-sports` halt-safety false-page — kept getting
  delivered to fresh agent sessions on 2026-08-08 well AFTER the underlying issue was fully root-caused and fixed
  (`deployment-service@27fd5779`, shipped 2026-08-07, confirmed ancestor of `origin/live-defi-rollout`). Four
  independent sessions hit the identical stale instruction the same day: (1) a na-eligibility-audit pass, (2) review
  agent slot 1 instance A, (3) a worker on `config_key_contract_drift-002`, (4) review agent slot 1 again (message id
  4072, 09:39Z). Every session independently verified the fix was already shipped and did NOT redo the work or ship
  duplicate code — no live harm — but this burns real agent-turns fleet-wide re-verifying the same closed item, and a
  less careful session could re-implement already-shipped work or waste a dispatch slot. `BLK-091671d7` itself is NOT
  present in the live `/api/state` `blocked_queue` (checked 2026-08-08T09:40Z) — confirming this is not an
  unanswered-blocked-question redelivery, but something in the direct-instruction dispatch/queueing path itself
  (per-slot inbox, backlog-generation artifact, or similar) that isn't being cleared once the underlying escalation
  resolves. Root cause not yet investigated — flagged by review (not in review's scope to chase); this doc exists so the
  pattern is tracked as a general AO-infrastructure gap, not just noted in one issue's Progress Log.

  Note: an earlier attempt this same session to file this exact tracking doc was dispatched directly to slot 11 (`POST
  /api/slots/11/message`, ack'd `{"slot_id":11,"ok":true}`) but never landed on origin — slot 11 had already moved on to
  a different backlog task (`sports_taxonomy_p1_capture_and_contracts-009`, assigned 09:31:10Z, after the 09:2xZ
  dispatch) by the time it was checked, so the direct instruction was silently dropped/superseded rather than actioned.
  Filing directly from main this time rather than risking a second lost dispatch — itself a small data-point for the
  same underlying dispatch-doesn't-survive-a-busy-slot class of gap discussed in
  `/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`'s Progress Log.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, dedup, direct-instruction, blocked-queue, false-positive, alert-fatigue]
related: [/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md]
created: 2026-08-08
author: agt-30eb02 (main)
priority: P2
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
source: >-
  Review agent (slot 1) flagged the 4th same-day recurrence in chat (message id 4072, 2026-08-08T09:39:23Z). Main
  independently confirmed `BLK-091671d7` is absent from the live `blocked_queue` and that a prior same-session attempt
  to file this doc via slot 11 was itself lost to a busy-slot dispatch race, then filed this doc directly.
---

# AO direct-instruction dispatch redelivers a stale message after its underlying blocked-question/escalation resolves

## What happens

A "Direct instruction from main" message citing a specific blocked-question/escalation id can remain queued somewhere in
the dispatch path and get delivered to a worker or review-agent session AFTER the underlying blocked-question/escalation
has already been resolved and its fix already shipped and verified live. This causes idle/fresh sessions to spend cycles
re-verifying already-fulfilled work instead of it being a no-op.

## Evidence (2026-08-08)

The DP-VM-001 false-page fix (`deployment-service@27fd5779`, shipped 2026-08-07 by slot-2, confirmed ancestor of
`origin/live-defi-rollout`) was independently re-litigated **four** separate times on 2026-08-08 by sessions that each
received the same stale direct-instruction text citing escalation `BLK-091671d7` / `agt-fe0635`:

1. A na-eligibility-audit pass.
2. Review agent (slot 1), instance A.
3. A worker session on `config_key_contract_drift-002`.
4. Review agent (slot 1) again — message id 4072, 2026-08-08T09:39:23Z, explicitly noting this was its own 2nd hit and
   the 4th fleet-wide.

Full technical detail of the underlying (already-fixed) issue is in
`/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`'s Progress Log (entries
"na-eligibility-audit 2026-08-08" and "review agent (slot 1) 2026-08-08").

`BLK-091671d7` was checked against the live `/api/state` `blocked_queue` on 2026-08-08T09:40Z and is **not present** —
ruling out a simple "unanswered blocked-question redelivers on every poll" explanation. Whatever is re-queueing this
instruction is not visible in the blocked-queue itself.

## Root cause — CONFIRMED (review agent, slot 1, 2026-08-08, live DB + code read)

Not a blocked-question/escalation bug at all — confirmed structural gap in the `SlotMessageRow` delivery primitive
itself (`agent-orchestrator/server/state_store/activity.py`), verified by reading the live `data/state/state.db`
(read-only) plus the delivery code:

1. `POST /api/slots/{slot_id}/message` (`server/routes/slots_ops.py:75-85`) is the send path main used for this
   instruction (and for every other free-text "Direct instruction from main — bypasses backlog" send). Its
   `SendMessageRequest` body has **no `task_id` field at all** — the handler always calls
   `ss.enqueue_message(session, slot_id, text=req.text, from_role=req.from_role)` with `task_id` implicitly `None`.
2. `enqueue_message`'s own docstring (`activity.py:277-286`) says leaving `task_id` unset is correct for "general
   slot-directed notices (git-health alerts, operator broadcasts) that aren't tied to one task's lifecycle" — but a
   one-shot "go implement fix X" instruction is NOT that kind of message; it has no live condition to keep re-checking,
   it either got done or didn't.
3. `take_pending_messages` (`activity.py:289-367`) is the read/redeliver path. For a `task_id IS NULL` row, the ONLY way
   `answered_at` ever gets stamped is `redelivery_count >= max_redeliveries` (default 30, `server/config.py:893`) —
   there is **no ack/reply primitive for `slot_messages` at all**, by explicit design (class docstring: "task workers
   have no reply endpoint... 'unanswered' is unobservable for them"). Every NEW `claude_session_id` on the target slot
   (any fresh spawn — a respawn, a task-boundary reset, a review-agent recycle) re-satisfies the
   `delivered_to_session != live_session` redelivery predicate, so the message is handed to literally every future
   session on that slot until the 30x cap, with **zero way for a recipient session to close it early** even after
   independently confirming the underlying ask is already fulfilled.
4. This design is CORRECT for the notices it was built for (a dirty-worktree nag SHOULD re-show to a fresh session — the
   fresh session can re-check the live condition and the redelivery is doing real work). It is the wrong bucket for a
   one-shot ask, and main's own `POST /message` endpoint has no other bucket to put one in.

**Confirmed live blast radius (2026-08-08, queried directly against `data/state/state.db`, read-only)**: this is not one
stale message — **15 distinct "Direct instruction from main — bypasses backlog" message campaigns** are currently
unanswered (`answered_at IS NULL`), spanning **18 rows across 12 distinct slots** (0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11,
15), `redelivery_count` ranging 0–17 out of the 30 cap (none capped yet, several past halfway: slot 9 at 17, slots 4 and
10 at 16, slot 2 at 14). Every one of these campaigns is structurally unable to close early, for the identical reason —
this is the general shape of every message main sends through this endpoint, not a one-off. One row (id 5883, slot 15)
is main's own follow-up explicitly titled "CORRECTED / REPLACES an earlier garbled message I just sent to this slot" —
even main's manual attempt to retract a mistake did not (and structurally could not, since no supersede/ack path exists)
mark the original (id 5882) answered; both are still live and independently redelivering today.

This confirms the review/main hypothesis's shape (independent of role, independent of physical slot — a fresh
`claude_session_id` on ANY slot re-triggers delivery) but the actual mechanism is simpler and fully deterministic: no
race, no queueing artifact, no per-escalation state — just a redelivery predicate with no early-exit for
`task_id IS NULL` messages.

## Blast radius

Low-severity so far — every hit was caught by careful independent verification before any wasted code work — but not
guaranteed to stay that way: a less careful session could re-implement already-shipped work, or waste a dispatch slot
re-investigating a closed issue. Four confirmed hits in one day on a single stale instruction is a real, measurable
rate, not a one-off. Also relevant: this doc's own first same-session filing attempt (via a direct slot-11 dispatch) was
itself silently dropped when the target slot picked up other backlog work first — suggesting direct-instruction delivery
in general doesn't reliably survive a slot that's mid-task, which is adjacent to (but distinct from) the
stale-redelivery problem this doc is primarily about.

## Todo

- [x] [INFRA] P3. Root-cause why the `BLK-091671d7` / DP-VM-001 direct instruction survived at least 4 respawn/dispatch
      cycles after its underlying escalation was resolved on 2026-08-07 — CONFIRMED 2026-08-08 (review agent, slot 1).
      See "Root cause — CONFIRMED" above: `POST /api/slots/{id}/message` never sets `task_id`, so every free-text direct
      instruction falls into the `task_id IS NULL` "general notice" bucket, which has no ack path short of the 30x
      redelivery cap. Not escalation-state-related — no dedup against `blocked_id`/escalation `answered_at` exists or is
      needed; the fix belongs in the message-delivery primitive itself (see the new todo below). Evidence: direct read
      of `server/state_store/activity.py` (`enqueue_message`/`take_pending_messages`) + a live, read-only query against
      `data/state/state.db` (15 distinct unanswered "Direct instruction from main" campaigns, 18 rows, 12 slots,
      `redelivery_count` up to 17/30).
- [ ] [INFRA] P2. Implement the fix: add an explicit close/ack primitive for `slot_messages` so a one-shot instruction
      can terminate the moment ANY recipient session confirms it's fulfilled/stale, instead of waiting out up to 30
      redeliveries across up to 30 future sessions. Recommended shape (mirrors the `agent_messages`/`/reply` pattern
      that already solves this exact problem for the main/review/chat channel):
      `POST /api/slots/{slot_id}/messages/{message_id}/ack` stamps `answered_at` immediately; update
      `unified-trading-pm/agents/worker.md` + `review.md` so a session that reads a "Direct instruction from main"
      message and determines the ask is already done (by someone else, or moot) calls this before continuing, closing
      the loop the same turn rather than leaving it to expire. Bonus: accept an optional `supersedes_message_id` on
      `POST /api/slots/{slot_id}/message` so a correction (e.g. id 5883 correcting garbled id 5882 — both still live
      today) auto-acks the message it replaces. Cheaper interim mitigation if the new endpoint is non-trivial: let
      `SendMessageRequest` carry a `max_redeliveries` override (e.g. 2-3) for one-shot sends, distinct from the 30
      default that's correctly tuned for recurring notices (git-health, etc.) — bounds the blast radius without a new
      endpoint. Done-when: a session that acks a one-shot instruction (or hits the lowered cap) stops seeing it
      redelivered to the NEXT fresh session on that slot, verified live against a real send, not just a unit test.
- [ ] [INFRA] P3. Separately check whether `POST /api/slots/{id}/message` direct instructions are reliably durable
      against a slot that's mid-task when the message arrives (this doc's own first filing attempt was lost this way) —
      confirm whether the message is genuinely dropped in that case, or whether it should have queued and simply hasn't
      been checked long enough yet; if genuinely dropped, that is a second, related dispatch-durability gap worth its
      own fix.

## Progress Log

- **review agent (slot 1) 2026-08-08**: Root-caused live (see "Root cause — CONFIRMED" above) via direct, read-only
  inspection of `data/state/state.db` (`slot_messages` table) cross-referenced against
  `server/state_store/activity.py`'s `enqueue_message`/`take_pending_messages` and `server/routes/slots_ops.py`'s
  `post_message` handler — no speculation, no DB writes (read-only `sqlite3` URI connection throughout; did not mutate
  live server state). This session's own hit was message id 5866 (slot 1, `redelivery_count=6` at read time,
  `delivered_to_session` matching this session's own id verbatim) — the 5th confirmed same-day redelivery of the
  identical `BLK-091671d7` text fleet-wide, and independently re-verified (again) that `deployment-service@27fd5779`'s
  exit_code=5 carve-out + both regression tests are still intact at `origin/live-defi-rollout` HEAD — no code changes
  needed, nothing to ship for the underlying DP-VM-001 finding. Went further than prior sessions (which correctly
  flagged this as outside review's code-editing scope but didn't chase the server-side mechanism) by tracing the exact
  live DB rows and confirming the fix belongs in the message-delivery primitive, not the exit_code=5 handling. Updated
  Todo 1 to `[x]` with evidence, added Todo 2 with a concrete recommended fix shape, left implementation to a worker
  session (out of review's own `does_not: edit/commit code` scope). Flagged to main via chat with the same summary + a
  recommendation to reconsider this doc's priority given the confirmed scope (15 distinct active campaigns, not one
  message) — decision left to main/operator.
- **main (agt-30eb02) 2026-08-08**: independently verified review's root-cause before acting on it — read
  `server/routes/slots_ops.py:76-78` directly (confirmed `post_message` calls `enqueue_message(...)` with no `task_id`
  arg, `SendMessageRequest` in `server/models/worker_api.py:274-278` has only `text`/`from_role` fields, no ack route
  exists for `slot_messages` in `slots_ops.py`) and independently re-ran the blast-radius query against the live
  `data/state/state.db` (read-only):
  `SELECT COUNT(*), COUNT(DISTINCT slot_id) FROM slot_messages WHERE answered_at IS NULL AND text LIKE '%Direct instruction from main%'`
  → 18 rows / 12 slots, matching review's numbers exactly. Accepting the priority-bump recommendation: **P3 → P2** (doc
  frontmatter + Todo 2, the actual fix) — this is no longer a single stale-message annoyance but a confirmed structural
  gap hitting 12 of 16 slots simultaneously with no self-resolution short of a 30x redelivery cap; Todo 3
  (dispatch-durability against a busy slot) stays P3 as a smaller, separately-scoped follow-up. Leaving implementation
  to normal AO dispatch (Todo 2 is properly scoped + determinable, per dispatch-eligibility rules) rather than
  personally implementing it.
