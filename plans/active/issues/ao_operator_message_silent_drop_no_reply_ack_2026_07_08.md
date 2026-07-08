---
doc_type: issue
title:
  "Operator→agent chat messages are silently dropped — delivery is marked on POLL (drain), not on REPLY, with no
  reply-ack and no redelivery; the main agent has answered no operator message since 2026-06-29"
summary:
  'Operator noticed the main agent (orch-agent-main / agt-eabad6) never answers questions in the dashboard chat, while
  the review-agent chat is full of messages. Root-caused 2026-07-08. TWO layers. Layer 1 (durable bug): operator→agent
  delivery is at-most-once and marked delivered on the POLL that drains it —
  server/state_store/agents.py::drain_agent_pending stamps delivered_at=now on every undelivered to_agent message it
  returns, and future polls only return delivered_at IS NULL. The agent must SEPARATELY POST /reply; nothing links drain
  to reply. So any loop tick that polls (drains) but does not complete the reply step (tick ended, a mid-tick /compact
  dropped the messages from working memory, or the LLM simply skipped STEP 2B) permanently consumes the message with
  ZERO operator-visible signal — no answered_at, no redelivery, no "delivered-but-unanswered" surfacing. Layer 2
  (trigger): the main agent has drifted into a heads-down monitoring /loop and keeps compacting (context 13%); main.md
  STEP 2C only handles "messages empty → do nothing", with no path for "drained but could not answer this tick", so it
  triggers Layer 1 on nearly every tick. Confirmed concrete loss: operator questions id=641 + id=643 (2026-07-07 11:01)
  were delivered to agt-eabad6 and never answered; agents.last_msg frozen at "641" for ~19h; last from_role=main chat
  message is 2026-06-29. NOT caused by the 2026-07-08 ao_dispatch_correctness deploy (predates it by ~9 days). Fix =
  make operator→agent delivery at-least-once with reply-ack (Option A) or add a redeliver-unanswered reconcile loop
  (Option B), plus dashboard visibility for unanswered questions and a loop-hardening so a /compact cannot lose a
  drained-unanswered message.'
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, operator-chat, message-delivery, reply-ack, at-least-once, silent-drop, main-agent, reliability]
related: []
created: 2026-07-08
parent_epic: orchestrator_master
priority: P1
source:
  'Operator, 2026-07-08: "the main agent have not sent any messages to the chat, I asked couple of questions to it but I
  havent received any answers... please check properly whats happening there?" Investigated during the
  ao_dispatch_correctness deploy session; root-caused via live DB + tmux pane + code read (drain_agent_pending /
  agent_poll / agent_reply / send_to_role).'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: backend-engineer
drift_direction: advance-code
locked_since:
---

# Operator→agent chat: silent message drop (no reply-ack, no redelivery)

## Symptom (operator-reported, 2026-07-08)

The **main agent never answers** in the dashboard chat; the operator asked "a couple of questions" and got no reply. The
**review-agent chat is full of messages** — but those are the review agent's OWN automated `REVIEW tick-NNNN` fleet
summaries (every ~15 min, `review->review`), not the main agent's answers. Main answered nowhere.

## Evidence (live state at 2026-07-08 ~06:26 UTC)

- Main agent `agt-eabad6` (session `orch-agent-main`): `status=active, online=1, last_ping≈10s` — **alive and
  heartbeating**, context only 13%. Its pane loops "✻ Running scheduled task", emits internal status ("blk=0, queued=1,
  dispatched=2 … parked on gate flips"), and polls itself.
- Operator questions **delivered but never answered**:
  - `id=641` (2026-07-07 11:01:11) "what are the remaining 2 dispatched + 1 queued tasks?" —
    `delivered_at=2026-07-07 11:01:12`, `delivered_to=agt-eabad6`.
  - `id=643` (2026-07-07 11:01:46) "if 2 tasks are dispatched then why no worker is in working state?" —
    `delivered_at=2026-07-07 11:01:51`, `delivered_to=agt-eabad6`.
- `agents.last_msg` for main = **"641"** — frozen for ~19h (also a field-misuse: main.md wants a status STRING there,
  agent is stuffing a message-id).
- Last `from_role=main` chat message is **2026-06-29** — this main session (registered 2026-06-29 04:30) has produced
  **zero** operator replies in its life.
- `agent_messages`: `target_role=main` total=429, **undelivered=0** → delivery is not the miss; the agent
  receiving-then-not-replying is.

## Root cause

### Layer 1 — durable bug: delivery marked on POLL (drain), decoupled from REPLY, no redelivery

`agent_poll` → `drain_agent_pending()` is an **at-most-once drain**:

- [server/state_store/agents.py:621](../../agent-orchestrator/server/state_store/agents.py#L621) `drain_agent_pending`
  selects `to_agent` messages with `delivered_at IS NULL` and **stamps `delivered_at=now` on every one it returns**
  (agents.py:636). A future poll only returns `delivered_at IS NULL`, so a drained message is **never returned again**.
- [server/routes/agents.py:560](../../agent-orchestrator/server/routes/agents.py#L560) `agent_poll` calls the drain and
  returns the messages.
- [server/routes/agents.py:582](../../agent-orchestrator/server/routes/agents.py#L582) `agent_reply` is a **separate**
  call posting a `from_agent` message. **Nothing links drain → reply.**
- `agents/main.md` STEP 2B ("for each message … POST /reply") / STEP 2C ("if messages was empty, do nothing") assume
  reply always follows drain in the same tick; there is **no path for "drained but could not answer this tick."**

Consequence: any tick that polls (drains) but does not complete the reply step **permanently consumes** the message. No
`answered_at`, no redelivery, no operator-visible "delivered-but-unanswered" state. It is an at-most-once channel
presented as reliable — it will drop a message whenever poll and reply do not complete atomically in one tick.

### Layer 2 — trigger: the main agent's monitoring loop constantly drains-without-replying

The main agent runs a 60s `/loop` (config `DEFAULT_MAIN_LOOP_SECONDS`), but has drifted into a heads-down monitoring
cycle (gate-watching, "Cogitated for 31s") and keeps compacting (context 13%). A `/compact` between the drain (STEP 2A)
and the reply (STEP 2B) drops the just-drained messages from working memory — but Layer 1 already stamped them
delivered, so they are gone. This exposes Layer 1 on nearly every tick, so main has answered no one since 2026-06-29.

**Not deploy-caused** — predates the 2026-07-08 `ao_dispatch_correctness` deploy by ~9 days.

## Fix design

### Option A — at-least-once with reply-ack (recommended; correct end-state)

Stop treating drain as consumption. Delivery is complete only when the agent has ANSWERED.

- Add `answered_at` (+ optional `redelivery_count`) to `agent_messages`, applied idempotently by `bootstrap.py` at
  startup (same pattern as `slots.last_role`).
- `drain_agent_pending` returns `to_agent` messages that are **undelivered OR delivered-but-unanswered** (re-surfaced on
  every poll until answered), ordered oldest-first. Keep `delivered_at` as a "first-seen" timestamp; add
  `redelivery_count++`.
- `agent_reply` stamps `answered_at=now` on the outstanding unanswered `to_agent` message(s) for the agent's role (all
  currently-unanswered, or a specific `in_reply_to` id if the reply carries one).
- **Cap redelivery**: after N redeliveries / M minutes unanswered → mark `needs_operator=true`, stop redelivering, and
  surface it (so a genuinely-dead agent does not loop forever).

### Option B — redeliver-unanswered reconcile loop (lighter; no hot-path change)

Keep drain-on-poll, but add a background reconcile that finds `to_agent` messages with `delivered_at` set and **no
following `from_agent` reply** within M minutes → clear `delivered_at` (re-queue) + re-nudge the holder +
dashboard-flag. Smaller blast radius; fixes silent loss without touching the poll path. (A→correct; B→fast mitigation. B
can ship first, A can supersede.)

### Cross-cutting (both options)

- **Dashboard visibility**: surface "delivered, awaiting reply >N min" / count of unanswered operator questions so a
  drop is _visible_ instead of vanishing.
- **Loop hardening (main.md)**: before processing, persist drained-unanswered messages to a per-session scratch file,
  and add a STEP for "drained but could not answer → keep in scratch, retry next tick," so a mid-tick `/compact` cannot
  lose a message even under Option B.

## Todos

- [ ] [BACKEND] P1. Add `answered_at` (+ `redelivery_count`) to `agent_messages`, idempotent `bootstrap.py` migrate
      (mirror the `slots.last_role` add). (Option A)
- [ ] [BACKEND] P1. `drain_agent_pending`: return undelivered OR delivered-but-unanswered `to_agent` messages (redeliver
      until answered), oldest-first; increment `redelivery_count`. (Option A)
- [ ] [BACKEND] P1. `agent_reply`: stamp `answered_at` on the outstanding unanswered `to_agent` message(s) for the role
      (support optional `in_reply_to` id). (Option A)
- [ ] [BACKEND] P2. Redelivery cap: after N redeliveries / M min unanswered → set `needs_operator`, stop redelivering.
      Config knobs. (Option A)
- [ ] [BACKEND] P2. (Alt / mitigation-first) Redeliver-unanswered reconcile loop that re-queues + re-nudges
      delivered-but-unanswered messages after M min. (Option B — can ship before A)
- [ ] [UI] P2. Dashboard: surface unanswered operator questions ("delivered, awaiting reply >N min") per role so a
      silent drop is visible.
- [ ] [DOCS] P2. Harden `agents/main.md` loop: persist drained-unanswered messages to a scratch file before processing;
      add a "drained-but-unanswered → retry next tick" step (survive `/compact`).
- [ ] [BACKEND] P3. Fix the `last_msg` field misuse (main.md wants a status STRING; agent sends a message-id) so the
      dashboard "current activity" is not frozen at a stale id.
- [ ] [TEST] P1. Unit tests: drain→no-reply→next drain STILL returns the message; `/reply` stamps `answered_at`;
      redelivery cap fires; regression reproducing the 641/643 silent drop.
- [ ] [BACKEND] P2. Verify the `send_to_role` tmux nudge reliably wakes a heads-down `/loop` (`tmux_spawn.nudge` →
      `_nudge_message`); if flaky, make it idempotent + retried.

## Immediate remediation (operator-gated — NOT part of the code fix)

The two lost questions (641/643) are already gone from the queue; the durable fix will not resurrect them. To restore
main's responsiveness NOW: **respawn `orch-agent-main`** (fresh session; context is only 13% so minimal loss) so it
starts a clean, responsive `/loop`, then **re-send the questions**. Operator earlier chose "investigate root-cause" over
an immediate respawn — respawn remains available on your go. (Meanwhile the fleet is separately degraded: tasks
`understat_local_backfill_completion-001` [slot 7] and `v1_enumerator_dispatch_not_deletable-009` [slot 6] are
orphaned-dispatched — their slots last pinged ~4h ago — which is the real answer to operator question 643; that
fleet-reclaim gap is a separate issue worth its own doc.)

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what happened>.` -->

- **2026-07-08** — Filed. Root-caused the silent-drop (drain-on-poll, no reply-ack/redelivery — Layer 1; main agent
  monitoring-loop drain-without-reply — Layer 2) from live DB + tmux pane + code read during the
  `ao_dispatch_correctness` deploy session. Human plan (`assigned_vm: NA`), operator-chosen. Fix Option A
  (at-least-once + reply-ack) recommended; Option B (reconcile loop) as ship-first mitigation. No code shipped yet —
  design captured for operator review.
