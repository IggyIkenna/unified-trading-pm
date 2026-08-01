---
doc_type: issue
title:
  Transient plan_health_dispatch spawns (na_eligibility_auditor and others) can target a tmux session already running a
  persistent-role agent, killing it — slot 1's review agent hit a 6-respawn / ~30min outage
summary: >-
  Slot 1 runs the persistent `review` role (`lifecycle: persistent` per `agents/review.md`), which should stay up
  continuously polling for messages and spot-checking worker output. Between `2026-08-01T12:29:20Z` and
  `2026-08-01T12:51:38Z`, slot 1's tmux session (`orch-slot-1`) was killed and respawned 6 times, each session living
  only 2-8 minutes — meaning no sustained review work happened for roughly half an hour. At least one kill has a direct,
  tightly-correlated cause in the live activity feed: `plan_health_dispatch_initiated` events (`mode: "na_eligibility"`)
  explicitly targeting `slot=1` at `12:48:12-14Z`, followed by a `tmux_session_lost` kill for `orch-slot-1` only 18-20
  seconds later at `12:48:32Z`. A `stale_spawn_base_role_cleared` event at `12:55:28Z` (`stale_role:
  "na_eligibility_auditor"`, `tmux_session: "orch-slot-1"`, `reason: "no_agentrow"`) — firing right before the review
  agent's next (successful, stable) boot — confirms slot 1 was left holding a stale `na_eligibility_auditor` role claim
  that a transient plan_health_dispatch spawn had planted there, on top of the persistent review agent's own claim to
  that same tmux session. The same `stale_spawn_base_role_cleared` pattern, with a different colliding role
  (`data_pipeline_failure`), also fired for slots 9, 5, and 4 in the same session window — this looks like a general
  dispatch-coordination gap (a transient/one-shot dispatch mechanism spawning onto a tmux session without checking
  whether a different, already-running role already owns it), not something specific to `na_eligibility_auditor` or to
  slot 1.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    spawn-dispatch,
    tmux-collision,
    persistent-slot,
    plan-health-dispatch,
    na-eligibility-auditor,
    review-role,
    reliability,
  ]
related:
  - /plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md
  - /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md
created: 2026-08-01
priority: P1
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
assigned_role: infra
estimate_class: refactor
locked_by:
resolved_by:
depends_on: []
gate_on_depends: false
supersedes:
superseded_by:
source: >-
  Filed by the review agent (slot 1, agt-fed62c) at main's direct request (chat id 3122, 2026-08-01T13:06:55Z) after
  reporting the pattern as a finding — main confirmed it explains fleet-wide recycle churn tracked separately this
  session and asked the reporting agent to file this doc since it holds the precise event-evidence chain.
---

# Persistent-slot tmux session hijacked by a transient plan_health_dispatch spawn

## What's confirmed (from `GET /api/activity`, event IDs cited)

Timeline, all UTC, 2026-08-01, slot 1 / tmux session `orch-slot-1`:

- `id=260586` `12:29:20.145Z` — `tmux_session_lost` (scope=slot, new_status=killed) for slot 1.
- `id=260590` `12:29:33.552Z` — `agentkeeper_review_succeeded` (role=review) — AgentKeeper respawns the review role.
- `id=260604` `12:30:27.104Z` — `slot_boot` for slot 1.
- `id=260738` `12:37:45.129Z` — `tmux_session_lost` (killed) for slot 1. Session lived ~7 min.
- (respawn cycle repeats: `agentkeeper_review_succeeded` → `slot_boot` → …)
- `id=260789` `12:43:53.043Z` — `tmux_session_lost` (killed) for slot 1. Session lived ~4 min.
- `id=260892`-`id=260894` `12:48:12.637Z`-`12:48:14.178Z` — **three `plan_health_dispatch_initiated` events with
  `mode: "na_eligibility"` and `slot=1` explicitly in the event record** (`dispatch_id`s `agt-40b18e`, `agt-bb3601`,
  `agt-a54931`).
- `id=260898` `12:48:32.856Z` — `tmux_session_lost` (killed) for slot 1, **18-20 seconds after** the na_eligibility
  dispatch events above explicitly targeted `slot=1`. This is the one kill in the sequence with a tight, direct temporal
  correlation to a named colliding dispatch.
- `id=260913` `12:49:20.118Z` — `agentkeeper_review_failed`,
  `error: "benign: session already exists (raced by another spawn path)"` — the review AgentKeeper's own respawn attempt
  observes a race against another spawn path (consistent with a competing dispatch mechanism touching the same tmux
  session).
- `id=260937` `12:51:38.040Z` — `tmux_session_lost` (killed) for slot 1. Session lived ~2 min.
- `id=260969` `12:55:27.263Z` — `agentkeeper_review_succeeded` (role=review, account sub-d-odum1default) — this is the
  session that became the current, stable occupant.
- `id=260970` `12:55:28.625Z` — **`stale_spawn_base_role_cleared`**:
  `{"stale_role": "na_eligibility_auditor", "tmux_session": "orch-slot-1", "reason": "no_agentrow"}` — fires 1 second
  after the review agent re-registers, right before its `slot_boot` at `id=260976` `12:56:13.665Z`. This is the server
  cleaning up a leftover `na_eligibility_auditor` role claim on `orch-slot-1` that had no backing `AgentRow` — direct
  confirmation that a `na_eligibility_auditor` dispatch had claimed this tmux session at some point in the preceding
  cycle.
- No further `tmux_session_lost` for slot 1 since `12:51:38Z` — stable for 20+ minutes as of this doc's filing (~13:10Z)
  and still stable as of the Progress Log entry below.

**Not every kill in the 12:29-12:51 sequence has an equally direct correlated `plan_health_dispatch_initiated` (or
similar) event visible in the activity feed** — only the `12:48:32Z` kill does. The earlier kills (`12:29:20Z`,
`12:37:45Z`, `12:43:53Z`) may be attributable to the SEPARATE, already-tracked `boot_read_unconfirmed` 428-loop
(`/plans/active/issues/review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md` — a session stuck failing `/boot`
repeatedly may read as unproductive/stuck to a watchdog and get reaped), to an uninstrumented variant of this same
collision class, or to both compounding. Do not assume all 6 kills share one root cause — the `12:48:32Z` one is the
only one this doc claims a confirmed direct link for.

**The pattern is not na_eligibility_auditor-specific or slot-1-specific.** The same `stale_spawn_base_role_cleared`
shape, with a _different_ colliding role, also fired in the identical session window:

- `id=260787` `12:43:44.176Z` — slot 9, `stale_role: "data_pipeline_failure"`.
- `id=260953` `12:52:54.298Z` — slot 5, `stale_role: "data_pipeline_failure"`.
- `id=260989` `12:57:58.335Z` — slot 4, `stale_role: "data_pipeline_failure"`.

Four `stale_spawn_base_role_cleared` events, two distinct colliding roles (`na_eligibility_auditor`,
`data_pipeline_failure`), four different target slots, all within one ~30-minute window — this reads as a systemic
dispatch-coordination gap rather than a one-off.

## Root cause (NOT yet confirmed at the code level — flagging for the assigned worker)

This doc documents the **observable behavior** via the activity log; it does not cite an exact file:line root cause the
way a code-level incident doc normally would, because the reporting agent (review role) does not edit/read
agent-orchestrator server internals as part of its normal remit. The working hypothesis, for the assigned worker to
confirm or refute against the actual dispatch code (`server/` in `agent-orchestrator`, likely near wherever
`plan_health_dispatch_initiated` / `stale_spawn_base_role_cleared` / `spawn_base_role` are emitted — see the related
boot-loop doc's citation of `server/prompts.py` and `server/routes/slots_worker.py` as adjacent territory):

- A transient/one-shot dispatch mechanism (`plan_health_dispatch`, in at least `na_eligibility` and — inferred from the
  `data_pipeline_failure` stale-role clears — possibly other modes/escalation paths too) selects a target tmux session
  (e.g. `orch-slot-1`) and spawns onto it WITHOUT checking whether a different, already-running **persistent** role
  (e.g. `review`) currently owns that session.
- The spawn either kills the persistent session outright or otherwise disrupts it, leaving a `spawn_base_role` /
  role-claim marker (`na_eligibility_auditor`, `data_pipeline_failure`) on that tmux session with no backing `AgentRow`
  — which a later cleanup pass (`stale_spawn_base_role_cleared`) has to sweep up after the fact.
- Net effect: the persistent role (review, and per main agent's own tracking this session, _possibly_ also `main` /
  `monitor` if they are similarly addressable as dispatch targets) suffers repeated involuntary respawns until either
  the transient dispatch mechanism stops targeting that session, or the cleanup fires and the persistent role finally
  gets an uncontested boot.

## Why it matters

- **Direct fleet-visibility gap**: for ~30 minutes, the ONLY review-role agent in the fleet was not stably running,
  meaning no slot_done spot-checks, no discipline-warning monitoring, no git-health watch happened during that window
  from this role. Any worker-actionable defect shipped in that window would have gone unreviewed until the session
  stabilized.
- **Not confined to slot 1 / review**: the same `stale_spawn_base_role_cleared` shape hit 3 other slots with a different
  colliding role in the same window — this is a fleet-wide reliability gap for any tmux session a transient dispatch
  mechanism might target, not a one-slot quirk.
- **Compounds with the separately-tracked 428 boot-loop bug**
  (`review_role_boot_read_unconfirmed_stuck_loop_2026_08_01.md`) — a session already struggling to clear the boot
  read-confirmation gate is even more likely to look "available" to a collision-blind dispatcher, and each
  collision-forced respawn is a fresh chance to re-hit that gate too.
- **Named at-risk by main agent this same session**: main (agt-cb1851) independently flagged that `main` and `monitor` —
  the other persistent, single-instance roles in this fleet — may be exposed to the identical hijack path, which would
  be a materially worse blast radius than a transient review-role outage.

## Recommended decision

- [ ] [BACKEND] P1. Locate the dispatch/spawn code path(s) that emit `plan_health_dispatch_initiated` (at minimum the
      `na_eligibility` mode; audit every mode: `na_eligibility`, `ag_closeout`, and whatever emits the
      `data_pipeline_failure` stale-role-clear pattern) and confirm whether they select a target tmux session/slot
      without checking for an existing, live, persistent-role claim on it. If confirmed, make the selection
      collision-aware: skip a tmux session that already has a live `AgentRow` for a persistent role (`review`, `main`,
      `monitor`), and pick a different / dedicated session for the transient dispatch instead. (repo:
      agent-orchestrator)
- [ ] [BACKEND] P1. Audit whether `main` and `monitor` (the fleet's other persistent, single-instance roles) are
      reachable as targets by the same transient-dispatch selection logic, per main agent's own concern in chat
      (2026-08-01T13:06:55Z). If they are, this is materially higher severity than the review-role case documented here
      — file a follow-up or fold into the fix above. (repo: agent-orchestrator)
- [ ] [BACKEND] P2. Make `stale_spawn_base_role_cleared` (or a sibling event) fire a distinct, higher-visibility signal
      when the role it's clearing belongs to a KNOWN transient-dispatch mode colliding with a KNOWN persistent role —
      today it reads as routine cleanup; it should be diagnosable as "a collision just happened" without needing to
      cross-reference `plan_health_dispatch_initiated` timestamps by hand, the way this doc had to.
- [ ] [BACKEND] P3. Add a regression test: dispatching a transient role (e.g. `na_eligibility_auditor`) while a
      persistent role (e.g. `review`) already holds a live session on the same target must either be refused/rerouted,
      or must not produce a `tmux_session_lost` kill for the persistent occupant. (repo: agent-orchestrator)

## Codex SSOTs

`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`.
