---
doc_type: issue
title:
  "AO direct-instruction dispatch redelivers a stale message citing an already-resolved blocked-question/escalation —
  confirmed 4x same-day (2026-08-08) across both review and worker roles"
summary: >-
  A "Direct instruction from main" message citing escalation `BLK-091671d7` / DP-VM-001 (`agt-fe0635`) — asking the
  recipient to investigate/relaunch for the `expected-universe-v2-sports` halt-safety false-page — kept getting
  delivered to fresh agent sessions on 2026-08-08 well AFTER the underlying issue was fully root-caused and fixed
  (`deployment-service@27fd5779`, shipped 2026-08-07, confirmed ancestor of `origin/live-defi-rollout`). Four
  independent sessions hit the identical stale instruction the same day: (1) a na-eligibility-audit pass, (2) review
  agent slot 1 instance A, (3) a worker on `config_key_contract_drift-002`, (4) review agent slot 1 again (message id
  4072, 09:39Z). Every session independently verified the fix was already shipped and did NOT redo the work or ship
  duplicate code — no live harm — but this burns real agent-turns fleet-wide re-verifying the same closed item, and a
  less careful session could re-implement already-shipped work or waste a dispatch slot. `BLK-091671d7` itself is NOT
  present in the live `/api/state` `blocked_queue` (checked 2026-08-08T09:40Z) — confirming this is not an
  unanswered-blocked-question redelivery, but something in the direct-instruction dispatch/queueing path itself
  (per-slot inbox, backlog-generation artifact, or similar) that isn't being cleared once the underlying escalation
  resolves. Root cause not yet investigated — flagged by review (not in review's scope to chase); this doc exists so the
  pattern is tracked as a general AO-infrastructure gap, not just noted in one issue's Progress Log.

  Note: an earlier attempt this same session to file this exact tracking doc was dispatched directly to slot 11 (`POST
  /api/slots/11/message`, ack'd `{"slot_id":11,"ok":true}`) but never landed on origin — slot 11 had already moved on to
  a different backlog task (`sports_taxonomy_p1_capture_and_contracts-009`, assigned 09:31:10Z, after the 09:2xZ
  dispatch) by the time it was checked, so the direct instruction was silently dropped/superseded rather than actioned.
  Filing directly from main this time rather than risking a second lost dispatch — itself a small data-point for the
  same underlying dispatch-doesn't-survive-a-busy-slot class of gap discussed in
  `/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`'s Progress Log.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, dedup, direct-instruction, blocked-queue, false-positive, alert-fatigue]
related: [/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md]
created: 2026-08-08
author: agt-30eb02 (main)
priority: P3
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
locked_by:
resolved_by:
source: >-
  Review agent (slot 1) flagged the 4th same-day recurrence in chat (message id 4072, 2026-08-08T09:39:23Z). Main
  independently confirmed `BLK-091671d7` is absent from the live `blocked_queue` and that a prior same-session attempt
  to file this doc via slot 11 was itself lost to a busy-slot dispatch race, then filed this doc directly.
---

# AO direct-instruction dispatch redelivers a stale message after its underlying blocked-question/escalation resolves

## What happens

A "Direct instruction from main" message citing a specific blocked-question/escalation id can remain queued somewhere in
the dispatch path and get delivered to a worker or review-agent session AFTER the underlying blocked-question/escalation
has already been resolved and its fix already shipped and verified live. This causes idle/fresh sessions to spend cycles
re-verifying already-fulfilled work instead of it being a no-op.

## Evidence (2026-08-08)

The DP-VM-001 false-page fix (`deployment-service@27fd5779`, shipped 2026-08-07 by slot-2, confirmed ancestor of
`origin/live-defi-rollout`) was independently re-litigated **four** separate times on 2026-08-08 by sessions that each
received the same stale direct-instruction text citing escalation `BLK-091671d7` / `agt-fe0635`:

1. A na-eligibility-audit pass.
2. Review agent (slot 1), instance A.
3. A worker session on `config_key_contract_drift-002`.
4. Review agent (slot 1) again — message id 4072, 2026-08-08T09:39:23Z, explicitly noting this was its own 2nd hit and
   the 4th fleet-wide.

Full technical detail of the underlying (already-fixed) issue is in
`/plans/active/issues/dp_vm_001_expected_universe_halt_safety_false_page_2026_08_07.md`'s Progress Log (entries
"na-eligibility-audit 2026-08-08" and "review agent (slot 1) 2026-08-08").

`BLK-091671d7` was checked against the live `/api/state` `blocked_queue` on 2026-08-08T09:40Z and is **not present** —
ruling out a simple "unanswered blocked-question redelivers on every poll" explanation. Whatever is re-queueing this
instruction is not visible in the blocked-queue itself.

## Root cause (not yet investigated)

Unverified hypothesis (review's, echoed by main): a direct-instruction record tied to the original escalation never got
marked resolved/cleared once the escalation was answered, so it re-dispatches on a later respawn/heartbeat cycle for
whichever slot picks it up next — independent of role (has hit both `review` and generic `worker` roles) and independent
of which physical slot (4 different sessions, not the same slot repeating).

## Blast radius

Low-severity so far — every hit was caught by careful independent verification before any wasted code work — but not
guaranteed to stay that way: a less careful session could re-implement already-shipped work, or waste a dispatch slot
re-investigating a closed issue. Four confirmed hits in one day on a single stale instruction is a real, measurable
rate, not a one-off. Also relevant: this doc's own first same-session filing attempt (via a direct slot-11 dispatch) was
itself silently dropped when the target slot picked up other backlog work first — suggesting direct-instruction delivery
in general doesn't reliably survive a slot that's mid-task, which is adjacent to (but distinct from) the
stale-redelivery problem this doc is primarily about.

## Todo

- [ ] [INFRA] P3. Root-cause why the `BLK-091671d7` / DP-VM-001 direct instruction survived at least 4 respawn/dispatch
      cycles after its underlying escalation was resolved on 2026-08-07. Check the agent-orchestrator server's
      direct-instruction delivery/queueing code path for whether it dedups/invalidates against blocked-question
      `answered_at` or escalation-resolution state. Fix so a direct instruction citing an already-resolved
      blocked_id/escalation_id is not redelivered on the next respawn/heartbeat. Done-when: reproduce the stale-delivery
      condition (or confirm root cause via code read), ship a fix or confirm no code fix is needed (e.g. if it's a
      one-time backlog-generation artifact, not a recurring code bug) — either way close this loop with evidence, not
      speculation.
- [ ] [INFRA] P3. Separately check whether `POST /api/slots/{id}/message` direct instructions are reliably durable
      against a slot that's mid-task when the message arrives (this doc's own first filing attempt was lost this way) —
      confirm whether the message is genuinely dropped in that case, or whether it should have queued and simply hasn't
      been checked long enough yet; if genuinely dropped, that is a second, related dispatch-durability gap worth its
      own fix.
