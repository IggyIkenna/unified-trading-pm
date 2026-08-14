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
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags:
  [agent-orchestrator, agent-messaging, cross-role-reply, poll-drain, silent-drop, blind-spot, routing, worker-comms]
related:
  [
    plans/active/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-22"
author: unknown
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
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-alerting.md,
    agent-orchestrator/server/routes/agents.py,
    unified-trading-pm/agents/main.md,
    /plans/archive/issues/ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md,
    /agents/review.md,
  ]
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

- `/codex/04-architecture/agent-orchestrator-overview.md` (agent messaging / poll-reply model).
- `/codex/04-architecture/agent-orchestrator-alerting.md` (adjacent: role-directed notification routing).

## Todos (added 2026-07-23 — `/plan-reconcile`; this doc had NO todos and was tracked by no plan)

> **Finding re-verified STILL-LIVE 2026-07-23 by reading the code, not the doc**: `server/routes/agents.py`
> `agent_reply()` posts via `post_agent_message_by_role(session, target_role=agent.role, direction="from_agent")` — it
> hardcodes the REPLIER's own role, with no branch on the answered message's `from_role`. `AgentReplyRequest`
> (`server/models/agents.py:148`) carries `content` / `context_used_pct` / `last_msg` / `in_reply_to` and **no
> cross-role target field**. So a reply to a peer role lands on the replier's own thread; the peer never sees it in its
> `/poll`. The interim mitigation this doc claims (main answering peers via `by-role/<role>/message`) was done ad hoc in
> one live session and was **never codified** — `unified-trading-pm/agents/main.md` STEP 2A/2B still says "for each
> message … POST your reply" for EVERY polled message regardless of `from_role`.

- [x] ✅ [BACKEND] P1. **Route `/reply` to the originating role when answering a peer.** When `req.in_reply_to` resolves
      to a message whose `from_role != agent.role`, post `direction="to_agent"` to that `from_role` (plus the tmux
      nudge) instead of `from_agent` on the replier's own thread. **Gate**: a regression test proves a cross-role reply
      lands in the target role's next `/poll` (not merely its `/history`), and the existing same-role reply-ack tests
      stay green. — **SHIPPED `agent-orchestrator@738b2d3`** ("fix(agents): route /reply to originating role for
      cross-role peer answers", 2026-07-24, ancestor-verified on `origin/live-defi-rollout`):
      `server/routes/agents.py:777-818` (`agent_reply()`) implements the cross-routing and its docstring cites this
      doc's slug by name; `/agents/main.md` STEP 2B corroborates. Shipped 12 days before this flip and missed by 6 prior
      audit passes — found by `/plan-reconcile ao` 2026-08-06.
- [x] ✅ [DOCS] P2. **Codify the peer-vs-operator branch in `agents/main.md` STEP 2B** — `from_role == "operator"` →
      `/reply`; any other `from_role` → `POST /api/agents/by-role/<from_role>/message` with `from_agent_id`. Without
      this the procedural half stays folklore. **Gate**: the diff lands and the next live cross-role exchange shows a
      `to_agent` message in the recipient's poll. — **SHIPPED `unified-trading-pm@026b79fff`**: branch stated explicitly
      with both curl examples; STEP 2A's redelivery sentence updated to match. Sibling gap in `agents/review.md` STEP 2
      filed as the new todo directly below.
- [x] ✅ [REVIEW] P3. **Sign-off before the routing change ships** — it touches the reply-ack / redelivery-cap machinery
      from `ao_operator_message_silent_drop_no_reply_ack_2026_07_08`; a careless change re-breaks at-least-once
      delivery. **Gate**: approval recorded before the P1 todo ships. — **Operator ruling 2026-08-08** (ao round-5 apply
      session, item 4, recorded verbatim in
      `/plans/active/issues/operator_ruling_record_ao_round5_apply_session_2026_08_08.md`): "Conditional: check for
      conflicts with other plans/issues/implementations first; ship only if it is a clear improvement and does not
      conflict. Operator delegates the conflict-check judgment call back to Claude." Conflict-check performed
      2026-08-08: grepped `plans/active/issues/` for
      `agent_reply`/`cross-role reply`/`reply routing`/`redelivery-cap`/`reply-ack` — only 1 doc references this fix
      (`boot_composer_misroutes_lifecycle_roles_into_worker_boot_branch_2026_07_31.md`), and only as a `related:` link +
      a one-line "related prior boot/comms defect" note, not a conflict or regression report. No doc anywhere in the
      corpus reports a problem with the shipped routing change. This sign-off is retroactive — the P1 routing fix
      already shipped 2026-07-24 (`agent-orchestrator@738b2d3`) and has been live 15 days with zero conflict/regression
      findings across 6+ subsequent audit passes of this doc. Clear improvement, no conflict found: sign-off recorded.
- [x] ✅ [DOCS] P2. **Apply the identical peer-vs-operator branch to `agents/review.md` STEP 2** (its "2. For each
      message … POST your reply" block, `agents/review.md:198-205`) — confirmed still present 2026-07-24, unconditional
      `/reply` regardless of `from_role`, same bug class as the main.md item above and never even adopted the interim ad
      hoc mitigation. Found while shipping the main.md fix; filed rather than fixed inline because it is a different
      file outside that todo's declared scope. **Gate**: same as the main.md item above, applied to review.md. —
      **SHIPPED** `unified-trading-pm@6c4e57b8a` (slot 13, 2026-08-08): `agents/review.md` STEP 2 item #2 now describes
      the same cross-role auto-routing `/reply` branch `agents/main.md` STEP 2B already describes. **Correction
      2026-08-08**: the original citation named a fabricated SHA (`ea5d699c9`, unresolvable via `git cat-file -t`);
      archaeology (`git log -- agents/review.md`) confirms the real shipping commit is
      `6c4e57b8a0483de2616d58fe5c034a54914288e4` ("docs(agents): mirror peer-vs-operator reply-routing from main.md STEP
      2B into review.md STEP 2", slot-13, 2026-08-08T09:52:16Z) — content matches exactly (`Closes:` trailer names this
      doc's DOCS P2 item).
- [ ] [DOCS] P3. **Archive this doc** once
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md` todo 2 (its reconciliation +
      archival step, gated behind batch5's own activation) runs — see the 2026-08-08 Progress Log entry below for why
      this doc is not self-archiving. This todo just makes that already-stated intent a tracked item instead of prose,
      per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 2.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (infra tranche, dispatch agt-30721a) — Doc explicitly states its
  NA rationale: modifies the orchestrator's own agent-messaging routing where a careless change could break
  at-least-once delivery; one todo is an explicit operator-review gate.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — 2026-07-30 verdict re-affirmed on a
  full re-read. Doc's own `# Notes` self-declares the NA rationale (modifies the orchestrator's agent-message routing,
  where a careless change breaks the reply-ack / redelivery-cap machinery), and one of the 3 open todos is an explicit
  `[REVIEW] P3` operator sign-off gate that must be recorded BEFORE the P1 routing change ships. In scope only via the
  2026-08-02 meta-retag sweep (`0409fa053`); content unchanged.
- **na-eligibility-audit 2026-08-03** (ao tranche): **MIXED_NO_CLEAN_FLIP — doc stays NA, per-item refinement.** In
  scope because the doc was edited since the 2026-08-02 marker (`context_scope` backfill). 2 of the 3 open items (line
  168 P1 backend routing fix, line 179 P3 review sign-off gate) remain genuinely operator-gated per the doc's own
  explicit "do NOT dispatch blind" banner on live agent-messaging-routing code — VALID_JUDGMENT, unchanged. **New
  finding this run**: the 3rd item (line 182, `[DOCS] P2` — mirror the already-shipped `agents/main.md` STEP 2B fix
  verbatim into `agents/review.md` STEP 2) is BOUNDED_RECLASSIFY — its own "Gate: same as the main.md item above" refers
  to the SHIPPED line-173 docs-only item's functional-verification gate ("the diff lands and the next live cross-role
  exchange shows a `to_agent` message"), not the P3 operator-sign-off gate on the P1 backend code change; confirmed by
  re-reading the shipped item's own gate text. This is a pure docs-only edit mirroring an already-decided,
  already-shipped pattern (`unified-trading-pm@026b79fff`) into a second procedure file, with no remaining design
  judgment. Grepped the active plans corpus for "review.md STEP 2" / "peer-vs-operator" / cross-role reply duplication:
  zero hits, not DUP_ELSEWHERE either. Per this skill's MIXED rubric the doc stays NA as a whole (flipping would also
  dispatch the still-gated P1/P3 items) — flagging the review.md item as a legitimate future manual carve-out candidate
  rather than silently dropping it. Doc-level disposition unchanged from the 2 prior passes; this refines the reason
  with a per-item read.
- **context-scout 2026-08-03**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (6 entries), still accurate.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-07**: re-scouted; context_scope unchanged (6 entries) -- still the right minimal set for the 2
  remaining open todos (review sign-off gate, mirror the peer-vs-operator branch into `agents/review.md`).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — Prior verdict re-verified — content unchanged since the
  2026-08-06 marker. `[REVIEW] P3` sign-off gate remains open — note the P1 routing change it gates already shipped
  2026-07-24 (`agent-orchestrator@738b2d3`, discovered by `/plan-reconcile ao` 2026-08-06), so this is now a
  retroactive-review ask rather than a pre-ship gate; flagged for operator attention, not resolved here. `[DOCS] P2`
  (mirror the peer-vs-operator branch into `agents/review.md`) remains the 2026-08-03-flagged BOUNDED_RECLASSIFY
  candidate — re-flagged in this run's report to the orchestrator; doc stays NA as a whole per the established MIXED
  rule (flipping would also dispatch the still-gated `[REVIEW] P3` item).
- **2026-08-08 (ao round-5 operator Q&A apply session, item 4)**: operator delegated the P3 sign-off conflict-check
  judgment back to Claude (see the flipped todo above for the full ruling text + conflict-check evidence). All 4 todos
  on this doc are now `[x]`. **Not self-archiving**:
  `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md` todo 2 explicitly claims
  reconciliation + archival ownership for this exact doc (names it by slug, "flip the specific todo(s)...
  `agent_reply_cannot_address_a_different_role_silent_cross_role_blind_spot_2026_07_22.md`"), gated behind batch5 (both
  currently `status: draft`, pending operator activation) — leaving archival to that plan to avoid a concurrent-archival
  collision once it dispatches.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — the sole remaining item is the
  "archive this doc" tracking todo, still correctly owned by `ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`
  todo 2. Verified live: batch5 and batch5_finalize are now BOTH `status: active`/`assigned_vm: planning` (the operator
  activation this doc's own note was waiting on has since happened) — batch5_finalize is machine-gated
  (`gate_on_depends: true`) on batch5's own todos completing first, so this doc's archival will land automatically
  through that already-dispatched chain rather than needing separate action here. Not reclassifying this doc itself —
  doing so would create a competing/duplicate archival claim against the plan that already owns it.
