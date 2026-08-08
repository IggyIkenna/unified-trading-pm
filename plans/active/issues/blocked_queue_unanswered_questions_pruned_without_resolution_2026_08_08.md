---
doc_type: issue
title:
  AO `/blocked` question queue silently drops unanswered questions — 3 consecutive blocked-questions on the same task
  vanished from `blocked_queue` before ever being answered, with no resolution signal to the waiting worker.
summary: >
  Live-observed 2026-08-08 on task `defi_expected_unattempted_backlog_1m_2026_07_03_finalize-002` (plan
  `defi_expected_unattempted_backlog_1m_2026_07_03_finalize_2026_08_08.md`): the `[DOC]` archival todo is gated on an
  operator decision to unlock a `locked_by`-protected plan (a genuine HARD-RULE gate — agents must never unlock
  autonomously). Four separate slots (30, 29, 12, 19) were dispatched this same task in succession. Slot 30 filed a
  `/blocked` question; slot 29 found no trace of it in the live `blocked_queue` and re-filed as `BLK-3d18ef7c`; slot 12
  confirmed `BLK-3d18ef7c` was still present with `answered_at: null` (genuinely pending, correctly did not re-file per
  RULES.md §5); slot 19 (this session) checked `GET /api/state` again and found `BLK-3d18ef7c` **no longer present in
  `blocked_queue` at all** — not present, not in an answered state, just gone. Cross-checked: of the 65 entries
  currently live in `blocked_queue`, ZERO have `answered_at` set, suggesting the removal mechanism is a time-based prune
  rather than an answer-and-archive flow. Re-filed a fourth question (`BLK-ce0fe830`) per the same reasoning slot 29
  used, since no live pending question remained for this task.

  Why this matters beyond this one task: `/blocked` is documented (RULES.md §5, worker.md §4) as the sanctioned
  mechanism for a worker to escalate a genuine judgment call to a human and then WAIT for the answer via a future
  `/progress`/`/heartbeat` message. If unanswered questions silently expire from the queue with no notification to the
  filer and no distinguishable state from "resolved", the mechanism is unreliable for exactly the cases it exists for:
  locked-plan unlock decisions, ambiguous specs, and other genuinely human-gated calls. A worker cannot tell the
  difference between "the operator hasn't looked yet" and "my question expired and nobody will ever see it" without
  manually re-polling `GET /api/state` and comparing blocked_ids across sessions — which is exactly the anti-pattern
  RULES.md §5 tells workers NOT to do ("don't re-ask a pending question"). This also means any workspace metric counting
  "resolved blocked-questions" from the absence of a blocked_id in the live queue would be silently wrong —
  pruned-unanswered and answered-and-cleared are indistinguishable from the outside.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-queue, escalation, worker-lifecycle, cross-cutting, reliability]
related:
  [
    /plans/active/defi_expected_unattempted_backlog_1m_2026_07_03_finalize_2026_08_08.md,
    /plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
  ]
created: 2026-08-08
author: data_engineering worker slot-19
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
drift_direction: NA
source:
  data_engineering worker slot-19, 2026-08-08, discovered while working the `defi_expected_unattempted_backlog_1m`
  finalize plan's `[DOC]` archival todo — 4th consecutive dispatch to hit the same locked-plan unlock gate, 3rd
  consecutive `/blocked` question filed against it.
resolved_by:
depends_on: []
locked_by:
context_scope:
  [
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    unified-trading-pm/agents/RULES.md,
    unified-trading-pm/agents/worker.md,
  ]
---

## What I found

Working task `defi_expected_unattempted_backlog_1m_2026_07_03_finalize-002` this session (slot 19), I read the plan's
Progress Log and found a chain of 3 prior dispatches (slots 30, 29, 12) all hitting the same gate: both source and
finalize docs have zero open todos, but the source doc carries a genuine `locked_by: live-defi-rollout` /
`locked_since: 2026-07-03` lock, and the HARD RULE against autonomous unlocking means archival requires an explicit
operator decision.

- Slot 30 filed a `/blocked` question recommending unlock-and-archive.
- Slot 29 found no trace of slot 30's question in the live `blocked_queue`, concluded it was "likely pruned or never
  surfaced against this specific task_id," and re-filed as `BLK-3d18ef7c`.
- Slot 12 (redispatched the same task) checked `GET /api/state` directly and confirmed `BLK-3d18ef7c` WAS present, with
  `answered_at: null` — genuinely pending, no operator response yet. Correctly did not re-file (RULES.md §5: a pending
  question is not re-asked).
- Slot 19 (this session, redispatched a 4th time) checked `GET /api/state` again: `BLK-3d18ef7c` is **no longer present
  in `blocked_queue` at all**. Confirmed via direct JSON inspection (65 total entries, none matching that `blocked_id`,
  none matching this task's `task_id`). Also checked: of all 65 live entries, **zero have `answered_at` set** — the
  field exists and is tracked (confirmed from the schema of other entries), but nothing in the current live queue shows
  a resolved state, which is consistent with a time-based prune removing rows rather than an answer-and-archive flow
  moving them to a resolved state.

Net effect: a genuine, correctly-filed, correctly-non-duplicated human escalation vanished with `answered_at: null` its
whole life — never resolved, never explicitly rejected, just gone.

## Why it matters

`/blocked` is the sanctioned RULES.md §5 mechanism precisely for "a genuine judgment call where YOU need a human... to
decide SOMETHING before you can continue." The contract workers are told to trust is: file once, then wait — the answer
"comes back as a message on your next `/progress` call." If the underlying question can disappear from the queue before
an answer ever lands, that contract is broken in a way that's invisible to the filing worker (which just sees
`can_continue: false` play out as "nothing happened, redispatch me later") and invisible to any downstream process
treating "not in `blocked_queue`" as a proxy for "resolved." This specific case is a locked-plan unlock decision, but
the same failure mode would silently swallow ANY blocked-question — including higher-stakes ones (data correctness
surprises, cross-repo SSOT contradictions) that the workspace's own governance rules classify as "big findings"
requiring the operator be notified.

This has now recurred 3 times in a row on the same task (`BLK` slot-30's question, then `BLK-3d18ef7c`, then this
session's `BLK-ce0fe830`) — meeting the same "recurring, not a one-off" bar the workspace uses to justify a P1 rather
than a passive note.

## Recommended decision

Investigate the actual `blocked_queue` lifecycle in `agent-orchestrator/server/` — specifically what removes an entry
from the live queue when `answered_at` is still `null` (a TTL/expiry sweep, a size cap eviction, or something else), and
whether that removal is intentional. If intentional, the mechanism needs to at minimum: (a) notify the filing slot/task
that its question expired unanswered rather than leaving it to silently vanish, and (b) distinguish "expired unanswered"
from "answered" in whatever surfaces `blocked_queue` state, so a worker (or a future audit) can tell them apart without
cross-referencing `answered_at` across two point-in-time snapshots the way this session had to. If unintentional (a
bug), fix the removal condition so a `blocked_id` with `answered_at: null` stays live until either answered or
explicitly expired-with-signal.

## Todo

- [ ] [BACKEND] P1. Read `agent-orchestrator/server/` for the `blocked_queue` storage + removal logic (search for
      `blocked_queue`, `blocked_id`, `answered_at` read/write sites). Confirm whether unanswered (`answered_at: null`)
      entries are removed by a time-based prune, a size cap, or some other mechanism, and cite the exact code location +
      condition. (repo: agent-orchestrator)
- [ ] [BACKEND] P1. If a prune/expiry mechanism is confirmed: add a notification path so the filing slot/task learns its
      question expired unanswered (a message on the slot's next `/progress`/`/heartbeat`, analogous to how an answer is
      currently delivered), instead of silent disappearance. If the removal is a bug rather than a designed behavior,
      fix the condition so `answered_at: null` entries are never removed except by an explicit expiry-with-signal path.
      (repo: agent-orchestrator)

## Progress Log

- 2026-08-08 (slot 19): Issue filed during pre-compact audit of the
  `defi_expected_unattempted_backlog_1m_2026_07_03_finalize-002` session — the underlying task's own Progress Log
  already records the observation inline; this doc promotes it to tracked, actionable work per the workspace's
  findings-closure HARD RULE (a chat/log-only observation is not closure). No investigation performed yet — both todos
  above are unstarted.
- 2026-08-08 (slot 9): Additional data point for whoever picks up the `[BACKEND]` todos — `BLK-ce0fe830` (this doc's own
  trigger) was re-checked via `GET /api/state` across ~13 consecutive `/heartbeat` cycles between `created_at`
  `18:41:32Z` and `19:25:42Z` (~44 min elapsed). Unlike its 3 predecessors (which vanished before an answer landed, some
  apparently within a similar or shorter window), `BLK-ce0fe830` stayed present with `answered_at: null` the entire time
  — no pruning observed in this window. This doesn't resolve the question of what removes unanswered entries, but it's
  evidence against a short fixed-TTL-per-entry theory (this one outlived at least 44 min without being pruned) —
  consistent with a size-cap/LRU-style eviction (65-66 entries observed live) or some other non-time-uniform mechanism.
  Worth checking entry count/ordering effects, not just age, when doing the `[BACKEND]` code read. No action taken on
  the task itself — still correctly parked, no autonomous unlock, no re-filing.
