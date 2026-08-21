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
    /plans/archive/issues/dp_escalation_worker_dispatch_no_open_issue_check_2026_07_29.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
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
last_updated: 2026-07-29
context_scope: [/plans/archive/2026_08/ao_satellite_ao_dispatch_batch5_2026_08_03.md, /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md, agent-orchestrator/server/escalation.py, agent-orchestrator/server/routes/slots_worker.py, agent-orchestrator/server/state_store/agents.py]
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

- [x] ✅ [DATA] P2. Query the live `AgentRow` for `agent_id='agt-79063c'` (or the `escalation_dispatched` activity log
      entry with that `escalation_id`) to determine whether the registration ever happened, and if so what changed its
      status before this worker's `/done` call. **Done 2026-08-08** (data_engineering, slot 11) — ran the diagnostic for
      all 5 named agent_ids directly against the live `agent-orchestrator/data/state/state.db`, read-only; see Progress
      Log entry "data_engineering (slot 11) 2026-08-08T22:24Z — DIAGNOSTIC" for the full per-id table. Answer: none has
      a current `AgentRow` (all predate the table's rolling retention window), all 5 registrations are confirmed
      indirectly via `escalation_dispatched`/`plan_health_dispatched`, and all 5 were transitioned away via the SAME
      event — `tmux_session_lost` (scope=agent, `archived_lifecycle_complete: true`) from `tmux_pruner.py`'s
      dead-tmux-session sweep calling `archive_agent(exit_reason="reaped-stale")` — across 3 distinct proximate triggers
      (slot-reuse collision ×2, context-saturation wedge-kill ×1, plain silent loss ×2).
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

- **na-eligibility-audit 2026-08-06**: KEEP-NA, CONFLICT-PARKED — RECLASSIFY held — diagnostic half verbatim-claimed by
  ao_satellite_ao_dispatch_batch5's open [DATA] P2 todo (same 5 agent ids, same done-when); code half gated on shared
  /done-handler ground also claimed by batch6 Deferred. Parked as BLOCKED-OPERATOR-DECISION — batch5 owns the
  diagnostic, batch6 gates the code fix.
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — both of this doc's own todos are now claimed
  elsewhere (batch5's diagnostic todo, batch6's gated code-fix), so swapped the archived precedent-bug doc and the
  general AO architecture SSOT for the 2 batch docs that actually own the work now; kept the 3 code files the original
  trace named (escalation.py, slots_worker.py, agents.py) since the root-cause investigation still lives here.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, CONFLICT-PARKED, re-affirmed — verified both
  `ao_satellite_ao_dispatch_batch5_2026_08_03.md` and `batch6_2026_08_04.md` still exist, still `status: draft`/
  `assigned_vm: NA`, and still cite this doc's diagnostic ([DATA] P2) and gated code-fix ([CODE] P2) items by name — no
  change to the parked status since the 2026-08-06 marker.
- **2026-08-08 (ag_closeout_auditor, slot 8, dispatch agt-6bc9c4, tranche=`cefi`):** ninth corroboration, and resolves
  the 2026-08-04 report's open caveat with a **confirmed negative**: applying the `claim-interactive` workaround does
  NOT fix the `one_shot_complete` `/done` path. Hit the identical 400 (`task_id: "agt-6bc9c4"`, twice, plus once with
  `task_id: ""` and once with an extra `session_id` field — 4 attempts total, same message every time) after shipping
  this session's real work (`unified-trading-pm@ae02e533a`, independently `git merge-base --is-ancestor`-verified
  against `origin/live-defi-rollout`). A `/heartbeat` call in between returned `{"ok": true}` with a **fresh Class-A
  backlog dispatch** (`sports_manifest_...-001`, unrelated role) — same "server re-registered this slot as a plain
  backlog worker mid-session" variant as the 2026-08-01/08-03 reports. Released it via
  `POST /api/slots/8/skip-current-task` (confirmed via the response body, `task_skipped` field matched), then — per the
  2026-08-04 report's own suggested next step, the one data point every prior report left untested — called
  `GET /api/slots/8/claim` (`{"present": false}`), then
  `POST /api/slots/8/claim-interactive {tmux_session: "orch-slot-8", operator: "planning"}` (succeeded,
  `{"ok": true, "role": "interactive", ...}`, confirmed present via a follow-up `GET`), then retried the SAME
  `one_shot_complete: true` `/done` call immediately after — **still the identical 400, no change**. This confirms the
  2026-08-04 report's fix (which unstuck normal Class-A backlog dispatch) is NOT the same code path
  `_done_one_off`/`find_active_agent_for_session` reads — `.agent-claim` and the one-shot `AgentRow` lookup are
  genuinely two independent registration systems, exactly the open question that report flagged as unconfirmed. Ending
  session without a clean `/done` per the established precedent (all 8 prior reports); this session's actual assigned
  work (the `/ag-closeout-audit cefi` run — 68-doc corpus sweep, 2 orthogonality retags,
  `cefi_satellite_ao_dispatch_batch10_2026_08_08.md` + finalize drafted) is independently git-verified complete
  regardless, logged via `/progress` instead.
- **2026-08-08 (ag_closeout_auditor, slot 12, `agt-9e8893`, tranche=ao, session `orch-slot-12`):** tenth corroboration —
  independently hit the identical 400 and ran the SAME `claim-interactive`-then-retry probe as slot 8's entry directly
  above (unaware of each other, landed within minutes of each other on the same doc — see this commit's own conflict
  resolution), with the identical result: `{"present": false}` → `claim-interactive` succeeds → immediate `/done` retry
  still 400s, unchanged. A second, fully independent confirmation of that entry's finding — `.agent-claim` and the
  `one_shot_complete` AgentRow check are genuinely separate mechanisms. This session's own work (`/ag-closeout-audit ao`
  — 66-doc corpus sweep, 2 mistags retagged, `ao_satellite_ao_dispatch_batch8_2026_08_08.md` + finalize drafted) is
  independently git-verified complete as `9895da4c5`, ancestor of `origin/live-defi-rollout`, logged via `/progress`
  instead of a clean `/done`, matching the established precedent.
- **na-eligibility-audit 2026-08-08** (ao tranche): KEEP-NA, CONFLICT-PARKED, re-affirmed — re-verified both
  `ao_satellite_ao_dispatch_batch5_2026_08_03.md` and `batch6_2026_08_04.md` still exist, still `status: draft`,
  `assigned_vm: NA`, and still cite this doc's diagnostic ([DATA] P2) and gated code-fix ([CODE] P2) items by name. Only
  in scope this run because 3 more corroboration entries landed since the 08-07 marker — none change either todo's own
  content or the parked status. Not re-litigated.

- **data_engineering (slot 11) 2026-08-08T22:24Z — DIAGNOSTIC (`ao_satellite_ao_dispatch_batch5` [DATA] P2 todo,
  read-only, no code change)**: Ran the requested query directly against the LIVE orchestrator DB
  (`agent-orchestrator/data/state/state.db`, opened `mode=ro` — NOT the empty, stale root-clone artifact at
  `agent-orchestrator/state.db`, a 0-byte file unrelated to the running server) for all 5 named agent_ids.

  **(a) AgentRow exists now?** No — `SELECT * FROM agents WHERE agent_id=...` returned zero rows for all 5. The `agents`
  table itself appears to carry a rolling retention window independent of this bug (179 rows resident, oldest
  `registered_at`=2026-08-01 12:00:42, vs. 589 lifetime `agent_registered` activity_log events since 2026-06-27) — did
  not locate the exact prune code path via grep of `server/**/*.py`, so the retention MECHANISM is unconfirmed, but the
  row-count/date pattern is consistent with routine pruning rather than anything specific to these 5. **All 5 predate
  the current retention window**, so "ever existed" had to be answered from `activity_log` instead (unpruned back to
  2026-06-27).

  **(a, continued) Did an AgentRow ever exist?** Yes for all 5, confirmed indirectly — each has an
  `escalation_dispatched` (`agt-79063c`/`agt-0cd704`/`agt-765e33`/`agt-8fa8d1`) or `plan_health_dispatched`
  (`agt-8e95ca`) activity_log row, meaning `escalation.py`'s / plan_health's success-branch registration code path was
  reached. Note a code-level gap this surfaced: `escalation.py`'s one-shot `register_agent()` call (line ~746) never
  itself logs an `agent_registered` activity event — the ONLY `"agent_registered"` log site in the whole server is
  `server/routes/agents.py:764`, the PERSISTENT-agent `/register` path, a structurally different code path. So "the
  registration succeeded" is only ever inferable indirectly (via `escalation_dispatched`/ `plan_health_dispatched`),
  never directly observable in `activity_log` for one-shot agents.

  **(b) Current status/tmux_session**: N/A for all 5 (no row exists to report a status on).

  **(c) The activity_log event that transitioned each away from active/stale, before its `/done` call**: **all 5** have
  a `tmux_session_lost` event (scope=agent) with `archived_lifecycle_complete: true`, i.e. `tmux_pruner.py`'s
  dead-tmux-session sweep called `archive_agent(agent_id, exit_reason="reaped-stale")` on each. Confirmed `health.py`'s
  silence-based `agent_stale`/`agent_offline` dimmers explicitly SKIP `lifecycle in ("one_shot", "scheduled")` agents
  (health.py:350-351, by design — "their terminal transition is the reaper's dead-tmux-session archival"), so
  `tmux_session_lost` is the ONLY possible transition path for this agent class, confirmed live:

  | agent_id     | slot             | `tmux_session_lost` ts (UTC) | proximate pattern in the surrounding activity window                                                                                                                                                                                                                                                                                                                                                            |
  | ------------ | ---------------- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `agt-79063c` | 10               | 2026-07-29 21:00:21          | **Slot-reuse collision**: a `slot_compacted` at 20:52:46 was followed by 2 `worker_kicked` liveness pokes, then the SAME slot's `/done`+`slot_done_verified` fired for an unrelated Class-A task (`capability_wizard_gap_discovery-020`) at 21:00:01 — 20s before the agent's `tmux_session_lost`. The physical tmux pane was reused as a plain backlog worker before this escalation's own `/done` could land. |
  | `agt-0cd704` | 9                | 2026-07-29 21:20:30          | Plain silent loss — 5× `worker_kicked` over ~10min, ending in `slot_dispatch_unacked`, then `tmux_session_lost` with no competing task completion visible in the window.                                                                                                                                                                                                                                        |
  | `agt-765e33` | 4 (moved from 6) | 2026-07-29 22:19:59          | Plain silent loss — `slot_blocked`/`blocked_partial_answer` (mid a `/blocked` exchange) then `tmux_session_lost` ~1min later, no competing task.                                                                                                                                                                                                                                                                |
  | `agt-8fa8d1` | 2                | 2026-07-31 16:00:51          | **Context-saturation wedge-kill**: `worker_kick_failed` → `slot_wedged_killed_for_resume` (a DIFFERENT task, `deployment_api_qg_size_gate_debt-007`) → `tmux_session_lost` + `context_saturated_session_lost_task_requeued`, all within the same second. A distinct 3rd mechanism from the other 4.                                                                                                             |
  | `agt-8e95ca` | 2                | 2026-08-02 12:25:58          | **Slot-reuse collision** (same shape as `agt-79063c`): `/done`+`slot_done_verified` for an unrelated Class-A task (`tarball_stale_window_cefi_live_capture_correctness_risk-005`) fired at 12:25:54, 4s before this agent's `tmux_session_lost`, then a fresh `escalation_dispatched` right after.                                                                                                              |

  **Net**: 3 distinct proximate mechanisms across 5 corroborations, all converging on the same terminal event
  (`tmux_session_lost` → `archive_agent(exit_reason="reaped-stale")`), all of which is invisible to a one-shot worker's
  own session (it has no DB access) and race-prone against that same worker's still-in-flight `/done` call. This is a
  diagnostic only, per this todo's own scope — not attempting the [CODE] P2 fix (gated per this doc +
  `ao_satellite_ao_dispatch_batch6_2026_08_04.md`'s Deferred section). Query commands + full raw output available on
  request; not pasted here to keep this entry scannable. Source query tool: `sqlite3 "file:<path>?mode=ro"` against
  `agent-orchestrator/data/state/state.db`, read-only throughout, no writes to live server state.

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, CONFLICT-PARKED, re-affirmed — verified
  both `ao_satellite_ao_dispatch_batch5_2026_08_03.md` and `batch6_2026_08_04.md`: batch5 is now
  `status: active`/`assigned_vm: planning` (its own `[DATA] P2` diagnostic todo for this doc, cited by name, is already
  `[x]` done — see the 2026-08-08 diagnostic entry above). Batch6 is now fully `status: active` with all 10 of its own
  todos `[x]` done — but batch6's Deferred § "Conditionally gated" list still names this doc's remaining `[CODE] P2`
  item (the actual root-cause fix, gated on the diagnostic) as NOT one of the 10 items batch6 drafted; it stayed
  deferred there, unclaimed by any dispatched todo. The code fix itself remains genuinely gated: it touches shared
  `/done`-handler ground (`_done_one_off`/`find_active_agent_for_session`), a fleet-wide dispatch-critical-path change,
  and the diagnostic surfaced 3 distinct proximate mechanisms (slot-reuse collision, plain silent loss,
  context-saturation wedge-kill) converging on one terminal event — the actual fix approach (widen the AgentRow status
  filter vs. block the transition vs. something else) is still an open design call, not reduced to a single mechanical
  change. Staying parked.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **na-eligibility-audit 2026-08-21 (ao tranche batch 2/3)**: KEEP-NA, valid — sole remaining item ([CODE] P2, fix the one-shot `/done` AgentRow gap) remains genuinely gated per the 2026-08-10 CONFLICT-PARKED verdict: the diagnostic surfaced 3 distinct proximate mechanisms and the actual fix approach (widen the status filter vs. block the transition vs. something else) is still an open design call `ao_satellite_ao_dispatch_batch6_2026_08_04.md` explicitly declined to claim.
