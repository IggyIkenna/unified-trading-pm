---
doc_type: issue
title:
  "cicd escalation's AgentRow was marked status=archived/exit_reason=lifecycle-complete ~40 minutes before the session
  ever attempted /done — a third, distinct trigger for the 'one_shot_complete: no active agent owns its session' bug
  family, neither of the two already-shipped fixes (agent-orchestrator@a01aeae, @babba14/@d59f1af) covers this case"
summary: >-
  Reproduced live on slot 3, 2026-07-29, escalation agt-a14109 (repo=unified-trading-pm, wall_type=plan_health,
  PR#1780). Followed cicd.md's boot sequence exactly: STEP 0 heartbeat returned `new_task: null` with `dispatch_reason:
  "heartbeat — cicd still running (task-less one-off, held working)"` — i.e. the already-fixed "first heartbeat steals
  the slot into Class-A dispatch" mechanism
  (/plans/archive/issues/cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md,
  agent-orchestrator@babba14/@d59f1af) demonstrably did NOT fire this time — confirms that fix is still working. Never
  called `/api/slots/3/boot` at all (cicd.md's STEP 2 explicitly says there is no separate task-fetch/boot call for this
  one-shot role), so the OTHER precedent's mechanism
  (/plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_recurrence_2026_07_29.md, `boot_slot()`'s
  top-of-function resume-check short-circuiting the `PLAN_HEALTH_FAMILY_ROLES` lazy-AgentRow gate) cannot apply either —
  that gate lives entirely inside `boot_slot()`, a function this session's flow never invokes, and `cicd` is not even a
  member of `PLAN_HEALTH_FAMILY_ROLES` (`{plan_health, plan_reconciler, docs_reconciler, ag_closeout_auditor,
  na_eligibility_auditor}` — verified by reading `server/plan_health.py:86-101` this session). Did the full assigned
  mandate correctly (reproduced 3 hard failures on the plan_health gate, root-caused each, fixed 2 independently before
  discovering a concurrent duplicate escalation, agt-ebe4e0/slot-12, had already pushed an equivalent fix; verified
  green on a fresh pull, no redundant commit made). `POST /api/slots/3/done {"task_id": "", "sha": "", "evidence":
  "...", "one_shot_complete": true}` (and a retry with `task_id: "agt-a14109"`) both 400d with the exact familiar
  message: `"one_shot_complete on slot 3 but no active agent owns its session 'orch-slot-3' — a Class-A worker must
  /done with a task_id."` `GET /api/agents/agt-a14109` (only resolvable via the direct-by-id lookup, NOT via `GET
  /api/agents` or `?include_finished=true`, which both omit it) shows: `status: "archived"`, `online: false`,
  `registered_at: "2026-07-29T19:49:32Z"`, `last_ping: "2026-07-29T19:49:32Z"` (identical to registered_at — no ping
  ever recorded against THIS row, despite this session sending 2 `/progress` calls during its lifetime), `finished_at:
  "2026-07-29T20:13:32Z"`, `exit_reason: "lifecycle-complete"`. This session never called `/done` before ~20:53Z (the
  timestamp of its own final `/progress` call, `activity` event id 235343) — so something OTHER than this session's own
  action marked the row finished/archived at 20:13:32Z, roughly 24 minutes into the session and ~40 minutes before the
  session's actual `/done` attempts. The `activity` feed additionally shows a `watchdog_heartbeat_resumed` event for
  this exact `claude_session_id` at 20:29:16Z (`resume_n: 1`) — 16 minutes AFTER the row's `finished_at` — so the
  liveness watchdog's resume/re-nudge mechanism fired on a session whose AgentRow the system already believed was
  lifecycle-complete, which is itself an inconsistent state regardless of what caused the original archival.
status: open
nature: issue
asset_group: [ao] # retagged 2026-07-31 (corpus-sweep meta fold-in) -- was [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [orchestrator, slot-lifecycle, one-shot, cicd, escalation, agentrow, watchdog, self-heal, recurrence]
related:
  [
    /plans/archive/issues/cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md,
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_2026_07_26.md,
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_recurrence_2026_07_29.md,
    /plans/active/issues/one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks_2026_07_25.md,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-07-29"
author: unknown
parent_epic: agent_operating_framework_master
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
assigned_vm: NA
execution_scope: local-only
sequential: true
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
source: "slot 3, cicd escalation agt-a14109 (wall_type=plan_health, repo=unified-trading-pm#1780), 2026-07-29"
context_scope:
  [
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/state_store/agents.py,
    agent-orchestrator/server/tmux_pruner.py,
    /plans/archive/issues/ag_closeout_auditor_one_shot_complete_no_agentrow_recurrence_2026_07_29.md,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
    /plans/archive/issues/cicd_escalation_heartbeat_steals_slot_before_done_no_agentrow_2026_07_28.md,
  ]
---

# `one_shot_complete` — AgentRow archived ~40 min before the session ever called `/done`, a third distinct trigger

## What I found

Same terminal symptom as both precedent docs (`"one_shot_complete ... no active agent owns its session"`), but neither
already-shipped fix applies here — confirmed by directly ruling each one out against this session's own observed
behavior rather than assuming either fix regressed:

1. **Not the heartbeat-steals-slot mechanism** (`agent-orchestrator@babba14`/`@d59f1af`, fixed 2026-07-28). That bug
   was: a freshly `claim_slot_for_typed_agent`'d slot's mandated STEP-0 heartbeat took `heartbeat_slot`'s idle branch
   and `assign_task_to_slot`'d an unrelated Class-A task, clobbering `spawn_base_role`. This session's own STEP-0
   heartbeat response was
   `{"new_task": null, "dispatch_reason": "heartbeat — cicd still running (task-less one-off, held working)", ...}` —
   the fixed idle-branch guard correctly recognized this slot as a typed one-shot occupant and did NOT dispatch a
   foreign task. That fix is confirmed still working.
2. **Not the boot-vs-Class-A-task binding mechanism** (`agent-orchestrator@bb13e93`, fixed 2026-07-29, for
   `ag_closeout_auditor`). That fix lives entirely inside `boot_slot()` (`server/routes/slots_worker.py`), gated on
   `req.slot_role in PLAN_HEALTH_FAMILY_ROLES`. This session never called `/api/slots/3/boot` at all — per cicd.md's own
   STEP 2 ("your task is already fully specified by the session variables above ... there is no separate task-fetch call
   for this one-shot role"), the cicd role's documented contract skips `/boot` entirely. Separately, `cicd` is not even
   in `PLAN_HEALTH_FAMILY_ROLES` (verified by reading `server/plan_health.py:86-101` this session:
   `{plan_health, plan_reconciler, docs_reconciler, ag_closeout_auditor, na_eligibility_auditor}` — `cicd` absent), so
   even a hypothetical direct `/boot` call with `slot_role: "cicd"` would not have reached that gate.

## The actual observed sequence

- `19:49:32Z` — `POST /api/slots/3/heartbeat` (STEP 0). `AgentRow` `registered_at`/`last_ping` both stamp this exact
  timestamp (confirms the row existed from spawn, via `escalation.py`'s `dispatch()` → `_register_agent(...)`, per the
  code-path already verified by the 2026-07-28 precedent doc).
- (unlogged, ~20-30 min) — Read RULES.md/cicd.md, reproduced the plan_health wall (3 hard failures, not the 1 named in
  the escalation's `CONTEXT`), root-caused + fixed each (reference-path existence, AG-closeout linkage, archive
  candidates), including reading all 14 archive-candidate docs in full to separate genuine completions from mechanical
  false-positives.
- `20:13:32Z` — `AgentRow.finished_at` stamps this timestamp, `status` → `archived`, `exit_reason` →
  `"lifecycle-complete"`. **This session never called `/done` at this point** — still deep in the archival-ritual edits
  (banners, `git mv`, referrer fixes) with no `/done` attempt logged anywhere in this transcript before ~20:53Z.
  Something OTHER than this session's own action archived the row.
- `20:29:16Z` — `activity` event `watchdog_heartbeat_resumed`, `slot_id: 3`, `claude_session_id` matching this exact
  session, `resume_n: 1`. **16 minutes AFTER** the row was already `finished_at`/archived — i.e. the liveness watchdog's
  resume mechanism fired against a session the system had already marked lifecycle-complete 16 minutes earlier, which is
  internally inconsistent regardless of root cause (a resume implies "still alive, still working"; an
  already-`finished_at` `AgentRow` implies the opposite).
- `~20:35Z` (approx, after the archival edits, branch-drift pull, and stash reconciliation) — first `/done` attempt:
  400, `"no active agent owns its session"`. Retried with an explicit `task_id: "agt-a14109"` (in case the endpoint
  wanted a non-empty value per its own error text) — identical 400.
- `20:53:51Z` — final `/progress` heartbeat (`activity` id 235343) reporting the wall already green via a converged
  concurrent fix; this doc authored immediately after as the closing move, per both precedents' established pattern.

A fourth, independently-filed sibling landed on `live-defi-rollout` the same day from a completely different one-shot
role: `/plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md` (escalation agt-79063c, slot
10, `wall_type=data_pipeline_failure`) hit the identical 400 and traced the registration code path as far as a worker
without live DB access can, but couldn't determine the AgentRow's actual state at `/done` time. This doc's direct
`GET /api/agents/<id>` read (available because the AgentRow, once archived, is still fetchable by exact ID — see below)
supplies exactly the state-at-/done-time evidence that doc was missing.

## Why this is a third, distinct trigger (not a regression of either shipped fix)

Both `GET /api/agents` (default) and `GET /api/agents?include_finished=true` **omit** `agt-a14109` entirely — only the
direct `GET /api/agents/agt-a14109` by-id lookup returns it. That is itself worth a callout: whatever the
`?include_finished=true` query is meant to surface, it did not surface this archived one-shot row, which suggests either
a filter-window issue (perhaps age-bounded) or that "archived" is a distinct status bucket the `include_finished` flag
doesn't cover — not chased further here (bounded one-shot scope), but worth the fix's own triage step to check before
assuming the two are equivalent.

The `finished_at`/`exit_reason: "lifecycle-complete"` shape is the SAME shape a legitimate, successful `/done` call
produces (per cicd.md's own documented contract: "The backend archives your AgentRow lifecycle-complete, frees your
slot..."). That strongly suggests _some_ code path called the equivalent of the done/archive transition against this
AgentRow — just not this session's own worker process, and roughly 40 minutes before this worker ever tried to. A
`reap_orphan_agents`-style pass (referenced in the 2026-07-29 `ag_closeout_auditor` precedent doc as a plausible actor
for a related symptom) marking a still-actively-working one-shot session "lifecycle-complete" under some staleness
heuristic — rather than under its own genuine `/done` call — would explain the data cleanly, but was not confirmed
against the actual reaper code this session (bounded scope; flagging for the fix's own investigation rather than digging
further, matching both precedents' own stated boundary).

## Why it matters

Same accounting-gap consequence both precedents already named, now with a third confirmed trigger family: a `cicd`
one-shot worker can do its entire assigned job correctly (this session: 3 hard-failure gate reproduced, root-caused,
independently converged with another agent's fix, verified green) and still have no way to formally signal `/done`,
because _something else_ already closed its AgentRow out from under it while it was still working — not because of
anything the worker itself did wrong. Every future `cicd`/`plan_health`-family one-shot escalation is exposed to this
same silent-mid-session-archival pattern regardless of which of the two already-fixed triggers it avoids.

## Recommended decision

- [x] [BACKEND] P2. ✅ — agent-orchestrator@81f54a8 CONFIRMED: `reap_orphan_agents` (`server/state_store/agents.py`) is
      NOT the only heuristic actor — `TmuxPruner` (`server/tmux_pruner.py:392`) independently stamps the SAME
      `exit_reason: "lifecycle-complete"` string on a `has_session()`-heuristic dead-session verdict, with NO retry/
      debounce around the underlying `tmux has-session` subprocess call (`tmux_spawn.has_session`, 2s timeout, no
      liveness confirmation beyond a single exit-code check) — a transient false-negative on a busy shared host (this
      workspace's own CLAUDE.md documents concurrent-QG shared-host contention) would archive a still-working one_shot
      row exactly like this incident, and the row would be indistinguishable from a genuine `/done` afterward. Could not
      forensically pin down, from code alone, which of the two daemons' four heuristic branches (reaper's
      dead-tmux-session / session-reused / stale-no-session, or the pruner's dead-session-in-ACT-phase) fired for
      `agt-a14109` specifically — that would need the 2026-07-29 DB/log state, which is no longer live. Shipped the
      stated OR-fix instead (agent-orchestrator@81f54a8): every heuristic-driven archival of a terminal-lifecycle
      (`one_shot`/`scheduled`) `AgentRow`, across BOTH `reap_orphan_agents`' three branches AND `TmuxPruner`'s
      dead-session branch, now stamps `exit_reason: "reaped-stale"` instead of `"lifecycle-complete"` — that string is
      now reserved exclusively for the two genuine `/done`/`one_shot_complete`-triggered archival call sites
      (`server/routes/slots_worker.py:1193` and `:1640`). Updated the reap docstring + `docs/SLOTS_AGENTS_AND_FLEET.md`
      to document the distinction, and updated the affected assertions in `tests/test_reap_orphan_agents.py` +
      `tests/test_tmux_pruner_agent_reap.py` (the genuine-`/done` tests in `tests/test_done_one_off.py` and
      `tests/test_task_lifecycle_done_gate_resume.py` were left asserting `"lifecycle-complete"`, unchanged — they
      exercise the real API call, not a heuristic). 114 tests green across the four affected test files. (repo:
      agent-orchestrator)
- [x] ✅ [BACKEND] P3. Investigate why `GET /api/agents?include_finished=true` omitted `agt-a14109` (only the direct
      by-id `GET /api/agents/agt-a14109` surfaced it) — confirm whether this is an intentional time-window/status-enum
      gap or a real bug in that endpoint's filter, since the two precedent docs' own diagnostic recipe
      (`GET     /api/agents`) would have silently reported "zero active/stale AgentRow rows" here too, same
      false-negative shape the 2026-07-26 doc already flagged once. (repo: agent-orchestrator) — **Investigated via full
      call-chain code read (`server/routes/agents.py::list_agents` → `server/state_store/agents.py::list_agents`); NOT
      reproducible as a filter/status-enum bug in the current code.** With `include_finished=true` and no explicit
      `status`, the SQL applies NO status filter at all
      (`elif not include_finished: stmt = stmt.where(...notin_(archived,     finished))` — the exclusion is skipped
      entirely once `include_finished=True`), so an archived row is included by construction; confirmed the dashboard's
      own caller (`dashboard/src/App.tsx` → `api.ts::listAgents`) passes `{ include_finished: true }` with no `limit`,
      matching the no-narrowing case. One real (but narrower) issue found along the way, worth flagging even though it
      doesn't explain a full omission: the query's `ORDER BY role,     agent_id` is NOT recency-ordered, so any caller
      that DOES pass a `limit` for "recent past runs" (a reasonable reading of the endpoint's own docstring) gets an
      alphabetically-arbitrary slice, not the most-recent rows — a genuinely recent archived row could be silently
      absent from a limited page while older-but-alphabetically-earlier rows fill it. Not fixed here (no evidence the
      reporting session's own query used a `limit` — fixing an ordering bug that may not be the actual cause would be a
      speculative change to fleet-critical query code); noting for whoever next touches `list_agents`' ordering. The
      specific `agt-a14109` omission is most plausibly a transient artifact of that investigation session (unknown exact
      query mechanics, no live DB access to reproduce) rather than a standing code defect — closing as
      investigated/non-reproducible rather than leaving open indefinitely.
- [ ] [BACKEND] P3. Once the reap-vs-done distinction above lands, consider whether `one_shot_complete` should
      special-case an already-`exit_reason: "lifecycle-complete"` (or the new `"reaped-stale"`) row for a session whose
      OWN `claude_session_id`/`tmux_session` matches the caller — i.e. treat "the row is already archived AND it is
      genuinely mine" as an idempotent success rather than a 400, so a worker that finishes real, correct,
      independently-verified work is never blocked from a clean sign-off purely by an unrelated prior archival race.
      (repo: agent-orchestrator) — **Declined for this pass (2026-07-30, corpus-reduction sweep): read
      `_done_one_off`/`find_active_agent_for_session` (`server/routes/slots_worker.py:1153-1220`,
      `server/state_store/agents.py:203-221`) and confirmed the fix is real but NOT safely bounded without deeper
      verification.** `tmux_session` (the only identity `find_active_agent_for_session` currently matches on) is a
      per-SLOT name (`orch-slot-N`) reused across every worker that ever occupies that slot — a naive "archived row with
      this tmux_session exists → treat as idempotent success" would also match a DIFFERENT, later worker's late `/done`
      call against a slot that has since been reused, unless the match is ALSO gated on `claude_session_id` (which
      `DoneRequest` does not currently carry — would need a request-schema change too). Getting this right needs tracing
      the full slot-reuse lifecycle + a live-fleet check for whether `claude_session_id` is reliably available at
      `/done` time, which is exactly the kind of `/done`-endpoint (fleet-wide, every worker, every completion) surgery
      this corpus-reduction pass is scoped to decline rather than rush — left open for a dedicated backend-engineer
      pass.

## Current session status (informational, not part of the fix)

This escalation's assigned mandate (fix the `unified-trading-pm` `plan_health` wall, PR#1780) is fully complete and
independently verified: 3 hard failures reproduced (reference-path existence 903/901, AG-closeout linkage 1-then-2
orphans/0, archive-candidates 14/11), each root-caused and fixed, but a concurrent duplicate escalation
(`agt-ebe4e0`/slot-12, `unified-trading-pm@8dab56cbd`) independently pushed an equivalent fix first; hit branch drift on
this session's own commit attempt, pulled, found the gate already green on the fresh `origin/live-defi-rollout` HEAD
(`4599cd653`), and made no redundant/conflicting commit. `git status` /
`git rev-list --count HEAD ^origin/live-defi-rollout` = 0 on `unified-trading-pm` (clean, on `live-defi-rollout`, fully
caught up). No open `repo-blockers` needed fast-pathing (this was a `plan_health` wall, not `ldr_qg_failure`). Unable to
formally signal `/done` due to the gap documented above; ending this turn with this issue doc instead of retrying a call
whose immediate cause (a vanished `AgentRow`) is already confirmed and outside this worker's control, per both
precedents' own closing-move precedent.

## Recurrence corroboration (slot 13, escalation agt-068e39, same day)

A fifth instance of the identical symptom, same day: escalation `agt-068e39` (`wall_type=plan_health`, `repo`
`unified-trading-pm`, `PR#1788`). This session's `CONTEXT` named exactly 1 hard failure (`AG-closeout linkage`, 1 orphan
vs baseline 0). On investigation the wall was **already resolved before this session started** —
`origin/live-defi-rollout` had advanced past a `[plan-health-autofix]` auto-fix commit (`6816ec1d6`) and PR#1788 was
already `MERGED` by the time this worker ran a fresh `git pull --ff-only` + re-ran
`bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci`: 0 hard failures, AG-closeout linkage 0/0. No code change was
needed or made (working tree left clean, `git rev-list --count HEAD ^origin/live-defi-rollout` = 0).
`POST /api/slots/13/done {"task_id": "", ..., "one_shot_complete": true}` and a retry with `task_id: "agt-068e39"` both
400d with the byte-identical message this doc already documents:
`"one_shot_complete on slot 13 but no active agent owns its session 'orch-slot-13' — a Class-A worker must /done with a task_id."`
Same shape as the `agt-a14109` case above (task genuinely complete/no-op-verified, `/done` unreachable) — adds no new
diagnostic surface, just another data point that this is a recurring, not one-off, failure mode. Not retrying `/done`
further per the precedent set above; ending this turn here.

## Recurrence corroboration (slot 11, escalation agt-0773cd, same day)

A sixth instance, same day: escalation `agt-0773cd` (`wall_type=plan_health`, `repo` `unified-trading-pm`, `PR#1789`,
already `MERGED` by the time this worker checked). This session's `CONTEXT` named exactly 1 hard failure
(`AG-closeout linkage`, 1 orphan vs baseline 0) — already independently fixed by a concurrent commit before this worker
pulled, verified identical. The full `run_hygiene_sweep.sh --ci` also surfaced a second, unnamed hard failure
(`check_archive_candidates.sh` false-flagging 3 `depends_on`/`gate_on_depends`-gated satellite-batch plans as
done-but-unarchived — archiving each is literally its own gated finalize-plan's own todo) — root-caused and fixed
(`unified-trading-pm@2f5a9d966`, baseline ratcheted 10→7), independently verified (not a duplicate of the concurrent
commit above, which only bumped the baseline to 10 rather than fixing the false-positive).
`git rev-list --count HEAD ^origin/live-defi-rollout` = 0 on the pushed HEAD.
`POST /api/slots/11/done {"task_id": "", ..., "one_shot_complete": true}` and a retry with `task_id: "agt-0773cd"` both
400d with the byte-identical message this doc already documents:
`"one_shot_complete on slot 11 but no active agent owns its session 'orch-slot-11' — a Class-A worker must /done with a task_id."`
Not retrying `/done` further per the precedent set above; ending this turn here.

## Recurrence corroboration (slot 4, escalation agt-0cadd0, 2026-08-01)

A seventh instance, different `wall_type` this time (`main_ci_red` — every prior recurrence in this doc was
`plan_health`): escalation `agt-0cadd0` (`repo=features-service`, `#0`), assigned mandate fully complete and
independently verified (main's HEAD confirmed a literal ancestor of `live-defi-rollout` — no code fix existed or was
needed; the wall is the tracked fleet-wide QG capacity crisis, corroborated in
`/plans/active/issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`). This session's own investigation
spanned ~5h (multiple bounded `ScheduleWakeup` cycles polling a genuinely slow CI queue — not idle drift), which is
plausibly exactly the kind of long-elapsed, session-spanning gap the `TmuxPruner`/`reap_orphan_agents` heuristics (P2
fix `agent-orchestrator@81f54a8` above) are prone to false-negative on. `POST /api/slots/4/done` with both `task_id: ""`
and a retry with `task_id: "agt-0cadd0"` 400d with the byte-identical message. Tried two recovery steps not previously
logged in this doc, neither helped: (1) re-sent `/heartbeat` first, hoping a fresh ping would reactivate the row the way
`touch_main_agent_heartbeat`/`reactivate_review_agent` do for their roles — it succeeded (200, slot went
`status=working`) but `/done` still 400d identically, confirming heartbeat only touches `SlotRow`, not the archived
`AgentRow`, for this role; (2) the successful heartbeat's own response carried an unrelated `new_task` (a
`defi_satellite_ao_dispatch_batch2` backlog item) — the dispatcher treating the slot as idle-and-claimable despite the
escalation still being mid-session, consistent with the AgentRow already reading `archived` from its side. Skipped that
erroneous dispatch via `/skip-current-task` before the (still-400) final `/done` retry, so it doesn't strand a task. Not
retrying further per the precedent set above; ending this turn here. Adds one new data point for the open P3 todo above
(idempotent-success-on-already-archived-own-row): this occurrence's own `tmux_session`/escalation pairing would have
been a clean, safe match for that proposed fix (single occupant, no slot-reuse ambiguity in this session's own
timeline), i.e. a real instance where that declined-for-now fix would have let a fully-correct wall resolution sign off
cleanly instead of ending on an issue-doc corroboration.

## Progress Log

- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-02** (autonomous, tranche `ao`): KEEP-NA, valid — first marker on this doc. Sole open
  todo (`[BACKEND] P3`, idempotent-success on an already-archived own row) was explicitly DECLINED for a dedicated
  backend pass on 2026-07-30, with the reason recorded inline: `tmux_session` is a per-SLOT name reused across
  occupants, so a safe match also needs `claude_session_id`, which `DoneRequest` does not currently carry — i.e. the fix
  needs a request-schema change plus full slot-reuse-lifecycle tracing on the fleet-wide `/done` endpoint. Doc is
  `sequential: true` behind the shipped P2, and the 2026-08-01 slot-4 recurrence (7th instance, new `main_ci_red`
  wall_type) confirms the finding is live, not moot.
- **na-eligibility-audit 2026-08-03** (ao tranche): KEEP-NA, valid — re-affirmed. Sole open todo remains explicitly
  DECLINED-for-now backend design work (a `/done`-endpoint identity-matching change touching every worker's completion
  path), unchanged since the 2026-08-02 marker. Only file change since is a mechanical `context_scope` path fix — no
  content drift.
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) — already source-anchored (3 AO server modules)
  - the 3 precedent/sibling issue docs the doc's own "why this is a third, distinct trigger" section rules out against;
    left unchanged.
- **context-scout 2026-08-03**: reviewed, still accurate — refreshed marker (6 entries).
- **2026-08-04 (main agt-1756f6) — NEW live recurrence (≥8th instance), restart-correlated, via blocked-queue
  BLK-f0a24efb**: slot 10, one-shot `ag_closeout_auditor` dispatch `agt-8e2ecb` (tranche=infra) finished + shipped its
  real deliverable (`unified-trading-pm@2a3c10ec9` + `@5241ed222` — main independently verified BOTH are ancestors of
  `origin/live-defi-rollout`; audit report `plans/active/issues/ag_closeout_audit_infra_parked_2026_08_04.md` present,
  13.7 KB). `POST /api/slots/10/done {one_shot_complete: true}` 400s with the exact family error
  `one_shot_complete on slot 10 but no active agent owns its session 'orch-slot-10'` — tried empty and `agt-8e2ecb`
  task_id, same result; heartbeat succeeds and even offers backlog tasks (correctly declined, one-shot). **The worker
  explicitly correlated it with a mid-session orchestrator restart** ("connection refused for a few minutes, then came
  back — same error before and after") — i.e. the AgentRow for `agt-8e2ecb` was lost/archived across the restart, so
  `find_active_agent_for_session('orch-slot-10')` returns None and `_done_one_off`
  (`server/routes/slots_worker.py:1228`) deterministically 400s with no fallback. This is precisely the still-open
  `[BACKEND] P3` idempotent-success-on- already-archived-own-row fix above; retrying (the worker's option B) is futile
  because the 400 is deterministic. Main directed the worker to STOP retrying and stand down (deliverable is durably on
  LDR — nothing is lost) and flagged the stuck `agt-8e2ecb`/slot-10 dispatch for backend/operator server-side
  reconciliation. **Reinforces urgency**: the restart-triggered variant is now common enough (≥8 instances since
  2026-07-26) that a mid-session backend restart — which happens routinely — strands whatever one-shot worker was
  mid-flight; the declined P3 request-schema fix (`claude_session_id` on `DoneRequest` → treat "archived AND genuinely
  mine" as idempotent success) is the durable cure and is worth re-weighing against its declared cost given the
  recurrence rate.

- **na-eligibility-audit 2026-08-04** (autonomous, tranche `ao`): KEEP-NA, valid — re-affirmed. The sole open todo
  remains the same explicitly-declined-for-now `/done`-endpoint identity-matching change (needs a `DoneRequest` schema
  addition plus full slot-reuse-lifecycle tracing, touching every worker's completion path fleet-wide) — squarely
  live-dispatch-critical-path machinery per the standing corpus ruling this tranche applies consistently (see
  `boot_composer_misroutes...`'s marker today). The new 8th-recurrence entry above (restart-correlated) raises the fix's
  urgency but does not change its eligibility — still a genuine design/risk call, not a bounded worker-executable todo.
  Cross-validated: today's sibling `/ag-closeout-audit ao` batch6 run independently declined this doc into its
  "too-large/unscoped-design" bucket.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **2026-08-06 (cicd escalation agt-ca03f6, slot 9, wall ldr_qg_failure / repo-blocker RB-fbeef249) — another
  restart-correlated recurrence of the identical terminal symptom**: `POST /api/slots/9/done {one_shot_complete: true}`
  (and a retry with `task_id: "agt-ca03f6"`) both 400
  `"one_shot_complete on slot 9 but no active agent owns its session 'orch-slot-9' — a Class-A worker must /done with a task_id."`
  Correlated with a mid-session backend outage (server unreachable ~30s mid-session; identical 400 before and after
  recovery — same restart-variant shape as the 2026-08-04 `agt-8e2ecb`/slot-10 entry; a fresh `/done` retry after the
  server returned still 400s deterministically). **Substantive deliverable COMPLETE regardless**: declared blocker cause
  (finalize-plan-coverage QG red) already green on origin via `6c5927a06`; fixed `check_terminal_status_archived` 4->0
  (3 docs archived, 1 re-opened for its open P3 follow-up); landed + independently verified
  `unified-trading-pm@fc207c245` is an ancestor of `origin/live-defi-rollout`; repo-blocker RB-fbeef249 resolved via
  `reporter` (`waiters_notified=1`); authoring slot 4 pinged; all slot repos clean on `live-defi-rollout`. Nothing lost
  — deliverable durably on LDR. Standing down per the documented closing pattern (final heartbeat + this recurrence
  note); the still-open `[BACKEND] P3` identity-matching fix remains the durable cure.
- **2026-08-06 (scheduled `ag_closeout_auditor` agt-4ef1c1, slot 9, tranche=defi) — another restart-correlated
  recurrence, same slot as the entry directly above, later the same day**: the Phase-1 Workflow this session launched
  was reported `stopped` mid-run by a `task-notification` ("No completion record was found... it may have been
  stopped... or running when the previous Claude Code process exited"), consistent with a mid-session backend/harness
  restart — resumed cleanly via `Workflow({scriptPath, resumeFromRunId})` with all prior agent results cached, no work
  lost. A subsequent `/heartbeat` call (context_used_pct=25, well before the restart-correlated one) returned a foreign
  `new_task` (`ci_satellite_ao_dispatch_batch4-002`) unprompted — the same "dispatcher treats the slot as idle/
  claimable" symptom the 2026-08-01 slot-4 entry above first flagged — correctly declined (this is a one-shot role, per
  RULES.md never enters the backlog-drain loop).
  `POST /api/slots/9/done {"task_id": "", ..., "one_shot_complete": true}` and a retry with `task_id: "agt-4ef1c1"` both
  400d with the byte-identical message:
  `"one_shot_complete on slot 9 but no active agent owns its session 'orch-slot-9' — a Class-A worker must /done with a task_id."`
  `GET /api/agents` (no `include_finished` — the default listing) shows only 2 rows fleet-wide (`main`, `review`/slot-1)
  — zero AgentRow for `agt-4ef1c1`/`orch-slot-9` at all, the same shape prior entries confirmed via the by-id lookup.
  **Substantive deliverable COMPLETE regardless**: full `/ag-closeout-audit defi` Phase 0-3 run (107 AG-primary docs
  classified via a 107-agent Workflow fan-out, 0 errors; drafted `defi_satellite_ao_dispatch_batch10_2026_08_06.md` +
  `_finalize.md`, `status: draft`, 9 conflict-cleared AO-eligible todos); shipped + independently verified
  `unified-trading-pm@1176ef806` is an ancestor of `origin/live-defi-rollout` (`git merge-base --is-ancestor` confirmed
  true); working tree clean on `live-defi-rollout`. Nothing lost — deliverable durably on LDR. Standing down per the
  documented closing pattern (message `main` + this recurrence note, no further `/done` retries); the still-open
  `[BACKEND] P3` identity-matching fix remains the durable cure.
- **context-scout 2026-08-07**: re-scouted; context_scope re-verified (6 entries), unchanged -- the two new 2026-08-06
  recurrence entries (restart-correlated, slots 9) reaffirm rather than change the finding; the 3 AO server modules + 3
  precedent issue docs already cover it.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — re-verified; sole open item
  (`[BACKEND] P3`, idempotent-success-on-already-archived-own-row) remains the explicitly-declined-for-now
  `/done`-endpoint identity-matching change (needs a `DoneRequest` schema addition + full slot-reuse-lifecycle tracing,
  touching every worker's completion path fleet-wide) — unchanged since the 2026-08-06 marker, still `sequential: true`
  behind no unresolved prerequisite.
- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — checked against the round7-10 precedent set; none
  apply (this is fleet-wide `/done`-endpoint surgery, explicitly declined for rushed scoping, not a defaulted judgment
  call). Corroborated same-day: `/ag-closeout-audit ao` batch12 independently lists this doc under too-large-or-risky
  (1).
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open todo remains fleet-wide `/done`-endpoint identity-matching surgery (a `DoneRequest` schema
  addition + full slot-reuse-lifecycle tracing touching every worker's completion path), explicitly declined for rushed
  scoping on 2026-07-30 and re-affirmed as still-genuinely-risky across every subsequent pass, most recently round11's
  corroboration against `/ag-closeout-audit ao` batch12's independent same-day too-large-or-risky classification.
