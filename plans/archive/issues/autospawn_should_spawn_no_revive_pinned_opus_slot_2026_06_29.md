---
doc_type: issue
title: AutoSpawn — _should_spawn does not revive a live-idle slot pinned to a higher-tier (opus) task
summary:
  The model-tier dispatch fix upgrades a slot's spawn model to its affinity-pinned task's tier, but only when the slot
  actually (re)spawns. A live-but-idle Sonnet slot that is an opus task's affinity target is never killed, so it never
  self-upgrades and the opus task can starve queued even with idle fleet headroom.
status: resolved
nature: record
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, autospawn, model-tier, opus, dispatch, starvation, follow-up]
related: [/codex/04-architecture/agent-orchestrator-autospawn.md]
created: 2026-06-29
parent_epic: orchestrator_master
priority: P2
source:
  [
    operator request 2026-06-29,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
    session 2026-06-28/29 opus-routing fix,
  ]
assigned_vm: planning
resolved_by: "agent-orchestrator@826a496 — see Fix section below"
locked_by:
execution_scope: orchestrator-agent
assigned_role: backend_engineer
model_tier: opus-required
thinking_tier: high
drift_direction: advance-code
last_updated: 2026-07-12
depends_on: []
---

> **(2026-07-12, finding 219, §A2 B-queue ruling)**: frontmatter `status` synced `open` → `resolved` (was: `open`) —
> this doc's single Fix todo is checked `[x]` with commit `agent-orchestrator@826a496`, 9 unit tests, and an integration
> assertion, and the Notes section frames it as closing "the residual starvation edge" with nothing else outstanding.

# AutoSpawn — `_should_spawn` doesn't revive a live-idle slot pinned to an opus task

## Context (the RESOLVED part — do not re-do)

The 2026-06-29 model-tier dispatch fix (codex `agent-orchestrator-autospawn.md` § "Model-tier-aware dispatch") routes
`model_tier: opus-required` to Opus workers via four mechanisms — prereq-aware tick model (`_top_queued_task_params`),
per-slot affinity-pinned upgrade (`_slot_required_model`), dispatch model-gate (`pick_next_task` /
`_task_outranks_slot`), upgrade-only (`_higher_model`). Commits `agent-orchestrator@c627276` + `@5929815`. **Verified
live**: an autospawned Opus slot executed an opus-required task (`mdps_polars_engine_cost_sharpening`). This issue is
the **residual edge only**.

## The residual gap (this issue)

The per-slot UPGRADE (`autospawn._slot_required_model`) only fires when `_should_spawn` ACTUALLY (re)spawns the target
slot. A **live-but-idle Sonnet slot** that is the `affinity=high` target of a queued opus task is **not killed** by
autospawn (it has a live worker, merely idle), so:

- it never self-upgrades to Opus;
- the dispatch model-gate correctly keeps the opus task off every OTHER slot;
- → the opus task can **starve queued** even with idle fleet headroom, until slot N happens to go idle/dead and respawn.

**Symptom to watch:** an opus-required task sits `queued` with `target_slot=N affinity=high` while slot N is
`idle`/`worker_alive=true` on Sonnet and no Opus slot appears despite account headroom.

## Fix

- [x] [AGENT] P2. ✅ (opus) Make autospawn (or the keeper) detect a **live slot whose model is BELOW** the tier of a
      prereq-met, `affinity=high` queued task targeting it, and **kill + respawn** it so the affinity-pinned UPGRADE
      (`_slot_required_model`) brings it up at the required model. Guard against flap (only an idle/parked worker, never
      one actively working) and churn (one respawn, then cooldown). — Gate: a unit test where a live-idle Sonnet slot
      pinned to a queued opus task is flagged for respawn; an integration assertion that an opus task no longer starves
      behind idle Sonnet headroom; `agent-orchestrator` QG green + quickmerge. — agent-orchestrator@826a496 (new
      `AutoSpawnLoop._maybe_kill_for_tier_upgrade` wired into `_run_one_tick` before `_should_spawn`; `status=='idle'`
      flap guard + per-slot cooldown churn guard in `_tier_upgrade_killed_at`; 9 unit tests + integration
      `_run_one_tick` assertion in `tests/test_autospawn.py`).

## Notes

- **Lower priority than the shipped fix** — the main routing works (opus tasks DO get Opus workers once their slot
  respawns). This closes only the residual starvation edge.
- **Do NOT hot-patch the live dispatcher under time pressure** — this is a deliberate, tested follow-up. The 2026-06-29
  session already shipped three live-dispatcher changes; this one earns its own clean pass.
