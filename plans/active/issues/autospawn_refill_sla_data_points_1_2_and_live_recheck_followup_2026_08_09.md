---
doc_type: issue
title:
  "AutoSpawn refill SLA fix (dfef970) — data points 1/2 not independently explained + production live-recheck
  outstanding"
summary: >-
  Follow-up captured while archiving autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md per the 6-step
  archival ritual's todos-not-prose rule: that doc's own root-cause todo carried two caveats stated only in prose, never
  converted to tracked todos. (1) The shipped fix (`_do_spawns_concurrently()`, agent-orchestrator@dfef970) explains
  data point 3 (5-slot simultaneous batch, only 1/5 within-SLA) but was NOT independently proven to explain data points
  1/2 (slot 11's lone 38-min gap, slot 10's lone 33-min gap) — each was a single slot, not competing with siblings in
  the same tick, so serialization alone doesn't obviously account for those; an account/quota-headroom gate or cooldown
  interaction remains a plausible independent contributor, not ruled out. (2) A live recheck of slots 10/11/13/16/21's
  current respawn status/health following the fix was never performed in that session.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, sla, worker-liveness, follow-up]
related:
  [
    /plans/archive/2026_08/issues/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md,
    /plans/archive/2026_08/autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08_finalize_2026_08_08.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
  ]
created: 2026-08-09
author: slot-25-infra
priority: P3
parent_epic: orchestrator_master
source:
  "slot-25, infra, 2026-08-09 — migrated from prose caveats in the parent doc per the todos-not-prose archival rule
  (plan-completion-and-archival-discipline.md §2), during the parent doc's archival"
execution_scope: orchestrator-agent
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
assigned_vm: planning
resolved_by:
locked_by:
context_scope:
  [agent-orchestrator/server/autospawn.py, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md]
---

# AutoSpawn refill SLA fix — data points 1/2 unexplained + live recheck outstanding

## Background

`autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md` (archived 2026-08-09) root-caused and fixed a 5-slot
simultaneous refill-SLA miss: both `AutoSpawnLoop._run_one_tick()`'s spawn path and `_resume_pass()`'s resume path drove
`_do_spawn()` serially per slot; `agent-orchestrator@dfef970` replaced both with `_do_spawns_concurrently()`
(`ThreadPoolExecutor` bounded by `fleet_worker_cap()`). That fix is confirmed to explain data point 3 (the 5-slot batch,
13:18:42-13:19:03Z, only 1/5 within-SLA). Two caveats from that investigation were stated in prose only and never became
tracked todos — migrating them here per the archival ritual's "every follow-up is a canonical todo, never prose" rule.

## Todos

- [ ] [BACKEND] P3. Independently determine whether data points 1/2 (slot 11's lone 38-min gap at 2026-08-08 ~10:42,
      slot 10's lone 33-min gap at ~10:48) are explained by the same serialization root cause, or by a separate
      contributor (an account/quota-headroom gate, a scheduling-lock, a cooldown interaction) not addressed by
      `dfef970`. Done when: either a confirmed second root cause + fix, or documented evidence that no distinct root
      cause exists (e.g. the lone-slot spawn cost itself already approaches the SLA boundary under some other measured
      condition). Repo: agent-orchestrator.
- [ ] [BACKEND] P3. Live-recheck slots 10/11/13/16/21's current respawn health against `/api/state` (or
      `check-ao-backlog-status.sh`) now that `dfef970` has been live for some time — confirm no slot is still stuck
      unspawned, and record whether any post-fix refill has exceeded the ~60s SLA. Done when: a dated observation is
      logged with the actual per-slot respawn latency for at least one real kill-and-refill event post-fix.

## Progress Log

- **2026-08-09 (slot 25, infra)**: Filed while archiving the parent doc + its finalize plan — these two caveats were
  stated only in the parent doc's Progress Log prose ("caveat carried forward"), never as tracked `- [ ]` todos,
  violating `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §2. No code change in this task
  (archival-only); this doc exists solely to keep the deferral from evaporating with the archived plan.
