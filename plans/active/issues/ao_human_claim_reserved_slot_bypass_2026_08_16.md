---
doc_type: issue
title:
  Reserved review slot silently hijacked by an ordinary backlog task via the human-claim routes, which never checked
  `human_slot_ids()` — the review agent "disappears" because its one reserved slot gets bound to a real Class-A task and
  wedges for hours with no `role=review` agent ever registering
summary: >-
  Operator reported the AO fleet's persistent "review" role agent keeps "disappearing." Investigated: `review.md`
  defines review as a persistent, one-per-machine singleton pinned to `config.review_slot_ids()`, and dispatch's own
  `pick_next_task` correctly gates ordinary backlog assignment away from those slots (the `"review_slot"` filter,
  `dispatch.py` R6, shipped 2026-07-13). But `ao_human_fleet_integration_2026_08_15` added a SEPARATE assignment path —
  `POST /api/slots/{slot_id}/human-claim` + its `GET .../human-claim-check` sibling in `server/routes/slots_worker.py`
  — that bypasses `pick_next_task` entirely by design (a human always names the task) and only pre-flight-checks
  `rank_eligible_tasks(..., scope=FilterScope.FLEET)`, which never evaluates the SLOT-scope `"review_slot"` filter.
  Unlike its sibling endpoints `human_heartbeat`/`human_usage_push` (both of which already gate
  `if slot_id not in human_slot_ids(): raise HTTPException(400, ...)`), `human_claim`/`human_claim_check` had no
  `human_slot_ids()` membership check at all — any `slot_id`, including the reserved review slot, could claim a live
  backlog task. Confirmed live via read-only SSM against the orchestrator VM (i-0c9b283b31d6b5ca7) 2026-08-16T17:02Z:
  the sole configured review slot (slot 2, `kind: 'review', reserved_for: 'review'`) showed `current_task:
  'cf_manifest_audit_first_full_rollup_findings-d1fc625d0914'`, `plan_ref: 'plans/active/issues/
  cf_manifest_audit_first_full_rollup_findings_2026_07_26.md'`, worker-style `/done` messaging, `assigned_at:
  2026-08-15T10:57:01Z` (~30h earlier, ~19h after the human-fleet routes shipped without the guard), `status: 'stale'`,
  `worker_alive: False`, `last_ping` ~11h stale — and `GET /api/agents` showed ZERO agents with `role: 'review'`. The
  reserved slot was occupied by a stuck ordinary task instead of running review's boot loop, so no review agent
  existed to be found — this is what "disappearing" concretely means: not a respawn-failure bug in the usual
  worker-liveness sense, but the reserved slot getting hijacked at the assignment layer by a route that skipped the
  gate every other human-fleet endpoint already had.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, review-agent, worker-lifecycle, human-fleet, dispatch, slot-reservation]
related:
  [
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: "2026-08-16"
author: main (Claude Code, interactive session, operator-reported)
parent_epic: orchestrator_master
resolved_by: agent-orchestrator (uncommitted working-tree diff — operator to confirm before ship)
locked_by:
source: >-
  Operator report, 2026-08-16: "the AO fleet's review role agent keeps disappearing" — asked to investigate, track, and
  harden/fix if a real bug.
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
---

# Review slot hijacked by the human-claim routes' missing `human_slot_ids()` guard

## What "disappearing" concretely means (with evidence)

Not a classic liveness/respawn gap (`WorkerLivenessKicker`/`AgentKeeper`/`HealthMonitor` all tick review correctly per
`agent-orchestrator-worker-liveness.md`). The reserved review slot (slot 2, the only one configured) was bound to an
ordinary Class-A backlog task by `POST /api/slots/2/human-claim`, which had no check against `config.review_slot_ids()`
or `human_slot_ids()`. Once bound, the slot ran an ordinary worker session (not review's `review` boot prompt), that
session wedged (`status: 'stale'`, `worker_alive: False`, `last_ping` ~11h stale at observation time,
`current_task`/`plan_ref` unchanged for ~30h), and because the slot was occupied by this non-review session,
`ensure_review_agents` (`server/autospawn.py`) — which only acts on slots with no live session — never re-established a
`role=review` agent. `GET /api/agents` showed zero `role=review` rows at observation time: from the operator's/
dashboard's perspective, review had vanished.

## Root cause (file:line)

- `server/routes/slots_worker.py` — `human_claim_check` (GET) and `human_claim` (POST, the actionable write via
  `ss.assign_task_to_slot`) both call `_human_claim_verdict` → `rank_eligible_tasks(session, backlog,
  scope=FilterScope.FLEET, ...)` (`dispatch.py:619-652`), which deliberately never runs the SLOT-scope filters
  (`"review_slot"`, `"scheduled_reserve"` — `dispatch.py:172-173, 340-357`) that `pick_next_task` (the normal dispatch
  path, `dispatch.py:575-616`) already gates on.
- Sibling endpoints `human_heartbeat` (`slots_worker.py:2987-2991`) and `human_usage_push` (`slots_worker.py:3125-3129`)
  both already guard `if slot_id not in human_slot_ids(): raise HTTPException(400, ...)`. `human_claim_check`/
  `human_claim` — added one day earlier by `ao_human_fleet_integration_2026_08_15` — never got the same guard.

## Fix (implemented, NOT committed/pushed — operator to confirm before shipping)

Added the identical `human_slot_ids()` membership guard to both `human_claim_check` and `human_claim` in
`server/routes/slots_worker.py`, matching the existing sibling-endpoint pattern exactly (400 + the same error-message
shape). Added two regression tests to `tests/test_human_fleet_endpoints.py`:
`test_claim_check_rejects_non_human_slot` (GET) and `test_claim_rejects_non_human_slot_and_does_not_bind_task` (POST,
asserts the `TaskRow` stays `status="queued"`/`dispatched_to=None` — the write never happens). Both new tests plus the
full existing `test_human_fleet_endpoints.py` (21 passed) and `test_dispatch_review_slot_gate.py` +
`test_dispatch_scheduled_reserve_gate.py` (10 passed, unaffected) pass locally.

## Todos

- [x] ✅ [OPERATOR] P1. **DONE 2026-08-16.** Shipped via `quickmerge.sh` — `agent-orchestrator@d13788ec2f`, verified
      against `HEAD` directly (not just a clean-tree assumption, per this workspace's own "ahead=0 ≠ landed" rule — a
      first quickmerge attempt silently lost this exact diff in a concurrent-commit race, caught and re-shipped in the
      same session). Both regression tests confirmed present in the landed blob.
- [ ] [OPERATOR] P2. Decide whether the currently-live review slot (slot 2 on the orchestrator VM) needs a manual
      recovery (kill the wedged ordinary-task session + let `ensure_review_agents` respawn review's boot loop) — this
      is a live-infra write action explicitly left out of this investigation's scope; verify current state via
      `GET /api/state` slot 2 before deciding it's still needed (it may self-resolve once the stuck task eventually
      completes/times out).
- [ ] [BACKEND] P3. Second, independent gap noted but not chased: `ensure_review_agents`/the AgentKeeper reap path
      appears to treat any review slot with `tmux_alive: True` as "something is running, leave it alone" rather than
      checking whether that something is actually review's own boot loop vs. a stray non-review session — this fix
      closes the ENTRY point (nothing should get bound there again), but does not add a detect-and-recover path for a
      review slot that ends up wedged by some other future mechanism. Worth a follow-up: should
      `ensure_review_agents`/`AgentKeeper` positively verify a review slot's live session is actually running the
      `review` prompt (not just any live session) before treating it as healthy?

## Progress Log

- 2026-08-16: Filed per direct operator report ("review keeps disappearing"). Investigated via `unified-trading-pm`
  (`agents/review.md`), `agent-orchestrator/server/` code reading (`autospawn.py`, `main_agent_keeper.py`,
  `context_lifecycle.py`, `health.py`), the existing archived prior-art docs on main/review context-lifecycle scoping
  (`ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md`,
  `main_agent_context_saturation_idle_gate_mismatch_2026_08_13.md` — both confirmed NOT the cause here, since they
  concern compact/idle-gate timing, not slot assignment), and live read-only SSM evidence against the orchestrator VM
  (`GET /api/agents`, `GET /api/state`) showing zero live `role=review` agents and the reserved slot bound to a stale
  ordinary task. Root-caused to `server/routes/slots_worker.py`'s `human_claim`/`human_claim_check` missing the
  `human_slot_ids()` guard their siblings already have. Fix implemented + tested (diff left uncommitted per this
  session's read-only-live/code-fix-only scope) — see "Fix" section above.
