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
status: resolved
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
  "slot-5, backend_engineer, 2026-08-09 — both todos closed via live /api/activity + /api/state investigation on the
  planning VM itself; confirmed distinct root cause (fleet_worker_cap headroom throttling, not the dfef970 batch case)
  and live-recheck evidence it is still routinely missing the SLA today; fix decision handed off to
  autospawn_fleet_cap_headroom_throttling_routine_sla_miss_2026_08_09.md"
locked_by:
context_scope:
  [agent-orchestrator/server/autospawn.py, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md]
---

# AutoSpawn refill SLA fix — data points 1/2 unexplained + live recheck outstanding

> **🟢 ARCHIVED (2026-08-09).** Both todos done: data points 1/2 root-caused to `_apply_fleet_cap()` headroom throttling
> (distinct from `dfef970`'s within-tick batch fix); live-recheck confirms the SLA is still routinely missed today. Fix
> decision (capacity/tuning judgment call) handed off to
> `/plans/active/issues/autospawn_fleet_cap_headroom_throttling_routine_sla_miss_2026_08_09.md`.

## Background

`autospawn_refill_slower_than_60s_sla_two_slots_2026_08_08.md` (archived 2026-08-09) root-caused and fixed a 5-slot
simultaneous refill-SLA miss: both `AutoSpawnLoop._run_one_tick()`'s spawn path and `_resume_pass()`'s resume path drove
`_do_spawn()` serially per slot; `agent-orchestrator@dfef970` replaced both with `_do_spawns_concurrently()`
(`ThreadPoolExecutor` bounded by `fleet_worker_cap()`). That fix is confirmed to explain data point 3 (the 5-slot batch,
13:18:42-13:19:03Z, only 1/5 within-SLA). Two caveats from that investigation were stated in prose only and never became
tracked todos — migrating them here per the archival ritual's "every follow-up is a canonical todo, never prose" rule.

## Todos

- [x] ✅ [BACKEND] P3. Independently determine whether data points 1/2 (slot 11's lone 38-min gap at 2026-08-08 ~10:42,
      slot 10's lone 33-min gap at ~10:48) are explained by the same serialization root cause, or by a separate
      contributor (an account/quota-headroom gate, a scheduling-lock, a cooldown interaction) not addressed by
      `dfef970`. Done when: either a confirmed second root cause + fix, or documented evidence that no distinct root
      cause exists (e.g. the lone-slot spawn cost itself already approaches the SLA boundary under some other measured
      condition). Repo: agent-orchestrator. **Confirmed distinct root cause (code + live-data confirmed, not
      asserted)**: data points 1/2 were framed as "lone slot, not competing with siblings in the same tick" — that
      framing is WRONG once the full fleet activity feed is checked, not just the reporting slot's own history. In the
      ~50min window around the two incidents (2026-08-08 10:30-11:28Z), `activity` shows **24 `tmux_session_lost` events
      across ~14 distinct slots** (several arriving within seconds of each other — e.g. slots 4/9/10/12 all lost at
      10:48:25), and 14 `autospawn_succeeded` events trickled in one-by-one over that same 43-minute span (10:44:16 ->
      11:27:06), with slot 11 dead last. `dfef970`'s fix only parallelizes the `_do_spawn()` calls THE TICK ALREADY
      CHOSE to run within one tick (`_do_spawns_concurrently`) — it does NOT change how MANY slots a tick chooses. That
      count (`spawn_budget`) is capped by `_apply_fleet_cap()`: `fleet_headroom = effective_cap - active_workers`, where
      `effective_cap` comes from `fleet_worker_cap()` / `ORCHESTRATOR_FLEET_WORKER_CAP`
      (`agent-orchestrator/.env.local.bak-20260808-030522` shows the cap was **15** on 2026-08-08; live today it's
      **25**, `agent-orchestrator/.env.local`). With the fleet routinely running 20-25 concurrently-active workers
      (confirmed live via `/api/state`, 23/25 active at check time today) against that cap, per-tick headroom is
      frequently 0-2 — so when a wave of slots die faster than OTHER active slots vacate headroom, the backlog drains
      slot-by-slot at the rate active workers naturally finish tasks, NOT at dfef970's now-parallel per-tick spawn
      speed. This is a real, distinct, currently-live mechanism (`_apply_fleet_cap`, `server/autospawn.py`) — but it is
      DESIGNED capacity throttling (a deliberate VM-load safety cap), not a code defect dfef970 could have fixed or was
      scoped to fix. See todo 2 below for live confirmation this is still happening today, well past `dfef970`.
- [x] ✅ [BACKEND] P3. Live-recheck slots 10/11/13/16/21's current respawn health against `/api/state` (or
      `check-ao-backlog-status.sh`) now that `dfef970` has been live for some time — confirm no slot is still stuck
      unspawned, and record whether any post-fix refill has exceeded the ~60s SLA. Done when: a dated observation is
      logged with the actual per-slot respawn latency for at least one real kill-and-refill event post-fix. **2026-08-09
      live observation** (via live `/api/activity` on this same orchestrator host,
      `slot=<N>&types=tmux_session_lost,autospawn_succeeded` over 05:00Z-21:47Z today): all 5 slots are alive/healthy
      right now (10/11/16/21 `status=working` with fresh `last_ping`; slot 13 `status=killed` since 21:44:09Z — a fresh
      `worker_one_task_per_session_reset`, not stuck, respawn confirmed still pending 10.5+ min after
      `tmux_session_lost` at filing time — a live SIXTH data point, in the same order of magnitude as the others below).
      **The ~60s SLA is routinely missed, confirming todo 1's root cause is live and ongoing, not historical**: slot 10,
      18 measured kill->respawn cycles today, gaps 0.6-35.3 min (median ~13 min); slot 11, 14 measured cycles, gaps
      1.1-43.0 min (median ~17 min); slot 16 gaps 1.2-83 min (13:44:41Z ->15:07:51Z); slot 21 one measured gap of
      **3h11min** (05:15:49Z tmux_session_lost -> 08:27:01Z autospawn_succeeded). None of this is the 2026-08-08
      batch-context-wedge scenario `dfef970` targeted — these are today's routine, spread-out, one-slot-at-a-time
      deaths, still missing the documented SLA by 1-2 orders of magnitude because fleet headroom is thin (23/25 active
      workers measured live today). Filed a properly-scoped operator-judgment follow-up:
      `/plans/active/issues/autospawn_fleet_cap_headroom_throttling_routine_sla_miss_2026_08_09.md` (raising the cap
      further vs. redesigning spawn-budget allocation is a capacity/tuning decision, not a bounded code fix — out of
      this P3 investigation's scope).

## Progress Log

- **2026-08-09 (slot 25, infra)**: Filed while archiving the parent doc + its finalize plan — these two caveats were
  stated only in the parent doc's Progress Log prose ("caveat carried forward"), never as tracked `- [ ]` todos,
  violating `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` §2. No code change in this task
  (archival-only); this doc exists solely to keep the deferral from evaporating with the archived plan.
- **2026-08-09 (slot 5, backend_engineer)**: Both todos closed via live investigation against the running orchestrator's
  own `/api/activity` + `/api/state` (this slot IS the `planning` VM, so `localhost:8765` is directly reachable — no SSM
  needed). Root cause for data points 1/2: NOT a second independent mechanism (account/quota gate, cooldown) as
  hypothesized — the "lone slot" framing itself was the gap; both incidents sat inside a much larger overlapping wave of
  14 distinct slots needing respawn in the same ~50min window, throttled by `_apply_fleet_cap()`'s
  `fleet_headroom = effective_cap - active_workers`, which `dfef970` does not touch (it only parallelizes the spawns a
  tick already selected, not how many it selects). Live-recheck confirms this mechanism is STILL live today (2026-08-09)
  and causing routine multi-minute-to-hours SLA misses across all 5 named slots, worst case slot 21 at 3h11min. No code
  change shipped in THIS doc (both todos are investigation-scoped per their own "done when" — root cause + evidence, not
  necessarily a fix); the fix decision (operator capacity/tuning call) is handed off to the new follow-up issue doc.
  `status` left `open` in this commit (per RULES.md § 2 — never combine the checkbox flip with the archival `git mv` in
  one commit, so the M3 flip-detection check sees a plain edit at the still-active path); flipping `status: resolved` +
  archive banner + `git mv` follow in the immediate next commit, same session.
