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
resolved_by: agent-orchestrator@d13788ec2f
locked_by:
source: >-
  Operator report, 2026-08-16: "the AO fleet's review role agent keeps disappearing" — asked to investigate, track, and
  harden/fix if a real bug.
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: []
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/tests/test_human_fleet_endpoints.py,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    agent-orchestrator/server/autospawn.py,
  ]
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
- [x] ✅ [BACKEND] P3. **DONE 2026-08-19.** Second, independent gap — `ensure_review_agents` treated any review slot
      with `tmux_alive: True` as "something is running, leave it alone" without ever checking whether that something
      was actually review's own boot loop vs. a stray non-review session. Fixed via
      `agent-orchestrator@13b51c2e1e` (shipped `--isolated` under confirmed heavy concurrent contention on the shared
      checkout — an unrelated peer session's in-progress WIP was independently confirmed as the source of the only
      other quality-gate failures at ship time, not this change; independently re-verified as an ancestor of
      `origin/live-defi-rollout` post-push, not just trusted from the script's exit code). Added
      `_review_slot_occupant_is_verified_review()` (`server/autospawn.py`): requires a `role=review` `AgentRow`
      actually registered against the exact tmux session before trusting the working-pane-refresh /
      heartbeat-silent checks that follow it. A boot-grace exemption (anchored on the tmux session's own measured
      creation time via `tmux_spawn.session_created_at`, mirroring `orphan_reap.py`'s PID-age boot-grace pattern —
      not DB bookkeeping, so it is robust to whatever mechanism actually created the session) protects a freshly
      (re)spawned review agent that has not self-registered yet. Past that grace with zero registration, the
      occupant is killed and respawned via the same account-pick + `_do_spawn` path a hung review agent already
      uses (`review_slot_occupied_by_non_review_session` activity-log event). Regression tests added to
      `tests/test_autospawn.py` covering both cases: a genuinely-running (verified) review session is left alone
      (`test_ensure_review_agents_runs_normal_checks_when_review_registration_verified`), an unregistered session
      still within boot grace is left alone
      (`test_ensure_review_agents_leaves_alone_unregistered_session_within_boot_grace`), and a stray non-review
      occupant past boot grace is detected and recovered
      (`test_ensure_review_agents_kills_and_respawns_non_review_slot_occupant`) — plus 4 focused unit tests on the
      new helper itself. Full agent-orchestrator quality gate green (4151 passed, 8 skipped) inside the isolated
      ship worktree.

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
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **na-eligibility-audit 2026-08-17 (ao tranche)** [body-hash:da3ed222c3680a3d]: KEEP-NA — the 'second, independent gap' item (ensure_review_agents liveness-verification depth) is ALREADY claimed by the active `ao_satellite_ao_dispatch_batch22_2026_08_16.md` (its todo 6 cites this doc + this exact todo text); leave open, do not duplicate. The [OPERATOR] manual-recovery-decision item stays KEEP-NA.
- 2026-08-19: Implemented + shipped the `[BACKEND] P3` "second, independent gap" fix — see the flipped todo above for
  the full evidence (`agent-orchestrator@13b51c2e1e`). **Superseding `ao_satellite_ao_dispatch_batch22_2026_08_16.md`'s
  todo 6 claim on this exact item**: that plan is `status: draft` and was never activated/ingested by AO (confirmed via
  its frontmatter before starting this work), so it held no live lock on the item — nothing to unlock or coordinate
  with. Noting here so a future `/ag-closeout-audit`, `/na-eligibility-audit`, or operator activating that draft plan
  does not re-dispatch already-completed work from its todo 6; that plan's own todo 6 checkbox was intentionally left
  untouched by this session (out of scope for this doc's edit) but its "Done when" criteria are now satisfied by this
  fix. The `[OPERATOR] P2` manual-recovery-decision todo remains open (live-infra judgment call, unrelated to this
  fix) — this doc stays `active`, not archived.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
