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
last_updated: 2026-07-17
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
      agent-orchestrator) **CONFIRMED REVERTED 2026-07-17T15:0xZ (data_engineering slot-2, re-dispatched to this task,
      `already_in_progress:     true`/`dispatch_reason: "resume"`)**: the park did NOT survive. `GET /api/backlog` + the
      live `agent-orchestrator/data/config/backlog.yaml` both showed `priority: 10` (reverted from `999`),
      `priority_override` field ABSENT entirely (not even `false`), `prereqs.prerequisites: []` (reverted from
      `[defi_onchain_v10_universe_v2_seed_or_backfill_progressed]`) — the gating condition itself was untouched
      (`defi_onchain_v10_universe_v2_seed_or_backfill_progressed=false`,
      `set_by: data_engineering-slot3,     set_at: 2026-07-16T20:30:56Z`, still live in `/api/state`'s `prerequisites`),
      only the task's hand-tuning was lost. **Refined root cause — this is NOT a recurrence of Defect A/B from
      `backlog_regen_drops_handtuned_prereqs_2026_07_12.md` (that doc's fix, `agent-orchestrator@8dd5763`, targets
      same-id priority re-derivation + docs the `prereqs.prerequisites` field correctly)**: the task's numeric ID
      SHIFTED from `-002` (what slot-3 parked) to `-001` (what this session was dispatched to) between park-time and now
      — `mvp_backfill_defi_onchain_v10-003` (the sibling DRIFT-specific todo) was flipped ✅ SUPERSEDED at
      2026-07-16T13:23Z (BEFORE the 20:3xZ park), so by the time of the NEXT `PlanRegenLoop` tick after the park, only
      one open checkbox remained in the plan and `regen_backlog_from_plan.py`'s positional numbering (`plan_order`-based
      suffix assignment across a plan's open todos) reassigned it `-001`. The regen's field-preservation logic (whatever
      merges hand-tuned `priority`/`priority_override`/`prereqs` across a regen tick) appears to be keyed by task ID —
      when the ID itself changes, the old `-002` row's hand-tuning has nothing to merge onto and the new `-001` row gets
      plan-derived defaults. This is a DISTINCT defect from Defect A/B: hand-tuned backlog fields are not durable across
      a plan-todo-count change that shifts the numeric suffix, even for an id that logically refers to the same checkbox
      throughout. **Re-applied the park under the current id** (`mvp_backfill_defi_onchain_v10-001`): same condition
      (already existed, still `false`, reused rather than recreated), `priority: 10→999`,
      `priority_override: (absent)→true`,
      `prereqs.prerequisites: []→[defi_onchain_v10_universe_v2_seed_or_backfill_progressed]` directly in the live
      `agent-orchestrator/data/config/backlog.yaml`, `POST /api/backlog/reload` → `ok:true`, `GET /api/backlog`
      confirmed `priority: 999` live. Filed a new fix-todo below for the renumbering-drops-hand-tuning defect itself
      (repo: agent-orchestrator) rather than re-closing this checkbox, since the underlying mechanism is still unfixed
      and will silently drop this exact park again the next time a sibling todo in this plan resolves (there are none
      left, but the pattern will recur on ANY multi-todo plan with a parked non-final task). (repo: agent-orchestrator)
- [ ] [ADMIN] P1. Wire the unpark: whoever owns `data_completion_defi_2026_07_15.md`'s seed-chain progress (or the
      `[INFRA]` VM-relaunch todo) flips `defi_onchain_v10_universe_v2_seed_or_backfill_progressed` → `true` once a chunk
      materially closes the `dex_pool_swaps`/`dex_pool_state` gap, then clears `priority_override`. (repo:
      agent-orchestrator)
- [ ] [DESIGN] P3. Evaluate the fleet-wide auto-park-on-repeated-skip heuristic described above; write it up as its own
      plan item if the operator agrees it's worth building. (repo: agent-orchestrator)
- [ ] [CODE] P1. **NEW (2026-07-17, data_engineering slot-2)**: fix `regen_backlog_from_plan.py`'s hand-tuned-field
      preservation so it survives a task's numeric-suffix renumbering, not just a same-id regen tick. Root cause: task
      ids are assigned positionally (`<plan-slug>-NNN` over a plan's remaining open todos via `plan_order`), so when a
      sibling todo in the SAME plan resolves/is removed, every subsequent todo's suffix shifts down — a parked task's
      hand-tuned `priority`/`priority_override`/`prereqs.prerequisites` are keyed to the OLD id and have nothing to
      merge onto under the NEW id, silently reverting to plan-derived defaults. Suggested fix direction: key the
      preservation-merge on a stable identity (e.g. `plan_ref` + a stable per-todo anchor — line-content hash or an
      explicit todo-id comment in the plan markdown — rather than the positional numeric suffix), or at minimum detect a
      renumbering (old id disappears + a new id appears at the same `plan_order` position with matching `brief`) and
      carry the hand-tuning across. Repro: this exact task went `-002` (parked 2026-07-16T20:3xZ) → `-001` (found
      reverted 2026-07-17T15:0xZ) when its sibling `-003` resolved between those two timestamps. (repo:
      agent-orchestrator)

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-17** — data_engineering slot-2, re-dispatched to `mvp_backfill_defi_onchain_v10-001`
  (`already_in_progress: true`/`dispatch_reason: "resume"`, ~19h after the 2026-07-16 park). Fresh
  `measure_honest_coverage.py --asset-group defi` re-run confirms the gate is still nowhere close on any of the 6
  data_types (numbers essentially unchanged vs the 2026-07-16T19:47Z reading — `dex_pool_swaps` still ~3.9M
  `expected_unattempted`) and the seed chain's own remaining work is explicitly "operator/VM, NOT code" per
  `data_completion_defi_2026_07_15.md`; zero DeFi seed/backfill VMs running for 5 of 6 data_types
  (`gcloud compute instances list` via the working non-snap SDK). **Found the 2026-07-16 park had been silently
  reverted**: task id shifted `-002`→`-001` (its sibling `-003` resolved the same evening, shifting the positional
  numbering), and the hand-tuned `priority`/`priority_override`/`prereqs.prerequisites` did not carry over to the new id
  — see the refined root-cause note on fix-todo-1 above (a distinct defect from Defect A/B, filed as a new fix-todo).
  Re-applied the park under `-001` (same pre-existing condition, still `false`); confirmed live via `GET /api/backlog`.
  No code changes; gate genuinely unmet; checkbox not flipped on the owning plan. `/skip-current-task` after re-parking.
- **2026-07-16** — Applied fix-todo-1 (data_engineering slot-3, dispatched to `mvp_backfill_defi_onchain_v10-002` at
  20:2xZ). Created prerequisite `defi_onchain_v10_universe_v2_seed_or_backfill_progressed=false`; edited the live
  `agent-orchestrator/data/config/backlog.yaml` entry (`priority→999`, `priority_override→true`,
  `prereqs.prerequisites→[defi_onchain_v10_universe_v2_seed_or_backfill_progressed]`); `/api/backlog/reload` →
  `ok:true`; `GET /api/backlog` confirmed `priority: 999` live. Released the in-progress dispatch via
  `/skip-current-task` (the gate itself remains unmet — see `mvp_backfill_defi_onchain_v10_2026_06_27.md` G2 Progress
  Log). Fix-todo-2 (unpark once the seed/backfill chain progresses) and fix-todo-3 (auto-park heuristic design) remain
  open.
