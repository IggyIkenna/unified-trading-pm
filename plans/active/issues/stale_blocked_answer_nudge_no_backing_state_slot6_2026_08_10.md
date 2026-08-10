---
doc_type: issue
title:
  "Repeated 'Operator answered your BLOCKED question' user-turn nudge on slot 6 with zero backing AO state, 16+
  consecutive occurrences"
created: 2026-08-10
author: slot-6
assigned_vm: NA
status: open
tags: [agent-orchestrator, worker-lifecycle, blocked-question, nudge, notification, harness, incident]
source: ["slot-6 idle session, 2026-08-10, observed across ~16 consecutive conversation turns"]
summary:
  "After fully resolving my one real /blocked escalation this session (BLK-13405a35 — filed, answered, acted on, acked),
  the exact literal text 'Operator answered your BLOCKED question — check your messages now and resume' kept arriving as
  a new user-turn message 16+ times in a row, each with zero backing state across every AO API surface checked."
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
related: [/plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md]
parent_epic: orchestrator_master
resolved_by: null
execution_scope: local-only
priority: P3
drift_direction: advance-code
depends_on: []
sequential: false
locked_by:
locked_since:
---

## What I found

While idle on slot 6 (no dispatched task, `status: idle`, `current_task: null`), the literal text **"Operator answered
your BLOCKED question — check your messages now and resume"** arrived as a new conversational turn 16+ times in a row,
verbatim, with no variation and no elapsed-time gating (some arrivals were seconds apart, one arrived mid-tool-call).

This is distinct from the ALREADY-DOCUMENTED
`ao_direct_instruction_stale_redelivery_after_blocked_resolution_2026_08_08.md` class (a `POST /api/slots/<N>/message`
"Direct instruction from main" redelivering up to 30x for lack of an ack) — I checked every surface that class's fix
relies on, and none show anything pending:

1. `POST /api/slots/6/heartbeat` (checked 6+ times across the incident): `messages: []`, `message_ids: []`,
   `new_task: null` every time.
2. `GET /api/slots/6/messages` (the dedicated message-listing endpoint per `dashboard/API_REFERENCE.md:538`):
   `{"messages": []}`.
3. `GET /api/state`'s `blocked_queue` filtered to `slot_id == 6`: only one entry, `BLK-dd01168b` (`task_id: agt-1a9b86`)
   — a stale, unrelated, already-declined-by-main codex-drift ruling from an EARLIER, already- finished task on this
   slot (`created_at: 2026-08-09T01:05:51Z`, `authority: operator_pending`, `answered_at: null`). Not a fresh answer;
   not tied to my actual dispatched work this session.
4. The ONE real `/blocked` I filed this session, `BLK-13405a35` (task
   `delta_one_cefi_lookback_instrument_id_form_mismatch-53a0d8ce974a`, the venue-representative question in
   `delta_one_cefi_btc_perp_representative_venue_mismatch_2026_08_09.md`) — fully resolved: main answered it (option A),
   I acked message id `6709`, filed the resulting scoped fix todo, and skipped the gated task. It no longer even appears
   in `blocked_queue` (pruned as resolved).
5. `GET /api/state`'s own slot-6 row: `status: "idle"`, `current_task: null`, `last_msg` is just the fleet-wide backlog
   summary ("315 task(s) blocked on ...", unrelated collision/prereq counts), `last_ping` fresh.

Every channel the orchestrator exposes for delivering a genuine answered-blocked-question notification is checked and
empty. The notification's phrasing and repeated-verbatim delivery pattern strongly resembles the AO's own nudge
mechanisms (git-status-red nudges, direct-instruction redelivery), but I could not find where THIS specific text
originates in `agent-orchestrator/server/`— it does not match any string I could locate via grep, and it arrives as a
raw conversational turn rather than through any of the `messages`/`message_ids` API fields the documented mechanisms
use.

## Why it matters

If this is a genuine backend nudge (a mechanism I haven't located), it has no visible backing state and therefore no
self-closing condition — same failure shape as the `ao_direct_instruction_stale_redelivery` incident, but through a
channel I couldn't find via the API to ack. If it is NOT a backend nudge (e.g., a harness/tmux-level injection separate
from the AO server entirely), then this doc is the wrong place to fix it, but is still worth recording so whoever
investigates doesn't have to re-derive the "I checked everything, found nothing" trail from scratch.

Either way: a worker receiving this exact text with no way to resolve it via any documented API is a real gap — worth
tracing to its source rather than each future occurrence re-doing the same exhaustive-and-empty check.

## Recommended decision

Options, in order of likely usefulness for whoever picks this up (human/main, since tracing an unlocated notification
source across the harness/AO boundary is a judgment call, not a bounded worker todo):

- [ ] [OPERATOR] P3. Trace the actual source of this exact nudge text (grep `agent-orchestrator/server/` and the Claude
      Code harness/tmux-injection layer for "Operator answered your BLOCKED question" or a template producing it) —
      confirm whether it's a real AO-side mechanism lacking an ack path, or a harness-level artifact outside AO's scope.
      If AO-side: add the same ack-on-confirmed-stale pattern
      `ao_direct_instruction_stale_redelivery_after_     blocked_resolution_2026_08_08.md` already established. If
      harness-side: redirect this finding to whichever surface owns that layer.

## Progress Log

- 2026-08-10 (slot-6): Filed after 16+ consecutive identical occurrences with zero backing state across every AO API
  surface (heartbeat, dedicated messages endpoint, blocked_queue, slot status) — see "What I found" for the full
  per-channel trail. Not actioned further (root cause requires tracing a notification-delivery mechanism I could not
  locate via grep from a worker's read-only vantage point).
