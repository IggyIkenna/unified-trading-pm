---
doc_type: issue
title:
  agent /reply always posts to the sender's OWN role thread (direction=from_agent) — main→peer-role "replies" are
  silently never delivered to that role's /poll, a session-long one-way cross-role blind spot
summary: >-
  On 2026-07-22 the review-role agent (agt-dc5ab1) reported that its /poll returned messages:[] on every tick for ~2.5h
  even though main had sent it 5 replies (msgs 1615/1617/1620/1622/1624) — which it only found by directly querying
  /api/agents/by-role/main/history. Root cause is NOT the poll-drain / pending-count logic (that is correct). It is the
  /api/agents/<id>/reply endpoint: it ALWAYS posts to the SENDER's own role thread with direction=from_agent
  (routes/agents.py:618-625 -> post_agent_message_by_role(target_role=agent.role, direction="from_agent")). So when main
  (agt-b8247c, role=main) "replied to review" via its own /reply endpoint, the messages were persisted as
  target_role=main / from_agent — an already-delivered response in the MAIN thread, never enqueued as a to_agent
  deliverable for review's poll. review's drain_agent_pending correctly matches only target_role==review AND
  direction==to_agent, so it never matched them; count_pending_to_agent(review)=0 was likewise correct (zero unanswered
  to_agent msgs for review). Net: any time an agent uses /reply to answer a DIFFERENT role, the answer is silently
  invisible to that role's /poll. Verified by re-sending the ACK via the correct channel (POST
  /api/agents/by-role/review/message, direction=to_agent, msg 1627) — that path delivers + tmux-nudges correctly.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags:
  [agent-orchestrator, agent-messaging, cross-role-reply, poll-drain, silent-drop, blind-spot, routing, worker-comms]
related:
  [
    plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md,
  ]
created: "2026-07-22"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
source: [review-role-bug-report-1626, main-orchestrator-triage]
resolved_by:
locked_by:
locked_since:
depends_on: []
---

# What was reported

The review-role agent (`agt-dc5ab1`, the only active review agent, registered continuously since 23:32) reported via
`POST /api/agents/by-role/main/message` (msg 1626, 2026-07-22 02:20Z) that:

- `/api/agents/agt-dc5ab1/poll` returned `messages: []` on every tick this session (6+ ticks over ~2.5h),
- yet `/api/agents/by-role/main/history` showed **5 replies from main** (msgs 1615/1617/1620/1622/1624) it never
  received via poll — found only by directly querying the history endpoint,
- and `GET /api/agents` showed its `pending_count=0` / `needs_operator_count=0` the entire time.

The review agent hypothesized the poll-drain / pending-message-count logic was broken for `role=review`.

# Root cause (verified — it is NOT the poll-drain / counter logic)

The poll-drain and counters are **correct**. The defect is upstream on the **sender** side.

`POST /api/agents/{agent_id}/reply` (`server/routes/agents.py:604-635`) resolves the sender's own role and posts the
reply to **that** role's thread as an already-delivered response:

```python
# routes/agents.py:618-625
msg = ss.post_agent_message_by_role(
    session,
    target_role=agent.role,          # <-- the SENDER's role, always
    direction="from_agent",          # <-- delivered_at stamped now; NOT a pollable to_agent msg
    from_role=agent.role,
    content=req.content,
    sender_agent_id=agent_id,
)
```

`post_agent_message_by_role` (`server/state_store/agents.py:703-729`): `direction="from_agent"` sets `delivered_at=now`
immediately — the row is a response the dashboard reads, never a `to_agent` item queued for anyone's `/poll`.

So when main (`agt-b8247c`, role=main) "replied to review" through its own `/reply` endpoint, each reply was persisted
as `target_role="main"` / `direction="from_agent"` — landing in the **main** role's history (exactly why review found
them under `by-role/main/history`), and never enqueued for review.

review's `drain_agent_pending` (`state_store/agents.py:749-758`) correctly selects only:

```python
AgentMessageRow.target_role == agent.role,      # == "review"
AgentMessageRow.direction == "to_agent",
AgentMessageRow.answered_at.is_(None),
```

main's replies were `target_role="main"` / `from_agent` → they never match → `messages: []` every tick. Likewise
`count_pending_to_agent("review")` (`agents.py:792-803`) returned 0 because there were genuinely **zero unanswered
`to_agent` messages for review** — the counter was accurate, not broken.

**The only endpoint that actually reaches a role's `/poll` is `POST /api/agents/by-role/{role}/message`**
(`routes/agents.py:662-715` → `direction="to_agent"` + a best-effort tmux nudge). Confirmed live: re-sending the ACK to
review via that endpoint delivered correctly (msg **1627**, `direction:to_agent`).

# Why it matters

- **Silent one-way cross-role blind spot.** Any agent that uses `/reply` to answer a _different_ role produces a reply
  that is invisible to that role's `/poll`. The recipient has no signal it's missing anything (`pending_count=0` is
  "correct"), so it can act on stale information indefinitely — here, review would have kept re-flagging slot 14 forever
  had it not discovered the `history` workaround.
- The `/reply` endpoint is the natural, documented thing to reach for ("reply to the message"), and the main loop's own
  step-2 instruction says to answer via `/api/agents/<main-id>/reply` — which is **correct for OPERATOR messages** (they
  arrive as `target_role=main`, so `/reply` acks + posts to the main thread the operator reads) but **wrong for
  answering a peer role**. The trap is that both cases look identical at the call site.
- No work lost this instance (review found the history endpoint; main re-sent via the correct channel). This is a
  correctness/latency defect in inter-role comms, not data loss.

# Candidate fixes (operator / careful review — this is the orchestrator's own comms path; do NOT dispatch blind)

1. **First-class cross-role reply (recommended).** Add an optional `to_role` (and/or `in_reply_to`-derived target) to
   the `/reply` request: when the message being answered has a `from_role` different from the sender's role, route the
   reply as `direction="to_agent"` to that originating role (plus the tmux nudge), instead of posting `from_agent` to
   the sender's own thread. This makes "reply to whoever asked me" correct by construction and closes the trap.
2. **Guard-rail / loud path split.** If a full `to_role` param is deemed too broad, at minimum have `/reply` detect when
   `in_reply_to` points at a message whose `from_role != agent.role` and either (a) auto-redirect to
   `by-role/<from_role>/message`, or (b) reject with a 400 that names the correct endpoint — so a mis-address fails loud
   instead of silently.
3. **Procedure/docs (interim, zero-code).** Document that answering a _peer role_ MUST use
   `POST /api/agents/by-role/<role>/message` with `from_agent_id=<mine>`, and that `/reply` is own-thread-only (for
   operator/dashboard-facing responses). Update `main.md` step-2 to distinguish "reply to operator" (`/reply`) from
   "answer a peer role" (`by-role/<role>/message`). Main has already adopted this behavior as of 2026-07-22.

Recommended order: (3) immediately (already in effect for main), then (1) as the real fix; (2) only if (1) is considered
too large.

# Notes

- Filed `assigned_vm: NA` / `execution_scope: local-only`: this modifies the orchestrator's own agent-messaging routing,
  where a careless change to the `to_agent` / `from_agent` semantics could break the reply-ack / redelivery-cap
  machinery (`ao_operator_message_silent_drop_no_reply_ack_2026_07_08`) or the dashboard history thread. Operator should
  review the routing predicate before it dispatches. Same worker-safety-automation class as
  `wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md` and
  `quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md`.
- Interim mitigation already live: main now answers non-operator roles via `by-role/<role>/message` (proven by msg
  1627). The 5 stranded replies (1615/1617/1620/1622/1624) were already read by review via the history workaround, so no
  re-send of those is required.

# Codex SSOTs

- `codex/04-architecture/agent-orchestrator-overview.md` (agent messaging / poll-reply model).
- `codex/04-architecture/agent-orchestrator-alerting.md` (adjacent: role-directed notification routing).
