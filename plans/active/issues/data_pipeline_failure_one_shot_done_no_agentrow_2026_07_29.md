---
doc_type: issue
title:
  "`data_pipeline_failure` one-shot escalation worker cannot signal `/done` (`one_shot_complete: true`) — 400 'no active
  agent owns its session' despite a code path that should have registered the AgentRow"
summary: >-
  Escalation worker agt-79063c (slot 10, role=data_pipeline_failure) finished its assigned DP-FETCH-009 fix and tried to
  signal completion via `POST /api/slots/10/done {task_id, sha, evidence, one_shot_complete: true}` per its boot
  contract. The call 400'd with "one_shot_complete on slot 10 but no active agent owns its session 'orch-slot-10' — a
  Class-A worker must /done with a task_id" on two separate attempts (different task_id values, same error, minutes
  apart, with a heartbeat call succeeding normally in between). Code reading in `agent-orchestrator` shows
  `server/escalation.py`'s `escalate()` success path DOES register an AgentRow (`lifecycle="one_shot"`,
  `tmux_session=tmux_spawn.session_name(slot_id)`, `agent_id=escalation_id`) for exactly this role
  (`data_pipeline_failure` IS in `_AGENT_KIND_BY_PROMPT_TEMPLATE`), so the registration SHOULD have happened at dispatch
  time — yet `find_active_agent_for_session` (which requires `AgentRow.status IN (active, stale)` matched to
  `tmux_session`) finds nothing at `/done` time. Not root-caused to the exact failure point (no live DB access from a
  worker slot) — flagging with the diagnostic head-start for whoever has orchestrator-DB access.
status: open
nature: issue
asset_group:
  [ao] # corrected 2026-08-02 (/ag-closeout-audit cross-cutting, operator-ruled) -- was [cross-cutting]; the defect is
  # agent-orchestrator's one-shot AgentRow / `/done` lifecycle (repos: [agent-orchestrator]), squarely ao-tranche --
  # `data_pipeline_failure` is the worker ROLE that hit it, not a data/multi-AG subject.
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, one-shot-lifecycle, escalation, data_pipeline_failure, done-endpoint, agentrow]
related:
  [
    /plans/active/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-29
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: "data_pipeline_failure escalation worker, slot 10, escalation_id agt-79063c"
last_updated: 2026-07-29
context_scope:
  [
    /plans/active/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/state_store/agents.py,
  ]
---

# `data_pipeline_failure` one-shot worker's `/done {one_shot_complete: true}` 400s despite a registration path that should cover it

## What I found

Slot 10 was booted as a one-shot `data_pipeline_failure` escalation worker (`escalation_id=agt-79063c`,
`repo=market-tick-data-service`, `pr_number=0`). After completing its assigned DP-FETCH-009 fix (see the sibling
`cefi_high_attempted_failed_batch_cluster_2026_07_23.md` / `deribit_options_chain_af_g4_blocker_2026_07_03.md` Progress
Log entries for that work), it followed its boot contract's exit step:

```
POST http://localhost:8765/api/slots/10/done
{"task_id": "agt-79063c", "sha": "d6dcb97", "evidence": "...", "one_shot_complete": true}
```

Response (400), reproduced twice (different `task_id` values tried — `""` and `"agt-79063c"` — same error both times,
with a successful `POST /api/slots/10/heartbeat` call in between that returned `{"ok": true, "status": "working", ...}`
normally):

```
{"detail":"one_shot_complete on slot 10 but no active agent owns its session 'orch-slot-10' — a Class-A worker must /done with a task_id."}
```

### Code path traced (read-only, `agent-orchestrator` repo checked out in this slot)

- `server/routes/slots_worker.py::_done_one_off` (the `one_shot_complete` handler) computes
  `tmux_session = slot.tmux_session or tmux_spawn.session_name(slot_id)`, then calls
  `ss.find_active_agent_for_session(session, tmux_session)`; a `None` result raises exactly the 400 seen.
- `server/state_store/agents.py::find_active_agent_for_session` requires
  `AgentRow.tmux_session == tmux_session AND AgentRow.status IN ("active", "stale")`.
- `server/escalation.py`'s `escalate()` success branch (the path that should have spawned slot 10 for this
  `wall_type=data_pipeline_failure` dispatch) DOES call
  `_register_agent(... agent_id=escalation_id, tmux_session=tmux_session_name, lifecycle="one_shot", ...)` where
  `tmux_session_name = tmux_spawn.session_name(slot_id)` — i.e. `"orch-slot-10"`, matching the `/done` error's own
  session name. `data_pipeline_failure` IS a registered key in `_AGENT_KIND_BY_PROMPT_TEMPLATE`
  (`server/escalation.py:134-137`), so this is not the already-fixed `ag_closeout_auditor`-family "never routed through
  the right dispatch endpoint" bug class (that fix — lazy AgentRow creation in `boot_slot` — is scoped to
  `_plan_health.PLAN_HEALTH_FAMILY_ROLES` only, per `tests/test_boot_typed_role_gate.py`'s
  `test_direct_boot_of_plan_health_family_role_lazily_creates_agentrow` /
  `test_direct_boot_lazy_agentrow_then_one_shot_complete_succeeds` — a DIFFERENT family, but worth noting as the
  precedent bug shape and possibly the same fix pattern applies).

### Not established (needs live DB access this worker slot does not have)

- Whether the AgentRow for `agt-79063c` was ever actually created (i.e. whether `escalate()`'s success branch is truly
  what spawned this session, vs. some other path this investigation didn't find).
- If it WAS created: whether its `status` had already transitioned away from `active`/`stale` (e.g. an intervening
  `HealthMonitor` sweep, a slot-reclaim, or a second dispatch reusing slot 10) before this worker's own `/done` call —
  the gap between dispatch and this worker's `/done` call spanned a long diagnostic session (the worker also did
  substantive DP-FETCH-009 work + a self-caught mistake + revert in between, so real wall-clock time elapsed).
- If it was NEVER created: why `escalate()`'s registration code, which reads as unconditional on the success branch,
  didn't run for this dispatch — a spawn-failure branch that skipped straight to the
  `if err and not _is_no_capacity_error(err)` path without the `else` ever executing would explain it, but this worker
  has no way to see which branch fired for its own dispatch.

## Why this matters

Per `ao_uniform_agent_liveness_contract_2026_07_20` (referenced in `_done_one_off`'s own docstring), a one-shot agent
that cannot cleanly signal `/done` leaves its tmux session to be reaped only via the idle-lingering-reclaim path instead
of the intended `lifecycle-complete` archive — the exact "finished-immortal" failure mode that contract was built to
close. This worker's session ended by simply stopping tool calls after logging the blocker via `/progress`, not via a
clean `/done`.

## Recommended next step

Whoever has orchestrator-DB access (or a review/main agent with dashboard JWT) should: (1) query the `AgentRow` table
for `agent_id='agt-79063c'` to see whether it exists at all, and if so its current `status`/`tmux_session`; (2) if it
never existed, trace `escalate()`'s actual branch taken for this dispatch (server logs / `escalation_dispatched`
activity event, which per the code IS logged on the success branch — check whether that event fired for this
escalation_id); (3) if it existed but flipped to a non-active/stale status, find what transitioned it and whether
`_done_one_off`'s status filter should be widened or the transition should be blocked while a one-shot worker's task is
still in flight.

## Todos

- [ ] [DATA] P2. Query the live `AgentRow` for `agent_id='agt-79063c'` (or the `escalation_dispatched` activity log
      entry with that `escalation_id`) to determine whether the registration ever happened, and if so what changed its
      status before this worker's `/done` call.
- [ ] [CODE] P2. Once root-caused: fix the gap (either the registration path for `data_pipeline_failure` dispatches, or
      widen/guard `_done_one_off`'s active-agent lookup), and add a regression test mirroring
      `test_direct_boot_lazy_agentrow_then_one_shot_complete_succeeds` but for the `escalation.py` dispatch path rather
      than the `plan_health` boot path.

## Progress Log

- **2026-07-29 (data_pipeline_failure escalation worker, agt-79063c):** Filed after two failed `/done` attempts blocked
  a clean session exit for an otherwise-complete DP-FETCH-009 escalation (see
  `cefi_high_attempted_failed_batch_cluster_2026_07_23.md` for that work). Traced the code path as far as possible
  without live DB/dashboard access; left the remaining root-cause step (which branch fired / what changed the AgentRow's
  status) as the first todo for whoever picks this up. Did not attempt a blind code fix without confirming which of the
  two failure hypotheses (never-registered vs. registered-then-status-changed) is correct.

- **2026-07-29 (cicd escalation worker, slot 9, `agt-0cd704`, role=`cicd` not `data_pipeline_failure`):** corroborating
  — same 400 (`"no active agent owns its session 'orch-slot-9' ... a Class-A worker must /done with a task_id"`) on two
  `/done {one_shot_complete: true}` attempts, once with `task_id: ""` and once with `task_id: "agt-0cd704"` — confirms
  this is not `data_pipeline_failure`-specific (title should probably be read as the _discovering_ role, not the
  _affected_ role scope) and not sensitive to which `task_id` value is sent. Ending session without a clean `/done` per
  this doc's own precedent (no blind fix attempted); relying on the idle-lingering-reclaim reaper path.

- **2026-07-29 (cicd escalation worker, slot 6, `agt-765e33`, role=`cicd`, wall_type=`ldr_qg_failure`,
  repo=`instruments-service#1024`):** second `cicd`-role corroboration, different wall_type/repo than slot 9's. Same 400
  on both `task_id: ""` and `task_id: "agt-765e33"` attempts (a heartbeat call to the same slot succeeded normally in
  between, matching slot 10's observation that the slot itself is reachable — only the AgentRow lookup fails). Unrelated
  to this session's actual assigned wall: that reproduced as the fleet-wide GitHub Actions billing-wall recurrence (see
  `github_actions_billing_wall_recurrence_2026_07_29.md`) — a separate, already-tracked, operator-gated root cause with
  no code fix available; noting this explicitly so a reader doesn't conflate the two blockers (one is GitHub's billing
  API, the other is this orchestrator's own local `/done` endpoint — no causal link between them). Ending session
  without a clean `/done` per the established precedent; relying on the idle-lingering-reclaim reaper path.

- **na-eligibility-audit 2026-07-30**: RECLASSIFY NA → planning — both todos are bounded: query the live
  AgentRow/`escalation_dispatched` record for a named escalation_id, then fix whichever of the two stated hypotheses it
  proves, with a named precedent regression test. All 3 citations are `related:` cross-refs, not dispatch claims.

- **2026-07-31 (data_pipeline_failure escalation worker, slot 2, `agt-8fa8d1`, wall_type=`data_pipeline_failure`,
  repo=`market-tick-data-service`):** fourth corroboration, same shape — 400 on three `/done {one_shot_complete: true}`
  attempts (`task_id: ""`, `task_id: "agt-8fa8d1"`, retried after a `heartbeat` call whose `dispatch_reason` read "spawn
  registration pending (grace window, holding slot)" — that text did not resolve the mismatch; heartbeat itself
  succeeded normally every time, only the AgentRow lookup fails, matching all three prior reports). This session's
  actual assigned root-cause fix (DP-VM-002 false-CRITICAL on an early-SPOT-preempted VM whose in-guest shutdown-script
  never ran) shipped clean and unrelated: `unified-trading-library@61566617` + `deployment-service@09a2374`, both
  QG-green on `live-defi-rollout`. Ending session without a clean `/done` per the established precedent; relying on the
  idle-lingering-reclaim reaper path. Not attempting the diagnostic todos below (no orchestrator-DB/dashboard access
  from this worker slot, same constraint every prior reporter hit).

- **2026-08-01 (na_eligibility_auditor, slot 2, `agt-8e95ca`, mode=`na_eligibility`, tranche=`ao`):** fifth
  corroboration, a NEW variant of the same root cause. This session's `/boot` call never registered a
  `na_eligibility_auditor` AgentRow at all — the server instead returned a stale/unrelated Class-A backlog task
  (`code_tarball_refresh_job_silently_failing_since_2026_07_30-001`, `assigned_role: infra`) already bound to slot 2. A
  subsequent `/done {task_id: "", one_shot_complete: true}` 400'd with the same message this doc already tracks ("no
  active agent owns its session 'orch-slot-2' ... a Class-A worker must /done with a task_id"), and a follow-up
  heartbeat confirmed the server still sees slot 2 as the Class-A `code_tarball_refresh` worker
  (`dispatch_reason: "resume"`), not as this session's actual na_eligibility_auditor dispatch. Unlike the four prior
  reports (which hit the gap AFTER real work but WITH a correctly-registered AgentRow), this occurrence never had a
  matching AgentRow to begin with — suggesting the registration gap can also manifest as a `plan_health_dispatch` spawn
  landing on a slot whose tmux session already carries a DIFFERENT role's live claim, i.e. the same collision class as
  `/plans/archive/issues/persistent_slot_tmux_session_hijacked_by_transient_plan_health_dispatch_2026_08_01.md` (also
  reclassified to `planning` this same audit run) rather than a pure post-hoc AgentRow-status change. This session's
  actual assigned work (the `/na-eligibility-audit ao` run) is independently git-verified complete regardless — 4
  doc-edit commits + 1 ratchet-baseline commit, all confirmed ancestors of `origin/live-defi-rollout`
  (`ded844253`/`c4a8dc394`/`96797d327`/`f667a4dc9`/`5411ba307`). Ending session without a clean `/done` per the
  established precedent; relying on the idle-lingering-reclaim reaper path. from this worker slot, same constraint every
  prior reporter hit).
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
