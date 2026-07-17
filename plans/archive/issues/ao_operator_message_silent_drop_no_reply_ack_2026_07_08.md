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
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, operator-chat, message-delivery, reply-ack, at-least-once, silent-drop, main-agent, reliability]
related: [ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md]
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
  - "agent-orchestrator@8076257 — at-least-once delivery + reply-ack: `drain_agent_pending` now returns
    delivered-but-UNANSWERED rows and bumps `redelivery_count` (agents.py:704); `mark_role_messages_answered` (:742)
    stamps `answered_at` only on an actual reply, called from `agent_reply` (routes/agents.py:629). Delivery is no
    longer marked on POLL. Idempotent migration + delivered->answered backfill (bootstrap.py:82)"
  - "agent-orchestrator@62d4da8f — orphaned dispatched-task reclaim (state_store/tasks.py:104 + watchdog wiring)"
  - "agent-orchestrator@da053a9 — tmux nudge now checks returncode and RAISES instead of silently reporting success
    (tmux_spawn.py:1424), with bounded retry/backoff"
  - "agent-orchestrator@fa73b5d — dashboard needs-operator delivery chip (layout.tsx:2465); this doc still marked it
    `[~] remaining` but it shipped under the sibling ao_dispatch_hardening plan"
  - "VERIFIED 2026-07-17 by independent skeptical audit: 4 SHAs reachable; regression suites RUN LIVE at HEAD —
    test_agent_message_redelivery (8 passed, incl. the 641/643 regression), test_orphaned_task_reclaim (7 passed),
    test_agent_nudge (7 passed), dashboard layout.test.ts (14 passed). NOTE: agents/main.md moved to
    unified-trading-pm/agents/ on 2026-07-10 (@5eaea29) — the prompt hardening SURVIVED the move; this doc's in-repo
    path citation is stale, the content is intact"
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
last_updated:
  "2026-07-13 (was: 2026-07-08 — verify-rerun-2 finding 191, corrected 2026-07-14 — Progress Log carries a 2026-07-13
  entry cross-referencing ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md; frontmatter never bumped)"
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
---

# Operator→agent chat: silent message drop (no reply-ack, no redelivery)

> **✅ ACKED-INTO-CODE 2026-07-17 — all todos closed; archived.** The `agent_messages` channel fix shipped at
> `agent-orchestrator@8076257`; the last two boxes (a superseded alternative and the `needs_operator_count` badge,
> `@fa73b5d`) were flipped 2026-07-17. `resolved_by` carries the SHAs + an independent audit that RAN the suites at
> HEAD.
>
> **The finding this doc did not know it had.** Fixing the `agent_messages` channel fixed it only for main/review/custom
> CHAT agents. The parallel `SlotMessageRow` channel that **craft task workers** use carried the identical bug and was
> never touched — surfaced by the 2026-07-16 sweep and fixed under
> [`ao_dispatch_hardening_2026_07_16`](../../active/ao_dispatch_hardening_2026_07_16.md) Phase 2b (`@d90f0f5`), which
> deliberately did **not** port this doc's redeliver-until-`/reply` design: task workers have no reply endpoint, so
> "unanswered" is unobservable for them and redelivering until an ack that can never arrive would risk duplicate
> ACTIONS. Delivery there is session-scoped instead. If you are reading this doc for the messaging contract, read that
> plan too — this one describes only half the system.

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

- [x] [BACKEND] P1. Add `answered_at` (+ `redelivery_count`) to `agent_messages`, idempotent `bootstrap.py` migrate
      (mirror the `slots.last_role` add) + a one-time delivered→answered backfill so deploy doesn't re-flood. (Option A)
      — ao@8076257 (`orm.py`, `bootstrap.py::_migrate_agent_message_reply_ack`)
- [x] [BACKEND] P1. `drain_agent_pending`: return undelivered OR delivered-but-unanswered `to_agent` messages (redeliver
      until answered), oldest-first; increment `redelivery_count`. (Option A) — ao@8076257 (`state_store/agents.py`)
- [x] [BACKEND] P1. `agent_reply`: stamp `answered_at` on the outstanding unanswered `to_agent` message(s) for the role
      via `mark_role_messages_answered` (optional `in_reply_to` id). (Option A) — ao@8076257 (`routes/agents.py`,
      `models/agents.py`)
- [x] [BACKEND] P2. Redelivery cap: after `agent_message_max_redeliveries` (default 30) unanswered → stops redelivering,
      surfaced via `count_needs_operator_to_agent` + `AgentView.needs_operator_count`. Config knob. (Option A) —
      ao@8076257
- [x] [BACKEND] P2. ✅ **WON'T-DO 2026-07-17 — decided, not deferred.** (Alt / mitigation-first) Redeliver-unanswered
      reconcile loop. **SUPERSEDED by Option A** — redelivery is now inline in `drain_agent_pending`
      (`routes/agents.py:704`), so a separate background loop is unnecessary and would be a second mechanism racing the
      first. Not shipping, and nothing is left open by that: the `[~]` only ever meant "an alternative we did not take".
- [x] [UI] P2. ✅ **DONE — shipped `agent-orchestrator@fa73b5d` under the sibling
      [`ao_dispatch_hardening_2026_07_16`](../ao_dispatch_hardening_2026_07_16.md) Phase 2b; flipped here 2026-07-17.**
      The box stayed `[~]` for a day AFTER the work landed — this doc's own `resolved_by` already recorded the sha while
      the checkbox still said "Remaining", which is the half-1-without-half-2 failure the commit-push-flip rule names.
      **Re-verified at HEAD (not trusted from the plan's claim)**: `deliveryChip` takes `needsOperatorCount` and renders
      the red "needs operator N" chip at `dashboard/src/layout.tsx:2469-2474`, wired at `:2538`/`:2588`; the
      `needs_operator_count` field is declared on `AgentView` at `dashboard/src/types.ts:447` — it had been **absent
      from the TS type entirely**, so the UI was structurally blind to a field the API already served. The
      `needsOperatorCount > 0` branch deliberately OUTRANKS "queued": in the realistic stuck case both counts are
      non-zero, so a `pendingCount`-first check would render the benign amber chip and the operator would never learn
      the agent had stopped answering. ~~**Remaining**: render a Vite badge for `needs_operator_count`.~~
- [x] [DOCS] P2. Harden `agents/main.md` loop: persist drained-unanswered messages to a scratch file before processing;
      add a "drained-but-unanswered → retry next tick" step (survive `/compact`). — ao@8076257 (`agents/main.md`)
- [x] [BACKEND] P3. Fix the `last_msg` field misuse (main.md now says status STRING, NOT a message-id). — ao@8076257
      (`agents/main.md`)
- [x] [TEST] P1. Unit tests: drain→no-reply→next drain STILL returns the message; `/reply` stamps `answered_at`;
      redelivery cap fires; 641/643 silent-drop regression; migration backfill. 8 tests, full QG green. — ao@8076257
      (`tests/test_agent_message_redelivery.py`)
- [x] [BACKEND] P2. ✅ **DONE 2026-07-16 — `agent-orchestrator@da053a9`.** Verified, and it was worse than this todo
      assumed: `send_command` called `subprocess.run` twice with `capture_output=True`, **no `check=`, and never
      inspected `returncode`** — so a failed `tmux send-keys` raised nothing and `nudge()` returned **True**, i.e. a
      send that never landed reported as delivered. Now raises on a non-zero send AND on a non-zero `C-m` submit;
      `nudge` retries (`nudge_attempts`, default 3). Retry follows ONLY a raised failure — a **successful** send is
      never repeated, because re-typing a delivered wake into a live pane risks the agent acting twice (pinned by a
      test; an unconditional retry loop would look tidier and be a bug). ~~Verify the `send_to_role` tmux nudge reliably
      wakes a heads-down `/loop` (`tmux_spawn.nudge` →~~ `_nudge_message`); if flaky, make it idempotent + retried.
      (Existing `test_agent_nudge.py` covers the primitive + endpoint + auto-nudge; no flakiness surfaced this pass —
      deeper hardening deferred.)

## Immediate remediation (operator-gated — NOT part of the code fix)

The two lost questions (641/643) are already gone from the queue; the durable fix will not resurrect them. To restore
main's responsiveness NOW: **respawn `orch-agent-main`** (fresh session; context is only 13% so minimal loss) so it
starts a clean, responsive `/loop`, then **re-send the questions**. Operator earlier chose "investigate root-cause" over
an immediate respawn — respawn remains available on your go. (Meanwhile the fleet is separately degraded: tasks
`understat_local_backfill_completion-001` [slot 7] and `v1_enumerator_dispatch_not_deletable-009` [slot 6] are
orphaned-dispatched — their slots last pinged ~4h ago — which is the real answer to operator question 643; that
fleet-reclaim gap is a separate issue worth its own doc.)

## Follow-on fix (same session, 2026-07-08): orphaned dispatched-task reclaim

The "separate fleet-reclaim gap" flagged above turned out to be a real, related dispatch bug — fixed in the same session
per operator ("fix the root cause right away, add it to this plan").

**Root cause**: `WorkerLivenessWatchdog._reclaim_exited_slot` cleared `slot.current_task` when a crashed worker's tmux
session was gone, but did NOT release the task — leaving it `status=dispatched` with no owning slot. Such an orphan is
unreachable by `/reassign` (its precondition checks `slot.current_task` → 400 "slot has no current task") and requeued
by nothing, so it sat `dispatched` forever (`understat_local_backfill_completion-001`,
`v1_enumerator_dispatch_not_deletable-009`). (The main agent's chat report blamed the tmux_pruner; the real culprit was
the watchdog's own reclaim.)

- [x] [BACKEND] `_reclaim_exited_slot` releases the still-`dispatched` task inline before clearing `current_task`
      (root-cause fix). — ao@62d4da8f (`server/worker_liveness_watchdog.py`)
- [x] [BACKEND] Task-centric backstop `reclaim_orphaned_dispatched_tasks` — the watchdog requeues any `dispatched` task
      whose slot no longer owns it (`slot.current_task != task_id`) every tick (60s), preserving `target_slot`+affinity,
      guarded by a 120s dispatch grace so a just-dispatched task is never falsely reclaimed. — ao@62d4da8f
      (`server/state_store/tasks.py`, `server/config.py`)
- [x] [TEST] 7 tests: broken-binding / missing-slot / live-binding-untouched / fresh-within-grace / queued+done ignored
      / `_reclaim_exited_slot` releases / done-task-untouched. Full `quality-gates.sh` green. — ao@62d4da8f
      (`tests/test_orphaned_task_reclaim.py`)

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what happened>.` -->

- **2026-07-13** — Checked against a separate operator-reported gap ("operator rulings never reach the AO
  blocked-question queue", proven on `BLK-f2bb67c2`). Confirmed this doc's fix (Option A, `agent_messages` reply-ack)
  does NOT cover it — `blocked_queue`/`BlockedRow` is a wholly separate table this doc never touches, and the remaining
  open todo here (tmux-nudge reliability) is unrelated. Filed + shipped as its own issue:
  `ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md` (`BlockedQueueReconciler`,
  agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009). No todos here flipped — genuinely a different gap.
- **2026-07-08** — ✅ **Orphaned dispatched-task reclaim SHIPPED** (ao@62d4da8f, live-defi-rollout; staging-first
  drain). Root-caused live during operator's chat with the main agent (main tried `/api/slots/6,7/reassign`, got 400
  "slot has no current task"): `WorkerLivenessWatchdog._reclaim_exited_slot` cleared `slot.current_task` on a
  session-gone worker WITHOUT releasing the task → orphaned dispatched, unreachable by `/reassign`, requeued by nothing.
  Fixed the creation path (release inline) + added a task-centric backstop (`reclaim_orphaned_dispatched_tasks`,
  watchdog every 60s, preserves affinity, 120s grace). 7 tests, full QG green. Verified the main agent's own manual
  patch (`ss.release_task_to_queue` on both tasks) was correct + safe first; this makes it self-heal so it never needs a
  manual patch again. (Operator: fix-now, no separate issue doc — tracked in this plan.)
- **2026-07-08** — ✅ **Option A SHIPPED** (ao@8076257, live-defi-rollout; staging-first drain → v2-gated).
  Operator→agent delivery is now AT-LEAST-ONCE with reply-ack: `drain_agent_pending` redelivers
  undelivered-OR-unanswered messages every poll until `/reply` stamps `answered_at` (`mark_role_messages_answered`,
  optional `in_reply_to`); a `redelivery_count` cap (config `agent_message_max_redeliveries`, default 30) stops runaway
  redelivery and surfaces `needs_operator_count`. `agent_messages` gained `answered_at`+`redelivery_count` via
  idempotent `bootstrap.py` migrate with a **one-time delivered→answered backfill** (so the deploy does NOT re-flood
  main with 400+ historical messages). `count_pending_to_agent` now = unanswered (sticky in the dashboard).
  `agents/main.md` loop hardened (scratch-file, `in_reply_to`, don't-fake-ack, `last_msg` is a status-string). 8
  regression tests incl. the 641/643 case; full `quality-gates.sh` green (1102 py + 79 vitest). ao-self-pull
  auto-restarts the live backend within 15 min (applies the migration). **Remaining**: `[UI]` Vite badge for
  `needs_operator_count`; `[BACKEND]` nudge-reliability verify (both P2, low-risk). Option B (reconcile loop) superseded
  by Option A. Recovered a careless `git stash` that tangled a foreign `redeploy2` stash into `server/escalation.py` —
  restored to HEAD, foreign stash preserved (not dropped).
- **2026-07-08** — Filed. Root-caused the silent-drop (drain-on-poll, no reply-ack/redelivery — Layer 1; main agent
  monitoring-loop drain-without-reply — Layer 2) from live DB + tmux pane + code read during the
  `ao_dispatch_correctness` deploy session. Human plan (`assigned_vm: NA`), operator-chosen. Fix Option A
  (at-least-once + reply-ack) recommended; Option B (reconcile loop) as ship-first mitigation. No code shipped yet —
  design captured for operator review.
