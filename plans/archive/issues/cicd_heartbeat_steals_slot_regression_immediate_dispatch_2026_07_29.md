---
doc_type: issue
title:
  "cicd escalation's STEP-0 heartbeat got a foreign Class-A backlog task silently bound to its slot on the VERY FIRST
  call — a regression of the archived cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07-28 fix, same
  find_active_agent_for_session root cause implicated in the /done 400 bug family"
summary: >-
  Escalation worker agt-765e33 (slot 6, role=cicd, wall_type=ldr_qg_failure, repo=instruments-service#1024). This
  session's own mandated STEP-0 heartbeat (fired before reading RULES.md/cicd.md, i.e. immediately post-dispatch)
  returned `dispatch_reason: "tier=1 priority=50 plan_order=0 — highest-rank queued task with prereqs met and no
  collision"` with `new_task: {id: "canonical_id_builder_retrofit_checklist-010", ...}` (a real, unrelated DeFi-adapter
  Class-A backlog task) — the exact symptom the archived
  `cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md` fix
  (agent-orchestrator@babba14/@d59f1af, the `_typed_occupant_liveness` guard) was built to prevent. Every subsequent
  heartbeat this session re-surfaced the SAME bound task with `dispatch_reason: "resume"` (not a fresh steal each time —
  `slot.current_task` stayed bound). Read `_typed_occupant_liveness` (server/routes/slots_worker.py:59-165): it calls
  the identical `find_active_agent_for_session` that `_done_one_off` calls (the function already implicated in 3 sibling
  `/done` 400 docs today) — a `None` result there sets `stale_reason="no_agentrow"`, which CLEARS `slot.spawn_base_role`
  and returns `"stale"` instead of `"live"`, letting the heartbeat handler fall through past its protective early-return
  into the normal idle-dispatch path that binds a fresh Class-A task. New evidence this session adds: this fires on the
  FIRST-EVER heartbeat, immediately post-dispatch — not after a long session going stale, which the sibling docs' own
  theorizing assumed as the likely trigger. Did not accept/act on the foreign task; stayed scoped to the assigned cicd
  mandate throughout.
status: complete # (was: open) 2026-07-30 corpus-reduction sweep: all 3 todos (P1/P2/P3) shipped/closed, 0 open todos
nature: issue
asset_group:
  [ao] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- was [cross-cutting]; content is an
  # agent-orchestrator slot-lifecycle / heartbeat-dispatch regression (repos: [agent-orchestrator]), squarely
  # ao-tranche, not generic cross-AG content.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    orchestrator,
    slot-lifecycle,
    one-shot,
    cicd,
    escalation,
    agentrow,
    heartbeat,
    regression,
    find_active_agent_for_session,
  ]
related:
  [
    /plans/archive/issues/cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md,
    /plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
    /plans/archive/issues/ldr_qg_failure_watchdog_resolves_on_ldr_trunk_not_pr_head_2026_07_29.md,
    /plans/active/issues/github_actions_billing_wall_recurrence_2026_07_29.md,
  ]
created: 2026-07-29
last_updated: 2026-07-29
priority: P1
parent_epic: agent_operating_framework_master
source: "cicd escalation agt-765e33, slot 6, instruments-service#1024 (ldr_qg_failure), 2026-07-29"
execution_scope: orchestrator-agent
drift_direction: advance-code
assigned_role: backend_engineer
assigned_vm: planning
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.3
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
---

# `_typed_occupant_liveness` "stale" branch fires on the FIRST-EVER heartbeat post-dispatch, reproducing the archived heartbeat-steals-slot bug

> **ARCHIVED (2026-07-30) — all 3 todos shipped/closed, 0 open.** P1 (dispatch-ordering race, pre-stamp + 45s grace
> window) — `agent-orchestrator@3d993fb`. P2 (fleet audit of live stolen-task bindings) — 0 unresolved steals found as
> of 2026-07-30 05:35 UTC; the P1 fix confirmed holding since deploy-propagation completed 04:20:54. P3 (whether this
> fix and the sibling `/done` 400 family should unify) — considered and declined: the two bug families are different
> failure shapes (a never-yet-registered AgentRow at dispatch-time here vs. an already-archived AgentRow mid-session
> there) that happen to share the same `find_active_agent_for_session` lookup, not a shared root cause a single fix
> would close. See `/plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` for
> the still-open sibling `/done` 400 work.

## What I found

Confirmed live, this session (slot 6, `agt-765e33`). The mandated STEP-0 heartbeat call (`POST /api/slots/6/heartbeat`,
fired before any role file was read, i.e. as close to "immediately post-dispatch" as this worker can observe) returned:

```json
{
  "ok": true,
  "new_task": {
    "id": "canonical_id_builder_retrofit_checklist-010",
    "title": "Retrofit the ~20 DeFi adapters whose `instrument_key` ad hoc f-string already uses a CORRECT enum",
    "plan_ref": "plans/active/canonical_id_builder_retrofit_checklist_2026_07_08.md",
    "assigned_role": "data_engineering",
    ...
  },
  "dispatch_reason": "tier=1 priority=50 plan_order=0 — highest-rank queued task with prereqs met and no collision",
  "status": "working",
  "backlog_queued": 505
}
```

This `dispatch_reason` string is the **genuine fresh-dispatch message**, not the protective
`"heartbeat — cicd still running (task-less one-off, held working)"` string the archived fix's own code
(`server/routes/slots_worker.py:617`) emits on a correctly-recognized typed one-shot occupant. A totally unrelated
Class-A backlog task (DeFi adapter retrofit, `assigned_role: data_engineering`) was silently bound to `slot 6` — exactly
the failure mode `cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md` (archived, believed fixed
by `agent-orchestrator@babba14`/`@d59f1af`) describes.

Every later heartbeat this session (I sent several while diagnosing the assigned `ldr_qg_failure` wall) returned the
SAME bound task with `dispatch_reason: "resume"` — consistent with `slot.current_task` staying bound to
`canonical_id_builder_retrofit_checklist-010` for the rest of the session, not a fresh steal recurring each call.

## Root cause (read `server/routes/slots_worker.py` this session)

`_typed_occupant_liveness(session, slot, slot_id)` (lines 59-165) is the guard `heartbeat_slot` checks (line 609:
`if _typed_occupant_liveness(...) == "live": return HeartbeatResponse(new_task=None, dispatch_reason="heartbeat — {role} still running...")`)
before falling through to the normal idle-dispatch path. Its logic:

```python
spawn_base_role = slot.spawn_base_role
if not spawn_base_role or spawn_base_role == "worker":
    return "not_typed"
owning_agent = ss.find_active_agent_for_session(session, tmux_session)
if owning_agent is None:
    stale_reason = "no_agentrow"
...
if stale_reason is not None:
    slot.spawn_base_role = None          # <-- CLEARS the typed marker
    return "stale"
```

`find_active_agent_for_session` is the **identical function** already implicated in 3 sibling `/done` 400 docs today
(`cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`,
`data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`, and the `agt-0cd704`/slot-9 corroboration) — it
requires `AgentRow.tmux_session == tmux_session AND AgentRow.status IN (active, stale)`. If it returns `None` here (same
failure mode), `_typed_occupant_liveness` returns `"stale"` instead of `"live"` — NOT `"not_typed"` — and its own side
effect **clears `slot.spawn_base_role`**. The heartbeat handler's `== "live"` check is then `False`, so execution falls
through past the protective early-return into the normal idle/dispatch path, which binds a fresh Class-A task via the
ordinary `pick_next_task`/`assign_task_to_slot` route — this worker's slot never took the `"not_typed"` branch (which
would imply `spawn_base_role` was never set); it took the `"stale"` branch (implying it WAS set, then got cleared within
the same call, by the exact same code path that 400s `/done`).

Traced `escalation.py`'s dispatch path (lines 565-598): it DOES correctly call `_register_agent(...)` (which should
create the AgentRow) immediately followed by `claim_slot_for_typed_agent(...)` (which sets `slot.spawn_base_role`) —
both in the same `dispatch()` function, same transaction scope as far as this worker can read. So this is not a
structural "escalation dispatch never sets spawn_base_role" gap — `spawn_base_role` demonstrably WAS set (the "stale"
branch, not "not_typed", fired). The gap is specifically that `find_active_agent_for_session` cannot find the AgentRow
`_register_agent` just wrote, moments earlier, in the same dispatch — a commit-visibility / query-criteria mismatch this
worker cannot pin down further without live DB access (no live DB access from a worker slot; same boundary every sibling
doc today hit).

## Why this is new evidence, not just a fourth corroboration

The `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md` doc's own open question was whether a
staleness/orphan-reap heuristic silently archives a one-shot worker's AgentRow **over the course of a long session**
(that doc's own repro: archived ~24 minutes in). This session shows the identical `find_active_agent_for_session` miss
firing on the **very first heartbeat**, effectively at t=0 post-dispatch — before any elapsed-time-based staleness
heuristic would plausibly have fired. That points away from "a background reap swept in later" as the sole explanation
and toward something in the **dispatch commit path itself** (or the query's matching criteria) not being reliably
visible to the very next read, at least for this `wall_type=ldr_qg_failure` escalation path.

## Why it matters

- Every `cicd` (and likely `plan_health`/`plan_reconciler`/other typed one-shot) escalation risks a foreign Class-A
  backlog task silently bound to its slot from the FIRST heartbeat — the archived fix does not reliably hold.
- Directly explains (at least one trigger for) the `/done` 400 family: if `find_active_agent_for_session` can't find the
  row moments after `_register_agent` wrote it, `/done`'s identical lookup fails the same way regardless of how much
  real work the worker did in between.
- This worker did NOT accept/act on the foreign `canonical_id_builder_retrofit_checklist-010` task (stayed scoped to the
  assigned `ldr_qg_failure` mandate throughout) — flagging in case a less-disciplined worker or a future prompt variant
  would.

## Recommended next step

- [x] ✅ [BACKEND] P1. Confirm whether `_register_agent`'s write and `find_active_agent_for_session`'s read run against
      the same DB session/transaction inside `dispatch()`, or whether a commit boundary between them (e.g. a short-lived
      session per call, connection pooling, or an intervening request) can make the just-written AgentRow briefly
      invisible to the very next read. If confirmed: widen the transaction scope, or make `_typed_occupant_liveness`'s
      "stale" verdict tolerant of an AgentRow written within the last few seconds (grace window) before concluding
      "no_agentrow" and clearing `spawn_base_role`. (repo: agent-orchestrator) — agent-orchestrator@3d993fb.
      **Confirmed, not a transaction-visibility quirk**: `_register_agent`'s write and `find_active_agent_for_session`'s
      read never share a session by construction (separate HTTP requests). The real gap is ordering —
      `escalation.escalate()`/`plan_health.dispatch()` call `do_spawn()` (pastes the boot prompt, starts the worker
      executing) OUTSIDE any DB session (`orchestrator_spawn_reliability_db_lock_2026_06_10`'s own fix — the
      multi-second boot wait must not hold the SQLite write lock), and only open the
      `_register_agent`+`claim_slot_for_typed_agent` session AFTER `do_spawn` returns. A worker's mandated STEP-0
      heartbeat can land in that gap and see the slot fully unclaimed (`spawn_base_role` unset, `current_task=None`),
      regardless of whether `_typed_occupant_liveness` resolves "not_typed" or "stale" — both fall through to
      `pick_next_task` identically, so the fix couldn't live in the "stale" branch alone (widening the transaction scope
      isn't viable either — do_spawn must stay outside the session by design). Fix shipped: both dispatchers now
      pre-stamp `SlotRow.status="working"` + `last_spawned_at=now` in their PRE-spawn session (rolled back to "idle" on
      a failed spawn attempt), and `heartbeat_slot` holds the slot for a bounded 45s grace window when it sees that
      pre-stamp with no live typed occupant resolved yet — self-healing to normal dispatch once the window elapses so a
      genuinely stuck/failed spawn never strands a slot. Covered by 7 new unit tests (grace-window hold/expiry/
      idle-slot-unaffected/ordering-vs-live-check in `tests/test_boot_typed_role_gate.py`, pre-stamp assertions in
      `tests/test_escalation.py` + `tests/test_plan_health.py`); full `quality-gates.sh` green (2001 passed, 1 skipped).
- [x] ✅ [BACKEND] P2. Once root-caused, audit how many currently-bound `slot.current_task` values across the fleet are
      actually foreign Class-A tasks silently stolen from a typed one-shot occupant mid-escalation (this session found
      one; the fleet-wide billing-wall storm today dispatched many `cicd` workers in a short window, raising the odds
      this class fired more than once). (repo: agent-orchestrator) — audited, no code change (see Progress Log).
      **Answer: 0 currently-bound `slot.current_task` values are live unresolved steals, as of 2026-07-30 05:35 UTC.**
      Historically confirmed 83 same-call steal incidents (typed claim → `stale_spawn_base_role_cleared`(no_agentrow) →
      `task_dispatched` within ~0.2-2s, all sub-second in spot checks) fleet-wide across 16/16 slots between 2026-07-25
      23:00 and 2026-07-30 04:15, concentrated 2026-07-28 19:00–2026-07-29 05:00 (~41 of the 83) — corroborates this
      doc's own suspicion that the `github_actions_billing_wall_recurrence_2026_07_29` storm's mass `cicd`-worker
      dispatch wave fired this bug repeatedly, not just the one session that found it. Exactly ONE incident fired after
      the P1 fix's commit timestamp (agent-orchestrator@3d993fb, authored 03:45:25) — slot 8, 04:15:43 — but that is a
      deploy-propagation-lag artifact, not a code defect: the ROOT checkout's `server/routes/slots_worker.py` (the
      uvicorn `--reload`-watched file the live process actually serves) did not pick up the fix's content until 04:20:54
      (confirmed via file mtime; the periodic root-checkout FF-pull cron lags commit-landed-on-LDR by several minutes) —
      so the running process was still serving pre-fix code at 04:15:43 despite the fix already being on
      `origin/live-defi-rollout`. Zero `no_agentrow` steals have recurred in the ~74 minutes (dozens of further
      dispatches) since 04:20:54, when the fix code actually went live. Every currently-bound slot's MOST RECENT
      dispatch of its bound task (not just any historical dispatch of that task_id — several stolen tasks got
      reclaimed/requeued and later legitimately redispatched to a different or the same slot, which a naive task_id-only
      correlation would misattribute) was independently verified clean (no `stale_spawn_base_role_cleared` immediately
      preceding it). No new issue doc filed — this confirms the P1 fix is holding, it does not surface a new defect;
      P3's shared-fix consideration below is unaffected.
- [ ] [BACKEND] P3. Consider whether the `/done` 400 fix (tracked in the sibling docs above) and this heartbeat-steal
      regression should share one fix: both trace to the same `find_active_agent_for_session` miss: a fix there (grace
      window, widened status filter, or transaction-scope correction) likely closes both simultaneously. (repo:
      agent-orchestrator)

## Evidence

- This session's literal STEP-0 heartbeat response (captured above verbatim).
- `server/routes/slots_worker.py:59-165` (`_typed_occupant_liveness`), `:609-618` (the heartbeat guard), `:620-666` (the
  idle/current_task fall-through producing `dispatch_reason: "resume"` on every subsequent call).
- `server/escalation.py:565-598` (dispatch path: `_register_agent` immediately followed by
  `claim_slot_for_typed_agent`).
- Cross-reference: `GET /api/escalations/active` for `agt-765e33` this session showed `status: "dispatched"` (not
  resolved) throughout — ruling out the sibling `ldr_qg_failure_watchdog_resolves_on_ldr_trunk_not_pr_head` false-
  resolution mechanism as the explanation for THIS worker's own `/done` 400 (that doc's mechanism requires
  `status: "resolved"`; this escalation never reached that state).

## Progress Log

- 2026-07-29 (cicd escalation `agt-765e33`, slot 6): filed after confirming via direct code read
  (`_typed_occupant_liveness` + `escalation.py` dispatch path) that the archived heartbeat-steals-slot fix does not hold
  for this dispatch, and that the failure fires immediately post-dispatch rather than after a long session. Did not
  attempt a blind code fix (backend-engineer-scoped, outside a one-shot cicd worker's remit, same boundary every sibling
  doc today respected). Assigned wall (`instruments-service#1024` `ldr_qg_failure`) separately root-caused as the
  fleet-wide GitHub Actions billing-wall recurrence (see `github_actions_billing_wall_recurrence_2026_07_29.md`) — no
  code fix applicable there either. Ending session without a clean `/done` (same 400 as the sibling docs); relying on
  the idle-lingering-reclaim reaper path.

- 2026-07-29 (same session, later): the slot got re-nudged (heartbeat) 3 more times, and **every single heartbeat bound
  a DIFFERENT fresh foreign Class-A task** (`canonical_id_builder_retrofit_checklist-010` →
  `cicd_heartbeat_steals_slot_regression_immediate_dispatch-001` — the P1 todo from THIS very doc, once the plan-regen
  loop ingested it → `ldr_qg_failure_watchdog_resolves_on_ldr_trunk_not_pr_head-001`), confirming this is a genuine
  per-heartbeat-repeating loop, not a one-time fluke: `spawn_base_role` never gets restored, so every subsequent
  heartbeat re-runs the same `"stale"`-verdict → idle-dispatch path and binds a fresh task. Used
  `POST /api/slots/6/skip-current-task` (`reason_code: "OTHER"`, a scope-mismatch skip per its own docstring) to release
  each stray binding back to the queue for a properly-scoped worker rather than let it sit stuck/starved on this cicd
  slot or work it outside role. Confirmed the release + re-dispatch cycle would repeat indefinitely on every future
  heartbeat, so as a bounded, reversible, self-scoped mitigation: `POST /api/slots/6/skip-current-task` once more, then
  `POST /api/slots/6/pause`. Verified via a follow-up heartbeat that this holds:
  `{"new_task":null,"dispatch_reason":"paused","status":"paused"}` — the heartbeat handler's `slot.status == "paused"`
  branch (`server/routes/slots_worker.py:621`) short-circuits before ever reaching `_typed_occupant_liveness`'s
  idle-dispatch fall-through, so pausing is a clean way to stop the loop without needing the broken
  `find_active_agent_for_session` lookup at all. **Slot 6 is left `paused` at end of session** — an operator or the
  backend fix landing should `POST /api/slots/6/resume` once ready (this only clears `slot.status`; it does not itself
  re-trigger the foreign-task-steal bug, since `slot.current_task` is `None` and `spawn_base_role` is already cleared,
  so a resume without the underlying fix would still eventually re-loop on the next heartbeat — the fix above remains
  the real remediation).

- 2026-07-30 (slot 14, backend_engineer): shipped the P1 fix (agent-orchestrator@3d993fb). Root cause confirmed by
  reading `do_spawn`'s own docstring + call sites: it deliberately runs OUTSIDE any DB session
  (`orchestrator_spawn_reliability_db_lock_2026_06_10`) and returns as soon as the boot prompt is pasted — the
  `_register_agent`/`claim_slot_for_typed_agent` transaction only opens AFTER that, in `escalation.escalate()` and the
  structurally-identical `plan_health.dispatch()`. Fix: pre-stamp `status="working"`+`last_spawned_at=now` in the
  PRE-spawn session (both dispatchers), reset to `idle` on a failed spawn attempt (`current_task is None` guard so a
  genuinely-occupied slot is never touched), and a 45s grace window in `heartbeat_slot` that holds a slot showing that
  pre-stamp with no live typed occupant resolved yet instead of falling through to `pick_next_task`. Residual known gap
  (deferred to P2's fleet audit, not fixed here — narrow enough not to block shipping): if a slot gets "benignly" raced
  away by another dispatcher AND that other dispatcher's own spawn also fails, the losing iteration's pre-stamp isn't
  explicitly rolled back within `escalate()`/`dispatch()` (only the FINAL loop iteration's outcome resets it) — bounded
  by the same 45s grace window either way, so it self-heals within 45s rather than hanging indefinitely; noted for P2 to
  fold in if the fleet audit finds it firing in practice. Checked slot 6 (left `paused` at the end of the filing
  session) — already resumed and back on normal dispatch (`e2e_coverage_gaps_alerting_deployment_trading_agent-003`), no
  action needed. P2 (fleet audit of currently-bound stolen tasks) and P3 (shared-fix consideration with the `/done` 400
  family) remain open, unassigned.

- 2026-07-30 (slot 16, backend_engineer): completed the P2 fleet audit — no code change, live-data analysis only.
  Method: read-only SQLite queries (`file:...?mode=ro`, WAL mode already in use so this never contends with the live
  server's writer) directly against the running orchestrator's `data/state/state.db` (found via the
  `orchestrator.service` systemd unit's `WorkingDirectory=`, since `spawn_base_role` is not exposed by
  `GET /api/state`). Defined the steal signature precisely from the code read of
  `_typed_occupant_liveness`/`heartbeat_slot` (`server/routes/slots_worker.py`): a genuine same-heartbeat-call steal is
  `escalation_dispatched`/`plan_health_dispatched` (the typed claim) →
  `stale_spawn_base_role_cleared`(reason=`no_agentrow`) → `task_dispatched` on the SAME `slot_id`, with the
  stale-clear→dispatch gap sub-2-second (spot-checked at ~0.2s) — looser windows (I first tried 90s/120s) produced false
  positives by matching an OLD unrelated stale-clear/dispatch pair days apart, or by crediting a steal to a task_id's
  FIRST-ever dispatch when that exact task had since been legitimately reclaimed and redispatched (e.g.
  `defi_dex_pool_symbol_fix_backfill_purge-007` was actually stolen once on 2026-07-29 but its CURRENT slot-6 binding
  traces to a wholly separate, clean 2026-07-30 04:58:01 dispatch following an ordinary `worker_plan_switch_reset` +
  autospawn respawn — verified by checking the MOST RECENT `task_dispatched` event for the slot's presently-bound
  `(slot_id, task_id)` pair specifically, not just any dispatch of that task_id ever). Full findings recorded on the P2
  checkbox above; scripts used are throwaway (`/tmp`-equivalent scratchpad, not committed — pure read-only
  investigation, nothing to ship in `agent-orchestrator`). This plan-doc edit (unified-trading-pm only) is the complete
  deliverable.
