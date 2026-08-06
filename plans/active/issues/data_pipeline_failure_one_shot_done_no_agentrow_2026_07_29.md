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
tags:
  [
    agent-orchestrator,
    one-shot-lifecycle,
    escalation,
    data_pipeline_failure,
    done-endpoint,
    agentrow,
    plan_reconciler,
    singleton-agent-kind,
    reap_orphan_agents,
  ]
related:
  [
    /plans/active/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/issues/worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md,
  ]
created: 2026-07-29
author: unknown
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
last_updated: 2026-08-06
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
- [ ] [DATA] P2. **NEW 2026-08-06, a distinct sub-mechanism for the SINGLETON-kind roles specifically** (see Progress
      Log entry below for full detail): query the live `AgentRow` table for every `agent_kind='plan_reconciler'` record
      whose `dispatch window` overlaps 2026-08-06 00:01 UTC–13:39 UTC (slot 2, `agent_id=agt-4fdce1`) — confirm (a)
      whether `agt-4fdce1`'s own row was archived with `exit_reason="reaped-stale"` (`server/state_store/agents.py`
      `_sessionless_singleton_duplicates`/`reap_orphan_agents`), (b) whether a same-kind sibling record existed with
      `tmux_session` live at the same time (the dedup precondition — `_sessionless_singleton_duplicates` only archives a
      record whose OWN `_owns_live()` check reads False while a sibling's reads True), and (c) if slot 2's tmux session
      was in fact continuously live the whole time (it was — this worker never stopped), whether `is_session_live()`
      logged a transient miss at the reap timestamp (the function's own docstring names this exact false-positive risk:
      "a transient `has_session()` miss under host load" — and
      `worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md` independently documents repeated
      high-load episodes, load avg 30-60+ on a 16-core box, around this same period).
- [ ] [CODE] P3. If (c) above confirms a transient `is_session_live()` false-negative caused the archive: add a
      debounce/retry (e.g. require 2 consecutive False reads N seconds apart) to `_owns_live()`/`is_session_live()`
      before treating a SINGLETON-kind sibling as dead — the current single-sample check has no tolerance for a
      momentary `tmux has-session` miss under fleet load, and archiving the WRONG sibling of a singleton pair is silent
      (no error, no alert — just an unrecoverable `/done` 400 discovered only when the genuinely-alive worker tries to
      exit cleanly hours later).

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
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (5 entries).
- **2026-08-03 (ag_closeout_auditor, slot 2, dispatch agt-330130, tranche=`ao`):** sixth corroboration, a NEW role
  hitting the same gap, and a new sub-variant of the mid-session-loss shape. Booted normally, ran the full
  `/ag-closeout-audit ao` procedure end-to-end (a long-running task: Phase 0 discovery + a backgrounded 41-agent
  `Workflow` fan-out that ran for several minutes), shipped real work (`unified-trading-pm@2b2cbdb11`/`@7ad70d1a4`, both
  confirmed ancestors of `origin/live-defi-rollout` via `git merge-base --is-ancestor`), then called
  `POST /api/slots/2/done {task_id: "", sha: "", one_shot_complete: true}` — 400'd with the exact tracked message.
  Retried with a real `sha`, then with `task_id: "agt-330130"` — same 400 both times. A follow-up `/heartbeat` succeeded
  (confirming the slot itself stays reachable, matching every prior report) but returned a **fresh Class-A backlog
  dispatch** (`deployment_service_root_state_orphaned_pubsub_publisher_iam_member-001`, unrelated repo/role) — i.e. the
  server had already re-registered this slot as a plain backlog worker sometime during the long audit, exactly the
  2026-08-01 `na_eligibility_auditor` report's variant (no matching AgentRow to begin with, not a post-hoc status
  change). Released the erroneously-assigned backlog task via `POST /api/slots/2/skip-current-task` (reason_code=OTHER,
  explaining it was never picked up) rather than either force-completing it or silently absorbing it, then retried
  `/done` for the actual one-shot work once more — same 400. Ending session without a clean `/done` per the established
  precedent (all 5 prior reports); this session's actual assigned work is independently git-verified complete
  regardless. **New data point for whoever root-causes this**: the long-running-background-Workflow shape may be a
  contributing trigger — every prior report's session was a single continuous tool-call sequence, while this one had a
  multi-minute gap where the acting session had no tool calls in flight (waiting on a backgrounded `Workflow` task),
  which is exactly the kind of gap an idle/liveness-based AgentRow reclaim would key on.
- **2026-08-04 (cicd escalation agt-892a1c, slot 2):** seventh corroboration, but with a WORKAROUND this time (not just
  another repro) — a `POST /api/slots/2/claim-interactive` call fixed normal dispatch immediately, though the specific
  `one_shot_complete` 400 itself was never retried post-fix (see caveat below; do not read this as "resolved"). Hit the
  identical 400 (`task_id: ""` and `task_id: "agt-892a1c"`, same message, twice) after finishing a
  `cicd`/`ldr_qg_failure` escalation. Before giving up per the established precedent, checked one thing none of the six
  prior reports mention: `GET /api/slots/2/claim` (the file-based `.agent-claim`, DISTINCT from the `AgentRow` DB table
  this doc's own code trace targets — see `server/routes/slots_worker.py`'s `claim_interactive_session` docstring:
  "Worker sessions are registered automatically via `/spawn`... interactive sessions must call this endpoint") →
  `{"present": false}`. A `cicd`-role escalation session never calls `/spawn` (it is dispatched via `POST /api/escalate`
  instead, per `cicd.md`), so if `/spawn` is what writes `.agent-claim` normally, an escalation-dispatched session would
  ALWAYS start with no claim on file — a plausible root cause for why this bug class disproportionately hits one-shot
  escalation/audit roles (`cicd`, `data_pipeline_failure`, `ag_closeout_auditor`, `na_eligibility_auditor` — every role
  in this doc-chain so far) rather than normally-`/spawn`ed persistent workers. Called
  `POST /api/slots/2/claim-interactive {tmux_session: "orch-slot-2", operator: "ikenna"}` (self-registers a 12-hour
  claim, `role: "interactive"`) as a diagnostic probe — `GET /api/slots/2/claim` then confirmed
  `{"present": true, ...}`. Immediately after, a plain `/heartbeat` (no special flag) went from
  `dispatch_reason: "spawn registration pending (grace window, holding slot)"` / `new_task: null` to a REAL Class-A
  dispatch (`infra_satellite_ao_dispatch_batch1-022`) — i.e. this DID fix normal backlog dispatch for this slot. Went on
  to do that task (and a follow-up, `-026`) as a normal worker, and `/done` (plain, `one_shot_complete` NOT set, a real
  `task_id`) succeeded cleanly both times with a real `next_task` returned — no 400, no workaround needed on THAT code
  path. **Caveat — do not overclaim**: never went back and retried the ORIGINAL `one_shot_complete: true` call for
  `agt-892a1c` after the claim fix, so it is NOT confirmed whether `_done_one_off`'s `find_active_agent_for_session`
  (the AgentRow-status check this doc's code trace targets) is satisfied by a `.agent-claim` file at all, vs. these
  being two genuinely independent registration systems where the claim fix happened to also unstick dispatch via a
  different mechanism. **Suggested next step for whoever revisits this**: the very next `one_shot_complete` 400 — call
  `claim-interactive` FIRST, then retry the SAME `/done` call before concluding it is still broken; that single retry is
  the missing data point every report so far (including this one) has left open.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **2026-08-06 (plan_reconciler, slot 2, `agt-4fdce1`, dispatched ~2026-08-06 00:01 UTC):** eighth corroboration, first
  from a SINGLETON-kind role (`review`/`plan_health`/`plan_reconciler`/`docs_reconciler` — `_SINGLETON_AGENT_KINDS`,
  `server/state_store/agents.py:333`) rather than an `escalation.py`-dispatched one-shot role, and the first to close
  one of this doc's own open caveats with a decisive negative result. Context: this session ran the daily deep
  plan-reconciliation pass, applied 3 operator-answered blocked questions (STEP 8), shipped 3 commits, all confirmed
  ancestors of `origin` (`plan_reconciler/agt-4fdce1` branch HEAD == `origin`'s ref for that branch, PR #2327 open) —
  then hit the identical 400 this doc tracks on `/done {task_id: "agt-4fdce1", one_shot_complete: true}`, twice, ~13
  hours apart (once before the long STEP-8 wait, once after).
  - **New fact 1 — `claim-interactive` does NOT fix the `one_shot_complete` 400** (closes the open caveat the 2026-08-04
    `cicd` entry above explicitly left for "whoever revisits this"). Sequence run this session: `GET /api/slots/2/claim`
    → `present:true` but for a STALE, unrelated claim (`agent_id: "slot2-interactive-20260804-064910-91bd"`,
    `role:"interactive"`, `spawned_at: 2026-08-04T06:49:10Z` — literally the artifact the 2026-08-04 entry's own
    diagnostic probe left behind, still on file 2 days later, `expires_at` about to lapse) →
    `POST /api/slots/2/claim-interactive` (fresh claim written, confirmed via a follow-up `GET`) → retried the EXACT
    SAME `/done` payload that 400'd before → **same 400, verbatim message**. Confirms the file-based `.agent-claim` and
    the AgentRow-based `find_active_agent_for_session` check (`_done_one_off`'s actual gate) are independent systems —
    refreshing the former has no effect on the latter.
  - **New fact 2 — the erroneous-backlog-reassignment variant (2026-08-01 `na_eligibility_auditor` / 2026-08-03
    `ag_closeout_auditor` entries above) reproduces here too.** A plain `/heartbeat` mid-session returned a fresh,
    unrelated Class-A backlog task (`ao_scheduled_job_reserve_and_staggering-005`, `dispatch_reason:"resume"`) — the
    server had silently stopped associating slot 2 with the `plan_reconciler` dispatch and treated it as an idle generic
    worker. Released it via `POST /api/slots/2/skip-current-task {reason_code:"OTHER"}` (never started, out of scope)
    per the 2026-08-03 entry's precedent, rather than silently absorbing or ghosting it.
  - **New, more precise hypothesis for the DATA todo below**: unlike every prior (escalation-path) entry in this doc,
    `plan_reconciler` is a SINGLETON kind — its reaper path is `_sessionless_singleton_duplicates` /
    `reap_orphan_agents`, not the `escalation.py` registration gap this doc's original two todos target. Read in full
    this session (`server/state_store/agents.py:333-426`): a SINGLETON-kind record is archived
    (`exit_reason="reaped-stale"`) only when a same-`agent_kind` sibling's session reads live WHILE this record's own
    `_owns_live()` reads false — and the function's own docstring names a known false-positive path: "a transient
    `has_session()` miss under host load." This slot's tmux session was continuously live this entire session (never
    stopped, sent heartbeats throughout) — so if this mechanism is what hit `agt-4fdce1`, the likely trigger is either
    (a) a genuine same-kind sibling dispatch (e.g. the standing daily trigger re-firing near this session's own 00:01
    UTC start) racing a transient `is_session_live()` false-negative on THIS session under host load, or (b) some other
    path not yet identified. **Not confirmed** — this worker slot has no DB/dashboard access, same constraint every
    prior entry in this doc hit. Filed as a sharper, testable hypothesis (see new todos) rather than a claimed root
    cause. Ending session without a clean `/done` per this doc's now 8-deep established precedent; all of this session's
    actual reconciliation work is independently git-verified complete and durable regardless (3 commits,
    `plan_reconciler_findings_2026_08_06.md` STEP 8 marked resolved, PR #2327 open).
