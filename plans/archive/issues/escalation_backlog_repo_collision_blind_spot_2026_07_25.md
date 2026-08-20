---
doc_type: issue
title:
  Escalation dispatch and backlog dispatch are two independently-atomic pipelines with zero cross-visibility on repo —
  an escalation worker was spawned onto instruments-service while a backlog worker already held that same repo
  (defi_gmx_venue_removal-003, slot 7), fully overlapping in real time
summary: >-
  Confirmed via live `/api/backlog` + `/api/activity` evidence (2026-07-25): task_dispatched fired exactly ONCE for
  defi_gmx_venue_removal-003 (slot 7, 10:28:43Z–11:35:48Z, sha 0214bb3c) — this is NOT a backlog claim race and NOT a
  false-reclaim/requeue (no stale_dispatch_reclaimed / slot_dispatch_unacked event exists for this task_id anywhere in
  the window; the backlog's own SQLite BEGIN IMMEDIATE serialization in session_scope() closes off a raw claim race by
  construction). What actually happened: a SEPARATE pipeline — `server/escalation.py::escalate()` — spawned an
  independent worker (slot 4, 11:18:49Z–11:31:40Z) onto the SAME repo (instruments-service) for an `ldr_qg_failure` wall
  (golden fixture/dedup-count stale after the sibling UAC GMX-removal commit), fully inside slot 7's still-open dispatch
  window on that repo. Root cause: `escalation.py::_find_open_escalation` dedups only on wall identity `(repo,
  pr_number, wall_type)`, never against the backlog's active-repo state; `escalation.py::_pick_free_slot` has no
  repo-collision check at all; and the backlog's own repo-collision protection (`dispatch.py::_blocks_repo_collision` →
  `_active_repos_excluding`) resolves each OTHER slot's repos via `backlog.get(slot.current_task)` — a typed/one-off
  agent slot (escalation/cicd/plan_health/conflict_resolver, claimed via `claim_slot_for_typed_agent`) has
  `SlotRow.current_task` set to `None` (the descriptor goes in `last_msg` instead — see Root cause item 3, corrected
  2026-07-25 after adversarial review), so `_active_repos_excluding` skips the slot via `if slot.current_task is None:
  continue` and never reaches `backlog.get()` at all. It contributes NOTHING to `active_repos` either way. The blind
  spot is bidirectional and structural: two atomically-correct claim mechanisms (backlog's SQLite-serialized
  transaction; escalation's own slot-pick loop), each internally consistent, with no shared repo-level lock or
  visibility between them. In THIS incident both workers happened to converge safely (the escalation fixed a stale
  fixture caused by an upstream UAC commit, independent of whether slot 7's own fix had landed; no reported file-level
  conflict), but the pattern is a real double-dispatch risk on the same repo any time an LDR QG wall fires for a repo a
  backlog task is already actively working.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, escalation, repo-collision, duplicate-dispatch, backlog, cicd]
related:
  [
    /plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P2
parent_epic: orchestrator_master
source:
  "sub-agent investigation (fresh context, dispatched to diagnose defi_gmx_venue_removal-003 duplicate-dispatch report)
  via SSM /api/backlog + /api/activity read + full read of server/routes/slots_worker.py, server/dispatch.py,
  server/db.py, server/state_store/tasks.py, server/stale_dispatch.py, server/worker_liveness_watchdog.py,
  server/escalation.py, 2026-07-25"
assigned_vm: NA
execution_scope: local-only
estimate_class: design
drift_direction: advance-code
resolved_by: agent-orchestrator@7c937f99e0 (option b, symmetric fix)
locked_by:
context_scope:
  [
    /plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/dispatch.py,
  ]
depends_on: []
---

> **🟢 ARCHIVED 2026-08-01** — both todos resolved. Operator directionality decision (b) symmetric was made AND
> implemented in the same commit, `agent-orchestrator@7c937f99e0` (2026-07-31). Zero open todos, `locked_by:` empty.

# Escalation ↔ backlog repo-collision blind spot — two dispatch pipelines, zero shared repo visibility

## Why this is filed as an issue, not shipped as a bugfix

The dispatching sub-agent was instructed to implement a minimal fix ONLY if the root cause was a backlog claim race
(fix: atomic `UPDATE ... WHERE status='queued'`) or a false-reclaim (fix: tighten a timeout/matching check) — and to
stop and write up the ambiguity otherwise. Both of those specific mechanisms were investigated and ruled out (see
summary). The actual gap requires a genuine design decision before any code should move, for reasons below — this is NOT
a case where a one-line patch is obviously correct.

## Evidence

- `10:28:43.968987Z` — `task_dispatched` → slot 7, task `defi_gmx_venue_removal-003`
  (`tier=1 priority=50 plan_order=2`).
- `11:18:49.825928Z` — `escalation_dispatch_initiated` slot 4,
  `escalation_id=agt-d660ec, repo=instruments-service, wall_type=ldr_qg_failure`.
- `11:19:45.143173Z` — `escalation_dispatched` slot 4.
- `11:22:48Z` — slot 4 `slot_progress`: "diagnosed: GMX golden fixture + rule11 dedup target-count constant stale after
  UAC GMX removal (uac@18d53d63); regenerated defi.json golden…".
- `11:27:28Z` — operator message: "escalation agt-d660ec for instruments-service#0 (ldr_qg_failure): fixed+pushed
  @8df301f4".
- `11:27:36Z` — `slot_done_one_off` (slot 4, lifecycle-complete).
- `11:31:40Z` — `escalation_resolved`, `resolution=qg_v2_green`.
- `11:35:48.443364Z` — `slot_done` on slot 7 for `defi_gmx_venue_removal-003`, sha `0214bb3c`.
- No `stale_dispatch_reclaimed` / `slot_dispatch_unacked` event exists for `defi_gmx_venue_removal-003` anywhere in the
  window — this rules out the reclaim/requeue failure mode entirely.

Slot 4's entire escalation lifecycle (`11:18:49`–`11:31:40`) sits fully inside slot 7's still-open dispatch window on
the same repo (`10:28:43`–`11:35:48`) — a genuine real-time overlap, not a narrow race or a minutes-apart re-dispatch
after abandonment.

## Root cause (confirmed, code-level)

1. `escalation.py::_find_open_escalation` (~line 716) dedups only on wall identity `(repo, pr_number, wall_type)` — it
   prevents a second escalation for the SAME wall, but never queries the backlog for tasks already dispatched against
   that `repo`.
2. `escalation.py::_pick_free_slot` (~line 171) picks any slot with no live tmux session — no repo-collision check at
   all.
3. `dispatch.py::_active_repos_excluding` (~line 690) — the backlog's OWN repo-collision table — resolves each other
   slot's repos via `backlog.get(slot.current_task)`. **Corrected 2026-07-25 (adversarial review caught the original
   mechanism citation was wrong):** typed/one-off agent slots (escalation/cicd/plan_health/conflict_resolver), claimed
   via `state_store.slots.claim_slot_for_typed_agent` (`server/state_store/slots.py:229-230`), do NOT get a free-text
   descriptor in `SlotRow.current_task` — that function explicitly sets `slot.current_task = None` and puts the
   descriptor in `slot.last_msg` instead (its own docstring: "a free-form descriptor must NOT go there"). So
   `_active_repos_excluding` skips the slot entirely via `if slot.current_task is None: continue` — it never even calls
   `backlog.get()` for these occupants. The end conclusion is unchanged (escalation-occupied slots are invisible to the
   repo-collision table), but the causal mechanism is `current_task is None`, not a `backlog.get()` miss on a descriptor
   string.
4. `SlotRow` (server/orm.py) has no structured `repo` column read directly by `_active_repos_excluding` for typed-agent
   occupants. **However** (also surfaced by adversarial review): `AgentRow.source` is already populated with the repo at
   escalation-dispatch time (`server/escalation.py`'s `register_agent(..., source=repo, ...)`), and
   `SlotRow.tmux_session` equals `AgentRow.tmux_session` for the same occupant (both derived from
   `tmux_spawn.session_name(slot_id)`) — so a join from `SlotRow` to `AgentRow` on `tmux_session` COULD recover the repo
   for escalation/cicd/conflict_resolver/data_pipeline_failure occupants today, with no schema change, just a new read.
   This is NOT universal: `plan_health`'s `register_agent` call (`server/plan_health.py:432-445`) does not set `source`
   at all (plan_health isn't repo-scoped, so arguably fine, but it means a join-based fix wouldn't uniformly cover every
   typed-agent kind — see the updated option list below).

## Why this needs a design decision, not a mechanical patch

- **Directionality is not obvious.** Two independent options were identified, and picking between them changes the
  system's behavior under load: (a) `escalate()` consults the backlog's active-repo state (via something like
  `dispatch._active_repos_excluding`) before dispatching a repo-scoped wall, and queues if it collides (the existing
  `_queue_escalation` retry machinery already exists for the no-capacity case and could plausibly be reused) — this
  protects only the direction actually observed in this incident (backlog-first, escalation-second). (b)
  `_active_repos_excluding` (and its sibling `_active_collision_groups_excluding`) is made aware of typed-agent
  occupants too (requires carrying a structured `repo` on the claim, not just a free-text descriptor) — this closes the
  gap symmetrically (backlog-first-then-escalation AND escalation-first-then-backlog) but requires a schema/interface
  change (`claim_slot_for_typed_agent` + every one-off caller — cicd/conflict_resolver/
  plan_health/data_pipeline_failure — would need to start passing a real `repo`, and `SlotRow` likely needs a new column
  since `current_task` is currently the only per-slot "what am I doing" field and is already overloaded as a
  human-readable descriptor). (c) **Cheaper partial version of (b), added 2026-07-25 after adversarial review**: join
  `SlotRow.tmux_session` to `AgentRow.tmux_session` and read `AgentRow.source` (already populated with the repo for
  escalation-dispatched agents, no schema change) — this makes `_active_repos_excluding` symmetric for
  escalation/cicd/conflict_resolver/data_pipeline_failure occupants specifically, at the cost of NOT covering
  `plan_health` (which never sets `source`) unless that call site is also updated. Whoever makes the directionality
  decision should weigh (c) against (b) as a lower-cost stepping stone, not just (a) vs (b).
- **Urgency-vs-safety tradeoff for escalations specifically.** Several wall_types (`ldr_qg_failure`, `sit_failure`,
  `main_ci_red`) exist BECAUSE CI is red — deferring/queuing that escalation until a same-repo backlog task finishes
  keeps CI red longer, which may itself be worse than the (bounded, so far self-resolving) collision risk. Whether ALL
  wall_types should defer-on-collision, or only some (and which), is a product/ops policy call, not a bug fix.
- **No `parallel_safe` equivalent exists for escalations.** `BacklogTask` has an explicit `parallel_safe: true` escape
  hatch a plan author can set; escalations have no equivalent concept today, so even the queuing behavior in option (a)
  needs a decision about whether it is unconditional or itself needs an override.
- **A single external read is not atomically safe against the fix it's meant to prevent.** The backlog's collision guard
  is correct BECAUSE the check lives inside a `session_scope()` (`BEGIN IMMEDIATE`)-serialized transaction. A naive
  `escalate()`-side check against `_active_repos_excluding` called from OUTSIDE that lock only narrows the race window,
  it doesn't close it — `escalate()`'s slot-pick loop already tolerates and retries "benign:" races today precisely
  because true atomicity across pipelines isn't free. Doing this correctly likely means either running the escalation's
  repo check inside the SAME transaction/lock the backlog uses, or accepting a best-effort (non-atomic) check as "good
  enough" — that acceptance is itself the design call.

## Todos (for a BACKEND owner + an operator design decision — NOT for autonomous dispatch as-is)

- [x] ✅ [OPERATOR-DECISION] P2. **DONE — `agent-orchestrator@7c937f99e0` (2026-07-31, slot-1 harsh_pc).** Decided
      **option (b), symmetric** — implemented, not just decided.
- [x] ✅ [BACKEND] P3. **DONE — same commit.** New `SlotRow.claimed_repo` column (+ migration), set by
      `claim_slot_for_typed_agent`, cleared by `assign_task_to_slot` on recycle. `dispatch._active_repos_excluding`
      renamed to public `active_repos_excluding` and extended to read `claimed_repo` for a `current_task=None`
      typed-occupant. `escalation.py::escalate()` gets a pre-dispatch collision check (queues or raises
      `EscalationError`, mirroring the existing no-capacity gate shapes) instead of dispatching onto an already-active
      repo. Best-effort, not fully atomic with the backlog's own BEGIN-IMMEDIATE-serialized claim — narrows the race
      window per this doc's own accepted tradeoff, does not fully close it. 10 new tests (dispatch
      `active_repos_excluding` ×4, claim/assign persistence ×3, escalation collision-guard ×3) + all 140 pre-existing
      tests in the touched files still pass. Full `quality-gates.sh` green (2155 passed, 2 skipped, basedpyright 0/0/0,
      ruff clean). Commit's own `Source:` line cites this doc directly.

## Triage note

Filed per the workspace's cross-repo/SSOT-contradiction big-finding triage rule — this is a structural gap in the
orchestrator's own dispatch correctness (cross-cutting: affects every repo any escalation wall can fire against while a
backlog worker is also active there), not scoped to any single asset_group. No code changed in agent-orchestrator by
this sub-agent — the investigation and this issue doc are the full deliverable for this pass, per the "stop and write up
the ambiguity" branch of the dispatching instructions.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the Todos heading itself reads
  `(for a BACKEND owner + an operator design decision — NOT for autonomous dispatch as-is)`; todo 1 is
  `[OPERATOR-DECISION]` on directionality (a)/(b)/(c) and todo 2 is labelled 'blocked on the decision above'. The doc's
  `Why this needs a design decision, not a mechanical patch` section adds an explicit urgency-vs-safety product/ops
  policy call. Same ruling in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`'s operator-decision Deferred list.
