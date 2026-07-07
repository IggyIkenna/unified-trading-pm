---
doc_type: issue
title:
  AO fleet stalled idle with ready tasks — backlog tier/role frozen (regen no-propagate) + no craft filter + slot_skips
  thrash
summary:
  On 2026-07-07 the agent-orchestrator fleet sat idle (0 working, 14 idle slots) while 30 tasks were queued and
  blocker-free. Not a crash — the server + VM were healthy and AutoSpawn was spawning workers every ~30s. Root causes
  compounded — the whole backlog was frozen at model=opus/effort=max (regen does not propagate plan frontmatter
  tier/role changes to already-queued tasks), so every spawn was Opus/max (a cost inefficiency — the accounts themselves
  are healthy, verified live); pick_next_task has no assigned_role craft filter, so infra tasks dispatched to
  data_engineering slots and were skipped; 326 per-(slot,task) slot_skips accumulated and persist across respawns,
  starving dispatch; and the monitor agents over-generalized one sports gate to the whole backlog and went passive. This
  doc records the failure mode + the prevention fixes so it does not recur.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch, autospawn, slot-skips, model-tier, craft-routing, fleet-stall, incident]
related:
  [
    instruments_completion_tracker_2026_07_06.md,
    ../infra_capture_and_devops_leftovers_2026_07_06.md,
    ../../../codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-07
last_updated: 2026-07-07
parent_epic: orchestrator_master
priority: P0
source: fleet-idle investigation 2026-07-07 (operator-reported no workers running)
assigned_vm: NA
resolved_by:
locked_by:
locked_since:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: high
estimate_class: design
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.2
supersedes:
superseded_by:
depends_on:
assigned_role: backend-engineer
drift_direction: advance-code
---

> **NOTIFY-OPERATOR incident (fleet availability).** 2026-07-07: the AO fleet went idle overnight with ~30 ready tasks
> queued. Investigated live (SSH + `state.db` + `/api/*`). NOT a crash — a compounded dispatch stall. This doc is the
> root-cause + prevention record.

## Symptom

- `/api/fleet/summary`: `slots_working=0`, `slots_idle=14`, `backlog_queued=30`, `backlog_dispatched=1`.
- `/api/backlog/{id}/blockers` for the queued tasks: **"ready (no blockers)"**.
- VM healthy (24d uptime, 53 GiB free RAM, 111 GiB free disk); server up on `127.0.0.1:8765`; AutoSpawn firing
  `autospawn_succeeded` every ~30s (journalctl: `--model opus --effort max --max-thinking-tokens 31999`).
- The main + monitor agents looped `"fleet deadlocked"` /
  `"30 tasks queued all gated on understat prereq → continue monitoring"`.

## Root causes (compounded — no single bug)

1. **Backlog tier/role FROZEN — regen does not propagate plan frontmatter changes (PRIMARY).** The DB `tasks` table
   stores neither `model` nor `assigned_role`; those live on the `backlog.yaml` `BacklogTask`, set by
   `regen_backlog_from_plan.py` at task CREATION. Regen is idempotent-by-brief
   (`if description in existing_briefs: skip`), so when a plan's `model_tier` / `thinking_tier` / `assigned_role` change
   later, the **already-queued tasks keep their original tier/role**. Evidence: after retiering all 6 plans to
   Sonnet/high, every queued task still read `model=opus effort=max` (incl. `tradfi_v9_stage1_finish-004`, whose plan
   was Sonnet since 2026-07-06), and `infra_capture_and_devops_leftovers-001` still read `role=infra` after the plan was
   re-homed to `data_engineering`. → **Every spawn is Opus/max** (`_top_queued_task_params` picks the top task's tier) —
   a cost inefficiency (burns Opus quota for tasks the plans intended to run cheap on Sonnet), though NOT an
   availability blocker since the accounts are healthy (RC-5).

2. **`pick_next_task` has NO `assigned_role` craft filter.** `server/dispatch.py::pick_next_task` filters on status,
   model-tier, deferred-prefix, prereqs, affinity(target_slot), repo-collision, collision_group, and slot_skips — but
   **not craft/role**. So an `assigned_role: infra` task is dispatched to a `data_engineering` slot, which then refuses
   it at the worker level ("role mismatch — data_engineering slot cannot execute infra-scoped task") and calls
   `/skip-current-task`. The `long_lived_vm_logs` infra task was re-dispatched to the wrong craft **6 times in one day**
   (the plan's own Progress Log recommends "land the AO dispatcher-side `assigned_role` filter").

3. **`slot_skips` accumulate and persist across respawns.** Each craft-mismatch / prereq-park / context-limit skip
   writes a per-(slot_id, task_id) row (`slot_skips`), and `pick_next_task` excludes them (filter 6). Skips are keyed by
   **slot_id, not worker session** — so when AutoSpawn respawns a worker on the same slot, it INHERITS the slot's old
   skips. Overnight this reached **326 rows across 95 tasks × 13 slots (~30/slot)** and starved dispatch (though not to
   a full deadlock — every slot could still take 15-30 of the 30 queued; it was thrash + partial starvation, not a hard
   lock).

4. **Monitor agents over-generalized one real gate.** One genuine sports gate (understat backfill VM incomplete) was
   extrapolated by the main + monitor agents to `"30 tasks all gated on understat prereq"`, and they dropped into
   passive monitoring instead of dispatching — even though the blockers API said the tasks were ready.

5. **Account status — VERIFIED HEALTHY 2026-07-07, NOT a root cause.** A live `claude /usage` refresh on all 4 accounts
   (each via its own `oauth_token_env_file`; probe SUCCEEDED = tokens authenticate) returned `unified_status: allowed`
   for all 4, none rate-limited (`rate_limited_until` all stale at 2026-07-01, expired), with subscription headroom
   (weekly 25-78%, 5h 12-19%). The `overage_status: rejected` (sub-c `out_of_credits`; sub-a/b/d `org_level_disabled`)
   governs only PAID OVERAGE beyond the subscription — it does NOT block normal in-quota use. Earlier framing of
   accounts as a blocker was WRONG; corrected here. The Opus/max load (RC-1) is a COST/efficiency problem, not an
   availability one.

## Immediate remediation applied 2026-07-07

- ✅ Retiered all 6 instruments-completion plans to Sonnet/high (Plan 1 was the last Opus one; its C2 justification
  shipped `is@2170d9a3`) — `unified-trading-pm@65e5d01ee`. _(Plan-level; inert on existing backlog tasks until RC-1 is
  addressed — see below.)_
- ✅ Re-homed `infra_capture_and_devops_leftovers` role `infra` → `data_engineering` + `[INFRA]`→`[DATA]` retag — same
  commit. _(Same RC-1 caveat.)_
- ✅ Cleared the 145 `slot_skips` rows tied to the 30 queued tasks (backup: VM `/tmp/slot_skips_backup.json`) — fleet
  began resuming (`working` 0→1, `dispatched` 1→2).
- ⏳ **PENDING OPERATOR DECISION — make the retier/re-home effective on the frozen backlog.** Requires updating the
  queued tasks' `model`/`effort`/`assigned_role` in `backlog.yaml`, which crosses the **"never hand-edit backlog.yaml"**
  HARD RULE. Options: (a) one-time scoped correction of the 6 plans' tasks (backed up, reversible); (b) fix RC-1 in
  regen (below) + reload; (c) delete+regen the tasks (new IDs, lost dispatch state). NOT done autonomously.
- ✅ Accounts verified HEALTHY (live `/usage` refresh 2026-07-07) — all 4 `unified_status: allowed`, authenticated, not
  rate-limited, subscription headroom. The overage-rejected flags are not a blocker. NO operator action needed on
  accounts.

## Prevention (the fix-so-it-doesn't-recur todos)

- [ ] [CODE] P0. **regen must propagate tier/role changes to existing queued tasks** — when a plan's
      `model_tier`/`thinking_tier`/`assigned_role` changes, update the matching `backlog.yaml` tasks (match by
      `plan_ref` + brief) instead of skip-on-dedup. Or add an explicit `POST /api/backlog/retier-from-plans` refresh op.
      This is the PRIMARY gap — without it, every plan retier is silently inert on in-flight work.
- [ ] [CODE] P0. **Add an `assigned_role` craft filter to `pick_next_task`** — a task whose `assigned_role` has no
      matching-craft idle slot should NOT be dispatched to a mismatched slot (leave it queued, like the model-tier
      gate). Kills the dispatch→skip→re-dispatch craft-mismatch thrash (6× in one day on one task).
- [ ] [CODE] P1. **`slot_skips` hygiene** — expire skips after N hours, and/or clear a task's skips when its plan
      changes (tier/role/brief) or a prereq lands, and/or scope craft-mismatch skips so a re-home clears them. Persisted
      per-slot skips inheriting across respawns is the starvation multiplier.
- [ ] [CODE] P1. **AutoSpawn should not spawn the whole tick at the top task's tier when the queue is mixed-tier** —
      spawn per-task-tier (or at least don't force Opus for a queue that is 29/30 Sonnet). Ref `_top_queued_task_params`
      "known limitation".
- [ ] [DESIGN] P2. **Monitor/main agent guard** — do not extrapolate a single task's gate to the whole backlog; re-check
      `/api/backlog/{id}/blockers` before declaring "fleet deadlocked" and going passive.
- [ ] [ADMIN] P2. **Operating guidance** — avoid a single high-priority Opus plan mixed with Sonnet plans in the same
      queue (it drags every spawn to Opus until RC-4 is fixed); if a plan genuinely needs Opus, isolate it.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-07** — Filed from the fleet-idle investigation. RC-1 (regen no-propagate → whole backlog frozen Opus/max) is
  the primary finding; RC-2 (no craft filter) + RC-3 (slot_skips thrash) compound it. Remediation applied: plans
  retiered/re-homed (`pm@65e5d01ee`), 145 queued-task slot_skips cleared (fleet resuming). Backlog tier-correction +
  account credits pending operator.
