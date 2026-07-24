---
doc_type: issue
title:
  "Operator rulings given in chat/interactive Q&A never reach the AO blocked-question queue — `POST
  /api/blocked/{id}/answer` is a manual step nobody is forced to take, so workers re-verify already-decided
  preconditions indefinitely (proven: BLK-f2bb67c2)"
summary:
  'Operator-authorized ops+code investigation, 2026-07-13. A worker files a structured BLOCKED question (`add_blocked`
  -> `blocked_queue`), and the ONLY way it gets `answered_at` set is a human/agent explicitly calling `POST
  /api/blocked/{id}/answer`. When the operator instead rules on the underlying question in free-text chat/ interactive
  Q&A (or the decision only gets written into a plan doc''s Progress Log), NOTHING bridges that ruling into
  `blocked_queue` — the row silently stays `answered_at: null` forever. Every worker that later re-dispatches to the
  gated checkbox reads `GET /api/state -> blocked_queue`, sees `null`, and re-verifies the same already-decided
  preconditions from scratch. Proven live on `BLK-f2bb67c2` (sports_manifest_canonicalisation_2026_06_01.md): operator
  ruled "Execute now" 2026-07-12, E3+E4 executed + verified the same day, yet 4+ overnight workers each re-checked
  `answered_at` and found it still null, because nobody ever called the answer endpoint. This is a THIRD, distinct root
  cause from two adjacent, already-investigated gaps that do NOT touch `blocked_queue`/`BlockedRow` at all:
  `ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md` (the SEPARATE `agent_messages` free-text chat reply-ack
  gap, already fixed ao@8076257) and `ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md` (AutoSpawn
  tier-propagation / dispatch-fairness bugs). Fix shipped: `BlockedQueueReconciler`
  (agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009) — a periodic (120s) + on-demand (`POST
  /api/blocked/reconcile`) sweep that scans the plans corpus for an explicit, low-false-positive resolution marker
  (`ANSWERED` / `Operator ruling:` / `resolved`) next to a `BLK-xxxxxxxx` token and auto-syncs it into `blocked_queue`,
  so a re-filed/duplicate BLOCKED question for an already-plan-documented decision self-heals within one tick instead of
  blocking forever on a manual click.'
status: resolved
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    blocked-queue,
    operator-ruling,
    reconciliation,
    reply-sync,
    dispatch-thrash,
    sports_manifest_canonicalisation,
  ]
related:
  [
    /plans/archive/issues/ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md,
    /plans/archive/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    /plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md,
    ../sports_manifest_canonicalisation_2026_06_01.md,
  ]
created: 2026-07-13
parent_epic: orchestrator_master
priority: P1
source:
  'Operator, 2026-07-13 (chat ruling): "operator rulings given in chat/Q&A never reach the AO blocked-question queue, so
  workers re-check answered questions indefinitely (proven: BLK-f2bb67c2 — operator ruled ''Execute now'' 2026-07-12,
  E3/E4 RAN to completion, yet 4+ overnight workers each re-verified preconditions against a still-null answered_at)."
  Investigated + fixed same session via live DB read (`/var/lib/orchestrator/state.db`, WAL-merged), `GET /api/state`,
  and a full read of the sports_manifest_canonicalisation plan''s E3+E4 OPERATIONAL RUN section.'
assigned_vm: NA
resolved_by: agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: design
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.9
last_updated: 2026-07-13
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
locked_since:
---

# AO blocked-queue operator-ruling sync gap

## Symptom (operator-reported, 2026-07-13)

Operator rulings made in chat/interactive Q&A resolve a worker's BLOCKED question conceptually, but never reach
`blocked_queue.answered_at`. Workers re-dispatched to the same gated checkbox re-read `GET /api/state -> blocked_queue`,
find the SAME row still `answered_at: null`, and re-verify the same already-decided preconditions — proven concretely on
`BLK-f2bb67c2` in `sports_manifest_canonicalisation_2026_06_01.md`: the operator ruled "Execute now" 2026-07-12 (Option
A), E3 (writer drain) + E4 (canonical migration VM fleet, 16/16 `exit_code=0`) EXECUTED and VERIFIED the same day — yet
the twentieth, twenty-first, and twenty-second E8-verify touches (2026-07-13, spanning several hours) each independently
confirmed `BLK-f2bb67c2` still `answered_at: null` and declined to re-run the real audit (correctly, since nothing had
changed) but could not FLIP the underlying gate either, because the only thing gating dispatch is the unanswered row.

## Investigation (2026-07-13)

**Mechanism confirmed** (`agent-orchestrator` repo):

- A worker escalation is `POST /api/slots/{id}/blocked` -> `state_store.activity.add_blocked` -> `blocked_queue` row
  (`server/orm.py::BlockedRow`) with `answered_at=NULL`.
- The ONLY way `answered_at` gets set is `POST /api/blocked/{blocked_id}/answer` ->
  `state_store.activity.answer_blocked` (`server/routes/backlog.py::answer_blocked_endpoint`) — which also delivers a
  `slot_messages` row to the worker and flips the slot back to `working`.
- Auth: local direct calls to `127.0.0.1:8765` (no `X-Forwarded-For`) are anonymous-permissive
  (`server/auth.py::get_current_user`, `ALLOW_ANONYMOUS`) — any worker/main-agent/curl on the VM can call `/answer`
  without a bearer token. The gap is NOT auth friction; it's that nothing ever calls it after a chat ruling.
- Live-checked the orchestrator's real `blocked_queue` on this VM (`/var/lib/orchestrator/state.db`, WAL journal merged;
  cross-checked against `GET /api/state`): 0 rows total, 0 unanswered, and `activity_log`'s full history carries zero
  `slot_blocked`/`blocked_answered` events. `BLK-f2bb67c2` is not currently a live row on this instance (rows appear to
  rotate/reset between sessions on this VM) — confirmed by attempting the documented answer against it live:
  `POST /api/blocked/BLK-f2bb67c2/answer` returned HTTP 500 (`answer_blocked` raises `ValueError` on an unknown id,
  unhandled by the route). No row was fabricated to force a "success" — the decision is instead recorded durably in the
  plan doc itself (see below) with the exact marker convention the new reconciler looks for, so a future re-filed
  duplicate self-heals for real.

**Ruled out as the cause**: two adjacent, already-investigated AO issue docs were checked in full — neither touches
`blocked_queue`/`BlockedRow`:

- `ao_operator_message_silent_drop_no_reply_ack_2026_07_08.md` — fixed (`ao@8076257`) a SEPARATE gap on the
  `agent_messages` table (free-text operator<->agent chat): drain-on-poll with no reply-ack/redelivery. Its one
  remaining open todo (`[BACKEND] P2. Verify the send_to_role tmux nudge...`) is about nudge reliability, unrelated to
  blocked questions.
- `ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md` — three open prevention todos are about AutoSpawn spawning
  the whole tick at the top task's tier, the monitor/main agent over-generalizing a single gate to the whole backlog,
  and operating guidance on mixing Opus/Sonnet plans. None of the three is satisfied by this fix (verified — not
  flipping any of them; they remain open, genuinely unrelated).

## Root cause

There is no bridge from "an operator ruling exists" (in chat, or written into a plan's Progress Log) to "the
`blocked_queue` row for that decision is marked answered." The only path is a human or agent remembering to call
`POST /api/blocked/{id}/answer` in the moment. A plan doc can accurately narrate "per the operator ruling this
executed..." while the structured queue the DASHBOARD and WORKERS actually check never learns about it — the prose and
the queue silently diverge.

## Fix shipped

**`BlockedQueueReconciler`** (`agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009`,
`server/blocked_reconcile.py`):

- `find_resolution_in_plans(blocked_id, pm_path)` — scans every `.md` under `plans/active/` (incl. `issues/`) for a line
  mentioning the `blocked_id`; if a resolution marker (`answered`, `operator ruling`, `operator ruled`, `resolved` —
  word-bounded so it never matches the literal field name `answered_at`) appears within `_CONTEXT_WINDOW_LINES` (12)
  lines, returns `(answer_text, "file:line")`. Deliberately conservative: a bare mention of a BLK id with no marker
  (e.g. "still `answered_at: null`") never matches.
- `reconcile_once(pm_path=...)` — one pass over every currently-unanswered `BlockedRow`; for each match, calls the SAME
  state transition the manual `/answer` endpoint uses (`answer_blocked` + `enqueue_message` + slot unblock +
  `blocked_answered` activity log), `answered_by="reconciliation-sweep"`, citing the plan file:line in the answer text.
- `BlockedQueueReconciler` — daemon thread (mirrors `GhRateLimitMonitor`/`TmuxPruner`), 120s default tick
  (`ORCHESTRATOR_BLOCKED_RECONCILE_INTERVAL_SECONDS`, 0 disables), registered with `LoopSupervisor` so a dead thread
  self-revives.
- `POST /api/blocked/reconcile` (`server/routes/backlog.py`) — on-demand trigger for main/operator/scripts, same
  `reconcile_once()` under the hood.
- 15 unit tests (`tests/test_blocked_reconcile.py`) incl. the exact BLK-f2bb67c2/BLK-d48acae4 marker shapes, the
  false-positive regression (`answered_at: null` must NOT match), idempotency on rerun, and thread start/stop/config
  plumbing. Full `quality-gates.sh` green (1228 tests).
- **Live-verified** on this VM's `orchestrator.service` (systemd-managed, `/var/lib/orchestrator/state.db`): service
  auto-restarted on the push (`ao-self-pull`), journal shows `BlockedQueueReconciler started (interval=120s)` with no
  startup errors, `POST /api/blocked/reconcile` returned `200 {"checked": 0, "synced": [], "unresolved": []}` against
  the real (currently empty) live queue — a safe, honest no-op, not a fabricated success.
- `sports_manifest_canonicalisation_2026_06_01.md` gained a closing "Ops sync" section recording `BLK-f2bb67c2 ANSWERED`
  with the operator's verbatim ruling + citation, using the exact marker convention the reconciler matches — so a future
  re-filed duplicate of this question self-heals within one tick instead of triggering a 24th manual re-verification.

## Todos

- [x] [BACKEND] P1. Ship `BlockedQueueReconciler` (periodic + on-demand) that syncs plan-documented operator rulings
      into `blocked_queue`. — agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009
      (`server/blocked_reconcile.py`)
- [x] [BACKEND] P1. Wire into `server/server.py` startup/shutdown + `LoopSupervisor` (self-revives on thread death). —
      agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009
- [x] [BACKEND] P2. On-demand `POST /api/blocked/reconcile` endpoint (main/operator/script trigger, no wait for the next
      tick). — agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009 (`server/routes/backlog.py`)
- [x] [TEST] P1. 15 unit tests incl. the BLK-f2bb67c2/BLK-d48acae4 marker regression + the `answered_at` false-positive
      guard + idempotency. Full `quality-gates.sh` green (1228 tests, ruff+basedpyright clean). —
      agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009 (`tests/test_blocked_reconcile.py`)
- [x] [DOCS] P1. Sync `BLK-f2bb67c2` into `sports_manifest_canonicalisation_2026_06_01.md` with the operator's verbatim
      ruling + citation, using the marker convention the reconciler matches (closes the repeated re-verification churn
      for this specific question going forward). — unified-trading-pm (this session)
- [x] [OPS] P1. Live-verify on `orchestrator.service`: clean restart, no startup errors, on-demand endpoint returns the
      correct shape against the real (empty) `blocked_queue`. — verified 2026-07-13, this session

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what happened>.` -->

- **2026-07-13** — ✅ **SHIPPED + live-verified**. Root-caused (a distinct third gap from the two adjacent AO issue docs
  named in the operator's ruling — neither touches `blocked_queue`), built `BlockedQueueReconciler`
  (agent-orchestrator@bec9373a99fb49793efbb874339dcaf81a3ae009), full QG green (1228 tests), landed on
  `live-defi-rollout`, live-verified on this VM's real `orchestrator.service` (clean restart via `ao-self-pull`,
  reconciler thread started, on-demand endpoint returns a correct honest no-op against the currently-empty live queue).
  Also cleared the specific stale question this was reported against: `BLK-f2bb67c2` was NOT present as a live row on
  this VM (0 rows in `blocked_queue`, confirmed via direct SQLite + `GET /api/state` + a zero-hit `activity_log` history
  for `slot_blocked`/`blocked_answered` events) — did not fabricate a row to force a POST "success"; instead synced the
  operator's verbatim ruling into `sports_manifest_canonicalisation_2026_06_01.md` using the reconciler's own marker
  convention, so any future re-filed duplicate of this exact question self-heals automatically. Did not flip any todos
  in the two related, already-investigated issue docs — verified none of their open items are actually satisfied by this
  fix (genuinely separate root causes).
