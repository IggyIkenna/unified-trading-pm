---
doc_type: issue
title: mvp_backfill_defi_onchain_v10-002 dispatch-thrash — role-matched but craft-actionless task keeps re-dispatching
summary:
  Task `mvp_backfill_defi_onchain_v10-002` (the G2 "all 6 defi data_types honest-complete" gate) has been dispatched to
  `data_engineering` slots 20+ times across 2026-07-14 through 2026-07-16, each dispatch reaching the identical
  conclusion — gate far from met, root cause owned by a separate plan (`data_completion_defi_2026_07_15.md`'s
  expected-universe-v2 seed chain) plus idle `[INFRA]`-scoped backfill VMs — with zero `data_engineering`-craft action
  available. Unlike the already-fixed 2026-07-07 incident (role-mismatch + unbounded slot_skips), this task IS correctly
  role-matched; the thrash is a distinct gap — `skip-current-task` has no fleet-wide cooldown, so a task skipped by one
  slot is immediately re-offered to any other idle same-role slot within minutes, burning a full agent turn per dispatch
  for zero new information.
status: open
nature: notes
asset_group: [meta, defi]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, slot-skips, task-parking, fleet-efficiency, defi]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/data_completion_defi_2026_07_15.md,
    plans/archive/issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md,
  ]
created: 2026-07-16
last_updated: 2026-07-16
parent_epic: orchestrator_master
priority: P1
source: data_engineering slot-6, dispatched to mvp_backfill_defi_onchain_v10-002 within minutes of slot-15's decline
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
supersedes:
superseded_by:
depends_on:
assigned_role: backend_engineer
drift_direction: advance-code
---

> **NOTIFY-OPERATOR (fleet efficiency, not correctness).** Not data-loss or a wrong-result bug — a dispatch-efficiency
> defect burning real agent-hours re-deriving the same "not actionable yet" verdict on one task, repeatedly, in a tight
> loop.

## What I found

`mvp_backfill_defi_onchain_v10-002` ("Final defi MVP verification: all 6 data_types attempted_failed=0 AND
expected_unattempted=0") is `assigned_role: data_engineering`, `priority: 10` (P0), so it is the top-ranked queued task
for every idle `data_engineering` slot. Its own plan's Progress Log
(`plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md`) records at least 20 distinct dispatches to this exact
task-id since 2026-07-14, most recently:

- **2026-07-16T19:45-19:51Z, slot-2**: fresh `measure_honest_coverage.py --asset-group defi` run. Gate NOT met on any of
  the 6 data_types (`dex_pool_swaps` alone: 3.9M `expected_unattempted`). Root cause: the separately-owned
  `data_completion_defi_2026_07_15.md` 64.39M-row expected-universe-v2 seed chain (only 2018/2019 landed as of its last
  update) plus zero currently-running backfill VMs for 5 of the 6 data_types. No `data_engineering`-craft action
  available; declined via `/skip-current-task`.
- **2026-07-16T19:5xZ, slot-15**: re-dispatched to the SAME task within ~5-10 minutes of slot-2's check (via `/done` on
  an unrelated task). Confirmed nothing changed, declined identically, `/skip-current-task`.
- **2026-07-16T~20:0xZ, slot-6 (this dispatch)**: re-dispatched again within minutes of slot-15's decline
  (`already_in_progress: true`, `dispatch_reason: "resume"` on `/boot`). Attempted a cheap live-VM check (no expensive
  corpus scan) to look for anything new since slot-2's measurement — `gcloud` is unavailable in this session
  (`snap-confine` / `cap_dac_override` sandbox error, an environment defect, not evidence of anything changing). No new
  information. Same conclusion.

I read the orchestrator's skip-task code (`server/routes/slots_ops.py:589`, `server/models/slots.py:94`,
`server/dispatch.py`'s `_FILTERS`) to check for an anti-thrash mechanism: `skip-current-task` records a
`(slot_id, task_id)` row in `slot_skips` (TTL-bounded, `config.slot_skip_ttl_hours` — the fix from the 2026-07-07
incident) and releases the task back to the queue with `target_slot=None, affinity="none"`. The `SLOT`-scoped skip
filter only blocks the **skipping slot** from re-claiming that task; it does NOT block any **other** idle slot from
claiming it on its very next heartbeat (~60s cadence). `queued_at` is stamped on release but is used only for
age/tie-break reporting, not a dispatch-delay gate. So a P0 task with zero currently-actionable craft work gets handed
to a fresh idle slot every time one becomes free — which, given `data_engineering`'s idle-slot churn, has been happening
every 5-30 minutes for 2+ days.

This is a DIFFERENT defect from the already-closed 2026-07-07 incident
(`ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md`, all 5 prevention todos landed 2026-07-12/16): that one was
role-MISMATCH thrash (an `infra` task dispatched to a `data_engineering` slot) fixed by the craft filter + `slot_skips`
TTL. This task IS correctly role-matched — the craft filter doesn't help, because a data_engineering worker legitimately
picks it up, legitimately finds no data_engineering-scoped action, and legitimately declines. The gap is that nothing
tells the dispatcher "this specific task has no actionable work right now regardless of WHICH slot claims it."

## Why it matters

Each dispatch costs a full agent boot (~5-15 min wall-clock, real token spend) to re-derive an unchanged verdict. At the
observed cadence (3 dispatches in under an hour on 2026-07-16 alone, 20+ over 3 days), this is a material, ongoing
efficiency loss with zero corresponding progress — and it will keep recurring at the same P0 priority until either (a)
the separately-owned seed chain materially closes the gap (multi-week timeline per its own plan) or (b) someone parks
this specific task.

## Recommended decision

**Park `mvp_backfill_defi_onchain_v10-002`** per `unified-trading-pm/agents/RULES.md` § "Park a task": set
`priority: 999` + `priority_override: true` on its `backlog.yaml` entry, gated on a new prerequisite condition (e.g.
`defi_onchain_v10_universe_v2_seed_or_backfill_progressed`, created `false`) that `data_completion_defi_2026_07_15.md`'s
owning agent (or an `[INFRA]` VM-relaunch dispatch) flips `true` once it lands a chunk materially closing the
`dex_pool_swaps`/`dex_pool_state` gap (the two largest, ~6M combined `expected_unattempted`) — mirroring how
`mvp_backfill_defi_onchain_v10-003` was already flipped SUPERSEDED (2026-07-16T13:14Z, slot-3) once its own blocker
resolved structurally. This is backlog/orchestrator-admin work, outside `data_engineering` craft scope — filing here per
findings-triage rather than actioning it directly.

**Secondary, lower-priority**: consider a fleet-wide fix in `dispatch.py` — if a task accumulates N skips (e.g. ≥3)
within a short window (e.g. 2h) **across any slots**, auto-park it (priority → low + a synthetic `auto-parked:<task_id>`
prerequisite) until a human/main agent reviews and clears it. This generalizes past this one task to any future
"role-matched but structurally blocked" case. Not required to close this issue — the manual park above is sufficient for
the immediate bleed.

## Fix todos

- [x] ✅ [ADMIN] P1. Park `mvp_backfill_defi_onchain_v10-002`: `priority: 999` + `priority_override: true` +
      `prereqs.prerequisites: [defi_onchain_v10_universe_v2_seed_or_backfill_progressed]` (create the condition `false`
      via `POST /api/prerequisites/...` first) on its `backlog.yaml` entry, then `POST /api/backlog/reload`. **Applied
      2026-07-16T20:3xZ (data_engineering slot-3)** — condition created `false`; entry edited (`priority: 10→999`,
      `priority_override: false→true`,
      `prereqs.prerequisites: []→[defi_onchain_v10_universe_v2_seed_or_backfill_progressed]`); `/api/backlog/reload`
      confirmed `ok:true`; `GET /api/backlog` verified `priority: 999` live. Task released via `/skip-current-task`
      immediately after (gate itself still not met — this todo doesn't flip the G2 checkbox, only stops the redispatch).
      **Still open**: verify it survives the next `PlanRegenLoop` tick (not just `/reload`) per the
      `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` precedent — check back after the next tick. (repo:
      agent-orchestrator)
- [ ] [ADMIN] P1. Wire the unpark: whoever owns `data_completion_defi_2026_07_15.md`'s seed-chain progress (or the
      `[INFRA]` VM-relaunch todo) flips `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` → `true` once a chunk
      materially closes the `dex_pool_swaps`/`dex_pool_state` gap, then clears `priority_override`. (repo:
      agent-orchestrator)
- [ ] [DESIGN] P3. Evaluate the fleet-wide auto-park-on-repeated-skip heuristic described above; write it up as its own
      plan item if the operator agrees it's worth building. (repo: agent-orchestrator)

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-16** — Applied fix-todo-1 (data_engineering slot-3, dispatched to `mvp_backfill_defi_onchain_v10-002` at
  20:2xZ). Created prerequisite `defi_onchain_v10_universe_v2_seed_or_backfill_progressed=false`; edited the live
  `agent-orchestrator/data/config/backlog.yaml` entry (`priority→999`, `priority_override→true`,
  `prereqs.prerequisites→[defi_onchain_v10_universe_v2_seed_or_backfill_progressed]`); `/api/backlog/reload` →
  `ok:true`; `GET /api/backlog` confirmed `priority: 999` live. Released the in-progress dispatch via
  `/skip-current-task` (the gate itself remains unmet — see `mvp_backfill_defi_onchain_v10_2026_06_27.md` G2 Progress
  Log). Fix-todo-2 (unpark once the seed/backfill chain progresses) and fix-todo-3 (auto-park heuristic design) remain
  open.
