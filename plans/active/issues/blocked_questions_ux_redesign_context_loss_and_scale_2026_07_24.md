---
doc_type: issue
title:
  "Blocked-question UX doesn't scale and loses context once the asking agent dies — operator design input for
  escalation_and_disaster_recovery_master's E1 (deliberately NOT scoped or actioned yet)"
summary:
  Operator-reported pain, live-experienced this session (2026-07-24, the BLK-f09e9ca9/slot-2 episode) — a blocked
  question's stated question+options often don't carry enough context for an informed decision; at scale (up to ~30 open
  questions) that ambiguity compounds; the same question sometimes gets asked by multiple different agents, or multiple
  times by different sessions on the same slot; and when the operator needs to go back and ask the ORIGINATING agent for
  more context, that agent is frequently already dead. Operator's own proposed direction — a stable id per question that
  jumps straight to the asking session's transcript — is technically groundable (a durable session-transcript renderer
  already exists) but nothing wires it to the blocked-question path today. Operator explicitly deferred this — broader
  than E1's scoped-link fix, a real UX/API redesign, pick up later.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, deployment-ui]
scope: [engineer, admin]
tags: [agent-orchestrator, blocked-questions, escalation, ux, dashboard, dead-agent-context]
related:
  [
    /plans/epics/escalation_and_disaster_recovery_master.md,
    /plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
priority: P2
parent_epic: escalation_and_disaster_recovery_master
source: "Operator design context, relayed 2026-07-24 after the /api/escalation/{id} scope question"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## The pain, in the operator's own framing

1. **Insufficient context to decide.** A blocked question's `question` + `options[]` text sometimes doesn't cover
   everything actually needed to make an informed call — the worker researched its own angle, but the operator may need
   context the worker never thought to include.
2. **Scale.** With up to ~30 blocked questions open at once, this ambiguity compounds — hard to tell which are urgent,
   which are duplicates, which need a real decision versus a rubber-stamp.
3. **Duplication.** The same underlying question sometimes gets asked by multiple different agents independently, or
   multiple times by different sessions that occupied the same slot (a respawn re-asking something an earlier session on
   that slot already asked) — no dedup, no "this was already answered elsewhere" surfacing.
4. **Dead-agent unreachability.** The single most disruptive pattern: the operator wants to ask the ORIGINATING agent a
   follow-up ("what did you mean by X", "why didn't you consider Y") and that agent is already dead — no live worker to
   ask, and no easy path back to what it was actually looking at when it asked.

This is not hypothetical — it is exactly what happened this session (see
[`dispatch_sequential_gate_fix_2026_07_24.md`](dispatch_sequential_gate_fix_2026_07_24.md) and the `pre-compact`
summary): BLK-f09e9ca9 (task `ao_remediation_a_independent_fixes-008`) was answered at 06:38 UTC, but the worker that
asked it had already skipped the task and gone idle at 06:35 — by the time the answer was enqueued there was no live
session to receive it, and the operator's only path to more context on what that worker actually saw would have been its
transcript, not a live re-ask.

## Operator's proposed direction

Assign each blocked question a stable id (it already effectively has one — `BlockedRow.blocked_id` — but it isn't
surfaced as a navigable handle), and use it to jump DIRECTLY into the session that asked it, rather than only into the
live slot (which may since have respawned to a different, unrelated session).

## What already exists that this could build on

- **`server/transcript_log.py`** — the dashboard's "Show log" already renders a durable, complete transcript from
  Claude's own JSONL log file, keyed by the globally-unique `claude_session_id` (survives respawns and TUI redraws —
  built specifically because `tmux capture-pane` returns only ~24 lines of an alternate-screen TUI). The retrieval
  PRIMITIVE already works.
- **The gap**: `BlockedRow` (`server/orm.py`) stores `blocked_id`, `slot_id`, `task_id`, `question`, `options_json`,
  `recommendation`, `authority`, plus the answer fields — **it does NOT store `claude_session_id`**. So even though a
  transcript render exists, nothing captures WHICH session asked a given blocked question at creation time. Once the
  slot respawns (exactly what happened in the BLK-f09e9ca9 episode), `slot_id` alone points at the CURRENT session, not
  the one that actually asked — the one piece of information the operator would need to go "back" is silently dropped
  the moment a respawn happens.
- No existing dedup / similarity surfacing across `BlockedRow` entries, and no existing "N other open questions look
  like this one" signal.

## Why this is bigger than E1

`escalation_and_disaster_recovery_master`'s E1 (role-agnostic escalation pipeline, paused, 5 UNBUILT todos) already
plans a scoped `/escalation/{id}` link and an `open/in-progress/resolved` state machine — necessary but NOT sufficient
for this. E1 as scoped doesn't address: capturing `claude_session_id` at creation time, surfacing a transcript-jump
affordance in the resolution UI, cross-question dedup/similarity, or any policy for what to show when the transcript's
own session has ALSO expired/rotated out from under the id. Those are real, unscoped design decisions — exactly what the
operator flagged as "we can pick this up again afterwards, not now."

## Explicitly NOT actioned

No code, no UI mockup, no plan authored. This doc exists so the context isn't lost before E1 (or a wider blocked-
questions redesign) is picked up. When it is: read this doc + `escalation_and_disaster_recovery_master`'s "Why this epic
exists" section together before scoping the workstream.

## Progress Log

- **2026-07-24**: Filed verbatim from operator context, prompted by clarifying `/api/escalation/{id}`'s scope. Grounded
  the "jump to session" idea against `transcript_log.py` (retrieval already works) and `BlockedRow`'s schema (the
  missing link is `claude_session_id` capture at creation time). Deliberately deferred per operator instruction.
