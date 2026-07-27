---
doc_type: issue
title:
  Answering an AO blocked-question never wakes the worker — delivery is pull-based only, and a delayed answer races the
  liveness watchdog into a spurious resume/respawn
summary:
  Neither POST /api/blocked/{id}/answer nor the BlockedQueueReconciler ever calls tmux_spawn.nudge() after recording an
  operator's answer, so the enqueued message is only delivered when the worker itself next polls. Flipping the slot to
  "working" also immediately removes it from the watchdog's blocked exemption, so a real-world delay past the heartbeat
  timeout triggers a resume-or-respawn — very likely the "have to regenerate everything" the operator observed.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, blocked-questions, operator-answer, nudge, watchdog, dispatch]
related:
  [
    /plans/archive/issues/ao_blocked_queue_operator_ruling_sync_gap_2026_07_13.md,
    /plans/active/issues/blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24.md,
  ]
created: 2026-07-27
last_updated: 2026-07-27
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: NA
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
supersedes:
superseded_by:
source:
  Dispatched as one of five parallel audit agents this session investigating an operator-raised bug report (not yet
  triaged before this session) — "when ao asks a operator question and it's answered doesn't always trigger unblock of
  that task workflow so have to regenerate everything. same story for delayed responses to operator blocked questions
  they seem to get blocked."
---

# Operator-answer nudge gap — 2026-07-27

## What I found

A worker files a blocked question via `POST /api/slots/{id}/blocked` (`server/routes/slots_worker.py:1377-1411`), which
sets `slot.status = "blocked"`. The operator's answer is recorded by `POST /api/blocked/{id}/answer`
(`server/routes/backlog.py:680-739`): it eagerly writes `answered_at`, enqueues a `SlotMessageRow` (`enqueue_message`),
and flips `slot.status` back to `"working"` (lines 704-706). The periodic `BlockedQueueReconciler`
(`server/blocked_reconcile.py:147-215`, 120-second tick) does the identical eager-write pattern for plan-doc-documented
rulings.

**Neither path ever calls `tmux_spawn.nudge()`** (`server/tmux_spawn.py:1497`) — a function whose own docstring says it
exists specifically to "wake a possibly idle-looping agent... instead of waiting for its next `/loop` tick." Comparable
routes DO nudge (`set_loop_interval`, `routes/slots_ops.py:793-816`; agent-chat replies,
`routes/agents.py:659/764/803`). Without a nudge, the enqueued answer is only delivered when the worker itself next
calls `/boot`, `/heartbeat`, `/progress`, or `/messages` — pull-based, not pushed. `POST /api/backlog/regen` touches
neither the blocked queue nor tmux at all (it's plan-checkbox ingestion only), so the operator's own "regen fixes it"
workaround is most likely a red herring/placebo that just happens to correlate with the worker's own next natural poll.

**Compounding bug**: flipping `slot.status` to `"working"` immediately removes the slot from the watchdog's protective
exemption (`worker_liveness_watchdog.py:733-739`, which excludes `blocked` slots from its active-slot query). If the
operator's answer arrives more than `watchdog_heartbeat_timeout` (900s, `server/config.py:330`) after the worker's last
heartbeat — true for any real-world delay — the next 60-second watchdog tick sees a stale `last_ping` on a slot that
LOOKS like it should be actively working, and calls `_resume_or_fresh_respawn` (`:1904`): one context-preserving
`--resume` attempt (capped at 1, `config.py:331`), then a hard kill + fresh AutoSpawn respawn. This is plausibly the
exact "have to regenerate everything" the operator described — not a backlog regen at all, but a watchdog-forced respawn
losing the in-flight context.

Confirmed genuinely-blocked slots ARE excluded from every watchdog reap query, so the wait itself is clean by design —
the "stuck" feeling is specifically this flip-then-stale-heartbeat race, and it gets MORE likely the longer the operator
takes to answer.

Existing related docs: `ao_blocked_queue_operator_ruling_sync_gap_2026_07_13` is RESOLVED but covers a different gap
(plan-doc rulings, not this nudge mechanism). `blocked_questions_ux_redesign_context_loss_and_scale_2026_07_24` (OPEN
P2) documents a live corroborating instance (`BLK-f09e9ca9`: answered but the worker was already idle with no live
session to receive it) but is scoped as a UX/ context-loss redesign, not this specific nudge-gap root cause.

## Why it matters

An operator who answers a blocked question reasonably expects the worker to act on it promptly. Instead, the answer
silently waits for the worker's own poll cadence, and a slow-to-answer operator actively increases the odds the worker
gets kicked/respawned right as the answer lands — the worst possible outcome (the answer arrives, then the context that
needed it gets destroyed anyway).

## Todos

- [ ] [BACKEND] P2. **Add a `tmux_spawn.nudge()` call after both answer-recording paths** —
      `POST /api/blocked/{id}/answer` (`server/routes/backlog.py:680-739`) and `BlockedQueueReconciler`'s ruling-sync
      path (`server/blocked_reconcile.py:147-215`) — right after the message is enqueued and the slot flips to
      `working`. Add a regression test confirming `nudge()` is called exactly once per answer, patching the same mock
      surface used by `test_slots_ops` for `set_loop_interval`'s nudge call.
- [ ] [BACKEND] P2. **Fix the flip-then-stale-heartbeat race**: either (a) don't flip `slot.status` to `working` until
      the worker's NEXT heartbeat actually arrives (keep it in a state the watchdog still exempts until then), or (b)
      have the watchdog treat a slot whose `answered_at`/status-flip is more recent than `watchdog_heartbeat_timeout` as
      freshly-woken rather than stale-and-unhealthy (a short grace window keyed off the flip timestamp, not the old
      heartbeat). Pick whichever is the smaller, more surgical change after reading `worker_liveness_watchdog.py`'s
      active-slot query and `_resume_or_fresh_respawn` in full — report which was chosen and why before implementing if
      both look equally reasonable.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — worker lifecycle, blocked-question flow,
  watchdog model.
- `/codex/04-architecture/agent-orchestrator-alerting.md` — BLOCKED answered/auto-resolved close-bookend contract (this
  nudge gap is upstream of that bookend ever having a chance to fire promptly).
